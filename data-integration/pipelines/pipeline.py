"""
Complete Financial Data Pipeline Orchestrator

Orchestrates the entire flow:
1. Extract financial data from SEC EDGAR
2. Calculate metrics and ratios
3. Store in relational and vector databases
4. Export analysis results

This module coordinates all components for a complete data pipeline.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.extract_10k_data import ExtractionPipeline
from analysis.analysis_calculator import analyze_financial_data
from db import (
    DatabaseFactory,
    ChromaVectorDB,
    sync_extraction_to_databases,
    DatabaseInitializer,
)

logger = logging.getLogger(__name__)


class FinancialDataPipeline:
    """Complete financial data extraction, analysis, and storage pipeline"""
    
    def __init__(
        self,
        sec_identity: str,
        data_dir: Optional[str] = None,
        db_type: str = 'sqlite'
    ):
        """
        Initialize pipeline.
        
        Args:
            sec_identity: Identity string for SEC EDGAR API (e.g., "Name email@example.com")
            data_dir: Base data directory (default: ../data/)
            db_type: 'sqlite' or 'postgresql'
        """
        self.sec_identity = sec_identity
        
        # Setup directories
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'
        else:
            data_dir = Path(data_dir)
        
        self.data_dir = data_dir
        self.raw_csv = data_dir / 'financial_data_raw.csv'
        self.analysis_dir = data_dir / 'analysis'
        self.db_path = data_dir / 'financial.db'
        self.vector_db_path = data_dir / 'chroma'
        
        # Initialize directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Database setup
        self.db_type = db_type
        self.db = None
        self.vector_db = None
        
        logger.info(f"Pipeline initialized: {self.data_dir}")
    
    def extract_data(
        self,
        companies: list,
        years: int = 3,
        force_rerun: bool = False
    ) -> str:
        """
        Extract financial data from SEC EDGAR.
        
        Args:
            companies: List of (ticker, name) tuples
            years: Number of years to extract
            force_rerun: Skip CSV if it exists (default: False)
            
        Returns:
            Path to generated CSV file
        """
        logger.info("="*80)
        logger.info("PHASE 1: DATA EXTRACTION")
        logger.info("="*80)
        
        # Check if CSV already exists
        if self.raw_csv.exists() and not force_rerun:
            logger.info(f"✓ CSV already exists: {self.raw_csv}")
            logger.info("  (use force_rerun=True to re-extract)")
            return str(self.raw_csv)
        
        try:
            logger.info(f"Extracting data for {len(companies)} companies...")
            
            pipeline = ExtractionPipeline(self.sec_identity, str(self.raw_csv))
            pipeline.extract_batch(companies, years=years)
            csv_path = pipeline.save_csv()
            
            logger.info(f"✓ Extraction complete: {csv_path}")
            logger.info(f"  Companies: {[c[0] for c in companies]}")
            logger.info(f"  Years: {years}")
            
            return str(csv_path)
        
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise
    
    def analyze_data(self) -> Dict:
        """
        Analyze extracted financial data and calculate metrics.
        
        Returns:
            Summary report dictionary
        """
        logger.info("="*80)
        logger.info("PHASE 2: FINANCIAL ANALYSIS")
        logger.info("="*80)
        
        try:
            logger.info(f"Analyzing data from: {self.raw_csv}")
            
            summary, files = analyze_financial_data(str(self.raw_csv), str(self.analysis_dir))
            
            logger.info("✓ Analysis complete")
            logger.info(f"  Revenue leaders: {[r['company'] for r in summary['revenue_ranking'][:3]]}")
            
            if 'profitability_leaders' in summary:
                logger.info(f"  Profitability leaders: {[p['company'] for p in summary['profitability_leaders'][:3]]}")
            
            logger.info(f"  Output files: {len(files)}")
            for name, path in files.items():
                logger.info(f"    - {name}")
            
            return summary
        
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
    
    def initialize_databases(self, use_vector_db: bool = True):
        """
        Initialize relational and vector databases.
        
        Args:
            use_vector_db: Include vector DB for semantic search
        """
        logger.info("="*80)
        logger.info("PHASE 3: DATABASE INITIALIZATION")
        logger.info("="*80)
        
        try:
            # Relational database
            if self.db_type == 'sqlite':
                logger.info(f"Initializing SQLite: {self.db_path}")
                self.db = DatabaseFactory.create_sqlite(str(self.db_path))
            else:
                raise ValueError(f"Unsupported DB type: {self.db_type}")
            
            self.db.create_tables()
            logger.info("✓ Relational database initialized")
            
            # Vector database
            if use_vector_db:
                logger.info(f"Initializing Chroma (vector DB): {self.vector_db_path}")
                self.vector_db = ChromaVectorDB(persist_dir=str(self.vector_db_path))
                self.vector_db.create_collection()
                logger.info("✓ Vector database initialized")
        
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def load_data_to_databases(self) -> Tuple[int, int]:
        """
        Load extracted CSV data into databases.
        
        Returns:
            Tuple of (relational_count, vector_count)
        """
        logger.info("="*80)
        logger.info("PHASE 4: DATA LOADING")
        logger.info("="*80)
        
        if not self.raw_csv.exists():
            raise FileNotFoundError(f"CSV not found: {self.raw_csv}")
        
        if self.db is None:
            raise RuntimeError("Database not initialized. Call initialize_databases() first.")
        
        try:
            logger.info(f"Loading CSV to databases: {self.raw_csv}")
            
            rel_count, vec_count = sync_extraction_to_databases(
                csv_path=str(self.raw_csv),
                db_manager=self.db,
                vector_db=self.vector_db
            )
            
            logger.info(f"✓ Data loading complete")
            logger.info(f"  Relational records: {rel_count}")
            logger.info(f"  Vector documents: {vec_count}")
            
            return rel_count, vec_count
        
        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            raise
    
    def run_complete_pipeline(
        self,
        companies: list,
        years: int = 3,
        force_extract: bool = False,
        use_vector_db: bool = True
    ) -> Dict:
        """
        Run the complete financial data pipeline end-to-end.
        
        Args:
            companies: List of (ticker, name) tuples to extract
            years: Number of fiscal years to extract
            force_extract: Force re-extraction even if CSV exists
            use_vector_db: Include vector database for semantic search
            
        Returns:
            Pipeline results including summary report and statistics
        """
        logger.info("\n" + "="*80)
        logger.info("FINANCIAL DATA PIPELINE - COMPLETE RUN")
        logger.info("="*80 + "\n")
        
        results = {
            'status': 'running',
            'timestamp': None,
            'phases': {}
        }
        
        try:
            import datetime
            results['timestamp'] = datetime.datetime.now().isoformat()
            
            # Phase 1: Extract
            csv_path = self.extract_data(companies, years, force_extract)
            results['phases']['extraction'] = {'status': 'success', 'csv_path': csv_path}
            
            # Phase 2: Analyze
            summary = self.analyze_data()
            results['phases']['analysis'] = {'status': 'success', 'summary': summary}
            
            # Phase 3: Initialize Databases
            self.initialize_databases(use_vector_db)
            results['phases']['db_init'] = {'status': 'success'}
            
            # Phase 4: Load Data
            rel_count, vec_count = self.load_data_to_databases()
            results['phases']['data_loading'] = {
                'status': 'success',
                'relational_records': rel_count,
                'vector_documents': vec_count
            }
            
            results['status'] = 'complete'
            
            # Print summary
            self._print_completion_summary(results)
            
            logger.info("\n" + "="*80)
            logger.info("✅ PIPELINE COMPLETE")
            logger.info("="*80)
            
            return results
        
        except Exception as e:
            logger.error(f"\n❌ PIPELINE FAILED: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            raise
    
    def _print_completion_summary(self, results: Dict):
        """Print detailed completion summary"""
        print("\n" + "="*80)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*80)
        
        summary = results['phases']['analysis']['summary']
        
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"  Companies analyzed: {summary['companies_analyzed']}")
        print(f"  Total records: {summary['total_records']}")
        print(f"  Fiscal years: {summary['fiscal_years']}")
        
        print(f"\n💰 REVENUE LEADERS (Latest Year):")
        for item in summary['revenue_ranking'][:3]:
            print(f"  {item['rank']}. {item['company']} ({item['ticker']}): ${item['revenue_billions']}B")
        
        if 'growth_leaders' in summary:
            print(f"\n📈 GROWTH LEADERS (YoY Revenue Growth):")
            for item in summary['growth_leaders'][:3]:
                if item['revenue_yoy_percent']:
                    print(f"  {item['company']} ({item['ticker']}): {item['revenue_yoy_percent']:+.2f}%")
        
        if 'profitability_leaders' in summary:
            print(f"\n📊 PROFITABILITY LEADERS (Net Profit Margin):")
            for item in summary['profitability_leaders'][:3]:
                print(f"  {item['company']} ({item['ticker']}): {item['profit_margin_percent']:.2f}%")
        
        if 'financial_health' in summary:
            print(f"\n🏦 FINANCIAL HEALTH (Debt-to-Equity):")
            for item in summary['financial_health'][:3]:
                print(f"  {item['company']} ({item['ticker']}): {item['debt_to_equity']:.2f} ({item['leverage_status']})")
        
        loading = results['phases']['data_loading']
        print(f"\n💾 DATABASE STORAGE:")
        print(f"  Relational records: {loading['relational_records']}")
        print(f"  Vector documents: {loading['vector_documents']}")
        
        print("\n" + "="*80)
        print("✅ All phases completed successfully!")
        print("="*80 + "\n")


def main():
    """Example usage of the complete pipeline"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('financial_pipeline.log'),
            logging.StreamHandler()
        ]
    )
    
    # Pipeline configuration
    SEC_IDENTITY = "KPATCHA Josue josuekpatcha1@gmail.com"
    
    # Large list of companies for comprehensive analysis
    COMPANIES = [
        # Tech Giants
        ('MSFT', 'Microsoft'),
        ('AAPL', 'Apple'),
        ('TSLA', 'Tesla'),
        ('GOOGL', 'Alphabet'),
        ('META', 'Meta Platforms'),
        ('NVDA', 'NVIDIA'),
        ('AMD', 'Advanced Micro Devices'),
        ('INTC', 'Intel'),
        
        # Financials
        ('JPM', 'JPMorgan Chase'),
        ('BAC', 'Bank of America'),
        ('WFC', 'Wells Fargo'),
        ('GS', 'Goldman Sachs'),
        ('MS', 'Morgan Stanley'),
        
        # Consumer/Retail
        ('WMT', 'Walmart'),
        ('KO', 'Coca-Cola'),
        ('PEP', 'PepsiCo'),
        ('MCD', 'McDonald\'s'),
        ('TM', 'Toyota'),
        ('F', 'Ford'),
        
        # Healthcare/Pharma
        ('JNJ', 'Johnson & Johnson'),
        ('PFE', 'Pfizer'),
        ('ABBV', 'AbbVie'),
        ('MRK', 'Merck'),
        ('LLY', 'Eli Lilly'),
        
        # Energy/Utilities
        ('XOM', 'ExxonMobil'),
        ('CVX', 'Chevron'),
        ('NEE', 'NextEra Energy'),
        ('SO', 'Southern Company'),
        
        # Industrial/Manufacturing
        ('BA', 'Boeing'),
        ('CAT', 'Caterpillar'),
        ('HON', 'Honeywell'),
        ('MMM', '3M'),
    ]
    
    # Initialize and run pipeline
    pipeline = FinancialDataPipeline(
        sec_identity=SEC_IDENTITY,
        db_type='sqlite'
    )
    
    try:
        results = pipeline.run_complete_pipeline(
            companies=COMPANIES,
            years=3,
            force_extract=False,
            use_vector_db=True
        )
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
