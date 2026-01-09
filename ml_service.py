"""
PortfoliAI ML Service
Handles model loading, inference, and risk profiling for the PortfoliAI application.
"""

import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfoliAIMLService:
    """Main ML service class for PortfoliAI risk assessment and profiling."""
    
    def __init__(self, models_dir: str = None):
        """Initialize the ML service with model directory."""
        if models_dir is None:
            models_dir = Path(__file__).parent / "models"
        
        self.models_dir = Path(models_dir)
        self.models = {}
        self.encoders = None
        
        # Load models and encoders
        self._load_models()
        self._load_encoders()
    
    def _load_models(self):
        """Load all trained models from the models directory."""
        try:
            # Load NEW properly trained survey models (Nov 2024)
            survey_models_dir = self.models_dir.parent / "portfoliai_survey_models_20251029_075727"
            
            if survey_models_dir.exists():
                regressor_new_path = survey_models_dir / "risk_score_model_20251029_075727.pkl"
                classifier_new_path = survey_models_dir / "risk_archetype_classifier_20251029_075727.pkl"
                metadata_path = survey_models_dir / "model_metadata_20251029_075727.json"
                
                if regressor_new_path.exists():
                    import joblib
                    self.models['survey_regressor'] = joblib.load(regressor_new_path)
                    logger.info("✅ Loaded NEW survey regressor (R²=0.89)")
                    
                if classifier_new_path.exists():
                    import joblib
                    self.models['survey_classifier'] = joblib.load(classifier_new_path)
                    logger.info("✅ Loaded NEW survey classifier (Acc~85%)")
                    
                if metadata_path.exists():
                    import json
                    with open(metadata_path) as f:
                        self.models['survey_metadata'] = json.load(f)
                    logger.info(f"✅ Loaded model metadata ({self.models['survey_metadata']['n_features']} features)")
            
            # Load main behavioral model (try corrected version first)
            rf_path_corrected = self.models_dir / "tuned_random_forest_corrected.pkl"
            rf_path_new = self.models_dir / "tuned_random_forest.pkl"
            rf_path_old = self.models_dir / "tuned_random_forest.pkl"
            
            if rf_path_corrected.exists():
                try:
                    self.models['random_forest'] = pickle.load(open(rf_path_corrected, 'rb'))
                    logger.info("Loaded corrected Random Forest model")
                except Exception as e:
                    logger.warning(f"Could not load corrected Random Forest model: {e}")
                    self.models['random_forest'] = None
            elif rf_path_new.exists():
                try:
                    self.models['random_forest'] = pickle.load(open(rf_path_new, 'rb'))
                    logger.info("Loaded new Random Forest model")
                except Exception as e:
                    logger.warning(f"Could not load new Random Forest model: {e}")
                    self.models['random_forest'] = None
            elif rf_path_old.exists():
                try:
                    self.models['random_forest'] = pickle.load(open(rf_path_old, 'rb'))
                    logger.info("Loaded old Random Forest model")
                except Exception as e:
                    logger.warning(f"Could not load old Random Forest model: {e}")
                    self.models['random_forest'] = None
            
            # Skip legacy risk classifier (incompatible with current sklearn)
            self.models['risk_classifier'] = None
            logger.info("Skipping legacy risk classifier model (deprecated)")
            
            # SKIP loading old survey models - we have the NEW ones from portfoliai_survey_models_20251029_075727
            # The NEW models are already loaded above and should NOT be overwritten
            if self.models.get('survey_regressor') is None:
                logger.warning("NEW survey models not found, attempting to load old ones...")
                survey_regressor_path_new = self.models_dir / "survey_regressor_new.pkl"
                survey_regressor_path_old = self.models_dir.parent / "data" / "processed" / "survey_rf_regressor.pkl"
                
                if survey_regressor_path_new.exists():
                    try:
                        self.models['survey_regressor'] = pickle.load(open(survey_regressor_path_new, 'rb'))
                        logger.info("Loaded old survey_regressor_new.pkl (NOT RECOMMENDED)")
                    except Exception as e:
                        logger.warning(f"Could not load old survey regressor: {e}")
            
            if self.models.get('survey_classifier') is None:
                survey_classifier_path_new = self.models_dir / "survey_classifier_new.pkl"
                
                if survey_classifier_path_new.exists():
                    try:
                        self.models['survey_classifier'] = pickle.load(open(survey_classifier_path_new, 'rb'))
                        logger.info("Loaded old survey_classifier_new.pkl (NOT RECOMMENDED)")
                    except Exception as e:
                        logger.warning(f"Could not load old survey classifier: {e}")
            
            # Load clustering models
            clusters_path = self.models_dir / "investor_profile_clusters.pkl"
            if clusters_path.exists():
                try:
                    self.models['profile_clusters'] = pickle.load(open(clusters_path, 'rb'))
                    logger.info("Loaded Profile Clusters model")
                except Exception as e:
                    logger.warning(f"Could not load Profile Clusters model: {e}")
                    self.models['profile_clusters'] = None
            
            # Load scalers (try new version first)
            scaler_path_new = self.models_dir / "onboarding_scaler_new.pkl"
            scaler_path_old = self.models_dir / "onboarding_scaler.pkl"
            
            if scaler_path_new.exists():
                try:
                    self.models['onboarding_scaler'] = pickle.load(open(scaler_path_new, 'rb'))
                    logger.info("Loaded new Onboarding Scaler")
                except Exception as e:
                    logger.warning(f"Could not load new Onboarding Scaler: {e}")
                    self.models['onboarding_scaler'] = None
            elif scaler_path_old.exists():
                try:
                    self.models['onboarding_scaler'] = pickle.load(open(scaler_path_old, 'rb'))
                    logger.info("Loaded old Onboarding Scaler")
                except Exception as e:
                    logger.warning(f"Could not load old Onboarding Scaler: {e}")
                    self.models['onboarding_scaler'] = None
            
            # Load profile mappings
            mappings_path = self.models_dir / "profile_mappings.pkl"
            if mappings_path.exists():
                try:
                    self.models['profile_mappings'] = pickle.load(open(mappings_path, 'rb'))
                    logger.info("Loaded Profile Mappings")
                except Exception as e:
                    logger.warning(f"Could not load Profile Mappings: {e}")
                    self.models['profile_mappings'] = None
            
            # Load investor profiles
            profiles_path = self.models_dir / "investor_profiles.pkl"
            if profiles_path.exists():
                try:
                    self.models['investor_profiles'] = pickle.load(open(profiles_path, 'rb'))
                    logger.info("Loaded Investor Profiles")
                except Exception as e:
                    logger.warning(f"Could not load Investor Profiles: {e}")
                    self.models['investor_profiles'] = None
            
            # Check if any models were loaded successfully
            if not any(model is not None for model in self.models.values()):
                logger.warning("No models could be loaded. Using fallback functionality.")
                
        except Exception as e:
            logger.exception("Error loading models: %s", e)
            logger.warning("Using fallback functionality.")
    
    def _load_encoders(self):
        """Load encoders module."""
        try:
            import sys
            import importlib
            sys.path.append(str(Path(__file__).parent / "src"))
            
            # Force reload to pick up changes
            if 'encoders' in sys.modules:
                import encoders
                importlib.reload(encoders)
                from encoders import parse_pct_midpoint, map_horizon_to_years, map_monitoring_to_freq_per_month
            else:
                from encoders import parse_pct_midpoint, map_horizon_to_years, map_monitoring_to_freq_per_month
                
            self.encoders = {
                'parse_pct_midpoint': parse_pct_midpoint,
                'map_horizon_to_years': map_horizon_to_years,
                'map_monitoring_to_freq_per_month': map_monitoring_to_freq_per_month
            }
            logger.info("Loaded encoders")
        except Exception as e:
            logger.error(f"Error loading encoders: {e}")
            raise
    
    def predict_survey_risk(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict risk profile from survey data.
        
        Args:
            survey_data: Dictionary containing survey responses
            
        Returns:
            Dictionary with risk score, category, and persona
        """
        try:
            # Check if we have the NEW regressor model
            if self.models.get('survey_regressor') is None:
                logger.info("Using fallback survey risk prediction (NEW regressor not loaded)")
                return self._fallback_survey_prediction(survey_data)
            
            # Prepare survey features (22 features for new models)
            features = self._prepare_survey_features(survey_data)
            
            # NEW models DON'T need scaling - they were trained on raw features
            # Predict risk score using regressor
            regressor = self.models.get('survey_regressor')
            
            logger.info(f"Using NEW Regressor Model (R²=0.89)")
            logger.info(f"Features ({len(features)} total): {features[:12]}...")  # Show first 12
            
            risk_score = None
            risk_category = None
            
            try:
                risk_score = regressor.predict([features])[0]
                logger.info(f"✅ NEW Regressor predicted risk_score: {risk_score:.4f}")
            except Exception as e:
                logger.error(f"❌ Regressor prediction failed: {e}")
                raise
            
            # Map continuous risk score to categorical archetype
            # Based on training data distribution:
            # Conservative: < 0.3, Comfortable: 0.3-0.6, Enthusiastic: > 0.6
            if risk_score < 0.3:
                risk_category = 'Conservative'
            elif risk_score < 0.6:
                risk_category = 'Comfortable'
            else:
                risk_category = 'Enthusiastic'
            
            logger.info(f"✅ Mapped to archetype: {risk_category}")
            
            # Get persona mapping based on continuous risk score
            persona = self._get_survey_persona(risk_score)
            logger.info(f"✅ Mapped persona: {persona}")
            
            return {
                'risk_score': float(risk_score) if risk_score is not None else 0.0,
                'risk_category': risk_category,
                'persona': persona,
                'confidence': 0.8  # Placeholder confidence score
            }
            
        except Exception as e:
            logger.error(f"Error predicting survey risk: {e}")
            return self._fallback_survey_prediction(survey_data)
    
    def predict_transaction_risk(self, transaction_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict risk profile from transaction data.
        
        Args:
            transaction_data: List of transaction records
            
        Returns:
            Dictionary with behavioral risk score and persona
        """
        try:
            # Check if we have working models
            if self.models.get('random_forest') is None:
                logger.info("Using fallback transaction risk prediction")
                return self._fallback_transaction_prediction(transaction_data)
            
            # Prepare behavioral features from transactions
            features = self._prepare_behavioral_features(transaction_data)
            
            # Predict using Random Forest model
            rf_model = self.models.get('random_forest')
            
            # Make prediction
            prediction = rf_model.predict([features])[0]
            probabilities = rf_model.predict_proba([features])[0]
            
            # Map prediction to persona
            persona = self._get_behavioral_persona(prediction)
            
            # Calculate behavioral risk score
            risk_score = self._calculate_behavioral_risk_score(features)
            
            return {
                'risk_score': float(risk_score),
                'risk_category': prediction,
                'persona': persona,
                'confidence': float(max(probabilities)),
                'probabilities': dict(zip(rf_model.classes_, probabilities))
            }
            
        except Exception as e:
            logger.error(f"Error predicting transaction risk: {e}")
            return self._fallback_transaction_prediction(transaction_data)
    
    def predict_meta_risk(self, survey_data: Dict[str, Any], 
                         transaction_data: List[Dict[str, Any]] = None,
                         survey_weight: float = 0.5) -> Dict[str, Any]:
        """
        Predict meta risk profile combining survey and transaction data.
        
        Args:
            survey_data: Dictionary containing survey responses
            transaction_data: Optional list of transaction records
            survey_weight: Weight for survey data (0-1, default 0.5)
            
        Returns:
            Dictionary with unified risk profile
        """
        try:
            # Get survey risk
            survey_risk = self.predict_survey_risk(survey_data)
            
            # Get transaction risk if available
            transaction_risk = None
            if transaction_data:
                transaction_risk = self.predict_transaction_risk(transaction_data)
            
            # Calculate meta risk score
            if transaction_risk:
                meta_score = (survey_weight * survey_risk['risk_score'] + 
                             (1 - survey_weight) * transaction_risk['risk_score'])
                meta_confidence = (survey_risk['confidence'] + transaction_risk['confidence']) / 2
            else:
                meta_score = survey_risk['risk_score']
                meta_confidence = survey_risk['confidence']
            
            # Determine risk bucket
            risk_bucket = self._get_risk_bucket(meta_score)
            
            # Get meta persona
            meta_persona = self._get_meta_persona(survey_risk, transaction_risk)
            
            return {
                'meta_risk_score': float(meta_score),
                'risk_bucket': risk_bucket,
                'meta_persona': meta_persona,
                'confidence': float(meta_confidence),
                'survey_profile': survey_risk,
                'transaction_profile': transaction_risk,
                'survey_weight': survey_weight
            }
            
        except Exception as e:
            logger.error(f"Error predicting meta risk: {e}")
            return {
                'meta_risk_score': 0.0,
                'risk_bucket': 'Low',
                'meta_persona': 'Steady Saver',
                'confidence': 0.0,
                'survey_profile': survey_risk,
                'transaction_profile': None,
                'survey_weight': survey_weight
            }
    
    def _prepare_survey_features(self, survey_data: Dict[str, Any]) -> List[float]:
        """Prepare survey features for model input."""
        # The NEW models expect 22 features in this order:
        # ['gender_male', 'age', 'education_level', 'invests', 'invest_prop_pct',
        #  'monitor_freq_per_month', 'expected_return_pct', 'horizon_years',
        #  'rank_equity', 'rank_mutuals', 'invests_stock', 'raw_index',
        #  'occupation_Others', 'occupation_Salaried', 'occupation_Self-employed', 'occupation_Student',
        #  'main_avenue_Bonds', 'main_avenue_Equity', 'main_avenue_Fixed Deposits',
        #  'main_avenue_Gold / SGBs', 'main_avenue_Mutual Funds', 'main_avenue_PPF - Public Provident Fund']
        
        logger.info(f"Preparing features from survey_data: {survey_data}")
        features = []
        
        # gender_male (0 for female, 1 for male)
        features.append(1 if survey_data.get('gender', 'male') == 'male' else 0)
        
        # age
        features.append(survey_data.get('age', 35))
        
        # education_level (1-5 scale, default 3)
        features.append(survey_data.get('education_level', 3))
        
        # invests (0 or 1, default 1)
        features.append(1 if survey_data.get('invests', True) else 0)
        
        # invest_prop_pct
        invest_prop = survey_data.get('investment_proportion', '10% - 20%')
        features.append(self.encoders['parse_pct_midpoint'](invest_prop))
        
        # monitor_freq_per_month
        monitor_freq = survey_data.get('monitoring_frequency', 'Monthly')
        features.append(self.encoders['map_monitoring_to_freq_per_month'](monitor_freq))
        
        # expected_return_pct
        expected_return = survey_data.get('expected_return', '5% - 10%')
        features.append(self.encoders['parse_pct_midpoint'](expected_return))
        
        # horizon_years
        horizon = survey_data.get('investment_horizon', '3-5 years')
        features.append(self.encoders['map_horizon_to_years'](horizon))
        
        # rank_equity
        features.append(survey_data.get('equity_rank', 3))
        
        # rank_mutuals
        features.append(survey_data.get('fund_rank', 2))
        
        # invests_stock (0 or 1, default 1)
        features.append(1 if survey_data.get('invests_stock', True) else 0)
        
        # raw_index (default 0)
        features.append(survey_data.get('raw_index', 0))
        
        # One-hot encoded occupation (default: Salaried)
        occupation = survey_data.get('occupation', 'Salaried')
        features.append(1 if occupation == 'Others' else 0)
        features.append(1 if occupation == 'Salaried' else 0)
        features.append(1 if occupation == 'Self-employed' else 0)
        features.append(1 if occupation == 'Student' else 0)
        
        # One-hot encoded main investment avenue (default: Equity)
        main_avenue = survey_data.get('main_avenue', 'Equity')
        features.append(1 if main_avenue == 'Bonds' else 0)
        features.append(1 if main_avenue == 'Equity' else 0)
        features.append(1 if main_avenue == 'Fixed Deposits' else 0)
        features.append(1 if main_avenue == 'Gold / SGBs' else 0)
        features.append(1 if main_avenue == 'Mutual Funds' else 0)
        features.append(1 if main_avenue == 'PPF - Public Provident Fund' else 0)
        
        logger.info(f"Generated feature vector ({len(features)} features): {features}")
        return features
    
    def _prepare_behavioral_features(self, transaction_data: List[Dict[str, Any]]) -> List[float]:
        """Prepare behavioral features from transaction data."""
        if not transaction_data:
            return [0.0] * 8  # Return default features (model expects 8 features)
        
        df = pd.DataFrame(transaction_data)
        
        # Calculate basic metrics
        n_trades = len(df)
        avg_trade_value = df['amount'].mean() if 'amount' in df.columns else 0
        max_trade_value = df['amount'].max() if 'amount' in df.columns else 0
        trade_freq = n_trades / 30 if n_trades > 0 else 0  # Assume 30-day period
        
        # Portfolio composition
        n_assets = df['asset_id'].nunique() if 'asset_id' in df.columns else 0
        
        # Calculate stock/bond/fund shares
        if 'asset_type' in df.columns:
            total_value = df['amount'].sum()
            stock_value = df[df['asset_type'] == 'Stock']['amount'].sum() if total_value > 0 else 0
            bond_value = df[df['asset_type'] == 'Bond']['amount'].sum() if total_value > 0 else 0
            fund_value = df[df['asset_type'] == 'Fund']['amount'].sum() if total_value > 0 else 0
            
            stock_share = stock_value / total_value if total_value > 0 else 0
            bond_share = bond_value / total_value if total_value > 0 else 0
            fund_share = fund_value / total_value if total_value > 0 else 0
        else:
            stock_share = bond_share = fund_share = 0.0
        
        # Create behavioural feature vector (matching the original model's expected 8 features)
        features = [
            n_trades,
            avg_trade_value,
            max_trade_value,
            trade_freq,
            n_assets,
            stock_share,
            bond_share,
            fund_share
        ]
        
        return features
    
    def _get_survey_persona(self, risk_score: float) -> str:
        """Map survey risk score to persona."""
        if risk_score < 0.3:
            return "Steady Saver"
        elif risk_score < 0.6:
            return "Strategic Balancer"
        else:
            return "Risk Seeker"
    
    def _get_behavioral_persona(self, risk_category: str) -> str:
        """Map behavioral risk category to persona."""
        mapping = {
            'Conservative': 'Steady Saver',
            'Income': 'Strategic Balancer',
            'Balanced': 'Strategic Balancer',
            'Aggressive': 'Risk Seeker'
        }
        return mapping.get(risk_category, 'Steady Saver')
    
    def _get_meta_persona(self, survey_risk: Dict[str, Any], 
                         transaction_risk: Optional[Dict[str, Any]]) -> str:
        """Determine meta persona from survey and transaction profiles."""
        if transaction_risk:
            # Combine both profiles
            survey_persona = survey_risk.get('persona', 'Steady Saver')
            transaction_persona = transaction_risk.get('persona', 'Steady Saver')
            
            # Simple logic: if both agree, use that; otherwise use the more conservative
            if survey_persona == transaction_persona:
                return survey_persona
            else:
                # Return more conservative option
                personas = [survey_persona, transaction_persona]
                if 'Steady Saver' in personas:
                    return 'Steady Saver'
                elif 'Strategic Balancer' in personas:
                    return 'Strategic Balancer'
                else:
                    return 'Risk Seeker'
        else:
            return survey_risk.get('persona', 'Steady Saver')
    
    def _calculate_behavioral_risk_score(self, features: List[float]) -> float:
        """Calculate behavioral risk score from features."""
        # Simple weighted combination of key features
        weights = [0.2, 0.3, 0.3, 0.1, 0.1]  # n_trades, avg_trade, max_trade, trade_freq, stock_share
        score = sum(w * f for w, f in zip(weights, features[:5]))
        
        # Normalize to 0-1 range
        return min(max(score / 1000, 0), 1)  # Rough normalization
    
    def _get_risk_bucket(self, risk_score: float) -> str:
        """Map risk score to risk bucket."""
        if risk_score < 0.33:
            return "Low"
        elif risk_score < 0.66:
            return "Medium"
        else:
            return "High"
    
    def _fallback_survey_prediction(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback survey prediction with sophisticated rule-based logic."""
        # Extract all relevant features
        age = survey_data.get('age', 35)
        gender = survey_data.get('gender', 'male')
        education = survey_data.get('education_level', 3)
        invests = survey_data.get('invests', True)
        invests_stock = survey_data.get('invests_stock', True)
        investment_proportion = survey_data.get('investment_proportion', '10% - 20%')
        expected_return = survey_data.get('expected_return', '5% - 10%')
        investment_horizon = survey_data.get('investment_horizon', '3-5 years')
        monitoring_frequency = survey_data.get('monitoring_frequency', 'Monthly')
        equity_rank = survey_data.get('equity_rank', 3)
        fund_rank = survey_data.get('fund_rank', 2)
        
        # Initialize risk score
        risk_score = 0.0
        
        # 1. Age factor (younger = higher risk tolerance) - Weight: 15%
        if age < 25:
            risk_score += 0.20
        elif age < 35:
            risk_score += 0.15
        elif age < 45:
            risk_score += 0.10
        elif age < 55:
            risk_score += 0.05
        else:
            risk_score += 0.02
        
        # 2. Investment proportion - Weight: 15%
        if '40%' in investment_proportion or 'above' in investment_proportion:
            risk_score += 0.15
        elif '30%' in investment_proportion:
            risk_score += 0.10
        elif '20%' in investment_proportion:
            risk_score += 0.07
        else:
            risk_score += 0.03
        
        # 3. Expected return - Weight: 20%
        if '15%' in expected_return or 'above' in expected_return.lower():
            risk_score += 0.25
        elif '10%' in expected_return:
            risk_score += 0.15
        elif '5%' in expected_return:
            risk_score += 0.08
        else:
            risk_score += 0.03
        
        # 4. Monitoring frequency - Weight: 15%
        if 'daily' in monitoring_frequency.lower():
            risk_score += 0.18
        elif 'weekly' in monitoring_frequency.lower():
            risk_score += 0.12
        elif 'monthly' in monitoring_frequency.lower():
            risk_score += 0.06
        else:
            risk_score += 0.02
        
        # 5. Investment horizon - Weight: 10%
        if '5+' in investment_horizon or 'more than 5' in investment_horizon:
            risk_score += 0.12
        elif '3-5' in investment_horizon:
            risk_score += 0.08
        elif '1-3' in investment_horizon:
            risk_score += 0.04
        else:
            risk_score += 0.01
        
        # 6. Equity preference - Weight: 15%
        equity_score = (equity_rank - 1) / 6.0  # Normalize 1-7 to 0-1
        risk_score += equity_score * 0.20
        
        # 7. Fund preference - Weight: 5%
        fund_score = (fund_rank - 1) / 6.0
        risk_score += fund_score * 0.08
        
        # 8. Stock investment - Weight: 5%
        if invests_stock:
            risk_score += 0.08
        else:
            risk_score += 0.01
        
        # 9. Currently invests - Weight: 5%
        if invests:
            risk_score += 0.05
        else:
            risk_score += 0.01
        
        # 10. Education level - slight modifier
        if education >= 4:
            risk_score += 0.03
        elif education >= 3:
            risk_score += 0.02
        
        # 11. Gender - research shows slight differences
        if gender == 'male':
            risk_score += 0.02
        
        # Normalize to 0-1 range
        risk_score = min(max(risk_score, 0.0), 1.0)
        
        # Determine category and persona
        if risk_score < 0.3:
            category = 'Conservative'
            persona = 'Steady Saver'
        elif risk_score < 0.6:
            category = 'Balanced'
            persona = 'Strategic Balancer'
        else:
            category = 'Aggressive'
            persona = 'Risk Seeker'
        
        return {
            'risk_score': float(risk_score),
            'risk_category': category,
            'persona': persona,
            'confidence': 0.6  # Lower confidence for fallback
        }
    
    def _fallback_transaction_prediction(self, transaction_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback transaction prediction when models are not available."""
        if not transaction_data:
            return {
                'risk_score': 0.0,
                'risk_category': 'Conservative',
                'persona': 'Steady Saver',
                'confidence': 0.5,
                'probabilities': {
                    'Conservative': 0.8,
                    'Income': 0.1,
                    'Balanced': 0.05,
                    'Aggressive': 0.05
                }
            }
        
        # Simple rule-based analysis
        total_amount = sum(tx.get('amount', 0) for tx in transaction_data)
        avg_amount = total_amount / len(transaction_data) if transaction_data else 0
        
        # Count asset types
        asset_types = {}
        for tx in transaction_data:
            asset_type = tx.get('asset_type', 'Unknown')
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
        
        # Calculate risk score based on trading patterns
        risk_score = 0.0
        
        # Trading frequency (more trades = higher risk)
        if len(transaction_data) > 10:
            risk_score += 0.3
        elif len(transaction_data) > 5:
            risk_score += 0.2
        else:
            risk_score += 0.1
        
        # Average transaction size
        if avg_amount > 10000:
            risk_score += 0.3
        elif avg_amount > 5000:
            risk_score += 0.2
        else:
            risk_score += 0.1
        
        # Asset type preference
        stock_ratio = asset_types.get('Stock', 0) / len(transaction_data)
        if stock_ratio > 0.7:
            risk_score += 0.4
        elif stock_ratio > 0.4:
            risk_score += 0.2
        else:
            risk_score += 0.1
        
        # Normalize to 0-1 range
        risk_score = min(max(risk_score, 0.0), 1.0)
        
        # Determine category and persona
        if risk_score < 0.3:
            category = 'Conservative'
            persona = 'Steady Saver'
        elif risk_score < 0.6:
            category = 'Balanced'
            persona = 'Strategic Balancer'
        else:
            category = 'Aggressive'
            persona = 'Risk Seeker'
        
        # Generate probabilities
        probabilities = {
            'Conservative': max(0.1, 1.0 - risk_score),
            'Income': max(0.05, (0.5 - abs(risk_score - 0.5))),
            'Balanced': max(0.05, (0.5 - abs(risk_score - 0.5))),
            'Aggressive': max(0.1, risk_score)
        }
        
        return {
            'risk_score': float(risk_score),
            'risk_category': category,
            'persona': persona,
            'confidence': 0.6,  # Lower confidence for fallback
            'probabilities': probabilities
        }


# Global instance
ml_service = None

def get_ml_service() -> PortfoliAIMLService:
    """Get the global ML service instance."""
    global ml_service
    if ml_service is None:
        ml_service = PortfoliAIMLService()
    return ml_service


if __name__ == "__main__":
    # Test the service
    service = PortfoliAIMLService()
    
    # Test survey prediction
    survey_data = {
        'age': 30,
        'investment_proportion': '10% - 20%',
        'expected_return': '5% - 10%',
        'investment_horizon': '3-5 years',
        'monitoring_frequency': 'Monthly',
        'equity_rank': 3,
        'fund_rank': 2
    }
    
    result = service.predict_survey_risk(survey_data)
    print("Survey Risk Prediction:", result)
