// ── Constants ─────────────────────────────────────────────────────────────────
const WHEEL_ORDER = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
const RED_NUMS    = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);

let chipAmt = 25;
let wheelRotation = 0;
let spinning = false;
let currentActiveBets = {};   // player's current bets — tracked for chip display
const recentResults = [];

// ── Chip colour helpers ───────────────────────────────────────────────────────
function chipColor(amount) {
  if (amount >= 500) return '#c8a84b';
  if (amount >= 100) return '#5b2c6f';
  if (amount >= 50)  return '#b9770e';
  if (amount >= 25)  return '#1a7a40';
  if (amount >= 10)  return '#1f618d';
  return '#a93226';
}
function chipLabel(amount) {
  return amount >= 1000 ? Math.round(amount / 1000) + 'k' : amount;
}

const AI_CHIP_COLOR = { aggressive: '#c0392b', moderate: '#2471a3', conservative: '#1a7a40' };
const AI_PERSONALITY_ORDER = ['aggressive', 'moderate', 'conservative'];

// ── Table chip rendering ──────────────────────────────────────────────────────
function clearTableChips() {
  document.querySelectorAll('.table-chip').forEach(el => el.remove());
}

function showTableChips(activeBets, aiBets) {
  clearTableChips();

  // Player chips — centred on each bet cell
  Object.entries(activeBets || {}).forEach(([key, amount]) => {
    document.querySelectorAll(`[data-key="${key}"]`).forEach(cell => {
      const chip = document.createElement('div');
      chip.className = 'table-chip table-chip-player';
      chip.style.background = chipColor(amount);
      chip.textContent = chipLabel(amount);
      cell.appendChild(chip);
    });
  });

  // AI chips — small, in fixed corners based on personality order
  Object.entries(aiBets || {}).forEach(([name, bet]) => {
    const posIdx = AI_PERSONALITY_ORDER.indexOf(bet.personality);
    const pos    = posIdx >= 0 ? posIdx : 0;
    document.querySelectorAll(`[data-key="${bet.bet_key}"]`).forEach(cell => {
      const chip = document.createElement('div');
      chip.className = `table-chip table-chip-ai ai-pos-${pos}`;
      chip.style.background = AI_CHIP_COLOR[bet.personality] || '#555';
      chip.title = `${name}: $${bet.amount}`;
      chip.textContent = name.charAt(0);
      cell.appendChild(chip);
    });
  });
}

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

// ── Wheel drawing ─────────────────────────────────────────────────────────────
const canvas = document.getElementById('wheel-canvas');
const ctx    = canvas.getContext('2d');
const CX = canvas.width  / 2;
const CY = canvas.height / 2;
const R  = CX - 4;

function drawWheel(rotation, highlightIdx = -1, bAngle = -Math.PI / 2, bRadius = null) {
  if (bRadius === null) bRadius = R * 0.93;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const seg = (2 * Math.PI) / 37;

  // Outer ring
  ctx.beginPath();
  ctx.arc(CX, CY, R + 3, 0, 2 * Math.PI);
  ctx.fillStyle = '#8B7536';
  ctx.fill();

  for (let i = 0; i < 37; i++) {
    const n     = WHEEL_ORDER[i];
    const start = rotation + i * seg - Math.PI / 2;
    const end   = start + seg;

    ctx.beginPath();
    ctx.moveTo(CX, CY);
    ctx.arc(CX, CY, R, start, end);
    ctx.closePath();

    if (i === highlightIdx)      ctx.fillStyle = '#f5d020';
    else if (n === 0)            ctx.fillStyle = '#1a7a40';
    else if (RED_NUMS.has(n))    ctx.fillStyle = '#c0392b';
    else                         ctx.fillStyle = '#1c1c1c';

    ctx.fill();
    ctx.strokeStyle = '#555';
    ctx.lineWidth = 0.5;
    ctx.stroke();

    // Number label
    const mid = start + seg / 2;
    const tx  = CX + R * 0.72 * Math.cos(mid);
    const ty  = CY + R * 0.72 * Math.sin(mid);
    ctx.save();
    ctx.translate(tx, ty);
    ctx.rotate(mid + Math.PI / 2);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 8px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(n.toString(), 0, 0);
    ctx.restore();
  }

  // Center hub
  ctx.beginPath();
  ctx.arc(CX, CY, R * 0.14, 0, 2 * Math.PI);
  ctx.fillStyle = '#8B7536';
  ctx.fill();
  ctx.beginPath();
  ctx.arc(CX, CY, R * 0.09, 0, 2 * Math.PI);
  ctx.fillStyle = '#c8a84b';
  ctx.fill();

  // White ball
  const bx = CX + bRadius * Math.cos(bAngle);
  const by = CY + bRadius * Math.sin(bAngle);

  // Shadow
  ctx.beginPath();
  ctx.arc(bx + 1.5, by + 1.5, 5, 0, 2 * Math.PI);
  ctx.fillStyle = 'rgba(0,0,0,0.45)';
  ctx.fill();

  // Ball with radial gradient for 3-D look
  const grad = ctx.createRadialGradient(bx - 1.5, by - 1.5, 0.5, bx, by, 5);
  grad.addColorStop(0, '#ffffff');
  grad.addColorStop(1, '#bbbbbb');
  ctx.beginPath();
  ctx.arc(bx, by, 5, 0, 2 * Math.PI);
  ctx.fillStyle = grad;
  ctx.fill();
  ctx.strokeStyle = '#999';
  ctx.lineWidth = 0.5;
  ctx.stroke();
}

