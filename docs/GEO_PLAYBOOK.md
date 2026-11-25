# Revé GEO playbook

Written Nov 18, 2026. Lives in `docs/`, which `_config.yml` keeps off the public site.
Whoever runs the SEO loop (Grok bot, Codex, a person) reads this file and
`content/guides/README.md` before every run.

---

## 1. What @alexxgrowth actually did for Content Rewards

He posted 7x AI traffic on Nov 7 and 3x daily signups on Nov 18, with $0 spend,
and when people asked how, he said "back link maxxing" and "grok + Claude + codex till
something worked". His public site shows what that meant in practice.

**A publishing sprint.** contentrewards.com/articles has 121 posts. About 35 went
up between February and August, and 3 on Nov 1. **About 83 went up between Nov 8 and Nov 17**,
roughly 8 a day. That's the sprint.

**The mix of page types** (approximate counts):

| Type | Count | Examples | Why AI assistants cite it |
| --- | --- | --- | --- |
| How-to | ~30 | how-to-start-clipping-with-no-followers | Matches a question word for word |
| Niche/category pages | ~20 | fitness-, anime-, podcast-clipping-campaigns | One page per sub-intent, same template |
| **Own-data reports** | ~12 | "TikTok Clipping CPM Rates in November 2026: Data from 651 Campaigns" | Specific numbers nobody else has, with a date and sample size |
| "Best…" lists | ~10 | best-clipping-campaigns-for-beginners | "Best" pages get the biggest share of AI referrals |
| Brand questions | ~10 | is-content-rewards-legit, is-content-rewards-part-of-whop / -of-x, how-much-does-content-rewards-pay | Wins the branded questions people ask ChatGPT about him, and untangles name confusion |
| Comparisons and alternatives | ~14 | sideshift-alternatives, clipping-vs-influencer-marketing | Bottom-of-funnel; drives signups |
| Definitions | ~6 | clipping-glossary, what-is-ugc | Definitions are easy to lift into an answer |

**Article template** (every post): the first sentence is the answer, with the
number in it. A bulleted "headline numbers" block. One H2 per sub-question. A
5–7 question FAQ at the bottom. 25–40 internal links. Month and year in the title,
`modified_time` bumped when re-checked, and notes like "re-checked Nov 16". A
corporate byline.

**Supporting pieces:** an `llms.txt`, a `/faqs` page, a CPM calculator tool, a help
center subdomain, and **hundreds of indexable campaign pages in the sitemap**
with fresh `lastmod` dates (programmatic, user-generated).

**What doesn't look like the lever:** his robots.txt has no AI-crawler rules, bylines
are just "By Content Rewards", and I couldn't find structured data in the pages I fetched
(the fetch tool may strip scripts, so treat that as unconfirmed). Technical SEO wasn't what changed.

**Caveats on his numbers:**
- The first spike (Oct 8 to Nov 6 window) **predates most of the sprint**. Something
  else started it: the Nov 1 rewrites of three big posts, the campaign pages, or brand demand.
- Content Rewards already had huge brand demand: it claims 1M+ creator signups, and it's all
  over TikTok and Discord. A lot of its AI traffic is probably people asking ChatGPT
  *about Content Rewards* ("is it legit", "how much does it pay"). Revé doesn't have that yet.
- His GA4 property shows the "data is being estimated" banner, he says himself the
  ratios keep changing, and absolute numbers are hidden. 7x of a small base is still small.

**What carries over:** volume on a repeatable template, answer-first pages with
specific dated facts, own data, brand and disambiguation pages, comparison pages,
and measuring AI referrals so you know what's working.

---

## 2. Where usereve.com stood before this branch

| Area | Status | Notes |
| --- | --- | --- |
| Technical SEO | Good | JSON-LD on every page, FAQPage, breadcrumbs, IndexNow on deploy, sitemap. At least as good as Content Rewards. |
| **Content** | **The bottleneck** | 12 pages, almost all variants of "Revé is a [peptide/supplement/GLP-1] tracker for women". They describe the product but don't answer questions. AI assistants cite answers. |
| Citable facts | Almost none | The copy is hedged until there's nothing to quote ("This page does not tell you what to take" appears on most pages). One boundary block per page is enough. |
| Cannibalization | Yes | peptide-tracker-for-women, womens-peptide-app and peptide-menstrual-cycle-tracker target nearly the same query. |
| **Analytics** | **None** | No GA4, Plausible or anything else. AI referrals can't be measured. |
| Entity | Weak | Organization schema was named "Trendset Enterprises LLC", not Revé. No sameAs. No llms.txt. "Reve" collides with Reve AI (reve.com, the image model), REVE Chat, and others. |
| Hub/internal links | None | No index page and no guide-to-guide links. |

