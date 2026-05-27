<div align="center">

![auto-itera banner](./docs/images/banner.png)

# 🧪 auto-itera

<p><strong>The scientific method for AI engineering decisions.</strong></p>

<p><em>Set a goal. Define candidate approaches. Run a rigorous experiment. Get a ship-or-kill verdict in hours — with statistical confidence and built-in honesty checks.</em></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](./LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/clfhaha1234/auto-itera?style=flat-square)](https://github.com/clfhaha1234/auto-itera/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/clfhaha1234/auto-itera?style=flat-square)](https://github.com/clfhaha1234/auto-itera/network)
[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-D77757?style=flat-square)](https://docs.claude.com/en/docs/claude-code/skills)

</div>

## What it does

Every team shipping an LLM product has decisions like these on the table:

- Should we switch from Sonnet to Opus?
- Is RAG actually helping, or just adding latency?
- Did that prompt tuning round move the needle?
- Which of these three retrieval strategies wins on real customer queries?

`auto-itera` turns each of these into a **rigorous experiment** that returns a defensible verdict in hours:

1. **Frame** the question + competing arms + pre-registered success threshold.
2. **Source** real production data; split into train / dev / sealed test.
3. **Run** baseline + arms in parallel; measure aggregate, per-slice, variance, and cost.
4. **Iterate** in disciplined 3-iteration sprints, each followed by a generalization gate that strips out dev-set memorization before the next sprint.
5. **Verdict** on the held-out test set — one pass, no re-runs. Ship the winner, scope it to the slice that wins, or kill.

The output is a **one-page conclusion doc** with three publication-quality figures (`arm-bar`, `forest-plot`, `cost-vs-accuracy`) that anyone — your team, a CTO, a future-you in 3 months — can audit.

## The six phases

![The Six Phases of a Rigorous Experiment](./docs/images/six-phases.png)

**01. Frame.** Write the question, hypothesis, baseline, arms, and stop conditions — on paper, before touching data.

**02. Source + Split.** Sample from production. Partition into ~30% train / ~50% dev / ~20% sealed test.

**03. Metric.** Pre-register the primary metric and effect-size threshold. Lock the LLM-judge rubric.

**04. Run.** Pilot N=1 first. Then full dev run with a variance baseline (≥3 trials) and a cross-judge sanity check on 5 dev rows.

**05. Diagnose.** Per-row diffs. Sprint up to 3 iterations, each changing ONE thing. Run the generalization gate. Continue or lock.

**06. Verdict.** One pass on the held-out test set. Per-slice scores. Ship or kill — no re-runs.

## The sprint-and-generalize loop

The core of Phase 5 — and the thing most "vibes-based eval" workflows skip:

```
iterate × up to 3
   ↓
generalization gate
   ↓
   ├──  every change is a universal mechanism (or got promoted to one) → start next sprint
   ├──  dev signal saturated → lock and run Phase 6 verdict
   └──  changes were mostly "if input X return Y" hardcodes → kill this arm
```

The 3 inside a sprint is a working-memory cap (humans can't reliably attribute outcomes across more than ~3 simultaneous hypothesis edits). The gate between sprints is what separates **principled iteration** (finding deeper mechanisms) from **dev-set memorization** (adding rules that win specific rows but won't survive Phase 6).

Most decisions converge in 1–2 sprints. Past 3 sprints, the prior shifts strongly to "the gate is failing to catch dev-memorization" — the rule isn't "stop iterating," it's "audit the gate harder before continuing."

## What it guards against

Five real failure modes drawn from actual shipped-and-regressed AI products. The framework's 22 explicit guards exist because each of these has happened, repeatedly:

| What the team would have shipped | What `auto-itera` caught |
|---|---|
| *"Prompt v3 is +12% on eval. Ship it."* | The "improvement" came from rows the engineer read during debugging. Test set was contaminated. Production regressed 8%. |
| *"GPT-4o beat Claude on our 50-row eval."* | Eval too small. Gap was 5pp, within-arm noise was 4pp. Not a real signal. |
| *"Aggregate accuracy up 6pp across all customers."* | One major tenant slice regressed -8pp. Aggregate winners are not winners when a major slice loses. |
| *"Best-of-5 trial: 91% accuracy."* | Mean was 84% ± 4pp. Best-of-N is biased high by ~√log N. |
| *"New rubric finally captures what matters."* | Rubric was rewritten *after* seeing scores. It happened to favor the arm they wanted to win. |

Each one is a specific anti-pattern with a specific safeguard. There are **22 in total**, plus a "Common Rationalizations" table cataloging the excuses engineers reach for in the moment. Both lists live in [SKILL.md](./SKILL.md).

## Who this is for

Teams **shipping LLM products** who need to make decisions that affect production:

- Choosing between models when cost and accuracy both matter
- Validating a prompt change actually helps before deploying it
- Comparing retrieval strategies on real customer queries
- Auditing whether your eval methodology is biased

If you're a solo dev experimenting in a notebook, you can skip this. If you have customers depending on whether your AI decisions are right, you can't.

## Example output

A complete worked example lives at [`examples/prompt-tuning-classifier/`](./examples/prompt-tuning-classifier/) — three figures rendered from one `data.json`, telling one coherent teaching story.

![Phase 3 arm comparison with variance error bars](./examples/prompt-tuning-classifier/charts/arm-bar.png)

> **Phase 3** — both candidate arms beat baseline by +8.9pp, well above the 2× variance noise floor.

![Phase 5 effect-size forest plot, aggregate and per-slice](./examples/prompt-tuning-classifier/charts/forest-plot.png)

> **Phase 5** — both arms clear the aggregate threshold. But `v3` regresses SMB tenants by -3.3pp, crossing the pre-registered loss floor. **Aggregate winner ≠ winner.**

![Cost vs accuracy Pareto across all arms](./examples/prompt-tuning-classifier/charts/cost-vs-accuracy.png)

> **Cost view** — `v2` is the Pareto move: +8.9pp at +$0.60 / 1k rows. Ship `v2`. Kill `v3`.

Every experiment ends with a one-page conclusion doc embedding these three charts and a discipline self-audit checklist. Code is throw-away; the conclusion is what compounds.

## The hard rules

**Never peek at the test set.** A single peek contaminates the row and biases your judgment of every neighbor.

**One thing per iteration.** Change two variables at once and you can't attribute the win.

**Falsification is a finished iteration, not a "try harder" signal.** When iter 3 of a sprint disproves the hypothesis, run the gate, then decide whether to start a new sprint with a fresh hypothesis or lock and run Phase 6.

**Aggregate wins don't override per-slice losses.** Either ship narrowly to the slice that wins, or kill.

**Lock the latest gate-passed iter, not the highest-scoring one.** Picking by dev score is multi-iteration multiple-comparison bias.

These are a sample of the 22 forbidden moves the skill blocks. Full set in [SKILL.md](./SKILL.md).

## Quick Start

```bash
git clone https://github.com/clfhaha1234/auto-itera.git ~/.claude/skills/auto-itera
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

**What is `auto-itera` actually doing?**
Running the experimental discipline that AI teams know they should follow but skip because it's tedious. Pre-register the metric. Hold the test set sealed. Iterate in disciplined sprints. Strip out dev-set memorization between sprints via the generalization gate. Pick the latest gate-passed iter, not the highest-scoring one. Ship by the held-out test, not the dev set. The 22 guards make the discipline mechanical; the charts are a side effect.

**Does this work with non-Claude models?**
Yes. The skill is model-agnostic — it tells Claude Code what discipline to enforce, but the arms you compare can be any models, any providers, any prompt / retrieval / architecture variants.

**Why a 3-iteration sprint cap, not a hard "stop at 3" rule?**
3 is a working-memory cap — humans can't reliably attribute outcomes across more than ~3 simultaneous hypothesis edits inside a single sprint. But iteration itself isn't the enemy; *un-audited* iteration is. After each sprint, the generalization gate strips out dev-set memorization (any `if input X return Y` rule that wins specific rows but isn't a real mechanism). If the gate passes and dev signal isn't saturated, you start a fresh sprint. Most decisions converge in 1–2 sprints. Past 3 sprints, the prior shifts strongly toward "the gate is failing to catch dev-memorization" — and the right move is to audit the gate, not to keep iterating.

**How is this different from a Jupyter notebook with matplotlib?**
A notebook lets you do anything — including all the things that quietly bias your conclusion. `auto-itera` makes the discipline mechanical: forbids peeking at test, forbids picking best-of-N on test, forbids moving the metric after the score, forbids skipping the generalization gate between sprints. The discipline is what you can't get from a notebook.

**Can I use this on experiments I've already run?**
Use it on the *next* decision. For already-run experiments where the test set was peeked at during debugging, the test set is contaminated for that question — reseal from fresh production data before running `auto-itera` on it.

**Does the chart helper require Python?**
Yes. `scripts/chart.py` uses matplotlib via a PEP 723 inline-deps header — `uv run` provisions an isolated env automatically; `python3` works as fallback if matplotlib is already installed. The skill itself (the discipline + conclusion doc) works without Python.

## Contributing

Issues and PRs welcome. The highest-value contribution is a new entry to the *Common Rationalizations* table in [SKILL.md](./SKILL.md) from a real experience — the kind that ends *"…and we shipped it, and then production regressed."* Those are the stories the skill exists to prevent.

## License

[MIT](./LICENSE)
