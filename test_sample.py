"""
Sample API test script - demonstrates API usage
"""

import requests
import json
from datetime import datetime

# API base URL (adjust for your deployment)
BASE_URL = "http://localhost:8000"  # Local development
# BASE_URL = "http://your-alb-url.com"  # Production

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Status: {data['status']}")
        print(f"   Model loaded: {data['model_loaded']}")
        print(f"   Version: {data['version']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
    
    return response.status_code == 200

def test_model_info():
    """Test the model info endpoint"""
    print("\n🔍 Testing model info...")
    
    response = requests.get(f"{BASE_URL}/model/info")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Model info retrieved")
        print(f"   Algorithm: {data['algorithm']}")
        print(f"   Features: {data['features']}")
        print(f"   AUC-ROC: {data['performance']['auc_roc']}")
        print(f"   Precision: {data['performance']['precision']}")
        print(f"   Recall: {data['performance']['recall']}")
        print(f"   Annual Savings: ${data['business_impact']['annual_net_savings']:,.0f}")
    else:
        print(f"❌ Model info failed: {response.status_code}")
    
    return response.status_code == 200

def test_single_prediction():
    """Test single patient prediction"""
    print("\n🔍 Testing single prediction...")
    
    # High-risk patient example
    high_risk_patient = {
        "age_at_admission": 82.0,
        "gender": 1,  # Male
        "race_ethnicity": 1,
        "los_calculated": 8,
        "chronic_condition_count": 6,
        "admission_month": 12,
        "admission_quarter": 4,
        "icd9_dgns_cd_1": "41401",  # CHF
        "clm_drg_cd": "127",
        "prior_admissions_30d": 1,
        "prior_admissions_90d": 2,
        "prior_admissions_180d": 3,
        "prior_admissions_365d": 5,
        "sp_chf": True,
        "sp_diabetes": True,
        "sp_copd": True,
        "sp_ischmcht": True,
        "sp_chrnkidn": True
    }
    
    response = requests.post(f"{BASE_URL}/predict", json=high_risk_patient)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Prediction successful")
        print(f"   Readmission Probability: {data['readmission_probability']:.3f}")
        print(f"   Risk Category: {data['risk_category']}")
        print(f"   Risk Score: {data['risk_score']:.1f}")
        print(f"   Confidence: {data['confidence']}")
        print(f"   Intervention Recommended: {data['intervention_recommended']}")
        print(f"   Key Risk Factors: {', '.join(data['key_risk_factors'][:3])}")
        print(f"   Clinical Recommendations: {len(data['clinical_recommendations'])} items")
    else:
        print(f"❌ Prediction failed: {response.status_code}")
        if response.text:
            print(f"   Error: {response.text}")
    
    return response.status_code == 200

def test_low_risk_prediction():
    """Test low-risk patient prediction"""
    print("\n🔍 Testing low-risk prediction...")
    
    # Low-risk patient example
    low_risk_patient = {
        "age_at_admission": 45.0,
        "gender": 2,  # Female
        "race_ethnicity": 1,
        "los_calculated": 2,
        "chronic_condition_count": 1,
        "admission_month": 6,
        "admission_quarter": 2,
        "prior_admissions_30d": 0,
        "prior_admissions_90d": 0,
        "prior_admissions_180d": 0,
        "prior_admissions_365d": 0,
        "sp_chf": False,
        "sp_diabetes": True,  # Only diabetes
        "sp_copd": False,
        "sp_ischmcht": False,
        "sp_chrnkidn": False
    }
    
    response = requests.post(f"{BASE_URL}/predict", json=low_risk_patient)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Low-risk prediction successful")
        print(f"   Readmission Probability: {data['readmission_probability']:.3f}")
        print(f"   Risk Category: {data['risk_category']}")
        print(f"   Intervention Recommended: {data['intervention_recommended']}")
    else:
        print(f"❌ Low-risk prediction failed: {response.status_code}")
    
    return response.status_code == 200

def test_batch_prediction():
    """Test batch prediction"""
    print("\n🔍 Testing batch prediction...")
    
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
            "age_at_admission": 68.0,
            "gender": 1,
            "los_calculated": 3,
            "chronic_condition_count": 2,
            "admission_month": 9,
            "admission_quarter": 3,
            "prior_admissions_30d": 0,
            "prior_admissions_90d": 0,
            "prior_admissions_180d": 1,
            "prior_admissions_365d": 1,
            "sp_chf": False,
            "sp_diabetes": True,
            "sp_copd": True,
            "sp_ischmcht": False,
            "sp_chrnkidn": False
        }
    ]
    
    response = requests.post(f"{BASE_URL}/predict/batch", json=patients)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Batch prediction successful")
        print(f"   Total processed: {data['total_processed']}")
        
        for i, prediction in enumerate(data['predictions']):
            print(f"   Patient {i+1}: {prediction['risk_category']} ({prediction['readmission_probability']:.3f})")
    else:
        print(f"❌ Batch prediction failed: {response.status_code}")
    
    return response.status_code == 200

def test_error_handling():
    """Test error handling with invalid data"""
    print("\n🔍 Testing error handling...")
    
    # Invalid patient data (age too high)
    invalid_patient = {
        "age_at_admission": 150.0,  # Invalid
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
    
    response = requests.post(f"{BASE_URL}/predict", json=invalid_patient)
    
    if response.status_code == 422:
        print(f"✅ Error handling works correctly")
        print(f"   Status code: {response.status_code}")
        print(f"   Validation error returned as expected")
    else:
        print(f"❌ Error handling failed: Expected 422, got {response.status_code}")
    
    return response.status_code == 422

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting comprehensive API test suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Model Info", test_model_info),
        ("Single Prediction", test_single_prediction),
        ("Low Risk Prediction", test_low_risk_prediction),
        ("Batch Prediction", test_batch_prediction),
        ("Error Handling", test_error_handling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the API deployment.")
    
    return passed == total

if __name__ == "__main__":
    # Check if API is accessible
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"🌐 API accessible at {BASE_URL}")
            run_comprehensive_test()
        else:
            print(f"❌ API not accessible at {BASE_URL}")
            print("Make sure the API is running locally or update BASE_URL for production")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API at {BASE_URL}")
        print(f"Error: {str(e)}")
        print("\nTo run locally:")
        print("1. cd to project directory")
        print("2. python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
        print("3. Run this test script again")