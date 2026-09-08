# Spotify Data Science Project: Comprehensive History & Summary

*This document serves as a complete memory snapshot of our progress on the Spotify Machine Learning Roadmap project, detailing every phase from initial data import to the final visualization optimizations.*

## 1. Project Objective
To process raw Spotify user data exports and run them through a complete Data Science pipeline: Data Cleaning -> Exploratory Data Analysis (EDA) -> Actionable Business Visualization -> Predictive Machine Learning (Skip Prediction).

## 2. Phase 0: Data Cleaning & Feature Engineering
* **Time Features:** Converted raw timestamps into Pandas Datetime objects. Extracted Year, Month, Day, and Hour for temporal analysis.
* **Duration Metrics:** Converted `ms_played` to `sec_played` to make the data human-readable.
* **Platform Categorization:** Mapped highly technical OS strings into clean categories: `Android`, `Windows`, `Linux`, `iOS`, `Mac`, and `Other`. 
* **The Linux Mystery:** Discovered that high Linux usage was actually attributable to the Brave Browser (anti-tracking user agents) and Smart Speakers/IoT devices.
* **Data Forensics (The Epoch Incident):** Investigated strange timestamps and identified `1784897000` as a UNIX epoch timestamp.
* **Data Forensics (The FUSHIGI Outlier):** Investigated an outlier where `sec_played` was astronomically high (over 24 minutes for a single track) on row 211505. Traced this anomaly back to an "offline repeat loop" event.
* **Skip Logic Mastery:** Determined that `reason_end == 'fwdbtn'` is the only true, reliable indicator of a user-initiated skip. The boolean `skipped` column is notoriously unreliable for early skips.

## 3. Phase 1: Exploratory Data Analysis (EDA)
We utilized highly chained, one-liner Pandas aggregations (adhering to strict coding preferences) to compute robust variables that would later power the visualizations:
* **Temporal Habits:** Identified a massive listening/skip spike at 4 PM and a dead zone at 4 AM.
* **Niche Metrics Calculated:**
  * `longest_artist_streaks`: Built complex `.diff()` and `.cumsum()` logic to find the longest consecutive yearly and monthly streaks for specific artists.
  * `one_hit_wonders`: Identified artists with massive play counts but exactly 1 unique `song_name`.
  * `attention_span`: Calculated the median `sec_played` for skips to determine how patience runs out.
  * `top_artist_yearly`: Grouped listening volume by year.
* **Advanced Data Engineering (One-Hot Encoded Genres):**
  * **The `.T.dot()` Matrix Trick:** Bypassed heavy Pandas groupings by calculating All-Time genre play counts and listen time simultaneously using pure C-optimized Linear Algebra (dot products) on the OHE matrix.
  * **Map-Reduce Architecture:** Implemented a custom Map-Reduce `for` loop to calculate genre stats across time-series (Yearly, Seasonal, Monthly, Daily) without exploding RAM. It slices the dataset into temporal chunks, applies the matrix math, and uses `pd.concat` to merge them.
  * **Time vs. Space Complexity Showdown:** Profiled memory usage using `sys.getsizeof()`. We proved that using `.str.split(", ").explode()` for Daily stats was lightning fast (0.2s) but spawned a massive 1.6 GB dataframe. The Map-Reduce loop was slower (19s) but only used 0.18 MB of RAM (9,157x less memory).

## 4. The Master Visualization Architecture
We architected a 30-graph roadmap saved in `VISUALISATION_PLAN.md` split into 3 distinct phases:
1. **The Consumer (Spotify Wrapped):** Fun, lifestyle, and serendipity graphs.
2. **The Business (Infrastructure):** Graphs designed to save bandwidth and analyze hardware.
3. **The Data Scientist (Machine Learning):** Correlation matrices and feature selection.

## 5. Visualization Execution & Strict Memory Optimization
We completed the execution of the Phase 1 Consumer graphs. During this phase, we transitioned from Pedagogical Mode to direct code implementation, enforcing **extreme memory efficiency rules**:

