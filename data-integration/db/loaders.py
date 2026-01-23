"""
Data loaders for ingesting financial data into relational and vector databases.
Handles CSV → SQLite/PostgreSQL and data → Chroma vector embeddings.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

try:
    from schemas.models import Company, FinancialMetric
    from db.init_db import DatabaseManager
except ImportError:
    from ..schemas.models import Company, FinancialMetric
    from ..db.init_db import DatabaseManager

try:
    from schemas.models import FinancialRatio
except ImportError:
    from ..schemas.models import FinancialRatio

logger = logging.getLogger(__name__)



class FinancialDataLoader:
    """Load extracted financial data from CSV into relational database"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize loader.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def load_from_csv(self, csv_path: str, skip_duplicates: bool = True) -> int:
        """
        Load financial data from CSV file.
        
        Args:
            csv_path: Path to CSV file with extracted financial data
            skip_duplicates: Skip records that already exist in database
            
        Returns:
            Number of records inserted
        """
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return 0
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV with {len(df)} rows from {csv_path}")
            
            # Validate required columns
            required_cols = ['Company', 'Ticker', 'Fiscal Year']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return 0
            
            inserted = 0
            for _, row in df.iterrows():
                try:
                    if self._insert_record(row, skip_duplicates):
                        inserted += 1
                except Exception as e:
                    logger.warning(f"Skipped row due to error: {e}")
                    continue
            
            logger.info(f"Loaded {inserted} financial records into database")
            return inserted
        
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return 0
    
    def _insert_record(self, row: pd.Series, skip_duplicates: bool = True) -> bool:
        """Insert a single financial record"""
        session = self.db.get_session()
        try:
            ticker = row['Ticker'].strip()
            company_name = row['Company'].strip()
            fiscal_year_str = str(row['Fiscal Year'])
            
            # Convert to datetime - handle different formats
            try:
                fiscal_year = pd.to_datetime(fiscal_year_str)
            except:
                # If it's just a year, make it end of that year
                fiscal_year = pd.to_datetime(f"{int(float(fiscal_year_str))}-12-31")
            
            # Insert or get company
            company = session.query(Company).filter_by(ticker=ticker).first()
            if not company:
                company = Company(ticker=ticker, name=company_name)
                session.add(company)
                session.flush()
            
            # Check if record already exists
            existing = session.query(FinancialMetric).filter_by(
                company_id=company.id,
                fiscal_year_end=fiscal_year
            ).first()
            
            if existing and skip_duplicates:
                logger.debug(f"Skipped duplicate: {ticker} {fiscal_year.year}")
                return False
            
            # Prepare metrics dictionary
            metrics = {}
            for col in row.index:
                if col not in ['Company', 'Ticker', 'Fiscal Year']:
                    value = row[col]
                    if pd.notna(value):
                        # Convert column name to snake_case for database
                        db_col = col.lower().replace(' ', '_')
                        try:
                            metrics[db_col] = float(value)
                        except:
                            pass
            
            # Calculate derived metrics if raw data available
            if 'total_revenue' in metrics and 'net_income' in metrics:
                if metrics['total_revenue'] != 0:
                    metrics['profit_margin'] = (metrics['net_income'] / metrics['total_revenue'] * 100)
            
            if 'total_assets' in metrics and 'net_income' in metrics:
                if metrics['total_assets'] != 0:
                    metrics['roa'] = (metrics['net_income'] / metrics['total_assets'] * 100)
            
            if 'total_assets' in metrics and 'total_liabilities' in metrics:
                equity = metrics['total_assets'] - metrics['total_liabilities']
                if equity > 0:
                    metrics['debt_to_equity'] = metrics['total_liabilities'] / equity
                if metrics['total_assets'] > 0:
                    metrics['debt_to_assets'] = metrics['total_liabilities'] / metrics['total_assets']
            
            if 'total_revenue' in metrics and 'total_assets' in metrics:
                if metrics['total_assets'] > 0:
                    metrics['asset_turnover'] = metrics['total_revenue'] / metrics['total_assets']
            
            if 'operating_cash_flow' in metrics and 'total_liabilities' in metrics:
                if metrics['total_liabilities'] > 0:
                    metrics['ocf_to_liabilities'] = metrics['operating_cash_flow'] / metrics['total_liabilities']
            
            # Insert or update financial metrics
            fm = existing if existing else FinancialMetric(
                company_id=company.id,
                fiscal_year=fiscal_year.year,
                fiscal_year_end=fiscal_year
            )
            
            for key, value in metrics.items():
                if hasattr(fm, key):
                    setattr(fm, key, value)
            
            session.add(fm)
            session.commit()
            
            logger.debug(f"Inserted: {ticker} {fiscal_year.year}")
            return True
        
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def load_batch(self, csv_files: List[str]) -> int:
        """Load multiple CSV files"""
        total_inserted = 0
        for csv_file in csv_files:
            total_inserted += self.load_from_csv(csv_file)
        return total_inserted


