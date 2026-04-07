import tkinter as tk
from tkinter import messagebox
import random
import math
from ai_players import AggressivePlayer, ModeratePlayer, ConservativePlayer
from theme import (BG_HDR, TABLE, TABLE_LT, CTRL, GOLD, GOLD_DIM,
                   HDR_TEXT, TABLE_TEXT, TABLE_LT_TEXT, CTRL_TEXT,
                   CARD_BG, SUIT_RED, SUIT_BLK,
                   F_H2, F_LABEL, F_VALUE, F_BTN_LG, F_BTN_SM, F_CHIP,
                   contrast_text, styled_btn, _bind_hover, gold_divider)

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27,
    13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1,
    20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
]

PAYOUTS = {
    "red": 1, "black": 1,
    "even": 1, "odd": 1,
    "low": 1, "high": 1,
    "dozen1": 2, "dozen2": 2, "dozen3": 2,
    "col1": 2, "col2": 2, "col3": 2,
}


def get_payout(bet_key):
    if bet_key.startswith("n_"):
        return 35
    return PAYOUTS.get(bet_key, 1)


def check_win(bet_key, result):
    if bet_key.startswith("n_"):
        return result == int(bet_key[2:])
    if bet_key == "red":     return result in RED_NUMBERS
    if bet_key == "black":   return result in BLACK_NUMBERS
    if bet_key == "even":    return result != 0 and result % 2 == 0
    if bet_key == "odd":     return result % 2 == 1
    if bet_key == "low":     return 1 <= result <= 18
    if bet_key == "high":    return 19 <= result <= 36
    if bet_key == "dozen1":  return 1 <= result <= 12
    if bet_key == "dozen2":  return 13 <= result <= 24
    if bet_key == "dozen3":  return 25 <= result <= 36
    if bet_key == "col1":    return result != 0 and result % 3 == 1
    if bet_key == "col2":    return result != 0 and result % 3 == 2
    if bet_key == "col3":    return result != 0 and result % 3 == 0
    return False


