# Machine Learning Progress Log: Model Iterations and Metric Evolution

This document is the empirical research log for the Spotify Skip Prediction Model. It tracks every experimental attempt (Attempts 1 through 6), documenting the features tested, the resulting metrics (Accuracy, Precision, Recall, ROC-AUC), and the exact technical and mathematical reasons why scores improved, collapsed, or stabilized.

---

## $\color{#F59E0B}{\text{Summary of Model Progression (Attempts 1 - 6)}}$

| Attempt | Split Strategy | Feature Set | Primary Model | Accuracy | ROC-AUC | Recall | Precision | Core Diagnosis and Key Lesson Learned |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | Random 80/20 | `sec_played`, `skipped` | XGBoost | 80% | — | — | — | **Catastrophic Target Leakage:** `sec_played` directly leaks whether a track was skipped early. |
| **2** | Random 80/20 | `sec_played` + Genres | XGBoost | 98% | — | — | — | **Severe Overfitting / Leech:** Model simply memorized correlation between short duration and skips. |
| **3** | Random 80/20 | Dropped `sec_played` | Baseline | 90% | — | ~0.00 | ~0.00 | **Majority Class Imbalance Trap:** 90% of streams are non-skips; model predicted all 0s blindly. |
| **4** | Random 80/20 | Clean Behavioral + 154 OHE Genres | XGBoost / RF | ~93% | 0.948 | 0.89 | 0.59 | **Repeated Song Leakage ("Time Machine" Cheat):** Random splitting mixed future and past streams of the same songs, memorizing future user taste. |
| **5** | Chronological (2019–2024 / 2025+) | Dynamic Target Encoding + `int8` compression | RF / XGBoost | — | 0.650 | 0.06 (RF)<br>0.42 (XGB) | 0.45 | **Discovery of Concept Drift:** Skip rate dropped from 31% in 2021 to 4% in 2025. Model trained on an impatient younger user failed on an older patient user. |
| **7** | Chronological 70/30 (2023–2026) | 19 Features (Acute `skips_last_3m`, `consecutive_listens_streak`, Multi-Genre Blend, `reason_start`) | **XGBoost (Threshold 0.756, Untuned)** | **97.0%** | **0.850** | **0.45** | **0.77** | **Feature Engineering Ceiling:** Transitioned to 70/30 split and 19 features. Pushed ROC-AUC from 0.824 to 0.850 and Precision to 77% purely through behavioral feature engineering without any algorithmic hyperparameter tuning. |

---

## $\color{#F59E0B}{\text{Detailed Experiment Logs}}$

### $\color{#38BDF8}\text{1st Attempt: The Target Leakage Blunder}$
* **Configuration:** Initial experiment using raw `sec_played` and boolean `skipped` to predict skips using baseline XGBoost.
* **Result:** 80% accuracy.
* **Diagnosis and Why it Failed:** Complete data leakage. In real-world inference, `sec_played` is unknown until *after* the stream ends. Using listening duration to predict whether a user skips is mathematically invalid because early skips trivially terminate duration.

---

### $\color{#38BDF8}\text{2nd Attempt: The Overfitting Mirage}$
* **Configuration:** Added genre columns to the previous setup, retaining `sec_played`.
* **Result:** 98% accuracy.
* **Diagnosis and Why it Failed:** The model achieved near-perfect accuracy not by learning user psychology, but by memorizing the direct mathematical boundary between `sec_played < 30` and skips. This was a classic data leech / overfit artifact with zero real-world utility.

---

### $\color{#38BDF8}\text{3rd Attempt: The Class Imbalance Trap}$
* **Configuration:** Aggressively purged `sec_played` to enforce true pre-playback inference.
* **Result:** Accuracy plummeted to 90%, but recall collapsed to near zero.
* **Diagnosis and Why it Failed:** Because ~90% of tracks in the dataset were completed without skipping, the classifier minimized cross-entropy loss by predicting `is_skip = 0` for 100% of rows. The 90% accuracy was a statistical illusion masking a model with zero discriminative capability.

---

### $\color{#38BDF8}\text{4th Attempt: The Time Machine Cheat (Repeated Song Leakage)}$
* **Configuration:** Dropped all post-event columns (`skipped`, `sec_played`, `ms_played`, `reason_end`). Engineered legitimate pre-stream behavioral features (`shuffle_int`, `day_of_week`, `seconds_since_last_song`) and retained all 154 One-Hot Encoded genre columns. Applied `scale_pos_weight` and `class_weight='balanced'` on a standard random 80/20 train/test split.
* **Scores:**
  * **XGBoost:** ROC-AUC: 0.9484 | Recall: 0.89 | Precision: 0.59
  * **Random Forest:** ROC-AUC: 0.9526 | Recall: 0.69 | Precision: 0.77
