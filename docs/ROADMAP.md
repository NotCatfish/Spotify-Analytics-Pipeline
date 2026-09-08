# Zero to Mercari Data Analyst: The Roadmap and Production Pipeline

This roadmap is strictly optimized for the Data Analyst Intern recruitment cycle.
Inside each section, the tasks are ordered from **Highest Priority (Do not fail)** down to **Lowest Priority (Bonus Points)**.

---

## $\color{#F59E0B}{\text{Production CLI Pipeline}}$ (`pipeline/`)
We have converted the exploratory Jupyter Notebooks into a professional, production-ready Command Line Interface (CLI) pipeline that matches the research notebooks 1:1.

**Usage Instructions:**
1. **$\color{#38BDF8}\text{Data Cleaning:}$** Process raw JSON streams into SQLite/PostgreSQL with Last.fm enrichment and datatype compression:
   ```bash
   python pipeline/01_data_cleaning.py
   ```
2. **$\color{#38BDF8}\text{EDA and Visualizations:}$** Generate statistical tables, 21 Japanese Winter Night figures into `reports/EDA_Report.md`, and export the ML feature store:
   ```bash
   python pipeline/02_eda_visualizations.py
   ```
3. **$\color{#38BDF8}\text{Machine Learning:}$** Train balanced Random Forest and cost-sensitive XGBoost with threshold calibration, saving the model artifact:
   ```bash
   python pipeline/03_ml_modeling.py
   ```

---

## $\color{#F59E0B}{\text{THEORY (Product Sense and Metrics)}}$
**Goal:** Understand how a tech company measures success. This is critical for behavioral and case-study interviews.

- [ ] **$\color{#38BDF8}\text{[Priority 1: Instant Fail] Core Product Metrics:}$** Understand DAU/MAU (Daily/Monthly Active Users), Retention Rate, Churn Rate, and ARPU (Average Revenue Per User).
- [ ] **$\color{#38BDF8}\text{[Priority 1: A/B Testing Statistics]}$** Learn how to explain P-values, Statistical Significance, and Confidence Intervals to a non-technical product manager.
- [ ] **$\color{#38BDF8}\text{[Priority 2: The E-commerce Funnel]}$** Understand the user journey: Acquisition → Activation → Retention → Referral → Revenue (AARRR). How does a user go from opening Mercari to buying an item?
- [ ] **$\color{#38BDF8}\text{[Priority 3: Read Engineering Blogs]}$** Read the *Mercari Engineering Blog* (specifically their Data Analytics and BI posts) to understand their specific KPIs.

---

## $\color{#F59E0B}{\text{PRACTICAL (The 9-Day SQL Grind)}}$
**Goal:** Build raw muscle memory for the Online Assessment (OA). The OA will be heavily SQL-based.

- [ ] **$\color{#38BDF8}\text{[Priority 1: The Resume Filter] LeetCode SQL (Mediums and Hards):}$** Do 3-5 SQL problems a day from LeetCode.
- [ ] **$\color{#38BDF8}\text{[Priority 1: Window Function Mastery]}$** You MUST master `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LEAD()`, and `LAG()`. Mercari will test your ability to track user events over time.
- [ ] **$\color{#38BDF8}\text{[Priority 1: CTEs (Common Table Expressions)]}$** Master using `WITH` clauses to break down complex queries instead of writing messy subqueries.
- [ ] **$\color{#38BDF8}\text{[Priority 2: Data Cleaning in SQL]}$** Practice handling `NULL` values (`COALESCE`), casting data types, and extracting dates/times from timestamps (`EXTRACT(MONTH FROM date)`).
- [ ] **$\color{#38BDF8}\text{[Priority 3: Python Pandas Refresher]}$** While the OA is usually SQL, ensure you can still write clean `.groupby()` and `.merge()` logic in Pandas just in case.

---

## $\color{#F59E0B}{\text{The Vibecoding Compromise}}$
- [ ] You don't have to abandon AI entirely, but for this 9-day sprint: **you must be able to write the LeetCode SQL queries completely from memory on a blank screen.** In a proctored OA, the AI cannot save you.
