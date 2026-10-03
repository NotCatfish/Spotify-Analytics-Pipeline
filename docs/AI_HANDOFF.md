# AI Session Context Snapshot & Handoff

## 1. Repository Identity & Core Purpose
- **Repository:** `Spotify-Analytics-Pipeline` (Owned by `@NotCatfish` / Indraneel Samanta).
- **Core Domain:** End-to-end data engineering, automated EDA reporting, and low-latency skip prediction for Spotify streaming logs.
- **Key Metric Guardrail:** Precision >= 80% (Business SLA threshold: 0.7816, ROC-AUC: 0.9380, Recall: 0.6844).
- **Dual Policy Dispatched:** High skip probabilities trigger CDN prefetch throttling (`JIT_3SEC_CHUNKING`) and recommendation queue purges (`SILENT_AUTOPLAY_PURGE`).

---

## 2. Directory Architecture & Modular Structure
```
Spotify-Analytics-Pipeline/
├── .github/workflows/
│   ├── ci.yml                           # CI runner (flake8 + pytest)
│   ├── spotify_sync.yml                 # 24/7 Cloud Listening Sync & Model Audit (cron: 14,47 * * * *)
│   └── model_retrain.yml                # Daily automated 00:00 UTC model retraining (cron: 0,37 * * * *)
├── app/
│   ├── api/                             # FastAPI microservice & static dashboard UI
│   │   ├── main.py                      # Serving app with robust sys.path and degraded-mode resilience
│   │   ├── schemas.py                   # Pydantic v2 schemas
│   │   ├── spotify_client.py            # Spotipy OAuth + Last.fm live tagger (recently-played scope)
│   │   └── static/dashboard.html        # Dark-mode dashboard (900ms auto-refresh)
│   ├── notebooks/                       # Scrubbed research notebooks (01, 02, 03 - 0 outputs/vars)
│   ├── pipeline/                        # Production CLI engines (01 through 08)
│   │   ├── 07_cloud_listening_sync.py   # Headless cron sync & strictly causal session replay
│   │   ├── 08_daily_model_retrain.py    # Autonomous daily retraining engine & state machine
│   │   └── get_refresh_token.py         # Local one-time OAuth token helper
│   ├── tests/                           # 24 automated Pytest test cases across 7 suites
│   │   ├── test_cloud_sync.py           # Session momentum, replay, and idempotency tests
│   │   └── ...
│   └── path_utils.py                    # Robust dynamic project root discovery
├── data/
│   ├── raw/                             # Raw Spotify JSONs (ignored)
│   ├── processed/                       # Feature store (modern_historical_baseline.parquet + SQLite via .dvc)
│   └── audit/                           # shadow_audit.jsonl, production_audit.db, retrain_status.json
├── docs/                                # Architectural, EDA, ML, changelog & handoff documentation
└── models/                              # Serialized XGBoost models (tracked directly in Git)
```

---

## 3. Cloud Architecture & Autonomous Operation (Next 10–15 Days)

During the 10–15 day hiatus, two serverless GitHub Actions workflows run autonomously in the background at zero cost:

1. **24/7 Listening Synchronization (`.github/workflows/spotify_sync.yml`):**
   - **Trigger:** Runs twice every hour (`14,47 * * * *`) via off-peak POSIX cron and manual dispatch.
   - **Action:** Authenticates headlessly via `SPOTIPY_REFRESH_TOKEN`, pulls recent Spotify history, reconstructs causal session momentum, predicts skip risk, resolves ground-truth playback duration, and appends unique records to `data/audit/shadow_audit.jsonl`.
   - **Commit:** Automatically commits new telemetry with `[skip ci]` via `github-actions[bot]`.

2. **Daily Autonomous Model Retraining (`.github/workflows/model_retrain.yml`):**
   - **Trigger:** Runs daily at 00:00 UTC with automated 37-minute retries (`0,37 * * * *`).
   - **Action:** Ingests the 126,800 historical baseline records (`data/processed/modern_historical_baseline.parquet`) combined with all novel records in `data/audit/shadow_audit.jsonl`. Fits XGBoost on CPU, optimizes decision threshold to strictly enforce Precision >= 80%, saves updated binary to `models/spotify_skip_predictor_xgb.pkl`, and writes `data/audit/retrain_status.json`.
   - **Commit:** Commits updated model binary and status flag back to `origin/main` with `[skip ci]`.

---

## 4. Current State & Validated Baseline Metrics

- **Current Production Commit:** Fully synchronized on `origin/main` ([NotCatfish/Spotify-Analytics-Pipeline](https://github.com/NotCatfish/Spotify-Analytics-Pipeline)).
- **Unit Test Suite:** 24 out of 24 tests passing.
- **Model Checkpoint:**
  - **Dataset Size:** 127,373 records (126,800 baseline modern records + 573 clean audit records).
  - **Global ROC-AUC:** 0.9380
  - **Optimal Decision Threshold:** 0.7816
  - **Achieved Precision:** 80.01% (SLA Guardrail >= 80% met)
  - **Achieved Recall:** 68.44%
  - **Model Binary:** `models/spotify_skip_predictor_xgb.pkl` (853.55 KB).
- **Ground Truth Integrity:**
  - `shadow_audit.jsonl` verified: Exactly 12 true skips and 561 completed listens (2.09% skip rate).
  - Causal session replay in `07_cloud_listening_sync.py` uses strictly backward-looking delta (`t[i] - t[i-1]`).

---

## 5. Resume Protocol (When Returning After 10–15 Days)

Follow these exact steps when opening a new session after the 10–15 day collection period:

### Step 1: Pull Accumulated Cloud Telemetry
```bash
git pull origin main
```
This pulls all telemetry collected by the sync cron and any daily retrained model binaries committed by `github-actions[bot]`.

### Step 2: Inspect Telemetry Growth
```bash
python -c "
import json
with open('data/audit/shadow_audit.jsonl', encoding='utf-8') as f:
    lines = [json.loads(l) for l in f if l.strip()]
print(f'Total shadow audit records: {len(lines)}')
with open('data/audit/retrain_status.json') as f:
    print('Latest retrain status:', json.load(f))
"
```

### Step 3: Run Full Verification Suite
```bash
pytest
```
Ensure all 24 unit tests continue to pass with the updated model artifact.

### Step 4: Proceed with Phase 8 Milestones
1. **Automated Drift Alerting:** Configure webhook or issue notifications if daily retrain Precision dips below 78%.
2. **FastAPI Load Testing:** Benchmark `/predict_skip` latency under concurrent batch loads.
3. **Dashboard Real-Time Integration:** Verify live queue recommendations against the newly trained weights.

---

## 6. Critical Technical Rules & Gotchas
1. **Dynamic Pathing:** NEVER use hardcoded or relative paths. Always use `from path_utils import resolve_path, find_project_root`.
2. **Model Tracking:** `models/spotify_skip_predictor_xgb.pkl` is directly tracked in Git for zero-friction serverless runner execution without DVC credentials.
3. **CI/CD Resilience:** All automated workflow commits MUST include `[skip ci]` to prevent recursive triggering loops.
4. **Notebooks Cleanliness:** Notebooks must remain 100% scrubbed of execution outputs and stored data variables before committing.
5. **Pre-Commit Gate:** The local `.git/hooks/pre-commit` enforces that all 24 Pytest tests pass before any commit can succeed.
