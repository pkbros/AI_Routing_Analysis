"""Stage 2: Deterministic Ground-Truth Verification & Idempotency Check.

Computes exact ground-truth metrics from `data/sprout_llm_routing.csv` so every
number reported by Avaloka CLI or the Avaloka web platform can be audited against
deterministic Python arithmetic.

Per-model aggregates (all 13 models, which the curated CSV does not carry
individually) are computed from the raw HuggingFace cache written by stage 1.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "artifacts"

# Mirrors MODEL_PRICING in scripts/01_fetch_and_prepare_data.py.
# (input $/Mtok, output $/Mtok, tier)
MODEL_PRICING: dict[str, tuple[float, float, str]] = {
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

    by_model = {}
    raw_cache = DATA_DIR / "_raw_sprout_test_cache.json"
    if raw_cache.exists():
        raw_rows = json.loads(raw_cache.read_text(encoding="utf-8"))
        for model, (p_in, p_out, tier) in MODEL_PRICING.items():
            scores: list[float] = []
            costs: list[float] = []
            in_tok: list[int] = []
            out_tok: list[int] = []
            for row in raw_rows:
                rec = row.get("models", {}).get(model)
                if not rec:
                    continue
                scores.append(float(rec.get("score") or 0.0))
                n_in = int(rec.get("num_input_tokens") or 0)
                n_out = int(rec.get("num_output_tokens") or 0)
                in_tok.append(n_in)
                out_tok.append(n_out)
                costs.append((n_in * p_in + n_out * p_out) / 1_000_000.0)
            if not scores:
                continue
            by_model[model] = {
                "tier": tier,
                "n": len(scores),
                "mean_score": round(sum(scores) / len(scores), 4),
                "perfect_pct": round(
                    100.0 * sum(1 for s in scores if s >= 0.999) / len(scores), 1
                ),
                "mean_cost_per_1k_usd": round(1000.0 * sum(costs) / len(costs), 4),
                "mean_input_tokens": round(sum(in_tok) / len(in_tok), 1),
                "mean_output_tokens": round(sum(out_tok) / len(out_tok), 1),
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
        "by_model": by_model,
    }

    out_file = ARTIFACTS_DIR / "ground_truth_metrics.json"
    out_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
