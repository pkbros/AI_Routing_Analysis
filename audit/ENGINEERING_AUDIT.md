# Engineering Audit — Avaloka 1.6.0 (local CLI)

Every claim here was produced by running the shipped `avaloka` CLI on this machine
(Avaloka 1.6.0, Python 3.12.10, Windows) and capturing the raw output. The whole
audit is reproducible in one command:

```bash
python scripts/03_reproduce_edge_cases.py
```

- Machine-readable verdicts: `audit/reproduction_results.json`
- Verbatim CLI output per probe: `audit/logs/<probe>.log`

Result: **4 / 4 contract checks hold; 1 / 1 declared gap reproduced.**

| Probe | Class | Declared as | Result |
|---|---|---|---|
| Sheet selection ignores the question | EXPECTED_GAP | `xlsx_decoy_sheet_outweighs_the_answer` | reproduced |
| Unresolved measure is disclosed, not counted | CONTRACT | #475 | **pass** |
| A post-call feature that encodes the target fails training | CONTRACT | DQ-01 | **pass** |
| The winner is compared with a trivial baseline | CONTRACT | DQ-05 | **pass** |
| A null-like word stays a category | CONTRACT | #474 / #479 | **pass** |

A *CONTRACT* probe is behaviour that must hold; if one failed it would be a real
regression. An *EXPECTED_GAP* probe is a limitation Avaloka 1.6 already declares
in `avaloka/benchmark/known_defects.py`; it is reproduced here so the limitation
is evidenced rather than asserted.

Two further findings came from manual runs rather than the probe script, and are
not declared anywhere upstream:

- **Finding 1, part two** — the sizing line counts newline bytes inside an xlsx
  ZIP, so it announced `99 rows` for a 400-row sheet, as an exact figure.
- **Finding 6** — the Validator has eight checks for whether a result is safe,
  and none for whether the question was answered, so an unanswered goal ships
  `status: "limited"` and `verdict: "pass"` in the same bundle.

---

## Finding 1 — the workbook reader picks a sheet by size, not by the question

**Class:** declared known defect, reproduced. **Severity:** medium (silent
wrong-sheet read).

**What I did.** Built a two-sheet workbook, `data/sprout_multi_sheet_audit.xlsx`:

- `Raw_Token_Log_Decoy` — 400 rows x 5 columns of raw token counts.
- `Routing_Cost_Summary` — the small sheet that actually holds
  `best_frontier_score` and `task_domain`, and the one my goal names.

Then asked a question that can only be answered from the second sheet:

```bash
avaloka analyze data/sprout_multi_sheet_audit.xlsx --goal "average best_frontier_score by task_domain"
```

**What happened.** Avaloka read the decoy, never saw `best_frontier_score`, and
reported the goal as unanswerable — while still printing `Validation verdict: PASS`:

```
Avaloka  Let me look… 99 rows across several columns.
  ↩ Ava-Scout returns: Profiled 5 columns x 400 rows; quality score 100/100
What I found
  • This goal does not map to a supported goal-specific calculation.
Validation verdict: PASS; max safe deployment level 1/4
```

**Root cause.** `avaloka/io/loader.py::_read_excel`, line 158:

```python
name, raw = max(book.items(), key=lambda kv: kv[1].notna().sum().sum())
```

The sheet is chosen by **non-empty cell count**, with no reference to the goal.
The function's own docstring says as much — "Neither heuristic asks what the
question was about" — and the same defect is listed in `known_defects.py` as
`xlsx_decoy_sheet_outweighs_the_answer` and in the `CHANGELOG` under *Known
issues*.

**The second, undeclared part — the spoken row count is wrong and unflagged.**
The sizing line said `99 rows`; the reader then profiled `400 rows`. Same file,
same run, two numbers. Root cause in `avaloka/workload.py::peek`, lines 84-85:

```python
n_rows, estimated = _count_csv_rows(path)
```

`peek` special-cases `.parquet` and then treats **every other suffix as CSV**.
`_count_csv_rows` counts `\n` bytes. On an `.xlsx` — a ZIP archive — that counts
newline *bytes in the compressed container*, which has no relationship to the
row count of any sheet. Because the file is under the 4 MB sampling threshold,
`_count_csv_rows` also returns `estimated=False`, so the number is spoken as if
it were exact.

**Why it matters.** Sizing drives the lane (online / sampled / batch) and the
sentence the user is shown first. A wrong exact-looking row count for a
spreadsheet is the kind of number a reader trusts. Here it did not change the
lane, but it corrupts the one figure the product states before doing any work.

**Suggested fix (small, testable).**

1. In `peek`, add an Excel branch that returns rows from the workbook the reader
   will actually use (`openpyxl`/pandas `sheet_name=None`), or at minimum
   return `0, n_bytes, True` so the count is marked an estimate rather than a
   false exact.
