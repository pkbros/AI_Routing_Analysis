# TRACKER — Multi-Agent LLM Routing Economics & Reliability Audit

## Current Status

- **Phase:** Complete — Verified & Committed
- **State:** Dataset fetched (`2,000 x 31`), ground truth verified, all Avaloka CLI missions (`analyze`, `train`, `coordinate`) executed, engineering audit reproduced (`4/4` contract checks hold, `1/1` declared gap + `workload.peek` root cause documented), `index.html` and `README.md` verified and committed. Private guides (including the new `05_INDEX_HTML_GUIDE.md`) aligned around the six-beat video order.
- **Immediate Next Step:** Participant records the 2-minute screen capture using `_participant_guides/02_VIDEO_SCRIPT_2MIN.md` (local CLI + `index.html`, no web-app footage required), pushes the repo to GitHub, and submits the Google Form using `_participant_guides/03_GOOGLE_FORM_ANSWERS.md`.

---

## Milestone Checklist

- [x] **M0: Project Discipline Bootstrap**
  - [x] `.gitignore` isolating `_participant_guides/`, `.avaloka-src/`, `.venv/`, raw cache
  - [x] `SPEC.md` defining the research question, staged pipeline, dataset provenance
  - [x] `TRACKER.md` with task + append-only decision logs
- [x] **M1: Local Avaloka 1.6 Environment Setup**
  - [x] Cloned `guruvaidev/avaloka` into `.avaloka-src/`
  - [x] Python 3.12 `.venv`, editable install with `[formats,benchmark,dev]`
  - [x] `avaloka --version` -> `1.6.0`; `scripts/doctor.py` -> core packages clean (torch/cryptography optional and absent)
- [x] **M2: Real Public Dataset (`CARROT-LLM-Routing/SPROUT`) & Ground Truth**
  - [x] `scripts/01_fetch_and_prepare_data.py` — $0, 0 AI tokens, real judge scores + token counts for 2,000 prompts x 13 models
  - [x] `scripts/02_verify_ground_truth.py` — deterministic metrics, `artifacts/ground_truth_metrics.json`
- [x] **M3: Avaloka CLI Execution (`analyze`, `train`, `coordinate`)**
  - [x] `analyze` x 3 goals (by `agent_role`, by `fallback_route`, by `task_domain`)
  - [x] `train` clean -> `random_forest` roc_auc 0.9560 holdout / 0.933 +/- 0.006 CV, level **4/4**
  - [x] `train` leaky (post-call column) -> verdict **FAIL**, `target_leakage` names the column, ceiling capped at **1/4**
  - [x] `coordinate --workers 4` -> 4 sub-Avalokas, 2,000 rows merged, verdict pass
- [x] **M4: Engineering Audit ("What Broke or Was Confusing")**
  - [x] `scripts/03_reproduce_edge_cases.py` runs 5 probes, captures raw logs
  - [x] `audit/ENGINEERING_AUDIT.md` with symptom -> root cause (file:line) -> evidence -> suggested fix
- [x] **M5: Public Documentation, Interactive Report & Visual Verification**
  - [x] `audit/ENGINEERING_AUDIT.md`
  - [x] `README.md` and `MANUAL.md`; Mermaid flow validated by the parser checker (1 passed, 0 failed)
  - [x] `index.html` self-contained report; 4 inline SVG charts rasterized and inspected via resvg (PASS 4/4 after fixing a label collision)
