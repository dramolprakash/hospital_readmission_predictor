# Hospital Readmission Predictor — Project Guide

## Project Goal
Predict 30-day hospital readmissions using CMS DE-SynPUF Medicare claims data.
Target: improve model precision and AUC by incorporating outpatient, carrier, and prescription drug data.

---

## Original Baseline (Sample 1 only, Inpatient + Beneficiary)
- Algorithm: Logistic Regression (L2, C=0.1, class_weight=balanced)
- Training samples: 53,418 | Test samples: 13,355 | Features: 50
- Accuracy: 74.52% | Precision: 19.29% | Recall: 47.60% | F1: 27.46% | AUC-ROC: 69.39%
- Annual net savings: $1,492,000 | ROI: 44.7% | Prevented readmissions: 322/yr

## Current Model Results (Samples 1–5, all 5 data types, leakage-free)
- Algorithm: Logistic Regression (L2, class_weight=balanced, optimized threshold)
- Dataset: 28,695 records | Features: 55 (excludes ID, raw-date, and outcome-leakage cols)
- Accuracy: 80.3% | Precision: 22.2% | Recall: 37.8% | F1: 28.0% | AUC-ROC: 69.6%
- Annual net savings: $661,000 | ROI: 66.8% | Prevented readmissions: 110/yr
- Best model artifact: `models/readmission_model_logistic_regression.joblib`
- Leakage columns excluded: DAYS_TO_READMISSION, HAS_READMISSION, READMISSION_DATE, DEATH_WITHIN_30_DAYS, OBSERVATION_DAYS, raw IDs and date cols

---

## Data Scope Decision
**Use samples 1–5 only** (avoids missing carrier/PDE files for samples 11 & 17, and the malformed "Sample_17 - Copy" 2010 beneficiary file).

### Data types to use (all from `data/raw/`)
| Type | Files per sample | Pattern |
|---|---|---|
| Beneficiary Summary | 3 (2008, 2009, 2010) | `DE1_0_{YEAR}_Beneficiary_Summary_File_Sample_{N}.csv` |
| Inpatient Claims | 1 | `DE1_0_2008_to_2010_Inpatient_Claims_Sample_{N}.csv` |
| Outpatient Claims | 1 (**NEW**) | `DE1_0_2008_to_2010_Outpatient_Claims_Sample_{N}.csv` |
| Carrier Claims | 2 (A+B split) (**NEW**) | `DE1_0_2008_to_2010_Carrier_Claims_Sample_{N}A.csv` + `...{N}B.csv` |
| Prescription Drug Events | 1 (**NEW**) | `DE1_0_2008_to_2010_Prescription_Drug_Events_Sample_{N}.csv` |

---

## Pipeline — Notebook Structure

### Notebook 01 — Data Loading & Exploration
**Current state:** Loads Sample 1 only (Beneficiary 2008/09/10 + Inpatient). Outputs to `data/processed/`.

**Required changes:**
- Loop over samples 1–5 and concatenate each data type
- Add loading for Outpatient, Carrier (A+B concatenated), and PDE files
- Explore schema and null rates for the three new data types
- Save processed parquets per data type (not just beneficiary + inpatient)

**Output files (new targets):**
- `data/processed/beneficiary_2008_processed.parquet` (all 5 samples combined)
- `data/processed/beneficiary_2009_processed.parquet`
- `data/processed/beneficiary_2010_processed.parquet`
- `data/processed/inpatient_processed.parquet`
- `data/processed/outpatient_processed.parquet` (**NEW**)
- `data/processed/carrier_processed.parquet` (**NEW**)
- `data/processed/pde_processed.parquet` (**NEW**)

### Notebook 02 — Data Combination & Preprocessing
**Current state:** Merges Beneficiary + Inpatient into master clean files.

**Required changes:**
- Add preprocessing steps for Outpatient, Carrier, PDE
- Date parsing and deduplication for each new type
- Merge all types on `DESYNPUF_ID`

