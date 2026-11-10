# Avaloka mission `0ee49c7e6145`

**Goal:** Predict 'high_compute_route'

This bundle was produced by Avaloka as a governed *Data Mission* — an outcome, not an interaction. Economic multiplier: **11.1x** (≈26.1 manual hours compressed).

## Deliverables

- `executive_report.html` — the decision-maker summary
- `technical_report.html` — full methodology, schema, quality and validation
- `analysis.ipynb` / `analysis.py` — reproducible pipeline
- `transformed_dataset.parquet` — cleaned working dataset
- `data_quality.json`, `validation_report.json`, `planner_graph.json` — evidence
- `assumptions.yaml`, `lineage.json`, `environment.lock` — governance & reproducibility
- `model/` + `model_card.md` — the validated model and its card
- `evaluation_report.html`, `cost_quality.json` — candidate comparison & economics
- `service.py`, `Dockerfile`, `deployment/` — the deployment package
- `feature_contract.yaml`, `inference_schema.json`, `monitoring_config.yaml` — the serving contract

## Key findings

- 'prompt_words' and 'prompt_chars' are strongly associated (|corr|=0.9947).
- 'prompt_tokens' and 'prompt_chars' are strongly associated (|corr|=0.9906).
- Column has a single value; no predictive content.
- Best model 'random_forest' scored 0.9560 roc_auc on holdout.
- 'prompt_words' and 'prompt_chars' move together (|corr|=0.9947); consider redundancy or a shared driver.

## Limitations

- Estimated manual effort and value are heuristics pending customer calibration.

## Reproduce

```bash
python analysis.py  # reproduce data preparation
```

## Serve locally

```bash
pip install -r requirements.lock
uvicorn service:app --port 8080
# then: avaloka deploy . --target local
```

---
_Reproduce or adapt this mission with `avaloka`._