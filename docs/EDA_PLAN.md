# Spotify EDA Master Blueprint

> [!NOTE]
> **Status (August 2026):** Phase 1 (Top Charts & Temporal Habits) is mostly complete. The immediate project focus has shifted to **MLOps Deployment (FastAPI)** for the ML model. The remaining niche EDA metrics will be revisited if time permits before internship applications.

Here is the master blueprint for your Spotify Exploratory Data Analysis (EDA). Use this as a checklist for your Jupyter Notebook or Power BI dashboards.

### 🏆 1. The "Top Charts" (Basic Rankings)

* **Top N Artists**
  * All-Time
  * By Year (How your favorite artist changed over time)
  * By Month
  * By Season (Do you listen to different artists in Winter vs. Summer?)
* **Top N Songs**
  * All-Time
  * By Year
  * By Month
  * *The "Obsession" Metric:* Songs you listened to the most times in a single 24-hour period.
* **Top N Albums**
  * All-Time
  * By Year
  * By Month
  * By Day
* **Top N Genres** *(Powered by the 300+ OHE columns)*
  * All-Time Most Listened Genres
  * *Genre Evolution:* How your taste in genres shifted from 2019 to 2024.

### 🕒 2. Temporal & Behavioral Habits (Time-Series)

* **Total Listening Volume (in Hours/Minutes)**
  * Total Hours Listened per Year
  * Total Hours Listened per Month
* **Daily & Hourly Habits**
  * *Day of the Week:* Which day you listen the most (e.g., Friday vs. Monday)
  * *Hour of the Day:* Are you a morning listener or a late-night listener?
  * *The "Silent" Days:* Days where you listened to 0 hours of music.
* **Streaks**
  * Your longest consecutive streak of days listening to Spotify without a break.

### ⏭️ 3. Engagement & Skip Behavior

* **Skip Rates**
  * *Most Skipped Artists:* Artists you skip the most often.
  * *Most Skipped Songs:* Songs that always get skipped.
  * *Time of Day Skip Rate:* Are you more impatient (higher skip rate) in the mornings or at night?
* **Shuffle Behavior**
  * Do you use `shuffle` more often on Weekends or Weekdays?
  * Do certain Genres trigger you to turn `shuffle` on?
* **Action Behaviors**
  * *Reason Start:* How often do you actively click a song (`playbtn`) vs. letting the algorithm choose for you (`trackdone`)?

### 💻 4. Technical & Geographic Metrics

* **Platform Usage**
  * Which devices do you use the most? (e.g., Android vs. Windows PC)
  * Do you listen to different *genres* on your phone vs. your computer?
* **Geographic Tracking**
  * Where in the world were you when listening? (Using `conn_country`)
* **Offline Mode**
  * How often do you listen with no internet (`offline` == True)?

### 🕵️ 5. Niche & Advanced Metrics (The Fun Stuff)

* **The "Loyalty" Metric:** Which artists have you listened to at least once *every single month* for the past 5 years?
* **The "One-Hit Wonder" Metric:** Artists where you have listened to exactly ONE of their songs, and completely ignored the rest of their discography.
* **The "Attention Span" Metric:** Average seconds played before a skip occurs. Are your skips instant (under 5 seconds), or do you listen half-way through before skipping?
