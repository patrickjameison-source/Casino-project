import tkinter as tk
from tkinter import ttk
from roulette import RouletteApp
from blackjack import BlackjackApp
from poker import PokerApp
from theme import (BG_HDR, GOLD, GOLD_DIM, HDR_TEXT, CTRL, CTRL_TEXT,
                   F_TITLE, F_LABEL, F_BTN, styled_btn, _STYLE, _bind_hover)
from ai_players import AggressivePlayer, ModeratePlayer, ConservativePlayer


class Casino:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Casino Royale")
        self.root.geometry("980x560")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_HDR)

        self.bankroll = 1000
        self.starting_bankroll = 1000
        self.history = []
        # AI players live here so their bankroll persists across all games
        self.ai_players = [AggressivePlayer(), ModeratePlayer(), ConservativePlayer()]
        self._build_lobby()
        self.root.mainloop()

    def _build_lobby(self):
        # ── Title ─────────────────────────────────────────────────────────────
        title_frame = tk.Frame(self.root, bg=BG_HDR)
        title_frame.pack(fill="x", pady=(40, 0))

        tk.Label(title_frame,
                 text="♠  ♥    CASINO ROYALE    ♦  ♣",
                 font=F_TITLE, fg=HDR_TEXT, bg=BG_HDR).pack()
        tk.Label(title_frame,
                 text="♦   Your House, Your Rules   ♦",
                 font=("Georgia", 11, "italic"), fg=GOLD_DIM, bg=BG_HDR).pack(pady=(4, 0))

        tk.Frame(self.root, bg=GOLD_DIM, height=1).pack(fill="x", padx=90, pady=(12, 0))

        # ── Bankroll ──────────────────────────────────────────────────────────
        tk.Label(self.root, text="YOUR BANKROLL", font=("Arial", 9, "bold"),
                 fg=GOLD_DIM, bg=BG_HDR).pack(pady=(14, 2))
        self.bankroll_label = tk.Label(self.root,
                                       text=f"${self.bankroll:,}",
                                       font=("Georgia", 28, "bold"), fg=GOLD, bg=BG_HDR)
        self.bankroll_label.pack(pady=(0, 22))

        # ── Game buttons ──────────────────────────────────────────────────────
        btn_row = tk.Frame(self.root, bg=BG_HDR)
        btn_row.pack()

        games = [
            ("♦  ♣\nROULETTE",   "red",    self._play_roulette),
            ("♠  ♥\nBLACKJACK",  "blue",   self._play_blackjack),
            ("♥  ♦\nPOKER",       "green",  self._play_poker),
        ]
        for text, style, cmd in games:
            styled_btn(btn_row, text, cmd, style=style,
                       font=("Georgia", 15, "bold"),
                       width=16, height=5, fg="black").pack(side="left", padx=18)

        # ── Balance & History button ───────────────────────────────────────────
        tk.Frame(self.root, bg=GOLD_DIM, height=1).pack(fill="x", padx=90, pady=(24, 0))
        styled_btn(self.root, "Balance & History", self._show_history,
                   style="gold", font=F_BTN, width=22, height=2, fg="black").pack(pady=14)

    def _play_roulette(self):
        win = tk.Toplevel(self.root)
        win.grab_set()
        RouletteApp(win, bankroll=self.bankroll, on_close=self._game_closed,
                    ai_players=self.ai_players)

    def _play_blackjack(self):
        win = tk.Toplevel(self.root)
        win.grab_set()
        BlackjackApp(win, bankroll=self.bankroll, on_close=self._game_closed,
                     ai_players=self.ai_players)

    def _play_poker(self):
        win = tk.Toplevel(self.root)
        win.grab_set()
        PokerApp(win, bankroll=self.bankroll, on_close=self._game_closed,
                 ai_players=self.ai_players)

    def _game_closed(self, new_bankroll, session_log=None):
        self.bankroll = new_bankroll
        self.bankroll_label.config(text=f"${self.bankroll:,}")
        if session_log:
            nets = [e["net"] for e in session_log]
            br_before = new_bankroll - sum(nets)
            cumulative = 0
            for entry in session_log:
                cumulative += entry["net"]
                self.history.append({**entry, "bankroll": br_before + cumulative})

    def _show_history(self):
        win = tk.Toplevel(self.root)
        win.title("Balance & History")
        win.geometry("640x720")
        win.resizable(False, False)
        win.configure(bg=BG_HDR)
        win.grab_set()

        # ── Balance header ────────────────────────────────────────────────────
        tk.Label(win, text="YOUR BALANCE", font=("Arial", 11, "bold"),
                 fg=GOLD, bg=BG_HDR).pack(pady=(20, 4))
        tk.Label(win, text=f"${self.bankroll:,}",
                 font=("Georgia", 36, "bold"), fg=HDR_TEXT, bg=BG_HDR).pack()

        tk.Frame(win, bg=GOLD_DIM, height=1).pack(fill="x", padx=40, pady=(14, 0))

        # ── Player standings ──────────────────────────────────────────────────
        tk.Label(win, text="PLAYER STANDINGS", font=("Arial", 11, "bold"),
                 fg=GOLD, bg=BG_HDR).pack(pady=(10, 6))

        standings_frame = tk.Frame(win, bg=BG_HDR)
        standings_frame.pack(padx=40, fill="x")

        human_pl = self.bankroll - self.starting_bankroll
        rows = [("You", self.bankroll, human_pl)]
        for ai in self.ai_players:
            rows.append((ai.name, ai.bankroll, ai.profit_loss))
        rows.sort(key=lambda r: r[1], reverse=True)

        hdrs = ("#", "Player", "Balance", "P / L")
        widths = (3, 14, 10, 10)
        for col, (h, w) in enumerate(zip(hdrs, widths)):
            tk.Label(standings_frame, text=h, font=("Arial", 9, "bold"),
                     fg=GOLD, bg=BG_HDR, width=w, anchor="w").grid(
                         row=0, column=col, padx=(0, 4), pady=(0, 4))

        for rank, (name, bankroll, pl) in enumerate(rows, 1):
            pl_str   = f"+${pl:,}" if pl > 0 else f"-${abs(pl):,}" if pl < 0 else "$0"
            pl_color = "#4caf50" if pl > 0 else "#e74c3c" if pl < 0 else CTRL_TEXT
            is_you   = (name == "You")
            bg_row   = CTRL

            row_bg = tk.Frame(standings_frame, bg=bg_row)
            row_bg.grid(row=rank, column=0, columnspan=4, sticky="ew", pady=2)
            standings_frame.columnconfigure(0, weight=0)

            cells = [
                (str(rank),        widths[0], HDR_TEXT if is_you else CTRL_TEXT),
                (name,             widths[1], GOLD if is_you else HDR_TEXT),
                (f"${bankroll:,}", widths[2], HDR_TEXT if is_you else CTRL_TEXT),
                (pl_str,           widths[3], pl_color),
            ]
            for col, (text, w, color) in enumerate(cells):
                tk.Label(row_bg, text=text, font=("Arial", 10, "bold" if is_you else "normal"),
                         fg=color, bg=bg_row, width=w, anchor="w",
                         padx=6, pady=4).pack(side="left")

        tk.Frame(win, bg=GOLD_DIM, height=1).pack(fill="x", padx=40, pady=(12, 0))

        # ── Tabs: History / Analytics ─────────────────────────────────────────
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Casino.TNotebook",        background=BG_HDR, borderwidth=0, tabmargins=0)
        s.configure("Casino.TNotebook.Tab",    background=CTRL,   foreground=CTRL_TEXT,
                    font=("Arial", 10, "bold"), padding=(14, 6))
        s.map("Casino.TNotebook.Tab",
              background=[("selected", "#1c1c1c")],
              foreground=[("selected", GOLD)])
        s.configure("History.Treeview",
                    background=CTRL, foreground="white",
                    fieldbackground=CTRL, rowheight=26, font=("Arial", 10))
        s.configure("History.Treeview.Heading",
                    background="#1c1c1c", foreground=GOLD,
                    font=("Arial", 10, "bold"), relief="flat")
        s.map("History.Treeview", background=[("selected", "#2a2a2a")])

        nb = ttk.Notebook(win, style="Casino.TNotebook")
        nb.pack(fill="both", expand=True, padx=20, pady=(8, 0))

        hist_frame = tk.Frame(nb, bg=BG_HDR)
        nb.add(hist_frame, text="  History  ")
        self._build_history_tab(hist_frame)

        ana_frame = tk.Frame(nb, bg=BG_HDR)
        nb.add(ana_frame, text="  Analytics  ")
        self._build_analytics_tab(ana_frame)

        styled_btn(win, "Close", win.destroy,
                   style="dark", font=F_BTN, width=12, fg="black").pack(pady=(6, 14))

    def _build_history_tab(self, parent):
        if not self.history:
            tk.Label(parent, text="No bets placed yet this session.",
                     font=("Arial", 11), fg=CTRL_TEXT, bg=BG_HDR).pack(pady=30)
            return

        frame = tk.Frame(parent, bg=BG_HDR)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("#", "Game", "Bet", "Result", "Net")
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="History.Treeview")
        tree.heading("#",      text="#")
        tree.heading("Game",   text="Game")
        tree.heading("Bet",    text="Bet")
        tree.heading("Result", text="Result")
        tree.heading("Net",    text="Net")
        tree.column("#",      width=36,  anchor="center")
        tree.column("Game",   width=100, anchor="center")
        tree.column("Bet",    width=80,  anchor="center")
        tree.column("Result", width=220, anchor="center")
        tree.column("Net",    width=90,  anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for i, entry in enumerate(reversed(self.history), 1):
            net = entry["net"]
            net_str = f"+${net:,}" if net > 0 else f"-${abs(net):,}" if net < 0 else "$0"
            tree.insert("", "end", values=(
                len(self.history) - i + 1,
                entry["game"],
                f"${entry['bet']:,}",
                entry["result"],
                net_str,
            ))

    def _build_analytics_tab(self, parent):
        if not self.history:
            tk.Label(parent, text="Play some rounds to see analytics.",
                     font=("Arial", 11), fg=CTRL_TEXT, bg=BG_HDR).pack(pady=30)
            return

        # ── Compute stats ─────────────────────────────────────────────────────
        all_nets = [e["net"] for e in self.history]
        total    = len(self.history)
        biggest_win  = max(all_nets)
        biggest_loss = min(all_nets)

        games = ["Roulette", "Blackjack", "Poker"]
        by_game = {}
        for g in games:
            entries = [e for e in self.history if e["game"] == g]
            wins = sum(1 for e in entries if e["net"] > 0)
            by_game[g] = {
                "rounds":   len(entries),
                "win_rate": (wins / len(entries)) if entries else 0.0,
                "net":      sum(e["net"] for e in entries),
            }

        # Bankroll series: reconstruct if "bankroll" key missing (old entries)
        br_series = [self.starting_bankroll]
        for e in self.history:
            br_series.append(e.get("bankroll", br_series[-1] + e["net"]))

        # ── Layout ────────────────────────────────────────────────────────────
        scroll_canvas = tk.Canvas(parent, bg=BG_HDR, highlightthickness=0)
        scroll_canvas.pack(fill="both", expand=True)

        inner = tk.Frame(scroll_canvas, bg=BG_HDR)
        scroll_canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(e):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        inner.bind("<Configure>", _on_configure)

        pad = dict(padx=24, pady=3)

        # ── Overview row ──────────────────────────────────────────────────────
        tk.Frame(inner, bg=GOLD_DIM, height=1).pack(fill="x", padx=20, pady=(10, 6))
        tk.Label(inner, text="OVERVIEW", font=("Arial", 9, "bold"),
                 fg=GOLD_DIM, bg=BG_HDR).pack(anchor="w", padx=24, pady=(0, 4))

        ov = tk.Frame(inner, bg=BG_HDR)
        ov.pack(fill="x", **pad)

        def _stat(parent, label, value, value_color=HDR_TEXT):
            f = tk.Frame(parent, bg=CTRL, padx=10, pady=8)
            f.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(f, text=label, font=("Arial", 8, "bold"),
                     fg=GOLD_DIM, bg=CTRL).pack(anchor="w")
            tk.Label(f, text=value, font=("Arial", 14, "bold"),
                     fg=value_color, bg=CTRL).pack(anchor="w")

        _stat(ov, "TOTAL ROUNDS", str(total))
        bw_color = "#4caf50" if biggest_win > 0 else HDR_TEXT
        bl_color = "#e74c3c" if biggest_loss < 0 else HDR_TEXT
        _stat(ov, "BIGGEST WIN",
              f"+${biggest_win:,}" if biggest_win > 0 else f"${biggest_win:,}", bw_color)
        _stat(ov, "BIGGEST LOSS",
              f"-${abs(biggest_loss):,}" if biggest_loss < 0 else f"${biggest_loss:,}", bl_color)

        # ── Per-game stats ────────────────────────────────────────────────────
        tk.Frame(inner, bg=GOLD_DIM, height=1).pack(fill="x", padx=20, pady=(10, 6))
        tk.Label(inner, text="BY GAME", font=("Arial", 9, "bold"),
                 fg=GOLD_DIM, bg=BG_HDR).pack(anchor="w", padx=24, pady=(0, 4))

        tbl = tk.Frame(inner, bg=BG_HDR)
        tbl.pack(fill="x", padx=24, pady=(0, 4))

        hdrs = ("Game", "Rounds", "Win Rate", "Net P/L")
        col_w = (10, 8, 10, 10)
        for col, (h, w) in enumerate(zip(hdrs, col_w)):
            tk.Label(tbl, text=h, font=("Arial", 9, "bold"),
                     fg=GOLD, bg=BG_HDR, width=w, anchor="w").grid(
                     row=0, column=col, padx=(0, 8), pady=(0, 4))

        for row_i, g in enumerate(games, 1):
            d = by_game[g]
            net = d["net"]
            net_str   = f"+${net:,}" if net > 0 else f"-${abs(net):,}" if net < 0 else "$0"
            net_color = "#4caf50" if net > 0 else "#e74c3c" if net < 0 else CTRL_TEXT
            wr_str    = f"{d['win_rate']*100:.0f}%" if d["rounds"] else "—"
            rounds_str = str(d["rounds"]) if d["rounds"] else "—"

            row_bg = tk.Frame(tbl, bg=CTRL)
            row_bg.grid(row=row_i, column=0, columnspan=4, sticky="ew", pady=2)

            cells = [
                (g,          col_w[0], HDR_TEXT),
                (rounds_str, col_w[1], CTRL_TEXT),
                (wr_str,     col_w[2], CTRL_TEXT),
                (net_str,    col_w[3], net_color),
            ]
            for col, (text, w, color) in enumerate(cells):
                tk.Label(row_bg, text=text, font=("Arial", 10),
                         fg=color, bg=CTRL, width=w, anchor="w",
                         padx=6, pady=4).pack(side="left")

        # ── Bankroll chart ────────────────────────────────────────────────────
        tk.Frame(inner, bg=GOLD_DIM, height=1).pack(fill="x", padx=20, pady=(10, 6))
        tk.Label(inner, text="BANKROLL OVER TIME", font=("Arial", 9, "bold"),
                 fg=GOLD_DIM, bg=BG_HDR).pack(anchor="w", padx=24, pady=(0, 4))

        cw, ch = 576, 160
        chart = tk.Canvas(inner, width=cw, height=ch, bg=CTRL,
                          highlightthickness=0)
        chart.pack(padx=24, pady=(0, 16))

        margin = dict(l=52, r=12, t=10, b=28)
        pw = cw - margin["l"] - margin["r"]
        ph = ch - margin["t"] - margin["b"]

        lo, hi = min(br_series), max(br_series)
        if lo == hi:
            lo, hi = lo - 100, hi + 100
        y_pad = (hi - lo) * 0.08
        lo -= y_pad; hi += y_pad

        def _px(i, br):
            x = margin["l"] + i / (len(br_series) - 1) * pw if len(br_series) > 1 else margin["l"] + pw / 2
            y = margin["t"] + ph - (br - lo) / (hi - lo) * ph
            return x, y

        # Gridlines + y-labels
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            br_val = lo + frac * (hi - lo)
            _, y = _px(0, br_val)
            chart.create_line(margin["l"], y, margin["l"] + pw, y,
                              fill="#2a2a2a", dash=(3, 4))
            chart.create_text(margin["l"] - 4, y,
                              text=f"${int(br_val):,}", anchor="e",
                              font=("Arial", 7), fill=CTRL_TEXT)

        # Break-even line
        if lo < self.starting_bankroll < hi:
            _, y_be = _px(0, self.starting_bankroll)
            chart.create_line(margin["l"], y_be, margin["l"] + pw, y_be,
                              fill=GOLD_DIM, dash=(4, 3))

        # Bankroll line
        pts = [_px(i, br) for i, br in enumerate(br_series)]
        if len(pts) > 1:
            flat = [coord for p in pts for coord in p]
            chart.create_line(*flat, fill=GOLD, width=2, smooth=True)

        # End point dot
        ex, ey = pts[-1]
        dot_color = "#4caf50" if br_series[-1] >= self.starting_bankroll else "#e74c3c"
        chart.create_oval(ex - 4, ey - 4, ex + 4, ey + 4,
                          fill=dot_color, outline="")

        # X-axis labels
        chart.create_text(margin["l"], ch - margin["b"] + 10,
                          text="Start", anchor="w",
                          font=("Arial", 7), fill=CTRL_TEXT)
        chart.create_text(margin["l"] + pw, ch - margin["b"] + 10,
                          text=f"Round {total}", anchor="e",
                          font=("Arial", 7), fill=CTRL_TEXT)


if __name__ == "__main__":
    Casino()
