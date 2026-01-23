"""
Financial Metrics and Ratios Calculator

Complete financial analysis module that computes:
- Year-over-Year (YoY) growth rates
- Profitability metrics (Net Profit Margin)
- Financial health ratios (Debt-to-Equity, ROA, Asset Turnover, etc.)
- Comparative analysis across companies

All calculations are extracted from the analysis.ipynb notebook.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class FinancialMetricsCalculator:
    """Calculate financial metrics and ratios from raw financial data"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize calculator with financial data.
        
        Args:
            df: DataFrame with columns: Company, Ticker, Fiscal Year,
                Total Revenue, Net Income, Total Assets, Total Liabilities, 
                Operating Cash Flow, etc.
        """
        self.df = df.copy()
        self.validate_data()
        
        # Ensure Fiscal Year is datetime
        if self.df['Fiscal Year'].dtype == 'object':
            self.df['Fiscal Year'] = pd.to_datetime(self.df['Fiscal Year'])
    
    def validate_data(self):
        """Validate required columns exist"""
        required_cols = ['Company', 'Ticker', 'Fiscal Year']
        missing = [col for col in required_cols if col not in self.df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
    
    def check_metrics_completeness(self) -> Dict[str, Dict]:
        """
        Check which metrics are already present in CSV for each company-year combination.
        Helps avoid redundant calculations.
        
        Returns:
            Dictionary with completeness status for each company-year:
            {
                'MSFT-2024': {
                    'has_balance_sheet': True,
                    'income_statement_completeness': 0.95,
                    'can_calculate_ratios': True
                },
                'AAPL-2023': {
                    'has_balance_sheet': False,
                    'income_statement_completeness': 0.85,
                    'can_calculate_ratios': False
                }
            }
        """
        balance_sheet_cols = [
            'Total Assets', 'Current Assets', 'Long-term Assets',
            'Total Liabilities', 'Current Liabilities', 'Long-term Liabilities',
            'Long-term Debt', 'Stockholders Equity'
        ]
        
        income_stmt_cols = [
            'Total Revenue', 'COGS', 'Gross Profit', 
            'Operating Expenses', 'Operating Income', 'Net Income'
        ]
        
        cash_flow_cols = [
            'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow'
        ]
        
        completeness = {}
        
        for ticker in self.df['Ticker'].unique():
            company_data = self.df[self.df['Ticker'] == ticker]
            
            for _, row in company_data.iterrows():
                key = f"{ticker}-{row['Fiscal Year'].year if hasattr(row['Fiscal Year'], 'year') else row['Fiscal Year']}"
                
                # Check balance sheet presence
                bs_cols_present = [col for col in balance_sheet_cols if col in self.df.columns]
                bs_available = all(pd.notna(row.get(col)) for col in bs_cols_present)
                
                # Check income statement completeness
                is_cols_present = [col for col in income_stmt_cols if col in self.df.columns]
                is_available = sum(1 for col in is_cols_present if pd.notna(row.get(col))) / len(is_cols_present) if is_cols_present else 0
                
                # Check if can calculate ratios (needs balance sheet)
                can_calc_ratios = bs_available and len(bs_cols_present) >= 4
                
                completeness[key] = {
                    'has_balance_sheet': bs_available,
                    'balance_sheet_completeness': sum(1 for col in bs_cols_present if pd.notna(row.get(col))) / len(bs_cols_present) if bs_cols_present else 0,
                    'income_statement_completeness': is_available,
                    'cash_flow_available': any(pd.notna(row.get(col)) for col in cash_flow_cols if col in self.df.columns),
                    'can_calculate_ratios': can_calc_ratios
                }
        
        return completeness
    
    def calculate_yoy_growth(self) -> pd.DataFrame:
        """
        Calculate Year-over-Year (YoY) growth rates for key metrics.
        
        Returns:
            DataFrame with YoY growth percentages for each metric
        """
        logger.info("Calculating YoY growth rates...")
        
        yoy_growth_all = []
        
        for ticker in sorted(self.df['Ticker'].unique()):
            company_data = self.df[self.df['Ticker'] == ticker].sort_values('Fiscal Year')
            company_name = company_data['Company'].iloc[0]
            
            for idx, (_, row) in enumerate(company_data.iterrows()):
                # Skip first year - no previous year to compare
                if idx == 0:
                    logger.debug(f"Skipping first year for {ticker} - no YoY comparison possible")
                    continue
                
                fiscal_year = row['Fiscal Year']
                prev_row = company_data.iloc[idx - 1]
                
                # Calculate YoY growth for each metric
                growth_metrics = {
                    'Revenue YoY %': self._calculate_growth(
                        row.get('Total Revenue'), 
                        prev_row.get('Total Revenue')
                    ),
                    'COGS YoY %': self._calculate_growth(
                        row.get('COGS'), 
                        prev_row.get('COGS')
                    ),
                    'Gross Profit YoY %': self._calculate_growth(
                        row.get('Gross Profit'), 
                        prev_row.get('Gross Profit')
                    ),
                    'Operating Income YoY %': self._calculate_growth(
                        row.get('Operating Income'), 
                        prev_row.get('Operating Income')
                    ),
                    'Net Income YoY %': self._calculate_growth(
                        row.get('Net Income'), 
                        prev_row.get('Net Income')
                    ),
                    'Total Assets YoY %': self._calculate_growth(
                        row.get('Total Assets'), 
                        prev_row.get('Total Assets')
                    ),
                    'Current Assets YoY %': self._calculate_growth(
                        row.get('Current Assets'), 
                        prev_row.get('Current Assets')
                    ),
                    'Total Liabilities YoY %': self._calculate_growth(
                        row.get('Total Liabilities'), 
                        prev_row.get('Total Liabilities')
                    ),
                    'Operating Cash Flow YoY %': self._calculate_growth(
                        row.get('Operating Cash Flow'), 
                        prev_row.get('Operating Cash Flow')
                    ),
                }
                
                yoy_growth_all.append({
                    'Company': company_name,
                    'Ticker': ticker,
                    'Fiscal Year': fiscal_year.strftime('%Y-%m-%d') if hasattr(fiscal_year, 'strftime') else str(fiscal_year),
                    'Previous Fiscal Year': prev_row['Fiscal Year'].strftime('%Y-%m-%d') if hasattr(prev_row['Fiscal Year'], 'strftime') else str(prev_row['Fiscal Year']),
                    **growth_metrics
                })
        
        yoy_df = pd.DataFrame(yoy_growth_all)
        logger.info(f"Calculated YoY growth for {len(yoy_df)} records (first year excluded)")
        
        return yoy_df
    
    @staticmethod
    def _calculate_growth(current: float, previous: float) -> Optional[float]:
        """
        Calculate percentage growth between two values.
        
        Args:
            current: Current period value
            previous: Previous period value
            
        Returns:
            Growth percentage or None if calculation not possible
        """
        if pd.notna(current) and pd.notna(previous) and previous != 0:
            return ((current - previous) / previous * 100)
        return None
    
    def calculate_profitability_metrics(self) -> pd.DataFrame:
        """
        Calculate profitability metrics (Net Profit Margin, Gross Margin, Operating Margin).
        
        Returns:
            DataFrame with profit margins for each company and year
        """
        logger.info("Calculating profitability metrics...")
        
        profit_data = []
        
        for ticker in self.df['Ticker'].unique():
            company_data = self.df[self.df['Ticker'] == ticker].sort_values('Fiscal Year')
            company_name = company_data['Company'].iloc[0]
            
            for _, row in company_data.iterrows():
                revenue = row.get('Total Revenue')
                gross_profit = row.get('Gross Profit')
                operating_income = row.get('Operating Income')
                net_income = row.get('Net Income')
                cogs = row.get('COGS')
                
                # Gross Profit Margin
                gross_margin = None
                if pd.notna(revenue) and pd.notna(gross_profit) and revenue != 0:
                    gross_margin = (gross_profit / revenue) * 100
                elif pd.notna(revenue) and pd.notna(cogs) and revenue != 0:
                    gross_margin = ((revenue - cogs) / revenue) * 100
                
                # Operating Profit Margin
                operating_margin = None
                if pd.notna(revenue) and pd.notna(operating_income) and revenue != 0:
                    operating_margin = (operating_income / revenue) * 100
                
                # Net Profit Margin
                net_margin = None
                if pd.notna(revenue) and pd.notna(net_income) and revenue != 0:
                    net_margin = (net_income / revenue) * 100
                
                profit_data.append({
                    'Company': company_name,
                    'Ticker': ticker,
                    'Fiscal Year': row['Fiscal Year'].strftime('%Y-%m-%d') if hasattr(row['Fiscal Year'], 'strftime') else str(row['Fiscal Year']),
                    'Gross Profit Margin %': gross_margin,
                    'Operating Profit Margin %': operating_margin,
                    'Net Profit Margin %': net_margin,
                })
        
        profit_df = pd.DataFrame(profit_data)
        logger.info(f"Calculated profit margins for {len(profit_df)} records")
        
        return profit_df
    
    def calculate_financial_ratios(self) -> pd.DataFrame:
        """
        Calculate key financial health ratios.
        
        Uses data from CSV where available (Total Assets, Liabilities, etc.)
        Only calculates ratios for rows with complete balance sheet data.
        
        Ratios computed:
        - Debt-to-Equity: Total Liabilities / Stockholders' Equity
        - Debt-to-Assets: Total Liabilities / Total Assets
        - ROA: (Net Income / Assets) × 100
        - Asset Turnover: Revenue / Assets
        - OCF-to-Liabilities: Operating Cash Flow / Liabilities
        
        Returns:
            DataFrame with financial ratios for each company
        """
        logger.info("Calculating financial ratios...")
        
        ratios_data = []
        
        for ticker in self.df['Ticker'].unique():
            company_data = self.df[self.df['Ticker'] == ticker].sort_values('Fiscal Year')
            company_name = company_data['Company'].iloc[0]
            
            # Process each row, only calculate ratios for rows with balance sheet data
            for _, row in company_data.iterrows():
                fiscal_year = row['Fiscal Year']
                
                # Check if we have balance sheet data for this row
                has_balance_sheet = (
                    pd.notna(row.get('Total Assets')) and 
                    pd.notna(row.get('Total Liabilities'))
                )
                
                if not has_balance_sheet:
                    logger.debug(f"Skipping ratios for {ticker} {fiscal_year} - no balance sheet data")
                    continue
                
                # Extract values (use CSV values directly)
                assets = row.get('Total Assets')
                current_assets = row.get('Current Assets')
                long_term_assets = row.get('Long-term Assets')
                liabilities = row.get('Total Liabilities')
                current_liabilities = row.get('Current Liabilities')
                long_term_liabilities = row.get('Long-term Liabilities')
                long_term_debt = row.get('Long-term Debt')
                equity = row.get('Stockholders Equity')  # Use from CSV
                revenue = row.get('Total Revenue')
                gross_profit = row.get('Gross Profit')
                net_income = row.get('Net Income')
                operating_income = row.get('Operating Income')
                ocf = row.get('Operating Cash Flow')
                investing_cf = row.get('Investing Cash Flow')
                financing_cf = row.get('Financing Cash Flow')
                
                # Calculate ratios with safety checks
                ratios = {
                    'Company': company_name,
                    'Ticker': ticker,
                    'Fiscal Year': fiscal_year.strftime('%Y-%m-%d') if hasattr(fiscal_year, 'strftime') else str(fiscal_year),
                }
                
                # Liquidity Ratios
                if current_assets and pd.notna(current_assets) and current_liabilities and current_liabilities > 0:
                    ratios['Current Ratio'] = current_assets / current_liabilities
                else:
                    ratios['Current Ratio'] = np.nan
                
                # Debt-to-Equity
                if equity and equity > 0:
                    ratios['Debt-to-Equity'] = liabilities / equity
                else:
                    ratios['Debt-to-Equity'] = np.nan
                
                # Debt-to-Assets
                if assets and assets > 0:
                    ratios['Debt-to-Assets'] = liabilities / assets
                else:
                    ratios['Debt-to-Assets'] = np.nan
                
                # Long-term Debt-to-Equity
                if long_term_debt and pd.notna(long_term_debt) and equity and equity > 0:
                    ratios['LT-Debt-to-Equity'] = long_term_debt / equity
                else:
                    ratios['LT-Debt-to-Equity'] = np.nan
                
                # Return on Assets (ROA)
                if assets and assets > 0 and pd.notna(net_income):
                    ratios['ROA (%)'] = (net_income / assets * 100)
                else:
                    ratios['ROA (%)'] = np.nan
                
                # Return on Equity (ROE)
                if equity and equity > 0 and pd.notna(net_income):
                    ratios['ROE (%)'] = (net_income / equity * 100)
                else:
                    ratios['ROE (%)'] = np.nan
                
                # Asset Turnover
                if assets and assets > 0 and pd.notna(revenue):
                    ratios['Asset Turnover'] = revenue / assets
                else:
                    ratios['Asset Turnover'] = np.nan
                
                # Gross Profit Margin
                if pd.notna(revenue) and revenue > 0 and pd.notna(gross_profit):
                    ratios['Gross Margin (%)'] = (gross_profit / revenue * 100)
                else:
                    ratios['Gross Margin (%)'] = np.nan
                
                # Operating Margin
                if pd.notna(revenue) and revenue > 0 and pd.notna(operating_income):
                    ratios['Operating Margin (%)'] = (operating_income / revenue * 100)
                else:
                    ratios['Operating Margin (%)'] = np.nan
                
                # Net Profit Margin
                if pd.notna(revenue) and revenue > 0 and pd.notna(net_income):
                    ratios['Net Margin (%)'] = (net_income / revenue * 100)
                else:
                    ratios['Net Margin (%)'] = np.nan
                
                # OCF-to-Liabilities
                if liabilities and liabilities > 0 and pd.notna(ocf):
                    ratios['OCF-to-Liabilities'] = ocf / liabilities
                else:
                    ratios['OCF-to-Liabilities'] = np.nan
                
                # Free Cash Flow (OCF - CapEx approximation)
                if pd.notna(ocf) and pd.notna(investing_cf):
                    # Investing CF is typically negative, so add it
                    ratios['Free Cash Flow ($M)'] = ocf + investing_cf
                else:
                    ratios['Free Cash Flow ($M)'] = np.nan
                
                # OCF Margin
                if pd.notna(revenue) and revenue > 0 and pd.notna(ocf):
                    ratios['OCF Margin (%)'] = (ocf / revenue * 100)
                else:
                    ratios['OCF Margin (%)'] = np.nan
                
                ratios_data.append(ratios)
        
        ratios_df = pd.DataFrame(ratios_data)
        logger.info(f"Calculated financial ratios for {len(ratios_df)} records")
        
        return ratios_df
    
    def calculate_comparative_metrics(self) -> Dict[str, pd.DataFrame]:
        """
        Comprehensive comparative analysis across multiple dimensions.
        
        Generates comparisons at different levels:
        1. General: All companies' latest metrics
        2. By Business Category: Benchmark within category
        3. By Industry: Benchmark within industry
        4. By Fiscal Year: Trends over time
        
        Returns:
            Dictionary with DataFrames for each comparison type
        """
        logger.info("Calculating comprehensive comparative metrics...")
        
        comparisons = {}
        
        # 1. GENERAL COMPARISON - Latest metrics across all companies
        logger.info("  - General comparison (latest metrics)")
        general_data = []
        
        for ticker in sorted(self.df['Ticker'].unique()):
            company_data = self.df[self.df['Ticker'] == ticker].sort_values('Fiscal Year')
            latest = company_data.iloc[-1]
            
            general_data.append({
                'Company': latest['Company'],
                'Ticker': ticker,
                'Industry': latest.get('Industry', 'N/A'),
                'Business Category': latest.get('Business Category', 'N/A'),
                'Fiscal Year': latest['Fiscal Year'].strftime('%Y-%m-%d') if hasattr(latest['Fiscal Year'], 'strftime') else str(latest['Fiscal Year']),
                'Total Revenue ($B)': latest.get('Total Revenue', 0) / 1e9,
                'Net Income ($B)': latest.get('Net Income', 0) / 1e9,
                'Total Assets ($B)': latest.get('Total Assets', 0) / 1e9 if pd.notna(latest.get('Total Assets')) else None,
                'Operating Cash Flow ($B)': latest.get('Operating Cash Flow', 0) / 1e9 if pd.notna(latest.get('Operating Cash Flow')) else None,
                'Net Margin %': (latest.get('Net Income', 0) / latest.get('Total Revenue', 1) * 100) if pd.notna(latest.get('Total Revenue')) and latest.get('Total Revenue', 0) > 0 else None,
            })
        
        comparisons['general'] = pd.DataFrame(general_data).sort_values('Total Revenue ($B)', ascending=False)
        
        # 2. BY BUSINESS CATEGORY
        logger.info("  - Category comparison (latest year)")
        category_data = []
        
        for category in self.df['Business Category'].unique():
            if pd.isna(category):
                continue
            
            cat_data = self.df[self.df['Business Category'] == category].sort_values('Fiscal Year')
            
            for ticker in cat_data['Ticker'].unique():
                ticker_data = cat_data[cat_data['Ticker'] == ticker]
                latest = ticker_data.iloc[-1]
                
                category_data.append({
                    'Category': category,
                    'Company': latest['Company'],
                    'Ticker': ticker,
                    'Fiscal Year': latest['Fiscal Year'].strftime('%Y-%m-%d') if hasattr(latest['Fiscal Year'], 'strftime') else str(latest['Fiscal Year']),
                    'Revenue ($B)': latest.get('Total Revenue', 0) / 1e9,
                    'Net Income ($B)': latest.get('Net Income', 0) / 1e9,
                    'Asset Efficiency': (latest.get('Total Revenue', 0) / latest.get('Total Assets', 1)) if pd.notna(latest.get('Total Assets')) and latest.get('Total Assets', 0) > 0 else None,
                })
        
        comparisons['by_category'] = pd.DataFrame(category_data).sort_values(['Category', 'Revenue ($B)'], ascending=[True, False])
        
        # 3. BY INDUSTRY
        logger.info("  - Industry comparison (latest year)")
        industry_data = []
        
        for industry in self.df['Industry'].unique():
            if pd.isna(industry):
                continue
            
            ind_data = self.df[self.df['Industry'] == industry].sort_values('Fiscal Year')
            
            for ticker in ind_data['Ticker'].unique():
                ticker_data = ind_data[ind_data['Ticker'] == ticker]
                latest = ticker_data.iloc[-1]
                
                industry_data.append({
                    'Industry': industry,
                    'Company': latest['Company'],
                    'Ticker': ticker,
                    'Fiscal Year': latest['Fiscal Year'].strftime('%Y-%m-%d') if hasattr(latest['Fiscal Year'], 'strftime') else str(latest['Fiscal Year']),
                    'Revenue ($B)': latest.get('Total Revenue', 0) / 1e9,
                    'Net Income ($B)': latest.get('Net Income', 0) / 1e9,
                    'Profitability %': (latest.get('Net Income', 0) / latest.get('Total Revenue', 1) * 100) if pd.notna(latest.get('Total Revenue')) and latest.get('Total Revenue', 0) > 0 else None,
                })
        
        comparisons['by_industry'] = pd.DataFrame(industry_data).sort_values(['Industry', 'Revenue ($B)'], ascending=[True, False])
        
        # 4. BY FISCAL YEAR - Trends
        logger.info("  - Year-over-year trends")
        yearly_data = []
        
        for ticker in sorted(self.df['Ticker'].unique()):
            company_data = self.df[self.df['Ticker'] == ticker].sort_values('Fiscal Year')
            company_name = company_data['Company'].iloc[0]
            industry = company_data['Industry'].iloc[0]
            category = company_data['Business Category'].iloc[0]
            
            for _, row in company_data.iterrows():
                yearly_data.append({
                    'Company': company_name,
                    'Ticker': ticker,
                    'Industry': industry,
                    'Category': category,
                    'Fiscal Year': row['Fiscal Year'].strftime('%Y-%m-%d') if hasattr(row['Fiscal Year'], 'strftime') else str(row['Fiscal Year']),
                    'Fiscal Year (Short)': row['Fiscal Year'].strftime('%Y') if hasattr(row['Fiscal Year'], 'strftime') else str(row['Fiscal Year'])[-4:],
                    'Revenue ($B)': row.get('Total Revenue', 0) / 1e9,
                    'Net Income ($B)': row.get('Net Income', 0) / 1e9,
                    'Total Assets ($B)': row.get('Total Assets', 0) / 1e9 if pd.notna(row.get('Total Assets')) else None,
                    'OCF ($B)': row.get('Operating Cash Flow', 0) / 1e9 if pd.notna(row.get('Operating Cash Flow')) else None,
                })
        
        comparisons['by_year'] = pd.DataFrame(yearly_data).sort_values(['Company', 'Fiscal Year'])
        
        logger.info(f"Calculated comparative metrics: General({len(comparisons['general'])}), Category({len(comparisons['by_category'])}), Industry({len(comparisons['by_industry'])}), Yearly({len(comparisons['by_year'])})")
        
        return comparisons
    
    def generate_summary_report(
        self,
        yoy_df: pd.DataFrame,
        profit_df: pd.DataFrame,
        ratios_df: pd.DataFrame
    ) -> Dict:
        """
        Generate comprehensive summary report with rankings and insights.
        
        Args:
            yoy_df: YoY growth DataFrame
            profit_df: Profitability metrics DataFrame
            ratios_df: Financial ratios DataFrame
            
        Returns:
            Dictionary with summary insights
        """
        logger.info("Generating summary report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'companies_analyzed': self.df['Company'].nunique(),
            'fiscal_years': len(self.df['Fiscal Year'].unique()),
            'total_records': len(self.df),
        }
        
        # Revenue Rankings
        revenue_ranking = self.df.dropna(subset=['Total Revenue']).sort_values(
            'Fiscal Year'
        ).drop_duplicates('Ticker', keep='last').sort_values('Total Revenue', ascending=False)
        
        report['revenue_ranking'] = [
            {
                'rank': i + 1,
                'company': row['Company'],
                'ticker': row['Ticker'],
                'revenue_billions': round(row['Total Revenue'] / 1e9, 2)
            }
            for i, (_, row) in enumerate(revenue_ranking.iterrows())
        ]
        
        # Growth Leaders
        if len(yoy_df) > 0:
            growth_leaders = yoy_df.sort_values('Revenue YoY %', ascending=False, na_position='last')
            report['growth_leaders'] = [
                {
                    'company': row['Company'],
                    'ticker': row['Ticker'],
                    'fiscal_year': row['Fiscal Year'],
                    'revenue_yoy_percent': round(row['Revenue YoY %'], 2) if pd.notna(row['Revenue YoY %']) else None
                }
                for _, row in growth_leaders.head(5).iterrows()
                if pd.notna(row['Revenue YoY %'])
            ]
        
        # Profitability Leaders
        if len(profit_df) > 0:
            profit_latest = profit_df.sort_values('Fiscal Year').drop_duplicates(
                'Company', keep='last'
            ).sort_values('Net Profit Margin %', ascending=False, na_position='last')
            
            report['profitability_leaders'] = [
                {
                    'company': row['Company'],
                    'ticker': row['Ticker'],
                    'profit_margin_percent': round(row['Net Profit Margin %'], 2) if pd.notna(row['Net Profit Margin %']) else None
                }
                for _, row in profit_latest.iterrows()
                if pd.notna(row['Net Profit Margin %'])
            ]
        
        # Financial Health (Leverage)
        if len(ratios_df) > 0:
            dte_sorted = ratios_df.dropna(subset=['Debt-to-Equity']).sort_values('Debt-to-Equity')
            
            report['financial_health'] = [
                {
                    'company': row['Company'],
                    'ticker': row['Ticker'],
                    'debt_to_equity': round(row['Debt-to-Equity'], 2),
                    'leverage_status': self._classify_leverage(row['Debt-to-Equity'])
                }
                for _, row in dte_sorted.iterrows()
            ]
        
        return report
    
    @staticmethod
    def _classify_leverage(debt_to_equity: float) -> str:
        """Classify leverage level based on D/E ratio"""
        if debt_to_equity < 1:
            return "Conservative"
        elif debt_to_equity < 2:
            return "Moderate"
        else:
            return "High"


class AnalysisExporter:
    """Export analysis results to CSV files"""
    
    @staticmethod
    def export_all_analyses(
        output_dir: str,
        yoy_df: pd.DataFrame,
        profit_df: pd.DataFrame,
        ratios_df: pd.DataFrame,
        comparisons_dict: Dict[str, pd.DataFrame],
        raw_df: pd.DataFrame
    ) -> Dict[str, str]:
        """
        Export all analysis DataFrames to CSV files.
        
        Args:
            output_dir: Directory to save CSV files
            yoy_df: YoY growth DataFrame
            profit_df: Profitability DataFrame
            ratios_df: Financial ratios DataFrame
            comparisons_dict: Dict of comparison DataFrames (general, by_category, by_industry, by_year)
            raw_df: Raw financial data
            
        Returns:
            Dictionary mapping file names to file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files = {}
        
        # YoY Growth Analysis
        yoy_file = output_dir / 'yoy_growth_analysis.csv'
        yoy_df.to_csv(yoy_file, index=False)
        files['yoy_growth'] = str(yoy_file)
        logger.info(f"Exported YoY growth: {yoy_file}")
        
        # Profit Margin Analysis
        profit_file = output_dir / 'profit_margin_analysis.csv'
        profit_df.to_csv(profit_file, index=False)
        files['profit_margins'] = str(profit_file)
        logger.info(f"Exported profit margins: {profit_file}")
        
        # Financial Ratios Analysis
        ratios_file = output_dir / 'financial_ratios_analysis.csv'
        ratios_df.to_csv(ratios_file, index=False)
        files['financial_ratios'] = str(ratios_file)
        logger.info(f"Exported financial ratios: {ratios_file}")
        
        # Comparative Metrics - General
        comp_general_file = output_dir / 'comparative_general.csv'
        comparisons_dict['general'].to_csv(comp_general_file, index=False)
        files['comparative_general'] = str(comp_general_file)
        logger.info(f"Exported comparative general: {comp_general_file}")
        
        # Comparative Metrics - By Category
        comp_category_file = output_dir / 'comparative_by_category.csv'
        comparisons_dict['by_category'].to_csv(comp_category_file, index=False)
        files['comparative_by_category'] = str(comp_category_file)
        logger.info(f"Exported comparative by category: {comp_category_file}")
        
        # Comparative Metrics - By Industry
        comp_industry_file = output_dir / 'comparative_by_industry.csv'
        comparisons_dict['by_industry'].to_csv(comp_industry_file, index=False)
        files['comparative_by_industry'] = str(comp_industry_file)
        logger.info(f"Exported comparative by industry: {comp_industry_file}")
        
        # Comparative Metrics - By Year
        comp_year_file = output_dir / 'comparative_by_year.csv'
        comparisons_dict['by_year'].to_csv(comp_year_file, index=False)
        files['comparative_by_year'] = str(comp_year_file)
        logger.info(f"Exported comparative by year: {comp_year_file}")
        
        # Latest Year Summary
        latest_data = raw_df.sort_values('Fiscal Year', ascending=False).drop_duplicates(
            'Company'
        ).reset_index(drop=True)
        latest_file = output_dir / 'latest_financial_summary.csv'
        latest_data.to_csv(latest_file, index=False)
        files['latest_summary'] = str(latest_file)
        logger.info(f"Exported latest summary: {latest_file}")
        
        return files


