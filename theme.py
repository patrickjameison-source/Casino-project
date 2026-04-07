import tkinter as tk

# ── Color Palette ─────────────────────────────────────────────────────────────
BG       = "#0d0d0d"
BG_HDR   = "#0f0f0f"
TABLE    = "#0b3d2e"
TABLE_LT = "#0f4f3a"
CTRL     = "#141414"

GOLD     = "#c8a84b"
GOLD_HVR = "#dfc468"
GOLD_DIM = "#7a6420"
CARD_BG  = "#f5f0e8"

SUIT_RED = "#c0392b"
SUIT_BLK = "#1a1a1a"

# ── Outcome colors ────────────────────────────────────────────────────────────
WIN_COLOR  = "#4caf50"
LOSS_COLOR = "#e74c3c"
PUSH_COLOR = "#c8a84b"   # same as GOLD

# ── Personality accent colors (for AI player cards) ───────────────────────────
PERSONALITY_COLORS = {
    "aggressive":   "#c0392b",
    "moderate":     "#2471a3",
    "conservative": "#1a7a40",
}

# ── Typography ────────────────────────────────────────────────────────────────
F_TITLE  = ("Georgia", 32, "bold")
F_H2     = ("Georgia", 18, "bold")
F_LABEL  = ("Arial",   10, "bold")
F_VALUE  = ("Arial",   20, "bold")
F_RESULT = ("Georgia", 19, "bold")
F_BTN_LG = ("Arial",   13, "bold")
F_BTN    = ("Arial",   11, "bold")
F_BTN_SM = ("Arial",    9, "bold")
F_CHIP   = ("Arial",    9, "bold")

# ── Contrast function (WCAG relative luminance) ───────────────────────────────
def contrast_text(bg):
    """
    Return 'black' or 'white' — whichever has higher contrast against bg.
    Uses WCAG 2.1 relative luminance: L = 0.2126R + 0.7152G + 0.0722B
    (after gamma linearisation). Threshold 0.179 ≈ optimal contrast crossover.
    """
    _named = {"black": (0, 0, 0), "white": (255, 255, 255),
              "gold": (255, 215, 0), "red": (255, 0, 0)}
    lc = bg.lower().strip()

    if lc in _named:
        r, g, b = _named[lc]
    elif lc.startswith("#"):
        h = lc.lstrip("#")
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    else:
        return "white"   # safe fallback: assume unknown named color is dark

    def _lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    L = 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)
    return "black" if L > 0.179 else "white"

# ── Pre-computed text colors for common backgrounds ───────────────────────────
# Call contrast_text() once at startup; reuse the result everywhere.
HDR_TEXT      = contrast_text(BG_HDR)     # → "white"
TABLE_TEXT    = contrast_text(TABLE)      # → "white"
TABLE_LT_TEXT = contrast_text(TABLE_LT)  # → "white"
CTRL_TEXT     = contrast_text(CTRL)       # → "white"
CARD_TEXT     = contrast_text(CARD_BG)    # → "black"

# ── Button style map (fg auto-computed) ───────────────────────────────────────
_STYLE = {
    "gold":   (GOLD,      contrast_text(GOLD),      GOLD_HVR,   contrast_text(GOLD_HVR)),
    "red":    ("#a93226", contrast_text("#a93226"), "#c0392b",   contrast_text("#c0392b")),
    "green":  ("#1a7a40", contrast_text("#1a7a40"), "#229954",   contrast_text("#229954")),
    "blue":   ("#1a4f7a", contrast_text("#1a4f7a"), "#2471a3",   contrast_text("#2471a3")),
    "purple": ("#6c3483", contrast_text("#6c3483"), "#8e44ad",   contrast_text("#8e44ad")),
    "orange": ("#a86000", contrast_text("#a86000"), "#ca7d0a",   contrast_text("#ca7d0a")),
    "dark":   ("#1c1c1c", contrast_text("#1c1c1c"), "#2e2e2e",   contrast_text("#2e2e2e")),
    "muted":  ("#222222", contrast_text("#222222"), "#333333",   contrast_text("#333333")),
    "cancel": ("#7b241c", contrast_text("#7b241c"), "#a93226",   contrast_text("#a93226")),
}

# ── Hover binding ─────────────────────────────────────────────────────────────
def _bind_hover(btn, n_bg, n_fg, h_bg, h_fg):
    def on_enter(e):
        if str(btn["state"]) != "disabled":
            btn.config(bg=h_bg, fg=h_fg)
    def on_leave(e):
        btn.config(bg=n_bg, fg=n_fg)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

# ── Button factory ────────────────────────────────────────────────────────────
def styled_btn(parent, text, command=None, style="dark",
               width=None, height=None, font=None, state="normal", **kw):
    bg, fg, hbg, hfg = _STYLE.get(style, _STYLE["dark"])
    cfg = dict(text=text, bg=bg, fg=fg, font=font or F_BTN,
               relief="flat", bd=0, cursor="hand2", state=state,
               activebackground=hbg, activeforeground=hfg)
    if command is not None: cfg["command"] = command
    if width is not None:   cfg["width"]   = width
    if height is not None:  cfg["height"]  = height
    cfg.update(kw)
    btn = tk.Button(parent, **cfg)
    _bind_hover(btn, bg, cfg["fg"], hbg, hfg)
    return btn

# ── Gold divider ──────────────────────────────────────────────────────────────
def gold_divider(parent, padx=0, pady=0):
    f = tk.Frame(parent, bg=GOLD_DIM, height=1)
    f.pack(fill="x", padx=padx, pady=pady)
    return f
