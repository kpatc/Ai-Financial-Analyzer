#!/usr/bin/env python3
"""
Financial Chatbot Configuration
Centralized settings for NLP, Vector DB, Flask, and LLM
"""

# ============================================================================
# NLP & EMBEDDINGS CONFIGURATION
# ============================================================================
NLP_CONFIG = {
    'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
    'embedding_dimension': 384,
    'similarity_threshold': 0.3,
    'device': 'cpu',  # Use 'cuda' for GPU acceleration
    'batch_size': 32
}

# ============================================================================
# VECTOR DATABASE CONFIGURATION
# ============================================================================
CHROMA_CONFIG = {
    'path': './chroma_db',
    'collection_name': 'financial_documents',
    'metadata_filter': True,
    'similarity_metric': 'cosine'
}

# ============================================================================
# FLASK API CONFIGURATION
# ============================================================================
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'threaded': True,
    'max_content_length': 16 * 1024 * 1024  # 16MB max request size
}

# ============================================================================
# QUERY CATEGORIES & CLASSIFICATION
# ============================================================================
QUERY_CATEGORIES = {
    'revenue': {
        'keywords': ['revenue', 'sales', 'income', 'earnings', 'turnover'],
        'priority': 1
    },
    'profitability': {
        'keywords': ['profit', 'margin', 'profitable', 'earning power', 'net income'],
        'priority': 2
    },
    'liquidity': {
        'keywords': ['cash flow', 'liquidity', 'cash', 'operating cash', 'ocf'],
        'priority': 3
    },
    'leverage': {
        'keywords': ['debt', 'leverage', 'liabilities', 'financial risk', 'equity'],
        'priority': 4
    },
    'efficiency': {
        'keywords': ['efficiency', 'roa', 'asset turnover', 'roi', 'utilization'],
        'priority': 5
    },
    'trend': {
        'keywords': ['trend', 'growth', 'trajectory', 'momentum', 'yoy'],
        'priority': 6
    },
    'comparison': {
        'keywords': ['compare', 'vs', 'versus', 'comparison', 'competing'],
        'priority': 7
    }
}

# ============================================================================
# SYSTEM PROMPT & PERSONALITY
# ============================================================================
SYSTEM_PROMPT = """You are an expert financial analyst chatbot for Global Finance Corp.
Your role is to provide accurate, insightful financial analysis of companies based on 10-K filings.

Key responsibilities:
1. Analyze financial metrics with precision and context
2. Provide actionable insights backed by data
3. Suggest follow-up questions to encourage deeper exploration
4. Present information in clear, professional language
5. Highlight trends and comparative advantages

Tone: Professional, analytical, helpful, and engaging.
Always cite specific numbers and time periods.
Provide context for why metrics matter.
"""

# ============================================================================
# AVAILABLE COMPANIES & METRICS
# ============================================================================
COMPANIES = ['Microsoft', 'Apple']

METRICS = [
    'Total Revenue',
    'Net Income',
    'Total Assets',
    'Total Liabilities',
    'Operating Cash Flow',
    'Fiscal Year'
]

RATIOS = [
    'Net Profit Margin',
    'Debt-to-Equity',
    'Debt-to-Assets',
    'Return on Assets (ROA)',
    'Asset Turnover',
    'Operating Cash Flow to Liabilities'
]

# ============================================================================
# CHART CONFIGURATION
# ============================================================================
CHART_CONFIG = {
    'revenue_trend': {
        'type': 'line',
        'title': 'Revenue Trends',
        'ylabel': 'Revenue (Billions $)',
        'colors': ['#667eea', '#764ba2']
    },
    'profit_margin': {
        'type': 'bar',
        'title': 'Net Profit Margin Comparison',
        'ylabel': 'Margin (%)',
        'colors': ['#667eea', '#764ba2']
    },
    'comparison': {
        'type': 'bar',
        'title': 'Financial Metrics Comparison',
        'ylabel': 'Billions ($)',
        'colors': ['#667eea', '#764ba2']
    },
    'leverage': {
        'type': 'bar',
        'title': 'Debt-to-Equity Ratio',
        'ylabel': 'D/E Ratio',
        'colors': ['#667eea', '#764ba2']
    }
}

# ============================================================================
# LLM INTEGRATION (OPTIONAL - FOR FUTURE ENHANCEMENT)
# ============================================================================
LLM_CONFIG = {
    'provider': 'openai',  # 'openai', 'anthropic', 'local'
    'model': 'gpt-4',
    'api_key': None,  # Load from environment variable
    'temperature': 0.7,
    'max_tokens': 500,
    'system_prompt': SYSTEM_PROMPT
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'chatbot.log',
    'max_file_size': 10485760  # 10MB
}

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================
PERFORMANCE_CONFIG = {
    'cache_embeddings': True,
    'cache_ttl': 3600,  # 1 hour
    'batch_processing': True,
    'async_enabled': True,
    'max_workers': 4
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================
SECURITY_CONFIG = {
    'rate_limit': '100 per hour',
    'cors_origins': ['http://localhost:3000', 'http://localhost:8000'],
    'input_validation': True,
    'sanitize_output': True,
    'max_query_length': 500
}
