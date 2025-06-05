"""
Readmission Prediction Script
Usage: python predict_readmission.py
"""

import joblib
import pandas as pd
import numpy as np

def load_model():
    """Load the trained readmission prediction model"""
    model = joblib.load('readmission_model_logistic_regression.joblib')
    return model

def predict_readmission(patient_data):
    """
    Predict readmission probability for a patient
    
    Args:
        patient_data (dict or pd.DataFrame): Patient features
        
    Returns:
        dict: Prediction results
    """
    model = load_model()
    
    # Convert to DataFrame if dict
    if isinstance(patient_data, dict):
        patient_data = pd.DataFrame([patient_data])
    
    # Make prediction
    prob = model.predict_proba(patient_data)[:, 1][0]
    prediction = model.predict(patient_data)[0]
    
    # Risk category
    if prob >= 0.5:
        risk_category = "Very High" if prob >= 0.8 else "High"
    elif prob >= 0.3:
        risk_category = "Moderate"
    elif prob >= 0.1:
        risk_category = "Low"
    else:
        risk_category = "Very Low"
    
    return {
        'readmission_probability': prob,
        'readmission_prediction': bool(prediction),
        'risk_category': risk_category,
        'confidence': 'High' if prob >= 0.8 or prob <= 0.2 else 'Moderate'
    }

if __name__ == "__main__":
    # Example usage
    sample_patient = {
        # Add sample patient features here
        'AGE_AT_ADMISSION': 75,
        'LOS_CALCULATED': 5,
        'CHRONIC_CONDITION_COUNT': 3,
        # ... other features
    }
    
    result = predict_readmission(sample_patient)
    print(f"Readmission Probability: {result['readmission_probability']:.3f}")
    print(f"Risk Category: {result['risk_category']}")
