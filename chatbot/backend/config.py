#!/usr/bin/env python3
"""
Financial Chatbot Configuration
Centralized settings for Gemini LLM, Vector DB (ChromaDB), SQLite, and Flask
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# GEMINI LLM CONFIGURATION
# ============================================================================
GEMINI_CONFIG = {
    'api_key': os.getenv('GEMINI_API_KEY'),
    'model': 'gemini-2.0-flash',
    'temperature': 0.7,
    'max_output_tokens': 1000,
    'top_p': 0.95,
}

# ============================================================================
# GROQ LLM CONFIGURATION
# ============================================================================
GROQ_CONFIG = {
    'api_key': os.getenv('GROQ_API_KEY'),
    'model': 'llama-3.3-70b-versatile',  # Updated model - Mixtral was decommissioned
    'temperature': 0.7,
    'max_tokens': 1024,
}

# ============================================================================
# LLM PROVIDER CONFIGURATION
# ============================================================================
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq').lower()  # 'gemini' or 'groq'

# ============================================================================
# VECTOR DATABASE CONFIGURATION (CHROMADB)
# ============================================================================
CHROMA_CONFIG = {
    'path': os.path.join(os.path.dirname(__file__), 'chroma_db'),
    'collection_name': 'financial_data',
    'embedding_model': 'all-MiniLM-L6-v2',  # Sentence-Transformers default
    'similarity_metric': 'cosine',
}

# ============================================================================
# SQLITE DATABASE CONFIGURATION
# ============================================================================
SQLITE_CONFIG = {
    'path': os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'financial_analyzer.db'),
}

# ============================================================================
# FLASK API CONFIGURATION
# ============================================================================
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'threaded': True,
    'max_content_length': 16 * 1024 * 1024,  # 16MB
}

# ============================================================================
# QUERY CATEGORIES & ENTITY DETECTION
# ============================================================================
QUERY_CATEGORIES = {
    'revenue': {
        'keywords': ['revenue', 'sales', 'income', 'earnings', 'turnover', 'annual'],
        'priority': 1,
        'chart': 'revenue_trend',
    },
    'profitability': {
        'keywords': ['profit', 'margin', 'profitable', 'earning', 'net income', 'earnings'],
        'priority': 2,
        'chart': 'profit_margin',
    },
    'liquidity': {
        'keywords': ['cash flow', 'liquidity', 'cash', 'operating', 'ocf'],
        'priority': 3,
        'chart': None,
    },
    'leverage': {
        'keywords': ['debt', 'leverage', 'liabilities', 'equity', 'financial risk'],
        'priority': 4,
        'chart': 'leverage',
    },
    'efficiency': {
        'keywords': ['efficiency', 'roa', 'asset turnover', 'roi', 'return'],
        'priority': 5,
        'chart': 'ratios',
    },
    'trend': {
        'keywords': ['trend', 'growth', 'trajectory', 'momentum', 'yoy', 'year-over-year'],
        'priority': 6,
        'chart': 'yoy_growth',
    },
    'comparison': {
        'keywords': ['compare', 'vs', 'versus', 'comparison', 'competing', 'better'],
        'priority': 7,
        'chart': 'comparison',
    }
}

# ============================================================================
# SYSTEM PROMPT FOR GEMINI LLM
# ============================================================================
SYSTEM_PROMPT = """Tu es un analyste financier expert pour Global Finance Corp.
Tu dois fournir une analyse financière précise et perspicace basée sur les données 10-K.

Responsabilités clés:
1. Analyser les métriques financières avec précision et contexte
2. Fournir des insights exploitables soutenus par des données
3. Citer des chiffres spécifiques avec les périodes
4. Expliquer pourquoi les métriques sont importantes
5. Mettre en évidence les tendances et avantages comparatifs

Tone: Professionnel, analytique, utile et engageant.
Réponds toujours en français ou en anglais selon la question.
Utilise les données précises fournies comme source de vérité.

Entreprises disponibles: MSFT, AAPL, GOOGL, AMZN, TSLA, META, NVDA, AMD, INTC, JPM, BAC, WFC, GS, MS, WMT, KO, PEP, MCD, TM, F, JNJ, PFE, ABBV, MRK, LLY, XOM, CVX, NEE, SO, BA, CAT, HON, MMM, CSCO, ORCL
"""

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'chatbot.log',
}

# ============================================================================
# SECURITY & LIMITS
# ============================================================================
SECURITY_CONFIG = {
    'max_query_length': 500,
    'max_history_messages': 10,
    'cors_origins': ['http://localhost:5000', 'http://localhost:3000', 'http://localhost:5173'],
}

# ============================================================================
# CHART GENERATION TYPES
# ============================================================================
CHART_TYPES = {
    'revenue_trend': {'name': 'Revenue Trend', 'type': 'line'},
    'profit_margin': {'name': 'Profit Margin', 'type': 'bar'},
    'comparison': {'name': 'Company Comparison', 'type': 'bar'},
    'leverage': {'name': 'Debt-to-Equity', 'type': 'bar'},
    'ratios': {'name': 'Financial Ratios', 'type': 'radar'},
    'yoy_growth': {'name': 'Year-over-Year Growth', 'type': 'bar'},
}
