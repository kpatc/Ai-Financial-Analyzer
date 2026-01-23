import sys
from pathlib import Path
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple

try:
    from edgar import Company, set_identity
except ImportError:
    print("Error: edgartools not installed. Run: pip install edgartools")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FinancialDataExtractor:

    XBRL_CONCEPTS = {
        # Income Statement
        'revenue': ['us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax', 'us-gaap_Revenues', 'us-gaap_SalesRevenueNet'],
        'cogs': ['us-gaap_CostOfGoodsAndServicesSold', 'us-gaap_CostOfRevenue'],
        'operating_expenses': ['us-gaap_OperatingExpenses', 'us-gaap_CostsAndExpenses', 'us-gaap_SG_A', 'us-gaap_SellingGeneralAndAdministrativeExpense'],
        'operating_income': ['us-gaap_OperatingIncomeLoss'],
        'net_income': ['us-gaap_NetIncomeLoss'],
        'gross_profit': ['us-gaap_GrossProfit'],
        
        # Balance Sheet
        'total_assets': ['us-gaap_Assets'],
        'current_assets': ['us-gaap_AssetsCurrent'],
        'long_term_assets': ['us-gaap_AssetsNoncurrent', 'us-gaap_OtherAssetsNoncurrent'],
        'total_liabilities': ['us-gaap_Liabilities'],
        'current_liabilities': ['us-gaap_LiabilitiesCurrent'],
        'long_term_liabilities': ['us-gaap_LiabilitiesNoncurrent', 'us-gaap_OtherLiabilitiesNoncurrent', 'us-gaap_LongTermDebtAndOperatingLeaseLiabilities'],
        'long_term_debt': ['us-gaap_LongTermDebt', 'us-gaap_LongTermDebtNoncurrent'],
        'stockholders_equity': ['us-gaap_StockholdersEquity'],
        
        # Cash Flow Statement
        'operating_cash_flow': ['us-gaap_NetCashProvidedByUsedInOperatingActivities'],
        'investing_cash_flow': ['us-gaap_NetCashProvidedByUsedInInvestingActivities'],
        'financing_cash_flow': ['us-gaap_NetCashProvidedByUsedInFinancingActivities'],
    }

    def __init__(self, sec_identity: str):
        set_identity(sec_identity)
        logger.info(f"Initialized extractor")
    
    def _extract_company_info(self, company) -> Dict:
        """Extract company information for semantic search"""
        company_info = {
            'Company Name': company.name if hasattr(company, 'name') else 'N/A',
            'CIK': company.cik if hasattr(company, 'cik') else 'N/A',
            'Industry': company.industry if hasattr(company, 'industry') else 'N/A',
            'Business Category': company.business_category if hasattr(company, 'business_category') else 'N/A',
            'State of Incorporation': company.state_of_incorporation if hasattr(company, 'state_of_incorporation') else 'N/A',
            'Address': str(company.business_address()) if hasattr(company, 'business_address') else 'N/A',
            'Phone': company.phone if hasattr(company, 'phone') else 'N/A',
        }
        logger.info(f"Extracted company info: {company_info['Company Name']} ({company_info['Industry']})")
        return company_info

    def extract_company(
        self,
        ticker: str,
        company_name: str,
        years: int = 3,
        fallback_labels: bool = True
    ) -> pd.DataFrame:

        logger.info(f"Extracting {ticker} ({company_name}) - {years} years")

        try:
            company = Company(ticker)
            logger.info(f"Found company: {company.name}")

            # Get latest financials first (usually has 2 years)
            financials = company.get_financials()

            if not self._validate_statements(financials):
                logger.error(f"Incomplete financial statements for {ticker}")
                return pd.DataFrame()

            is_df = financials.income_statement().to_dataframe()
            bs_df = financials.balance_sheet().to_dataframe()
            cf_df = financials.cashflow_statement().to_dataframe()

            logger.info(f"Retrieved financial statements for {ticker}")

            # Extract company information once
            company_info = self._extract_company_info(company)

            extracted_data = []
            date_cols = self._get_date_columns(is_df)[:years]
            
            # Check if we need older years (2023)
            needs_older_years = years > len(date_cols)
            
            # Extract from latest financials first
            for date_col in date_cols:
                try:
                    metrics = self._extract_metrics(
                        date_col,
                        is_df, bs_df, cf_df,
                        fallback_labels
                    )

                    metrics['Company'] = company_name
                    metrics['Ticker'] = ticker
                    metrics['Fiscal Year'] = date_col
                    
                    # Add company information for semantic search
                    metrics.update(company_info)

                    extracted_data.append(metrics)

                except Exception as e:
                    logger.warning(f"Error extracting metrics for {date_col}: {e}")
                    continue
            
            # Try to get older years from historical 10-K filings if needed
            if needs_older_years:
                logger.info(f"Attempting to extract older years for {ticker}...")
                try:
                    self._extract_older_years(company, ticker, company_name, company_info, 
                                            extracted_data, years - len(date_cols), fallback_labels)
                except Exception as e:
                    logger.warning(f"Could not extract older years for {ticker}: {e}")
            
            df = pd.DataFrame(extracted_data)
            logger.info(f"Successfully extracted {len(df)} records for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Extraction failed for {ticker}: {e}")
            return pd.DataFrame()

    def _validate_statements(self, financials) -> bool:
        try:
            return all([
                financials.income_statement() is not None,
                financials.balance_sheet() is not None,
                financials.cashflow_statement() is not None,
            ])
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def _get_date_columns(self, df: pd.DataFrame) -> List[str]:
        metadata_cols = {
            'concept', 'label', 'standard_concept', 'level', 'abstract',
            'dimension', 'is_breakdown', 'dimension_axis', 'dimension_member',
            'dimension_member_label', 'dimension_label', 'balance', 'weight',
            'preferred_sign', 'parent_concept', 'parent_abstract_concept'
        }
        return sorted(
            [col for col in df.columns if col not in metadata_cols],
            reverse=True
        )

    def _extract_metrics(
        self,
        date_col: str,
        is_df: pd.DataFrame,
        bs_df: pd.DataFrame,
        cf_df: pd.DataFrame,
        fallback_labels: bool = True
    ) -> Dict:
        metrics = {
            # Income Statement
            'Total Revenue': self._find_metric(is_df, 'revenue', date_col, fallback_labels),
            'COGS': self._find_metric(is_df, 'cogs', date_col, fallback_labels),
            'Gross Profit': self._find_metric(is_df, 'gross_profit', date_col, fallback_labels),
            'Operating Expenses': self._find_metric(is_df, 'operating_expenses', date_col, fallback_labels),
            'Operating Income': self._find_metric(is_df, 'operating_income', date_col, fallback_labels),
            'Net Income': self._find_metric(is_df, 'net_income', date_col, fallback_labels),
            
            # Balance Sheet
            'Total Assets': self._find_metric(bs_df, 'total_assets', date_col, fallback_labels),
            'Current Assets': self._find_metric(bs_df, 'current_assets', date_col, fallback_labels),
            'Long-term Assets': self._find_metric(bs_df, 'long_term_assets', date_col, fallback_labels),
            'Total Liabilities': self._find_metric(bs_df, 'total_liabilities', date_col, fallback_labels),
            'Current Liabilities': self._find_metric(bs_df, 'current_liabilities', date_col, fallback_labels),
            'Long-term Liabilities': self._find_metric(bs_df, 'long_term_liabilities', date_col, fallback_labels),
            'Long-term Debt': self._find_metric(bs_df, 'long_term_debt', date_col, fallback_labels),
            'Stockholders Equity': self._find_metric(bs_df, 'stockholders_equity', date_col, fallback_labels),
            
            # Cash Flow Statement
            'Operating Cash Flow': self._find_metric(cf_df, 'operating_cash_flow', date_col, fallback_labels),
            'Investing Cash Flow': self._find_metric(cf_df, 'investing_cash_flow', date_col, fallback_labels),
            'Financing Cash Flow': self._find_metric(cf_df, 'financing_cash_flow', date_col, fallback_labels),
        }
        return metrics

    def _find_metric(
        self,
        df: pd.DataFrame,
        metric: str,
        date_col: str,
        fallback_labels: bool = True
    ) -> Optional[float]:
        if metric not in self.XBRL_CONCEPTS:
            return None

        for concept in self.XBRL_CONCEPTS[metric]:
            rows = df[df['concept'] == concept]
            if len(rows) > 0:
                value = rows.iloc[0].get(date_col)
                if pd.notna(value):
                    return float(value)

        if fallback_labels:
            label_keywords = self._get_label_keywords(metric)
            for idx, row in df.iterrows():
                label = str(row.get('label', '')).lower()
                if all(kw in label for kw in label_keywords):
                    value = row.get(date_col)
                    if pd.notna(value):
                        return float(value)

        return None

    def _get_label_keywords(self, metric: str) -> List[str]:
        keywords_map = {
            # Income Statement
            'revenue': ['revenue', 'sales'],
            'cogs': ['cost', 'goods', 'sold'],
            'gross_profit': ['gross', 'profit'],
            'operating_expenses': ['operating', 'expenses'],
            'operating_income': ['operating', 'income'],
            'net_income': ['net', 'income'],
            
            # Balance Sheet
            'total_assets': ['total', 'assets'],
            'current_assets': ['current', 'assets'],
            'long_term_assets': ['noncurrent', 'assets'],
            'total_liabilities': ['total', 'liabilities'],
            'current_liabilities': ['current', 'liabilities'],
            'long_term_liabilities': ['noncurrent', 'liabilities'],
            'long_term_debt': ['long', 'term', 'debt'],
            'stockholders_equity': ['stockholders', 'equity'],
            
            # Cash Flow Statement
            'operating_cash_flow': ['operating', 'cash'],
            'investing_cash_flow': ['investing', 'cash'],
            'financing_cash_flow': ['financing', 'cash'],
        }
        return keywords_map.get(metric, [])
    
    def _extract_older_years(self, company, ticker: str, company_name: str, 
                            company_info: Dict, extracted_data: List, 
                            years_needed: int, fallback_labels: bool = True):
        """
        Extract older years (e.g., 2023) from historical 10-K filings.
        Tries to access financials from specific 10-K filing dates.
        """
        try:
            # Get historical 10-K filings (excluding amendments)
            filings = company.get_filings(form="10-K", amendments=False).latest(years_needed + 2)
            
            logger.info(f"Found {len(filings)} historical 10-K filings for {ticker}")
            
            # Skip the first filing (we already have its data)
            for filing in list(filings)[1:years_needed+1]:
                try:
                    # Try to get financials from this specific filing
                    financials = filing.get_financials()
                    
                    if not self._validate_statements(financials):
                        logger.warning(f"Incomplete statements for {ticker} filing {filing.filing_date}")
                        continue
                    
                    is_df = financials.income_statement().to_dataframe()
                    bs_df = financials.balance_sheet().to_dataframe()
                    cf_df = financials.cashflow_statement().to_dataframe()
                    
                    # Get the first (and usually only) date column for historical data
                    date_cols = self._get_date_columns(is_df)
                    if not date_cols:
                        continue
                    
                    date_col = date_cols[0]  # Most recent date in this filing
                    
                    metrics = self._extract_metrics(
                        date_col,
                        is_df, bs_df, cf_df,
                        fallback_labels
                    )
                    
                    if metrics:  # Only add if we got some data
                        metrics['Company'] = company_name
                        metrics['Ticker'] = ticker
                        metrics['Fiscal Year'] = date_col
                        metrics.update(company_info)
                        extracted_data.append(metrics)
                        logger.info(f"Extracted older year data from {filing.filing_date} for {ticker}")
                
                except Exception as e:
                    logger.warning(f"Could not extract from {filing.filing_date}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Could not access historical filings for {ticker}: {e}")


