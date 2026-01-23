"""
SQLAlchemy Data Models for Financial Data
Relational database schema for structured financial data
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

Base = declarative_base()


class Company(Base):
    """Company information"""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    sector = Column(String(100))
    industry = Column(String(100))
    description = Column(Text)
    cik = Column(String(20), unique=True, index=True)  # SEC CIK number
    state_of_incorporation = Column(String(50))  # State where incorporated
    phone = Column(String(20))
    address = Column(Text)
    business_category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    financial_metrics = relationship('FinancialMetric', back_populates='company', cascade='all, delete-orphan')
    financial_ratios = relationship('FinancialRatio', back_populates='company', cascade='all, delete-orphan')
    analyses = relationship('Analysis', back_populates='company', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_company_ticker', 'ticker'),
        Index('idx_company_name', 'name'),
        Index('idx_company_cik', 'cik'),
    )
    
    def __repr__(self):
        return f"<Company(name='{self.name}', ticker='{self.ticker}', industry='{self.industry}')>"


class FinancialMetric(Base):
    """Raw financial metrics extracted from 10-K"""
    __tablename__ = 'financial_metrics'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_year_end = Column(DateTime, nullable=False)
    
    # Income Statement
    total_revenue = Column(Float)
    cogs = Column(Float)  # Cost of Goods Sold
    gross_profit = Column(Float)
    operating_expenses = Column(Float)
    operating_income = Column(Float)
    net_income = Column(Float)
    
    # Balance Sheet
    total_assets = Column(Float)
    current_assets = Column(Float)
    long_term_assets = Column(Float)
    total_liabilities = Column(Float)
    current_liabilities = Column(Float)
    long_term_liabilities = Column(Float)
    long_term_debt = Column(Float)
    stockholders_equity = Column(Float)
    
    # Cash Flow
    operating_cash_flow = Column(Float)
    investing_cash_flow = Column(Float)
    financing_cash_flow = Column(Float)
    
    # Metadata
    data_source = Column(String(50))  # 'sec_edgar', 'manual_input', etc.
    is_audited = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company', back_populates='financial_metrics')
    ratio = relationship('FinancialRatio', back_populates='metric', uselist=False, cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_metric_company_year', 'company_id', 'fiscal_year'),
        Index('idx_metric_year_end', 'fiscal_year_end'),
    )
    
    def __repr__(self):
        return f"<FinancialMetric(company_id={self.company_id}, year={self.fiscal_year})>"


class FinancialRatio(Base):
    """Calculated financial ratios"""
    __tablename__ = 'financial_ratios'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey('financial_metrics.id'), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    
    # Liquidity ratios
    current_ratio = Column(Float)
    
    # Leverage ratios
    debt_to_equity = Column(Float)
    debt_to_assets = Column(Float)
    lt_debt_to_equity = Column(Float)  # Long-term debt to equity
    
    # Profitability ratios
    gross_margin = Column(Float)  # %
    operating_margin = Column(Float)  # %
    net_profit_margin = Column(Float)  # %
    roa = Column(Float)  # Return on Assets %
    roe = Column(Float)  # Return on Equity %
    
    # Efficiency ratios
    asset_turnover = Column(Float)
    ocf_to_liabilities = Column(Float)
    ocf_margin = Column(Float)  # %
    
    # Cash Flow
    free_cash_flow = Column(Float)
    
    # Growth metrics (YoY %)
    revenue_growth_yoy = Column(Float)  # %
    income_growth_yoy = Column(Float)  # %
    
    # Metadata
    calculation_method = Column(String(50))
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company', back_populates='financial_ratios')
    metric = relationship('FinancialMetric', back_populates='ratio')
    
    __table_args__ = (
        Index('idx_ratio_company_year', 'company_id', 'fiscal_year'),
    )


class Analysis(Base):
    """Analysis summaries and insights"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    
    # Analysis content
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    key_insights = Column(JSON)  # List of insights
    recommendations = Column(JSON)  # List of recommendations
    
    # Metadata
    analysis_type = Column(String(50))  # 'yoy_comparison', 'trend_analysis', etc.
    data_quality_score = Column(Float)  # 0-1
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))  # User/system that created it
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company', back_populates='analyses')
    
    __table_args__ = (
        Index('idx_analysis_company_year', 'company_id', 'fiscal_year'),
        Index('idx_analysis_type', 'analysis_type'),
    )


class DataIngestionLog(Base):
    """Track data ingestion and synchronization"""
    __tablename__ = 'data_ingestion_logs'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)  # 'company', 'metric', etc.
    num_records = Column(Integer)
    status = Column(String(20))  # 'success', 'failed', 'partial'
    error_message = Column(Text)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Metadata
    metadata_info = Column(JSON)  # Additional info (file size, record counts, etc.)
    
    def __repr__(self):
        return f"<DataIngestionLog(source='{self.source}', status='{self.status}')>"


class VectorIndexLog(Base):
    """Track vector database indexing"""
    __tablename__ = 'vector_index_logs'
    
    id = Column(Integer, primary_key=True)
    collection_name = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    num_vectors = Column(Integer)
    embedding_model = Column(String(100))
    status = Column(String(20))
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<VectorIndexLog(collection='{self.collection_name}', status='{self.status}')>"
