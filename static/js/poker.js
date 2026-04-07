// ── State ─────────────────────────────────────────────────────────────────────
let chipAmt = 25;
let currentBet = 0;
let lastRoundNets = {};  // name -> net
const RED_SUITS = new Set(['♥', '♦']);

// ── API ───────────────────────────────────────────────────────────────────────
async function api(path, body = null) {
  const opts = body != null
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(path, opts);
  return r.json();
}

// ── Cards ─────────────────────────────────────────────────────────────────────
function makeCard(rank, suit, mini = false) {
  const div = document.createElement('div');
  div.className = 'card' + (mini ? ' card-mini' : '');
  if (rank === '?') { div.classList.add('face-down'); return div; }
  div.classList.add(RED_SUITS.has(suit) ? 'red' : 'black');
  div.innerHTML = `<span class="c-rank">${rank}</span><span class="c-suit">${suit}</span>`;
  return div;
}

function renderCards(containerId, hand, mini = false) {
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  (hand || []).forEach(([rank, suit]) => el.appendChild(makeCard(rank, suit, mini)));
}

// ── Chip / bet ────────────────────────────────────────────────────────────────
function setChip(amt) {
  chipAmt = amt;
  document.querySelectorAll('.chip').forEach(b => {
    const val = parseInt(b.textContent.replace('$',''));
    b.classList.toggle('active', val === amt);
  });
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
  btn.onclick = () => { setChip(parseInt(btn.textContent.replace('$',''))); addChip(); };
});

// ── Actions ───────────────────────────────────────────────────────────────────
async function deal() {
  if (currentBet === 0) return;
  const state = await api('/api/poker/deal', { bet: currentBet });
  if (state.error) { alert(state.error); return; }
  clearBet();
  lastRoundNets = {};
  render(state);
}

async function check() {
  const state = await api('/api/poker/check', {});
  if (state.error) { alert(state.error); return; }
  lastRoundNets['You'] = state.net;
  (state.ai_players || []).forEach(ai => { lastRoundNets[ai.name] = ai.last_net; });
  render(state);
}

async function fold() {
  const state = await api('/api/poker/fold', {});
  if (state.error) { alert(state.error); return; }
  lastRoundNets['You'] = state.net;
  (state.ai_players || []).forEach(ai => { lastRoundNets[ai.name] = ai.last_net; });
  render(state);
}

// ── Render ────────────────────────────────────────────────────────────────────
function render(state) {
  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();

  // Community cards
  renderCards('community-cards', state.community);

  // Pot
  const potEl = document.getElementById('pot-display');
  potEl.textContent = state.pot > 0 ? `Pot: $${state.pot.toLocaleString()}` : '';

  // Player cards
  renderCards('player-cards', state.player_hole);

  // Hand name
  document.getElementById('hand-name').textContent = state.player_hand_name || '';

  // Result
  showResult(state);

  // Controls visibility
  const isBetting = state.state === 'betting';
  document.getElementById('bet-controls').style.display   = isBetting ? 'flex' : 'none';
  document.getElementById('round-controls').style.display = !isBetting ? 'flex' : 'none';

  // AI panel
  updateAIPanel(state.ai_players, state.bankroll, state.state !== 'betting');
}

function showResult(state) {
  const banner = document.getElementById('result-banner');
  if (!state.outcome) { banner.textContent = ''; banner.className = 'result-banner'; return; }

  const net = state.net;
  const netStr = net > 0 ? `+$${net.toLocaleString()}` : net < 0 ? `-$${Math.abs(net).toLocaleString()}` : '$0';

  let msg, cls;
  if (state.outcome === 'win') {
    msg = `YOU WIN! ${netStr}  (${state.player_hand_name || ''})`;
    cls = 'win';
  } else if (state.outcome === 'lose') {
    msg = `YOU LOSE ${netStr}  (${state.player_hand_name || ''})`;
    cls = 'loss';
  } else if (state.outcome === 'fold') {
    msg = `YOU FOLDED  ${netStr}`;
    cls = 'loss';
  } else {
    msg = netStr;
    cls = 'push';
  }
  banner.textContent = msg;
  banner.className   = `result-banner ${cls}`;
}

function updateAIPanel(aiPlayers, bankroll, showCards) {
  const container = document.getElementById('ai-cards-container');
  container.innerHTML = '';

  (aiPlayers || []).forEach(ai => {
    const card = document.createElement('div');
    card.className = 'ai-card';

    let statusLine = '';
    if (ai.folded) {
      statusLine = '<span class="text-loss">Folded</span>';
    } else if (ai.last_result) {
      const net = ai.last_net;
      const netStr = net > 0 ? `+$${net.toLocaleString()}` : net < 0 ? `-$${Math.abs(net).toLocaleString()}` : '$0';
      const cls = net > 0 ? 'text-win' : net < 0 ? 'text-loss' : 'text-muted';
      statusLine = `<span class="${cls}">${ai.last_result}  ${netStr}</span>`;
    } else if (ai.bet > 0) {
      statusLine = `Ante: $${ai.bet.toLocaleString()}`;
    }

    card.innerHTML = `
      <div class="ai-card-accent ${ai.personality}"></div>
      <div class="ai-name ${ai.personality}">${ai.name.toUpperCase()}</div>
      <div class="ai-bankroll">$${ai.bankroll.toLocaleString()}</div>
      <div class="ai-info">${statusLine}</div>
      <div class="ai-cards-row" id="ai-hand-${ai.name}"></div>`;
    container.appendChild(card);

    // Show AI cards if revealed (showdown or fold)
    const handEl = document.getElementById(`ai-hand-${ai.name}`);
    if (showCards && ai.hand && ai.hand.length) {
      ai.hand.forEach(([r, s]) => handEl.appendChild(makeCard(r, s, true)));
    }
  });

  // Last round
  const lrEl = document.getElementById('last-round');
  lrEl.innerHTML = '';
  const allNames = ['You', ...(aiPlayers||[]).map(a => a.name)];
  allNames.forEach(name => {
    const net = lastRoundNets[name];
    const row = document.createElement('div');
    row.className = 'lb-row' + (name === 'You' ? ' you' : '');
    const netStr = net == null ? '—'
      : net > 0 ? `<span class="text-win">+$${net.toLocaleString()}</span>`
      : net < 0 ? `<span class="text-loss">-$${Math.abs(net).toLocaleString()}</span>`
      : '$0';
    row.innerHTML = `<span>${name}</span><span>${netStr}</span>`;
    lrEl.appendChild(row);
  });

  // Leaderboard
  const lbEl = document.getElementById('leaderboard');
  lbEl.innerHTML = '';
  const players = [['You', bankroll], ...(aiPlayers||[]).map(a => [a.name, a.bankroll])];
  players.sort((a, b) => b[1] - a[1]);
  players.forEach(([name, br], i) => {
    const row = document.createElement('div');
    row.className = 'lb-row' + (name === 'You' ? ' you' : '');
    row.innerHTML = `<span>${i+1}  ${name}</span><span>$${br.toLocaleString()}</span>`;
    lbEl.appendChild(row);
  });
}

// ── Leave ─────────────────────────────────────────────────────────────────────
document.getElementById('back-btn').addEventListener('click', async (e) => {
  e.preventDefault();
  await api('/api/poker/leave', {});
  window.location.href = '/';
});

// ── Init ──────────────────────────────────────────────────────────────────────
setChip(25);
api('/api/poker/state').then(render);
