/* ============================================================
   Blog posts — isakzvegelj.com/blog
   ------------------------------------------------------------
   Add posts with `python3 blog/publish.py` from the repository
   root. The tool creates this entry, a static article page, and
   the sitemap entry together. The template below documents the
   data shape for legacy/manual maintenance.
   ============================================================ */

window.BLOG_POSTS = [

  /* ---------- TEMPLATE (copy me) ----------
  {
    id: "slug-for-the-url",            // unique, lowercase, dashes
    url: "slug-for-the-url.html",       // publisher-created; omit without a matching static page
    title: "Your post title",
    date: "2026-08-03",                // YYYY-MM-DD
    tag: "Update",                     // e.g. Update, Racing, Building
    excerpt: "One-line summary shown on the blog list page.",
    content: `
      <p>Write the article here. You can use HTML: <strong>bold</strong>,
      <em>italics</em>, lists, links, images, headings.</p>
      <h2>A section</h2>
      <p>More text.</p>
    `
  },
  ---------- END TEMPLATE ---------- */

];
