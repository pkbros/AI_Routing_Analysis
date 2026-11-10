# Avaloka mission `5e29bb113d82`

**Goal:** average frontier_cost_multiplier by task_domain

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

- task_domain=general_instruction: mean frontier_cost_multiplier=73.4.
- task_domain=enterprise_rag: mean frontier_cost_multiplier=61.1.
- task_domain=multistep_deduction: mean frontier_cost_multiplier=59.2.
- task_domain=graduate_science_qa: mean frontier_cost_multiplier=57.5.
- task_domain=multitask_knowledge: mean frontier_cost_multiplier=56.3.

## Limitations

- Estimated manual effort and value are heuristics pending customer calibration.

## Reproduce

```bash
avaloka analyze 'data\sprout_llm_routing.csv' --goal 'average frontier_cost_multiplier by task_domain' --output ./reproduced-analysis
```

---
_Reproduce or adapt this mission with `avaloka`._