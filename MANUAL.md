# MANUAL — operating this repository

Behaviour reference for the routing-economics audit. Read `README.md` for the
findings; read this to run, extend or check the work.

---

## 1. One-time setup

Requires Python 3.11 or 3.12 and git. No API key, no cloud account, no billing.

```bash
# clone the Avaloka engine we audit (gitignored, never published from here)
git clone https://github.com/guruvaidev/avaloka.git .avaloka-src

# isolated environment
python -m venv .venv

# Windows
.venv/Scripts/pip install -e ".avaloka-src[formats,benchmark,dev]"
# macOS / Linux
.venv/bin/pip install -e ".avaloka-src[formats,benchmark,dev]"

# prove the install
.venv/Scripts/avaloka --version          # -> 1.6.0
.venv/Scripts/python .avaloka-src/scripts/doctor.py
```

`doctor.py` finishes with `Usable, with 2 optional thing(s) missing` on a clean
machine: `torch` (model training to PyTorch format) and `cryptography` (the API
server) are optional and not needed here.

---

## 2. The four commands, in order

| Command | Reads | Writes | Cost |
|---|---|---|---|
| `python scripts/01_fetch_and_prepare_data.py` | HuggingFace SPROUT test split | `data/*.csv`, `data/*.parquet`, `data/*.xlsx`, `data/provenance.json` | $0, 0 LLM tokens |
| `python scripts/02_verify_ground_truth.py` | `data/sprout_llm_routing.csv` | `artifacts/ground_truth_metrics.json` | $0 |
| `python scripts/03_reproduce_edge_cases.py` | `data/*` | `audit/reproduction_results.json`, `audit/logs/*.log` | $0 |
| (the Avaloka runs below) | `data/*` | `artifacts/avaloka-*` | $0 (local lane) |

`01` caches its HTTP responses in `data/_raw_sprout_test_cache.json`, so a second
run is offline and identical. Delete that file to re-fetch. Reruns are
idempotent: same input twice means zero changed rows.

---

## 3. Running Avaloka by hand

```bash
A=.venv/Scripts/avaloka            # Windows; use .venv/bin/avaloka elsewhere

# 1. analysis — the economics, three ways
$A analyze data/sprout_llm_routing.csv --goal "average frontier_gain_over_mini by agent_role"   --output artifacts/avaloka-analyze-role
$A analyze data/sprout_llm_routing.csv --goal "average cost_per_1k_frontier_usd by fallback_route" --output artifacts/avaloka-analyze-fallback
$A analyze data/sprout_llm_routing.csv --goal "average frontier_cost_multiplier by task_domain"  --output artifacts/avaloka-analyze-domain

# 2. the router, clean vs leaky
$A train data/sprout_pre_execution_routing.csv --target high_compute_route --metric roc_auc --deployable --output artifacts/avaloka-train-clean
$A train data/sprout_llm_routing_leaky.csv     --target high_compute_route --metric roc_auc             --output artifacts/avaloka-train-leaky

# 3. the fleet
$A coordinate data/sprout_llm_routing.csv --workers 4 --goal "average frontier_gain_over_mini by agent_role" --output artifacts/avaloka-fleet
```

Every run prints its own deliverable path; copy the path it prints rather than
the ones above, because the analyzed folder name can vary with the goal.

---

## 4. Reading an Avaloka bundle

Each `artifacts/avaloka-*` directory is a self-contained mission:

| File | What it is |
|---|---|
| `executive_report.html` | the decision summary — open in a browser |
| `README.md` | findings, assumptions and limitations |
| `analysis.py` / `analysis.ipynb` | code that reproduces the run exactly |
| `goal_analysis.json` | the full answer as data, every group named |
| `data_quality.json` | the profile every downstream step reasoned from |
| `validation_report.json` | the verdict, each check, and the deployment ceiling |
| `lineage.json` | where every number came from |
| `mission.json` | economics: duration, manual hours replaced, cost, multiplier |
| `model_card.md` | (train runs) the winner, the panel, the baseline |
| `model/`, `deployment/`, `mlflow/` | (train runs) the Level-2 shippable package |

---

## 5. Where the numbers come from

- **Costs** are computed in `scripts/01_fetch_and_prepare_data.py` from the
  published 2026 per-million-token list prices in `MODEL_PRICING`, applied to
  the token counts the SPROUT dataset recorded for each model. They are model
  prices, not measured bills.
- **Scores** are the SPROUT judge's correctness score (0-1), recorded per model
  per prompt — not something this project computed.
- **`frontier_advantage`** = best frontier-tier score minus best economy-tier
  score, per prompt.
- **`frontier_gain_over_mini`** = Claude-3.5-Sonnet score minus GPT-4o-mini
  score, per prompt (the single cheapest-to-frontier comparison).
- **`high_compute_route`** is the modelling target: 1 when a prompt's measured
  output tokens and frontier advantage indicate it needed the higher reasoning
  budget, from pre-call structure alone.

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: typer` after install | the editable install timed out mid-download | re-run `pip install -e ".avaloka-src[formats,benchmark,dev]"` |
| `UnicodeEncodeError: charmap` from `doctor.py` on Windows | console codepage | set `PYTHONUTF8=1` before running |
| `01` re-downloads slowly | first run only | it writes `data/_raw_sprout_test_cache.json`; later runs use it |
| Avaloka reads the wrong sheet from the `.xlsx` | the declared defect in Finding 1 | upload only the sheet you mean, or use the CSV |
| `avaloka train` needs a target column | `--target` is required | pass `--target high_compute_route` |

---

## 7. Extending

- **A different question:** add a `--goal` to an `analyze` call. Supported
  goals include grouped comparisons, correlations, missingness and trends; an
  unsupported goal is disclosed as `limited`, never guessed.
- **A different dataset:** drop a CSV/Parquet/Excel anywhere and pass the path.
- **Cross-source parity:** Avaloka accepts a `sqlite:///...#table` or
  `s3://...` URI in place of a path; the pipeline is identical.
