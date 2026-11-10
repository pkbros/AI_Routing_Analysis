# Spec: Multi-Agent LLM Routing Economics & Reliability Audit (Avaloka 1.6)

## 1. Vision & Research Question

Modern AI systems route requests across heterogeneous models—pairing fast, cheap planners (`openai/gpt-oss-120b`, `gpt-4o-mini`, Groq) with frontier coding or reasoning specialists (`claude-3-5-sonnet`, `gpt-4o`, `llama-3-405b`). However, engineering teams lack empirical, statistically validated answers to three concrete questions:

1. **Cost vs. Quality Frontier:** Across 2,000 real benchmark prompts and 13 models (`CARROT-LLM-Routing/SPROUT` on HuggingFace), where does paying ~62x more per turn actually buy correctness, and where does an economy model match a frontier model?
2. **Role & Domain Drivers:** Which Avaloka agent roles (`profiler`, `coder`, `summarizer`, `planner`, `validator`) and task domains (`multitask_knowledge`, `math_reasoning`, `general_instruction`, `enterprise_rag`, `graduate_science_qa`, `multistep_deduction`) exhibit a positive frontier payoff, and how does the `"None"` fallback routing category behave under strict null-policy ingestion (`#474`/`#479`)?
3. **Pre-Execution Routing Model & Verification Gate:** Can we train a deployable classifier (`high_compute_route`) using only pre-call features, and does Avaloka's evidence layer simultaneously certify the clean model (level 4/4 against a mandatory trivial baseline, `DQ-05`) while blocking a post-call leaky feature (`post_call_route_flag`, `DQ-01`)?

## 2. Architecture & Staged Pipeline

Following deterministic staged-artifact discipline, every stage writes inspectable, versioned files to disk:

| Stage | System / Entry Point | Input | Output Artifact(s) |
|---|---|---|---|
| **Stage 1: Upstream Data Acquisition & Curation** | `scripts/01_fetch_and_prepare_data.py` | Public `CARROT-LLM-Routing/SPROUT` dataset (HuggingFace test split) | `data/sprout_llm_routing.csv`, `data/sprout_llm_routing.parquet`, `data/sprout_pre_execution_routing.csv`, `data/sprout_llm_routing_leaky.csv`, `data/sprout_multi_sheet_audit.xlsx`, `data/provenance.json` |
| **Stage 2: Deterministic Ground-Truth Verification** | `scripts/02_verify_ground_truth.py` | `data/sprout_llm_routing.csv` | `artifacts/ground_truth_metrics.json` |
| **Stage 3: Avaloka CLI Execution (`analyze`, `train`, `coordinate`)** | `avaloka` CLI (`v1.6.0`) | `data/sprout_*.csv` | `artifacts/avaloka-analyze-role/`, `artifacts/avaloka-analyze-fallback/`, `artifacts/avaloka-analyze-domain/`, `artifacts/avaloka-train-clean/`, `artifacts/avaloka-train-leaky/`, `artifacts/avaloka-fleet/` |
| **Stage 4: Avaloka 1.6 Engineering & Edge-Case Audit** | `scripts/03_reproduce_edge_cases.py` | `data/sprout_multi_sheet_audit.xlsx` + CLI goal probes | `audit/ENGINEERING_AUDIT.md`, `audit/reproduction_results.json`, `audit/logs/*.log` |
| **Stage 5: Visual Report & Documentation** | `index.html`, `README.md`, `MANUAL.md` | Staged JSON/HTML artifacts | Self-contained interactive report + validated Mermaid diagrams |

## 3. Dataset Provenance

- **Primary Upstream Source:** [CARROT-LLM-Routing/SPROUT (HuggingFace)](https://huggingface.co/datasets/CARROT-LLM-Routing/SPROUT) — 6,637 test prompts evaluated across 13 LLMs spanning frontier, mid-tier, and economy models with judge correctness scores (0–1) and measured input/output token counts per model.
- **Curated Analytical Table (`data/sprout_llm_routing.csv`):** 2,000 deterministically sampled test prompts across 31 columns, including structural pre-call features, agent-role and domain mappings, literal `"None"` category labels in `fallback_route` (81.55% of rows), per-tier correctness scores, 2026 list-price costs per 1,000 turns, and the binary target `high_compute_route`.

## 4. Out of Scope

- No LLM-fabricated synthetic numbers: every metric comes from real benchmark evaluations and deterministic Python execution.
- Private hackathon participant guides (`_participant_guides/`), local Avaloka source clone (`.avaloka-src/`), and `.venv/` are strictly isolated via `.gitignore` and never committed to the public repository.
