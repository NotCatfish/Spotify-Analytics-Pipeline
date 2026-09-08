# Spotify ML Architecture and Skip Prediction Roadmap

## $\color{#F59E0B}{\text{1. The Goal}}$
Build a **Binary Classifier** using XGBoost (and Random Forest for comparison) to predict whether a user will skip a song.
* **Target Variable:** `is_skip` (1 = Skipped via `fwdbtn`, 0 = Listened)
* **Business Objective:** Maximize the detection of True Skips while understanding the trade-off of False Alarms (False Positives).

## $\color{#F59E0B}{\text{2. Feature Engineering Strategy}}$

To make XGBoost incredibly accurate, we need to translate text (which ML models hate) into mathematical risk probabilities (which ML models love).

### $\color{#38BDF8}\text{A. Target Encoded Features (The Risk Profile)}$
We will convert categorical text strings into their historical skip percentage.
* **`artist_skip_pct`**: The historical % this specific artist is skipped.
* **`song_skip_pct`**: The historical % this specific song is skipped.
* **`album_skip_pct`**: The historical % this specific album is skipped.

**Why this works:** If 5 different artists all have a 10.5% skip rate, XGBoost groups them together as a "10.5% Risk". It doesn't need to learn their names, just their mathematical behavior.

### $\color{#38BDF8}\text{B. Raw Numeric Features (Time and Date)}$
XGBoost can naturally interpret numbers, so we will pass these datetime attributes directly into the model without any conversion:
* **`hour_of_day`**: 0 to 23
* **`day_of_week`**: 0 to 6 (Monday to Sunday)
* **`day_of_month`**: 1 to 31
* **`year`**: e.g., 2021, 2024

### $\color{#38BDF8}\text{C. God-Tier Behavioral Features (Context)}$
We will engineer columns that give the model context about the user's *current mood* at the exact moment the song plays:
* **`previous_song_skipped` (1/0)**: Was the immediately preceding song skipped? (Detects if the user is in a "skipping mood").
* **`session_length_minutes`**: How long has the user been actively listening to music in this current unbroken session?

## $\color{#F59E0B}{\text{3. Data Leakage and Concept Drift Prevention Protocol}}$

Random 80/20 train-test splits create a "Time Machine" leak where future listening behaviors leak into past predictions. Furthermore, long historical windows suffer from severe **Concept Drift** (e.g., skip rates dropping from 31% in 2021 to 4% in 2025).

