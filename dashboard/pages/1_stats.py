import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import timedelta
import json
import glob

from app import check_password
from lib.supabase_client import get_run_logs, upsert_run_logs

st.set_page_config(page_title="Stats", layout="wide")
if not check_password():
    st.stop()

st.title("📊 Stats")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(ROOT, "services/admaven/logs")

if st.button("🔄 Sync local logs → Supabase"):
    logs = []
    for path in glob.glob(os.path.join(LOGS_DIR, "run_logs_*.jsonl")):
        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry.setdefault("source", "local")
                    logs.append(entry)
                except Exception:
                    pass
    upsert_run_logs(logs)
    st.success(f"Synced {len(logs)} log entries")

# ── Filters ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    source = st.selectbox("Source", ["all", "local", "gha_repo1", "gha_repo2"])
with col2:
    success_filter = st.selectbox("Status", ["all", "success", "failed"])
with col3:
    days = st.slider("Last N days", 1, 30, 7)

filters = {}
if source != "all":
    filters["source"] = source
if success_filter == "success":
    filters["success"] = True
elif success_filter == "failed":
    filters["success"] = False

raw = get_run_logs(filters)
df = pd.DataFrame(raw)

if df.empty:
    st.info("No logs yet — sync local logs or run the automation.")
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
cutoff = pd.Timestamp.now(tz="UTC") - timedelta(days=days)
df = df[df["created_at"] >= cutoff]

# ── Metrics ───────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Runs", len(df))
m2.metric("Success Rate", f"{df['success'].mean()*100:.1f}%" if len(df) else "—")
m3.metric("Avg Bandwidth", f"{df['bw_kb'].mean():.0f} KB" if len(df) else "—")
m4.metric("Failures", int((~df["success"]).sum()) if len(df) else 0)

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Runs per hour")
    df["hour"] = df["created_at"].dt.hour
    st.bar_chart(df.groupby("hour").size())

with col_b:
    st.subheader("Failure reasons")
    reasons = df[~df["success"]]["reason"].value_counts()
    if not reasons.empty:
        st.bar_chart(reasons)
    else:
        st.info("No failures")

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Top countries")
    st.bar_chart(df["country"].value_counts().head(10))

with col_d:
    st.subheader("Devices")
    st.bar_chart(df["device"].value_counts().head(10))

st.divider()
st.subheader("Raw logs")
st.dataframe(
    df[["created_at", "source", "device", "country", "success", "reason", "bw_kb", "url"]],
    use_container_width=True,
    hide_index=True,
)
