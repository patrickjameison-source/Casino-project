// ── State ─────────────────────────────────────────────────────────────────────
let chipAmt = 25;
let currentBet = 0;
let chipStack = [];
let lastRoundNets = {};
let communityCount = 0;
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

// Render a full hand into a container. animate=true flips cards one by one.
// startIdx is the first card index for delay calculation (used for community cards).
function renderCards(containerId, hand, mini = false, animate = false, startIdx = 0) {
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  (hand || []).forEach(([rank, suit], i) => {
    const { wrap, inner } = makeFlipCard(rank, suit, mini);
    el.appendChild(wrap);
    if (rank !== '?' && (animate ? false : true)) {
      inner.classList.add('flipped');
    } else if (rank !== '?') {
      setTimeout(() => inner.classList.add('flipped'), (startIdx + i) * 300);
    }
    // Unknown cards ('?') stay face-down — no flip
  });
}

// Append new cards to an existing container with animation (used for turn+river).
function appendCards(containerId, hand, mini = false, baseDelay = 0) {
  const el = document.getElementById(containerId);
  (hand || []).forEach(([rank, suit], i) => {
    const { wrap, inner } = makeFlipCard(rank, suit, mini);
    el.appendChild(wrap);
    setTimeout(() => inner.classList.add('flipped'), baseDelay + i * 320);
  });
}

// ── Chip / bet ────────────────────────────────────────────────────────────────
function chipColor(amt) {
  if (amt >= 500) return '#6a0dad';
  if (amt >= 100) return '#1a1a2e';
  if (amt >= 50)  return '#1565c0';
  if (amt >= 25)  return '#388e3c';
  if (amt >= 10)  return '#c62828';
  return '#bdbdbd';
}
function chipLabel(amt) {
  return amt >= 1000 ? '$' + (amt / 1000) + 'k' : '$' + amt;
}

function renderChipStack() {
  const area = document.getElementById('player-bet-area');
  if (!area) return;
  area.innerHTML = '';
  chipStack.forEach((amt, i) => {
    const chip = document.createElement('div');
    chip.className = 'bet-chip-visual';
    chip.style.background = chipColor(amt);
    if (i > 0) chip.style.marginLeft = '-8px';
    chip.textContent = chipLabel(amt);
    area.appendChild(chip);
  });
}

function clearChipStack() {
  chipStack = [];
  const area = document.getElementById('player-bet-area');
  if (area) area.innerHTML = '';
}

function setChip(amt) {
  chipAmt = amt;
  document.querySelectorAll('.chip').forEach(b => {
    b.classList.toggle('active', parseInt(b.textContent.replace('$', '')) === amt);
  });
}

function addChip() {
  currentBet += chipAmt;
  chipStack.push(chipAmt);
  document.getElementById('bet-display').textContent = '$' + currentBet.toLocaleString();
  renderChipStack();
}

function clearBet() {
  currentBet = 0;
  document.getElementById('bet-display').textContent = '$0';
  clearChipStack();
}

document.querySelectorAll('.chip').forEach(btn => {
  btn.onclick = () => { setChip(parseInt(btn.textContent.replace('$', ''))); addChip(); };
});

// ── Actions ───────────────────────────────────────────────────────────────────
async function deal() {
  if (currentBet === 0) return;
  const state = await api('/api/poker/deal', { bet: currentBet });
  if (state.error) { alert(state.error); return; }
  currentBet = 0;
  document.getElementById('bet-display').textContent = '$0';
  clearChipStack();
  lastRoundNets = {};
  communityCount = 0;

  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  document.getElementById('result-banner').textContent = '';
  document.getElementById('result-banner').className = 'result-banner';
  document.getElementById('hand-name').textContent = '';
  document.getElementById('pot-display').textContent = `Pot: $${state.pot.toLocaleString()}`;

  // Player cards first (0ms, 300ms)
  renderCards('player-cards', state.player_hole, false, true, 0);

  // Community cards after player cards finish (2 × 300ms + 200ms buffer = 800ms)
  const commDelay = 2 * 300 + 200;
  const commEl = document.getElementById('community-cards');
  commEl.innerHTML = '';
  (state.community || []).forEach(([rank, suit], i) => {
    const { wrap, inner } = makeFlipCard(rank, suit, false);
    commEl.appendChild(wrap);
    setTimeout(() => inner.classList.add('flipped'), commDelay + i * 300);
  });
  communityCount = (state.community || []).length;

  setControls(state.state);
  // AI cards face-down during play
  updateAIPanel(state.ai_players, state.bankroll, false, false, 0);
}