That explains why the bot's work moved things only a little: it was polishing the
technical layer, which wasn't the constraint.

**Competitive reality.** "Peptide tracker app" is crowded: dozens of iOS apps
and a wave of AI-generated "best peptide app 2026" sites on pages.dev. Women-focused
GLP-1 apps are already running GEO plays too (MeAgain has /alternatives/shotsy,
/glp-1-for-perimenopause and similar). Revé's open lane is **women + menstrual cycle +
GLP-1s/peptides, answered with label-sourced facts**. Nobody owns that with
primary-source answers yet.

---

## 3. What this branch ships

- `tools/geo/build.py`: a dependency-free generator. Markdown + TOML front matter →
  `/guides/<slug>/` in the site's design, with Article, FAQPage, BreadcrumbList and
  DefinedTermSet JSON-LD, a dated byline, sources and related links. It also rebuilds
  `/guides/`, `sitemap.xml` (lastmod for guides) and `llms.txt`. **A new page costs
  about 150 lines of Markdown instead of about 600 lines of hand-written HTML.**
  That's what makes sprint volume possible.
- 4 guides, each a page type that worked for Content Rewards:
  - `is-reve-legit`: brand facts and Reve-name disambiguation (his is-legit / is-part-of-X pages)
  - `mounjaro-zepbound-birth-control`: the tirzepatide 4-week label rule, with 10 primary sources (his data and fact pages)
  - `best-glp-1-and-peptide-tracker-apps-for-women`: a dated, honest comparison of 8 apps (his best-of and alternatives pages)
  - `peptide-and-cycle-tracking-glossary`: 34 terms (his clipping-glossary)
- `/guides/` hub page, `llms.txt`, and a sitemap with lastmod
- Organization schema renamed to Revé (legalName Trendset Enterprises LLC), with logo and sameAs, on every page
- "Guides" added to the nav and footer, "About Revé" in the footer, and contextual links from /faq/ and /glp-1-tracker-for-women/
- `_config.yml` excluding content/, tools/ and docs/ from GitHub Pages
- `.github/workflows/guides-check.yml`: CI fails if the generated HTML is stale

### Related cards

Guides already set `category` in front matter. The generator prints that string
as the eyebrow and on the hub, and uses it when `related_guides` names fewer
than three guides.

Cards named in `related_guides` are always shown. Open slots are filled from
other guides, same `category` first, then guides in other categories, newest
first. A guide outside About Revé does not receive an About Revé card this way.
About Revé is the category used by `is-reve-legit`, `how-much-does-reve-cost`,
and `reve-privacy`. Those three slugs are matched even if the category string
differs, so pricing and privacy stay off health guides after they merge. Put
the slug in `related_guides` when that card should still appear.

---

## 4. Do this week (needs a human with logins)

1. **Analytics.** Add GA4 (or Plausible) to every page. In GA4: Admin → Data display →
   Channel groups → copy the default → add a channel "AI Assistant" *above* Referral with
   source matching regex:
   `chatgpt\.com|openai\.com|perplexity\.ai|claude\.ai|gemini\.google\.com|copilot\.microsoft\.com|meta\.ai|grok\.com|deepseek\.com|you\.com`
   That's the same report Alex screenshots.
2. **App Store campaign links.** Web visits aren't installs. In App Store Connect → App
   Analytics → Campaigns, create a campaign link and use `?pt=<provider>&ct=<page-slug>&mt=8` on every
   App Store button, so installs show up by source page. (`build.py` has `APP_URL`
   in one place for this.)
3. **Bing Webmaster Tools + Google Search Console.** Verify usereve.com, submit the sitemap,
   and check how many pages are indexed. ChatGPT search leans on Bing's index.
   IndexNow is already wired, but you need BWT to see whether pages actually get in.
4. **Social profiles in sameAs.** Add every official account URL to `ORGANIZATION["sameAs"]`
   in `build.py` and to the Organization block on existing pages.
5. **Check the App Store listing.** Searching the web for "Reve: Peptide & Cycle Tracker"
   didn't return the listing. Make sure the listing's marketing URL is usereve.com and its
   subtitle and description use the words women search for (peptide, GLP-1, cycle).
6. **A named reviewer for health pages.** Google holds health content to a higher bar
   than Alex's niche. A pharmacist, RD or ob-gyn reviewing the GLP-1 pages
   (`reviewed_by` in the front matter) is worth more than ten extra pages.
   Never invent one.

