# Project Changelog

This document tracks completed work, configuration changes, and system states across AI sessions to ensure perfect synchronization.

## [2026-09-19] Pre-Deployment Global Pathing Audit & Cache Purge
- **Audited:** Conducted a global pre-deployment scan for fragile path logic (e.g., `Path.cwd()`, `../` strings) across the entire workspace.
- **Refactored:** Scrubbed remaining legacy relative paths in research notebooks (`01_data_cleaning.ipynb`, `02_eda_visualizations.ipynb`, `03_ml_modeling.ipynb`) and injected dynamic `path_utils.py` logic into `app/pipeline/` Python scripts, guaranteeing absolute path safety regardless of execution environment.
- **Cleaned:** Purged root-level `.pytest_cache`, `__pycache__`, and `.cache` directories to enforce pristine workspace aesthetics. Kept critical system dotfiles (`.env`, `.git`, `.dvc`) strictly at the root.
- **Verified:** Ran the complete Pytest suite (`pytest -v`), confirming a flawless 20/20 pass rate (100%) with zero regressions. Project is certified 100% complete and ready for AWS cloud deployment.

## [2026-09-17] AWS Infrastructure Preparation
- **Added:** Installed AWS CLI v2 globally on the local Windows machine.
- **Added:** Configured AWS Agent Toolkit (installed 23 default ML/AWS skills).
- **Added:** Set up `spotify-ml` AWS CLI profile and authenticated via SSO.
- **Added:** Integrated `aws-mcp` server into global IDE configuration (`mcp_config.json`).
- **Added:** Appended official AWS Experience Rules to `.agents/AGENTS.md`.
- **Status:** AWS Account creation verified. EC2 `t3.micro` instance deployed in `ap-south-1`. Security groups configured, Docker installed, and FastAPI container successfully deployed via SCP.
- **Added:** Edge-case resilience configurations for production cloud deployment:
  - Docker log rotation (`max-size: 10m`) added to `docker-compose.yml` to prevent AWS hard drive exhaustion.
  - Upgraded terminal TUI dashboard to an immortal background `monitor` daemon via Docker Compose `restart: unless-stopped`.
  - Finalized SSH Port Forwarding strategy (`ssh -L 8000:localhost:8000`) for seamless, secure Spotify OAuth authentication without SSL certificates.

## [2026-09-18] Feature Engineering Fixes & Final Pipeline Sync
- **Fixed:** Critical data leakage vulnerability in Phase 3 Feature Engineering. Replaced the static `global_skip_rate` (which looked into the future) with an expanding window (`cumsum`/`cumcount`) to maintain strict zero-leakage chronology.
- **Optimized:** Resolved an $O(N^2)$ execution bottleneck in `notebooks/02_eda_visualizations.ipynb` caused by evaluating the new Pandas Series inside a row-by-row `zip` loop. Implemented dictionary caching, reducing runtime to 4 seconds.
- **Synced:** Formalized Attempt 11 as the Production Champion. Updated `pipeline/03_ml_modeling.py` to synchronize 1:1 with the Attempt 11 Optuna-tuned hyperparameters (`ROC-AUC 0.858`, `Recall 47.67%`).
- **Docs:** Finalized all markdown documentation (README, ROADMAP, AI_HANDOFF, ML_PROGRESS_LOG), restoring KaTeX colors and updating the experiment history tables.

