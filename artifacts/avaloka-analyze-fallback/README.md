# Avaloka mission `f6d36bb2a27d`

**Goal:** average cost_per_1k_frontier_usd by fallback_route

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

- fallback_route=mid_tier_llama70b: mean cost_per_1k_frontier_usd=5.53.
- fallback_route=human_review_escalation: mean cost_per_1k_frontier_usd=5.1.
- fallback_route=None: mean cost_per_1k_frontier_usd=4.75.
- fallback_route=frontier_claude_gpt4o: mean cost_per_1k_frontier_usd=4.45.

## Limitations

- Estimated manual effort and value are heuristics pending customer calibration.

## Reproduce

```bash
avaloka analyze 'data\sprout_llm_routing.csv' --goal 'average cost_per_1k_frontier_usd by fallback_route' --output ./reproduced-analysis
```

---
_Reproduce or adapt this mission with `avaloka`._