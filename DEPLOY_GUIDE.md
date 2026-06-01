# 🚀 Esports Archive — Complete Deployment Guide
## Hosting + SEO + Google Ads + Search Ranking

---

## STEP 1 — Get a Domain Name (₹800/year)

Buy from **Namecheap** (cheapest, best for .in domains):
1. Go to https://namecheap.com
2. Search: `esportsarchive.in` or `ffarchive.in`
3. Buy for ~₹800/year
4. You'll use this domain in all steps below

---

## STEP 2 — Deploy on Railway (Free → $5/month)

Railway is the easiest platform for Flask. No server management needed.

### A. Push your project to GitHub first:
```bash
cd esports_archive/
git init
git add .
git commit -m "Initial commit — Esports Archive Flask app"
# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/esports-archive.git
git push -u origin main
```

### B. Deploy on Railway:
1. Go to https://railway.app → Sign up with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `esports-archive` repository
4. Railway auto-detects Python/Flask from `Procfile`
5. Under **Variables** tab, add:
   ```
   SECRET_KEY = any_random_long_string_here_minimum_32_chars
   ```
6. Your site will be live at: `https://esports-archive-production.up.railway.app`

### C. Connect your custom domain:
1. In Railway → Settings → Custom Domain
2. Add: `esportsarchive.in` and `www.esportsarchive.in`
3. Railway gives you DNS records to add at Namecheap:
   - Go to Namecheap → Domain → Advanced DNS
   - Add CNAME record: `www` → your Railway URL
   - Add ALIAS/A record for root domain

---

## STEP 3 — Free CDN with Cloudflare (Makes site 3x faster)

Cloudflare is FREE and makes your site load fast worldwide including India.

1. Go to https://cloudflare.com → Add Site → Enter your domain
2. Cloudflare scans your DNS and imports records
3. Change nameservers at Namecheap to Cloudflare's nameservers
4. In Cloudflare dashboard, enable:
   - **Speed → Optimization**: Auto Minify (JS, CSS, HTML) ✅
   - **Speed → Optimization**: Brotli compression ✅
   - **Caching → Configuration**: Browser Cache TTL = 4 hours
   - **SSL/TLS**: Full (strict) — free HTTPS certificate
   - **Security → Bots**: Bot Fight Mode ON

Your site will now load via Cloudflare's global network — fast from Mumbai, Delhi, Bangalore, etc.

---

## STEP 4 — Update Settings for Live Site

Edit `database/settings.json`:
```json
{
  "siteUrl": "https://esportsarchive.in",
  "googleAnalyticsId": "G-XXXXXXXXXX",
  "googleSearchConsoleTag": "your_verification_token",
  "adsenseId": "ca-pub-XXXXXXXXXXXXXXXX"
}
```

Push changes to GitHub → Railway auto-redeploys in ~30 seconds.

---

## STEP 5 — Google Search Console (Get on Google)

This is how Google finds and indexes your site.

1. Go to https://search.google.com/search-console
2. Click **Add Property** → Enter `https://esportsarchive.in`
3. Choose **HTML tag** verification
4. Copy the verification content token (looks like: `abc123xyz...`)
5. Paste it in `database/settings.json` as `googleSearchConsoleTag`
6. Redeploy → come back and click **Verify**
7. After verification:
   - Go to **Sitemaps** → Enter `https://esportsarchive.in/sitemap.xml` → Submit
   - Go to **URL Inspection** → Enter your homepage URL → Request Indexing

Google will crawl your site within 1-3 days. Check **Coverage** tab to see indexed pages.

### Also submit to Bing:
1. Go to https://www.bing.com/webmasters
2. Sign in with Microsoft account
3. Add site → Enter your URL
4. Import from Google Search Console (one click!)

---

## STEP 6 — Google Analytics (Track visitors)

1. Go to https://analytics.google.com
2. Create Account → Create Property → Enter site name
3. Choose **Web** → Enter your URL
4. Get your **Measurement ID** (looks like: `G-XXXXXXXXXX`)
5. Add to `database/settings.json` as `googleAnalyticsId`
6. Redeploy

You can now see: how many visitors, which pages, which countries, which devices, how long they stay.

---

## STEP 7 — Google AdSense (Earn money from ads)

**Requirements before applying:**
- Site must be LIVE (not localhost)
- At least 10-20 pages of original content ✅ (you have this)
- Privacy Policy page ✅ (included in this project)
- Site must not be brand new — wait 2-4 weeks after going live

### Apply:
1. Go to https://adsense.google.com
2. Sign in with Google account → **Get Started**
3. Enter: `https://esportsarchive.in`
4. Google will review your site (takes 1-14 days)
5. You'll get an email when approved

