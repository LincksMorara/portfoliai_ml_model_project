"""
Survey Mapper - Redesigned UX to Backend ML Features
Maps user-friendly questions to existing model features WITHOUT retraining.
"""

def map_redesigned_survey_to_backend(answers):
    """
    Maps redesigned survey answers to backend ML model format.
    
    Args:
        answers: Dict with keys like 'happiness_outcome', 'horizon', 'risk_slider', etc.
        
    Returns:
        Dict with backend feature names matching ml_service.py expectations
    """
    
    # Initialize with defaults
    backend = {
        'age': 35,
        'gender': 'male',
        'education_level': 3,
        'occupation': 'Salaried',
        'invests': True,
        'investment_proportion': '20% - 30%',
        'expected_return': '10% - 15%',
        'investment_horizon': '3-5 years',
        'monitoring_frequency': 'Monthly',
        'equity_rank': 4,
        'fund_rank': 4,
        'invests_stock': True,
        'main_avenue': 'Mutual Funds'
    }
    
    # Q1: Happiness Outcome (Expected Return)
    happiness = answers.get('happiness_outcome', 'b')
    if happiness == 'a':  # $10,500 (5%)
        backend['expected_return'] = '5% - 10%'
        backend['main_avenue'] = 'Fixed Deposits'
        backend['equity_rank'] = 2
    elif happiness == 'b':  # $11,000 (10%)
        backend['expected_return'] = '10% - 15%'
        backend['main_avenue'] = 'Mutual Funds'
        backend['equity_rank'] = 4
    else:  # c: $11,500+ (15%+)
        backend['expected_return'] = '15% and above'
        backend['main_avenue'] = 'Equity'
        backend['equity_rank'] = 6
    
    # Q2: Investment Horizon
    horizon_map = {
        'a': '1-3 years',
        'b': '3-5 years',
        'c': '5+ years'
    }
    backend['investment_horizon'] = horizon_map.get(answers.get('horizon', 'b'), '3-5 years')
    
    # Q3: Risk Tolerance Slider (1-10)
    risk_level = int(answers.get('risk_slider', 5))
    backend['equity_rank'] = min(7, max(1, int(risk_level * 0.7)))
    backend['fund_rank'] = min(7, max(1, 8 - int(risk_level * 0.5)))
    
    if risk_level <= 3:
        backend['expected_return'] = '5% - 10%'
    elif risk_level <= 7:
        backend['expected_return'] = '10% - 15%'
    else:
        backend['expected_return'] = '15% and above'
    
    # Q4: Market Reaction (STRONGEST SIGNAL)
    reaction = answers.get('market_reaction', 'b')
    if reaction == 'a':  # Sell everything
        backend['equity_rank'] = 1
        backend['fund_rank'] = 2
        backend['invests_stock'] = False
        backend['main_avenue'] = 'Fixed Deposits'
        backend['expected_return'] = '5% - 10%'
    elif reaction == 'c':  # Buy more
        backend['equity_rank'] = 7
        backend['fund_rank'] = 6
        backend['invests_stock'] = True
        backend['main_avenue'] = 'Equity'
        backend['expected_return'] = '15% and above'
    else:  # Wait and watch
        backend['invests_stock'] = True
    
    # Q5: Financial Knowledge Slider (1-10)
    knowledge = int(answers.get('knowledge_slider', 5))
    if knowledge <= 2:
        backend['education_level'] = 1
        backend['investment_proportion'] = '10% - 20%'
    elif knowledge <= 4:
        backend['education_level'] = 2
        backend['investment_proportion'] = '10% - 20%'
    elif knowledge <= 6:
        backend['education_level'] = 3
        backend['investment_proportion'] = '20% - 30%'
    elif knowledge <= 8:
        backend['education_level'] = 4
        backend['investment_proportion'] = '30% - 40%'
    else:
        backend['education_level'] = 5
        backend['investment_proportion'] = '30% - 40%'
    
    # Q6: Income Stability → Occupation
    stability = answers.get('income_stability', 'a')
    if stability == 'a':  # Highly stable
        backend['occupation'] = 'Salaried'
    elif stability == 'c':  # Irregular
        backend['occupation'] = 'Self-employed'
        backend['investment_proportion'] = '30% - 40%'
    else:
        backend['occupation'] = 'Salaried'
    
    # Q7: Investment Experience
    experience = answers.get('experience', 'b')
    if experience == 'a':  # None
        backend['invests'] = False
        backend['invests_stock'] = False
        backend['equity_rank'] = min(backend['equity_rank'], 3)
    elif experience == 'c':  # 4+ years
        backend['invests'] = True
        backend['invests_stock'] = True
        backend['equity_rank'] = max(backend['equity_rank'], 5)
    else:  # 1-3 years
        backend['invests'] = True
        backend['invests_stock'] = True
    
    # Q8: Age Group
    age_map = {'a': 25, 'b': 40, 'c': 60}
    backend['age'] = age_map.get(answers.get('age_group', 'b'), 40)
    
    if answers.get('age_group') == 'a':  # Young
        backend['investment_horizon'] = '5+ years'
    elif answers.get('age_group') == 'c':  # Near retirement
        backend['equity_rank'] = min(backend['equity_rank'], 4)
    
    # Q9: Financial Goals
    goal = answers.get('goal', 'b')
    if goal == 'a':  # Preserve wealth
        backend['main_avenue'] = 'Fixed Deposits'
        backend['expected_return'] = '5% - 10%'
        backend['equity_rank'] = min(backend['equity_rank'], 2)
    elif goal == 'c':  # Maximize returns
        backend['main_avenue'] = 'Equity'
        backend['expected_return'] = '15% and above'
        backend['equity_rank'] = max(backend['equity_rank'], 6)
        backend['invests_stock'] = True
    else:  # Grow steadily
        backend['main_avenue'] = 'Mutual Funds'
        backend['fund_rank'] = max(backend['fund_rank'], 5)
    
    # Q10: Loss Tolerance
    loss_map = {'a': 5, 'b': 15, 'c': 30, 'd': 50}
    loss_pct = loss_map.get(answers.get('loss_tolerance', 'b'), 15)
    
    if loss_pct <= 5:
        backend['equity_rank'] = min(backend['equity_rank'], 2)
        backend['main_avenue'] = 'Fixed Deposits'
    elif loss_pct >= 30:
        backend['equity_rank'] = max(backend['equity_rank'], 5)
    
    # Q11: Liquidity Needs → Investment Horizon
    liquidity = answers.get('liquidity', 'b')
    if liquidity == 'a':  # Very important
        backend['investment_horizon'] = '1-3 years'
        backend['main_avenue'] = 'Mutual Funds'
    elif liquidity == 'c':  # Not important
        if backend['investment_horizon'] == '1-3 years':
            backend['investment_horizon'] = '3-5 years'
    
    # Q12: Diversification Preference
    diversification = answers.get('diversification', 'b')
    if diversification == 'a':  # Few focused bets
        backend['main_avenue'] = 'Equity'
        backend['equity_rank'] = 7
        backend['fund_rank'] = 2
        backend['invests_stock'] = True
    elif diversification == 'c':  # Broad diversification
        backend['main_avenue'] = 'Mutual Funds'
        backend['fund_rank'] = 7
        backend['equity_rank'] = 4
    else:  # Mix of both
        backend['fund_rank'] = 5
        backend['equity_rank'] = 5
    
    # Q13: Monitoring Frequency
    monitoring_map = {
        'a': 'Quarterly',
        'b': 'Quarterly',
        'c': 'Monthly',
        'd': 'Weekly',
        'e': 'Daily'
    }
    backend['monitoring_frequency'] = monitoring_map.get(answers.get('monitoring', 'c'), 'Monthly')
    
    if answers.get('monitoring') in ['d', 'e']:  # Weekly or Daily
        backend['equity_rank'] = min(7, backend['equity_rank'] + 1)
        backend['invests_stock'] = True
    
    # FINAL CONSISTENCY CHECK
    if not backend['invests']:
        backend['invests_stock'] = False
        backend['equity_rank'] = min(backend['equity_rank'], 3)
    
    if backend['main_avenue'] == 'Fixed Deposits':
        backend['expected_return'] = '5% - 10%'
        backend['invests_stock'] = False
    
    if backend['equity_rank'] >= 6:
        backend['invests_stock'] = True
        backend['invests'] = True
    
    return backend


def get_risk_profile_summary(backend_data):
    """
    Generate human-readable summary of the mapped profile.
    """
    risk_score_estimate = {
        'Fixed Deposits': 0.2,
        'Bonds': 0.3,
        'Mutual Funds': 0.5,
        'Equity': 0.8
    }.get(backend_data['main_avenue'], 0.5)
    
    # Adjust based on equity rank
    risk_score_estimate += (backend_data['equity_rank'] - 4) * 0.05
    risk_score_estimate = max(0.0, min(1.0, risk_score_estimate))
    
    if risk_score_estimate < 0.3:
        category = "Conservative"
        persona = "Steady Saver"
    elif risk_score_estimate < 0.6:
        category = "Comfortable"
        persona = "Strategic Balancer"
    else:
        category = "Enthusiastic"
        persona = "Risk Seeker"
    
    return {
        'estimated_risk_score': risk_score_estimate,
        'category': category,
        'persona': persona,
        'main_avenue': backend_data['main_avenue'],
        'expected_return': backend_data['expected_return']
    }







