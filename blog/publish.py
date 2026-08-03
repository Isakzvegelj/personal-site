#!/usr/bin/env python3
"""Isak's blog publish tool — type an article, hit Publish, it's live.

Run:  python3 /Users/isakzvegelj/projects/personal-site/blog/publish.py
Then open the printed URL in your browser.

The page lets you paste a title + article (plain text or light markdown),
click Publish, and it:
  1. converts your text to HTML
  2. appends a new entry to blog/posts.js
  3. commits and pushes to GitHub (main) -> isakzvegelj.com/blog goes live.

Stdlib only. No installs.
"""
import http.server
import json
import os
import re
import subprocess
import sys
import urllib.parse
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))          # .../blog
REPO = os.path.dirname(BASE)                                # .../personal-site
POSTS_FILE = os.path.join(BASE, "posts.js")
LIVE_URL = "https://isakzvegelj.com/blog/"

HOST = "127.0.0.1"
PORT = int(os.environ.get("BLOG_PORT", "8123"))

# ---------------------------------------------------------------- markdown -> html
def _inline(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
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
            out.append(f'<img src="{m.group(2)}" alt="{m.group(1)}">'); i += 1; continue
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

def make_entry(title, tag, date, excerpt, content_html):
    obj = {
        "id": slugify(title),
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

def git(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)

def publish(entry):
    insert_into_posts(entry)
    git(["git", "add", "blog/posts.js"])
    git(["git", "commit", "-m", f"Add blog post"])
    pull = git(["git", "pull", "--rebase", "origin", "main"])
    push = git(["git", "push", "origin", "main"])
    if pull.returncode != 0:
        return False, "git pull failed: " + pull.stderr.strip()
    if push.returncode != 0:
        return False, "git push failed: " + push.stderr.strip()
    return True, ""

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
<p class="sub">Write it, click <strong>Publish</strong> — it goes live on isakzvegelj.com/blog.</p>
<form id="form">
  <label>Title</label>
  <input type="text" id="title" name="title" placeholder="e.g. World Cup prep update" required>

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
        <option value="publish">Publish live</option>
        <option value="draft">Save draft only</option>
      </select>
    </div>
  </div>

  <label>Article (plain text or light markdown)</label>
  <textarea id="content" name="content" rows="14" placeholder="Write your post here.&#10;&#10;## A heading&#10;&#10;Some paragraph text. **bold** and *italic* work.&#10;&#10;- bullet one&#10;- bullet two&#10;&#10;![caption](https://example.com/photo.jpg)"></textarea>

  <button type="submit" class="btn">Publish</button>
  <span id="status"></span>
</form>
<p class="hint" style="margin-top:26px">Markdown you can use: <code>## heading</code>, <code>**bold**</code>, <code>*italic*</code>, <code>- bullet</code>, blank line = new paragraph, <code>![alt](url)</code> = image. Or just paste plain text and hit Publish.</p>
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
    btn.disabled = true; btn.textContent = 'Publishing…';
    fetch('/publish', {method:'POST', body:new URLSearchParams(fd)})
      .then(function(r){return r.json();})
      .then(function(d){
        btn.disabled=false; btn.textContent='Publish';
        st.className = d.ok ? 'ok' : 'err';
        st.textContent = d.message;
      })
      .catch(function(err){
        btn.disabled=false; btn.textContent='Publish';
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
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, PAGE)

    def do_POST(self):
        if self.path.rstrip("/") != "/publish":
            self._send(404, json.dumps({"ok": False, "message": "not found"}))
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        form = urllib.parse.parse_qs(body)
        g = lambda k: (form.get(k) or [""])[0].strip()
        title = g("title"); content = g("content")
        tag = g("tag") or "Update"
        date = g("date")
        mode = g("mode") or "publish"
        if not title:
            self._send(200, json.dumps({"ok": False, "message": "Please add a title."})); return
        if not content:
            self._send(200, json.dumps({"ok": False, "message": "The article is empty."})); return

        html = md_to_html(content)
        entry = make_entry(title, tag, date, "", html)

        if mode == "draft":
            insert_into_posts(entry)
            self._send(200, json.dumps({"ok": True, "message":
                "Saved as a draft in blog/posts.js (not pushed). It is NOT live yet."}))
            return

        ok, err = publish(entry)
        if ok:
            self._send(200, json.dumps({"ok": True, "message":
                "Published! It's live at " + LIVE_URL + " (appears within ~1 min)."}))
        else:
            self._send(200, json.dumps({"ok": False, "message": err}))

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
