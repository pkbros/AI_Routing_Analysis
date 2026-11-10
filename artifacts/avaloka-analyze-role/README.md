# Avaloka mission `c1d064a79765`

**Goal:** average frontier_gain_over_mini by agent_role

This bundle was produced by Avaloka as a governed *Data Mission* — an outcome, not an interaction. Economic multiplier: **11.1x** (≈16.1 manual hours compressed).

## Deliverables

- `executive_report.html` — the decision-maker summary
- `technical_report.html` — full methodology, schema, quality and validation
- `analysis.ipynb` / `analysis.py` — reproducible pipeline
- `transformed_dataset.parquet` — cleaned working dataset
- `data_quality.json`, `validation_report.json`, `planner_graph.json` — evidence
- `assumptions.yaml`, `lineage.json`, `environment.lock` — governance & reproducibility
- `goal_analysis.json` — measured answer to the stated goal

## Key findings

- agent_role=profiler: mean frontier_gain_over_mini=0.122.
- agent_role=coder: mean frontier_gain_over_mini=0.0729.
- agent_role=summarizer: mean frontier_gain_over_mini=0.0136.
- agent_role=planner: mean frontier_gain_over_mini=-0.000741.
- agent_role=validator: mean frontier_gain_over_mini=-0.0359.

## Limitations

- Estimated manual effort and value are heuristics pending customer calibration.

## Reproduce

```bash
avaloka analyze 'data\sprout_llm_routing.csv' --goal 'average frontier_gain_over_mini by agent_role' --output ./reproduced-analysis
```

---
_Reproduce or adapt this mission with `avaloka`._