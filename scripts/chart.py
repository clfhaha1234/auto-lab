#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.8",
# ]
# ///
"""auto-lab chart helper.

Reads a single data.json (per-arm aggregates + variance + cost) and renders
one of three publication-quality figures:

    arm-bar           Phase 3 arm-comparison bar with variance error bars
    forest-plot       Phase 5 effect-size + 95% CI + per-slice break-down
    cost-vs-accuracy  Cost-vs-accuracy Pareto scatter

Usage (uv reads the PEP 723 header above and provisions matplotlib in an
isolated env — no pip step needed if you have uv installed):

    uv run scripts/chart.py arm-bar          --data data.json --out arm-bar.png
    uv run scripts/chart.py forest-plot      --data data.json --out forest.png
    uv run scripts/chart.py cost-vs-accuracy --data data.json --out cost.png

Plain python also works if matplotlib is already installed:

    python scripts/chart.py arm-bar --data data.json --out arm-bar.png

Data shape: see examples/prompt-tuning-classifier/data.json for the canonical
schema. Briefly:
    arms[]                — id, name, cost_per_1k_usd
    slices[]              — id, name
    variance_trials       — arm_id -> [trial1_score, trial2_score, ...]
    test_set_aggregate    — arm_id -> aggregate accuracy on held-out test
    test_set_per_slice    — arm_id -> {slice_id -> accuracy}
    effect_sizes          — non-baseline arm_id -> {aggregate, per_slice}
                            each with delta, ci_low, ci_high
    experiment.threshold_pct  — pre-registered effect-size threshold (pp)
    experiment.threshold_rule — human-readable rule for the figure caption
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt


PALETTE = {
    "ink": "#1F3A93",        # accent ink-blue
    "baseline": "#9A9A9A",   # neutral grey for baseline arm
    "win": "#2E7D32",        # passes all gates
    "loss": "#C62828",       # fails per-slice or threshold
    "near": "#C7892B",       # near-threshold / ambiguous
    "bg": "#FAFAF7",         # parchment off-white
    "grid": "#E2DFD6",       # subtle gridlines
    "text": "#222222",
    "muted": "#666666",
}


def apply_style() -> None:
    """Researcher-blog aesthetic: serif, off-white parchment, hairline grid."""
    mpl.rcParams.update(
        {
            "figure.facecolor": PALETTE["bg"],
            "axes.facecolor": PALETTE["bg"],
            "axes.edgecolor": PALETTE["text"],
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": PALETTE["grid"],
            "grid.linestyle": "-",
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "axes.labelcolor": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "text.color": PALETTE["text"],
            "font.family": "serif",
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlepad": 14,
            "figure.dpi": 140,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "savefig.facecolor": PALETTE["bg"],
        }
    )


def _arm_color(arm_id: str, baseline_id: str, verdict: dict) -> str:
    if arm_id == baseline_id:
        return PALETTE["baseline"]
    if arm_id == verdict.get("winner"):
        return PALETTE["win"]
    if arm_id in verdict.get("killed", []):
        return PALETTE["loss"]
    return PALETTE["ink"]


def _baseline_id(data: dict) -> str:
    return data["arms"][0]["id"]


# ---------- Chart 1: Arm bar with variance error bars ------------------------


def cmd_arm_bar(data: dict, out: Path) -> None:
    arms = data["arms"]
    trials = data["variance_trials"]
    agg = data["test_set_aggregate"]
    verdict = data.get("verdict", {})
    baseline_id = _baseline_id(data)
    baseline_score = agg[baseline_id]
    threshold_pp = data["experiment"]["threshold_pct"] / 100.0

    names = [a["name"] for a in arms]
    means = [agg[a["id"]] for a in arms]
    stds = [statistics.stdev(trials[a["id"]]) for a in arms]
    colors = [_arm_color(a["id"], baseline_id, verdict) for a in arms]

    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    x = list(range(len(arms)))
    bars = ax.bar(x, means, yerr=stds, capsize=7, color=colors, edgecolor="none", width=0.55)
    for b in bars:
        b.set_alpha(0.92)

    # threshold band: baseline + 5pp horizontal dashed line. Anchor the label
    # in the top-left empty region (above the baseline bar) so it never sits
    # behind the right-most arm bar.
    threshold_y = baseline_score + threshold_pp
    ax.axhline(threshold_y, color=PALETTE["muted"], linestyle="--", linewidth=1.0, zorder=1)
    ax.text(
        -0.35,
        threshold_y + 0.012,
        f"pre-registered threshold  (+{threshold_pp*100:.0f}pp over baseline)",
        ha="left",
        va="bottom",
        fontsize=9,
        color=PALETTE["muted"],
        style="italic",
    )

    # delta annotation above non-baseline bars
    for i, a in enumerate(arms):
        if a["id"] == baseline_id:
            continue
        delta_pp = (means[i] - baseline_score) * 100
        ax.text(
            i,
            means[i] + stds[i] + 0.012,
            f"+{delta_pp:.1f}pp",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color=colors[i],
        )

    ax.set_xticks(x)
    # Wrap long arm names on " (+ " or " (" so they don't collide on the x axis.
    wrapped = [n.replace(" (+ ", "\n(+ ").replace(" (", "\n(", 1) for n in names]
    ax.set_xticklabels(wrapped, fontsize=10)
    ax.set_ylabel("Accuracy on held-out test set")
    ax.set_ylim(0, max(means) + max(stds) + 0.14)
    ax.set_title("Phase 3: arm comparison (mean ± std across 3 trials)", loc="left")

    fig.text(
        0.01,
        -0.02,
        "Bars: aggregate accuracy on the held-out test set. Error bars: std across 3 same-prompt trials.",
        fontsize=8.5,
        style="italic",
        color=PALETTE["muted"],
    )

    fig.savefig(out)
    plt.close(fig)


# ---------- Chart 2: Forest plot + per-slice break-down ----------------------


def cmd_forest(data: dict, out: Path) -> None:
    arms = data["arms"]
    slices = data["slices"]
    effects = data["effect_sizes"]
    verdict = data.get("verdict", {})
    baseline_id = _baseline_id(data)
    non_baseline = [a for a in arms if a["id"] != baseline_id]
    threshold_pp = data["experiment"]["threshold_pct"] / 100.0
    loss_floor_pp = -0.02  # -2pp per-slice loss tolerance from threshold_rule

    # Each arm gets a 3-row block: aggregate, slice 1, slice 2 (top→bottom).
    rows_per_arm = 1 + len(slices)
    n_rows = len(non_baseline) * rows_per_arm + (len(non_baseline) - 1)  # 1-row gap between arms
    fig, ax = plt.subplots(figsize=(10.0, 0.55 * n_rows + 2.5))

    y_labels: list[str] = []
    y_pos: list[float] = []
    row_idx = 0

    for arm_n, arm in enumerate(non_baseline):
        if arm_n > 0:
            row_idx += 1  # gap row
        eff = effects[arm["id"]]
        color = _arm_color(arm["id"], baseline_id, verdict)

        # Aggregate row (bold)
        agg = eff["aggregate"]
        y = -row_idx
        ax.errorbar(
            agg["delta"],
            y,
            xerr=[[agg["delta"] - agg["ci_low"]], [agg["ci_high"] - agg["delta"]]],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=2.0,
            capsize=5,
            markersize=10,
        )
        ax.text(
            agg["ci_high"] + 0.005,
            y,
            f"  Δ={agg['delta']*100:+.1f}pp  CI [{agg['ci_low']*100:+.1f}, {agg['ci_high']*100:+.1f}]",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=color,
        )
        y_labels.append(f"{arm['name']}")
        y_pos.append(y)
        row_idx += 1

        # Per-slice rows (thinner, hollow markers)
        for sl in slices:
            ps = eff["per_slice"][sl["id"]]
            y = -row_idx
            slice_color = color if ps["ci_low"] > loss_floor_pp else PALETTE["loss"]
            ax.errorbar(
                ps["delta"],
                y,
                xerr=[[ps["delta"] - ps["ci_low"]], [ps["ci_high"] - ps["delta"]]],
                fmt="o",
                mfc="none",
                mec=slice_color,
                ecolor=slice_color,
                elinewidth=1.3,
                capsize=4,
                markersize=7,
                markeredgewidth=1.6,
            )
            fail_mark = ""
            if ps["ci_low"] <= loss_floor_pp:
                fail_mark = "   — fails per-slice rule"
            ax.text(
                ps["ci_high"] + 0.005,
                y,
                f"  Δ={ps['delta']*100:+.1f}pp  CI [{ps['ci_low']*100:+.1f}, {ps['ci_high']*100:+.1f}]{fail_mark}",
                va="center",
                fontsize=9,
                color=slice_color,
            )
            y_labels.append(f"    └ {sl['name']}")
            y_pos.append(y)
            row_idx += 1

    # Reference lines: zero (solid), aggregate threshold (dashed), per-slice
    # loss floor (dotted red). Anchor the labels to the TOP of the axes using a
    # blended transform — the rows live at negative y, so absolute data-y for
    # the labels would clip off the top of the plot.
    ax.axvline(0, color=PALETTE["text"], linewidth=0.7, linestyle="-", zorder=1)
    ax.axvline(threshold_pp, color=PALETTE["muted"], linewidth=1.0, linestyle="--", zorder=1)
    ax.axvline(loss_floor_pp, color=PALETTE["loss"], linewidth=0.9, linestyle=":", zorder=1, alpha=0.7)
    trans = mpl.transforms.blended_transform_factory(ax.transData, ax.transAxes)
    ax.text(threshold_pp, 0.985, f" +{threshold_pp*100:.0f}pp aggregate threshold",
            fontsize=8.5, color=PALETTE["muted"], style="italic",
            ha="left", va="top", transform=trans)
    ax.text(loss_floor_pp, 0.985, f"{loss_floor_pp*100:.0f}pp per-slice loss floor ",
            fontsize=8.5, color=PALETTE["loss"], style="italic",
            ha="right", va="top", transform=trans)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=10)
    ax.set_xlabel("Effect size (Δ accuracy vs baseline, percentage points)")
    # Right margin must accommodate the longest Δ annotation (~+25pp CI high +
    # 14 chars of text). Bump to +0.38 for safety.
    ax.set_xlim(loss_floor_pp - 0.04, max(0.38, threshold_pp + 0.05))
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v*100:+.0f}pp"))
    ax.set_title("Phase 5: effect-size forest plot, aggregate and per-slice", loc="left")

    fig.text(
        0.01,
        -0.01,
        "Filled markers: aggregate effect. Hollow markers: per-slice effect. Bars: 95% CI. "
        "An arm fails the verdict if any slice CI crosses the loss floor.",
        fontsize=8.5,
        style="italic",
        color=PALETTE["muted"],
    )

    fig.savefig(out)
    plt.close(fig)


# ---------- Chart 3: Cost-vs-accuracy Pareto ---------------------------------


def cmd_cost(data: dict, out: Path) -> None:
    arms = data["arms"]
    agg = data["test_set_aggregate"]
    verdict = data.get("verdict", {})
    baseline_id = _baseline_id(data)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    # Per-arm label offsets in DATA units. Hand-tuned so winner / loser pairs
    # that sit at nearly the same (cost, score) point don't overlap their text.
    # Winner → above-left and bold; loser → below-right; baseline → below.
    winner_id = verdict.get("winner")
    killed = set(verdict.get("killed", []))

    def _label_offset(arm_id: str) -> tuple[float, float, str, str]:
        # returns (dx, dy, ha, va)
        if arm_id == baseline_id:
            return (0.03, -0.025, "left", "top")
        if arm_id == winner_id:
            return (-0.04, 0.025, "right", "bottom")
        if arm_id in killed:
            return (0.04, -0.025, "left", "top")
        return (0.04, 0.020, "left", "bottom")

    for arm in arms:
        color = _arm_color(arm["id"], baseline_id, verdict)
        ax.scatter(
            arm["cost_per_1k_usd"],
            agg[arm["id"]],
            s=180,
            color=color,
            edgecolor="white",
            linewidth=2.0,
            zorder=3,
        )
        dx, dy, ha, va = _label_offset(arm["id"])
        ax.annotate(
            arm["name"],
            (arm["cost_per_1k_usd"], agg[arm["id"]]),
            xytext=(arm["cost_per_1k_usd"] + dx, agg[arm["id"]] + dy),
            fontsize=10,
            color=color,
            fontweight="bold" if arm["id"] == winner_id else "normal",
            ha=ha,
            va=va,
        )

    # Pareto frontier hint: from baseline up to winner
    winner_id = verdict.get("winner")
    if winner_id:
        b = next(a for a in arms if a["id"] == baseline_id)
        w = next(a for a in arms if a["id"] == winner_id)
        ax.annotate(
            "",
            xy=(w["cost_per_1k_usd"], agg[w["id"]]),
            xytext=(b["cost_per_1k_usd"], agg[b["id"]]),
            arrowprops=dict(arrowstyle="->", color=PALETTE["muted"], lw=1.0, ls="--"),
        )
        midx = (b["cost_per_1k_usd"] + w["cost_per_1k_usd"]) / 2
        midy = (agg[b["id"]] + agg[w["id"]]) / 2
        # Position slightly to the right of the dashed arrow line so the label
        # sits in clean whitespace.
        ax.text(midx + 0.10, midy - 0.005, "Pareto move",
                fontsize=9, color=PALETTE["muted"], style="italic", rotation=22)

    ax.set_xlabel("Cost per 1k rows (USD)")
    ax.set_ylabel("Accuracy on held-out test set")
    ax.set_title("Cost vs accuracy — Pareto view of all arms", loc="left")
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"${v:.2f}"))

    xs = [a["cost_per_1k_usd"] for a in arms]
    ys = [agg[a["id"]] for a in arms]
    ax.set_xlim(min(xs) - 0.2, max(xs) + 0.5)
    ax.set_ylim(min(ys) - 0.04, max(ys) + 0.06)

    fig.text(
        0.01,
        -0.02,
        "Each point: one arm. Green: ship. Red: kill (fails per-slice rule). Grey: baseline.",
        fontsize=8.5,
        style="italic",
        color=PALETTE["muted"],
    )

    fig.savefig(out)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("arm-bar", "forest-plot", "cost-vs-accuracy"):
        s = sub.add_parser(cmd)
        s.add_argument("--data", required=True, type=Path, help="path to data.json")
        s.add_argument("--out", required=True, type=Path, help="path to output PNG")
    args = ap.parse_args()

    data = json.loads(args.data.read_text())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    apply_style()

    handlers = {
        "arm-bar": cmd_arm_bar,
        "forest-plot": cmd_forest,
        "cost-vs-accuracy": cmd_cost,
    }
    handlers[args.cmd](data, args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