### After approval — Add Ad Units:
1. In AdSense → **Ads** → **Ad Units** → Create new unit
2. Choose **Display ads** → Give it a name → Get the code
3. Your Publisher ID looks like: `ca-pub-1234567890123456`
4. Add to `database/settings.json` as `adsenseId`
5. Redeploy — Auto Ads will automatically place ads on your site

### Manual Ad Placement (better control):
Add ad units in your HTML pages where you want ads to appear:

```html
<!-- Paste this where you want an ad (between sections) -->
<div class="ad-container" style="text-align:center; margin:2rem 0;">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
       data-ad-slot="XXXXXXXXXX"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
```

**Best ad placement for esports archive:**
- Between hero stats and Latest Tournament (homepage)
- After every 4th tournament/team card in list pages
- Below article content (article-detail.html)
- Sidebar on detail pages (team/player/tournament)

### Expected AdSense Revenue (India, Gaming niche):
| Monthly Visitors | Estimated Monthly Earnings |
|---|---|
| 5,000 | ₹200 – ₹600 |
| 20,000 | ₹800 – ₹2,500 |
| 1,00,000 | ₹4,000 – ₹12,000 |
| 5,00,000 | ₹20,000 – ₹60,000 |

Gaming niche gets higher CPM than average Indian sites.

---

## STEP 8 — Get Ranked on Google (SEO Actions)

Your site already has excellent technical SEO. Now you need these actions:

### Immediate (Do on launch day):
- [ ] Submit sitemap to Google Search Console
- [ ] Submit sitemap to Bing Webmasters
- [ ] Request indexing of homepage, /tournaments, /teams, /players
- [ ] Share launch on r/IndianGaming (reddit.com/r/IndianGaming)
- [ ] Share on r/FreeFireIndia if it exists
- [ ] Post in Indian esports Discord servers

### Week 1-4:
- [ ] Write 2-3 new articles per week (Google loves fresh content)
- [ ] Each tournament page = one article = one more indexed URL
- [ ] Add player profiles for popular Free Fire streamers
- [ ] Get backlinks: ask Free Fire YouTubers to link to player profiles

### Target Keywords (your site already optimized for these):
- "Free Fire India esports" — medium competition
- "FFIC 2024 results" — low competition
- "Free Fire India teams" — medium competition
- "Ajjubhai Free Fire stats" — low competition (lots of searches)
- "Free Fire esports archive" — very low competition
- "Indian Free Fire players" — low competition

### Content Strategy to Rank:
1. **For each major player**: Create detailed profile page (birthday, career, achievements)
2. **For each tournament**: Write a detailed recap article
3. **Comparison articles**: "Top 10 Free Fire India players of all time"
4. **Historical articles**: "History of FFIC — Season 1 to Season 8"

---

## STEP 9 — Monthly Cost Summary

| Item | Cost |
|---|---|
| Domain (.in) | ₹800/year = **₹67/month** |
| Railway hosting | **$5/month = ₹420/month** |
| Cloudflare CDN | **FREE** |
| Google Analytics | **FREE** |
| Google Search Console | **FREE** |
| Google AdSense | **FREE** (pays YOU) |
| **Total** | **~₹490/month** |

If AdSense earns even ₹500/month (achievable at ~10,000 visitors for gaming niche), the site pays for itself.

---

## STEP 10 — Environment Variables Reference

Set these in Railway dashboard under Variables:
```
SECRET_KEY = generate at: https://randomkeygen.com (use "CodeIgniter Encryption Keys")
PORT = 5000 (Railway sets this automatically)
```

---

## API Testing Reference

```bash
# Health check
curl https://esportsarchive.in/api/health

# Get all teams
curl https://esportsarchive.in/api/teams

# Search
curl "https://esportsarchive.in/api/search?q=total+gaming"

# Stats
curl https://esportsarchive.in/api/stats

# Sitemap
curl https://esportsarchive.in/sitemap.xml

# Login (admin only)
curl -X POST https://esportsarchive.in/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_PASSWORD"}'
```

---

## Troubleshooting

**Site not loading after deploy:**
- Check Railway logs for Python errors
- Ensure `Procfile` exists in root directory
- Verify `SECRET_KEY` environment variable is set

**Google not indexing pages:**
- Check robots.txt at: `https://yoursite.in/robots.txt`
- Verify sitemap at: `https://yoursite.in/sitemap.xml`
- Use Google Search Console → URL Inspection → Request Indexing

**AdSense not showing ads:**
- Ads take 24-48 hours to appear after adding code
- Must be approved by Google first
- Check browser console for AdSense errors
