"""
Database initialization and management utilities.
Provides commands to initialize, reset, and validate databases.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from ..schemas.models import Base, Company, FinancialMetric
    from .loaders import FinancialDataLoader, DataSynchronizer
except ImportError:
    from schemas.models import Base, Company, FinancialMetric
    from loaders import FinancialDataLoader, DataSynchronizer

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Simple database manager for connections"""
    
    def __init__(self, db_url: str):
        """Initialize database manager"""
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized: {db_url}")
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        logger.info("All tables created")
    
    def drop_tables(self):
        """Drop all tables"""
        Base.metadata.drop_all(self.engine)
        logger.info("All tables dropped")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close connections"""
        self.engine.dispose()


class DatabaseFactory:
    """Factory for creating database managers"""
    
    @staticmethod
    def create_sqlite(db_path: Optional[str] = None) -> DatabaseManager:
        """Create SQLite database"""
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / 'data' / 'financial.db')
        db_url = f"sqlite:///{db_path}"
        return DatabaseManager(db_url)
    
    @staticmethod
    def create_postgresql(
        host: str,
        port: int,
        user: str,
        password: str,
        database: str
    ) -> DatabaseManager:
        """Create PostgreSQL database"""
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return DatabaseManager(db_url)


class DatabaseInitializer:
    """Initialize and manage databases"""
    
    @staticmethod
    def init_sqlite(db_path: Optional[str] = None) -> DatabaseManager:
        """
        Initialize SQLite database for development.
        
        Args:
            db_path: Optional path to database file. If None, uses default location.
            
        Returns:
            DatabaseManager instance
        """
        db = DatabaseFactory.create_sqlite(db_path)
        db.create_tables()
        logger.info("SQLite database initialized")
        return db
    
    @staticmethod
    def init_postgresql(
        host: str,
        port: int = 5432,
        user: str = 'postgres',
        password: str = '',
        database: str = 'financial_data'
    ) -> DatabaseManager:
        """
        Initialize PostgreSQL database for production.
        
        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            
        Returns:
            DatabaseManager instance
        """
        try:
            db = DatabaseFactory.create_postgresql(host, port, user, password, database)
            db.create_tables()
            logger.info(f"PostgreSQL database initialized: {database}@{host}:{port}")
            return db
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    @staticmethod
    def reset_database(db: DatabaseManager, confirm: bool = True):
        """
        Reset database (drop and recreate all tables).
        
        Args:
            db: DatabaseManager instance
            confirm: Require user confirmation before dropping
        """
        if confirm:
            response = input("⚠️  WARNING: This will delete all data. Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                logger.info("Reset cancelled")
                return
        
        db.drop_tables()
        db.create_tables()
        logger.info("Database reset complete")
    
    @staticmethod
    def validate_database(db: DatabaseManager) -> bool:
        """
        Validate database connectivity and schema.
        
        Args:
            db: DatabaseManager instance
            
        Returns:
            True if database is valid, False otherwise
        """
        try:
            session = db.get_session()
            # Simple validation query
            session.query(Company).count()
            session.close()
            logger.info("Database validation passed")
            return True
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False


class DataInitializer:
    """Initialize data in databases"""
    
    @staticmethod
    def load_extracted_data(
        db: DatabaseManager,
        csv_path: str,
        vector_db=None
    ) -> tuple:
        """
        Load extracted financial data from CSV into databases.
        
        Args:
            db: DatabaseManager instance (relational)
            csv_path: Path to extracted financial CSV
            vector_db: Optional vector database for semantic search
            
        Returns:
            Tuple of (relational_count, vector_count)
        """
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return 0, 0
        
        if vector_db:
            synchronizer = DataSynchronizer(db, vector_db)
            return synchronizer.sync_csv_to_databases(str(csv_path))
        else:
            loader = FinancialDataLoader(db)
            count = loader.load_from_csv(str(csv_path))
            return count, 0


class DatabaseCLI:
    """Command-line interface for database operations"""
    
    @staticmethod
    def run():
        """Run interactive CLI"""
        print("\n" + "="*70)
        print("FINANCIAL DATA DATABASE INITIALIZATION")
        print("="*70)
        
        while True:
            print("\nOptions:")
            print("  1. Initialize SQLite (development)")
            print("  2. Initialize PostgreSQL (production)")
            print("  3. Load financial data from CSV")
            print("  4. Reset database")
            print("  5. Validate database")
            print("  6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                try:
                    db = DatabaseInitializer.init_sqlite()
                    print("✅ SQLite database initialized")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif choice == '2':
                host = input("Database host (default: localhost): ").strip() or 'localhost'
                port = int(input("Database port (default: 5432): ").strip() or '5432')
                user = input("Database user (default: postgres): ").strip() or 'postgres'
                password = input("Database password: ").strip()
                db_name = input("Database name (default: financial_data): ").strip() or 'financial_data'
                
                try:
                    db = DatabaseInitializer.init_postgresql(host, port, user, password, db_name)
                    print("✅ PostgreSQL database initialized")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif choice == '3':
                csv_path = input("Path to CSV file: ").strip()
                db_type = input("Database type (sqlite/postgresql): ").strip().lower()
                
                try:
                    if db_type == 'sqlite':
                        db = DatabaseFactory.create_sqlite()
                    else:
                        print("PostgreSQL requires additional parameters")
                        continue
                    
                    count, _ = DataInitializer.load_extracted_data(db, csv_path)
                    print(f"✅ Loaded {count} financial records")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif choice == '4':
                db_type = input("Database type (sqlite/postgresql): ").strip().lower()
                
                try:
                    if db_type == 'sqlite':
                        db = DatabaseFactory.create_sqlite()
                    else:
                        print("PostgreSQL requires additional parameters")
                        continue
                    
                    DatabaseInitializer.reset_database(db, confirm=True)
                    print("✅ Database reset complete")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif choice == '5':
                db_type = input("Database type (sqlite/postgresql): ").strip().lower()
                
                try:
                    if db_type == 'sqlite':
                        db = DatabaseFactory.create_sqlite()
                    else:
                        print("PostgreSQL requires additional parameters")
                        continue
                    
                    if DatabaseInitializer.validate_database(db):
                        print("✅ Database validation passed")
                    else:
                        print("❌ Database validation failed")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif choice == '6':
                print("Exiting...")
                break
            
            else:
                print("❌ Invalid option")


def init_dev_environment():
    """Quick initialization for development"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Initializing development environment...")
    
    # Initialize SQLite
    db = DatabaseInitializer.init_sqlite()
    
    # Validate
    if DatabaseInitializer.validate_database(db):
        logger.info("✅ Development environment ready")
        return db
    else:
        logger.error("❌ Failed to initialize development environment")
        return None


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init-dev':
            init_dev_environment()
        elif command == 'cli':
            DatabaseCLI.run()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init-dev, cli")
    else:
        # Run CLI by default
        DatabaseCLI.run()
