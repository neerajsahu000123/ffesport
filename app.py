"""
ESPORTS ARCHIVE — Production Flask Backend
==========================================
- REST API for all entities (JSON file storage)
- Flask session auth (no localStorage)
- Full SEO: sitemap, robots, meta, Schema.org, OG, Twitter Card
- Google Analytics + AdSense + Search Console support
- Gzip compression
- Cache headers for static assets
- Privacy Policy, Terms pages
"""

import json, os, re, uuid, gzip, io
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import (
    Flask, request, jsonify, session, send_from_directory,
    make_response, abort, redirect, url_for
)

# ── CONFIG ──────────────────────────────────────────────────
app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key        = os.environ.get('SECRET_KEY', 'ea_change_this_secret_2025!')
app.permanent_session_lifetime = timedelta(hours=24)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR   = os.path.join(BASE_DIR, 'database')

# ── GZIP MIDDLEWARE ──────────────────────────────────────────
@app.after_request
def compress_response(response):
    # Compress HTML/JSON/CSS/JS responses > 1KB
    if response.status_code < 200 or response.status_code >= 300:
        return response
    if response.direct_passthrough:
        return response
    content_type = response.content_type.lower()
    compressible  = any(ct in content_type for ct in ['text/', 'application/json', 'application/javascript', 'application/xml'])
    accept_enc    = request.headers.get('Accept-Encoding', '')
    if compressible and 'gzip' in accept_enc and len(response.get_data()) > 1024:
        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(mode='wb', fileobj=gzip_buffer, compresslevel=6) as gz:
            gz.write(response.get_data())
        response.set_data(gzip_buffer.getvalue())
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length']   = len(response.get_data())
    return response

# ── CACHE HEADERS ────────────────────────────────────────────
@app.after_request
def add_cache_headers(response):
    path = request.path
    if path.startswith('/assets/css/') or path.startswith('/assets/js/'):
        response.headers['Cache-Control'] = 'public, max-age=604800'  # 7 days
    elif path.startswith('/assets/'):
        response.headers['Cache-Control'] = 'public, max-age=2592000' # 30 days
    elif path in ['/sitemap.xml', '/robots.txt']:
        response.headers['Cache-Control'] = 'public, max-age=86400'   # 1 day
    elif path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-cache, no-store'
    return response

# ── SECURITY HEADERS ────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options']  = 'nosniff'
    response.headers['X-Frame-Options']         = 'SAMEORIGIN'
    response.headers['X-XSS-Protection']        = '1; mode=block'
    response.headers['Referrer-Policy']          = 'strict-origin-when-cross-origin'
    return response

