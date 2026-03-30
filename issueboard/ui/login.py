import threading
import webbrowser
import customtkinter as ctk
from issueboard.config import load_config, save_config
from issueboard.ui.colors import COLORS, btn
from issueboard.github.auth import (
    device_flow_start, device_flow_poll,
    SCOPES_PUBLIC, SCOPES_PRIVATE,
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

        btn(box, "Login with GitHub →", self._start,
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

        btn(box, "Open GitHub →",
            lambda: webbrowser.open(verification_uri),
            primary=True, height=38).pack(fill="x", padx=40, pady=(0, 6))

        btn(box, "Cancel", self._build_idle,
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