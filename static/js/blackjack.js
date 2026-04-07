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

// ── Card rendering ────────────────────────────────────────────────────────────
function makeCard(rank, suit, mini = false) {
  const div = document.createElement('div');
  div.className = 'card' + (mini ? ' card-mini' : '');
  if (rank === '?') {
    div.classList.add('face-down');
    return div;
  }
  const isRed = RED_SUITS.has(suit);
  div.classList.add(isRed ? 'red' : 'black');
  div.innerHTML = `<span class="c-rank">${rank}</span><span class="c-suit">${suit}</span>`;
  return div;
}

function renderCards(containerId, hand, mini = false) {
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  (hand || []).forEach(([rank, suit]) => el.appendChild(makeCard(rank, suit, mini)));
}

// ── UI update ─────────────────────────────────────────────────────────────────
function renderAICards(container, ai, mini = true) {
  container.innerHTML = '';
  (ai.hand || []).forEach(([rank, suit]) => container.appendChild(makeCard(rank, suit, mini)));
}

function updateAIPanel(aiPlayers, bankroll) {
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
      const info = document.getElementById(`ai-info-${ai.name}`);
      info.innerHTML = `<span class="${netClass}">${ai.last_result} ${netStr}</span>`;
      const handRow = document.getElementById(`ai-hand-${ai.name}`);
      renderAICards(handRow, ai, true);
    }
  });

  // Last round
  const lastRoundEl = document.getElementById('last-round');
  lastRoundEl.innerHTML = '';
  // Include human
  const humanNet = window._lastHumanNet;
  const allNames = ['You', ...aiPlayers.map(a => a.name)];
  const allNets  = [humanNet, ...aiPlayers.map(a => a.last_net)];
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

function render(state) {
  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  renderCards('dealer-cards', state.dealer_hand);
  renderCards('player-cards', state.player_hand);

  document.getElementById('dealer-value').textContent = state.player_hand?.length ? state.dealer_value : '';
  document.getElementById('player-value').textContent = state.player_hand?.length ? state.player_value : '';

  window._canDouble = state.can_double;
  setButtons(state.state);
  showResult(state);
  if (state.ai_players) updateAIPanel(state.ai_players, state.bankroll);
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

// Make clicking a chip also add it to the bet
document.querySelectorAll('.chip').forEach(btn => {
  const orig = btn.onclick;
  btn.onclick = (e) => { setChip(parseInt(btn.dataset.amt)); addChip(); };
});

// ── Actions ───────────────────────────────────────────────────────────────────
async function deal() {
  if (currentBet === 0) return;
  const state = await api('/api/blackjack/deal', { bet: currentBet });
  window._lastHumanNet = state.net ?? null;
  currentBet = 0;
  document.getElementById('bet-display').textContent = '$0';
  document.getElementById('result-banner').textContent = '';
  document.getElementById('result-banner').className = 'result-banner';
  render(state);
  if (state.outcome) window._lastHumanNet = state.net;
}

async function hit() {
  const state = await api('/api/blackjack/hit', {});
  window._lastHumanNet = state.net ?? window._lastHumanNet;
  render(state);
}

async function stand() {
  const state = await api('/api/blackjack/stand', {});
  window._lastHumanNet = state.net ?? window._lastHumanNet;
  render(state);
}

async function dbl() {
  const state = await api('/api/blackjack/double', {});
  window._lastHumanNet = state.net ?? window._lastHumanNet;
  render(state);
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
