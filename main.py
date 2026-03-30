import customtkinter as ctk
import threading
import webbrowser
import json
import time
import requests
from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path

CLIENT_ID   = "Ov23li0DqEQROkXMdstK"
CONFIG_PATH = Path.home() / ".issueboard" / "config.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

SCOPES_PUBLIC  = "read:user public_repo"
SCOPES_PRIVATE = "read:user repo"

COLUMNS = ["Open", "In Progress", "Done"]

COLORS = {
    "bg":         "#0d1117",
    "surface":    "#161b22",
    "surface2":   "#1c2128",
    "border":     "#30363d",
    "accent":     "#58a6ff",
    "accent2":    "#3fb950",
    "accent3":    "#f78166",
    "warn":       "#d29922",
    "text":       "#e6edf3",
    "text_muted": "#8b949e",
    "col_open":   "#1f2d3d",
    "col_wip":    "#1f2b1f",
    "col_done":   "#2d1f2b",
    "tag_bg":     "#21262d",
}

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

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {}

def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

def device_flow_start(scopes: str) -> dict:
    r = requests.post(
        "https://github.com/login/device/code",
        headers={"Accept": "application/json"},
        data={"client_id": CLIENT_ID, "scope": scopes},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()

def device_flow_poll(device_code: str, interval: int,
                     stop_event: threading.Event,
                     on_token: Callable[[str], None],
                     on_error: Callable[[str], None]):
    while not stop_event.is_set():
        time.sleep(interval)
        try:
            r = requests.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id":   CLIENT_ID,
                    "device_code": device_code,
                    "grant_type":  "urn:ietf:params:oauth:grant-type:device_code",
                },
                timeout=10,
            )
            data = r.json()
        except Exception as e:
            on_error(str(e))
            return

        err = data.get("error")
        if err == "authorization_pending":
            continue
        elif err == "slow_down":
            interval += 5
            continue
        elif err == "expired_token":
            on_error("Code expired. Please try again.")
            return
        elif err == "access_denied":
            on_error("Access denied.")
            return
        elif "access_token" in data:
            on_token(data["access_token"])
            return
        else:
            on_error(f"Unexpected: {data}")
            return

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

def _add_issue(item, issues, seen):
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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def _label_color(name: str) -> str:
    n = name.lower()
    if "bug"  in n or "fix" in n:     return COLORS["accent3"]
    if "wip"  in n:                   return COLORS["warn"]
    if "todo" in n:                   return COLORS["accent"]
    if "enhance" in n or "feat" in n: return COLORS["accent2"]
    return COLORS["text_muted"]

