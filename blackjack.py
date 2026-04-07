import tkinter as tk
from tkinter import messagebox
import random
from theme import (BG_HDR, TABLE, TABLE_LT, CTRL, GOLD, GOLD_DIM,
                   CARD_BG, SUIT_RED, SUIT_BLK,
                   HDR_TEXT, TABLE_TEXT, TABLE_LT_TEXT, CTRL_TEXT,
                   WIN_COLOR, LOSS_COLOR, PUSH_COLOR, PERSONALITY_COLORS,
                   F_H2, F_LABEL, F_VALUE, F_RESULT, F_BTN_LG, F_BTN_SM, F_CHIP,
                   contrast_text, styled_btn, _bind_hover, gold_divider)
from blackjack_ai import BlackjackAI

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RED_SUITS = {'♥', '♦'}
CARD_W, CARD_H = 74, 104


def hand_value(hand):
    total, aces = 0, 0
    for rank, _ in hand:
        if rank == 'A':
            aces += 1
            total += 11
        elif rank in ('J', 'Q', 'K'):
            total += 10
        else:
            total += int(rank)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_blackjack(hand):
    return len(hand) == 2 and hand_value(hand) == 21


class BlackjackApp:
    def __init__(self, root, bankroll=1000, on_close=None, ai_players=None):
        self.root = root
        self.bankroll = bankroll
        self.on_close = on_close
        self.session_log = []
        self._bj_ais = [BlackjackAI(p) for p in ai_players] if ai_players else []
        self._ai_widgets = []
        self._human_last_net = None

        self.root.title("Casino Blackjack")
        self.root.geometry("960x780")
        self.root.minsize(880, 700)
        self.root.configure(bg="#0b3d2e")
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_lobby)

        self.bet = 0
        self.chip_amount = 25
        self.player_hand = []
        self.dealer_hand = []
        self.state = "betting"   # betting | playing | result
        self._cancel_id = None
        self._new_shoe()
        self._build_ui()

    # ── Deck ─────────────────────────────────────────────────────────────────

    def _new_shoe(self, decks=6):
        self.deck = [(r, s) for s in SUITS for r in RANKS] * decks
        random.shuffle(self.deck)

    def _deal_card(self):
        if len(self.deck) < 52:
            self._new_shoe()
        return self.deck.pop()

    # ── UI ───────────────────────────────────────────────────────────────────

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

        tk.Label(inner, text="♠  BLACKJACK  ♠", font=F_H2,
                 fg=HDR_TEXT, bg=BG_HDR).pack(side="left", padx=16, pady=12)

        self.bankroll_label = tk.Label(inner, text=f"Bankroll:  ${self.bankroll:,}",
                                       font=("Arial", 15, "bold"), fg=HDR_TEXT, bg=BG_HDR)
        self.bankroll_label.pack(side="right", pady=12)

        gold_divider(self.root)

        # ── Table ─────────────────────────────────────────────────────────────
        table = tk.Frame(self.root, bg=TABLE)
        table.pack(fill="both", expand=True, padx=16, pady=8)

        # AI panel on the right (if AI players present)
        if self._bj_ais:
            self._build_ai_panel(table)

        # Game area fills the rest
        game_area = tk.Frame(table, bg=TABLE)
        game_area.pack(side="left", fill="both", expand=True)

        # Dealer
        d_box = tk.Frame(game_area, bg=TABLE_LT)
        d_box.pack(fill="x", pady=(0, 4))
        d_top = tk.Frame(d_box, bg=TABLE_LT)
        d_top.pack(fill="x", padx=14, pady=(10, 2))
        tk.Label(d_top, text="DEALER", font=F_LABEL,
                 fg=TABLE_LT_TEXT, bg=TABLE_LT).pack(side="left")
        self.dealer_score = tk.Label(d_top, text="", font=F_VALUE,
                                     fg=TABLE_LT_TEXT, bg=TABLE_LT)
        self.dealer_score.pack(side="right")
        self.dealer_canvas = tk.Canvas(d_box, height=CARD_H + 16,
                                       bg=TABLE_LT, highlightthickness=0)
        self.dealer_canvas.pack(fill="x", padx=14, pady=(2, 12))

        # Result
        self.result_label = tk.Label(game_area, text="", font=F_RESULT,
                                     fg=TABLE_TEXT, bg=TABLE, height=2)
        self.result_label.pack()

        # Player
        p_box = tk.Frame(game_area, bg=TABLE_LT)
        p_box.pack(fill="x", pady=(4, 0))
        p_top = tk.Frame(p_box, bg=TABLE_LT)
        p_top.pack(fill="x", padx=14, pady=(10, 2))
        tk.Label(p_top, text="YOUR HAND", font=F_LABEL,
                 fg=TABLE_LT_TEXT, bg=TABLE_LT).pack(side="left")
        self.player_score = tk.Label(p_top, text="", font=F_VALUE,
                                     fg=TABLE_LT_TEXT, bg=TABLE_LT)
        self.player_score.pack(side="right")
        self.player_canvas = tk.Canvas(p_box, height=CARD_H + 16,
                                       bg=TABLE_LT, highlightthickness=0)
        self.player_canvas.pack(fill="x", padx=14, pady=(2, 12))

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
        tk.Label(bet_col, text="CURRENT BET", font=F_LABEL,
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

        self.hit_btn = styled_btn(act, "HIT", self._hit,
                                  style="green", font=F_BTN_LG, width=8, height=2,
                                  state="disabled", fg="black")
        self.hit_btn.pack(side="left", padx=3)

        self.stand_btn = styled_btn(act, "STAND", self._stand,
                                    style="orange", font=F_BTN_LG, width=8, height=2,
                                    state="disabled", fg="black")
        self.stand_btn.pack(side="left", padx=3)

        self.double_btn = styled_btn(act, "DOUBLE", self._double,
                                     style="purple", font=F_BTN_LG, width=8, height=2,
                                     state="disabled", fg="black")
        self.double_btn.pack(side="left", padx=3)

        self.cancel_btn = styled_btn(act, "CANCEL BET", self._cancel_deal,
                                     style="cancel", font=F_BTN_SM, width=10, height=2,
                                     state="disabled", fg="black")
        self.cancel_btn.pack(side="left", padx=3)

    # ── AI panel ──────────────────────────────────────────────────────────────

    def _build_ai_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_HDR, width=196)
        panel.pack(side="right", fill="y", padx=(8, 0))
        panel.pack_propagate(False)

        tk.Label(panel, text="AI PLAYERS", font=F_LABEL,
                 fg=GOLD, bg=BG_HDR).pack(pady=(12, 4))
        tk.Frame(panel, bg=GOLD_DIM, height=1).pack(fill="x", padx=10, pady=(0, 6))

        self._ai_widgets = []
        for ai in self._bj_ais:
            card = tk.Frame(panel, bg=CTRL, padx=8, pady=4)
            card.pack(fill="x", padx=8, pady=2)
            accent_color = PERSONALITY_COLORS.get(ai.personality, GOLD)
            tk.Frame(card, bg=accent_color, height=2).pack(fill="x", pady=(0, 4))

            tk.Label(card, text=ai.name.upper(), font=("Arial", 10, "bold"),
                     fg=accent_color, bg=CTRL).pack(anchor="w")

            bankroll_lbl = tk.Label(card, text=f"${ai.bankroll:,}",
                                    font=("Arial", 11, "bold"), fg=HDR_TEXT, bg=CTRL)
            bankroll_lbl.pack(anchor="w")

            bet_lbl = tk.Label(card, text="Bet: —", font=("Arial", 9),
                               fg=CTRL_TEXT, bg=CTRL)
            bet_lbl.pack(anchor="w")

            result_lbl = tk.Label(card, text="—", font=("Arial", 9),
                                  fg=CTRL_TEXT, bg=CTRL)
            result_lbl.pack(anchor="w")

            hand_canvas = tk.Canvas(card, height=44, bg=CTRL, highlightthickness=0)
            hand_canvas.pack(fill="x", pady=(2, 0))

            self._ai_widgets.append({
                "bankroll":    bankroll_lbl,
                "bet":         bet_lbl,
                "result":      result_lbl,
                "hand_canvas": hand_canvas,
            })

        # ── Last round ────────────────────────────────────────────────────────
        tk.Frame(panel, bg=GOLD_DIM, height=1).pack(fill="x", padx=10, pady=(6, 3))
        tk.Label(panel, text="LAST ROUND", font=("Arial", 8, "bold"),
                 fg=GOLD, bg=BG_HDR).pack(anchor="w", padx=12)

        self._round_rows = []
        names = ["You"] + [ai.name for ai in self._bj_ais]
        for name in names:
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
        for ai, w in zip(self._bj_ais, self._ai_widgets):
            w["bankroll"].config(text=f"${ai.bankroll:,}")
            if ai.bet > 0:
                w["bet"].config(text=f"Bet: ${ai.bet:,}")
            else:
                w["bet"].config(text="Bet: —")
            if ai.last_result is not None:
                net = ai.last_net
                net_str = f"+${net:,}" if net > 0 else f"-${abs(net):,}" if net < 0 else "$0"
                color = "#4caf50" if net > 0 else "#e74c3c" if net < 0 else CTRL_TEXT
                w["result"].config(text=f"{ai.last_result}  {net_str}", fg=color)
                self._draw_mini_hand(w["hand_canvas"], ai.hand)
            else:
                w["result"].config(text="—", fg=CTRL_TEXT)
                w["hand_canvas"].delete("all")

    def _update_round_summary(self):
        nets = [self._human_last_net] + [ai.last_net for ai in self._bj_ais]
        for lbl, net in zip(self._round_rows, nets):
            if net is None:
                lbl.config(text="—", fg=CTRL_TEXT)
            else:
                s = f"+${net:,}" if net > 0 else f"-${abs(net):,}" if net < 0 else "$0"
                lbl.config(text=s, fg="#4caf50" if net > 0 else "#e74c3c" if net < 0 else CTRL_TEXT)

    def _update_leaderboard(self):
        players = [("You", self.bankroll)] + [(ai.name, ai.bankroll) for ai in self._bj_ais]
        players.sort(key=lambda x: x[1], reverse=True)
        for rank, (lbl, (name, br)) in enumerate(zip(self._lbrd_rows, players), 1):
            lbl.config(text=f"{rank}  {name:<11} ${br:,}",
                       fg=GOLD if name == "You" else HDR_TEXT)

    _BJ_MW, _BJ_MH = 30, 38   # mini-card size for AI panel

    def _draw_mini_hand(self, canvas, hand):
        """Draw all cards in an AI hand as small cards in the panel canvas."""
        canvas.delete("all")
        if not hand:
            return
        x = 4
        for rank, suit in hand:
            canvas.create_rectangle(x+2, 4, x+self._BJ_MW+2, 4+self._BJ_MH,
                                     fill="#061a10", outline="")
            canvas.create_rectangle(x, 2, x+self._BJ_MW, 2+self._BJ_MH,
                                     fill=CARD_BG, outline="#c8b89a", width=1)
            col = SUIT_RED if suit in RED_SUITS else SUIT_BLK
            canvas.create_text(x+4,             2+5,           text=rank,
                                font=("Arial", 8, "bold"), fill=col, anchor="nw")
            canvas.create_text(x+4,             2+15,          text=suit,
                                font=("Arial", 8), fill=col, anchor="nw")
            canvas.create_text(x+self._BJ_MW//2, 2+self._BJ_MH//2, text=suit,
                                font=("Arial", 16), fill=col)
            x += self._BJ_MW + 5

    # ── Card drawing ──────────────────────────────────────────────────────────

    def _draw_cards(self, canvas, hand, hide_second=False):
        canvas.delete("all")
        x = 8
        for i, (rank, suit) in enumerate(hand):
            self._draw_card(canvas, x, 7, rank, suit, face_down=(hide_second and i == 1))
            x += CARD_W + 8

    def _draw_card(self, canvas, x, y, rank, suit, face_down=False):
        # Shadow
        canvas.create_rectangle(x + 3, y + 3, x + CARD_W + 3, y + CARD_H + 3,
                                 fill="#061a10", outline="")
        # Face
        canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                 fill=CARD_BG, outline="#c8b89a", width=1)
        if face_down:
            canvas.create_rectangle(x + 5, y + 5, x + CARD_W - 5, y + CARD_H - 5,
                                     fill="#1a3a6b", outline="")
            canvas.create_text(x + CARD_W // 2, y + CARD_H // 2,
                                text="?", font=("Arial", 22, "bold"), fill="white")
        else:
            color = SUIT_RED if suit in RED_SUITS else SUIT_BLK
            canvas.create_text(x + 7, y + 9, text=rank,
                                font=("Arial", 12, "bold"), fill=color, anchor="nw")
            canvas.create_text(x + 7, y + 24, text=suit,
                                font=("Arial", 12), fill=color, anchor="nw")
            canvas.create_text(x + CARD_W // 2, y + CARD_H // 2,
                                text=suit, font=("Arial", 28), fill=color)

    # ── Display helpers ───────────────────────────────────────────────────────

    def _refresh(self, hide_hole=True):
        self._draw_cards(self.dealer_canvas, self.dealer_hand, hide_second=hide_hole)
        self._draw_cards(self.player_canvas, self.player_hand)

        # Player score
        if self.player_hand:
            pv = hand_value(self.player_hand)
            self.player_score.config(text=str(pv))
        else:
            self.player_score.config(text="")

        # Dealer score
        if self.dealer_hand:
            if hide_hole:
                r, _ = self.dealer_hand[0]
                v = 10 if r in ('J', 'Q', 'K') else 11 if r == 'A' else int(r)
                self.dealer_score.config(text=f"{v} + ?")
            else:
                self.dealer_score.config(text=str(hand_value(self.dealer_hand)))
        else:
            self.dealer_score.config(text="")

    def _set_buttons(self, state):
        if state == "betting":
            self.deal_btn.config(state="normal", text="DEAL")
            self.hit_btn.config(state="disabled")
            self.stand_btn.config(state="disabled")
            self.double_btn.config(state="disabled")
        elif state == "playing":
            self.deal_btn.config(state="disabled")
            self.hit_btn.config(state="normal")
            self.stand_btn.config(state="normal")
            can_dbl = self.bet * 2 <= self.bankroll
            self.double_btn.config(state="normal" if can_dbl else "disabled")
        elif state == "dealer":
            self.deal_btn.config(state="disabled")
            self.hit_btn.config(state="disabled")
            self.stand_btn.config(state="disabled")
            self.double_btn.config(state="disabled")
        elif state == "result":
            self.deal_btn.config(state="normal", text="DEAL")
            self.hit_btn.config(state="disabled")
            self.stand_btn.config(state="disabled")
            self.double_btn.config(state="disabled")

    # ── Chip / bet controls ───────────────────────────────────────────────────

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

    # ── Game actions ──────────────────────────────────────────────────────────

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
            messagebox.showwarning("No Bet", "Place a bet before dealing.")
            return

        self._hide_cancel()
        self.player_hand = []
        self.dealer_hand = []
        self.state = "playing"
        self.result_label.config(text="")
        self._set_buttons("dealer")   # locked during animation
        self._refresh(hide_hole=True)

        # Set up AI bets before dealing; clear last-round cards
        for bj_ai in self._bj_ais:
            bj_ai.start_hand()
            bj_ai.choose_bet()
        for w in self._ai_widgets:
            w["hand_canvas"].delete("all")
        if self._bj_ais:
            self._update_ai_panel()

        # Deal in casino order: player, dealer, player, dealer — one card every 280ms
        sequence = [
            (self.player_hand, self._deal_card()),
            (self.dealer_hand, self._deal_card()),
            (self.player_hand, self._deal_card()),
            (self.dealer_hand, self._deal_card()),
        ]

        def deal_step(i):
            if i >= len(sequence):
                # Deal and auto-play AI hands (no animation)
                for bj_ai in self._bj_ais:
                    if bj_ai.bet > 0:
                        bj_ai.hand.append(self._deal_card())
                        bj_ai.hand.append(self._deal_card())
                        while bj_ai.decide() == "hit":
                            bj_ai.hand.append(self._deal_card())
                if self._bj_ais:
                    self._update_ai_panel()

                self._set_buttons("playing")
                player_bj = is_blackjack(self.player_hand)
                dealer_bj = is_blackjack(self.dealer_hand)
                if player_bj and dealer_bj:
                    self._end_round("push")
                elif player_bj:
                    self._end_round("blackjack")
                elif dealer_bj:
                    self._end_round("lose")
                return
            hand, card = sequence[i]
            hand.append(card)
            self._refresh(hide_hole=True)
            self.root.after(280, lambda: deal_step(i + 1))

        deal_step(0)

    def _hit(self):
        self._set_buttons("dealer")
        card = self._deal_card()
        self.root.after(220, lambda: self._apply_hit(card))

    def _apply_hit(self, card):
        self.player_hand.append(card)
        self._refresh(hide_hole=True)
        pv = hand_value(self.player_hand)
        if pv > 21:
            self._end_round("bust")
        elif pv == 21:
            self._play_dealer()
        else:
            self.hit_btn.config(state="normal")
            self.stand_btn.config(state="normal")
            self.double_btn.config(state="disabled")  # can't double after a hit

    def _stand(self):
        self._set_buttons("dealer")
        self._play_dealer()

    def _double(self):
        if self.bet * 2 > self.bankroll:
            messagebox.showerror("Insufficient Funds", "Not enough to double down.")
            return
        self.bet *= 2
        self.bet_label.config(text=f"${self.bet:,}")
        self._set_buttons("dealer")
        card = self._deal_card()
        self.root.after(220, lambda: self._apply_double(card))

    def _apply_double(self, card):
        self.player_hand.append(card)
        self._refresh(hide_hole=True)
        pv = hand_value(self.player_hand)
        if pv > 21:
            self._end_round("bust")
        else:
            self._play_dealer()

    def _play_dealer(self):
        self._refresh(hide_hole=False)
        self.root.after(600, self._dealer_step)

    def _dealer_step(self):
        dv = hand_value(self.dealer_hand)
        if dv < 17:
            self.dealer_hand.append(self._deal_card())
            self._refresh(hide_hole=False)
            self.root.after(600, self._dealer_step)
        else:
            self._determine_outcome()

    def _determine_outcome(self):
        pv = hand_value(self.player_hand)
        dv = hand_value(self.dealer_hand)
        if dv > 21:
            self._end_round("dealer_bust")
        elif pv > dv:
            self._end_round("win")
        elif pv < dv:
            self._end_round("lose")
        else:
            self._end_round("push")

    def _finish_dealer_silently(self):
        """Draw dealer to 17+ without animation (needed for AI resolution)."""
        while self.dealer_hand and hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self._deal_card())

    def _end_round(self, outcome):
        self.state = "result"
        self._set_buttons("result")
        self._finish_dealer_silently()
        self._refresh(hide_hole=False)

        if outcome == "blackjack":
            gain = int(self.bet * 1.5)
            self.bankroll += gain
            self._human_last_net = gain
            self.result_label.config(text=f"BLACKJACK!  +${gain:,}", fg=WIN_COLOR)
            self.session_log.append({"game": "Blackjack", "bet": self.bet, "result": "Blackjack", "net": gain})
        elif outcome == "win":
            self.bankroll += self.bet
            self._human_last_net = self.bet
            self.result_label.config(text=f"YOU WIN!  +${self.bet:,}", fg=WIN_COLOR)
            self.session_log.append({"game": "Blackjack", "bet": self.bet, "result": "Win", "net": self.bet})
        elif outcome == "dealer_bust":
            self.bankroll += self.bet
            self._human_last_net = self.bet
            self.result_label.config(text=f"DEALER BUSTS — YOU WIN!  +${self.bet:,}", fg=WIN_COLOR)
            self.session_log.append({"game": "Blackjack", "bet": self.bet, "result": "Dealer Bust", "net": self.bet})
        elif outcome in ("lose", "bust"):
            self.bankroll -= self.bet
            self._human_last_net = -self.bet
            msg = "BUST!" if outcome == "bust" else "DEALER WINS"
            self.result_label.config(text=f"{msg}  -${self.bet:,}", fg=LOSS_COLOR)
            self.session_log.append({"game": "Blackjack", "bet": self.bet, "result": msg, "net": -self.bet})
        elif outcome == "push":
            self._human_last_net = 0
            self.result_label.config(text="PUSH — Bet returned", fg=PUSH_COLOR)
            self.session_log.append({"game": "Blackjack", "bet": self.bet, "result": "Push", "net": 0})

        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")
        self.bet = 0
        self.bet_label.config(text="$0")

        # Resolve AI players against the (now fully played) dealer hand
        for bj_ai in self._bj_ais:
            bj_ai.resolve(self.dealer_hand)
        if self._bj_ais:
            self._update_ai_panel()
            self._update_round_summary()
            self._update_leaderboard()

        if self.bankroll <= 0:
            messagebox.showinfo("Broke!", "You ran out of money! Resetting to $1,000.")
            self.bankroll = 1000
            self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")

        # Return to betting state so chips and Deal button work immediately
        self.state = "betting"
        self._set_buttons("betting")

    # ── Navigation ────────────────────────────────────────────────────────────

    def back_to_lobby(self):
        if self.on_close:
            self.on_close(self.bankroll, self.session_log)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    BlackjackApp(root)
    root.mainloop()