async function check() {
  const prevCount = communityCount;
  const state = await api('/api/poker/check', {});
  if (state.error) { alert(state.error); return; }
  lastRoundNets['You'] = state.net;
  (state.ai_players || []).forEach(ai => { lastRoundNets[ai.name] = ai.last_net; });

  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  document.getElementById('pot-display').textContent = '';
  document.getElementById('hand-name').textContent = state.player_hand_name || '';

  // Animate only the new community cards (turn + river)
  const newCards = (state.community || []).slice(prevCount);
  appendCards('community-cards', newCards, false, 0);
  communityCount = (state.community || []).length;

  // Show result after new cards finish flipping
  const resultDelay = newCards.length * 320 + 150;
  setTimeout(() => showResult(state), resultDelay);
  clearChipStack();

  setControls(state.state);

  // Reveal AI cards after result appears
  const aiDelay = resultDelay + 300;
  updateAIPanel(state.ai_players, state.bankroll, !!state.reveal_ai, true, aiDelay);
}

async function fold() {
  const state = await api('/api/poker/fold', {});
  if (state.error) { alert(state.error); return; }
  lastRoundNets['You'] = state.net;
  (state.ai_players || []).forEach(ai => { lastRoundNets[ai.name] = ai.last_net; });

  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  document.getElementById('pot-display').textContent = '';
  showResult(state);
  clearChipStack();
  setControls(state.state);
  // Reveal AI cards immediately (no animation on fold)
  updateAIPanel(state.ai_players, state.bankroll, true, false, 0);
}

// ── Render helpers ────────────────────────────────────────────────────────────
function setControls(stateStr) {
  const isBetting = stateStr === 'betting';
  document.getElementById('bet-controls').style.display   = isBetting ? 'flex' : 'none';
  document.getElementById('round-controls').style.display = !isBetting ? 'flex' : 'none';
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
    msg = netStr; cls = 'push';
  }
  banner.textContent = msg;
  banner.className = `result-banner ${cls}`;
}

function updateAIPanel(aiPlayers, bankroll, showCards, animate, baseDelay) {
  const container = document.getElementById('ai-cards-container');
  container.innerHTML = '';

  (aiPlayers || []).forEach(ai => {
    const card = document.createElement('div');
    card.className = 'ai-card';

    let statusLine = '';
    const aiChip = ai.bet > 0
      ? `<span class="ai-bet-chip" style="background:${chipColor(ai.bet)}">${chipLabel(ai.bet)}</span>`
      : '';
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
      <div class="ai-info">${aiChip} ${statusLine}</div>
      <div class="ai-cards-row" id="ai-hand-${ai.name}"></div>`;
    container.appendChild(card);

    const handEl = document.getElementById(`ai-hand-${ai.name}`);
    if (ai.hand && ai.hand.length) {
      ai.hand.forEach(([r, s], i) => {
        const isReal = r !== '?';
        const { wrap, inner } = makeFlipCard(r, s, true);
        handEl.appendChild(wrap);
        if (isReal && showCards) {
          // Flip to reveal: animated or instant
          if (animate) {
            setTimeout(() => inner.classList.add('flipped'), baseDelay + i * 280);
          } else {
            inner.classList.add('flipped');
          }
        }
        // Unknown or not revealed: stays face-down (card back visible)
      });
    }
  });

  // Last round
  const lrEl = document.getElementById('last-round');
  lrEl.innerHTML = '';
  ['You', ...(aiPlayers || []).map(a => a.name)].forEach(name => {
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
  const players = [['You', bankroll], ...(aiPlayers || []).map(a => [a.name, a.bankroll])];
  players.sort((a, b) => b[1] - a[1]);
  players.forEach(([name, br], i) => {
    const row = document.createElement('div');
    row.className = 'lb-row' + (name === 'You' ? ' you' : '');
    row.innerHTML = `<span>${i + 1}  ${name}</span><span>$${br.toLocaleString()}</span>`;
    lbEl.appendChild(row);
  });
}

// Full state render (used on init — no animation)
function render(state) {
  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  document.getElementById('pot-display').textContent = state.pot > 0 ? `Pot: $${state.pot.toLocaleString()}` : '';

  renderCards('player-cards',    state.player_hole, false, false);
  renderCards('community-cards', state.community,   false, false);
  communityCount = (state.community || []).length;

  document.getElementById('hand-name').textContent = state.player_hand_name || '';
  showResult(state);
  setControls(state.state);
  updateAIPanel(state.ai_players, state.bankroll,
    state.state !== 'betting' || !!state.reveal_ai, false, 0);
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