- **Rolled Back:** Deleted Linux `wsl_venv` and reverted back to native Windows execution to eliminate the massive 9P file system WSL overhead, which was starving the GPU of data.
- **Completed:** ML Phase B (Focal Loss) and Phase C (Stacking/Soft Voting) were executed and formally documented as failed experiments due to Noisy Labels and Multicollinearity, respectively.
- **Locked In:** XGBoost Attempt 10 (Optuna-tuned on the fully leak-free engineered feature set) is formally locked in as the Production Champion for the pipeline. It achieved 0.858 ROC-AUC and 47.67% Safe Recall at 80% Precision, beating Attempt 8.
- **Completed:** Built a standalone Vanilla HTML/JS Live Web Dashboard (`fastapi/static/index.html`) served natively through FastAPI. Replicates the terminal state machine, continuously tracks session mood (CALM_FLOW, SKIP_SPREE), and displays real-time risk probabilities for the 10-track upcoming Spotify queue.
- **Redesign & Controls:** Upgraded the Web Dashboard to mimic the Spotify UI (pitch black background, gold text) and added a persistent bottom player bar. Built fast `spotipy` REST endpoints (`/player/play`, `/player/pause`, `/player/next`, `/player/volume`) allowing the dashboard to instantly control live Spotify playback and volume.
- **Simplification & Redesign:** Following caching bugs and permission issues with Spotify OAuth scopes (`user-modify-playback-state`), the UI and API were aggressively simplified. All player controls (buttons, volume, backend endpoints) were entirely ripped out and the Spotify OAuth scope was reverted to strictly read-only.
- **Queue Expansion:** Expanded the ML queue forecast lookahead limit from 10 to 20 tracks.
- **Now Playing Display:** Added a dynamic "Now Playing" UI component at the top of the dashboard containing a live progress bar and a local 3-minute skip tracking counter to analyze user flow state.
- **Refactored Dashboard:** Migrated the dashboard entirely away from external frameworks (like Streamlit) to prevent AWS storage exhaustion ("No space left on device"). The dashboard is now built as a pure native HTML/JS endpoint directly inside `fastapi/main.py` (`/dashboard`), serving live Shadow Audit metrics and the live queue.
- **Fixed Database Bug:** Resolved a critical bug where upcoming tracks were permanently locked as `PENDING` with stale probabilities. Updated `fastapi/audit_logger.py` to continuously `UPDATE` existing rows with fresh probabilities until the song actively plays and resolves.
- **Optimized Polling:** Reduced the `live_monitor.py` polling interval to 0.9 seconds for tighter real-time tracking of rapid skip sprees.

## [2026-09-19] Automated Pytest Test Suite Setup
- **Added:** Built production-grade automated Pytest test suite (`tests/`) containing 10 test cases.
- **Coverage:**
  - `conftest.py`: Shared session-scoped fixtures for XGBoost model loading, synthetic streaming datasets, and FastAPI `TestClient`.
  - `test_feature_engineering.py`: Zero-leakage expanding window verification, rolling micro-mood momentum, and cold-start fallback handling.
  - `test_inference.py`: XGBoost artifact structure validation, probability bound checks `[0.0, 1.0]`, and high-risk vs. low-risk predictions.
  - `test_api.py`: FastAPI REST API contract tests for `/health`, `/predict-skip`, and network-mocked `/predict/live-queue`.
- **Status:** All 10 unit tests executed and passed cleanly in 4.84 seconds (`pytest tests/ -v`).

## [2026-09-19] GitHub Actions CI/CD Pipeline Setup
- **Added:** Created `.github/workflows/ci.yml` configuring automated GitHub Actions build and test runner on `ubuntu-latest` with Python 3.11.
- **Workflow:** Runs `flake8` syntax checking, executes `pytest tests/ -v`, and verifies serialized XGBoost model binary integrity (`models/spotify_skip_predictor_xgb.pkl`).
- **Badge:** Integrated live CI build status badge into `README.md`.
- **Validation:** Executed local simulation run — 0 syntax errors, 10/10 pytest passed, model sanity check verified.

## [2026-09-19] MLflow Tracking & Spotify Rate-Limit Protection
- **Added:** Integrated MLflow experiment tracking into `pipeline/03_ml_modeling.py`.
- **Logged:** Parameter metrics (ROC-AUC 0.858 / 0.832, Precision 78-80%, Recall 48%), confusion matrix artifacts, and registered Champion model version 2 (`Spotify_Skip_Predictor_XGBoost`) into the MLflow Model Registry.
- **Fixed:** Spotify API rate-limiting (HTTP 429). Updated `fastapi/spotify_client.py` with an in-memory 0.9s TTL cache (`_LIVE_SPOTIFY_CACHE`) and zero retries timeout to serve dashboard requests cleanly without exceeding Spotify API rate limits.
- **Synced:** Downloaded remote SQLite audit log from EC2 container to `data/production_audit_remote.db` (24 audit records total, 19 resolved).

## [2026-09-19] Phase 5C: Automated Retraining Trigger & Challenger Evaluation
- **Added:** Built `pipeline/04_retrain_trigger.py` monitoring `data/production_audit.db` for resolved feedback with a threshold of **100 songs** (supports `--force` flag).
- **Added:** Built `pipeline/05_challenger_evaluation.py` training candidate models on feedback data, evaluating ROC-AUC/Precision against registered MLflow Champion, and promoting to `Production` stage only if ROC-AUC improves by >= 0.002.
- **Added:** Created automated test suite `tests/test_retrain_challenger.py` verifying trigger counts, thresholding, and MLflow promotion guardrails (14/14 unit tests passed in 5.78s).

