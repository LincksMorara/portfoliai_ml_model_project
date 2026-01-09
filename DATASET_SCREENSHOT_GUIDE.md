# 📊 Dataset Screenshot Guide for Proposal Document

## ✅ RECOMMENDED DATASET: `survey_with_scores_and_archetypes.csv`

**This is the BEST dataset to screenshot** because:

1. ✅ **Primary Training Dataset** - Used to train the main survey risk model (R²=0.89)
2. ✅ **Perfect Size** - 132 rows × 28 columns (manageable for screenshots)
3. ✅ **Complete Pipeline** - Shows features AND target variables
4. ✅ **Directly Documented** - Matches the 22 features in `model_metadata_20251029_075727.json`
5. ✅ **Professional Appearance** - Clean, processed data ready for documentation

### Dataset Details:
- **Location**: `data/processed/survey_with_scores_and_archetypes.csv`
- **Rows**: 132 (training samples)
- **Columns**: 28 total
  - **22 Feature Columns** (inputs to the model):
    - `gender_male`, `age`, `education_level`, `invests`
    - `invest_prop_pct`, `monitor_freq_per_month`, `expected_return_pct`
    - `horizon_years`, `rank_equity`, `rank_mutuals`, `invests_stock`
    - `raw_index`
    - `occupation_*` (4 one-hot encoded columns)
    - `main_avenue_*` (6 one-hot encoded columns)
  
  - **3 Target Variables** (what the model predicts):
    - `survey_risk_score` (continuous, 0-1)
    - `survey_archetype` (categorical: Conservative/Comfortable/Enthusiastic)
    - `risk_raw` (raw risk calculation)
  
  - **3 Metadata Columns**:
    - `Timestamp`, `inv_horizon`, `cluster`

---

## 📸 How to Take the Screenshot

### Option 1: Using Excel/Numbers/Google Sheets (Recommended)

1. **Open the CSV file**:
   ```bash
   # On Mac:
   open data/processed/survey_with_scores_and_archetypes.csv
   
   # Or manually: Right-click → Open With → Excel/Numbers
   ```

2. **Format for Screenshot**:
   - Freeze the header row (View → Freeze Panes)
   - Adjust column widths to show full column names
   - Show first 10-15 rows (enough to demonstrate structure)
   - Show first 10-12 columns (key features + target variables)

3. **Recommended Columns to Show**:
   - `gender_male`
   - `age`
   - `education_level`
   - `invest_prop_pct`
   - `expected_return_pct`
   - `horizon_years`
   - `monitor_freq_per_month`
   - `survey_risk_score` ⭐ (target variable)
   - `survey_archetype` ⭐ (target variable)
   - `risk_raw` ⭐ (target variable)

4. **Take Screenshot**:
   - Use Cmd+Shift+4 (Mac) or Snipping Tool (Windows)
   - Capture the table showing:
     - Header row with column names
     - 10-15 data rows
     - Clean formatting

---

### Option 2: Using Python/Pandas (For More Control)

1. **Create a preview script**:
   ```python
   import pandas as pd
   
   # Load dataset
   df = pd.read_csv('data/processed/survey_with_scores_and_archetypes.csv')
   
   # Select key columns for screenshot
   key_cols = [
       'gender_male', 'age', 'education_level', 
       'invest_prop_pct', 'expected_return_pct', 'horizon_years',
       'monitor_freq_per_month', 
       'survey_risk_score', 'survey_archetype', 'risk_raw'
   ]
   
   # Show first 12 rows
   preview = df[key_cols].head(12)
   
   # Display with formatting
   print(preview.to_string())
   
   # Or save to Excel for better formatting
   preview.to_excel('dataset_preview.xlsx', index=False)
   ```

2. **Run the script**:
   ```bash
   cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project
   source venv/bin/activate
   python dataset_preview.py
   ```

3. **Open the Excel file** and take screenshot

---

### Option 3: Using VS Code / Jupyter Notebook

1. **Open in VS Code**:
   - Install "Excel Viewer" extension
   - Right-click CSV → "Open Preview"
   - Take screenshot

2. **Or use Jupyter**:
   ```python
   import pandas as pd
   df = pd.read_csv('data/processed/survey_with_scores_and_archetypes.csv')
   df.head(12)[['gender_male', 'age', 'education_level', 
                 'invest_prop_pct', 'expected_return_pct', 
                 'survey_risk_score', 'survey_archetype']]
   ```
   - Display the output
   - Take screenshot

---

## 🎯 What the Screenshot Should Show

### Essential Elements:
1. ✅ **Dataset Name** visible (in filename or caption)
2. ✅ **Column Headers** clearly readable
3. ✅ **Sample Rows** (10-15 rows minimum)
4. ✅ **Key Features** visible (age, investment proportion, etc.)
5. ✅ **Target Variables** visible (`survey_risk_score`, `survey_archetype`)
6. ✅ **Clean Formatting** (no cut-off text, proper alignment)

### Optional but Recommended:
- Add a **caption** in your document: 
  > "Figure X: Cleaned training dataset (`survey_with_scores_and_archetypes.csv`) containing 132 samples with 22 engineered features and target variables (risk_score, archetype) used to train the Random Forest model (R²=0.89)."

---

## 📋 Alternative Datasets (If Needed)

### Option 2: `far_customers_features_enhanced.csv`
- **Use Case**: For showing behavioral/transaction-based features
- **Size**: 32,124 rows × 17 columns
- **Best For**: Demonstrating transaction feature engineering
- **Note**: Too large for full screenshot - show sample rows only

### Option 3: `combined_investors_clean.csv`
- **Use Case**: For showing combined/meta-model data
- **Size**: 32,600 rows × 14 columns
- **Best For**: Showing data integration pipeline
- **Note**: Also large - show sample only

---

## ✅ Final Recommendation

**Use `survey_with_scores_and_archetypes.csv`** because:
- It's the PRIMARY model's training data
- Perfect size for documentation
- Shows complete ML pipeline (features → targets)
- Directly referenced in your model metadata
- Professional and clean appearance

**Screenshot Composition:**
```
┌─────────────────────────────────────────────────────────────┐
│ survey_with_scores_and_archetypes.csv                       │
├──────┬─────┬──────┬──────────┬──────────┬──────────┬────────┤
│gender│ age │ educ │ invest_  │ expected│ survey_  │ survey │
│_male │     │_level│ prop_pct │ return_ │ risk_    │ arche  │
│      │     │      │          │ pct     │ score    │ type   │
├──────┼─────┼──────┼──────────┼──────────┼──────────┼────────┤
│ 1.0  │ 39  │  3   │  15.0    │  12.5   │  0.65    │ Comfort│
│ 1.0  │ 30  │  4   │  25.0    │  15.0   │  0.72    │ Enthus │
│ 0.0  │ 26  │  2   │  10.0    │  8.0    │  0.45    │ Conserv│
│ ...  │ ... │ ... │  ...     │  ...    │  ...     │  ...   │
└──────┴─────┴──────┴──────────┴──────────┴──────────┴────────┘
```

---

## 🚀 Quick Start Command

```bash
# Open the recommended dataset
cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project
open data/processed/survey_with_scores_and_archetypes.csv

# Then format and screenshot in Excel/Numbers
```

---

**Good luck with your proposal! 📄✨**



