"""Casino Royale — Flask web app."""
import secrets
from flask import Flask, request, jsonify, session, render_template
from ai_players import AggressivePlayer, ModeratePlayer, ConservativePlayer
from bj_engine import BlackjackGame
from roulette_engine import RouletteGame
from poker_engine import PokerGame

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Server-side session store  {sid -> session_dict}
_sessions: dict = {}


# ── Session helpers ───────────────────────────────────────────────────────────

def _get_sess():
    if 'sid' not in session:
        session['sid'] = secrets.token_hex(16)
    sid = session['sid']
    if sid not in _sessions:
        _sessions[sid] = {
            'bankroll':          1000,
            'starting_bankroll': 1000,
            'history':           [],
            'ai_players':        [AggressivePlayer(), ModeratePlayer(), ConservativePlayer()],
            'bj':                None,
            'roulette':          None,
            'poker':             None,
        }
    return _sessions[sid]


def _flush(sess, game_key):
    """Copy new session_log entries from a game into session history."""
    game = sess[game_key]
    if not game:
        return
    offset_key = f'{game_key}_offset'
    offset     = sess.get(offset_key, 0)
    new        = game.session_log[offset:]
    sess['history'].extend(new)
    sess[offset_key] = len(game.session_log)
    sess['bankroll'] = game.bankroll


def _sync_bankroll(sess, game):
    sess['bankroll'] = game.bankroll


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route('/')
def lobby():
    _get_sess()
    return render_template('lobby.html')


@app.route('/blackjack')
def blackjack_page():
    _get_sess()
    return render_template('blackjack.html')


@app.route('/roulette')
def roulette_page():
    _get_sess()
    return render_template('roulette.html')


@app.route('/poker')
def poker_page():
    _get_sess()
    return render_template('poker.html')


# ── Lobby API ─────────────────────────────────────────────────────────────────

@app.route('/api/lobby')
def api_lobby():
    sess = _get_sess()
    # Flush any pending game logs
    for key in ('bj', 'roulette', 'poker'):
        _flush(sess, key)
    human_pl = sess['bankroll'] - sess['starting_bankroll']
    # Reconstruct human balance history from full session history
    h_hist = [sess['starting_bankroll']]
    for e in sess['history']:
        h_hist.append(h_hist[-1] + e['net'])
    return jsonify({
        'bankroll':          sess['bankroll'],
        'busted':            sess['bankroll'] <= 0,
        'starting_bankroll': sess['starting_bankroll'],
        'human_pl':          human_pl,
        'history':           sess['history'][-50:],
        'human_history':     h_hist,
        'ai_players': [
            {
                'name':             p.name,
                'bankroll':         p.bankroll,
                'profit_loss':      p.profit_loss,
                'personality':      p.personality,
                'bankroll_history': p.bankroll_history,
            }
            for p in sess['ai_players']
        ],
    })


# ── Blackjack API ─────────────────────────────────────────────────────────────

def _bj(sess):
    if sess['bj'] is None:
        sess['bj'] = BlackjackGame(sess['bankroll'], sess['ai_players'])
    return sess['bj']


@app.route('/api/blackjack/state')
def bj_state():
    sess = _get_sess()
    return jsonify(_bj(sess).get_state())


@app.route('/api/blackjack/deal', methods=['POST'])
def bj_deal():
    sess = _get_sess()
    bet  = int(request.json.get('bet', 0))
    result = _bj(sess).deal(bet)
    _sync_bankroll(sess, sess['bj'])
    return jsonify(result)


@app.route('/api/blackjack/hit', methods=['POST'])
def bj_hit():
    sess = _get_sess()
    result = _bj(sess).hit()
    _sync_bankroll(sess, sess['bj'])
    return jsonify(result)


@app.route('/api/blackjack/stand', methods=['POST'])
def bj_stand():
    sess = _get_sess()
    result = _bj(sess).stand()
    _sync_bankroll(sess, sess['bj'])
    return jsonify(result)


@app.route('/api/blackjack/double', methods=['POST'])
def bj_double():
    sess = _get_sess()
    result = _bj(sess).double()
    _sync_bankroll(sess, sess['bj'])
    return jsonify(result)


@app.route('/api/blackjack/leave', methods=['POST'])
def bj_leave():
    sess = _get_sess()
    _flush(sess, 'bj')
    return jsonify({'bankroll': sess['bankroll']})


# ── Roulette API ──────────────────────────────────────────────────────────────

def _roulette(sess):
    if sess['roulette'] is None:
        sess['roulette'] = RouletteGame(sess['bankroll'], sess['ai_players'])
    return sess['roulette']


@app.route('/api/roulette/state')
def roulette_state():
    sess = _get_sess()
    return jsonify(_roulette(sess).get_state())


@app.route('/api/roulette/bet', methods=['POST'])
def roulette_bet():
    sess    = _get_sess()
    bet_key = request.json.get('bet_key')
    amount  = int(request.json.get('amount', 0))
    return jsonify(_roulette(sess).place_bet(bet_key, amount))


@app.route('/api/roulette/clear', methods=['POST'])
def roulette_clear():
    sess = _get_sess()
    return jsonify(_roulette(sess).clear_bets())


@app.route('/api/roulette/spin', methods=['POST'])
def roulette_spin():
    sess   = _get_sess()
    result = _roulette(sess).spin()
    _sync_bankroll(sess, sess['roulette'])
    return jsonify(result)


@app.route('/api/roulette/leave', methods=['POST'])
def roulette_leave():
    sess = _get_sess()
    _flush(sess, 'roulette')
    return jsonify({'bankroll': sess['bankroll']})


# ── Poker API ─────────────────────────────────────────────────────────────────

def _poker(sess):
    if sess['poker'] is None:
        sess['poker'] = PokerGame(sess['bankroll'], sess['ai_players'])
    return sess['poker']


@app.route('/api/poker/state')
def poker_state():
    sess = _get_sess()
    return jsonify(_poker(sess).get_state())


@app.route('/api/poker/deal', methods=['POST'])
def poker_deal():
    sess   = _get_sess()
    bet    = int(request.json.get('bet', 0))
    result = _poker(sess).deal(bet)
    _sync_bankroll(sess, sess['poker'])
    return jsonify(result)


@app.route('/api/poker/check', methods=['POST'])
def poker_check():
    sess   = _get_sess()
    result = _poker(sess).check()
    _sync_bankroll(sess, sess['poker'])
    return jsonify(result)


@app.route('/api/poker/fold', methods=['POST'])
def poker_fold():
    sess   = _get_sess()
    result = _poker(sess).fold()
    _sync_bankroll(sess, sess['poker'])
    return jsonify(result)


@app.route('/api/poker/leave', methods=['POST'])
def poker_leave():
    sess = _get_sess()
    _flush(sess, 'poker')
    return jsonify({'bankroll': sess['bankroll']})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