# ── JSON HELPERS ─────────────────────────────────────────────
def read_json(filename: str):
    path = os.path.join(DB_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        try:    return json.load(f)
        except: return []

def write_json(filename: str, data) -> None:
    path = os.path.join(DB_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_id(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug + '-' + uuid.uuid4().hex[:6]

def get_settings() -> dict:
    s = read_json('settings.json')
    return s if isinstance(s, dict) else {}

# ── AUTH DECORATORS ──────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

# ── CRUD FACTORY ─────────────────────────────────────────────
def make_crud(filename: str):
    def view():
        if request.method == 'GET':
            return jsonify(read_json(filename))

        if not session.get('logged_in') or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        if request.method == 'POST':
            record = request.get_json(force=True) or {}
            if not record:
                return jsonify({'error': 'No data'}), 400
            all_data = read_json(filename)
            if not isinstance(all_data, list):
                # For object files like settings/media, just overwrite
                write_json(filename, record)
                return jsonify(record), 200
            if 'id' not in record or not record['id']:
                record['id'] = generate_id(
                    record.get('name') or record.get('title') or
                    record.get('ign') or record.get('username') or 'record'
                )
            all_data = [r for r in all_data if r.get('id') != record['id']]
            all_data.append(record)
            write_json(filename, all_data)
            _update_sitemap_entry(filename)
            return jsonify(record), 201

        if request.method == 'PUT':
            record = request.get_json(force=True) or {}
            if not record.get('id'):
                return jsonify({'error': 'ID required'}), 400
            all_data = read_json(filename)
            idx = next((i for i, r in enumerate(all_data) if r.get('id') == record['id']), -1)
            if idx == -1:
                return jsonify({'error': 'Not found'}), 404
            all_data[idx] = {**all_data[idx], **record}
            write_json(filename, all_data)
            return jsonify(all_data[idx])

        if request.method == 'DELETE':
            rid = request.args.get('id') or (request.get_json(force=True) or {}).get('id')
            if not rid:
                return jsonify({'error': 'ID required'}), 400
            all_data = [r for r in read_json(filename) if r.get('id') != rid]
            write_json(filename, all_data)
            _update_sitemap_entry(filename)
            return jsonify({'deleted': rid})

    view.__name__ = f'crud_{filename}'
    return view

# Register CRUD routes
CRUD_MAP = {
    '/api/tournaments': 'tournaments.json',
    '/api/teams':       'teams.json',
    '/api/players':     'players.json',
    '/api/timeline':    'timeline.json',
    '/api/articles':    'articles.json',
    '/api/upcoming':    'upcoming.json',
    '/api/users':       'users.json',
    '/api/media':       'media.json',
    '/api/settings':    'settings.json',
}
for _route, _file in CRUD_MAP.items():
    app.add_url_rule(_route, view_func=make_crud(_file), methods=['GET','POST','PUT','DELETE'])

# ── AUTH ENDPOINTS ───────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(force=True) or {}
    username = data.get('username','').strip()
    password = data.get('password','')
    users = read_json('users.json')
    user = next((u for u in users if u.get('username')==username and u.get('password')==password), None)
    if not user:
        return jsonify({'error':'Invalid credentials'}), 401
    session.permanent = True
    session.update({
        'logged_in': True,
        'user_id':   user['id'],
        'username':  user['username'],
        'role':      user.get('role','viewer'),
        'displayName': user.get('displayName', username),
    })
    return jsonify({'loggedIn':True,'username':user['username'],'role':user.get('role'),'displayName':user.get('displayName')})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'loggedIn':False})

@app.route('/api/session')
def api_session():
    if session.get('logged_in'):
        return jsonify({'loggedIn':True,'username':session.get('username'),'role':session.get('role'),'displayName':session.get('displayName')})
    return jsonify({'loggedIn':False})

# ── GET BY ID ────────────────────────────────────────────────
@app.route('/api/<entity>/<record_id>')
def get_by_id(entity, record_id):
    file_map = {'tournaments':'tournaments.json','teams':'teams.json','players':'players.json',
                'timeline':'timeline.json','articles':'articles.json','upcoming':'upcoming.json','users':'users.json'}
    filename = file_map.get(entity)
    if not filename: abort(404)
    record = next((r for r in read_json(filename) if r.get('id')==record_id), None)
    if not record: abort(404)
    return jsonify(record)

# ── SEARCH ───────────────────────────────────────────────────
@app.route('/api/search')
def api_search():
    q = (request.args.get('q') or '').strip().lower()
    if len(q) < 2: return jsonify([])
    results = []
    for t in read_json('tournaments.json'):
        if q in (t.get('name','')+t.get('champion','')+t.get('organizer','')).lower():
            results.append({'type':'Tournament','title':t['name'],'sub':f"{t.get('year','')} · {t.get('champion','')}",
                            'href':f"/tournament-detail.html?id={t['id']}",'id':t['id']})
    for t in read_json('teams.json'):
        if q in (t.get('name','')+t.get('shortName','')+t.get('region','')).lower():
            results.append({'type':'Team','title':t['name'],'sub':t.get('region',''),
                            'href':f"/team-detail.html?id={t['id']}",'id':t['id']})
    for p in read_json('players.json'):
        if q in (p.get('ign','')+p.get('realName','')+p.get('role','')).lower():
            results.append({'type':'Player','title':p['ign'],'sub':f"{p.get('role','')} · {p.get('currentTeam','')}",
                            'href':f"/player-detail.html?id={p['id']}",'id':p['id']})
    for a in read_json('articles.json'):
        if q in (a.get('title','')+a.get('summary','')+a.get('category','')).lower():
            results.append({'type':'Article','title':a['title'],'sub':a.get('category',''),
                            'href':f"/article-detail.html?id={a['id']}",'id':a['id']})
    for t in read_json('timeline.json'):
        if q in (t.get('title','')+t.get('detail','')).lower():
            results.append({'type':'Timeline','title':t['title'],'sub':str(t.get('year','')),
                            'href':'/timeline.html','id':t.get('id','')})
    return jsonify(results[:15])

# ── STATS ─────────────────────────────────────────────────────
@app.route('/api/stats')
def api_stats():
    return jsonify({
        'tournaments': len(read_json('tournaments.json')),
        'teams':       len(read_json('teams.json')),
        'players':     len(read_json('players.json')),
        'articles':    len(read_json('articles.json')),
        'timeline':    len(read_json('timeline.json')),
        'upcoming':    len(read_json('upcoming.json')),
    })

# ── HEALTH ───────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({'status':'ok','timestamp':datetime.now(timezone.utc).isoformat()})

# ── SITEMAP ───────────────────────────────────────────────────
SITEMAP_ENTITIES = {
    'teams.json':       '/team/',
    'players.json':     '/player/',
    'tournaments.json': '/tournament/',
    'articles.json':    '/article/',
}

def _update_sitemap_entry(filename):
    if filename in SITEMAP_ENTITIES:
        _generate_sitemap()

def _generate_sitemap() -> str:
    s    = get_settings()
    base = s.get('siteUrl','https://esportsarchive.in').rstrip('/')
    today= datetime.now(timezone.utc).strftime('%Y-%m-%d')

    static_urls = [
        ('/','/','1.0','daily'),('/tournaments.html','Tournaments','0.9','weekly'),
        ('/teams.html','Teams','0.9','weekly'),('/players.html','Players','0.9','weekly'),
        ('/timeline.html','Timeline','0.8','monthly'),('/articles.html','Articles','0.8','weekly'),
        ('/upcoming.html','Upcoming','0.7','daily'),('/privacy.html','Privacy','0.3','yearly'),
    ]

    urls = []
    for loc, _, pri, freq in static_urls:
        urls.append(f'  <url>\n    <loc>{base}{loc}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>')

    for filename, prefix in SITEMAP_ENTITIES.items():
        for item in read_json(filename):
            iid = item.get('id','')
            if iid:
                urls.append(f'  <url>\n    <loc>{base}{prefix}{iid}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.65</priority>\n  </url>')

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '\n'.join(urls) + '\n</urlset>'
    with open(os.path.join(BASE_DIR,'sitemap.xml'),'w') as f:
        f.write(xml)
    return xml

@app.route('/sitemap.xml')
def sitemap():
    path = os.path.join(BASE_DIR,'sitemap.xml')
    if not os.path.exists(path):
        xml = _generate_sitemap()
    else:
        with open(path) as f: xml = f.read()
    resp = make_response(xml)
    resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return resp

@app.route('/api/sitemap/regenerate', methods=['POST'])
@admin_required
def regenerate_sitemap():
    _generate_sitemap()
    return jsonify({'status':'ok'})

# ── ROBOTS.TXT ───────────────────────────────────────────────
@app.route('/robots.txt')
def robots():
    s    = get_settings()
    base = s.get('siteUrl','https://esportsarchive.in').rstrip('/')
    txt = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /login.html

# Google
User-agent: Googlebot
Allow: /

# Bing
User-agent: Bingbot
Allow: /

# Allow all crawlers on public pages
User-agent: *
Crawl-delay: 1

Sitemap: {base}/sitemap.xml
"""
    resp = make_response(txt)
    resp.headers['Content-Type'] = 'text/plain'
    return resp

# ── SEO META INJECTION ────────────────────────────────────────
def _inject_seo(html_file: str, title: str, description: str, keywords: str,
                og_type: str = 'website', schema: dict = None,
                og_image: str = None) -> str:
    filepath = os.path.join(BASE_DIR, html_file)
    if not os.path.exists(filepath):
        abort(404)
    with open(filepath,'r',encoding='utf-8') as f:
        html = f.read()

    s         = get_settings()
    base      = s.get('siteUrl','https://esportsarchive.in').rstrip('/')
    site_name = s.get('siteName','Esports Archive')
    ga_id     = s.get('googleAnalyticsId','')
    gsc_tag   = s.get('googleSearchConsoleTag','')
    adsense_id= s.get('adsenseId','')
    canonical = base + request.path
    img       = og_image or f"{base}/assets/images/og-default.png"

    meta = f"""
    <!-- Primary SEO -->
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
    <meta name="author" content="{site_name}">
    <link rel="canonical" href="{canonical}">

    <!-- Open Graph (Facebook, WhatsApp, Discord) -->
    <meta property="og:type" content="{og_type}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{img}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:url" content="{canonical}">
    <meta property="og:site_name" content="{site_name}">
    <meta property="og:locale" content="en_IN">

    <!-- Twitter / X Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{img}">
    <meta name="twitter:site" content="@esportsarchivein">

    <!-- Mobile / PWA -->
    <meta name="theme-color" content="#FF4A00">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="icon" type="image/png" href="{base}/assets/images/favicon.png">
"""

    if gsc_tag:
        meta += f'\n    <meta name="google-site-verification" content="{gsc_tag}">\n'

    # Schema.org structured data
    schema_block = ''
    if schema:
        schema_block = f'\n    <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>'

    # Google Analytics 4
    ga_block = ''
    if ga_id:
        ga_block = f"""
    <!-- Google Analytics 4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{ga_id}', {{
        page_title: document.title,
        page_location: window.location.href
      }});
    </script>"""

    # Google AdSense auto-ads
    adsense_block = ''
    if adsense_id:
        adsense_block = f"""
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={adsense_id}"
     crossorigin="anonymous"></script>"""

    inject = meta + schema_block + ga_block + adsense_block
    html   = html.replace('</head>', inject + '\n</head>', 1)
    # Update title tag
    html   = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', html, count=1)
    return html


def _base_schema():
    s    = get_settings()
    base = s.get('siteUrl','https://esportsarchive.in').rstrip('/')
    name = s.get('siteName','Esports Archive')
    return base, name

# ── PAGE ROUTES ────────────────────────────────────────────────
@app.route('/')
@app.route('/index.html')
def home():
    base, name = _base_schema()
    schema = {"@context":"https://schema.org","@graph":[
        {"@type":"Organization","name":name,"url":base,
         "description":"The definitive historical archive for Free Fire esports in India — tournaments, teams, players, competitive history since 2019.",
         "logo":{"@type":"ImageObject","url":f"{base}/assets/images/logo.png"}},
        {"@type":"WebSite","name":name,"url":base,
         "potentialAction":{"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":f"{base}/api/search?q={{search_term_string}}"},"query-input":"required name=search_term_string"}},
        {"@type":"WebPage","@id":f"{base}/","url":f"{base}/","name":f"{name} — Indian Free Fire Esports Historical Database",
         "isPartOf":{"@id":f"{base}/"},"description":"Complete archive of Indian Free Fire esports — FFIC, FFWS, teams, players, history."}
    ]}
    return _inject_seo('index.html',
        f"{name} — Indian Free Fire Esports Historical Database",
        "The #1 archive for Indian Free Fire esports. Complete history of FFIC, FFWS, teams like Total Gaming Esports, Blind Esports, and 100+ player profiles. Free Fire India database since 2019.",
        "Free Fire India esports, FFIC, Free Fire esports archive India, Free Fire teams India, Free Fire players India, FFWS India, Indian esports history, Free Fire competitive India",
        schema=schema)

@app.route('/tournaments.html')
@app.route('/tournaments')
def tournaments_page():
    base, name = _base_schema()
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":"Indian Free Fire Tournaments — Complete History","url":f"{base}/tournaments.html","description":"Every FFIC, FFSCC, FFWS India and regional Free Fire tournament — prize pools, champions, brackets."}
    return _inject_seo('tournaments.html',
        'Tournaments — Indian Free Fire Esports Complete History | Esports Archive',
        'Complete history of Indian Free Fire esports tournaments — FFIC 2019 to 2024, FFSCC, FFWS India qualifiers. Prize pools, champions, brackets, and full results.',
        'FFIC tournaments, Free Fire India Championship, FFSCC, FFWS India, Free Fire esports tournaments, FFIC 2024, FFIC 2023, Indian Free Fire history, Free Fire tournament results',
        schema=schema)

@app.route('/teams.html')
@app.route('/teams')
def teams_page():
    base, name = _base_schema()
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":"Indian Free Fire Esports Teams Database","url":f"{base}/teams.html","description":"Every organization in Indian Free Fire esports — active rosters, history, championships."}
    return _inject_seo('teams.html',
        'Teams — Free Fire India Esports Team Database | Esports Archive',
        'Complete database of Indian Free Fire esports teams — Total Gaming Esports, Blind Esports, Galaxy Racer India, YoloStar, and every org that competed in FFIC.',
        'Free Fire India teams, Total Gaming Esports, Blind Esports, Free Fire esports teams India, Galaxy Racer India, YoloStar Gang, FFIC teams, Indian Free Fire organizations',
        schema=schema)

@app.route('/players.html')
@app.route('/players')
def players_page():
    base, name = _base_schema()
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":"Indian Free Fire Pro Player Database","url":f"{base}/players.html","description":"Profiles for every notable Indian Free Fire competitive player."}
    return _inject_seo('players.html',
        'Players — Free Fire India Pro Player Database | Esports Archive',
        'Every notable Indian Free Fire esports player — Ajjubhai, Raistar, Lokesh Gamer, K18, career stats, tournament history, and current team affiliations.',
        'Free Fire India players, Ajjubhai Free Fire, Raistar Free Fire, Lokesh Gamer, K18 Free Fire, Indian Free Fire pros, Free Fire player database, FFIC players',
        schema=schema)

@app.route('/timeline.html')
@app.route('/timeline')
def timeline_page():
    return _inject_seo('timeline.html',
        'Timeline — Indian Free Fire Esports History | Esports Archive',
        'The complete chronological history of Indian Free Fire esports — tournaments, team formations, player transfers, and key milestones from 2019 to present.',
        'Free Fire India history, Free Fire esports timeline, FFIC history, Indian esports milestones, Free Fire India 2019 2020 2021 2022 2023 2024',
        schema={"@context":"https://schema.org","@type":"WebPage","name":"Indian Free Fire Esports Timeline"})

@app.route('/articles.html')
@app.route('/articles')
def articles_page():
    return _inject_seo('articles.html',
        'Articles — Free Fire India Esports Stories | Esports Archive',
        'In-depth articles on Indian Free Fire esports — tournament recaps, team histories, player interviews, competitive analysis and esports journalism.',
        'Free Fire India articles, Free Fire esports stories, FFIC history articles, Free Fire India analysis, Indian esports journalism',
        og_type='blog',
        schema={"@context":"https://schema.org","@type":"Blog","name":"Esports Archive Articles"})

@app.route('/upcoming.html')
@app.route('/upcoming')
def upcoming_page():
    return _inject_seo('upcoming.html',
        'Upcoming Events — Free Fire India Tournament Schedule 2025 | Esports Archive',
        'Upcoming Free Fire India esports tournaments 2025 — schedules, registration status, prize pools, team slots and qualification info.',
        'Free Fire India upcoming tournaments 2025, FFIC 2025, Free Fire esports schedule, Free Fire India events, Free Fire tournament registration')

# ── SEO ENTITY DETAIL PAGES ──────────────────────────────────
@app.route('/team/<team_id>')
@app.route('/team-detail.html')
def team_detail(team_id=None):
    team_id = team_id or request.args.get('id','')
    team = next((t for t in read_json('teams.json') if t.get('id')==team_id), None)
    if not team:
        return send_from_directory(BASE_DIR,'team-detail.html')
    base, site_name = _base_schema()
    schema = {"@context":"https://schema.org","@type":"SportsTeam",
              "name":team.get('name'),"sport":"Free Fire Esports",
              "foundingDate":team.get('founded',''),"url":f"{base}/team/{team_id}",
              "location":{"@type":"Place","name":team.get('region','India')},
              "description":team.get('bio',f"{team.get('name')} is an Indian Free Fire esports organization.")}
    return _inject_seo('team-detail.html',
        f"{team.get('name')} — Team Profile | Esports Archive",
        f"{team.get('name')} ({team.get('shortName','')}) Free Fire esports team. {team.get('championships',0)} championships, founded {team.get('founded','')}. Roster, tournament history, and stats.",
        f"{team.get('name')}, {team.get('shortName','')}, Free Fire India team, {team.get('region','India')} esports, FFIC",
        schema=schema)

@app.route('/player/<player_id>')
@app.route('/player-detail.html')
def player_detail(player_id=None):
    player_id = player_id or request.args.get('id','')
    player = next((p for p in read_json('players.json') if p.get('id')==player_id), None)
    if not player:
        return send_from_directory(BASE_DIR,'player-detail.html')
    base, site_name = _base_schema()
    schema = {"@context":"https://schema.org","@type":"Person",
              "name":player.get('ign'),"alternateName":player.get('realName',''),
              "jobTitle":f"Free Fire Esports Player — {player.get('role','')}",
              "nationality":"Indian","url":f"{base}/player/{player_id}",
              "description":player.get('bio',f"{player.get('ign')} is an Indian Free Fire esports player.")}
    return _inject_seo('player-detail.html',
        f"{player.get('ign')} — Player Profile | Esports Archive",
        f"{player.get('ign')} ({player.get('realName','')}) — {player.get('role','')} in Indian Free Fire esports. Career stats, team history, tournament results and achievements.",
        f"{player.get('ign')}, {player.get('realName','')}, Free Fire India player, {player.get('role','')} Free Fire, FFIC player",
        og_type='profile', schema=schema)

@app.route('/tournament/<tournament_id>')
@app.route('/tournament-detail.html')
def tournament_detail(tournament_id=None):
    tournament_id = tournament_id or request.args.get('id','')
    t = next((x for x in read_json('tournaments.json') if x.get('id')==tournament_id), None)
    if not t:
        return send_from_directory(BASE_DIR,'tournament-detail.html')
    base, site_name = _base_schema()
    schema = {"@context":"https://schema.org","@type":"SportsEvent",
              "name":t.get('name'),"sport":"Free Fire Esports",
              "startDate":t.get('startDate',''),"endDate":t.get('endDate',''),
              "url":f"{base}/tournament/{tournament_id}",
              "location":{"@type":"Place","name":"India"},
              "organizer":{"@type":"Organization","name":t.get('organizer','')},
              "description":t.get('description',f"{t.get('name')} — prize pool {t.get('prizePool','')}."),
              "winner":{"@type":"SportsTeam","name":t.get('champion','')}}
    return _inject_seo('tournament-detail.html',
        f"{t.get('name')} ({t.get('year')}) — Tournament Details | Esports Archive",
        f"{t.get('name')} {t.get('year')} — {t.get('organizer')}. Champion: {t.get('champion','')}. Prize Pool: {t.get('prizePool','')}. Complete results, brackets, and team standings.",
        f"{t.get('name')}, {t.get('year')} Free Fire India tournament, {t.get('organizer')}, {t.get('champion')} champion, FFIC, Free Fire India",
        schema=schema)

@app.route('/article/<article_id>')
@app.route('/article-detail.html')
def article_detail(article_id=None):
    article_id = article_id or request.args.get('id','')
    a = next((x for x in read_json('articles.json') if x.get('id')==article_id), None)
    if not a:
        return send_from_directory(BASE_DIR,'article-detail.html')
    base, site_name = _base_schema()
    schema = {"@context":"https://schema.org","@type":"Article",
              "headline":a.get('title'),"description":a.get('summary',''),
              "datePublished":a.get('date',''),"dateModified":a.get('date',''),
              "author":{"@type":"Person","name":a.get('author','Esports Archive Staff')},
              "publisher":{"@type":"Organization","name":site_name,"url":base},
              "url":f"{base}/article/{article_id}",
              "articleSection":a.get('category','Esports'),
              "keywords":f"Free Fire India, {a.get('category','')}, Indian esports"}
    return _inject_seo('article-detail.html',
        f"{a.get('title')} | Esports Archive",
        a.get('summary') or a.get('title',''),
        f"{a.get('category','')}, Free Fire India, {a.get('title','')}, Indian esports",
        og_type='article', schema=schema)

# ── STATIC PAGES ─────────────────────────────────────────────
@app.route('/privacy.html')
@app.route('/privacy')
def privacy():
    return _inject_seo('privacy.html',
        'Privacy Policy | Esports Archive',
        'Privacy Policy for Esports Archive — how we collect, use and protect your data.',
        'privacy policy, esports archive privacy',
        og_type='website')

@app.route('/login.html')
def login_page():
    return send_from_directory(BASE_DIR,'login.html')

@app.route('/admin/')
@app.route('/admin/dashboard.html')
def admin_dashboard():
    return send_from_directory(os.path.join(BASE_DIR,'admin'),'dashboard.html')

# ── 404 ──────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return send_from_directory(BASE_DIR,'404.html'), 404

# ── STARTUP ──────────────────────────────────────────────────
def startup():
    if not os.path.exists(os.path.join(BASE_DIR,'sitemap.xml')):
        _generate_sitemap()

if __name__ == '__main__':
    startup()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
