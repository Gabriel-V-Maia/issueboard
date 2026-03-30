import customtkinter as ctk
from issueboard.config import load_config
from issueboard.ui.colors import COLORS
from issueboard.ui.login import LoginScreen
from issueboard.ui.board import BoardScreen

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


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