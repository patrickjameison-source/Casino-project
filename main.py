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
            self.history.extend(session_log)

    def _show_history(self):
        win = tk.Toplevel(self.root)
        win.title("Balance & History")
        win.geometry("640x600")
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

        # Build rows: (label, bankroll, profit_loss)
        human_pl = self.bankroll - self.starting_bankroll
        rows = [("You", self.bankroll, human_pl)]
        for ai in self.ai_players:
            rows.append((ai.name, ai.bankroll, ai.profit_loss))
        rows.sort(key=lambda r: r[1], reverse=True)

        # Header row
        hdrs = ("#", "Player", "Balance", "P / L")
        widths = (3, 14, 10, 10)
        for col, (h, w) in enumerate(zip(hdrs, widths)):
            tk.Label(standings_frame, text=h, font=("Arial", 9, "bold"),
                     fg=GOLD, bg=BG_HDR, width=w, anchor="w").grid(
                         row=0, column=col, padx=(0, 4), pady=(0, 4))

        for rank, (name, bankroll, pl) in enumerate(rows, 1):
            pl_str  = f"+${pl:,}" if pl > 0 else f"-${abs(pl):,}" if pl < 0 else "$0"
            pl_color = "#4caf50" if pl > 0 else "#e74c3c" if pl < 0 else CTRL_TEXT
            is_you  = (name == "You")
            fg      = HDR_TEXT if is_you else CTRL_TEXT
            bg_row  = CTRL

            row_bg = tk.Frame(standings_frame, bg=bg_row)
            row_bg.grid(row=rank, column=0, columnspan=4, sticky="ew",
                        pady=2, padx=0)
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

        tk.Label(win, text="YOUR BET HISTORY", font=("Arial", 11, "bold"),
                 fg=GOLD, bg=BG_HDR).pack(pady=(10, 6))

        if not self.history:
            tk.Label(win, text="No bets placed yet this session.",
                     font=("Arial", 11), fg=CTRL_TEXT, bg=BG_HDR).pack(pady=20)
        else:
            # Scrollable table
            frame = tk.Frame(win, bg=BG_HDR)
            frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

            style = ttk.Style()
            style.theme_use("default")
            style.configure("History.Treeview",
                            background=CTRL, foreground="white",
                            fieldbackground=CTRL, rowheight=26,
                            font=("Arial", 10))
            style.configure("History.Treeview.Heading",
                            background="#1c1c1c", foreground=GOLD,
                            font=("Arial", 10, "bold"), relief="flat")
            style.map("History.Treeview", background=[("selected", "#2a2a2a")])

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

        styled_btn(win, "Close", win.destroy,
                   style="dark", font=F_BTN, width=12, fg="black").pack(pady=(0, 16))


if __name__ == "__main__":
    Casino()
