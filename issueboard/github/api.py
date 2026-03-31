import time
import requests
import threading

from issueboard.models import Issue
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_user(token: str) -> dict:
    r = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    return r.json()


def fetch_todo_issues(token: str, progress_cb=None) -> list[Issue]:
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}
    issues = []
    seen   = set()
    lock   = threading.Lock()

    def do_search(q):
        url = f"https://api.github.com/search/issues?q={requests.utils.quote(q)}&per_page=50"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.json().get("items", [])
        except Exception:
            pass
        return []

    searches = [
        "is:issue involves:@me is:open   label:todo",
        "is:issue involves:@me is:open   label:wip",
        'is:issue involves:@me is:open   in:title TODO',
        'is:issue involves:@me is:open   in:title WIP',
        'is:issue involves:@me is:open   in:title FIXME',
        'is:issue involves:@me is:closed in:title TODO',
        'is:issue involves:@me is:closed in:title WIP',
    ]

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(do_search, q): q for q in searches}
        for future in as_completed(futures):
            items = future.result()
            with lock:
                for item in items:
                    _add_issue(item, issues, seen)
            if progress_cb:
                progress_cb()

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