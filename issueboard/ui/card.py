import customtkinter as ctk
from issueboard.models import Issue
from issueboard.ui.colors import COLORS, FONT, FONT_SIZE, SP, label_color


class IssueCard(ctk.CTkFrame):
    def __init__(self, parent, issue: Issue, on_open, on_drag_start=None, **kw):
        super().__init__(
            parent,
            fg_color=COLORS["surface2"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            **kw,
        )
        self._issue        = issue
        self._on_open      = on_open
        self._on_drag_start = on_drag_start
        self._drag_threshold = 6
        self._press_x = 0
        self._press_y = 0
        self._dragging = False

        self.configure(cursor="hand2")
        self.bind("<Button-1>",         self._press)
        self.bind("<B1-Motion>",        self._motion)
        self.bind("<ButtonRelease-1>",  self._release)

        def lbl(text, size_key, color, row, pady, bold=False, **extra):
            fg = extra.pop("fg_color", "transparent")
            w = ctk.CTkLabel(
                self, text=text,
                font=ctk.CTkFont(FONT, FONT_SIZE[size_key],
                                 weight="bold" if bold else "normal"),
                text_color=color, fg_color=fg, **extra,
            )
            w.grid(row=row, column=0, sticky="w", padx=SP[2], pady=pady)
            w.bind("<Button-1>",        self._press)
            w.bind("<B1-Motion>",       self._motion)
            w.bind("<ButtonRelease-1>", self._release)
            return w

        lbl(issue.repo, "xs", COLORS["accent"], 0, (SP[2], SP[1]),
            fg_color=COLORS["tag_bg"], corner_radius=4)

        lbl(issue.title, "sm", COLORS["text"], 1, SP[1],
            bold=True, wraplength=220, justify="left", anchor="w")

        if issue.labels:
            lf = ctk.CTkFrame(self, fg_color="transparent")
            lf.grid(row=2, column=0, sticky="w", padx=SP[2], pady=SP[1])
            lf.bind("<Button-1>",        self._press)
            lf.bind("<B1-Motion>",       self._motion)
            lf.bind("<ButtonRelease-1>", self._release)
            for lb in issue.labels[:3]:
                tag = ctk.CTkLabel(
                    lf, text=lb,
                    font=ctk.CTkFont(FONT, FONT_SIZE["xs"]),
                    text_color=label_color(lb),
                    fg_color=COLORS["tag_bg"],
                    corner_radius=4,
                )
                tag.pack(side="left", padx=(0, SP[1]))
                tag.bind("<Button-1>",        self._press)
                tag.bind("<B1-Motion>",       self._motion)
                tag.bind("<ButtonRelease-1>", self._release)

        lbl(f"#{issue.number}  ·  {issue.created_at}", "xs",
            COLORS["text_muted"], 3, (SP[1], SP[2]))

        self.grid_columnconfigure(0, weight=1)

    def _press(self, e):
        self._press_x = e.x_root
        self._press_y = e.y_root
        self._dragging = False

    def _motion(self, e):
        if not self._dragging:
            dx = abs(e.x_root - self._press_x)
            dy = abs(e.y_root - self._press_y)
            if dx > self._drag_threshold or dy > self._drag_threshold:
                self._dragging = True
                if self._on_drag_start:
                    self._on_drag_start(self._issue, e)

    def _release(self, e):
        if not self._dragging:
            self._on_open(self._issue)
        self._dragging = False
