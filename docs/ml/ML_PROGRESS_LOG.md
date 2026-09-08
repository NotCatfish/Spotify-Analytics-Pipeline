# Machine Learning Progress Log: Model Iterations & Metric Evolution

This document is the empirical research log for the Spotify Skip Prediction Model. It tracks every experimental attempt (Attempts 1 through 6), documenting the features tested, the resulting metrics (Accuracy, Precision, Recall, ROC-AUC), and the exact technical and mathematical reasons why scores improved, collapsed, or stabilized.

---

## 📊 Summary of Model Progression (Attempts 1–6)

| Attempt | Split Strategy | Feature Set | Primary Model | Accuracy | ROC-AUC | Recall | Precision | Core Diagnosis & Key Lesson Learned |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | Random 80/20 | `sec_played`, `skipped` | XGBoost | 80% | — | — | — | **Catastrophic Target Leakage:** `sec_played` directly leaks whether a track was skipped early. |
| **2** | Random 80/20 | `sec_played` + Genres | XGBoost | 98% | — | — | — | **Severe Overfitting / Leech:** Model simply memorized correlation between short duration and skips. |
| **3** | Random 80/20 | Dropped `sec_played` | Baseline | 90% | — | ~0.00 | ~0.00 | **Majority Class Imbalance Trap:** 90% of streams are non-skips; model predicted all 0s blindly. |
| **4** | Random 80/20 | Clean Behavioral + 154 OHE Genres | XGBoost / RF | ~93% | 0.948 | 0.89 | 0.59 | **Repeated Song Leakage ("Time Machine" Cheat):** Random splitting mixed future and past streams of the same songs, memorizing future user taste. |
| **5** | Chronological (2019–2024 / 2025+) | Dynamic Target Encoding + `int8` compression | RF / XGBoost | — | 0.650 | 0.06 (RF)<br>0.42 (XGB) | 0.45 | **Discovery of Concept Drift:** Skip rate dropped from 31% in 2021 to 4% in 2025. Model trained on an impatient younger user failed on an older patient user. |
| **6** | Chronological Windowed (2023–2024 / 2025+) | Windowing (2023+) + Micro-Moods (`seconds_since_last_skip`, `skips_last_15m`) | **XGBoost (Threshold 0.625)** | **97.0%** | **0.824** | **0.48** | **0.74** | **Current Baseline (Untuned):** Defeated concept drift and proved micro-mood importance, but **Recall (0.48) is a major bottleneck** (misses 52% of skips); systematic hyperparameter tuning is pending. |

---

## Detailed Experiment Logs

### 1st Attempt: The Target Leakage Blunder
* **Configuration:** Initial experiment using raw `sec_played` and boolean `skipped` to predict skips using baseline XGBoost.
* **Result:** 80% accuracy.
* **Diagnosis & Why it Failed:** Complete data leakage. In real-world inference, `sec_played` is unknown until *after* the stream ends. Using listening duration to predict whether a user skips is mathematically invalid because early skips trivially terminate duration.

---

### 2nd Attempt: The Overfitting Mirage
* **Configuration:** Added genre columns to the previous setup, retaining `sec_played`.
* **Result:** 98% accuracy.
* **Diagnosis & Why it Failed:** The model achieved near-perfect accuracy not by learning user psychology, but by memorizing the direct mathematical boundary between `sec_played < 30` and skips. This was a classic data leech / overfit artifact with zero real-world utility.

---

### 3rd Attempt: The Class Imbalance Trap
* **Configuration:** Aggressively purged `sec_played` to enforce true pre-playback inference.
* **Result:** Accuracy plummeted to 90%, but recall collapsed to near zero.
* **Diagnosis & Why it Failed:** Because ~90% of tracks in the dataset were completed without skipping, the classifier minimized cross-entropy loss by predicting `is_skip = 0` for 100% of rows. The 90% accuracy was a statistical illusion masking a model with zero discriminative capability.

---

