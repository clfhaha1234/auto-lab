# Phase 0 — Frame

> *Synthetic demo modeled after a real prompt-tuning decision encountered while
> building a B2B SaaS classifier. The shape of the decision and the per-slice
> gotcha are real; the numbers are illustrative.*

| Field | Value |
|---|---|
| **Question** | Does a cross-source prompt outperform the baseline classifier on transaction categorization? |
| **Hypothesis** | Adding cross-source signals (cousin-account context, vendor history from sibling tenants) raises accuracy on edge cases the baseline currently misclassifies — and the effect holds across both enterprise and SMB tenants. |
| **Baseline** | `prompt-v1` — current production classifier, single-row context, no cross-source signals. Referenced as `classify/processor.ts:42`. |
| **Arms** | `prompt-v2`: baseline + cross-source signal block injected into the system prompt.<br>`prompt-v3`: prompt-v2 + an additional "amount-direction" hint to disambiguate transfers from spend. |
| **Metric** | Classification accuracy vs human-labeled ground truth. LLM-judge: Claude Sonnet 4.6 with rubric locked in Phase 2. |
| **Stop conditions** | Ship an arm only if BOTH (a) aggregate effect >= +5pp AND (b) no per-slice CI lower bound below -2pp. Otherwise kill. |

**Locked at:** 2026-04-12 (before any data was sampled).

## Phase 1 — data split

- Source: 200 real production rows from the last 30 days, sampled across both tenant tiers in proportion to their actual traffic share.
- Train / scratch: 60 rows (used freely to debug prompts).
- Dev: 80 rows (used for Phase 3-4 iteration; scored only, individual rows not read past iter 1).
- Test (held-out): 60 rows. **Sealed until Phase 5. Opened ONCE.**

Per-slice stratification: 30 Enterprise + 30 SMB rows in each of dev and test, matching production traffic shape.

## Phase 2 — metric pre-registration

Primary: aggregate accuracy on held-out test set (judge: Claude Sonnet 4.6, rubric locked below).

Secondaries (decision-affecting, not aggregated into primary):
- Per-slice accuracy (Enterprise / SMB)
- Cost per 1k rows in USD

Judge rubric locked at: 2026-04-12 (one paragraph; pasted into `judge_prompt.md`). No drift past this point.

Cross-judge sanity check: 5 dev rows re-scored by Gemini-2.5-Pro as a second judge to mitigate self-judging bias.
