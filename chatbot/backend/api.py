#!/usr/bin/env python3
"""
Financial Chatbot REST API
Flask API with RAG engine, semantic search, chart generation, and conversation history
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

import os
from config import FLASK_CONFIG, SECURITY_CONFIG, CHART_TYPES, SQLITE_CONFIG
from rag_engine import RAGEngine
from db_client import FinancialDBClient
from vector_sync import ensure_vector_db_synced

# Get the base directory paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
CHATBOT_DIR = os.path.dirname(BACKEND_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=SECURITY_CONFIG.get('cors_origins', ['*']))
app.config['MAX_CONTENT_LENGTH'] = FLASK_CONFIG['max_content_length']

# Global instances
_rag_engine = None
_conversation_histories = {}  # Track per-session conversations


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_services():
    """Initialize RAG engine and databases"""
    global _rag_engine

    try:
        logger.info("Initializing services...")

        # Ensure ChromaDB is synced
        logger.info("Syncing ChromaDB...")
        count = ensure_vector_db_synced(force=False)
        logger.info(f"ChromaDB ready with {count} documents")

        # Initialize RAG engine
        _rag_engine = RAGEngine()
        logger.info("RAG engine initialized")

        # Note: DB client will be initialized per-request to avoid threading issues
        logger.info("Database client will be initialized per-request")

        logger.info("✓ All services initialized successfully")

    except Exception as e:
        logger.error(f"Service initialization failed: {e}", exc_info=True)
        raise


def get_db_client():
    """Get a database client for the current thread"""
    return FinancialDBClient(SQLITE_CONFIG['path'])

@app.before_request
def ensure_initialized():
    """Ensure services are initialized before handling requests"""
    global _rag_engine
    if _rag_engine is None:
        initialize_services()


# ============================================================================
# CHART GENERATION
# ============================================================================

def build_chart_data(chart_hint: Dict[str, Any], db: FinancialDBClient) -> Dict[str, Any]:
    """
    Build Chart.js-compatible data for a chart

    Args:
        chart_hint: {type, tickers}
        db: Database client

    Returns:
        Chart.js data dict {type, data, title}
    """
    if not chart_hint or not chart_hint.get('type'):
        return {}

    chart_type = chart_hint['type']
    tickers = chart_hint.get('tickers', [])

    try:
        if chart_type == 'revenue_trend' and tickers:
            # Line chart with revenue trend
            ticker = tickers[0]
            trend = db.get_revenue_trend(ticker, years=3)

            if not trend:
                return {}

            return {
                'type': 'line',
                'data': {
                    'labels': [str(t['fiscal_year']) for t in trend],
                    'datasets': [{
                        'label': f'{ticker} Revenue',
                        'data': [t.get('revenue_billions', 0) for t in trend],
                        'borderColor': '#6366f1',
                        'backgroundColor': '#6366f122',
                        'tension': 0.4,
                        'fill': True,
                        'pointRadius': 5,
                        'pointHoverRadius': 7,
                    }, {
                        'label': f'{ticker} Net Income',
                        'data': [t.get('net_income_billions', 0) for t in trend],
                        'borderColor': '#10b981',
                        'backgroundColor': '#10b98122',
                        'tension': 0.4,
                        'fill': True,
                        'pointRadius': 5,
                    }]
                },
                'title': f'Revenue Trend - {ticker}',
            }

        elif chart_type == 'profit_margin' and tickers:
            # Bar chart for profit margins
            comparison = db.get_comparison(tickers)

            if not comparison:
                return {}

            return {
                'type': 'bar',
                'data': {
                    'labels': [c['ticker'] for c in comparison],
                    'datasets': [{
                        'label': 'Net Profit Margin (%)',
                        'data': [c.get('net_margin_pct', 0) for c in comparison],
                        'backgroundColor': '#6366f1',
                        'borderRadius': 8,
                        'borderSkipped': False,
                    }]
                },
                'title': 'Net Profit Margin Comparison',
            }

        elif chart_type == 'comparison':
            # Grouped bar chart for multiple metrics
            if not tickers:
                # Get top 5 by revenue
                rankings = db.get_rankings('revenue', top_n=5)
                tickers = [r['ticker'] for r in rankings]

            comparison = db.get_comparison(tickers)

            if not comparison:
                return {}

            return {
                'type': 'bar',
                'data': {
                    'labels': [c['ticker'] for c in comparison],
                    'datasets': [
                        {
                            'label': 'Revenue ($B)',
                            'data': [c.get('revenue_billions', 0) for c in comparison],
                            'backgroundColor': '#6366f1',
                            'borderRadius': 4,
                        },
                        {
                            'label': 'Net Income ($B)',
                            'data': [c.get('net_income_billions', 0) for c in comparison],
                            'backgroundColor': '#10b981',
                            'borderRadius': 4,
                        },
                        {
                            'label': 'OCF ($B)',
                            'data': [c.get('operating_cash_flow_billions', 0) for c in comparison],
                            'backgroundColor': '#f59e0b',
                            'borderRadius': 4,
                        }
                    ]
                },
                'title': 'Financial Metrics Comparison',
            }

        elif chart_type == 'leverage' and tickers:
            # Bar chart for debt-to-equity
            comparison = db.get_comparison(tickers)

            if not comparison:
                return {}

            return {
                'type': 'bar',
                'data': {
                    'labels': [c['ticker'] for c in comparison],
                    'datasets': [{
                        'label': 'Debt-to-Equity Ratio',
                        'data': [c.get('debt_to_equity', 0) for c in comparison],
                        'backgroundColor': '#ef4444',
                        'borderRadius': 8,
                        'borderSkipped': False,
                    }]
                },
                'title': 'Debt-to-Equity Comparison',
            }

        elif chart_type == 'ratios' and tickers:
            # Radar chart for multiple ratios
            ticker = tickers[0]
            ratios = db.get_ratios(ticker)

            if not ratios:
                return {}

            return {
                'type': 'radar',
                'data': {
                    'labels': ['ROA %', 'D/E', 'Asset Turnover', 'Net Margin %'],
                    'datasets': [{
                        'label': f'{ticker} Financial Ratios',
                        'data': [
                            ratios.get('roa_pct', 0),
                            ratios.get('debt_to_equity', 0),
                            ratios.get('asset_turnover', 0),
                            ratios.get('net_margin_pct', 0),
                        ],
                        'borderColor': '#6366f1',
                        'backgroundColor': '#6366f144',
                        'pointBackgroundColor': '#6366f1',
                    }]
                },
                'title': f'Financial Ratios - {ticker}',
            }

        elif chart_type == 'yoy_growth' and tickers:
            # Horizontal bar for YoY growth
            ticker = tickers[0]
            yoy = db.get_yoy_growth(ticker)

            if not yoy:
                return {}

            return {
                'type': 'bar',
                'data': {
                    'labels': ['Revenue', 'Net Income', 'OCF'],
                    'datasets': [{
                        'label': 'YoY Growth (%)',
                        'data': [
                            yoy.get('revenue_yoy_pct', 0),
                            yoy.get('net_income_yoy_pct', 0),
                            yoy.get('operating_cash_flow_yoy_pct', 0),
                        ],
                        'backgroundColor': '#10b981',
                        'borderRadius': 8,
                    }]
                },
                'title': f'Year-over-Year Growth - {ticker}',
            }

        return {}

    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return {}


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        db = get_db_client()
        companies = db.get_all_companies()

        return jsonify({
            'status': 'healthy',
            'service': 'Financial Chatbot API',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'companies_count': len(companies),
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint
    POST body: {message, session_id (optional)}
    """
    try:
        data = request.get_json()

        if not data or not data.get('message'):
            return jsonify({'error': 'Message required'}), 400

        message = data.get('message', '').strip()
        if len(message) > SECURITY_CONFIG['max_query_length']:
            return jsonify({
                'error': f'Message too long (max {SECURITY_CONFIG["max_query_length"]} chars)'
            }), 400

        session_id = data.get('session_id', 'default')

        # Get conversation history for this session
        history = _conversation_histories.get(session_id, [])

        # Process query through RAG engine
        rag_result = _rag_engine.process(message, history=history)

        # Update history
        history.append({'role': 'user', 'content': message})
        history.append({'role': 'assistant', 'content': rag_result['response']})

        # Keep only last N messages
        max_history = SECURITY_CONFIG.get('max_history_messages', 10)
        history = history[-max_history:]
        _conversation_histories[session_id] = history

        # Build chart data if hint provided
        chart_data = {}
        if rag_result.get('chart_hint'):
            chart_data = build_chart_data(rag_result['chart_hint'], get_db_client())

        # Return response
        return jsonify({
            'response': rag_result['response'],
            'chart': chart_data or None,
            'sources': rag_result.get('sources', []),
            'category': rag_result.get('category'),
            'timestamp': datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return jsonify({
            'error': 'Error processing query',
            'message': str(e)
        }), 500


@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Get list of all companies"""
    try:
        companies = get_db_client().get_all_companies()
        return jsonify({
            'companies': companies,
            'count': len(companies)
        }), 200

    except Exception as e:
        logger.error(f"Get companies error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics/<ticker>', methods=['GET'])
def get_metrics(ticker):
    """Get latest metrics for a company"""
    try:
        metrics = get_db_client().get_company_metrics(ticker.upper())

        if not metrics:
            return jsonify({'error': f'Company {ticker} not found'}), 404

        return jsonify(metrics), 200

    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/comparison', methods=['GET'])
def get_comparison():
    """Get comparison data for all top companies"""
    try:
        # Get top 5 companies by revenue
        rankings = get_db_client().get_rankings('revenue', top_n=5)
        tickers = [r['ticker'] for r in rankings]

        comparison = get_db_client().get_comparison(tickers)

        return jsonify({
            'comparison_data': comparison,
            'count': len(comparison)
        }), 200

    except Exception as e:
        logger.error(f"Get comparison error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """Reset conversation history"""
    try:
        session_id = request.get_json().get('session_id', 'default') if request.get_json() else 'default'

        if session_id in _conversation_histories:
            del _conversation_histories[session_id]

        return jsonify({
            'message': 'Conversation history reset',
            'session_id': session_id
        }), 200

    except Exception as e:
        logger.error(f"Reset chat error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """Search financial documents semantically"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Query required'}), 400

        # Search vector DB
        from vector_sync import VectorSync
        vector_sync = VectorSync()
        results = vector_sync.search(query, n_results=5)

        return jsonify({
            'results': results,
            'count': len(results)
        }), 200

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500




# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    try:
        logger.info("Starting Financial Chatbot API...")
        initialize_services()

        app.run(
            host=FLASK_CONFIG['host'],
            port=FLASK_CONFIG['port'],
            debug=FLASK_CONFIG['debug'],
            threaded=FLASK_CONFIG['threaded']
        )

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
