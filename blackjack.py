import tkinter as tk
from tkinter import messagebox
import random

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
    def __init__(self, root, bankroll=1000, on_close=None):
        self.root = root
        self.bankroll = bankroll
        self.on_close = on_close

        self.root.title("Casino Blackjack")
        self.root.geometry("960x700")
        self.root.minsize(880, 640)
        self.root.configure(bg="#0b3d2e")
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_lobby)

        self.bet = 0
        self.chip_amount = 25
        self.player_hand = []
        self.dealer_hand = []
        self.state = "betting"   # betting | playing | result
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
        # Header
        header = tk.Frame(self.root, bg="#111111", height=62)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="♠  CASINO BLACKJACK  ♠", font=("Georgia", 22, "bold"),
                 fg="gold", bg="#111111").pack(side="left", padx=22, pady=15)

        self.bankroll_label = tk.Label(header, text=f"Bankroll: ${self.bankroll:,}",
                                       font=("Arial", 17, "bold"), fg="white", bg="#111111")
        self.bankroll_label.pack(side="right", padx=22)

        # Table
        table = tk.Frame(self.root, bg="#0b3d2e")
        table.pack(fill="both", expand=True, padx=18, pady=8)

        # Dealer section
        dealer_box = tk.Frame(table, bg="#145a32", bd=2, relief="ridge")
        dealer_box.pack(fill="x", pady=(0, 4))

        dealer_top = tk.Frame(dealer_box, bg="#145a32")
        dealer_top.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(dealer_top, text="DEALER", font=("Arial", 11, "bold"),
                 fg="#aab7b8", bg="#145a32").pack(side="left")
        self.dealer_score = tk.Label(dealer_top, text="", font=("Arial", 20, "bold"),
                                     fg="white", bg="#145a32")
        self.dealer_score.pack(side="right")

        self.dealer_canvas = tk.Canvas(dealer_box, height=CARD_H + 14,
                                       bg="#145a32", highlightthickness=0)
        self.dealer_canvas.pack(fill="x", padx=12, pady=(2, 10))

        # Result
        self.result_label = tk.Label(table, text="", font=("Arial", 20, "bold"),
                                     fg="white", bg="#0b3d2e", height=2)
        self.result_label.pack()

        # Player section
        player_box = tk.Frame(table, bg="#145a32", bd=2, relief="ridge")
        player_box.pack(fill="x", pady=(4, 0))

        player_top = tk.Frame(player_box, bg="#145a32")
        player_top.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(player_top, text="PLAYER", font=("Arial", 11, "bold"),
                 fg="#aab7b8", bg="#145a32").pack(side="left")
        self.player_score = tk.Label(player_top, text="", font=("Arial", 20, "bold"),
                                     fg="white", bg="#145a32")
        self.player_score.pack(side="right")

        self.player_canvas = tk.Canvas(player_box, height=CARD_H + 14,
                                       bg="#145a32", highlightthickness=0)
        self.player_canvas.pack(fill="x", padx=12, pady=(2, 10))

        # Controls bar
        bar = tk.Frame(self.root, bg="#1c2833", bd=2, relief="ridge")
        bar.pack(fill="x", padx=18, pady=(0, 14))

        # Chips
        chip_col = tk.Frame(bar, bg="#1c2833")
        chip_col.pack(side="left", padx=14, pady=10)

        tk.Label(chip_col, text="Select Chip", font=("Arial", 9, "bold"),
                 fg="#aab7b8", bg="#1c2833").pack(anchor="w")

        chip_row = tk.Frame(chip_col, bg="#1c2833")
        chip_row.pack()

        chips = [(5, "#e74c3c"), (10, "#3498db"), (25, "#27ae60"),
                 (50, "#e67e22"), (100, "#8e44ad"), (500, "#f1c40f")]
        self.chip_btns = {}
        for amt, color in chips:
            btn = tk.Button(chip_row, text=f"${amt}", font=("Arial", 9, "bold"),
                            bg=color, fg="black", width=5, height=1, relief="raised", bd=2,
                            command=lambda a=amt: self._add_chip(a))
            btn.pack(side="left", padx=2)
            self.chip_btns[amt] = btn
        self._set_chip(25)

        # Bet display
        bet_col = tk.Frame(bar, bg="#1c2833")
        bet_col.pack(side="left", padx=18, pady=10)

        tk.Label(bet_col, text="Current Bet", font=("Arial", 9, "bold"),
                 fg="#aab7b8", bg="#1c2833").pack()
        self.bet_label = tk.Label(bet_col, text="$0", font=("Arial", 22, "bold"),
                                  fg="gold", bg="#1c2833", width=7)
        self.bet_label.pack()
        tk.Button(bet_col, text="Clear", font=("Arial", 8), bg="#566573", fg="white",
                  width=5, command=self._clear_bet).pack(pady=2)

        # Action buttons
        act = tk.Frame(bar, bg="#1c2833")
        act.pack(side="right", padx=14, pady=10)

        self.deal_btn = tk.Button(act, text="DEAL", font=("Arial", 13, "bold"),
                                  bg="gold", fg="black", width=8, height=2,
                                  command=self._deal)
        self.deal_btn.pack(side="left", padx=3)

        self.hit_btn = tk.Button(act, text="HIT", font=("Arial", 13, "bold"),
                                 bg="#27ae60", fg="black", width=8, height=2,
                                 state="disabled", command=self._hit)
        self.hit_btn.pack(side="left", padx=3)

        self.stand_btn = tk.Button(act, text="STAND", font=("Arial", 13, "bold"),
                                   bg="#e67e22", fg="black", width=8, height=2,
                                   state="disabled", command=self._stand)
        self.stand_btn.pack(side="left", padx=3)

        self.double_btn = tk.Button(act, text="DOUBLE", font=("Arial", 13, "bold"),
                                    bg="#8e44ad", fg="black", width=8, height=2,
                                    state="disabled", command=self._double)
        self.double_btn.pack(side="left", padx=3)

        tk.Button(act, text="Lobby", font=("Arial", 10), bg="#2c3e50", fg="white",
                  width=7, height=2, command=self.back_to_lobby).pack(side="left", padx=3)

    # ── Card drawing ──────────────────────────────────────────────────────────

    def _draw_cards(self, canvas, hand, hide_second=False):
        canvas.delete("all")
        x = 8
        for i, (rank, suit) in enumerate(hand):
            self._draw_card(canvas, x, 7, rank, suit, face_down=(hide_second and i == 1))
            x += CARD_W + 8

    def _draw_card(self, canvas, x, y, rank, suit, face_down=False):
        canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                 fill="white", outline="#bbb", width=2)
        if face_down:
            canvas.create_rectangle(x + 5, y + 5, x + CARD_W - 5, y + CARD_H - 5,
                                     fill="#1a5276", outline="")
            canvas.create_text(x + CARD_W // 2, y + CARD_H // 2,
                                text="?", font=("Arial", 22, "bold"), fill="white")
        else:
            color = "#c0392b" if suit in RED_SUITS else "#17202a"
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
            btn.config(relief="sunken" if amt == amount else "raised",
                       bd=3 if amt == amount else 2)

    def _add_chip(self, amount):
        if self.state != "betting":
            return
        if self.bet + amount > self.bankroll:
            messagebox.showerror("Insufficient Funds", "Not enough bankroll.")
            return
        self._set_chip(amount)
        self.bet += amount
        self.bet_label.config(text=f"${self.bet:,}")

    def _clear_bet(self):
        if self.state != "betting":
            return
        self.bet = 0
        self.bet_label.config(text="$0")

    # ── Game actions ──────────────────────────────────────────────────────────

    def _deal(self):
        if self.bet == 0:
            messagebox.showwarning("No Bet", "Place a bet before dealing.")
            return

        self.player_hand = []
        self.dealer_hand = []
        self.state = "playing"
        self.result_label.config(text="")
        self._set_buttons("dealer")   # locked during animation
        self._refresh(hide_hole=True)

        # Deal in casino order: player, dealer, player, dealer — one card every 280ms
        sequence = [
            (self.player_hand, self._deal_card()),
            (self.dealer_hand, self._deal_card()),
            (self.player_hand, self._deal_card()),
            (self.dealer_hand, self._deal_card()),
        ]

        def deal_step(i):
            if i >= len(sequence):
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

    def _end_round(self, outcome):
        self.state = "result"
        self._set_buttons("result")
        self._refresh(hide_hole=False)

        if outcome == "blackjack":
            gain = int(self.bet * 1.5)
            self.bankroll += gain
            self.result_label.config(text=f"BLACKJACK!  +${gain:,}", fg="#f1c40f")
        elif outcome == "win":
            self.bankroll += self.bet
            self.result_label.config(text=f"YOU WIN!  +${self.bet:,}", fg="#2ecc71")
        elif outcome == "dealer_bust":
            self.bankroll += self.bet
            self.result_label.config(text=f"DEALER BUSTS — YOU WIN!  +${self.bet:,}", fg="#2ecc71")
        elif outcome in ("lose", "bust"):
            self.bankroll -= self.bet
            msg = "BUST!" if outcome == "bust" else "DEALER WINS"
            self.result_label.config(text=f"{msg}  -${self.bet:,}", fg="#e74c3c")
        elif outcome == "push":
            self.result_label.config(text="PUSH — Bet returned", fg="white")

        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")
        self.bet = 0
        self.bet_label.config(text="$0")

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
            self.on_close(self.bankroll)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    BlackjackApp(root)
    root.mainloop()
