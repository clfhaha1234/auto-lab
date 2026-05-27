<div align="center">

![auto-itera banner](./docs/images/banner.png)

# 🧪 auto-itera

<p><strong>Autonomous experimentation engine for AI engineering decisions.</strong></p>

<p><em>Define a goal. Give it the candidates. Get back a defensible ship-or-kill verdict in hours — sourced from real production data, scored across arms in parallel, sprint-iterated with discipline, and signed off on a sealed test set.</em></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](./LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/clfhaha1234/auto-itera?style=flat-square)](https://github.com/clfhaha1234/auto-itera/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/clfhaha1234/auto-itera?style=flat-square)](https://github.com/clfhaha1234/auto-itera/network)
[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-D77757?style=flat-square)](https://docs.claude.com/en/docs/claude-code/skills)

</div>

## From handcrafted trial-and-error to autonomous scientific search

Every team shipping an LLM product has decisions like these on the table:

- **Prompt optimization** — does the new system prompt actually beat the current one?
- **Model selection** — Sonnet, Haiku, or Opus for this hop?
- **Retrieval strategies** — BM25, dense, or hybrid on real customer queries?
- **Workflow tuning** — single-call vs two-call orchestration; sync vs queued?
- **Architecture experiments** — does adding a router LLM help or just add latency?

Today most teams answer these with vibes, eyeballed diffs, or notebooks they've quietly tuned the system against. `auto-itera` automates the rigorous version of this work: you state the goal, hand over the candidates, and the loop runs to a verdict you can defend in a code review.

## The loop

![auto-itera autonomous experimentation loop — two lanes: you provide 3 inputs, auto-itera autonomously runs 5 stages](./docs/images/autonomous-loop.png)

**You provide (3 inputs):**

1. **Goal** — the question you want answered ("does prompt-v2 beat v1 on classification?")
2. **Candidates** — the concrete arms to compare (a baseline + 1–3 alternatives)
3. **Threshold** — pre-registered effect size + per-slice loss floor ("ship if ≥5pp aggregate AND no slice regresses >2pp")

**`auto-itera` runs (5 autonomous stages):**

4. **Source** — sample real production data, stratify by tenant/class, split into train / dev / sealed test
5. **Score** — run baseline + every arm in parallel on dev, with variance baseline (≥3 trials) + cross-judge sanity check
6. **Diagnose** — per-row diffs against baseline, identify wins/losses by cluster, write a hypothesis for the next change
7. **Iterate** — sprint of up to 3 hypothesis-driven iterations, then a **generalization gate** that strips out dev-set memorization. Continue or lock.
8. **Verdict** — ONE pass on the sealed test set. Per-slice scores. Ship / scope narrowly / kill — with a conclusion doc and three publication-quality charts.

The output: a one-page conclusion doc embedding `arm-bar`, `forest-plot`, and `cost-vs-accuracy` figures, plus a discipline self-audit checklist. Code is throw-away; the conclusion is what compounds.

## Honest expectation boundary

> `auto-itera` automates everything *between* candidates-and-criterion and verdict. It does NOT autonomously brainstorm what to test.

You — or Claude, if you ask it — still write the candidate prompts, pick the model versions to compare, and define the success threshold. `auto-itera` then takes that search space and runs the experiment to a defensible result. Think of it as **an autonomous experiment runner, not an autonomous AI scientist that invents hypotheses from scratch**.

This boundary is what keeps the verdict trustworthy: the human commits to a falsifiable hypothesis upfront, and the loop is honest about whether the evidence supports it.

## Why a sprint-and-generalize loop

The most interesting design choice is in stage 7. Naive "iterate until it looks better" optimizes the dev set — every refinement that doesn't survive the held-out test is overfitting in a lab coat. A flat "stop after 3 iterations" rule prevents that, but it also blocks legitimate deeper exploration.

`auto-itera` splits the difference:

```
iterate × up to 3
   ↓
generalization gate
   ↓
   ├──  every change is a universal mechanism (or got promoted to one) → start next sprint
   ├──  dev signal saturated → lock and run the test pass
   └──  changes were mostly "if input X return Y" hardcodes → kill this arm
```

The 3 inside a sprint is a working-memory cap (humans can't reliably attribute outcomes across more than ~3 simultaneous hypothesis edits). The gate between sprints separates **principled iteration** (finding deeper mechanisms) from **dev-set memorization** (adding rules that win specific rows but won't survive the test).

Most decisions converge in 1–2 sprints. Past 3 sprints, the prior shifts toward "the gate is failing to catch dev-memorization" — the right move is to audit the gate, not to keep iterating.

## Safeguards — the 22 ways auto-itera refuses to lie to you

Autonomy without honesty is a worse outcome than vibes-based evals — at least vibes don't pretend to be science. `auto-itera` ships with 22 explicit safeguards that block the specific moves that look reasonable but contaminate the verdict.

Five real failure modes, drawn from actual shipped-and-regressed AI products:

| What the team would have shipped | What `auto-itera` caught |
|---|---|
| *"Prompt v3 is +12% on eval. Ship it."* | The "improvement" came from rows the engineer read during debugging. Test set was contaminated. Production regressed 8%. |
| *"GPT-4o beat Claude on our 50-row eval."* | Eval too small. Gap was 5pp, within-arm noise was 4pp. Not a real signal. |
| *"Aggregate accuracy up 6pp across all customers."* | One major tenant slice regressed -8pp. Aggregate winners are not winners when a major slice loses. |
| *"Best-of-5 trial: 91% accuracy."* | Mean was 84% ± 4pp. Best-of-N is biased high by ~√log N. |
| *"New rubric finally captures what matters."* | Rubric was rewritten *after* seeing scores. It happened to favor the arm they wanted to win. |

Each one is a specific anti-pattern with a specific safeguard. Other guards include held-out test sealing, pre-registered metrics, variance-floor noise checks, the generalization gate, cross-judge sanity checks, and a per-slice loss floor. The full list — plus a "Common Rationalizations" table cataloging the excuses engineers reach for in the moment — lives in [SKILL.md](./SKILL.md).

## Example output

A complete worked example lives at [`examples/prompt-tuning-classifier/`](./examples/prompt-tuning-classifier/) — three figures rendered from one `data.json`, telling one coherent teaching story.

![Phase 3 arm comparison with variance error bars](./examples/prompt-tuning-classifier/charts/arm-bar.png)

> **Stage 5** — both candidate arms beat baseline by +8.9pp, well above the 2× variance noise floor.

![Phase 5 effect-size forest plot, aggregate and per-slice](./examples/prompt-tuning-classifier/charts/forest-plot.png)

> **Stage 8** — both arms clear the aggregate threshold. But `v3` regresses SMB tenants by -3.3pp, crossing the pre-registered loss floor. **Aggregate winner ≠ winner.**

![Cost vs accuracy Pareto across all arms](./examples/prompt-tuning-classifier/charts/cost-vs-accuracy.png)

> **Cost view** — `v2` is the Pareto move: +8.9pp at +$0.60 / 1k rows. Ship `v2`. Kill `v3`.

## Who this is for

Teams **shipping LLM products** who need decisions that survive production:

- Choosing between models when cost and accuracy both matter
- Validating a prompt change actually helps before deploying it
- Comparing retrieval strategies on real customer queries
- Auditing whether your eval methodology is biased

If you're a solo dev experimenting in a notebook, you can skip this. If you have customers depending on whether your AI decisions are right, you can't.

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

Re-render the loop diagram (if you fork and want a customized version):

```bash
uv run scripts/render-loop-diagram.py --out docs/images/autonomous-loop.png
```

PEP 723 inline deps — `uv run` provisions matplotlib automatically. `python3 scripts/*.py …` also works if matplotlib is already installed.

## FAQ

**What is `auto-itera` actually doing?**
Running the experimental discipline that AI teams know they should follow but skip because it's tedious. You hand it a goal + candidate arms + success threshold; it sources real production data, scores baseline + arms in parallel, diagnoses per-row, sprints with a generalization gate between rounds, picks the latest gate-passed iter, and runs the held-out test pass. The 22 safeguards make the discipline mechanical; the charts are a side effect; the verdict is the product.

**Why "autonomous experimentation" and not "AI scientist"?**
Because the skill autonomously runs experiments — it does not autonomously invent hypotheses or brainstorm what to test. The human (or Claude in conversation with the human) supplies the candidate arms; `auto-itera` runs the loop from there to verdict. Calling it an "AI scientist" would oversell what it does and undersell what it does well: turning a vague "should we use X or Y?" question into a defensible verdict in hours.

**Does this work with non-Claude models?**
Yes. The skill is model-agnostic — it tells Claude Code what discipline to enforce, but the arms you compare can be any models, any providers, any prompt / retrieval / architecture variants.

**Why a 3-iteration sprint cap, not a hard "stop at 3" rule?**
3 is a working-memory cap — humans can't reliably attribute outcomes across more than ~3 simultaneous hypothesis edits inside a single sprint. But iteration itself isn't the enemy; *un-audited* iteration is. After each sprint, the generalization gate strips out dev-set memorization. If the gate passes and dev signal isn't saturated, you start a fresh sprint. Most decisions converge in 1–2 sprints. Past 3 sprints, the prior shifts toward "the gate is failing to catch dev-memorization" — and the right move is to audit the gate, not to keep iterating.

**How is this different from a Jupyter notebook with matplotlib?**
A notebook lets you do anything — including all the things that quietly bias your conclusion. `auto-itera` makes the discipline mechanical: forbids peeking at test, forbids picking best-of-N on test, forbids moving the metric after the score, forbids skipping the generalization gate between sprints. The discipline is what you can't get from a notebook.

**Can I use this on experiments I've already run?**
Use it on the *next* decision. For already-run experiments where the test set was peeked at during debugging, the test set is contaminated for that question — reseal from fresh production data before running `auto-itera` on it.

**Does the chart helper require Python?**
Yes. `scripts/chart.py` and `scripts/render-loop-diagram.py` use matplotlib via a PEP 723 inline-deps header — `uv run` provisions an isolated env automatically; `python3` works as fallback if matplotlib is already installed. The skill itself (the discipline + conclusion doc) works without Python.

## Contributing

Issues and PRs welcome. The highest-value contribution is a new entry to the *Common Rationalizations* table in [SKILL.md](./SKILL.md) from a real experience — the kind that ends *"…and we shipped it, and then production regressed."* Those are the stories the skill exists to prevent.

## License

[MIT](./LICENSE)
