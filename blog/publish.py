#!/usr/bin/env python3
"""Isak's blog generator — type an article, generate it locally, then review.

Run from the repository root:  python3 blog/publish.py
Then open the printed URL in your browser.

The page lets you paste a title + article (plain text or light markdown),
click Generate, and it:
  1. converts your text to safe HTML
  2. creates a static, SEO-friendly blog/<slug>.html page
  3. appends the page to blog/posts.js and the sitemap
  4. leaves generated files local for review; deployment is a separate Git operation.

Stdlib only. No installs.
"""
import datetime
import html
import hmac
import http.server
import json
import os
import re
import secrets
import sys
import urllib.parse
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))          # .../blog
REPO = os.path.dirname(BASE)                                # .../personal-site
POSTS_FILE = os.path.join(BASE, "posts.js")
POST_TEMPLATE_FILE = os.path.join(BASE, "post.html")
SITEMAP_FILE = os.path.join(REPO, "sitemap.xml")
LIVE_URL = "https://isakzvegelj.com/blog/"
SOCIAL_IMAGE_URL = "https://isakzvegelj.com/assets/img/social-share.jpg"
SAFE_POST_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

HOST = "127.0.0.1"
PORT = int(os.environ.get("BLOG_PORT", "8123"))
MAX_BODY_BYTES = 1_000_000
CSRF_TOKEN = secrets.token_urlsafe(32)

def is_valid_csrf(token):
    return hmac.compare_digest(token or "", CSRF_TOKEN)

# ---------------------------------------------------------------- markdown -> html
def _safe_url(value):
    """Allow only web URLs in generated links and images."""
    value = value.strip()
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme.lower() not in ("http", "https"):
        return ""
    return html.escape(value, quote=True)

