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
│   ├── ci.yml                      # CI runner (flake8 + pytest)
│   └── spotify_sync.yml            # 24/7 Cloud Listening Sync & Model Audit (cron / dispatch)
├── app/
│   ├── api/                        # FastAPI microservice & static dashboard UI
│   │   ├── main.py                 # Serving app with degraded-mode boot resilience
│   │   ├── schemas.py              # Pydantic v2 schemas
│   │   ├── spotify_client.py       # Spotipy OAuth + Last.fm live tagger (with recently-played scope)
│   │   └── static/dashboard.html   # Dark-mode dashboard (900ms auto-refresh)
│   ├── notebooks/                  # Scrubbed research notebooks (01, 02, 03)
│   ├── pipeline/                   # Production CLI engines (01 through 07)
│   │   ├── 07_cloud_listening_sync.py # Headless cron sync & zero-leakage session replay
│   │   └── get_refresh_token.py    # Local one-time OAuth token helper
│   ├── tests/                      # 24 automated Pytest test cases across 7 suites
│   │   ├── test_cloud_sync.py      # Session momentum, replay, and idempotency tests
│   │   └── ...
│   └── path_utils.py               # Robust dynamic project root discovery
├── data/
│   ├── raw/                        # Raw Spotify JSONs (ignored)
│   ├── processed/                  # Feature Store SQLite DB (tracked via .dvc)
│   └── audit/                      # Shadow Mode SQLite audit database & shadow_audit.jsonl
├── docs/                           # Architectural, EDA, ML & handoff documentation
└── models/                         # Serialized XGBoost models (tracked via .dvc)
```

---

## 3. Cloud Architecture & AWS Decommissioning Decision
- **Previous Architecture (Decommissioned):**
  - Docker container hosted on AWS EC2 (`t3.micro`) with SSH port-forwarding and manual keypair management (`.pem`).
  - **Why Stopped:** AWS introduced constant friction: recurring account suspension risks, credential expirations (12-hour SSO sessions), credit card billing exposure, and unnecessary 24/7 idle server compute overhead.
- **Current Architecture (GitHub Actions Serverless Cron):**
  - **Zero Cost & Zero Maintenance:** 100% free runner tier on public GitHub repositories with zero server maintenance.
  - **Execution Engine:** `.github/workflows/spotify_sync.yml` triggers twice every hour (`14,47 * * * *`) via off-peak POSIX cron + manual `workflow_dispatch`.
  - **Causal Session Replay:** `app/pipeline/07_cloud_listening_sync.py` pulls recently played tracks, calculates past session momentum strictly before prediction time, resolves actual skip outcomes via subsequent track timestamps (`duration - 10s`), and logs predictions.
  - **Stateless Deduplication:** Since cloud runners are ephemeral and do not retain SQLite state, the runner deduplicates incoming tracks against `data/audit/shadow_audit.jsonl` in-memory.
  - **Git-Native Storage:** Results are auto-committed by `github-actions[bot]` with `[skip ci]` directly into Git, creating a verifiable public audit trail.

---

## 4. Critical Technical Rules & Gotchas
1. **Dynamic Pathing:** NEVER use hardcoded or brittle relative paths. Always use `from path_utils import resolve_path, find_project_root`.
2. **Model Binary Tracking:**
   - `models/spotify_skip_predictor_xgb.pkl` (1.19 MB) is directly tracked in Git to allow cloud runners to execute full XGBoost inferences without external DVC pull overhead.
   - Large raw datasets remain tracked via `.dvc`.
3. **CI/CD Resilience & Cloud Sync:**
   - Cloud sync commits `data/audit/shadow_audit.jsonl` using `[skip ci]` to prevent recurring CI trigger loops.
   - GitHub Encrypted Secrets configure `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REFRESH_TOKEN`.
4. **Git Pre-Commit Gate:**
   - Local `.git/hooks/pre-commit` enforces that all 24 Pytest tests pass before any commit can succeed.
5. **PII and Data Leaks:**
   - Sensitive credentials (`.env`, `SPOTIPY_REFRESH_TOKEN`, `.spotify_cache`) must NEVER be committed to Git.

---

## 5. Current Work State & Immediate Next Steps
- **State:** 24/7 cloud sync pipeline is in active production on GitHub Actions running on an off-peak twice-hourly cron schedule (`14,47 * * * *`) with `--hours 0`. Real-world streaming logs are automatically evaluated with XGBoost and committed to `data/audit/shadow_audit.jsonl` with zero data leakage.
- **Active Task:** Continuous 24/7 passive shadow evaluation running in the background.
- **Next Planned Milestone:** Monitor shadow audit accuracy across the next 100-200 tracks; evaluate when to trigger challenger model retraining via `app/pipeline/04_retrain_trigger.py`.


