#!/usr/bin/env python3
"""
Response Formatter
Structures chatbot responses with charts, tables, and summaries
"""

import json
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    """Response content types"""
    SUMMARY = "summary"
    CHART = "chart"
    TABLE = "table"
    COMPARISON = "comparison"
    DETAILED = "detailed"


class ResponseFormatter:
    """Formats and structures chatbot responses"""

    def __init__(self):
        """Initialize formatter"""
        pass

    def format_summary_response(self,
                               summary: str,
                               key_metrics: Optional[Dict[str, Any]] = None,
                               sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Format a summary response with key metrics

        Args:
            summary: Main response text
            key_metrics: Dict of metric_name: value pairs
            sources: List of data source references

        Returns:
            Formatted response dict
        """
        response = {
            'type': ResponseType.SUMMARY.value,
            'text': summary,
            'metrics': key_metrics or {},
            'sources': sources or [],
        }

        return response

    def format_chart_response(self,
                            summary: str,
                            chart: Dict[str, Any],
                            key_insights: Optional[List[str]] = None,
                            sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Format a response focused on chart visualization

        Args:
            summary: Main response text
            chart: Chart.js compatible chart data
            key_insights: Bullet points highlighting chart insights
            sources: List of data source references

        Returns:
            Formatted response dict
        """
        response = {
            'type': ResponseType.CHART.value,
            'text': summary,
            'chart': chart,
            'insights': key_insights or [],
            'sources': sources or [],
        }

        return response

    def format_table_response(self,
                            summary: str,
                            table_data: List[Dict[str, Any]],
                            columns: Optional[List[str]] = None,
                            key_insights: Optional[List[str]] = None,
                            sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Format a response with structured table data

        Args:
            summary: Main response text
            table_data: List of row dicts
            columns: List of column names (for display order)
            key_insights: Bullet points from table
            sources: List of data source references

        Returns:
            Formatted response dict
        """
        response = {
            'type': ResponseType.TABLE.value,
            'text': summary,
            'table': {
                'data': table_data,
                'columns': columns or (list(table_data[0].keys()) if table_data else []),
                'row_count': len(table_data),
            },
            'insights': key_insights or [],
            'sources': sources or [],
        }

        return response

    def format_comparison_response(self,
                                  summary: str,
                                  comparison_data: List[Dict[str, Any]],
                                  tickers: List[str],
                                  chart: Optional[Dict[str, Any]] = None,
                                  key_insights: Optional[List[str]] = None,
                                  sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Format a comparison response with chart and table

        Args:
            summary: Main response text
            comparison_data: List of company comparison dicts
            tickers: Tickers being compared
            chart: Optional Chart.js data for visualization
            key_insights: Key findings from comparison
            sources: List of data source references

        Returns:
            Formatted response dict
        """
        response = {
            'type': ResponseType.COMPARISON.value,
            'text': summary,
            'companies': tickers,
            'data': comparison_data,
            'chart': chart,
            'insights': key_insights or [],
            'sources': sources or [],
        }

        return response

    def format_detailed_response(self,
                                summary: str,
                                sections: Dict[str, Any],
                                chart: Optional[Dict[str, Any]] = None,
                                sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Format a detailed multi-section response

        Args:
            summary: Main response text
            sections: Dict of {section_name: content}
            chart: Optional chart visualization
            sources: List of data source references

        Returns:
            Formatted response dict
        """
        response = {
            'type': ResponseType.DETAILED.value,
            'text': summary,
            'sections': sections,
            'chart': chart,
            'sources': sources or [],
        }

        return response

    @staticmethod
    def extract_key_insights(data: Dict[str, Any],
                            metric_keys: List[str],
                            threshold: float = 0.1) -> List[str]:
        """
        Extract key insights from data (e.g., high/low values)

        Args:
            data: Dict with metric values
            metric_keys: Keys to analyze
            threshold: % change threshold for highlighting

        Returns:
            List of insight strings
        """
        insights = []

        for key in metric_keys:
            if key not in data:
                continue

            value = data[key]
            if value is None:
                continue

            # Format insight based on metric type
            if 'margin' in key.lower() or 'pct' in key.lower():
                if isinstance(value, (int, float)):
                    insights.append(f"{key.replace('_', ' ').title()}: {value:.1f}%")

            elif 'ratio' in key.lower():
                if isinstance(value, (int, float)):
                    insights.append(f"{key.replace('_', ' ').title()}: {value:.2f}x")

            elif 'billions' in key.lower():
                if isinstance(value, (int, float)):
                    insights.append(f"{key.replace('_', ' ').title()}: ${value:.2f}B")

        return insights

    @staticmethod
    def build_metric_summary(metrics: Dict[str, Any]) -> str:
        """
        Build a readable summary of key metrics

        Args:
            metrics: Dict with metric values

        Returns:
            Formatted summary string
        """
        lines = []

        # Revenue
        if 'revenue' in metrics:
            rev = metrics['revenue']
            lines.append(f"• Revenue: ${rev:.2f}B" if isinstance(rev, (int, float)) else f"• Revenue: {rev}")

        # Net Income
        if 'net_income' in metrics:
            ni = metrics['net_income']
            lines.append(f"• Net Income: ${ni:.2f}B" if isinstance(ni, (int, float)) else f"• Net Income: {ni}")

        # Margins
        if 'net_margin_pct' in metrics:
            margin = metrics['net_margin_pct']
            lines.append(f"• Net Margin: {margin:.1f}%" if isinstance(margin, (int, float)) else f"• Net Margin: {margin}")

        # Key Ratios
        if 'debt_to_equity' in metrics:
            de = metrics['debt_to_equity']
            lines.append(f"• Debt-to-Equity: {de:.2f}x" if isinstance(de, (int, float)) else f"• D/E Ratio: {de}")

        if 'roa_pct' in metrics:
            roa = metrics['roa_pct']
            lines.append(f"• ROA: {roa:.1f}%" if isinstance(roa, (int, float)) else f"• ROA: {roa}")

        return "\n".join(lines) if lines else "No metrics available"


def format_company_profile(ticker: str,
                         company_info: Dict[str, Any],
                         latest_metrics: Dict[str, Any]) -> str:
    """
    Format a company profile summary

    Args:
        ticker: Company ticker
        company_info: Company info dict
        latest_metrics: Latest financial metrics

    Returns:
        Formatted profile string
    """
    lines = [
        f"**{company_info.get('name', ticker)}** ({ticker})",
        f"Sector: {company_info.get('sector', 'N/A')} | Industry: {company_info.get('industry', 'N/A')}",
        "",
        "**Key Metrics:**"
    ]

    # Add metrics
    if latest_metrics:
        formatter = ResponseFormatter()
        summary = formatter.build_metric_summary(latest_metrics)
        lines.append(summary)

    return "\n".join(lines)


def format_comparison_insights(comparison_data: List[Dict[str, Any]],
                             metric: str = 'net_margin_pct') -> List[str]:
    """
    Generate comparison insights from comparison data

    Args:
        comparison_data: List of company comparison dicts
        metric: Metric to analyze

    Returns:
        List of insight strings
    """
    insights = []

    if not comparison_data or metric not in comparison_data[0]:
        return insights

    # Sort by metric
    sorted_data = sorted(
        comparison_data,
        key=lambda x: x.get(metric, float('-inf')),
        reverse=True
    )

    if len(sorted_data) >= 2:
        leader = sorted_data[0]
        laggard = sorted_data[-1]

        leader_ticker = leader.get('ticker', 'Unknown')
        laggard_ticker = laggard.get('ticker', 'Unknown')
        leader_val = leader.get(metric, 0)
        laggard_val = laggard.get(metric, 0)

        if metric.endswith('_pct'):
            insights.append(f"Leader: {leader_ticker} with {leader_val:.1f}%")
            insights.append(f"Laggard: {laggard_ticker} with {laggard_val:.1f}%")
        else:
            insights.append(f"Leader: {leader_ticker} ({leader_val:.2f})")
            insights.append(f"Lowest: {laggard_ticker} ({laggard_val:.2f})")

    return insights
