#!/usr/bin/env python3
"""Focused regression tests for the local blog publisher."""
import json
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import publish


class PublishSafetyTests(unittest.TestCase):
    def workspace(self, stack):
        tmp = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        blog = tmp / "blog"
        blog.mkdir()
        posts = blog / "posts.js"
        posts.write_text("window.BLOG_POSTS = [\n\n];\n", encoding="utf-8")
        template = blog / "post.html"
        template.write_text(Path(publish.POST_TEMPLATE_FILE).read_text(encoding="utf-8"), encoding="utf-8")
        sitemap = tmp / "sitemap.xml"
        sitemap.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            '  <url><loc>https://isakzvegelj.com/</loc></url>\n'
            '</urlset>\n',
            encoding="utf-8",
        )
        stack.enter_context(patch.object(publish, "BASE", str(blog)))
        stack.enter_context(patch.object(publish, "REPO", str(tmp)))
        stack.enter_context(patch.object(publish, "POSTS_FILE", str(posts)))
        stack.enter_context(patch.object(publish, "POST_TEMPLATE_FILE", str(template)))
        stack.enter_context(patch.object(publish, "SITEMAP_FILE", str(sitemap)))
        return blog, posts, sitemap

    def test_csrf_rejects_missing_and_malicious_tokens(self):
        self.assertTrue(publish.is_valid_csrf(publish.CSRF_TOKEN))
        self.assertFalse(publish.is_valid_csrf(""))
        self.assertFalse(publish.is_valid_csrf("attacker-token"))

    def test_duplicate_slug_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            posts = Path(tmp) / "posts.js"
            posts.write_text('window.BLOG_POSTS = [\n  { "id": "same-title" }\n];\n', encoding="utf-8")
            with patch.object(publish, "POSTS_FILE", str(posts)):
                with self.assertRaisesRegex(ValueError, "same-title"):
                    publish.ensure_unique_slug("Same Title")

    def test_entry_has_safe_static_url_and_rejects_traversal(self):
        entry = publish.make_entry("Example", "Update", "2026-08-19", "Summary", "<p>Body</p>", "example-title")
        self.assertIn('"id": "example-title"', entry)
        self.assertIn('"url": "example-title.html"', entry)
        with self.assertRaises(ValueError):
            publish.post_filename("../escape")
        with self.assertRaises(ValueError):
            publish.post_filename("double--dash")

    def test_excerpt_generation_and_unsafe_markdown_urls(self):
        content = publish.md_to_html(
            "A **useful** summary with [safe](https://example.com).\n\n"
            "[bad](javascript:alert(1))\n\n![bad](data:text/html,x)"
        )
        self.assertIn('href="https://example.com"', content)
        self.assertNotIn("javascript:", content)
        self.assertNotIn("data:text", content)
        self.assertTrue(publish.excerpt_from_html(content).startswith("A useful summary"))

    def test_static_page_has_escaped_metadata_and_structured_data(self):
        page = publish.render_post_page(
            'A "quoted" </title> update',
            "Racing & Results",
            "2026-08-19",
            'A summary with "quotes" & details.',
            "<p>Safe <strong>article</strong> body.</p>",
            "quoted-update",
        )
        self.assertIn("https://isakzvegelj.com/blog/quoted-update.html", page)
        self.assertIn("A &quot;quoted&quot; &lt;/title&gt; update", page)
        self.assertIn("Racing &amp; Results", page)
        self.assertIn("Safe <strong>article</strong> body", page)
        self.assertNotIn('src="posts.js"', page)
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page)
        self.assertIsNotNone(match)
        structured = json.loads(match.group(1))
        self.assertEqual(structured["@type"], "BlogPosting")
        self.assertEqual(structured["datePublished"], "2026-08-19")

    def test_draft_creates_page_and_entry_without_sitemap(self):
        with ExitStack() as stack:
            blog, posts, sitemap = self.workspace(stack)
            before = sitemap.read_text(encoding="utf-8")
            destination = publish.save_post_files(
                "Draft Article", "Building", "2026-08-19", "", "<p>Draft body.</p>", "draft-article", False
            )
            self.assertEqual(Path(destination), blog / "draft-article.html")
            self.assertTrue(Path(destination).exists())
            self.assertIn('"url": "draft-article.html"', posts.read_text(encoding="utf-8"))
            self.assertEqual(sitemap.read_text(encoding="utf-8"), before)

    def test_published_post_updates_sitemap_once(self):
        with ExitStack() as stack:
            blog, posts, sitemap = self.workspace(stack)
            publish.save_post_files(
                "Published Article", "Update", "2026-08-19", "A summary", "<p>Published body.</p>", "published-article", True
            )
            sitemap_text = sitemap.read_text(encoding="utf-8")
            canonical = "https://isakzvegelj.com/blog/published-article.html"
            self.assertEqual(sitemap_text.count(canonical), 1)
            self.assertFalse(publish.update_sitemap("published-article", "2026-08-19"))
            self.assertEqual(sitemap.read_text(encoding="utf-8").count(canonical), 1)
            self.assertTrue((blog / "published-article.html").exists())
            self.assertIn("published-article.html", posts.read_text(encoding="utf-8"))

    def test_static_page_collision_is_not_overwritten(self):
        with ExitStack() as stack:
            blog, _posts, _sitemap = self.workspace(stack)
            target = blog / "existing-page.html"
            target.write_text("keep me", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                publish.write_post_page("existing-page", "replacement")
            self.assertEqual(target.read_text(encoding="utf-8"), "keep me")

    def test_publish_stages_only_generated_files(self):
        success = SimpleNamespace(returncode=0, stderr="")
        with patch.object(publish, "git", return_value=success) as mocked:
            ok, error = publish.publish("new-post")
        self.assertTrue(ok)
        self.assertEqual(error, "")
        first_command = mocked.call_args_list[0].args[0]
        self.assertEqual(
            first_command,
            ["git", "add", "blog/posts.js", "blog/new-post.html", "sitemap.xml"],
        )
        commit_command = mocked.call_args_list[1].args[0]
        self.assertEqual(commit_command[-4:], ["--", "blog/posts.js", "blog/new-post.html", "sitemap.xml"])

    def test_blog_index_prefers_safe_static_url_with_legacy_fallback(self):
        source = (Path(publish.BASE) / "index.html").read_text(encoding="utf-8")
        self.assertIn("typeof p.url === 'string'", source)
        self.assertIn("post.html?id=", source)

    def test_http_endpoint_rejects_bad_csrf_and_disables_caching(self):
        server = publish.http.server.HTTPServer(("127.0.0.1", 0), publish.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urllib.request.urlopen(base + "/", timeout=5) as response:
                page = response.read().decode()
                self.assertIn(publish.CSRF_TOKEN, page)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(response.headers["X-Frame-Options"], "DENY")
                self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
                self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
            request = urllib.request.Request(
                base + "/publish",
                data=b"title=x&content=y&csrf_token=wrong",
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=5)
            self.assertEqual(raised.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
