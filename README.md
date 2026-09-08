# Spotify Analytics & Machine Learning Pipeline

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/XGBoost-97.0%25_Accuracy-2ea44f?style=for-the-badge" alt="XGBoost" />
  <img src="https://img.shields.io/badge/ROC--AUC-0.824-3b82f6?style=for-the-badge" alt="ROC-AUC" />
  <img src="https://img.shields.io/badge/RAM_Saved-85%25-00bcd4?style=for-the-badge" alt="RAM" />
  <img src="https://img.shields.io/badge/PostgreSQL-Streaming_COPY-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="Postgres" />
  <img src="https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge" alt="License" />
</p>

An end-to-end Python data engineering, automated exploratory data analysis (EDA), and predictive machine learning pipeline that transforms raw Spotify listening logs into deep behavioral insights and user skip predictions.

---

## Key Highlights & Engineering Wins

| Innovation Area | Metric / Achievement | Engineering Implementation |
| :--- | :--- | :--- |
| **Memory Optimization** | ![RAM Saved](https://img.shields.io/badge/RAM_Saved-85%25-2ea44f?style=flat-square) | Compressed in-memory dataset from **277 MB down to 42.5 MB** via targeted `int8`/`category` downcasting |
| **Linear Algebra Speedup** | ![300x Faster](https://img.shields.io/badge/BLAS_Dot_Product->300x_Faster-00bcd4?style=flat-square) | Replaced multi-genre `.groupby()` loops with compiled BLAS `.T.dot()` matrix operations (<0.05s runtime) |
| **Temporal Map-Reduce** | ![9157x Drop](https://img.shields.io/badge/Map--Reduce-9%2C157x_Less_RAM-7c3aed?style=flat-square) | Chunked temporal Map-Reduce replacing `.explode()`, dropping intermediate RAM from **1.6 GB to 0.18 MB** |
| **High-Throughput Streaming** | ![3.2s Export](https://img.shields.io/badge/PostgreSQL_COPY-15m_→_3.2s-f59e0b?style=flat-square) | SQLite in-memory pragmas and PostgreSQL native buffer streaming via `COPY FROM STDIN` |
| **Automated Reporting** | ![21 Figures](https://img.shields.io/badge/Executive_Dossier-21_Figures-ec4899?style=flat-square) | Headless single-prompt generation of a 5-section Markdown dossier with 21 Japanese Winter Night figures in [`reports/EDA_Report.md`](reports/EDA_Report.md) |
| **Zero Temporal Leakage** | ![Zero Leakage](https://img.shields.io/badge/Validation-Walk--Forward_Split-10b981?style=flat-square) | Strict **chronological walk-forward split** (2023–2024 train, 2025+ test) with dynamic target encoding |
| **Concept Drift Mitigation** | ![97% Accuracy](https://img.shields.io/badge/Skip_Predictor-97.0%25_Accuracy-3b82f6?style=flat-square) | Overcame 31% → 4% skip rate collapse via micro-mood features (`seconds_since_last_skip`, `skips_last_15m`), scoring **0.824 ROC-AUC** |
| **Architectural Blueprint** | ![Theory Guide](https://img.shields.io/badge/Deep_Dive-Technical_Blueprint-6366f1?style=flat-square) | Complete mathematical derivations, complexity analysis, and recruiter notes in [`docs/eda/EDA_THEORY_AND_METHODS.md`](docs/eda/EDA_THEORY_AND_METHODS.md) |

---

## Table of Contents
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Core Pipeline Modules](#core-pipeline-modules)
- [The ML Engineering Journey](#ml-engineering-journey)
- [Obtaining Your Spotify Data](#obtaining-your-spotify-data)
- [AI Agent / IDE Directive](#ai-agent-directive)
- [Getting Started & Usage](#getting-started-usage)
- [Research Notebooks](#research-notebooks)
- [Author & Connect](#author-connect)
- [License](#license)

---

## <a id="system-architecture"></a>System Architecture

### 1. Research & Prototyping Workflow (`notebooks/`)
The research workflow relies on structured database connections for rapid exploratory querying, visual validation, and model experimentation:

```mermaid
flowchart LR
    A["Raw Spotify Logs<br/>(JSON)"] --> B["01_data_cleaning.ipynb<br/>(ETL & Compression)"]
    B --> C[("SQL Database<br/>(SQLite / Postgres)")]
    C -->|"SQL Queries"| D["02_eda_visualizations.ipynb<br/>(Visual Analysis)"]
    C -->|"SQL Queries"| E["03_ml_modeling.ipynb<br/>(Model Experiments)"]
    D --> F["Interactive Plots<br/>& Visual Insights"]
    E --> G["Model Metrics<br/>& Evaluation"]
```

### 2. Standalone Production CLI Pipeline (`pipeline/`)
The Python CLI scripts are decoupled and format-agnostic—matching the notebooks 1:1 and capable of ingesting and exporting across any data format:

```mermaid
flowchart LR
    A["Raw Data<br/>(JSON / SQL)"] --> B["pipeline/01_data_cleaning.py<br/>(ETL Engine)"]
    B --> C[("Cleaned Database<br/>(SQLite / Postgres)")]
    
    C --> D["pipeline/02_eda_visualizations.py<br/>(EDA Engine)"]
    D --> E["reports/EDA_Report.md<br/>(21 Aesthetic Plots)"]
    D --> F[("Engineered Feature Store<br/>(SQLite / Postgres)")]
    F --> G["pipeline/03_ml_modeling.py<br/>(ML Engine)"]
    G --> H["Model Metrics<br/>& Saved Artifacts"]
```

---

## <a id="tech-stack"></a>Tech Stack

| Layer | Tools & Frameworks |
| :--- | :--- |
| **Language & Core** | ![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=flat-square&logo=python&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white) |
| **Data Engineering** | ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white) ![Psycopg2](https://img.shields.io/badge/Psycopg2-336791?style=flat-square&logo=postgresql&logoColor=white) |
| **Databases** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) |
| **Machine Learning** | ![Scikit-Learn](https://img.shields.io/badge/scikit_learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white) ![XGBoost](https://img.shields.io/badge/XGBoost-111?style=flat-square&logo=xgboost&logoColor=white) ![Joblib](https://img.shields.io/badge/Joblib-007ACC?style=flat-square) |
| **Data Visualization** | ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white) ![Seaborn](https://img.shields.io/badge/Seaborn-388E3C?style=flat-square) ![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=flat-square) ![Kaleido](https://img.shields.io/badge/Kaleido-7B1FA2?style=flat-square) |

---

## <a id="core-pipeline-modules"></a>Core Pipeline Modules

### 1. [`pipeline/01_data_cleaning.py`](pipeline/01_data_cleaning.py) ![ETL Engine](https://img.shields.io/badge/Module-ETL_%26_Ingestion-00bcd4?style=flat-square)
- Accepts raw Spotify JSON streams, SQLite databases, or PostgreSQL connections.
- Normalizes timestamps (UTC to Asia/Kolkata), decodes IP origins, drops high-sparsity metadata, and handles categorical encodings.
- Exports cleaned data directly into SQLite or PostgreSQL tables with native COPY streams and minimal RAM overhead.

### 2. [`pipeline/02_eda_visualizations.py`](pipeline/02_eda_visualizations.py) ![EDA Engine](https://img.shields.io/badge/Module-Automated_EDA_%26_Visuals-ec4899?style=flat-square)
- Form-agnostic loader that reads directly from **SQLite or PostgreSQL** with seamless default fallback on `Enter`.
- Asks the user once for `top_n` items (artists, songs, genres, albums) and dynamically shapes all ranking charts.
- Autonomously executes comprehensive Exploratory Data Analysis, generating 21 Japanese Winter Night figures (`reports/images/`) and interactive Plotly HTML Sankey navigation funnels.
- Compiles tabular metrics and visual charts cleanly into `reports/EDA_Report.md` (no terminal clutter).
- Features Phase 3 Feature Store engineering and interactive SQL export in the terminal.

### 3. [`pipeline/03_ml_modeling.py`](pipeline/03_ml_modeling.py) ![ML Engine](https://img.shields.io/badge/Module-Predictive_Modeling-2ea44f?style=flat-square)
- Ingests engineered features from **SQLite or PostgreSQL** (with automatic on-the-fly calculation fallback).
- Combats concept drift with modern chronological train/test splitting (2023+).
- Trains and evaluates Cost-Sensitive XGBoost and Balanced Random Forest classifiers with optimal threshold tuning.
- Serializes trained production artifacts directly to `models/spotify_skip_predictor_xgb.pkl`.

---

## <a id="ml-engineering-journey"></a>The ML Engineering Journey

During model development in the research phase, four critical machine learning challenges were identified and systematically resolved:

```
[Attempts 1–3] ────► [Attempt 4] ──────────► [Attempt 5] ──────────► [Attempt 6: Baseline]
Leakage from         Random 80/20 Split      Chronological Split     Micro-Mood Engineering
`sec_played`         0.95 ROC-AUC            Score collapsed due     Tuned thresholds (XGBoost 0.625)
(Identified &        (Lookahead Bias &       to Concept Drift        Defeated drift & eliminated
 Dropped)             Leakage uncovered)      (Skip rate 31% -> 4%)   all data leakage
```

| Experiment Phase | Validation Strategy | Outcome / Metric | Key Engineering Takeaway |
| :--- | :--- | :--- | :--- |
| **Attempts 1–3** | Random 80/20 Split | ![Target Leakage](https://img.shields.io/badge/Status-Target_Leakage-e11d48?style=flat-square) | `sec_played` and `skipped` leaked future state; purged to enforce pre-stream prediction |
| **Attempt 4** | Random 80/20 Split | ![Lookahead Bias](https://img.shields.io/badge/Status-Lookahead_Bias-f59e0b?style=flat-square) | Random split mixed past/future streams of identical songs, artificially inflating AUC to 0.95 |
| **Attempt 5** | Chronological (2019–2024 / 2025+) | ![Concept Drift](https://img.shields.io/badge/Status-Concept_Drift-8b5cf6?style=flat-square) | Revealed massive concept drift: user skip rate plummeted from 31% (2021) to 4% (2025) |
| **Attempt 6** | Chronological Windowed (2023+) | ![Working Baseline](https://img.shields.io/badge/Status-97.0%25_Acc_|_0.824_AUC-22c55e?style=flat-square) | Windowing and short-term micro-moods eliminated drift, establishing a robust baseline |

1. **Eliminating Lookahead Bias:** A standard random train/test split allowed future listening patterns to leak into the past. Moving to a strict **Chronological Forward Split** restored real-world evaluation integrity.
2. **Defeating Concept Drift:** Listener habits changed drastically over the multi-year history. Restricting the training window to recent years and engineering short-term **Micro-Mood** variables anchored ~60% of predictive power to immediate psychological context rather than stale historical preferences.
3. **Threshold Tuning for Imbalance:** Because skips represent a small minority of listening events, default 0.50 decision thresholds were replaced with tuned precision-recall thresholds (XGBoost @ 0.625) to maximize F1 and precision.
4. **Optimization Roadmap:** While Attempt 6 achieves 97.0% overall accuracy and 0.824 ROC-AUC, its recall stands at 0.48. A formal Optuna Bayesian hyperparameter search and Focal Loss tuning roadmap is detailed in [`docs/ml/ML_PLAN.md`](docs/ml/ML_PLAN.md).

---

## <a id="obtaining-your-spotify-data"></a>Obtaining Your Spotify Data

To run this pipeline on your own personal listening history:

1. Request your **Extended Streaming History (JSON)** directly from [Spotify Privacy Settings](https://www.spotify.com/account/privacy/).
2. Select **"Extended streaming history"** and submit the request *(Spotify will email you a download link within a few days)*.
3. Extract the downloaded zip file and place all `Streaming_History_Audio_*.json` files inside the `data/raw/` directory:
```
Spotify-Analytics-Pipeline/
└── data/
    └── raw/
        ├── Streaming_History_Audio_2019-2023_0.json
        ├── Streaming_History_Audio_2023-2024_1.json
        └── ...
```

---

## <a id="ai-agent-directive"></a>AI Agent / IDE Directive

If you are an AI assistant (Cursor, Windsurf, Copilot, or terminal agent) executing this project for the user, follow these directives:

```text
[AGENT DIRECTIVE]:
1. Verify that requirements are installed (`pip install -r requirements.txt`).
2. Check that raw JSON files exist in `data/raw/`.
3. Execute data cleaning: `python pipeline/01_data_cleaning.py`
4. Generate the EDA report: `python pipeline/02_eda_visualizations.py`
5. Run the predictive models: `python pipeline/03_ml_modeling.py`
6. Summarize the generated `reports/EDA_Report.md` and print top model metrics to the user.
```

---

## <a id="getting-started-usage"></a>Getting Started & Usage

### Prerequisites
- Python 3.9+
- Git

### 1. Clone & Install
```bash
git clone https://github.com/NotCatfish/Spotify-Analytics-Pipeline.git
cd Spotify-Analytics-Pipeline
pip install -r requirements.txt
```

### 2. Running the Interactive CLI Tools

All scripts feature an interactive prompt mode with default fallbacks on `Enter`:

**Step 1: Clean Raw Data**
```bash
python pipeline/01_data_cleaning.py
```
*(Prompts for your input source [json/sqlite/postgres] and target output [sqlite/postgres].)*

**Step 2: Generate Automated EDA Visualizations & Markdown Report**
```bash
python pipeline/02_eda_visualizations.py
```
*(Prompts once for `top_n` items to display, generates `reports/EDA_Report.md` + 21 charts in `reports/images/`, and interactively exports the ML feature store in the terminal.)*

**Step 3: Train Skip Prediction Models**
```bash
python pipeline/03_ml_modeling.py
```
*(Loads the feature store, trains balanced Random Forest and cost-sensitive XGBoost models, optimizes probability thresholds, and saves `models/spotify_skip_predictor_xgb.pkl`.)*

---

## <a id="research-notebooks"></a>Research Notebooks

Explore and run the step-by-step Jupyter notebooks directly in your browser:

| Notebook | Domain | Output Status | Interactive Cloud Runner |
| :--- | :--- | :--- | :--- |
| [`01_data_cleaning.ipynb`](notebooks/01_data_cleaning.ipynb) | Initial ETL, schema design, and column pruning | ![Clean PII](https://img.shields.io/badge/PII-Scrubbed-2ea44f?style=flat-square) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NotCatfish/Spotify-Analytics-Pipeline/blob/main/notebooks/01_data_cleaning.ipynb) |
| [`02_eda_visualizations.ipynb`](notebooks/02_eda_visualizations.ipynb) | Interactive visualization drafting and distribution plots | ![Clean PII](https://img.shields.io/badge/PII-Scrubbed-2ea44f?style=flat-square) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NotCatfish/Spotify-Analytics-Pipeline/blob/main/notebooks/02_eda_visualizations.ipynb) |
| [`03_ml_modeling.ipynb`](notebooks/03_ml_modeling.ipynb) | Model benchmarking, chronological validation, concept drift | ![Clean PII](https://img.shields.io/badge/PII-Scrubbed-2ea44f?style=flat-square) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NotCatfish/Spotify-Analytics-Pipeline/blob/main/notebooks/03_ml_modeling.ipynb) |

*Note: All cell outputs have been scrubbed to protect Personally Identifiable Information (PII).*

---

## <a id="author-connect"></a>Author & Connect

**Indraneel Samanta**  
*Aspiring Data & AI Engineer | B.Tech in AIML @ DJSCE*

- **Portfolio**: [indraneelsamanta.vercel.app](https://indraneelsamanta.vercel.app/)
- **LinkedIn**: [linkedin.com/in/indraneel-samanta](https://www.linkedin.com/in/indraneel-samanta/)
- **GitHub**: [@NotCatfish](https://github.com/NotCatfish)

---

## <a id="license"></a>License

This project is open-source and available under the [MIT License](LICENSE).
