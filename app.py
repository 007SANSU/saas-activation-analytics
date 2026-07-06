"""
Pulse activation dashboard.

Reads analysis/summary.json (+ data/users.csv) and renders the funnel,
retention split, and segment cuts that back the PRD.

Run:  streamlit run dashboard/app.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parents[1]

st.set_page_config(page_title="Pulse — Activation Dashboard", layout="wide")


@st.cache_data
def load():
    with open(BASE / "analysis" / "summary.json") as f:
        summary = json.load(f)
    users = pd.read_csv(BASE / "data" / "users.csv")
    return summary, users


try:
    summary, users = load()
except FileNotFoundError:
    st.error("Run `python data/generate_data.py` then `python analysis/analysis.py` first.")
    st.stop()

st.title("Pulse — Activation & Retention")
st.caption("Synthetic data. The story: connecting a data source is the activation event that predicts retention.")

ret = summary["retention"]
up = summary["upside"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Week-4 retention (overall)", f"{ret['overall_w4_retention']}%")
c2.metric("Connected a source", f"{ret['connected_w4_retention']}%",
          delta=f"{ret['retention_lift_x']}x vs not")
c3.metric("Did not connect", f"{ret['not_connected_w4_retention']}%")
c4.metric("Users who connect", f"{ret['pct_users_connected']}%")

st.divider()

left, right = st.columns([3, 2])

with left:
    st.subheader("Onboarding funnel")
    fdf = pd.DataFrame(summary["funnel"])
    fdf = fdf.rename(columns={
        "step": "Step", "users": "Users",
        "pct_of_signups": "% of signups", "step_conversion": "Step conv %",
    })
    st.bar_chart(fdf.set_index("Step")["Users"])
    st.dataframe(fdf, use_container_width=True, hide_index=True)
    st.info("Biggest drop is at **connect_source** — the activation bottleneck.")

with right:
    st.subheader("Retention: connected vs not")
    rdf = pd.DataFrame({
        "Cohort": ["Connected", "Did not connect"],
        "Week-4 retention %": [ret["connected_w4_retention"],
                               ret["not_connected_w4_retention"]],
    })
    st.bar_chart(rdf.set_index("Cohort"))

    st.subheader("Modeled upside")
    st.metric(
        f"Lift connect rate {up['current_connect_rate']}% → {up['target_connect_rate']}%",
        f"+{up['added_retained_users_per_cohort']} retained/cohort",
        delta=f"+{up['relative_retention_gain_pct']}% relative",
    )

st.divider()
st.subheader("Segments")
tab1, tab2, tab3 = st.tabs(["By channel", "By plan", "By company size"])
with tab1:
    st.dataframe(pd.DataFrame(summary["by_channel"]), use_container_width=True, hide_index=True)
with tab2:
    st.dataframe(pd.DataFrame(summary["by_plan"]), use_container_width=True, hide_index=True)
with tab3:
    st.dataframe(pd.DataFrame(summary["by_company_size"]), use_container_width=True, hide_index=True)

st.caption("See analysis/metrics_report.md for the memo and docs/PRD.md for the proposal.")