def _inline(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def link(match):
        url = _safe_url(html.unescape(match.group(2)))
        return f'<a href="{url}">{match.group(1)}</a>' if url else match.group(1)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return s

def md_to_html(text):
    lines = text.split("\n")
    out, i = [], 0
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    while i < len(lines):
        s = lines[i].strip()
        if s == "":
            close_list(); i += 1; continue
        if s == "---":
            close_list(); out.append("<hr>"); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            close_list()
            num = len(m.group(1))
            lvl = 2 if num <= 2 else min(num, 5)   # # or ##  -> h2 ; ### -> h3 ; #### -> h4
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>"); i += 1; continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s)
        if m:
            close_list()
            src = _safe_url(m.group(2))
            if src:
                out.append(f'<img src="{src}" alt="{html.escape(m.group(1), quote=True)}" loading="lazy" decoding="async">')
            else:
                out.append(f'<p>{html.escape(m.group(1))}</p>')
            i += 1; continue
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{_inline(m.group(1))}</li>"); i += 1; continue
        close_list()
        para = []
        while i < len(lines) and lines[i].strip() != "":
            para.append(lines[i].strip()); i += 1
        out.append(f"<p>{_inline(' '.join(para))}</p>")
    close_list()
    return "\n".join(out)

# ---------------------------------------------------------------- posts.js editing
def slugify(title):
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "post"

def existing_post_ids():
    """Read IDs without executing the JavaScript posts file."""
    try:
        with open(POSTS_FILE, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return set()
    return set(re.findall(r"(?:^|[{,])\s*(?:[\"']?id[\"']?)\s*:\s*[\"']([^\"']+)[\"']", text, re.MULTILINE))

def ensure_unique_slug(title):
    slug = slugify(title)
    if slug in existing_post_ids():
        raise ValueError(f"A post with the slug '{slug}' already exists; choose a different title.")
    return slug


def post_filename(post_id):
    """Return a safe relative filename for a validated post slug."""
    if not SAFE_POST_ID.fullmatch(post_id or ""):
        raise ValueError("Post IDs must contain only lowercase letters, numbers, and single dashes.")
    return f"{post_id}.html"


def canonical_post_url(post_id):
    return LIVE_URL + post_filename(post_id)


def excerpt_from_html(content_html, limit=190):
    """Build a compact plain-text description when no excerpt was supplied."""
    text = re.sub(r"<[^>]+>", " ", content_html)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    if len(text) <= limit:
        return text
    shortened = text[: limit + 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return (shortened or text[:limit]).rstrip() + "…"


def display_date(value):
    try:
        parsed = datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return value or "Undated"
    return f"{parsed.day} {parsed.strftime('%B %Y')}"


def sitemap_date(value):
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        return datetime.date.today().isoformat()


def validate_date(value):
    """Reject invalid dates instead of silently changing sitemap metadata."""
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError("Date must use YYYY-MM-DD.") from exc


def make_entry(title, tag, date, excerpt, content_html, post_id=None):
    slug = post_id or slugify(title)
    obj = {
        "id": slug,
        "url": post_filename(slug),
        "title": title,
        "date": date,
        "tag": tag,
        "excerpt": excerpt,
        "content": content_html,
    }
    body = json.dumps(obj, ensure_ascii=False, indent=2).split("\n")
    lines = ["  {"]
    for ln in body[1:-1]:
        lines.append("  " + ln if ln else ln)
    lines.append("  },")
    return "\n".join(lines)

def insert_into_posts(entry):
    with open(POSTS_FILE, encoding="utf-8") as f:
        text = f.read()
    marker = "window.BLOG_POSTS = ["
    idx = text.index(marker) + len(marker)
    while text[idx] != "\n":
        idx += 1
    idx += 1  # just after the opening-bracket newline
    new_text = text[:idx] + entry + "\n" + text[idx:]
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        f.write(new_text)
    return new_text

def _replace_required(text, pattern, replacement, label, flags=0):
    updated, count = re.subn(pattern, lambda _match: replacement, text, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"Post template is missing its {label} placeholder.")
    return updated


def _set_meta(text, attribute, name, value):
    escaped = html.escape(value, quote=True)
    pattern = rf'(<meta\s+{attribute}="{re.escape(name)}"\s+content=")[^"]*(">)'
    updated, count = re.subn(pattern, lambda match: match.group(1) + escaped + match.group(2), text, count=1)
    if count != 1:
        raise ValueError(f"Post template is missing {attribute}={name!r} metadata.")
    return updated


def render_post_page(title, tag, date, excerpt, content_html, post_id):
    """Render one standalone article from the maintained dynamic post shell."""
    with open(POST_TEMPLATE_FILE, encoding="utf-8") as template_file:
        page = template_file.read()

    canonical = canonical_post_url(post_id)
    description = excerpt.strip() or excerpt_from_html(content_html)
    if not description:
        description = f"An update from Isak Žvegelj: {title}"
    safe_title = html.escape(title, quote=False)
    safe_tag = html.escape(tag or "Update", quote=False)
    safe_date = html.escape(display_date(date), quote=False)

    page = _replace_required(page, r"<title>.*?</title>", f"<title>{safe_title} — Isak Žvegelj</title>", "title")
    page = _replace_required(
        page,
        r'<link\s+rel="canonical"\s+href="[^"]*">',
        f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">',
        "canonical link",
    )
    page = _set_meta(page, "name", "description", description)
    page = _set_meta(page, "property", "og:title", title)
    page = _set_meta(page, "property", "og:description", description)
    page = _set_meta(page, "property", "og:url", canonical)
    page = _set_meta(page, "name", "twitter:title", title)
    page = _set_meta(page, "name", "twitter:description", description)
    page = _replace_required(
        page,
        r'<p class="eyebrow" id="postTag">.*?</p>',
        f'<p class="eyebrow" id="postTag">{safe_tag}</p>',
        "post tag",
    )
    page = _replace_required(
        page,
        r'<h1 id="postTitle">.*?</h1>',
        f'<h1 id="postTitle">{safe_title}</h1>',
        "post title",
    )
    page = _replace_required(
        page,
        r'<p class="post-date" id="postDate">.*?</p>',
        f'<p class="post-date" id="postDate">{safe_date}</p>',
        "post date",
    )
    page = _replace_required(
        page,
        r'<div id="postContent" class="prose">.*?</div>',
        f'<div id="postContent" class="prose">{content_html}</div>',
        "post content",
        flags=re.DOTALL,
    )
    page = _replace_required(
        page,
        r'\s*<script src="posts\.js"></script>\s*<script>\s*/\* Render the single post based on \?id= \*/.*?</script>',
        "",
        "dynamic post renderer",
        flags=re.DOTALL,
    )

    structured = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": description,
        "mainEntityOfPage": canonical,
        "image": SOCIAL_IMAGE_URL,
        "author": {
            "@type": "Person",
            "name": "Isak Žvegelj",
            "url": "https://isakzvegelj.com/",
        },
    }
    try:
        structured["datePublished"] = datetime.date.fromisoformat(date).isoformat()
    except (TypeError, ValueError):
        pass
    structured_json = json.dumps(structured, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace(
        "</head>",
        f'<script type="application/ld+json">{structured_json}</script>\n</head>',
        1,
    )
    return page


def write_post_page(post_id, page):
    """Write a new post page atomically without overwriting existing content."""
    destination = os.path.join(BASE, post_filename(post_id))
    if os.path.exists(destination):
        raise FileExistsError(f"Static post page already exists: {os.path.basename(destination)}")
    temporary = destination + f".{secrets.token_hex(8)}.tmp"
    try:
        with open(temporary, "x", encoding="utf-8") as output:
            output.write(page)
            output.flush()
            os.fsync(output.fileno())
        if os.path.exists(destination):
            raise FileExistsError(f"Static post page already exists: {os.path.basename(destination)}")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return destination


def update_sitemap(post_id, date):
    """Append a static article URL once while preserving the existing sitemap."""
    canonical = canonical_post_url(post_id)
    with open(SITEMAP_FILE, encoding="utf-8") as sitemap_file:
        sitemap = sitemap_file.read()
    if re.search(rf"<loc>\s*{re.escape(canonical)}\s*</loc>", sitemap):
        return False
    marker = "</urlset>"
    if marker not in sitemap:
        raise ValueError("Sitemap is missing its closing </urlset> tag.")
    entry = (
        "  <url>\n"
        f"    <loc>{html.escape(canonical)}</loc>\n"
        f"    <lastmod>{sitemap_date(date)}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>0.6</priority>\n"
        "  </url>\n"
    )
    updated = sitemap.replace(marker, entry + marker, 1)
    temporary = SITEMAP_FILE + f".{secrets.token_hex(8)}.tmp"
    try:
        with open(temporary, "x", encoding="utf-8") as output:
            output.write(updated)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, SITEMAP_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def save_post_files(title, tag, date, excerpt, content_html, post_id, published):
    """Create generated files together; roll back if any write fails."""
    final_excerpt = excerpt.strip() or excerpt_from_html(content_html)
    entry = make_entry(title, tag, date, final_excerpt, content_html, post_id)
    page = render_post_page(title, tag, date, final_excerpt, content_html, post_id)
    with open(POSTS_FILE, encoding="utf-8") as posts_file:
        original_posts = posts_file.read()
    original_sitemap = None
    if published:
        with open(SITEMAP_FILE, encoding="utf-8") as sitemap_file:
            original_sitemap = sitemap_file.read()
    destination = write_post_page(post_id, page)
    try:
        insert_into_posts(entry)
        if published:
            update_sitemap(post_id, date)
    except Exception:
        with open(POSTS_FILE, "w", encoding="utf-8") as posts_file:
            posts_file.write(original_posts)
        if original_sitemap is not None:
            with open(SITEMAP_FILE, "w", encoding="utf-8") as sitemap_file:
                sitemap_file.write(original_sitemap)
        if os.path.exists(destination):
            os.unlink(destination)
        raise
    return destination


def generated_files(post_id):
    """Return the files a release would contain, without touching Git."""
    return ["blog/posts.js", f"blog/{post_filename(post_id)}", "sitemap.xml"]

# ---------------------------------------------------------------- http server
PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>New blog post — Isak Žvegelj</title>
<style>
:root{--bg:#f7f4ee;--ink:#1a1d22;--muted:#5b6067;--green:#1e3a32;--gold:#b08d57;--line:#e2ddd1;--white:#fff;--serif:Georgia,'Times New Roman',serif;--sans:'Segoe UI',system-ui,sans-serif}
*{box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--ink);margin:0;line-height:1.6}
.wrap{max-width:720px;margin:0 auto;padding:48px 20px 80px}
h1{font-family:var(--serif);font-weight:600;font-size:2.4rem;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 32px}
label{display:block;font-size:.8rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:18px 0 6px}
input[type=text],input[type=date],textarea{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--white);font-family:var(--sans);font-size:1rem;color:var(--ink)}
textarea{resize:vertical;white-space:pre-wrap}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.row.trio{grid-template-columns:1fr 1fr 1fr}
.hint{font-size:.78rem;color:var(--muted);margin-top:5px}
.btn{margin-top:28px;padding:14px 30px;border:0;border-radius:50px;background:var(--green);color:#fff;font-size:1rem;font-weight:600;cursor:pointer}
.btn:hover{opacity:.9}
.btn.secondary{background:#d8d3c5;color:var(--ink);margin-left:10px}
#status{margin-top:18px;padding:14px 16px;border-radius:10px;font-size:.95rem;display:none;white-space:pre-wrap}
#status.ok{background:#e8f2ea;color:#1e6b34;border:1px solid #bfe0c8;display:block}
#status.err{background:#fbecec;color:#b3261e;border:1px solid #f2c4c4;display:block}
@media(max-width:560px){.row,.row.trio{grid-template-columns:1fr}}
</style></head>
<body><div class="wrap">
<h1>New blog post</h1>
<p class="sub">Write it, click <strong>Generate</strong> — then review the local files before release.</p>
<form id="form">
  <input type="hidden" name="csrf_token" value="__CSRF_TOKEN__">
  <label>Title</label>
  <input type="text" id="title" name="title" placeholder="e.g. World Cup prep update" required>

  <label>Short description <span style="text-transform:none;font-weight:400">(optional)</span></label>
  <input type="text" id="excerpt" name="excerpt" maxlength="240" placeholder="Used on the blog list and in search/social previews; generated from the article if blank">

  <div class="row trio">
    <div>
      <label>Date</label>
      <input type="date" id="date" name="date" required>
    </div>
    <div>
      <label>Tag</label>
      <input type="text" id="tag" name="tag" placeholder="Update">
    </div>
    <div>
      <label>Status</label>
      <select id="mode" name="mode" style="width:100%;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--white);font-size:1rem">
        <option value="publish">Generate for release</option>
        <option value="draft">Save draft only</option>
      </select>
    </div>
  </div>

  <label>Article (plain text or light markdown)</label>
  <textarea id="content" name="content" rows="14" placeholder="Write your post here.&#10;&#10;## A heading&#10;&#10;Some paragraph text. **bold** and *italic* work.&#10;&#10;- bullet one&#10;- bullet two&#10;&#10;![caption](https://example.com/photo.jpg)"></textarea>

  <button type="submit" class="btn">Generate</button>
  <span id="status"></span>
</form>
<p class="hint" style="margin-top:26px">Markdown you can use: <code>## heading</code>, <code>**bold**</code>, <code>*italic*</code>, <code>- bullet</code>, blank line = new paragraph, <code>![alt](url)</code> = image. Or just paste plain text and hit Generate.</p>
</div>
<script>
(function(){
  document.getElementById('date').value = new Date().toISOString().slice(0,10);
  var f = document.getElementById('form');
  var st = document.getElementById('status');
  f.addEventListener('submit', function(e){
    e.preventDefault();
    var fd = new FormData(f);
    st.className = ''; st.style.display = 'none';
    var btn = f.querySelector('.btn');
    btn.disabled = true; btn.textContent = 'Generating…';
    fetch('/publish', {method:'POST', body:new URLSearchParams(fd)})
      .then(function(r){return r.json();})
      .then(function(d){
        btn.disabled=false; btn.textContent='Generate';
        st.className = d.ok ? 'ok' : 'err';
        st.textContent = d.message;
      })
      .catch(function(err){
        btn.disabled=false; btn.textContent='Generate';
        st.className='err'; st.textContent='Something went wrong: '+err;
      });
  });
})();
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        page = PAGE.replace("__CSRF_TOKEN__", html.escape(CSRF_TOKEN, quote=True))
        self._send(200, page)

    def do_POST(self):
        if self.path.rstrip("/") != "/publish":
            self._send(404, json.dumps({"ok": False, "message": "not found"}), "application/json; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0:
            self._send(411, json.dumps({"ok": False, "message": "content length required"}), "application/json; charset=utf-8")
            return
        if length > MAX_BODY_BYTES:
            self._send(413, json.dumps({"ok": False, "message": "request body is too large"}), "application/json; charset=utf-8")
            return
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        form = urllib.parse.parse_qs(body)
        provided_token = (form.get("csrf_token") or [""])[0]
        if not is_valid_csrf(provided_token):
            self._send(403, json.dumps({"ok": False, "message": "invalid CSRF token"}), "application/json; charset=utf-8")
            return
        g = lambda k: (form.get(k) or [""])[0].strip()
        title = g("title"); content = g("content")
        excerpt = g("excerpt")
        tag = g("tag") or "Update"
        date = g("date")
        mode = g("mode") or "publish"
        if not title:
            self._send(200, json.dumps({"ok": False, "message": "Please add a title."})); return
        if not content:
            self._send(200, json.dumps({"ok": False, "message": "The article is empty."})); return
        try:
            date = validate_date(date)
        except ValueError as exc:
            self._send(400, json.dumps({"ok": False, "message": str(exc)}), "application/json; charset=utf-8")
            return
        if mode not in ("publish", "draft"):
            self._send(400, json.dumps({"ok": False, "message": "invalid publish mode"}), "application/json; charset=utf-8")
            return

        try:
            post_id = ensure_unique_slug(title)
            content_html = md_to_html(content)
            save_post_files(title, tag, date, excerpt, content_html, post_id, mode == "publish")
        except (OSError, ValueError) as exc:
            self._send(409, json.dumps({"ok": False, "message": str(exc)}), "application/json; charset=utf-8")
            return

        files = ", ".join(generated_files(post_id))
        if mode == "draft":
            self._send(200, json.dumps({"ok": True, "message":
                f"Saved blog/{post_filename(post_id)} and posts.js as a local draft (not released)."}))
            return

        self._send(200, json.dumps({"ok": True, "message":
            f"Generated locally for review: {files}. Nothing was committed or pushed."}))

    def log_message(self, format, *args):
        pass

def main():
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://localhost:{PORT}/"
    print(f"Blog publish tool running at:  {url}")
    print("Tip: bookmark this URL. Same network + tool must be running to publish.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