def _btn(parent, text, command, primary=False, **kw):
    height        = kw.pop("height", 40)
    font_size     = kw.pop("font_size", 12)
    fg_color      = kw.pop("fg_color",     COLORS["accent"]  if primary else COLORS["surface2"])
    hover_color   = kw.pop("hover_color",  "#1f6feb"         if primary else COLORS["border"])
    text_color    = kw.pop("text_color",   "#0d1117"         if primary else COLORS["text"])
    border_width  = kw.pop("border_width", 0                 if primary else 1)
    border_color  = kw.pop("border_color", COLORS["border"])
    corner_radius = kw.pop("corner_radius", 8)

    return ctk.CTkButton(
        parent, text=text, command=command,
        height=height,
        font=ctk.CTkFont("Courier New", font_size, weight="bold" if primary else "normal"),
        fg_color=fg_color,
        hover_color=hover_color,
        text_color=text_color,
        border_width=border_width,
        border_color=border_color,
        corner_radius=corner_radius,
        **kw,
    )


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_token, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], **kw)
        self.on_token   = on_token
        self._stop_poll = threading.Event()
        self._dots      = 0
        self._scope_var = ctk.StringVar(value="public")
        self._build_idle()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _box(self, height=400):
        box = ctk.CTkFrame(self, fg_color=COLORS["surface"],
                           corner_radius=14, width=460, height=height)
        box.place(relx=0.5, rely=0.5, anchor="center")
        box.pack_propagate(False)
        return box

    def _build_idle(self):
        self._clear()
        self._stop_poll.set()
        self._scope_var = ctk.StringVar(value="public")
        box = self._box(500)

        ctk.CTkLabel(box, text="⬡",
                     font=ctk.CTkFont("Courier New", 48),
                     text_color=COLORS["accent"]).pack(pady=(28, 0))

        ctk.CTkLabel(box, text="issueboard",
                     font=ctk.CTkFont("Courier New", 26, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(4, 2))

        ctk.CTkLabel(box, text="your github TODOs, organized",
                     font=ctk.CTkFont("Courier New", 12),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 16))

        ctk.CTkFrame(box, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=40, pady=(0, 16))

        ctk.CTkLabel(box, text="repository access",
                     font=ctk.CTkFont("Courier New", 11, weight="bold"),
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=40, pady=(0, 8))

        opt_public = ctk.CTkFrame(box, fg_color=COLORS["surface2"], corner_radius=8)
        opt_public.pack(fill="x", padx=40, pady=(0, 6))

        ctk.CTkRadioButton(
            opt_public, text="",
            variable=self._scope_var, value="public",
            fg_color=COLORS["accent"], border_color=COLORS["border"],
            command=self._update_warn,
        ).pack(side="left", padx=(12, 6), pady=12)

        tf = ctk.CTkFrame(opt_public, fg_color="transparent")
        tf.pack(side="left", pady=10)
        ctk.CTkLabel(tf, text="Public repos only",
                     font=ctk.CTkFont("Courier New", 12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(tf, text="read:user  public_repo",
                     font=ctk.CTkFont("Courier New", 10),
                     text_color=COLORS["accent2"]).pack(anchor="w")

        opt_all = ctk.CTkFrame(box, fg_color=COLORS["surface2"], corner_radius=8)
        opt_all.pack(fill="x", padx=40, pady=(0, 6))

        ctk.CTkRadioButton(
            opt_all, text="",
            variable=self._scope_var, value="private",
            fg_color=COLORS["accent"], border_color=COLORS["border"],
            command=self._update_warn,
        ).pack(side="left", padx=(12, 6), pady=12)

        tf2 = ctk.CTkFrame(opt_all, fg_color="transparent")
        tf2.pack(side="left", pady=10)
        ctk.CTkLabel(tf2, text="Public + private repos",
                     font=ctk.CTkFont("Courier New", 12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(tf2, text="read:user  repo  (full repo access)",
                     font=ctk.CTkFont("Courier New", 10),
                     text_color=COLORS["warn"]).pack(anchor="w")

        self._warn_lbl = ctk.CTkLabel(box, text="",
                                      font=ctk.CTkFont("Courier New", 10),
                                      text_color=COLORS["warn"],
                                      wraplength=380, justify="left")
        self._warn_lbl.pack(padx=40, pady=(4, 0), anchor="w")

        self._err = ctk.CTkLabel(box, text="",
                                 font=ctk.CTkFont("Courier New", 11),
                                 text_color=COLORS["accent3"])
        self._err.pack(pady=(4, 0))

        _btn(box, "Login with GitHub →", self._start,
             primary=True, height=46, font_size=13).pack(fill="x", padx=40, pady=(10, 24))

    def _update_warn(self):
        if self._scope_var.get() == "private":
            self._warn_lbl.configure(
                text="⚠ GitHub requires full repo access to read private issues. No data is written."
            )
        else:
            self._warn_lbl.configure(text="")

    def _build_waiting(self, user_code, verification_uri):
        self._clear()
        box = self._box(460)

        ctk.CTkLabel(box, text="⬡ issueboard",
                     font=ctk.CTkFont("Courier New", 18, weight="bold"),
                     text_color=COLORS["accent"]).pack(pady=(28, 16))

        ctk.CTkLabel(box, text="1. Open this URL in your browser",
                     font=ctk.CTkFont("Courier New", 11),
                     text_color=COLORS["text_muted"]).pack()

        uf = ctk.CTkFrame(box, fg_color=COLORS["surface2"], corner_radius=8)
        uf.pack(fill="x", padx=40, pady=(6, 18))
        ctk.CTkLabel(uf, text=verification_uri,
                     font=ctk.CTkFont("Courier New", 13, weight="bold"),
                     text_color=COLORS["accent"]).pack(pady=10)

        ctk.CTkLabel(box, text="2. Enter this code",
                     font=ctk.CTkFont("Courier New", 11),
                     text_color=COLORS["text_muted"]).pack()

        cf = ctk.CTkFrame(box, fg_color=COLORS["tag_bg"], corner_radius=10)
        cf.pack(padx=40, pady=(8, 18))
        ctk.CTkLabel(cf, text=user_code,
                     font=ctk.CTkFont("Courier New", 34, weight="bold"),
                     text_color=COLORS["text"]).pack(padx=36, pady=14)

        self._wait_lbl = ctk.CTkLabel(box, text="Waiting for authorization…",
                                      font=ctk.CTkFont("Courier New", 11),
                                      text_color=COLORS["text_muted"])
        self._wait_lbl.pack(pady=(0, 10))
        self._dots = 0
        self._tick()

        _btn(box, "Open GitHub →",
             lambda: webbrowser.open(verification_uri),
             primary=True, height=38).pack(fill="x", padx=40, pady=(0, 6))

        _btn(box, "Cancel", self._build_idle,
             height=34, font_size=11).pack(fill="x", padx=40, pady=(0, 20))

    def _tick(self):
        if not self.winfo_exists():
            return
        try:
            dots = "." * (self._dots % 4)
            self._wait_lbl.configure(text=f"Waiting for authorization{dots}")
            self._dots += 1
            self.after(500, self._tick)
        except Exception:
            pass

    def _start(self):
        scopes = SCOPES_PRIVATE if self._scope_var.get() == "private" else SCOPES_PUBLIC
        try:
            data = device_flow_start(scopes)
        except Exception as e:
            self._err.configure(text=f"Network error: {e}")
            return

        device_code      = data["device_code"]
        user_code        = data["user_code"]
        verification_uri = data["verification_uri"]
        interval         = data.get("interval", 5)

        self._build_waiting(user_code, verification_uri)
        webbrowser.open(verification_uri)

        self._stop_poll = threading.Event()
        threading.Thread(
            target=device_flow_poll,
            args=(device_code, interval, self._stop_poll,
                  self._on_token, self._on_error),
            daemon=True,
        ).start()

    def _on_token(self, token):
        cfg = load_config()
        cfg["token"] = token
        save_config(cfg)
        self.after(0, lambda: self.on_token(token))

    def _on_error(self, msg):
        def _show():
            self._build_idle()
            self._err.configure(text=msg)
        self.after(0, _show)


class IssueCard(ctk.CTkFrame):
    def __init__(self, parent, issue: Issue, on_open, **kw):
        super().__init__(parent,
                         fg_color=COLORS["surface2"],
                         corner_radius=8,
                         border_width=1,
                         border_color=COLORS["border"],
                         **kw)
        self._issue   = issue
        self._on_open = on_open
        self.configure(cursor="hand2")
        self.bind("<Button-1>", self._click)

        def lbl(text, size, color, row, pady, bold=False, **extra):
            fg = extra.pop("fg_color", "transparent")
            w = ctk.CTkLabel(self, text=text,
                             font=ctk.CTkFont("Courier New", size,
                                              weight="bold" if bold else "normal"),
                             text_color=color, fg_color=fg, **extra)
            w.grid(row=row, column=0, sticky="w", padx=8, pady=pady)
            w.bind("<Button-1>", self._click)
            return w

        lbl(issue.repo, 10, COLORS["accent"], 0, (8, 2),
            fg_color=COLORS["tag_bg"], corner_radius=4)
        lbl(issue.title, 12, COLORS["text"], 1, 2,
            bold=True, wraplength=220, justify="left", anchor="w")

        if issue.labels:
            lf = ctk.CTkFrame(self, fg_color="transparent")
            lf.grid(row=2, column=0, sticky="w", padx=8, pady=2)
            lf.bind("<Button-1>", self._click)
            for lb in issue.labels[:3]:
                tag = ctk.CTkLabel(lf, text=lb,
                                   font=ctk.CTkFont("Courier New", 9),
                                   text_color=_label_color(lb),
                                   fg_color=COLORS["tag_bg"],
                                   corner_radius=4)
                tag.pack(side="left", padx=(0, 4))
                tag.bind("<Button-1>", self._click)

        lbl(f"#{issue.number}  ·  {issue.created_at}", 9,
            COLORS["text_muted"], 3, (2, 8))

        self.grid_columnconfigure(0, weight=1)

    def _click(self, _=None):
        self._on_open(self._issue)


class KanbanColumn(ctk.CTkFrame):
    _DOT = {"Open": COLORS["accent"], "In Progress": COLORS["warn"],  "Done": COLORS["accent2"]}
    _BG  = {"Open": COLORS["col_open"], "In Progress": COLORS["col_wip"], "Done": COLORS["col_done"]}

    def __init__(self, parent, title: str, on_open, **kw):
        super().__init__(parent, fg_color=self._BG[title], corner_radius=10, **kw)
        self._cards = []

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(hdr, text="●", font=ctk.CTkFont(size=10),
                     text_color=self._DOT[title]).pack(side="left")
        ctk.CTkLabel(hdr, text=title.upper(),
                     font=ctk.CTkFont("Courier New", 11, weight="bold"),
                     text_color=COLORS["text"]).pack(side="left", padx=6)

        self._count = ctk.CTkLabel(hdr, text="0",
                                   font=ctk.CTkFont("Courier New", 10),
                                   text_color=COLORS["text_muted"])
        self._count.pack(side="right")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                              scrollbar_button_color=COLORS["border"])
        self._scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._on_open = on_open

    def clear(self):
        for c in self._cards:
            c.destroy()
        self._cards.clear()
        self._count.configure(text="0")

    def add(self, issue: Issue):
        card = IssueCard(self._scroll, issue, self._on_open)
        card.pack(fill="x", pady=(0, 6))
        self._cards.append(card)
        self._count.configure(text=str(len(self._cards)))


class DetailWindow(ctk.CTkToplevel):
    def __init__(self, parent, issue: Issue, on_wip_toggle, **kw):
        super().__init__(parent, **kw)
        self.title(f"#{issue.number} — {issue.repo}")
        self.configure(fg_color=COLORS["bg"])
        self.geometry("540x460")
        self.resizable(False, False)
        self._issue         = issue
        self._on_wip_toggle = on_wip_toggle
        self._build()
        self.lift()
        self.focus()

    def _build(self):
        i = self._issue

        ctk.CTkLabel(self, text=i.repo,
                     font=ctk.CTkFont("Courier New", 11),
                     text_color=COLORS["accent"]).pack(anchor="w", padx=24, pady=(20, 2))

        ctk.CTkLabel(self, text=f"#{i.number}  {i.title}",
                     font=ctk.CTkFont("Courier New", 14, weight="bold"),
                     text_color=COLORS["text"],
                     wraplength=490, justify="left").pack(anchor="w", padx=24, pady=4)

        if i.labels:
            lf = ctk.CTkFrame(self, fg_color="transparent")
            lf.pack(anchor="w", padx=24, pady=(0, 4))
            for lb in i.labels:
                ctk.CTkLabel(lf, text=lb,
                             font=ctk.CTkFont("Courier New", 10),
                             text_color=_label_color(lb),
                             fg_color=COLORS["tag_bg"],
                             corner_radius=4).pack(side="left", padx=(0, 6))

        meta = []
        if i.assignee:   meta.append(f"assigned → {i.assignee}")
        if i.created_at: meta.append(f"opened {i.created_at}")
        if meta:
            ctk.CTkLabel(self, text="  ·  ".join(meta),
                         font=ctk.CTkFont("Courier New", 10),
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=24, pady=(0, 8))

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=24)

        ctk.CTkLabel(self, text=i.body or "(no description)",
                     font=ctk.CTkFont("Courier New", 11),
                     text_color=COLORS["text_muted"],
                     wraplength=490, justify="left").pack(anchor="w", padx=24, pady=14)

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=24, pady=(4, 0))

        _btn(bf, "Open on GitHub ↗",
             lambda: webbrowser.open(i.url),
             primary=True, height=38).pack(side="left", padx=(0, 8))

        wip_lbl = "↳ Mark In Progress" if i.state == "open" else "↩ Move to Open"
        _btn(bf, wip_lbl, self._toggle, height=38).pack(side="left")

        _btn(bf, "Close", self.destroy, height=38,
             fg_color="transparent",
             hover_color=COLORS["surface2"],
             text_color=COLORS["text_muted"]).pack(side="right")

    def _toggle(self):
        self._on_wip_toggle(self._issue)
        self.destroy()


class BoardScreen(ctk.CTkFrame):
    def __init__(self, parent, token: str, on_logout, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], **kw)
        self.token     = token
        self.on_logout = on_logout
        self._issues   = []
        self._wip_ids  = set()
        self._filter   = "All"
        self._build()
        self._load()

    def _build(self):
        bar = ctk.CTkFrame(self, fg_color=COLORS["surface"], height=52, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="⬡ issueboard",
                     font=ctk.CTkFont("Courier New", 16, weight="bold"),
                     text_color=COLORS["accent"]).pack(side="left", padx=20)

        self._user_lbl = ctk.CTkLabel(bar, text="",
                                      font=ctk.CTkFont("Courier New", 11),
                                      text_color=COLORS["text_muted"])
        self._user_lbl.pack(side="left", padx=4)

        self._filter_var = ctk.StringVar(value="All")
        self._filter_menu = ctk.CTkOptionMenu(
            bar, values=["All"],
            variable=self._filter_var,
            font=ctk.CTkFont("Courier New", 11),
            fg_color=COLORS["surface2"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface"],
            dropdown_text_color=COLORS["text"],
            width=210,
            command=self._on_filter,
        )
        self._filter_menu.pack(side="left", padx=12)

        self._status = ctk.CTkLabel(bar, text="",
                                    font=ctk.CTkFont("Courier New", 11),
                                    text_color=COLORS["text_muted"])
        self._status.pack(side="left", padx=4)

        _btn(bar, "↻", self._load, height=32, width=36, font_size=14).pack(side="right", padx=8)
        _btn(bar, "Logout", self._do_logout, height=32, font_size=11,
             fg_color="transparent",
             hover_color=COLORS["surface2"],
             text_color=COLORS["text_muted"]).pack(side="right", padx=(0, 4))

        self._progress = ctk.CTkProgressBar(self,
                                            fg_color=COLORS["surface"],
                                            progress_color=COLORS["accent"])
        self._progress.set(0)

        board = ctk.CTkFrame(self, fg_color="transparent")
        board.pack(fill="both", expand=True, padx=16, pady=12)
        board.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        board.grid_rowconfigure(0, weight=1)

        self._cols = {}
        for i, name in enumerate(COLUMNS):
            col = KanbanColumn(board, name, self._open_issue)
            col.grid(row=0, column=i, sticky="nsew", padx=6)
            self._cols[name] = col

    def _load(self):
        self._status.configure(text="fetching…", text_color=COLORS["text_muted"])
        self._progress.pack(fill="x")
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        for col in self._cols.values():
            col.clear()
        threading.Thread(target=self._load_user,   daemon=True).start()
        threading.Thread(target=self._load_issues, daemon=True).start()

    def _load_user(self):
        try:
            user  = get_user(self.token)
            login = user.get("login", "")
            self.after(0, lambda: self._user_lbl.configure(text=f"@{login}"))
        except Exception:
            pass

    def _load_issues(self):
        total = 9
        done  = [0]

        def tick():
            done[0] += 1
            f = done[0] / total
            self.after(0, lambda v=f: self._progress.set(v))

        issues = fetch_todo_issues(self.token, progress_cb=tick)
        self.after(0, lambda: self._on_loaded(issues))

    def _on_loaded(self, issues):
        self._progress.stop()
        self._progress.pack_forget()
        self._issues = issues
        repos = sorted({i.repo for i in issues})
        self._filter_menu.configure(values=["All"] + repos)
        self._render()
        n = len(issues)
        self._status.configure(
            text=f"{n} issue{'s' if n != 1 else ''} found",
            text_color=COLORS["text_muted"],
        )

    def _on_filter(self, val):
        self._filter = val
        self._render()

    def _render(self):
        for col in self._cols.values():
            col.clear()
        issues = self._issues
        if self._filter != "All":
            issues = [i for i in issues if i.repo == self._filter]
        for issue in issues:
            self._cols[self._classify(issue)].add(issue)

    def _classify(self, issue: Issue) -> str:
        if issue.state == "closed":
            return "Done"
        if issue.id in self._wip_ids:
            return "In Progress"
        if any(lb.lower() in ("in progress", "wip", "doing") for lb in issue.labels):
            return "In Progress"
        return "Open"

    def _open_issue(self, issue: Issue):
        DetailWindow(self, issue, on_wip_toggle=self._toggle_wip)

    def _toggle_wip(self, issue: Issue):
        if issue.id in self._wip_ids:
            self._wip_ids.discard(issue.id)
        else:
            self._wip_ids.add(issue.id)
        self._render()

    def _do_logout(self):
        cfg = load_config()
        cfg.pop("token", None)
        save_config(cfg)
        self.on_logout()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("issueboard")
        self.geometry("1020x700")
        self.minsize(820, 560)
        self.configure(fg_color=COLORS["bg"])
        self._frame = None

        token = load_config().get("token")
        if token:
            self._show_board(token)
        else:
            self._show_login()

    def _swap(self, frame):
        if self._frame:
            self._frame.pack_forget()
            self._frame.destroy()
        self._frame = frame
        frame.pack(fill="both", expand=True)

    def _show_login(self):
        self._swap(LoginScreen(self, on_token=self._show_board))

    def _show_board(self, token: str):
        self._swap(BoardScreen(self, token=token, on_logout=self._show_login))


if __name__ == "__main__":
    App().mainloop()
