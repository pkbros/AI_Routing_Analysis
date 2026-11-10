"""Stage 2: Deterministic Ground-Truth Verification & Idempotency Check.

Computes exact ground-truth metrics from `data/sprout_llm_routing.csv` so every
number reported by Avaloka CLI or the Avaloka web platform can be audited against
deterministic Python arithmetic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "artifacts"


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    # Important: keep_default_na=False on fallback_route or read with null policy
    df = pd.read_csv(DATA_DIR / "sprout_llm_routing.csv", keep_default_na=False)
    numeric_cols = [
        "prompt_tokens", "prompt_words", "prompt_chars", "prompt_lines",
        "question_marks", "code_fences", "math_symbols", "digit_count",
        "uppercase_ratio", "avg_word_length", "golden_reference_words",
        "claude_sonnet_score", "gpt4o_score", "llama70b_score",
        "gpt4o_mini_score", "llama8b_score", "best_frontier_score",
        "best_mid_score", "best_economy_score", "frontier_advantage",
        "frontier_gain_over_mini",
        "cost_per_1k_frontier_usd", "cost_per_1k_economy_usd",
        "frontier_cost_multiplier", "high_compute_route",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    by_domain = {}
    for domain, g in df.groupby("task_domain"):
        by_domain[str(domain)] = {
            "count": int(len(g)),
            "mean_frontier_advantage": round(float(g["frontier_advantage"].mean()), 6),
            "mean_best_frontier_score": round(float(g["best_frontier_score"].mean()), 6),
            "mean_best_economy_score": round(float(g["best_economy_score"].mean()), 6),
            "mean_cost_per_1k_frontier_usd": round(float(g["cost_per_1k_frontier_usd"].mean()), 6),
            "mean_cost_per_1k_economy_usd": round(float(g["cost_per_1k_economy_usd"].mean()), 6),
            "mean_frontier_cost_multiplier": round(float(g["frontier_cost_multiplier"].mean()), 4),
            "high_compute_route_rate": round(float(g["high_compute_route"].mean()), 4),
        }

    by_agent_role = {}
    for role, g in df.groupby("agent_role"):
        by_agent_role[str(role)] = {
            "count": int(len(g)),
            "mean_frontier_advantage": round(float(g["frontier_advantage"].mean()), 6),
            "mean_frontier_gain_over_mini": round(float(g["frontier_gain_over_mini"].mean()), 6),
            "mean_cost_per_1k_frontier_usd": round(float(g["cost_per_1k_frontier_usd"].mean()), 6),
            "mean_cost_per_1k_economy_usd": round(float(g["cost_per_1k_economy_usd"].mean()), 6),
            "mean_claude_sonnet_score": round(float(g["claude_sonnet_score"].mean()), 6),
            "mean_gpt4o_mini_score": round(float(g["gpt4o_mini_score"].mean()), 6),
            "high_compute_route_rate": round(float(g["high_compute_route"].mean()), 4),
        }

    by_fallback = {}
    for route, g in df.groupby("fallback_route"):
        by_fallback[str(route)] = {
            "count": int(len(g)),
            "share_pct": round(float(len(g) / len(df) * 100.0), 2),
            "mean_cost_per_1k_frontier_usd": round(float(g["cost_per_1k_frontier_usd"].mean()), 6),
            "total_cost_per_1k_frontier_usd": round(float(g["cost_per_1k_frontier_usd"].sum()), 6),
            "mean_frontier_advantage": round(float(g["frontier_advantage"].mean()), 6),
        }

    summary = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "overall": {
            "mean_claude_sonnet_score": round(float(df["claude_sonnet_score"].mean()), 6),
            "mean_gpt4o_score": round(float(df["gpt4o_score"].mean()), 6),
            "mean_llama70b_score": round(float(df["llama70b_score"].mean()), 6),
            "mean_gpt4o_mini_score": round(float(df["gpt4o_mini_score"].mean()), 6),
            "mean_llama8b_score": round(float(df["llama8b_score"].mean()), 6),
            "mean_best_frontier_score": round(float(df["best_frontier_score"].mean()), 6),
            "mean_best_mid_score": round(float(df["best_mid_score"].mean()), 6),
            "mean_best_economy_score": round(float(df["best_economy_score"].mean()), 6),
            "mean_frontier_advantage": round(float(df["frontier_advantage"].mean()), 6),
            "mean_cost_per_1k_frontier_usd": round(float(df["cost_per_1k_frontier_usd"].mean()), 6),
            "mean_cost_per_1k_economy_usd": round(float(df["cost_per_1k_economy_usd"].mean()), 6),
            "mean_frontier_cost_multiplier": round(float(df["frontier_cost_multiplier"].mean()), 4),
            "high_compute_route_positive_rate": round(float(df["high_compute_route"].mean()), 4),
        },
        "by_task_domain": by_domain,
        "by_agent_role": by_agent_role,
        "by_fallback_route": by_fallback,
    }

    out_file = ARTIFACTS_DIR / "ground_truth_metrics.json"
    out_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
