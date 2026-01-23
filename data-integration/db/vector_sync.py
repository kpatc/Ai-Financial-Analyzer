"""
Vector database synchronization module.
Handles data flow between relational DB and vector DB (Chroma) for semantic search.
"""

import logging
from typing import List, Optional, Dict
import pandas as pd
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

try:
    from schemas.models import Company, FinancialMetric
except ImportError:
    from ..schemas.models import Company, FinancialMetric

logger = logging.getLogger(__name__)


class ChromaVectorDB:
    """Wrapper for Chroma vector database"""
    
    def __init__(self, persist_dir: Optional[str] = None, collection_name: str = 'financial_docs'):
        """
        Initialize Chroma vector database.
        
        Args:
            persist_dir: Directory for persistent storage. If None, uses in-memory.
            collection_name: Default collection name
        """
        if chromadb is None:
            raise ImportError("chromadb not installed. Run: pip install chromadb")
        
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.client = self._init_client()
        self.collection = None
    
    def _init_client(self):
        """Initialize Chroma client"""
        try:
            if self.persist_dir:
                # Persistent mode
                settings = Settings(
                    chroma_db_impl='duckdb+parquet',
                    persist_directory=str(self.persist_dir),
                    anonymized_telemetry=False,
                )
                client = chromadb.Client(settings)
                logger.info(f"Chroma initialized (persistent): {self.persist_dir}")
            else:
                # In-memory mode
                client = chromadb.Client()
                logger.info("Chroma initialized (in-memory)")
            
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}")
            raise
    
    def create_collection(self, name: str = None):
        """Create or get a collection"""
        name = name or self.collection_name
        try:
            self.collection = self.client.get_or_create_collection(name=name)
            logger.info(f"Collection ready: {name}")
            return self.collection
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadatas: List[Dict],
        collection: str = None
    ):
        """Add documents to collection"""
        collection = collection or self.collection_name
        
        if not self.collection:
            self.create_collection(collection)
        
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Added {len(documents)} documents to {collection}")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        collection: str = None
    ) -> Dict:
        """
        Search documents by semantic similarity.
        
        Args:
            query: Search query
            n_results: Number of results to return
            collection: Collection name
            
        Returns:
            Search results with documents and metadata
        """
        collection = collection or self.collection_name
        
        if not self.collection:
            self.create_collection(collection)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None
    
    def delete_all(self, collection: str = None):
        """Delete all documents in collection"""
        collection = collection or self.collection_name
        
        try:
            # Get all IDs
            collection_obj = self.client.get_collection(name=collection)
            all_ids = collection_obj.get()['ids']
            
            # Delete in batches
            batch_size = 100
            for i in range(0, len(all_ids), batch_size):
                batch = all_ids[i:i+batch_size]
                collection_obj.delete(ids=batch)
            
            logger.info(f"Deleted {len(all_ids)} documents from {collection}")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
    
    def persist(self):
        """Persist data to disk (if using persistent mode)"""
        if self.persist_dir and hasattr(self.client, 'persist'):
            try:
                self.client.persist()
                logger.info("Vector DB persisted to disk")
            except Exception as e:
                logger.warning(f"Failed to persist: {e}")