function spinTo(resultNum, callback) {
  const idx = WHEEL_ORDER.indexOf(resultNum);
  const seg = (2 * Math.PI) / 37;

  // Wheel: stops at a RANDOM position (not aligned to any specific number at top).
  // This makes the wheel feel physically independent of the result.
  const wheelSpins  = 5 + Math.floor(Math.random() * 4);          // 5–8 full laps
  const randomStop  = Math.random() * 2 * Math.PI;                 // random stopping angle
  const endRot      = wheelRotation - (wheelRotation % (2 * Math.PI))
                    - (2 * Math.PI * wheelSpins) + randomStop;
  const startRot    = wheelRotation;

  // Calculate where the center of the winning pocket will be on screen once the wheel stops.
  // Segment idx centre = endRot + idx*seg − π/2 + seg/2
  const pocketAngle = endRot + idx * seg - Math.PI / 2 + seg / 2;

  // Ball: clockwise (opposite to wheel), makes 10–14 extra laps then ends
  // precisely at pocketAngle — wherever that happens to be around the wheel.
  const ballSpins = 10 + Math.floor(Math.random() * 5);
  const ballStart = -Math.PI / 2;  // ball begins at 12 o'clock

  // Clockwise distance from ballStart to pocketAngle
  let cwDist = ((pocketAngle - ballStart) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI);
  if (cwDist < 0.01) cwDist = 2 * Math.PI;  // avoid near-zero jump
  const ballEndAngle = ballStart + 2 * Math.PI * ballSpins + cwDist;

  const ballOuterR  = R * 0.93;  // outer track groove
  const ballPocketR = R * 0.81;  // resting inside the numbered pocket

  const duration = 4500;
  const startTs  = performance.now();

  // Wheel uses quartic, ball uses cubic — different deceleration rates make
  // them feel like separate physical objects moving against each other.
  function easeWheel(t) { return 1 - Math.pow(1 - t, 4); }
  function easeBall(t)  { return 1 - Math.pow(1 - t, 3); }

  function frame(now) {
    const t = Math.min((now - startTs) / duration, 1);

    const rot    = startRot + (endRot - startRot) * easeWheel(t);
    const bAngle = ballStart + (ballEndAngle - ballStart) * easeBall(t);

    // Ball drops from outer groove into the pocket over the last 25 % of the spin
    const fallT   = Math.max(0, (t - 0.75) / 0.25);
    const bRadius = ballOuterR + (ballPocketR - ballOuterR) * fallT;

    drawWheel(rot, t > 0.97 ? idx : -1, bAngle, bRadius);

    if (t < 1) {
      requestAnimationFrame(frame);
    } else {
      wheelRotation = endRot;
      // Final frame: ball sitting in the winning pocket wherever it landed
      drawWheel(endRot, idx, pocketAngle, ballPocketR);
      callback();
    }
  }
  requestAnimationFrame(frame);
}

// ── Board ─────────────────────────────────────────────────────────────────────
function buildBoard() {
  const grid = document.getElementById('board-numbers');
  grid.innerHTML = '';
  // 3 rows × 12 cols: row0=top (multiples of 3), row1=mid, row2=bottom
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 12; col++) {
      const n   = col * 3 + (3 - row);
      const btn = document.createElement('button');
      btn.className       = `num-cell ${numColor(n)}`;
      btn.textContent     = n;
      btn.dataset.n       = n;
      btn.dataset.key     = `n_${n}`;
      btn.onclick         = () => placeBet(`n_${n}`, chipAmt);
      grid.appendChild(btn);
    }
  }
}

