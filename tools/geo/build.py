#!/usr/bin/env python3
"""Build Revé guide pages from Markdown.

Each file in content/guides/*.md becomes /guides/<slug>/index.html in the
site's own look, with Article, FAQPage, BreadcrumbList (and, for glossaries,
DefinedTermSet) JSON-LD. The script also rebuilds:

  /guides/index.html   hub page that links every guide and product page
  /sitemap.xml         every public page, with <lastmod> for guides
  /llms.txt            plain-text map of the site for AI assistants

No third-party packages: needs Python 3.11+ (tomllib).

Usage:  python3 tools/geo/build.py          # build everything
        python3 tools/geo/build.py --check  # build, then fail if anything is stale

Front matter is TOML between +++ lines. See content/guides/README.md.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content" / "guides"
SITE = "https://usereve.com"
APP_URL = "https://apps.apple.com/us/app/reve-peptide-cycle-tracker/id6810085933"
APP_NAME = "Reve: Peptide & Cycle Tracker"
OG_IMAGE = f"{SITE}/assets/og-image.png"
CSS_VERSION = "guides-1"
# Google tag (GA4). Same snippet as the hand-written pages; must sit right after <head>.
GOOGLE_TAG = """<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-TFD2QR3K"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
</script>"""

ORGANIZATION = {
    "@type": "Organization",
    "@id": f"{SITE}/#organization",
    "name": "Revé",
    "legalName": "Trendset Enterprises LLC",
    "url": f"{SITE}/",
    "logo": f"{SITE}/assets/reve-wordmark.png",
    "email": "zareef@usereve.com",
    "address": {"@type": "PostalAddress", "addressLocality": "New York", "addressRegion": "NY", "addressCountry": "US"},
    # Add every official profile here (X, Instagram, TikTok, LinkedIn...). sameAs is
    # how search engines and LLMs connect the brand to its accounts.
    "sameAs": [APP_URL],
}

# Filled when related_guides names fewer than this many other guides.
RELATED_GUIDE_SLOTS = 3

# Brand pages. The slug list covers pricing and privacy, which may land after
# this change. The category covers any later page filed under the same eyebrow.
ABOUT_REVE_SLUGS = frozenset({
    "how-much-does-reve-cost",
    "is-reve-legit",
    "reve-privacy",
})
ABOUT_REVE_CATEGORY = "About Revé"

# Pages that exist outside the generator. Order = order in footer and hub.
PRODUCT_PAGES = [
    ("/peptide-tracker-for-women/", "Peptide Tracker for Women"),
    ("/supplement-tracker-for-women/", "Supplement Tracker for Women"),
    ("/glp-1-tracker-for-women/", "GLP-1 Tracker for Women"),
    ("/peptide-menstrual-cycle-tracker/", "Peptide & Menstrual Cycle Tracker"),
    ("/womens-peptide-app/", "Women's Peptide App"),
    ("/peptide-and-cycle-log-template/", "Peptide & Cycle Log Template"),
    ("/notes-for-your-clinician/", "Notes for Your Clinician"),
    ("/progress-tracking-by-cycle-phase/", "Progress by Cycle Phase"),
    ("/what-to-track-in-a-peptide-journal/", "Peptide Journal"),
    ("/choosing-a-peptide-tracker-app/", "Choosing a Peptide Tracker App"),
    ("/cycle-phase-calculator/", "Cycle Phase Calculator"),
    ("/faq/", "FAQ"),
]

e = html.escape


# --------------------------------------------------------------------------- #
# Markdown (small, predictable subset)
# --------------------------------------------------------------------------- #

def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text.lower().replace("&", " and "))
    return re.sub(r"[\s-]+", "-", text).strip("-")[:60]


def inline(text: str) -> str:
    """Escape, then apply links, code, bold, italic."""
    out = e(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)

    def link(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        url = url.replace('"', "%22")
        ext = url.startswith("http") and not url.startswith(SITE)
        rel = ' rel="noopener"' if ext else ""
        return f'<a href="{url}"{rel}>{label}</a>'

    out = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", out)
    return out


def plain(text: str) -> str:
    """Markdown inline -> plain text (for schema and meta)."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def md_to_html(md: str):
    lines = md.strip("\n").split("\n")
    out: list[str] = []
    toc: list[tuple[str, str]] = []
    terms: list[tuple[str, str]] = []
    para: list[str] = []
    pending_term: str | None = None
    used_ids: set[str] = set()
    i = 0

    def uid(text: str) -> str:
        base = slugify(text) or "section"
        cand, n = base, 2
        while cand in used_ids:
            cand, n = f"{base}-{n}", n + 1
        used_ids.add(cand)
        return cand

    def flush():
        nonlocal para, pending_term
        if para:
            txt = " ".join(s.strip() for s in para)
            out.append(f"<p>{inline(txt)}</p>")
            if pending_term:
                terms.append((pending_term, plain(txt)))
                pending_term = None
            para = []

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith("<"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip():
                block.append(lines[i]); i += 1
            out.append("\n".join(block))
            continue
        m = re.match(r"^(#{2,3})\s+(.*)$", s)
        if m:
            flush()
            level, text = len(m.group(1)), m.group(2).strip()
            hid = uid(text)
            if level == 2:
                toc.append((hid, plain(text)))
                out.append(f'<h2 id="{hid}">{inline(text)}</h2>')
            else:
                out.append(f'<h3 id="{hid}">{inline(text)}</h3>')
                pending_term = plain(text)
            i += 1; continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            head, body = cells[0], [r for r in cells[1:] if not re.fullmatch(r"[\s:|-]*", "|".join(r))]
            t = ['<div class="table-wrap"><table>', "<thead><tr>"]
            t += [f'<th scope="col">{inline(c)}</th>' for c in head]
            t += ["</tr></thead><tbody>"]
            for r in body:
                t.append("<tr>" + "".join(
                    (f'<th scope="row">{inline(c)}</th>' if j == 0 else f"<td>{inline(c)}</td>")
                    for j, c in enumerate(r)) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if re.match(r"^([-*]|\d+\.)\s+", s):
            flush()
            ordered = bool(re.match(r"^\d+\.", s))
            items: list[str] = []
            while i < len(lines):
                cur = lines[i]
                mm = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", cur)
                if mm and (bool(re.match(r"\d+\.", mm.group(1))) == ordered):
                    items.append(mm.group(2)); i += 1
                elif cur.startswith("  ") and cur.strip() and items:
                    items[-1] += " " + cur.strip(); i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if s.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip()); i += 1
            out.append(f'<aside class="callout"><p>{inline(" ".join(quote))}</p></aside>')
            continue
        para.append(line); i += 1
    flush()
    return "\n".join(out), toc, terms


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

REQUIRED = ["title", "h1", "slug", "description", "lede", "summary", "category", "published", "updated"]


def load_guides() -> list[dict]:
    guides = []
    for path in sorted(CONTENT.glob("*.md")):
        if path.name.upper().startswith("README") or path.name.startswith("_"):
            continue
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^\+\+\+\n(.*?)\n\+\+\+\n(.*)$", raw, re.S)
        if not m:
            raise SystemExit(f"{path.name}: missing +++ TOML front matter")
        meta = tomllib.loads(m.group(1))
        missing = [k for k in REQUIRED if k not in meta]
        if missing:
            raise SystemExit(f"{path.name}: missing {', '.join(missing)}")
        if meta.get("draft"):
            continue
        for k in ("published", "updated"):
            if isinstance(meta[k], dt.datetime):
                meta[k] = meta[k].date()
        if len(meta["description"]) > 165:
            print(f"warning: {path.name} description is {len(meta['description'])} chars (aim for <=160)")
        meta["body"] = m.group(2)
        meta["url"] = f"{SITE}/guides/{meta['slug']}/"
        meta["path"] = f"/guides/{meta['slug']}/"
        guides.append(meta)
    slugs = [g["slug"] for g in guides]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slug in content/guides")
    return sorted(guides, key=lambda g: (g["updated"], g["published"]), reverse=True)


def fmt_date(d: dt.date) -> str:
    return d.strftime("%b %-d, %Y")


# --------------------------------------------------------------------------- #
# Page chrome
# --------------------------------------------------------------------------- #

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '  <link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&amp;'
         'family=IBM+Plex+Mono:wght@400;500&amp;family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;'
         '1,6..72,400;1,6..72,500&amp;display=swap" rel="stylesheet">')


