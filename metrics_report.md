# Activation Analysis: The Connect-a-Source Bottleneck

**Author:** Sanskar Maurya · **Date:** 2025 · **Status:** For review

> A product memo written from a synthetic-but-realistic dataset (6,000 users,
> ~31.7k events). The goal is to show the reasoning path from raw data to a
> prioritized, quantified recommendation — the way a TPM would frame it for
> eng and leadership.

## TL;DR

Week-4 retention is **9.8%**, but that average hides a bimodal product. Users
who **connect a data source in onboarding retain at 41%**; those who don't
retain at **1.8%** — a **22.8x** difference. Only **20.6% of signups** ever
connect a source, and the funnel shows the drop happens precisely at that step
(43% step-conversion, the leakiest in the flow).

**Recommendation:** treat "connect a source" as the activation event and invest
in getting users to it. Lifting the connect rate from ~21% to 60% would add an
estimated **~927 retained users per signup cohort (+157% relative)** without
acquiring a single new user.

## The funnel

| Step | Users | % of signups | Step conversion |
|---|---:|---:|---:|
| signup | 6,000 | 100.0% | 100.0% |
| verify_email | 5,160 | 86.0% | 86.0% |
| complete_profile | 4,004 | 66.7% | 77.6% |
| create_project | 2,874 | 47.9% | 71.8% |
| **connect_source** | **1,235** | **20.6%** | **43.0%** |
| first_dashboard | 1,097 | 18.3% | 88.8% |
| invite_teammate | 628 | 10.5% | 57.2% |

Two things stand out. First, the biggest single drop is at **connect_source**
(only 43% of users who create a project go on to connect one). Second, once a
user *does* connect a source, the next step (`first_dashboard`) converts at
88.8% — the product delivers value quickly *if* users reach the aha moment. The
problem is getting them there, not what happens after.

## The retention split

| Segment | Week-4 retention |
|---|---:|
| Connected a source | **41.0%** |
| Did not connect | 1.8% |
| Overall | 9.8% |

This is the core insight: **the connect-source step is not just a funnel stage,
it's the activation event that predicts long-term retention.** Reporting a
single blended retention number would hide this entirely.

> **Caveat on causality.** This is a correlation. Connecting a source may
> partly be a *marker* of already-motivated users rather than a pure *cause* of
> retention. The upside estimate below assumes newly-nudged connectors behave
> like today's connectors, which likely overstates the effect. That's exactly
> why the PRD ships this as an experiment with a holdout, not a global rollout.

## Where the leak concentrates

Segmenting the connect rate shows the problem isn't uniform — it's worst for
lower-intent acquisition channels and smaller companies, which points at
targeting for the fix.

- **By channel (the real signal):** connect rate ranges from **28.6%
  (referral)** and 24.1% (content) down to just **13.9% (paid_ads)** — a 2x
  spread. Retention tracks it directly (referral 15.0% vs paid_ads 6.5%). Paid
  traffic is both the leakiest *and* the most expensive, which makes it the
  sharpest place to target the fix.
- **By company size (flat):** connect rate sits in a narrow 19–22% band across
  all sizes — company size is *not* a useful lever here. Worth stating
  explicitly so the team doesn't over-index on it.

Takeaway: **channel is the meaningful cut, company size isn't.** The experiment
should target and analyze by channel, especially paid_ads.

## Quantified upside

If we lift the connect-source rate from **20.6% → 60%**, and assume newly
connected users retain at the connected-cohort rate, the model projects:

- **+927 week-4 retained users per signup cohort**
- **+157% relative** increase in retained users
- Achieved with **zero additional acquisition spend**

Even discounting heavily for the causality caveat (say, assume the nudged
cohort retains at half the rate of today's self-motivated connectors), the
intervention still clears a meaningful bar — which is what makes it worth an
experiment.

## Recommendation & next step

1. **Redefine activation** company-wide as *connected a source within 7 days*.
   Make it the north-star input metric for the onboarding team.
2. **Ship a guided setup experiment** to raise the connect rate (see
   [`docs/PRD.md`](../docs/PRD.md)).
3. **Instrument the step** properly so we can see *why* users drop — no source
   available, auth failure, or abandonment (see [`docs/tech_spec.md`](../docs/tech_spec.md)).

Reproduce every number here with `python analysis/analysis.py`.
