
const API_BASE = 'http://localhost:5000';

// ── DOM refs ──────────────────────────────────────────────
const newsInput  = document.getElementById('news-input');
const charCount  = document.getElementById('char-count');
const checkBtn   = document.getElementById('check-btn');
const loading    = document.getElementById('loading');
const progressBar= document.getElementById('progress-bar');
const stepTxt    = document.getElementById('step-txt');
const resultBox  = document.getElementById('result-box');
const errBox     = document.getElementById('err-box');
const errMsg     = document.getElementById('err-msg');
const scoreArc   = document.getElementById('score-arc');
const scoreLabel = document.getElementById('score-label');
const verdictChip= document.getElementById('verdict-chip');
const verdictDesc= document.getElementById('verdict-desc');
const contextTxt = document.getElementById('context-text');
const srcList    = document.getElementById('sources-list');
const summaryTxt = document.getElementById('summary-text');

// ── Char counter ──────────────────────────────────────────
newsInput.addEventListener('input', () => {
  const n = newsInput.value.length;
  charCount.textContent = `${n} / 2000`;
  charCount.style.color = n > 1800 ? 'var(--amber)' : '';
});

// ── Main action ───────────────────────────────────────────
async function checkNews() {
  const text = newsInput.value.trim();
  if (!text || text.length < 8) {
    showError('Please enter a longer headline or article excerpt.');
    return;
  }

  clearResults();
  setLoading(true);
  checkBtn.disabled = true;

  try {
    const data = await fetchResult(text);
    renderResult(data);
  } catch (e) {
    showError(e.message || 'Could not reach the server. Is your Python backend running?');
  } finally {
    setLoading(false);
    checkBtn.disabled = false;
  }
}

// ── API call ──────────────────────────────────────────────
async function fetchResult(text) {
  const res  = await fetch(`${API_BASE}/api/check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);
  return data;
}

// ── Render ────────────────────────────────────────────────
function renderResult({ score, verdict, context, summary, sources }) {
  resultBox.style.display = 'block';

  // Score ring  (circumference = 2π × 32 ≈ 201)
  const pct    = Math.min(Math.max(Number(score) || 0, 0), 100);
  const offset = 201 - (201 * pct / 100);
  scoreArc.style.strokeDashoffset = offset;

  const ringColor = pct >= 65 ? '#4ade80' : pct >= 35 ? '#fbbf24' : '#f87171';
  scoreArc.style.stroke = ringColor;
  scoreLabel.textContent = `${pct}%`;

  // Verdict chip
  const verdictMap = {
    high:   { label: '✔ Likely Credible',    desc: 'This content closely aligns with verified reporting. Apply normal media literacy.' },
    medium: { label: '⚠ Needs Verification', desc: 'Some claims match verified sources, but context may be incomplete or distorted.' },
    low:    { label: '✘ Possibly Misleading', desc: 'This content significantly diverges from verified sources. Treat with caution.' }
  };
  const v = verdictMap[verdict] || verdictMap.medium;
  verdictChip.textContent  = v.label;
  verdictChip.className    = `verdict-chip ${verdict || 'medium'}`;
  verdictDesc.textContent  = v.desc;

  // Tab content
  contextTxt.textContent = context || 'No contextual information returned.';
  summaryTxt.textContent = summary || 'No summary returned.';

  srcList.innerHTML = '';
  const srcs = Array.isArray(sources) ? sources : [];
  if (srcs.length) {
    srcs.forEach(s => {
      const li   = document.createElement('li');
      const meta = [s.publisher, s.date].filter(Boolean).join(' · ');
      li.innerHTML = `
        <span class="src-dot"></span>
        <div>
          <a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>
          ${meta ? `<div class="src-meta">${esc(meta)}</div>` : ''}
        </div>`;
      srcList.appendChild(li);
    });
  } else {
    srcList.innerHTML = '<li style="color:var(--muted);font-size:.86rem">No sources returned.</li>';
  }

  switchTab(document.querySelector('.tab[data-tab="context"]'), 'context');
}

// ── Tabs ──────────────────────────────────────────────────
function switchTab(el, id) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
  el.classList.add('active');
  document.getElementById('tab-' + id).classList.remove('hidden');
}

// ── Loading animation ─────────────────────────────────────
const STEPS = [
  'Embedding input…',
  'Searching vector database…',
  'Retrieving verified sources…',
  'Generating credibility report…'
];
const WIDTHS = ['18%', '42%', '68%', '90%'];
let stepTimer, stepIdx = 0;

function setLoading(on) {
  loading.style.display = on ? 'flex' : 'none';
  if (on) {
    stepIdx = 0;
    stepTxt.textContent    = STEPS[0];
    progressBar.style.width = WIDTHS[0];
    stepTimer = setInterval(() => {
      stepIdx = Math.min(stepIdx + 1, STEPS.length - 1);
      stepTxt.textContent    = STEPS[stepIdx];
      progressBar.style.width = WIDTHS[stepIdx];
    }, 1800);
  } else {
    clearInterval(stepTimer);
    progressBar.style.width = '0%';
  }
}

// ── Helpers ───────────────────────────────────────────────
function showError(msg) {
  errMsg.textContent    = msg;
  errBox.style.display  = 'flex';
}

function clearResults() {
  resultBox.style.display = 'none';
  errBox.style.display    = 'none';
  scoreArc.style.strokeDashoffset = '201';
}

function clearAll() {
  newsInput.value        = '';
  charCount.textContent  = '0 / 2000';
  clearResults();
  setLoading(false);
}

function esc(str) {
  return String(str || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Keyboard shortcut ─────────────────────────────────────
// ── Keyboard shortcut ─────────────────────────────────────
newsInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    checkNews();
  }
  // Shift+Enter = new line (default browser behavior)
});