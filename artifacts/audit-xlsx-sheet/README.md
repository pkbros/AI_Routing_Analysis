# Avaloka mission `8a67a2b0db7c`

**Goal:** average best_frontier_score by task_domain

This bundle was produced by Avaloka as a governed *Data Mission* — an outcome, not an interaction. Economic multiplier: **11.1x** (≈8.2 manual hours compressed).

## Deliverables

- `executive_report.html` — the decision-maker summary
- `technical_report.html` — full methodology, schema, quality and validation
- `analysis.ipynb` / `analysis.py` — the preparation steps as code; they do not re-read the source (an Excel workbook) and say so when run
- `transformed_dataset.parquet` — cleaned working dataset
- `data_quality.json`, `validation_report.json`, `planner_graph.json` — evidence
- `assumptions.yaml`, `lineage.json`, `environment.lock` — governance & reproducibility
- `goal_analysis.json` — measured answer to the stated goal

## Key findings

- This goal does not map to a supported goal-specific calculation. The remaining report is a general dataset profile, not an answer to the question.

## Limitations

- The stated goal was not fully answered by a supported calculation; see goal_analysis.json for the reason.
- Estimated manual effort and value are heuristics pending customer calibration.

## Reproduce

```bash
avaloka analyze 'data\sprout_multi_sheet_audit.xlsx' --goal 'average best_frontier_score by task_domain' --output ./reproduced-analysis
```

---
_Reproduce or adapt this mission with `avaloka`._