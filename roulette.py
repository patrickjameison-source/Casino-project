import tkinter as tk
from tkinter import messagebox
import random
import math

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

PAYOUTS = {
    "number": 35,
    "red": 1, "black": 1,
    "even": 1, "odd": 1,
    "low": 1, "high": 1,
    "dozen1": 2, "dozen2": 2, "dozen3": 2,
    "col1": 2, "col2": 2, "col3": 2,
}

# Wheel order (standard European roulette)
WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27,
    13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1,
    20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
]


class RouletteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Casino Roulette")
        self.root.geometry("1350x850")
        self.root.minsize(1200, 780)
        self.root.configure(bg="#0b3d2e")

        self.bankroll = 1000
        self.current_bet_type = tk.StringVar(value="red")
        self.current_number = tk.StringVar(value="0")
        self.bet_amount = 25
        self.last_result = None
        self.history = []
        self.spinning = False
        self.ball_angle = 0

        self.build_ui()

    def build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg="#111111", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="♠  CASINO ROULETTE  ♠", font=("Georgia", 26, "bold"),
                 fg="gold", bg="#111111").pack(side="left", padx=25, pady=15)

        self.bankroll_label = tk.Label(header, text=f"Bankroll: ${self.bankroll:,}",
                                       font=("Arial", 20, "bold"), fg="white", bg="#111111")
        self.bankroll_label.pack(side="right", padx=25)

        # ── Main area ────────────────────────────────────────────────────────
        main = tk.Frame(self.root, bg="#0b3d2e")
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # Left panel: wheel + history
        left = tk.Frame(main, bg="#145a32", bd=3, relief="ridge")
        left.pack(side="left", fill="y", padx=(0, 12))

        tk.Label(left, text="Roulette Wheel", font=("Arial", 16, "bold"),
                 fg="white", bg="#145a32").pack(pady=(15, 4))

        self.result_label = tk.Label(left, text="Place your bet and SPIN!",
                                     font=("Arial", 15, "bold"), fg="white", bg="#145a32")
        self.result_label.pack()

        self.result_detail = tk.Label(left, text="", font=("Arial", 13),
                                      fg="#f0e68c", bg="#145a32")
        self.result_detail.pack(pady=3)

        self.canvas = tk.Canvas(left, width=310, height=310, bg="#145a32",
                                highlightthickness=0)
        self.canvas.pack(pady=8, padx=15)
        self.draw_wheel()

        # Recent results
        tk.Label(left, text="Recent Results", font=("Arial", 12, "bold"),
                 fg="white", bg="#145a32").pack(pady=(8, 3))

        hist_frame = tk.Frame(left, bg="#145a32")
        hist_frame.pack(padx=12, pady=(0, 15))

        self.history_labels = []
        for i in range(20):
            lbl = tk.Label(hist_frame, text="", width=3, height=1,
                           font=("Arial", 9, "bold"), fg="white", bg="#145a32",
                           relief="flat", bd=1)
            lbl.grid(row=i // 5, column=i % 5, padx=2, pady=2)
            self.history_labels.append(lbl)

        # Middle panel: bet controls
        mid = tk.Frame(main, bg="#1c2833", width=300, bd=3, relief="ridge")
        mid.pack(side="left", fill="y", padx=(0, 12))
        mid.pack_propagate(False)

        tk.Label(mid, text="Place Your Bet", font=("Arial", 17, "bold"),
                 fg="gold", bg="#1c2833").pack(pady=(18, 8))

        # Chip buttons
        tk.Label(mid, text="Select Chip", font=("Arial", 11, "bold"),
                 fg="#aab7b8", bg="#1c2833").pack(anchor="w", padx=15)

        chip_frame = tk.Frame(mid, bg="#1c2833")
        chip_frame.pack(padx=12, pady=5, fill="x")

        chips = [(5, "#e74c3c"), (10, "#3498db"), (25, "#27ae60"),
                 (50, "#e67e22"), (100, "#8e44ad"), (500, "#f1c40f")]

        self.chip_btns = {}
        for i, (amt, color) in enumerate(chips):
            btn = tk.Button(chip_frame, text=f"${amt}", font=("Arial", 10, "bold"),
                            bg=color, fg="white", width=6, height=2,
                            relief="raised", bd=3,
                            command=lambda a=amt: self.set_chip(a))
            btn.grid(row=i // 3, column=i % 3, padx=3, pady=3)
            self.chip_btns[amt] = btn

        self.chip_label = tk.Label(mid, text="Selected Chip: $25",
                                   font=("Arial", 11, "bold"), fg="#f0e68c", bg="#1c2833")
        self.chip_label.pack(pady=3)
        self.set_chip(25)

        # Bet types
        sep = tk.Frame(mid, bg="#2e4053", height=1)
        sep.pack(fill="x", padx=15, pady=8)

        tk.Label(mid, text="Bet Type", font=("Arial", 11, "bold"),
                 fg="#aab7b8", bg="#1c2833").pack(anchor="w", padx=15)

        bets = [
            ("Single Number  (35:1)", "number"),
            ("Red  (1:1)", "red"),
            ("Black  (1:1)", "black"),
            ("Even  (1:1)", "even"),
            ("Odd  (1:1)", "odd"),
            ("Low 1-18  (1:1)", "low"),
            ("High 19-36  (1:1)", "high"),
            ("1st Dozen 1-12  (2:1)", "dozen1"),
            ("2nd Dozen 13-24  (2:1)", "dozen2"),
            ("3rd Dozen 25-36  (2:1)", "dozen3"),
            ("Column 1  (2:1)", "col1"),
            ("Column 2  (2:1)", "col2"),
            ("Column 3  (2:1)", "col3"),
        ]

        rb_frame = tk.Frame(mid, bg="#1c2833")
        rb_frame.pack(fill="x", padx=5)

        for text, value in bets:
            tk.Radiobutton(rb_frame, text=text, variable=self.current_bet_type,
                           value=value, font=("Arial", 10), fg="white", bg="#1c2833",
                           selectcolor="#2c3e50", activebackground="#1c2833",
                           activeforeground="white",
                           command=self.on_bet_type_change
                           ).pack(anchor="w", padx=20, pady=1)

        # Number picker (only visible for single number bet)
        self.num_frame = tk.Frame(mid, bg="#1c2833")
        self.num_frame.pack(fill="x", padx=15, pady=(4, 0))

        tk.Label(self.num_frame, text="Choose Number:", font=("Arial", 10),
                 fg="white", bg="#1c2833").pack(side="left")

        number_menu = tk.OptionMenu(self.num_frame, self.current_number,
                                    *[str(i) for i in range(37)])
        number_menu.config(font=("Arial", 10), width=4, bg="#2c3e50", fg="white",
                           highlightthickness=0)
        number_menu.pack(side="left", padx=8)
        self.num_frame.pack_forget()  # hidden by default

        # Spin + Reset
        sep2 = tk.Frame(mid, bg="#2e4053", height=1)
        sep2.pack(fill="x", padx=15, pady=8)

        self.spin_btn = tk.Button(mid, text="SPIN", font=("Arial", 20, "bold"),
                                  bg="gold", fg="black", width=12, height=2,
                                  cursor="hand2", relief="raised", bd=4,
                                  command=self.spin)
        self.spin_btn.pack(pady=8)

        tk.Button(mid, text="Reset Bankroll ($1,000)", font=("Arial", 10),
                  bg="#566573", fg="white", width=20,
                  command=self.reset_bankroll).pack(pady=3)

        # Right panel: betting board
        right = tk.Frame(main, bg="#0b3d2e")
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Betting Board  —  click any section to bet",
                 font=("Arial", 14, "bold"), fg="white", bg="#0b3d2e").pack(anchor="w", pady=(0, 8))

        board_outer = tk.Frame(right, bg="#0b3d2e")
        board_outer.pack(anchor="w")

        grid_frame = tk.Frame(board_outer, bg="#0b3d2e")
        grid_frame.pack()

        self.number_buttons = {}

        # 0 spans all 3 rows on the left
        zero_btn = tk.Button(grid_frame, text="0", width=5, height=5,
                             font=("Arial", 14, "bold"), bg="#1e8449", fg="white",
                             cursor="hand2",
                             command=lambda: self.quick_number_bet(0))
        zero_btn.grid(row=0, column=0, rowspan=3, padx=3, pady=2, sticky="nsew")
        self.number_buttons[0] = zero_btn

        # Numbers 1-36: row = (i-1)%3, col = (i-1)//3 + 1
        for i in range(1, 37):
            r = (i - 1) % 3
            c = (i - 1) // 3 + 1
            bg = "#c0392b" if i in RED_NUMBERS else "#1a252f"
            btn = tk.Button(grid_frame, text=str(i), width=5, height=3,
                            font=("Arial", 11, "bold"), bg=bg, fg="white",
                            cursor="hand2", relief="raised", bd=2,
                            command=lambda n=i: self.quick_number_bet(n))
            btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
            self.number_buttons[i] = btn

        # 2:1 column buttons (right of grid)
        col_labels = ["Col 1\n2:1", "Col 2\n2:1", "Col 3\n2:1"]
        for r, (label, bet) in enumerate(zip(col_labels, ["col1", "col2", "col3"])):
            btn = tk.Button(grid_frame, text=label, width=6, height=3,
                            font=("Arial", 9, "bold"), bg="#2e4053", fg="white",
                            cursor="hand2",
                            command=lambda b=bet: self.set_bet(b))
            btn.grid(row=r, column=13, padx=3, pady=2, sticky="nsew")

        # Dozen buttons below grid
        dozen_frame = tk.Frame(board_outer, bg="#0b3d2e")
        dozen_frame.pack(anchor="w", pady=(2, 0))

        tk.Frame(dozen_frame, width=44, bg="#0b3d2e").pack(side="left")  # spacer for 0 col

        dozens = [("1st 12  (1-12)", "dozen1"), ("2nd 12  (13-24)", "dozen2"),
                  ("3rd 12  (25-36)", "dozen3")]
        for text, bet in dozens:
            btn = tk.Button(dozen_frame, text=text, font=("Arial", 10, "bold"),
                            bg="#2e4053", fg="white", height=2, width=18,
                            cursor="hand2",
                            command=lambda b=bet: self.set_bet(b))
            btn.pack(side="left", padx=2, pady=2)

        # Outside bets row
        outside_frame = tk.Frame(board_outer, bg="#0b3d2e")
        outside_frame.pack(anchor="w", pady=(2, 0))

        tk.Frame(outside_frame, width=44, bg="#0b3d2e").pack(side="left")

        outside = [
            ("1-18", "low", "#2e4053"),
            ("EVEN", "even", "#2e4053"),
            ("RED", "red", "#c0392b"),
            ("BLACK", "black", "#1a252f"),
            ("ODD", "odd", "#2e4053"),
            ("19-36", "high", "#2e4053"),
        ]
        for text, bet, bg in outside:
            btn = tk.Button(outside_frame, text=text, font=("Arial", 11, "bold"),
                            bg=bg, fg="white", height=2, width=9,
                            cursor="hand2",
                            command=lambda b=bet: self.set_bet(b))
            btn.pack(side="left", padx=2, pady=2)

    # ── Chip & bet helpers ───────────────────────────────────────────────────

    def set_chip(self, amount):
        self.bet_amount = amount
        self.chip_label.config(text=f"Selected Chip: ${amount:,}")
        for amt, btn in self.chip_btns.items():
            btn.config(relief="sunken" if amt == amount else "raised",
                       bd=3 if amt == amount else 2)

    def set_bet(self, bet_type):
        self.current_bet_type.set(bet_type)
        self.on_bet_type_change()

    def on_bet_type_change(self):
        if self.current_bet_type.get() == "number":
            self.num_frame.pack(fill="x", padx=15, pady=(4, 0))
        else:
            self.num_frame.pack_forget()

    def quick_number_bet(self, number):
        self.current_bet_type.set("number")
        self.current_number.set(str(number))
        self.on_bet_type_change()

    # ── Wheel drawing ────────────────────────────────────────────────────────

    def draw_wheel(self, ball_pos=None):
        self.canvas.delete("all")
        cx, cy = 155, 155
        r_rim = 148
        r_outer = 138
        r_inner = 72
        r_center = 50

        # Outer rim
        self.canvas.create_oval(cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim,
                                fill="#7d6608", outline="#b8860b", width=5)

        # Pockets
        n = len(WHEEL_ORDER)
        for i, num in enumerate(WHEEL_ORDER):
            start_angle = 360 * i / n - 90
            extent = 360 / n
            bg = "#1e8449" if num == 0 else "#c0392b" if num in RED_NUMBERS else "#1a252f"
            self.canvas.create_arc(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
                                   start=start_angle, extent=extent,
                                   fill=bg, outline="#d4ac0d", width=1)

            # Pocket number text
            mid_angle = math.radians(start_angle + extent / 2)
            r_text = (r_outer + r_inner) / 2
            tx = cx + r_text * math.cos(mid_angle)
            ty = cy - r_text * math.sin(mid_angle)
            self.canvas.create_text(tx, ty, text=str(num), fill="white",
                                    font=("Arial", 7, "bold"))

        # Inner disc
        self.canvas.create_oval(cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
                                fill="#0b3d2e", outline="#d4ac0d", width=3)

        # Center
        self.canvas.create_oval(cx - r_center, cy - r_center, cx + r_center, cy + r_center,
                                fill="#117864", outline="gold", width=2)

        if self.last_result is not None:
            n_val = self.last_result
            color = "#2ecc71" if n_val == 0 else "#e74c3c" if n_val in RED_NUMBERS else "#ecf0f1"
            self.canvas.create_oval(cx - 28, cy - 28, cx + 28, cy + 28,
                                    fill=color, outline="white", width=2)
            self.canvas.create_text(cx, cy, text=str(n_val), fill="white",
                                    font=("Arial", 20, "bold"))
        else:
            self.canvas.create_text(cx, cy, text="?", fill="white",
                                    font=("Arial", 28, "bold"))

        # Ball
        if ball_pos is not None:
            r_ball = r_outer - 8
            bx = cx + r_ball * math.cos(math.radians(ball_pos))
            by = cy - r_ball * math.sin(math.radians(ball_pos))
            self.canvas.create_oval(bx - 7, by - 7, bx + 7, by + 7,
                                    fill="white", outline="#aaa", width=1)

    # ── Spin animation ───────────────────────────────────────────────────────

    def animate_spin(self, final_number, step, total_steps):
        progress = step / total_steps
        # Slow down as we approach the end
        speed = max(3, int(50 * progress))
        self.ball_angle = (self.ball_angle + speed) % 360

        # Show fake results during spin
        fake = WHEEL_ORDER[int(self.ball_angle / (360 / len(WHEEL_ORDER)))]
        self.last_result = fake
        self.draw_wheel(ball_pos=self.ball_angle)

        if step < total_steps:
            delay = max(16, int(80 * progress))
            self.root.after(delay, lambda: self.animate_spin(final_number, step + 1, total_steps))
        else:
            # Land ball on actual result pocket
            idx = WHEEL_ORDER.index(final_number)
            final_angle = (idx * 360 / len(WHEEL_ORDER) + 90) % 360
            self.ball_angle = final_angle
            self.last_result = final_number
            self.draw_wheel(ball_pos=self.ball_angle)
            self.root.after(300, lambda: self.finish_spin(final_number))

    def finish_spin(self, result):
        self.resolve_bet(result)
        self.update_history(result)
        self.highlight_result(result)
        self.spinning = False
        self.spin_btn.config(state="normal", bg="gold", text="SPIN")

    # ── Game logic ───────────────────────────────────────────────────────────

    def spin(self):
        if self.spinning:
            return

        if self.bet_amount > self.bankroll:
            messagebox.showerror("Invalid Bet", "Bet exceeds your bankroll.")
            return

        self.spinning = True
        self.spin_btn.config(state="disabled", bg="#aaa", text="Spinning...")
        self.result_label.config(text="Spinning...", fg="white")
        self.result_detail.config(text="")

        final = random.randint(0, 36)
        self.animate_spin(final, step=0, total_steps=60)

    def resolve_bet(self, result):
        bet_type = self.current_bet_type.get()
        bet_amount = self.bet_amount
        color_name = "Green" if result == 0 else "Red" if result in RED_NUMBERS else "Black"

        won = False
        if bet_type == "number":
            won = result == int(self.current_number.get())
        elif bet_type == "red":
            won = result in RED_NUMBERS
        elif bet_type == "black":
            won = result in BLACK_NUMBERS
        elif bet_type == "even":
            won = result != 0 and result % 2 == 0
        elif bet_type == "odd":
            won = result % 2 == 1
        elif bet_type == "low":
            won = 1 <= result <= 18
        elif bet_type == "high":
            won = 19 <= result <= 36
        elif bet_type == "dozen1":
            won = 1 <= result <= 12
        elif bet_type == "dozen2":
            won = 13 <= result <= 24
        elif bet_type == "dozen3":
            won = 25 <= result <= 36
        elif bet_type == "col1":
            won = result != 0 and result % 3 == 1
        elif bet_type == "col2":
            won = result != 0 and result % 3 == 2
        elif bet_type == "col3":
            won = result != 0 and result % 3 == 0

        payout_mult = PAYOUTS.get(bet_type, 1)

        if won:
            winnings = bet_amount * payout_mult
            self.bankroll += winnings
            self.result_label.config(
                text=f"{result}  ({color_name})  —  YOU WON!", fg="#2ecc71")
            self.result_detail.config(text=f"+${winnings:,}", fg="#2ecc71")
        else:
            self.bankroll -= bet_amount
            self.result_label.config(
                text=f"{result}  ({color_name})  —  You lost", fg="#e74c3c")
            self.result_detail.config(text=f"-${bet_amount:,}", fg="#e74c3c")

        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")

        if self.bankroll <= 0:
            messagebox.showinfo("Broke!", "You ran out of money. Resetting to $1,000.")
            self.reset_bankroll()

    def update_history(self, number):
        self.history.insert(0, number)
        self.history = self.history[:20]
        for i, lbl in enumerate(self.history_labels):
            if i < len(self.history):
                n = self.history[i]
                bg = "#2ecc71" if n == 0 else "#e74c3c" if n in RED_NUMBERS else "#2c3e50"
                lbl.config(text=str(n), bg=bg, relief="groove")
            else:
                lbl.config(text="", bg="#145a32", relief="flat")

    def highlight_result(self, number):
        for n, btn in self.number_buttons.items():
            orig = "#1e8449" if n == 0 else "#c0392b" if n in RED_NUMBERS else "#1a252f"
            if n == number:
                btn.config(bg="gold", fg="black", relief="sunken", bd=4)
            else:
                btn.config(bg=orig, fg="white", relief="raised", bd=2)

    def reset_bankroll(self):
        self.bankroll = 1000
        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")
        self.result_label.config(text="Place your bet and SPIN!", fg="white")
        self.result_detail.config(text="", fg="#f0e68c")
        self.last_result = None
        self.history = []
        self.ball_angle = 0
        self.draw_wheel()
        self.update_history(-1)
        for n, btn in self.number_buttons.items():
            orig = "#1e8449" if n == 0 else "#c0392b" if n in RED_NUMBERS else "#1a252f"
            btn.config(bg=orig, fg="white", relief="raised", bd=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = RouletteApp(root)
    root.mainloop()
