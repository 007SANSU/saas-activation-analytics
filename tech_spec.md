# Tech Spec: Activation Instrumentation & Guided Connect Flow

| | |
|---|---|
| **Author** | Sanskar Maurya, Technical PM |
| **Status** | Draft for eng review |
| **Related** | [PRD](./PRD.md) · [Metrics definitions](./metrics_definitions.md) |

This spec covers the two engineering-facing pieces the PRD depends on:
(1) **event instrumentation** that lets us see *why* the connect step fails, and
(2) the **guided connect flow** service design. It's written to give eng enough
to estimate and to give me (the TPM) enough to call out gaps in estimates.

## 1. Goals

- Emit a clean, well-typed event for every onboarding funnel step **and every
  connect-attempt outcome** (success + typed failure reason).
- Support A/B assignment lookups at low latency in the onboarding path.
- Keep the connect flow resilient to third-party connector outages.

## Non-goals

- Building new connectors. We instrument and wrap the existing catalog.
- Warehouse/BI modeling beyond the raw event contract below.

## 2. Current-state problem

Today the connect step emits a single `connect_source` success event and
nothing on failure or abandonment. We literally cannot distinguish "user gave
up" from "OAuth to the warehouse failed." That ambiguity is open question #1 in
the PRD, and it blocks prioritization. **This is the first thing to fix.**

## 3. Event contract

All onboarding events share an envelope and are emitted through a single typed
client wrapper (no raw `track()` calls scattered across the codebase).

```json
{
  "event_name": "connect_source_attempt",
  "user_id": "usr_123",
  "session_id": "ses_abc",
  "ts": "2025-03-14T18:04:21Z",
  "experiment": { "guided_setup": "treatment" },
  "props": {
    "connector_type": "snowflake",
    "outcome": "failure",
    "failure_reason": "auth_denied",
    "attempt_number": 1,
    "source_kind": "real"
  }
}
```

**Enumerations (closed sets, validated at emit time):**

- `outcome`: `success | failure | abandoned`
- `failure_reason`: `auth_denied | credentials_invalid | connector_timeout |
  permission_scope | user_cancelled | unknown`
- `source_kind`: `real | sample`

New funnel events to add: `connect_source_started`, `connect_source_attempt`
(one per attempt, with outcome), `connect_source_succeeded`,
`connect_source_abandoned` (fired by a client-side timeout / navigation-away).

**Why typed enums matter:** the analysis and the ship/no-ship decision depend on
splitting drop-off into *failure* vs *abandonment*. Free-text reasons would make
that split unanalyzable. Validation happens in the client wrapper so bad events
never reach the warehouse.

## 4. Architecture

```
 ┌───────────┐   assign    ┌──────────────────┐
 │  Web app  │────────────▶│ Experiment svc   │  (flag + variant, cached)
 │ onboarding│◀────────────│  GET /assign     │
 └─────┬─────┘   variant   └──────────────────┘
       │ start connect
       ▼
 ┌──────────────────┐   OAuth / creds   ┌──────────────┐
 │ Connect service  │──────────────────▶│  Connector   │
 │ (wizard backend) │◀──────────────────│  (3rd party) │
 └───────┬──────────┘   ok / error      └──────────────┘
         │ emit typed event
         ▼
 ┌──────────────────┐      ┌──────────────┐      ┌───────────────┐
 │  Event gateway   │─────▶│ Event stream │─────▶│  Warehouse    │
 │ (schema validate)│      │  (queue)     │      │ (funnel/BI)   │
 └──────────────────┘      └──────────────┘      └───────────────┘
```

### Components

**Experiment service.** Returns `{variant}` for `(user_id, experiment_key)`.
Deterministic hash assignment so a user is stable across sessions. Response
cached at the edge; assignment must add **< 50 ms p95** to the onboarding path,
and must **fail open** to control if unavailable (never block onboarding on the
experiment service).

**Connect service.** Wraps the connector catalog behind one internal API:
`POST /connect/start`, `POST /connect/callback`, `GET /connect/status`. Owns
retry/backoff to third parties, normalizes their errors into our
`failure_reason` enum, and emits the typed events. The "connect sample data"
path is a first-class branch here — it provisions a canned dataset so a user
can reach a populated dashboard without a real source.

**Event gateway.** Validates every event against the schema (rejects unknown
`event_name`, bad enum values) before it hits the stream. Invalid events go to a
dead-letter queue with an alert, not silently dropped.

## 5. Data model (warehouse)

```
fct_onboarding_events
  event_id (pk)     user_id        session_id     event_name
  ts                connector_type outcome        failure_reason
  source_kind       experiment_variant

dim_user
  user_id (pk)  signup_ts  channel  plan  company_size
  activated_flag  activated_ts   -- activated = first connect_source_succeeded ≤7d
```

`activated_flag` / `activated_ts` are derived nightly and are the canonical
definition of activation used by every downstream metric — one definition, one
place. See [metrics definitions](./metrics_definitions.md).

## 6. Failure modes & resilience

| Failure | Behavior | Rationale |
|---|---|---|
| Experiment svc down | Serve **control**, log, continue | Never block onboarding on an experiment |
| Connector 3rd-party timeout | Retry w/ backoff, then typed `connector_timeout` failure + user-facing retry | Distinguish infra failure from user abandonment |
| Event gateway rejects event | Dead-letter + alert | Preserve data integrity; bad data is worse than missing data |
| Warehouse lag | Metrics eventually-consistent; dashboards show freshness ts | Don't make ship decisions on stale reads |

## 7. Rollout plan

1. **Phase 0 — instrumentation only.** Ship the event contract + gateway
   validation behind no user-visible change. Backfill nothing; start clean.
   *This alone answers PRD open question #1.*
2. **Phase 1 — experiment plumbing.** Wire the experiment service into the
   onboarding path, assignment logged, no UI change (A/A test to validate
   assignment + metrics pipeline before trusting any A/B read).
3. **Phase 2 — guided setup UI.** Ship PRD component A (checklist) to treatment.
4. **Phase 3 — connect wizard + sample data + nudges** (components B, C).

## 8. Estimation checklist (TPM ↔ eng)

Questions I'll want answered before locking scope — and the kind of thing a TPM
should catch in an estimate rather than discover mid-sprint:

- Is the connector error surface already normalized, or does each connector
  return bespoke errors we'd need to map to the enum? (Likely hidden work.)
- Does the current analytics client support schema validation, or is that new?
- Can the experiment service meet the <50 ms p95 budget, or do we need edge
  caching first?
- What's the client-side definition of "abandoned" — a timeout, a route change,
  or a session end? (Ambiguity here corrupts the core metric.)

## 9. Test & verification

- **Contract tests** for every event type against the JSON schema.
- **A/A test** in Phase 1: variants must show no significant difference — if
  they do, the pipeline is biased and no A/B result can be trusted.
- **Synthetic failure injection** on connectors to confirm each `failure_reason`
  maps correctly.
- **Metric parity check:** warehouse `activated_flag` count must reconcile with
  raw `connect_source_succeeded` events within tolerance nightly.
