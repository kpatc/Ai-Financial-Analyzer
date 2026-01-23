#!/usr/bin/env python3
"""
Query financial data from SQLite database.
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'financial_analyzer.db'

def query_companies():
    """Get all companies"""
    conn = sqlite3.connect(str(DB_PATH))
    query = "SELECT ticker, name, industry, business_category FROM companies"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def query_latest_metrics():
    """Get latest year metrics for each company"""
    conn = sqlite3.connect(str(DB_PATH))
    query = '''
        SELECT 
            c.ticker,
            c.name,
            fm.fiscal_year,
            fm.revenue / 1e9 as revenue_b,
            fm.net_income / 1e9 as net_income_b,
            fm.total_assets / 1e9 as total_assets_b
        FROM companies c
        JOIN financial_metrics fm ON c.id = fm.company_id
        ORDER BY c.ticker, fm.fiscal_year DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def query_yoy_comparison():
    """Get YoY growth comparison"""
    conn = sqlite3.connect(str(DB_PATH))
    query = '''
        SELECT 
            c.ticker,
            c.name,
            yg.fiscal_year,
            ROUND(yg.revenue_yoy_pct, 2) as revenue_yoy,
            ROUND(yg.net_income_yoy_pct, 2) as net_income_yoy,
            ROUND(yg.operating_cash_flow_yoy_pct, 2) as ocf_yoy
        FROM companies c
        JOIN yoy_growth yg ON c.id = yg.company_id
        ORDER BY c.ticker, yg.fiscal_year
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def query_profitability():
    """Get profitability metrics"""
    conn = sqlite3.connect(str(DB_PATH))
    query = '''
        SELECT 
            c.ticker,
            c.name,
            p.fiscal_year,
            ROUND(p.gross_margin_pct, 2) as gross_margin,
            ROUND(p.operating_margin_pct, 2) as operating_margin,
            ROUND(p.net_margin_pct, 2) as net_margin
        FROM companies c
        JOIN profitability p ON c.id = p.company_id
        ORDER BY c.ticker, p.fiscal_year
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def query_financial_health():
    """Get financial ratios for health assessment"""
    conn = sqlite3.connect(str(DB_PATH))
    query = '''
        SELECT 
            c.ticker,
            c.name,
            fr.fiscal_year,
            ROUND(fr.current_ratio, 2) as current_ratio,
            ROUND(fr.debt_to_equity, 2) as d_to_e,
            ROUND(fr.roe_pct, 2) as roe,
            ROUND(fr.roa_pct, 2) as roa
        FROM companies c
        JOIN financial_ratios fr ON c.id = fr.company_id
        ORDER BY c.ticker, fr.fiscal_year
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    print("\n" + "="*80)
    print("FINANCIAL DATA QUERIES")
    print("="*80)
    
    print("\n1. COMPANIES")
    print(query_companies().to_string(index=False))
    
    print("\n2. LATEST METRICS (Latest Year)")
    df = query_latest_metrics()
    # Get latest year per company
    latest = df.sort_values('fiscal_year').drop_duplicates('ticker', keep='last')
    print(latest.to_string(index=False))
    
    print("\n3. YEAR-OVER-YEAR GROWTH")
    print(query_yoy_comparison().to_string(index=False))
    
    print("\n4. PROFITABILITY ANALYSIS")
    print(query_profitability().to_string(index=False))
    
    print("\n5. FINANCIAL HEALTH RATIOS")
    print(query_financial_health().to_string(index=False))
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
