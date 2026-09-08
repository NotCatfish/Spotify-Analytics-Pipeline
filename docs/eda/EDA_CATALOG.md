# Spotify EDA Metrics and Table Catalog

This catalog documents every analytical metric, tabular aggregation, and ranking calculated across the exploratory analysis pipeline. All metrics dynamically adapt to the user's single `top_n` configuration prompt (default: 10) and compile directly into the executive markdown report at [`reports/EDA_Report.md`](../../reports/EDA_Report.md).

---

## $\color{#F59E0B}{\text{Quick Reference Index}}$

- [Section 1: The Top Charts (Volume and Affinity Rankings)](#section-1-top-charts)
- [Section 2: Temporal and Behavioral Habits (Time-Series)](#section-2-temporal-habits)
- [Section 3: Engagement and Skip Behavior](#section-3-skip-behavior)
- [Section 4: Technical and Geographic Metrics](#section-4-technical-geographic)
- [Section 5: Niche and Advanced Behavioral Metrics](#section-5-niche-metrics)

---

## <a id="section-1-top-charts"></a>$\color{#F59E0B}{\text{Section 1: The Top Charts (Volume and Affinity Rankings)}}$

### $\color{#38BDF8}\text{1.1 All-Time Top N Artists}$
* **Objective:** Identify the core artist discographies that dominate total playback history.
* **Input Columns:** `artist_name`, `sec_played`.
* **Aggregation Method:** Group by `artist_name`, compute `.agg(play_count=('artist_name', 'count'), total_hours=('sec_played', lambda s: s.sum() / 3600.0))`, sort descending by `play_count`.
* **Output Format:** Markdown table with rank, artist name, total play count, and cumulative listening hours.

### $\color{#38BDF8}\text{1.2 Top N Artists by Year, Month and Season}$
* **Objective:** Track longitudinal taste shifts across calendar years and meteorological seasons.
* **Input Columns:** `artist_name`, `year`, `month`, `season` (`Winter`, `Spring`, `Summer`, `Fall`).
* **Aggregation Method:** Multi-level groupby `[year, artist_name]` with `.head(top_n)` slice per partition.
* **Key Analytical Insight:** Discovers how listening habits pivot from energetic summer genres to ambient/lo-fi winter music.

### $\color{#38BDF8}\text{1.3 All-Time and Periodic Top N Songs}$
* **Objective:** Rank the individual tracks with the highest total stream count and playback volume.
* **Input Columns:** `song_name`, `artist_name`, `sec_played`.
* **Aggregation Method:** Group by `['song_name', 'artist_name']`, count streams, and sum duration.
* **Output Format:** Clean tabular ranking highlighting track name, artist, total plays, and listening hours.

### $\color{#38BDF8}\text{1.4 The Obsession Metric (24-Hour Stream Velocity)}$
* **Objective:** Detect single-song listening obsessions by identifying tracks played the most times within a single 24-hour window.
* **Input Columns:** `time_stamp`, `song_name`, `artist_name`.
* **Aggregation Method:** Truncate timestamp to calendar day (`dt.floor('D')`), group by `[date, song_name, artist_name]`, take `.size().nlargest(top_n)`.
* **Key Analytical Insight:** Pinpoints acute binge periods where a single track was looped 20–50+ times in a single day.

### $\color{#38BDF8}\text{1.5 Top N Albums All-Time and Periodically}$
* **Objective:** Rank full-length album projects by total stream counts across all constituent tracks.
* **Input Columns:** `album_name`, `artist_name`, `sec_played`.
* **Aggregation Method:** Group by `['album_name', 'artist_name']`, aggregate play count and hours.

### $\color{#38BDF8}\text{1.6 All-Time and Yearly Top N Genres (Linear Algebra Dot Product)}$
* **Objective:** Calculate play counts and total hours across all 340+ One-Hot Encoded genre columns simultaneously.
* **Input Columns:** 340+ binary genre indicator columns, `sec_played`.
* **Aggregation Method:** C-compiled matrix dot products:
  * Plays: $\mathbf{c} = G^T \cdot \mathbf{1}_N$
  * Hours: $\mathbf{h} = \frac{1}{3600} (G^T \cdot \mathbf{s})$
* **Performance:** Executes in **<0.05 seconds** with **0 MB** transient dataframe expansion.

---

## <a id="section-2-temporal-habits"></a>$\color{#F59E0B}{\text{Section 2: Temporal and Behavioral Habits (Time-Series)}}$

### $\color{#38BDF8}\text{2.1 Yearly and Monthly Listening Volume}$
* **Objective:** Measure long-term user retention, platform engagement trends, and lifetime streaming volume.
* **Input Columns:** `year`, `month`, `year_month_period`, `sec_played`.
* **Aggregation Method:** Group by calendar periods, computing total tracks streamed, total minutes, and total hours.
* **Output Format:** Sequential time-series table tracking growth from 2019 through 2026.

### $\color{#38BDF8}\text{2.2 Day-of-Week Listening Distribution}$
* **Objective:** Identify the user's weekly rhythm (e.g. Workday focus vs. Weekend relaxation).
* **Input Columns:** `day_of_week` (0=Monday to 6=Sunday), `day_name`, `sec_played`.
* **Aggregation Method:** Group by day index, calculating total streams, percentage share of weekly volume, and average hours per day.

### $\color{#38BDF8}\text{2.3 Hour-of-Day Listening Distribution (24-Hour Circadian Rhythm)}$
* **Objective:** Map the user's diurnal listening habits across 24 hourly buckets.
* **Input Columns:** `hour_of_day` (0 to 23), `sec_played`.
* **Aggregation Method:** Group by hour, computing play counts and total hours streamed.
* **Key Analytical Insight:** Identifies peak traffic spikes (e.g. 4:00 PM evening surge) and baseline sleep troughs (4:00 AM).

### $\color{#38BDF8}\text{2.4 The Silent Days Metric}$
* **Objective:** Detect complete platform disengagement by isolating calendar dates with 0 streamed songs.
* **Input Columns:** `time_stamp`.
* **Aggregation Method:** Generate a complete daily date range $\mathcal{D} = [D_{\min}, D_{\max}]$; compute set difference $\mathcal{D}_{\text{silent}} = \mathcal{D} \setminus \text{unique}(df['\text{date}'])$.
* **Output Format:** Summary count and listing of unbroken hiatus intervals.

### $\color{#38BDF8}\text{2.5 Longest Consecutive Daily Listening Streak}$
* **Objective:** Determine the user's longest continuous streak of consecutive calendar days streaming Spotify.
* **Input Columns:** `time_stamp`.
* **Aggregation Method:** Vectorized Gaps-and-Islands:
  $$\Delta = \text{diff}(\text{unique dates}) \quad \rightarrow \quad \text{island id} = \sum (\Delta \neq 1 \text{ day})$$
  Longest streak is computed as $\max(\text{size}(\text{island id}))$.

---

## <a id="section-3-skip-behavior"></a>$\color{#F59E0B}{\text{Section 3: Engagement and Skip Behavior}}$

### $\color{#38BDF8}\text{3.1 Artist Skip Rates (Impatience Index)}$
* **Objective:** Rank artists with significant stream volume ($\ge 20$ plays) by the percentage of tracks skipped before completion.
* **Input Columns:** `artist_name`, `reason_end`.
* **Skip Definition:** `is_skip = (reason_end == 'fwdbtn')`.
* **Aggregation Method:** Group by `artist_name`, filter `count >= 20`, compute $\frac{\sum \text{is skip}}{\text{count}}$, sort descending.

### $\color{#38BDF8}\text{3.2 Song Skip Rates (Repeat Skip Offenders)}$
* **Objective:** Isolate individual tracks ($\ge 10$ plays) that trigger immediate user rejection.
* **Input Columns:** `song_name`, `artist_name`, `reason_end`.
* **Aggregation Method:** Group by track, filter volume threshold, compute skip percentage.

### $\color{#38BDF8}\text{3.3 Time-of-Day and Day-of-Week Skip Volatility}$
* **Objective:** Determine whether user impatience correlates with fatigue, work hours, or weekend leisure.
* **Input Columns:** `hour_of_day`, `day_of_week`, `reason_end`.
* **Aggregation Method:** 2D pivot table cross-tabulating hourly and daily skip percentages.

### $\color{#38BDF8}\text{3.4 Shuffle Mode Dynamics}$
* **Objective:** Analyze whether the user relies on random algorithmic playback on weekends versus structured listening on weekdays.
* **Input Columns:** `shuffle`, `is_weekend`, `reason_end`.
* **Aggregation Method:** Group by weekend flag, calculating `% shuffle == True` and corresponding skip rates.

### $\color{#38BDF8}\text{3.5 Lifecycle Transition Matrix}$ (`reason_start` → `reason_end`)
* **Objective:** Trace the complete journey of a stream from start trigger to termination trigger.
* **Input Columns:** `reason_start` (`clickrow`, `trackdone`, `fwdbtn`, `playbtn`), `reason_end` (`trackdone`, `fwdbtn`, `endplay`, `unexpected-exit`).
* **Aggregation Method:** Cross-tabulation `pd.crosstab(master_df['reason_start'], master_df['reason_end'], normalize='index') * 100`.

---

## <a id="section-4-technical-geographic"></a>$\color{#F59E0B}{\text{Section 4: Technical and Geographic Metrics}}$

### $\color{#38BDF8}\text{4.1 Platform and Device Distribution}$
* **Objective:** Track the hardware ecosystem utilized to access Spotify over 7 years.
* **Input Columns:** `platform` (`Android`, `Windows`, `Linux/IoT`, `iOS`, `Mac`, `Other`).
* **Aggregation Method:** Value counts and listening hours per platform category.

### $\color{#38BDF8}\text{4.2 Platform Engagement and Skip Ratios}$
* **Objective:** Compare user behavior across mobile (Android) and desktop/workstation (Windows/Linux) environments.
* **Input Columns:** `platform`, `reason_end`, `sec_played`.
* **Aggregation Method:** Group by platform, computing average stream duration and skip percentage.

### $\color{#38BDF8}\text{4.3 Geographic Streaming Breakdown}$
* **Objective:** Map international listening volume across country codes.
* **Input Columns:** Standardized `country` column (with legacy `conn_country` fallback).
* **Aggregation Method:** Group by country code, calculating stream volume and percentage share.

### $\color{#38BDF8}\text{4.4 Offline Playback Utilization}$
* **Objective:** Quantify the percentage of listening conducted without active network connectivity.
* **Input Columns:** `offline` (boolean).
* **Aggregation Method:** Compute normalized distribution of `offline == True` streams.

---

## <a id="section-5-niche-metrics"></a>$\color{#F59E0B}{\text{Section 5: Niche and Advanced Behavioral Metrics}}$

### $\color{#38BDF8}\text{5.1 The Loyalty Metric (Unbroken Monthly Streaks)}$
* **Objective:** Identify artists listened to at least once *every single month* over extended consecutive month stretches.
* **Input Columns:** `artist_name`, `year_month_period`.
* **Aggregation Method:** Group unique `[artist, period]` pairs, compute month diffs, group by consecutive month islands, and extract maximum streak length per artist.

### $\color{#38BDF8}\text{5.2 The One-Hit Wonder Wall of Fame}$
* **Objective:** Detect artists with high aggregate play counts ($\ge 15$ streams) where the user listened to exactly ONE unique song across their entire discography.
* **Input Columns:** `artist_name`, `song_name`.
* **Aggregation Method:** Group by `artist_name`, filter `nunique(song_name) == 1` and `count >= 15`, sort descending by play count.

### $\color{#38BDF8}\text{5.3 True Attention Span Decay}$
* **Objective:** Measure the average seconds played before a skip occurs, filtered to standard song lengths ($\le 630$ seconds) to eliminate podcast distortion.
* **Input Columns:** `year`, `sec_played`, `reason_end`.
* **Aggregation Method:** Filter `reason_end == 'fwdbtn'` and `sec_played <= 630`; group by year, calculating $\frac{\sum \text{sec played}}{N}$.

### $\color{#38BDF8}\text{5.4 Session Binge Duration Distribution}$
* **Objective:** Segment continuous listening sessions separated by $\ge 30$ minutes of silence to analyze binge listening habits.
* **Input Columns:** `time_stamp`, `sec_played`.
* **Aggregation Method:** Session boundary detected where `time_stamp - shift(1) > 30 minutes`. Group by session ID, sum hours, and compute quantile distribution (p50, p75, p90, p99).