class RouletteApp:
    def __init__(self, root, bankroll=1000, on_close=None, ai_players=None):
        self.root = root
        self.root.title("Casino Roulette")
        self.root.geometry("1400x860")
        self.root.minsize(1300, 760)
        self.root.configure(bg="#0b3d2e")

        self.bankroll = bankroll
        self.on_close = on_close
        self.chip_amount = 25
        self.active_bets = {}      # bet_key → total amount placed
        self.last_result = None
        self.session_log = []
        self.history = []
        # Accept shared AI players from Casino, or create local ones as fallback
        self.ai_players = ai_players if ai_players is not None \
            else [AggressivePlayer(), ModeratePlayer(), ConservativePlayer()]
        self.last_human_net      = None   # net result of last round for human
        self.last_human_bet      = 0
        self.last_human_bet_keys = []
        self.spinning = False
        self.ball_angle = 0
        self._cancel_id = None
        self.board_buttons = {}    # bet_key → (widget, base_label, base_bg)

        self.root.protocol("WM_DELETE_WINDOW", self.back_to_lobby)
        self.build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def build_ui(self):
        self.root.configure(bg=TABLE)

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG_HDR, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        inner = tk.Frame(hdr, bg=BG_HDR)
        inner.pack(fill="both", expand=True, padx=18)

        if self.on_close:
            styled_btn(inner, "← Lobby", self.back_to_lobby,
                       style="muted", font=F_BTN_SM, fg="black").pack(side="left", pady=12)

        tk.Label(inner, text="♦  ROULETTE  ♦", font=F_H2,
                 fg=HDR_TEXT, bg=BG_HDR).pack(side="left", padx=16, pady=12)

        self.bankroll_label = tk.Label(inner, text=f"Bankroll:  ${self.bankroll:,}",
                                       font=("Arial", 15, "bold"), fg=HDR_TEXT, bg=BG_HDR)
        self.bankroll_label.pack(side="right", pady=12)

        self.total_bet_label = tk.Label(inner, text="Total Bet: $0",
                                        font=F_LABEL, fg=HDR_TEXT, bg=BG_HDR)
        self.total_bet_label.pack(side="right", padx=20, pady=12)

        gold_divider(self.root)

        # ── Main area ──────────────────────────────────────────────────────────
        main = tk.Frame(self.root, bg=TABLE)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        self._build_left_panel(main)
        self._build_ai_panel(main)
        self._build_board(main)

    def _build_left_panel(self, parent):
        left = tk.Frame(parent, bg=CTRL, bd=0, width=295)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        tk.Label(left, text="ROULETTE WHEEL", font=F_LABEL,
                 fg=CTRL_TEXT, bg=CTRL).pack(pady=(14, 2))

        self.result_label = tk.Label(left, text="Place bets and SPIN!",
                                     font=("Arial", 12, "bold"), fg=CTRL_TEXT, bg=CTRL)
        self.result_label.pack()

        self.result_detail = tk.Label(left, text="", font=("Arial", 11),
                                      fg=CTRL_TEXT, bg=CTRL)
        self.result_detail.pack(pady=2)

        self.canvas = tk.Canvas(left, width=270, height=270, bg=CTRL,
                                highlightthickness=0)
        self.canvas.pack(pady=5, padx=10)
        self.draw_wheel()

        # History
        gold_divider(left, padx=10)
        tk.Label(left, text="RECENT RESULTS", font=F_LABEL,
                 fg=CTRL_TEXT, bg=CTRL).pack(pady=(6, 2))

        hist_frame = tk.Frame(left, bg=CTRL)
        hist_frame.pack(padx=10, pady=(0, 6))

        self.history_labels = []
        for i in range(15):
            lbl = tk.Label(hist_frame, text="", width=3, height=1,
                           font=("Arial", 8, "bold"), fg=CTRL_TEXT, bg=CTRL,
                           relief="flat", bd=0)
            lbl.grid(row=i // 5, column=i % 5, padx=2, pady=1)
            self.history_labels.append(lbl)

        gold_divider(left, padx=10, pady=(4, 0))

        # Chip selector
        tk.Label(left, text="SELECT CHIP", font=F_LABEL,
                 fg=CTRL_TEXT, bg=CTRL).pack(anchor="w", padx=12, pady=(8, 4))

        chip_frame = tk.Frame(left, bg=CTRL)
        chip_frame.pack(padx=8, pady=(0, 4), fill="x")

        self.chip_btns = {}
        for i, (amt, color) in enumerate([(1,"#566573"),(5,"#a93226"),(10,"#1f618d"),
                                           (25,"#1a7a40"),(50,"#b9770e"),(100,"#5b2c6f"),
                                           (500,"#c8a84b")]):
            btn = tk.Button(chip_frame, text=f"${amt}", font=F_CHIP,
                            bg=color, fg="black", width=5, height=2,
                            relief="flat", bd=0, cursor="hand2",
                            command=lambda a=amt: self.set_chip(a))
            btn.grid(row=i // 4, column=i % 4, padx=2, pady=2)
            _bind_hover(btn, color, "black", color, "black")
            self.chip_btns[amt] = btn

        self.chip_label = tk.Label(left, text="Chip:  $25",
                                   font=F_LABEL, fg=CTRL_TEXT, bg=CTRL)
        self.chip_label.pack(pady=(0, 4))
        self.set_chip(25)

        gold_divider(left, padx=10)

        self.spin_btn = styled_btn(left, "SPIN", self.spin, style="gold",
                                   font=("Georgia", 16, "bold"), width=14, height=2, fg="black")
        self.spin_btn.pack(pady=(10, 4))

        self.cancel_btn = styled_btn(left, "CANCEL BET", self._cancel_spin,
                                     style="cancel", font=F_BTN_SM, width=14,
                                     state="disabled", fg="black")
        self.cancel_btn.pack(pady=2)

        styled_btn(left, "Clear All Bets", self.clear_bets,
                   style="red", font=F_BTN_SM, width=14, fg="black").pack(pady=2)

        styled_btn(left, "Reset Bankroll", self.reset_bankroll,
                   style="muted", font=F_BTN_SM, width=14, fg="black").pack(pady=2)

    def back_to_lobby(self):
        if self.on_close:
            self.on_close(self.bankroll, self.session_log)
        self.root.destroy()

    # ── AI player panel ───────────────────────────────────────────────────────

    _AI_STYLE = {
        "Aggressive":   ("High Risk",  "#c0392b"),
        "Moderate":     ("Balanced",   "#b9770e"),
        "Conservative": ("Low Risk",   "#1a7a40"),
    }

    def _build_ai_panel(self, parent):
        panel = tk.Frame(parent, bg=CTRL, bd=0, width=210)
        panel.pack(side="right", fill="y", padx=(12, 0))
        panel.pack_propagate(False)

        tk.Label(panel, text="AI PLAYERS", font=F_LABEL,
                 fg=GOLD, bg=CTRL).pack(pady=(14, 2))
        gold_divider(panel, padx=10)

        self._ai_label_refs = []

        for ai in self.ai_players:
            subtitle, accent = self._AI_STYLE.get(ai.name, ("Player", GOLD))
            card = tk.Frame(panel, bg="#1a1a1a", bd=0)
            card.pack(fill="x", padx=10, pady=(8, 0))

            # Name row
            name_row = tk.Frame(card, bg="#1a1a1a")
            name_row.pack(fill="x", padx=8, pady=(8, 2))
            tk.Label(name_row, text=ai.name, font=("Arial", 11, "bold"),
                     fg=accent, bg="#1a1a1a", anchor="w").pack(side="left")

            tk.Label(card, text=subtitle, font=("Arial", 8),
                     fg="#888888", bg="#1a1a1a", anchor="w").pack(fill="x", padx=8)

            tk.Frame(card, bg="#333333", height=1).pack(fill="x", padx=8, pady=(4, 0))

            # Bankroll
            row_br = tk.Frame(card, bg="#1a1a1a")
            row_br.pack(fill="x", padx=8, pady=(6, 1))
            tk.Label(row_br, text="Bankroll", font=("Arial", 8),
                     fg="#888888", bg="#1a1a1a", anchor="w").pack(side="left")
            lbl_br = tk.Label(row_br, text=f"${ai.bankroll:,}",
                              font=("Arial", 10, "bold"), fg=CTRL_TEXT,
                              bg="#1a1a1a", anchor="e")
            lbl_br.pack(side="right")

            # Current bet
            row_bet = tk.Frame(card, bg="#1a1a1a")
            row_bet.pack(fill="x", padx=8, pady=1)
            tk.Label(row_bet, text="Bet", font=("Arial", 8),
                     fg="#888888", bg="#1a1a1a", anchor="w").pack(side="left")
            lbl_bet = tk.Label(row_bet, text="—",
                               font=("Arial", 10, "bold"), fg=CTRL_TEXT,
                               bg="#1a1a1a", anchor="e")
            lbl_bet.pack(side="right")

            # P/L
            row_pl = tk.Frame(card, bg="#1a1a1a")
            row_pl.pack(fill="x", padx=8, pady=(1, 8))
            tk.Label(row_pl, text="P/L", font=("Arial", 8),
                     fg="#888888", bg="#1a1a1a", anchor="w").pack(side="left")
            lbl_pl = tk.Label(row_pl, text="$0",
                              font=("Arial", 10, "bold"), fg=CTRL_TEXT,
                              bg="#1a1a1a", anchor="e")
            lbl_pl.pack(side="right")

            self._ai_label_refs.append((lbl_br, lbl_bet, lbl_pl))

        # ── Last Round section ────────────────────────────────────────────────
        gold_divider(panel, padx=10, pady=(10, 0))
        tk.Label(panel, text="LAST ROUND", font=F_LABEL,
                 fg=GOLD, bg=CTRL).pack(pady=(6, 2))

        self._round_rows = []
        for display_name in ["You", "Aggressive", "Moderate", "Conservative"]:
            block = tk.Frame(panel, bg=CTRL)
            block.pack(fill="x", padx=12, pady=(2, 0))

            top_row = tk.Frame(block, bg=CTRL)
            top_row.pack(fill="x")
            tk.Label(top_row, text=display_name, font=("Arial", 8, "bold"),
                     fg=CTRL_TEXT, bg=CTRL, anchor="w").pack(side="left")
            lbl_net = tk.Label(top_row, text="—", font=("Arial", 8, "bold"),
                               fg=CTRL_TEXT, bg=CTRL, anchor="e")
            lbl_net.pack(side="right")

            lbl_key = tk.Label(block, text="", font=("Arial", 7),
                               fg="#666666", bg=CTRL, anchor="w")
            lbl_key.pack(fill="x")

            self._round_rows.append((lbl_net, lbl_key))

        # ── Leaderboard section ───────────────────────────────────────────────
        gold_divider(panel, padx=10, pady=(10, 0))
        tk.Label(panel, text="LEADERBOARD", font=F_LABEL,
                 fg=GOLD, bg=CTRL).pack(pady=(6, 2))

        self._lb_rows = []
        for _ in range(4):
            row = tk.Frame(panel, bg=CTRL)
            row.pack(fill="x", padx=12, pady=1)
            lbl_rank = tk.Label(row, text="—", font=("Arial", 8, "bold"),
                                fg=CTRL_TEXT, bg=CTRL, anchor="w")
            lbl_rank.pack(side="left")
            lbl_br = tk.Label(row, text="—", font=("Arial", 8, "bold"),
                              fg=CTRL_TEXT, bg=CTRL, anchor="e")
            lbl_br.pack(side="right")
            self._lb_rows.append((lbl_rank, lbl_br))

    def _update_ai_panel(self):
        for ai, (lbl_br, lbl_bet, lbl_pl) in zip(self.ai_players, self._ai_label_refs):
            # Bankroll
            lbl_br.config(text=f"${ai.bankroll:,}")

            # Current bet (only visible while bet is pending)
            if ai.current_bet_key and ai.current_bet > 0:
                lbl_bet.config(text=f"${ai.current_bet:,}  ({ai.current_bet_key})")
            else:
                lbl_bet.config(text="—")

            # P/L with colour
            pl = ai.profit_loss
            if pl > 0:
                lbl_pl.config(text=f"+${pl:,}", fg="#2ecc71")
            elif pl < 0:
                lbl_pl.config(text=f"-${abs(pl):,}", fg="#e74c3c")
            else:
                lbl_pl.config(text="$0", fg=CTRL_TEXT)

    @staticmethod
    def _fmt_key(key):
        if not key:
            return ""
        if key.startswith("n_"):
            return f"#{key[2:]}"
        return {"dozen1": "1st 12", "dozen2": "2nd 12", "dozen3": "3rd 12",
                "col1": "Col 1",    "col2": "Col 2",    "col3": "Col 3"}.get(key, key)

    def _update_round_summary(self):
        # Human row
        net = self.last_human_net
        keys_str = ", ".join(self._fmt_key(k) for k in self.last_human_bet_keys[:2])
        if len(self.last_human_bet_keys) > 2:
            keys_str += "…"
        lbl_net, lbl_key = self._round_rows[0]
        lbl_key.config(text=keys_str)
        if net is None:
            lbl_net.config(text="—", fg=CTRL_TEXT)
        elif net > 0:
            lbl_net.config(text=f"+${net:,}", fg="#2ecc71")
        elif net < 0:
            lbl_net.config(text=f"-${abs(net):,}", fg="#e74c3c")
        else:
            lbl_net.config(text="Push", fg=CTRL_TEXT)

        # AI rows
        for i, ai in enumerate(self.ai_players):
            lbl_net, lbl_key = self._round_rows[i + 1]
            lbl_key.config(text=self._fmt_key(ai.last_bet_key))
            rn = ai.last_net
            if rn is None:
                lbl_net.config(text="—", fg=CTRL_TEXT)
            elif rn > 0:
                lbl_net.config(text=f"+${rn:,}", fg="#2ecc71")
            elif rn < 0:
                lbl_net.config(text=f"-${abs(rn):,}", fg="#e74c3c")
            else:
                lbl_net.config(text="Push", fg=CTRL_TEXT)

    def _update_leaderboard(self):
        players = [("You", self.bankroll, 1000)] + \
                  [(ai.name, ai.bankroll, ai.starting_bankroll) for ai in self.ai_players]
        players.sort(key=lambda x: x[1], reverse=True)
        for i, ((name, br, start), (lbl_rank, lbl_br)) in enumerate(
                zip(players, self._lb_rows)):
            lbl_rank.config(text=f"{i + 1}.  {name}")
            if br > start:
                lbl_br.config(text=f"${br:,}", fg="#2ecc71")
            elif br < start:
                lbl_br.config(text=f"${br:,}", fg="#e74c3c")
            else:
                lbl_br.config(text=f"${br:,}", fg=CTRL_TEXT)

    def _build_board(self, parent):
        right = tk.Frame(parent, bg=TABLE)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="BETTING BOARD — select a chip, then click",
                 font=F_LABEL, fg=TABLE_TEXT, bg=TABLE).pack(anchor="w", pady=(0, 6))

        self._build_chip_tray(right)   # packed side="bottom" before board

        board = tk.Frame(right, bg=TABLE)
        board.pack(fill="both", expand=True)

        # 14 columns (col 0 = zero, cols 1-12 = numbers, col 13 = 2:1)
        for c in range(14):
            board.columnconfigure(c, weight=1)
        # 5 rows: 0-2 numbers, 3 = dozens, 4 = outside bets
        for r in range(5):
            board.rowconfigure(r, weight=1)

        # 0 (spans rows 0-2)
        self._board_btn(board, "n_0", "0", "#1e8449", row=0, col=0, rowspan=3)

        # Numbers 1–36
        for i in range(1, 37):
            r = (i - 1) % 3
            c = (i - 1) // 3 + 1
            bg = "#c0392b" if i in RED_NUMBERS else "#1a252f"
            self._board_btn(board, f"n_{i}", str(i), bg, row=r, col=c)

        # 2:1 column buttons
        for r, (key, lbl) in enumerate(zip(
                ["col1", "col2", "col3"],
                ["Col 1\n2:1", "Col 2\n2:1", "Col 3\n2:1"])):
            self._board_btn(board, key, lbl, "#2e4053", row=r, col=13)

        # Dozens (row 3, cols 1-12 split into thirds)
        tk.Frame(board, bg=TABLE).grid(row=3, column=0, sticky="nsew")
        for i, (key, lbl) in enumerate(zip(
                ["dozen1", "dozen2", "dozen3"],
                ["1st 12  (1–12)", "2nd 12  (13–24)", "3rd 12  (25–36)"])):
            self._board_btn(board, key, lbl, "#2e4053",
                            row=3, col=1 + i * 4, colspan=4)

        # Outside bets (row 4, cols 1-12 split into sixths)
        tk.Frame(board, bg=TABLE).grid(row=4, column=0, sticky="nsew")
        outside = [
            ("low",   "1–18",  "#2e4053"),
            ("even",  "EVEN",  "#2e4053"),
            ("red",   "RED",   "#c0392b"),
            ("black", "BLACK", "#1a252f"),
            ("odd",   "ODD",   "#2e4053"),
            ("high",  "19–36", "#2e4053"),
        ]
        for i, (key, lbl, bg) in enumerate(outside):
            self._board_btn(board, key, lbl, bg,
                            row=4, col=1 + i * 2, colspan=2)

    # ── Chip tray ─────────────────────────────────────────────────────────────

    _TRAY_PLAYERS = [
        ("You",          "#c8a84b"),   # gold
        ("Aggressive",   "#c0392b"),   # red
        ("Moderate",     "#b9770e"),   # orange
        ("Conservative", "#1a7a40"),   # green
    ]

    def _build_chip_tray(self, parent):
        tray = tk.Frame(parent, bg=CTRL, height=110)
        tray.pack(side="bottom", fill="x", pady=(6, 0))
        tray.pack_propagate(False)

        tk.Label(tray, text="CHIP STACKS", font=F_LABEL,
                 fg=GOLD, bg=CTRL).pack(pady=(5, 2))

        cols_frame = tk.Frame(tray, bg=CTRL)
        cols_frame.pack(fill="both", expand=True, padx=8)

        self._chip_canvases = []
        for name, color in self._TRAY_PLAYERS:
            col = tk.Frame(cols_frame, bg=CTRL)
            col.pack(side="left", fill="both", expand=True)

            tk.Label(col, text=name, font=("Arial", 8, "bold"),
                     fg=CTRL_TEXT, bg=CTRL).pack()

            cv = tk.Canvas(col, width=64, height=52, bg=CTRL,
                           highlightthickness=0)
            cv.pack()

            amt_lbl = tk.Label(col, text="$0", font=("Arial", 8),
                               fg=CTRL_TEXT, bg=CTRL)
            amt_lbl.pack()

            self._chip_canvases.append((cv, amt_lbl, color))

    @staticmethod
    def _chip_count(bet):
        if bet <= 0:   return 0
        if bet < 10:   return 1
        if bet < 50:   return 2
        if bet < 150:  return 3
        if bet < 400:  return 4
        if bet < 800:  return 5
        return 6

    def _draw_chips(self, canvas, bet, color):
        canvas.delete("all")
        n = self._chip_count(bet)
        if n == 0:
            canvas.create_text(32, 28, text="—", fill="#555555",
                               font=("Arial", 11))
            return
        cx = 32
        # Draw chips bottom-up; each chip is a flat oval
        for i in range(n):
            y = 44 - i * 7
            # shadow
            canvas.create_oval(cx - 26, y - 5, cx + 26, y + 5,
                               fill="#111111", outline="")
            # chip body
            canvas.create_oval(cx - 26, y - 7, cx + 26, y + 3,
                               fill=color, outline="white", width=1)
            # centre stripe
            canvas.create_oval(cx - 8, y - 5, cx + 8, y + 1,
                               fill="white", outline="", stipple="gray50")

    def _update_chip_tray(self):
        human_bet = sum(self.active_bets.values())
        ai_bets   = [ai.current_bet for ai in self.ai_players]
        all_bets  = [human_bet] + ai_bets

        for (cv, lbl, color), bet in zip(self._chip_canvases, all_bets):
            self._draw_chips(cv, bet, color)
            lbl.config(text=f"${bet:,}" if bet > 0 else "$0")

    def _board_btn(self, parent, bet_key, label, bg,
                   row, col, rowspan=1, colspan=1):
        btn = tk.Button(parent, text=label, font=("Arial", 11, "bold"),
                        bg=bg, fg="black", cursor="hand2", relief="flat", bd=0,
                        command=lambda k=bet_key: self.place_chip(k))
        btn.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
                 padx=2, pady=2, sticky="nsew")
        _bind_hover(btn, bg, "black", bg, GOLD)
        self.board_buttons[bet_key] = (btn, label, bg)

    # ── Chip & bet logic ─────────────────────────────────────────────────────

    def set_chip(self, amount):
        self.chip_amount = amount
        self.chip_label.config(text=f"Chip:  ${amount:,}")
        for amt, btn in self.chip_btns.items():
            btn.config(relief="solid" if amt == amount else "flat",
                       bd=2 if amt == amount else 0)

    CONFLICTS = {"red": "black", "black": "red", "even": "odd", "odd": "even"}

    def place_chip(self, bet_key):
        if self.spinning:
            return
        conflict = self.CONFLICTS.get(bet_key)
        if conflict and conflict in self.active_bets:
            messagebox.showwarning("Invalid Bet",
                                   f"Can't bet {bet_key} and {conflict} at the same time.")
            return
        already_bet = sum(self.active_bets.values())
        if already_bet + self.chip_amount > self.bankroll:
            messagebox.showerror("Insufficient Funds",
                                 f"Only ${self.bankroll - already_bet:,} available.")
            return
        self.active_bets[bet_key] = self.active_bets.get(bet_key, 0) + self.chip_amount
        self._refresh_btn(bet_key)
        self._update_total()
        self._update_chip_tray()
        self._start_cancel_timer()

    def _refresh_btn(self, bet_key):
        btn, base_label, base_bg = self.board_buttons[bet_key]
        amount = self.active_bets.get(bet_key, 0)
        if amount > 0:
            btn.config(text=f"{base_label}\n${amount:,}",
                       bg=GOLD, fg="#111111", relief="flat", bd=0)
        else:
            btn.config(text=base_label, bg=base_bg, fg="black",
                       relief="flat", bd=0)

    def _update_total(self):
        total = sum(self.active_bets.values())
        self.total_bet_label.config(text=f"Total Bet: ${total:,}")

    def clear_bets(self):
        self.active_bets.clear()
        for key in self.board_buttons:
            btn, label, bg = self.board_buttons[key]
            btn.config(text=label, bg=bg, fg="black", relief="flat", bd=0)
        self._update_total()
        self._update_chip_tray()

    # ── Wheel drawing ────────────────────────────────────────────────────────

    def draw_wheel(self, ball_pos=None):
        self.canvas.delete("all")
        cx, cy = 140, 140
        r_rim = 135
        r_outer = 125
        r_inner = 64
        r_center = 44

        self.canvas.create_oval(cx-r_rim, cy-r_rim, cx+r_rim, cy+r_rim,
                                fill="#7d6608", outline="#b8860b", width=5)

        n = len(WHEEL_ORDER)
        for i, num in enumerate(WHEEL_ORDER):
            start = 360 * i / n - 90
            ext = 360 / n
            bg = "#1e8449" if num == 0 else "#c0392b" if num in RED_NUMBERS else "#1a252f"
            self.canvas.create_arc(cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer,
                                   start=start, extent=ext, fill=bg,
                                   outline="#d4ac0d", width=1)
            mid = math.radians(start + ext / 2)
            r_t = (r_outer + r_inner) / 2
            self.canvas.create_text(cx + r_t * math.cos(mid),
                                    cy - r_t * math.sin(mid),
                                    text=str(num), fill="white",
                                    font=("Arial", 6, "bold"))

        self.canvas.create_oval(cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner,
                                fill="#0b3d2e", outline="#d4ac0d", width=3)
        self.canvas.create_oval(cx-r_center, cy-r_center, cx+r_center, cy+r_center,
                                fill="#117864", outline="gold", width=2)

        if self.last_result is not None:
            v = self.last_result
            col = "#2ecc71" if v == 0 else "#e74c3c" if v in RED_NUMBERS else "#ecf0f1"
            self.canvas.create_oval(cx-25, cy-25, cx+25, cy+25,
                                    fill=col, outline="white", width=2)
            self.canvas.create_text(cx, cy, text=str(v), fill="white",
                                    font=("Arial", 17, "bold"))
        else:
            self.canvas.create_text(cx, cy, text="?", fill="white",
                                    font=("Arial", 24, "bold"))

        if ball_pos is not None:
            r_b = r_outer - 7
            bx = cx + r_b * math.cos(math.radians(ball_pos))
            by = cy - r_b * math.sin(math.radians(ball_pos))
            self.canvas.create_oval(bx-6, by-6, bx+6, by+6,
                                    fill="white", outline="#aaa", width=1)

    # ── Spin animation ───────────────────────────────────────────────────────

    def _start_cancel_timer(self):
        if self._cancel_id:
            self.root.after_cancel(self._cancel_id)
            self._cancel_id = None
        self._cancel_secs = 7
        self.cancel_btn.config(state="normal", text=f"CANCEL BET  {self._cancel_secs}s")
        self._tick_cancel()

    def _tick_cancel(self):
        if self._cancel_secs <= 0:
            self._hide_cancel()
            return
        self.cancel_btn.config(text=f"CANCEL BET  {self._cancel_secs}s")
        self._cancel_secs -= 1
        self._cancel_id = self.root.after(1000, self._tick_cancel)

    def _hide_cancel(self):
        if self._cancel_id:
            self.root.after_cancel(self._cancel_id)
            self._cancel_id = None
        self.cancel_btn.config(state="disabled", text="CANCEL BET")

    def _cancel_spin(self):
        self._hide_cancel()
        self.clear_bets()
        self.result_label.config(text="Bets cancelled — chips returned", fg=CTRL_TEXT)

    def animate_spin(self, step, total, init_speed):
        progress = step / total
        speed = max(2, int(init_speed * (1 - progress)))
        self.ball_angle = (self.ball_angle + speed) % 360
        self.draw_wheel(ball_pos=self.ball_angle)

        if step < total:
            self.root.after(max(16, int(60 * progress)),
                            lambda: self.animate_spin(step + 1, total, init_speed))
        else:
            n = len(WHEEL_ORDER)
            slot = int(((self.ball_angle + 90) % 360) * n / 360) % n
            result = WHEEL_ORDER[slot]
            self.last_result = result
            self.draw_wheel(ball_pos=self.ball_angle)
            self.root.after(300, lambda: self.finish_spin(result))

    def finish_spin(self, result):
        self._hide_cancel()
        self.resolve_bets(result)
        for ai in self.ai_players:
            ai.resolve(result, check_win, get_payout)
        self._update_ai_panel()
        self._update_round_summary()
        self._update_leaderboard()
        self._update_chip_tray()
        self.update_history(result)
        self.highlight_winner(result)
        self.spinning = False
        self.spin_btn.config(state="normal", bg=GOLD, text="SPIN")

    # ── Game logic ───────────────────────────────────────────────────────────

    def spin(self):
        if self.spinning:
            return
        if not self.active_bets:
            messagebox.showwarning("No Bets", "Click the board to place at least one bet.")
            return
        self.spinning = True
        self._hide_cancel()
        self.spin_btn.config(state="disabled", bg="#555555", text="Spinning...")
        for ai in self.ai_players:
            ai.choose_bet()
        self._update_ai_panel()
        self._update_chip_tray()
        self.result_label.config(text="Spinning...", fg=CTRL_TEXT)
        self.result_detail.config(text="")
        total = random.randint(45, 80)
        init_speed = random.randint(32, 52)
        self.animate_spin(step=0, total=total, init_speed=init_speed)

    def resolve_bets(self, result):
        net = 0
        for key, amount in self.active_bets.items():
            if check_win(key, result):
                net += amount * get_payout(key)
            else:
                net -= amount

        self.bankroll += net
        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")

        color = "Green" if result == 0 else "Red" if result in RED_NUMBERS else "Black"
        if net > 0:
            self.result_label.config(text=f"{result}  ({color})  —  YOU WON!", fg=CTRL_TEXT)
            self.result_detail.config(text=f"Net: +${net:,}", fg=CTRL_TEXT)
        elif net < 0:
            self.result_label.config(text=f"{result}  ({color})  —  You lost", fg=CTRL_TEXT)
            self.result_detail.config(text=f"Net: -${abs(net):,}", fg=CTRL_TEXT)
        else:
            self.result_label.config(text=f"{result}  ({color})  —  Push", fg=CTRL_TEXT)
            self.result_detail.config(text="Net: $0", fg=CTRL_TEXT)

        total_bet = sum(self.active_bets.values())
        color_str = "Green" if result == 0 else "Red" if result in RED_NUMBERS else "Black"
        self.session_log.append({"game": "Roulette", "bet": total_bet,
                                  "result": f"{result} ({color_str})", "net": net})
        self.last_human_net      = net
        self.last_human_bet      = total_bet
        self.last_human_bet_keys = list(self.active_bets.keys())
        self.active_bets.clear()
        self._update_total()

        if self.bankroll <= 0:
            messagebox.showinfo("Broke!", "You ran out of money. Resetting to $1,000.")
            self.reset_bankroll()

    def update_history(self, number):
        self.history.insert(0, number)
        self.history = self.history[:15]
        for i, lbl in enumerate(self.history_labels):
            if i < len(self.history):
                n = self.history[i]
                bg = "#2ecc71" if n == 0 else "#e74c3c" if n in RED_NUMBERS else "#2c3e50"
                lbl.config(text=str(n), bg=bg, fg=contrast_text(bg), relief="groove")
            else:
                lbl.config(text="", bg=CTRL, fg=CTRL_TEXT, relief="flat")

    def highlight_winner(self, number):
        key = f"n_{number}"
        for k, (btn, label, orig_bg) in self.board_buttons.items():
            if k == key:
                btn.config(text=label, bg=GOLD, fg="#111111", relief="flat", bd=0)
            else:
                btn.config(text=label, bg=orig_bg, fg="black", relief="flat", bd=0)

    def reset_bankroll(self):
        self.bankroll = 1000
        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")
        self.result_label.config(text="Place bets and SPIN!", fg=CTRL_TEXT)
        self.result_detail.config(text="", fg=CTRL_TEXT)
        self.last_result = None
        self.history = []
        self.ball_angle = 0
        self.active_bets.clear()
        self.draw_wheel()
        self._update_total()
        for lbl in self.history_labels:
            lbl.config(text="", bg="#145a32", relief="flat")
        for k, (btn, label, orig_bg) in self.board_buttons.items():
            btn.config(text=label, bg=orig_bg, fg="black", relief="flat", bd=0)
        self._update_chip_tray()


if __name__ == "__main__":
    root = tk.Tk()
    app = RouletteApp(root)
    root.mainloop()
