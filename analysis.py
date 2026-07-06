"""
Product analysis for Pulse onboarding & activation.

Computes:
  1. The onboarding funnel and where users drop off.
  2. Week-4 retention overall and split by whether a user connected a data source.
  3. A simple driver comparison across segments (channel, plan, company size).
  4. Estimated retained-user upside from closing the activation gap.

Outputs a machine-readable summary (analysis/summary.json) that the report and
dashboard read from, plus console output for quick inspection.

Run:  python analysis/analysis.py
"""

import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
OUT = Path(__file__).resolve().parent

FUNNEL_STEPS = [
    "signup", "verify_email", "complete_profile", "create_project",
    "connect_source", "first_dashboard", "invite_teammate",
]


def load():
    events = pd.read_csv(DATA / "events.csv", parse_dates=["event_dt"])
    users = pd.read_csv(DATA / "users.csv", parse_dates=["signup_dt"])
    return events, users


def build_funnel(events):
    reached = (
        events[events["event_name"].isin(FUNNEL_STEPS)]
        .groupby("event_name")["user_id"]
        .nunique()
    )
    rows = []
    top = reached.get("signup", 0)
    prev = top
    for step in FUNNEL_STEPS:
        n = int(reached.get(step, 0))
        pct_of_top = round(100 * n / top, 1) if top else 0.0
        step_conv = round(100 * n / prev, 1) if prev else 0.0
        rows.append(
            {
                "step": step,
                "users": n,
                "pct_of_signups": pct_of_top,
                "step_conversion": step_conv,
            }
        )
        prev = n if n else prev
    return rows


def retention_split(users):
    overall = round(100 * users["retained_w4"].mean(), 1)
    connected = users[users["connected_source"] == 1]
    not_connected = users[users["connected_source"] == 0]
    r_conn = round(100 * connected["retained_w4"].mean(), 1)
    r_noconn = round(100 * not_connected["retained_w4"].mean(), 1)
    lift = round(r_conn / r_noconn, 1) if r_noconn else None
    return {
        "overall_w4_retention": overall,
        "connected_w4_retention": r_conn,
        "not_connected_w4_retention": r_noconn,
        "retention_lift_x": lift,
        "pct_users_connected": round(100 * users["connected_source"].mean(), 1),
    }


def segment_table(users, dim):
    g = users.groupby(dim).agg(
        users=("user_id", "count"),
        pct_connected=("connected_source", lambda s: round(100 * s.mean(), 1)),
        w4_retention=("retained_w4", lambda s: round(100 * s.mean(), 1)),
    )
    g = g.sort_values("w4_retention", ascending=False)
    return g.reset_index().to_dict(orient="records")


def upside_estimate(users, target_connect_rate=0.60):
    """
    If we lifted the connect-source rate to `target_connect_rate`, and newly
    connected users retained at the connected cohort's rate, how many more
    week-4 retained users would we expect per signup cohort?
    """
    n = len(users)
    current_rate = users["connected_source"].mean()
    r_conn = users[users["connected_source"] == 1]["retained_w4"].mean()
    r_noconn = users[users["connected_source"] == 0]["retained_w4"].mean()

    if target_connect_rate <= current_rate:
        target_connect_rate = current_rate

    added_connectors = (target_connect_rate - current_rate) * n
    # Those users move from the not-connected retention rate to connected rate.
    added_retained = added_connectors * (r_conn - r_noconn)
    current_retained = users["retained_w4"].sum()
    pct_gain = round(100 * added_retained / current_retained, 1) if current_retained else 0.0
    return {
        "current_connect_rate": round(100 * current_rate, 1),
        "target_connect_rate": round(100 * target_connect_rate, 1),
        "added_retained_users_per_cohort": int(round(added_retained)),
        "current_retained_users": int(current_retained),
        "relative_retention_gain_pct": pct_gain,
    }


def main():
    events, users = load()
    funnel = build_funnel(events)
    ret = retention_split(users)
    by_channel = segment_table(users, "channel")
    by_plan = segment_table(users, "plan")
    by_size = segment_table(users, "company_size")
    upside = upside_estimate(users)

    summary = {
        "n_users": int(len(users)),
        "n_events": int(len(events)),
        "funnel": funnel,
        "retention": ret,
        "by_channel": by_channel,
        "by_plan": by_plan,
        "by_company_size": by_size,
        "upside": upside,
    }

    with open(OUT / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # ---- Console report ----
    print("\n=== ONBOARDING FUNNEL ===")
    print(f"{'step':<18}{'users':>8}{'% signups':>12}{'step conv':>12}")
    for r in funnel:
        print(f"{r['step']:<18}{r['users']:>8}{r['pct_of_signups']:>11}%{r['step_conversion']:>11}%")

    print("\n=== WEEK-4 RETENTION ===")
    print(f"Overall:                 {ret['overall_w4_retention']}%")
    print(f"Connected a source:      {ret['connected_w4_retention']}%")
    print(f"Did NOT connect:         {ret['not_connected_w4_retention']}%")
    print(f"Lift:                    {ret['retention_lift_x']}x")
    print(f"% of users who connect:  {ret['pct_users_connected']}%")

    print("\n=== UPSIDE (lift connect rate to 60%) ===")
    print(f"+{upside['added_retained_users_per_cohort']} retained users per cohort "
          f"(+{upside['relative_retention_gain_pct']}% relative)")

    print(f"\nWrote {OUT/'summary.json'}")


if __name__ == "__main__":
    main()
