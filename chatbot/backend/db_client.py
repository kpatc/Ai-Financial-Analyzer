#!/usr/bin/env python3
"""
Financial Database Client
Clean SQLite interface for financial data queries
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class FinancialDBClient:
    """SQLite client for financial data access"""

    def __init__(self, db_path: str):
        """
        Initialize database client

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row  # Return dicts instead of tuples
        logger.info(f"Connected to database: {db_path}")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========================================================================
    # COMPANY DATA
    # ========================================================================

    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        Get list of all companies

        Returns:
            List of company dicts {id, ticker, name, sector, industry, ...}
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, ticker, name, industry, business_category as sector
            FROM companies
            ORDER BY name
        """)
        companies = [dict(row) for row in cursor.fetchall()]
        logger.debug(f"Retrieved {len(companies)} companies")
        return companies

    def get_company_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get company by ticker

        Args:
            ticker: Company ticker symbol

        Returns:
            Company dict or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, ticker, name, industry, business_category as sector, cik
            FROM companies
            WHERE UPPER(ticker) = UPPER(?)
        """, (ticker,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def search_tickers(self, query: str) -> List[str]:
        """
        Search for tickers by company name

        Args:
            query: Company name or partial match

        Returns:
            List of matching tickers
        """
        cursor = self.connection.cursor()
        query_pattern = f"%{query}%"
        cursor.execute("""
            SELECT ticker
            FROM companies
            WHERE UPPER(name) LIKE UPPER(?)
            ORDER BY name
        """, (query_pattern,))
        tickers = [row[0] for row in cursor.fetchall()]
        return tickers

    def get_sector_companies(self, sector: str) -> List[Dict[str, Any]]:
        """
        Get all companies in a sector

        Args:
            sector: Business category/sector name

        Returns:
            List of company dicts
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, ticker, name, business_category as sector
            FROM companies
            WHERE UPPER(business_category) = UPPER(?)
            ORDER BY name
        """, (sector,))
        companies = [dict(row) for row in cursor.fetchall()]
        return companies

    # ========================================================================
    # FINANCIAL METRICS
    # ========================================================================

    def get_company_metrics(self, ticker: str, fiscal_year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get latest or specific fiscal year metrics for a company

        Args:
            ticker: Company ticker
            fiscal_year: Specific year, or None for latest

        Returns:
            Metrics dict {revenue, net_income, total_assets, ...} or None
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return None

        cursor = self.connection.cursor()

        if fiscal_year is None:
            # Get latest fiscal year
            cursor.execute("""
                SELECT *
                FROM financial_metrics
                WHERE company_id = ?
                ORDER BY fiscal_year DESC
                LIMIT 1
            """, (company['id'],))
        else:
            cursor.execute("""
                SELECT *
                FROM financial_metrics
                WHERE company_id = ? AND fiscal_year = ?
            """, (company['id'], fiscal_year))

        row = cursor.fetchone()
        if not row:
            return None

        metrics = dict(row)
        metrics['ticker'] = ticker
        metrics['company_name'] = company['name']
        metrics['sector'] = company['sector']
        return metrics

    def get_revenue_trend(self, ticker: str, years: int = 3) -> List[Dict[str, Any]]:
        """
        Get revenue and net income trend for a company

        Args:
            ticker: Company ticker
            years: Number of years to retrieve

        Returns:
            List of {fiscal_year, revenue, net_income, revenue_billions, ...}
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return []

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                fiscal_year,
                revenue,
                net_income,
                operating_cash_flow,
                total_assets,
                total_liabilities
            FROM financial_metrics
            WHERE company_id = ?
            ORDER BY fiscal_year DESC
            LIMIT ?
        """, (company['id'], years))

        trends = []
        for row in cursor.fetchall():
            trend = dict(row)
            # Convert to billions for display
            if trend['revenue']:
                trend['revenue_billions'] = round(trend['revenue'] / 1e9, 2)
            if trend['net_income']:
                trend['net_income_billions'] = round(trend['net_income'] / 1e9, 2)
            trends.append(trend)

        trends.reverse()  # Return chronologically ordered
        return trends

    # ========================================================================
    # FINANCIAL RATIOS & PROFITABILITY
    # ========================================================================

    def get_ratios(self, ticker: str, fiscal_year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get financial ratios for a company

        Args:
            ticker: Company ticker
            fiscal_year: Specific year, or None for latest

        Returns:
            Ratios dict {debt_to_equity, roa_pct, net_margin_pct, ...}
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return None

        cursor = self.connection.cursor()

        if fiscal_year is None:
            cursor.execute("""
                SELECT *
                FROM financial_ratios
                WHERE company_id = ?
                ORDER BY fiscal_year DESC
                LIMIT 1
            """, (company['id'],))
        else:
            cursor.execute("""
                SELECT *
                FROM financial_ratios
                WHERE company_id = ? AND fiscal_year = ?
            """, (company['id'], fiscal_year))

        row = cursor.fetchone()
        if not row:
            return None

        ratios = dict(row)
        ratios['ticker'] = ticker
        return ratios

    def get_profitability(self, ticker: str, fiscal_year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get profitability metrics (margins)

        Args:
            ticker: Company ticker
            fiscal_year: Specific year, or None for latest

        Returns:
            Profitability dict {gross_margin_pct, operating_margin_pct, net_margin_pct}
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return None

        cursor = self.connection.cursor()

        if fiscal_year is None:
            cursor.execute("""
                SELECT fiscal_year, gross_margin_pct, operating_margin_pct, net_margin_pct
                FROM profitability
                WHERE company_id = ?
                ORDER BY fiscal_year DESC
                LIMIT 1
            """, (company['id'],))
        else:
            cursor.execute("""
                SELECT fiscal_year, gross_margin_pct, operating_margin_pct, net_margin_pct
                FROM profitability
                WHERE company_id = ? AND fiscal_year = ?
            """, (company['id'], fiscal_year))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ========================================================================
    # RANKINGS & COMPARISONS
    # ========================================================================

    def get_rankings(self, metric: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top companies by a metric

        Args:
            metric: Column name (revenue, net_income, total_assets, etc.)
            top_n: Number of top companies to return

        Returns:
            Ranked list of companies with the metric
        """
        valid_metrics = [
            'revenue', 'net_income', 'total_assets', 'total_liabilities',
            'operating_cash_flow', 'stockholders_equity', 'long_term_debt'
        ]

        if metric not in valid_metrics:
            logger.warning(f"Invalid metric for ranking: {metric}")
            return []

        cursor = self.connection.cursor()
        cursor.execute(f"""
            SELECT
                c.ticker,
                c.name,
                c.business_category as sector,
                fm.fiscal_year,
                fm.{metric}
            FROM financial_metrics fm
            JOIN companies c ON fm.company_id = c.id
            WHERE fm.{metric} IS NOT NULL
            ORDER BY fm.fiscal_year DESC, fm.{metric} DESC
            LIMIT ?
        """, (top_n,))

        rankings = []
        seen_tickers = set()
        for row in cursor.fetchall():
            ticker = row[0]
            # Only keep first (latest year) occurrence per company
            if ticker not in seen_tickers:
                rankings.append({
                    'ticker': ticker,
                    'name': row[1],
                    'sector': row[2],
                    'fiscal_year': row[3],
                    'value': row[4],
                    'value_billions': round(row[4] / 1e9, 2) if row[4] else None,
                })
                seen_tickers.add(ticker)

        return rankings[:top_n]

    def get_comparison(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """
        Get latest metrics for multiple companies

        Args:
            tickers: List of company tickers

        Returns:
            List of company metric dicts for comparison
        """
        if not tickers:
            return []

        comparison = []
        for ticker in tickers:
            metrics = self.get_company_metrics(ticker)
            if metrics:
                # Add profitability and ratios
                prof = self.get_profitability(ticker)
                ratios = self.get_ratios(ticker)

                comparison_item = {
                    'ticker': ticker,
                    'name': metrics.get('company_name'),
                    'sector': metrics.get('sector'),
                    'fiscal_year': metrics.get('fiscal_year'),
                    'revenue_billions': round(metrics.get('revenue', 0) / 1e9, 2) if metrics.get('revenue') else None,
                    'net_income_billions': round(metrics.get('net_income', 0) / 1e9, 2) if metrics.get('net_income') else None,
                    'total_assets_billions': round(metrics.get('total_assets', 0) / 1e9, 2) if metrics.get('total_assets') else None,
                    'operating_cash_flow_billions': round(metrics.get('operating_cash_flow', 0) / 1e9, 2) if metrics.get('operating_cash_flow') else None,
                }

                if prof:
                    comparison_item['net_margin_pct'] = round(prof.get('net_margin_pct', 0), 2)

                if ratios:
                    comparison_item['debt_to_equity'] = round(ratios.get('debt_to_equity', 0), 2)
                    comparison_item['roa_pct'] = round(ratios.get('roa_pct', 0), 2)

                comparison.append(comparison_item)

        return comparison

    def get_yoy_growth(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get year-over-year growth rates for a company

        Args:
            ticker: Company ticker

        Returns:
            YoY growth dict {revenue_yoy_pct, net_income_yoy_pct, ...}
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return None

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT fiscal_year, revenue_yoy_pct, net_income_yoy_pct, operating_cash_flow_yoy_pct
            FROM yoy_growth
            WHERE company_id = ?
            ORDER BY fiscal_year DESC
            LIMIT 1
        """, (company['id'],))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ========================================================================
    # AGGREGATE / ANALYTICS
    # ========================================================================

    def get_sector_metrics(self, sector: str) -> Dict[str, Any]:
        """
        Get aggregate metrics for a sector

        Args:
            sector: Business category/sector name

        Returns:
            Aggregated sector metrics {avg_revenue, count, ...}
        """
        companies = self.get_sector_companies(sector)
        if not companies:
            return {}

        tickers = [c['ticker'] for c in companies]
        comparison = self.get_comparison(tickers)

        if not comparison:
            return {}

        # Calculate averages
        total_revenue = sum([c.get('revenue_billions', 0) for c in comparison])
        avg_revenue = total_revenue / len(comparison) if comparison else 0
        avg_margin = sum([c.get('net_margin_pct', 0) for c in comparison]) / len(comparison) if comparison else 0

        return {
            'sector': sector,
            'company_count': len(comparison),
            'total_revenue_billions': round(total_revenue, 2),
            'average_revenue_billions': round(avg_revenue, 2),
            'average_net_margin_pct': round(avg_margin, 2),
            'companies': comparison,
        }


def get_db_client(db_path: str = None) -> FinancialDBClient:
    """
    Factory function to get a database client

    Args:
        db_path: Path to SQLite database, or None to use default from config

    Returns:
        FinancialDBClient instance
    """
    if db_path is None:
        from config import SQLITE_CONFIG
        db_path = SQLITE_CONFIG['path']

    return FinancialDBClient(db_path)