class VectorSynchronizer:
    """Synchronize between relational and vector databases"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        vector_db: Optional[ChromaVectorDB] = None
    ):
        """
        Initialize synchronizer.
        
        Args:
            db_manager: Relational database manager
            vector_db: Chroma vector database (created if None)
        """
        self.db = db_manager
        self.vector_db = vector_db or ChromaVectorDB()
    
    def sync_to_vector_db(self) -> int:
        """
        Sync all financial data from relational DB to vector DB.
        
        Returns:
            Number of documents synced
        """
        logger.info("Starting synchronization to vector DB...")
        
        try:
            session = self.db.get_session()
            
            # Get all companies
            companies = session.query(Company).all()
            
            documents = []
            ids = []
            metadatas = []
            
            for company in companies:
                # Get all financials for company
                financials = session.query(FinancialMetric).filter_by(company_id=company.id).order_by(
                    FinancialMetric.fiscal_year.desc()
                ).all()
                
                for fm in financials:
                    # Create document
                    doc_text = self._create_document(company, fm)
                    doc_id = f"{company.ticker}_{fm.fiscal_year.year}"
                    
                    # Metadata for filtering
                    metadata = {
                        'ticker': company.ticker,
                        'company': company.name,
                        'fiscal_year': str(fm.fiscal_year.year),
                        'source': 'financial_metrics',
                    }
                    
                    documents.append(doc_text)
                    ids.append(doc_id)
                    metadatas.append(metadata)
            
            # Add to vector DB
            if documents:
                self.vector_db.create_collection()
                self.vector_db.add_documents(documents, ids, metadatas)
            
            logger.info(f"Synchronized {len(documents)} documents to vector DB")
            return len(documents)
        
        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            return 0
        finally:
            session.close()
    
    def sync_company(self, ticker: str) -> int:
        """
        Sync specific company data to vector DB.
        
        Args:
            ticker: Company ticker
            
        Returns:
            Number of documents synced
        """
        logger.info(f"Syncing company: {ticker}")
        
        try:
            session = self.db.get_session()
            
            company = session.query(Company).filter_by(ticker=ticker).first()
            if not company:
                logger.warning(f"Company not found: {ticker}")
                return 0
            
            financials = session.query(FinancialMetric).filter_by(company_id=company.id).all()
            
            documents = []
            ids = []
            metadatas = []
            
            for fm in financials:
                doc_text = self._create_document(company, fm)
                doc_id = f"{company.ticker}_{fm.fiscal_year.year}"
                
                metadata = {
                    'ticker': company.ticker,
                    'company': company.name,
                    'fiscal_year': str(fm.fiscal_year.year),
                    'source': 'financial_metrics',
                }
                
                documents.append(doc_text)
                ids.append(doc_id)
                metadatas.append(metadata)
            
            if documents:
                self.vector_db.create_collection()
                self.vector_db.add_documents(documents, ids, metadatas)
            
            logger.info(f"Synced {len(documents)} documents for {ticker}")
            return len(documents)
        
        except Exception as e:
            logger.error(f"Company sync failed: {e}")
            return 0
        finally:
            session.close()
    
    def search_financial_documents(
        self,
        query: str,
        n_results: int = 5
    ) -> Dict:
        """
        Search financial documents by semantic similarity.
        
        Args:
            query: Natural language search query
            n_results: Number of results
            
        Returns:
            Search results with metadata
        """
        self.vector_db.create_collection()
        return self.vector_db.search(query, n_results)
    
    def _create_document(self, company: Company, fm: FinancialMetric) -> str:
        """
        Create a document string from financial metrics.
        Optimized for semantic search with company info enrichment.
        """
        lines = [
            f"Company: {company.name}",
            f"Ticker: {company.ticker}",
            f"Fiscal Year: {fm.fiscal_year.year}",
        ]
        
        # Add company information for semantic enrichment
        if company.sector:
            lines.append(f"Sector: {company.sector}")
        if company.industry:
            lines.append(f"Industry: {company.industry}")
        if hasattr(company, 'cik') and company.cik:
            lines.append(f"CIK: {company.cik}")
        if hasattr(company, 'state_of_incorporation') and company.state_of_incorporation:
            lines.append(f"State: {company.state_of_incorporation}")
        
        lines.append("")
        lines.append("Financial Metrics:")
        
        # Income Statement
        if fm.total_revenue is not None:
            lines.append(f"Total Revenue: ${fm.total_revenue/1e9:.2f}B")
        if fm.cogs is not None:
            lines.append(f"COGS: ${fm.cogs/1e9:.2f}B")
        if fm.gross_profit is not None:
            lines.append(f"Gross Profit: ${fm.gross_profit/1e9:.2f}B")
        if fm.operating_expenses is not None:
            lines.append(f"Operating Expenses: ${fm.operating_expenses/1e9:.2f}B")
        if fm.operating_income is not None:
            lines.append(f"Operating Income: ${fm.operating_income/1e9:.2f}B")
        if fm.net_income is not None:
            lines.append(f"Net Income: ${fm.net_income/1e9:.2f}B")
        
        # Balance Sheet
        if fm.total_assets is not None:
            lines.append(f"Total Assets: ${fm.total_assets/1e9:.2f}B")
        if fm.current_assets is not None:
            lines.append(f"Current Assets: ${fm.current_assets/1e9:.2f}B")
        if fm.long_term_assets is not None:
            lines.append(f"Long-term Assets: ${fm.long_term_assets/1e9:.2f}B")
        if fm.total_liabilities is not None:
            lines.append(f"Total Liabilities: ${fm.total_liabilities/1e9:.2f}B")
        if fm.current_liabilities is not None:
            lines.append(f"Current Liabilities: ${fm.current_liabilities/1e9:.2f}B")
        if fm.long_term_liabilities is not None:
            lines.append(f"Long-term Liabilities: ${fm.long_term_liabilities/1e9:.2f}B")
        if fm.long_term_debt is not None:
            lines.append(f"Long-term Debt: ${fm.long_term_debt/1e9:.2f}B")
        if fm.stockholders_equity is not None:
            lines.append(f"Stockholders Equity: ${fm.stockholders_equity/1e9:.2f}B")
        
        # Cash Flow
        if fm.operating_cash_flow is not None:
            lines.append(f"Operating Cash Flow: ${fm.operating_cash_flow/1e9:.2f}B")
        if fm.investing_cash_flow is not None:
            lines.append(f"Investing Cash Flow: ${fm.investing_cash_flow/1e9:.2f}B")
        if fm.financing_cash_flow is not None:
            lines.append(f"Financing Cash Flow: ${fm.financing_cash_flow/1e9:.2f}B")
        
        # Ratios
        lines.append("")
        lines.append("Financial Ratios:")
        
        if fm.profit_margin is not None:
            lines.append(f"Net Profit Margin: {fm.profit_margin:.2f}%")
        if fm.roa is not None:
            lines.append(f"Return on Assets (ROA): {fm.roa:.2f}%")
        if fm.debt_to_equity is not None:
            lines.append(f"Debt-to-Equity Ratio: {fm.debt_to_equity:.2f}")
        if fm.asset_turnover is not None:
            lines.append(f"Asset Turnover Ratio: {fm.asset_turnover:.2f}")
        
        return "\n".join(lines)


def sync_extraction_to_databases(
    csv_path: str,
    db_manager: DatabaseManager,
    vector_db: Optional[ChromaVectorDB] = None
) -> tuple:
    """
    Complete data pipeline: CSV → Relational DB → Vector DB
    
    Args:
        csv_path: Path to extracted financial CSV
        db_manager: Relational database manager
        vector_db: Vector database (optional)
        
    Returns:
        Tuple of (relational_count, vector_count)
    """
    from loaders import FinancialDataLoader
    
    logger.info("Starting complete data sync pipeline...")
    
    # 1. Load to relational database
    logger.info("Step 1: Loading CSV to relational database...")
    loader = FinancialDataLoader(db_manager)
    relational_count = loader.load_from_csv(csv_path)
    
    # 2. Sync to vector database
    vector_count = 0
    if vector_db:
        logger.info("Step 2: Syncing to vector database...")
        synchronizer = VectorSynchronizer(db_manager, vector_db)
        vector_count = synchronizer.sync_to_vector_db()
        vector_db.persist()
    
    logger.info(f"✅ Sync complete: {relational_count} relational, {vector_count} vector docs")
    return relational_count, vector_count


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Example: Initialize both databases and sync
    from schemas import DatabaseFactory
    
    # Create relational DB
    db = DatabaseFactory.create_sqlite()
    db.create_tables()
    
    # Create vector DB
    vector_db = ChromaVectorDB(persist_dir=None)  # In-memory for demo
    
    # Sync data
    csv_path = Path(__file__).parent.parent / 'data' / 'financial_data_raw.csv'
    if csv_path.exists():
        sync_extraction_to_databases(str(csv_path), db, vector_db)
    else:
        print(f"CSV not found: {csv_path}")
