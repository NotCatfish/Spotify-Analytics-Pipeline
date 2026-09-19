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
├── .github/workflows/ci.yml        # CI runner (flake8 + pytest)
├── app/
│   ├── api/                        # FastAPI microservice & static dashboard UI
│   │   ├── main.py                 # Serving app with degraded-mode boot resilience
│   │   ├── schemas.py              # Pydantic v2 schemas
│   │   ├── spotify_client.py       # Spotipy OAuth + Last.fm live tagger
│   │   └── static/dashboard.html   # Dark-mode dashboard (900ms auto-refresh)
│   ├── notebooks/                  # Scrubbed research notebooks (01, 02, 03)
│   ├── pipeline/                   # Production CLI engines (01 through 06)
│   ├── tests/                      # 20 automated Pytest test cases across 6 suites
│   │   ├── conftest.py             # Session-scoped fixtures & sys.path injection
│   │   ├── test_ab_simulation.py   # Net utility formula & champion superiority
│   │   ├── test_api.py             # Endpoint checks & degraded mode marks
│   │   ├── test_dvc_tracking.py    # DVC pointer presence & md5 validation
│   │   ├── test_feature_engineering.py # Zero-leakage chronological split
│   │   ├── test_inference.py       # Model prediction bounds & risk separation
│   │   └── test_retrain_challenger.py # Retraining trigger & promotion guardrail
│   └── path_utils.py               # Robust dynamic project root discovery
├── data/
│   ├── raw/                        # Raw Spotify JSONs (ignored)
│   ├── processed/                  # Feature Store SQLite DB (tracked via .dvc)
│   └── audit/                      # Shadow Mode SQLite audit database
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
3. **CI/CD Resilience:**
   - GitHub Actions runners do not pull multi-megabyte DVC binaries.
   - Tests requiring physical `.pkl` model files are marked with `@requires_model` in `test_api.py` or use `pytest.skip()` in `conftest.py` / `test_ab_simulation.py`.
   - FastAPI in `app/api/main.py` boots into a degraded mode when model files are absent, allowing non-model tests to run without crashing.
4. **Git Pre-Commit Gate:**
   - Local `.git/hooks/pre-commit` enforces that all 20 Pytest tests pass before any commit can succeed.
5. **PII and Data Leaks:**
   - Jupyter notebooks in `app/notebooks/` must have all execution outputs scrubbed before committing.
   - No `.pem`, API secrets, or IP addresses in any committed file.

---

## 4. Current Work State & Immediate Next Steps
- **State:** Repository is completely organized, production-hardened, tested (20/20 passing), and versioned with DVC.
- **Active Task:** Root `README.md` updated with comprehensive production documentation.
- **Next Planned Milestone:** Deployment to AWS EC2 (`t3.micro`) using Docker Compose as documented in `docs/setup/SETUP.md`.
