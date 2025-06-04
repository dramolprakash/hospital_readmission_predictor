# Hospital Readmission Risk Predictor

## Project Overview
Machine learning model to predict 30-day hospital readmissions using CMS DE-SynPUF data.

## Dataset
CMS Data Entrepreneurs' Synthetic Public Use File (DE-SynPUF) Sample 1
- Timeframe: 2008-2010
- ~116K beneficiaries
- Multiple claim types: Inpatient, Outpatient, Carrier, PDE

## Project Structure
- `data/` - Data files (not tracked in Git)
- `src/` - Source code
- `notebooks/` - Jupyter notebooks
- `models/` - Saved models
- `reports/` - Analysis outputs

## Setup
1. Clone repository
2. Create virtual environment
3. Install requirements: `pip install -r requirements.txt`
4. Add data files to `data/raw/`

## Target Metrics
- Precision: >75%
- Business Impact: $2.3M+ potential savings