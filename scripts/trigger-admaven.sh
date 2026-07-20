#!/usr/bin/env bash
# Trigger the GHA admaven workflow via workflow_dispatch.
# Called by cron on the VPS every hour (replaces GHA's own schedule).
#
# Setup:
#   1. put GH_TOKEN + GH_REPO in /etc/cinemap.env (chmod 600)
#   2. copy this script to /opt/cinemap/trigger-admaven.sh, chmod +x
#   3. crontab -e:  0 * * * * /opt/cinemap/trigger-admaven.sh
set -eu
source /etc/cinemap.env

LOG=/var/log/cinemap-trigger.log
STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

HTTP_CODE=$(curl -sS -o /tmp/gh-resp -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$GH_REPO/actions/workflows/admaven.yml/dispatches" \
  -d '{"ref":"main"}')

if [ "$HTTP_CODE" = "204" ]; then
  echo "$STAMP  ok" >> "$LOG"
else
  echo "$STAMP  FAIL http=$HTTP_CODE body=$(cat /tmp/gh-resp)" >> "$LOG"
  exit 1
fi