* **The Theme:** We established a gorgeous custom "Japanese Winter Night" aesthetic (`#0D1321` background, `#111827` axes, `Meiryo` font).
* **The Spaghetti Graph Lesson:** We learned why Line Charts fail mathematically when tracking "Top 3 Artists per year" (lines break when an artist drops out). We pivoted to a faceted bar chart (`sns.catplot`).
* **The Strict Memory Rules:**
  1. **Zero `.copy()` Usage:** Dataframes must NEVER be copied into new variables (`.copy()`) just for a single graph.
  2. **EDA Variable Re-use:** Visualization cells must NOT run expensive `master_df.groupby()` operations if the data was already calculated in the EDA phase. We actively refactored the notebook to use pre-existing variables like `top_artist_yearly`, `one_hit_wonders`, and `longest_artist_streaks` directly inside Seaborn.
  3. **On-the-fly Filtering:** Filters and column subsets must be applied *before* grouping (e.g. `master_df[["time_stamp", "artist_name", "reason_start"]]`) to save RAM.
* **The Attention Span Decay:** We successfully plotted the True Attention Span as a continuous line chart over the years. To do this accurately, we applied a `<= 630` seconds filter to remove long podcast/song outliers, and explicitly calculated the mean using `sec_played / count`.
* **Agent Miscommunication (The Notebook Injection Incident):** The AI mistakenly executed a Python script (`nbformat`) to automatically inject 10 unauthorized Phase 2 graphs into the bottom of `spotify_eda.ipynb`. The AI was ordered to write a correction script (`fix_notebook.py`) that successfully deleted the junk cells and fully applied the memory-optimization rules to the existing visual cells.

## 6. Phase Transition: From Exploratory EDA to Production ML & Engineering
Following the completion of the Phase 1 visualization suite, all remaining EDA metric groupings (Temporal Engagement, Skip Technicals, Geographic, and Niche Metrics) were successfully completed using strict memory-optimized aggregations without intermediate copies. Rather than relying on fragile manual notebook pasting, the workflow was structured into clear reproducible phases, culminating in the machine learning skip prediction modeling and the production CLI pipeline.

## 7. Phase 2: Machine Learning & The Concept Drift Discovery
We architected a binary classification pipeline using **XGBoost** and **Random Forest** to predict if a user would skip a song.

* **Dynamic Target Encoding:** To avoid data leakage, we refused to use `.transform('mean')`. Instead, we used `.expanding().mean().shift(1)` to calculate a rolling, historical skip percentage for every artist and song *up to the moment the song was played*.
* **Memory Optimization:** We casted all One-Hot Encoded genre columns and boolean flags to `int8`, slashing RAM usage from 277MB to 42.5MB.
* **The Chronological Split:** We avoided random 80/20 splits to prevent "Repeated Song Leakage" (the sandbox effect). We split chronologically: Train on 2019-2024, Test on 2025-2026.
* **The Concept Drift Trap:** Initial testing yielded abysmal recall (XGBoost 14%, RF 6%). We analyzed the output and discovered massive **Concept Drift**: The user's skip rate was 31% in 2021, but plummeted to 4% in 2025. The AI was trained on a hyper-active younger user but tested on an older, patient user.
* **Imbalance Correction:** We dynamically calculated an `imbalance_ratio` of 5.03 and applied it via `scale_pos_weight`. XGBoost's recall immediately tripled to 42%.

