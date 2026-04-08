import threading
import webbrowser
import customtkinter as ctk
from issueboard.models import Issue
from issueboard.ui.colors import COLORS, FONT, FONT_SIZE, SP, label_color, btn


class DetailWindow(ctk.CTkToplevel):
    def __init__(self, parent, issue: Issue, on_wip_toggle, on_close_issue=None, **kw):
        super().__init__(parent, **kw)
        self.title(f"#{issue.number} — {issue.repo}")
        self.configure(fg_color=COLORS["bg"])
        self.geometry("540x500")
        self.resizable(False, False)
        self._issue          = issue
        self._on_wip_toggle  = on_wip_toggle
        self._on_close_issue = on_close_issue
        self._working        = False
        self._build()
        self.after(10, self._focus)

    def _focus(self):
        self.lift()
        self.focus_force()

    def _build(self):
        i = self._issue

        ctk.CTkLabel(self, text=i.repo,
                     font=ctk.CTkFont(FONT, FONT_SIZE["sm"]),
                     text_color=COLORS["accent"]).pack(
                         anchor="w", padx=SP[6], pady=(SP[5], SP[1]))

        ctk.CTkLabel(self, text=f"#{i.number}  {i.title}",
                     font=ctk.CTkFont(FONT, FONT_SIZE["md"], weight="bold"),
                     text_color=COLORS["text"],
                     wraplength=490, justify="left").pack(
                         anchor="w", padx=SP[6], pady=SP[1])

        if i.labels:
            lf = ctk.CTkFrame(self, fg_color="transparent")
            lf.pack(anchor="w", padx=SP[6], pady=(0, SP[1]))
            for lb in i.labels:
                ctk.CTkLabel(lf, text=lb,
                             font=ctk.CTkFont(FONT, FONT_SIZE["xs"]),
                             text_color=label_color(lb),
                             fg_color=COLORS["tag_bg"],
                             corner_radius=4).pack(side="left", padx=(0, SP[2]))

        meta = []
        if i.assignee:   meta.append(f"assigned → {i.assignee}")
        if i.created_at: meta.append(f"opened {i.created_at}")
        if meta:
            ctk.CTkLabel(self, text="  ·  ".join(meta),
                         font=ctk.CTkFont(FONT, FONT_SIZE["xs"]),
                         text_color=COLORS["text_muted"]).pack(
                             anchor="w", padx=SP[6], pady=(0, SP[2]))

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=SP[6])

        ctk.CTkLabel(self, text=i.body or "(no description)",
                     font=ctk.CTkFont(FONT, FONT_SIZE["sm"]),
                     text_color=COLORS["text_muted"],
                     wraplength=490, justify="left").pack(
                         anchor="w", padx=SP[6], pady=SP[4])

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=SP[6], pady=(SP[1], 0))

        btn(bf, "Open on GitHub ↗",
            lambda: webbrowser.open(i.url),
            primary=True, height=38).pack(side="left", padx=(0, SP[2]))

        if i.state == "open":
            wip_lbl = "↳ Mark In Progress"
            btn(bf, wip_lbl, self._toggle_wip, height=38).pack(side="left", padx=(0, SP[2]))

        self._status_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(FONT, FONT_SIZE["xs"]),
            text_color=COLORS["text_muted"],
        )
        self._status_lbl.pack(anchor="w", padx=SP[6], pady=(SP[2], 0))

        bf2 = ctk.CTkFrame(self, fg_color="transparent")
        bf2.pack(fill="x", padx=SP[6], pady=(SP[2], SP[4]))

        if i.state == "open":
            close_lbl = "✓ Close Issue"
            close_color = COLORS.get("danger", "#c0392b")
            self._close_btn = btn(
                bf2, close_lbl, self._close_issue, height=38,
                fg_color=close_color,
                hover_color=COLORS.get("danger_hover", "#922b21"),
                text_color="#ffffff",
            )
            self._close_btn.pack(side="left", padx=(0, SP[2]))
        else:
            self._close_btn = btn(
                bf2, "↩ Reopen Issue", self._reopen_issue, height=38,
            )
            self._close_btn.pack(side="left", padx=(0, SP[2]))

        btn(bf2, "Close", self.destroy, height=38,
            fg_color="transparent",
            hover_color=COLORS["surface2"],
            text_color=COLORS["text_muted"]).pack(side="right")

    def _toggle_wip(self):
        self._on_wip_toggle(self._issue)
        self.destroy()

    def _close_issue(self):
        if self._working or not self._on_close_issue:
            return
        self._working = True
        self._close_btn.configure(state="disabled")
        self._status_lbl.configure(text="Closing issue on GitHub…")
        threading.Thread(
            target=self._on_close_issue,
            args=(self._issue, "closed", self.destroy),
            daemon=True,
        ).start()

    def _reopen_issue(self):
        if self._working or not self._on_close_issue:
            return
        self._working = True
        self._close_btn.configure(state="disabled")
        self._status_lbl.configure(text="Reopening issue on GitHub…")
        threading.Thread(
            target=self._on_close_issue,
            args=(self._issue, "open", self.destroy),
            daemon=True,
        ).start()
