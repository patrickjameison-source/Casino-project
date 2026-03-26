import tkinter as tk
from tkinter import messagebox
import random
from collections import Counter
from itertools import combinations

SUITS    = ['♠', '♥', '♦', '♣']
RANKS    = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
RED_SUITS = {'♥', '♦'}
CARD_W, CARD_H = 70, 100
RANK_VAL = {r: i + 2 for i, r in enumerate(RANKS)}   # '2'→2 … 'A'→14


# ── Hand evaluation ───────────────────────────────────────────────────────────

def evaluate(hand):
    """Score a 5-card hand. Returns (score 0-9, name, tiebreak_list)."""
    vals  = sorted([RANK_VAL[r] for r, _ in hand], reverse=True)
    suits = [s for _, s in hand]

    flush    = len(set(suits)) == 1
    straight = False
    s_vals   = vals
    if len(set(vals)) == 5:
        if vals[0] - vals[4] == 4:
            straight = True
        elif set(vals) == {14, 2, 3, 4, 5}:        # wheel (A-2-3-4-5)
            straight, s_vals = True, [5, 4, 3, 2, 1]

    cnt    = Counter(vals)
    groups = sorted(cnt.items(), key=lambda x: (x[1], x[0]), reverse=True)
    gc     = [c for _, c in groups]
    tb     = [v for v, _ in groups]   # high-count then high-rank first

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
    """Best 5-card hand from n cards (n ≥ 5). Returns (score, name, tiebreak)."""
    if len(cards) == 5:
        return evaluate(cards)
    return max(
        (evaluate(list(c)) for c in combinations(cards, 5)),
        key=lambda x: (x[0], x[2])
    )


def compare_hands(cards1, cards2):
    """Compare two card sets (up to 7 cards each). Returns 1 / -1 / 0."""
    s1, _, tb1 = best_hand(cards1)
    s2, _, tb2 = best_hand(cards2)
    if s1 != s2:
        return 1 if s1 > s2 else -1
    for v1, v2 in zip(tb1, tb2):
        if v1 != v2:
            return 1 if v1 > v2 else -1
    return 0


# ── App ───────────────────────────────────────────────────────────────────────

