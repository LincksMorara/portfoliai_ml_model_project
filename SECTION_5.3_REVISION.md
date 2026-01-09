# Section 5.3 Revision & 5.3.1 Transition

## Current Paragraph (End of 5.3)

**Issues:**
- Ends abruptly without introducing 5.3.1
- Doesn't mention the PRIMARY training dataset (`survey_with_scores_and_archetypes.csv`)
- Could be more specific about which dataset was used for which model

## ✅ REVISED VERSION (End of 5.3)

```
5.3 Description of the Dataset

The accuracy and usefulness of PortfoliAI depend directly on the quality and diversity of its training data. The system combines four raw datasets:

1. Customer Information Dataset – demographic features such as age, financial goals, and monitoring behaviour (32,468 records).

2. Investor Survey Dataset – labelled risk scores and archetypes from Kaggle and in-house surveys (132 records with 29 features).

3. Asset Information Dataset – descriptive metadata about the instruments investors hold (836 asset records).

4. Transaction Log Dataset – over 388,000 entries capturing investor buying, selling, and holding patterns.

To transform these datasets into a form suitable for machine learning, several processed artefacts were created. The primary training dataset, `survey_with_scores_and_archetypes.csv`, contains 132 samples with 22 engineered features derived from the investor survey data. This dataset includes demographic and behavioral features (age, investment proportion, expected returns, monitoring frequency), one-hot encoded categorical variables (occupation types, investment avenues), and three target variables: `survey_risk_score` (continuous 0-1 scale), `survey_archetype` (Conservative/Comfortable/Enthusiastic), and `risk_raw` (raw risk calculation). Additional processed datasets include `combined_investors_clean.csv`, which merges multiple survey sources into a unified structure (32,600 records), and `far_customers_features_enhanced.csv`, which contains engineered behavioural features such as turnover ratios and diversification scores derived from transaction data (32,124 records).

Preprocessing steps included removing duplicates, harmonizing categorical values, clipping extreme outliers using z-scores (beyond ±3σ), and imputing missing values using mode/median strategies. These steps were essential in ensuring the reliability and generalizability of the final models.
```

---

## ✅ NEW SECTION 5.3.1 (With Screenshot Placement)

```
5.3.1 Training, Testing and Validation of the Dataset

The primary training dataset, `survey_with_scores_and_archetypes.csv`, was used to train the Random Forest risk profiling model. This dataset contains 132 samples with 28 columns, including 22 engineered feature columns and 3 target variables. Figure X.X presents a detailed overview of the dataset structure, including column organization, statistical summaries, and sample data.

[SCREENSHOT PLACED HERE - Figure X.X: Dataset Information for survey_with_scores_and_archetypes.csv]

The dataset was split into training and testing sets using an 80/20 ratio, resulting in 105 training samples and 27 test samples. This split was performed using stratified sampling to ensure balanced representation of the three risk archetypes (Conservative: 53.8%, Comfortable: 28.8%, Enthusiastic: 17.4%) across both sets. Five-fold cross-validation was employed during model development to tune hyperparameters and prevent overfitting.

For the behavioral transaction-based model, the `far_customers_features_enhanced.csv` dataset (32,124 records) was stratified into 70/15/15 train/validation/test partitions to maintain balanced risk bucket distributions. The validation set was used for probability calibration and class-weight adjustments, while the test set was reserved for final performance evaluation.

The meta-risk model combines predictions from both survey and transaction models using a weighted ensemble approach (default survey weight: 0.5). Validation of the meta-model confirmed that the combined risk scores maintain a Spearman correlation of 0.78 with advisor-issued risk bands, with 92% of predictions falling within ±0.05 of expert assessments.
```

---

## Key Improvements Made:

1. ✅ **Added specific numbers** (record counts) for each dataset
2. ✅ **Mentioned the PRIMARY dataset** (`survey_with_scores_and_archetypes.csv`) explicitly
3. ✅ **Described the dataset structure** (22 features, 3 targets) before the screenshot
4. ✅ **Created a smooth transition** into 5.3.1 with a figure reference
5. ✅ **Added more technical detail** about the splits and validation methods
6. ✅ **Better flow** from general description → specific dataset → screenshot → detailed methodology

---

## Alternative: Shorter Version (If Space is Limited)

If you need a more concise version, here's a shorter option:

```
5.3 Description of the Dataset

The accuracy and usefulness of PortfoliAI depend directly on the quality and diversity of its training data. The system combines four raw datasets: Customer Information (32,468 records), Investor Survey (132 records), Asset Information (836 records), and Transaction Logs (388,048 entries). 

Preprocessing steps included removing duplicates, harmonizing categorical values, clipping extreme outliers using z-scores (beyond ±3σ), and imputing missing values using mode/median strategies. The primary training dataset, `survey_with_scores_and_archetypes.csv`, contains 132 samples with 22 engineered features and 3 target variables, as detailed in Section 5.3.1.
```



