"""
issueboard — GitHub TODO Issue Kanban
MVP: OAuth login → scan repos → pull TODO issues → kanban board
"""

import customtkinter as ctk
import threading
import webbrowser
import http.server
import urllib.parse
import json
import os
import time
import requests
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

APP_NAME = "issueboard"
CONFIG_PATH = Path.home() / ".issueboard" / "config.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

TODO_KEYWORDS = ["TODO", "todo", "WIP", "wip", "FIXME", "fixme", "HACK", "hack"]
TODO_LABELS   = ["todo", "TODO", "wip", "WIP", "enhancement", "bug", "help wanted"]

COLUMNS = ["Open", "In Progress", "Done"]
COLUMN_STATES = {
    "Open":        "open",
    "In Progress": "open",
    "Done":        "closed",
}

COLORS = {
    "bg":          "#0d1117",
    "surface":     "#161b22",
    "surface2":    "#1c2128",
    "border":      "#30363d",
    "accent":      "#58a6ff",
    "accent2":     "#3fb950",
    "accent3":     "#f78166",
    "text":        "#e6edf3",
    "text_muted":  "#8b949e",
    "col_open":    "#1f2d3d",
    "col_wip":     "#1f2b1f",
    "col_done":    "#2d1f2b",
    "tag_bg":      "#21262d",
}

# ─── Data ─────────────────────────────────────────────────────────────────────

@dataclass
class Issue:
    id:         int
    title:      str
    url:        str
    state:      str
    labels:     list
    repo:       str
    number:     int
    assignee:   Optional[str] = None
    created_at: str = ""
    body:       str = ""
    wip:        bool = False       # manually moved to In Progress

# ─── Config persistence ───────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {}

def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

# ─── GitHub OAuth helpers ─────────────────────────────────────────────────────

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            OAuthHandler.code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
<html><body style="background:#0d1117;color:#e6edf3;font-family:monospace;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="text-align:center">
  <div style="font-size:2rem;margin-bottom:1rem">&#10003;</div>
  <h2 style="color:#58a6ff;margin:0">issueboard authorized</h2>
  <p style="color:#8b949e">you can close this tab</p>
