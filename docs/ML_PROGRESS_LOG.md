### 1st attempt

very first time using only sec_played and skipped using xgboost got 80%accuracy but it was incorrect as data leeach

### 2nd attempt

2nd time used genre etc and tried it got 98 but there was data leech so the model just memorized i.e overfitted using sec_played and skipped correlation

### 3rd attempt

3rda ttempt stopped the sec_played accuracy dropped to 90%  but there was still overfitting as the model literally memorized as 90% of the data is false as i dont skip just keep guessing it as false

### 4th attempt: SUCCESS!

We aggressively dropped all "cheat codes" (`skipped`, `sec_played`, `ms_played`, `reason_end`) and trained on engineered behavioral features (`shuffle_int`, `day_of_week`, `seconds_since_last_song`) plus all One-Hot Encoded Genres. We used XGBoost and Random Forest, applying `scale_pos_weight` and `class_weight='balanced'` to force the AI to care about the 14% minority "skip" class.

**Final Scores (Attempt 4):**

- **XGBoost:** ROC-AUC: 0.9484 | Recall: 0.89 | Precision: 0.59 (Highly aggressive, threw false alarms to catch 89% of skips).
- **Random Forest:** ROC-AUC: 0.9526 | Recall: 0.69 | Precision: 0.77 (Cautious, optimized for UX by avoiding false alarms).

**Why was the score a massive 0.95+? (The "Time Machine" Cheat)**
Initially, we thought this was a brilliant success, but the 0.95 ROC-AUC was actually a lie caused by **Data Leakage (The Sandbox Effect)**.
Because we used a Random 80/20 Split, we accidentally created a "Time Machine." If a song was played 100 times over 5 years (e.g., loved in 2023, hated in 2025), the random shuffle mixed the 2023 and 2025 plays together.
The Training set received future data (2025 plays) and used it to predict the Test set (2023 plays). The AI didn't learn how to predict skips; it simply peeked into the future to memorize exactly how your taste would change, bypassing the "Cold Start Problem" that real-world AI faces.

**Winner:** Random Forest. In a consumer application, UX is king. It's better to miss a skip (lower recall) than to accidentally skip a song the user wanted to hear (high precision), protecting Lifetime Customer Value over short-term server savings.

---

### 5th Attempt: The Chronological Split & Discovery of "Concept Drift"

We transitioned from a random 80/20 split (which caused "Repeated Song Leakage") to a **Strict Chronological Split** (train on 2019-2024, test on 2025-2026). We replaced static encoding with **Dynamic Target Encoding** using `expanding().mean().shift(1)` to create rolling skip risk profiles without leaking future data. We converted memory-heavy columns to `int8`, reducing RAM usage from 277MB to 58MB.

**Final Scores (Attempt 5):**

- **Random Forest:** Recall: 0.06 (Abysmal failure).
- **XGBoost (with scale_pos_weight):** Recall: 0.42 (Adapted aggressively to the imbalance).

**Why did the score collapse? (The Concept Drift Trap)**

1. **Concept Drift:** We discovered the user's skip rate was a massive **31%** in 2021, but plummeted to just **4%** in 2025.
2. **Behavioral Change:** The model perfectly memorized a younger, hyper-active user, but was tested on an older, patient user. It failed to adapt to the new behavior.

**Winner:** XGBoost, proving its superior flexibility over Random Forest when handling severe concept drift and extreme class imbalance.

---

### 6th Attempt: Windowing & Micro-Mood Engineering (The Champion Model)

To defeat Concept Drift without resorting to messy SMOTE hallucination (which failed spectacularly due to geometric interpolation on 154 sparse One-Hot genre columns), we deployed the "Pro Playbook." We used **Strategy 1 (Windowing)** by deleting all ancient data prior to 2023. We dropped the 154 OHE columns and engineered dense **Micro-Moods** (`seconds_since_last_skip`, `skips_last_15m`) and **Smoothed Dynamic Target Encoding** for artists and songs. Finally, we performed **Precision-Recall Threshold Tuning** to find the mathematical F1 sweet spot instead of relying on the default 0.50 threshold.

**Final Scores (Attempt 6):**

- **XGBoost (Threshold 0.632):** ROC-AUC: 0.825 | Recall: 0.48 | Precision: 0.74 (Strongest overall mathematical model, anchored 71.6% of its logic on `seconds_since_last_skip`).
- **Random Forest (Threshold 0.330):** ROC-AUC: 0.794 | Recall: 0.45 | Precision: 0.77 (Highly balanced learning profile, prioritizing user experience with fewer false alarms).

**Why is this the ultimate champion model?**

1. **No Data Leakage:** Tested on a strict 2025+ chronological split with perfectly isolated target encoding.
2. **Defeating Concept Drift:** By starving the model of pre-2023 data, it perfectly learned the "modern user."
3. **Psychology over History:** The feature importance proved that immediate psychological context (Micro-Moods) accounts for ~60% of predictive power, vastly outperforming historical genre/artist preferences.

**Winner:** Both are viable champions. **Random Forest** is better for a consumer-facing Auto-Skip UI feature (where avoiding false alarms is critical to protect UX), while **XGBoost** is better for invisible background caching (where catching every skip saves bandwidth).

---

### August 2026 Status Update: The Data Analyst Pivot

With the Champion Model selected and tuned to defeat Concept Drift, the Jupyter Notebook phase is officially concluded. 
> [!CAUTION]
> **We have officially cancelled the MLOps deployment phase.** 
> To hit the August 31st deadline for the Mercari Summer 2027 application cycle, we have pivoted strictly to a **Data Analyst Intern** roadmap. 
> All Machine Learning work is frozen. The immediate focus is a 9-day sprint grinding LeetCode SQL (Window Functions, CTEs) and Product Analytics to pass the Mercari Online Assessment (OA).