class PokerApp:
    def __init__(self, root, bankroll=1000, on_close=None):
        self.root     = root
        self.bankroll = bankroll
        self.on_close = on_close

        self.root.title("Texas Hold'em")
        self.root.geometry("920x720")
        self.root.minsize(840, 660)
        self.root.configure(bg="#0b3d2e")
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_lobby)

        self.bet         = 0
        self.chip_amount = 25
        self.player_hole = []
        self.dealer_hole = []
        self.community   = []
        self.state       = "betting"   # betting | flop | dealing
        self._new_deck()
        self._build_ui()

    # ── Deck ──────────────────────────────────────────────────────────────────

    def _new_deck(self):
        self.deck = [(r, s) for s in SUITS for r in RANKS]
        random.shuffle(self.deck)

    def _draw(self):
        if len(self.deck) < 9:
            self._new_deck()
        return self.deck.pop()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#111111", height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="♠  TEXAS HOLD'EM  ♠", font=("Georgia", 22, "bold"),
                 fg="gold", bg="#111111").pack(side="left", padx=22, pady=15)
        self.bankroll_label = tk.Label(hdr, text=f"Bankroll: ${self.bankroll:,}",
                                       font=("Arial", 17, "bold"), fg="white", bg="#111111")
        self.bankroll_label.pack(side="right", padx=22)

        # Table
        table = tk.Frame(self.root, bg="#0b3d2e")
        table.pack(fill="both", expand=True, padx=18, pady=6)

        # Dealer hole cards
        d_box = tk.Frame(table, bg="#145a32", bd=2, relief="ridge")
        d_box.pack(fill="x", pady=(0, 3))
        d_top = tk.Frame(d_box, bg="#145a32")
        d_top.pack(fill="x", padx=12, pady=(7, 2))
        tk.Label(d_top, text="DEALER", font=("Arial", 11, "bold"),
                 fg="#aab7b8", bg="#145a32").pack(side="left")
        self.dealer_hand_lbl = tk.Label(d_top, text="", font=("Arial", 14, "bold"),
                                        fg="gold", bg="#145a32")
        self.dealer_hand_lbl.pack(side="right")
        self.dealer_canvas = tk.Canvas(d_box, height=CARD_H + 12,
                                       bg="#145a32", highlightthickness=0)
        self.dealer_canvas.pack(fill="x", padx=12, pady=(2, 8))

        # Community cards (different bg to distinguish)
        c_box = tk.Frame(table, bg="#0d5c35", bd=2, relief="ridge")
        c_box.pack(fill="x", pady=3)
        c_top = tk.Frame(c_box, bg="#0d5c35")
        c_top.pack(fill="x", padx=12, pady=(7, 2))
        tk.Label(c_top, text="COMMUNITY", font=("Arial", 11, "bold"),
                 fg="#aab7b8", bg="#0d5c35").pack(side="left")
        self.community_canvas = tk.Canvas(c_box, height=CARD_H + 12,
                                          bg="#0d5c35", highlightthickness=0)
        self.community_canvas.pack(fill="x", padx=12, pady=(2, 8))

        # Result
        self.result_label = tk.Label(table, text="Place a bet and DEAL",
                                     font=("Arial", 16, "bold"), fg="white",
                                     bg="#0b3d2e", height=2)
        self.result_label.pack(pady=2)

        # Player hole cards
        p_box = tk.Frame(table, bg="#145a32", bd=2, relief="ridge")
        p_box.pack(fill="x", pady=(3, 0))
        p_top = tk.Frame(p_box, bg="#145a32")
        p_top.pack(fill="x", padx=12, pady=(7, 2))
        tk.Label(p_top, text="YOUR HAND", font=("Arial", 11, "bold"),
                 fg="#aab7b8", bg="#145a32").pack(side="left")
        self.player_hand_lbl = tk.Label(p_top, text="", font=("Arial", 14, "bold"),
                                        fg="gold", bg="#145a32")
        self.player_hand_lbl.pack(side="right")
        self.player_canvas = tk.Canvas(p_box, height=CARD_H + 12,
                                       bg="#145a32", highlightthickness=0)
        self.player_canvas.pack(fill="x", padx=12, pady=(2, 8))

        # Controls bar
        bar = tk.Frame(self.root, bg="#1c2833", bd=2, relief="ridge")
        bar.pack(fill="x", padx=18, pady=(0, 12))

        # Chips
        chip_col = tk.Frame(bar, bg="#1c2833")
        chip_col.pack(side="left", padx=14, pady=10)
        tk.Label(chip_col, text="Select Chip", font=("Arial", 9, "bold"),
                 fg="#aab7b8", bg="#1c2833").pack(anchor="w")
        chip_row = tk.Frame(chip_col, bg="#1c2833")
        chip_row.pack()
        self.chip_btns = {}
        for amt, color in [(5,"#e74c3c"),(10,"#3498db"),(25,"#27ae60"),
                           (50,"#e67e22"),(100,"#8e44ad"),(500,"#f1c40f")]:
            btn = tk.Button(chip_row, text=f"${amt}", font=("Arial", 9, "bold"),
                            bg=color, fg="black", width=5, height=1,
                            relief="raised", bd=2,
                            command=lambda a=amt: self._add_chip(a))
            btn.pack(side="left", padx=2)
            self.chip_btns[amt] = btn
        self._set_chip(25)

        # Bet display
        bet_col = tk.Frame(bar, bg="#1c2833")
        bet_col.pack(side="left", padx=16, pady=10)
        tk.Label(bet_col, text="Ante Bet", font=("Arial", 9, "bold"),
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

        self.check_btn = tk.Button(act, text="CHECK", font=("Arial", 13, "bold"),
                                   bg="#27ae60", fg="black", width=8, height=2,
                                   state="disabled", command=self._check)
        self.check_btn.pack(side="left", padx=3)

        self.fold_btn = tk.Button(act, text="FOLD", font=("Arial", 13, "bold"),
                                  bg="#c0392b", fg="white", width=8, height=2,
                                  state="disabled", command=self._fold)
        self.fold_btn.pack(side="left", padx=3)

        tk.Button(act, text="Lobby", font=("Arial", 10), bg="#2c3e50", fg="white",
                  width=7, height=2, command=self.back_to_lobby).pack(side="left", padx=3)

    # ── Button states ─────────────────────────────────────────────────────────

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

    # ── Chip controls ─────────────────────────────────────────────────────────

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

    # ── Card drawing ──────────────────────────────────────────────────────────

    def _draw_cards(self, canvas, hand, face_down=None):
        canvas.delete("all")
        if face_down is None:
            face_down = set()
        x = 8
        for i, (rank, suit) in enumerate(hand):
            self._draw_card(canvas, x, 6, rank, suit, i in face_down)
            x += CARD_W + 8

    def _draw_card(self, canvas, x, y, rank, suit, face_down=False):
        canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                 fill="white", outline="#bbb", width=2)
        if face_down:
            canvas.create_rectangle(x + 4, y + 4, x + CARD_W - 4, y + CARD_H - 4,
                                     fill="#1a5276", outline="")
            canvas.create_text(x + CARD_W // 2, y + CARD_H // 2,
                                text="?", font=("Arial", 20, "bold"), fill="white")
        else:
            col = "#c0392b" if suit in RED_SUITS else "#17202a"
            canvas.create_text(x + 6,           y + 8,  text=rank,
                                font=("Arial", 11, "bold"), fill=col, anchor="nw")
            canvas.create_text(x + 6,           y + 22, text=suit,
                                font=("Arial", 11), fill=col, anchor="nw")
            canvas.create_text(x + CARD_W // 2, y + CARD_H // 2, text=suit,
                                font=("Arial", 26), fill=col)

    # ── Game flow ─────────────────────────────────────────────────────────────

    def _deal(self):
        if self.bet == 0:
            messagebox.showwarning("No Bet", "Place an ante bet before dealing.")
            return

        self.player_hole = []
        self.dealer_hole = []
        self.community   = []
        self.state       = "dealing"

        self.result_label.config(text="", fg="white")
        self.player_hand_lbl.config(text="")
        self.dealer_hand_lbl.config(text="")
        for c in (self.dealer_canvas, self.community_canvas, self.player_canvas):
            c.delete("all")
        self._set_buttons("dealing")

        # Pre-draw all cards for this round
        p1, p2   = self._draw(), self._draw()
        d1, d2   = self._draw(), self._draw()
        f1,f2,f3 = self._draw(), self._draw(), self._draw()

        # Animate: player1, dealer1, player2, dealer2, flop1, flop2, flop3
        sequence = [
            ("player", p1), ("dealer", d1),
            ("player", p2), ("dealer", d2),
            ("flop",   f1), ("flop",   f2), ("flop",   f3),
        ]

        def step(i):
            if i >= len(sequence):
                # All cards dealt — show flop decision
                self.state = "flop"
                self._set_buttons("flop")
                self._show_player_hand()
                self.result_label.config(
                    text="CHECK to see Turn & River  —  or  FOLD")
                return
            who, card = sequence[i]
            if who == "player":
                self.player_hole.append(card)
                self._draw_cards(self.player_canvas, self.player_hole)
            elif who == "dealer":
                self.dealer_hole.append(card)
                self._draw_cards(self.dealer_canvas, self.dealer_hole, face_down={0, 1})
            else:
                self.community.append(card)
                self._draw_cards(self.community_canvas, self.community)
            self.root.after(220, lambda: step(i + 1))

        step(0)

    def _check(self):
        """Deal turn + river, then reveal dealer and resolve."""
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
                self.result_label.config(text="Dealer reveals...", fg="white")
                self.root.after(500, lambda: self._reveal_dealer(0))

        deal_remaining(0)

    def _reveal_dealer(self, i):
        """Flip dealer hole cards face-up one at a time."""
        if i < 2:
            self._draw_cards(self.dealer_canvas, self.dealer_hole,
                             face_down=set(range(i + 1, 2)))
            self.root.after(300, lambda: self._reveal_dealer(i + 1))
        else:
            self.root.after(300, self._resolve)

    def _fold(self):
        self.bankroll -= self.bet
        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")
        self.result_label.config(text=f"You folded  —  -${self.bet:,}", fg="#e74c3c")
        # Show dealer hole cards on fold
        self._draw_cards(self.dealer_canvas, self.dealer_hole)
        self.bet = 0
        self.bet_label.config(text="$0")
        self.state = "betting"
        self._set_buttons("betting")
        self._check_broke()

    def _resolve(self):
        p_cards = self.player_hole + self.community
        d_cards = self.dealer_hole + self.community

        _, p_name, _ = best_hand(p_cards)
        _, d_name, _ = best_hand(d_cards)
        outcome      = compare_hands(p_cards, d_cards)

        self.player_hand_lbl.config(text=p_name)
        self.dealer_hand_lbl.config(text=d_name)

        if outcome > 0:
            self.bankroll += self.bet
            self.result_label.config(text=f"YOU WIN!  +${self.bet:,}", fg="#2ecc71")
        elif outcome < 0:
            self.bankroll -= self.bet
            self.result_label.config(text=f"DEALER WINS  -${self.bet:,}", fg="#e74c3c")
        else:
            self.result_label.config(text="TIE — Bet returned", fg="white")

        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")
        self.bet = 0
        self.bet_label.config(text="$0")
        self.state = "betting"
        self._set_buttons("betting")
        self._check_broke()

    def _show_player_hand(self):
        cards = self.player_hole + self.community
        if len(cards) >= 5:
            _, name, _ = best_hand(cards)
            self.player_hand_lbl.config(text=name)

    def _check_broke(self):
        if self.bankroll <= 0:
            messagebox.showinfo("Broke!", "You ran out of money! Resetting to $1,000.")
            self.bankroll = 1000
            self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")

    # ── Navigation ────────────────────────────────────────────────────────────

    def back_to_lobby(self):
        if self.on_close:
            self.on_close(self.bankroll)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    PokerApp(root)
    root.mainloop()