def analyze_financial_data(
    csv_path: str,
    output_dir: Optional[str] = None
) -> Tuple[Dict, Dict[str, str]]:
    """
    Complete financial analysis pipeline.
    
    Optimizations:
    - Checks data completeness before calculating ratios
    - Logs which metrics are already available in CSV
    - Only calculates missing metrics
    
    Args:
        csv_path: Path to extracted financial data CSV
        output_dir: Output directory for CSV exports (optional)
        
    Returns:
        Tuple of (summary_report, exported_files_dict)
    """
    logger.info(f"Starting financial analysis from {csv_path}")
    
    # Load raw data
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} records from CSV")
    
    # Initialize calculator
    calculator = FinancialMetricsCalculator(df)
    
    # Check data completeness
    completeness = calculator.check_metrics_completeness()
    logger.info("Data Completeness Report:")
    for key, status in completeness.items():
        logger.info(f"  {key}:")
        logger.info(f"    - Balance Sheet: {status['balance_sheet_completeness']*100:.0f}% complete")
        logger.info(f"    - Income Statement: {status['income_statement_completeness']*100:.0f}% complete")
        logger.info(f"    - Can calculate ratios: {status['can_calculate_ratios']}")
    
    # Calculate all metrics
    yoy_df = calculator.calculate_yoy_growth()
    profit_df = calculator.calculate_profitability_metrics()
    ratios_df = calculator.calculate_financial_ratios()
    comparisons_dict = calculator.calculate_comparative_metrics()
    
    logger.info(f"Results: YoY={len(yoy_df)}, Profitability={len(profit_df)}, Ratios={len(ratios_df)}, " + 
                f"Comparisons: General={len(comparisons_dict['general'])}, Category={len(comparisons_dict['by_category'])}, " +
                f"Industry={len(comparisons_dict['by_industry'])}, Yearly={len(comparisons_dict['by_year'])}")
    
    # Generate summary
    summary = calculator.generate_summary_report(yoy_df, profit_df, ratios_df)
    
    # Export if output directory specified
    files_exported = {}
    if output_dir:
        files_exported = AnalysisExporter.export_all_analyses(
            output_dir,
            yoy_df,
            profit_df,
            ratios_df,
            comparisons_dict,
            df
        )
    
    logger.info("Financial analysis complete")
    
    return summary, files_exported


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    csv_path = Path(__file__).parent.parent.parent / 'data' / 'financial_data_raw.csv'
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis'
    
    if csv_path.exists():
        summary, files = analyze_financial_data(str(csv_path), str(output_dir))
        
        print("\n" + "="*80)
        print("FINANCIAL ANALYSIS SUMMARY")
        print("="*80)
        print(f"Companies Analyzed: {summary['companies_analyzed']}")
        print(f"Total Records: {summary['total_records']}")
        print(f"\nRevenue Leaders:")
        for item in summary['revenue_ranking'][:3]:
            print(f"  {item['rank']}. {item['company']}: ${item['revenue_billions']}B")
        print(f"\nFiles Exported:")
        for name, path in files.items():
            print(f"  ✓ {name}: {path}")
        print("="*80)
    else:
        print(f"CSV file not found: {csv_path}")
