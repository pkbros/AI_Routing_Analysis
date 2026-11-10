# Model card — Predict 'high_compute_route'

- **Mission:** `0ee49c7e6145`
- **Task:** binary_classification
- **Target:** high_compute_route
- **Primary metric:** roc_auc
- **Selected model:** random_forest
- **Validation verdict:** PASS (max safe deployment level 4/4)

## Intended use

Decision support for the stated goal. Not a substitute for human judgement on high-stakes decisions.

## Performance

| Candidate | roc_auc | CV mean ± std |
|---|---|---|
| random_forest | 0.9560 | 0.933 ± 0.006 |
| gradient_boosting | 0.9486 | 0.931 ± 0.015 |
| logistic_regression | 0.9443 | 0.920 ± 0.013 |

## Training data

- Rows: 1600 train / 400 test
- Features: 14

## Limitations & ethical considerations

- Estimated manual effort and value are heuristics pending customer calibration.

## Validation checks

- **data_sufficiency** — PASS: ~50 rows/feature suggests >= 750 rows for 15 features.
- **target_leakage** — PASS: No feature is near-perfectly predictive of the target.
- **split_validity** — PASS: Used 'stratified_train_test' (1600 train / 400 test rows).
- **beats_baseline** — PASS: CV roc_auc 0.933 beats the prior baseline (0.500) by more than fold noise.
- **stability** — PASS: CV roc_auc = 0.933 +/- 0.006 (stable).
- **overfitting** — PASS: Holdout and CV scores are consistent.
