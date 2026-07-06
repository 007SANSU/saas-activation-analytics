"""
Synthetic event-data generator for "Pulse" — a fictional B2B SaaS analytics product.

The data is engineered to contain a realistic, discoverable product story:
signups flow through an onboarding funnel, and the single strongest predictor of
week-4 retention is whether a user connects a data source in their first session.
Only a minority of users reach that step, which is the core opportunity the
analysis and PRD are built around.

Run:  python data/generate_data.py
Out:  data/events.csv, data/users.csv
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

N_USERS = 6000
START = datetime(2025, 1, 1)
SIGNUP_WINDOW_DAYS = 90  # users sign up across a 90-day window

DATA_DIR = Path(__file__).resolve().parent

# Acquisition channels with different baseline quality (affects activation odds).
CHANNELS = {
    "organic_search": {"weight": 0.30, "quality": 1.00},
    "paid_ads":       {"weight": 0.25, "quality": 0.75},
    "referral":       {"weight": 0.15, "quality": 1.25},
    "content":        {"weight": 0.20, "quality": 1.10},
    "outbound":       {"weight": 0.10, "quality": 0.90},
}

PLANS = ["free", "team", "business"]

# Ordered onboarding funnel. Each step has a base pass-through rate; the
# "connect_source" step is deliberately the leakiest and the most predictive.
FUNNEL = [
    ("signup",          1.00),
    ("verify_email",    0.86),
    ("complete_profile",0.78),
    ("create_project",  0.71),
    ("connect_source",  0.42),   # <-- the activation bottleneck ("aha" step)
    ("first_dashboard", 0.88),   # conditional on connecting a source
    ("invite_teammate", 0.55),
]


def weighted_choice(d):
    keys = list(d.keys())
    weights = [d[k]["weight"] for k in keys]
    return random.choices(keys, weights=weights, k=1)[0]


def make_users():
    users = []
    for i in range(1, N_USERS + 1):
        channel = weighted_choice(CHANNELS)
        signup_offset = random.randint(0, SIGNUP_WINDOW_DAYS)
        signup_dt = START + timedelta(
            days=signup_offset,
            hours=random.randint(6, 22),
            minutes=random.randint(0, 59),
        )
        plan = random.choices(PLANS, weights=[0.70, 0.22, 0.08])[0]
        company_size = random.choices(
            ["1-10", "11-50", "51-200", "201-1000", "1000+"],
            weights=[0.35, 0.28, 0.20, 0.12, 0.05],
        )[0]
        users.append(
            {
                "user_id": i,
                "signup_dt": signup_dt,
                "channel": channel,
                "plan": plan,
                "company_size": company_size,
                "quality": CHANNELS[channel]["quality"],
            }
        )
    return users


def simulate_events(users):
    events = []
    user_rows = []

    for u in users:
        uid = u["user_id"]
        t = u["signup_dt"]
        quality = u["quality"]

        reached = {}
        connected_source = False
        # Walk the onboarding funnel; stop when a user drops off.
        for step, base_rate in FUNNEL:
            if step == "signup":
                passed = True
            else:
                # Channel quality nudges pass-through; clamp to a sane range.
                rate = min(0.98, base_rate * (0.6 + 0.4 * quality))
                passed = random.random() < rate
            if not passed:
                break
            t = t + timedelta(minutes=random.randint(1, 40))
            events.append((uid, step, t))
            reached[step] = t
            if step == "connect_source":
                connected_source = True

        # ---- Retention simulation over 4 weeks ----
        # Base weekly return probability; connecting a source is the single
        # biggest lift. This is the signal the analysis is meant to surface.
        base_return = 0.18 * quality
        if connected_source:
            base_return += 0.42
        if reached.get("invite_teammate"):
            base_return += 0.10

        active_weeks = []
        for week in range(1, 5):
            # Retention decays each week; connected users decay much slower.
            decay = 0.06 * week if connected_source else 0.11 * week
            p_return = max(0.02, base_return - decay)
            if random.random() < p_return:
                active_weeks.append(week)
                # Generate a few in-app events during that active week.
                week_start = u["signup_dt"] + timedelta(weeks=week)
                for _ in range(random.randint(1, 6)):
                    ev_t = week_start + timedelta(
                        days=random.randint(0, 6),
                        hours=random.randint(8, 20),
                        minutes=random.randint(0, 59),
                    )
                    action = random.choice(
                        ["view_dashboard", "run_query", "create_report",
                         "share_report", "edit_dashboard"]
                    )
                    events.append((uid, action, ev_t))

        user_rows.append(
            {
                "user_id": uid,
                "signup_dt": u["signup_dt"].isoformat(),
                "channel": u["channel"],
                "plan": u["plan"],
                "company_size": u["company_size"],
                "connected_source": int(connected_source),
                "reached_first_dashboard": int("first_dashboard" in reached),
                "invited_teammate": int("invite_teammate" in reached),
                "retained_w4": int(4 in active_weeks),
                "active_weeks": len(active_weeks),
            }
        )

    events.sort(key=lambda e: e[2])
    return events, user_rows


def write_csv(events, user_rows):
    with open(DATA_DIR / "events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "event_name", "event_dt"])
        for uid, name, dt in events:
            w.writerow([uid, name, dt.isoformat()])

    fields = list(user_rows[0].keys())
    with open(DATA_DIR / "users.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(user_rows)


if __name__ == "__main__":
    users = make_users()
    events, user_rows = simulate_events(users)
    write_csv(events, user_rows)
    print(f"Generated {len(user_rows)} users and {len(events)} events.")
    print(f"Wrote {DATA_DIR/'events.csv'} and {DATA_DIR/'users.csv'}")