class ExtractionPipeline:

    def __init__(self, sec_identity: str, output_csv: Path):
        self.extractor = FinancialDataExtractor(sec_identity)
        self.output_csv = Path(output_csv)
        self.extracted_data = []

    def add_company(self, ticker: str, company_name: str, years: int = 3):
        df = self.extractor.extract_company(ticker, company_name, years)
        if not df.empty:
            self.extracted_data.append(df)
            logger.info(f"Added {company_name} to pipeline")
        else:
            logger.warning(f"No data extracted for {company_name}")

    def extract_batch(self, companies: List[Tuple[str, str]], years: int = 3):
        logger.info(f"Starting extraction for {len(companies)} companies")
        for ticker, name in companies:
            try:
                self.add_company(ticker, name, years)
            except Exception as e:
                logger.error(f"Failed to extract {ticker}: {e}")
                continue

    def save_csv(self) -> Path:
        if not self.extracted_data:
            logger.error("No data to save")
            return None

        df = pd.concat(self.extracted_data, ignore_index=True)

        if 'Fiscal Year' in df.columns:
            df['Fiscal Year'] = pd.to_datetime(df['Fiscal Year'])

        # Reorder columns logically: company info first, then dates, then metrics
        column_order = [
            # Company Information
            'Company', 'Ticker', 'Company Name', 'CIK', 'Industry', 'Business Category',
            'State of Incorporation', 'Phone', 'Address',
            # Dates
            'Fiscal Year',
            # Income Statement
            'Total Revenue', 'COGS', 'Gross Profit', 'Operating Expenses', 
            'Operating Income', 'Net Income',
            # Balance Sheet
            'Total Assets', 'Current Assets', 'Long-term Assets',
            'Total Liabilities', 'Current Liabilities', 'Long-term Liabilities',
            'Long-term Debt', 'Stockholders Equity',
            # Cash Flow
            'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow',
        ]
        
        # Only include columns that exist
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]

        self.output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_csv, index=False)

        logger.info(f"Saved {len(df)} records to {self.output_csv}")
        return self.output_csv

    def get_dataframe(self) -> pd.DataFrame:
        if not self.extracted_data:
            return pd.DataFrame()
        return pd.concat(self.extracted_data, ignore_index=True)


