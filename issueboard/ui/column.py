import customtkinter as ctk
from issueboard.models import Issue
from issueboard.ui.colors import COLORS
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
    def __init__(self, parent, title: str, on_open, **kw):
        super().__init__(parent, fg_color=_BG_COLOR[title], corner_radius=10, **kw)
        self._cards = []

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(hdr, text="●", font=ctk.CTkFont(size=10),
                     text_color=_DOT_COLOR[title]).pack(side="left")
        ctk.CTkLabel(hdr, text=title.upper(),
                     font=ctk.CTkFont("Courier New", 11, weight="bold"),
                     text_color=COLORS["text"]).pack(side="left", padx=6)

        self._count = ctk.CTkLabel(hdr, text="0",
                                   font=ctk.CTkFont("Courier New", 10),
                                   text_color=COLORS["text_muted"])
        self._count.pack(side="right")

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
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