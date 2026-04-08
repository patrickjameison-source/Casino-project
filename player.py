"""
player.py — Game-agnostic Player base class.

Tracks identity and bankroll state only. No game-specific logic lives here.
To add a player to a new game, subclass Player and implement game-specific
bet selection and resolution in that subclass.
"""


class Player:
    """
    Shared state for any casino player (human or AI) across all games.

    Fields intentionally kept generic so they work for Roulette,
    Blackjack, Poker, or any future game:
      - name / personality  — identity
      - bankroll            — current balance (shared across games)
      - starting_bankroll   — reference point for P/L calculation
      - active              — False once bankroll hits zero
      - last_net            — net gain/loss from the most recent round
      - last_bet            — amount wagered last round
      - last_bet_key        — game-specific bet descriptor (e.g. "red",
                               "n_14", "hit", None for games without one)
    """

    def __init__(self, name: str, personality: str, starting_bankroll: int = 1000):
        self.name              = name
        self.personality       = personality   # "aggressive" | "moderate" | "conservative"
        self.starting_bankroll = starting_bankroll
        self.bankroll          = starting_bankroll
        self.active            = True

        # Balance history — one entry per round, starting with initial bankroll
        self.bankroll_history  = [starting_bankroll]

        # Last-round data (reset each time apply_result is called)
        self.last_net          = None
        self.last_bet          = 0
        self.last_bet_key      = None   # game-specific; None for games that don't use it

    # ── Derived state ─────────────────────────────────────────────────────────

    @property
    def profit_loss(self) -> int:
        return self.bankroll - self.starting_bankroll

    # ── Called by game logic after each round ─────────────────────────────────

    def apply_result(self, net: int, bet: int = 0, bet_key=None) -> None:
        """
        Apply the outcome of one round.

        Args:
            net     — positive = won, negative = lost, zero = push
            bet     — amount staked (for display / history)
            bet_key — game-specific bet descriptor (optional)
        """
        self.last_net     = net
        self.last_bet     = bet
        self.last_bet_key = bet_key

        self.bankroll += net
        self.bankroll_history.append(self.bankroll)
        if self.bankroll <= 0:
            self.bankroll = 0
            self.active   = False
