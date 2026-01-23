"""
Data Integration Configuration
Centralized settings for extraction, analysis, and database operations
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DB_DIR = BASE_DIR / 'db'

# Create data directory if not exists
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# EXTRACTION CONFIGURATION
# ============================================================================

EXTRACTION_CONFIG = {
    'SEC_IDENTITY': os.getenv('SEC_IDENTITY', 'YOUR_NAME your.email@example.com'),
    'DEFAULT_YEARS': 3,
    'OUTPUT_CSV': str(DATA_DIR / 'financial_data_raw.csv'),
    'XBRL_CONCEPTS': {
        'revenue': ['us-gaap_Revenues', 'us-gaap_SalesRevenueNet'],
        'net_income': ['us-gaap_NetIncomeLoss'],
        'total_assets': ['us-gaap_Assets'],
        'total_liabilities': ['us-gaap_Liabilities'],
        'operating_cash_flow': ['us-gaap_NetCashProvidedByUsedInOperatingActivities'],
        'stockholders_equity': ['us-gaap_StockholdersEquity'],
        'long_term_debt': ['us-gaap_LongTermDebt'],
        'current_assets': ['us-gaap_CurrentAssets'],
        'current_liabilities': ['us-gaap_CurrentLiabilities'],
        'gross_profit': ['us-gaap_GrossProfit'],
        'operating_income': ['us-gaap_OperatingIncomeLoss'],
    },
    'FALLBACK_LABELS': True,  # Use label-based search if XBRL concept not found
    'LOG_FILE': str(BASE_DIR / 'extraction.log'),
}

# Default companies (for demonstration)
DEFAULT_COMPANIES = [
    ('MSFT', 'Microsoft'),
    ('AAPL', 'Apple'),
    ('TSLA', 'Tesla'),
    ('GOOGL', 'Alphabet'),
    ('AMZN', 'Amazon'),
]

# ============================================================================
# ANALYSIS CONFIGURATION
# ============================================================================

ANALYSIS_CONFIG = {
    'INPUT_CSV': str(DATA_DIR / 'financial_data_raw.csv'),
    'OUTPUT_DIR': str(DATA_DIR / 'analysis'),
    'VISUALIZATIONS': {
        'revenue_trends': True,
        'profit_margin_trends': True,
        'yoy_growth': True,
        'financial_ratios': True,
    },
    'METRICS': {
        'income_statement': [
            'Total Revenue',
            'Net Income',
            'Gross Profit',
            'Operating Income',
        ],
        'balance_sheet': [
            'Total Assets',
            'Total Liabilities',
            'Stockholders Equity',
            'Long Term Debt',
        ],
        'cash_flow': [
            'Operating Cash Flow',
        ],
        'ratios': [
            'Profit Margin',
            'ROA',
            'Debt-to-Equity',
            'Asset Turnover',
            'OCF-to-Liabilities',
        ],
    },
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Database selection: 'sqlite' or 'postgresql'
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')

DATABASE_CONFIG = {
    'sqlite': {
        'type': 'sqlite',
        'path': str(DATA_DIR / 'financial.db'),
        'url': f"sqlite:///{DATA_DIR / 'financial.db'}",
    },
    'postgresql': {
        'type': 'postgresql',
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'financial_data'),
        'url': f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{int(os.getenv('DB_PORT', 5432))}/{os.getenv('DB_NAME', 'financial_data')}",
    }
}

# Get active database config
ACTIVE_DB_CONFIG = DATABASE_CONFIG[DATABASE_TYPE]
DATABASE_URL = ACTIVE_DB_CONFIG['url']

# ============================================================================
# VECTOR DATABASE CONFIGURATION
# ============================================================================

VECTOR_DB_CONFIG = {
    'type': 'chroma',
    'persist_dir': str(DATA_DIR / 'chroma'),
    'collection_name': 'financial_documents',
    'embedding_model': 'all-MiniLM-L6-v2',  # Sentence-Transformers model
    'similarity_metric': 'cosine',
    'batch_size': 100,
}

# Create persist directory
Path(VECTOR_DB_CONFIG['persist_dir']).mkdir(exist_ok=True)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(BASE_DIR / 'data_integration.log'),
        },
    },
    'loggers': {
        'data_integration': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
        },
        'sqlalchemy': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'chromadb': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
    },
}

# ============================================================================
# DERIVED METRICS CALCULATION
# ============================================================================

DERIVED_METRICS = {
    'profit_margin': {
        'formula': '(net_income / total_revenue) * 100',
        'unit': '%',
        'description': 'Percentage of revenue that becomes net profit',
    },
    'roa': {
        'formula': '(net_income / total_assets) * 100',
        'unit': '%',
        'description': 'Return on assets - profit per dollar of assets',
    },
    'debt_to_equity': {
        'formula': 'total_liabilities / stockholders_equity',
        'unit': 'ratio',
        'description': 'Leverage ratio - debt relative to equity',
    },
    'debt_to_assets': {
        'formula': 'total_liabilities / total_assets',
        'unit': '%',
        'description': 'Percentage of assets financed by debt',
    },
    'asset_turnover': {
        'formula': 'total_revenue / total_assets',
        'unit': 'ratio',
        'description': 'Revenue generation efficiency per dollar of assets',
    },
    'ocf_to_liabilities': {
        'formula': 'operating_cash_flow / total_liabilities',
        'unit': 'ratio',
        'description': 'Operating cash coverage of liabilities',
    },
}

# ============================================================================
# FEATURE FLAGS
# ============================================================================

FEATURES = {
    'ENABLE_EXTRACTION': True,
    'ENABLE_ANALYSIS': True,
    'ENABLE_RELATIONAL_DB': True,
    'ENABLE_VECTOR_DB': True,
    'ENABLE_SYNCHRONIZATION': True,
    'AUTO_CALCULATE_RATIOS': True,
    'SKIP_DUPLICATE_RECORDS': True,
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_database_url(db_type=None):
    """Get database URL for specified type"""
    db_type = db_type or DATABASE_TYPE
    return DATABASE_CONFIG[db_type]['url']


def get_extraction_config():
    """Get extraction configuration"""
    return EXTRACTION_CONFIG


def get_analysis_config():
    """Get analysis configuration"""
    return ANALYSIS_CONFIG


def validate_configuration():
    """Validate configuration"""
    print("Validating configuration...")
    print(f"  Database type: {DATABASE_TYPE}")
    print(f"  Database URL: {DATABASE_URL}")
    print(f"  Vector DB: {VECTOR_DB_CONFIG['persist_dir']}")
    print(f"  Data directory: {DATA_DIR}")
    print("✅ Configuration valid")


if __name__ == '__main__':
    validate_configuration()

