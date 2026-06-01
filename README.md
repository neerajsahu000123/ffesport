# Esports Archive — Flask Migration

## What Changed

### Files Removed / Gutted
| Item | Before | After |
|------|--------|-------|
| `DB` object | Entire localStorage CRUD layer | **Removed** |
| `initDatabase()` | Loaded seed JSON → localStorage | **Removed** |
| `Auth.login/logout/getSession` | Read/write `localStorage` session key | Now calls `POST /api/login`, `POST /api/logout`, `GET /api/session` |
| `globalSearch()` | Iterated `DB.getAll(*)` in-memory | Now calls `GET /api/search?q=` |
| `getDynamicStats()` | Counted from localStorage | Now calls `GET /api/stats` |
| `teamLogoHTML()` / `playerAvatarHTML()` | Called `DB.getMedia()` | Now calls `Api.getMedia()` (fetch) |

### Functions Added (app.js)
| Function | Description |
|----------|-------------|
| `Api.getAll(entity)` | `GET /api/{entity}` |
| `Api.getById(entity, id)` | `GET /api/{entity}/{id}` |
| `Api.add(entity, record)` | `POST /api/{entity}` |
| `Api.update(entity, record)` | `PUT /api/{entity}` |
| `Api.delete(entity, id)` | `DELETE /api/{entity}?id=` |
| `Api.getSettings()` | `GET /api/settings` |
| `Api.saveSettings(data)` | `POST /api/settings` |
| `Api.getMedia()` | `GET /api/media` |
| `Api.saveMedia(obj)` | `POST /api/media` |
| `Api.getStats()` | `GET /api/stats` |
| `teamLogoHTMLSync()` | Sync fallback (no fetch, for list renders) |
| `playerAvatarHTMLSync()` | Sync fallback |

### Functions Added (app.py)
| Function | Description |
|----------|-------------|
| `read_json(filename)` | Read JSON from `database/` folder |
| `write_json(filename, data)` | Write JSON to `database/` folder |
| `generate_id(name)` | Create URL-friendly slug IDs |
| `make_crud(filename)` | Factory: returns GET/POST/PUT/DELETE handler |
| `_generate_sitemap()` | Auto-generates `sitemap.xml` |
| `_meta_page(...)` | Injects SEO meta tags into HTML |
| `startup()` | Runs on first boot, ensures sitemap exists |

---

## How to Run

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start Flask development server
python app.py

# 3. Open browser
http://localhost:5000
```

For production:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## API Endpoints

### Auth
```
POST /api/login         Body: {"username":"admin","password":"neeraj"}
POST /api/logout
GET  /api/session
```

### Data (all support GET, POST, PUT, DELETE)
```
/api/tournaments
/api/teams
/api/players
/api/timeline
/api/articles
/api/upcoming
/api/users
/api/media
/api/settings
```

### Utility
```
GET  /api/search?q=<query>   → Global search across all entities
GET  /api/stats              → Count of all entities
GET  /api/health             → Health check
POST /api/sitemap/regenerate → Admin: regenerate sitemap.xml
```

### SEO Routes (serve HTML with dynamic meta)
```
/                                  → index.html with Schema.org
/tournaments.html or /tournaments
/teams.html or /teams
/players.html or /players
/timeline.html or /timeline
/articles.html or /articles
/upcoming.html or /upcoming
/team/<team-id>                    → Team detail with SportsTeam schema
/player/<player-id>                → Player detail with Person schema
/tournament/<tournament-id>        → Tournament detail with SportsEvent schema
/article/<article-id>              → Article detail with Article schema
/sitemap.xml                       → Auto-generated sitemap
/robots.txt                        → Generated robots.txt
```

---

## Testing APIs (curl examples)

```bash
# Login
curl -c cookies.txt -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"neeraj"}'

# Get all teams
curl http://localhost:5000/api/teams

# Get single team
curl http://localhost:5000/api/teams/total-gaming-esports

# Add a tournament (requires login)
curl -b cookies.txt -X POST http://localhost:5000/api/tournaments \
  -H "Content-Type: application/json" \
  -d '{"name":"FFIC 2025 S1","year":2025,"organizer":"Garena India","champion":"TBD","prizePool":"₹60,00,000"}'

# Search
curl "http://localhost:5000/api/search?q=ajju"

# Stats
curl http://localhost:5000/api/stats

# Sitemap
curl http://localhost:5000/sitemap.xml
```

---

## SEO Configuration

Edit `database/settings.json` to configure:

```json
{
  "siteName": "Esports Archive",
  "siteUrl": "https://esportsarchive.in",
  "description": "...",
  "googleAnalyticsId": "G-XXXXXXXXXX",
  "googleSearchConsoleTag": "your-verification-token"
}
```

Sitemap auto-regenerates whenever a team, player, tournament, or article is added.

---

## Data Files

All data persists in `database/` as JSON:
```
database/
  users.json
  teams.json
  players.json
  tournaments.json
  timeline.json
  articles.json
  upcoming.json
  media.json
  settings.json
```

No database server required. JSON files are the database.
