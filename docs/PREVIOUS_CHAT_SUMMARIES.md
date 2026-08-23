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

## 6. Next Steps
* Complete the remaining complex EDA metric groupings (Temporal Engagement, Skip Technicals, Geographic, and Niche Metrics) in the condensed notebook, applying the same Map-Reduce and memory optimization techniques.
* Once EDA and visual pipelines are finalized, officially transition into the final project phase (Deciding between FastAPI MLOps Web App vs PyTorch/Deep Learning).
* Do NOT run automated scripts to inject code into the `.ipynb` without explicit permission. Give the user the code to paste.

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

**Final ML Verdict:** We proved the ultimate Data Science axiom: *Smart Feature Engineering (Windowing & Target Encoding) will always beat blindly throwing Advanced Algorithms at a dataset.* Strategy 1 (Windowed Random Forest) remains the champion.

---

## 8. Current State & Immediate Goal (August 2026)

The project has reached a massive milestone: Both the primary EDA visualizations (Phase 1) and the Predictive Machine Learning model are complete and documented.

**The Pivot to MLOps:**
Because the Summer 2027 internship application cycle is currently opening, we are pausing the remaining "nice to have" EDA graphs. The absolute highest priority is taking the Champion ML Model and wrapping it in a **FastAPI** web server to create an interactive API. This proves end-to-end engineering capability (from raw data to deployed software).

**Action Items:**
1. Extract the trained XGBoost model from the Jupyter Notebook.
2. Build a FastAPI backend (`app.py`).
3. Launch aggressive internship applications to Mercari, Rakuten, and PayPay using this completed project as the centerpiece of the portfolio.