def head(title: str, description: str, url: str, og_type: str, schema: dict, extra_meta: str = "") -> str:
    data = json.dumps(schema, indent=2, ensure_ascii=False).replace("</", "<\\/")
    t, d = e(title), e(description)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{GOOGLE_TAG}
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <link rel="canonical" href="{url}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Revé">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Revé wordmark on a cream background">{extra_meta}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t}">
  <meta name="twitter:description" content="{d}">
  <meta name="twitter:image" content="{OG_IMAGE}">
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">
  <meta name="apple-itunes-app" content="app-id=6810085933">
  <meta name="theme-color" content="#FBF9F4">
  {FONTS}
  <link rel="stylesheet" href="/assets/content.css?v=footer-groups-2">
  <link rel="stylesheet" href="/assets/guide.css?v={CSS_VERSION}">
  <script type="application/ld+json">
{data}
  </script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header>
    <div class="wrap nav">
      <a href="/" aria-label="Revé home"><img src="/assets/reve-wordmark.png" alt="Revé" class="wordmark-img" width="640" height="191"></a>
      <nav class="nav-links" aria-label="Main navigation">
        <a href="/guides/">Guides</a>
        <a href="/faq/">FAQ</a>
        <a href="/#company">Company</a>
        <a href="mailto:zareef@usereve.com">Contact</a>
      </nav>
    </div>
  </header>
