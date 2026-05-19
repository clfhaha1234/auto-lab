<div align="center">

# 🧪 auto-lab

<p><em>Rigorous, anti-overfitting experiments for engineering decisions — applied to prompt tuning, model selection, retrieval strategies, and architecture comparisons.</em></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](./LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/clfhaha1234/auto-lab?style=flat-square)](https://github.com/clfhaha1234/auto-lab/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/clfhaha1234/auto-lab?style=flat-square)](https://github.com/clfhaha1234/auto-lab/network)
[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-D77757?style=flat-square)](https://docs.claude.com/en/docs/claude-code/skills)

</div>

## ⚡ Why

Most engineering "experiments" leak. You peek at the test set to debug. You pick best-of-N on the same set you'll report from. You tune prompts on the rows the LLM got wrong. You move the metric after seeing the score. Each move is reasonable in the moment — and together they make the conclusion look like science while generalizing worse than a coin flip.

`auto-lab` is the discipline that closes those leaks: **scientific method applied to fast-moving AI engineering decisions**.

## 🔄 How it works

A six-phase loop: **Frame → Source → Metric → Run → Diagnose → Conclude**.

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

The discipline that ships with it:

- **Held-out test set, sealed until the final pass** — one open, one verdict.
- **Pre-registered metric + effect-size threshold** — no post-hoc moves.
- **Pilot N=1 before any full run** — catches instrumentation bugs in 30 seconds.
- **Variance baseline before celebrating any gap** — a 5pp win with 4pp noise is noise.
- **3-iteration cap on dev refinement** — past that you're overfitting to dev.
- **Per-slice verification, not just aggregate** — aggregate winners that lose on major slices are not winners.

## 📊 Example output

A complete worked example lives at [`examples/prompt-tuning-classifier/`](./examples/prompt-tuning-classifier/) — three publication-quality figures rendered from a single `data.json`. The example tells one coherent teaching story (see the conclusion doc for the full write-up):

**Phase 3 — arm comparison.** Three arms ran on the dev set; baseline at 61.7%, both candidate arms at ~70.6% (+8.9pp). Within-arm std is ~1.4pp across 3 trials, so the effect clears the 2× variance noise floor.

![Phase 3 arm comparison with variance error bars](./examples/prompt-tuning-classifier/charts/arm-bar.png)

**Phase 5 — verdict (the per-slice gotcha).** On the held-out test set, both `prompt-v2` and `prompt-v3` pass the pre-registered aggregate threshold (+8.9pp, CI lower bound +5.0pp). But the per-slice forest plot reveals the trap: `prompt-v3` regresses SMB tenants by -3.3pp (CI `[-8.8, +2.2]`), crossing the pre-registered -2pp loss floor. **Aggregate winner, per-slice loser.** Without the per-slice rule pre-registered in Phase 0, we'd have shipped `v3` and quietly hurt every SMB customer.

![Phase 5 effect-size forest plot, aggregate and per-slice](./examples/prompt-tuning-classifier/charts/forest-plot.png)

**Cost view.** `prompt-v2` is the Pareto move: +8.9pp aggregate accuracy at +$0.60 / 1k rows. `prompt-v3` adds +$0.10 more for zero aggregate gain and a per-slice regression.

![Cost vs accuracy Pareto](./examples/prompt-tuning-classifier/charts/cost-vs-accuracy.png)

Verdict: ship `prompt-v2`. Kill `prompt-v3`. Follow-up question (a separate Phase 0): can amount-direction hints be made slice-conditional?

## 🚀 Quick start

```bash
# Install (Claude Code)
git clone https://github.com/clfhaha1234/auto-lab.git ~/.claude/skills/auto-lab
```

Then, in any conversation:

> "Let's compare prompt-v1, prompt-v2, and prompt-v3 on this classifier."
> "Is Haiku 4.5 good enough here, or do we need Sonnet?"
> "Should we use BM25, vector, or hybrid retrieval for this RAG?"

Claude will walk through Phase 0 (frame the question on paper), sample data, lock the metric, pilot N=1, run dev, diagnose, and produce a conclusion doc with all three charts auto-rendered from `data.json` via `scripts/chart.py`.

### Render charts manually

```bash
uv run scripts/chart.py arm-bar          --data data.json --out charts/arm-bar.png
uv run scripts/chart.py forest-plot      --data data.json --out charts/forest-plot.png
uv run scripts/chart.py cost-vs-accuracy --data data.json --out charts/cost-vs-accuracy.png
```

PEP 723 inline dependencies — `uv run` provisions matplotlib automatically. `python3 scripts/chart.py ...` also works if matplotlib is installed.

## 🧠 What it enforces

The skill encodes 22 rationalizations engineers use to leak data into their conclusions, with explicit counters. A sample of forbidden moves:

| Anti-pattern | Why it's bad | What to do instead |
|---|---|---|
| Tune prompts by reading rows the LLM got wrong **on test** | Training on test → biased upward → real-world regression | Move those rows to dev. Reseal test from new prod data. |
| Try N prompts, pick best by test-set score | Multiple-comparison bias inflates best-of-N | Pick on dev. Run only the locked winner on test. |
| Run 10 trials, report best | Cherry-picking noise | Report mean ± stdev across all trials. |
| Move the metric after seeing the score | The metric was wrong, not the score | Restart Phase 0 with fresh data and a corrected metric. |
| Add LLM-judge rubric items that favor your arm | Judge is now biased toward your desired conclusion | Lock the rubric in Phase 2, before any arm output is seen. |
| Iter 3 falsified the hypothesis — let me try iter 4 | The 3-iter cap is the discipline. Falsification is a finished iteration. | Lock the arm, run the test pass, accept the result. |

The full set lives in [SKILL.md](./SKILL.md) — required reading before invoking the skill in anger.

## 🌍 What you can use this for

| Decision type | Example question |
|---|---|
| Prompt tuning | "Does prompt-v2 beat the baseline classifier across both tenant tiers?" |
| Model selection | "Can we downgrade from Opus 4.7 to Haiku 4.5 here without losing accuracy?" |
| Retrieval strategy | "Hybrid (BM25 + vector) vs vector-only vs BM25-only on real customer queries?" |
| Architecture choice | "One-call vs two-call orchestration for the cleanup workflow?" |
| Eval methodology | "Same-family judge vs cross-family judge — which gives a more honest verdict?" |

Anything you'd write as **"should we use X or Y in production?"** where production data is the ground truth and a "ship or kill" decision is needed within ~1 day.

## 🤝 Contributing

Issues and PRs welcome. The skill is intentionally compact (one SKILL.md + one chart helper + templates). Changes should preserve that property.

The highest-value contribution is a **new entry to the "Common Rationalizations" table** — if you've used `auto-lab` for a real decision and a rationalization you encountered isn't already on the list, that's the PR most likely to land.

## 📈 Star history

<a href="https://www.star-history.com/#clfhaha1234/auto-lab&type=date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=clfhaha1234/auto-lab&type=date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=clfhaha1234/auto-lab&type=date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=clfhaha1234/auto-lab&type=date" />
 </picture>
</a>

## License

MIT — see [LICENSE](./LICENSE).

---

*If you've shipped a decision the discipline actually changed your mind on, [open an issue](https://github.com/clfhaha1234/auto-lab/issues) — the rationalization table grows from real engagements.*
