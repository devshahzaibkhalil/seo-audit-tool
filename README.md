# SEO Audit Tool

A full-site SEO auditor in a single Python file. No installation, no dependencies, no
build step. Paste a URL, get a branded report covering technical SEO, on-page, content,
internal linking, speed, images, structured data, rankings and off-page.

Built and maintained by [B My Marketer](https://bmymarketer.com).

---

## Run it on your own computer

1. Install [Python 3.9 or newer](https://www.python.org/downloads/) — on Windows, tick
   **"Add Python to PATH"** during setup.
2. Download `seo_tool.py`.
3. Double-click it.

Your browser opens the tool. The first run asks you to create a username and password.
Then paste a website address and press **Start audit**.

Full instructions, every setting explained: **[USAGE.md](USAGE.md)**

## Put it online

Free hosting, roughly ten minutes, no card required:
**[DEPLOY.md](DEPLOY.md)**

---

## What it checks

| Area | Covered |
|---|---|
| **Crawl & status** | 4xx/5xx, redirect chains and loops, temporary redirects, broken internal and outbound links, HTTPS, mixed content, HSTS, soft 404s, www duplication |
| **Indexing** | noindex, robots.txt blocks, canonicals, hreflang, orphan pages, sitemap validity, a yes/no list of every URL with the reason |
| **On-page** | Titles, descriptions, H1s, full heading outlines, viewport, lang, charset, Open Graph, URL structure |
| **Content** | Thin and duplicate content, near-duplicates, reading level, concrete detail, filler phrases, repetition |
| **Keywords** | Topic extraction from your own pages, per-page keywords, cannibalisation |
| **Internal links** | Contextual vs navigation links, anchor text classified by type, link ratios, click depth, internal PageRank |
| **Speed** | Server response times, real measured page weight, render-blocking resources, heaviest files, Core Web Vitals |
| **Images** | Alt text, formats, WebP/AVIF share, oversized files, lazy loading, srcset |
| **Structured data** | JSON-LD validity, missing types, Organization markup |
| **Tracking** | 26 analytics and pixel tools, page coverage, what's missing |
| **Search Console** | Verification via meta tag and live DNS lookup |
| **Rankings** | Striking-distance keywords, CTR outliers, cannibalisation (needs a Search Console export) |
| **Off-page** | Referring domains, anchor profile, authority spread, social presence (backlink data needs an export) |

Output is a self-contained HTML report plus seven CSVs.

## What it deliberately doesn't do

- **No AI-content score.** Detectors are unreliable and Google ranks helpfulness, not
  authorship. The tool measures what actually makes content weak instead: specificity,
  filler and repetition.
- **No invented backlink data.** Who links to you can't be discovered by crawling your own
  site. Upload a free Search Console links export or any paid export and the section fills in.
- **No calculated DA/PA.** Those are Moz's proprietary metrics — the tool fetches them if
  you supply a Moz key, and otherwise reports internal PageRank, which it can compute honestly.

## Security

Local by default: binds to `127.0.0.1`, so nothing outside your machine can reach it.
Login uses PBKDF2-SHA256 at 600,000 rounds with lockout, CSRF tokens, origin checks and
strict cookie flags. Hosted mode adds environment-variable credentials, Secure cookies and
blocking of private network targets. Details in [USAGE.md](USAGE.md#your-login-and-how-its-protected).

## Licence

MIT — see [LICENSE](LICENSE). Use it, change it, sell audits with it.
