import requests
from datetime import datetime, timezone


def trigger_workflow(repo: str, workflow_file: str, token: str) -> bool:
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"ref": "main"},
    )
    return resp.status_code == 204


def get_recent_runs(repo: str, workflow_file: str, token: str, limit: int = 5) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/runs"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        params={"per_page": limit},
    )
    if resp.status_code != 200:
        return []
    runs = resp.json().get("workflow_runs", [])
    result = []
    for r in runs:
        duration = None
        if r.get("updated_at") and r.get("created_at"):
            start = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
            duration = int((end - start).total_seconds())
        result.append({
            "id": r["id"],
            "status": r["status"],
            "conclusion": r["conclusion"],
            "created_at": r["created_at"],
            "duration_s": duration,
        })
    return result
