# Model card — Predict 'high_compute_route'

- **Mission:** `06dd7f789e75`
- **Task:** binary_classification
- **Target:** high_compute_route
- **Primary metric:** roc_auc
- **Selected model:** logistic_regression
- **Validation verdict:** FAIL (max safe deployment level 1/4)

## Intended use

Decision support for the stated goal. Not a substitute for human judgement on high-stakes decisions.

## Performance

| Candidate | roc_auc | CV mean ± std |
|---|---|---|
| logistic_regression | 1.0000 | 1.000 ± 0.000 |
| random_forest | 1.0000 | 1.000 ± 0.000 |
| gradient_boosting | 1.0000 | 1.000 ± 0.000 |

## Training data

- Rows: 1600 train / 400 test
- Features: 29

## Limitations & ethical considerations

- Potential target leakage detected; resolve before trusting model metrics.
- Estimated manual effort and value are heuristics pending customer calibration.

## Validation checks

- **data_sufficiency** — PASS: ~50 rows/feature suggests >= 1500 rows for 30 features.
- **target_leakage** — FAIL: 1 feature(s) appear to encode the target: post_call_route_flag
- **split_validity** — PASS: Used 'stratified_train_test' (1600 train / 400 test rows).
- **beats_baseline** — PASS: CV roc_auc 1.000 beats the prior baseline (0.500) by more than fold noise.
- **stability** — PASS: CV roc_auc = 1.000 +/- 0.000 (stable).
- **overfitting** — PASS: Holdout and CV scores are consistent.
