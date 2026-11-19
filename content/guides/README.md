# Writing a Revé guide

Every `.md` file in this folder (except this README and files starting with `_`)
becomes a page at `https://usereve.com/guides/<slug>/`.

```bash
python3 tools/geo/build.py          # writes /guides/*, /sitemap.xml, /llms.txt
python3 tools/geo/build.py --check  # what CI runs; fails if outputs are stale
```

Commit the markdown **and** the generated HTML together. The IndexNow workflow
pings Bing/Yandex for every changed HTML page after GitHub Pages deploys.

## File format

TOML front matter between `+++` lines, then the body in Markdown.

```toml
+++
slug = "url-slug"                       # lowercase, hyphens, matches the query
title = "Search Title (≤60 chars) | Revé"
h1 = "Visible heading with *one italic phrase*"
crumb = "Short breadcrumb"
category = "GLP-1s & contraception"     # eyebrow + hub label
description = "≤160 chars. States the answer, not a teaser."
lede = "One or two sentences under the H1."
published = 2026-11-18
updated = 2026-11-18                    # bump on every real edit; drives lastmod + byline
about = ["Entity", "Entity"]            # schema.org about
related_guides = ["other-slug"]
related_pages = ["/glp-1-tracker-for-women/"]   # must be in PRODUCT_PAGES in build.py
faq_heading = "Questions about X"
# reviewed_by = "Full Name"             # only a real person who actually reviewed it
# reviewer_credentials = "PharmD"
# glossary = true                       # H3 + following paragraph become DefinedTerms
# draft = true                          # skip without deleting
summary = """
The 40–80 word answer an AI assistant would quote. Lead with the fact.
"""

[[faq]]
q = "Question phrased the way people type it into ChatGPT?"
a = "Two to four sentences. Self-contained: no 'see above'."

[[sources]]
title = "Exact document title"
publisher = "U.S. FDA"
url = "https://..."
+++

## First H2

Body...
```

Markdown supported: `##`/`###` headings, paragraphs, `-` and `1.` lists,
pipe tables, `> callouts`, `**bold**`, `*italic*`, `[links](/path/)`, inline code.
Lines starting with `<` pass through as raw HTML.

## Editorial rules (non-negotiable for a health app)

1. **Answer first.** The `summary` must answer the query in the first sentence,
   with the specific fact (a number, a name, a date, a yes/no).
2. **Every drug or health fact has a primary source** in `[[sources]]`:
   FDA label, manufacturer medical information, a regulator (FDA, TGA, EMA, MHRA),
   a peer-reviewed paper, or a government health site. Not other blogs, not
   other apps' SEO pages, not Reddit.
3. **No dosing.** Never recommend a dose, protocol, stack, timing, or a change
   based on cycle phase. Never write reconstitution math or "how much to inject".
   Describing what an FDA label says about titration windows is fine; telling a
   reader what to take is not.
4. **No research-use-only how-tos.** We can define BPC-157 or say what the FDA
   has said about it. We don't explain sourcing, mixing, or using it.
5. **Don't overclaim Revé.** Only describe features that are live in the app.
   Never say Revé predicts ovulation, fertility, or effects.
6. **Competitors are described from their own listings**, dated, with the
   listing linked. Say where they're a better fit. A comparison that always
   ranks us first gets ignored by readers and by AI models.
7. **Date-stamp numbers.** "4.8 stars from ~35,000 ratings (AppGoblin, Nov 2026)",
   not "highly rated".
8. **One page per question.** If two queries need different first sentences,
   they're two pages. If they'd have the same first sentence, they're one page.
9. **Update, don't duplicate.** When facts change, edit the page and bump
   `updated`. Don't publish "…(2027 update)" as a new URL.