### Defeating Concept Drift & The Pro Pipeline Failure
We launched multiple strategies to defeat the Concept Drift and optimize Precision/Recall:
1. **Strategy 1 (Windowing):** We brutally deleted all data prior to 2023. By starving the model of ancient history, it learned the "modern user" perfectly. This resulted in the highest precision (Random Forest hit 67% precision).
2. **Strategy 2 (Time Decay):** We kept all data but assigned heavier `sample_weights` to recent years. It failed to beat the pure Windowing strategy.
3. **The "Pro" Pipeline (SMOTE + GridSearchCV):** We attempted to use SMOTE to synthetically hallucinate fake skips to perfectly balance the data, and Optuna/GridSearchCV to tune hyperparameters. 
4. **The Golden Lesson:** The Pro Pipeline collapsed (Precision dropped to 32%). We discovered that applying SMOTE geometric hallucination to 154 dimensions of binary `int8` One-Hot Encoded genre columns created mathematically impossible garbage data (e.g. `genre_rock = 0.43`). The hyper-tuned XGBoost memorized corrupted garbage.

**Final ML Verdict:** We proved the ultimate Data Science axiom: *Smart Feature Engineering (Windowing & Target Encoding) will always beat blindly throwing Advanced Algorithms at a dataset.* Strategy 1 (Windowed Feature Engineering) proved to be the most resilient baseline.

---

## 8. Current State & September 2026 Milestone

The project has achieved complete end-to-end realization across both research and production tiers:
1. **Research Tier:** Three polished Jupyter Notebooks (`01_data_cleaning.ipynb`, `02_eda_visualizations.ipynb`, `03_ml_modeling.ipynb`).
2. **Production Tier:** A modernized CLI pipeline in `pipeline/` (`01_data_cleaning.py`, `02_eda_visualizations.py`, `03_ml_modeling.py`).
3. **Automated Analytics:** Automated Markdown reporting generating [`reports/EDA_Report.md`](../reports/EDA_Report.md) with 21 embedded figures and an interactive Plotly HTML Sankey.
4. **Production Model:** Serialized XGBoost predictor in [`models/spotify_skip_predictor_xgb.pkl`](../models/spotify_skip_predictor_xgb.pkl) (431.71 KB).

---

## 9. Phase 3: Pipeline Modernization, UX & Security Sprint (September 2026)

* **Universal Default Fallback Architecture:**
  * Implemented an interactive prompt system across all notebooks and scripts where pressing `Enter` automatically selects canonical defaults (`Cleaned_Spotify_Portable`, `Engineered_Spotify_Portable`, `1` for SQLite, default local PostgreSQL connection string).
  * Implemented strict validation loops that re-prompt until valid choices or `Esc` (exit) are given.
* **Security & Credential Sanitization:**
  * Scrubbed all raw API keys and passwords from tracked files and cell outputs.
  * Added dynamic regex password masking (`:****@`) to all terminal connection logs and error messages.
  * Added comprehensive `.gitignore` rules for `data/`, `models/`, `sql/`, `agents/`, `reports/`, and `.env`.
* **Retirement of `src/` & Creation of `pipeline/`:**
  * Removed legacy scripts in `src/` and created clean, production-grade scripts in `pipeline/` matching the research notebooks 1:1.
* **Dynamic `top_n` & Headless Markdown Reporting:**
  * In `pipeline/02_eda_visualizations.py`, the user is prompted **only once** for their ranking preference (`top_n`, default 10).
  * All 5 sections of Tabular EDA and 21 Japanese Winter Night figures are output directly to `reports/EDA_Report.md` and `reports/images/`, keeping the terminal clean and free of table clutter.
  * Phase 3 Feature Engineering and SQL export remains interactive in the terminal.
* **Model Serialization & Production Accuracy:**
  * `pipeline/03_ml_modeling.py` executes chronological splitting (2023+), balanced Random Forest and cost-sensitive XGBoost training, optimal threshold tuning (0.625), confusion matrix heatmap generation, and saves the trained payload to `models/spotify_skip_predictor_xgb.pkl` with 97% overall accuracy.

---

### 10. Phase 4: Documentation Overhaul, Recruiter Blueprint & Subfolder Architecture (September 2026)