class FinancialRatioLoader:
    """Load calculated financial ratios into database"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize ratio loader.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def load_from_csv(self, csv_path: str, ratio_type: str = 'ratios') -> int:
        """
        Load financial ratios from CSV file.
        
        Args:
            csv_path: Path to analysis CSV file
            ratio_type: Type of analysis ('yoy', 'margins', 'ratios', etc.)
            
        Returns:
            Number of records inserted
        """
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return 0
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {ratio_type} CSV with {len(df)} rows from {csv_path}")
            
            inserted = 0
            for _, row in df.iterrows():
                try:
                    if self._insert_ratio_record(row, ratio_type):
                        inserted += 1
                except Exception as e:
                    logger.warning(f"Skipped row due to error: {e}")
                    continue
            
            logger.info(f"Loaded {inserted} {ratio_type} records into database")
            return inserted
        
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return 0
    
    def _insert_ratio_record(self, row: pd.Series, ratio_type: str) -> bool:
        """Insert a single financial ratio record"""
        session = self.db.get_session()
        try:
            ticker = row.get('Ticker', row.get('ticker'))
            if ticker:
                ticker = ticker.strip()
            
            company_name = row.get('Company', row.get('company'))
            if company_name:
                company_name = company_name.strip()
            
            fiscal_year_str = str(row.get('Fiscal Year', row.get('fiscal_year', row.get('fiscal year'))))
            
            # Convert to datetime - handle different formats
            try:
                fiscal_year = pd.to_datetime(fiscal_year_str)
            except:
                # If it's just a year, make it end of that year
                try:
                    fiscal_year = pd.to_datetime(f"{int(float(fiscal_year_str))}-12-31")
                except:
                    logger.warning(f"Could not parse fiscal year: {fiscal_year_str}")
                    return False
            
            # Get company
            company = session.query(Company).filter_by(ticker=ticker).first()
            if not company:
                logger.warning(f"Company not found for ticker: {ticker}")
                return False
            
            # Check if ratio record already exists for this company and year
            existing = session.query(FinancialRatio).filter_by(
                company_id=company.id,
                fiscal_year=fiscal_year.year
            ).first()
            
            if existing:
                logger.debug(f"Updating existing ratio record for {ticker} {fiscal_year.year}")
                ratio_obj = existing
            else:
                ratio_obj = FinancialRatio(
                    company_id=company.id,
                    fiscal_year=fiscal_year.year
                )
            
            # Map columns based on ratio type
            ratio_obj.calculation_method = ratio_type
            
            # Map common ratio columns
            column_mapping = {
                'Current Ratio': 'current_ratio',
                'Debt-to-Equity': 'debt_to_equity',
                'Debt-to-Assets': 'debt_to_assets',
                'LT-Debt-to-Equity': 'lt_debt_to_equity',
                'Gross Margin (%)': 'gross_margin',
                'Operating Margin (%)': 'operating_margin',
                'Net Margin (%)': 'net_profit_margin',
                'Net Profit Margin %': 'net_profit_margin',
                'ROA (%)': 'roa',
                'ROE (%)': 'roe',
                'Asset Turnover': 'asset_turnover',
                'OCF-to-Liabilities': 'ocf_to_liabilities',
                'OCF Margin (%)': 'ocf_margin',
                'Free Cash Flow ($M)': 'free_cash_flow',
                'Revenue YoY %': 'revenue_growth_yoy',
                'Net Income YoY %': 'income_growth_yoy',
                'Gross Profit Margin %': 'gross_margin',
                'Operating Profit Margin %': 'operating_margin',
            }
            
            for csv_col, db_col in column_mapping.items():
                if csv_col in row and pd.notna(row[csv_col]):
                    try:
                        value = float(row[csv_col])
                        setattr(ratio_obj, db_col, value)
                    except (ValueError, TypeError):
                        pass
            
            session.add(ratio_obj)
            session.commit()
            
            logger.debug(f"Inserted {ratio_type} for {ticker} {fiscal_year.year}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting ratio record: {e}")
            raise
        finally:
            session.close()


class VectorDataLoader:
    """Load financial data into vector database for semantic search"""
    
    def __init__(self, vector_db=None):
        """
        Initialize vector loader.
        
        Args:
            vector_db: Chroma or compatible vector database instance
        """
        self.vector_db = vector_db
    
    def load_from_database(self, db_manager: DatabaseManager, collection_name: str = 'financial_docs'):
        """
        Load financial data from relational DB into vector DB.
        Creates embeddings and stores financial documents.
        
        Args:
            db_manager: DatabaseManager instance
            collection_name: Chroma collection name
        """
        if self.vector_db is None:
            logger.warning("Vector DB not configured")
            return 0
        
        try:
            session = db_manager.get_session()
            
            # Query all companies and their financials
            companies = session.query(Company).all()
            
            documents = []
            ids = []
            metadatas = []
            
            for company in companies:
                financials = session.query(FinancialMetric).filter_by(company_id=company.id).all()
                
                for fm in financials:
                    # Create document text from financial data
                    doc_text = self._create_financial_document(company, fm)
                    
                    # Generate unique ID
                    doc_id = f"{company.ticker}_{fm.fiscal_year.year}"
                    
                    # Metadata for filtering
                    metadata = {
                        'ticker': company.ticker,
                        'company_name': company.name,
                        'fiscal_year': fm.fiscal_year.isoformat(),
                        'year': str(fm.fiscal_year.year),
                    }
                    
                    documents.append(doc_text)
                    ids.append(doc_id)
                    metadatas.append(metadata)
            
            # Add to vector database
            if documents:
                self.vector_db.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                logger.info(f"Loaded {len(documents)} documents into vector DB")
                return len(documents)
            
            return 0
        
        except Exception as e:
            logger.error(f"Failed to load into vector DB: {e}")
            return 0
        finally:
            session.close()
    
    def _create_financial_document(self, company: Company, fm: FinancialMetric) -> str:
        """Create human-readable financial document text"""
        lines = [
            f"Company: {company.name} ({company.ticker})",
            f"Fiscal Year: {fm.fiscal_year.year}",
            ""
        ]
        
        # Add available metrics
        metrics = [
            ('Total Revenue', fm.total_revenue),
            ('Net Income', fm.net_income),
            ('Gross Profit', fm.gross_profit),
            ('Operating Income', fm.operating_income),
            ('Total Assets', fm.total_assets),
            ('Total Liabilities', fm.total_liabilities),
            ('Stockholders Equity', fm.stockholders_equity),
            ('Operating Cash Flow', fm.operating_cash_flow),
            ('Profit Margin', fm.profit_margin),
            ('Return on Assets', fm.roa),
            ('Debt-to-Equity', fm.debt_to_equity),
            ('Asset Turnover', fm.asset_turnover),
        ]
        
        for metric_name, value in metrics:
            if value is not None:
                if isinstance(value, float):
                    lines.append(f"{metric_name}: {value:,.2f}")
                else:
                    lines.append(f"{metric_name}: {value}")
        
        return "\n".join(lines)


class DataSynchronizer:
    """Synchronize between relational and vector databases"""
    
    def __init__(self, db_manager: DatabaseManager, vector_db=None):
        """
        Initialize synchronizer.
        
        Args:
            db_manager: Relational database manager
            vector_db: Vector database instance (Chroma)
        """
        self.db = db_manager
        self.vector_db = vector_db
        self.relational_loader = FinancialDataLoader(db_manager)
        self.vector_loader = VectorDataLoader(vector_db)
    
    def sync_csv_to_databases(self, csv_path: str):
        """
        Complete sync: CSV → Relational DB → Vector DB
        
        Args:
            csv_path: Path to extracted financial data CSV
        """
        logger.info("Starting data synchronization...")
        
        # 1. Load into relational database
        logger.info("Step 1: Loading into relational database...")
        relational_count = self.relational_loader.load_from_csv(csv_path)
        
        # 2. Sync to vector database
        if self.vector_db:
            logger.info("Step 2: Synchronizing to vector database...")
            vector_count = self.vector_loader.load_from_database(self.db)
        else:
            logger.warning("Vector DB not configured, skipping vector sync")
            vector_count = 0
        
        logger.info(f"Sync complete: {relational_count} relational records, {vector_count} vector documents")
        return relational_count, vector_count


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create database manager
    from schemas import DatabaseFactory
    db = DatabaseFactory.create_sqlite()
    db.create_tables()
    
    # Load from CSV
    loader = FinancialDataLoader(db)
    csv_path = Path(__file__).parent.parent / 'data' / 'financial_data_raw.csv'
    count = loader.load_from_csv(str(csv_path))
    
    print(f"Loaded {count} records successfully!")