---

## 5. The sprint queue

Work top to bottom. ☐ = not started. Each item is one page unless noted.
Verify every drug fact against the current label before writing.

### A. Brand and entity (do first, cheap, protects the name)
- ☑ is-reve-legit
- ☑ `how-much-does-reve-cost`: subscription price, trial, what's free (fill from App Store Connect). This mirrors his featured page.
- ☐ `reve-privacy`: what's stored, where, who can see it, how to delete. For a health app this is the #1 trust question.
- ☑ `does-reve-work-with-apple-health`: parked by owner Nov 20, 2026, not published. Only if true; otherwise skip. See Parked.

### B. Women + GLP-1 label facts (the open lane)
- ☑ mounjaro-zepbound-birth-control
- ☐ `ozempic-wegovy-and-the-pill`: short page; why semaglutide's label differs (reuse sources)
- ☐ `glp-1-and-planning-a-pregnancy`: what each label says about stopping before a planned pregnancy (verify Wegovy, Zepbound, Mounjaro labels separately)
- ☐ `zepbound-and-hrt`: Lilly's medical-information answer on HRT
- ☐ `missed-dose-rules-zepbound-wegovy-ozempic`: per-label missed-dose windows, in a table
- ☐ `glp-1-period-changes`: what's documented (label, studies) and what's anecdotal; how to log it
- ☐ `glp-1-side-effects-by-cycle-phase-how-to-log`: a logging how-to with no effect claims
- ☐ `glp-1-perimenopause-tracking`: what to track; cite research, no claims
- ☐ `glp-1-pcos-what-the-research-says`: careful, cited (and it doubles as research for the PCOS segment decision)
- ☐ `compounded-vs-branded-glp-1-what-fda-says`

### C. Comparisons and alternatives (bottom of funnel, drives installs)
- ☑ best-glp-1-and-peptide-tracker-apps-for-women
- ☐ `shotsy-alternatives-for-women`
- ☒ `best-peptide-tracker-for-women`: dropped Nov 20, 2026. A standalone page would compete with best-glp-1-and-peptide-tracker-apps-for-women. See Parked.
- ☐ `reve-vs-back2me`, `reve-vs-meagain`, `reve-vs-steady`: honest, from their listings
- ☐ `can-flo-track-glp-1-shots`, `can-clue-track-peptides`: check each app first; answer yes or no plainly
- ☐ `glp-1-tracker-apps-for-android`: honest page even though Revé is iPhone-only. It earns trust and links.

### D. Tools (his CPM calculator equivalent)
- ☑ cycle-phase-calculator (exists)
- ☐ **Backup-contraception window calculator**: enter the first tirzepatide dose and each increase date, get the 4-week windows on a calendar. Pure label arithmetic, useful, and nobody has it. Link it from the birth-control guide.
- ☐ Printable injection-site rotation log
- ☒ **Peptide reconstitution calculator: decide deliberately.** It's the highest-volume tool query in the niche, but it's dosing math, mostly for research-use-only compounds, on a women's health brand. My recommendation is to skip it.

