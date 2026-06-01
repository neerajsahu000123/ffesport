/* ============================================================
   ESPORTS ARCHIVE — SHARED APP JAVASCRIPT
   Flask API Layer + UI Components + Auth (NO localStorage)
   ============================================================ */

// ── ROOT PATH ───────────────────────────────────────────────
let ROOT = '';
(function detectRoot() {
  if (window.location.pathname.includes('/admin/')) ROOT = '../';
})();

// ── API BASE ─────────────────────────────────────────────────
const API = ROOT + '';   // Flask serves from same origin

/* ============================================================
   Api — replaces DB object (all localStorage removed)
   ============================================================ */
const Api = {
  async getAll(entity) {
    try {
      const res = await fetch(`${API}api/${entity}`);
      if (!res.ok) return [];
      return await res.json();
    } catch { return []; }
  },

  async getById(entity, id) {
    try {
      const res = await fetch(`${API}api/${entity}/${id}`);
      if (!res.ok) return null;
      return await res.json();
    } catch { return null; }
  },

  async add(entity, record) {
    const res = await fetch(`${API}api/${entity}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record)
    });
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  },

  async update(entity, record) {
    const res = await fetch(`${API}api/${entity}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record)
    });
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  },

  async delete(entity, id) {
    const res = await fetch(`${API}api/${entity}?id=${encodeURIComponent(id)}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  },

  async getSettings() {
    const s = await this.getAll('settings');
    return Array.isArray(s) ? {} : s;
  },

  async saveSettings(data) {
    const res = await fetch(`${API}api/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.ok;
  },

  async getMedia() {
    try {
      const res = await fetch(`${API}api/media`);
      if (!res.ok) return { teamLogos:{}, playerImages:{}, tournamentBanners:{}, articleImages:{} };
      const data = await res.json();
      return Array.isArray(data)
        ? { teamLogos:{}, playerImages:{}, tournamentBanners:{}, articleImages:{} }
        : data;
    } catch { return { teamLogos:{}, playerImages:{}, tournamentBanners:{}, articleImages:{} }; }
  },

  async saveMedia(mediaObj) {
    await fetch(`${API}api/media`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mediaObj)
    });
  },

  async getStats() {
    try {
      const res = await fetch(`${API}api/stats`);
      return res.ok ? await res.json() : {};
    } catch { return {}; }
  }
};