"""


COPYRIGHT_YEAR = 2026  # bumped automatically below to the newest guide's year


def footer(current: str = "") -> str:
    def a(path, label):
        cur = ' aria-current="page"' if path == current else ""
        return f'          <a href="{path}"{cur}>{e(label)}</a>'
    explore = "\n".join([a("/guides/", "Guides")] + [a(p, l) for p, l in PRODUCT_PAGES])
    return f"""  <footer>
    <div class="wrap footer-layout">
      <div class="footer-brand">
        <a href="/" aria-label="Revé home"><img src="/assets/reve-wordmark.png" alt="Revé" class="wordmark-img" width="640" height="191"></a>
        <p class="foot-legal">© {COPYRIGHT_YEAR} Trendset Enterprises LLC · New York, USA</p>
      </div>
      <nav class="footer-groups" aria-label="Footer navigation">
        <div class="footer-group" role="group" aria-labelledby="footer-explore">
          <span id="footer-explore" class="eyebrow">Explore</span>
{explore}
        </div>
        <div class="footer-group" role="group" aria-labelledby="footer-company">
          <span id="footer-company" class="eyebrow">Company</span>
          <a href="/guides/is-reve-legit/">About Revé</a>
          <a href="mailto:zareef@usereve.com">Contact</a>
        </div>
        <div class="footer-group" role="group" aria-labelledby="footer-legal">
          <span id="footer-legal" class="eyebrow">Legal</span>
          <a href="https://legal.usereve.com/privacy">Privacy Policy</a>
          <a href="https://legal.usereve.com/terms">Terms of Service</a>
        </div>
      </nav>
    </div>
  </footer>