### E. Own data (his most-cited format; start now, it compounds)
- ☐ `womens-glp-1-and-peptide-app-dataset-2026`: compile 40+ tracker apps from the App Store (platform, price model, rating count, cycle support, export, on-device or cloud). Put the month in the title, re-check monthly, publish a CSV. Original data gets cited and linked.
- ☐ **Survey**: 10 questions to women on GLP-1s/peptides via the creator outreach already running → "How women track GLP-1s and peptides (2026 survey, n=…)". This is how backlinks happen.
- ☐ In-app aggregates (later, and only with privacy-policy coverage, minimum cohort sizes, and counsel's sign-off on state health-data laws): "most-logged check-ins by cycle phase".

### F. Definitions
- ☑ peptide-and-cycle-tracking-glossary
- ☐ Spin out single-term pages only where a term has its own search demand and a cycle-specific angle (e.g. "peptide cycle vs menstrual cycle").

### G. Fix the existing pages
- ☐ Merge or differentiate peptide-tracker-for-women / womens-peptide-app / peptide-menstrual-cycle-tracker. Pick one canonical page for "peptide tracker for women" and turn the others into answers to different questions.
- ☐ Give each existing page an answer-first opening sentence with a specific fact, and cut repeated disclaimers down to one boundary block.

---

## 6. Off-site (where "back link maxxing" happens; the repo bot can't do this)

AI assistants mostly cite pages *other than yours* when recommending apps:
listicles, Reddit threads, YouTube videos, app directories.

1. **Get into the lists AI already cites.** Run the prompts below in ChatGPT and Perplexity,
   collect every cited URL, and email each author with a 3-line pitch and the facts from
   `is-reve-legit`.
2. **Directories:** Product Hunt, AlternativeTo (list Revé as an alternative to Shotsy,
   MeAgain, Flo), and app review aggregators.
3. **Reddit:** r/Zepbound, r/tirzepatide, r/Semaglutide, r/PCOS, r/Peptides. Answer the
   birth-control and tracking questions with the sourced facts. Link the guide only when
   it *is* the answer. Follow each sub's rules. No sockpuppets.
4. **Creators:** the influencer outreach already running. Ask for usereve.com in every
   video description. YouTube descriptions get indexed and cited.
5. **Same description everywhere:** "Revé: peptide & cycle tracker for women (iPhone), by Trendset Enterprises LLC."

---

## 7. Measure weekly

- GA4 → "AI Assistant" channel sessions and key events
- App Store Connect → installs by campaign token and by web referrer
- Bing and Google indexed-page counts
- **Prompt panel**: run these 20 in ChatGPT, Perplexity, Gemini and Claude every Monday, and log whether Revé is *mentioned* and whether usereve.com is *cited*:

  1. best GLP-1 tracker app for women
  2. app to track Zepbound and my period
  3. does Mounjaro affect birth control
  4. how long do I need backup birth control on Zepbound
  5. peptide tracker app for women
  6. track peptides with my menstrual cycle
  7. app to track semaglutide side effects and my cycle
  8. is the Revé app legit
  9. what is the Reve peptide app
  10. Shotsy alternative for women
  11. GLP-1 app for PCOS
  12. GLP-1 app for perimenopause
  13. how to track GLP-1 side effects by cycle phase
  14. peptide journal template
  15. what phase of my cycle am I in
  16. does Ozempic affect the pill
  17. compounded tirzepatide and birth control
  18. app to track supplements and my cycle
  19. women's peptide app
  20. my period changed on a GLP-1, how do I track it

---

## 8. Guardrails (why Revé can't copy Alex 1:1)

- **Pace: 2 to 3 pages a day, not 8.** Health content falls under Google's
  "Your Money or Your Life" scrutiny, and Google's scaled-content-abuse policy targets
  mass-produced pages made mainly to rank, however they're written. Every health page
  gets a human read before merge.
- **No dosing, no RUO how-tos, no feature claims that aren't live.** See `content/guides/README.md`.
- **Never fake a reviewer, a dataset, or a "we tested" claim.** One caught fabrication costs more than the whole sprint earns.

---

## 9. Bot instructions (paste into the Grok bot / Codex)

```
You maintain the Revé website repo (static site on GitHub Pages, domain usereve.com).

Before each run, read docs/GEO_PLAYBOOK.md and content/guides/README.md in full.

Each run:
1. Take the first unchecked ☐ item in section 5 of the playbook (skip tool items
   unless told otherwise).
2. Research it from primary sources only: FDA/EMA/TGA labels, manufacturer medical
   information, regulators, peer-reviewed papers, government health sites, and each
   competitor's own App Store listing. Record every URL you rely on.
3. Write content/guides/<slug>.md following README.md exactly: answer-first summary
   with the specific fact, 4–8 H2 sections, a 4–7 item FAQ in the reader's words,
   every factual claim backed by a [[sources]] entry, published/updated = today.
4. Run: python3 tools/geo/build.py && python3 tools/geo/build.py --check
5. Open a pull request titled "guide: <slug>" whose description lists each health
   claim next to its source URL. Do not merge health pages yourself.
6. Tick the item in docs/GEO_PLAYBOOK.md (☐ → ☑) in the same PR.

Weekly (Mondays): for every guide with dated numbers (ratings, counts, prices,
label versions), re-check the source; if anything changed, edit the page and bump
`updated`. If nothing changed, leave the file alone. Never bump dates without a real change.

Never: recommend doses, protocols or timing; explain reconstitution or sourcing of
research-use-only compounds; claim Revé features that aren't live; invent reviewers,
data, testimonials or "we tested" claims; publish two pages that answer the same question.
```

---

## Parked

Not the next page to publish. Do not delete these.

- `does-reve-work-with-apple-health`: parked by owner Nov 20, 2026. Only if true; otherwise skip. Not a published page.
- `best-peptide-tracker-for-women`: dropped as a standalone page Nov 20, 2026. It would compete with `best-glp-1-and-peptide-tracker-apps-for-women`. The approved edit is the update to that guide.