// ── AUTH LAYER (Flask sessions, no localStorage) ─────────────
const Auth = {
  _session: null,

  async login(username, password) {
    const res = await fetch(`${API}api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) return false;
    this._session = await res.json();
    return true;
  },

  async logout() {
    await fetch(`${API}api/logout`, { method: 'POST' });
    this._session = null;
    window.location.href = ROOT + 'index.html';
  },

  async getSession() {
    if (this._session !== null) return this._session;
    try {
      const res = await fetch(`${API}api/session`);
      this._session = res.ok ? await res.json() : { loggedIn: false };
    } catch { this._session = { loggedIn: false }; }
    return this._session;
  },

  async isLoggedIn() {
    const s = await this.getSession();
    return !!(s && s.loggedIn);
  },

  async isAdmin() {
    const s = await this.getSession();
    return !!(s && s.loggedIn && s.role === 'admin');
  },

  async requireAdmin() {
    if (!await this.isAdmin()) {
      window.location.href = ROOT + 'login.html?redirect=admin';
    }
  }
};

// ── NAVIGATION RENDERER ─────────────────────────────────────
async function renderNav(activePage) {
  const session = await Auth.getSession();
  const isLoggedIn = !!(session && session.loggedIn);

  const navLinks = [
    { href: ROOT + 'tournaments.html', label: 'Tournaments', key: 'tournaments' },
    { href: ROOT + 'teams.html',       label: 'Teams',       key: 'teams' },
    { href: ROOT + 'players.html',     label: 'Players',     key: 'players' },
    { href: ROOT + 'timeline.html',    label: 'Timeline',    key: 'timeline' },
    { href: ROOT + 'articles.html',    label: 'Articles',    key: 'articles' },
    { href: ROOT + 'upcoming.html',    label: 'Upcoming Events', key: 'upcoming' },
  ];

  const linksHTML = navLinks.map(l =>
    `<li><a href="${l.href}" class="${activePage === l.key ? 'active' : ''}">${l.label}</a></li>`
  ).join('');

  const rightHTML = isLoggedIn
    ? `<span class="nav-user-badge"><span class="nav-user-dot"></span>${session.displayName || session.username}</span>
       <button class="btn-outline btn-sm" onclick="Auth.logout()">Logout</button>
       <a href="${ROOT}admin/dashboard.html" class="btn-primary btn-sm">Dashboard</a>`
    : `<a href="${ROOT}login.html" class="nav-login-btn">Login</a>`;

  const navHTML = `
<nav>
  <a href="${ROOT}index.html" class="nav-logo">
    <div class="nav-logo-icon"></div>
    <div class="nav-logo-text">
      <span class="brand">ESPORTS ARCHIVE</span>
      <span class="sub">Indian Free Fire Esports Database</span>
    </div>
  </a>
  <ul class="nav-center">${linksHTML}</ul>
  <div class="nav-right">
    <div class="nav-search-wrap" style="position:relative;">
      <input class="nav-search-input" id="navSearchInput" type="text" placeholder="Search..." onkeydown="if(event.key==='Enter')navSearchGo()" oninput="navSearchSuggest(this.value)" autocomplete="off">
      <div class="nav-search-dropdown" id="navSearchDropdown"></div>
    </div>
    ${rightHTML}
  </div>
  <button class="nav-mobile-btn" onclick="toggleMobileMenu()" aria-label="Menu">☰</button>
</nav>
<div class="mobile-menu" id="mobileMenu">
  ${navLinks.map(l => `<a href="${l.href}">${l.label}</a>`).join('')}
  ${isLoggedIn
    ? `<a href="${ROOT}admin/dashboard.html">Admin Dashboard</a><a href="#" onclick="Auth.logout()">Logout</a>`
    : `<a href="${ROOT}login.html">Login</a>`}
</div>`;

  const navEl = document.querySelector('nav');
  if (navEl) navEl.outerHTML = navHTML;
  else document.body.insertAdjacentHTML('afterbegin', navHTML);
}

function toggleMobileMenu() { document.getElementById('mobileMenu')?.classList.toggle('open'); }

// ── FOOTER RENDERER ──────────────────────────────────────────
function renderFooter() {
  const footerHTML = `
<footer>
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="${ROOT}index.html" class="nav-logo" style="margin-bottom:.5rem;">
          <div class="nav-logo-icon"></div>
          <div class="nav-logo-text">
            <span class="brand">ESPORTS ARCHIVE</span>
            <span class="sub">Indian Free Fire Esports Database</span>
          </div>
        </a>
        <p>The definitive historical archive for Free Fire esports in India. Preserving tournaments, teams, players, and competitive milestones since 2019.</p>
      </div>
      <div class="footer-col">
        <h4>Archive</h4>
        <ul>
          <li><a href="${ROOT}tournaments.html">All Tournaments</a></li>
          <li><a href="${ROOT}timeline.html">Historical Timeline</a></li>
          <li><a href="${ROOT}articles.html">Articles</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Database</h4>
        <ul>
          <li><a href="${ROOT}teams.html">Team Database</a></li>
          <li><a href="${ROOT}players.html">Player Profiles</a></li>
          <li><a href="${ROOT}upcoming.html">Upcoming Events</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>More</h4>
        <ul>
          <li><a href="${ROOT}timeline.html">Timeline</a></li>
          <li><a href="${ROOT}articles.html">Articles</a></li>
          <li><a href="${ROOT}upcoming.html">Upcoming Events</a></li>
          <li><a href="${ROOT}login.html">Admin Login</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2025 Esports Archive · Indian Free Fire Esports Historical Database · All records are independently documented</p>
      <p class="footer-note">Free Fire is a registered trademark of Garena International I Private Limited. This is an independent fan archive and is not affiliated with or endorsed by Garena.</p>
    </div>
  </div>
</footer>`;

  const existing = document.querySelector('footer');
  if (existing) existing.outerHTML = footerHTML;
  else document.body.insertAdjacentHTML('beforeend', footerHTML);
}

// ── FADE-IN OBSERVER ─────────────────────────────────────────
function initFadeIn() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
  }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
}

// ── TOAST ────────────────────────────────────────────────────
function showToast(message, type = '') {
  let toast = document.getElementById('ea-toast');
  if (!toast) { toast = document.createElement('div'); toast.id = 'ea-toast'; toast.className = 'toast'; document.body.appendChild(toast); }
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove('show'), 3500);
}

// ── HELPERS ──────────────────────────────────────────────────
function getParam(name) { return new URLSearchParams(window.location.search).get(name); }

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try { return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }); }
  catch { return dateStr; }
}

function getMonthName(dateStr) {
  if (!dateStr) return '';
  try { return new Date(dateStr).toLocaleDateString('en-IN', { month: 'short' }).toUpperCase(); }
  catch { return ''; }
}

function getDayNum(dateStr) {
  if (!dateStr) return '';
  try { return new Date(dateStr).getDate().toString().padStart(2, '0'); }
  catch { return ''; }
}

function generateId(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '-' + Date.now().toString(36);
}

function getTypeClass(type) {
  const map = { championship:'type-championship', tournament:'type-tournament', 'team-creation':'type-team-creation', 'team-disband':'type-team-disband', transfer:'type-transfer', announcement:'type-announcement', launch:'type-launch' };
  return map[type] || 'type-announcement';
}

function getDotClass(type) {
  if (['championship', 'launch'].includes(type)) return 'gold';
  if (['tournament', 'team-creation'].includes(type)) return 'fire';
  return '';
}

function getStatusClass(status) {
  if (status === 'active') return 'status-active';
  if (status === 'inactive') return 'status-inactive';
  if (status === 'disbanded') return 'status-disbanded';
  return '';
}

function getRegStatusClass(status) {
  if (status === 'open') return 'status-reg-open';
  if (status === 'announced') return 'status-announced';
  return 'status-tba';
}

function getRegStatusLabel(status) {
  if (status === 'open') return 'Reg. Open';
  if (status === 'announced') return 'Announced';
  return 'TBA';
}

// Sync logo helpers (no media fetch, for list renders)
function teamLogoHTMLSync(team, size = 64) {
  const initials = (team.shortName || team.name.substring(0, 3)).substring(0, 3);
  return `<div class="team-logo" style="width:${size}px;height:${size}px;background:${team.logoColor||'#FF4A00'}22;border:2px solid ${team.logoColor||'#FF4A00'}44;font-size:${Math.round(size*0.35)}px;">${initials}</div>`;
}

function playerAvatarHTMLSync(player, size = 52) {
  const initials = (player.ign || '?').substring(0, 2).toUpperCase();
  return `<div class="player-avatar" style="width:${size}px;height:${size}px;background:${player.avatarColor||'#FF4A00'}22;border:2px solid ${player.avatarColor||'#FF4A00'}44;">${initials}</div>`;
}

// Async versions (fetch media from API)
async function teamLogoHTML(team, size = 64) {
  const media = await Api.getMedia();
  if (media.teamLogos && media.teamLogos[team.id]) {
    return `<img src="${media.teamLogos[team.id]}" alt="${team.name}" loading="lazy" style="width:${size}px;height:${size}px;object-fit:contain;border-radius:var(--radius);">`;
  }
  return teamLogoHTMLSync(team, size);
}

async function playerAvatarHTML(player, size = 52) {
  const media = await Api.getMedia();
  if (media.playerImages && media.playerImages[player.id]) {
    return `<img src="${media.playerImages[player.id]}" alt="${player.ign}" loading="lazy" style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;border:2px solid ${player.avatarColor||'#FF4A00'}44;">`;
  }
  return playerAvatarHTMLSync(player, size);
}

// ── GLOBAL SEARCH (queries /api/search) ──────────────────────
async function globalSearch(query) {
  if (!query || query.trim().length < 2) return [];
  try {
    const res = await fetch(`${API}api/search?q=${encodeURIComponent(query)}`);
    return res.ok ? await res.json() : [];
  } catch { return []; }
}

// ── DYNAMIC STATS (queries /api/stats) ───────────────────────
async function getDynamicStats() {
  return await Api.getStats();
}

// ── INIT ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('page-transition');
  setTimeout(initFadeIn, 100);
});

// ── NAV SEARCH ────────────────────────────────────────────────
function navSearchGo() {
  const q = document.getElementById('navSearchInput')?.value?.trim();
  if (!q) return;
  document.getElementById('navSearchDropdown').innerHTML = '';
}

async function navSearchSuggest(q) {
  const dd = document.getElementById('navSearchDropdown');
  if (!dd) return;
  if (!q || q.length < 2) { dd.innerHTML = ''; dd.style.display='none'; return; }
  const results = await globalSearch(q);
  if (!results.length) { dd.style.display='none'; return; }
  dd.innerHTML = results.map(r => `
    <a class="nav-search-result" href="${r.href}">
      <span class="nsr-type">${r.type}</span>
      <span class="nsr-title">${r.title}</span>
      ${r.sub ? `<span class="nsr-sub">${r.sub}</span>` : ''}
    </a>`).join('');
  dd.style.display = 'block';
}

document.addEventListener('click', (e) => {
  if (!e.target.closest('.nav-search-wrap')) {
    const dd = document.getElementById('navSearchDropdown');
    if (dd) dd.style.display = 'none';
  }
});
