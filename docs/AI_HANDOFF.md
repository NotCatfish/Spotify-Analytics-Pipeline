# AI Session Context Snapshot & Handoff

## 1. Repository Identity & Core Purpose
- **Repository:** `Spotify-Analytics-Pipeline` (Owned by `@NotCatfish` / Indraneel Samanta).
- **Core Domain:** End-to-end data engineering, automated EDA reporting, and low-latency skip prediction for Spotify streaming logs.
- **Key Metric Guardrail:** Precision >= 80% (Business SLA threshold: 0.749, ROC-AUC: 0.858, F1: 0.60).
- **Dual Policy Dispatched:** High skip probabilities trigger CDN prefetch throttling (`JIT_3SEC_CHUNKING`) and recommendation queue purges (`SILENT_AUTOPLAY_PURGE`).

---

## 2. Directory Architecture & Modular Structure
```
Spotify-Analytics-Pipeline/
├── .github/workflows/
│   ├── ci.yml                           # CI runner (flake8 + pytest)
│   ├── spotify_sync.yml                 # 24/7 Cloud Listening Sync & Model Audit (cron / dispatch)
│   └── model_retrain.yml                # Daily automated 00:00 UTC model retraining with 37m retry
├── app/
│   ├── api/                             # FastAPI microservice & static dashboard UI
│   │   ├── main.py                      # Serving app with degraded-mode boot resilience
│   │   ├── schemas.py                   # Pydantic v2 schemas
│   │   ├── spotify_client.py            # Spotipy OAuth + Last.fm live tagger (with recently-played scope)
│   │   └── static/dashboard.html        # Dark-mode dashboard (900ms auto-refresh)
│   ├── notebooks/                       # Scrubbed research notebooks (01, 02, 03 - 0 outputs/vars)
│   ├── pipeline/                        # Production CLI engines (01 through 08)
│   │   ├── 07_cloud_listening_sync.py   # Headless cron sync & zero-leakage session replay
│   │   ├── 08_daily_model_retrain.py    # Autonomous daily retraining engine & flag checker
│   │   └── get_refresh_token.py         # Local one-time OAuth token helper
│   ├── tests/                           # 24 automated Pytest test cases across 7 suites
│   │   ├── test_cloud_sync.py           # Session momentum, replay, and idempotency tests
│   │   └── ...
│   └── path_utils.py                    # Robust dynamic project root discovery
├── data/
│   ├── raw/                             # Raw Spotify JSONs (ignored)
│   ├── processed/                       # Feature store (modern_historical_baseline.parquet + SQLite via .dvc)
│   └── audit/                           # shadow_audit.jsonl, production_audit.db, retrain_status.json
├── docs/                                # Architectural, EDA, ML & handoff documentation
└── models/                              # Serialized XGBoost models (tracked in Git & .dvc)
```

---

## 3. Cloud Architecture & AWS Decommissioning Decision
- **Previous Architecture (Decommissioned):**
  - Docker container hosted on AWS EC2 (`t3.micro`) with SSH port-forwarding and manual keypair management (`.pem`).
  - **Why Stopped:** AWS introduced constant friction: recurring account suspension risks, credential expirations (12-hour SSO sessions), credit card billing exposure, and unnecessary 24/7 idle server compute overhead.
- **Current Architecture (GitHub Actions Serverless Cron):**
  - **Zero Cost & Zero Maintenance:** 100% free runner tier on public GitHub repositories with zero server maintenance.
  - **Execution Engine:** `.github/workflows/spotify_sync.yml` triggers twice every hour (`14,47 * * * *`) via off-peak POSIX cron + manual `workflow_dispatch`.
  - **Autonomous Daily Retraining:** `.github/workflows/model_retrain.yml` triggers daily at 00:00 UTC with automated 37-minute retries (`0,37 * * * *`) backed by persistent state flag `data/audit/retrain_status.json`.
  - **Causal Session Replay:** `app/pipeline/07_cloud_listening_sync.py` pulls recently played tracks, calculates past session momentum strictly before prediction time, resolves actual skip outcomes via elapsed playback time (`elapsed = t[i] - t[i-1] < duration - 10s`), and logs predictions.
  - **Stateless Deduplication:** Since cloud runners are ephemeral and do not retain SQLite state, the runner deduplicates incoming tracks against `data/audit/shadow_audit.jsonl` in-memory.
  - **Git-Native Storage:** Results and updated model binaries are auto-committed by `github-actions[bot]` with `[skip ci]` directly into Git, creating a verifiable public audit trail.

---

## 4. Critical Technical Rules & Gotchas
1. **Dynamic Pathing:** NEVER use hardcoded or brittle relative paths. Always use `from path_utils import resolve_path, find_project_root`.
2. **Model Binary Tracking:**
   - `models/spotify_skip_predictor_xgb.pkl` is directly tracked in Git to allow cloud runners to execute full XGBoost inferences and updates without external DVC pull overhead.
   - Large raw datasets remain tracked via `.dvc`, while modern training baseline (`modern_historical_baseline.parquet`, 4.04 MB) is tracked in Git.
3. **CI/CD Resilience & Cloud Sync:**
   - Cloud sync and retrain runners commit with `[skip ci]` to prevent recurring CI trigger loops.
   - GitHub Encrypted Secrets configure `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REFRESH_TOKEN`.
4. **Git Pre-Commit Gate:**
   - Local `.git/hooks/pre-commit` enforces that all 24 Pytest tests pass before any commit can succeed.
5. **PII and Data Leaks:**
   - Sensitive credentials (`.env`, `SPOTIPY_REFRESH_TOKEN`, `.spotify_cache`) must NEVER be committed to Git.
   - Notebooks must be committed scrubbed of all execution outputs and stored data variables.

---

## 5. Current Work State & Immediate Next Steps
- **State:** Fixed Spotify `played_at` timestamp resolution bug in `app/pipeline/07_cloud_listening_sync.py` by switching from forward-looking delta to strictly backward-looking delta (`t[i] - t[i-1]`). Re-graded all 573 audit records (12 true skips, 561 non-skips). All 24 automated unit tests pass.
- **Active Phase:** Phase 8 (Drift Alerting & Production Serving Hardening).
- **Next Planned Milestone:** Implement automated webhook/issue alerting if weekly skip precision slips below the 78% business guardrail; benchmark FastAPI `/predict_skip` latency under high-concurrency batch loads.



