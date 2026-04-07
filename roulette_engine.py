"""Roulette game engine — no tkinter, pure logic."""
import random

RED_NUMBERS  = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

PAYOUTS = {
    'red':1,'black':1,'even':1,'odd':1,'low':1,'high':1,
    'dozen1':2,'dozen2':2,'dozen3':2,
    'col1':2,'col2':2,'col3':2,
}


def get_payout(bet_key):
    if bet_key.startswith('n_'):
        return 35
    return PAYOUTS.get(bet_key, 1)


def check_win(bet_key, result):
    if bet_key.startswith('n_'): return result == int(bet_key[2:])
    if bet_key == 'red':    return result in RED_NUMBERS
    if bet_key == 'black':  return result in BLACK_NUMBERS
    if bet_key == 'even':   return result != 0 and result % 2 == 0
    if bet_key == 'odd':    return result % 2 == 1
    if bet_key == 'low':    return 1 <= result <= 18
    if bet_key == 'high':   return 19 <= result <= 36
    if bet_key == 'dozen1': return 1 <= result <= 12
    if bet_key == 'dozen2': return 13 <= result <= 24
    if bet_key == 'dozen3': return 25 <= result <= 36
    if bet_key == 'col1':   return result != 0 and result % 3 == 1
    if bet_key == 'col2':   return result != 0 and result % 3 == 2
    if bet_key == 'col3':   return result != 0 and result % 3 == 0
    return False


def number_color(n):
    if n == 0:           return 'green'
    if n in RED_NUMBERS: return 'red'
    return 'black'


class RouletteGame:
    def __init__(self, bankroll, ai_players):
        self.bankroll    = bankroll
        self.active_bets = {}   # bet_key -> amount
        self.last_result = None
        self.last_net    = None
        self.session_log = []
        self.ai_players  = ai_players   # RouletteAI instances (AggressivePlayer etc.)

    def place_bet(self, bet_key, amount):
        if amount <= 0:
            return {'error': 'Invalid amount'}
        if sum(self.active_bets.values()) + amount > self.bankroll:
            return {'error': 'Insufficient funds'}
        self.active_bets[bet_key] = self.active_bets.get(bet_key, 0) + amount
        return self.get_state()

    def clear_bets(self):
        self.active_bets = {}
        return self.get_state()

    def spin(self):
        if not self.active_bets:
            return {'error': 'No bets placed'}

        result = random.randint(0, 36)

        # AI choose bets
        for ai in self.ai_players:
            ai.choose_bet()

        # Calculate human net
        net = sum(
            amount * get_payout(k) if check_win(k, result) else -amount
            for k, amount in self.active_bets.items()
        )
        total_bet = sum(self.active_bets.values())
        won_bets  = [k for k in self.active_bets if check_win(k, result)]

        self.bankroll += net
        self.last_result = result
        self.last_net    = net

        color = number_color(result)
        result_str = f"{result} ({'Red' if color == 'red' else 'Black' if color == 'black' else 'Green'})"
        self.session_log.append({'game': 'Roulette', 'bet': total_bet,
                                 'result': result_str, 'net': net})

        # Resolve AI
        for ai in self.ai_players:
            ai.resolve(result, check_win, get_payout)

        if self.bankroll <= 0:
            self.bankroll = 1000

        self.active_bets = {}
        state = self.get_state()
        state.update({
            'spin_result': result,
            'result_color': color,
            'net': net,
            'won_bets': won_bets,
        })
        return state

    def get_state(self):
        return {
            'bankroll':    self.bankroll,
            'active_bets': self.active_bets,
            'total_bet':   sum(self.active_bets.values()),
            'last_result': self.last_result,
            'last_net':    self.last_net,
            'ai_players':  [
                {
                    'name':        ai.name,
                    'bankroll':    ai.bankroll,
                    'personality': ai.personality,
                    'last_net':    ai.last_net,
                    'profit_loss': ai.profit_loss,
                }
                for ai in self.ai_players
            ],
        }