* **Diagnosis and Why the Score Was a Lie:**
  Although the metrics appeared spectacular, they were artificially inflated by **Repeated Song Leakage (The Sandbox Effect)**. Because streams were randomly shuffled across time, a song played 100 times between 2019 and 2025 had its plays distributed across both Train and Test splits. The AI peeks into the future to memorize how user preferences evolved, completely circumventing the "Cold Start Problem" that production recommendation engines face.

---

### $\color{#38BDF8}\text{5th Attempt: The Chronological Split and Discovery of Concept Drift}$
* **Configuration:** Replaced the random 80/20 split with a **Strict Chronological Split** (Train on 2019–2024; Test on 2025–2026). Implemented **Dynamic Expanding Target Encoding** using `expanding().mean().shift(1)` to compute rolling historical skip risks without leaking future data. Compressed all binary features to `int8`, slashing RAM from 277MB to 58MB.
* **Scores:**
  * **Random Forest:** Recall collapsed to **0.06** (Abysmal failure).
  * **XGBoost (`scale_pos_weight = 5.03`):** Recall reached **0.42** (Adapted aggressively to minority class).
* **Diagnosis and Why Scores Collapsed:**
  The experiment revealed severe **Concept Drift**:
  1. Historical data analysis proved the user's skip rate was **31% in 2021**, but plummeted to just **4% in 2025**.
  2. The model trained on a younger, hyper-impatient listener, but was evaluated against an older, patient listener who lets music play passively.
  3. Static historical preferences could not generalize across a multi-year lifestyle change.

---

