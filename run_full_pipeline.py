#!/usr/bin/env python3
"""
Complete Financial Analysis Pipeline - End to End
Extraction -> Analysis -> Database Storage
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'

def run_command(cmd, description):
    """Run a command and report status"""
    print("\n" + "="*80)
    print(f"STEP: {description}")
    print("="*80)
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ FAILED: {description}")
        sys.exit(1)
    
    print(f"✓ SUCCESS: {description}")
    return True

def main():
    print("\n" + "="*80)
    print("FINANCIAL DATA PIPELINE - COMPLETE RUN")
    print("="*80)
    
    # Step 1: Extract data with many companies
    print("\n\n" + "="*80)
    print("PHASE 1: DATA EXTRACTION (34 companies)")
    print("="*80)
    
    extraction_script = BASE_DIR / 'data-integration' / 'extraction' / 'extract_10k_data.py'
    
    # Create extraction script with all companies
    extraction_code = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from extraction.extract_10k_data import ExtractionPipeline

companies = [
    ('MSFT', 'Microsoft'),
    ('AAPL', 'Apple'),
    ('TSLA', 'Tesla'),
    ('GOOGL', 'Alphabet'),
    ('META', 'Meta Platforms'),
    ('NVDA', 'NVIDIA'),
    ('AMD', 'Advanced Micro Devices'),
    ('INTC', 'Intel'),
    ('JPM', 'JPMorgan Chase'),
    ('BAC', 'Bank of America'),
    ('WFC', 'Wells Fargo'),
    ('GS', 'Goldman Sachs'),
    ('MS', 'Morgan Stanley'),
    ('WMT', 'Walmart'),
    ('KO', 'Coca-Cola'),
    ('PEP', 'PepsiCo'),
    ('MCD', 'McDonald\'s'),
    ('TM', 'Toyota'),
    ('F', 'Ford'),
    ('JNJ', 'Johnson & Johnson'),
    ('PFE', 'Pfizer'),
    ('ABBV', 'AbbVie'),
    ('MRK', 'Merck'),
    ('LLY', 'Eli Lilly'),
    ('XOM', 'ExxonMobil'),
    ('CVX', 'Chevron'),
    ('NEE', 'NextEra Energy'),
    ('SO', 'Southern Company'),
    ('BA', 'Boeing'),
    ('CAT', 'Caterpillar'),
    ('HON', 'Honeywell'),
    ('MMM', '3M'),
    ('CSCO', 'Cisco Systems'),
    ('ORCL', 'Oracle'),
]

pipeline = ExtractionPipeline(
    "KPATCHA Josue josuekpatcha1@gmail.com",
    str(Path(__file__).parent.parent / 'data' / 'financial_data_raw.csv')
)

print(f"Extracting {len(companies)} companies...")
pipeline.extract_batch(companies, years=3)
csv_path = pipeline.save_csv()
print(f"✓ Extraction complete: {csv_path}")
'''
    
    extraction_cmd = f"cd {BASE_DIR / 'data-integration'} && ../../venv/bin/python -c \"{extraction_code.replace(chr(34), chr(92)+chr(34))}\""
    
    run_command(
        f"cd {BASE_DIR} && ./venv/bin/python data-integration/extraction/extract_10k_data.py",
        "Extract financial data from SEC EDGAR (34 companies)"
    )
    
    # Step 2: Analyze extracted data
    print("\n\n" + "="*80)
    print("PHASE 2: FINANCIAL ANALYSIS")
    print("="*80)
    
    run_command(
        f"cd {BASE_DIR} && ./venv/bin/python data-integration/analysis/analysis_calculator.py",
        "Calculate financial metrics, YoY growth, profitability, and ratios"
    )
    
    # Step 3: Load to database
    print("\n\n" + "="*80)
    print("PHASE 3: LOAD TO DATABASE")
    print("="*80)
    
    run_command(
        f"cd {BASE_DIR} && ./venv/bin/python load_to_database.py",
        "Load analysis results to SQLite database"
    )
    
    # Step 4: Query and display results
    print("\n\n" + "="*80)
    print("PHASE 4: QUERY RESULTS")
    print("="*80)
    
    run_command(
        f"cd {BASE_DIR} && ./venv/bin/python query_database.py",
        "Display database contents and analysis results"
    )
    
    print("\n" + "="*80)
    print("✅ COMPLETE PIPELINE FINISHED SUCCESSFULLY!")
    print("="*80)
    print(f"\nDatabase: {DATA_DIR / 'financial_analyzer.db'}")
    print(f"Analysis files: {DATA_DIR / 'analysis'}/*.csv")
    print("\n")

if __name__ == '__main__':
    from pathlib import Path
    main()