// ── Chip ─────────────────────────────────────────────────────────────────────
function setChip(amt) {
  chipAmt = amt;
  document.querySelectorAll('.chip').forEach(b => {
    b.classList.toggle('active', parseInt(b.textContent.replace('$','')) === amt);
  });
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function placeBet(betKey, amount) {
  if (spinning) return;
  const state = await api('/api/roulette/bet', { bet_key: betKey, amount });
  if (state.error) { alert(state.error); return; }
  renderBets(state);
}

async function clearBets() {
  if (spinning) return;
  const state = await api('/api/roulette/clear', {});
  renderBets(state);
}

async function spin() {
  if (spinning) return;
  spinning = true;
  document.getElementById('btn-spin').disabled = true;

  // Save player bets before the API call clears them server-side
  const betsAtSpin = { ...currentActiveBets };

  const state = await api('/api/roulette/spin', {});
  if (state.error) {
    alert(state.error);
    spinning = false;
    document.getElementById('btn-spin').disabled = false;
    return;
  }

  // Show player chips + AI chips on the table while the wheel spins
  showTableChips(betsAtSpin, state.ai_bets);

  spinTo(state.spin_result, () => {
    clearTableChips();
    spinning = false;
    document.getElementById('btn-spin').disabled = false;
    renderSpin(state);
  });
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderBets(state) {
  currentActiveBets = state.active_bets || {};

  document.getElementById('bankroll').textContent  = '$' + state.bankroll.toLocaleString();
  document.getElementById('total-bet').textContent = '$' + state.total_bet.toLocaleString();

  document.querySelectorAll('.num-cell, .outside-cell').forEach(el => el.classList.remove('active'));
  Object.keys(currentActiveBets).forEach(key => {
    document.querySelectorAll(`[data-key="${key}"]`).forEach(el => el.classList.add('active'));
  });

  // Show player chips on table
  showTableChips(currentActiveBets, {});

  const bets   = currentActiveBets;
  const betsEl = document.getElementById('active-bets');
  if (Object.keys(bets).length === 0) {
    betsEl.textContent = 'None';
  } else {
    betsEl.innerHTML = Object.entries(bets)
      .map(([k,v]) => `<span style="margin-right:8px">${k}: <strong>$${v}</strong></span>`)
      .join('');
  }
  renderAI(state.ai_players, state.bankroll);
}

function renderSpin(state) {
  document.getElementById('bankroll').textContent  = '$' + state.bankroll.toLocaleString();
  document.getElementById('total-bet').textContent = '$0';

  const n     = state.spin_result;
  const color = state.result_color;
  const net   = state.net;

  // Result label under wheel
  const label = { red:'Red', black:'Black', green:'Green' }[color];
  document.getElementById('spin-result-display').innerHTML =
    `<strong style="font-size:1.1rem;color:${color==='red'?'#e74c3c':color==='green'?'#4caf50':'#aaa'}">${n}</strong> &nbsp;${label}`;

  const netEl  = document.getElementById('net-display');
  const netStr = net > 0 ? `+$${net.toLocaleString()}` : net < 0 ? `-$${Math.abs(net).toLocaleString()}` : '$0';
  netEl.textContent = netStr;
  netEl.style.color = net > 0 ? '#4caf50' : net < 0 ? '#e74c3c' : '#777';

  // Recent dots
  recentResults.unshift({ n, color });
  if (recentResults.length > 18) recentResults.pop();
  const recentEl = document.getElementById('recent-results');
  recentEl.innerHTML = '';
  recentResults.forEach(({ n: rn, color: rc }) => {
    const dot = document.createElement('div');
    dot.className   = `res-dot ${rc}`;
    dot.textContent = rn;
    recentEl.appendChild(dot);
  });

  document.querySelectorAll('.num-cell, .outside-cell').forEach(el => el.classList.remove('active'));
  document.getElementById('active-bets').textContent = 'None';

  renderAI(state.ai_players, state.bankroll);
}

function renderAI(aiPlayers, bankroll) {
  const container = document.getElementById('ai-cards-container');
  container.innerHTML = '';
  (aiPlayers || []).forEach(ai => {
    const net    = ai.last_net;
    const netStr = net == null ? '—'
      : net > 0 ? `+$${net.toLocaleString()}` : net < 0 ? `-$${Math.abs(net).toLocaleString()}` : '$0';
    const cls    = net > 0 ? 'text-win' : net < 0 ? 'text-loss' : 'text-muted';
    const card   = document.createElement('div');
    card.className = 'ai-card';
    card.innerHTML = `
      <div class="ai-card-accent ${ai.personality}"></div>
      <div class="ai-name ${ai.personality}">${ai.name.toUpperCase()}</div>
      <div class="ai-bankroll">$${ai.bankroll.toLocaleString()}</div>
      <div class="ai-info"><span class="${cls}">${netStr}</span></div>`;
    container.appendChild(card);
  });

  // Leaderboard
  const lbEl   = document.getElementById('leaderboard');
  lbEl.innerHTML = '';
  const players = [['You', bankroll], ...(aiPlayers||[]).map(a => [a.name, a.bankroll])];
  players.sort((a,b) => b[1] - a[1]);
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

// Attach data-key to outside cells for highlight matching
document.querySelectorAll('.outside-cell').forEach(btn => {
  const m = btn.getAttribute('onclick')?.match(/placeBet\('([^']+)'/);
  if (m) btn.dataset.key = m[1];
});

setChip(25);
drawWheel(0);
api('/api/roulette/state').then(renderBets);
