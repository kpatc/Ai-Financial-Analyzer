#!/usr/bin/env python3
"""
Company name mappings - Ticker to full company names
"""

TICKER_TO_NAME = {
    'MSFT': 'Microsoft',
    'AAPL': 'Apple',
    'GOOGL': 'Google',
    'AMZN': 'Amazon',
    'TSLA': 'Tesla',
    'META': 'Meta',
    'NVDA': 'NVIDIA',
    'AMD': 'AMD',
    'INTC': 'Intel',
    'JPM': 'JPMorgan',
    'BAC': 'Bank of America',
    'WFC': 'Wells Fargo',
    'GS': 'Goldman Sachs',
    'MS': 'Morgan Stanley',
    'WMT': 'Walmart',
    'KO': 'Coca-Cola',
    'PEP': 'PepsiCo',
    'MCD': "McDonald's",
    'TM': 'Toyota',
    'F': 'Ford',
    'JNJ': 'Johnson & Johnson',
    'PFE': 'Pfizer',
    'ABBV': 'AbbVie',
    'MRK': 'Merck',
    'LLY': 'Eli Lilly',
    'XOM': 'Exxon Mobil',
    'CVX': 'Chevron',
    'NEE': 'NextEra Energy',
    'SO': 'Southern Company',
    'BA': 'Boeing',
    'CAT': 'Caterpillar',
    'HON': 'Honeywell',
    'MMM': '3M',
    'CSCO': 'Cisco',
    'ORCL': 'Oracle',
}

def get_company_name(ticker: str) -> str:
    """Get full company name from ticker"""
    return TICKER_TO_NAME.get(ticker.upper(), ticker)

def get_ticker(name: str) -> str:
    """Get ticker from company name (case-insensitive)"""
    name_lower = name.lower()
    for ticker, company_name in TICKER_TO_NAME.items():
        if company_name.lower() == name_lower:
            return ticker
    return name.upper()
