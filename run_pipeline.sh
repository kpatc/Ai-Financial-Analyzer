#!/bin/bash

# Complete Financial Analysis Pipeline
# This script runs all phases sequentially

set -e  # Exit on error

BASE_DIR="/home/josh/Forage/Ai-Financial-Analyzer"
VENV="$BASE_DIR/venv/bin/python"

echo ""
echo "================================================================================"
echo "FINANCIAL DATA PIPELINE - COMPLETE RUN"
echo "================================================================================"
echo ""

# Phase 1: Extract financial data
echo ""
echo "================================================================================"
echo "PHASE 1: EXTRACTION (34 companies)"
echo "================================================================================"

echo "Starting data extraction..."
cd "$BASE_DIR"
$VENV data-integration/extraction/extract_10k_data.py

# Phase 2: Analysis
echo ""
echo "================================================================================"
echo "PHASE 2: FINANCIAL ANALYSIS"
echo "================================================================================"

cd "$BASE_DIR"
$VENV data-integration/analysis/analysis_calculator.py

# Phase 3: Load to Database
echo ""
echo "================================================================================"
echo "PHASE 3: LOAD TO DATABASE"
echo "================================================================================"

cd "$BASE_DIR"
$VENV load_to_database.py

# Phase 4: Display Results
echo ""
echo "================================================================================"
echo "PHASE 4: DISPLAY RESULTS"
echo "================================================================================"

cd "$BASE_DIR"
$VENV query_database.py

echo ""
echo "================================================================================"
echo "✅ PIPELINE COMPLETE"
echo "================================================================================"
echo ""
echo "Database: $BASE_DIR/data/financial_analyzer.db"
echo "Analysis: $BASE_DIR/data/analysis/*.csv"
echo ""
