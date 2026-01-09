#!/usr/bin/env python3
"""
Test script for PortfoliAI ML Service
"""

import sys
import os
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from ml_service import PortfoliAIMLService

def test_survey_prediction():
    """Test survey-based risk prediction"""
    print("Testing Survey Risk Prediction...")
    
    service = PortfoliAIMLService()
    
    # Sample survey data
    survey_data = {
        'age': 30,
        'investment_proportion': '10% - 20%',
        'expected_return': '5% - 10%',
        'investment_horizon': '3-5 years',
        'monitoring_frequency': 'Monthly',
        'equity_rank': 3,
        'fund_rank': 2
    }
    
    try:
        result = service.predict_survey_risk(survey_data)
        print("✅ Survey prediction successful!")
        print(f"Risk Score: {result['risk_score']:.3f}")
        print(f"Risk Category: {result['risk_category']}")
        print(f"Persona: {result['persona']}")
        print(f"Confidence: {result['confidence']:.3f}")
        return True
    except Exception as e:
        print(f"❌ Survey prediction failed: {e}")
        return False

def test_transaction_prediction():
    """Test transaction-based risk prediction"""
    print("\nTesting Transaction Risk Prediction...")
    
    service = PortfoliAIMLService()
    
    # Sample transaction data
    transaction_data = [
        {
            'amount': 5000,
            'asset_id': 'AAPL',
            'asset_type': 'Stock',
            'trade_type': 'buy',
            'timestamp': '2024-01-15'
        },
        {
            'amount': 3000,
            'asset_id': 'VTSAX',
            'asset_type': 'Fund',
            'trade_type': 'buy',
            'timestamp': '2024-01-20'
        },
        {
            'amount': 2000,
            'asset_id': 'TLT',
            'asset_type': 'Bond',
            'trade_type': 'buy',
            'timestamp': '2024-01-25'
        }
    ]
    
    try:
        result = service.predict_transaction_risk(transaction_data)
        print("✅ Transaction prediction successful!")
        print(f"Risk Score: {result['risk_score']:.3f}")
        print(f"Risk Category: {result['risk_category']}")
        print(f"Persona: {result['persona']}")
        print(f"Confidence: {result['confidence']:.3f}")
        if result.get('probabilities'):
            print("Probabilities:")
            for category, prob in result['probabilities'].items():
                print(f"  {category}: {prob:.3f}")
        return True
    except Exception as e:
        print(f"❌ Transaction prediction failed: {e}")
        return False

def test_meta_prediction():
    """Test meta risk prediction"""
    print("\nTesting Meta Risk Prediction...")
    
    service = PortfoliAIMLService()
    
    # Sample survey data
    survey_data = {
        'age': 35,
        'investment_proportion': '20% - 30%',
        'expected_return': '10% - 15%',
        'investment_horizon': '5+ years',
        'monitoring_frequency': 'Weekly',
        'equity_rank': 4,
        'fund_rank': 3
    }
    
    # Sample transaction data
    transaction_data = [
        {
            'amount': 10000,
            'asset_id': 'TSLA',
            'asset_type': 'Stock',
            'trade_type': 'buy',
            'timestamp': '2024-01-15'
        },
        {
            'amount': 5000,
            'asset_id': 'QQQ',
            'asset_type': 'Fund',
            'trade_type': 'buy',
            'timestamp': '2024-01-20'
        }
    ]
    
    try:
        result = service.predict_meta_risk(survey_data, transaction_data, 0.5)
        print("✅ Meta prediction successful!")
        print(f"Meta Risk Score: {result['meta_risk_score']:.3f}")
        print(f"Risk Bucket: {result['risk_bucket']}")
        print(f"Meta Persona: {result['meta_persona']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Survey Weight: {result['survey_weight']}")
        return True
    except Exception as e:
        print(f"❌ Meta prediction failed: {e}")
        return False

def main():
    """Run all tests"""
    print("PortfoliAI ML Service Test Suite")
    print("=" * 40)
    
    # Check if models directory exists
    models_dir = Path(__file__).parent / "models"
    if not models_dir.exists():
        print("❌ Models directory not found!")
        print("Please ensure the models are in the correct location.")
        return False
    
    # Check if required models exist
    required_models = [
        "tuned_random_forest.pkl",
        "onboarding_scaler.pkl"
    ]
    
    missing_models = []
    for model in required_models:
        if not (models_dir / model).exists():
            missing_models.append(model)
    
    if missing_models:
        print(f"❌ Missing required models: {missing_models}")
        print("Please ensure all required models are present.")
        return False
    
    print("✅ All required models found!")
    
    # Run tests
    tests = [
        test_survey_prediction,
        test_transaction_prediction,
        test_meta_prediction
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ML service is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


