import threading
import customtkinter as ctk
from issueboard.models import Issue
from issueboard.config import load_config, save_config
from issueboard.github.api import get_user, fetch_todo_issues
from issueboard.ui.colors import COLORS, btn
from issueboard.ui.column import KanbanColumn, COLUMNS
from issueboard.ui.detail import DetailWindow


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

        btn(bar, "↻", self._load, height=32, width=36, font_size=14).pack(side="right", padx=8)
        btn(bar, "Logout", self._do_logout, height=32, font_size=11,
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