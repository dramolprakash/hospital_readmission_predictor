"""
Hospital Readmission Prediction API
Production-ready FastAPI application for clinical decision support
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import joblib
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import os
from typing import Optional, Dict, List
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hospital Readmission Risk Predictor API",
    description="Clinical decision support API for predicting 30-day readmission risk",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientData(BaseModel):
    """Patient data model with comprehensive validation"""
    
    # Demographics
    age_at_admission: float = Field(..., ge=18, le=120, description="Patient age in years")
    gender: int = Field(..., ge=1, le=2, description="Gender (1=Male, 2=Female)")
    race_ethnicity: Optional[int] = Field(1, ge=1, le=5, description="Race/ethnicity code")
    
    # Clinical data
    los_calculated: int = Field(..., ge=1, le=365, description="Length of stay in days")
    chronic_condition_count: int = Field(..., ge=0, le=11, description="Number of chronic conditions")
    admission_month: int = Field(..., ge=1, le=12, description="Month of admission")
    admission_quarter: int = Field(..., ge=1, le=4, description="Quarter of admission")
    
    # Diagnosis and complexity
    icd9_dgns_cd_1: Optional[str] = Field(None, description="Primary diagnosis code")
    clm_drg_cd: Optional[str] = Field(None, description="DRG code")
    
    # Prior utilization
    prior_admissions_30d: int = Field(0, ge=0, le=10, description="Prior admissions in 30 days")
    prior_admissions_90d: int = Field(0, ge=0, le=20, description="Prior admissions in 90 days")
    prior_admissions_180d: int = Field(0, ge=0, le=30, description="Prior admissions in 180 days")
    prior_admissions_365d: int = Field(0, ge=0, le=50, description="Prior admissions in 365 days")
    
    # Risk scores (computed features)
    comprehensive_risk_score: Optional[float] = Field(None, description="Comprehensive risk score")
    comorbidity_risk_score: Optional[float] = Field(None, description="Comorbidity risk score")
    clinical_complexity_score: Optional[float] = Field(None, description="Clinical complexity score")
    
    # Chronic conditions (boolean flags)
    sp_chf: bool = Field(False, description="Congestive Heart Failure")
    sp_diabetes: bool = Field(False, description="Diabetes")
    sp_copd: bool = Field(False, description="COPD")
    sp_ischmcht: bool = Field(False, description="Ischemic Heart Disease")
    sp_chrnkidn: bool = Field(False, description="Chronic Kidney Disease")
    
    @validator('age_at_admission')
    def validate_age(cls, v):
        if v < 18 or v > 120:
            raise ValueError('Age must be between 18 and 120 years')
        return v
    
    @validator('los_calculated')
    def validate_los(cls, v):
        if v < 1:
            raise ValueError('Length of stay must be at least 1 day')
        return v

class PredictionResponse(BaseModel):
    """Standardized prediction response"""
    patient_id: Optional[str] = None
    readmission_probability: float = Field(..., description="Probability of 30-day readmission")
    risk_category: str = Field(..., description="Risk category (Very Low, Low, Moderate, High, Very High)")
    risk_score: float = Field(..., description="Numerical risk score")
    confidence: str = Field(..., description="Prediction confidence (High, Moderate, Low)")
    intervention_recommended: bool = Field(..., description="Whether clinical intervention is recommended")
    prediction_timestamp: datetime = Field(default_factory=datetime.now)
    
    # Clinical insights
    key_risk_factors: List[str] = Field(..., description="Primary factors driving risk")
    clinical_recommendations: List[str] = Field(..., description="Clinical action recommendations")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    model_loaded: bool
    version: str

# Global model storage
model = None
feature_names = None

def load_model_artifacts():
    """Load model and associated artifacts"""
    global model, feature_names
    
    try:
        model_path = "../models/readmission_model_logistic_regression.joblib"
        model = joblib.load(model_path)
        
        # Load feature names
        feature_names_path = "../models/feature_names.txt"
        with open(feature_names_path, 'r') as f:
            feature_names = [line.strip().split('. ', 1)[1] for line in f.readlines()[3:]]  # Skip header
        
        logger.info(f"Model loaded successfully with {len(feature_names)} features")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return False

def create_feature_vector(patient_data: PatientData) -> pd.DataFrame:
    """Create feature vector from patient data"""
    
    # Base features from patient data
    features = {
        'AGE_AT_ADMISSION': patient_data.age_at_admission,
        'GENDER': patient_data.gender,
        'LOS_CALCULATED': patient_data.los_calculated,
        'CHRONIC_CONDITION_COUNT': patient_data.chronic_condition_count,
        'ADMISSION_MONTH': patient_data.admission_month,
        'ADMISSION_QUARTER': patient_data.admission_quarter,
        'PRIOR_ADMISSIONS_30D': patient_data.prior_admissions_30d,
        'PRIOR_ADMISSIONS_90D': patient_data.prior_admissions_90d,
        'PRIOR_ADMISSIONS_180D': patient_data.prior_admissions_180d,
        'PRIOR_ADMISSIONS_365D': patient_data.prior_admissions_365d,
    }
    
    # Add chronic condition flags
    features.update({
        'SP_CHF': patient_data.sp_chf,
        'SP_DIABETES': patient_data.sp_diabetes,
        'SP_COPD': patient_data.sp_copd,
        'SP_ISCHMCHT': patient_data.sp_ischmcht,
        'SP_CHRNKIDN': patient_data.sp_chrnkidn,
    })
    
    # Create engineered features
    features.update(_create_engineered_features(patient_data, features))
    
    # Create DataFrame with all required features
    feature_df = pd.DataFrame([features])
    
    # Add missing features with default values
    for feature_name in feature_names:
        if feature_name not in feature_df.columns:
            feature_df[feature_name] = 0
    
    # Ensure correct order
    feature_df = feature_df[feature_names]
    
    return feature_df

def _create_engineered_features(patient_data: PatientData, base_features: dict) -> dict:
    """Create engineered features based on business rules"""
    
    engineered = {}
    
    # Comprehensive risk score
    risk_score = (
        patient_data.age_at_admission * 0.1 +
        patient_data.chronic_condition_count * 0.15 +
        patient_data.prior_admissions_365d * 0.2 +
        patient_data.los_calculated * 0.05
    )
    engineered['COMPREHENSIVE_RISK_SCORE'] = risk_score
    
    # Comorbidity scoring
    comorbidity_score = patient_data.chronic_condition_count
    if patient_data.sp_chf and patient_data.sp_diabetes:
        comorbidity_score += 1  # Diabetes+CHF combo
    engineered['COMORBIDITY_RISK_SCORE'] = comorbidity_score
    
    # Clinical complexity
    complexity = 0
    if patient_data.chronic_condition_count >= 5:
        complexity += 2
    if patient_data.los_calculated >= 7:
        complexity += 1
    if patient_data.prior_admissions_90d >= 2:
        complexity += 1
    engineered['CLINICAL_COMPLEXITY_SCORE'] = complexity
    
    # Risk categories
    engineered['HIGH_COMORBIDITY'] = patient_data.chronic_condition_count >= 5
    engineered['ELDERLY_COMPLEX'] = patient_data.age_at_admission >= 75 and patient_data.chronic_condition_count >= 3
    engineered['FREQUENT_FLYER'] = patient_data.prior_admissions_365d >= 3
    engineered['LONG_STAY'] = patient_data.los_calculated >= 7
    
    # Age categories
    if patient_data.age_at_admission >= 85:
        age_cat = 4
    elif patient_data.age_at_admission >= 75:
        age_cat = 3
    elif patient_data.age_at_admission >= 65:
        age_cat = 2
    else:
        age_cat = 1
    engineered['AGE_CATEGORY'] = age_cat
    
    # Additional boolean features
    engineered['HAS_CARDIOVASCULAR'] = patient_data.sp_chf or patient_data.sp_ischmcht
    engineered['HAS_METABOLIC'] = patient_data.sp_diabetes
    engineered['HAS_RESPIRATORY'] = patient_data.sp_copd
    engineered['RECENT_ADMISSION_30D'] = patient_data.prior_admissions_30d > 0
    engineered['RECENT_ADMISSION_90D'] = patient_data.prior_admissions_90d > 0
    
    return engineered

def generate_clinical_insights(patient_data: PatientData, probability: float) -> tuple:
    """Generate clinical insights and recommendations"""
    
    risk_factors = []
    recommendations = []
    
    # Identify key risk factors
    if patient_data.chronic_condition_count >= 5:
        risk_factors.append("High chronic disease burden")
        recommendations.append("Consider comprehensive care coordination")
    
    if patient_data.prior_admissions_90d >= 2:
        risk_factors.append("Recent frequent admissions")
        recommendations.append("Evaluate discharge planning and home support")
    
    if patient_data.los_calculated >= 7:
        risk_factors.append("Extended length of stay")
        recommendations.append("Assess for complex medical needs")
    
    if patient_data.age_at_admission >= 75:
        risk_factors.append("Advanced age")
        recommendations.append("Consider geriatric assessment")
    
    if patient_data.sp_chf and patient_data.sp_diabetes:
        risk_factors.append("Diabetes + Heart Failure combination")
        recommendations.append("Intensify medication management and monitoring")
    
    # General recommendations based on risk level
    if probability >= 0.5:
        recommendations.extend([
            "High priority for transitional care management",
            "Schedule follow-up within 7 days",
            "Consider home health services"
        ])
    elif probability >= 0.3:
        recommendations.extend([
            "Standard transitional care",
            "Schedule follow-up within 14 days",
            "Medication reconciliation required"
        ])
    
    return risk_factors, recommendations

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting Hospital Readmission Prediction API...")
    
    if not load_model_artifacts():
        logger.error("Failed to load model artifacts")
        raise RuntimeError("Model loading failed")
    
    logger.info("API startup completed successfully")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        model_loaded=model is not None,
        version="1.0.0"
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_readmission(patient_data: PatientData):
    """
    Predict 30-day readmission risk for a patient
    
    Returns comprehensive risk assessment with clinical recommendations
    """
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Create feature vector
        feature_vector = create_feature_vector(patient_data)
        
        # Make prediction
        probability = model.predict_proba(feature_vector)[0, 1]
        prediction = model.predict(feature_vector)[0]
        
        # Determine risk category
        if probability >= 0.8:
            risk_category = "Very High"
            confidence = "High"
        elif probability >= 0.5:
            risk_category = "High"
            confidence = "High"
        elif probability >= 0.3:
            risk_category = "Moderate"
            confidence = "Moderate"
        elif probability >= 0.1:
            risk_category = "Low"
            confidence = "Moderate"
        else:
            risk_category = "Very Low"
            confidence = "High"
        
        # Generate clinical insights
        risk_factors, recommendations = generate_clinical_insights(patient_data, probability)
        
        # Log prediction for monitoring
        logger.info(f"Prediction made: probability={probability:.3f}, category={risk_category}")
        
        return PredictionResponse(
            readmission_probability=float(probability),
            risk_category=risk_category,
            risk_score=float(probability * 100),
            confidence=confidence,
            intervention_recommended=probability >= 0.3,
            key_risk_factors=risk_factors,
            clinical_recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/model/info")
async def model_info():
    """Get model information and performance metrics"""
    
    model_metadata = {
        "algorithm": "Logistic Regression",
        "features": len(feature_names) if feature_names else 0,
        "performance": {
            "precision": 0.1942,
            "recall": 0.4642,
            "f1_score": 0.2738,
            "auc_roc": 0.6935,
            "accuracy": 0.7506
        },
        "business_impact": {
            "annual_net_savings": 1476000,
            "roi": 45.6,
            "prevention_rate": 11.6
        },
        "clinical_thresholds": {
            "high_risk": 0.5,
            "moderate_risk": 0.3,
            "low_risk": 0.1
        }
    }
    
    return model_metadata

@app.post("/predict/batch")
async def predict_batch(patients: List[PatientData]):
    """Batch prediction endpoint for multiple patients"""
    
    if len(patients) > 100:
        raise HTTPException(status_code=400, detail="Batch size limited to 100 patients")
    
    predictions = []
    for i, patient in enumerate(patients):
        try:
            prediction = await predict_readmission(patient)
            prediction.patient_id = f"patient_{i+1}"
            predictions.append(prediction)
        except Exception as e:
            logger.error(f"Error predicting for patient {i+1}: {str(e)}")
            # Continue with other patients
    
    return {"predictions": predictions, "total_processed": len(predictions)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)