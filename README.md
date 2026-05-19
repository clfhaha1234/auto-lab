# Auto Lab

> A Claude Code skill for running rigorous, anti-overfitting experiments — applied to fast-moving engineering decisions like prompt choice, model selection, architecture comparisons, and retrieval strategies.

`auto-lab` encodes a six-phase loop — **Frame → Source → Metric → Run → Diagnose → Conclude** — with first-principles guards against the most common ways engineers accidentally lie to themselves with data.

## Why this exists

Most engineering "experiments" leak. We peek at test sets to debug. We pick best-of-N on the same set we'll report from. We tune prompts on rows the LLM got wrong. We move metrics after seeing scores. The result looks like science but generalizes worse than a coin flip.

`auto-lab` enforces the discipline that makes the conclusion trustworthy:

- **Held-out test set, sealed until the final pass** — one open, one verdict
- **Pre-registered metric + effect-size threshold** — no post-hoc moves
- **Pilot N=1 before any full run** — catches instrumentation bugs in 30 seconds
- **Variance baseline before celebrating any gap** — a 5pp win with 4pp noise is noise
- **3-iteration cap on dev refinement** — past that you're overfitting to dev
- **Per-slice verification, not just aggregate** — aggregate wins that lose on major slices are not wins

The skill ships with a 22-row "Common Rationalizations" table and a "Red Flags — STOP" checklist designed to interrupt the exact moments engineers talk themselves into a contaminated conclusion.

## When to use

- Comparing competing approaches (2 LLMs vs 1, Sonnet vs Haiku, prompt A vs B, retrieval strategy X vs Y)
- A "ship or kill" decision is needed within ~1 day
- Production data is available as ground truth

## When NOT to use

- The decision can be made from first-principles reasoning alone — just fix it
- No real production data available (synthetic-only experiments are weaker than thoughtful design)
- The arms are mechanically the same (whitespace tweaks, ordering changes)
- You want to debug a single arm — that's iterative self-improvement, not comparison

## Installation

### Claude Code

```bash
git clone https://github.com/clfhaha1234/auto-lab.git ~/.claude/skills/auto-lab
```

After the clone, restart Claude Code (or start a new conversation) and the skill becomes discoverable via the `Skill` tool and the `/auto-lab` slash command.

Single-file install (if you only want the skill, no git history):

```bash
mkdir -p ~/.claude/skills/auto-lab
curl -fsSL -o ~/.claude/skills/auto-lab/SKILL.md \
  https://raw.githubusercontent.com/clfhaha1234/auto-lab/main/SKILL.md
```

### Other agent runtimes

The skill is a single Markdown file with YAML frontmatter. Any agent runtime that supports the Anthropic skill format (Codex via `~/.agents/skills/`, OpenCode, etc.) can use it by dropping `SKILL.md` into the appropriate skills directory.

## Usage

When you have a "should we use X or Y?" question for which production data is the ground truth, ask Claude:

> "Let's experiment with the two-call vs one-call cleanup flow."
> "Is Haiku 4.5 good enough for the survey-translate skill, or do we need Sonnet?"
> "Compare retrieval strategy A vs B on real customer queries."

Claude will then walk through the six phases:

1. **Phase 0 — Frame**: write down question, hypothesis, baseline, arms, and stop conditions BEFORE touching data.
2. **Phase 1 — Source + split**: sample from production, partition into ~30% train / ~50% dev / ~20% sealed test.
3. **Phase 2 — Metric**: pre-register the primary metric and effect-size threshold; lock the LLM-judge rubric if applicable.
4. **Phase 3 — Run**: pilot N=1 first, then full dev run with variance baseline + cross-judge sanity check.
5. **Phase 4 — Diagnose**: per-row diffs, ≤3 refinement iterations, each changing ONE thing.
6. **Phase 5 — Verdict**: one pass on the held-out test set, per-slice scores, ship or kill.

The output is a ~200-word conclusion doc with the question, baseline + arm definitions, test-set scores, verdict, and a 13-item discipline self-audit checklist.

## What this skill is NOT

- **Not** for single-arm iterative debugging — use a self-improvement skill for that.
- **Not** for fixing bugs — if a code path is wrong, just fix it.
- **Not** for synthetic benchmarking — `auto-lab` is built around production data as ground truth.

## Design philosophy

This skill is opinionated. It will refuse moves that look reasonable in the moment but contaminate the conclusion:

- Peeking at one test row to "understand what's happening" — that row is contaminated. Move it to dev.
- Locking the iter with the best dev score instead of the latest hypothesis-driven iter — multi-iteration cherry-picking.
- Reporting cost from a first-call (cache-cold) measurement — misleading by 5-15×.
- Trying a fourth iteration because iter 3 falsified the hypothesis — falsification is a finished result, not a license to keep going.

The discipline is the value. If you want a tool that lets you tweak until the numbers look good, use a different one.

## License

MIT — see [LICENSE](./LICENSE).

## Contributing

Issues and PRs welcome. The skill is intentionally compact (one Markdown file); changes should preserve that property unless there's a clear reason to add supporting files.

If you've used `auto-lab` for a real decision and have a rationalization that's missing from the "Common Rationalizations" table, that's a high-value PR.
