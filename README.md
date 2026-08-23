# 🎵 Spotify Analytics Pipeline

An automated, end-to-end data engineering, analytics, and machine learning pipeline for extracting actionable intelligence from user streaming behavior.

This project processes raw Spotify JSON streams, cleanses and imputes the data, structures it into an optimized SQL database, generates an automated business intelligence report (complete with over 60 temporal and behavioral charts), and trains machine learning models to predict user skip-behavior and session outcomes.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- SQLite (built-in) or PostgreSQL (if utilizing the Postgres pipeline)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/<YOUR_USERNAME>/Spotify-Analytics-Pipeline.git
cd Spotify-Analytics-Pipeline
```

### 2. Install Dependencies
This project relies on standard data science libraries (Pandas, Numpy, Scikit-Learn, Plotly, Seaborn) alongside database drivers.
```bash
pip install -r requirements.txt
```

---

## 💻 How to Use

The pipeline is completely interactive. You can run the CLI tools and follow the terminal prompts, or pass arguments directly.

### Step 1: Clean Your Data
Run the data cleaner to parse your raw Spotify JSON/CSV logs into a highly queryable SQL format.
```bash
python src/data_cleaning.py
```
*You will be prompted to select your raw data format (json/csv/postgres) and your output destination (sqlite/postgres). If using PostgreSQL, you will need to provide your database URI.*

### Step 2: Generate the EDA Report
Generate a massive Markdown document containing visualizations of your listening habits.
```bash
python src/eda_reporting.py
```
*The script runs silently and outputs a progress bar. Once finished, open `reports/EDA_Report.md` in any Markdown viewer (or GitHub) to explore your personalized analytics.*

### Step 3: Run Predictive Models
Train machine learning models on your newly created database to predict your listening behavior.
```bash
python src/ml_modeling.py
```
*The terminal will display the classification metrics and feature importances to show exactly what triggers a "skip" in your listening sessions.*

---

## 🚀 Architecture Overview

The pipeline consists of three core components executed in sequence:

1. **`src/data_cleaning.py` (ETL & Imputation)**
   - **Input:** Spotify extended streaming history (JSON), raw CSV logs, or existing SQL extracts.
   - **Process:** Timezone normalization (UTC), IP decoding, high-sparsity column filtering, categorical encoding, and contextual session tracking.
   - **Output:** Cleaned, structured data dumped natively into an optimized PostgreSQL or SQLite database, minimizing RAM footprint.

2. **`src/eda_reporting.py` (Automated BI Reporting)**
   - **Process:** Connects to the cleaned database and performs autonomous Exploratory Data Analysis (EDA). Computes skip ratios, identifies listening marathons, profiles user genre preferences over time, and maps cross-device navigation flows.
   - **Output:** Generates `EDA_Report.md` locally, populated with 60+ static charts and embedded interactive Plotly HTML Sankey diagrams—all processed entirely headlessly (no terminal popups).

3. **`src/ml_modeling.py` (Behavioral Prediction)**
   - **Process:** Engineers time-lagged and rolling-window features. Trains multiple models (XGBoost, Random Forest, Logistic Regression) to predict boolean skip outcomes or session lengths.
   - **Output:** Terminal-based model evaluations (Accuracy, Precision, Recall, F1, ROC-AUC) and feature importance mappings.

---

## 📓 Notebooks

The `notebooks/` directory contains the original Jupyter Notebooks used for rapid prototyping and hypothesis testing:
- `01_data_cleaning.ipynb`
- `02_eda_visualizations.ipynb`
- `03_ml_modeling.ipynb`

**Note:** All cell outputs have been intentionally scrubbed to protect Personally Identifiable Information (PII) such as IP addresses. You can re-execute these notebooks locally for an interactive, block-by-block view of the code logic.

---

## 📊 Sample Output (Sankey Funnel)

*The pipeline automatically tracks device navigation and renders interactive funnels. (HTML outputs are saved directly to `images/`)*
```text
Device: Android ➔ Start: appload ➔ End: trackdone
Device: Windows ➔ Start: clickrow ➔ End: fwdbtn
```

---
*Created as a comprehensive portfolio project demonstrating Data Engineering, BI Reporting, and Machine Learning workflows.*