def main():
    SEC_IDENTITY = "KPATCHA Josue josuekpatcha1@gmail.com"
    OUTPUT_CSV = Path(__file__).parent.parent.parent / 'data' / 'financial_data_raw.csv'

    # 34 companies across multiple sectors
    companies = [
        # Tech Giants
        ('MSFT', 'Microsoft'),
        ('AAPL', 'Apple'),
        ('TSLA', 'Tesla'),
        ('GOOGL', 'Alphabet'),
        ('META', 'Meta Platforms'),
        ('NVDA', 'NVIDIA'),
        ('AMD', 'Advanced Micro Devices'),
        ('INTC', 'Intel'),
        ('CSCO', 'Cisco Systems'),
        ('ORCL', 'Oracle'),
        
        # Financials
        ('JPM', 'JPMorgan Chase'),
        ('BAC', 'Bank of America'),
        ('WFC', 'Wells Fargo'),
        ('GS', 'Goldman Sachs'),
        ('MS', 'Morgan Stanley'),
        
        # Consumer/Retail
        ('WMT', 'Walmart'),
        ('KO', 'Coca-Cola'),
        ('PEP', 'PepsiCo'),
        ('MCD', 'McDonald\'s'),
        ('TM', 'Toyota'),
        ('F', 'Ford'),
        ('GE', 'General Electric'),
        
        # Healthcare/Pharma
        ('JNJ', 'Johnson & Johnson'),
        ('PFE', 'Pfizer'),
        ('ABBV', 'AbbVie'),
        ('MRK', 'Merck'),
        ('LLY', 'Eli Lilly'),
        
        # Energy/Utilities
        ('XOM', 'ExxonMobil'),
        ('CVX', 'Chevron'),
        ('NEE', 'NextEra Energy'),
        ('SO', 'Southern Company'),
        
        # Industrial/Manufacturing
        ('BA', 'Boeing'),
        ('CAT', 'Caterpillar'),
        ('HON', 'Honeywell'),
        ('MMM', '3M'),
    ]

    pipeline = ExtractionPipeline(SEC_IDENTITY, OUTPUT_CSV)
    pipeline.extract_batch(companies, years=3)
    pipeline.save_csv()

    df = pipeline.get_dataframe()
    if not df.empty:
        # Ensure Fiscal Year is datetime
        if 'Fiscal Year' in df.columns and df['Fiscal Year'].dtype == 'object':
            df['Fiscal Year'] = pd.to_datetime(df['Fiscal Year'])
        
        print("\n" + "="*70)
        print("EXTRACTION SUMMARY")
        print("="*70)
        print(f"Total records: {len(df)}")
        print(f"Companies: {df['Ticker'].unique().tolist()}")
        print(f"Fiscal years: {sorted(df['Fiscal Year'].dt.year.unique())}")
        print(f"CSV saved to: {OUTPUT_CSV}")
        print("="*70)


if __name__ == '__main__':
    main()
