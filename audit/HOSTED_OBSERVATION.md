# Hosted-app observation — a confident answer computed from 183 of 2,000 rows

**Where:** `app.avaloka.ai`, analysis of `data/sprout_llm_routing.csv` (2,000 rows,
31 columns), same dashboard shown in the submission screenshots.

**Class:** undeclared, product-level. **Severity:** high — the answer is plausible,
internally consistent, and wrong by 15-45x on every group.

This is the one finding in this repository that did **not** come from the CLI. The
CLI cannot produce it: `avaloka analyze` never filters rows by the thing being
measured. It is recorded here because it is the failure the product's own README
describes as the one that destroys credibility — *a fluent, well-formatted, wrong
answer* — and because it is trivially reproducible in five clicks.

---

## 1. What I asked

```
where does paying much more for the frontier model actually pay off, by job type?
```

## 2. What it returned

| agent_role | count | avg_frontier_advantage |
|---|---:|---:|
| profiler | 67 | 0.79 |
| validator | 28 | 0.86 |
| planner | 70 | 0.28 |
| coder | 17 | 0.26 |
| summarizer | 1 | 0.10 |

**67 + 28 + 70 + 17 + 1 = 183.** The chat narrated it as fact: *"The frontier
model pays off most for validators… Profiler has the highest performance gain
(0.793)… Planner and coder show similar cost gains but much lower payoffs."*

Nothing on the result card said which rows were used.

## 3. What those 183 rows are

183 is exactly the number of prompts in the dataset where
`best_frontier_score > best_economy_score` — the prompts where the expensive model
won. The app confirms this itself when asked directly:

> **Q:** `how many rows have frontier_advantage greater than 0?`
> **A:** `183 rows have a frontier_advantage greater than 0.`

And the per-role counts in the answer match the winning subset exactly:

| agent_role | rows in all 2,000 | rows in the 183 wins | count in the answer |
|---|---:|---:|---:|
| profiler | 511 | **67** | 67 |
| validator | 465 | **28** | 28 |
| planner | 810 | **70** | 70 |
| coder | 170 | **17** | 17 |
| summarizer | 44 | **1** | 1 |

So the analysis was performed on the successes, then reported as a property of
the dataset. This is selection on the outcome.

## 4. The same question, asked plainly

```
average frontier_advantage by agent_role
```

returns the correct 2,000-row table — and it matches
`artifacts/ground_truth_metrics.json` to two decimals:

| agent_role | app (all rows) | ground truth |
|---|---:|---:|
| profiler | 0.05 | 0.054 |
| validator | 0.02 | 0.019 |
| coder | 0.00 | 0.001 |
| planner | -0.00 | -0.001 |
| summarizer | -0.00 | -0.005 |

The capability is present. The defect is that the phrase **"pay off"** was
translated into a row filter (`frontier_advantage > 0`) and the filter was not
disclosed.

## 5. Why the guard rail did not catch it

The claim checker compares the *prose* to the *computed table*. Here they agree
perfectly — every sentence is a true statement about the 183 rows. The checker
never asks whether the table covers the dataset.

It then fired on the **next, correct** answer instead:

> ⚠ *Some numbers or claims in this answer did not check out.*
> *Contradicted by the computed results: says 'lowest' at 0.054, but the min of
> `avg_frontier_advantage` is -0.00454545.*

The summary had said the profiler was **highest** at 0.054. So the checker bound a
superlative to the wrong number: a false negative on the filtered answer, followed
by a false positive on the correct one.

## 6. What held

Asked something the data cannot answer — `total revenue by region` — the app
answered honestly: *"The dataset you provided does not contain a revenue column or
any financial metrics, so I cannot calculate total revenue by region."* No invented
number, no fallback row count. That is the behaviour the product is built for, and
it worked.

## 7. Suggested fix

1. **Print the population on every result card** — `183 of 2,000 rows` — and carry
   it into the chart title and the chat narration.
2. **Never derive a filter from the question silently.** If "pays off" is read as
   `advantage > 0`, say so in the result header.
3. **Verify the population before the arithmetic.** A `row_count` assertion in the
   claim verifier would have caught this; a prose-to-number check cannot.
4. **Bind qualifiers to numbers by proximity in the same clause**, not by nearest
   token, to remove the false positive in §5.

## 8. Reproduce

1. Open `app.avaloka.ai`, upload `data/sprout_llm_routing.csv`.
2. In the chat, send the question in §1. Record the five row counts.
3. Send `average frontier_advantage by agent_role`. Compare with §4.
4. Send `how many rows have frontier_advantage greater than 0?`. Expect `183`.

The CLI half of the audit — including the validator gap, the workbook reader and
the row-count bug — is in `ENGINEERING_AUDIT.md`.
