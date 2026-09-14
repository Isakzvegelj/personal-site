#!/usr/bin/env python3
"""Small dependency-free checks for the static site."""
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.refs = []
        self.headings = []
        self._heading = None
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for name in ("href", "src"):
            value = attrs.get(name)
            if value:
                self.refs.append(value)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading = [tag, ""]
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if self._heading and tag == self._heading[0]:
            self.headings.append(self._heading)
            self._heading = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._heading:
            self._heading[1] += data


def local_target(page, reference):
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or reference.startswith("/"):
        return None
    path = parsed.path
    if not path:
        return None
    return (page.parent / path).resolve()


def validate_page(page):
    parser = PageParser()
    parser.feed(page.read_text(encoding="utf-8"))
    errors = []
    for value in set(parser.ids):
        if parser.ids.count(value) > 1:
            errors.append(f"{page}: duplicate id {value!r}")
    if not parser.title.strip():
        errors.append(f"{page}: missing title")
    for tag, text in parser.headings:
        if not text.strip():
            errors.append(f"{page}: empty {tag}")
    for reference in parser.refs:
        target = local_target(page, reference)
        if target is not None and not target.exists():
            errors.append(f"{page}: missing local reference {reference!r}")
    return errors


def main():
    errors = []
    pages = sorted(ROOT.rglob("*.html"))
    for page in pages:
        errors.extend(validate_page(page))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(pages)} HTML pages and their local references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
