// ── State ─────────────────────────────────────────────────────────────────────
let chipAmt = 25;
let currentBet = 0;
const RED_SUITS = new Set(['♥', '♦']);

// ── API ───────────────────────────────────────────────────────────────────────
async function api(path, body = null) {
  const opts = body != null
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(path, opts);
  return r.json();
}

// ── Dealer value display ──────────────────────────────────────────────────────
// When the hole card is hidden, show only the visible card(s) total + " + ?"
function dealerDisplay(dealerHand, fullValue) {
  const hasHidden = (dealerHand || []).some(([r]) => r === '?');
  if (!hasHidden) return fullValue;
  const visible = (dealerHand || []).filter(([r]) => r !== '?');
  if (!visible.length) return '?';
  let total = 0, aces = 0;
  for (const [rank] of visible) {
    if (rank === 'A')                       { aces++; total += 11; }
    else if (['J','Q','K'].includes(rank))  { total += 10; }
    else                                    { total += parseInt(rank); }
  }
  while (total > 21 && aces) { total -= 10; aces--; }
  return total + ' + ?';
}

// ── Card flip ─────────────────────────────────────────────────────────────────
function makeFlipCard(rank, suit, mini = false) {
  const wrap = document.createElement('div');
  wrap.className = 'card-flip' + (mini ? ' card-flip-mini' : '');

  const inner = document.createElement('div');
  inner.className = 'card-flip-inner';

  const back = document.createElement('div');
  back.className = 'card-back-face';

  const front = document.createElement('div');
  const isUnknown = rank === '?';
  front.className = 'card-face card' + (mini ? ' card-mini' : '') +
    (isUnknown ? '' : ' ' + (RED_SUITS.has(suit) ? 'red' : 'black'));
  if (!isUnknown) {
    front.innerHTML = `<span class="c-rank">${rank}</span><span class="c-suit">${suit}</span>`;
  }

  inner.appendChild(back);
  inner.appendChild(front);
  wrap.appendChild(inner);
  return { wrap, inner };
}

// Append one card to a container, flip it after `delay` ms
function appendCard(containerId, rank, suit, mini = false, delay = 0) {
  const el = document.getElementById(containerId);
  const { wrap, inner } = makeFlipCard(rank, suit, mini);
  el.appendChild(wrap);
  if (rank !== '?') setTimeout(() => inner.classList.add('flipped'), delay);
  // '?' cards stay face-down (card back visible, never flipped)
}

// Render all cards instantly — used for state restore on page load
function renderCards(containerId, hand, mini = false) {
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  (hand || []).forEach(([rank, suit]) => {
    const { wrap, inner } = makeFlipCard(rank, suit, mini);
    el.appendChild(wrap);
    if (rank !== '?') inner.classList.add('flipped');
  });
}

// Re-render dealer hand; cards before revealFrom are instant, rest animate
function renderDealerReveal(hand, revealFrom = 1) {
  const el = document.getElementById('dealer-cards');
  el.innerHTML = '';
  hand.forEach(([rank, suit], i) => {
    const { wrap, inner } = makeFlipCard(rank, suit, false);
    el.appendChild(wrap);
    if (rank === '?') {
      // stays face-down
    } else if (i < revealFrom) {
      inner.classList.add('flipped'); // already visible
    } else {
      setTimeout(() => inner.classList.add('flipped'), (i - revealFrom) * 380);
    }
  });
}

// ── Buttons ───────────────────────────────────────────────────────────────────
function lockButtons() {
  ['btn-deal','btn-hit','btn-stand','btn-double'].forEach(id =>
    document.getElementById(id).disabled = true);
}

function setButtons(state) {
  document.getElementById('btn-deal').disabled   = state !== 'betting';
  document.getElementById('btn-hit').disabled    = state !== 'playing';
  document.getElementById('btn-stand').disabled  = state !== 'playing';
  document.getElementById('btn-double').disabled = state !== 'playing' || !window._canDouble;
}

function showResult(state) {
  const banner = document.getElementById('result-banner');
  if (!state.outcome) { banner.textContent = ''; banner.className = 'result-banner'; return; }
  const msgs = {
    blackjack:   `BLACKJACK! +$${state.net.toLocaleString()}`,
    win:         `YOU WIN! +$${state.net.toLocaleString()}`,
    dealer_bust: `DEALER BUSTS — YOU WIN! +$${state.net.toLocaleString()}`,
    bust:        `BUST! -$${Math.abs(state.net).toLocaleString()}`,
    lose:        `DEALER WINS -$${Math.abs(state.net).toLocaleString()}`,
    push:        `PUSH — Bet returned`,
  };
  const cls = ['blackjack','win','dealer_bust'].includes(state.outcome) ? 'win'
            : state.outcome === 'push' ? 'push' : 'loss';
  banner.textContent = msgs[state.outcome] || '';
  banner.className   = `result-banner ${cls}`;
}

