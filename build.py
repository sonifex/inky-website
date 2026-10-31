#!/usr/bin/env python3
"""Builds the SayInky.com website into docs/ (served by GitHub Pages).

Standard library only, so it runs on any Mac:  python3 build.py

  src/site.json         settings shared by every page (domain, email, company, App Store link)
  src/strings.json      the words around the pages (menu, footer, buttons) in each language
  src/pages/<lang>/     one HTML fragment per page, with a small header block
  static/               copied to docs/ as-is (styles, icons)

A page fragment starts with a header, then a blank line, then the HTML body:

  title: Privacy policy
  description: How Inky handles your family's data.

  <h1>…</h1>

{{key}} in a page is replaced by the value from site.json (for example {{email}}).
English pages live at the root (/privacy/), others under their language (/de/privacy/).
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "docs"

LANGS = ["en", "de", "fr"]  # first one is the default and lives at the root
PAGES = ["index", "privacy", "terms", "support"]  # every language must have all of these


def url_for(lang: str, page: str) -> str:
    prefix = "" if lang == LANGS[0] else f"/{lang}"
    return f"{prefix}/" if page == "index" else f"{prefix}/{page}/"


def read_page(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    head, sep, body = text.partition("\n\n")
    if not sep:
        sys.exit(f"{path}: needs a header, a blank line, then the body")
    meta = {}
    for line in head.splitlines():
        key, colon, value = line.partition(":")
        if not colon:
            sys.exit(f"{path}: bad header line {line!r}")
        meta[key.strip()] = value.strip()
    for key in ("title", "description"):
        if key not in meta:
            sys.exit(f"{path}: missing {key}")
    return meta, body.strip()


def fill(text: str, values: dict[str, str], where: str) -> str:
    def swap(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            sys.exit(f"{where}: unknown placeholder {{{{{key}}}}}")
        return values[key]

    return re.sub(r"\{\{(\w+)\}\}", swap, text)


def render(lang: str, page: str, meta: dict[str, str], body: str, site: dict, s: dict) -> str:
    base = site["base_url"].rstrip("/")
    here = url_for(lang, page)
    is_home = page == "index"
    title = s["brand"] if is_home and meta["title"] == s["brand"] else f'{meta["title"]} · {s["brand"]}'

    alternates = "" if page == "404" else "\n".join(
        f'  <link rel="alternate" hreflang="{l}" href="{base}{url_for(l, page)}">' for l in LANGS
    ) + f'\n  <link rel="alternate" hreflang="x-default" href="{base}{url_for(LANGS[0], page)}">\n  <link rel="canonical" href="{base}{here}">'

    smart_banner = (
        f'  <meta name="apple-itunes-app" content="app-id={site["apple_app_id"]}">\n'
        if site.get("apple_app_id") else ""
    )

    current_page = ' aria-current="page"'
    current_lang = ' aria-current="true"'
    nav = "\n".join(
        f'        <a href="{url_for(lang, p)}"{current_page if p == page else ""}>{s["nav"][p]}</a>'
        for p in ("support", "privacy", "terms")
    )
    switcher = "\n".join(
        f'        <a href="{url_for(l, "index" if page == "404" else page)}" hreflang="{l}" lang="{l}"'
        f'{current_lang if l == lang else ""}>{strings_all[l]["language_name"]}</a>'
        for l in LANGS
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(meta["description"])}">
{alternates}
{smart_banner}  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(meta["description"])}">
  <meta property="og:url" content="{base}{here}">
  <meta property="og:image" content="{base}/assets/inky-1024.png">
  <meta property="og:locale" content="{s["og_locale"]}">
  <meta name="theme-color" content="#2F80ED">
  <link rel="icon" href="/assets/favicon.png" type="image/png">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body class="page-{page}">
  <a class="skip" href="#main">{s["skip"]}</a>
  <header class="top">
    <div class="wrap top-inner">
      <a class="brand" href="{url_for(lang, "index")}">
        <img src="/assets/inky-128.png" alt="" width="40" height="40">
        <span>{s["brand"]}</span>
      </a>
      <nav class="menu" aria-label="{s["menu_label"]}">
{nav}
      </nav>
    </div>
  </header>
  <main id="main" class="{"home" if is_home else "wrap doc"}">
{body}
  </main>
  <footer class="bottom">
    <div class="wrap bottom-inner">
      <nav class="langs" aria-label="{s["language_label"]}">
{switcher}
      </nav>
      <p>{s["footer_contact"]} <a href="mailto:{site["email"]}">{site["email"]}</a></p>
      <p>© {site["year"]} {site["company"]}. {s["footer_trademark"]}</p>
    </div>
  </footer>
</body>
</html>
"""


def main() -> None:
    global strings_all
    site = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
    strings_all = json.loads((SRC / "strings.json").read_text(encoding="utf-8"))

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)

    values = {k: str(v) for k, v in site.items()}
    sitemap = []
    for lang in LANGS:
        s = strings_all[lang]
        values_lang = dict(values)
        values_lang["app_store_button"] = app_store_button(site, s)
        for page in PAGES:
            path = SRC / "pages" / lang / f"{page}.html"
            if not path.exists():
                sys.exit(f"missing page: {path.relative_to(ROOT)}")
            meta, body = read_page(path)
            body = fill(body, values_lang, str(path.relative_to(ROOT)))
            target = OUT / url_for(lang, page).lstrip("/") / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render(lang, page, meta, body, site, s), encoding="utf-8")
            sitemap.append(site["base_url"].rstrip("/") + url_for(lang, page))

    # 404 page: GitHub Pages serves docs/404.html for any missing address.
    s = strings_all[LANGS[0]]
    not_found = render(LANGS[0], "404", {"title": s["not_found_title"], "description": s["not_found_title"]},
                       f'<h1>{s["not_found_title"]}</h1>\n<p>{s["not_found_body"]}</p>', site, s)
    (OUT / "404.html").write_text(not_found, encoding="utf-8")

    (OUT / "CNAME").write_text(site["domain"] + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")  # serve files as they are
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site['base_url'].rstrip('/')}/sitemap.xml\n",
                                    encoding="utf-8")
    urls = "\n".join(f"  <url><loc>{u}</loc></url>" for u in sitemap)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
        encoding="utf-8")

    print(f"Built {len(sitemap) + 1} pages into {OUT.relative_to(ROOT)}/")


def app_store_button(site: dict, s: dict) -> str:
    """The big download button, or a 'coming soon' label until the app is live."""
    if site.get("app_store_url"):
        return (f'<a class="store-button" href="{site["app_store_url"]}">'
                f'<span class="store-small">{s["store_small"]}</span>'
                f'<span class="store-big">App Store</span></a>')
    return f'<p class="store-soon">{s["store_soon"]}</p>'


strings_all: dict = {}

if __name__ == "__main__":
    main()
