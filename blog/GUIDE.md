# How to make a blog post — isakzvegelj.com/blog

The absolute easiest way: use the **publish tool**. You type a title and
your article into a simple page, click **Publish**, and it is pushed to the staging branch for review —
no HTML, no git, no terminal needed.

---

## The one-click way (recommended)

1. Open a terminal and run:

       bash /Users/isakzvegelj/isak/personal-site/blog/start.sh

   (It opens the "New blog post" page in your browser automatically.
   Bookmark http://localhost:8123/ too — the tool must be running to
   publish, so keep this tab open when you want to post.)

2. Fill in:
   - **Title** — the headline.
   - **Date** — defaults to today.
   - **Tag** — optional small label (Update, Racing, Building…).
   - **Status** — *Publish live* (recommended) or *Save draft only*.
   - **Article** — type or paste plain text. No HTML needed.

3. Click **Publish**. It writes the post, commits, pushes to GitHub,
   and within about a minute it's live at isakzvegelj.com/blog.

You can even hand me a pure-text draft and I'll drop it in for you.
But with this tool you never have to ask.

### Handy markdown you can use in the article box (all optional)

| you type           | you get           |
|--------------------|-------------------|
| `## Heading`       | a section heading |
| `**bold**`         | bold text         |
| `*italic*`         | italic text       |
| `- bullet`         | a bulleted list   |
| blank line         | a new paragraph   |
| `![alt](url)`      | an image          |
| `[text](url)`      | a link            |

Plain text with blank lines between paragraphs works fine too — you
don't have to learn any of this.

---

## Older way — edit posts.js by hand

Your blog lives at `/Users/isakzvegelj/isak/personal-site/blog/`.
The whole thing is static and driven by one data file, `blog/posts.js`.
To publish a post you add one entry to that file, then commit + push.
The site's staging branch is for review; merge it into `main` only after approval.

If you want to do it by hand, here's exactly what to do.

### Step 1 — Open the right file

    /Users/isakzvegelj/isak/personal-site/blog/posts.js

### Step 2 — Understand the format

The file is one JavaScript array named `window.BLOG_POSTS`.
Everything between `[` and `]` is a list of posts. Each post is one
`{ ... }` block. See the comment block at the top of the file for a
copy-paste template.

A post has these fields:

| field     | what it is                                              |
|-----------|---------------------------------------------------------|
| `id`      | short unique url slug, lowercase with dashes, e.g. `paris-2028-preps` |
| `title`   | the headline shown on the list and at the top of the post |
| `date`    | `YYYY-MM-DD`, e.g. `2026-08-03`                          |
| `tag`     | small label, e.g. `Update`, `Racing`, `Building`          |
| `excerpt` | one-line summary shown on the blog listing page          |
| `content` | the article body — written in HTML (backticks around it) |

### Step 3 — Copy the template and fill it in

Copy this, paste it just above the closing `];`, and replace the values:

    {
      id: "my-first-post",
      title: "My first post",
      date: "2026-08-03",
      tag: "Update",
      excerpt: "A short line describing what this post is about.",
      content: `
        <p>Hello! This is my first blog post.</p>
        <h2>A section</h2>
        <p>Some more text here. Read on…</p>
        <ul>
          <li>Point one</li>
          <li>Point two</li>
        </ul>
        <p>Here is a <a href="https://example.com">link</a>.</p>
      `
    }

Rules to remember:

- **Comma between posts.** If there is already a post above yours,
  make sure there's a comma after the one before it.
- **`id` must be unique** and different from every other post.
- **`content` is HTML**, not plain text. Use `<p>`, `<h2>`, `<ul>/<li>`,
  `<strong>`, `<em>`, `<a>`, `<img>`, `<blockquote>`. It all gets rendered.
- Keep the backticks — they tell the site where the content starts/ends.

### Step 4 — Add an image (optional)

Put the image file in `/Users/isakzvegelj/isak/personal-site/blog/`
(or in `assets/img/`), then reference it from the content. If you save it
as `blog/my-photo.webp`:

    <img src="my-photo.webp" alt="Short description of the photo">

Supported formats: `.webp` (best), `.jpg`, `.png`.

### Step 5 — Verify it looks right (optional but nice)

Preview locally before publishing:

    cd /Users/isakzvegelj/isak/personal-site
    python3 -m http.server 8877

Then open http://localhost:8877/blog/ in your browser. Click your post to
see the full article. Hit Ctrl+C when done.

### Step 6 — Publish

    cd /Users/isakzvegelj/isak/personal-site
    git add blog/posts.js
    git commit -m "Add blog post: <your title>"
    git push origin staging

# Promote only after review: git switch main && git merge --no-ff staging && git push origin main

Wait about a minute, then check https://isakzvegelj.com/blog/

---

## Handy tips

- **Order.** Posts appear in the order they're listed in the file
  (first = top). Put your newest post at the **top** of the array, right
  under `[`, to keep the newest article first on the site.
- **Just paste ChatGPT / a draft** and ask me to format it — I'll turn
  your notes into clean HTML and publish.
- **Scheduling / reminders:** if you want, I can set up a recurring thing
  where the site nudges you to post, but nothing is required.

---

## Troubleshooting

- **Post not showing** → your `id`, `title`, etc. may have a typo, or
  the file has a JS error (missing comma/brace). Ask me to check it —
  I verify the file parses before it publishes.
- **Formatting looks off** → make sure `content` is proper HTML and
  closed tags (e.g. `<p>...</p>`, not just `<p>`).
- **Still stuck** → just tell me "add a post about X" and I'll do it.