- [x] **M6: Private Participant Guides (`_participant_guides/`)**
  - [x] `01_WEB_APP_WALKTHROUGH.md` (exact steps & prompts for `https://avaloka.ai`)
  - [x] `02_VIDEO_SCRIPT_2MIN.md` (second-by-second script)
  - [x] `03_GOOGLE_FORM_ANSWERS.md` (copy-paste answers for all submission fields)
  - [x] `04_INTERVIEW_CHEATSHEET.md` (talking points on Avaloka's codebase)
  - [x] `05_INDEX_HTML_GUIDE.md` (plain-language walkthrough of every section of `index.html`)
  - [x] `06_AVALOKA_PAGE_GUIDE.md` (walkthrough of `avaloka.html` + the 15-second clip)
  - [x] All guides aligned to the same video order after Finding 6 was added
- [x] **M7: Repository hygiene**
  - [x] `.gitignore` keeps `_participant_guides/`, `.avaloka-src/`, `.venv/`, raw cache, and `_audit_runs/` out of the public tree
  - [x] `git init` + clean commit verified

---

## Verification log

| Check | Command | Result |
|---|---|---|
| Avaloka install | `python .avaloka-src/scripts/doctor.py` | core packages clean; torch/cryptography optional and absent |
| Dataset + ground truth | `python scripts/01...` + `02...` | 2,000 x 31 rows; `ground_truth_metrics.json` written |
| Contract checks | `python scripts/03_reproduce_edge_cases.py` | **4/4** contract pass; **1/1** declared gap reproduced |
| Mermaid | `check_mermaid.mjs README.md` | **1 passed, 0 failed** |
| Report charts | `node check.js` (resvg) | **4/4** SVG blocks rasterize; label collision found and fixed |

---

## Key Measured Numbers (from this machine)

| Quantity | Value | Source |
|---|---|---|
| Prompts x models | 2,000 x 13 | `data/provenance.json` |
| Mean frontier cost / 1k turns | $4.82 | `artifacts/ground_truth_metrics.json` |
| Mean economy cost / 1k turns | $0.0939 | same |
| Mean frontier cost multiplier | 62.6x (range 5.98x-446x) | same |
| Mean frontier advantage (best frontier - best economy) | +0.0179 | same |
| Largest role gap (frontier gain over gpt-4o-mini) | profiler +0.122 | same |
| Smallest role gap | validator -0.036 | same |
| `fallback_route == "None"` share | 81.55% (1,631 rows) | same |
| Routing model (clean) | random_forest roc_auc 0.9560 holdout, CV 0.933 +/- 0.006, level 4/4 | `artifacts/avaloka-train-clean/model_card.md` |
| Leaky model | roc_auc 1.0000 -> verdict FAIL, level 1/4 | `artifacts/avaloka-train-leaky/` |
| Fleet | 4 sub-Avalokas, 2,000 rows, verdict pass | `artifacts/avaloka-fleet/coordination.json` |
| Data quality score | 98/100 | `data_quality.json` |

---

## Decisions Log (Append-Only)

| Date | Decision | Rationale |
|---|---|---|
| 2026-11-10 | Anchor analysis on real public LLM routing telemetry (`CARROT-LLM-Routing/SPROUT`, HuggingFace). | Directly aligns with Guruvai Sciences' `docs/model-routing-cost.md`, requires $0 and 0 AI tokens to fetch, and provides a permanent public URL for the Google Form. Supersedes the earlier RouterBench choice, whose smallest file is 95 MB of pickles rather than a directly readable table. |
| 2026-11-10 | Isolate participant coaching material in `_participant_guides/` and list it in `.gitignore`. | Gives the participant cheat sheets, form copy and video script locally while keeping the public repo clean and judge-facing. |
| 2026-11-10 | Clone `guruvaidev/avaloka` into `.avaloka-src/` (gitignored); commit only our scripts, dataset, generated Avaloka bundles, audit and dashboard. | Avoids a nested repo while allowing full local CLI runs and source-level root-cause tracing. |
| 2026-11-10 | Map SPROUT benchmark prompts onto Avaloka's own agent roles (`planner`, `coder`, `validator`, `profiler`, `summarizer`). | Makes the analysis speak the same vocabulary as `docs/model-routing-cost.md`, so the finding is directly actionable for the team. |
| 2026-11-10 | Build the predictive target as pre-execution-only (`high_compute_route`), and keep a separate leaky copy. | The clean file proves a deployable model exists from information available *before* routing; the leaky file proves the Integrity gate blocks post-call telemetry. |
| 2026-11-11 | Drop the hosted `avaloka.ai` web-app half; submit on the open-source CLI + `index.html` only. | Project creation on the hosted app requires a premium workspace. `docs/USER_GUIDE.md:114-117` states access is by invitation and an unknown email will not create an account; `docs/EDITIONS.md:42` names "self-host" as the intended workaround for a COST gate, and `EDITIONS.md:130-158` confirms the OSS edition gates nothing we used. The CLI path is therefore the documented route, not a workaround of convenience, and it makes the whole submission judge-reproducible with no account. Recorded as a product observation in `audit/ENGINEERING_AUDIT.md`. |
| 2026-11-12 | Lead the "what broke" answer with the `goal_answered` gap, not the regex goal parser. | The parser is a documented design choice (`EDITIONS.md:71`, `cli.py:365` `--llm` opt-in, hosted planner uses an LLM), so reporting it reads as a misreading of the architecture. The validator gap is undeclared, sits in the safety layer the product is built around, reproduces three ways, and has a five-line fix. |
| 2026-11-12 | Add `05_INDEX_HTML_GUIDE.md` and re-order every private guide around the six video beats. | The report page is the only surface shown in the video. A section-by-section plain-language guide makes it recordable without a data-science background, and one shared beat order keeps `02`, `03` and `05` consistent. |
| 2026-11-12 | Split the web surface: `index.html` = standalone findings, `avaloka.html` = pipeline, guard rail and engineering audit. | The submission must show Avaloka *was used*, not advertise it throughout. The analysis has to work as an independent project, so the findings page carries no tool-level material; the audit and pipeline live on their own page, which also gives the bug hunt a clean 15-second clip instead of interrupting the findings narrative. |
| 2026-11-12 | Move the leak-test callout off `index.html`; it lives only on `avaloka.html` §2. | The callout's subject was the validator's refusal ("verdict FAIL, ceiling 1/4") — a statement about tool behaviour, not about model costs. Keeping it on the findings page contradicted the split. The page now earns trust from one neutral fact: the feature set is pre-call only. |
| 2026-11-12 | Add `07_FORM_COPY_PASTE.md` and restore the hosted-access note in the form answer. | The form instructs "use Avaloka on the website", so the invitation-only workspace must be disclosed rather than silently skipped; `USER_GUIDE.md:114-117` and `EDITIONS.md:42` show self-host is the documented route, not a workaround. A bare paste-only file removes the risk of pasting commentary into the form. |
