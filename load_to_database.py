#!/usr/bin/env python3
"""
Load analysis results to SQLite and ChromaDB databases.
Standalone orchestration script for data integration.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Get paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
ANALYSIS_DIR = DATA_DIR / 'analysis'
RAW_CSV = DATA_DIR / 'financial_data_raw.csv'

def init_database():
    """Initialize SQLite database with required tables"""
    db_path = DATA_DIR / 'financial_analyzer.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Companies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY,
            ticker TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            cik TEXT,
            industry TEXT,
            business_category TEXT,
            state_of_incorporation TEXT,
            phone TEXT,
            address TEXT
        )
    ''')
    
    # Financial metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_metrics (
            id INTEGER PRIMARY KEY,
            company_id INTEGER NOT NULL,
            fiscal_year TEXT NOT NULL,
            revenue REAL,
            cogs REAL,
            gross_profit REAL,
            operating_expenses REAL,
            operating_income REAL,
            net_income REAL,
            total_assets REAL,
            current_assets REAL,
            long_term_assets REAL,
            total_liabilities REAL,
            current_liabilities REAL,
            long_term_liabilities REAL,
            long_term_debt REAL,
            stockholders_equity REAL,
            operating_cash_flow REAL,
            investing_cash_flow REAL,
            financing_cash_flow REAL,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    ''')
    
    # YoY growth table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS yoy_growth (
            id INTEGER PRIMARY KEY,
            company_id INTEGER NOT NULL,
            fiscal_year TEXT NOT NULL,
            previous_fiscal_year TEXT,
            revenue_yoy_pct REAL,
            cogs_yoy_pct REAL,
            gross_profit_yoy_pct REAL,
            operating_income_yoy_pct REAL,
            net_income_yoy_pct REAL,
            total_assets_yoy_pct REAL,
            current_assets_yoy_pct REAL,
            total_liabilities_yoy_pct REAL,
            operating_cash_flow_yoy_pct REAL,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    ''')
    
    # Profitability table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profitability (
            id INTEGER PRIMARY KEY,
            company_id INTEGER NOT NULL,
            fiscal_year TEXT NOT NULL,
            gross_margin_pct REAL,
            operating_margin_pct REAL,
            net_margin_pct REAL,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    ''')
    
    # Financial ratios table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_ratios (
            id INTEGER PRIMARY KEY,
            company_id INTEGER NOT NULL,
            fiscal_year TEXT NOT NULL,
            current_ratio REAL,
            debt_to_equity REAL,
            debt_to_assets REAL,
            lt_debt_to_equity REAL,
            roa_pct REAL,
            roe_pct REAL,
            asset_turnover REAL,
            gross_margin_pct REAL,
            operating_margin_pct REAL,
            net_margin_pct REAL,
            ocf_to_liabilities REAL,
            free_cash_flow REAL,
            ocf_margin_pct REAL,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized: {db_path}")
    return db_path

def load_companies(db_path):
    """Load unique companies from raw CSV"""
    df = pd.read_csv(RAW_CSV)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    companies_loaded = 0
    for _, row in df.drop_duplicates('Ticker').iterrows():
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO companies 
                (ticker, name, cik, industry, business_category, state_of_incorporation, phone, address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('Ticker'),
                row.get('Company Name'),
                row.get('CIK'),
                row.get('Industry'),
                row.get('Business Category'),
                row.get('State of Incorporation'),
                row.get('Phone'),
                row.get('Address')
            ))
            companies_loaded += 1
        except Exception as e:
            print(f"  ✗ Error loading {row.get('Ticker')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✓ Companies loaded: {companies_loaded}")

def load_financial_metrics(db_path):
    """Load financial metrics from raw CSV"""
    df = pd.read_csv(RAW_CSV)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    records_loaded = 0
    for _, row in df.iterrows():
        try:
            # Get company ID
            cursor.execute('SELECT id FROM companies WHERE ticker = ?', (row['Ticker'],))
            company_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO financial_metrics
                (company_id, fiscal_year, revenue, cogs, gross_profit, operating_expenses,
                 operating_income, net_income, total_assets, current_assets, long_term_assets,
                 total_liabilities, current_liabilities, long_term_liabilities, long_term_debt,
                 stockholders_equity, operating_cash_flow, investing_cash_flow, financing_cash_flow)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_id,
                str(row.get('Fiscal Year')),
                row.get('Total Revenue'),
                row.get('COGS'),
                row.get('Gross Profit'),
                row.get('Operating Expenses'),
                row.get('Operating Income'),
                row.get('Net Income'),
                row.get('Total Assets'),
                row.get('Current Assets'),
                row.get('Long-term Assets'),
                row.get('Total Liabilities'),
                row.get('Current Liabilities'),
                row.get('Long-term Liabilities'),
                row.get('Long-term Debt'),
                row.get('Stockholders Equity'),
                row.get('Operating Cash Flow'),
                row.get('Investing Cash Flow'),
                row.get('Financing Cash Flow')
            ))
            records_loaded += 1
        except Exception as e:
            print(f"  ✗ Error loading metrics for {row.get('Ticker')} {row.get('Fiscal Year')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✓ Financial metrics loaded: {records_loaded}")

def load_yoy_growth(db_path):
    """Load YoY growth from analysis CSV"""
    yoy_file = ANALYSIS_DIR / 'yoy_growth_analysis.csv'
    if not yoy_file.exists():
        print(f"⚠ YoY file not found: {yoy_file}")
        return
    
    df = pd.read_csv(yoy_file)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    records_loaded = 0
    for _, row in df.iterrows():
        try:
            cursor.execute('SELECT id FROM companies WHERE ticker = ?', (row['Ticker'],))
            company_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO yoy_growth
                (company_id, fiscal_year, previous_fiscal_year, revenue_yoy_pct, cogs_yoy_pct,
                 gross_profit_yoy_pct, operating_income_yoy_pct, net_income_yoy_pct,
                 total_assets_yoy_pct, current_assets_yoy_pct, total_liabilities_yoy_pct,
                 operating_cash_flow_yoy_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_id,
                row.get('Fiscal Year'),
                row.get('Previous Fiscal Year'),
                row.get('Revenue YoY %'),
                row.get('COGS YoY %'),
                row.get('Gross Profit YoY %'),
                row.get('Operating Income YoY %'),
                row.get('Net Income YoY %'),
                row.get('Total Assets YoY %'),
                row.get('Current Assets YoY %'),
                row.get('Total Liabilities YoY %'),
                row.get('Operating Cash Flow YoY %')
            ))
            records_loaded += 1
        except Exception as e:
            print(f"  ✗ Error loading YoY for {row.get('Ticker')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✓ YoY growth loaded: {records_loaded}")

def load_profitability(db_path):
    """Load profitability metrics from analysis CSV"""
    profit_file = ANALYSIS_DIR / 'profit_margin_analysis.csv'
    if not profit_file.exists():
        print(f"⚠ Profitability file not found: {profit_file}")
        return
    
    df = pd.read_csv(profit_file)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    records_loaded = 0
    for _, row in df.iterrows():
        try:
            cursor.execute('SELECT id FROM companies WHERE ticker = ?', (row['Ticker'],))
            company_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO profitability
                (company_id, fiscal_year, gross_margin_pct, operating_margin_pct, net_margin_pct)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                company_id,
                row.get('Fiscal Year'),
                row.get('Gross Profit Margin %'),
                row.get('Operating Profit Margin %'),
                row.get('Net Profit Margin %')
            ))
            records_loaded += 1
        except Exception as e:
            print(f"  ✗ Error loading profitability for {row.get('Ticker')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✓ Profitability metrics loaded: {records_loaded}")

def load_ratios(db_path):
    """Load financial ratios from analysis CSV"""
    ratios_file = ANALYSIS_DIR / 'financial_ratios_analysis.csv'
    if not ratios_file.exists():
        print(f"⚠ Ratios file not found: {ratios_file}")
        return
    
    df = pd.read_csv(ratios_file)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    records_loaded = 0
    for _, row in df.iterrows():
        try:
            cursor.execute('SELECT id FROM companies WHERE ticker = ?', (row['Ticker'],))
            company_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO financial_ratios
                (company_id, fiscal_year, current_ratio, debt_to_equity, debt_to_assets,
                 lt_debt_to_equity, roa_pct, roe_pct, asset_turnover, gross_margin_pct,
                 operating_margin_pct, net_margin_pct, ocf_to_liabilities, free_cash_flow,
                 ocf_margin_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_id,
                row.get('Fiscal Year'),
                row.get('Current Ratio'),
                row.get('Debt-to-Equity'),
                row.get('Debt-to-Assets'),
                row.get('LT-Debt-to-Equity'),
                row.get('ROA (%)'),
                row.get('ROE (%)'),
                row.get('Asset Turnover'),
                row.get('Gross Margin (%)'),
                row.get('Operating Margin (%)'),
                row.get('Net Margin (%)'),
                row.get('OCF-to-Liabilities'),
                row.get('Free Cash Flow ($M)'),
                row.get('OCF Margin (%)')
            ))
            records_loaded += 1
        except Exception as e:
            print(f"  ✗ Error loading ratios for {row.get('Ticker')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✓ Financial ratios loaded: {records_loaded}")

def main():
    print("\n" + "="*80)
    print("LOADING DATA TO DATABASES")
    print("="*80)
    
    # Initialize database
    db_path = init_database()
    
    # Load data
    print("\nLoading financial data...")
    load_companies(db_path)
    load_financial_metrics(db_path)
    load_yoy_growth(db_path)
    load_profitability(db_path)
    load_ratios(db_path)
    
    print("\n" + "="*80)
    print("✓ DATA LOADING COMPLETE")
    print("="*80)
    print(f"Database: {db_path}")
    
    # Show summary
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    for table in ['companies', 'financial_metrics', 'yoy_growth', 'profitability', 'financial_ratios']:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")
    
    conn.close()
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
