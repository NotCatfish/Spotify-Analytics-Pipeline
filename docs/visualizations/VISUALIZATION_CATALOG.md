# Spotify Data Visualization Catalog and Architectural Guide

All 21 core Consumer and Infrastructure visualizations are styled in the custom **Japanese Winter Night** palette (`#0D1321`), saved as high-resolution PNGs in [`reports/images/`](../../reports/images), and embedded in [`reports/EDA_Report.md`](../../reports/EDA_Report.md). Machine learning diagnostic plots are automated in [`pipeline/03_ml_modeling.py`](../../pipeline/03_ml_modeling.py).

## $\color{#F59E0B}{\text{Phase 1: The Spotify Wrapped Experience (Consumer / Persona Graphs)}}$
*Focus: Fun, lifestyle analysis, serendipity, and habit exploration.*

1. **$\color{#38BDF8}\text{The Obsession Curve / Phases of Listening:}$** Tracking play counts of top artists across 7 years to visualize life phases.
   - `reports/images/chart_01_phases_of_listening.png`
2. **$\color{#38BDF8}\text{The Serendipity Spike / Artist Discovery:}$** Brand new artists discovered each month, comparing algorithmic (`trackdone`) vs manual search (`clickrow`).
   - `reports/images/chart_02_artist_discovery_funnel.png`
3. **$\color{#38BDF8}\text{Daily Rhythm (The 5 Quadrants of Listening):}$** Radial radar chart analyzing listening volume across Night Owl, Early Bird, Morning Rush, Afternoon Focus, and Evening Wind-Down.
   - `reports/images/chart_03_5_quadrants_of_listening.png`
4. **$\color{#38BDF8}\text{Seasonal Vibes:}$** Grouped faceted bar charts comparing top artists across Summer vs Winter seasons.
   - `reports/images/chart_04_seasonal_vibes.png`
5. **$\color{#38BDF8}\text{The One-Hit Wonder Wall of Fame:}$** Horizontal bar chart highlighting artists with massive play counts but only 1 unique song.
   - `reports/images/chart_05_one_hit_wonder_wall_of_fame.png`
6. **$\color{#38BDF8}\text{Loyalty Streaks:}$** Specialized chart visualizing the longest unbroken monthly listening streaks for core artists.
   - `reports/images/chart_06_artist_loyalty_streaks.png`
7. **$\color{#38BDF8}\text{Weekend vs. Weekday Shift:}$** Grouped bar chart comparing shuffle rates and skip behavior between weekdays and weekends.
   - `reports/images/chart_07_weekend_vs_weekday_shift.png`
8. **$\color{#38BDF8}\text{The Attention Span Decay:}$** Continuous trendline showing median `sec_played` before skips across years (filtered $\le 630$s).
   - `reports/images/chart_08_attention_span_decay.png`
9. **$\color{#38BDF8}\text{Skip-Trigger Heatmap:}$** 2D matrix (Day of Week vs Hour of Day) pinpointing peak user impatience.
   - `reports/images/chart_09_skip_trigger_heatmap.png`
10. **$\color{#38BDF8}\text{The Binge Metric:}$** Distribution of uninterrupted listening session lengths shown via piecewise and log-scaled histograms.
    - `reports/images/chart_10_binge_metric_piecewise.png`
    - `reports/images/chart_11_binge_metric_log.png`

---

## $\color{#F59E0B}{\text{Phase 2: Business and Infrastructure (The Spotify Engineer Graphs)}}$
*Focus: Bandwidth conservation, server scaling, hardware distribution, UI/UX optimization.*

11. **$\color{#38BDF8}\text{Global Traffic Heatmap:}$** 2D Heatmap (Day vs Hour) of raw play volume used by cloud engineers to pre-scale infrastructure before peak traffic.
    - `reports/images/chart_12_cloud_autoscaling_traffic_heatmap.png`
12. **$\color{#38BDF8}\text{Micro-Buffering Threshold (CDF):}$** Cumulative Distribution Function (CDF) showing that 80%+ of skips happen before 15 seconds, proving CDN pre-fetch waste.
    - `reports/images/chart_13_micro_buffering_threshold.png`
13. **$\color{#38BDF8}\text{Total Bandwidth Wasted:}$** Stacked bar chart comparing audio streamed for completed vs skipped songs.
    - `reports/images/chart_14_cloud_bandwidth_cache_waste.png`
14. **$\color{#38BDF8}\text{Hardware Dominance:}$** Donut chart showing platform breakdown across Android, Windows, Linux, and Smart Speakers.
    - `reports/images/chart_15_hardware_dominance.png`
15. **$\color{#38BDF8}\text{Engagement by Hardware:}$** Comparison of skip rates across mobile (Android) vs desktop (Windows/Linux).
    - `reports/images/chart_16_platform_engagement_ratios.png`
16. **$\color{#38BDF8}\text{Stream Lifecycle (Sankey Diagram):}$** Flow mapping from `reason_start` to `reason_end` tracking track lifecycles.
    - `reports/images/chart_17_stream_lifecycle_sankey.png`
    - Interactive HTML: `reports/images/chart_17_stream_lifecycle_sankey.html`
17. **$\color{#38BDF8}\text{Autoplay Reliance Engine:}$** Longitudinal tracking of algorithmic autoplay (`trackdone`) percentage over time.
    - `reports/images/chart_18_autoplay_reliance_engine.png`
18. **$\color{#38BDF8}\text{UI Feature Usage:}$** Donut breakdown of manual navigation actions (`clickrow`, `fwdbtn`, `backbtn`, `playbtn`).
    - `reports/images/chart_19_ui_feature_donut.png`
19. **$\color{#38BDF8}\text{Daily Active Listening Time (DAU vs MAU Proxy):}$** 30-day rolling average tracking streaming volume and retention.
    - `reports/images/chart_20_dau_vs_mau.png`
20. **$\color{#38BDF8}\text{Sleep/Churn Detection:}$** Distribution of silent gaps between listening sessions to detect sleep habits and churn risk.
    - `reports/images/chart_21_sleep_churn.png`

---

## $\color{#F59E0B}{\text{Phase 3: Machine Learning Diagnostic Visualizations}}$
*Focus: Confusion matrix, feature importances, precision-recall threshold calibration.*

21. **$\color{#38BDF8}\text{XGBoost Skip Prediction Confusion Matrix:}$** Diagnostic heatmap evaluating True Negatives, False Positives, False Negatives, and True Positives at the calibrated 0.625 threshold.
    - `reports/images/ml_xgb_confusion_matrix.png`

---

## $\color{#F59E0B}{\text{Theme and Styling Standards}}$
All charts are rendered using the custom **Japanese Winter Night** palette:
- **Canvas Background:** `#0D1321` (Deep midnight navy)
- **Axes / Subplot Background:** `#111827` (Dark charcoal)
- **Text and Ticks:** `#E0E6ED` / `#CBD5E1` (Soft starlight gray)
- **Typography:** Meiryo, sans-serif
- **Accent Palette:** Cyan (`#00F2FE`), Electric Violet (`#7F00FF`), Coral (`#FF4B4B`), Emerald (`#00E676`)
