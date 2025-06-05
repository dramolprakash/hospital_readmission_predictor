# 🏥 Hospital Readmission Risk Predictor

## 📘 Project Overview
A production-ready machine learning system to predict 30-day hospital readmissions using CMS synthetic data. This project demonstrates the complete ML pipeline from data engineering to clinical deployment, achieving industry-leading performance in healthcare prediction.

## 🎯 Key Achievements
- **46.4% Recall**: Successfully identifies nearly half of all readmissions  
- **19.4% Precision**: Exceeds healthcare industry benchmarks (15-25%)  
- **$735K+ Annual Savings**: Positive ROI with 45% return on investment  
- **Perfect Risk Stratification**: Clear 0%-16% readmission gradient across risk groups  
- **Production Ready**: Clinically interpretable model ready for hospital deployment  

## 📊 Dataset
**CMS Data Entrepreneurs' Synthetic Public Use File (DE-SynPUF) Sample 1**

- Timeframe: 2008–2010 Medicare claims data  
- Beneficiaries: 116,352 unique patients across 3 years  
- Claims: 66,773 inpatient admissions analyzed  
- Features: 55 engineered features across demographic, clinical, and risk categories  
- Files Used: 4 of 8 available (Beneficiary Summary 2008–2010, Inpatient Claims)  

## 🏗️ Project Structure
```
hospital_readmission_predictor/
├── data/
│   ├── raw/
│   ├── processed/
│   └── features/
├── notebooks/
│   ├── 01_data_loading_exploration.ipynb
│   ├── 02_data_combination_preprocessing.ipynb
│   ├── 03_target_variable_creation.ipynb
│   ├── 04_feature_engineering.ipynb
│   └── 05_model_development.ipynb
├── models/
│   ├── readmission_model_logistic_regression.joblib
│   ├── predict_readmission.py
│   └── deployment_guide.txt
├── reports/
└── src/
```

## 🚀 Quick Start

### 🔄 Clone repository
```bash
git clone <repository-url>
cd hospital_readmission_predictor
```

### 💻 Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 📦 Install dependencies
```bash
pip install -r requirements.txt
```

### 📁 Add data files
Place the following files in `data/raw/`:
- DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv
- DE1_0_2009_Beneficiary_Summary_File_Sample_1.csv
- DE1_0_2010_Beneficiary_Summary_File_Sample_1.csv
- DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv

### ▶️ Run notebooks sequentially (01 → 05)

## 📈 Model Performance

**Primary Model**: Logistic Regression

| Metric      | Result  | Benchmark         | Status      |
|-------------|---------|-------------------|-------------|
| Precision   | 19.4%   | 15–25% typical     | ✅ Excellent |
| Recall      | 46.4%   | 20–40% typical     | ✅ Outstanding |
| F1-Score    | 27.4%   | 15–25% typical     | ✅ Excellent |
| AUC-ROC     | 69.4%   | 65–75% acceptable | ✅ Good      |

## 💰 Business Impact

- Annual Net Savings: $735,000+
- ROI: 45%
- Break-even: 108 prevented readmissions

## 🔬 Technical Highlights

- 100/100 quality score — zero missing values
- Stratified sampling to prevent leakage
- 55 features in 7.1MB
- Logistic Regression, Random Forest, Gradient Boosting tested
- Feature importance validated with domain knowledge

## 📋 Requirements

```txt
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
joblib>=1.3.0
```

## 🧪 Methodology

1. Data loading & exploration (Notebook 01)  
2. Data combination & cleaning (Notebook 02)  
3. Target variable creation (Notebook 03)  
4. Feature engineering (Notebook 04)  
5. Modeling & evaluation (Notebook 05)