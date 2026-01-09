3.2.2 Data Preprocessing and Feature Engineering

To prepare the survey dataset for machine learning, several preprocessing and feature engineering steps were applied to transform raw survey responses into numerical features suitable for Random Forest models. The dataset consisted of 132 labeled records from investor surveys, containing demographic information, investment behavior, and asset preferences.

**Data Cleaning:**
- Removed duplicate entries and validated data consistency
- Handled missing values using median imputation for numerical fields and mode imputation for categorical fields
- Validated data types and ranges to ensure quality

**Feature Encoding:**
Categorical variables were converted to numerical formats using appropriate encoding strategies:
- **One-hot encoding**: Applied to multi-category variables including occupation (Others, Salaried, Self-employed, Student) and main investment avenue (Bonds, Equity, Fixed Deposits, Gold/SGBs, Mutual Funds, PPF)
- **Binary encoding**: Gender was encoded as a binary variable (gender_male: 0 or 1)
- **Ordinal encoding**: Education level was mapped to numerical values reflecting increasing educational attainment

**Feature Engineering:**
Several derived features were created to capture investment behavior:
- **invest_prop_pct**: Percentage of income invested, converted from range responses to midpoint values (e.g., "10-20%" → 15%)
- **monitor_freq_per_month**: Portfolio monitoring frequency mapped to monthly frequency values
- **horizon_years**: Investment time horizon converted from categorical responses (e.g., "5-10 years") to numerical years
- **expected_return_pct**: Expected return percentage converted from range responses to midpoint values
- **rank_equity** and **rank_mutuals**: Asset class preference rankings (1-5 scale)
- **invests_stock**: Binary indicator of whether the user invests in stocks
- **raw_index**: Baseline risk computation derived from survey responses

**Final Feature Set:**
The preprocessing pipeline produced 22 engineered features used for model training:
- Demographic: gender_male, age, education_level
- Behavioral: invests, invest_prop_pct, monitor_freq_per_month, expected_return_pct, horizon_years
- Asset preferences: rank_equity, rank_mutuals, invests_stock, raw_index
- One-hot encoded: occupation categories (4 features), main_avenue categories (6 features)

These features were designed to capture both explicit investor preferences (stated in surveys) and behavioral patterns that correlate with risk tolerance and investment style.

3.2.3 Deriving Continuous Risk Score and Archetype Profile

The survey dataset contained pre-labeled risk scores and archetype classifications derived from expert assessment and survey responses. Each investor was assigned:
- **Continuous Risk Score**: A value ranging from 0 to 1, where 0 indicates very conservative behavior and 1 represents highly aggressive investment style. This served as the regression target for the Random Forest Regressor.
- **Archetype Classification**: One of three investor categories—Conservative, Comfortable, or Enthusiastic—which served as the classification target for the Random Forest Classifier.

**Target Variable Distribution:**
The dataset exhibited the following archetype distribution:
- Conservative: 53.8% of samples
- Comfortable: 28.8% of samples
- Enthusiastic: 17.4% of samples

This distribution reflects the natural skew toward more conservative investors in the survey population.

**Supervised Learning Approach:**
A supervised learning approach was adopted, where the 22 engineered features served as inputs to predict both the continuous risk score and the categorical archetype. This direct mapping from survey responses to risk profiles eliminated the need for unsupervised clustering or dimensionality reduction techniques.

The Random Forest models learned patterns directly from the labeled data, capturing relationships between demographic characteristics, investment behaviors, and asset preferences with the target risk metrics. This approach provided:
- **Interpretability**: Feature importance scores from Random Forest models reveal which survey responses most strongly predict risk tolerance
- **Scalability**: Real-time inference during user onboarding without requiring re-clustering or complex computations
- **Reliability**: Direct prediction from survey inputs to risk profiles, validated against expert-assessed labels

The supervised approach ensured that predictions aligned with advisor-validated risk assessments, providing a trustworthy foundation for personalized investment guidance.
