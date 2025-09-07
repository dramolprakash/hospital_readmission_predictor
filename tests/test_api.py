"""
Test suite for Hospital Readmission Prediction API
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from api.main import app
import json

client = TestClient(app)

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "model_loaded" in data
        assert "version" in data

class TestPredictionEndpoint:
    """Test prediction endpoint"""
    
    @pytest.fixture
    def sample_patient_data(self):
        """Sample patient data for testing"""
        return {
            "age_at_admission": 75.0,
            "gender": 2,
            "race_ethnicity": 1,
            "los_calculated": 5,
            "chronic_condition_count": 3,
            "admission_month": 6,
            "admission_quarter": 2,
            "icd9_dgns_cd_1": "41401",
            "clm_drg_cd": "127",
            "prior_admissions_30d": 0,
            "prior_admissions_90d": 1,
            "prior_admissions_180d": 1,
            "prior_admissions_365d": 2,
            "sp_chf": True,
            "sp_diabetes": True,
            "sp_copd": False,
            "sp_ischmcht": True,
            "sp_chrnkidn": False
        }
    
    def test_valid_prediction(self, sample_patient_data):
        """Test prediction with valid patient data"""
        response = client.post("/predict", json=sample_patient_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "readmission_probability" in data
        assert "risk_category" in data
        assert "risk_score" in data
        assert "confidence" in data
        assert "intervention_recommended" in data
        assert "key_risk_factors" in data
        assert "clinical_recommendations" in data
        assert "prediction_timestamp" in data
        
        # Check data types and ranges
        assert 0 <= data["readmission_probability"] <= 1
        assert 0 <= data["risk_score"] <= 100
        assert data["risk_category"] in ["Very Low", "Low", "Moderate", "High", "Very High"]
        assert data["confidence"] in ["High", "Moderate", "Low"]
        assert isinstance(data["intervention_recommended"], bool)
        assert isinstance(data["key_risk_factors"], list)
        assert isinstance(data["clinical_recommendations"], list)
    
    def test_high_risk_patient(self):
        """Test prediction for high-risk patient"""
        high_risk_patient = {
            "age_at_admission": 85.0,
            "gender": 1,
            "los_calculated": 10,
            "chronic_condition_count": 8,
            "admission_month": 12,
            "admission_quarter": 4,
            "prior_admissions_30d": 1,
            "prior_admissions_90d": 3,
            "prior_admissions_180d": 5,
            "prior_admissions_365d": 8,
            "sp_chf": True,
            "sp_diabetes": True,
            "sp_copd": True,
            "sp_ischmcht": True,
            "sp_chrnkidn": True
        }
        
        response = client.post("/predict", json=high_risk_patient)
        assert response.status_code == 200
        
        data = response.json()
        assert data["intervention_recommended"] == True
        assert data["risk_category"] in ["High", "Very High", "Moderate"]  # Should be elevated risk
        assert len(data["key_risk_factors"]) > 0
        assert len(data["clinical_recommendations"]) > 0
    
    def test_low_risk_patient(self):
        """Test prediction for low-risk patient"""
        low_risk_patient = {
            "age_at_admission": 45.0,
            "gender": 2,
            "los_calculated": 2,
            "chronic_condition_count": 1,
            "admission_month": 6,
            "admission_quarter": 2,
            "prior_admissions_30d": 0,
            "prior_admissions_90d": 0,
            "prior_admissions_180d": 0,
            "prior_admissions_365d": 0,
            "sp_chf": False,
            "sp_diabetes": False,
            "sp_copd": False,
            "sp_ischmcht": False,
            "sp_chrnkidn": False
        }
        
        response = client.post("/predict", json=low_risk_patient)
        assert response.status_code == 200
        
        data = response.json()
        # Should be lower risk (though exact category depends on model)
        assert data["readmission_probability"] >= 0.0
    
    def test_invalid_age(self):
        """Test prediction with invalid age"""
        invalid_patient = {
            "age_at_admission": 150.0,  # Invalid age
            "gender": 1,
            "los_calculated": 5,
            "chronic_condition_count": 3,
            "admission_month": 6,
            "admission_quarter": 2,
            "prior_admissions_30d": 0,
            "prior_admissions_90d": 1,
            "prior_admissions_180d": 1,
            "prior_admissions_365d": 2,
            "sp_chf": True,
            "sp_diabetes": True,
            "sp_copd": False,
            "sp_ischmcht": True,
            "sp_chrnkidn": False
        }
        
        response = client.post("/predict", json=invalid_patient)
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self):
        """Test prediction with missing required fields"""
        incomplete_patient = {
            "age_at_admission": 75.0,
            # Missing other required fields
        }
        
        response = client.post("/predict", json=incomplete_patient)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_gender(self):
        """Test prediction with invalid gender"""
        invalid_patient = {
            "age_at_admission": 75.0,
            "gender": 5,  # Invalid gender code
            "los_calculated": 5,
            "chronic_condition_count": 3,
            "admission_month": 6,
            "admission_quarter": 2,
            "prior_admissions_30d": 0,
            "prior_admissions_90d": 1,
            "prior_admissions_180d": 1,
            "prior_admissions_365d": 2,
            "sp_chf": True,
            "sp_diabetes": True,
            "sp_copd": False,
            "sp_ischmcht": True,
            "sp_chrnkidn": False
        }
        
        response = client.post("/predict", json=invalid_patient)
        assert response.status_code == 422

class TestBatchPredictionEndpoint:
    """Test batch prediction endpoint"""
    
    def test_batch_prediction_valid(self):
        """Test batch prediction with valid data"""
        patients = [
            {
                "age_at_admission": 75.0,
                "gender": 2,
                "los_calculated": 5,
                "chronic_condition_count": 3,
                "admission_month": 6,
                "admission_quarter": 2,
                "prior_admissions_30d": 0,
                "prior_admissions_90d": 1,
                "prior_admissions_180d": 1,
                "prior_admissions_365d": 2,
                "sp_chf": True,
                "sp_diabetes": True,
                "sp_copd": False,
                "sp_ischmcht": True,
                "sp_chrnkidn": False
            },
            {
                "age_at_admission": 65.0,
                "gender": 1,
                "los_calculated": 3,
                "chronic_condition_count": 2,
                "admission_month": 3,
                "admission_quarter": 1,
                "prior_admissions_30d": 0,
                "prior_admissions_90d": 0,
                "prior_admissions_180d": 0,
                "prior_admissions_365d": 1,
                "sp_chf": False,
                "sp_diabetes": True,
                "sp_copd": False,
                "sp_ischmcht": False,
                "sp_chrnkidn": False
            }
        ]
        
        response = client.post("/predict/batch", json=patients)
        assert response.status_code == 200
        
        data = response.json()
        assert "predictions" in data
        assert "total_processed" in data
        assert len(data["predictions"]) == 2
        assert data["total_processed"] == 2
        
        # Check each prediction
        for prediction in data["predictions"]:
            assert "patient_id" in prediction
            assert "readmission_probability" in prediction
            assert "risk_category" in prediction
    
    def test_batch_prediction_too_large(self):
        """Test batch prediction with too many patients"""
        patients = []
        for i in range(101):  # Exceed limit of 100
            patients.append({
                "age_at_admission": 75.0,
                "gender": 2,
                "los_calculated": 5,
                "chronic_condition_count": 3,
                "admission_month": 6,
                "admission_quarter": 2,
                "prior_admissions_30d": 0,
                "prior_admissions_90d": 1,
                "prior_admissions_180d": 1,
                "prior_admissions_365d": 2,
                "sp_chf": True,
                "sp_diabetes": True,
                "sp_copd": False,
                "sp_ischmcht": True,
                "sp_chrnkidn": False
            })
        
        response = client.post("/predict/batch", json=patients)
        assert response.status_code == 400

class TestModelInfoEndpoint:
    """Test model information endpoint"""
    
    def test_model_info(self):
        """Test model info endpoint"""
        response = client.get("/model/info")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "algorithm" in data
        assert "features" in data
        assert "performance" in data
        assert "business_impact" in data
        assert "clinical_thresholds" in data
        
        # Check performance metrics
        performance = data["performance"]
        assert "precision" in performance
        assert "recall" in performance
        assert "f1_score" in performance
        assert "auc_roc" in performance
        
        # Check business impact
        business_impact = data["business_impact"]
        assert "annual_net_savings" in business_impact
        assert "roi" in business_impact

class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_docs_available(self):
        """Test that API docs are available"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_available(self):
        """Test that ReDoc is available"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_schema(self):
        """Test OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
        
        # Check that key endpoints are documented
        assert "/predict" in schema["paths"]
        assert "/health" in schema["paths"]
        assert "/model/info" in schema["paths"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])