## [2026-09-19] Phase 5D: Data & Model Versioning with DVC
- **Added:** Installed DVC v3.67.1 and initialized `.dvc/` version control repository.
- **Added:** Tracked dataset binary (`data/processed/Engineered_Spotify_Portable.db.dvc`) and model artifact (`models/spotify_skip_predictor_xgb.pkl.dvc`) with cryptographic md5 hash pointers.
- **Added:** Configured local DVC remote storage (`C:\Users\lenovo\.dvc_storage\spotify_ml_remote`) and pushed initial data cache (`dvc push`).
- **Added:** Created `tests/test_dvc_tracking.py` verifying `.dvc` tracking files exist and point to valid targets (17/17 total unit tests passed in 4.62s).

## [2026-09-19] Repository Reorganization & Architectural Consolidation
- **Reorganized:** Consolidated top-level codebase into `app/` containing `app/api/`, `app/pipeline/`, `app/notebooks/`, and `app/tests/`.
- **Reorganized:** Consolidated all documentation and generated reports under `docs/` (`docs/ab_testing/`, `docs/reports/`, `docs/reports/images/`, `docs/eda/`, `docs/ml/`).
- **Preserved:** Preserved learning materials directory (`tutorials/`).
- **Updated:** Updated all relative imports, `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`, and Pytest path fixtures to maintain 100% test compatibility (20/20 unit tests passed in 5.40s).

## [2026-09-19] Repository Subfolder & Documentation Cleanliness Standard
- **Consolidated:** Cleaned up all loose files in `data/` by relocating `data/last_fm.md` to `docs/setup/LAST_FM_METADATA.md`, ensuring `data/` contains strictly subfolders (`data/raw/`, `data/processed/`, `data/audit/`).
- **Standardized:** Renamed documentation files for uniform proper naming across all `docs/` subfolders (`SETUP.md`, `SETUP_TROUBLESHOOTING.md`, `ANTIGRAVITY_RULES.md`).
- **Preserved:** Retained root ecosystem configuration files (`.gitignore`, `.env`, `.github/`, `.dvc/`, `.dvcignore`) at workspace root to maintain seamless Git tracking, GitHub Actions CI/CD, DVC data commands, and environment variable loading.
- **Verified:** Ran Pytest suite (`pytest app/tests/ -v`) confirming 20/20 unit tests pass cleanly in 5.35s.

## [2026-09-19] Robust Dynamic Path Resolution Architecture
- **Created:** Created [`app/path_utils.py`](file:///c:/Users/lenovo/Desktop/03_DSA_&_Machine_Learning/ML_Roadmap/app/path_utils.py) providing `find_project_root()` and `resolve_path()` to dynamically locate the workspace root and candidate resource paths by searching upwards for root marker files (`pytest.ini`, `.git`, `Dockerfile`, `README.md`).
- **Refactored:** Refactored all REST API modules (`main.py`, `spotify_client.py`, `audit_logger.py`), pipeline stage scripts (`01_data_cleaning.py`, `02_eda_visualizations.py`, `03_ml_modeling.py`, `04_retrain_trigger.py`, `05_challenger_evaluation.py`, `06_ab_testing_simulation.py`), and Pytest test fixtures (`conftest.py`, `test_dvc_tracking.py`, `test_ab_simulation.py`) to eliminate fixed directory depth assumptions (e.g. `.parent.parent.parent`).
- **Notebooks Updated:** Programmatically parsed and updated code cells across all research notebooks ([`app/notebooks/01_data_cleaning.ipynb`](file:///c:/Users/lenovo/Desktop/03_DSA_&_Machine_Learning/ML_Roadmap/app/notebooks/01_data_cleaning.ipynb), [`app/notebooks/02_eda_visualizations.ipynb`](file:///c:/Users/lenovo/Desktop/03_DSA_&_Machine_Learning/ML_Roadmap/app/notebooks/02_eda_visualizations.ipynb), [`app/notebooks/03_ml_modeling.ipynb`](file:///c:/Users/lenovo/Desktop/03_DSA_&_Machine_Learning/ML_Roadmap/app/notebooks/03_ml_modeling.ipynb)) with dynamic upward root searching (`pytest.ini` / `.git` / `README.md` markers).
- **Verified:** Executed Pytest suite — 20/20 unit tests passed cleanly in 5.77s.
