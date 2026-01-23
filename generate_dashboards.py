#!/usr/bin/env python3
"""
Generate professional financial dashboards with matplotlib and seaborn.
Reads from data/analysis/*.csv and creates 2 styled dashboard images.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.facecolor'] = '#f8f9fa'
plt.rcParams['axes.facecolor'] = '#ffffff'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9

# Data directory
DATA_DIR = Path('data/analysis')

def load_data():
    """Load all analysis CSV files"""
    try:
        yoy = pd.read_csv(DATA_DIR / 'yoy_growth_analysis.csv')
        profit = pd.read_csv(DATA_DIR / 'profit_margin_analysis.csv')
        ratios = pd.read_csv(DATA_DIR / 'financial_ratios_analysis.csv')
        comp_general = pd.read_csv(DATA_DIR / 'comparative_general.csv')
        comp_year = pd.read_csv(DATA_DIR / 'comparative_by_year.csv')
        comp_industry = pd.read_csv(DATA_DIR / 'comparative_by_industry.csv')
        
        print("✓ All data files loaded successfully")
        return yoy, profit, ratios, comp_general, comp_year, comp_industry
    except FileNotFoundError as e:
        print(f"✗ Missing file: {e}")
        return None, None, None, None, None, None

def create_dashboard_1(yoy, profit, ratios, comp_general, comp_year, comp_industry):
    """Dashboard 1: Growth & Profitability Analysis - REDESIGNED FOR READABILITY"""
    from matplotlib.gridspec import GridSpec
    
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle('Financial Dashboard 1: Growth & Profitability Analysis', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # Create custom grid: 2 rows, 2 cols for top, then 1 row full width for bottom
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3, top=0.93, bottom=0.08)
    
    # 1. Top Revenue Companies (larger chart, top-left)
    ax1 = fig.add_subplot(gs[0, 0])
    if not comp_year.empty:
        latest_year = comp_year['Fiscal Year'].max()
        top_revenue = comp_year[comp_year['Fiscal Year'] == latest_year].nlargest(12, 'Revenue ($B)')
        if not top_revenue.empty:
            bars = ax1.barh(top_revenue['Company'], top_revenue['Revenue ($B)'], 
                            color='#2E86AB', alpha=0.85, edgecolor='#0B3C5D', linewidth=1.5)
            ax1.set_xlabel('Revenue ($B)', fontweight='bold', fontsize=12)
            ax1.set_title('Top 12 Companies by Revenue', fontweight='bold', fontsize=13, pad=15)
            ax1.invert_yaxis()
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax1.text(width, bar.get_y() + bar.get_height()/2, f'${width:.1f}B',
                        ha='left', va='center', fontsize=9, fontweight='bold')
            ax1.tick_params(labelsize=10)
            ax1.grid(True, alpha=0.3, axis='x', linestyle='--')
    
    # 2. Revenue YoY Growth (horizontal bar, top-right)
    ax2 = fig.add_subplot(gs[0, 1])
    if not yoy.empty:
        yoy_latest = yoy.sort_values('Fiscal Year').drop_duplicates('Company', keep='last')
        yoy_top = yoy_latest.nlargest(12, 'Revenue YoY %')
        if not yoy_top.empty:
            colors_yoy = ['#27AE60' if x > 10 else '#F39C12' if x > 5 else '#E74C3C' 
                         for x in yoy_top['Revenue YoY %']]
            bars = ax2.barh(yoy_top['Company'], yoy_top['Revenue YoY %'], 
                            color=colors_yoy, alpha=0.85, edgecolor='black', linewidth=1.2)
            ax2.axvline(x=0, color='black', linestyle='-', linewidth=2)
            ax2.set_xlabel('Revenue YoY Growth (%)', fontweight='bold', fontsize=12)
            ax2.set_title('Revenue Year-over-Year Growth', fontweight='bold', fontsize=13, pad=15)
            ax2.invert_yaxis()
            for bar in bars:
                width = bar.get_width()
                ax2.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.1f}%',
                        ha='left', va='center', fontsize=9, fontweight='bold')
            ax2.tick_params(labelsize=10)
            ax2.grid(True, alpha=0.3, axis='x', linestyle='--')
    
    # 3. Profitability Leaders (middle row, left)
    ax3 = fig.add_subplot(gs[1, 0])
    if not profit.empty:
        profit_latest = profit.sort_values('Fiscal Year').drop_duplicates('Company', keep='last')
        top_profit = profit_latest.nlargest(10, 'Net Profit Margin %')
        if not top_profit.empty:
            bars = ax3.barh(top_profit['Company'], top_profit['Net Profit Margin %'], 
                            color='#27AE60', alpha=0.85, edgecolor='darkgreen', linewidth=1.2)
            ax3.set_xlabel('Net Profit Margin (%)', fontweight='bold', fontsize=12)
            ax3.set_title('Top Profitability Leaders', fontweight='bold', fontsize=13, pad=15)
            ax3.invert_yaxis()
            for bar in bars:
                width = bar.get_width()
                ax3.text(width, bar.get_y() + bar.get_height()/2, f'{width:.1f}%',
                        ha='left', va='center', fontsize=9, fontweight='bold')
            ax3.tick_params(labelsize=10)
            ax3.grid(True, alpha=0.3, axis='x', linestyle='--')
    
    # 4. Industry Profitability (middle row, right)
    ax4 = fig.add_subplot(gs[1, 1])
    if not comp_industry.empty:
        industry_profit = comp_industry.dropna(subset=['Profitability %'])
        if not industry_profit.empty:
            industry_margins = industry_profit.groupby('Industry')['Profitability %'].mean().sort_values(ascending=False).head(8)
            bars = ax4.barh(industry_margins.index, industry_margins.values, 
                            color='#F39C12', alpha=0.85, edgecolor='#D68910', linewidth=1.2)
            ax4.set_xlabel('Avg Profitability (%)', fontweight='bold', fontsize=12)
            ax4.set_title('Industry Profitability Benchmark', fontweight='bold', fontsize=13, pad=15)
            ax4.invert_yaxis()
            for bar in bars:
                width = bar.get_width()
                ax4.text(width, bar.get_y() + bar.get_height()/2, f'{width:.1f}%',
                        ha='left', va='center', fontsize=9, fontweight='bold')
            ax4.tick_params(labelsize=10)
            ax4.grid(True, alpha=0.3, axis='x', linestyle='--')
    
    # 5. Net Margin Trends Over Time (LARGE BOTTOM - spans full width, no rotation issues)
    ax5 = fig.add_subplot(gs[2, :])
    if not profit.empty:
        yearly_margins = profit.groupby('Fiscal Year')['Net Profit Margin %'].mean().sort_index()
        if len(yearly_margins) > 0:
            years = yearly_margins.index.astype(str)
            ax5.bar(range(len(yearly_margins)), yearly_margins.values, 
                   color='#1ABC9C', alpha=0.85, edgecolor='#0E6251', linewidth=2, width=0.6)
            ax5.set_xticks(range(len(yearly_margins)))
            ax5.set_xticklabels(years, fontsize=12, fontweight='bold')
            ax5.set_ylabel('Average Net Profit Margin (%)', fontweight='bold', fontsize=12)
            ax5.set_xlabel('Fiscal Year', fontweight='bold', fontsize=12)
            ax5.set_title('Net Margin Evolution Over Time', fontweight='bold', fontsize=14, pad=15)
            ax5.grid(True, alpha=0.3, axis='y', linestyle='--')
            for i, (year, value) in enumerate(zip(range(len(yearly_margins)), yearly_margins.values)):
                ax5.text(year, value + 0.5, f'{value:.1f}%', ha='center', va='bottom', 
                        fontsize=11, fontweight='bold')
            ax5.tick_params(labelsize=11)
    
    plt.savefig('data/dashboard_1_growth_profitability.png', dpi=300, bbox_inches='tight')
    print("✓ Dashboard 1 saved: data/dashboard_1_growth_profitability.png")
    plt.close()

def create_dashboard_2(profit, ratios, comp_general, comp_year, comp_industry, yoy):
    """Dashboard 2: Financial Health & Industry Benchmarking"""
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle('Financial Dashboard 2: Financial Health & Industry Benchmarking', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # 1. Debt-to-Equity Ratios (color coded)
    ax1 = plt.subplot(2, 3, 1)
    if not ratios.empty:
        de_latest = ratios.sort_values('Fiscal Year').drop_duplicates('Company', keep='last')
        de_sorted = de_latest.nlargest(8, 'Debt-to-Equity')
        if not de_sorted.empty:
            colors = ['#27ae60' if x < 1 else '#f39c12' if x < 2 else '#e74c3c' for x in de_sorted['Debt-to-Equity']]
            bars = ax1.barh(de_sorted['Company'], de_sorted['Debt-to-Equity'], 
                            color=colors, alpha=0.85, edgecolor='black', linewidth=0.8)
            ax1.axvline(x=1, color='#27ae60', linestyle='--', linewidth=2, label='Safe (1.0)', alpha=0.7)
            ax1.axvline(x=2, color='#f39c12', linestyle='--', linewidth=2, label='Caution (2.0)', alpha=0.7)
            ax1.set_xlabel('Debt-to-Equity Ratio', fontweight='bold', fontsize=10)
            ax1.set_title('Debt-to-Equity Ratio', fontweight='bold', fontsize=11)
            ax1.invert_yaxis()
            ax1.legend(fontsize=8, loc='lower right')
    
    # 2. ROE Leaders
    ax2 = plt.subplot(2, 3, 2)
    if not ratios.empty:
        roe_latest = ratios.sort_values('Fiscal Year').drop_duplicates('Company', keep='last')
        roe_top = roe_latest.nlargest(8, 'ROE (%)')
        if not roe_top.empty:
            bars = ax2.bar(range(len(roe_top)), roe_top['ROE (%)'], 
                          color='#f39c12', alpha=0.85, edgecolor='#d68910', linewidth=1.2)
            ax2.set_xticks(range(len(roe_top)))
            ax2.set_xticklabels(roe_top['Company'], rotation=45, ha='right', fontsize=9)
            ax2.set_ylabel('ROE (%)', fontweight='bold', fontsize=10)
            ax2.set_title('Return on Equity (ROE)', fontweight='bold', fontsize=11)
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, height,
                        f'{height:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # 3. Current Ratio Health
    ax3 = plt.subplot(2, 3, 3)
    if not ratios.empty:
        cr_latest = ratios.sort_values('Fiscal Year').drop_duplicates('Company', keep='last')
        cr_sorted = cr_latest.nlargest(8, 'Current Ratio')
        if not cr_sorted.empty:
            colors_cr = ['#27ae60' if 1.0 <= x <= 2.0 else '#3498db' if x > 2.0 else '#f39c12' 
                        for x in cr_sorted['Current Ratio']]
            bars = ax3.barh(cr_sorted['Company'], cr_sorted['Current Ratio'], 
                            color=colors_cr, alpha=0.85, edgecolor='black', linewidth=0.8)
            ax3.axvline(x=1.0, color='#f39c12', linestyle='--', linewidth=2, alpha=0.7, label='Min (1.0)')
            ax3.axvline(x=2.0, color='#3498db', linestyle='--', linewidth=2, alpha=0.7, label='Max (2.0)')
            ax3.set_xlabel('Current Ratio', fontweight='bold', fontsize=10)
            ax3.set_title('Current Ratio (Liquidity)', fontweight='bold', fontsize=11)
            ax3.invert_yaxis()
            ax3.legend(fontsize=8, loc='lower right')
    
    # 4. ROA Leaders
    ax4 = plt.subplot(2, 3, 4)
    if not ratios.empty:
        roa_latest = ratios.sort_values('Fiscal Year').drop_duplicates('Company', keep='last')
        roa_top = roa_latest.nlargest(8, 'ROA (%)')
        if not roa_top.empty:
            bars = ax4.barh(roa_top['Company'], roa_top['ROA (%)'], 
                            color='#9b59b6', alpha=0.85, edgecolor='#6c3483', linewidth=1.2)
            ax4.set_xlabel('ROA (%)', fontweight='bold', fontsize=10)
            ax4.set_title('Return on Assets (ROA)', fontweight='bold', fontsize=11)
            ax4.invert_yaxis()
            for bar in bars:
                width = bar.get_width()
                ax4.text(width, bar.get_y() + bar.get_height()/2, f'{width:.1f}%',
                        ha='left', va='center', fontsize=8, fontweight='bold')
    
    # 5. Industry Profitability Benchmark
    ax5 = plt.subplot(2, 3, 5)
    if not comp_industry.empty:
        industry_profit = comp_industry.dropna(subset=['Net Income ($B)'])
        if not industry_profit.empty:
            industry_avg = industry_profit.groupby('Industry')['Net Income ($B)'].mean().nlargest(6)
            bars = ax5.bar(range(len(industry_avg)), industry_avg.values, 
                          color='#3498db', alpha=0.85, edgecolor='#1e5a96', linewidth=1.2)
            ax5.set_xticks(range(len(industry_avg)))
            ax5.set_xticklabels(industry_avg.index, rotation=45, ha='right', fontsize=9)
            ax5.set_ylabel('Avg Net Income ($B)', fontweight='bold', fontsize=10)
            ax5.set_title('Industry Profitability Benchmark', fontweight='bold', fontsize=11)
            for bar in bars:
                height = bar.get_height()
                ax5.text(bar.get_x() + bar.get_width()/2, height,
                        f'${height:.1f}B', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # 6. Revenue Trends by Fiscal Year
    ax6 = plt.subplot(2, 3, 6)
    if not comp_year.empty:
        yearly_rev = comp_year.dropna(subset=['Revenue ($B)'])
        if not yearly_rev.empty:
            yearly_agg = yearly_rev.groupby('Fiscal Year (Short)')['Revenue ($B)'].sum()
            ax6.plot(range(len(yearly_agg)), yearly_agg.values, marker='o', linewidth=3.5,
                    markersize=12, color='#27ae60', markerfacecolor='#27ae60', markeredgecolor='darkgreen',
                    markeredgewidth=2, label='Total Revenue')
            ax6.fill_between(range(len(yearly_agg)), yearly_agg.values, alpha=0.25, color='#27ae60')
            ax6.set_xticks(range(len(yearly_agg)))
            ax6.set_xticklabels(yearly_agg.index, fontsize=9)
            ax6.set_ylabel('Total Revenue ($B)', fontweight='bold', fontsize=10)
            ax6.set_xlabel('Fiscal Year', fontweight='bold', fontsize=10)
            ax6.set_title('Revenue Trends Over Time', fontweight='bold', fontsize=11)
            ax6.grid(True, alpha=0.3, linestyle='--')
            ax6.legend(fontsize=9, loc='best')
    
    plt.tight_layout()
    plt.savefig('data/dashboard_2_health_benchmark.png', dpi=300, bbox_inches='tight')
    print("✓ Dashboard 2 saved: data/dashboard_2_health_benchmark.png")
    plt.close()

def main():
    """Main execution"""
    print("=" * 60)
    print("Financial Dashboard Generator")
    print("=" * 60)
    
    # Load data
    yoy, profit, ratios, comp_general, comp_year, comp_industry = load_data()
    
    if yoy is None:
        print("✗ Failed to load data. Exiting.")
        return
    
    # Generate dashboards
    print("\nGenerating Dashboard 1 (Growth & Profitability)...")
    create_dashboard_1(yoy, profit, ratios, comp_general, comp_year, comp_industry)
    
    print("\nGenerating Dashboard 2 (Health & Benchmarking)...")
    create_dashboard_2(profit, ratios, comp_general, comp_year, comp_industry, yoy)
    
    print("\n" + "=" * 60)
    print("✓ Dashboard generation complete!")
    print("=" * 60)
    print("\nOutput files:")
    print("  • data/dashboard_1_growth_profitability.png")
    print("  • data/dashboard_2_health_benchmark.png")

if __name__ == '__main__':
    main()
