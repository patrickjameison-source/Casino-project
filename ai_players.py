"""
ai_players.py — Roulette-specific AI player strategies.

Each class inherits game-agnostic state from Player (player.py) and adds
Roulette-specific betting logic in choose_bet() / resolve().

To add AI players to another game (Blackjack, Poker, etc.):
  1. Create a new file, e.g. blackjack_ai.py
  2. Subclass Player (or RouletteAI as a pattern reference)
  3. Implement choose_bet() with that game's bet types
  4. Call self.apply_result(net, bet, bet_key) after each hand
"""

import random
from player import Player

# ── Roulette bet pools ────────────────────────────────────────────────────────
_OUTSIDE = ["red", "black", "even", "odd", "low", "high"]
_DOZENS  = ["dozen1", "dozen2", "dozen3"]
_COLUMNS = ["col1", "col2", "col3"]
_NUMBERS = [f"n_{i}" for i in range(37)]


class RouletteAI(Player):
    """
    Base for all Roulette AI players.

    Adds:
      - current_bet / current_bet_key  — pending bet for this spin
      - _place()                       — validates and stores the bet
      - choose_bet()                   — subclasses implement strategy
      - resolve()                      — settles bet, calls apply_result()
    """

    def __init__(self, name: str, personality: str, starting_bankroll: int = 1000):
        super().__init__(name, personality, starting_bankroll)
        self.current_bet     = 0
        self.current_bet_key = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _place(self, bet_key: str, amount: int) -> None:
        """Store the chosen bet, capped to available bankroll (min $1)."""
        self.current_bet_key = bet_key
        self.current_bet     = min(max(1, amount), self.bankroll)

    # ── Called by RouletteApp ─────────────────────────────────────────────────

    def choose_bet(self) -> None:
        """Subclasses override this to pick bet_key + amount via _place()."""
        raise NotImplementedError

    def resolve(self, result: int, check_win, get_payout) -> None:
        """Settle this round and update bankroll via apply_result()."""
        if not self.active or self.current_bet_key is None:
            return

        won = check_win(self.current_bet_key, result)
        if won:
            round_net = self.current_bet * get_payout(self.current_bet_key)
        else:
            round_net = -self.current_bet

        self.apply_result(round_net, self.current_bet, self.current_bet_key)

        print(
            f"[AI] {self.name:<14}  bet ${self.current_bet:>4} on {self.current_bet_key:<10}"
            f"  result={result:>2}  {'WIN' if won else 'loss':<4}"
            f"  bankroll=${self.bankroll:>6,}  P/L={self.profit_loss:>+7,}"
        )

        self.current_bet     = 0
        self.current_bet_key = None


# ── Personalities ─────────────────────────────────────────────────────────────

class AggressivePlayer(RouletteAI):
    """
    Bets 10–30% of bankroll each round.
    40% chance of a straight single-number bet (35:1).
    30% dozens/columns (2:1). 30% outside (even-money but large stake).
    High variance — bankroll swings wildly.
    """

    def __init__(self):
        super().__init__("Aggressive", "aggressive")

    def choose_bet(self) -> None:
        if not self.active:
            return
        amount = int(self.bankroll * random.uniform(0.10, 0.30))
        roll = random.random()
        if roll < 0.40:
            bet_key = random.choice(_NUMBERS)
        elif roll < 0.70:
            bet_key = random.choice(_DOZENS + _COLUMNS)
        else:
            bet_key = random.choice(_OUTSIDE)
        self._place(bet_key, amount)


class ModeratePlayer(RouletteAI):
    """
    Bets 5–10% of bankroll each round.
    75% even-money outside bets, 15% dozens, 10% columns.
    Never plays straight numbers. Steady, predictable pattern.
    """

    def __init__(self):
        super().__init__("Moderate", "moderate")

    def choose_bet(self) -> None:
        if not self.active:
            return
        amount = int(self.bankroll * random.uniform(0.05, 0.10))
        roll = random.random()
        if roll < 0.75:
            bet_key = random.choice(_OUTSIDE)
        elif roll < 0.90:
            bet_key = random.choice(_DOZENS)
        else:
            bet_key = random.choice(_COLUMNS)
        self._place(bet_key, amount)


class ConservativePlayer(RouletteAI):
    """
    Bets 1–5% of bankroll each round.
    80% on red/black/even/odd, 20% on low/high.
    Never plays dozens, columns, or single numbers.
    Bankroll stays nearly flat over many rounds.
    """

    def __init__(self):
        super().__init__("Conservative", "conservative")

    def choose_bet(self) -> None:
        if not self.active:
            return
        amount = int(self.bankroll * random.uniform(0.01, 0.05))
        if random.random() < 0.80:
            bet_key = random.choice(["red", "black", "even", "odd"])
        else:
            bet_key = random.choice(["low", "high"])
        self._place(bet_key, amount)