</body>
</html>
"""


APP_CTA = f"""<div class="app-store-cta">
            <a href="{APP_URL}"><img src="/assets/app-store-badge.svg" alt="Download {e(APP_NAME)} on the App Store" width="120" height="40"></a>
            <span class="search-note">Search {e(APP_NAME)} on the App Store.</span>
          </div>"""


# --------------------------------------------------------------------------- #
# Guide page
# --------------------------------------------------------------------------- #

def is_about_reve(guide: dict) -> bool:
    category = str(guide.get("category", "")).strip()
    return guide.get("slug") in ABOUT_REVE_SLUGS or category.casefold() == ABOUT_REVE_CATEGORY.casefold()


def related_guides_for(guide: dict, all_guides: list[dict]) -> list[dict]:
    """Manual related_guides, then same category, then other guides, up to 3.

    About Revé pages are not added automatically to guides outside that set.
    A slug named in related_guides is kept either way.
    """
    named = set(guide.get("related_guides") or [])
    manual = [item for item in all_guides if item["slug"] in named and item["slug"] != guide["slug"]]
    if len(manual) >= RELATED_GUIDE_SLOTS:
        return manual
    taken = {item["slug"] for item in manual}
    taken.add(guide["slug"])
    pool = [item for item in all_guides if item["slug"] not in taken]
    if not is_about_reve(guide):
        pool = [item for item in pool if not is_about_reve(item)]
    category = guide.get("category")
    same = [item for item in pool if item.get("category") == category]
    other = [item for item in pool if item.get("category") != category]
    need = RELATED_GUIDE_SLOTS - len(manual)
    return manual + (same + other)[:need]


def render_guide(g: dict, all_guides: list[dict]) -> str:
    body_html, toc, terms = md_to_html(g["body"])
    summary_html, _, _ = md_to_html(g["summary"])
    faq = g.get("faq", [])
    sources = g.get("sources", [])
    url = g["url"]

    author = {"@id": f"{SITE}/#organization"}
    article = {
        "@type": g.get("schema_type", "Article"),
        "@id": f"{url}#article",
        "headline": g["title"].replace(" | Revé", ""),
        "description": g["description"],
        "datePublished": g["published"].isoformat(),
        "dateModified": g["updated"].isoformat(),
        "author": author,
        "publisher": {"@id": f"{SITE}/#organization"},
        "mainEntityOfPage": url,
        "image": OG_IMAGE,
        "inLanguage": "en-US",
    }
    if g.get("reviewed_by"):
        article["reviewedBy"] = {"@type": "Person", "name": g["reviewed_by"],
                                 **({"jobTitle": g["reviewer_credentials"]} if g.get("reviewer_credentials") else {})}
    if g.get("about"):
        article["about"] = [{"@type": "Thing", "name": x} for x in g["about"]]
    if sources:
        article["citation"] = [s["url"] for s in sources]
    graph = [ORGANIZATION,
             {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "Revé", "url": f"{SITE}/",
              "publisher": {"@id": f"{SITE}/#organization"}},
             article,
             {"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                 {"@type": "ListItem", "position": 2, "name": "Guides", "item": f"{SITE}/guides/"},
                 {"@type": "ListItem", "position": 3, "name": g.get("crumb", plain(g["h1"])), "item": url}]}]
    if faq:
        graph.append({"@type": "FAQPage", "@id": f"{url}#faq", "mainEntity": [
            {"@type": "Question", "name": plain(f["q"]),
             "acceptedAnswer": {"@type": "Answer", "text": plain(f["a"])}} for f in faq]})
    if g.get("glossary") and terms:
        graph.append({"@type": "DefinedTermSet", "@id": f"{url}#terms", "name": plain(g["h1"]),
                      "hasDefinedTerm": [{"@type": "DefinedTerm", "name": n, "description": d,
                                          "url": f"{url}#{slugify(n)}"} for n, d in terms]})
    schema = {"@context": "https://schema.org", "@graph": graph}

    extra = (f'\n  <meta property="article:published_time" content="{g["published"].isoformat()}">'
             f'\n  <meta property="article:modified_time" content="{g["updated"].isoformat()}">'
             f'\n  <meta property="article:author" content="Revé">')

    reviewed = ""
    if g.get("reviewed_by"):
        cred = f', {e(g["reviewer_credentials"])}' if g.get("reviewer_credentials") else ""
        reviewed = f' · Reviewed by {e(g["reviewed_by"])}{cred}'
    byline = (f'<p class="byline">By the Revé editorial team · Updated '
              f'<time datetime="{g["updated"].isoformat()}">{fmt_date(g["updated"])}</time>{reviewed}</p>')

    contents = ""
    if len(toc) >= 3:
        items = "\n".join(f'            <li><a href="#{i}"><span>{n:02d}</span>{e(t)}</a></li>'
                          for n, (i, t) in enumerate(toc, 1))
        contents = f"""
        <nav class="contents" aria-label="On this page">
          <p class="eyebrow">On this page</p>
          <ul>
{items}
          </ul>
        </nav>"""

    faq_html = ""
    if faq:
        cards = "\n".join(f"""          <div class="card feature-card">
            <h3>{inline(f['q'])}</h3>
            <p>{inline(f['a'])}</p>
          </div>""" for f in faq)
        faq_html = f"""
      <section id="faq" class="wrap content-section" aria-labelledby="faq-title">
        <div class="head-block">
          <span class="eyebrow">Questions</span>
          <h2 id="faq-title" class="serif-head">{e(g.get('faq_heading', 'Frequently asked questions'))}</h2>
        </div>
        <div class="feature-grid">
{cards}
        </div>
      </section>"""

    sources_html = ""
    if sources:
        items = "\n".join(
            f'            <li><a href="{e(s["url"])}" rel="noopener">{e(s["title"])}</a>'
            f'{" — " + e(s["publisher"]) if s.get("publisher") else ""}'
            f'{" (" + e(s["note"]) + ")" if s.get("note") else ""}</li>' for s in sources)
        sources_html = f"""
      <section id="sources" class="wrap narrow content-section sources" aria-labelledby="sources-title">
        <span class="eyebrow">Sources</span>
        <h2 id="sources-title" class="serif-head">Where these facts come from</h2>
        <p class="body-copy">Checked {fmt_date(g['updated'])}. Labels and listings change; if something here no longer matches the source, the source wins. Tell us at <a href="mailto:zareef@usereve.com">zareef@usereve.com</a>.</p>
        <ol class="sources-list">
{items}
        </ol>
      </section>"""

    related = related_guides_for(g, all_guides)
    rel_links = [(x["path"], plain(x["h1"])) for x in related] + [(p, dict(PRODUCT_PAGES)[p]) for p in g.get("related_pages", [])]
    rel_html = "\n".join(f'          <a class="card related-card" href="{p}"><span>{e(t)}</span></a>' for p, t in rel_links)

    boundary = e(g.get("boundary", "This page is general information, not medical advice. Revé is a personal logging tool. It does not prescribe, recommend doses, or tell you to change a treatment. Talk with a clinician or pharmacist about your own care."))

    return head(g["title"], g["description"], url, "article", schema, extra) + f"""
  <main id="main">
    <article aria-labelledby="page-title">
      <div class="content-hero wrap">
        <nav class="breadcrumbs" aria-label="Breadcrumb">
          <a href="/">Home</a><span aria-hidden="true">/</span><a href="/guides/">Guides</a><span aria-hidden="true">/</span><span aria-current="page">{e(g.get('crumb', plain(g['h1'])))}</span>
        </nav>
        <span class="eyebrow"><span class="dot" aria-hidden="true"></span> {e(g['category'])}</span>
        <h1 id="page-title">{inline(g['h1'])}</h1>
        <p class="lede">{inline(g['lede'])}</p>
        {byline}
      </div>

      <div class="wrap">
        <section class="card short-answer" aria-labelledby="short-answer-title">
          <h2 id="short-answer-title" class="eyebrow">Short answer</h2>
          <div class="short-answer-body">
{summary_html}
          </div>
        </section>{contents}
      </div>

      <div class="wrap narrow prose">
{body_html}
      </div>
{faq_html}
{sources_html}

      <section class="wrap content-section related" aria-labelledby="related-title">
        <span class="eyebrow">Keep reading</span>
        <h2 id="related-title" class="serif-head">Related</h2>
        <div class="related-grid">
{rel_html}
        </div>
      </section>

      <div class="editorial-band">
        <div class="wrap narrow content-section">
          <span class="eyebrow">A clear boundary</span>
          <p class="body-copy">{boundary}</p>
        </div>
      </div>

      <section class="cta" aria-labelledby="download-title">
        <div class="wrap narrow">
          <span class="eyebrow">On the App Store</span>
          <h2 id="download-title" class="serif-head">{e(g.get('cta_heading', 'Your log, tagged to your cycle.'))}</h2>
          <p class="lede">Log peptides, supplements, GLP-1 routines, check-ins, and measurements. Revé tags each one with your cycle day and phase.</p>
          {APP_CTA}
          <p class="disclaimer">Revé helps you see your own logged patterns. It doesn't tell you what to take, and it doesn't predict how you'll respond. It isn't medical advice.</p>
        </div>
      </section>
    </article>
  </main>

