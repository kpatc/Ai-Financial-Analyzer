#!/usr/bin/env python3
"""
Vector Database Synchronization
Sync financial data from SQLite to ChromaDB for semantic search
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings

from config import CHROMA_CONFIG, SQLITE_CONFIG
from db_client import FinancialDBClient

logger = logging.getLogger(__name__)


class VectorSync:
    """Synchronize financial data to ChromaDB"""

    def __init__(self, db_path: str = None, chroma_path: str = None):
        """
        Initialize vector sync

        Args:
            db_path: Path to SQLite database
            chroma_path: Path to ChromaDB persistent storage
        """
        self.db_path = db_path or SQLITE_CONFIG['path']
        self.chroma_path = chroma_path or CHROMA_CONFIG['path']
        self.collection_name = CHROMA_CONFIG['collection_name']

        # Initialize ChromaDB client
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.chroma_path)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={'hnsw:space': 'cosine'}
        )

        logger.info(f"Vector sync initialized: {self.chroma_path}")

    def sync(self, force: bool = False) -> int:
        """
        Sync financial data to ChromaDB

        Args:
            force: Force re-sync even if collection has documents

        Returns:
            Number of documents synced
        """
        # Check if already synced
        count = self.collection.count()
        if count > 0 and not force:
            logger.info(f"ChromaDB already populated with {count} documents. Use force=True to re-sync.")
            return count

        if force and count > 0:
            logger.info(f"Force sync: clearing {count} existing documents")
            # Delete all documents in collection
            all_ids = self.collection.get()['ids']
            if all_ids:
                self.collection.delete(ids=all_ids)

        logger.info("Starting financial data sync to ChromaDB...")

        try:
            with FinancialDBClient(self.db_path) as db:
                companies = db.get_all_companies()
                total_docs = 0

                for company in companies:
                    ticker = company['ticker']
                    company_name = company['name']
                    sector = company.get('sector', 'Unknown')

                    # Get all years of data for this company
                    cursor = db.connection.cursor()
                    cursor.execute("""
                        SELECT fiscal_year FROM financial_metrics
                        WHERE company_id = ?
                        ORDER BY fiscal_year DESC
                    """, (company['id'],))

                    years = [row[0] for row in cursor.fetchall()]

                    for fiscal_year in years:
                        # Create document
                        doc = self._create_document(
                            db, ticker, company_name, sector, fiscal_year
                        )

                        if doc:
                            doc_id = f"{ticker}_{fiscal_year}"
                            metadata = {
                                'ticker': ticker,
                                'company_name': company_name,
                                'sector': sector,
                                'fiscal_year': str(fiscal_year),
                                'data_type': 'financial_metrics'
                            }

                            # Add to collection
                            self.collection.add(
                                ids=[doc_id],
                                documents=[doc],
                                metadatas=[metadata]
                            )

                            total_docs += 1

                logger.info(f"✓ Synced {total_docs} financial documents to ChromaDB")
                return total_docs

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            raise

    def _create_document(
        self, db: FinancialDBClient, ticker: str, company_name: str, sector: str, fiscal_year: int
    ) -> str:
        """
        Create a rich text document for a company-year

        Args:
            db: Database client
            ticker: Company ticker
            company_name: Company full name
            sector: Business sector
            fiscal_year: Fiscal year

        Returns:
            Document text or None
        """
        try:
            metrics = db.get_company_metrics(ticker, fiscal_year)
            if not metrics:
                return None

            ratios = db.get_ratios(ticker, fiscal_year)
            prof = db.get_profitability(ticker, fiscal_year)

            # Build document
            doc_lines = [
                f"Company: {company_name}",
                f"Ticker: {ticker}",
                f"Sector: {sector}",
                f"Fiscal Year: {fiscal_year}",
                "",
                "FINANCIAL METRICS:",
            ]

            # Revenue and profitability
            revenue_b = metrics.get('revenue', 0) / 1e9 if metrics.get('revenue') else None
            net_income_b = metrics.get('net_income', 0) / 1e9 if metrics.get('net_income') else None
            gross_profit_b = metrics.get('gross_profit', 0) / 1e9 if metrics.get('gross_profit') else None
            operating_income_b = metrics.get('operating_income', 0) / 1e9 if metrics.get('operating_income') else None

            if revenue_b:
                doc_lines.append(f"Total Revenue: ${revenue_b:.2f}B")
            if gross_profit_b:
                doc_lines.append(f"Gross Profit: ${gross_profit_b:.2f}B")
            if operating_income_b:
                doc_lines.append(f"Operating Income: ${operating_income_b:.2f}B")
            if net_income_b:
                doc_lines.append(f"Net Income: ${net_income_b:.2f}B")

            # Balance sheet
            doc_lines.append("")
            total_assets_b = metrics.get('total_assets', 0) / 1e9 if metrics.get('total_assets') else None
            total_liab_b = metrics.get('total_liabilities', 0) / 1e9 if metrics.get('total_liabilities') else None
            equity_b = metrics.get('stockholders_equity', 0) / 1e9 if metrics.get('stockholders_equity') else None

            if total_assets_b:
                doc_lines.append(f"Total Assets: ${total_assets_b:.2f}B")
            if total_liab_b:
                doc_lines.append(f"Total Liabilities: ${total_liab_b:.2f}B")
            if equity_b:
                doc_lines.append(f"Stockholders' Equity: ${equity_b:.2f}B")

            # Cash flow
            doc_lines.append("")
            ocf = metrics.get('operating_cash_flow', 0) / 1e9 if metrics.get('operating_cash_flow') else None
            if ocf:
                doc_lines.append(f"Operating Cash Flow: ${ocf:.2f}B")

            # Profitability margins
            if prof:
                doc_lines.append("")
                doc_lines.append("PROFITABILITY:")
                if prof.get('gross_margin_pct'):
                    doc_lines.append(f"Gross Margin: {prof['gross_margin_pct']:.2f}%")
                if prof.get('operating_margin_pct'):
                    doc_lines.append(f"Operating Margin: {prof['operating_margin_pct']:.2f}%")
                if prof.get('net_margin_pct'):
                    doc_lines.append(f"Net Profit Margin: {prof['net_margin_pct']:.2f}%")

            # Financial ratios
            if ratios:
                doc_lines.append("")
                doc_lines.append("FINANCIAL RATIOS:")

                if ratios.get('current_ratio'):
                    doc_lines.append(f"Current Ratio: {ratios['current_ratio']:.2f}")

                if ratios.get('debt_to_equity') is not None:
                    doc_lines.append(f"Debt-to-Equity: {ratios['debt_to_equity']:.2f}")
                if ratios.get('debt_to_assets'):
                    doc_lines.append(f"Debt-to-Assets: {ratios['debt_to_assets']:.2f}")

                if ratios.get('roa_pct'):
                    doc_lines.append(f"Return on Assets (ROA): {ratios['roa_pct']:.2f}%")
                if ratios.get('roe_pct'):
                    doc_lines.append(f"Return on Equity (ROE): {ratios['roe_pct']:.2f}%")

                if ratios.get('asset_turnover'):
                    doc_lines.append(f"Asset Turnover: {ratios['asset_turnover']:.2f}")
                if ratios.get('ocf_to_liabilities'):
                    doc_lines.append(f"OCF to Liabilities: {ratios['ocf_to_liabilities']:.2f}")

                if ratios.get('free_cash_flow'):
                    fcf_b = ratios['free_cash_flow'] / 1e9
                    doc_lines.append(f"Free Cash Flow: ${fcf_b:.2f}B")

            return "\n".join(doc_lines)

        except Exception as e:
            logger.error(f"Error creating document for {ticker} {fiscal_year}: {e}")
            return None

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection

        Returns:
            Stats dict {count, companies, sectors, ...}
        """
        count = self.collection.count()

        # Get unique companies and sectors from metadata
        if count > 0:
            data = self.collection.get()
            companies = set([m.get('company_name', 'Unknown') for m in data.get('metadatas', [])])
            sectors = set([m.get('sector', 'Unknown') for m in data.get('metadatas', [])])
            years = set([m.get('fiscal_year', 'Unknown') for m in data.get('metadatas', [])])

            return {
                'total_documents': count,
                'companies': len(companies),
                'sectors': len(sectors),
                'fiscal_years': len(years),
                'collection_name': self.collection_name,
            }

        return {'total_documents': 0}

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search ChromaDB for relevant documents

        Args:
            query: Search query string
            n_results: Number of results to return

        Returns:
            List of result dicts {doc, metadata, distance}
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )

            output = []
            if results and results['documents']:
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    output.append({
                        'document': doc,
                        'metadata': meta,
                        'distance': dist,
                        'similarity': 1 - dist,  # Convert distance to similarity
                    })

            return output

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


def ensure_vector_db_synced(force: bool = False) -> int:
    """
    Ensure ChromaDB is populated with financial data

    Args:
        force: Force re-sync if already populated

    Returns:
        Number of documents in ChromaDB
    """
    syncer = VectorSync()
    count = syncer.sync(force=force)
    return count


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Sync and show stats
    syncer = VectorSync()
    count = syncer.sync()
    stats = syncer.get_collection_stats()
    print(f"\n✓ Sync complete!")
    print(f"Statistics: {stats}")
