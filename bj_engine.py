"""Blackjack game engine — no tkinter, pure logic."""
import random
from blackjack_ai import BlackjackAI

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


def hand_value(hand):
    total, aces = 0, 0
    for rank, _suit in hand:
        if rank == 'A':
            aces += 1; total += 11
        elif rank in ('J', 'Q', 'K'):
            total += 10
        else:
            total += int(rank)
    while total > 21 and aces:
        total -= 10; aces -= 1
    return total


def is_blackjack(hand):
    return len(hand) == 2 and hand_value(hand) == 21


class BlackjackGame:
    def __init__(self, bankroll, ai_players):
        self.bankroll = bankroll
        self.deck = []
        self._new_shoe()
        self.bet = 0
        self.player_hand = []
        self.dealer_hand = []
        self.state = 'betting'   # betting | playing | result
        self.session_log = []
        self._bj_ais = [BlackjackAI(p) for p in ai_players]

    def _new_shoe(self, decks=6):
        self.deck = [(r, s) for s in SUITS for r in RANKS] * decks
        random.shuffle(self.deck)

    def _draw(self):
        if len(self.deck) < 52:
            self._new_shoe()
        return self.deck.pop()

    # ── Actions ───────────────────────────────────────────────────────────────

    def deal(self, bet):
        if bet <= 0 or bet > self.bankroll:
            return {'error': 'Invalid bet'}
        self.bet = bet
        self.player_hand = [self._draw(), self._draw()]
        self.dealer_hand = [self._draw(), self._draw()]
        self.state = 'playing'

        for ai in self._bj_ais:
            ai.start_hand()
            ai.choose_bet()
            if ai.bet > 0:
                ai.hand = [self._draw(), self._draw()]
                while ai.decide() == 'hit':
                    ai.hand.append(self._draw())

        p_bj = is_blackjack(self.player_hand)
        d_bj = is_blackjack(self.dealer_hand)
        if p_bj and d_bj:
            return self._end_round('push')
        if p_bj:
            return self._end_round('blackjack')
        if d_bj:
            return self._end_round('lose')
        return self.get_state()

    def hit(self):
        if self.state != 'playing':
            return {'error': 'Not playing'}
        self.player_hand.append(self._draw())
        pv = hand_value(self.player_hand)
        if pv > 21:
            return self._end_round('bust')
        if pv == 21:
            return self._play_dealer()
        return self.get_state()

    def stand(self):
        if self.state != 'playing':
            return {'error': 'Not playing'}
        return self._play_dealer()

    def double(self):
        if self.state != 'playing':
            return {'error': 'Not playing'}
        if self.bet * 2 > self.bankroll:
            return {'error': 'Insufficient funds'}
        self.bet *= 2
        self.player_hand.append(self._draw())
        if hand_value(self.player_hand) > 21:
            return self._end_round('bust')
        return self._play_dealer()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _play_dealer(self):
        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self._draw())
        pv = hand_value(self.player_hand)
        dv = hand_value(self.dealer_hand)
        if dv > 21:
            return self._end_round('dealer_bust')
        if pv > dv:
            return self._end_round('win')
        if pv < dv:
            return self._end_round('lose')
        return self._end_round('push')

    def _end_round(self, outcome):
        # Ensure dealer is complete
        while self.dealer_hand and hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self._draw())

        if outcome == 'blackjack':
            net, result_str = int(self.bet * 1.5), 'Blackjack'
        elif outcome == 'win':
            net, result_str = self.bet, 'Win'
        elif outcome == 'dealer_bust':
            net, result_str = self.bet, 'Dealer Bust'
        elif outcome == 'bust':
            net, result_str = -self.bet, 'BUST!'
        elif outcome == 'lose':
            net, result_str = -self.bet, 'DEALER WINS'
        else:
            net, result_str = 0, 'Push'

        self.bankroll += net
        self.session_log.append({'game': 'Blackjack', 'bet': self.bet,
                                 'result': result_str, 'net': net})

        for ai in self._bj_ais:
            ai.resolve(self.dealer_hand)

        if self.bankroll <= 0:
            self.bankroll = 1000

        state = self.get_state(hide_hole=False)
        state.update({'outcome': outcome, 'net': net, 'result_str': result_str})
        self.bet = 0
        self.state = 'betting'
        return state

    def get_state(self, hide_hole=True):
        dealer = list(self.dealer_hand)
        if hide_hole and len(dealer) > 1 and self.state == 'playing':
            dealer = [dealer[0], ('?', '?')]
        return {
            'state': self.state,
            'bankroll': self.bankroll,
            'bet': self.bet,
            'player_hand': self.player_hand,
            'dealer_hand': dealer,
            'player_value': hand_value(self.player_hand) if self.player_hand else 0,
            'dealer_value': hand_value(self.dealer_hand) if self.dealer_hand else 0,
            'can_double': self.bet * 2 <= self.bankroll and self.state == 'playing',
            'ai_players': [
                {
                    'name': ai.name,
                    'bankroll': ai.bankroll,
                    'bet': ai.bet,
                    'hand': ai.hand,
                    'last_result': ai.last_result,
                    'last_net': ai.last_net,
                    'personality': ai.personality,
                }
                for ai in self._bj_ais
            ],
        }