""" + footer(g["path"])


# --------------------------------------------------------------------------- #
# Hub, sitemap, llms.txt
# --------------------------------------------------------------------------- #

def page_description(path: str) -> str:
    f = ROOT / path.strip("/") / "index.html"
    text = f.read_text(encoding="utf-8")
    for tag in re.findall(r"<meta\b[^>]*>", text):
        if re.search(r'\bname="description"', tag):
            m = re.search(r'\bcontent="([^"]*)"', tag)
            if m:
                return html.unescape(m.group(1))
    return ""


def render_hub(guides: list[dict]) -> str:
    url = f"{SITE}/guides/"
    desc = ("Guides from Revé on peptides, GLP-1 medications, and the menstrual cycle: label facts, "
            "app comparisons, glossaries, and logging how-tos for women.")
    schema = {"@context": "https://schema.org", "@graph": [
        ORGANIZATION,
        {"@type": "CollectionPage", "@id": f"{url}#page", "url": url, "name": "Revé Guides", "description": desc,
         "isPartOf": {"@id": f"{SITE}/#website"},
         "mainEntity": {"@type": "ItemList", "itemListElement": [
             {"@type": "ListItem", "position": n, "url": g["url"], "name": plain(g["h1"])} for n, g in enumerate(guides, 1)]}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": url}]}]}
    cards = "\n".join(f"""          <a class="card guide-card" href="{g['path']}">
            <span class="eyebrow">{e(g['category'])} · {fmt_date(g['updated'])}</span>
            <h3>{inline(g['h1'])}</h3>
            <p>{e(g['description'])}</p>
          </a>""" for g in guides)
    pages = "\n".join(f'          <li><a href="{p}">{e(l)}</a><span>{e(page_description(p))}</span></li>' for p, l in PRODUCT_PAGES)
    return head("Guides: Peptides, GLP-1s & the Menstrual Cycle | Revé", desc, url, "website", schema) + f"""
  <main id="main">
    <div class="content-hero wrap">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="/">Home</a><span aria-hidden="true">/</span><span aria-current="page">Guides</span>
      </nav>
      <span class="eyebrow"><span class="dot" aria-hidden="true"></span> {len(guides)} guides</span>
      <h1 id="page-title">Guides for women who track <em>peptides, GLP-1s and their cycle</em></h1>
      <p class="lede">Label facts with sources, honest app comparisons, and plain definitions. Each guide shows when it was last checked.</p>
    </div>
    <section class="wrap content-section hub-first" aria-labelledby="all-guides">
      <h2 id="all-guides" class="eyebrow">All guides</h2>
      <div class="guide-grid">
{cards}
      </div>
    </section>
    <section class="wrap content-section" aria-labelledby="pages-title">
      <h2 id="pages-title" class="eyebrow">About the app, templates and tools</h2>
      <ul class="page-list">
{pages}
      </ul>
    </section>
  </main>

