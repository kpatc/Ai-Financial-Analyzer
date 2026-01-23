# AI Financial Analyzer (BCG GenAI Job Simulation – Forage)

This repo contains my work for the **BCG GenAI Job Simulation on Forage**, where I act as a junior data scientist in BCG’s GenAI consulting team.

**Task 1** focuses on extracting key financial data from **10-K / 10-Q** filings, computing meaningful metrics, and producing clear, comparable outputs.

## What Task 1 delivers

- Automated extraction of key financial line items (income statement / balance sheet / cash flow)
- Cleaning + standardization across companies/years (including robust YoY handling)
- Financial metrics for growth, profitability, liquidity, leverage, and returns
- Dashboards and BI-ready exports for fast interpretation and benchmarking

## Repo structure (high-level)

```
data-integration/        # Extraction + analysis pipeline
notebooks/               # Task notebooks (exploration / prototypes)
data/                    # Local outputs (only Dashboard 2 is tracked)
generate_dashboards.py   # Generates dashboard images
run_full_pipeline.py     # End-to-end runner
```

## Dashboard (Task 1)

This is the current “clean” dashboard export (Dashboard 2):

![Dashboard 2: Financial Health & Benchmarking](data/dashboard_2_health_benchmark.png)

## Tech stack

- Python
- pandas, NumPy
- SEC/EDGAR extraction tooling
- SQLite
- Matplotlib, Seaborn

## Run

- Create a virtual environment and install deps: `pip install -r requirements.txt`
- Run end-to-end: `python run_full_pipeline.py`
- Generate dashboards only: `python generate_dashboards.py`

## Status

Current focus: **Task 1 (data extraction + initial analysis)**.

---
Client (simulation): Global Finance Corp. (GFC)
