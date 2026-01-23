#!/usr/bin/env python3
"""
Financial Chatbot REST API with Interactive Dialogue & Visual Analytics
Flask API with CORS support, semantic search, and chart visualization
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import traceback
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import get_chatbot
from config import FLASK_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global chatbot instance (lazy loaded)
_chatbot_instance = None

@app.before_request
def initialize_chatbot():
    """Lazy initialize chatbot on first request"""
    global _chatbot_instance
    if _chatbot_instance is None:
        try:
            _chatbot_instance = get_chatbot()
            logger.info("Chatbot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            raise

def get_chart_data(category, company=None):
    """
    Generate chart data for visualization
    Returns arrays suitable for Chart.js visualization
    """
    try:
        chatbot = _chatbot_instance
        
        if category == 'revenue_trend':
            # Get revenue data for all companies
            companies = ['Microsoft', 'Apple']
            chart_data = {
                'labels': ['2022', '2023', '2024'],
                'datasets': []
            }
            
            colors = ['#667eea', '#764ba2']
            for idx, company in enumerate(companies):
                try:
                    revenues = chatbot.financial_data.df[
                        chatbot.financial_data.df['Company'] == company
                    ].sort_values('Fiscal Year')['Total Revenue'].values / 1e9
                    
                    if len(revenues) > 0:
                        chart_data['datasets'].append({
                            'label': company,
                            'data': revenues.tolist(),
                            'borderColor': colors[idx],
                            'backgroundColor': colors[idx] + '22',
                            'fill': True,
                            'tension': 0.4
                        })
                except:
                    pass
            return chart_data
            
        elif category == 'profit_margin':
            # Profit margin comparison
            companies = ['Microsoft', 'Apple']
            chart_data = {
                'labels': companies,
                'datasets': [{
                    'label': 'Net Profit Margin (%)',
                    'data': [],
                    'backgroundColor': ['#667eea', '#764ba2'],
                    'borderRadius': 8
                }]
            }
            
            for company in companies:
                try:
                    data = chatbot.financial_data.df[
                        chatbot.financial_data.df['Company'] == company
                    ].sort_values('Fiscal Year').iloc[-1]
                    
                    margin = (data['Net Income'] / data['Total Revenue']) * 100
                    chart_data['datasets'][0]['data'].append(round(margin, 2))
                except:
                    chart_data['datasets'][0]['data'].append(0)
            
            return chart_data
            
        elif category == 'comparison':
            # Multi-metric comparison
            metrics = ['Total Revenue', 'Net Income', 'Operating Cash Flow']
            companies = ['Microsoft', 'Apple']
            
            chart_data = {
                'labels': [f'{m} ($B)' for m in metrics],
                'datasets': []
            }
            
            colors = ['#667eea', '#764ba2']
            for idx, company in enumerate(companies):
                try:
                    data = chatbot.financial_data.df[
                        chatbot.financial_data.df['Company'] == company
                    ].sort_values('Fiscal Year').iloc[-1]
                    
                    values = [
                        data['Total Revenue'] / 1e9,
                        data['Net Income'] / 1e9,
                        data['Operating Cash Flow'] / 1e9
                    ]
                    
                    chart_data['datasets'].append({
                        'label': company,
                        'data': [round(v, 2) for v in values],
                        'backgroundColor': colors[idx],
                        'borderRadius': 8
                    })
                except:
                    pass
            
            return chart_data
    
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        return {}

def get_follow_up_questions(category, company=None):
    """
    Generate contextual follow-up questions based on query type
    """
    follow_ups = {
        'revenue': [
            'How does this compare to last year?',
            'What about operating cash flow?',
            'Show me profitability margins'
        ],
        'profitability': [
            'How has net margin trended?',
            'Compare with competitor margins',
            'What about return on assets?'
        ],
        'liquidity': [
            'What about debt levels?',
            'Show operating cash flow trends',
            'Compare financial health metrics'
        ],
        'leverage': [
            'What is the debt-to-assets ratio?',
            'How does cash cover liabilities?',
            'Show financial stability assessment'
        ],
        'efficiency': [
            'Compare asset utilization',
            'Show revenue per asset dollar',
            'What about profit margins?'
        ],
        'trend': [
            'What drives this growth?',
            'How sustainable is it?',
            'Compare growth across companies'
        ],
        'comparison': [
            'Which company is financially healthier?',
            'Compare specific metrics',
            'Show margin differences'
        ]
    }
    
    return follow_ups.get(category, [
        'What other metrics interest you?',
        'Would you like a company comparison?',
        'Show me different time periods?'
    ])

def get_related_topics(category):
    """
    Suggest related topics for interactive exploration
    """
    related = {
        'revenue': ['Profitability', 'Growth Trends', 'Company Comparison'],
        'profitability': ['Leverage', 'Efficiency Metrics', 'Revenue Trends'],
        'liquidity': ['Leverage', 'Cash Flow', 'Financial Health'],
        'leverage': ['Liquidity', 'Debt Coverage', 'Financial Risk'],
        'efficiency': ['Profitability', 'Asset Utilization', 'ROA'],
        'trend': ['Growth Comparison', 'Future Outlook', 'Market Position'],
        'comparison': ['Detailed Metrics', 'Financial Health', 'Growth Prospects']
    }
    
    return related.get(category, ['Metrics Overview', 'Company Comparison', 'Trends'])

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Financial Chatbot API',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    }), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with interactive features"""
    try:
        # Validate request
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message field'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Process query through chatbot
        result = _chatbot_instance.process_query(user_message)
        
        # Extract category for contextual suggestions
        category = result.get('category', 'general')
        
        # Get follow-up questions
        follow_ups = get_follow_up_questions(category)
        
        # Get related topics
        related = get_related_topics(category)
        
        # Get chart data if applicable
        chart_data = {}
        if category in ['revenue', 'profitability', 'comparison']:
            chart_data = get_chart_data(f'{category}_trend' if category != 'comparison' else 'comparison')
        
        # Build response with interactive elements
        response = {
            'response': result['response'],
            'metadata': {
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'entities': result.get('entities', {}),
                'confidence': result.get('confidence', 0.8)
            },
            'interactive': {
                'followUpQuestions': follow_ups,
                'relatedTopics': related,
                'suggestedQueries': [
                    f'Compare {company} metrics' for company in ['Microsoft', 'Apple']
                ]
            },
            'visualization': {
                'chartData': chart_data,
                'chartType': _determine_chart_type(category),
                'insights': _generate_insights(category, chart_data)
            }
        }
        
        logger.info(f"Processed query: {user_message[:50]}... | Category: {category}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def _determine_chart_type(category):
    """Determine appropriate chart type for category"""
    chart_types = {
        'revenue': 'line',
        'profitability': 'bar',
        'comparison': 'bar',
        'trend': 'line',
        'efficiency': 'radar'
    }
    return chart_types.get(category, 'bar')

def _generate_insights(category, chart_data):
    """Generate data-driven insights from chart data"""
    if not chart_data or 'datasets' not in chart_data:
        return []
    
    insights = []
    
    if category == 'revenue' and chart_data.get('datasets'):
        # Analyze trends
        for dataset in chart_data['datasets']:
            if dataset['data'] and len(dataset['data']) > 1:
                growth = ((dataset['data'][-1] - dataset['data'][0]) / dataset['data'][0]) * 100
                insights.append(f"{dataset['label']}: {growth:.1f}% growth over period")
    
    elif category == 'comparison' and chart_data.get('datasets'):
        # Find strongest company
        if len(chart_data['datasets']) > 0:
            insights.append("Visual comparison shows relative strengths across key metrics")
    
    return insights

@app.route('/api/chat/history', methods=['GET'])
def get_history():
    """Retrieve conversation history"""
    try:
        history = _chatbot_instance.get_conversation_history()
        return jsonify({
            'history': history,
            'total_messages': len(history),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """Reset conversation history"""
    try:
        _chatbot_instance.reset_conversation()
        return jsonify({
            'message': 'Conversation history reset',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Reset error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Get list of available companies"""
    try:
        companies = _chatbot_instance.financial_data.df['Company'].unique().tolist()
        return jsonify({
            'companies': companies,
            'count': len(companies),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Companies endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/<company>', methods=['GET'])
def get_company_metrics(company):
    """Get metrics for a specific company"""
    try:
        metrics = {}
        df = _chatbot_instance.financial_data.df
        company_data = df[df['Company'] == company].sort_values('Fiscal Year').iloc[-1]
        
        if company_data is not None:
            metrics = {
                'company': company,
                'revenue': round(company_data['Total Revenue'] / 1e9, 2),
                'net_income': round(company_data['Net Income'] / 1e9, 2),
                'operating_cash_flow': round(company_data['Operating Cash Flow'] / 1e9, 2),
                'profit_margin': round((company_data['Net Income'] / company_data['Total Revenue']) * 100, 2),
                'fiscal_year': company_data['Fiscal Year'].strftime('%Y-%m-%d')
            }
        
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return jsonify({'error': f'Company not found: {company}'}), 404

@app.route('/api/comparison', methods=['GET'])
def get_comparison():
    """Multi-company financial comparison"""
    try:
        df = _chatbot_instance.financial_data.df
        companies = df['Company'].unique()
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'comparison_data': []
        }
        
        for company in sorted(companies):
            company_data = df[df['Company'] == company].sort_values('Fiscal Year').iloc[-1]
            comparison['comparison_data'].append({
                'company': company,
                'revenue_billions': round(company_data['Total Revenue'] / 1e9, 2),
                'net_income_billions': round(company_data['Net Income'] / 1e9, 2),
                'ocf_billions': round(company_data['Operating Cash Flow'] / 1e9, 2),
                'fiscal_year': company_data['Fiscal Year'].strftime('%Y-%m-%d')
            })
        
        return jsonify(comparison), 200
    except Exception as e:
        logger.error(f"Comparison endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/query/classify', methods=['POST'])
def classify_query():
    """Analyze and classify a query without generating response"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message field'}), 400
        
        user_message = data['message'].strip()
        
        # Use NLP engine to classify
        category = _chatbot_instance.nlp_engine.classify_query(user_message)
        entities = _chatbot_instance.nlp_engine.extract_entities(user_message)
        
        return jsonify({
            'query': user_message,
            'category': category,
            'entities': entities,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Query classification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info(f"Starting Financial Chatbot API on {FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
    app.run(
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port'],
        debug=FLASK_CONFIG['debug'],
        threaded=FLASK_CONFIG['threaded']
    )