</div></body></html>""")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, *args):
        pass


def exchange_token(client_id: str, client_secret: str, code: str) -> Optional[str]:
    r = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={"client_id": client_id, "client_secret": client_secret, "code": code},
        timeout=10,
    )
    return r.json().get("access_token")


def get_user(token: str) -> dict:
    r = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    return r.json()


def fetch_todo_issues(token: str, progress_cb=None) -> list[Issue]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    issues: list[Issue] = []
    seen = set()

    # Search by label
    for label in ["todo", "TODO", "wip", "WIP"]:
        url = f"https://api.github.com/search/issues?q=is:issue+label:{label}+author:@me+is:open&per_page=50"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                for item in r.json().get("items", []):
                    _add_issue(item, issues, seen)
        except Exception:
            pass
        if progress_cb:
            progress_cb()

    # Search by title keyword in user's repos
    for kw in ["TODO", "WIP", "FIXME"]:
        for state in ["open", "closed"]:
            url = (
                f"https://api.github.com/search/issues"
                f"?q=is:issue+{kw}+in:title+involves:@me+is:{state}&per_page=30"
            )
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    for item in r.json().get("items", []):
                        _add_issue(item, issues, seen)
            except Exception:
                pass
            if progress_cb:
                progress_cb()
            time.sleep(0.3)   # respect rate limit

    return issues


def _add_issue(item: dict, issues: list, seen: set):
    uid = item["id"]
    if uid in seen:
        return
    seen.add(uid)
    repo_url = item.get("repository_url", "")
    repo = "/".join(repo_url.split("/")[-2:]) if repo_url else "unknown"
    labels = [l["name"] for l in item.get("labels", [])]
    assignee = None
    if item.get("assignee"):
        assignee = item["assignee"]["login"]
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

# ─── UI Components ────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class IssueCard(ctk.CTkFrame):
    def __init__(self, parent, issue: Issue, on_open, col_color, **kw):
        super().__init__(
            parent,
            fg_color=COLORS["surface2"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            **kw
        )
        self.issue = issue
        self.configure(cursor="hand2")

        self.bind("<Button-1>", lambda e: on_open(issue))

        # Repo tag
        repo_lbl = ctk.CTkLabel(
            self, text=issue.repo,
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["accent"],
            fg_color=COLORS["tag_bg"],
            corner_radius=4,
        )
        repo_lbl.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        repo_lbl.bind("<Button-1>", lambda e: on_open(issue))

        # Title
        title_lbl = ctk.CTkLabel(
            self, text=issue.title,
            font=ctk.CTkFont("Courier New", 12, weight="bold"),
            text_color=COLORS["text"],
            wraplength=220,
            justify="left",
            anchor="w",
        )
        title_lbl.grid(row=1, column=0, sticky="w", padx=8, pady=2)
        title_lbl.bind("<Button-1>", lambda e: on_open(issue))

        # Labels row
        if issue.labels:
            lf = ctk.CTkFrame(self, fg_color="transparent")
            lf.grid(row=2, column=0, sticky="w", padx=8, pady=2)
            lf.bind("<Button-1>", lambda e: on_open(issue))
            for lb in issue.labels[:3]:
                c = _label_color(lb)
                tag = ctk.CTkLabel(
                    lf, text=lb,
                    font=ctk.CTkFont("Courier New", 9),
                    text_color=c,
                    fg_color=COLORS["tag_bg"],
                    corner_radius=4,
                )
                tag.pack(side="left", padx=(0, 4))
                tag.bind("<Button-1>", lambda e: on_open(issue))

        # Footer
        footer = ctk.CTkLabel(
            self,
            text=f"#{issue.number}  ·  {issue.created_at}",
            font=ctk.CTkFont("Courier New", 9),
            text_color=COLORS["text_muted"],
        )
        footer.grid(row=3, column=0, sticky="w", padx=8, pady=(2, 8))
        footer.bind("<Button-1>", lambda e: on_open(issue))

        self.grid_columnconfigure(0, weight=1)


def _label_color(name: str) -> str:
    n = name.lower()
    if "bug" in n or "fix" in n:    return COLORS["accent3"]
    if "wip" in n:                  return "#d29922"
    if "todo" in n:                 return COLORS["accent"]
    if "enhance" in n or "feat" in n: return COLORS["accent2"]
    return COLORS["text_muted"]


class KanbanColumn(ctk.CTkFrame):
    def __init__(self, parent, title: str, color: str, on_open, **kw):
        super().__init__(parent, fg_color=color, corner_radius=10, **kw)
        self.title = title
        self.on_open = on_open
        self.cards: list[IssueCard] = []

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 6))

        dot = ctk.CTkLabel(
            hdr,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=self._dot_color(),
        )
        dot.pack(side="left")

        self.title_lbl = ctk.CTkLabel(
            hdr,
            text=title.upper(),
            font=ctk.CTkFont("Courier New", 11, weight="bold"),
            text_color=COLORS["text"],
        )
        self.title_lbl.pack(side="left", padx=6)

        self.count_lbl = ctk.CTkLabel(
            hdr,
            text="0",
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["text_muted"],
        )
        self.count_lbl.pack(side="right")

        # Scrollable area for cards
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self.scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _dot_color(self):
        if self.title == "Open":       return COLORS["accent"]
        if self.title == "In Progress": return "#d29922"
        return COLORS["accent2"]

    def clear(self):
        for card in self.cards:
            card.destroy()
        self.cards.clear()
        self.count_lbl.configure(text="0")

    def add_issue(self, issue: Issue):
        col_color = self.cget("fg_color")
        card = IssueCard(self.scroll, issue, self.on_open, col_color)
        card.pack(fill="x", pady=(0, 6))
        self.cards.append(card)
        self.count_lbl.configure(text=str(len(self.cards)))


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_token, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], **kw)
        self.on_token = on_token
        self.cfg = load_config()
        self._build()

    def _build(self):
        # Center container — fixed size so entries never collapse
        box = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=12,
                           width=460, height=580)
        box.place(relx=0.5, rely=0.5, anchor="center")
        box.pack_propagate(False)

        # Logo / title
        ctk.CTkLabel(
            box, text="⬡ issueboard",
            font=ctk.CTkFont("Courier New", 28, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(32, 4))

        ctk.CTkLabel(
            box,
            text="github TODO kanban — for developers",
            font=ctk.CTkFont("Courier New", 12),
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 20))

        # Separator
        ctk.CTkFrame(box, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=32, pady=(0, 20))

        # Input: client id
        ctk.CTkLabel(box, text="GitHub OAuth App — Client ID",
                     font=ctk.CTkFont("Courier New", 11),
                     text_color=COLORS["text_muted"], anchor="w").pack(fill="x", padx=32)
        self.client_id_entry = ctk.CTkEntry(
            box, height=42,
            font=ctk.CTkFont("Courier New", 13),
            fg_color=COLORS["surface2"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            placeholder_text="Ghid_xxxxxxxxxxxx",
        )
        self.client_id_entry.pack(fill="x", padx=32, pady=(6, 14))
        self.client_id_entry.bind("<Return>", lambda e: self.client_secret_entry.focus())
        if self.cfg.get("client_id"):
            self.client_id_entry.insert(0, self.cfg["client_id"])

        # Input: client secret
        ctk.CTkLabel(box, text="Client Secret",
                     font=ctk.CTkFont("Courier New", 11),
                     text_color=COLORS["text_muted"], anchor="w").pack(fill="x", padx=32)
        self.client_secret_entry = ctk.CTkEntry(
            box, height=42, show="*",
            font=ctk.CTkFont("Courier New", 13),
            fg_color=COLORS["surface2"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            placeholder_text="••••••••••••••••",
        )
        self.client_secret_entry.pack(fill="x", padx=32, pady=(6, 6))
        self.client_secret_entry.bind("<Return>", lambda e: self._start_oauth())
        if self.cfg.get("client_secret"):
            self.client_secret_entry.insert(0, self.cfg["client_secret"])

        # Status
        self.status = ctk.CTkLabel(
            box, text="",
            font=ctk.CTkFont("Courier New", 11),
            text_color=COLORS["text_muted"],
        )
        self.status.pack(pady=(6, 0))

        # Login button
        self.btn = ctk.CTkButton(
            box, text="Login with GitHub →",
            height=44,
            font=ctk.CTkFont("Courier New", 13, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#1f6feb",
            text_color="#0d1117",
            corner_radius=8,
            command=self._start_oauth,
        )
        self.btn.pack(fill="x", padx=32, pady=(10, 10))

        # Or use PAT
        ctk.CTkLabel(box, text="— or use a Personal Access Token —",
                     font=ctk.CTkFont("Courier New", 10),
                     text_color=COLORS["text_muted"]).pack(pady=(4, 4))

        self.pat_entry = ctk.CTkEntry(
            box, height=42, show="*",
            font=ctk.CTkFont("Courier New", 13),
            fg_color=COLORS["surface2"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            placeholder_text="ghp_xxxxxxxxxxxxxxxxxxxx",
        )
        self.pat_entry.pack(fill="x", padx=32, pady=(0, 6))
        self.pat_entry.bind("<Return>", lambda e: self._use_pat())

        ctk.CTkButton(
            box, text="Use Token",
            height=40,
            font=ctk.CTkFont("Courier New", 12),
            fg_color=COLORS["surface2"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            command=self._use_pat,
        ).pack(fill="x", padx=32, pady=(0, 32))

    def _set_status(self, msg: str, color: str = None):
        self.status.configure(text=msg, text_color=color or COLORS["text_muted"])

    def _use_pat(self):
        token = self.pat_entry.get().strip()
        if not token:
            self._set_status("Enter a Personal Access Token first.", COLORS["accent3"])
            return
        cfg = load_config()
        cfg["token"] = token
        save_config(cfg)
        self.on_token(token)

    def _start_oauth(self):
        client_id = self.client_id_entry.get().strip()
        client_secret = self.client_secret_entry.get().strip()
        if not client_id or not client_secret:
            self._set_status("Fill in Client ID and Secret.", COLORS["accent3"])
            return
        cfg = load_config()
        cfg["client_id"] = client_id
        cfg["client_secret"] = client_secret
        save_config(cfg)
        self._set_status("Opening browser…")
        self.btn.configure(state="disabled")
        threading.Thread(target=self._oauth_flow,
                         args=(client_id, client_secret), daemon=True).start()

    def _oauth_flow(self, client_id: str, client_secret: str):
        auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}&scope=repo,read:user&redirect_uri=http://localhost:37242/callback"
        )
        webbrowser.open(auth_url)
        self.after(500, lambda: self._set_status("Waiting for GitHub authorization…"))

        OAuthHandler.code = None
        try:
            srv = http.server.HTTPServer(("localhost", 37242), OAuthHandler)
            srv.timeout = 120
            while OAuthHandler.code is None:
                srv.handle_request()
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Server error: {e}", COLORS["accent3"]))
            self.after(0, lambda: self.btn.configure(state="normal"))
            return

        code = OAuthHandler.code
        self.after(0, lambda: self._set_status("Exchanging token…"))
        token = exchange_token(client_id, client_secret, code)
        if not token:
            self.after(0, lambda: self._set_status("Token exchange failed.", COLORS["accent3"]))
            self.after(0, lambda: self.btn.configure(state="normal"))
            return

        cfg = load_config()
        cfg["token"] = token
        save_config(cfg)
        self.after(0, lambda: self.on_token(token))


class BoardScreen(ctk.CTkFrame):
    def __init__(self, parent, token: str, on_logout, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], **kw)
        self.token = token
        self.on_logout = on_logout
        self.issues: list[Issue] = []
        self.filter_repo = "All"
        self.wip_ids: set = set()
        self._build()
        self._load()

    def _build(self):
        # Top bar
        topbar = ctk.CTkFrame(self, fg_color=COLORS["surface"], height=52, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        ctk.CTkLabel(
            topbar, text="⬡ issueboard",
            font=ctk.CTkFont("Courier New", 16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=20)

        # Filter bar
        self.filter_var = ctk.StringVar(value="All")
        self.filter_menu = ctk.CTkOptionMenu(
            topbar,
            values=["All"],
            variable=self.filter_var,
            font=ctk.CTkFont("Courier New", 11),
            fg_color=COLORS["surface2"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface"],
            dropdown_text_color=COLORS["text"],
            width=200,
            command=self._on_filter,
        )
        self.filter_menu.pack(side="left", padx=12)

        self.status_lbl = ctk.CTkLabel(
            topbar, text="",
            font=ctk.CTkFont("Courier New", 11),
            text_color=COLORS["text_muted"],
        )
        self.status_lbl.pack(side="left", padx=8)

        ctk.CTkButton(
            topbar, text="↻ Refresh",
            width=90, height=32,
            font=ctk.CTkFont("Courier New", 11),
            fg_color=COLORS["surface2"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=6,
            command=self._load,
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            topbar, text="Logout",
            width=70, height=32,
            font=ctk.CTkFont("Courier New", 11),
            fg_color="transparent",
            hover_color=COLORS["surface2"],
            text_color=COLORS["text_muted"],
            corner_radius=6,
            command=self.on_logout,
        ).pack(side="right", padx=(0, 4))

        # Progress bar (hidden until loading)
        self.progress = ctk.CTkProgressBar(self, fg_color=COLORS["surface"], progress_color=COLORS["accent"])
        self.progress.set(0)

        # Kanban board
        board = ctk.CTkFrame(self, fg_color="transparent")
        board.pack(fill="both", expand=True, padx=16, pady=12)
        board.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        board.grid_rowconfigure(0, weight=1)

        col_colors = [COLORS["col_open"], COLORS["col_wip"], COLORS["col_done"]]
        self.columns: dict[str, KanbanColumn] = {}
        for i, (name, color) in enumerate(zip(COLUMNS, col_colors)):
            col = KanbanColumn(board, name, color, self._open_issue)
            col.grid(row=0, column=i, sticky="nsew", padx=6)
            self.columns[name] = col

    def _set_status(self, msg: str, color=None):
        self.status_lbl.configure(text=msg, text_color=color or COLORS["text_muted"])

    def _load(self):
        self._set_status("fetching issues…")
        self.progress.pack(fill="x", padx=0, pady=0)
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        for col in self.columns.values():
            col.clear()
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        steps = [0]
        total = 9  # number of search calls

        def tick():
            steps[0] += 1
            self.after(0, lambda: self.progress.set(steps[0] / total))

        issues = fetch_todo_issues(self.token, progress_cb=tick)
        self.after(0, lambda: self._on_loaded(issues))

    def _on_loaded(self, issues: list[Issue]):
        self.progress.stop()
        self.progress.pack_forget()
        self.issues = issues

        repos = sorted(set(i.repo for i in issues))
        self.filter_menu.configure(values=["All"] + repos)

        self._render()
        self._set_status(f"{len(issues)} issues found")

    def _on_filter(self, val: str):
        self.filter_repo = val
        self._render()

    def _render(self):
        for col in self.columns.values():
            col.clear()

        filtered = self.issues
        if self.filter_repo != "All":
            filtered = [i for i in self.issues if i.repo == self.filter_repo]

        for issue in filtered:
            col_name = self._classify(issue)
            self.columns[col_name].add_issue(issue)

    def _classify(self, issue: Issue) -> str:
        if issue.id in self.wip_ids:
            return "In Progress"
        if issue.state == "closed":
            return "Done"
        labels_lower = [l.lower() for l in issue.labels]
        if any(l in labels_lower for l in ["in progress", "wip", "doing"]):
            return "In Progress"
        return "Open"

    def _open_issue(self, issue: Issue):
        DetailWindow(self, issue, self.token,
                     on_wip_toggle=self._toggle_wip)

    def _toggle_wip(self, issue: Issue):
        if issue.id in self.wip_ids:
            self.wip_ids.discard(issue.id)
        else:
            self.wip_ids.add(issue.id)
        self._render()


class DetailWindow(ctk.CTkToplevel):
    def __init__(self, parent, issue: Issue, token: str, on_wip_toggle=None, **kw):
        super().__init__(parent, **kw)
        self.title(f"#{issue.number} — {issue.repo}")
        self.configure(fg_color=COLORS["bg"])
        self.geometry("540x440")
        self.resizable(False, False)
        self.issue = issue
        self.token = token
        self.on_wip_toggle = on_wip_toggle
        self._build()
        self.lift()
        self.focus()

    def _build(self):
        pad = {"padx": 24, "pady": 6}

        # Repo
        ctk.CTkLabel(
            self, text=self.issue.repo,
            font=ctk.CTkFont("Courier New", 11),
            text_color=COLORS["accent"],
        ).pack(anchor="w", padx=24, pady=(20, 2))

        # Title
        ctk.CTkLabel(
            self,
            text=f"#{self.issue.number}  {self.issue.title}",
            font=ctk.CTkFont("Courier New", 14, weight="bold"),
            text_color=COLORS["text"],
            wraplength=490,
            justify="left",
        ).pack(anchor="w", **pad)

        # Labels
        if self.issue.labels:
            lf = ctk.CTkFrame(self, fg_color="transparent")
            lf.pack(anchor="w", padx=24, pady=(0, 4))
            for lb in self.issue.labels:
                ctk.CTkLabel(
                    lf, text=lb,
                    font=ctk.CTkFont("Courier New", 10),
                    text_color=_label_color(lb),
                    fg_color=COLORS["tag_bg"],
                    corner_radius=4,
                ).pack(side="left", padx=(0, 6))

        # Meta
        meta = []
        if self.issue.assignee:  meta.append(f"assigned → {self.issue.assignee}")
        if self.issue.created_at: meta.append(f"opened {self.issue.created_at}")
        if meta:
            ctk.CTkLabel(
                self, text="  ·  ".join(meta),
                font=ctk.CTkFont("Courier New", 10),
                text_color=COLORS["text_muted"],
            ).pack(anchor="w", padx=24, pady=(0, 8))

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=24)

        # Body preview
        body_text = self.issue.body or "(no description)"
        ctk.CTkLabel(
            self,
            text=body_text,
            font=ctk.CTkFont("Courier New", 11),
            text_color=COLORS["text_muted"],
            wraplength=490,
            justify="left",
        ).pack(anchor="w", padx=24, pady=12)

        # Buttons
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=24, pady=(8, 0))

        ctk.CTkButton(
            bf, text="Open on GitHub ↗",
            height=38,
            font=ctk.CTkFont("Courier New", 12),
            fg_color=COLORS["accent"],
            hover_color="#1f6feb",
            text_color="#0d1117",
            corner_radius=8,
            command=lambda: webbrowser.open(self.issue.url),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bf, text="Mark In Progress" if self.issue.state == "open" else "Reopen",
            height=38,
            font=ctk.CTkFont("Courier New", 12),
            fg_color=COLORS["surface2"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            command=self._toggle_wip,
        ).pack(side="left")

        ctk.CTkButton(
            bf, text="Close",
            height=38,
            font=ctk.CTkFont("Courier New", 12),
            fg_color="transparent",
            hover_color=COLORS["surface2"],
            text_color=COLORS["text_muted"],
            corner_radius=8,
            command=self.destroy,
        ).pack(side="right")

    def _toggle_wip(self):
        if self.on_wip_toggle:
            self.on_wip_toggle(self.issue)
        self.destroy()


# ─── App root ─────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("issueboard")
        self.geometry("980x680")
        self.minsize(800, 560)
        self.configure(fg_color=COLORS["bg"])

        self.current_frame: Optional[ctk.CTkFrame] = None
        cfg = load_config()
        token = cfg.get("token")
        if token:
            self._show_board(token)
        else:
            self._show_login()

    def _clear(self):
        if self.current_frame:
            self.current_frame.pack_forget()
            self.current_frame.destroy()
            self.current_frame = None

    def _show_login(self):
        self._clear()
        frame = LoginScreen(self, on_token=self._show_board)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

    def _show_board(self, token: str):
        self._clear()
        frame = BoardScreen(self, token=token, on_logout=self._logout)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

    def _logout(self):
        cfg = load_config()
        cfg.pop("token", None)
        save_config(cfg)
        self._show_login()


if __name__ == "__main__":
    app = App()
    app.mainloop()