""" + footer("/guides/")


def render_sitemap(guides: list[dict]) -> str:
    # Only generated pages carry <lastmod>, taken from front matter, so output is
    # identical on every machine. Hand-written pages are listed without one.
    entries = [(f"{SITE}/", None)]
    known = {p for p, _ in PRODUCT_PAGES}
    found = sorted(f"/{d.name}/" for d in ROOT.iterdir()
                   if d.is_dir() and (d / "index.html").exists() and d.name not in {"guides", "assets"}
                   and not d.name.startswith((".", "_")))
    for p in [p for p, _ in PRODUCT_PAGES] + [p for p in found if p not in known]:
        entries.append((SITE + p, None))
    entries.append((f"{SITE}/guides/", guides[0]["updated"].isoformat() if guides else None))
    entries += [(g["url"], g["updated"].isoformat()) for g in guides]
    rows = []
    for loc, lastmod in entries:
        lm = f"\n    <lastmod>{lastmod}</lastmod>" if lastmod else ""
        rows.append(f"  <url>\n    <loc>{loc}</loc>{lm}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n")


def render_llms(guides: list[dict]) -> str:
    pages = "\n".join(f"- [{l}]({SITE}{p}): {page_description(p)}" for p, l in PRODUCT_PAGES)
    gl = "\n".join(f"- [{plain(g['h1'])}]({g['url']}): {g['description']} (updated {g['updated'].isoformat()})" for g in guides)
    return f"""# Revé

