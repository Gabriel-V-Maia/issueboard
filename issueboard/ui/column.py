import customtkinter as ctk
from issueboard.models import Issue
from issueboard.ui.colors import COLORS, FONT, FONT_SIZE, SP
from issueboard.ui.card import IssueCard

COLUMNS = ["Open", "In Progress", "Done"]

_DOT_COLOR = {
    "Open":        COLORS["accent"],
    "In Progress": COLORS["warn"],
    "Done":        COLORS["accent2"],
}
_BG_COLOR = {
    "Open":        COLORS["col_open"],
    "In Progress": COLORS["col_wip"],
    "Done":        COLORS["col_done"],
}


class KanbanColumn(ctk.CTkFrame):
    def __init__(self, parent, title: str, on_open, on_drop=None, on_drag_start=None, **kw):
        super().__init__(parent, fg_color=_BG_COLOR[title], corner_radius=10, **kw)
        self._title    = title
        self._cards    = []
        self._on_drop  = on_drop
        self._on_drag_start = on_drag_start
        self._highlighted = False

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=SP[3], pady=(SP[3], SP[2]))

        ctk.CTkLabel(hdr, text="●",
                     font=ctk.CTkFont(FONT, FONT_SIZE["xs"]),
                     text_color=_DOT_COLOR[title]).pack(side="left")

        ctk.CTkLabel(hdr, text=title.upper(),
                     font=ctk.CTkFont(FONT, FONT_SIZE["xs"], weight="bold"),
                     text_color=COLORS["text"]).pack(side="left", padx=SP[2])

        self._count = ctk.CTkLabel(hdr, text="0",
                                   font=ctk.CTkFont(FONT, FONT_SIZE["xs"]),
                                   text_color=COLORS["text_muted"])
        self._count.pack(side="right")

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self._scroll.pack(fill="both", expand=True, padx=SP[2], pady=(0, SP[2]))
        self._on_open = on_open

    def clear(self):
        for c in self._cards:
            c.destroy()
        self._cards.clear()
        self._count.configure(text="0")

    def add(self, issue: Issue):
        card = IssueCard(
            self._scroll, issue, self._on_open,
            on_drag_start=self._on_drag_start,
        )
        card.pack(fill="x", pady=(0, SP[2]))
        self._cards.append(card)
        self._count.configure(text=str(len(self._cards)))

    def set_drop_highlight(self, active: bool):
        if active == self._highlighted:
            return
        self._highlighted = active
        color = COLORS.get("col_drop_highlight", COLORS["border"]) if active else _BG_COLOR[self._title]
        self.configure(fg_color=color)

    def contains_point(self, x_root: int, y_root: int) -> bool:
        try:
            wx = self.winfo_rootx()
            wy = self.winfo_rooty()
            ww = self.winfo_width()
            wh = self.winfo_height()
            return wx <= x_root <= wx + ww and wy <= y_root <= wy + wh
        except Exception:
            return False
