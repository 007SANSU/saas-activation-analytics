# PRD: Guided Setup to Lift Source-Connection Rate

| | |
|---|---|
| **Author** | Sanskar Maurya, Technical PM |
| **Status** | Draft → In review |
| **Reviewers** | Eng Lead (Onboarding), Design, Data Science, Growth |
| **Related** | [Activation analysis](../analysis/metrics_report.md) · [Tech spec](./tech_spec.md) |

## 1. Problem

Week-4 retention is 9.8%, but this is a bimodal outcome. Users who connect a
data source during onboarding retain at **41%**; those who don't retain at
**1.8%** (22.8x gap). Only **20.6%** of signups ever connect a source, and the
funnel shows the failure is concentrated at that exact step (43% step
conversion — the leakiest in the flow).

We are leaving retained users on the table not because the product fails to
deliver value, but because most users never reach the moment where it does.

## 2. Goal & success metrics

**Goal:** Get more new users to connect a data source within their first 7 days.

| Metric | Type | Baseline | Target |
|---|---|---|---|
| Source-connection rate (≤7 days) | **Primary** | 20.6% | **≥ 35%** (stretch 60%) |
| Week-4 retention | Guardrail / north star | 9.8% | +3–5 pts |
| Time-to-first-connected-source | Secondary | — | ↓ 25% |
| Onboarding drop-off before connect | Secondary | 79.4% | ↓ meaningfully |
| Support tickets tagged `onboarding` | Guardrail | baseline | no increase |

**Primary metric rationale:** connection rate is the leading indicator we can
move in-quarter; retention is the lagging outcome we ultimately care about. We
commit to the connection rate as the ship/no-ship metric and monitor retention
via holdout.

## 3. Non-goals

- Redesigning the connector catalog or adding new integrations.
- Changing pricing or the free→paid conversion flow.
- Post-activation engagement (dashboards, sharing) — separate workstream.

## 4. Hypothesis

> If we replace the passive empty-state with a **guided, progress-tracked setup
> checklist** that makes connecting a source the obvious next action — and
> reduce the friction of the connect step itself — then more users will connect
> a source in their first session, because the current flow leaves them without
> a clear path or a reason to complete it.

## 5. Proposed solution

Three components, shippable independently and testable in isolation:

**A. Onboarding checklist (persistent).** A dismissible progress widget on the
home screen showing 3–4 steps, with "Connect your first data source" as the
highlighted primary action and a visible completion bar. Progress persists
across sessions.

**B. Guided connect flow.** When a user starts the connect step, present the
most relevant connectors first (ranked by their stated stack from
`complete_profile` and by company size), a 3-step wizard, and inline help for
auth. Add a "connect sample data" escape hatch so users with no data ready can
still reach a populated dashboard (aha moment) and return later.

**C. Contextual nudges.** If a user creates a project but doesn't connect a
source, trigger a next-session in-app prompt and a day-2 lifecycle email, both
deep-linking straight into the guided connect flow.

## 6. Rollout & experiment design

- **Method:** randomized A/B, user-level assignment, 50/50, with a permanent
  holdout for measuring the retention (lagging) effect.
- **Unit:** new signups only; existing users excluded.
- **Instrumentation:** every funnel step and every connect failure reason
  emitted as a discrete event (see tech spec). We cannot improve what we can't
  see fail.
- **Sample size / duration:** powered to detect a 5-pt absolute lift in
  connection rate at 80% power, α=0.05 — roughly a 3–4 week run at current
  signup volume. (Data science to confirm from live traffic.)
- **Phasing:** ship component A first (lowest risk), read results, then layer B
  and C. Avoids confounding all three in one test.

## 7. Ship / no-ship criteria

- **Ship** if connection rate improves ≥5 pts (stat-sig) with no guardrail
  regression (support tickets flat, no latency regression on connect).
- **Iterate** if connection rate moves but retention holdout shows no lift —
  signals we're nudging low-intent users who churn anyway (the causality
  caveat), and we should re-target using the segment cuts.
- **Roll back** if any guardrail regresses.

## 8. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Correlation ≠ causation; nudged users don't retain | Med | Holdout on retention; segment by intent; don't over-claim |
| Checklist feels naggy → dismissed | Med | Dismissible, quiet styling, cap nudge frequency |
| "Connect sample data" becomes a crutch, users never connect real data | Low-Med | Track real-vs-sample; follow-up nudge to connect real source |
| Connect-step failures are technical (auth), not motivational | Med | Instrument failure reasons *first*; may re-prioritize toward reliability |

## 9. Open questions

1. What share of connect-step drop-offs are *failures* (auth/errors) vs
   *abandonment*? The tech spec instrumentation answers this and may reshuffle
   priority between components B and C.
2. Do referral/content users (already high-connect) need this at all, or should
   we target paid/outbound segments only?
3. Should activation be time-boxed at 7 days, or does a 14-day window better
   match longer B2B evaluation cycles?

## 10. Appendix: what "done" looks like

A new user lands on the home screen, sees a clear checklist, connects a source
(real or sample) inside their first session via a 3-step wizard, reaches a
populated dashboard, and — if they stall — gets one well-timed nudge back into
the flow. Every step and failure is measured, and we can attribute the
retention change to the change we shipped.
