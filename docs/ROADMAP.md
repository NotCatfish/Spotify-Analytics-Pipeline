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

### Phase 6: Cloud Deployment & Monitoring [UPCOMING]
- [ ] Deploy Docker container to AWS EC2 (`t3.micro`) using Docker Compose.
- [ ] Configure reverse proxy (Nginx) and SSL/TLS termination.
- [ ] Set up continuous Prometheus & Grafana telemetry for live latency and prediction drift.
- [ ] Automated S3 remote storage sync for DVC data/model artifacts.