// ── Chip / bet ─────────────────────────────────────────────────────────────────
function setChip(amt) {
  chipAmt = amt;
  document.querySelectorAll('.chip').forEach(b =>
    b.classList.toggle('active', parseInt(b.dataset.amt) === amt));
}

function addChip() {
  currentBet += chipAmt;
  document.getElementById('bet-display').textContent = '$' + currentBet.toLocaleString();
}

function clearBet() {
  currentBet = 0;
  document.getElementById('bet-display').textContent = '$0';
}

document.querySelectorAll('.chip').forEach(btn => {
  btn.onclick = () => { setChip(parseInt(btn.dataset.amt)); addChip(); };
});

// ── AI panel ──────────────────────────────────────────────────────────────────
function updateAIPanel(aiPlayers, bankroll, animateCards = false, aiDelay = 0) {
  const container = document.getElementById('ai-cards-container');
  container.innerHTML = '';

  aiPlayers.forEach(ai => {
    const card = document.createElement('div');
    card.className = 'ai-card';
    card.innerHTML = `
      <div class="ai-card-accent ${ai.personality}"></div>
      <div class="ai-name ${ai.personality}">${ai.name.toUpperCase()}</div>
      <div class="ai-bankroll">$${ai.bankroll.toLocaleString()}</div>
      <div class="ai-info" id="ai-info-${ai.name}">Bet: ${ai.bet ? '$' + ai.bet.toLocaleString() : '—'}</div>
      <div class="ai-cards-row" id="ai-hand-${ai.name}"></div>`;
    container.appendChild(card);

    if (ai.last_result !== null && ai.last_result !== undefined) {
      const net = ai.last_net;
      const netStr = net > 0 ? `+$${net.toLocaleString()}` : net < 0 ? `-$${Math.abs(net).toLocaleString()}` : '$0';
      const netClass = net > 0 ? 'text-win' : net < 0 ? 'text-loss' : 'text-muted';
      document.getElementById(`ai-info-${ai.name}`).innerHTML =
        `<span class="${netClass}">${ai.last_result} ${netStr}</span>`;

      const handEl = document.getElementById(`ai-hand-${ai.name}`);
      (ai.hand || []).forEach(([rank, suit], i) => {
        const { wrap, inner } = makeFlipCard(rank, suit, true);
        handEl.appendChild(wrap);
        if (rank !== '?') {
          if (animateCards) {
            setTimeout(() => inner.classList.add('flipped'), aiDelay + i * 220);
          } else {
            inner.classList.add('flipped');
          }
        }
      });
    }
  });

  // Last round
  const lastRoundEl = document.getElementById('last-round');
  lastRoundEl.innerHTML = '';
  const allNames = ['You', ...aiPlayers.map(a => a.name)];
  const allNets  = [window._lastHumanNet, ...aiPlayers.map(a => a.last_net)];
  allNames.forEach((name, i) => {
    const net = allNets[i];
    const row = document.createElement('div');
    row.className = 'lb-row' + (name === 'You' ? ' you' : '');
    const netStr = net == null ? '—'
      : net > 0 ? `<span class="text-win">+$${net.toLocaleString()}</span>`
      : net < 0 ? `<span class="text-loss">-$${Math.abs(net).toLocaleString()}</span>`
      : '$0';
    row.innerHTML = `<span>${name}</span><span>${netStr}</span>`;
    lastRoundEl.appendChild(row);
  });

  // Leaderboard
  const lbEl = document.getElementById('leaderboard');
  lbEl.innerHTML = '';
  const players = [['You', bankroll], ...aiPlayers.map(a => [a.name, a.bankroll])];
  players.sort((a, b) => b[1] - a[1]);
  players.forEach(([name, br], i) => {
    const row = document.createElement('div');
    row.className = 'lb-row' + (name === 'You' ? ' you' : '');
    row.innerHTML = `<span>${i+1}  ${name}</span><span>$${br.toLocaleString()}</span>`;
    lbEl.appendChild(row);
  });
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function deal() {
  if (currentBet === 0) return;
  lockButtons();
  const state = await api('/api/blackjack/deal', { bet: currentBet });
  window._lastHumanNet = null;
  currentBet = 0;
  document.getElementById('bet-display').textContent = '$0';
  document.getElementById('result-banner').textContent = '';
  document.getElementById('result-banner').className = 'result-banner';
  document.getElementById('player-value').textContent = '';
  document.getElementById('dealer-value').textContent = '';
  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();

  // Clear hands
  document.getElementById('player-cards').innerHTML = '';
  document.getElementById('dealer-cards').innerHTML = '';

  // Deal in traditional order: player1 → dealer1 → player2 → dealer hole (face-down)
  const ph = state.player_hand;
  const dh = state.dealer_hand;
  appendCard('player-cards', ph[0][0], ph[0][1], false, 0);
  appendCard('dealer-cards', dh[0][0], dh[0][1], false, 320);
  if (ph[1]) appendCard('player-cards', ph[1][0], ph[1][1], false, 640);
  if (dh[1]) {
    // Hole card: append to DOM after delay but don't flip (stays face-down)
    const { wrap } = makeFlipCard(dh[1][0], dh[1][1], false);
    setTimeout(() => document.getElementById('dealer-cards').appendChild(wrap), 960);
  }

  // Show values + unlock buttons after deal animation finishes
  setTimeout(() => {
    document.getElementById('player-value').textContent = state.player_value;
    document.getElementById('dealer-value').textContent = dealerDisplay(state.dealer_hand, state.dealer_value);
    window._canDouble = state.can_double;
    setButtons(state.state);
    if (state.outcome) {
      // Blackjack / immediate result — flip dealer hole card
      renderDealerReveal(state.dealer_hand, 1);
      showResult(state);
      window._lastHumanNet = state.net;
      if (state.ai_players) updateAIPanel(state.ai_players, state.bankroll, true, 500);
    } else {
      if (state.ai_players) updateAIPanel(state.ai_players, state.bankroll, false, 0);
    }
  }, 1200);
}

async function hit() {
  lockButtons();
  const state = await api('/api/blackjack/hit', {});
  window._lastHumanNet = state.net ?? window._lastHumanNet;

  // Animate only the new card
  const ph = state.player_hand;
  const newCard = ph[ph.length - 1];
  appendCard('player-cards', newCard[0], newCard[1], false, 0);

  setTimeout(() => {
    document.getElementById('player-value').textContent = state.player_value;
    document.getElementById('dealer-value').textContent = dealerDisplay(state.dealer_hand, state.dealer_value);
    window._canDouble = state.can_double;
    setButtons(state.state);
    showResult(state);
    // Round ended (bust or hit to 21) — reveal dealer hole card + any drawn cards
    if (state.outcome) renderDealerReveal(state.dealer_hand, 1);
    if (state.ai_players) updateAIPanel(state.ai_players, state.bankroll,
      !!state.outcome, 0);
  }, 480);
}

async function stand() {
  lockButtons();
  const state = await api('/api/blackjack/stand', {});
  window._lastHumanNet = state.net ?? window._lastHumanNet;

  // Flip hole card + any new dealer cards (animate from index 1)
  renderDealerReveal(state.dealer_hand, 1);

  const revealDone = (state.dealer_hand.length - 1) * 380 + 250;
  setTimeout(() => {
    document.getElementById('dealer-value').textContent = dealerDisplay(state.dealer_hand, state.dealer_value);
    document.getElementById('player-value').textContent = state.player_value;
    window._canDouble = false;
    setButtons(state.state);
    showResult(state);
    if (state.ai_players) updateAIPanel(state.ai_players, state.bankroll, true, 0);
  }, revealDone);
}

async function dbl() {
  lockButtons();
  const state = await api('/api/blackjack/double', {});
  window._lastHumanNet = state.net ?? window._lastHumanNet;

  // Flip new player card first
  const ph = state.player_hand;
  appendCard('player-cards', ph[ph.length - 1][0], ph[ph.length - 1][1], false, 0);

  // Then reveal dealer (after 500ms)
  setTimeout(() => renderDealerReveal(state.dealer_hand, 1), 500);

  const totalDone = 500 + (state.dealer_hand.length - 1) * 380 + 250;
  setTimeout(() => {
    document.getElementById('player-value').textContent = state.player_value;
    document.getElementById('dealer-value').textContent = dealerDisplay(state.dealer_hand, state.dealer_value);
    window._canDouble = false;
    setButtons(state.state);
    showResult(state);
    if (state.ai_players) updateAIPanel(state.ai_players, state.bankroll, true, 0);
  }, totalDone);
}

// Full state render — no animation (page load / state restore)
function render(state) {
  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  renderCards('dealer-cards', state.dealer_hand);
  renderCards('player-cards', state.player_hand);
  document.getElementById('dealer-value').textContent = state.player_hand?.length ? dealerDisplay(state.dealer_hand, state.dealer_value) : '';
  document.getElementById('player-value').textContent = state.player_hand?.length ? state.player_value : '';
  window._canDouble = state.can_double;
  setButtons(state.state);
  showResult(state);
  if (state.ai_players) updateAIPanel(state.ai_players, state.bankroll, false, 0);
}

// ── Leave ─────────────────────────────────────────────────────────────────────
document.getElementById('back-btn').addEventListener('click', async (e) => {
  e.preventDefault();
  await api('/api/blackjack/leave', {});
  window.location.href = '/';
});

// ── Init ──────────────────────────────────────────────────────────────────────
window._lastHumanNet = null;
window._canDouble    = false;
setChip(25);
api('/api/blackjack/state').then(render);
