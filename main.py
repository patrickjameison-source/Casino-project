import tkinter as tk
from roulette import RouletteApp
from blackjack import BlackjackApp
from poker import PokerApp


class Casino:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Casino")
        self.root.geometry("860x440")
        self.root.resizable(False, False)
        self.root.configure(bg="#111111")

        self.bankroll = 1000
        self._build_lobby()
        self.root.mainloop()

    def _build_lobby(self):
        tk.Label(self.root, text="♠  C A S I N O  ♠",
                 font=("Georgia", 42, "bold"), fg="gold", bg="#111111").pack(pady=(60, 4))

        tk.Frame(self.root, bg="#b8860b", height=2).pack(fill="x", padx=80, pady=(0, 20))

        self.bankroll_label = tk.Label(self.root,
                                       text=f"Bankroll: ${self.bankroll:,}",
                                       font=("Arial", 18), fg="white", bg="#111111")
        self.bankroll_label.pack(pady=(0, 36))

        btn_row = tk.Frame(self.root, bg="#111111")
        btn_row.pack()

        tk.Button(btn_row, text="ROULETTE", font=("Arial", 16, "bold"),
                  bg="#c0392b", fg="white", width=14, height=3,
                  cursor="hand2", relief="raised", bd=3,
                  command=self._play_roulette).pack(side="left", padx=20)

        tk.Button(btn_row, text="BLACKJACK", font=("Arial", 16, "bold"),
                  bg="#1a5276", fg="white", width=14, height=3,
                  cursor="hand2", relief="raised", bd=3,
                  command=self._play_blackjack).pack(side="left", padx=20)

        tk.Button(btn_row, text="POKER", font=("Arial", 16, "bold"),
                  bg="#1e8449", fg="white", width=14, height=3,
                  cursor="hand2", relief="raised", bd=3,
                  command=self._play_poker).pack(side="left", padx=20)

    def _play_roulette(self):
        win = tk.Toplevel(self.root)
        win.grab_set()
        RouletteApp(win, bankroll=self.bankroll, on_close=self._game_closed)

    def _play_blackjack(self):
        win = tk.Toplevel(self.root)
        win.grab_set()
        BlackjackApp(win, bankroll=self.bankroll, on_close=self._game_closed)

    def _play_poker(self):
        win = tk.Toplevel(self.root)
        win.grab_set()
        PokerApp(win, bankroll=self.bankroll, on_close=self._game_closed)

    def _game_closed(self, new_bankroll):
        self.bankroll = new_bankroll
        self.bankroll_label.config(text=f"Bankroll: ${self.bankroll:,}")


if __name__ == "__main__":
    Casino()