2. The upstream fix the project already tracks — choose the sheet where the
   question is — closes the silent-wrong-sheet half; a regression test asserting
   that `peek()` and `DataScout` agree on `n_rows` for an `.xlsx` closes this half.

---

## Finding 2 — an unresolved measure is disclosed, not answered with a row count

**Class:** contract, holds (#475).

```bash
avaloka analyze data/sprout_llm_routing.csv --goal "total cost by task_domain"
```

`"cost"` is not a column, but three numeric columns contain the word. Avaloka
refuses to guess and names them:

```
What I found
  • The goal asks for cost, but no column is named that; it could mean
    cost_per_1k_frontier_usd, cost_per_1k_economy_usd, frontier_cost_multiplier.
    Name the column in the goal to get a figure.
```

This is exactly the behaviour #475 introduced: a goal that names a measure it
cannot find reports `limited` and lists candidates, instead of quietly counting
rows per group and calling it answered. Verified: all three candidate names
appear, and the goal is not answered as a statistic.

---

## Finding 3 — the Integrity gate blocks post-call leakage

**Class:** contract, holds (DQ-01).

I built a deliberately leaky copy of the training table by adding
`post_call_route_flag`, a column that reproduces the target exactly (it would
only exist *after* a call had run). Training on it:

```bash
avaloka train data/sprout_llm_routing_leaky.csv --target high_compute_route --metric roc_auc
```

```
↩ Ava-Scientist returns: Trained 3 candidate(s); selected 'logistic_regression' (roc_auc=1.0000).
↩ Ava-Skeptic returns: Validation verdict='fail'; 6 checks; max safe deployment level 1.
Validation verdict: FAIL; max safe deployment level 1/4
  ✗ target_leakage: 1 feature(s) appear to encode the target: post_call_route_flag
```

The perfect score is not celebrated — it is treated as the symptom it is. The
leaking column is named and the deployment ceiling is capped at 1/4.

---

## Finding 4 — a model must beat a trivial baseline

**Class:** contract, holds (DQ-05).

On the clean, pre-execution table (`data/sprout_pre_execution_routing.csv`, 17
columns, no post-call information):

```
↩ Ava-Scientist returns: Trained 3 candidate(s); selected 'random_forest' (roc_auc=0.9560).
Validation verdict: PASS; max safe deployment level 4/4
  beats_baseline  PASS: CV roc_auc 0.933 beats the prior baseline (0.500) by more than fold noise.
```

The score is never reported without the baseline it must beat. The comparison is
on the confidence interval, so a majority-class model cannot pass on
floating-point noise. Candidate panel and CV spread:

| Candidate | Holdout roc_auc | CV mean +/- std |
|---|---|---|
| random_forest | 0.9560 | 0.933 +/- 0.006 |
| gradient_boosting | 0.9486 | 0.931 +/- 0.015 |
| logistic_regression | 0.9443 | 0.920 +/- 0.013 |

---

## Finding 5 — `"None"` stays a category, not a missing value

**Class:** contract, holds (#474 / #479).

The `fallback_route` column contains the literal string `None` for 1,631 of
2,000 rows — the largest segment, and a real routing decision ("no fallback
needed"), not a gap. Pandas reads `None` as missing by default, which would have
erased the biggest group from every breakdown. Avaloka keeps it:

```bash
avaloka analyze data/sprout_llm_routing.csv --goal "average cost_per_1k_frontier_usd by fallback_route"
```

```
What I found
  • fallback_route=mid_tier_llama70b: mean cost_per_1k_frontier_usd=5.53.
  • fallback_route=human_review_escalation: mean cost_per_1k_frontier_usd=5.1.
  • fallback_route=None: mean cost_per_1k_frontier_usd=4.75.
  • fallback_route=frontier_claude_gpt4o: mean cost_per_1k_frontier_usd=4.45.
```

The `None` group is present by name. The rule (`avaloka/io/loader.py`, the
`NULL_WORDS` block): an empty cell is always missing, a null-like **word** is
missing in a typed column and a **label** in a text column.

---

## Finding 6 — the verdict never asks whether the question was answered

**Class:** undeclared. **Severity:** medium (a PASS printed on an unanswered goal).

**What I did.** Two independent runs, each asking something the data cannot
answer. First:

```bash
avaloka analyze data/sprout_llm_routing.csv --goal "total revenue by region"
```

Second, the decoy workbook from Finding 1, whose goal names a column Avaloka
never read. Both produced the same pair of files in the same bundle.

**`goal_analysis.json`** — honest, and explicit:

```json
{
  "goal": "total revenue by region",
  "kind": "dataset_overview",
  "status": "limited",
  "columns": [],
  "metrics": {},
  "findings": ["This goal does not map to a supported goal-specific calculation.
                The remaining report is a general dataset profile,
                not an answer to the question."]
}
```

**`validation_report.json`** — in the same folder, from the same run:

```json
{
  "verdict": "pass",
  "max_safe_deployment_level": 1,
  "checks": [{"name": "data_sufficiency", "status": "pass"}]
}
```

The reporter writes *"not an answer to the question."* The validator writes
**`PASS`**. Three separate runs reproduce it:

| Goal | `status` | Verdict | Checks run |
|---|---|---|---|
| `total revenue by region` | `limited` | **pass** | `data_sufficiency` only |
| decoy workbook (goal unreadable) | `limited` | **pass** | `data_sufficiency` only |
| `why did quality drop last quarter` | `limited` | **pass** | `data_sufficiency` only |

**Root cause.** The status is computed and stored —
`avaloka/fireflies/analysis_planner.py:148`:

```python
plan["goal_analysis_status"] = goal_result["status"]
```

and then nothing reads it. `avaloka/fireflies/validator.py` assembles its checks
from a fixed set of eight, and there is no ninth:

```
data_sufficiency   target_leakage   split_validity   beats_baseline
stability          overfitting      latency_budget   data_quality
```

Every one asks *"is this artifact statistically safe?"* Not one asks *"did we
answer the question that was asked?"*

**Why `PASS` is not literally a lie.** The Validator's mandate is the safety of
the artifact. With no model trained, nothing unsafe happened, so `pass` is
correct *by its own definition*. The defect is that the verdict has no word for
*"I did not answer you"*. Because a PASS and an explicit "not an answer" ship
side by side, and because PASS is the line a reader takes away, the bundle
contradicts itself in the one place designed to prevent exactly that.

**Suggested fix (five lines, in `validator.py`):**

```python
if plan.get("goal_analysis_status") == "limited":
    checks.append({
        "name": "goal_answered",
        "status": WARN,          # or FAIL, if the goal is the mission
        "severity": "high",
        "detail": "The stated goal was not answered by a supported calculation.",
    })
```

This also closes the silent `PASS` half of Finding 1: a wrong-sheet read that
leaves the goal unanswered would fail this check instead of passing quietly.

---

## Note — access to the hosted edition (product observation, not a CLI defect)

Before any of the above, the hosted web app could not be used from a new
account. Signing in and uploading a file worked; creating a project prompted for
a premium plan. That is consistent with two statements in the shipped docs:

- `docs/USER_GUIDE.md:114-117` — *"There is no sign-up form. Access comes from an
  invitation… Submitting an email that has no account will not create one."*
  A workspace is provisioned by invitation, so a new email has no self-serve path
  into one.
- `docs/EDITIONS.md:71` lists *conversational data analysis* as available in
  **every** edition, including Free; `docs/EDITIONS.md:103` lists *model
  training, registry, inference serving* as **OSS ● / Free ○ / Pro ●**.

So the capability this project needed was never the obstacle — workspace
provisioning was. `docs/EDITIONS.md:42` states the intended workaround for a
COST gate in as many words: **"Yes — self-host."** The open-source edition is
Apache-2.0 and carries no gate on analysis, profiling, visualization, training or
local execution (`docs/EDITIONS.md:130-158`).

**What this project did:** ran the open-source CLI, which is the documented path,
and reproduced every result locally with no API key and no cloud account. Nothing
below depends on the hosted app. The practical consequence for an evaluation
like this one is worth stating plainly: the fastest way to run Avaloka is the
clone-and-run path in `MANUAL.md`, and a participant who has not been invited to
a workspace should go straight there rather than treat the hosted gate as a
dead end.

---

## Summary

Avaloka 1.6's evidence layer behaved as documented on all four contract probes —
leakage blocked by name, a mandatory baseline, honest disclosure of an
unresolved measure, and null-word categories preserved. The one behavioural gap
reproduced here is the spreadsheet reader: it chose the wrong sheet and reported
a row count that matches nothing, both of which the project already tracks. The
`peek()`-on-a-ZIP half of that (Finding 1, part two) is not called out in the
`CHANGELOG` and is the more useful of the two to fix first, because it is small,
self-contained and currently speaks a confident wrong number.

The one non-code friction worth flagging is access: the hosted edition is
invite-only, and the docs say so — but only in `USER_GUIDE.md`, not on the
pricing or sign-up surface where a new user meets the wall. A single line at the
gate ("no workspace for this email — run the OSS edition or request an
invitation") would have saved the detour.

Of everything here, **Finding 6 is the one worth fixing first.** It is five
lines, it sits in the layer the product is built around, and it closes the only
place where the bundle contradicts itself: the reporter states plainly that the
question was not answered, and the validator beside it returns `PASS`. Adding a
`goal_answered` check costs almost nothing and makes the verdict honest in the
one situation where a reader most needs it to be.
