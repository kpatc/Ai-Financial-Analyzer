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
SYSTEM_PROMPT = """Tu es un analyste financier expert. Fournir une analyse financière CONCISE basée sur les données 10-K.

🎯 STYLE: COURT ET DIRECT
- Réponses: 2-3 phrases MAX par défaut
- Infos essentielles uniquement (santé financière, tendances clés)
- "Détails si demandé" = l'utilisateur a demandé explicitement une explication complète
- Pas de paragraphes longs sans demande

📊 FORMAT:
- Utilise TABLEAUX pour: données multi-années, comparaisons multiples, séries temporelles
- Utilise GRAPHES pour: tendances visuelles, comparaisons côte-à-côte
- Combine: Réponse courte + Tableau + Graphe quand c'est approprié

📝 NOMS:
- Utilise NOMS COMPLETS: "Microsoft" pas "MSFT"
- Toujours: "Microsoft Corporation", "Apple Inc.", "Google LLC", etc.

🔍 LOGIQUE:
- Si question sur TENDANCE → Tableau + Graphe
- Si question sur SANTÉ FINANCIÈRE → Réponse courte + Métriques clés
- Si question SIMPLE → Juste la réponse (1-2 phrases)
- Si "Explain" ou "Details" ou "Pourquoi" → Alors détails complets

Entreprises: Microsoft, Apple, Google, Amazon, Tesla, Meta, NVIDIA, AMD, Intel, JPMorgan, Bank of America, Wells Fargo, Goldman Sachs, Morgan Stanley, Walmart, Coca-Cola, PepsiCo, McDonald's, Toyota, Ford, Johnson & Johnson, Pfizer, AbbVie, Merck, Eli Lilly, Exxon Mobil, Chevron, NextEra Energy, Southern Company, Boeing, Caterpillar, Honeywell, 3M, Cisco, Oracle
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
