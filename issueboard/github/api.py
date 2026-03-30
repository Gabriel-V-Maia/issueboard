import time
import requests
from issueboard.models import Issue


def get_user(token: str) -> dict:
    r = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    return r.json()


def fetch_todo_issues(token: str, progress_cb=None) -> list:
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}
    issues = []
    seen   = set()

    searches = [
        "is:issue label:todo  involves:@me is:open",
        "is:issue label:TODO  involves:@me is:open",
        "is:issue label:wip   involves:@me is:open",
        "is:issue label:WIP   involves:@me is:open",
        "is:issue TODO  in:title involves:@me is:open",
        "is:issue WIP   in:title involves:@me is:open",
        "is:issue FIXME in:title involves:@me is:open",
        "is:issue TODO  in:title involves:@me is:closed",
        "is:issue WIP   in:title involves:@me is:closed",
    ]

    for q in searches:
        url = f"https://api.github.com/search/issues?q={requests.utils.quote(q)}&per_page=50"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                for item in r.json().get("items", []):
                    _add_issue(item, issues, seen)
        except Exception:
            pass
        if progress_cb:
            progress_cb()
        time.sleep(0.35)

    return issues


def _add_issue(item: dict, issues: list, seen: set):
    uid = item["id"]
    if uid in seen:
        return
    seen.add(uid)
    repo_url = item.get("repository_url", "")
    repo     = "/".join(repo_url.split("/")[-2:]) if repo_url else "unknown"
    labels   = [lb["name"] for lb in item.get("labels", [])]
    assignee = item["assignee"]["login"] if item.get("assignee") else None
    issues.append(Issue(
        id=uid,
        title=item["title"],
        url=item["html_url"],
        state=item.get("state", "open"),
        labels=labels,
        repo=repo,
        number=item["number"],
        assignee=assignee,
        created_at=item.get("created_at", "")[:10],
        body=(item.get("body") or "")[:200],
    ))