**The Production Protocol:**
1. **$\color{#38BDF8}\text{Windowing:}$** Filter dataset to modern listening history (`year >= 2023`) to starve the model of stale habits.
2. **$\color{#38BDF8}\text{Chronological Forward Split:}$** Train strictly on older modern data (2023–2024) and test on future holdout streams (2025+).
3. **$\color{#38BDF8}\text{Isolated Target Encoding:}$** Group `X_train` by Artist/Song and calculate smoothed historical skip probabilities.
4. **$\color{#38BDF8}\text{Dictionary Mapping:}$** Map the training risk dictionary onto both `X_train` and `X_test`.
5. **$\color{#38BDF8}\text{Cold-Start Fallback:}$** Any unseen artist or song in `X_test` receives the global training skip rate (~10.4%).
6. **$\color{#38BDF8}\text{Dense Micro-Moods:}$** Calculate `seconds_since_last_skip` and `skips_last_15m` to capture immediate psychological state without temporal leakage.

## $\color{#F59E0B}{\text{4. Model Evaluation and Imbalance Calibration}}$
Because user skips represent a minority class (~10.4% in modern streams), standard accuracy can be misleading:
* **$\color{#38BDF8}\text{Cost-Sensitive Weighting:}$** XGBoost is initialized with `scale_pos_weight = 8.63` (calculated from `negative_count / positive_count`), forcing the algorithm to aggressively penalize missed skips.
* **$\color{#38BDF8}\text{Balanced Comparison:}$** Random Forest is trained using `class_weight='balanced'` for comparison.
* **$\color{#38BDF8}\text{Precision vs. Recall Trade-off:}$**
  * **False Positive (False Alarm):** Model predicts a skip, but the user listened. (Degrades user experience if auto-skipped).
  * **False Negative (Missed Skip):** Model predicts a listen, but user skipped. (Wastes CDN cache bandwidth).
* **$\color{#38BDF8}\text{Diagnostic Confusion Matrix:}$** Visualized via Seaborn heatmap and saved to `reports/images/ml_xgb_confusion_matrix.png`.

## $\color{#F59E0B}{\text{5. The Probabilistic Upgrade (Advanced)}}$
Once the base Binary Classifier (1 or 0) is working perfectly, we will upgrade the architecture to use a **Probabilistic Approach** (`.predict_proba()`).
Instead of letting the model blindly guess 1 or 0 at a 50% threshold, we will extract the raw confidence percentage (e.g., `0.85`). This allows us to set custom business thresholds:
* **Auto-Skip UI Feature:** Set threshold to `0.90` (Only auto-skip if 90% sure, minimizing False Alarms).
* **Background Caching:** Set threshold to `0.60` (Save bandwidth by not caching if there is a 60% chance of a skip).

## $\color{#F59E0B}{\text{6. Model Serialization and Production CLI Pipeline [WORKING BASELINE]}}$
The baseline model has been serialized for inference and production pipeline execution:
* **$\color{#38BDF8}\text{Model Extraction:}$** The tuned XGBoost model, feature list, and calibrated decision threshold (0.625) are serialized via `joblib` into [`models/spotify_skip_predictor_xgb.pkl`](../models/spotify_skip_predictor_xgb.pkl) (431.71 KB).
* **$\color{#38BDF8}\text{Production CLI Engine:}$** Implemented in [`pipeline/03_ml_modeling.py`](../pipeline/03_ml_modeling.py) with automatic on-the-fly feature calculation fallback, modern windowing (2023+), threshold calibration, and confusion matrix heatmap generation.
* **$\color{#38BDF8}\text{Honest Benchmark Assessment:}$** While overall accuracy is 97.0% and precision is 0.74, **Recall stands at 0.48** (the model misses 52% of skips). The high accuracy is heavily weighted by non-skips. Formal hyperparameter tuning is required to push recall into optimal territory.

---

## $\color{#F59E0B}{\text{7. Timeline, Strategic Pivot and Productionization (August–September 2026)}}$

### $\color{#38BDF8}\text{August 2026: The Data Analyst Pivot}$
* Following initial feature engineering experiments in Jupyter notebooks, active MLOps deployment was strategically paused.
* To target technical assessment deadlines for Data Analyst / BI roles (Mercari, Rakuten, PayPay), focus temporarily pivoted toward LeetCode SQL (Window Functions, CTEs) and Product Analytics KPIs.

### $\color{#38BDF8}\text{September 2026: Full Pipeline Productionization}$
* Resumed the Machine Learning tier to elevate research notebooks into a standalone, reproducible CLI pipeline:
  * **Decoupled CLI Engine:** Created [`pipeline/03_ml_modeling.py`](../pipeline/03_ml_modeling.py) matching [`notebooks/03_ml_modeling.ipynb`](../notebooks/03_ml_modeling.ipynb) 1:1.
  * **Automated Fallback Calculation:** Enabled the CLI to compute micro-moods on the fly if pre-computed feature tables are not yet loaded.
  * **Model Serialization:** Persisted the working XGBoost model, calibrated decision threshold (0.625), and feature schema into [`models/spotify_skip_predictor_xgb.pkl`](../models/spotify_skip_predictor_xgb.pkl) (431.71 KB).
  * **Diagnostic Heatmap:** Automated rendering of confusion matrix diagnostics into `reports/images/ml_xgb_confusion_matrix.png` confirming **97.0% accuracy** and **0.824 ROC-AUC**.

---

## $\color{#F59E0B}{\text{8. Next Steps: Systematic Hyperparameter Tuning and Recall Optimization}}$

While the current pipeline successfully defeated Concept Drift and proved the dominance of Micro-Moods over static genres, **Recall (0.48) remains an open bottleneck**. Formal algorithmic tuning has not yet been executed.

### $\color{#38BDF8}\text{Phase A: Automated Hyperparameter Search (Optuna / Bayesian)}$
Execute a 500-trial Optuna study to optimize the continuous search space:
* `max_depth`: Search range `[3, 10]` to prevent shallow underfitting or leaf memorization.
* `learning_rate` (`eta`): Search range `[0.005, 0.2]` with cosine annealing schedule.
* `subsample` and `colsample_bytree`: Search range `[0.5, 0.95]` to add stochastic regularization.
* `min_child_weight`: Search range `[1, 12]` to control tree partitioning on minority skips.
* Regularization: `reg_alpha` (L1) and `reg_lambda` (L2) to penalize feature redundancy.

### $\color{#38BDF8}\text{Phase B: Tackling the Recall Bottleneck}$
1. **$\color{#38BDF8}\text{Focal Loss Implementation:}$** Replace standard binary cross-entropy with Focal Loss:
   $$\mathcal{L}_{\text{focal}} = -\alpha_t (1 - p_t)^\gamma \log(p_t)$$
   Down-weight easy negatives (non-skips) and focus gradient updates exclusively on hard-to-predict skip events.
2. **$\color{#38BDF8}\text{Cost-Sensitive Weight Sweeping:}$** Systematically evaluate `scale_pos_weight` across the range `[6.0, 16.0]` to force the decision boundary to capture $\ge 70\%$ of true skips.
3. **$\color{#38BDF8}\text{Threshold Sensitivity SLA:}$** Establish distinct operational thresholds based on business use cases:
   * **Aggressive Caching (High Recall Target $\ge 0.75$):** Set threshold lower (~0.45) to prioritize saving server cache bandwidth.
   * **Auto-Skip UI (High Precision Target $\ge 0.85$):** Retain higher threshold (~0.70) to prevent annoying false-alarm skips.

### $\color{#38BDF8}\text{Phase C: Advanced Architecture and Ensembling}$
* **Model Stacking:** Blend tuned XGBoost with LightGBM (histogram-based splits) and CatBoost (ordered target encoding).
* **Sequential Deep Learning:** Evaluate a lightweight 1D-CNN or GRU on sliding 5-song playback histories to test whether temporal momentum improves recall beyond gradient boosting trees.
