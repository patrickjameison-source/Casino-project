"""Poker game engine — no tkinter, pure logic. 4-player: human vs 3 AI."""
import random
from poker_ai import PokerAI, _best_hand

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']


class PokerGame:
    def __init__(self, bankroll, ai_players):
        self.bankroll    = bankroll
        self.deck        = []
        self.bet         = 0
        self.pot         = 0
        self.player_hole = []
        self.community   = []
        self.folded      = False
        self.state       = 'betting'   # betting | flop | result
        self.last_net    = None
        self.session_log = []
        self._pk_ais     = [PokerAI(p) for p in ai_players]

    def _new_shoe(self):
        self.deck = [(r, s) for s in SUITS for r in RANKS]
        random.shuffle(self.deck)

    def _draw(self):
        if not self.deck:
            self._new_shoe()
        return self.deck.pop()

    # ── Actions ───────────────────────────────────────────────────────────────

    def deal(self, bet):
        if bet <= 0 or bet > self.bankroll:
            return {'error': 'Invalid bet'}

        self._new_shoe()
        self.bet         = bet
        self.pot         = bet
        self.player_hole = [self._draw(), self._draw()]
        self.community   = []
        self.folded      = False
        self.last_net    = None

        # AI antes + hole cards
        for ai in self._pk_ais:
            ai.start_hand()
            ai.choose_bet()
            if ai.bet > 0:
                self.pot += ai.bet
                ai.hand = [self._draw(), self._draw()]

        # Flop
        self.community = [self._draw(), self._draw(), self._draw()]

        # AI flop decision
        for ai in self._pk_ais:
            if ai.hand and not ai.folded:
                if ai.decide(self.community) == 'fold':
                    ai.folded = True
                    ai.player.apply_result(-ai.bet, ai.bet, 'poker')
                    ai.last_result = 'Fold'
                    ai.last_net    = -ai.bet

        self.state = 'flop'
        return self.get_state()

    def check(self):
        if self.state != 'flop':
            return {'error': 'Not in flop state'}

        self.community.append(self._draw())   # turn
        self.community.append(self._draw())   # river

        return self._showdown()

    def fold(self):
        if self.state != 'flop':
            return {'error': 'Not in flop state'}

        self.folded = True
        net = -self.bet
        self.bankroll += net
        self.last_net  = net
        self.session_log.append({'game': 'Poker', 'bet': self.bet,
                                 'result': 'Fold', 'net': net})

        # Complete community for AI resolution
        while len(self.community) < 5:
            self.community.append(self._draw())

        self._resolve_ai_after_fold()

        self.bet   = 0
        self.pot   = 0
        self.state = 'betting'
        state = self.get_state(reveal_ai=True)
        state.update({'outcome': 'fold', 'net': net, 'reveal_ai': True})
        return state

    # ── Internal ──────────────────────────────────────────────────────────────

    def _showdown(self):
        entries = []

        p_cards = self.player_hole + self.community
        p_score, p_name, p_tb = _best_hand(p_cards)
        entries.append((p_score, p_tb, p_name, True, None))

        for ai in self._pk_ais:
            if not ai.folded and ai.hand:
                s, name, tb = _best_hand(ai.hand + self.community)
                entries.append((s, tb, name, False, ai))

        best = max((s, tb) for s, tb, *_ in entries)
        winners = [e for e in entries if (e[0], e[1]) == best]
        split   = self.pot // len(winners)

        human_wins = any(e[3] for e in winners)
        net = split - self.bet if human_wins else -self.bet
        self.bankroll += net
        self.last_net  = net

        result_str = f"Win ({p_name})" if human_wins else f"Loss ({p_name})"
        self.session_log.append({'game': 'Poker', 'bet': self.bet,
                                 'result': result_str, 'net': net})

        for ai in self._pk_ais:
            if not ai.folded and ai.hand:
                ai_wins  = any(e[4] is ai for e in winners)
                ai_net   = split - ai.bet if ai_wins else -ai.bet
                hand_name = _best_hand(ai.hand + self.community)[1]
                ai.player.apply_result(ai_net, ai.bet, 'poker')
                ai.last_result = f"Win ({hand_name})" if ai_wins else f"Loss ({hand_name})"
                ai.last_net    = ai_net

        self.bet   = 0
        self.pot   = 0
        self.state = 'betting'
        state = self.get_state(reveal_ai=True)
        state.update({
            'outcome':          'win' if human_wins else 'lose',
            'net':              net,
            'player_hand_name': p_name,
            'reveal_ai':        True,
        })
        return state

    def _resolve_ai_after_fold(self):
        """Resolve AIs against each other when human has folded."""
        active = [ai for ai in self._pk_ais if not ai.folded and ai.hand]
        if not active:
            return

        entries = [(  _best_hand(ai.hand + self.community), ai) for ai in active]
        best    = max((e[0][0], e[0][2]) for e in entries)
        winners = [ai for (s, _, tb), ai in entries if (s, tb) == best]
        split   = self.pot // len(winners)   # full pot (including human's ante)

        for ai in active:
            ai_wins   = any(w is ai for w in winners)
            ai_net    = split - ai.bet if ai_wins else -ai.bet
            hand_name = _best_hand(ai.hand + self.community)[1]
            ai.player.apply_result(ai_net, ai.bet, 'poker')
            ai.last_result = f"Win ({hand_name})" if ai_wins else f"Loss ({hand_name})"
            ai.last_net    = ai_net

    def _hand_name(self, hole):
        cards = hole + self.community
        if len(cards) < 5:
            return ''
        return _best_hand(cards)[1]

    def get_state(self, reveal_ai=False):
        cards = self.player_hole + self.community
        return {
            'state':            self.state,
            'busted':           self.bankroll <= 0,
            'bankroll':         self.bankroll,
            'bet':              self.bet,
            'pot':              self.pot,
            'player_hole':      self.player_hole,
            'community':        self.community,
            'folded':           self.folded,
            'player_hand_name': self._hand_name(self.player_hole),
            'ai_players': [
                {
                    'name':        ai.name,
                    'bankroll':    ai.bankroll,
                    'bet':         ai.bet,
                    'hand':        ai.hand if (reveal_ai or ai.folded) else
                                   [('?', '?'), ('?', '?')] if ai.hand else [],
                    'folded':      ai.folded,
                    'last_result': ai.last_result,
                    'last_net':    ai.last_net,
                    'personality': ai.personality,
                }
                for ai in self._pk_ais
            ],
        }
