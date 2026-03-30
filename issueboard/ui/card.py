import customtkinter as ctk
from issueboard.models import Issue
from issueboard.ui.colors import COLORS, label_color


class IssueCard(ctk.CTkFrame):
    def __init__(self, parent, issue: Issue, on_open, **kw):
        super().__init__(
            parent,
            fg_color=COLORS["surface2"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            **kw,
        )
        self._issue   = issue
        self._on_open = on_open
        self.configure(cursor="hand2")
        self.bind("<Button-1>", self._click)

        def lbl(text, size, color, row, pady, bold=False, **extra):
            fg = extra.pop("fg_color", "transparent")
            w = ctk.CTkLabel(
                self, text=text,
                font=ctk.CTkFont("Courier New", size, weight="bold" if bold else "normal"),
                text_color=color, fg_color=fg, **extra,
            )
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
                tag = ctk.CTkLabel(
                    lf, text=lb,
                    font=ctk.CTkFont("Courier New", 9),
                    text_color=label_color(lb),
                    fg_color=COLORS["tag_bg"],
                    corner_radius=4,
                )
                tag.pack(side="left", padx=(0, 4))
                tag.bind("<Button-1>", self._click)

        lbl(f"#{issue.number}  ·  {issue.created_at}", 9,
            COLORS["text_muted"], 3, (2, 8))

        self.grid_columnconfigure(0, weight=1)

    def _click(self, _=None):
        self._on_open(self._issue)