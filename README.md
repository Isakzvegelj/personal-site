# Isak Žvegelj personal site

Static personal website and blog for Isak Žvegelj. The site is plain HTML, CSS, and JavaScript and is served from the repository root by GitHub Pages. Blog tooling uses only Python 3's standard library.

## Local development

There is no build step. Preview the repository with any static server:

```bash
python3 -m http.server 4174
# open http://localhost:4174/
```

Run the checks before reviewing or releasing:

```bash
python3 blog/test_publish.py
python3 tools/validate_site.py
python3 -m py_compile blog/publish.py blog/test_publish.py tools/gsc.py tools/validate_site.py
```

## Blog workflow

Start the local authoring form with `bash blog/start.sh`, then open the printed local URL. It generates the static article, updates `blog/posts.js`, and updates the sitemap. **It does not commit, push, or deploy.** Review the generated diff locally first.

For a reviewed release, confirm the branch and working tree, then explicitly run:

```bash
git add blog/posts.js blog/<slug>.html sitemap.xml
git commit -m "Add blog post: <title>"
git push origin main
```

The push above is the production deployment. Do not run it until the changes and local preview are approved.

## Structure

- `index.html` — landing page
- `css/site.css`, `js/main.js` — shared styling and browser behavior
- `assets/` — imagery and icons
- `blog/` — blog pages, post registry, publisher, and tests
- `tools/validate_site.py` — dependency-free HTML/reference validation
- `tools/gsc.py` — optional Safe Browsing and Search Console CLI
- `sitemap.xml`, `robots.txt`, `CNAME`, `.nojekyll` — Pages metadata

## Deployment

GitHub Pages serves `main` at `https://isakzvegelj.com/`. Deployment is intentionally manual: review locally, run the checks, commit only intended files, and push explicitly.
