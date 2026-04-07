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

    def get_comparison(self, tickers: List[str], include_all_ratios: bool = False) -> List[Dict[str, Any]]:
        """
        Get latest metrics for multiple companies

        Args:
            tickers: List of company tickers
            include_all_ratios: If True, include all available ratios

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
                liquidity = self.get_liquidity(ticker)
                leverage = self.get_leverage(ticker)
                efficiency = self.get_efficiency(ticker)

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

                # Profitability
                if prof:
                    gm = prof.get('gross_margin_pct')
                    om = prof.get('operating_margin_pct')
                    nm = prof.get('net_margin_pct')
                    if gm is not None:
                        comparison_item['gross_margin_pct'] = round(gm, 2)
                    if om is not None:
                        comparison_item['operating_margin_pct'] = round(om, 2)
                    if nm is not None:
                        comparison_item['net_margin_pct'] = round(nm, 2)

                # Ratios (always include basic ones)
                if ratios:
                    comparison_item['debt_to_equity'] = round(ratios.get('debt_to_equity', 0), 2)
                    comparison_item['roa_pct'] = round(ratios.get('roa_pct', 0), 2)
                    comparison_item['roe_pct'] = round(ratios.get('roe_pct', 0), 2)
                    comparison_item['asset_turnover'] = round(ratios.get('asset_turnover', 0), 2)
                    comparison_item['free_cash_flow'] = round(ratios.get('free_cash_flow', 0) / 1e9, 2) if ratios.get('free_cash_flow') else None

                if include_all_ratios:
                    # Liquidity
                    if liquidity:
                        cr = liquidity.get('current_ratio')
                        qr = liquidity.get('quick_ratio')
                        ca = liquidity.get('cash_ratio')
                        if cr is not None:
                            comparison_item['current_ratio'] = round(cr, 2)
                        if qr is not None:
                            comparison_item['quick_ratio'] = round(qr, 2)
                        if ca is not None:
                            comparison_item['cash_ratio'] = round(ca, 2)

                    # Leverage
                    if leverage:
                        dr = leverage.get('debt_ratio')
                        ic = leverage.get('interest_coverage')
                        if dr is not None:
                            comparison_item['debt_ratio'] = round(dr, 2)
                        if ic is not None:
                            comparison_item['interest_coverage'] = round(ic, 2)

                    # Efficiency
                    if efficiency:
                        rt = efficiency.get('receivables_turnover')
                        it = efficiency.get('inventory_turnover')
                        roc = efficiency.get('roc_pct')
                        if rt is not None:
                            comparison_item['receivables_turnover'] = round(rt, 2)
                        if it is not None:
                            comparison_item['inventory_turnover'] = round(it, 2)
                        if roc is not None:
                            comparison_item['roc_pct'] = round(roc, 2)

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
            SELECT fiscal_year, revenue_yoy_pct, net_income_yoy_pct, operating_cash_flow_yoy_pct,
                   revenue_cagr_3y, net_income_cagr_3y, ocf_cagr_3y
            FROM yoy_growth
            WHERE company_id = ?
            ORDER BY fiscal_year DESC
            LIMIT 1
        """, (company['id'],))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ========================================================================
    # LIQUIDITY METRICS
    # ========================================================================

    def get_liquidity(self, ticker: str, fiscal_year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get liquidity metrics for a company

        Args:
            ticker: Company ticker
            fiscal_year: Specific year, or None for latest

        Returns:
            Liquidity dict {current_ratio, quick_ratio, cash_ratio}
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return None

        cursor = self.connection.cursor()

        if fiscal_year is None:
            cursor.execute("""
                SELECT fiscal_year, current_ratio, quick_ratio, cash_ratio
                FROM financial_ratios
                WHERE company_id = ?
                ORDER BY fiscal_year DESC
                LIMIT 1
            """, (company['id'],))
        else:
            cursor.execute("""
                SELECT fiscal_year, current_ratio, quick_ratio, cash_ratio
                FROM financial_ratios
                WHERE company_id = ? AND fiscal_year = ?
            """, (company['id'], fiscal_year))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ========================================================================
    # EFFICIENCY METRICS
    # ========================================================================

    def get_efficiency(self, ticker: str, fiscal_year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get efficiency metrics for a company

        Args:
            ticker: Company ticker
            fiscal_year: Specific year, or None for latest

        Returns:
            Efficiency dict {asset_turnover, receivables_turnover, inventory_turnover, roc_pct}
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return None

        cursor = self.connection.cursor()

        if fiscal_year is None:
            cursor.execute("""
                SELECT fiscal_year, asset_turnover, receivables_turnover, inventory_turnover,
                       receivables_days, inventory_days, roc_pct
                FROM financial_ratios
                WHERE company_id = ?
                ORDER BY fiscal_year DESC
                LIMIT 1
            """, (company['id'],))
        else:
            cursor.execute("""
                SELECT fiscal_year, asset_turnover, receivables_turnover, inventory_turnover,
                       receivables_days, inventory_days, roc_pct
                FROM financial_ratios
                WHERE company_id = ? AND fiscal_year = ?
            """, (company['id'], fiscal_year))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ========================================================================
    # LEVERAGE METRICS
    # ========================================================================

    def get_leverage(self, ticker: str, fiscal_year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get leverage/solvency metrics for a company

        Args:
            ticker: Company ticker
            fiscal_year: Specific year, or None for latest

        Returns:
            Leverage dict {debt_to_equity, debt_ratio, debt_to_assets, interest_coverage, lt_debt_to_equity}
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return None

        cursor = self.connection.cursor()

        if fiscal_year is None:
            cursor.execute("""
                SELECT fiscal_year, debt_to_equity, debt_ratio, debt_to_assets,
                       interest_coverage, lt_debt_to_equity
                FROM financial_ratios
                WHERE company_id = ?
                ORDER BY fiscal_year DESC
                LIMIT 1
            """, (company['id'],))
        else:
            cursor.execute("""
                SELECT fiscal_year, debt_to_equity, debt_ratio, debt_to_assets,
                       interest_coverage, lt_debt_to_equity
                FROM financial_ratios
                WHERE company_id = ? AND fiscal_year = ?
            """, (company['id'], fiscal_year))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_growth_metrics(self, ticker: str, years: int = 3) -> List[Dict[str, Any]]:
        """
        Get growth metrics over multiple years for a company

        Args:
            ticker: Company ticker
            years: Number of years to retrieve

        Returns:
            List of growth dicts with YoY and CAGR metrics
        """
        company = self.get_company_by_ticker(ticker)
        if not company:
            return []

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT fiscal_year, revenue_yoy_pct, net_income_yoy_pct, operating_cash_flow_yoy_pct,
                   revenue_cagr_3y, net_income_cagr_3y, ocf_cagr_3y
            FROM yoy_growth
            WHERE company_id = ?
            ORDER BY fiscal_year DESC
            LIMIT ?
        """, (company['id'], years))

        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # TABLE DATA (STRUCTURED FOR API)
    # ========================================================================

    def get_metrics_table(self, tickers: Optional[List[str]] = None,
                         fiscal_year: Optional[int] = None,
                         sort_by: str = 'revenue',
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get structured financial metrics table data

        Args:
            tickers: Filter by tickers, or None for all
            fiscal_year: Filter by fiscal year, or None for latest
            sort_by: Column to sort by
            limit: Max rows to return

        Returns:
            List of metric dicts suitable for table display
        """
        cursor = self.connection.cursor()

        ticker_filter = ""
        params = []

        if tickers:
            placeholders = ','.join(['?' for _ in tickers])
            ticker_filter = f"AND c.ticker IN ({placeholders})"
            params.extend(tickers)

        if fiscal_year:
            ticker_filter += " AND fm.fiscal_year = ?"
            params.append(fiscal_year)

        valid_sorts = ['revenue', 'net_income', 'total_assets', 'operating_cash_flow']
        if sort_by not in valid_sorts:
            sort_by = 'revenue'

        cursor.execute(f"""
            SELECT
                c.ticker,
                c.name,
                c.business_category as sector,
                fm.fiscal_year,
                fm.revenue,
                fm.net_income,
                fm.operating_cash_flow,
                fm.total_assets,
                fm.total_liabilities,
                fm.stockholders_equity
            FROM financial_metrics fm
            JOIN companies c ON fm.company_id = c.id
            WHERE fm.{sort_by} IS NOT NULL {ticker_filter}
            ORDER BY fm.fiscal_year DESC, fm.{sort_by} DESC
            LIMIT ?
        """, params + [limit])

        rows = cursor.fetchall()
        result = []

        for row in rows:
            result.append({
                'ticker': row[0],
                'name': row[1],
                'sector': row[2],
                'fiscal_year': row[3],
                'revenue': round(row[4] / 1e9, 2) if row[4] else None,
                'net_income': round(row[5] / 1e9, 2) if row[5] else None,
                'operating_cash_flow': round(row[6] / 1e9, 2) if row[6] else None,
                'total_assets': round(row[7] / 1e9, 2) if row[7] else None,
                'total_liabilities': round(row[8] / 1e9, 2) if row[8] else None,
                'stockholders_equity': round(row[9] / 1e9, 2) if row[9] else None,
            })

        return result

    def get_ratios_table(self, tickers: Optional[List[str]] = None,
                         fiscal_year: Optional[int] = None,
                         categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get structured financial ratios table data

        Args:
            tickers: Filter by tickers, or None for all
            fiscal_year: Filter by fiscal year, or None for latest
            categories: Filter by ratio categories (profitability, liquidity, leverage, efficiency)

        Returns:
            List of ratio dicts suitable for table display
        """
        cursor = self.connection.cursor()

        ticker_filter = ""
        params = []

        if tickers:
            placeholders = ','.join(['?' for _ in tickers])
            ticker_filter = f"AND c.ticker IN ({placeholders})"
            params.extend(tickers)

        if fiscal_year:
            ticker_filter += " AND fr.fiscal_year = ?"
            params.append(fiscal_year)
        else:
            # Get latest year per company
            ticker_filter += " AND fr.fiscal_year IN (SELECT MAX(fiscal_year) FROM financial_ratios WHERE company_id = fr.company_id)"

        cursor.execute(f"""
            SELECT
                c.ticker,
                c.name,
                c.business_category as sector,
                fr.fiscal_year,
                fr.gross_margin_pct,
                fr.operating_margin_pct,
                fr.net_margin_pct,
                fr.current_ratio,
                fr.quick_ratio,
                fr.debt_to_equity,
                fr.debt_ratio,
                fr.roa_pct,
                fr.roe_pct,
                fr.asset_turnover,
                fr.interest_coverage,
                fr.roc_pct
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.id
            WHERE fr.net_margin_pct IS NOT NULL {ticker_filter}
            ORDER BY fr.fiscal_year DESC, c.ticker
        """, params)

        rows = cursor.fetchall()
        result = []

        for row in rows:
            item = {
                'ticker': row[0],
                'name': row[1],
                'sector': row[2],
                'fiscal_year': row[3],
            }

            # Add ratio categories
            if categories is None or 'profitability' in categories:
                item.update({
                    'gross_margin_pct': round(row[4], 2) if row[4] else None,
                    'operating_margin_pct': round(row[5], 2) if row[5] else None,
                    'net_margin_pct': round(row[6], 2) if row[6] else None,
                })

            if categories is None or 'liquidity' in categories:
                item.update({
                    'current_ratio': round(row[7], 2) if row[7] else None,
                    'quick_ratio': round(row[8], 2) if row[8] else None,
                })

            if categories is None or 'leverage' in categories:
                item.update({
                    'debt_to_equity': round(row[9], 2) if row[9] else None,
                    'debt_ratio': round(row[10], 2) if row[10] else None,
                })

            if categories is None or 'efficiency' in categories:
                item.update({
                    'roa_pct': round(row[11], 2) if row[11] else None,
                    'roe_pct': round(row[12], 2) if row[12] else None,
                    'asset_turnover': round(row[13], 2) if row[13] else None,
                    'interest_coverage': round(row[14], 2) if row[14] else None,
                    'roc_pct': round(row[15], 2) if row[15] else None,
                })

            result.append(item)

        return result

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
