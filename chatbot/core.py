#!/usr/bin/env python3
"""
Financial Chatbot Core Logic with Advanced Query Routing
Handles financial data analysis and chatbot conversation management
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from nlp_engine import NLPEngine
from config import (
    COMPANIES, METRICS, RATIOS, QUERY_CATEGORIES, SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

class FinancialData:
    """Financial data loader and calculator"""
    
    def __init__(self, csv_path='../data/financial_data_raw.csv'):
        """Initialize financial data"""
        self.df = None
        self.company_data = {}
        self.load_data(csv_path)
    
    def load_data(self, csv_path):
        """Load financial data from CSV"""
        try:
            self.df = pd.read_csv(csv_path)
            self.df['Fiscal Year'] = pd.to_datetime(self.df['Fiscal Year'])
            self._prepare_company_data()
            logger.info(f"Financial data loaded: {len(self.df)} records")
        except Exception as e:
            logger.error(f"Error loading financial data: {e}")
            # Create empty dataframe as fallback
            self.df = pd.DataFrame()
    
    def _prepare_company_data(self):
        """Prepare lookup dictionaries for quick access"""
        for company in self.df['Company'].unique():
            company_df = self.df[self.df['Company'] == company].sort_values('Fiscal Year')
            self.company_data[company] = {
                'latest': company_df.iloc[-1] if len(company_df) > 0 else None,
                'data': company_df
            }
    
    def get_revenue(self, company, year='latest'):
        """Get revenue for company"""
        if company not in self.company_data:
            return None
        
        if year == 'latest':
            data = self.company_data[company]['latest']
            return data['Total Revenue'] if data is not None else None
        
        company_df = self.company_data[company]['data']
        matching = company_df[company_df['Fiscal Year'].dt.year == year]
        return matching['Total Revenue'].values[0] if len(matching) > 0 else None
    
    def get_net_income(self, company):
        """Get net income for company"""
        if company not in self.company_data:
            return None
        
        data = self.company_data[company]['latest']
        return data['Net Income'] if data is not None else None
    
    def get_operating_cash_flow(self, company):
        """Get operating cash flow"""
        if company not in self.company_data:
            return None
        
        data = self.company_data[company]['latest']
        return data['Operating Cash Flow'] if data is not None else None
    
    def calculate_profit_margin(self, company):
        """Calculate net profit margin"""
        if company not in self.company_data:
            return None
        
        data = self.company_data[company]['latest']
        if data is None or data['Total Revenue'] == 0:
            return None
        
        return (data['Net Income'] / data['Total Revenue']) * 100
    
    def calculate_debt_to_equity(self, company):
        """Calculate debt-to-equity ratio"""
        if company not in self.company_data:
            return None
        
        data = self.company_data[company]['latest']
        if data is None:
            return None
        
        # Find latest row with complete balance sheet data
        company_df = self.company_data[company]['data'].dropna(
            subset=['Total Assets', 'Total Liabilities']
        )
        
        if len(company_df) == 0:
            return None
        
        latest = company_df.iloc[-1]
        equity = latest['Total Assets'] - latest['Total Liabilities']
        
        if equity <= 0:
            return None
        
        return latest['Total Liabilities'] / equity
    
    def get_growth_rate(self, company, metric='Total Revenue'):
        """Calculate YoY growth rate"""
        if company not in self.company_data:
            return None
        
        company_df = self.company_data[company]['data'].sort_values('Fiscal Year')
        
        if len(company_df) < 2:
            return None
        
        latest = company_df.iloc[-1]
        previous = company_df.iloc[-2]
        
        if previous[metric] == 0:
            return None
        
        return ((latest[metric] - previous[metric]) / previous[metric]) * 100
    
    def rank_companies(self, metric='Total Revenue'):
        """Rank companies by metric"""
        latest_data = []
        
        for company in self.company_data:
            data = self.company_data[company]['latest']
            if data is not None and pd.notna(data[metric]):
                latest_data.append({
                    'company': company,
                    'value': data[metric],
                    'value_billions': data[metric] / 1e9
                })
        
        return sorted(latest_data, key=lambda x: x['value'], reverse=True)


class FinancialChatbot:
    """Main chatbot for financial analysis"""
    
    def __init__(self, financial_data):
        """Initialize chatbot"""
        self.financial_data = financial_data
        self.nlp_engine = NLPEngine()
        self.conversation_history = []
        logger.info("FinancialChatbot initialized")
    
    def process_query(self, user_query):
        """Process user query and generate response"""
        # Classify query
        category = self.nlp_engine.classify_query(user_query)
        
        # Extract entities
        entities = self.nlp_engine.extract_entities(user_query)
        
        # Route to appropriate handler
        response = self._route_query(category, user_query, entities)
        
        # Add to history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_query': user_query,
            'bot_response': response['response'],
            'category': category,
            'entities': entities
        })
        
        return response
    
    def _route_query(self, category, query, entities):
        """Route query to appropriate handler"""
        handlers = {
            'revenue': self._handle_revenue_query,
            'profitability': self._handle_profitability_query,
            'liquidity': self._handle_liquidity_query,
            'leverage': self._handle_leverage_query,
            'efficiency': self._handle_efficiency_query,
            'trend': self._handle_trend_query,
            'comparison': self._handle_comparison_query
        }
        
        handler = handlers.get(category, self._handle_general_query)
        return handler(query, entities)
    
    def _handle_revenue_query(self, query, entities):
        """Handle revenue-related queries"""
        response_text = "Revenue Analysis:\n\n"
        
        companies = entities.get('companies', [])
        if not companies:
            companies = list(self.financial_data.company_data.keys())
        
        for company in companies:
            revenue = self.financial_data.get_revenue(company)
            growth = self.financial_data.get_growth_rate(company, 'Total Revenue')
            
            if revenue is not None:
                response_text += f"• {company}: ${revenue/1e9:.2f}B"
                if growth is not None:
                    response_text += f" ({growth:+.2f}% YoY)"
                response_text += "\n"
        
        return {
            'response': response_text,
            'category': 'revenue',
            'entities': entities,
            'confidence': 0.85
        }
    
    def _handle_profitability_query(self, query, entities):
        """Handle profitability-related queries"""
        response_text = "Profitability Analysis (Net Profit Margin):\n\n"
        
        companies = entities.get('companies', [])
        if not companies:
            companies = list(self.financial_data.company_data.keys())
        
        margin_data = []
        for company in companies:
            margin = self.financial_data.calculate_profit_margin(company)
            if margin is not None:
                margin_data.append({'company': company, 'margin': margin})
        
        # Sort by margin descending
        margin_data.sort(key=lambda x: x['margin'], reverse=True)
        
        for item in margin_data:
            response_text += f"• {item['company']}: {item['margin']:.2f}%\n"
        
        response_text += "\nInterpretation: Higher margin indicates better cost control and pricing power."
        
        return {
            'response': response_text,
            'category': 'profitability',
            'entities': entities,
            'confidence': 0.85
        }
    
    def _handle_liquidity_query(self, query, entities):
        """Handle liquidity-related queries"""
        response_text = "Liquidity Analysis (Operating Cash Flow):\n\n"
        
        companies = entities.get('companies', [])
        if not companies:
            companies = list(self.financial_data.company_data.keys())
        
        ocf_ranking = self.financial_data.rank_companies('Operating Cash Flow')
        
        for item in ocf_ranking:
            response_text += f"• {item['company']}: ${item['value_billions']:.2f}B\n"
        
        response_text += "\nStrong OCF indicates ability to fund operations, investments, and dividends."
        
        return {
            'response': response_text,
            'category': 'liquidity',
            'entities': entities,
            'confidence': 0.85
        }
    
    def _handle_leverage_query(self, query, entities):
        """Handle leverage/debt-related queries"""
        response_text = "Leverage Analysis (Debt-to-Equity Ratio):\n\n"
        
        companies = entities.get('companies', [])
        if not companies:
            companies = list(self.financial_data.company_data.keys())
        
        for company in companies:
            dte = self.financial_data.calculate_debt_to_equity(company)
            
            if dte is not None:
                if dte < 1:
                    assessment = "Conservative - Low financial risk"
                elif dte < 2:
                    assessment = "Moderate - Balanced capital structure"
                else:
                    assessment = "Leveraged - Higher financial risk"
                
                response_text += f"• {company}: {dte:.2f} ({assessment})\n"
        
        return {
            'response': response_text,
            'category': 'leverage',
            'entities': entities,
            'confidence': 0.85
        }
    
    def _handle_efficiency_query(self, query, entities):
        """Handle efficiency-related queries"""
        response_text = "Efficiency Analysis:\n\n"
        
        companies = entities.get('companies', [])
        if not companies:
            companies = list(self.financial_data.company_data.keys())
        
        for company in companies:
            data = self.financial_data.company_data.get(company, {}).get('latest')
            
            if data is not None:
                response_text += f"{company}:\n"
                
                # ROA (Return on Assets)
                if pd.notna(data['Total Assets']) and data['Total Assets'] > 0:
                    roa = (data['Net Income'] / data['Total Assets']) * 100
                    response_text += f"  • Return on Assets (ROA): {roa:.2f}%\n"
                
                # Asset Turnover
                if pd.notna(data['Total Assets']) and data['Total Assets'] > 0:
                    turnover = data['Total Revenue'] / data['Total Assets']
                    response_text += f"  • Asset Turnover: {turnover:.2f}x\n"
        
        return {
            'response': response_text,
            'category': 'efficiency',
            'entities': entities,
            'confidence': 0.85
        }
    
    def _handle_trend_query(self, query, entities):
        """Handle trend-related queries"""
        response_text = "Financial Trends Analysis:\n\n"
        
        companies = entities.get('companies', [])
        if not companies:
            companies = list(self.financial_data.company_data.keys())
        
        for company in companies:
            response_text += f"{company}:\n"
            
            revenue_growth = self.financial_data.get_growth_rate(company, 'Total Revenue')
            income_growth = self.financial_data.get_growth_rate(company, 'Net Income')
            
            if revenue_growth is not None:
                response_text += f"  • Revenue Growth: {revenue_growth:+.2f}%\n"
            
            if income_growth is not None:
                response_text += f"  • Net Income Growth: {income_growth:+.2f}%\n"
        
        response_text += "\nTrends show company trajectory and momentum in key metrics."
        
        return {
            'response': response_text,
            'category': 'trend',
            'entities': entities,
            'confidence': 0.85
        }
    
    def _handle_comparison_query(self, query, entities):
        """Handle comparative analysis queries"""
        response_text = "Comparative Financial Analysis:\n\n"
        
        companies = entities.get('companies', [])
        if not companies:
            companies = list(self.financial_data.company_data.keys())
        
        # Revenue comparison
        response_text += "Revenue (Latest Year):\n"
        revenue_ranking = self.financial_data.rank_companies('Total Revenue')
        for idx, item in enumerate(revenue_ranking, 1):
            response_text += f"  {idx}. {item['company']}: ${item['value_billions']:.2f}B\n"
        
        response_text += "\nNet Income (Latest Year):\n"
        income_ranking = self.financial_data.rank_companies('Net Income')
        for idx, item in enumerate(income_ranking, 1):
            response_text += f"  {idx}. {item['company']}: ${item['value_billions']:.2f}B\n"
        
        response_text += "\nProfitability (Margins):\n"
        margins = []
        for company in companies:
            margin = self.financial_data.calculate_profit_margin(company)
            if margin is not None:
                margins.append({'company': company, 'margin': margin})
        
        margins.sort(key=lambda x: x['margin'], reverse=True)
        for idx, item in enumerate(margins, 1):
            response_text += f"  {idx}. {item['company']}: {item['margin']:.2f}%\n"
        
        return {
            'response': response_text,
            'category': 'comparison',
            'entities': entities,
            'confidence': 0.88
        }
    
    def _handle_general_query(self, query, entities):
        """Handle general/unknown queries"""
        response_text = """I can help you with financial analysis. Available topics:

