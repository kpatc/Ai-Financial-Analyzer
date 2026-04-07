#!/usr/bin/env python3
"""
RAG Engine - Retrieval Augmented Generation
Hybrid approach: ChromaDB semantic search + SQLite precise queries + LLM (Gemini or Groq)
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

import google.generativeai as genai
from groq import Groq

from config import GEMINI_CONFIG, GROQ_CONFIG, LLM_PROVIDER, QUERY_CATEGORIES, SYSTEM_PROMPT, SQLITE_CONFIG, CHROMA_CONFIG
from db_client import FinancialDBClient
from vector_sync import VectorSync
from response_formatter import ResponseFormatter, format_comparison_insights

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    RAG Engine combining semantic and precise retrieval with Gemini LLM
    """

    def __init__(self, db_path: str = None, chroma_path: str = None):
        """
        Initialize RAG engine

        Args:
            db_path: Path to SQLite database
            chroma_path: Path to ChromaDB
        """
        # Initialize LLM based on provider
        self.llm_provider = LLM_PROVIDER
        logger.info(f"Initializing RAG Engine with LLM provider: {self.llm_provider}")

        if self.llm_provider == 'groq':
            if not GROQ_CONFIG.get('api_key'):
                raise ValueError("GROQ_API_KEY environment variable not set")
            self.groq_client = Groq(api_key=GROQ_CONFIG['api_key'])
            self.model = None
        else:  # gemini (default)
            if not GEMINI_CONFIG.get('api_key'):
                raise ValueError("GEMINI_API_KEY environment variable not set")
            genai.configure(api_key=GEMINI_CONFIG['api_key'])
            self.model = genai.GenerativeModel(
                model_name=GEMINI_CONFIG['model'],
                system_instruction=SYSTEM_PROMPT
            )
            self.groq_client = None

        # Initialize databases
        self.db_path = db_path or SQLITE_CONFIG['path']
        self.chroma_path = chroma_path
        # Note: Don't create db connection here - create per-request to avoid threading issues
        self.vector_sync = VectorSync(self.db_path, chroma_path)

        # Cache for companies
        self._companies_cache = None
        self._tickers_cache = None
        self._company_name_to_ticker = None

        logger.info("RAG engine initialized")

    def _get_db(self):
        """Get a fresh database connection for the current thread"""
        return FinancialDBClient(self.db_path)

    def close(self):
        """Close database connections"""
        pass  # DB connections are per-thread, no need to close

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========================================================================
    # ENTITY DETECTION
    # ========================================================================

    def _get_all_tickers(self) -> List[str]:
        """Get cached list of all tickers"""
        if self._tickers_cache is None:
            companies = self._get_db().get_all_companies()
            self._tickers_cache = [c['ticker'] for c in companies]
        return self._tickers_cache

    def _get_company_mapping(self) -> Dict[str, str]:
        """Get mapping of company names/keywords to tickers"""
        if self._company_name_to_ticker is None:
            self._company_name_to_ticker = {}
            companies = self._get_db().get_all_companies()
            for company in companies:
                ticker = company['ticker']
                name = company['name']
                name_lower = name.lower()

                # Add ticker (both cases)
                self._company_name_to_ticker[ticker.lower()] = ticker
                self._company_name_to_ticker[ticker] = ticker

                # Add full company name
                self._company_name_to_ticker[name_lower] = ticker

                # Add name without Inc., Corp., etc.
                clean_name = name_lower.replace(' inc.', '').replace(' corp.', '').replace(' co.', '').replace(' co', '').strip()
                if clean_name != name_lower:
                    self._company_name_to_ticker[clean_name] = ticker

                # Add first word of company name
                first_word = name_lower.split()[0]
                self._company_name_to_ticker[first_word] = ticker

                # Add specific keywords
                if 'apple' in name_lower:
                    self._company_name_to_ticker['apple'] = ticker
                if 'microsoft' in name_lower:
                    self._company_name_to_ticker['microsoft'] = ticker
                if 'google' in name_lower:
                    self._company_name_to_ticker['google'] = ticker
                if 'meta' in name_lower:
                    self._company_name_to_ticker['meta'] = ticker
                if 'amazon' in name_lower:
                    self._company_name_to_ticker['amazon'] = ticker

        return self._company_name_to_ticker

    def detect_entities(self, query: str) -> Dict[str, Any]:
        """
        Detect tickers, metrics, and categories in query

        Args:
            query: User query string

        Returns:
            Dict {tickers: [], category: str, metrics: [], time_period: str}
        """
        query_lower = query.lower()
        entities = {
            'tickers': [],
            'category': None,
            'metrics': [],
            'time_period': 'latest'
        }

        # Detect tickers (by name or symbol)
        company_mapping = self._get_company_mapping()
        for name_or_ticker, ticker in company_mapping.items():
            if name_or_ticker in query_lower:
                entities['tickers'].append(ticker)

        # Detect category (highest priority keyword match)
        max_score = 0
        best_category = None

        for category, config in QUERY_CATEGORIES.items():
            score = 0
            for keyword in config['keywords']:
                if keyword.lower() in query_lower:
                    score += 1

            if score > max_score:
                max_score = score
                best_category = category

        if best_category:
            entities['category'] = best_category

        # Detect time period
        if any(word in query_lower for word in ['latest', 'recent', 'current', 'now']):
            entities['time_period'] = 'latest'
        elif any(word in query_lower for word in ['trend', 'growth', 'history', 'over time']):
            entities['time_period'] = 'trend'
        elif 'previous' in query_lower or 'last' in query_lower:
            entities['time_period'] = 'historical'

        # Remove duplicates
        entities['tickers'] = list(set(entities['tickers']))

        return entities

    # ========================================================================
    # RETRIEVAL
    # ========================================================================

    def retrieve_semantic(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve semantically relevant documents from ChromaDB

        Args:
            query: Search query
            n_results: Number of results

        Returns:
            List of relevant document dicts
        """
        try:
            results = self.vector_sync.search(query, n_results=n_results)
            logger.debug(f"Semantic search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def retrieve_precise(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve precise data from SQLite based on detected entities

        Args:
            entities: Detected entities {tickers, category, time_period}

        Returns:
            Dict with precise financial data
        """
        precise_data = {
            'companies_data': [],
            'comparisons': None,
            'rankings': None
        }

        tickers = entities.get('tickers', [])
        category = entities.get('category')

        # If specific tickers mentioned, get their data
        if tickers:
            for ticker in tickers:
                # Get all years of financial data for trend analysis
                company_info = self._get_db().get_company_by_ticker(ticker)
                if company_info:
                    company_data = {
                        'ticker': ticker,
                        'company_name': company_info['name'],
                        'sector': company_info.get('sector'),
                        'metrics': {}
                    }

                    # Get revenue trends (multiple years)
                    trends = self._get_db().get_revenue_trend(ticker, years=3)
                    for trend in reversed(trends):  # Reverse to get chronological order
                        # Extract year from fiscal_year (could be date string like '2025-09-27' or just year)
                        fiscal_year_str = str(trend['fiscal_year'])
                        year = fiscal_year_str[:4]  # Extract first 4 chars (YYYY)

                        company_data['metrics'][year] = {
                            'revenue_billions': (trend['revenue'] / 1e9) if trend.get('revenue') else 0,
                            'net_income_billions': (trend['net_income'] / 1e9) if trend.get('net_income') else 0,
                            'operating_cash_flow_billions': (trend['operating_cash_flow'] / 1e9) if trend.get('operating_cash_flow') else 0,
                            'total_assets_billions': (trend['total_assets'] / 1e9) if trend.get('total_assets') else 0,
                            'total_liabilities_billions': (trend['total_liabilities'] / 1e9) if trend.get('total_liabilities') else 0,
                        }

                    # Add ratios and profitability (latest year)
                    ratios = self._get_db().get_ratios(ticker)
                    prof = self._get_db().get_profitability(ticker)
                    yoy = self._get_db().get_yoy_growth(ticker)

                    company_data['ratios'] = ratios
                    company_data['profitability'] = prof
                    company_data['yoy_growth'] = yoy
                    precise_data['companies_data'].append(company_data)

            # If multiple companies, add comparison
            if len(tickers) > 1:
                precise_data['comparisons'] = self._get_db().get_comparison(tickers)

        # If category is specified, get rankings/relevant data for that category
        if category == 'revenue' and not tickers:
            precise_data['rankings'] = self._get_db().get_rankings('revenue', top_n=5)
        elif category == 'profitability' and not tickers:
            # Get top companies by net margin
            all_companies = self._get_db().get_all_companies()
            profiles = []
            for c in all_companies:
                prof = self._get_db().get_profitability(c['ticker'])
                if prof and prof.get('net_margin_pct'):
                    profiles.append({
                        'ticker': c['ticker'],
                        'company': c['name'],
                        'net_margin_pct': prof['net_margin_pct']
                    })
            profiles.sort(key=lambda x: x['net_margin_pct'], reverse=True)
            precise_data['rankings'] = profiles[:5]

        return precise_data

    # ========================================================================
    # CONTEXT BUILDING
    # ========================================================================

    def build_context(
        self,
        semantic_docs: List[Dict[str, Any]],
        precise_data: Dict[str, Any],
        entities: Dict[str, Any]
    ) -> str:
        """
        Build structured context for LLM prompt

        Args:
            semantic_docs: Documents from ChromaDB
            precise_data: Precise data from SQLite
            entities: Detected entities

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add semantic context
        if semantic_docs:
            context_parts.append("RELEVANT FINANCIAL DATA (from similar queries):")
            for i, doc in enumerate(semantic_docs[:3], 1):
                meta = doc.get('metadata', {})
                similarity = doc.get('similarity', 0)
                context_parts.append(f"\n[Source {i}, Similarity: {similarity:.2%}]")
                context_parts.append(doc.get('document', ''))

        # Add precise data
        if precise_data.get('companies_data'):
            context_parts.append("\nPRECISE FINANCIAL METRICS:")
            for company in precise_data['companies_data']:
                ticker = company.get('ticker', '?')
                context_parts.append(f"\n{ticker} Financial Data:")

                # Metrics
                context_parts.append(f"  Revenue: ${company.get('revenue', 0) / 1e9:.2f}B")
                context_parts.append(f"  Net Income: ${company.get('net_income', 0) / 1e9:.2f}B")
                context_parts.append(f"  Total Assets: ${company.get('total_assets', 0) / 1e9:.2f}B")

                # Ratios
                if company.get('ratios'):
                    ratios = company['ratios']
                    context_parts.append(f"  Debt-to-Equity: {ratios.get('debt_to_equity', 'N/A'):.2f}")
                    context_parts.append(f"  ROA: {ratios.get('roa_pct', 'N/A'):.2f}%")

                # Profitability
                if company.get('profitability'):
                    prof = company['profitability']
                    context_parts.append(f"  Net Margin: {prof.get('net_margin_pct', 'N/A'):.2f}%")

                # YoY Growth
                if company.get('yoy_growth'):
                    yoy = company['yoy_growth']
                    context_parts.append(f"  Revenue YoY Growth: {yoy.get('revenue_yoy_pct', 'N/A'):.2f}%")

        if precise_data.get('comparisons'):
            context_parts.append("\nCOMPARISON DATA:")
            for comp in precise_data['comparisons']:
                context_parts.append(f"  {comp['ticker']}: Revenue ${comp.get('revenue_billions', 0):.2f}B, Net Income ${comp.get('net_income_billions', 0):.2f}B")

        if precise_data.get('rankings'):
            context_parts.append("\nRANKINGS:")
            for item in precise_data['rankings'][:5]:
                if 'value' in item:
                    context_parts.append(f"  {item['ticker']}: {item['value']:.2f}")
                elif 'net_margin_pct' in item:
                    context_parts.append(f"  {item['ticker']}: {item['net_margin_pct']:.2f}%")

        return "\n".join(context_parts)

    # ========================================================================
    # LLM GENERATION
    # ========================================================================

    def generate(self, query: str, context: str, history: List[Dict] = None) -> str:
        """
        Generate response using LLM (Gemini or Groq)

        Args:
            query: User question
            context: RAG context
            history: Conversation history

        Returns:
            LLM response text
        """
        # Build the prompt
        full_prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
{context}

USER QUESTION:
{query}

Please provide a clear, analytical response based on the financial data provided above."""

        try:
            if self.llm_provider == 'groq':
                return self._generate_groq(full_prompt, history)
            else:
                return self._generate_gemini(full_prompt, history)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error generating response: {str(e)}"

    def _generate_gemini(self, prompt: str, history: List[Dict] = None) -> str:
        """Generate response using Gemini"""
        messages = []

        # Add recent history
        if history:
            for msg in history[-3:]:
                messages.append({
                    'role': 'user' if msg.get('role') == 'user' else 'model',
                    'parts': [msg.get('content', '')]
                })

        messages.append({'role': 'user', 'parts': [prompt]})

        response = self.model.generate_content(
            messages,
            generation_config=genai.types.GenerationConfig(
                temperature=GEMINI_CONFIG.get('temperature', 0.7),
                max_output_tokens=GEMINI_CONFIG.get('max_output_tokens', 1000),
                top_p=GEMINI_CONFIG.get('top_p', 0.95),
            )
        )

        text = response.text if response else "Unable to generate response"
        logger.debug(f"Generated response ({len(text)} chars)")
        return text

    def _generate_groq(self, prompt: str, history: List[Dict] = None) -> str:
        """Generate response using Groq"""
        messages = []

        # Add system message
        messages.append({'role': 'system', 'content': SYSTEM_PROMPT})

        # Add recent history
        if history:
            for msg in history[-3:]:
                messages.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                })

        # Add current prompt
        messages.append({'role': 'user', 'content': prompt})

        response = self.groq_client.chat.completions.create(
            model=GROQ_CONFIG.get('model', 'mixtral-8x7b-32768'),
            messages=messages,
            temperature=GROQ_CONFIG.get('temperature', 0.7),
            max_tokens=GROQ_CONFIG.get('max_tokens', 1000),
        )

        text = response.choices[0].message.content if response.choices else "Unable to generate response"
        logger.debug(f"Generated response ({len(text)} chars)")
        return text

    # ========================================================================
    # CHART GENERATION
    # ========================================================================

    def generate_chart_config(self, query: str, category: str, entities: Dict, precise_data: Dict) -> Dict:
        """
        Use LLM to analyze query and generate structured chart configuration

        Args:
            query: Original user question
            category: Detected category (revenue, profitability, etc)
            entities: Detected entities (tickers, time_period)
            precise_data: Retrieved financial data

        Returns:
            {type, tickers, years, metrics, title} or None
        """
        tickers = entities.get('tickers', [])
        logger.info(f"generate_chart_config called: query={query[:50]}, tickers={tickers}, category={category}")
        if not tickers:
            logger.warning(f"No tickers found for chart generation")
            return None

        # Build data summary for LLM to analyze
        data_summary = self._build_chart_data_summary(tickers, precise_data)

        # Create a structured prompt for the LLM
        chart_prompt = f"""Analyze this user query and the available financial data, then generate a precise chart configuration JSON.

USER QUERY: {query}
CATEGORY: {category}
AVAILABLE COMPANIES: {', '.join(tickers)}

DATA AVAILABLE:
{data_summary}

Generate a JSON configuration for the best chart to visualize this data. Respond ONLY with valid JSON (no markdown, no explanation).

Format: {{"type": "line|bar|radar", "title": "Chart Title with Years", "metrics": ["metric1", "metric2"], "years": [2023, 2024, 2025]}}

Rules:
- type: "line" for trends, "bar" for comparison, "radar" for ratios
- title: Must include years/period from the data and company name
- metrics: List specific metrics to show (revenue, profit, margin, etc)
- years: List EXACT years available in the data (not just current year!)

For trend analysis, include ALL years: [2023, 2024, 2025]
For comparisons between companies, include both tickers in title"""

        try:
            if self.llm_provider == 'groq':
                response = self.groq_client.chat.completions.create(
                    model=GROQ_CONFIG.get('model', 'llama-3.3-70b-versatile'),
                    messages=[
                        {'role': 'system', 'content': 'You are a financial data visualization expert. Generate precise chart configs as JSON.'},
                        {'role': 'user', 'content': chart_prompt}
                    ],
                    temperature=0.3,  # Low temp for structured output
                    max_tokens=500,
                )
                config_json = response.choices[0].message.content
            else:
                response = self.model.generate_content(
                    chart_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=500,
                    )
                )
                config_json = response.text

            logger.debug(f"LLM response (first 300 chars): {config_json[:300]}")

            # Parse and build the chart data
            config = json.loads(config_json.strip())
            logger.debug(f"Parsed config: {config}")

            # Build actual chart data based on config
            logger.debug(f"Building chart data: type={config.get('type')}, metrics={config.get('metrics')}, years={config.get('years')}")
            chart_data = self._build_chart_data(
                chart_type=config.get('type', 'line'),
                tickers=tickers,
                metrics=config.get('metrics', []),
                years=config.get('years', []),
                precise_data=precise_data
            )

            logger.debug(f"chart_data returned from _build_chart_data: {chart_data is not None}, type={type(chart_data)}")
            if not chart_data:
                logger.warning(f"chart_data is None/empty after building")
                return None

            logger.debug(f"Chart data built successfully, data keys: {chart_data.keys() if isinstance(chart_data, dict) else 'N/A'}")
            result = {
                'type': config.get('type', 'line'),
                'title': config.get('title', f'{category.title()} - {", ".join(tickers)}'),
                'data': chart_data,
            }
            logger.debug(f"Returning chart config with data: result={result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from LLM chart config: {e}. Raw: {config_json[:200]}")
            # Fallback: Generate simple chart config based on category
            return self._fallback_chart_config(tickers, category, precise_data)
        except Exception as e:
            logger.error(f"Chart config generation failed: {e}", exc_info=True)
            # Fallback: Generate simple chart config
            return self._fallback_chart_config(tickers, category, precise_data)

    def _enhance_precise_data_from_semantic(self, precise_data: Dict, semantic_docs: List[Dict], tickers: List[str]) -> Dict:
        """
        Enhance precise_data with financial metrics extracted from semantic documents

        Args:
            precise_data: Base precise data from SQLite
            semantic_docs: Semantic search results with financial data
            tickers: Target tickers

        Returns:
            Enhanced precise_data with multi-year metrics from semantic docs
        """
        # Build a map of year data from semantic docs
        year_data_map = {}  # {ticker: {year: {metrics}}}

        for doc in semantic_docs:
            metadata = doc.get('metadata', {})
            ticker = metadata.get('ticker')
            if ticker not in tickers:
                continue

            # Extract financial metrics from document content
            content = doc.get('document', '')

            # Try to extract fiscal year from metadata
            fiscal_year_str = metadata.get('fiscal_year', '')
            if fiscal_year_str:
                # Extract year (e.g., '2025-09-27' -> '2025' or '2025' -> '2025')
                year = fiscal_year_str[:4]
            else:
                continue

            # Extract revenue, net income, total assets from content
            import re
            revenue_match = re.search(r'Total Revenue.*?\$?\s*([\d.]+)\s*B', content)
            net_income_match = re.search(r'Net Income.*?\$?\s*([\d.]+)\s*B', content)
            total_assets_match = re.search(r'Total Assets.*?\$?\s*([\d.]+)\s*B', content)

            if not year_data_map.get(ticker):
                year_data_map[ticker] = {}

            year_metrics = {}
            if revenue_match:
                year_metrics['revenue_billions'] = float(revenue_match.group(1))
            if net_income_match:
                year_metrics['net_income_billions'] = float(net_income_match.group(1))
            if total_assets_match:
                year_metrics['total_assets_billions'] = float(total_assets_match.group(1))

            if year_metrics:
                year_data_map[ticker][year] = year_metrics

        # Merge semantic data into precise_data
        for company_data in precise_data.get('companies_data', []):
            ticker = company_data.get('ticker')
            if ticker in year_data_map:
                # Merge years (semantic data might have more years)
                if 'metrics' not in company_data:
                    company_data['metrics'] = {}
                for year, metrics in year_data_map[ticker].items():
                    if year not in company_data['metrics']:
                        company_data['metrics'][year] = metrics
                    else:
                        # Enhance with additional metrics from semantic docs
                        company_data['metrics'][year].update(metrics)

        return precise_data

    def _build_chart_data_summary(self, tickers: List[str], precise_data: Dict) -> str:
        """Build a summary of available data for the LLM"""
        summary = []

        for company in precise_data.get('companies_data', []):
            ticker = company.get('ticker')
            if ticker in tickers:
                summary.append(f"\n{ticker}:")
                if company.get('metrics'):
                    metrics = company['metrics']
                    summary.append(f"  Years available: {list(metrics.keys())}")
                    for year, data in metrics.items():
                        summary.append(f"    {year}: Revenue {data.get('revenue_billions')}B, Net Income {data.get('net_income_billions')}B")

        return '\n'.join(summary)

    def _build_chart_data(self, chart_type: str, tickers: List[str], metrics: List[str], years: List[int], precise_data: Dict) -> Dict:
        """Build Recharts-compatible data from financial data"""
        try:
            if chart_type == 'line':
                return self._build_line_chart(tickers, metrics, years, precise_data)
            elif chart_type == 'bar':
                return self._build_bar_chart(tickers, metrics, years, precise_data)
            elif chart_type == 'radar':
                return self._build_radar_chart(tickers, metrics, precise_data)
        except Exception as e:
            logger.error(f"Chart data building failed: {e}")
        return None

    def _build_line_chart(self, tickers: List[str], metrics: List[str], years: List[int], precise_data: Dict) -> Dict:
        """Build line chart data for trends"""
        chart_data = []
        datasets = []
        metric_colors = {
            'revenue': '#6366f1',
            'net_income': '#10b981',
            'profit_margin': '#f59e0b',
            'operating_margin': '#ec4899',
        }

        logger.debug(f"_build_line_chart: tickers={tickers}, metrics={metrics}, years={years}")
        logger.debug(f"_build_line_chart: companies_data count={len(precise_data.get('companies_data', []))}")

        for ticker in tickers:
            company_data = next((c for c in precise_data.get('companies_data', []) if c['ticker'] == ticker), None)
            if not company_data:
                logger.debug(f"No company data found for {ticker}")
                continue

            metrics_data = company_data.get('metrics', {})
            logger.debug(f"Company {ticker} has metrics for years: {list(metrics_data.keys())}")

            for i, year in enumerate(years):
                year_str = str(year)
                if year_str not in metrics_data:
                    logger.debug(f"Year {year_str} not in metrics for {ticker}")
                    continue

                if i >= len(chart_data):
                    chart_data.append({'name': year})

                year_metrics = metrics_data[year_str]
                logger.debug(f"Year {year_str} metrics: {year_metrics}")

                for metric in metrics:
                    metric_key = metric.lower().replace(' ', '_')
                    if metric_key == 'revenue':
                        value = year_metrics.get('revenue_billions', 0)
                    elif metric_key == 'net_income':
                        value = year_metrics.get('net_income_billions', 0)
                    else:
                        value = year_metrics.get(metric_key, 0)

                    label = f"{ticker} {metric}"
                    chart_data[i][label] = value
                    logger.debug(f"Set {label} = {value}")

        logger.debug(f"chart_data after loop: {chart_data}")

        # Add datasets
        seen_labels = set()
        for data_point in chart_data:
            for key, value in data_point.items():
                if key != 'name' and key not in seen_labels and isinstance(value, (int, float)):
                    seen_labels.add(key)
                    ticker = key.split()[0]
                    color = metric_colors.get(metrics[0].lower().replace(' ', '_'), '#6366f1')
                    datasets.append({
                        'label': key,
                        'data': [d.get(key, 0) for d in chart_data],
                        'borderColor': color,
                        'backgroundColor': color + '22',
                        'tension': 0.4,
                        'fill': True,
                    })

        result = {
            'labels': [str(d['name']) for d in chart_data],
            'datasets': datasets,
        }
        logger.debug(f"_build_line_chart returning: {result}")
        return result

    def _build_bar_chart(self, tickers: List[str], metrics: List[str], years: List[int], precise_data: Dict) -> Dict:
        """Build bar chart for comparisons"""
        chart_data = []

        for ticker in tickers:
            company_data = next((c for c in precise_data.get('companies_data', []) if c['ticker'] == ticker), None)
            if not company_data:
                continue

            metrics_data = company_data.get('metrics', {})
            latest_year = max([int(y) for y in metrics_data.keys() if y.isdigit()], default=None)

            if latest_year:
                year_metrics = metrics_data.get(str(latest_year), {})
                value = year_metrics.get('revenue_billions', 0) if metrics and 'revenue' in metrics[0].lower() else year_metrics.get('net_income_billions', 0)
                chart_data.append({'name': ticker, 'value': value})

        if not chart_data:
            return None

        return {
            'labels': [d['name'] for d in chart_data],
            'datasets': [{
                'label': 'Revenue (B$)',
                'data': [d['value'] for d in chart_data],
                'backgroundColor': '#6366f1',
            }]
        }

    def _fallback_chart_config(self, tickers: List[str], category: str, precise_data: Dict) -> Dict:
        """Fallback chart generation if LLM fails"""
        try:
            # Determine years from data
            years = set()
            for company in precise_data.get('companies_data', []):
                if company['ticker'] in tickers:
                    metrics_data = company.get('metrics', {})
                    years.update(int(y) for y in metrics_data.keys() if y.isdigit())

            years = sorted(list(years))[-3:] if years else [2023, 2024, 2025]  # Last 3 years

            # Simple chart based on category
            if category == 'revenue' or 'revenue' in category.lower():
                chart_type = 'line'
                metrics = ['revenue', 'net_income']
            elif category == 'profitability' or 'margin' in category.lower():
                chart_type = 'bar'
                metrics = ['profit_margin']
            else:
                chart_type = 'bar'
                metrics = ['revenue']

            chart_data = self._build_chart_data(
                chart_type=chart_type,
                tickers=tickers,
                metrics=metrics,
                years=years,
                precise_data=precise_data
            )

            if not chart_data:
                return None

            return {
                'type': chart_type,
                'title': f'{category.title()} Trend - {", ".join(tickers)} ({min(years)}-{max(years)})',
                'data': chart_data,
            }
        except Exception as e:
            logger.error(f"Fallback chart generation failed: {e}")
            return None

    def _build_radar_chart(self, tickers: List[str], metrics: List[str], precise_data: Dict) -> Dict:
        """Build radar chart for ratios/metrics"""
        company_data = next((c for c in precise_data.get('companies_data', []) if c['ticker'] in tickers), None)
        if not company_data:
            return None

        ratios = company_data.get('ratios', {})
        if not ratios:
            return None

        latest_year = max([int(y) for y in ratios.keys() if y.isdigit()], default=None)
        if not latest_year:
            return None

        year_ratios = ratios.get(str(latest_year), {})

        return {
            'labels': list(year_ratios.keys())[:6],
            'datasets': [{
                'label': tickers[0],
                'data': list(year_ratios.values())[:6],
                'borderColor': '#6366f1',
                'backgroundColor': '#6366f122',
            }]
        }

    # ========================================================================
    # PIPELINE
    # ========================================================================

    def process(
        self,
        query: str,
        history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: detect entities → retrieve → generate

        Args:
            query: User question
            history: Conversation history

        Returns:
            {response, sources, category, chart_hint}
        """
        if not query or len(query) > 500:
            return {
                'response': 'Query too long. Please keep it under 500 characters.',
                'sources': [],
                'category': None,
                'chart_hint': None
            }

        # Detect entities
        entities = self.detect_entities(query)
        logger.debug(f"Detected entities: {entities}")

        # Retrieve documents
        semantic_docs = self.retrieve_semantic(query, n_results=3)
        precise_data = self.retrieve_precise(entities)

        # Build context
        context = self.build_context(semantic_docs, precise_data, entities)

        # Generate response
        response_text = self.generate(query, context, history)

        # Extract sources
        sources = []
        for doc in semantic_docs[:2]:
            meta = doc.get('metadata', {})
            sources.append({
                'ticker': meta.get('ticker'),
                'company': meta.get('company_name'),
                'fiscal_year': meta.get('fiscal_year'),
                'source_type': meta.get('data_type')
            })

        for company in precise_data.get('companies_data', []):
            sources.append({
                'ticker': company.get('ticker'),
                'company': company.get('company_name'),
                'fiscal_year': company.get('fiscal_year'),
                'source_type': 'precise_metrics'
            })

        # Remove duplicates
        seen = set()
        unique_sources = []
        for s in sources:
            key = (s['ticker'], s['fiscal_year'])
            if key not in seen:
                unique_sources.append(s)
                seen.add(key)

        # Determine chart config (LLM-generated)
        category = entities.get('category')
        tickers = entities.get('tickers', [])
        chart_config = None
        table_data = None

        logger.debug(f"Chart generation: category={category}, tickers={tickers}")

        # Only generate chart if we have tickers and a category
        if category and tickers:
            logger.debug(f"Generating chart config for {tickers}")
            # Enhance precise_data with semantic doc metadata for multi-year data
            enhanced_precise_data = self._enhance_precise_data_from_semantic(
                precise_data, semantic_docs, tickers
            )
            chart_config = self.generate_chart_config(
                query=query,
                category=category,
                entities=entities,
                precise_data=enhanced_precise_data
            )
            logger.debug(f"Chart config generated: {bool(chart_config)}")

            # Add structured table data for comparisons
            if len(tickers) > 1:
                try:
                    comparison = self._get_db().get_comparison(tickers, include_all_ratios=True)
                    if comparison:
                        table_data = {
                            'type': 'comparison',
                            'data': comparison,
                            'columns': ['ticker', 'name', 'sector', 'revenue_billions', 'net_income_billions',
                                       'net_margin_pct', 'debt_to_equity', 'roa_pct']
                        }
                except Exception as e:
                    logger.debug(f"Table data generation failed: {e}")
        else:
            logger.debug(f"Skipping chart: category={bool(category)}, tickers={bool(tickers)}")

        return {
            'response': response_text,
            'sources': unique_sources,
            'category': category,
            'chart': chart_config,  # Changed from chart_hint to chart
            'table': table_data,
            'entities': entities
        }


def get_rag_engine(db_path: str = None, chroma_path: str = None) -> RAGEngine:
    """
    Factory function to get RAG engine instance

    Args:
        db_path: SQLite path
        chroma_path: ChromaDB path

    Returns:
        RAGEngine instance
    """
    return RAGEngine(db_path, chroma_path)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test RAG engine
    with RAGEngine() as rag:
        test_query = "Quelle est la tendance des revenus d'Apple?"
        result = rag.process(test_query)
        print(f"\nQuery: {test_query}")
        print(f"Response: {result['response']}")
        print(f"Sources: {result['sources']}")
        print(f"Chart hint: {result['chart_hint']}")
