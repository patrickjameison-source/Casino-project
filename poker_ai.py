"""
poker_ai.py — Poker-specific AI player adapter.

Wraps an existing Player (player.py) and adds:
  - bet sizing by personality
  - post-flop check/fold decision by hand strength
  - hand resolution via player.apply_result()

Hand evaluation is inlined here to avoid circular imports with poker.py.
"""

import random
from collections import Counter
from itertools import combinations
from player import Player


# ── Standalone hand helpers (mirrors poker.py — no import needed) ─────────────

_RANKS    = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
_RANK_VAL = {r: i + 2 for i, r in enumerate(_RANKS)}


def _evaluate(hand):
    vals  = sorted([_RANK_VAL[r] for r, _ in hand], reverse=True)
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


def _best_hand(cards):
    if len(cards) == 5:
        return _evaluate(cards)
    return max(
        (_evaluate(list(c)) for c in combinations(cards, 5)),
        key=lambda x: (x[0], x[2])
    )


def _compare(cards1, cards2):
    s1, _, tb1 = _best_hand(cards1)
    s2, _, tb2 = _best_hand(cards2)
    if s1 != s2:
        return 1 if s1 > s2 else -1
    for v1, v2 in zip(tb1, tb2):
        if v1 != v2:
            return 1 if v1 > v2 else -1
    return 0


# ── Adapter ───────────────────────────────────────────────────────────────────

class PokerAI:
    """
    Wraps a Player for one Poker hand.

    Lifecycle per hand:
      1. start_hand()          — reset state
      2. choose_bet()          — returns ante amount
      3. deal two cards into .hand, then community built up
      4. decide(community)     — "check" or "fold" after flop
      5. resolve(dealer_hole, community) — settles; no-op if folded
    """

    def __init__(self, player: Player):
        self.player      = player
        self.hand        = []
        self.bet         = 0
        self.folded      = False
        self.last_result = None   # "Win", "Loss", "Tie", "Fold", or None
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

    # ── Per-hand lifecycle ────────────────────────────────────────────────────

    def start_hand(self):
        self.hand        = []
        self.bet         = 0
        self.folded      = False
        self.last_result = None
        self.last_net    = None

    def choose_bet(self) -> int:
        """Return ante amount; 0 if player is inactive."""
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

    def decide(self, community: list) -> str:
        """
        Check or fold after seeing the flop (hole + 3 community cards).

        Personality thresholds (hand score 0=high card … 9=royal flush):
          aggressive  — folds only on high card, and only 20% of the time
          moderate    — folds on high card
          conservative — folds on less than two pair (score < 2)
        """
        if not self.hand or not community:
            return "check"

        score, _, _ = _best_hand(self.hand + community)

        p = self.player.personality
        if p == "aggressive":
            fold = (score == 0 and random.random() < 0.20)
        elif p == "moderate":
            fold = (score == 0)
        else:                              # conservative
            fold = (score < 2)

        return "fold" if fold else "check"

    def resolve(self, dealer_hole: list, community: list) -> None:
        """Compare AI hand to dealer, update bankroll, store result."""
        if not self.player.active or self.bet == 0 or self.folded or not self.hand:
            return

        p_cards = self.hand + community
        d_cards = dealer_hole + community
        outcome = _compare(p_cards, d_cards)

        _, p_name, _ = _best_hand(p_cards)

        if outcome > 0:
            net    = self.bet
            result = f"Win ({p_name})"
        elif outcome < 0:
            net    = -self.bet
            result = f"Loss ({p_name})"
        else:
            net    = 0
            result = f"Tie ({p_name})"

        self.player.apply_result(net, self.bet, "poker")
        self.last_result = result
        self.last_net    = net

        print(
            f"[AI-PK] {self.name:<14}  bet=${self.bet:>4}  {result:<22}  "
            f"net={net:>+5}  bankroll=${self.player.bankroll:,}"
        )
