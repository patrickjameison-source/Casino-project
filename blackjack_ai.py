"""
blackjack_ai.py — Blackjack-specific AI player adapter.

Wraps an existing Player (player.py) and adds:
  - bet sizing by personality
  - simple fixed strategy (stand on hard 17+, hit below)
  - hand resolution via player.apply_result()

No circular imports: hand logic is inlined here.
"""

import random
from player import Player


# ── Standalone hand helpers (mirrors blackjack.py — no import needed) ─────────

def _hand_value(hand) -> int:
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


def _is_blackjack(hand) -> bool:
    return len(hand) == 2 and _hand_value(hand) == 21


# ── Adapter ────────────────────────────────────────────────────────────────────

class BlackjackAI:
    """
    Wraps a Player for one Blackjack hand.

    Lifecycle per hand:
      1. start_hand()   — reset state
      2. choose_bet()   — returns bet amount based on personality
      3. deal two cards into .hand
      4. while decide() == "hit": deal one more card
      5. resolve(dealer_hand) — settles via player.apply_result()
    """

    def __init__(self, player: Player):
        self.player      = player
        self.hand        = []
        self.bet         = 0
        self._done       = False
        self.last_result = None   # "Win", "Loss", "Bust", "Push", "Blackjack"
        self.last_net    = None   # int — net gain/loss last hand

    # ── Convenience pass-throughs ─────────────────────────────────────────────

    @property
    def name(self) -> str:       return self.player.name
    @property
    def personality(self) -> str: return self.player.personality
    @property
    def bankroll(self) -> int:   return self.player.bankroll
    @property
    def active(self) -> bool:    return self.player.active
    @property
    def hand_value(self) -> int: return _hand_value(self.hand)

    # ── Per-hand lifecycle ────────────────────────────────────────────────────

    def start_hand(self):
        self.hand        = []
        self.bet         = 0
        self._done       = False
        self.last_result = None
        self.last_net    = None

    def choose_bet(self) -> int:
        """Return bet amount; 0 if player is inactive."""
        if not self.player.active:
            return 0
        p = self.player.personality
        if p == "aggressive":
            pct = random.uniform(0.10, 0.30)
        elif p == "moderate":
            pct = random.uniform(0.05, 0.10)
        else:                              # conservative
            pct = random.uniform(0.01, 0.05)
        self.bet = max(1, min(int(self.player.bankroll * pct), self.player.bankroll))
        return self.bet

    def decide(self) -> str:
        """
        Simple fixed strategy: stand on hard 17+, hit below.
        Returns "hit" or "stand".
        """
        if self._done or _hand_value(self.hand) >= 17:
            self._done = True
            return "stand"
        return "hit"

    def resolve(self, dealer_hand: list) -> None:
        """Compare AI hand to dealer, update bankroll, store round result."""
        if not self.player.active or self.bet == 0 or not self.hand:
            return

        pv   = _hand_value(self.hand)
        dv   = _hand_value(dealer_hand)
        p_bj = _is_blackjack(self.hand)
        d_bj = _is_blackjack(dealer_hand)

        if p_bj and not d_bj:
            net    = int(self.bet * 1.5)
            result = "Blackjack"
        elif d_bj and not p_bj:
            net    = -self.bet
            result = "Loss (BJ)"
        elif pv > 21:
            net    = -self.bet
            result = "Bust"
        elif dv > 21 or pv > dv:
            net    = self.bet
            result = "Win"
        elif pv < dv:
            net    = -self.bet
            result = "Loss"
        else:
            net    = 0
            result = "Push"

        self.player.apply_result(net, self.bet, "blackjack")
        self.last_result = result
        self.last_net    = net

        print(
            f"[AI-BJ] {self.name:<14}  bet=${self.bet:>4}  "
            f"hand={pv:>2}  dealer={dv:>2}  {result:<12}  "
            f"net={net:>+5}  bankroll=${self.player.bankroll:,}"
        )
