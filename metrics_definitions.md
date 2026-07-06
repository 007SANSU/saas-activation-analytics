# Metrics Definitions

One canonical definition per metric. If a number appears on a dashboard or in a
review, it should trace back to a definition here. Ambiguous metric definitions
are one of the most common ways product teams end up arguing about whose
dashboard is "right" — this doc exists to prevent that.

## North star

**Week-4 retained user** — a user with at least one qualifying in-app action
(`view_dashboard`, `run_query`, `create_report`, `share_report`,
`edit_dashboard`) during calendar week 4 after signup.
*Why:* it captures durable value delivery, not a one-time visit.

## Activation (input metric)

**Activated user** — a user whose first `connect_source_succeeded` event occurs
within **7 days** of signup.
*Why 7 days:* matches observed onboarding session behavior; revisit against B2B
evaluation cycles (PRD open question #3).
*Canonical source:* `dim_user.activated_flag` (derived nightly). Do not
recompute ad hoc.

## Funnel metrics

- **Step conversion** — unique users reaching step *N* ÷ unique users reaching
  step *N−1*.
- **% of signups** — unique users reaching step *N* ÷ unique signups.
- A user counts at a step if they emit that step's event at least once, ever
  (not restricted to first session), unless a metric explicitly says otherwise.

## Connect-step diagnostics

- **Connection rate** — users with ≥1 `connect_source_succeeded` ÷ signups.
- **Connect failure rate** — attempts with `outcome=failure` ÷ total attempts.
- **Abandonment rate** — users who fired `connect_source_started` but never
  `connect_source_succeeded` or `connect_source_attempt(failure)` — i.e. left
  without a technical failure. This is the split that separates "won't" from
  "can't."

## Guardrails

- **Onboarding support tickets** — tickets tagged `onboarding`, per 1,000
  signups.
- **Connect latency (p95)** — server time from `/connect/start` to terminal
  outcome.

## Segmentation dimensions

`channel`, `plan`, `company_size`. Standard cuts for every activation and
retention report so segment comparisons stay consistent across analyses.
