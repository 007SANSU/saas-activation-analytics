# Pulse: Finding & Fixing an Activation Bottleneck

**A technical product management case study — from raw event data to a
quantified, spec'd, and experiment-ready feature.**

This repo walks a full TPM loop on a fictional B2B SaaS product ("Pulse"):
analyze product data → find the leverage point → write the PRD → write the
technical spec → define the metrics that decide ship/no-ship. It's built to show
both halves of the role: the data/technical fluency *and* the product judgment.

> All data is synthetic (generated locally), but the numbers are real outputs of
> real analysis code — nothing in the write-ups is hand-waved.

---

## The finding in one paragraph

Pulse's blended week-4 retention is **9.8%** — but that average hides a bimodal
product. Users who **connect a data source during onboarding retain at 41%**;
those who don't retain at **1.8%** (a **22.8x** gap). Only **20.6% of signups**
ever connect a source, and the funnel pinpoints the failure at exactly that
step. Closing that gap — not buying more traffic — is the highest-leverage move
available. Lifting the connect rate to 60% would add an estimated **~927
retained users per cohort (+157%)** with zero new acquisition spend.

That insight drives everything else in the repo.

## What's inside (and what each piece demonstrates)

| File | What it is | What it shows a hiring manager |
|---|---|---|
| [`analysis/metrics_report.md`](analysis/metrics_report.md) | The product memo | Data → insight → prioritized, caveated recommendation |
| [`docs/PRD.md`](docs/PRD.md) | Product requirements doc | Problem framing, metrics, experiment design, ship criteria |
| [`docs/tech_spec.md`](docs/tech_spec.md) | System design & instrumentation spec | REST/event/architecture fluency; catching hidden eng work |
| [`docs/metrics_definitions.md`](docs/metrics_definitions.md) | Canonical metric definitions | Rigor; preventing "whose dashboard is right" fights |
| [`analysis/analysis.py`](analysis/analysis.py) | Funnel + retention + upside code | Can actually work with data, not just talk about it |
| [`data/generate_data.py`](data/generate_data.py) | Synthetic data generator | Understands event models and user behavior |
| [`dashboard/app.py`](dashboard/app.py) | Streamlit dashboard | Turns analysis into something stakeholders can explore |

**If you only read two files:** the [memo](analysis/metrics_report.md) and the
[PRD](docs/PRD.md).

## Reproduce it

```bash
pip install -r requirements.txt

python data/generate_data.py      # -> data/events.csv, data/users.csv
python analysis/analysis.py       # -> analysis/summary.json + console report
streamlit run dashboard/app.py    # interactive dashboard (optional)
```

`analysis/analysis.py` prints the funnel, the retention split, and the modeled
upside — the exact numbers cited across the docs.

## How I'd think about this as a TPM

The point of the case study isn't the chart; it's the reasoning:

- **I led with the metric that hides the story.** A single 9.8% retention number
  would have sent the team chasing the wrong thing. Splitting by the activation
  event reframed the whole problem.
- **I stayed honest about causality.** Connecting a source *correlates* with
  retention; it may partly mark motivated users rather than cause retention. So
  the PRD ships an experiment with a holdout, and the ship criteria explicitly
  handle the "we nudged low-intent users who churn anyway" outcome.
- **I made the eng work legible.** The tech spec fixes instrumentation *first*,
  because we currently can't tell a user who gave up from an OAuth failure — and
  that ambiguity blocks prioritization. That's the kind of hidden dependency a
  TPM is supposed to surface before it wrecks a sprint estimate.

## Stack

Python (pandas) for analysis, Streamlit for the dashboard, Markdown for the
product docs. Intentionally lightweight — the artifacts, not the tooling, are
the point.

---

*Fictional product, synthetic data, original analysis. Built as a portfolio
piece for technical product management roles.*
