# Project Roadmap: Spotify Analytics & Machine Learning Pipeline

## Vision & Objectives
Deliver an autonomous, low-latency, privacy-first audio streaming analytics microservice capable of predicting user skip behavior in real-time, optimizing CDN bandwidth usage, and improving playlist recommendation flow.

---

## Phase Milestones

### Phase 1: Ingestion, Sanitization & High-Throughput Storage [COMPLETED]
- [x] Ingest multi-year Spotify Extended Streaming History (JSON).
- [x] Implement robust PII sanitization (strip IP addresses, hardware identifiers).
- [x] Memory optimization via SQL integer/float downcasting (85% RAM reduction).
- [x] High-speed PostgreSQL `COPY FROM STDIN` and SQLite pragma acceleration.

### Phase 2: Autonomous EDA & Feature Store Engineering [COMPLETED]
- [x] Accelerated linear algebra dot-product genre profiling (>300x faster than `.groupby()`).
- [x] 21 high-resolution Japanese Winter Night theme visualizations.
- [x] Automated headless markdown report generation (`docs/reports/EDA_Report.md`).
- [x] Smoothed historical skip-rate target encodings (artist, track, genre, album).

### Phase 3: Machine Learning & Precision SLA Calibration [COMPLETED]
- [x] Eliminate lookahead bias via strict chronological walk-forward split (2023–2024 train, 2025+ test).
- [x] Defeat concept drift with acute micro-mood momentum features (`skips_last_3m`, `consecutive_listens_streak`).
- [x] GPU-accelerated Optuna Bayesian hyperparameter search (RTX 3060).
- [x] Enforce an 80% Precision SLA guardrail (Champion threshold: 0.749, ROC-AUC: 0.858, F1: 0.60).
- [x] MLflow experiment logging and model artifact serialization.

### Phase 4: Production Microservice, Live UI & MLOps [COMPLETED]
- [x] Production FastAPI service (`app/api/main.py`) with dynamic in-memory feature store (<0.2s startup).
- [x] Live Spotify queue prediction via Spotipy OAuth and Last.fm genre tagging.
- [x] Dual-policy action dispatching (CDN pre-fetch throttling + recommender track purging).
- [x] Dark-mode real-time monitoring dashboard (`/dashboard`) with 900ms auto-refresh.
- [x] Continuous shadow mode audit logger (`data/audit/production_audit.db`).
- [x] Retraining trigger daemon (`04_retrain_trigger.py`) & challenger evaluation (`05_challenger_evaluation.py`).
- [x] Financial utility A/B simulation engine (`06_ab_testing_simulation.py`).

### Phase 5: Production Hardening, Quality Gates & CI/CD [COMPLETED]
- [x] Consolidated and decoupled directory structure (`app/` package containing `api/`, `pipeline/`, `notebooks/`, `tests/`).
- [x] Dynamic project root discovery (`app/path_utils.py`) eliminating hardcoded absolute paths.
- [x] Comprehensive 20-test Pytest suite across API, inference, feature engineering, DVC, retraining, and A/B testing.
- [x] Local Git pre-commit hook enforcing 20/20 test passing.
- [x] GitHub Actions CI workflow with automated flake8 linting and DVC-resilient test execution.
- [x] Data Version Control (DVC) tracking for database and model binaries.
- [x] Complete notebook sanitization (0 PII/output leaks in version control).

### Phase 6: 24/7 Cloud Listening Sync & Autonomous Model Audit [COMPLETED]
- [x] Decommissioned AWS EC2 infrastructure to eliminate billing risk, credential expiration overhead, and account suspension friction.
- [x] Architected headless 24/7 Spotify listening synchronization via GitHub Actions off-peak cron runner (`14,47 * * * *`).
- [x] Zero-leakage causal session replay reconstructing historical micro-mood momentum (`skips_last_3m`, `consecutive_listens_streak`).
- [x] Dual audit logging to local SQLite (`data/audit/production_audit.db`) and Git-tracked JSON Lines (`data/audit/shadow_audit.jsonl`).
- [x] In-memory hash set deduplication against JSON Lines ensuring idempotent stateless cloud runner execution.
- [x] Automated Git push back to repository using `[skip ci]` to prevent recursive CI triggering.
- [x] Added 4 automated unit tests (`app/tests/test_cloud_sync.py`), expanding total suite to 24 passing tests.


### Phase 7: Real-World Concept Drift Monitoring & Retraining [ACTIVE]
- [ ] Accumulate 100+ real-world tracks in `data/audit/shadow_audit.jsonl`.
- [ ] Evaluate live precision and recall against the 80% Precision SLA baseline.
- [ ] Trigger automated challenger retraining via `app/pipeline/04_retrain_trigger.py` and promote candidate model upon confirmed accuracy gain.

