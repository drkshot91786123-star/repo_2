# Centralized Automation Dashboard — Design Spec
**Date:** 2026-07-01
**Stack:** Streamlit + Supabase
**Deployment:** Local (`streamlit run`) + Streamlit Cloud (password-protected)

---

## 1. Overview

A single Streamlit app that acts as the central control panel for the website automation project. It replaces manual file editing (`destinations.txt`, `paste_url.txt`, `daily_links.json`) with a database-backed UI. Everything — stats, link management, locker generation, and run triggers — lives in one place.

---

## 2. Architecture

```
dashboard/
  app.py                  # entry point, login gate, sidebar nav
  pages/
    1_stats.py            # run logs, metrics, charts
    2_links.py            # destination link manager
    3_generate.py         # generate admaven locker links
    4_triggers.py         # trigger GHA workflows or local runs
  lib/
    supabase_client.py    # Supabase DB connection
    gha.py                # GitHub Actions API (trigger, status)
    locker.py             # admaven locker link generation (wraps existing code)
    paste_rs.py           # paste.rs sync logic
  .streamlit/
    config.toml           # dark theme
    secrets.toml          # password, Supabase URL/key, GH token (gitignored)
```

**Data flow:**
```
Supabase DB
  ├── destinations        (all links + active flag)
  ├── locker_links        (generated admaven links)
  └── run_logs            (synced from JSONL logs)

Dashboard (Streamlit)
  ├── reads/writes → Supabase
  ├── triggers → GitHub Actions API
  └── triggers → local subprocess (admaven script)

Automation scripts (auto_admaven.py)
  └── reads active destinations → from Supabase (instead of destinations.txt)
```

---

## 3. Supabase Schema

### `destinations`
| column | type | notes |
|---|---|---|
| id | uuid | primary key |
| url | text | destination URL |
| category | text | `entertainment` or `soundy` |
| active | bool | if true, used in automation |
| created_at | timestamp | |

### `locker_links`
| column | type | notes |
|---|---|---|
| id | uuid | primary key |
| locker_url | text | generated admaven link |
| destination_id | uuid | FK → destinations |
| paste_rs_url | text | paste.rs URL used |
| created_at | timestamp | |

### `run_logs`
| column | type | notes |
|---|---|---|
| id | uuid | primary key |
| ts | text | run timestamp |
| instance | int | parallel instance number |
| device | text | emulated device |
| ip | text | proxy IP used |
| country | text | proxy country |
| mode | text | `high_cpm` or `any` |
| url | text | locker URL visited |
| redirect | text | destination redirect URL |
| success | bool | |
| reason | text | failure reason if any |
| error | text | full error message |
| video_reloads | int | |
| bw_kb | float | bandwidth used in KB |
| source | text | `local` or `gha_repo1` or `gha_repo2` |

---

## 4. Pages

### 4.1 Stats (`pages/1_stats.py`)

Displays metrics from `run_logs` table.

**Metrics shown:**
- Total runs today / this week
- Success rate (%) — overall and per repo
- Average bandwidth per run (KB)
- Failure breakdown by reason (`nav_failed`, `timeout`, etc.)
- Runs per hour chart (bar chart)
- Country distribution (top 10 countries)
- Device distribution

**Filters:**
- Date range picker
- Source filter (local / repo_1 / repo_2 / all)
- Success / fail / all toggle

**Log sync:**
- Button: "Sync local logs → Supabase" — reads all local JSONL files and upserts into `run_logs`

---

### 4.2 Link Manager (`pages/2_links.py`)

Manage destination URLs stored in Supabase.

**Features:**
- Table view of all destinations with columns: URL, category, active toggle, created date
- Add new links: paste one or multiple URLs → select category (entertainment / soundy) → Save
- Toggle active/inactive per link individually (checkbox in table)
- Delete links
- "Select All" / "Deselect All" buttons per category
- Active links are what the automation uses — saved persistently in DB

**Active link flow:**
When automation runs, `auto_admaven.py` queries Supabase for `active=true` destinations, formats them with the template, posts to paste.rs, saves the URL, and generates locker links.

---

### 4.3 Generate Locker Links (`pages/3_generate.py`)

Generate new admaven locker links from active destinations.

**Flow:**
1. Shows currently active destination links (pulled from Supabase)
2. Button: "Sync to paste.rs" — formats active links with template → posts to paste.rs → saves URL in `locker_links` table
3. Button: "Generate Locker Links" — calls locker generation for the paste.rs URL → saves result to `locker_links` table
4. Shows table of all generated locker links with: URL, paste.rs destination, created date
5. Copy button per locker link

---

### 4.4 Triggers (`pages/4_triggers.py`)

Trigger automation runs from the dashboard.

**Local run:**
- Input fields: count, concurrency, headed/headless toggle
- Button: "Run Locally" → spawns `auto_admaven.py` as a subprocess
- Live log tail: streams the subprocess stdout into the UI

**GHA — Repo 1:**
- Shows last 5 runs (status, timestamp, duration)
- Button: "Trigger Repo 1" → calls GitHub API `workflow_dispatch`
- Status refreshes every 10s after trigger

**GHA — Repo 2:**
- Same as above, independently controlled

---

## 5. Auth / Security

- Login gate in `app.py`: checks `st.session_state` for a password stored in `secrets.toml`
- Single shared password (personal tool, no multi-user needed)
- `secrets.toml` is gitignored — Streamlit Cloud reads secrets from its dashboard settings
- Supabase keys and GitHub token also stored in `secrets.toml`

---

## 6. Dark Theme

`.streamlit/config.toml`:
```toml
[theme]
base = "dark"
primaryColor = "#7C3AED"
backgroundColor = "#0F0F0F"
secondaryBackgroundColor = "#1A1A1A"
textColor = "#E5E5E5"
font = "monospace"
```

---

## 7. Automation Script Changes

`auto_admaven.py` changes:
- Remove `destinations.txt` / `paste_url.txt` / `daily_links.json` file reading
- Add `fetch_active_destinations()` — queries Supabase `destinations` table where `active=true`
- Add `log_run_to_supabase(entry)` — upserts each run result into `run_logs` table with `source` field set to `local` or `gha_repo1`/`gha_repo2` (passed via env var)
- GHA workflow passes `RUN_SOURCE=gha_repo1` env var so logs are tagged by source

---

## 8. Deployment

**Local:**
```bash
streamlit run dashboard/app.py
```

**Hosted (Streamlit Cloud):**
- Connect GitHub repo to Streamlit Cloud
- Set secrets in Streamlit Cloud dashboard (Supabase URL/key, GH token, password)
- Auto-deploys on push to `main`

---

## 9. What Gets Removed

- `destinations.txt` — replaced by Supabase `destinations` table
- `paste_url.txt` — stored in `locker_links` table
- `daily_links.json` — replaced by `locker_links` table
- `sync_destinations.py` — logic moves into `dashboard/lib/paste_rs.py`
- `destinations_template.txt` — template hardcoded in `paste_rs.py`

---

## 10. Out of Scope

- Multi-user access
- Earnings tracking (not currently logged)
- Mobile responsive design
- Real-time GHA log streaming (only status polling)
