import tkinter as tk
from tkinter import messagebox
import random
import math

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
    def __init__(self, root):
        self.root = root
        self.root.title("Casino Roulette")
        self.root.geometry("1400x860")
        self.root.minsize(1300, 760)
        self.root.configure(bg="#0b3d2e")

        self.bankroll = 1000
        self.chip_amount = 25
        self.active_bets = {}      # bet_key → total amount placed
        self.last_result = None
        self.history = []
        self.spinning = False
        self.ball_angle = 0
        self.board_buttons = {}    # bet_key → (widget, base_label, base_bg)

        self.build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#111111", height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="♠  CASINO ROULETTE  ♠", font=("Georgia", 24, "bold"),
                 fg="gold", bg="#111111").pack(side="left", padx=25, pady=15)

        self.bankroll_label = tk.Label(header, text=f"Bankroll: ${self.bankroll:,}",
                                       font=("Arial", 19, "bold"), fg="white", bg="#111111")
        self.bankroll_label.pack(side="right", padx=20)

        self.total_bet_label = tk.Label(header, text="Total Bet: $0",
                                        font=("Arial", 13), fg="#aab7b8", bg="#111111")
        self.total_bet_label.pack(side="right", padx=20)

        # Main area
        main = tk.Frame(self.root, bg="#0b3d2e")
        main.pack(fill="both", expand=True, padx=12, pady=8)

        self._build_left_panel(main)
        self._build_board(main)

    def _build_left_panel(self, parent):
        left = tk.Frame(parent, bg="#145a32", bd=3, relief="ridge", width=305)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        tk.Label(left, text="Roulette Wheel", font=("Arial", 13, "bold"),
                 fg="white", bg="#145a32").pack(pady=(10, 2))

        self.result_label = tk.Label(left, text="Place bets and SPIN!",
                                     font=("Arial", 12, "bold"), fg="white", bg="#145a32")
        self.result_label.pack()

        self.result_detail = tk.Label(left, text="", font=("Arial", 11),
                                      fg="#f0e68c", bg="#145a32")
        self.result_detail.pack(pady=2)

        self.canvas = tk.Canvas(left, width=280, height=280, bg="#145a32",
                                highlightthickness=0)
        self.canvas.pack(pady=5, padx=10)
        self.draw_wheel()

        # History
        tk.Label(left, text="Recent Results", font=("Arial", 10, "bold"),
                 fg="white", bg="#145a32").pack(pady=(4, 2))

        hist_frame = tk.Frame(left, bg="#145a32")
        hist_frame.pack(padx=10, pady=(0, 6))

        self.history_labels = []
        for i in range(15):
            lbl = tk.Label(hist_frame, text="", width=3, height=1,
                           font=("Arial", 8, "bold"), fg="white", bg="#145a32",
                           relief="flat", bd=1)
            lbl.grid(row=i // 5, column=i % 5, padx=2, pady=1)
            self.history_labels.append(lbl)

        tk.Frame(left, bg="#2e4053", height=1).pack(fill="x", padx=10, pady=6)

        # Chip selector
        tk.Label(left, text="Select Chip", font=("Arial", 10, "bold"),
                 fg="#aab7b8", bg="#145a32").pack(anchor="w", padx=12)

        chip_frame = tk.Frame(left, bg="#145a32")
        chip_frame.pack(padx=8, pady=3, fill="x")

        chips = [(1, "#95a5a6"), (5, "#e74c3c"), (10, "#3498db"),
                 (25, "#27ae60"), (50, "#e67e22"), (100, "#8e44ad"), (500, "#f1c40f")]

        self.chip_btns = {}
        for i, (amt, color) in enumerate(chips):
            btn = tk.Button(chip_frame, text=f"${amt}", font=("Arial", 9, "bold"),
                            bg=color, fg="black", width=5, height=2,
                            relief="raised", bd=2,
                            command=lambda a=amt: self.set_chip(a))
            btn.grid(row=i // 4, column=i % 4, padx=2, pady=2)
            self.chip_btns[amt] = btn

        self.chip_label = tk.Label(left, text="Chip: $25",
                                   font=("Arial", 10, "bold"), fg="#f0e68c", bg="#145a32")
        self.chip_label.pack(pady=2)
        self.set_chip(25)

        tk.Frame(left, bg="#2e4053", height=1).pack(fill="x", padx=10, pady=6)

        self.spin_btn = tk.Button(left, text="SPIN", font=("Arial", 17, "bold"),
                                  bg="gold", fg="black", width=12, height=2,
                                  cursor="hand2", bd=4, command=self.spin)
        self.spin_btn.pack(pady=5)

        tk.Button(left, text="Clear Bets", font=("Arial", 10),
                  bg="#c0392b", fg="white", width=14,
                  command=self.clear_bets).pack(pady=2)

        tk.Button(left, text="Reset Bankroll ($1,000)", font=("Arial", 9),
                  bg="#566573", fg="white", width=18,
                  command=self.reset_bankroll).pack(pady=2)

    def _build_board(self, parent):
        right = tk.Frame(parent, bg="#0b3d2e")
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Betting Board  —  select a chip, then click to bet",
                 font=("Arial", 12, "bold"), fg="white", bg="#0b3d2e").pack(anchor="w", pady=(0, 5))

        board = tk.Frame(right, bg="#0b3d2e")
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
        tk.Frame(board, bg="#0b3d2e").grid(row=3, column=0, sticky="nsew")
        for i, (key, lbl) in enumerate(zip(
                ["dozen1", "dozen2", "dozen3"],
                ["1st 12  (1–12)", "2nd 12  (13–24)", "3rd 12  (25–36)"])):
            self._board_btn(board, key, lbl, "#2e4053",
                            row=3, col=1 + i * 4, colspan=4)

        # Outside bets (row 4, cols 1-12 split into sixths)
        tk.Frame(board, bg="#0b3d2e").grid(row=4, column=0, sticky="nsew")
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

    def _board_btn(self, parent, bet_key, label, bg,
                   row, col, rowspan=1, colspan=1):
        btn = tk.Button(parent, text=label, font=("Arial", 11, "bold"),
                        bg=bg, fg="black", cursor="hand2", relief="raised", bd=2,
                        command=lambda k=bet_key: self.place_chip(k))
        btn.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
                 padx=2, pady=2, sticky="nsew")
        self.board_buttons[bet_key] = (btn, label, bg)

    # ── Chip & bet logic ─────────────────────────────────────────────────────

    def set_chip(self, amount):
        self.chip_amount = amount
        self.chip_label.config(text=f"Chip: ${amount:,}")
        for amt, btn in self.chip_btns.items():
            btn.config(relief="sunken" if amt == amount else "raised",
                       bd=3 if amt == amount else 2)

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

    def _refresh_btn(self, bet_key):
        btn, base_label, base_bg = self.board_buttons[bet_key]
        amount = self.active_bets.get(bet_key, 0)
        if amount > 0:
            btn.config(text=f"{base_label}\n${amount:,}",
                       bg="gold", fg="black", relief="sunken", bd=3)
        else:
            btn.config(text=base_label, bg=base_bg, fg="black",
                       relief="raised", bd=2)

    def _update_total(self):
        total = sum(self.active_bets.values())
        self.total_bet_label.config(text=f"Total Bet: ${total:,}")

    def clear_bets(self):
        self.active_bets.clear()
        for key in self.board_buttons:
            btn, label, bg = self.board_buttons[key]
            btn.config(text=label, bg=bg, fg="black", relief="raised", bd=2)
        self._update_total()

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

    def animate_spin(self, final, step, total):
        progress = step / total
        speed = max(2, int(40 * (1 - progress)))
        self.ball_angle = (self.ball_angle + speed) % 360

        n = len(WHEEL_ORDER)
        self.last_result = WHEEL_ORDER[int(((self.ball_angle + 90) % 360) * n / 360) % n]
        self.draw_wheel(ball_pos=self.ball_angle)

        if step < total:
            self.root.after(max(16, int(60 * progress)),
                            lambda: self.animate_spin(final, step + 1, total))
        else:
            idx = WHEEL_ORDER.index(final)
            self.ball_angle = (idx * 360 / n - 90 + 180 / n) % 360
            self.last_result = final
            self.draw_wheel(ball_pos=self.ball_angle)
            self.root.after(300, lambda: self.finish_spin(final))

    def finish_spin(self, result):
        self.resolve_bets(result)
        self.update_history(result)
        self.highlight_winner(result)
        self.spinning = False
        self.spin_btn.config(state="normal", bg="gold", text="SPIN")

    # ── Game logic ───────────────────────────────────────────────────────────

    def spin(self):
        if self.spinning:
            return
        if not self.active_bets:
            messagebox.showwarning("No Bets", "Click the board to place at least one bet.")
            return
        self.spinning = True
        self.spin_btn.config(state="disabled", bg="#aaa", text="Spinning...")
        self.result_label.config(text="Spinning...", fg="white")
        self.result_detail.config(text="")
        self.animate_spin(random.randint(0, 36), step=0, total=60)

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
            self.result_label.config(text=f"{result}  ({color})  —  YOU WON!", fg="#2ecc71")
            self.result_detail.config(text=f"Net: +${net:,}", fg="#2ecc71")
        elif net < 0:
            self.result_label.config(text=f"{result}  ({color})  —  You lost", fg="#e74c3c")
            self.result_detail.config(text=f"Net: -${abs(net):,}", fg="#e74c3c")
        else:
            self.result_label.config(text=f"{result}  ({color})  —  Push", fg="white")
            self.result_detail.config(text="Net: $0", fg="white")

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
                lbl.config(text=str(n), bg=bg, relief="groove")
            else:
                lbl.config(text="", bg="#145a32", relief="flat")

    def highlight_winner(self, number):
        key = f"n_{number}"
        for k, (btn, label, orig_bg) in self.board_buttons.items():
            if k == key:
                btn.config(text=label, bg="gold", fg="black", relief="sunken", bd=4)
            else:
                btn.config(text=label, bg=orig_bg, fg="black", relief="raised", bd=2)

    def reset_bankroll(self):
        self.bankroll = 1000
        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")
        self.result_label.config(text="Place bets and SPIN!", fg="white")
        self.result_detail.config(text="", fg="#f0e68c")
        self.last_result = None
        self.history = []
        self.ball_angle = 0
        self.active_bets.clear()
        self.draw_wheel()
        self._update_total()
        for lbl in self.history_labels:
            lbl.config(text="", bg="#145a32", relief="flat")
        for k, (btn, label, orig_bg) in self.board_buttons.items():
            btn.config(text=label, bg=orig_bg, fg="black", relief="raised", bd=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = RouletteApp(root)
    root.mainloop()
