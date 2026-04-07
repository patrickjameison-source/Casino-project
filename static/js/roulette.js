// ── State ─────────────────────────────────────────────────────────────────────
let chipAmt = 25;
const RED_NUMS  = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);
const BLACK_NUMS = new Set([2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]);
const recentResults = [];

function numColor(n) {
  if (n === 0) return 'green';
  return RED_NUMS.has(n) ? 'red' : 'black';
}

// ── API ───────────────────────────────────────────────────────────────────────
async function api(path, body = null) {
  const opts = body != null
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(path, opts);
  return r.json();
}

// ── Board construction ────────────────────────────────────────────────────────
// Standard layout: rows top=3,mid=2,bot=1; cols 1..12
// Row order on board: row3=[3,6,9,...36], row2=[2,5,8,...35], row1=[1,4,7,...34]
function buildBoard() {
  const grid = document.getElementById('board-numbers');
  grid.innerHTML = '';

  // Numbers: column-major (col 1 = 1,2,3; col 2 = 4,5,6 ...)
  // Display as 3 rows × 12 cols
  // row 0 (top):    3,  6,  9, 12, 15, 18, 21, 24, 27, 30, 33, 36
  // row 1 (middle): 2,  5,  8, 11, 14, 17, 20, 23, 26, 29, 32, 35
  // row 2 (bottom): 1,  4,  7, 10, 13, 16, 19, 22, 25, 28, 31, 34
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 12; col++) {
      const n = col * 3 + (3 - row);   // row0=+3, row1=+2, row2=+1
      const btn = document.createElement('button');
      btn.className = `num-cell ${numColor(n)}`;
      btn.textContent = n;
      btn.dataset.n = n;
      btn.onclick = () => placeBet(`n_${n}`, chipAmt);
      grid.appendChild(btn);
    }
  }
}

// ── Chip ─────────────────────────────────────────────────────────────────────
function setChip(amt) {
  chipAmt = amt;
  document.querySelectorAll('.chip').forEach(b => b.classList.remove('active'));
  // Mark active by looking at onclick content — simpler: store data-amt
  document.querySelectorAll('.chip').forEach(b => {
    if (parseInt(b.textContent.replace('$','')) === amt) b.classList.add('active');
  });
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function placeBet(betKey, amount) {
  const state = await api('/api/roulette/bet', { bet_key: betKey, amount });
  if (state.error) { alert(state.error); return; }
  renderBets(state);
}

async function clearBets() {
  const state = await api('/api/roulette/clear', {});
  renderBets(state);
}

async function spin() {
  const btn = document.getElementById('btn-spin');
  btn.disabled = true;
  const state = await api('/api/roulette/spin', {});
  btn.disabled = false;
  if (state.error) { alert(state.error); return; }
  renderSpin(state);
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderBets(state) {
  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  document.getElementById('total-bet').textContent = '$' + state.total_bet.toLocaleString();

  // Highlight active bet cells
  document.querySelectorAll('.num-cell, .outside-cell').forEach(el => el.classList.remove('active'));
  Object.keys(state.active_bets || {}).forEach(key => {
    if (key.startsWith('n_')) {
      document.querySelectorAll('.num-cell').forEach(el => {
        if (el.dataset.n == key.slice(2)) el.classList.add('active');
      });
    }
    // Outside bets: find by onclick text match — use data attribute instead
    document.querySelectorAll(`[data-key="${key}"]`).forEach(el => el.classList.add('active'));
  });

  // Bets summary
  const betsEl = document.getElementById('active-bets');
  const bets = state.active_bets || {};
  if (Object.keys(bets).length === 0) {
    betsEl.textContent = 'None';
  } else {
    betsEl.innerHTML = Object.entries(bets)
      .map(([k, v]) => `<span style="margin-right:8px;">${k}: <strong>$${v}</strong></span>`)
      .join('');
  }

  renderAI(state.ai_players, state.bankroll);
}

function renderSpin(state) {
  document.getElementById('bankroll').textContent = '$' + state.bankroll.toLocaleString();
  document.getElementById('total-bet').textContent = '$0';

  const n     = state.spin_result;
  const color = state.result_color;
  const net   = state.net;

  // Big result display
  const resultEl = document.getElementById('spin-result-display');
  resultEl.innerHTML = `
    <div class="spin-result-circle ${color}">
      <span>${n}</span>
      <span class="color-label">${color.charAt(0).toUpperCase() + color.slice(1)}</span>
    </div>`;

  const netEl = document.getElementById('net-display');
  const netStr = net > 0 ? `+$${net.toLocaleString()}` : net < 0 ? `-$${Math.abs(net).toLocaleString()}` : '$0';
  netEl.textContent = netStr;
  netEl.className = net > 0 ? 'text-win' : net < 0 ? 'text-loss' : 'text-muted';
  netEl.style.fontSize = '1.1rem';
  netEl.style.fontWeight = 'bold';

  // Recent results
  recentResults.unshift({ n, color });
  if (recentResults.length > 20) recentResults.pop();
  const recentEl = document.getElementById('recent-results');
  recentEl.innerHTML = '';
  recentResults.forEach(({ n: rn, color: rc }) => {
    const dot = document.createElement('div');
    dot.className = `res-dot ${rc}`;
    dot.textContent = rn;
    recentEl.appendChild(dot);
  });

  // Clear bet highlights
  document.querySelectorAll('.num-cell, .outside-cell').forEach(el => el.classList.remove('active'));
  document.getElementById('active-bets').textContent = 'None';

  renderAI(state.ai_players, state.bankroll);
  renderLeaderboard(state.ai_players, state.bankroll);
}

function renderAI(aiPlayers, bankroll) {
  const container = document.getElementById('ai-cards-container');
  container.innerHTML = '';
  (aiPlayers || []).forEach(ai => {
    const net = ai.last_net;
    const netStr = net == null ? '—'
      : net > 0 ? `+$${net.toLocaleString()}` : net < 0 ? `-$${Math.abs(net).toLocaleString()}` : '$0';
    const netClass = net > 0 ? 'text-win' : net < 0 ? 'text-loss' : 'text-muted';
    const card = document.createElement('div');
    card.className = 'ai-card';
    card.innerHTML = `
      <div class="ai-card-accent ${ai.personality}"></div>
      <div class="ai-name ${ai.personality}">${ai.name.toUpperCase()}</div>
      <div class="ai-bankroll">$${ai.bankroll.toLocaleString()}</div>
      <div class="ai-info"><span class="${netClass}">${netStr}</span></div>`;
    container.appendChild(card);
  });
  renderLeaderboard(aiPlayers, bankroll);
}

function renderLeaderboard(aiPlayers, bankroll) {
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
  await api('/api/roulette/leave', {});
  window.location.href = '/';
});

// ── Init ──────────────────────────────────────────────────────────────────────
buildBoard();

// Add data-key to outside cells for highlighting
document.querySelectorAll('.outside-cell').forEach(btn => {
  // Extract the bet key from the onclick string
  const match = btn.getAttribute('onclick')?.match(/placeBet\('([^']+)'/);
  if (match) btn.dataset.key = match[1];
});

setChip(25);
api('/api/roulette/state').then(state => renderBets(state));
