# Changelog: Spotify Analytics & Machine Learning Pipeline

All notable changes to this project are documented in this file.

---

## [1.3.0] - 2026-09-24: 24/7 Cloud Listening Sync & Automated Shadow Audit

### Added
- **Headless Cloud Listening Sync Engine (`app/pipeline/07_cloud_listening_sync.py`):** Automatically polls Spotify's Recently Played API, replays listening sessions in strict causal sequence with zero lookahead bias, executes XGBoost skip inference, and logs real-world ground truth outcomes.
- **Dual Audit Logging:** Persists evaluations both to the local SQLite database (`data/audit/production_audit.db`) and a lightweight, Git-tracked append-only log (`data/audit/shadow_audit.jsonl`).
- **Automated GitHub Actions Cron Workflow (`.github/workflows/spotify_sync.yml`):** Runs every 5 minutes in test mode (with `workflow_dispatch` manual trigger), safely injecting encrypted secrets (`SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIPY_REFRESH_TOKEN`), and auto-committing new listening records back to the repo with `[skip ci]`.
- **One-Time Token Generator (`app/pipeline/get_refresh_token.py`):** Interactive local OAuth helper to grant `user-read-recently-played` scope and retrieve a permanent headless refresh token.
- **Sync Test Suite (`app/tests/test_cloud_sync.py`):** 4 automated Pytest tests validating session replay momentum, zero-leakage skip resolution, database migration, and credential error handling (bringing total test coverage to 24 passing suites).

### Changed
- **Spotify Scope Expansion (`app/api/spotify_client.py`):** Expanded OAuth scopes to include `user-read-recently-played`.
- **Git Tracking Rules (`.gitignore`):** Whitelisted `!data/audit/shadow_audit.jsonl` while maintaining complete privacy for `.env`, credentials, and raw binaries.

---

## [1.2.0] - 2026-09-19: Production Hardening, DVC Integration & CI/CD Pipeline

### Added
- **GitHub Actions CI/CD Pipeline (`.github/workflows/ci.yml`):** Automated linting (`flake8`) and test execution (`pytest`) on all pushes and PRs to `main`.
- **Git Pre-Commit Hook (`.git/hooks/pre-commit`):** Mandates that all 20 automated tests pass locally before code can be committed.
- **DVC Data & Model Tracking:** Tracked heavy SQLite feature database (`Engineered_Spotify_Portable.db.dvc`) and serialized XGBoost model (`spotify_skip_predictor_xgb.pkl.dvc`) via lightweight Git pointer hashes.
- **CI DVC Skip Fixtures:** Introduced `@requires_model` marker in `app/tests/test_api.py` and `pytest.skip()` in `app/tests/test_ab_simulation.py` and `app/tests/conftest.py` so GitHub Actions test runners gracefully pass without requiring heavy binary downloads.
- **Degraded Mode FastAPI Boot:** Updated `app/api/main.py` lifespan to boot safely in degraded mode if models are missing, preventing crash loops in test/CI environments.
- **Automated Project Documentation:** Initialized `docs/ROADMAP.md`, `docs/CHANGELOG.md`, and `docs/AI_HANDOFF.md`.

### Changed
- **Unified Directory Restructuring:** Moved fragmented root folders into clean, decoupled subpackages inside `app/`: `app/api/`, `app/pipeline/`, `app/notebooks/`, and `app/tests/`.
- **Path Resolution Modernization:** Replaced brittle relative and hardcoded paths across all scripts and notebooks with dynamic project root discovery via `app/path_utils.py`.
- **Root README.md Overhaul:** Refactored documentation with updated architectural diagrams, comprehensive test coverage breakdown, Docker instructions, and accurate file paths.

### Fixed
- Fixed `.gitignore` rules to unignore `*.dvc` tracking files within `data/` and `models/`.
- Sanitized and cleared all execution outputs across Jupyter research notebooks (`01_data_cleaning.ipynb`, `02_eda_visualizations.ipynb`, `03_ml_modeling.ipynb`) to guarantee zero PII data leaks.

---

## [1.1.0] - 2026-09-18: Real-Time Microservice & Web Dashboard

### Added
- **FastAPI Real-Time Service (`app/api/main.py`):** Real-time skip prediction endpoints (`/predict-skip`, `/predict/live-queue`, `/health`).
- **Interactive Dark-Mode Dashboard (`app/api/static/dashboard.html`):** Real-time web UI showing current track, queue risk forecasts, and live confusion matrix metrics.
- **Spotipy & Last.fm Client (`app/api/spotify_client.py`):** OAuth2 authentication and automated live genre tag enrichment.
- **Shadow Mode Audit Logger (`data/audit/production_audit.db`):** Passive ground-truth evaluation logging user listening decisions against model predictions.
- **Retraining Daemon & Challenger Evaluation (`app/pipeline/04_retrain_trigger.py`, `05_challenger_evaluation.py`):** Automatic retraining upon reaching audit threshold.
- **A/B Testing Simulator (`app/pipeline/06_ab_testing_simulation.py`):** Financial utility modeling for CDN bandwidth savings vs. user friction penalties.

---

## [1.0.0] - 2026-09-17: Core Ingestion, Feature Store & Model Optimization

### Added
- **Data Cleaning Engine (`app/pipeline/01_data_cleaning.py`):** JSON ingestion, timestamp normalization, PII stripping, and SQL downcasting.
- **Automated EDA Engine (`app/pipeline/02_eda_visualizations.py`):** 21 Japanese Winter Night figures, executive markdown dossier (`docs/reports/EDA_Report.md`), and smoothed target encoding feature store.
- **Machine Learning Engine (`app/pipeline/03_ml_modeling.py`):** Strict chronological walk-forward split, 19-feature matrix, and Optuna Bayesian optimization on NVIDIA RTX 3060 with 80% Precision SLA constraint.
