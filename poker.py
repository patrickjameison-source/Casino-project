import tkinter as tk
from tkinter import messagebox
import random
from collections import Counter
from itertools import combinations
from theme import (BG_HDR, TABLE, TABLE_LT, CTRL, GOLD, GOLD_DIM,
                   HDR_TEXT, TABLE_TEXT, TABLE_LT_TEXT, CTRL_TEXT,
                   WIN_COLOR, LOSS_COLOR, PUSH_COLOR, PERSONALITY_COLORS,
                   CARD_BG, SUIT_RED, SUIT_BLK,
                   F_H2, F_LABEL, F_VALUE, F_RESULT, F_BTN_LG, F_BTN_SM, F_CHIP,
                   contrast_text, styled_btn, _bind_hover, gold_divider)
from poker_ai import PokerAI

SUITS    = ['♠', '♥', '♦', '♣']
RANKS    = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
RED_SUITS = {'♥', '♦'}
CARD_W, CARD_H = 70, 100
RANK_VAL = {r: i + 2 for i, r in enumerate(RANKS)}


# ── Hand evaluation ────────────────────────────────────────────────────────────

def evaluate(hand):
    vals  = sorted([RANK_VAL[r] for r, _ in hand], reverse=True)
    suits = [s for _, s in hand]

    flush    = len(set(suits)) == 1
    straight = False
    s_vals   = vals
    if len(set(vals)) == 5:
        if vals[0] - vals[4] == 4:
            straight = True
        elif set(vals) == {14, 2, 3, 4, 5}:
            straight, s_vals = True, [5, 4, 3, 2, 1]

    cnt    = Counter(vals)
    groups = sorted(cnt.items(), key=lambda x: (x[1], x[0]), reverse=True)
    gc     = [c for _, c in groups]
    tb     = [v for v, _ in groups]

    if straight and flush:
        royal = (vals[0] == 14 and vals[1] == 13)
        return (9 if royal else 8,
                "Royal Flush" if royal else "Straight Flush",
                s_vals)
    if gc[0] == 4:          return (7, "Four of a Kind",  tb)
    if gc[:2] == [3, 2]:    return (6, "Full House",       tb)
    if flush:               return (5, "Flush",            vals)
    if straight:            return (4, "Straight",         s_vals)
    if gc[0] == 3:          return (3, "Three of a Kind",  tb)
    if gc[:2] == [2, 2]:    return (2, "Two Pair",         tb)
    if gc[0] == 2:          return (1, "One Pair",         tb)
    return (0, "High Card", vals)


def best_hand(cards):
    if len(cards) == 5:
        return evaluate(cards)
    return max(
        (evaluate(list(c)) for c in combinations(cards, 5)),
        key=lambda x: (x[0], x[2])
    )


# ── App ────────────────────────────────────────────────────────────────────────