**Output files (new targets):**
- `data/processed/beneficiary_master_clean.parquet`
- `data/processed/inpatient_master_clean.parquet`
- `data/processed/outpatient_master_clean.parquet` (**NEW**)
- `data/processed/carrier_master_clean.parquet` (**NEW**)
- `data/processed/pde_master_clean.parquet` (**NEW**)

### Notebook 03 — Target Variable Creation
**Current state:** Creates 30-day readmission labels from inpatient data. Minimal changes needed.

**Required changes:**
- Re-run with larger inpatient dataset (5 samples vs 1)
- No structural changes to target logic

**Output files:** Same as before (`data/features/readmission_target_dataset.parquet`)

### Notebook 04 — Feature Engineering
**Current state:** 50 features from inpatient history + beneficiary demographics.

**Required changes — new feature groups:**

*Outpatient features (pre-admission window):*
- Outpatient visit count in 30/90/365 days before admission
- Days since last outpatient visit
- Unique outpatient providers seen
- ER visit count (outpatient claim type) in prior 90 days

*Carrier/physician features (pre-admission window):*
- Physician visit count in 30/90 days before admission
- Unique physicians seen
- Specialist visit flag (non-PCP claim types)
- Days since last physician visit

*Prescription Drug features (pre-admission window):*
- Unique drug count (polypharmacy — strong readmission signal)
- Days supply covered in prior 90 days (adherence proxy)
- High-risk drug class flags (anticoagulants, insulin, opioids)
- Medication gap flag (refill lapse > 7 days)

*Post-discharge features (outpatient, carrier):*
- Outpatient follow-up within 7 days of discharge (binary)
- Outpatient follow-up within 14 days of discharge (binary)
- Physician follow-up within 7 days of discharge (binary)

**Output files:** `data/features/readmission_features_final.parquet` (expanded feature set)

### Notebook 05 — Model Development
**Current state:** Trains Logistic Regression, Random Forest, Gradient Boosting. Already fixed:
- Added `SimpleImputer(strategy='median')` for NaN handling
- Replaced deprecated `np.trapz` with `np.trapezoid`

**Required changes:**
- Re-run with expanded feature set — no structural changes needed
- Update model_metadata.txt with new results

---

## Implementation Order
1. [x] Rewrite Notebook 01 — multi-sample loading for all 5 data types
2. [x] Rewrite Notebook 02 — preprocessing for Outpatient, Carrier, PDE
3. [x] Re-run Notebook 03 — target variable (minimal changes)
4. [x] Rewrite Notebook 04 — add outpatient/carrier/PDE feature groups
5. [x] Re-run Notebook 05 — retrain model on expanded features (leakage-free)
6. [x] Update Streamlit app metrics with new results

---

## Known Issues Fixed
- `ValueError: Input X contains NaN` in Notebook 05 — fixed with `SimpleImputer(strategy='median', keep_empty_features=True)` in `prepare_data_for_modeling()` (cell id: `76fe3559`)
- `AttributeError: module 'numpy' has no attribute 'trapz'` — replaced with `np.trapezoid` in visualization cell (cell id: `ee824282`)
- `KeyError: 'discharge_year'` in Notebook 03 — new NB01 uses uppercase `DISCHARGE_YEAR`; fixed in 2 cells of NB03
- `ValueError: Shape of passed values (28695, 55), indices imply (28695, 56)` in Notebook 05 — root cause: float64 YYYYMMDD dates in parquet; `pd.to_datetime(col.astype(str))` produced `"20090602.0"` → NaT; fixed with `parse_yyyymmdd()` helper using `.astype(int).astype(str)` in NB04
- Data leakage in Notebook 05 — `DAYS_TO_READMISSION` captured 99% of tree model feature importance; fixed by adding explicit EXCLUDE_COLS set in `prepare_data_for_modeling()` (cell id: `76fe3559`)

## Files to Ignore in data/raw/
- `DE1_0_2010_Beneficiary_Summary_File_Sample_17 - Copy.csv` — malformed duplicate, skip
- Carrier Claims samples 11, 17 — not in scope (using samples 1–5 only)
- PDE samples 11, 17 — not in scope (using samples 1–5 only)
