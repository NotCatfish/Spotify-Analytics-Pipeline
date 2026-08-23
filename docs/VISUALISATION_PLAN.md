# 📊 SPOTIFY DATA VISUALIZATION PLAN (3-Phase Master Architecture)

> [!NOTE]
> **Status (August 2026):** Phase 1 is **COMPLETE**. We are currently pivoting away from visualizations to focus on **MLOps and API Deployment** of the Champion XGBoost model to prepare for the Summer 2027 internship application cycle. Phases 2 and 3 are paused.

## Phase 1: The "Spotify Wrapped" Experience (Consumer / Persona Graphs) [COMPLETE]
*Focus: Fun, induced metrics, lifestyle analysis, and serendipity. Stuff to post on social media.*

1. **The "Obsession" Curve:** A temporal line chart tracking the play count of your Top 3 artists across all 7 years to visualize "phases" of your life.
2. **The Serendipity Spike:** A bar chart showing the count of *brand new* artists discovered each month, color-coded by algorithmic discovery (`trackdone`) vs manual search (`clickrow`).
3. **Daily Rhythm (The Persona Radar):** A radar/spider chart showing your listening volume across 4 quadrants: Morning, Afternoon, Evening, and Late-Night.
4. **Seasonal Vibes:** A grouped bar chart comparing your top 5 artists played in Summer vs. Winter months.
5. **The "One-Hit Wonder" Wall of Fame:** A horizontal bar chart of artists with massive play counts but only 1 unique song.
6. **Loyalty Streaks:** A specialized bar chart visualizing the longest consecutive monthly streaks for your most loyal artists.
7. **Weekend vs. Weekday Shift:** A stacked bar chart showing if your shuffle habits or skip rates change when the weekend hits.
8. **The Attention Span Decay:** A line chart showing your `avg_seconds_before_skip` over the years. Are you getting more impatient as you get older?
9. **Skip-Trigger Heatmap:** A 2D Heatmap (Day of Week vs. Hour of Day) showing exactly when you are most easily annoyed and skip songs.
10. **The "Binge" Metric:** A distribution plot of your longest single uninterrupted listening sessions (e.g., 5 hours straight).

---

## Phase 2: Business & Infrastructure (The "Spotify Engineer" Graphs) [PAUSED]
*Focus: Bandwidth, server scaling, hardware analysis, UI/UX tracking.*

1. **Global Traffic Heatmap:** A 2D Heatmap (Day vs Hour) of raw play volume used by AWS engineers to pre-scale servers before peak traffic.
2. **Micro-Buffering Threshold (CDF):** A Cumulative Distribution Function (CDF) plot of `sec_played` on skipped tracks to prove that 80% of skips happen before 15 seconds (saving CDN bandwidth).
3. **Total Bandwidth Wasted:** A stacked bar chart showing the total hours of audio streamed for songs that were actually finished vs. songs that were skipped.
4. **Hardware Dominance:** A Tree Map or Donut chart showing the exact breakdown of Android vs Linux/IoT vs Windows devices.
5. **Engagement by Hardware:** A grouped bar chart comparing the Skip Rate on Android (Mobile) vs Windows (Desktop). Do users skip more on their phones?
6. **The App Navigation Flow (Sankey Diagram):** A flow chart mapping `reason_start` to `reason_end` to see the complete lifecycle of a song stream.
7. **Autoplay Reliance Engine:** A line chart tracking your `trackdone` (algorithmic autoplay) percentage over time. Is the algorithm doing more of the heavy lifting?
8. **UI Feature Usage:** A horizontal bar chart comparing manual navigation (`clickrow`, `fwdbtn`, `backbtn`).
9. **Daily Active Listening Time (DAU proxy):** A line chart with a 30-day rolling average showing your total hours streamed per day to track long-term app retention.
10. **Sleep/Churn Detection:** A distribution plot of the gaps (hours of silence) between listening sessions to detect sleep schedules and churn risk.

---

## Phase 3: Machine Learning & Feature Selection (The "Data Scientist" Graphs) [PAUSED]
*Focus: Correlation, target variables, predictive modeling preparation for predicting "Skips".*

1. **Global Correlation Matrix:** A massive Seaborn Heatmap of all numeric and boolean features to spot multi-collinearity.
2. **Skip Target Correlation:** A sorted bar chart showing which features (hour, platform, shuffle state) correlate most heavily with the target variable (`skipped`).
3. **Time of Day vs. Skip Probability:** A Boxplot or Violin plot checking if the variance in skip rates changes significantly based on the hour.
4. **Shuffle State vs. Skip Probability:** A Violin plot comparing skip distributions when `shuffle` is True vs False.
5. **Session Length vs. Skip Rate:** A scatter plot with a linear regression line testing the hypothesis: "The longer a user listens, the higher their skip rate becomes."
6. **Platform Skip Volatility:** A Boxplot showing the distribution of skip percentages across different devices.
7. **Artist "Skip-ability" Index:** A Kernel Density Estimate (KDE) plot showing the distribution of skip rates across all artists in the dataset.
8. **Day of Week vs. Skip Probability:** A bar chart with error bars (confidence intervals) checking if Mondays have significantly higher skip rates than Fridays.
9. **The "Perfect Track" Profile:** A parallel coordinates plot showing the common feature pathways of tracks that are *never* skipped.
10. **Target Class Imbalance:** A simple Pie chart showing the ratio of `Skipped == True` vs `Skipped == False` to determine if we need SMOTE or class weighting for the ML model.
