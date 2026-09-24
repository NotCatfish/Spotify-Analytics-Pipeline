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

## 3. Critical Technical Rules & Gotchas
1. **Dynamic Pathing:** NEVER use hardcoded or brittle relative paths. Always use `from path_utils import resolve_path, find_project_root`.
2. **DVC Binary Management:**
   - Raw `.db`, `.pkl`, and `.csv` files are ignored by Git.
   - `.dvc` tracking files (`Engineered_Spotify_Portable.db.dvc`, `spotify_skip_predictor_xgb.pkl.dvc`) MUST be tracked by Git.
   - `.gitignore` contains explicit exclusions (`!data/**/*.dvc`, `!models/**/*.dvc`) to allow tracking.
3. **CI/CD Resilience & Cloud Sync:**
   - GitHub Actions runners do not pull multi-megabyte DVC binaries.
   - Both `main.py` and `07_cloud_listening_sync.py` support degraded telemetry mode when model or feature store binaries are absent.
   - Cloud sync commits `data/audit/shadow_audit.jsonl` using `[skip ci]` to prevent recurring CI trigger loops.
4. **Git Pre-Commit Gate:**
   - Local `.git/hooks/pre-commit` enforces that all 24 Pytest tests pass before any commit can succeed.
5. **PII and Data Leaks:**
   - Sensitive credentials (`.env`, `SPOTIPY_REFRESH_TOKEN`, `.spotify_cache`) must NEVER be committed to Git. Injected via GitHub Encrypted Secrets in CI/CD.

---

## 4. Current Work State & Immediate Next Steps
- **State:** 24/7 cloud sync pipeline implemented and tested (24/24 tests passing). Zero-leakage chronological replay verified.
- **Active Task:** User testing 5-minute cron sync on GitHub Actions using `SPOTIPY_REFRESH_TOKEN`.
- **Next Planned Milestone:** Run one-time token generator (`python app/pipeline/get_refresh_token.py`), set GitHub Secrets, and trigger initial cloud sync.
