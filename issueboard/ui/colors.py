import customtkinter as ctk

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


def label_color(name: str) -> str:
    n = name.lower()
    if "bug"  in n or "fix" in n:      return COLORS["accent3"]
    if "wip"  in n:                    return COLORS["warn"]
    if "todo" in n:                    return COLORS["accent"]
    if "enhance" in n or "feat" in n:  return COLORS["accent2"]
    return COLORS["text_muted"]


def btn(parent, text, command, primary=False, **kw):
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