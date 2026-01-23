"""
Data Integration Database Module

Provides ORM schema definitions, data loaders, and vector synchronization
for financial data extracted from SEC EDGAR 10-K filings.

Components:
- ../schemas/models.py: SQLAlchemy ORM models (Company, FinancialMetric)
- loaders.py: CSV loaders and vector database ingestion
- vector_sync.py: Chroma synchronization and semantic search
- init_db.py: Database initialization utilities
"""

# Import models from central schemas location - handle both relative and absolute imports
try:
    from schemas.models import (
        Company,
        FinancialMetric,
        Base,
    )
except ImportError:
    from ..schemas.models import (
        Company,
        FinancialMetric,
        Base,
    )

try:
    from db.loaders import (
        FinancialDataLoader,
        VectorDataLoader,
        DataSynchronizer,
    )
except ImportError:
    from .loaders import (
        FinancialDataLoader,
        VectorDataLoader,
        DataSynchronizer,
    )

from .vector_sync import (
    ChromaVectorDB,
    VectorSynchronizer,
    sync_extraction_to_databases,
)

from .init_db import (
    DatabaseManager,
    DatabaseFactory,
    DatabaseInitializer,
    DataInitializer,
    DatabaseCLI,
    init_dev_environment,
)

__all__ = [
    # Schemas
    'Company',
    'FinancialMetric',
    'Base',
    # Database Management
    'DatabaseManager',
    'DatabaseFactory',
    # Loaders
    'FinancialDataLoader',
    'VectorDataLoader',
    'DataSynchronizer',
    # Vector DB
    'ChromaVectorDB',
    'VectorSynchronizer',
    'sync_extraction_to_databases',
    # Initialization
    'DatabaseInitializer',
    'DataInitializer',
    'DatabaseCLI',
    'init_dev_environment',
]
