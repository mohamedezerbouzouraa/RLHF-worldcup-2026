let sidebarOpen = true;
let lastBotAnswer = '';
let lastUserQuestion = '';

document.addEventListener('DOMContentLoaded', () => {
  loadSidebar();
  checkModelStatus();
  showWelcome();
  document.getElementById('chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
});

async function loadSidebar() {
  try {
    const res = await fetch('/api/groups');
    const data = await res.json();
    const list = document.getElementById('group-list');
    list.innerHTML = '';
    Object.entries(data).forEach(([letter, teams]) => {
      const flags = teams.slice(0, 4).map(t => t.flag || '').join('');
      const btn = document.createElement('button');
      btn.className = 'group-item';
      btn.innerHTML = `<span class="grp-letter">G${letter}</span><span class="grp-flags">${flags}</span>`;
      btn.onclick = () => quickSend(`Groupe ${letter}`);
      list.appendChild(btn);
    });
  } catch (e) { console.error(e); }
}

async function checkModelStatus() {
  try {
    const res = await fetch('/api/model-status');
    const data = await res.json();
    const dot = document.getElementById('status-dot');
    const lbl = document.getElementById('status-label');
    const rlhf = document.getElementById('rlhf-count');
    if (data.loaded) {
      dot.classList.add('active');
      lbl.textContent = 'Llama 3.3 70B · Groq';
    } else {
      dot.classList.add('inactive');
      lbl.textContent = 'Mode Structuré';
    }
    if (rlhf) rlhf.textContent = `${data.rlhf_samples} feedbacks RLHF`;
  } catch (e) {}
}

function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  sidebarOpen = !sidebarOpen;
  if (window.innerWidth <= 768) sb.classList.toggle('open');
  else sb.classList.toggle('hidden');
}

function showWelcome() {
  const chips = [
    { label: '🇫🇷 Groupe I', msg: 'Groupe I' },
    { label: '🇦🇷 Groupe J', msg: 'Groupe J' },
    { label: '🇧🇷 Brésil', msg: 'Analyse le Brésil' },
    { label: '🇲🇦 Maroc', msg: 'Parle-moi du Maroc' },
    { label: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre', msg: "Analyse l'Angleterre" },
    { label: '📊 Tous les groupes', msg: 'Montre tous les groupes' },
    { label: '🏟️ Format 2026', msg: 'Explique le format de la Coupe du Monde 2026' },
    { label: '⭐ Favoris', msg: 'Qui sont les favoris pour gagner le Mondial 2026 ?' },
  ];
  const html = `<div class="welcome-banner">
    <div class="welcome-trophy">🏆</div>
    <div class="welcome-title">FIFA World Cup 2026</div>
    <div class="welcome-sub">Ton analyste IA — 48 équipes · 12 groupes · llama-3.3-70b-versatile<br>
    <span class="rlhf-badge">🧠 RLHF · Feedback Loop Actif</span></div>
    <div class="welcome-chips">${chips.map(c => `<button class="chip" onclick="quickSend('${c.msg}')">${c.label}</button>`).join('')}</div>
  </div>`;
  addBotMessage("<p>Bienvenue ! Je suis ton analyste IA de la <strong>Coupe du Monde 2026</strong>. Pose-moi n'importe quelle question !</p>", html);
}

function quickSend(text) {
  document.getElementById('chat-input').value = text;
  sendMessage();
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addUserMessage(text);
  showTyping();
  lastUserQuestion = text;
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    removeTyping();
    lastBotAnswer = data.answer;
    let cardHTML = '';
    if (data.context_type === 'team' && data.raw_data) {
      cardHTML = buildTeamCard(data.raw_data, data.context_id);
    } else if (data.context_type === 'group' && data.raw_data) {
      cardHTML = buildGroupCard(data.raw_data, data.context_id);
    }
    addBotMessage(formatBotText(data.answer), cardHTML);
    addFeedbackBar();
  } catch (e) {
    removeTyping();
    addBotMessage("<p>Erreur de communication avec le serveur.</p>");
  }
}

function formatBotText(txt) {
  if (!txt) return '';
  let html = txt.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>');
  html = `<p>${html}</p>`;
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/<\/p><p>\s*-\s*/g, '<ul><li>');
  return html;
}

