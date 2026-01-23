"""
Complete pipeline to load financial data into SQLite and ChromaDB.

Flow:
1. Load raw extracted CSV → SQLite via FinancialDataLoader
2. Load analysis CSVs → SQLite via FinancialRatioLoader
3. Synchronize SQLite → ChromaDB via DataSynchronizer
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from db.init_db import DatabaseManager, DatabaseFactory
    from db.loaders import FinancialDataLoader, FinancialRatioLoader
    from db.vector_sync import DataSynchronizer
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from db.init_db import DatabaseManager, DatabaseFactory
    from db.loaders import FinancialDataLoader, FinancialRatioLoader
    from db.vector_sync import DataSynchronizer

logger = logging.getLogger(__name__)


def load_financial_data_pipeline(
    raw_csv: str,
    analysis_dir: str,
    db_type: str = 'sqlite',
    db_path: str = None,
    chroma_path: str = None
) -> Dict[str, any]:
    """
    Complete pipeline: CSV → SQLite → ChromaDB
    
    Args:
        raw_csv: Path to raw extracted financial data CSV
        analysis_dir: Path to analysis CSV directory
        db_type: Database type ('sqlite' or 'postgresql')
        db_path: Path for SQLite database (if using SQLite)
        chroma_path: Path for ChromaDB persistence
        
    Returns:
        Dictionary with pipeline results and counts
    """
    logger.info("="*80)
    logger.info("FINANCIAL DATA LOADING PIPELINE")
    logger.info("="*80)
    
    results = {
        'raw_records_loaded': 0,
        'ratio_records_loaded': 0,
        'chroma_documents': 0,
        'errors': []
    }
    
    try:
        # 1. Initialize database
        logger.info("\n[1/4] Initializing database...")
        factory = DatabaseFactory()
        db_manager = factory.create_manager(db_type, db_path=db_path)
        db_manager.init_db()
        logger.info(f"✓ Database initialized ({db_type})")
        
        # 2. Load raw financial data
        logger.info("\n[2/4] Loading raw financial data from CSV...")
        raw_csv_path = Path(raw_csv)
        if raw_csv_path.exists():
            loader = FinancialDataLoader(db_manager)
            inserted = loader.load_from_csv(str(raw_csv_path))
            results['raw_records_loaded'] = inserted
            logger.info(f"✓ Loaded {inserted} financial records")
        else:
            msg = f"Raw CSV not found: {raw_csv}"
            logger.error(msg)
            results['errors'].append(msg)
        
        # 3. Load financial ratios from analysis CSVs
        logger.info("\n[3/4] Loading analysis results...")
        analysis_path = Path(analysis_dir)
        
        ratio_loader = FinancialRatioLoader(db_manager)
        
        # Load each analysis CSV
        ratio_files = [
            'yoy_growth_analysis.csv',
            'profit_margin_analysis.csv',
            'financial_ratios_analysis.csv'
        ]
        
        for ratio_file in ratio_files:
            file_path = analysis_path / ratio_file
            if file_path.exists():
                count = ratio_loader.load_from_csv(str(file_path), ratio_file.replace('_analysis.csv', ''))
                results['ratio_records_loaded'] += count
                logger.info(f"✓ Loaded {count} records from {ratio_file}")
            else:
                logger.warning(f"Analysis file not found: {file_path}")
        
        # 4. Synchronize to ChromaDB
        logger.info("\n[4/4] Synchronizing to ChromaDB (vector database)...")
        
        # Initialize ChromaDB synchronizer
        if chroma_path is None:
            chroma_path = Path(__file__).parent.parent.parent / 'data' / 'chroma_db'
        
        sync = DataSynchronizer(db_manager, chroma_path=str(chroma_path))
        sync.init_chroma()
        
        # Sync all companies and their financial data
        doc_count = sync.sync_all_data()
        results['chroma_documents'] = doc_count
        logger.info(f"✓ Synchronized {doc_count} documents to ChromaDB")
        
        # 5. Summary
        logger.info("\n" + "="*80)
        logger.info("PIPELINE COMPLETE")
        logger.info("="*80)
        logger.info(f"Raw financial records loaded: {results['raw_records_loaded']}")
        logger.info(f"Ratio analysis records loaded: {results['ratio_records_loaded']}")
        logger.info(f"ChromaDB documents created: {results['chroma_documents']}")
        
        if results['errors']:
            logger.warning(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                logger.warning(f"  - {error}")
        
        logger.info("="*80)
        
        return results
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        results['errors'].append(str(e))
        return results


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Paths
    root = Path(__file__).parent.parent.parent
    raw_csv = root / 'data' / 'financial_data_raw.csv'
    analysis_dir = root / 'data' / 'analysis'
    db_path = root / 'data' / 'financial_analyzer.db'
    chroma_path = root / 'data' / 'chroma_db'
    
    # Run pipeline
    results = load_financial_data_pipeline(
        raw_csv=str(raw_csv),
        analysis_dir=str(analysis_dir),
        db_type='sqlite',
        db_path=str(db_path),
        chroma_path=str(chroma_path)
    )
    
    # Exit with error code if there were errors
    exit(0 if not results['errors'] else 1)
