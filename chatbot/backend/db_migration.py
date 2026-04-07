#!/usr/bin/env python3
"""
Database Migration Script
Expand schema with missing financial ratios and add indexing
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'financial_analyzer.db'


def safe_execute(conn: sqlite3.Connection, sql: str, params=None) -> None:
    """Safely execute SQL, logging errors but continuing"""
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        logger.info(f"✓ {sql[:60]}...")
    except sqlite3.OperationalError as e:
        if 'already exists' in str(e):
            logger.info(f"⊘ Column/index already exists: {sql[:60]}...")
        else:
            logger.error(f"✗ Error: {e}")
            logger.error(f"  SQL: {sql[:80]}...")


def expand_financial_ratios_schema(conn: sqlite3.Connection) -> None:
    """Add missing financial ratio columns"""

    new_columns = [
        # Liquidity ratios
        ('quick_ratio', 'REAL'),
        ('cash_ratio', 'REAL'),

        # Efficiency ratios
        ('receivables_turnover', 'REAL'),
        ('inventory_turnover', 'REAL'),
        ('receivables_days', 'REAL'),
        ('inventory_days', 'REAL'),

        # Leverage ratios
        ('interest_coverage', 'REAL'),
        ('debt_ratio', 'REAL'),

        # Return metrics
        ('roc_pct', 'REAL'),  # Return on Capital
    ]

    logger.info("\nExpanding financial_ratios table schema...")

    for col_name, col_type in new_columns:
        sql = f"ALTER TABLE financial_ratios ADD COLUMN {col_name} {col_type}"
        safe_execute(conn, sql)


def expand_growth_metrics_schema(conn: sqlite3.Connection) -> None:
    """Add growth metrics like CAGR"""

    new_columns = [
        ('revenue_cagr_3y', 'REAL'),
        ('net_income_cagr_3y', 'REAL'),
        ('ocf_cagr_3y', 'REAL'),
    ]

    logger.info("\nExpanding yoy_growth table schema...")

    for col_name, col_type in new_columns:
        sql = f"ALTER TABLE yoy_growth ADD COLUMN {col_name} {col_type}"
        safe_execute(conn, sql)


def add_indexes(conn: sqlite3.Connection) -> None:
    """Add indexes for fast queries"""

    indexes = [
        # Company ID + Fiscal Year (most common queries)
        ("CREATE INDEX IF NOT EXISTS idx_financial_metrics_company_year "
         "ON financial_metrics(company_id, fiscal_year)"),

        ("CREATE INDEX IF NOT EXISTS idx_financial_ratios_company_year "
         "ON financial_ratios(company_id, fiscal_year)"),

        ("CREATE INDEX IF NOT EXISTS idx_yoy_growth_company_year "
         "ON yoy_growth(company_id, fiscal_year)"),

        ("CREATE INDEX IF NOT EXISTS idx_profitability_company_year "
         "ON profitability(company_id, fiscal_year)"),

        # Ticker searches
        ("CREATE INDEX IF NOT EXISTS idx_companies_ticker "
         "ON companies(ticker)"),

        # Fiscal year range queries
        ("CREATE INDEX IF NOT EXISTS idx_financial_metrics_year "
         "ON financial_metrics(fiscal_year)"),
    ]

    logger.info("\nAdding database indexes...")

    for index_sql in indexes:
        safe_execute(conn, index_sql)


def calculate_missing_ratios(conn: sqlite3.Connection) -> None:
    """Calculate and populate missing financial ratios"""

    logger.info("\nCalculating missing financial ratios...")

    cursor = conn.cursor()

    # Get all financial_metrics with missing ratios
    cursor.execute("""
        SELECT fm.id, fm.company_id, fm.fiscal_year, fm.revenue, fm.cogs, fm.total_assets,
               fm.current_assets, fm.total_liabilities, fm.current_liabilities,
               fm.long_term_debt, fm.stockholders_equity, fm.operating_income,
               fr.id as ratio_id
        FROM financial_metrics fm
        LEFT JOIN financial_ratios fr
            ON fm.company_id = fr.company_id AND fm.fiscal_year = fr.fiscal_year
        WHERE fm.revenue IS NOT NULL
        ORDER BY fm.company_id, fm.fiscal_year
    """)

    records = cursor.fetchall()
    logger.info(f"Processing {len(records)} financial metric records...")

    for record in records:
        (fm_id, company_id, fiscal_year, revenue, cogs, total_assets,
         current_assets, total_liabilities, current_liabilities,
         long_term_debt, stockholders_equity, operating_income, ratio_id) = record

        # Calculate ratios
        ratios = {}

        # Quick ratio (Current Assets - Inventory) / Current Liabilities
        # Approximation: Current Assets * 0.75 / Current Liabilities (without inventory data)
        if current_assets and current_liabilities:
            ratios['quick_ratio'] = (current_assets * 0.75) / current_liabilities if current_liabilities > 0 else None

        # Cash ratio (Cash) / Current Liabilities
        # Approximation: Current Assets * 0.25 / Current Liabilities
        if current_assets and current_liabilities:
            ratios['cash_ratio'] = (current_assets * 0.25) / current_liabilities if current_liabilities > 0 else None

        # Debt ratio = Total Liabilities / Total Assets
        if total_assets:
            ratios['debt_ratio'] = total_liabilities / total_assets if total_assets > 0 else None

        # Interest coverage (Operating Income / Interest Expense)
        # Approximation: Operating Income / (Long Term Debt * 0.05) - assuming 5% interest rate
        if operating_income and long_term_debt:
            interest_expense = long_term_debt * 0.05
            ratios['interest_coverage'] = operating_income / interest_expense if interest_expense > 0 else None

        # ROC (Return on Capital) = NOPAT / Invested Capital
        # Simplified: Operating Income / (Equity + LT Debt)
        if operating_income and stockholders_equity and long_term_debt:
            invested_capital = stockholders_equity + long_term_debt
            ratios['roc_pct'] = (operating_income / invested_capital * 100) if invested_capital > 0 else None

        # Update or insert ratios
        if ratio_id:
            # Update existing
            set_clause = ', '.join([f"{k} = ?" for k in ratios.keys()])
            if set_clause:
                sql = f"UPDATE financial_ratios SET {set_clause} WHERE id = ?"
                values = list(ratios.values()) + [ratio_id]
                safe_execute(conn, sql, values)
        else:
            # Insert new
            if ratios:
                cols = ['company_id', 'fiscal_year'] + list(ratios.keys())
                placeholders = ', '.join(['?'] * len(cols))
                sql = f"INSERT INTO financial_ratios ({', '.join(cols)}) VALUES ({placeholders})"
                values = [company_id, fiscal_year] + list(ratios.values())
                safe_execute(conn, sql, values)


def calculate_cagr(conn: sqlite3.Connection) -> None:
    """Calculate 3-year CAGR for growth metrics"""

    logger.info("\nCalculating 3-year CAGR...")

    cursor = conn.cursor()

    # Get all companies with 3 years of data
    cursor.execute("""
        SELECT company_id, fiscal_year, revenue, net_income, operating_cash_flow
        FROM financial_metrics
        WHERE revenue IS NOT NULL
        ORDER BY company_id, fiscal_year
    """)

    records = cursor.fetchall()

    # Group by company
    company_data = {}
    for record in records:
        company_id = record[0]
        if company_id not in company_data:
            company_data[company_id] = []
        company_data[company_id].append(record)

    # Calculate CAGR for each company
    for company_id, records in company_data.items():
        if len(records) >= 3:
            # Most recent year
            latest = records[-1]  # (company_id, fiscal_year, revenue, net_income, ocf)

            # Get prior year and 3 years back
            year_indices = {}
            for i, rec in enumerate(records):
                year_indices[rec[1]] = i

            # Try to find 3-year spread
            years = sorted(year_indices.keys())
            if len(years) >= 3:
                year_1 = records[year_indices[years[0]]]
                year_3 = records[year_indices[years[-1]]]

                # CAGR = (Ending Value / Beginning Value) ^ (1 / # of years) - 1
                def calc_cagr(start_val, end_val, years):
                    if start_val and end_val and start_val > 0:
                        return ((end_val / start_val) ** (1 / years) - 1) * 100
                    return None

                years_elapsed = len(years) - 1

                revenue_cagr = calc_cagr(year_1[2], year_3[2], years_elapsed)
                net_income_cagr = calc_cagr(year_1[3], year_3[3], years_elapsed) if year_1[3] and year_3[3] else None
                ocf_cagr = calc_cagr(year_1[4], year_3[4], years_elapsed) if year_1[4] and year_3[4] else None

                # Update yoy_growth table for the latest year
                cursor.execute("""
                    UPDATE yoy_growth
                    SET revenue_cagr_3y = ?, net_income_cagr_3y = ?, ocf_cagr_3y = ?
                    WHERE company_id = ? AND fiscal_year = ?
                """, (revenue_cagr, net_income_cagr, ocf_cagr, company_id, year_3[1]))

                conn.commit()


def migrate_database() -> None:
    """Run all migration steps"""

    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        return

    logger.info(f"Starting database migration for {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))

    try:
        expand_financial_ratios_schema(conn)
        expand_growth_metrics_schema(conn)
        add_indexes(conn)
        calculate_missing_ratios(conn)
        calculate_cagr(conn)

        logger.info("\n✓ Database migration completed successfully")

    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    migrate_database()
