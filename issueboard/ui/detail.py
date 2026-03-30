import webbrowser
import customtkinter as ctk
from issueboard.models import Issue
from issueboard.ui.colors import COLORS, label_color, btn


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
                             text_color=label_color(lb),
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

        btn(bf, "Open on GitHub ↗",
            lambda: webbrowser.open(i.url),
            primary=True, height=38).pack(side="left", padx=(0, 8))

        wip_lbl = "↳ Mark In Progress" if i.state == "open" else "↩ Move to Open"
        btn(bf, wip_lbl, self._toggle, height=38).pack(side="left")

        btn(bf, "Close", self.destroy, height=38,
            fg_color="transparent",
            hover_color=COLORS["surface2"],
            text_color=COLORS["text_muted"]).pack(side="right")

    def _toggle(self):
        self._on_wip_toggle(self._issue)
        self.destroy()