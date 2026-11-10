"""Stage 1: Fetch real LLM routing telemetry from CARROT-LLM-Routing/SPROUT (HuggingFace).

Zero LLM calls, $0 cost, 100% deterministic.
Downloads real prompt evaluations across 13 LLMs on the CARROT SPROUT test split,
extracts token counts, judge correctness scores, and published API costs per turn,
and writes:
  - data/sprout_llm_routing.csv            (clean dataset for avaloka analyze & train)
  - data/sprout_llm_routing.parquet        (Parquet format for batch/format parity)
  - data/sprout_llm_routing_leaky.csv      (includes post-call score gap to test Avaloka DQ-01 leakage check)
  - data/sprout_multi_sheet_audit.xlsx     (multi-sheet Excel workbook to reproduce Avaloka 1.6 spreadsheet defects)
  - data/provenance.json                   (cryptographic SHA-256 hashes, source URLs, and schema documentation)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_CACHE = DATA_DIR / "_raw_sprout_test_cache.json"

DATASET_ID = "CARROT-LLM-Routing/SPROUT"
SPLIT = "test"
TARGET_ROWS = 2000
BATCH_SIZE = 100

# Published API pricing ($ per 1M input tokens, $ per 1M output tokens)
# Matches industry standard OpenRouter / AWS Bedrock / OpenAI list prices
MODEL_PRICING: dict[str, tuple[float, float, str]] = {
    # model_col: (in_$/Mtok, out_$/Mtok, tier)
    "aws-claude-3-5-sonnet-v1": (3.00, 15.00, "frontier"),
    "openai-gpt-4o": (2.50, 10.00, "frontier"),
    "wxai-llama-3-405b-instruct": (3.00, 3.00, "frontier"),
    "aws-titan-text-premier-v1": (0.50, 1.50, "mid_tier"),
    "wxai-llama-3-3-70b-instruct": (0.60, 0.60, "mid_tier"),
    "wxai-llama-3-1-70b-instruct": (0.60, 0.60, "mid_tier"),
    "wxai-mixtral-8x7b-instruct-v01": (0.24, 0.24, "mid_tier"),
    "openai-gpt-4o-mini": (0.15, 0.60, "economy"),
    "wxai-llama-3-1-8b-instruct": (0.05, 0.08, "economy"),
    "wxai-granite-3-8b-instruct-8k-max-tokens": (0.06, 0.06, "economy"),
    "wxai-llama-3-2-3b-instruct": (0.03, 0.05, "economy"),
    "wxai-granite-3-2b-instruct-8k-max-tokens": (0.02, 0.02, "economy"),
    "wxai-llama-3-2-1b-instruct": (0.01, 0.02, "economy"),
}

FRONTIER_MODELS = [m for m, (_, _, t) in MODEL_PRICING.items() if t == "frontier"]
MID_MODELS = [m for m, (_, _, t) in MODEL_PRICING.items() if t == "mid_tier"]
ECONOMY_MODELS = [m for m, (_, _, t) in MODEL_PRICING.items() if t == "economy"]


def _turn_cost_usd(model: str, in_tok: int, out_tok: int) -> float:
    p_in, p_out, _ = MODEL_PRICING[model]
    return (in_tok * p_in + out_tok * p_out) / 1_000_000.0


def _map_domain(dataset_name: str) -> str:
    lower = (dataset_name or "").lower()
    if "math" in lower:
        return "math_reasoning"
    if "gpqa" in lower:
        return "graduate_science_qa"
    if "mmlu" in lower:
        return "multitask_knowledge"
    if "musr" in lower:
        return "multistep_deduction"
    if "ragbench" in lower:
        return "enterprise_rag"
    if "openhermes" in lower:
        return "general_instruction"
    return "other"


def _map_agent_role(domain: str, prompt_text: str) -> str:
    """Map benchmark prompt archetype to the equivalent Avaloka agent role."""
    p = (prompt_text or "").lower()
    if any(k in p for k in ("python", "def ", "code", "sql", "script", "function", "algorithm")):
        return "coder"
    if domain == "enterprise_rag":
        return "summarizer"
    if domain in ("math_reasoning", "graduate_science_qa"):
        return "validator"
    if domain == "multistep_deduction":
        return "planner"
    if domain == "multitask_knowledge":
        return "profiler"
    return "planner"


def fetch_raw_rows() -> list[dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_CACHE.exists():
        cached = json.loads(RAW_CACHE.read_text(encoding="utf-8"))
        if len(cached) >= TARGET_ROWS:
            print(f"[cache] Loaded {len(cached)} raw SPROUT rows from {RAW_CACHE.name}")
            return cached[:TARGET_ROWS]

    rows: list[dict[str, Any]] = []
    # Deterministically sample across the entire 6,637-row test split
    offsets = list(range(0, 6000, 300))  # 20 slices * 100 rows = 2,000 rows
    for idx, off in enumerate(offsets, 1):
        url = (
            f"https://datasets-server.huggingface.co/rows"
            f"?dataset=CARROT-LLM-Routing%2FSPROUT&config=default&split={SPLIT}"
            f"&offset={off}&length={BATCH_SIZE}"
        )
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Avaloka-Audit/1.6"})
                with urllib.request.urlopen(req, timeout=45) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                break
            except Exception as exc:
                if attempt == 2:
                    raise RuntimeError(f"Failed to fetch offset {off}: {exc}") from exc
                time.sleep(1.5 * (attempt + 1))

        batch = []
        for item in payload.get("rows", []):
            r = item["row"]
            compact: dict[str, Any] = {
                "key": r["key"],
                "dataset": r["dataset"],
                "dataset_level": r.get("dataset_level") or "",
                "dataset_idx": int(r.get("dataset_idx") or 0),
                "prompt": r.get("prompt") or "",
                "golden_answer": r.get("golden_answer") or "",
                "models": {},
            }
            for m in MODEL_PRICING:
                m_obj = r.get(m) or {}
                compact["models"][m] = {
                    "num_input_tokens": int(m_obj.get("num_input_tokens") or 0),
                    "num_output_tokens": int(m_obj.get("num_output_tokens") or 0),
                    "score": float(m_obj.get("score") or 0.0),
                }
            batch.append(compact)
        rows.extend(batch)
        print(f"[{idx:02d}/{len(offsets):02d}] Fetched offset={off} ({len(batch)} rows, total={len(rows)})")

    RAW_CACHE.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return rows[:TARGET_ROWS]


def transform_rows(raw_rows: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict[str, Any]] = []
    leaky_records: list[dict[str, Any]] = []

    for r in raw_rows:
        prompt = r["prompt"]
        golden = r["golden_answer"]
        domain = _map_domain(r["dataset"])
        agent_role = _map_agent_role(domain, prompt)

        # Prompt structural features (pre-execution features safe for training)
        prompt_chars = len(prompt)
        prompt_words = len(prompt.split())
        prompt_lines = prompt.count("\n") + 1
        question_marks = prompt.count("?")
        code_fences = prompt.count("```")
        math_symbols = len(re.findall(r"[\$\^\\\{\}\=\+\-\*/<>]|\\frac|\\sqrt|\\sum", prompt))
        digit_count = sum(ch.isdigit() for ch in prompt)
        uppercase_ratio = round(sum(ch.isupper() for ch in prompt) / max(1, prompt_chars), 4)
        avg_word_length = round(prompt_chars / max(1, prompt_words), 3)
        golden_reference_words = len(golden.split())

        m_data = r["models"]
        # Input tokens (measured from tokenizer across models)
        prompt_tokens = int(m_data["openai-gpt-4o"]["num_input_tokens"])

        # Per-tier scores, tokens, and costs
        frontier_scores = [m_data[m]["score"] for m in FRONTIER_MODELS]
        mid_scores = [m_data[m]["score"] for m in MID_MODELS]
        econ_scores = [m_data[m]["score"] for m in ECONOMY_MODELS]

        frontier_costs = [
            _turn_cost_usd(m, m_data[m]["num_input_tokens"], m_data[m]["num_output_tokens"])
            for m in FRONTIER_MODELS
        ]
        mid_costs = [
            _turn_cost_usd(m, m_data[m]["num_input_tokens"], m_data[m]["num_output_tokens"])
            for m in MID_MODELS
        ]
        econ_costs = [
            _turn_cost_usd(m, m_data[m]["num_input_tokens"], m_data[m]["num_output_tokens"])
            for m in ECONOMY_MODELS
        ]

        best_frontier_score = round(float(max(frontier_scores)), 4)
        best_mid_score = round(float(max(mid_scores)), 4)
        best_economy_score = round(float(max(econ_scores)), 4)

        claude_sonnet_score = round(float(m_data["aws-claude-3-5-sonnet-v1"]["score"]), 4)
        gpt4o_score = round(float(m_data["openai-gpt-4o"]["score"]), 4)
        llama70b_score = round(float(m_data["wxai-llama-3-3-70b-instruct"]["score"]), 4)
        gpt4o_mini_score = round(float(m_data["openai-gpt-4o-mini"]["score"]), 4)
        llama8b_score = round(float(m_data["wxai-llama-3-1-8b-instruct"]["score"]), 4)

        mean_frontier_cost_usd = round(float(np.mean(frontier_costs)), 6)
        mean_mid_cost_usd = round(float(np.mean(mid_costs)), 6)
        mean_economy_cost_usd = round(float(np.mean(econ_costs)), 6)
        cost_per_1k_frontier_usd = round(mean_frontier_cost_usd * 1000.0, 4)
        cost_per_1k_economy_usd = round(mean_economy_cost_usd * 1000.0, 4)
        frontier_cost_multiplier = round(
            mean_frontier_cost_usd / max(1e-7, mean_economy_cost_usd), 2
        )

        frontier_advantage = round(best_frontier_score - best_economy_score, 4)

        # Fallback policy includes literal string "None" when single economy default (gpt4o-mini) succeeds (>=0.8),
        # exercising Avaloka's null-word category preservation (#474 / #479)
        frontier_gain_over_mini = round(claude_sonnet_score - gpt4o_mini_score, 4)
        if gpt4o_mini_score >= 0.8:
            fallback_route = "None"
        elif llama70b_score >= 0.8:
            fallback_route = "mid_tier_llama70b"
        elif max(claude_sonnet_score, gpt4o_score) >= 0.8:
            fallback_route = "frontier_claude_gpt4o"
        else:
            fallback_route = "human_review_escalation"

        # Binary target for predictive routing (predictable from pre-execution prompt complexity + domain):
        # Does this request require high-compute reasoning (long/dense technical prompt or complex output)?
        avg_out_tokens = float(
            np.mean([m_data[m]["num_output_tokens"] for m in MODEL_PRICING])
        )
        # Target: `high_compute_route` (1 if turn requires high reasoning budget / frontier escalation, 0 otherwise)
        # Grounded in real measured token generation + frontier advantage
        high_compute_route = int(
            (avg_out_tokens >= 320.0) or (frontier_advantage >= 0.35 and prompt_tokens >= 180)
        )

        base_row = {
            "prompt_id": r["key"],
            "source_benchmark": r["dataset"],
            "task_domain": domain,
            "agent_role": agent_role,
            "difficulty_tag": r["dataset_level"] if r["dataset_level"] else "standard",
            "prompt_tokens": prompt_tokens,
            "prompt_words": prompt_words,
            "prompt_chars": prompt_chars,
            "prompt_lines": prompt_lines,
            "question_marks": question_marks,
            "code_fences": code_fences,
            "math_symbols": math_symbols,
            "digit_count": digit_count,
            "uppercase_ratio": uppercase_ratio,
            "avg_word_length": avg_word_length,
            "golden_reference_words": golden_reference_words,
            "fallback_route": fallback_route,
            "claude_sonnet_score": claude_sonnet_score,
            "gpt4o_score": gpt4o_score,
            "llama70b_score": llama70b_score,
            "gpt4o_mini_score": gpt4o_mini_score,
            "llama8b_score": llama8b_score,
            "best_frontier_score": best_frontier_score,
            "best_mid_score": best_mid_score,
            "best_economy_score": best_economy_score,
            "frontier_advantage": frontier_advantage,
            "frontier_gain_over_mini": frontier_gain_over_mini,
            "cost_per_1k_frontier_usd": cost_per_1k_frontier_usd,
            "cost_per_1k_economy_usd": cost_per_1k_economy_usd,
            "frontier_cost_multiplier": frontier_cost_multiplier,
            "high_compute_route": high_compute_route,
        }
        records.append(base_row)

        leaky_row = dict(base_row)
        # Deliberate post-call target leakage column to test Avaloka Validator/Skeptic (DQ-01)
        leaky_row["post_call_route_flag"] = high_compute_route
        leaky_records.append(leaky_row)

    df_full = pd.DataFrame(records)
    df_leaky = pd.DataFrame(leaky_records)
    return df_full, df_leaky


def build_multi_sheet_audit_xlsx(df: pd.DataFrame, out_path: Path) -> None:
    """Create a multi-sheet Excel workbook to test Avaloka 1.6 spreadsheet comprehension."""
    wb = openpyxl.Workbook()
    # Sheet 1: Decoy Raw Telemetry Log (longer sheet with more cells, testing xlsx_decoy_sheet_outweighs_the_answer)
    ws_decoy = wb.active
    ws_decoy.title = "Raw_Token_Log_Decoy"
    ws_decoy.append(["prompt_id", "prompt_tokens", "prompt_words", "prompt_chars", "digit_count"])
    for _, row in df.head(400).iterrows():
        ws_decoy.append([
            row["prompt_id"],
            int(row["prompt_tokens"]),
            int(row["prompt_words"]),
            int(row["prompt_chars"]),
            int(row["digit_count"]),
        ])

    # Sheet 2: Executive Cost Summary with title block, stacked header, and Grand Total row at bottom
    ws_summary = wb.create_sheet("Routing_Cost_Summary")
    ws_summary.append(["SPROUT Multi-LLM Routing Cost & Accuracy Summary (USD per 1,000 turns)"])
    ws_summary.append([])
    ws_summary.append([
        "task_domain",
        "prompt_count",
        "cost_per_1k_frontier_usd",
        "cost_per_1k_economy_usd",
        "best_frontier_score",
        "best_economy_score",
    ])
    grouped = (
        df.groupby("task_domain", as_index=False)
        .agg(
            prompt_count=("prompt_id", "count"),
            cost_per_1k_frontier_usd=("cost_per_1k_frontier_usd", "mean"),
            cost_per_1k_economy_usd=("cost_per_1k_economy_usd", "mean"),
            best_frontier_score=("best_frontier_score", "mean"),
            best_economy_score=("best_economy_score", "mean"),
        )
        .sort_values("prompt_count", ascending=False)
    )
    for _, r in grouped.iterrows():
        ws_summary.append([
            r["task_domain"],
            int(r["prompt_count"]),
            round(float(r["cost_per_1k_frontier_usd"]), 4),
            round(float(r["cost_per_1k_economy_usd"]), 4),
            round(float(r["best_frontier_score"]), 4),
            round(float(r["best_economy_score"]), 4),
        ])
    # Add Grand Total row at the bottom (triggers xlsx_totals_row_at_bottom)
    ws_summary.append([
        "Total",
        int(grouped["prompt_count"].sum()),
        round(float(grouped["cost_per_1k_frontier_usd"].sum()), 4),
        round(float(grouped["cost_per_1k_economy_usd"].sum()), 4),
        round(float(grouped["best_frontier_score"].mean()), 4),
        round(float(grouped["best_economy_score"].mean()), 4),
    ])
    wb.save(out_path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    raw_rows = fetch_raw_rows()
    df_full, df_leaky = transform_rows(raw_rows)

    # Also build a clean pre-execution modelling table (no post-call scores/costs that wouldn't exist before routing)
    pre_exec_cols = [
        "prompt_id",
        "source_benchmark",
        "task_domain",
        "agent_role",
        "difficulty_tag",
        "prompt_tokens",
        "prompt_words",
        "prompt_chars",
        "prompt_lines",
        "question_marks",
        "code_fences",
        "math_symbols",
        "digit_count",
        "uppercase_ratio",
        "avg_word_length",
        "golden_reference_words",
        "high_compute_route",
    ]
    df_pre_exec = df_full[pre_exec_cols].copy()

    csv_path = DATA_DIR / "sprout_llm_routing.csv"
    parquet_path = DATA_DIR / "sprout_llm_routing.parquet"
    pre_exec_path = DATA_DIR / "sprout_pre_execution_routing.csv"
    leaky_path = DATA_DIR / "sprout_llm_routing_leaky.csv"
    xlsx_path = DATA_DIR / "sprout_multi_sheet_audit.xlsx"

    df_full.to_csv(csv_path, index=False, lineterminator="\n")
    df_full.to_parquet(parquet_path, index=False)
    df_pre_exec.to_csv(pre_exec_path, index=False, lineterminator="\n")
    df_leaky.to_csv(leaky_path, index=False, lineterminator="\n")
    build_multi_sheet_audit_xlsx(df_full, xlsx_path)

    provenance = {
        "upstream_dataset": DATASET_ID,
        "upstream_url": "https://huggingface.co/datasets/CARROT-LLM-Routing/SPROUT",
        "split": SPLIT,
        "rows_extracted": len(df_full),
        "models_evaluated_per_prompt": len(MODEL_PRICING),
        "files": {
            csv_path.name: {"rows": len(df_full), "cols": df_full.shape[1], "sha256": sha256_file(csv_path)},
            parquet_path.name: {"rows": len(df_full), "cols": df_full.shape[1], "sha256": sha256_file(parquet_path)},
            pre_exec_path.name: {"rows": len(df_pre_exec), "cols": df_pre_exec.shape[1], "sha256": sha256_file(pre_exec_path)},
            leaky_path.name: {"rows": len(df_leaky), "cols": df_leaky.shape[1], "sha256": sha256_file(leaky_path)},
        },
    }
    (DATA_DIR / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {csv_path} ({len(df_full)} rows, {df_full.shape[1]} cols)")
    print(f"Wrote {pre_exec_path} ({len(df_pre_exec)} rows, {df_pre_exec.shape[1]} cols)")
    print("SHA-256 (sprout_llm_routing.csv):", provenance["files"][csv_path.name]["sha256"])


if __name__ == "__main__":
    main()
