<div align="center">

# 🧪 auto-lab

<p><em>Rigorous, anti-overfitting experiments for engineering decisions.</em></p>

<p>Prompt tuning · model selection · retrieval strategies · architecture comparisons.</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](./LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/clfhaha1234/auto-lab?style=flat-square)](https://github.com/clfhaha1234/auto-lab/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/clfhaha1234/auto-lab?style=flat-square)](https://github.com/clfhaha1234/auto-lab/network)
[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-D77757?style=flat-square)](https://docs.claude.com/en/docs/claude-code/skills)

</div>

## About

`auto-lab` is a Claude Code skill that turns "should we use X or Y?" engineering decisions into rigorous, anti-overfitting experiments. It encodes a six-phase scientific-method loop — **Frame → Source → Metric → Run → Diagnose → Conclude** — and surrounds it with twenty-two explicit guards against the exact rationalizations engineers use to leak data into their own conclusions. The skill ships with a matplotlib helper that renders three publication-quality figures from a single `data.json`, so every verdict comes with a Phase 3 arm-comparison, a Phase 5 effect-size forest plot with per-slice break-down, and a cost-vs-accuracy Pareto view. Use it when production data is the ground truth and a ship-or-kill decision is needed within a day.

## Key Features

**01. Held-out test discipline.** Test set sealed until Phase 5. Opened once.

**02. Pre-registered metric + threshold.** Locked in Phase 2. No post-hoc drift.

**03. Pilot N=1 instrumentation check.** Catches null / placeholder metric fields in 30 seconds, before a 5-minute full run wastes the iteration.

**04. Variance-floor noise check.** Effect must clear **2× within-arm std**, not just the registered threshold — a 5pp win with 4pp noise is noise.

**05. Three-iteration cap on dev refinement.** Past iter 3 you're overfitting to dev. Each iter changes ONE thing.

**06. Per-slice verification.** Aggregate winners that lose on a major tenant slice are not winners. Either ship narrowly, or kill.

**07. Publication-quality charts.** Three matplotlib figures auto-rendered from `data.json`: `arm-bar`, `forest-plot`, `cost-vs-accuracy`.

## Use Cases

**01.** Stress-testing a new prompt before promoting it to production.

**02.** Comparing model choices (Haiku vs Sonnet vs Opus) when cost and accuracy both matter.

**03.** Choosing between retrieval strategies (BM25 / vector / hybrid) on real customer queries.

**04.** Deciding between architectures (single-call vs two-call orchestration, sync vs queued).

**05.** Auditing eval methodology (same-family vs cross-family judge, locked vs free-form rubric).

## The Six Phases

```mermaid
flowchart LR
    F["Phase 0<br/>Frame"] --> S["Phase 1<br/>Source + Split"]
    S --> M["Phase 2<br/>Metric"]
    M --> R["Phase 3<br/>Run on dev"]
    R --> D["Phase 4<br/>Diagnose"]
    D -->|"≤3 iter<br/>ONE change per iter"| R
    D --> V["Phase 5<br/>Verdict on<br/>held-out test"]
    V --> C(["Conclusion doc<br/>+ charts"])
```

**01. Frame.** Write the question, hypothesis, baseline, arms, and stop conditions — on paper, before touching data.

**02. Source + Split.** Sample from production. Partition into ~30% train / ~50% dev / ~20% sealed test.

**03. Metric.** Pre-register the primary metric and effect-size threshold. Lock the LLM-judge rubric.

**04. Run.** Pilot N=1 first. Then full dev run with a variance baseline (≥3 trials) and a cross-judge sanity check on 5 dev rows.

**05. Diagnose.** Per-row diffs. ≤3 refinement iterations, each changing ONE thing.

**06. Verdict.** One pass on the held-out test set. Per-slice scores. Ship or kill — no re-runs.

## Example Output

A complete worked example lives at [`examples/prompt-tuning-classifier/`](./examples/prompt-tuning-classifier/) — three figures rendered from one `data.json`, telling one coherent teaching story.

![Phase 3 arm comparison with variance error bars](./examples/prompt-tuning-classifier/charts/arm-bar.png)

> **Phase 3** — both candidate arms beat baseline by +8.9pp, well above the 2× variance noise floor.

![Phase 5 effect-size forest plot, aggregate and per-slice](./examples/prompt-tuning-classifier/charts/forest-plot.png)

> **Phase 5** — both arms clear the aggregate threshold. But `v3` regresses SMB tenants by -3.3pp, crossing the pre-registered loss floor. **Aggregate winner ≠ winner.**

![Cost vs accuracy Pareto across all arms](./examples/prompt-tuning-classifier/charts/cost-vs-accuracy.png)

> **Cost view** — `v2` is the Pareto move: +8.9pp at +$0.60 / 1k rows. Ship `v2`. Kill `v3`.

## Rules

**Never peek at the test set.** A single peek contaminates the row and biases your judgment of every neighbor.

**One thing per iteration.** Change two variables at once and you can't attribute the win.

**Falsification is finished.** When iter 3 disproves the hypothesis, lock the arm and run the test pass. Trying iter 4 is overfitting to dev.

**Aggregate wins don't override per-slice losses.** Either ship narrowly to the slice that wins, or kill.

**Lock the latest hypothesis-driven iter, not the highest-scoring one.** Picking by dev score is multi-iteration multiple-comparison bias.

A sample of the twenty-two forbidden moves the skill blocks. Full set in [SKILL.md](./SKILL.md).

## Quick Start

```bash
git clone https://github.com/clfhaha1234/auto-lab.git ~/.claude/skills/auto-lab
```

Then ask Claude any "should we use X or Y?" question:

> *"Compare prompt-v1, v2, v3 on this classifier."*
> *"Is Haiku 4.5 enough here, or do we need Sonnet?"*
> *"BM25, vector, or hybrid retrieval for this RAG?"*

Render charts manually:

```bash
uv run scripts/chart.py arm-bar          --data data.json --out charts/arm-bar.png
uv run scripts/chart.py forest-plot      --data data.json --out charts/forest-plot.png
uv run scripts/chart.py cost-vs-accuracy --data data.json --out charts/cost-vs-accuracy.png
```

PEP 723 inline deps — `uv run` provisions matplotlib automatically. `python3 scripts/chart.py …` also works.

## FAQ

**What is the auto-lab skill for Claude Code?**
A planning + execution capability that runs rigorous, anti-overfitting experiments for "should we use X or Y?" engineering decisions. Six phases, twenty-two forbidden moves, three publication-quality charts.

**Does auto-lab work with non-Claude models?**
Yes. The skill is model-agnostic — it tells Claude Code what discipline to enforce, but the arms you compare can be any models, any providers, any prompt / retrieval / architecture variants.

**Why three iterations max?**
Past iter 3 on the dev set, each "refinement" is overfitting to dev rather than finding signal. Empirically, iters 1-2 surface real bugs in the arm; iter 3 is hypothesis-driven; iter 4+ is metric-chasing.

**How is this different from a Jupyter notebook with matplotlib?**
A notebook lets you do anything. `auto-lab` forbids the specific things that look reasonable but contaminate your conclusion — peeking at test, picking best-of-N on test, moving the metric after the score, dropping rows that score badly. The discipline is the value; the charts are a side effect.

**Can I use this on experiments I've already run?**
Use it on the *next* decision. For already-run experiments where the test set was peeked at during debugging, the test set is contaminated for that question — reseal from fresh production data before running `auto-lab` on it.

**Does the chart helper require Python?**
Yes. `scripts/chart.py` uses matplotlib via a PEP 723 inline-deps header — `uv run` provisions an isolated env automatically; `python3` works as fallback if matplotlib is already installed. The skill itself (the discipline + conclusion doc) works without Python.

## Contributing

Issues and PRs welcome. The highest-value contribution is a new entry to the *Common Rationalizations* table in [SKILL.md](./SKILL.md) from a real experience.

## License

[MIT](./LICENSE)