### 4th Attempt: The "Time Machine" Cheat (Repeated Song Leakage)
* **Configuration:** Dropped all post-event columns (`skipped`, `sec_played`, `ms_played`, `reason_end`). Engineered legitimate pre-stream behavioral features (`shuffle_int`, `day_of_week`, `seconds_since_last_song`) and retained all 154 One-Hot Encoded genre columns. Applied `scale_pos_weight` and `class_weight='balanced'` on a standard random 80/20 train/test split.
* **Scores:**
  * **XGBoost:** ROC-AUC: 0.9484 | Recall: 0.89 | Precision: 0.59
  * **Random Forest:** ROC-AUC: 0.9526 | Recall: 0.69 | Precision: 0.77
* **Diagnosis & Why the Score Was a Lie:**
  Although the metrics appeared spectacular, they were artificially inflated by **Repeated Song Leakage (The Sandbox Effect)**. Because streams were randomly shuffled across time, a song played 100 times between 2019 and 2025 had its plays distributed across both Train and Test splits. The AI peeks into the future to memorize how user preferences evolved, completely circumventing the "Cold Start Problem" that production recommendation engines face.

---

### 5th Attempt: The Chronological Split & Discovery of "Concept Drift"
* **Configuration:** Replaced the random 80/20 split with a **Strict Chronological Split** (Train on 2019–2024; Test on 2025–2026). Implemented **Dynamic Expanding Target Encoding** using `expanding().mean().shift(1)` to compute rolling historical skip risks without leaking future data. Compressed all binary features to `int8`, slashing RAM from 277MB to 58MB.
* **Scores:**
  * **Random Forest:** Recall collapsed to **0.06** (Abysmal failure).
  * **XGBoost (`scale_pos_weight = 5.03`):** Recall reached **0.42** (Adapted aggressively to minority class).
* **Diagnosis & Why Scores Collapsed:**
  The experiment revealed severe **Concept Drift**:
  1. Historical data analysis proved the user's skip rate was **31% in 2021**, but plummeted to just **4% in 2025**.
  2. The model trained on a younger, hyper-impatient listener, but was evaluated against an older, patient listener who lets music play passively.
  3. Static historical preferences could not generalize across a multi-year lifestyle change.

---

### 6th Attempt: Windowing & Micro-Mood Engineering (Current Baseline Model)
* **Configuration:**
  1. **Windowing (Strategy 1):** Permanently discarded all ancient data prior to 2023 (`year >= 2023`), starving the model of obsolete listening patterns.
  2. **Micro-Mood Features:** Engineered real-time psychological state indicators:
     * `seconds_since_last_skip`: Temporal distance to the last skip event.
     * `skips_last_15m`: Rolling count of skips within the preceding 15-minute sliding window.
     * `previous_song_skipped`: Immediate binary inertia indicator.
  3. **Target Encoding:** Dynamic smoothed target encoding on training data with global mean fallback (~10.4%) on holdout test data.
  4. **Threshold Calibration:** Tuned the decision boundary across the Precision-Recall curve to locate the mathematical F1 sweet spot (0.625) rather than using the arbitrary 0.50 threshold.
* **Current Baseline Scores (Untuned):**
  * **XGBoost (Threshold 0.625, `scale_pos_weight = 8.63`):**
    * **Overall Accuracy:** **97.0%**
    * **ROC-AUC:** **0.824**
    * **Recall:** **0.48** (Bottleneck)
    * **Precision:** **0.74**
  * **Random Forest (Threshold 0.330, `class_weight='balanced'`):**
    * **ROC-AUC:** 0.794
    * **Recall:** 0.45
    * **Precision:** 0.77
* **Key Findings, Achievements & Open Bottlenecks:**
  1. **Zero Data Leakage:** Validated on a strict forward chronological holdout split (2025+).
  2. **Defeated Concept Drift:** Confining training to 2023+ aligned the training distribution directly with modern user behavior.
  3. **Psychological State Trumps Taste:** Immediate psychological context (Micro-Moods) accounted for **~60% of predictive power**, proving current mood dictates skips more than historical artist affinity.
  4. **The Critical Recall Bottleneck:** At **0.48 Recall**, the model currently catches less than half of actual skips—missing **52%** of skip events. The high 97.0% accuracy is an artifact of the 10:1 non-skip class majority.
  5. **Hyperparameter Tuning Pending:** Systematic hyperparameter tuning (Optuna, tree depth, learning rate, subsample, regularization) has not been performed yet. This model is a functioning baseline that proves the feature engineering concepts, but requires formal algorithmic tuning to push Recall into viable production territory (target: $\ge 0.70$).