function buildTeamCard(raw, teamName) {
  const lines = raw.split('\n');
  let rank = '', coach = '', style = '', fact = '';
  lines.forEach(l => {
    if (l.includes('Rang FIFA')) rank = l.split(':')[1].trim();
    if (l.includes('Selectionneur')) coach = l.split(':')[1].trim();
    if (l.includes('Style de jeu')) style = l.split(':')[1].trim();
    if (l.includes('Anecdote')) fact = l.split(':')[1].trim();
  });
  return `<div class="wc-card">
    <div class="card-header">📊 Fiche Technique : ${teamName}</div>
    <div class="card-grid">
      <div class="card-item"><span class="card-lbl">Rang FIFA</span><span class="card-val">${rank || 'NC'}</span></div>
      <div class="card-item"><span class="card-lbl">Sélectionneur</span><span class="card-val">${coach || 'NC'}</span></div>
      <div class="card-item" style="grid-column: span 2;"><span class="card-lbl">Style de jeu</span><span class="card-val">${style || 'NC'}</span></div>
      ${fact ? `<div class="card-fact">${fact}</div>` : ''}
    </div>
  </div>`;
}

function buildGroupCard(raw, letter) {
  const lines = raw.split('\n');
  let teamsLine = '';
  lines.forEach(l => { if (l.includes('Equipes :')) teamsLine = l.split(':')[1].trim(); });
  const teams = teamsLine.split(',').map(t => t.trim());
  return `<div class="wc-card">
    <div class="card-header">🏆 Composition Groupe ${letter}</div>
    <div style="display:flex; flex-direction:column; gap:4px; margin-top:4px;">
      ${teams.map((t, i) => `<div style="display:flex; justify-content:space-between; font-size:13px; padding:4px 0; border-bottom:1px solid var(--border); font-weight:500;">
        <span>${i + 1}. ${t}</span>
      </div>`).join('')}
    </div>
  </div>`;
}

function addUserMessage(text) {
  const win = document.getElementById('chat-window');
  const w = document.createElement('div');
  w.className = 'msg-wrap user';
  w.innerHTML = `<div class="avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg></div>
    <div class="bubble user"><p>${escHtml(text)}</p></div>`;
  win.appendChild(w);
  win.scrollTop = win.scrollHeight;
}

function addBotMessage(textHTML, cardHTML = '') {
  const win = document.getElementById('chat-window');
  const w = document.createElement('div');
  w.className = 'msg-wrap bot';
  w.innerHTML = `<div class="avatar">⚽</div><div class=\"bubble bot\">${textHTML}${cardHTML}</div>`;
  win.appendChild(w);
  win.scrollTop = win.scrollHeight;
}

function showTyping() {
  const win = document.getElementById('chat-window');
  const w = document.createElement('div');
  w.className = 'msg-wrap bot'; w.id = 'typing';
  w.innerHTML = `<div class="avatar">⚽</div><div class="bubble bot typing-bubble">
    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    <span class="typing-label">Llama 3.3 analyse...</span></div>`;
  win.appendChild(w);
  win.scrollTop = win.scrollHeight;
}

function removeTyping() { const el = document.getElementById('typing'); if (el) el.remove(); }

function escHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function addFeedbackBar() {
  const bubbles = document.querySelectorAll('.bubble.bot');
  if (!bubbles.length) return;
  const lastBubble = bubbles[bubbles.length - 1];
  if (lastBubble.querySelector('.rlhf-bar')) return;
  const bar = document.createElement('div');
  bar.className = 'rlhf-bar';
  const q = lastUserQuestion;
  const a = lastBotAnswer;
  bar.innerHTML = `
    <span class="rlhf-label">Cette analyse est-elle correcte ?</span>
    <button class="rlhf-btn" data-score="1">👍</button>
    <button class="rlhf-btn" data-score="0">👎</button>
  `;
  bar.querySelectorAll('.rlhf-btn').forEach(btn => {
    btn.onclick = async () => {
      const score = parseInt(btn.getAttribute('data-score'));
      bar.innerHTML = '<span class="rlhf-thanks">Merci pour votre feedback ! (Loop RLHF mis à jour)</span>';
      try {
        await fetch('/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, answer: a, score: score, comment: '' })
        });
        checkModelStatus();
      } catch (e) { console.error(e); }
    };
  });
  lastBubble.appendChild(bar);
  document.getElementById('chat-window').scrollTop = document.getElementById('chat-window').scrollHeight;
}