> Revé is an iPhone app for women that logs peptides, supplements, GLP-1 routines, check-ins, measurements and progress photos, and tags every dose, check-in and measurement with menstrual cycle day and phase, so the same routine can be compared phase by phase and cycle to cycle.

- Name: Revé (App Store listing: "{APP_NAME}")
- Website: {SITE}
- App Store: {APP_URL}
- Platform: iPhone, iOS 17 or later
- Price: free download; a subscription is required for full access
- Company: Trendset Enterprises LLC, New York, USA. Contact: zareef@usereve.com
- Privacy policy: https://legal.usereve.com/privacy
- Not affiliated with Reve AI (reve.com, an AI image generator), REVE Chat, or other products with similar names.

## Important context
- Revé is a personal logging tool. It does not sell peptides or any compound, does not recommend doses, and is not medical advice.
- Cycle phase labels in Revé are for organizing notes. They are not for contraception or fertility planning.
- In Revé, "cycle" means the menstrual cycle. A peptide "cycle" (an on/off protocol schedule) is a different thing.
- Guides cite primary sources (FDA labels, manufacturer medical information) at the end of each page. Prefer those sources for drug facts.
- Cite as: Revé, {SITE}

## Product pages, templates and tools
{pages}

## Guides
{gl}
"""


# --------------------------------------------------------------------------- #

def main() -> int:
    global COPYRIGHT_YEAR
    check = "--check" in sys.argv
    guides = load_guides()
    if guides:
        COPYRIGHT_YEAR = max(COPYRIGHT_YEAR, max(g["updated"].year for g in guides))
    outputs: dict[Path, str] = {}
    for g in guides:
        outputs[ROOT / "guides" / g["slug"] / "index.html"] = render_guide(g, guides)
    outputs[ROOT / "guides" / "index.html"] = render_hub(guides)
    outputs[ROOT / "sitemap.xml"] = render_sitemap(guides)
    outputs[ROOT / "llms.txt"] = render_llms(guides)

    stale = []
    for path, text in outputs.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    # remove pages whose markdown was deleted or set to draft
    live = {g["slug"] for g in guides}
    for d in (ROOT / "guides").glob("*/"):
        if d.is_dir() and d.name not in live and (d / "index.html").exists():
            stale.append(d.relative_to(ROOT))
            if not check:
                (d / "index.html").unlink()
                if not any(d.iterdir()):
                    d.rmdir()
    if check and stale:
        print("stale outputs (run python3 tools/geo/build.py):", *map(str, stale), sep="\n  ")
        return 1
    print(f"{len(guides)} guides; {'checked' if check else 'wrote'} {len(outputs)} files"
          + (f"; changed: {', '.join(map(str, stale))}" if stale and not check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