1. Revenue Analysis - Total revenue and growth trends
2. Profitability - Net profit margins and efficiency
3. Liquidity - Cash flow and working capital
4. Leverage - Debt levels and financial risk
5. Efficiency Metrics - ROA, asset turnover
6. Trend Analysis - Growth trajectories
7. Company Comparison - Multi-company benchmarking

Try asking: "What is Apple's revenue?" or "Compare Microsoft and Apple"
"""
        return {
            'response': response_text,
            'category': 'general',
            'entities': entities,
            'confidence': 0.5
        }
    
    def get_conversation_history(self):
        """Get full conversation history"""
        return self.conversation_history
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        logger.info("Conversation history reset")


# Singleton instance
_chatbot_instance = None

def get_chatbot():
    """Get or create singleton chatbot instance"""
    global _chatbot_instance
    
    if _chatbot_instance is None:
        financial_data = FinancialData()
        _chatbot_instance = FinancialChatbot(financial_data)
    
    return _chatbot_instance

if __name__ == '__main__':
    # Test the chatbot
    chatbot = get_chatbot()
    
    test_queries = [
        "What is Microsoft's revenue?",
        "How profitable is Apple?",
        "Compare the two companies",
        "Show me financial trends"
    ]
    
    for query in test_queries:
        result = chatbot.process_query(query)
        print(f"\nQ: {query}")
        print(f"A: {result['response']}")
