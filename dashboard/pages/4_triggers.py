import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import subprocess

from app import check_password
from lib.gha import trigger_workflow, get_recent_runs

st.set_page_config(page_title="Triggers", layout="wide")
if not check_password():
    st.stop()

st.title("🚀 Triggers")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "run.py")

TOKEN = st.secrets["github"]["token"]
REPO_1 = st.secrets["github"]["repo_1"]
REPO_2 = st.secrets["github"]["repo_2"]
WORKFLOW = st.secrets["github"]["workflow_file"]

# ── Local run ─────────────────────────────────────────────────────────────────
st.subheader("💻 Local Run")
col1, col2, col3 = st.columns(3)
with col1:
    count = st.number_input("Count", min_value=1, max_value=50, value=5)
with col2:
    concurrency = st.number_input("Concurrency", min_value=1, max_value=20, value=5)
with col3:
    headed = st.checkbox("Headed (show browser)")

if st.button("▶️ Run Locally"):
    cmd = ["python3", SCRIPT, "--admaven", f"--count={int(count)}", f"--concurrency={int(concurrency)}", "--logs"]
    if headed:
        cmd.append("--headed")
    log_box = st.empty()
    output_lines = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
    for line in proc.stdout:
        output_lines.append(line.rstrip())
        log_box.code("\n".join(output_lines[-50:]), language="bash")
    proc.wait()
    st.success(f"Done (exit code {proc.returncode})")

st.divider()

# ── GHA Repo 1 ────────────────────────────────────────────────────────────────
st.subheader("🐙 GitHub Actions — Repo 1")
runs1 = get_recent_runs(REPO_1, WORKFLOW, TOKEN)
if runs1:
    for r in runs1:
        icon = "✅" if r["conclusion"] == "success" else ("🔄" if r["status"] == "in_progress" else "❌")
        duration = f"  {r['duration_s']}s" if r["duration_s"] else ""
        st.text(f"{icon}  {r['created_at'][:16]}  {r['status']}  {r['conclusion'] or ''}{duration}")
else:
    st.info("No recent runs")

if st.button("▶️ Trigger Repo 1"):
    if trigger_workflow(REPO_1, WORKFLOW, TOKEN):
        st.success("Triggered — refresh in ~30s to see it running")
    else:
        st.error("Trigger failed — check GH token permissions")

st.divider()

# ── GHA Repo 2 ────────────────────────────────────────────────────────────────
st.subheader("🐙 GitHub Actions — Repo 2")
runs2 = get_recent_runs(REPO_2, WORKFLOW, TOKEN)
if runs2:
    for r in runs2:
        icon = "✅" if r["conclusion"] == "success" else ("🔄" if r["status"] == "in_progress" else "❌")
        duration = f"  {r['duration_s']}s" if r["duration_s"] else ""
        st.text(f"{icon}  {r['created_at'][:16]}  {r['status']}  {r['conclusion'] or ''}{duration}")
else:
    st.info("No recent runs")

if st.button("▶️ Trigger Repo 2"):
    if trigger_workflow(REPO_2, WORKFLOW, TOKEN):
        st.success("Triggered — refresh in ~30s to see it running")
    else:
        st.error("Trigger failed — check GH token permissions")
