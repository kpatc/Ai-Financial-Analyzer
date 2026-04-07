#!/usr/bin/env python3
"""
Smart response logic - determine when to use tables, charts, short responses
"""

import re
from typing import Tuple, List

def should_use_table(query: str, tickers: List[str], entities: dict) -> Tuple[bool, str]:
    """
    Determine if response should include a table

    Returns: (should_use_table, table_type)
    table_type: 'metrics', 'ratios', 'comparison', 'trends'
    """
    query_lower = query.lower()

    # Trends over time = TABLE + GRAPH
    if any(word in query_lower for word in ['trend', 'evolution', 'progression', 'historique', 'over time', 'past', 'history']):
        return True, 'trends'

    # Multi-company comparison = TABLE
    if len(tickers) > 1 and any(word in query_lower for word in ['compare', 'vs', 'versus', 'comparison', 'vs.', 'against', 'versus']):
        return True, 'comparison'

    # Multiple metrics for one company over years = TABLE
    if len(tickers) == 1 and any(word in query_lower for word in ['metrics', 'financials', 'figures', 'numbers', 'data', 'historique']):
        return True, 'metrics'

    # Specific ratios request = TABLE
    if any(word in query_lower for word in ['ratio', 'margin', 'debt', 'liquidity', 'efficiency', 'profitability']):
        if any(word in query_lower for word in ['compare', 'vs', 'multiple', 'several']):
            return True, 'ratios'

    return False, None


def should_give_details(query: str) -> bool:
    """
    Determine if user wants detailed explanation
    """
    query_lower = query.lower()

    # Explicit detail requests
    detail_keywords = [
        'explain', 'pourquoi', 'why', 'comment', 'how', 'détail',
        'details', 'elaborate', 'breakdown', 'analyze', 'analyser',
        'deep dive', 'what does', 'qu\'est-ce', 'tell me more',
        'plus de détails', 'more info'
    ]

    return any(keyword in query_lower for keyword in detail_keywords)


def get_response_style(query: str, tickers: List[str]) -> str:
    """
    Determine response style: 'short', 'table', 'detailed'
    """
    if should_give_details(query):
        return 'detailed'

    should_table, table_type = should_use_table(query, tickers, {})
    if should_table:
        return 'table'

    return 'short'


def create_metrics_table_from_data(ticker: str, company_name: str, metrics_data: dict) -> dict:
    """
    Create a metrics table from multi-year financial data

    metrics_data: {year: {revenue, net_income, margins, ratios, ...}}
    """
    rows = []
    years = sorted([int(y) for y in metrics_data.keys() if y.isdigit()])

    for year in years:
        year_str = str(year)
        data = metrics_data.get(year_str, {})

        row = {
            'Year': year,
            'Revenue ($B)': data.get('revenue_billions', 'N/A'),
            'Net Income ($B)': data.get('net_income_billions', 'N/A'),
            'Net Margin (%)': data.get('net_margin_pct', 'N/A'),
            'ROA (%)': data.get('roa_pct', 'N/A'),
            'Debt/Equity': data.get('debt_to_equity', 'N/A'),
        }
        rows.append(row)

    return {
        'title': f'{company_name} - Financial Metrics',
        'data': rows,
        'columns': ['Year', 'Revenue ($B)', 'Net Income ($B)', 'Net Margin (%)', 'ROA (%)', 'Debt/Equity']
    }


def create_comparison_table(companies_data: List[dict], metric: str = 'all') -> dict:
    """
    Create comparison table from multiple companies
    """
    rows = []

    for comp in companies_data:
        ticker = comp.get('ticker', '')
        company_name = comp.get('company_name', ticker)

        row = {
            'Company': company_name,
            'Revenue ($B)': comp.get('revenue_billions', 'N/A'),
            'Net Income ($B)': comp.get('net_income_billions', 'N/A'),
            'Net Margin (%)': comp.get('net_margin_pct', 'N/A'),
            'ROA (%)': comp.get('roa_pct', 'N/A'),
            'D/E Ratio': comp.get('debt_to_equity', 'N/A'),
        }
        rows.append(row)

    return {
        'title': 'Company Comparison',
        'data': rows,
        'columns': ['Company', 'Revenue ($B)', 'Net Income ($B)', 'Net Margin (%)', 'ROA (%)', 'D/E Ratio']
    }


def shorten_response(response: str, max_sentences: int = 3) -> str:
    """
    Shorten a long response to key sentences only
    """
    sentences = re.split(r'[.!?]+', response)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Take first N sentences
    shortened = '.'.join(sentences[:max_sentences]) + '.'

    return shortened


def format_short_response(ticker: str, company_name: str, key_metrics: dict) -> str:
    """
    Format a short, concise response with key metrics

    Example output:
    Apple: Revenue $416.16B, Net Margin 26.9%, ROA 31.2%. Strong profitability with solid asset efficiency.
    """
    revenue = key_metrics.get('revenue_billions')
    net_margin = key_metrics.get('net_margin_pct')
    roa = key_metrics.get('roa_pct')
    de = key_metrics.get('debt_to_equity')
    yoy = key_metrics.get('revenue_yoy_pct')

    parts = [f"{company_name}:"]

    if revenue:
        parts.append(f"Revenue ${revenue}B")

    if net_margin:
        parts.append(f"Net Margin {net_margin:.1f}%")

    if roa:
        parts.append(f"ROA {roa:.1f}%")

    if de:
        parts.append(f"D/E {de:.2f}x")

    result = ", ".join(parts[:-1]) + f". {parts[-1]}"

    # Add health assessment
    if net_margin and net_margin > 15:
        result += " Strong profitability."
    elif net_margin and net_margin > 5:
        result += " Healthy profitability."
    else:
        result += " Watch profitability."

    if de and de < 1:
        result += " Low debt."
    elif de and de > 3:
        result += " High leverage."

    return result