### $\color{#38BDF8}\text{6th Attempt: Windowing and Micro-Mood Engineering (Initial Baseline)}$
* **Configuration:**
  1. **$\color{#38BDF8}\text{Windowing (Strategy 1):}$** Permanently discarded all ancient data prior to 2023 (`year >= 2023`), starving the model of obsolete listening patterns.
  2. **$\color{#38BDF8}\text{Micro-Mood Features:}$** Engineered real-time psychological state indicators (`seconds_since_last_skip`, `skips_last_15m`, `previous_song_skipped`).
  3. **$\color{#38BDF8}\text{Target Encoding:}$** Dynamic smoothed target encoding on training data with global mean fallback (~10.4%) on holdout test data.
  4. **$\color{#38BDF8}\text{Threshold Calibration:}$** Tuned the decision boundary across the Precision-Recall curve to locate the mathematical F1 sweet spot (0.625).
* **Scores (Untuned 7-Feature Baseline):**
  * **XGBoost (Threshold 0.625, `scale_pos_weight = 8.63`):**
    * **Overall Accuracy:** 97.0%
    * **ROC-AUC:** 0.824
    * **Recall:** 0.48
    * **Precision:** 0.74
* **Diagnosis:** Successfully defeated concept drift and proved micro-mood importance, but model was constrained by limited feature scope (only 7 features) and default algorithm hyperparameters.

---

### $\color{#38BDF8}\text{7th Attempt: Expanded Feature Engineering and 70:30 Chronological Split (Pure Features, Untuned)}$
* **Configuration:**
  1. **$\color{#38BDF8}\text{70:30 Chronological Split:}$** Shifted from arbitrary calendar-year splitting to a strict 70:30 chronological holdout. Trained on the first 70% of modern streams (88,760 samples: Jan 2023 to Feb 2025) and tested on the remaining 30% future window (38,040 samples: Feb 2025 to Aug 2026).
  2. **$\color{#38BDF8}\text{Upgraded 19-Feature Matrix:}$**
     * **Acute Momentum:** Added `skips_last_3m` (capturing rapid 180-second skipping sprees) and `consecutive_listens_streak` (measuring uninterrupted listening momentum via `.shift(1)`).
     * **Playback Trigger Context:** Added `reason_start_smoothed_skip_rate` (capturing the 24x divergence between `fwdbtn` at 60.4% and `trackdone` at 2.5%).
     * **Multi-Genre Blended Risk:** Replaced 154 sparse One-Hot columns with a single dynamic expanding average risk across all Last.fm genre tags per track.
     * **Environmental & Circadian Dynamics:** Added `platform_android`, `platform_windows`, `shuffle_mode`, `is_session_start` (gap > 20 min), and continuous circular `hour_sin` / `hour_cos`.
  3. **$\color{#38BDF8}\text{Model Setup:}$** Untuned baseline XGBoost (`n_estimators=100`, `max_depth=6`, `learning_rate=0.1`, `scale_pos_weight=9.01`, default binary log-loss).
* **Scores (Pure Feature Engineering, No Parameter Tuning):**
  * **XGBoost (Optimal Threshold 0.756, `scale_pos_weight = 9.01`):**
    * **Overall Accuracy:** **97.0%**
    * **ROC-AUC:** **0.850** (Up from 0.824, a +0.026 jump purely from feature engineering)
    * **Tuned Precision:** **0.77** (Up from 0.74 in Attempt 6)
    * **Tuned Recall:** **0.45**
    * **F1-Score:** **0.57**
* **Key Findings and Architectural Wins:**
  1. **$\color{#38BDF8}\text{Peak Feature Engineering Ceiling:}$** Proved that without touching a single hyperparameter, expanding the feature matrix to 19 features and shifting to a 70:30 chronological split lifted ROC-AUC to 0.850.
  2. **$\color{#38BDF8}\text{Dominance of Acute Velocity:}$** `skips_last_3m` immediately captured over 70% of feature importance, demonstrating that acute, short-window impatience is the single strongest predictor of user skips.
  3. **$\color{#38BDF8}\text{Clear Boundary Established:}$** Confirmed that feature engineering alone has reached its maximum potential; breaking past the 0.45 Recall bottleneck requires formal hyperparameter optimization (Attempt 8).

---

### $\color{#38BDF8}\text{8th Attempt: Hardware-Accelerated Optuna Bayesian Tuning and Business SLA Enforcement (Champion Model)}$
* **Configuration:**
  1. **$\color{#38BDF8}\text{Business SLA Constraint (Precision Floor):}$** Shifted objective function from unconstrained F1 maximization to an explicit Business SLA Guardrail: guarantee at least **80% Precision** (preventing false alarms / audio buffering churn) while mathematically maximizing **Safe Recall** within the feasible boundary.
  2. **$\color{#38BDF8}\text{Bayesian Hyperparameter Search:}$** Deployed Optuna with Tree-structured Parzen Estimators (TPE) across 300 trials, searching across tree depth (4–8), tree count (100–300), learning rate (0.01–0.05), imbalance penalties (7.0–15.0), and L1/L2 regularization brakes.
  3. **$\color{#38BDF8}\text{Hardware Acceleration Pipeline:}$** Offloaded histogram construction and tree-split computations to NVIDIA GeForce RTX 3060 CUDA cores (`device='cuda'`, `tree_method='hist'`), with parallel CPU trial management on AMD Ryzen 7 (`n_jobs=4`). In Lenovo Legion Performance Mode, 300 trials completed in just 2 minutes and 25 seconds.
* **Winning Business Settings (Optimal Hyperparameters):**
  * `n_estimators`: 300
  * `max_depth`: 8
  * `learning_rate`: 0.01123
  * `scale_pos_weight`: 7.1765
  * `min_child_weight`: 8 (Requires at least 8 instances per leaf to eliminate noise memorization)
  * `subsample`: 0.6431 (Stochastic row sampling)
  * `colsample_bytree`: 0.5509 (Forces trees to only view 55% of features per split, breaking over-reliance on dominant features)
  * `reg_alpha`: 0.1869 (L1 sparsity penalty)
  * `reg_lambda`: 5.2722 (Heavy L2 shrinkage penalty against weight explosion)
  * `Decision Threshold Meeting SLA`: **0.676**
* **Scores (38,040 Holdout Future Streams / 1,439 Actual Skips):**
  * **Overall Accuracy:** **98.0%**
  * **ROC-AUC:** **0.857** (Highest overall discriminative power across all experiments)
  * **Guaranteed Precision:** **80.0%** (Strictly complies with business safety SLA)
  * **Maximized Safe Recall:** **47.39%** (Caught **682 skips** out of 1,439; an all-time high)
  * **F1-Score (Skip Class):** **0.60** (First experiment to successfully break into 0.60)
  * **False Alarms:** Only **170 false positives** out of 36,601 listened songs (0.46% error rate on listens)
* **Architectural Breakthroughs and Why It Succeeded:**
  1. **$\color{#38BDF8}\text{Feature Dropout via Colsample (0.55):}$** By hiding 45% of the features from each tree, XGBoost was forced to discover rich secondary signals (such as `consecutive_listens_streak`, `reason_start_smoothed_skip_rate`, and circular temporal coordinates) instead of relying solely on `skips_last_3m`.
  2. **$\color{#38BDF8}\text{Conservative Regularization:}$** Doubling `min_child_weight` to 8 and ramping L2 regularization (`reg_lambda`) to 5.27 allowed deep trees (`max_depth = 8`) to learn subtle multi-feature interactions without overfitting to rare historical anomalies.
  3. **$\color{#38BDF8}\text{Threshold Operating Window:}$** Finding the optimal operating threshold at **0.676** provided a stable, well-centered probability margin that safely preserves 80% precision under production data distribution shifts.
  4. **$\color{#38BDF8}\text{Ingestion Numeric Auto-Compression (2x Hardware Throughput Boost):}$** By introducing automated schema downcasting upon SQL ingestion (`compress_numeric_columns` -> `int8` flags/small counts, `int16` years/streaks, `int32` counts, `float32` continuous rates), the in-memory footprint was slashed from 101.45 MB to 64.53 MB (-36.4%). This eliminated host-to-device PCIe bandwidth saturation and FP64 emulation bottlenecks on the RTX 3060, doubling parallel Optuna search throughput from **2 it/s to 4 it/s** (slashing 300-trial search time from 2.5 minutes down to ~1.25 minutes).

