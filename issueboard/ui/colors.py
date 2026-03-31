import customtkinter as ctk

COLORS = {
    "bg":         "#0d1117",
    "surface":    "#161b22",
    "surface2":   "#21262d",  
    "border":     "#30363d",
    "accent":     "#4d9eff",   
    "accent2":    "#3fb950",
    "accent3":    "#f78166",
    "warn":       "#d29922",
    "text":       "#e6edf3",
    "text_muted": "#a0aab4",   
    "col_open":   "#1f2d3d",
    "col_wip":    "#1f2b1f",
    "col_done":   "#2d1f2b",
    "tag_bg":     "#21262d",
}

# ---------------------------------------------------------------------------
# Sistema tipográfico 
# Escala modular baseada em razão 1.25 (Major Third) a partir de 11px base:
#   xs   = 10   (labels secundários, scopes)
#   sm   = 11   (body, labels, status)
#   md   = 13   (body emphasis, botões)
#   lg   = 16   (subtítulos, section headers)
#   xl   = 20   (títulos de tela)
#   2xl  = 28   (display — usado com moderação)
#   icon = 42   (ícone hero — reduzido de 48 pra equilibrar com xl)
# ---------------------------------------------------------------------------
FONT = "JetBrains Mono"

FONT_SIZE = {
    "xs":   10,
    "sm":   11,
    "md":   13,
    "lg":   16,
    "xl":   20,
    "2xl":  28,
    "icon": 42,
}

# ---------------------------------------------------------------------------
# Sistema de espaçamento com **BASE 4 GRID** <--- LEIA
# Usar sempre estes valores em pady/padx para criar ritmo visual consistente
#   SP1 =  4
#   SP2 =  8
#   SP3 = 12
#   SP4 = 16
#   SP5 = 20
#   SP6 = 24
#   SP7 = 28
#   SP8 = 32
# ---------------------------------------------------------------------------
SP = {1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 7: 28, 8: 32}


def label_color(name: str) -> str:
    n = name.lower()
    if "bug"  in n or "fix" in n:     return COLORS["accent3"]
    if "wip"  in n:                   return COLORS["warn"]
    if "todo" in n:                   return COLORS["accent"]
    if "enhance" in n or "feat" in n: return COLORS["accent2"]
    return COLORS["text_muted"]


def btn(parent, text, command, primary=False, **kw):
    height        = kw.pop("height",       42)
    font_size     = kw.pop("font_size",    FONT_SIZE["md"])
    fg_color      = kw.pop("fg_color",     COLORS["accent"]   if primary else COLORS["surface2"])
    hover_color   = kw.pop("hover_color",  "#1f6feb"          if primary else COLORS["border"])
    text_color    = kw.pop("text_color",   COLORS["bg"]       if primary else COLORS["text"])
    border_width  = kw.pop("border_width", 0                  if primary else 1)
    border_color  = kw.pop("border_color", COLORS["border"])
    corner_radius = kw.pop("corner_radius", 8)

    return ctk.CTkButton(
        parent, text=text, command=command,
        height=height,
        font=ctk.CTkFont(FONT, font_size, weight="bold" if primary else "normal"),
        fg_color=fg_color,
        hover_color=hover_color,
        text_color=text_color,
        border_width=border_width,
        border_color=border_color,
        corner_radius=corner_radius,
        **kw,
    )