* **Documentation Subfolder Modularization:**
  * Reorganized `docs/` into domain-specific subdirectories while maintaining core briefings at the root:
    * `docs/eda/`: Analytical theory, linear algebra proofs, and table catalogs.
    * `docs/visualizations/`: Cognitive design guide, chart selection theory, and 21-figure catalog.
    * `docs/ml/`: Modeling architecture, Optuna hyperparameter roadmap, and empirical experiment logs.
    * `docs/` Root: Operational briefing (`AI_HANDOFF.md`), CLI run guide (`ROADMAP.md`), historical log (`PREVIOUS_CHAT_SUMMARIES.md`), and developer system rules (`antigravityrule.txt`).
* **Creation of the EDA Catalog (`docs/eda/EDA_CATALOG.md`):**
  * Created a complete metric-by-metric catalog of all 5 EDA sections (Top Charts, Temporal Habits, Skip Behavior, Technical/Geographic, Niche Metrics) detailing input columns, aggregation formulas, dynamic `top_n` scaling, and business significance.
* **Creation of Visualization Theory & Design Guide (`docs/visualizations/VISUALIZATION_THEORY.md`):**
  * Authored a dedicated technical guide detailing why specific chart types were chosen over naive alternatives (e.g. Faceted Bars vs. Spaghetti Lines, Continuous CDF vs. Histograms for CDN buffering, 2D Heatmaps for AWS autoscaling, Radar projections for circadian personas).
  * Documented the complete **Japanese Winter Night** design system (`#0D1321` canvas, `#111827` axes, Meiryo multi-byte typography, vibrant neon tokens) and zero-leak Matplotlib/Kaleido rendering optimizations.
* **Theory & Mathematical Optimization Master Note (`docs/eda/EDA_THEORY_AND_METHODS.md`):**
  * Renamed `EDA_PLAN.md` and moved to `docs/eda/EDA_THEORY_AND_METHODS.md`.
  * Positioned the **⚡ Executive TL;DR: Smart Methods vs. Standard Approaches** comparison table at the very top of the file for instant 15-second recruiter visibility.
* **Visualization Catalog Renaming (`docs/visualizations/VISUALIZATION_CATALOG.md`):**
  * Renamed `VISUALISATION_PLAN.md` and moved to `docs/visualizations/VISUALIZATION_CATALOG.md`.
* **ML Experiment Log & Honest Assessment (`docs/ml/ML_PROGRESS_LOG.md`):**
  * Streamlined `docs/ml/ML_PROGRESS_LOG.md` strictly to empirical model accuracy tracking across Attempts 1 through 6.
  * Removed "champion" hyperbole; candidly documented that **Recall (0.48)** remains an acknowledged bottleneck (missing 52% of skips) because systematic hyperparameter tuning has not yet been executed.
* **ML Roadmap & Hyperparameter Tuning Expansion (`docs/ml/ML_PLAN.md`):**
  * Moved to `docs/ml/ML_PLAN.md`.
  * Added **Section 8: Systematic Hyperparameter Tuning & Recall Optimization**, defining a formal Optuna/Bayesian search roadmap (`max_depth`, `learning_rate`, `subsample`, `reg_alpha`, `reg_lambda`), Focal Loss implementation, and cost-sensitive re-weighting to push recall $\ge 0.70$.
* **Root README & AI Handoff Alignment:**
  * Updated `README.md` Key Highlights and `docs/AI_HANDOFF.md` directory trees to point to the new modular subfolder paths.
* **Purge of Meta Notes & Obsolete Warnings:**
  * Removed all meta status callouts (`> [!NOTE]`, `> [!WARNING]`, `> [!TIP]`) and `[COMPLETE]` tags across `docs/eda/`, `docs/visualizations/`, `docs/ml/`, `docs/ROADMAP.md`, and `README.md`.
  * Replaced "Champion Model" hyperbole in `README.md` with an objective `[Attempt 6: Baseline]` label and linked directly to the Optuna hyperparameter tuning roadmap in `docs/ml/ML_PLAN.md`.