class PokerApp:
    def __init__(self, root, bankroll=1000, on_close=None, ai_players=None):
        self.root        = root
        self.bankroll    = bankroll
        self.on_close    = on_close
        self.session_log = []
        self._pk_ais     = [PokerAI(p) for p in ai_players] if ai_players else []
        self._ai_widgets = []
        self._human_last_net = None

        self.root.title("Texas Hold'em")
        self.root.geometry("920x760")
        self.root.minsize(840, 700)
        self.root.configure(bg=TABLE)
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_lobby)

        self.bet         = 0
        self.chip_amount = 25
        self.player_hole = []
        self.community   = []
        self.folded      = False   # human folded this hand
        self.pot         = 0
        self.state       = "betting"
        self._cancel_id  = None
        self._new_deck()
        self._build_ui()

    # ── Deck ──────────────────────────────────────────────────────────────────

    def _new_deck(self):
        self.deck = [(r, s) for s in SUITS for r in RANKS]
        random.shuffle(self.deck)

    def _draw(self):
        if len(self.deck) < 12:
            self._new_deck()
        return self.deck.pop()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.configure(bg=TABLE)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG_HDR, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        inner = tk.Frame(hdr, bg=BG_HDR)
        inner.pack(fill="both", expand=True, padx=18)

        styled_btn(inner, "← Lobby", self.back_to_lobby,
                   style="muted", font=F_BTN_SM, fg="black").pack(side="left", pady=12)

        tk.Label(inner, text="♠  TEXAS HOLD'EM  ♠", font=F_H2,
                 fg=HDR_TEXT, bg=BG_HDR).pack(side="left", padx=16, pady=12)

        self.bankroll_label = tk.Label(inner, text=f"Bankroll:  ${self.bankroll:,}",
                                       font=("Arial", 15, "bold"), fg=HDR_TEXT, bg=BG_HDR)
        self.bankroll_label.pack(side="right", pady=12)

        gold_divider(self.root)

        # ── Table ─────────────────────────────────────────────────────────────
        table = tk.Frame(self.root, bg=TABLE)
        table.pack(fill="both", expand=True, padx=16, pady=6)

        if self._pk_ais:
            self._build_ai_panel(table)

        game_area = tk.Frame(table, bg=TABLE)
        game_area.pack(side="left", fill="both", expand=True)

        # Community
        c_box = tk.Frame(game_area, bg=TABLE)
        c_box.pack(fill="x", pady=(0, 3))
        c_top = tk.Frame(c_box, bg=TABLE)
        c_top.pack(fill="x", padx=14, pady=(8, 2))
        tk.Label(c_top, text="COMMUNITY", font=F_LABEL,
                 fg=TABLE_TEXT, bg=TABLE).pack(side="left")
        self.pot_label = tk.Label(c_top, text="Pot: $0", font=F_LABEL,
                                  fg=GOLD, bg=TABLE)
        self.pot_label.pack(side="right")
        self.community_canvas = tk.Canvas(c_box, height=CARD_H + 14,
                                          bg=TABLE, highlightthickness=0)
        self.community_canvas.pack(fill="x", padx=14, pady=(2, 8))

        # Result
        self.result_label = tk.Label(game_area, text="Place a bet and DEAL",
                                     font=F_RESULT, fg=TABLE_TEXT, bg=TABLE, height=2)
        self.result_label.pack(pady=4)

        # Player
        p_box = tk.Frame(game_area, bg=TABLE_LT)
        p_box.pack(fill="x", pady=(3, 0))
        p_top = tk.Frame(p_box, bg=TABLE_LT)
        p_top.pack(fill="x", padx=14, pady=(10, 2))
        tk.Label(p_top, text="YOUR HAND", font=F_LABEL,
                 fg=TABLE_LT_TEXT, bg=TABLE_LT).pack(side="left")
        self.player_hand_lbl = tk.Label(p_top, text="", font=("Arial", 14, "bold"),
                                        fg="black", bg=TABLE_LT)
        self.player_hand_lbl.pack(side="right")
        self.player_canvas = tk.Canvas(p_box, height=CARD_H + 14,
                                       bg=TABLE_LT, highlightthickness=0)
        self.player_canvas.pack(fill="x", padx=14, pady=(2, 10))

        # ── Controls ──────────────────────────────────────────────────────────
        gold_divider(self.root)
        bar = tk.Frame(self.root, bg=CTRL)
        bar.pack(fill="x")
        inner_bar = tk.Frame(bar, bg=CTRL)
        inner_bar.pack(fill="x", padx=18, pady=12)

        # Chip selector
        chip_col = tk.Frame(inner_bar, bg=CTRL)
        chip_col.pack(side="left")
        tk.Label(chip_col, text="SELECT CHIP", font=F_LABEL,
                 fg=CTRL_TEXT, bg=CTRL).pack(anchor="w", pady=(0, 6))
        chip_row = tk.Frame(chip_col, bg=CTRL)
        chip_row.pack()
        self.chip_btns = {}
        for amt, color in [(5,"#a93226"),(10,"#1f618d"),(25,"#1a7a40"),
                           (50,"#b9770e"),(100,"#5b2c6f"),(500,"#c8a84b")]:
            btn = tk.Button(chip_row, text=f"${amt}", font=F_CHIP,
                            bg=color, fg="black", width=5, height=2,
                            relief="flat", bd=0, cursor="hand2",
                            command=lambda a=amt: self._add_chip(a))
            btn.pack(side="left", padx=2)
            _bind_hover(btn, color, "black", color, "black")
            self.chip_btns[amt] = btn
        self._set_chip(25)

        # Bet display
        bet_col = tk.Frame(inner_bar, bg=CTRL)
        bet_col.pack(side="left", padx=22)
        tk.Label(bet_col, text="ANTE BET", font=F_LABEL,
                 fg=CTRL_TEXT, bg=CTRL).pack()
        self.bet_label = tk.Label(bet_col, text="$0", font=("Arial", 24, "bold"),
                                  fg=CTRL_TEXT, bg=CTRL, width=6)
        self.bet_label.pack()
        styled_btn(bet_col, "Clear", self._clear_bet,
                   style="muted", font=F_BTN_SM, width=5, fg="black").pack(pady=2)

        # Action buttons
        act = tk.Frame(inner_bar, bg=CTRL)
        act.pack(side="right")

        self.deal_btn = styled_btn(act, "DEAL", self._deal,
                                   style="gold", font=F_BTN_LG, width=8, height=2, fg="black")
        self.deal_btn.pack(side="left", padx=3)

        self.check_btn = styled_btn(act, "CHECK", self._check,
                                    style="green", font=F_BTN_LG, width=8, height=2,
                                    state="disabled", fg="black")
        self.check_btn.pack(side="left", padx=3)

        self.fold_btn = styled_btn(act, "FOLD", self._fold,
                                   style="red", font=F_BTN_LG, width=8, height=2,
                                   state="disabled", fg="black")
        self.fold_btn.pack(side="left", padx=3)

        self.cancel_btn = styled_btn(act, "CANCEL BET", self._cancel_deal,
                                     style="cancel", font=F_BTN_SM, width=10, height=2,
                                     state="disabled", fg="black")
        self.cancel_btn.pack(side="left", padx=3)

    # ── Button states ──────────────────────────────────────────────────────────

    def _set_buttons(self, state):
        if state == "betting":
            self.deal_btn.config(state="normal", text="DEAL")
            self.check_btn.config(state="disabled")
            self.fold_btn.config(state="disabled")
        elif state == "flop":
            self.deal_btn.config(state="disabled")
            self.check_btn.config(state="normal")
            self.fold_btn.config(state="normal")
        elif state == "dealing":
            self.deal_btn.config(state="disabled")
            self.check_btn.config(state="disabled")
            self.fold_btn.config(state="disabled")

    # ── Chip controls ──────────────────────────────────────────────────────────

    def _set_chip(self, amount):
        self.chip_amount = amount
        for amt, btn in self.chip_btns.items():
            btn.config(relief="solid" if amt == amount else "flat",
                       bd=2 if amt == amount else 0)

    def _add_chip(self, amount):
        if self.state != "betting":
            return
        if self.bet + amount > self.bankroll:
            messagebox.showerror("Insufficient Funds", "Not enough bankroll.")
            return
        self._set_chip(amount)
        self.bet += amount
        self.bet_label.config(text=f"${self.bet:,}")
        self._start_cancel_timer()

    def _clear_bet(self):
        if self.state != "betting":
            return
        self.bet = 0
        self.bet_label.config(text="$0")

    # ── AI panel ──────────────────────────────────────────────────────────────

    def _build_ai_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_HDR, width=196)
        panel.pack(side="right", fill="y", padx=(8, 0))
        panel.pack_propagate(False)

        tk.Label(panel, text="AI PLAYERS", font=F_LABEL,
                 fg=GOLD, bg=BG_HDR).pack(pady=(12, 4))
        tk.Frame(panel, bg=GOLD_DIM, height=1).pack(fill="x", padx=10, pady=(0, 6))

        self._ai_widgets = []
        for ai in self._pk_ais:
            card = tk.Frame(panel, bg=CTRL, padx=8, pady=3)
            card.pack(fill="x", padx=8, pady=2)
            accent_color = PERSONALITY_COLORS.get(ai.personality, GOLD)
            tk.Frame(card, bg=accent_color, height=2).pack(fill="x", pady=(0, 4))

            tk.Label(card, text=ai.name.upper(), font=("Arial", 10, "bold"),
                     fg=accent_color, bg=CTRL).pack(anchor="w")

            bankroll_lbl = tk.Label(card, text=f"${ai.bankroll:,}",
                                    font=("Arial", 11, "bold"), fg=HDR_TEXT, bg=CTRL)
            bankroll_lbl.pack(anchor="w")

            bet_lbl = tk.Label(card, text="Ante: —", font=("Arial", 9),
                               fg=CTRL_TEXT, bg=CTRL)
            bet_lbl.pack(anchor="w")

            status_lbl = tk.Label(card, text="—", font=("Arial", 9),
                                  fg=CTRL_TEXT, bg=CTRL)
            status_lbl.pack(anchor="w")

            hand_canvas = tk.Canvas(card, height=52, bg=CTRL,
                                    highlightthickness=0)
            hand_canvas.pack(fill="x", pady=(2, 0))

            self._ai_widgets.append({
                "bankroll":    bankroll_lbl,
                "bet":         bet_lbl,
                "status":      status_lbl,
                "hand_canvas": hand_canvas,
            })

        # ── Last round ────────────────────────────────────────────────────────
        tk.Frame(panel, bg=GOLD_DIM, height=1).pack(fill="x", padx=10, pady=(6, 3))
        tk.Label(panel, text="LAST ROUND", font=("Arial", 8, "bold"),
                 fg=GOLD, bg=BG_HDR).pack(anchor="w", padx=12)

        self._round_rows = []
        for name in ["You"] + [ai.name for ai in self._pk_ais]:
            row = tk.Frame(panel, bg=BG_HDR)
            row.pack(fill="x", padx=10)
            tk.Label(row, text=name, font=("Arial", 8), fg=CTRL_TEXT,
                     bg=BG_HDR, width=10, anchor="w").pack(side="left")
            net_lbl = tk.Label(row, text="—", font=("Arial", 8),
                               fg=CTRL_TEXT, bg=BG_HDR)
            net_lbl.pack(side="right")
            self._round_rows.append(net_lbl)

        # ── Leaderboard ───────────────────────────────────────────────────────
        tk.Frame(panel, bg=GOLD_DIM, height=1).pack(fill="x", padx=10, pady=(6, 3))
        tk.Label(panel, text="LEADERBOARD", font=("Arial", 8, "bold"),
                 fg=GOLD, bg=BG_HDR).pack(anchor="w", padx=12)

        self._lbrd_rows = []
        for _ in range(4):
            lbl = tk.Label(panel, text="", font=("Arial", 8),
                           fg=CTRL_TEXT, bg=BG_HDR, anchor="w")
            lbl.pack(fill="x", padx=12)
            self._lbrd_rows.append(lbl)

    def _update_ai_panel(self):
        for ai, w in zip(self._pk_ais, self._ai_widgets):
            w["bankroll"].config(text=f"${ai.bankroll:,}")
            if ai.bet > 0:
                w["bet"].config(text=f"Ante: ${ai.bet:,}")
            else:
                w["bet"].config(text="Ante: —")

            if ai.last_result is not None:
                net = ai.last_net
                net_str = f"+${net:,}" if net > 0 else f"-${abs(net):,}" if net < 0 else "$0"
                color = "#4caf50" if net > 0 else "#e74c3c" if net < 0 else CTRL_TEXT
                w["status"].config(text=f"{ai.last_result}  {net_str}", fg=color)
                # Reveal hole cards at end of round
                self._draw_mini_cards(w["hand_canvas"], ai.hand)
            elif ai.folded:
                w["status"].config(text="Folded", fg="#e74c3c")
                self._draw_mini_cards(w["hand_canvas"], ai.hand)
            elif ai.bet > 0:
                w["status"].config(text="Checking...", fg=CTRL_TEXT)
                w["hand_canvas"].delete("all")
            else:
                w["status"].config(text="—", fg=CTRL_TEXT)
                w["hand_canvas"].delete("all")

    def _update_round_summary(self):
        nets = [self._human_last_net] + [ai.last_net for ai in self._pk_ais]
        for lbl, net in zip(self._round_rows, nets):
            if net is None:
                lbl.config(text="—", fg=CTRL_TEXT)
            else:
                s = f"+${net:,}" if net > 0 else f"-${abs(net):,}" if net < 0 else "$0"
                lbl.config(text=s, fg="#4caf50" if net > 0 else "#e74c3c" if net < 0 else CTRL_TEXT)

    def _update_leaderboard(self):
        players = [("You", self.bankroll)] + [(ai.name, ai.bankroll) for ai in self._pk_ais]
        players.sort(key=lambda x: x[1], reverse=True)
        for rank, (lbl, (name, br)) in enumerate(zip(self._lbrd_rows, players), 1):
            lbl.config(text=f"{rank}  {name:<11} ${br:,}",
                       fg=GOLD if name == "You" else HDR_TEXT)

    # ── Card drawing ───────────────────────────────────────────────────────────

    _MW, _MH = 38, 44   # mini-card dimensions for AI panel

    def _draw_mini_cards(self, canvas, hand):
        """Draw two small hole cards inside an AI panel canvas."""
        canvas.delete("all")
        if not hand:
            return
        x = 4
        for rank, suit in hand:
            canvas.create_rectangle(x+2, 4, x+self._MW+2, 4+self._MH,
                                     fill="#061a10", outline="")
            canvas.create_rectangle(x, 2, x+self._MW, 2+self._MH,
                                     fill=CARD_BG, outline="#c8b89a", width=1)
            col = SUIT_RED if suit in RED_SUITS else SUIT_BLK
            canvas.create_text(x+5,           2+5,          text=rank,
                                font=("Arial", 9, "bold"), fill=col, anchor="nw")
            canvas.create_text(x+5,           2+16,         text=suit,
                                font=("Arial", 9), fill=col, anchor="nw")
            canvas.create_text(x+self._MW//2, 2+self._MH//2, text=suit,
                                font=("Arial", 18), fill=col)
            x += self._MW + 6

    def _draw_cards(self, canvas, hand, face_down=None):
        canvas.delete("all")
        if face_down is None:
            face_down = set()
        x = 8
        for i, (rank, suit) in enumerate(hand):
            self._draw_card(canvas, x, 6, rank, suit, i in face_down)
            x += CARD_W + 8

    def _draw_card(self, canvas, x, y, rank, suit, face_down=False):
        canvas.create_rectangle(x + 3, y + 3, x + CARD_W + 3, y + CARD_H + 3,
                                 fill="#061a10", outline="")
        canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                 fill=CARD_BG, outline="#c8b89a", width=1)
        if face_down:
            canvas.create_rectangle(x + 4, y + 4, x + CARD_W - 4, y + CARD_H - 4,
                                     fill="#1a3a6b", outline="")
            canvas.create_text(x + CARD_W // 2, y + CARD_H // 2,
                                text="?", font=("Arial", 20, "bold"), fill="white")
        else:
            col = SUIT_RED if suit in RED_SUITS else SUIT_BLK
            canvas.create_text(x + 6,           y + 8,  text=rank,
                                font=("Arial", 11, "bold"), fill=col, anchor="nw")
            canvas.create_text(x + 6,           y + 22, text=suit,
                                font=("Arial", 11), fill=col, anchor="nw")
            canvas.create_text(x + CARD_W // 2, y + CARD_H // 2, text=suit,
                                font=("Arial", 26), fill=col)

    # ── Game flow ──────────────────────────────────────────────────────────────

    def _start_cancel_timer(self):
        if self._cancel_id:
            self.root.after_cancel(self._cancel_id)
            self._cancel_id = None
        self._cancel_secs = 7
        self.cancel_btn.config(state="normal", text=f"CANCEL BET\n{self._cancel_secs}s")
        self._tick_cancel()

    def _tick_cancel(self):
        if self._cancel_secs <= 0:
            self._hide_cancel()
            return
        self.cancel_btn.config(text=f"CANCEL BET\n{self._cancel_secs}s")
        self._cancel_secs -= 1
        self._cancel_id = self.root.after(1000, self._tick_cancel)

    def _hide_cancel(self):
        if self._cancel_id:
            self.root.after_cancel(self._cancel_id)
            self._cancel_id = None
        self.cancel_btn.config(state="disabled", text="CANCEL BET")

    def _cancel_deal(self):
        self._hide_cancel()
        self._clear_bet()
        self.result_label.config(text="Bet cancelled — chips returned", fg=TABLE_TEXT)

    def _deal(self):
        if self.bet == 0:
            messagebox.showwarning("No Bet", "Place an ante bet before dealing.")
            return

        self.player_hole = []
        self.community   = []
        self.folded      = False
        self.state       = "dealing"
        self._hide_cancel()

        self.result_label.config(text="", fg=TABLE_TEXT)
        self.player_hand_lbl.config(text="")
        self.community_canvas.delete("all")
        self.player_canvas.delete("all")
        for w in self._ai_widgets:
            w["hand_canvas"].delete("all")
        self._set_buttons("dealing")

        # AI antes
        for pk_ai in self._pk_ais:
            pk_ai.start_hand()
            pk_ai.choose_bet()

        # Pot = human ante + all AI antes (committed before fold decisions)
        self.pot = self.bet + sum(ai.bet for ai in self._pk_ais)
        self.pot_label.config(text=f"Pot: ${self.pot:,}")

        if self._pk_ais:
            self._update_ai_panel()

        # Draw all hole cards and flop from the same deck
        p1, p2   = self._draw(), self._draw()
        for pk_ai in self._pk_ais:
            if pk_ai.bet > 0:
                pk_ai.hand = [self._draw(), self._draw()]
        f1, f2, f3 = self._draw(), self._draw(), self._draw()

        # Animate: player card 1, player card 2, flop 1-2-3
        sequence = [
            ("player", p1), ("player", p2),
            ("flop", f1), ("flop", f2), ("flop", f3),
        ]

        def step(i):
            if i >= len(sequence):
                # AI decides check or fold based on flop
                for pk_ai in self._pk_ais:
                    if pk_ai.bet > 0:
                        decision = pk_ai.decide(self.community)
                        if decision == "fold":
                            pk_ai.folded      = True
                            pk_ai.last_result = "Fold"
                            pk_ai.last_net    = -pk_ai.bet
                            pk_ai.player.apply_result(-pk_ai.bet, pk_ai.bet, "poker")
                if self._pk_ais:
                    self._update_ai_panel()

                self.state = "flop"
                self._set_buttons("flop")
                self._show_player_hand()
                self.result_label.config(text="CHECK to see Turn & River  —  or  FOLD")
                return
            who, card = sequence[i]
            if who == "player":
                self.player_hole.append(card)
                self._draw_cards(self.player_canvas, self.player_hole)
            else:
                self.community.append(card)
                self._draw_cards(self.community_canvas, self.community)
            self.root.after(220, lambda: step(i + 1))

        step(0)

    def _check(self):
        """Deal turn + river, then go to showdown."""
        self.state = "dealing"
        self._set_buttons("dealing")
        self.result_label.config(text="")

        turn  = self._draw()
        river = self._draw()

        def deal_remaining(i):
            if i == 0:
                self.community.append(turn)
                self._draw_cards(self.community_canvas, self.community)
                self.root.after(350, lambda: deal_remaining(1))
            elif i == 1:
                self.community.append(river)
                self._draw_cards(self.community_canvas, self.community)
                self.root.after(350, lambda: deal_remaining(2))
            else:
                self.root.after(400, self._showdown)

        deal_remaining(0)

    def _fold(self):
        """Human folds — lose ante; complete community silently for AI resolution."""
        self.folded = True
        net = -self.bet
        self._human_last_net = net
        self.bankroll += net
        self.bankroll_label.config(text=f"Bankroll:  ${self.bankroll:,}")
        self.session_log.append({"game": "Poker", "bet": self.bet,
                                 "result": "Fold", "net": net})

        # Draw turn + river silently so AI who checked can be resolved
        while len(self.community) < 5:
            self.community.append(self._draw())

        # Resolve AI-vs-AI among non-folded players
        self._resolve_all(human_active=False)

        # Show brief fold message then who won among AIs
        winner_name = self._ai_winner_name()
        if winner_name:
            self.result_label.config(
                text=f"You folded  —  -${self.bet:,}    {winner_name} wins the pot",
                fg=LOSS_COLOR)
        else:
            self.result_label.config(text=f"You folded  —  -${self.bet:,}", fg=LOSS_COLOR)

        self.pot_label.config(text="Pot: $0")
        self.bet = 0
        self.bet_label.config(text="$0")
        self.state = "betting"
        self._set_buttons("betting")
        self._check_broke()

    def _showdown(self):
        """Compare all active hands; winner takes the pot."""
        # Collect active (non-folded) entries: (score, tiebreak, label, is_human, pk_ai)
        entries = []

        p_cards = self.player_hole + self.community
        p_score, p_name, p_tb = best_hand(p_cards)
        self.player_hand_lbl.config(text=p_name)
        entries.append((p_score, p_tb, p_name, True, None))

        for pk_ai in self._pk_ais:
            if not pk_ai.folded and pk_ai.hand:
                ai_cards = pk_ai.hand + self.community
                s, name, tb = best_hand(ai_cards)
                entries.append((s, tb, name, False, pk_ai))

        # Find winning score
        best_score = max((s, tb) for s, tb, *_ in entries)
        winners    = [e for e in entries if (e[0], e[1]) == best_score]
        split      = self.pot // len(winners)

        self._resolve_all(human_active=True, winners=winners, split=split,
                          p_name=p_name)

        self.pot_label.config(text="Pot: $0")
        self.bet = 0
        self.bet_label.config(text="$0")
        self.state = "betting"
        self._set_buttons("betting")
        self._check_broke()

    # ── Resolution helpers ─────────────────────────────────────────────────────

    def _resolve_all(self, human_active, winners=None, split=0, p_name=""):
        """
        Apply bankroll changes to all players and update the UI.

        human_active=True  → full showdown path (winners/split/p_name provided)
        human_active=False → human already resolved (fold); only settle AIs vs each other
        """
        if human_active:
            human_wins  = any(e[3] for e in winners)   # is_human in any winner
            human_net   = split - self.bet if human_wins else -self.bet
            self._human_last_net = human_net
            self.bankroll += human_net
            self.bankroll_label.config(text=f"Bankroll:  ${self.bankroll:,}")

            if human_wins:
                txt   = f"YOU WIN!  +${human_net:,}  ({p_name})"
                color = WIN_COLOR
            elif len(winners) == 1 and not winners[0][3]:
                winner_ai = winners[0][4]
                txt   = f"{winner_ai.name} wins  -${self.bet:,}  (your {p_name})"
                color = LOSS_COLOR
            else:
                txt   = f"Loss  -${self.bet:,}  (your {p_name})"
                color = LOSS_COLOR
            self.result_label.config(text=txt, fg=color)
            self.session_log.append({"game": "Poker", "bet": self.bet,
                                     "result": f"{'Win' if human_wins else 'Loss'} ({p_name})",
                                     "net": human_net})

            # Settle AIs
            active_ais = [e[4] for e in winners if not e[3]]  # winning AI adapters
            for pk_ai in self._pk_ais:
                if pk_ai.folded:
                    continue
                ai_wins = pk_ai in active_ais
                ai_net  = split - pk_ai.bet if ai_wins else -pk_ai.bet
                _, ai_hand_name, _ = best_hand(pk_ai.hand + self.community)
                pk_ai.player.apply_result(ai_net, pk_ai.bet, "poker")
                pk_ai.last_net    = ai_net
                pk_ai.last_result = f"{'Win' if ai_wins else 'Loss'} ({ai_hand_name})"

        else:
            # Human folded — resolve AIs vs each other
            active_ais = [ai for ai in self._pk_ais if not ai.folded and ai.hand]
            if active_ais:
                # Find AI winner(s) among those still in
                ai_pot = self.pot   # full pot still goes to AI winner

                scored = []
                for ai in active_ais:
                    ai_cards = ai.hand + self.community
                    s, name, tb = best_hand(ai_cards)
                    scored.append((s, tb, name, ai))

                best_ai = max((s, tb) for s, tb, *_ in scored)
                ai_winners = [x for x in scored if (x[0], x[1]) == best_ai]
                ai_split   = ai_pot // len(ai_winners)
                winning_ais = [x[3] for x in ai_winners]

                for ai in active_ais:
                    ai_cards = ai.hand + self.community
                    _, ai_hand_name, _ = best_hand(ai_cards)
                    ai_wins = ai in winning_ais
                    ai_net  = ai_split - ai.bet if ai_wins else -ai.bet
                    ai.player.apply_result(ai_net, ai.bet, "poker")
                    ai.last_net    = ai_net
                    ai.last_result = f"{'Win' if ai_wins else 'Loss'} ({ai_hand_name})"

        if self._pk_ais:
            self._update_ai_panel()
            self._update_round_summary()
            self._update_leaderboard()

    def _ai_winner_name(self) -> str:
        """Return the name of the AI winner (for display after human fold)."""
        winning = [ai for ai in self._pk_ais
                   if not ai.folded and ai.last_result and ai.last_result.startswith("Win")]
        if len(winning) == 1:
            return winning[0].name
        if len(winning) > 1:
            return " & ".join(ai.name for ai in winning)
        return ""

    # ── Hand display ───────────────────────────────────────────────────────────

    def _show_player_hand(self):
        cards = self.player_hole + self.community
        if len(cards) >= 5:
            _, name, _ = best_hand(cards)
            self.player_hand_lbl.config(text=name)

    def _check_broke(self):
        if self.bankroll <= 0:
            messagebox.showinfo("Broke!", "You ran out of money! Resetting to $1,000.")
            self.bankroll = 1000
            self.bankroll_label.config(text=f"Bankroll:  ${self.bankroll:,}")

    # ── Navigation ────────────────────────────────────────────────────────────

    def back_to_lobby(self):
        if self.on_close:
            self.on_close(self.bankroll, self.session_log)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    PokerApp(root)
    root.mainloop()
