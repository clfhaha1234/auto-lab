#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.8",
# ]
# ///
"""Render the auto-itera autonomous-loop diagram for the README.

A two-lane swim diagram:
  Top lane    — what YOU provide (goal, candidates, threshold)
  Bottom lane — what auto-itera does autonomously (source -> score -> diagnose
                -> sprint+gate loop -> verdict -> conclusion doc + charts)

Usage:
    uv run scripts/render-loop-diagram.py --out docs/images/autonomous-loop.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


# Color palette — keep consistent with the project's existing charts.
COLOR_USER_FILL = "#FDEED9"      # warm sand — "you provide"
COLOR_USER_EDGE = "#C78A3A"
COLOR_AUTO_FILL = "#E3EEFB"      # cool blue — "auto-itera runs"
COLOR_AUTO_EDGE = "#3266A8"
COLOR_GATE_FILL = "#F6E0E0"      # pale rose — the discipline gates
COLOR_GATE_EDGE = "#B33A3A"
COLOR_TEXT = "#1B1B1B"
COLOR_ARROW = "#444444"


def add_box(ax, x, y, w, h, label, sub=None, *, fill, edge):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        facecolor=fill,
        edgecolor=edge,
        linewidth=1.4,
    )
    ax.add_patch(box)
    cx, cy = x + w / 2, y + h / 2
    if sub:
        ax.text(cx, cy + 0.10, label, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color=COLOR_TEXT)
        ax.text(cx, cy - 0.18, sub, ha="center", va="center",
                fontsize=8.5, color=COLOR_TEXT, style="italic")
    else:
        ax.text(cx, cy, label, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color=COLOR_TEXT)


def arrow(ax, x0, y0, x1, y1, *, style="->", connection="arc3,rad=0",
          color=COLOR_ARROW, lw=1.4):
    a = FancyArrowPatch(
        (x0, y0),
        (x1, y1),
        arrowstyle=style,
        connectionstyle=connection,
        color=color,
        linewidth=lw,
        mutation_scale=14,
    )
    ax.add_patch(a)


def render(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 5.8), dpi=170)

    # ---- frame ----
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.2)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- lane labels on the left ----
    ax.text(0.15, 5.10, "YOU\nPROVIDE",
            ha="left", va="center", fontsize=9.5, fontweight="bold",
            color=COLOR_USER_EDGE, linespacing=1.1)
    ax.text(0.15, 2.30, "auto-itera\nRUNS",
            ha="left", va="center", fontsize=9.5, fontweight="bold",
            color=COLOR_AUTO_EDGE, linespacing=1.1)

    # ---- TOP LANE: 3 user-provided inputs ----
    user_y = 4.6
    user_w, user_h = 2.7, 1.0

    add_box(ax, 1.6,  user_y, user_w, user_h,
            "1. Goal", sub="the question to answer",
            fill=COLOR_USER_FILL, edge=COLOR_USER_EDGE)
    add_box(ax, 5.15, user_y, user_w, user_h,
            "2. Candidates", sub="prompts / models / strategies",
            fill=COLOR_USER_FILL, edge=COLOR_USER_EDGE)
    add_box(ax, 8.7,  user_y, user_w, user_h,
            "3. Threshold", sub="effect size + stop rule",
            fill=COLOR_USER_FILL, edge=COLOR_USER_EDGE)

    # Down arrows from each user box into the auto lane
    for x_center in (1.6 + user_w / 2, 5.15 + user_w / 2, 8.7 + user_w / 2):
        arrow(ax, x_center, user_y, x_center, 3.55, lw=1.2)

    # ---- divider line ----
    ax.plot([1.3, 12.7], [4.1, 4.1], color="#BFBFBF",
            linewidth=0.8, linestyle=(0, (4, 3)))
    ax.plot([1.3, 12.7], [0.55, 0.55], color="#BFBFBF",
            linewidth=0.4, linestyle=(0, (2, 4)))

    # ---- BOTTOM LANE: 5 autonomous steps ----
    auto_y = 2.05
    auto_w, auto_h = 1.95, 1.0

    steps = [
        (1.30, "4. Source",       "real prod data\nsplit train/dev/test"),
        (3.55, "5. Score",        "baseline + every arm\nparallel, variance-floored"),
        (5.80, "6. Diagnose",     "per-row diffs\nhypothesis-driven sprint"),
        (8.05, "7. Iterate",      "≤3 iter / sprint\nthen generalization gate"),
        (10.30, "8. Verdict",     "ONE pass on sealed\ntest set — ship or kill"),
    ]

    centers = []
    for x, label, sub in steps:
        add_box(ax, x, auto_y, auto_w, auto_h, label, sub=sub,
                fill=COLOR_AUTO_FILL, edge=COLOR_AUTO_EDGE)
        centers.append(x + auto_w / 2)

    # Forward arrows between autonomous steps
    for i in range(len(centers) - 1):
        x0 = steps[i][0] + auto_w
        x1 = steps[i + 1][0]
        arrow(ax, x0 + 0.02, auto_y + auto_h / 2,
              x1 - 0.02, auto_y + auto_h / 2, lw=1.5)

    # Sprint loopback arrow: Iterate -> Diagnose (curving below)
    arrow(ax, centers[3], auto_y,
          centers[2], auto_y,
          connection="arc3,rad=0.55", lw=1.3,
          color=COLOR_AUTO_EDGE)
    ax.text((centers[2] + centers[3]) / 2, auto_y - 0.95,
            "sprint loop (≤3 iter, then gate)",
            ha="center", va="center", fontsize=8, style="italic",
            color=COLOR_AUTO_EDGE)

    # ---- Final output ----
    add_box(ax, 10.15, 0.05, 2.3, 0.4,
            "conclusion doc + charts",
            fill="#FFFFFF", edge=COLOR_AUTO_EDGE)
    arrow(ax, centers[4], auto_y,
          centers[4], 0.46, lw=1.3, color=COLOR_AUTO_EDGE)

    # ---- Legend ----
    legend_handles = [
        mpatches.Patch(facecolor=COLOR_USER_FILL,
                       edgecolor=COLOR_USER_EDGE,
                       label="You provide — 3 inputs"),
        mpatches.Patch(facecolor=COLOR_AUTO_FILL,
                       edgecolor=COLOR_AUTO_EDGE,
                       label="auto-itera runs autonomously — 5 stages"),
    ]
    ax.legend(handles=legend_handles, loc="upper right",
              bbox_to_anchor=(0.985, 0.99), frameon=False,
              fontsize=8.5)

    # ---- Title ----
    fig.suptitle("auto-itera — autonomous experimentation loop",
                 fontsize=13, fontweight="bold", color=COLOR_TEXT,
                 y=0.965)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=170, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"wrote {out_path}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path,
                   default=Path("docs/images/autonomous-loop.png"))
    args = p.parse_args()
    render(args.out)


if __name__ == "__main__":
    main()
