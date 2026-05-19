# Conclusion — prompt-tuning-classifier (synthetic demo)

> *Synthetic demo. Shape and per-slice gotcha modeled after a real
> classifier-prompt decision; numbers are illustrative.*

## Question (verbatim from Phase 0)

> Does a cross-source prompt outperform the baseline classifier on a B2B SaaS
> transaction-categorization task?

## Arms (each changes one thing vs baseline)

| Arm | Change | Cost / 1k rows |
|---|---|---|
| `prompt-v1` (baseline) | Production classifier as deployed (`classify/processor.ts:42`). | **$1.20** |
| `prompt-v2` | Baseline + cross-source signal block in system prompt. | **$1.80** |
| `prompt-v3` | prompt-v2 + amount-direction hint for transfer disambiguation. | **$1.90** |

## Metric + threshold (pre-registered Phase 2)

- Primary: classification accuracy vs human-labeled ground truth (judge: Claude Sonnet 4.6, rubric locked).
- Ship-rule: aggregate effect >= **+5pp** AND no per-slice CI lower bound below **-2pp**.

## Phase 3 — dev-set scores

![Arm comparison: mean accuracy with variance error bars across 3 trials](./charts/arm-bar.png)

All three arms beat baseline on aggregate by ~8.9pp (std across 3 trials: ~1.4pp). Both `v2` and `v3` are flagged as candidates for the held-out test pass.

## Phase 4 — diagnostic

Per-row diff inspection on dev surfaced one signal worth flagging into Phase 0 of any follow-up: `v3`'s amount-direction hint helped Enterprise rows (which carry rich amount context) but appears to **over-correct** SMB rows where the amount column is sparse or zero-filled. The iter-1 hypothesis ("amount hints universally help") was **falsified by iter-3**. Per the 3-iter cap, arms were locked and we proceeded to test.

## Phase 5 — verdict (one pass on held-out test set)

![Effect size forest plot, aggregate and per-slice with 95% CIs](./charts/forest-plot.png)

| Arm | Aggregate Δ | CI | Enterprise Δ | SMB Δ | Verdict |
|---|---|---|---|---|---|
| `prompt-v2` | **+8.9pp** | [+5.0, +12.8] | +13.4pp | +6.7pp | **ship** ✓ |
| `prompt-v3` | +8.9pp | [+5.0, +12.8] | +20.0pp | **-3.3pp** | **kill** ✗ |

**Verdict: ship `prompt-v2`, kill `prompt-v3`.**

`v2` passes the aggregate threshold (CI lower bound lands exactly on the registered +5pp floor) AND both per-slice rules (both CI lower bounds positive). `v3` passes aggregate just as cleanly, but its SMB slice CI is `[-8.8pp, +2.2pp]` — crosses zero, crosses the -2pp loss floor. **Aggregate winners are not winners when a major slice regresses.** Without the per-slice rule pre-registered in Phase 0, we would have shipped `v3` and quietly hurt every SMB customer.

## Cost view

![Cost vs accuracy Pareto across all three arms](./charts/cost-vs-accuracy.png)

`v2` is the Pareto-frontier move: +8.9pp aggregate at +$0.60 / 1k rows. `v3` adds +$0.10 / 1k for zero aggregate gain and a per-slice regression.

## What to test next

Investigate whether amount-direction hints can be made **slice-conditional** (apply only to Enterprise rows where the amount field is reliably populated). That is a separate Phase 0, not a v3 retry.

## Discipline self-audit

- [x] Test set sealed until Phase 5; opened ONCE
- [x] Pre-registered metric + threshold; no drift
- [x] Pilot N=1 validated all metric fields populated before full dev run
- [x] Distribution audit: per-slice counts match production traffic (50/50 Enterprise/SMB on this run; matches production)
- [x] Variance baseline measured: 3 same-prompt trials per arm, std ~1.4pp
- [x] Effect >= 2× variance (8.9pp vs ~2.8pp)
- [x] Cross-judge sanity: 5 rows checked with Gemini-2.5-Pro; agreed on ranking direction on 5/5
- [x] Blind judge (arm IDs anonymized per row)
- [x] Each iter changed ONE thing
- [x] Iter hypotheses written in advance; iter-3 falsification accepted as a finished iteration
- [x] 3-iteration cap enforced
- [x] Verdict locks LATEST hypothesis-driven iter (`prompt-v3` was locked for test even though its dev score wasn't higher than `prompt-v2`'s)
- [x] Per-slice scores reported; aggregate winner `v3` overturned by per-slice rule
