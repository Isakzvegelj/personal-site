/* ============================================================
   Blog posts — isakzvegelj.com/blog
   ------------------------------------------------------------
   Add posts with `python3 blog/publish.py` from the repository
   root. The tool creates this entry, a static article page, and
   the sitemap entry together. The template below documents the
   data shape for legacy/manual maintenance.
   ============================================================ */

window.BLOG_POSTS = [
  {
    "id": "hospitality-website-checklist",
    "url": "hospitality-website-checklist.html",
    "title": "A practical website checklist for hotels and hospitality businesses",
    "date": "2026-11-01",
    "tag": "Building",
    "excerpt": "Planning a hotel or hospitality website? A practical checklist covering mobile usability, guest information, booking handoffs and useful measurement.",
    "content": "<p>A hospitality website should help a guest decide whether a place fits their stay and make the next step clear. My portfolio includes hotel, accommodation and breakfast websites in Bled. Here is a practical checklist to use when planning a new site or reviewing an existing one.</p>\n<h2>Make the essentials easy to find</h2>\n<p>Give guests the location, the type of stay or meal, what is included and the next step. Use photographs that represent the actual property or business. Keep seasonal details, opening hours and contact information current.</p>\n<h2>Design the journey for a phone</h2>\n<p>Check the site on a small screen. Guests should be able to read room information, browse photographs and find a booking or enquiry action without fighting tiny controls. Use appropriately sized images so a visitor does not have to download desktop-sized photographs for every thumbnail.</p>\n<h2>Connect booking and enquiries clearly</h2>\n<p>A hotel may need live availability and a booking provider; a restaurant may need a table enquiry. Explain what happens when a guest taps the button. If the action opens an email app, say so. Test the handoff without placing an unintended booking.</p>\n<h2>Give each page a clear purpose</h2>\n<p>Write useful page titles and descriptions. Keep important information in readable HTML, link related pages, and maintain the sitemap when content changes. Search visibility depends on useful information and whether people can discover it; a checklist cannot promise rankings or bookings.</p>\n<h2>Measure enquiries and confirmed bookings</h2>\n<p>Search impressions, clicks, enquiries and confirmed bookings are different measures. Use Search Console to understand discovery and your actual booking or business records to understand outcomes. Compare equivalent periods and account for seasonality.</p>\n<h2>Explore live examples</h2>\n<p><a href=\"https://villa-pomona-bled.com/\">Villa Pomona Bled</a> is a hotel project. <a href=\"https://maxisbled.com/\">Maxis Penthouse</a> presents accommodation, and <a href=\"https://adorabreakfast.com/\">Adora Breakfast</a> focuses on hospitality. These are portfolio examples, not claims of measured booking or revenue improvements.</p>\n<h2>Start with your business goals</h2>\n<p>For a website project, send your business name, current site, the customers you want to reach, essential features, budget range and preferred launch date. View my projects and start a conversation.</p>"
  },

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
