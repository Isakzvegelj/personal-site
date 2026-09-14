# personal-site

**What:** Static personal website of Isak Žvegelj (Olympic rower, UPenn computational cognitive science grad, website builder), published on GitHub Pages at **isakzvegelj.com**. Includes a self-serve blog publisher that writes static posts and pushes them live.
**Status:** active
**Now:** Responsive hero/about interaction, centered section layout, and the new home-page media section are prepared locally and remain uncommitted; mobile hides the nonfunctional motion control and removes the empty creator gap. A short-lived Mac-accessible preview is running at `http://192.168.64.3:4174/`; nothing is deployed. Local HTML/reference validation passes; visual browser verification is still pending because the session browser executable is unavailable. Separate Websites, Partnerships, and Privacy pages are not part of the current site plan. Safe Browsing review remains pending. 2026-08-22 pass: SEO verified strong (meta/sitemap/OG); added Person JSON-LD to index.html (validated). Added Villa Adora Bled to the projects rail with horizontal scroll-snap navigation; changes remain uncommitted and local-only.
**Stack:** Plain HTML/CSS/JS — no build step, no framework. Python 3 stdlib for the blog tooling. Repo: `Isakzvegelj/personal-site`, branch `main`; GitHub Pages serves the repo root (`.nojekyll`, `CNAME`).

**Run & deploy:**
- View locally: open `index.html` in a browser (or any static server); nothing to build.
- Deploy = `git push origin main` — Pages goes live within ~a minute.
- Generate a blog post locally: `bash blog/start.sh` (wraps `python3 blog/publish.py`, opens http://localhost:8123/) → fill title/description/date/tag/article → **Generate**. The tool creates `blog/<slug>.html`, updates `blog/posts.js` + `sitemap.xml`, and never commits or pushes.
- Release only after review: `git add blog/posts.js blog/<slug>.html sitemap.xml && git commit -m "Add blog post: <title>" && git push origin main`.
- Tests: `python3 blog/test_publish.py` and `python3 tools/validate_site.py` (stdlib regression and static-reference checks).
- Authoring guide: `blog/GUIDE.md`.

**Structure:**
- `index.html` — landing page; `css/site.css`, `js/main.js`, `assets/img/` (hero/profile webp)
- `blog/` — `index.html` listing, `post.html` template, `posts.js` post registry, `publish.py` publisher, `start.sh`, `GUIDE.md`, `test_publish.py`
- Deployment metadata: `CNAME` (isakzvegelj.com), `robots.txt`, `sitemap.xml`, `404.html`, `.well-known/security.txt`, `.nojekyll`
- `DSH_CONTEXT.md` — earlier VM context note (kept for reference; this AGENTS.md is now canonical)
- `tools/` — `gsc.py`: stdlib+openssl CLI for Google Safe Browsing v4 lookups and Search Console API (list sites, list/submit sitemaps, URL inspection); takes an API key or service-account JSON path as argument, never embeds secrets

**Gotchas:** This checkout is the working copy inside the DSH VM, cloned from GitHub main; the owner's Mac checkout is separate (per DSH_CONTEXT.md) — coordinate before pushing. `publish.py` only generates files locally and binds a CSRF-token-protected server on port 8123 (`BLOG_PORT` to change) — keep it running only while authoring. Review generated files before an explicit Git release. Keep credentials/keys/browser data out of the repo. Uncommitted modified images sat in `assets/img/` at review time. Blog content lives in generated HTML + `posts.js`; edit posts through the publisher, not by hand.
Domain facts: isakzvegelj.com registered 2026-08-03 (Cloudflare Registrar); DNS proxied through Cloudflare (NS/MX on Cloudflare, Email Routing active) so live HTML differs from repo — Cloudflare rewrites mailto links to `/cdn-cgi/l/email-protection` and injects `email-decode.min.js`; both benign, don't "fix" them in git. GSC verified via TXT `google-site-verification`. Site content audited clean (2026-08-22) against Safe Browsing-style malware patterns; the browser warnings under investigation are a suspected new-domain reputation false positive, not a compromise. Search Console API cannot read security issues or request reviews (UI-only).
*Last reviewed: 2026-09-14*
