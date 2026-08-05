# SEO Audit Tool

One file. Nothing to install. You paste a website address into a box and get a full
SEO report.

---

## How to use it

**1. Check you have Python.** Most Macs already do. On Windows you probably need it:
go to [python.org/downloads](https://www.python.org/downloads/), click the big yellow
download button, run the installer, and **tick the box that says "Add Python to PATH"**
on the first screen. That box matters.

**2. Save `seo_tool.py`** anywhere you like — your Desktop is fine.

**3. Double-click it.**

A black window appears and your browser opens the tool. The first time, it asks you to
create a username and password — nobody can use the tool until you do. After that you
sign in, paste your website address into the box, press **Start audit**, and wait. The page tells you what it's doing
and updates itself.

When it's finished you get a health score out of 100 and a button to open the report.

Leave the black window open while you work. Close it when you're done.

> **If double-clicking opens a text editor instead of running:** right-click the file →
> Open With → Python. On Mac, right-click → Open With → Python Launcher.
>
> **If nothing seems to happen:** open Terminal (Mac) or Command Prompt (Windows), type
> `python ` with a space, drag the file into the window, and press Enter.

---

## What you get

**The report** — a web page you can read, print or email to a client. It opens with a
health score, then a picture of where the site's problems are concentrated, then the
eight things worth fixing first, then every single finding grouped by severity. Each one
explains why it matters and what to do about it, so you can hand it to a developer as-is.

**issues.csv** — every problem as a spreadsheet row: severity, URL, what's wrong, how to
fix it. This is your to-do list.

**Seven spreadsheets**, all downloadable from the finish screen:

| File | What's in it |
|---|---|
| `issues.csv` | Every problem: severity, URL, what's wrong, how to fix it |
| `pages.csv` | Every page: title, description, H1, words, status, depth, keywords, readability |
| `indexability.csv` | Every URL marked can-be-indexed yes/no, with the exact reason |
| `headings.csv` | Every heading on every page, in order, with its level |
| `images-missing-alt.csv` | Every image with no alt text, and the page it's on |
| `internal-links.csv` | Every internal link: source, target, anchor text, anchor type, contextual or navigation |
| `tracking.csv` | Which analytics tags fire on which page |

Everything is also saved in a `seo-reports` folder next to the tool, so you can come back
to old audits.

---

## Branding the report

**Already done.** Every report comes out branded B My Marketer: the logo is built into the
tool, and the palette is taken from the logo itself — `#1F7EBC` from the core of the mark
and `#168FBC` from the lighter end of its gradient. Section rules, the top bar, the health
score, keyword highlights and the footer all follow those two colours. You don't have to
set anything up.

To change any of it — a client's colours for a white-labelled report, or a different logo
— open **Report branding** on the form. Whatever you set is saved and reused.

If you upload a white or light-coloured logo, tick the "logo is white or light" box. That
puts it on a dark panel so it doesn't disappear against the report's pale background.

The logo is embedded inside the report file itself, so when you email the HTML to a
client it still shows. Nothing links back to a file on your computer.

One thing worth knowing: the severity colours (red, orange, gold) stay fixed no matter
what your brand colours are. They carry meaning rather than decoration — a client
scanning the report needs red to mean critical, not "on brand".

---

## Settings on the form

**Pages to check** — start at 100. Raise it once you've seen it work. A 1,000-page crawl
takes roughly ten to twenty minutes.

**Pause between pages** — how long to wait between requests. Leave it at 0.15. Raise it to
1 if the site is on slow shared hosting, so you don't strain it.

**Check outbound links** — finds dead links pointing away from your site. Adds a few
minutes.

**Ignore robots.txt** — only tick this on a site you own, when you deliberately want to see
pages that are blocked from crawlers.

---

## The three optional extras

Crawling a site tells you everything about the site itself. It cannot tell you how fast
real visitors find it, what you rank for, or who links to you — that information lives
with Google and with backlink providers. So the form has three optional slots for it,
under "Add rankings and backlink data".

**Rankings.** In Search Console: Performance → Search results → set the date range to the
last 3 months → **Export** → CSV. Upload that file. You'll get a rankings section, your
page-two keywords that are close to breaking through, snippets that under-perform their
position, and any keyword where several of your pages compete against each other.

**Backlinks.** Two ways to get this. Free: Search Console → Links → Top linking sites →
Export. Paid: any Ahrefs, Semrush or Majestic backlink export, no reformatting needed.
Upload either one and the off-page section fills in with referring domains and their
authority, follow versus nofollow split, anchor text classified by type, your most linked
pages, link quality spread and domain endings.

Without a file, the off-page section still reports what the crawl can see: which social
profiles the site links to and which are missing, whether you have Organization schema
tying your brand together, verification tags, and your outbound link profile. Who links
to *you* genuinely cannot be discovered by crawling your own site — no tool can do that
without buying the data.

**Domain Authority and Page Authority.** These are Moz's metrics, not Google's, and no
tool can calculate them — they can only be read from Moz's API. Add your Moz access ID and
secret on the form and DA, PA, spam score and linking domains appear in the Authority
section. Ahrefs' Domain Rating and Semrush's Authority Score work the same way: paid,
proprietary, fetched not computed. None of them is used by Google — they're third-party
estimates of link strength, useful for comparing against competitors and nothing more.
Without a key you still get the internal authority score, which is the part you control.

**Page speed.** Core Web Vitals are fetched automatically now. For reliable results get a
free PageSpeed Insights API key from
[Google](https://developers.google.com/speed/docs/insights/v5/get-started) and paste it in.
You'll get Core Web Vitals — LCP, CLS and INP — measured on real Chrome users where Google
has that data.

Skip all three and everything else still works. Those sections just won't appear.

---

## What it checks

**Technical** — broken pages, server errors, redirect chains and loops, temporary
redirects used permanently, HTTPS, mixed content, HSTS, robots.txt, XML sitemaps and
whether their URLs are actually valid, soft 404s, www vs non-www duplication, server
response time, compression, caching headers.

**Indexing** — noindex tags, pages blocked from crawlers, canonical tags that are missing,
duplicated, relative or pointing at broken URLs, hreflang errors, orphan pages, pages
missing from the sitemap.

**On-page** — titles and descriptions (missing, duplicate, wrong length), H1s, heading
order, mobile viewport, language and charset, image alt text, Open Graph tags, URL
structure.

**Content** — thin pages, exact duplicates, near-duplicates, text-to-code ratio, titles
that don't match their H1.

**Links** — how many clicks deep each page sits, how many internal links point to it,
dead-end pages, pages with too many links, vague anchor text like "click here", broken
outbound links.

**Structured data** — JSON-LD presence and validity, missing types, whether your homepage
identifies your organisation to Google.

**Indexability** — a straight yes/no list of every URL with the reason it can't be
indexed: noindex, robots block, canonical pointing elsewhere, redirect or error.

**Heading structure** — the full H1–H6 outline of every page, with missing H1s, duplicate
H1s and skipped levels flagged.

**Alt text** — every image with no alt attribute, listed by the page it sits on.

**Internal links and anchor text** — every anchor classified as branded, exact match,
partial match, generic, naked URL, image or long-tail; which pages use it and where it
points. Plus the ratios: contextual links versus navigation, links in versus out, and
internal versus external.

**Keyword cannibalisation** — pages competing for the same topic, detected from the crawl
itself. Add Search Console data and it also shows queries where several of your URLs rank.

**Analytics and tracking** — which of 26 tools are installed, what page coverage each has,
which pages have no tag at all, and what's worth adding.

**Speed** — server response time across every page, real page weight measured by
downloading the actual CSS, JavaScript and images, render-blocking resource counts, the
heaviest files on the site, uncompressed and uncached assets. Core Web Vitals (LCP, CLS,
INP) come from Google, and now work without an API key — though the free quota is shared,
so a key makes them reliable.

**Image formats** — every image's real format and file size, how much of your library is
WebP or AVIF versus still JPEG/PNG, oversized files, missing lazy-loading, missing srcset,
and an estimate of the megabytes you'd save by converting.

**Search Console** — checks whether the site is verified with Google, via the HTML meta
tag and a live DNS TXT lookup. Also checks Bing and whether your sitemap is declared in
robots.txt.

**Authority** — Domain and Page Authority if you add a Moz key, plus an internal authority
score for every page calculated with PageRank across your own internal links, so you can
see which pages hold your link equity and which are starved.

**Keywords** — the phrases your site actually talks about, pulled from your titles,
headings and descriptions, plus the top phrases on each individual page. If the keywords
you're targeting don't appear in that list, your site isn't saying what you think it is.

**Content quality** — reading level, sentence length, how much concrete detail each page
carries (numbers, dates, names, prices), filler-phrase count, and internal repetition.

---

## About "is my content AI-written?"

The tool deliberately doesn't answer that, because nothing can answer it reliably. AI
detectors flag plenty of human writing and miss plenty of machine writing, and Google
ranks pages on whether they help the reader rather than on how they were produced. A
score like that would send you rewriting pages that were fine.

What it does instead is measure the things that actually make content weak — which are
the same whoever or whatever wrote it:

- **Detail per 100 words.** Below 2 means the page has almost no numbers, dates, names or
  examples, so it could have been written about any company in your sector. This is the
  single most common reason a page fails to earn rankings or links.
- **Filler phrases.** Stock constructions — "in today's digital landscape", "it is
  important to note", "when it comes to" — that can be deleted without losing meaning.
- **Reading grade.** How much effort the page demands. 8 to 10 suits most commercial
  writing.
- **Repetition.** How much of the page recycles its own phrasing.

A page with real specifics, short sentences and no filler reads as authoritative whether
a person or a model drafted it. A page without them reads as padding either way. Fix
those three columns and you've fixed the thing people are really asking about.

## Your login, and how it's protected

On first run you create a username and password. They're stored on your computer only,
hashed with PBKDF2-SHA256 at 600,000 rounds — the file holds no readable password, and
it's set to owner-only permissions.

Forgot it? Run `python seo_tool.py --set-password` in a terminal to set a new one without
losing anything.

**What protects the login:**

| Protection | What it stops |
|---|---|
| Binds to 127.0.0.1 only | The tool isn't reachable from your network or the internet. Nobody outside your computer can even see it. |
| PBKDF2-SHA256, 600k rounds | Makes guessing at the stored hash impractical even if someone copies the file. |
| Lockout after 5 wrong tries | 15-minute freeze, so guessing at the login form goes nowhere. |
| Constant-time comparison | Stops timing attacks that leak a password one character at a time. |
| CSRF token on every form | A malicious page you visit can't make your browser start audits or change your password behind your back. |
| Origin check on every POST | A second, independent layer against the same attack. |
| HttpOnly, SameSite=Strict cookies | Scripts can't read your session, and other sites can't send it. |
| New session on each login | Stops session-fixation, where an attacker plants a session ID before you sign in. |
| 8-hour session expiry, logout clears it | Limits how long a forgotten open browser stays usable. |
| Changing your password signs out other browsers | Kicks anyone else out immediately. |
| CSP, X-Frame-Options, nosniff, no-referrer | Blocks clickjacking, MIME confusion and URL leakage. |
| Version banner suppressed | Doesn't advertise your Python version to anything probing locally. |

**Why there's no reCAPTCHA.** You asked, so here's the reasoning rather than a silent no.
A CAPTCHA stops bots hammering a form that's reachable from the internet. This form isn't
— it lives on 127.0.0.1, where the only thing that can reach it is something already
running on your machine, and anything with that much access is past a CAPTCHA anyway.
Adding one would mean sending every login to Google, needing site keys, and breaking the
tool whenever you're offline. Rate limiting plus slow hashing addresses the real risk, at
no cost. If you ever put this on a public server, that changes completely — tell me and
I'll add both a CAPTCHA and HTTPS, which you'd need first.

**Running it on a public server.** Hosted mode turns on automatically when a `PORT`
environment variable is present, and it changes three things: credentials come from the
`SEO_USER` and `SEO_PASSWORD` environment variables so a restart can't wipe them, session
cookies get the Secure flag, and the crawler refuses any target that resolves to a
private, loopback or link-local address. That last one matters — without it, a crawler on
a public server can be used to reach the host's own internal services. See
[DEPLOY.md](DEPLOY.md).

## Two honest limits

**It reads the page's source code, not the finished screen.** That's exactly how Google
first sees a page, which is what you want. But if your site builds its content with
JavaScript after loading, this tool won't see that content and will wrongly report thin
or missing text. If your site is built in React, Vue or similar, check a couple of pages
with Search Console's URL Inspection tool before acting on those findings.

**The score is a triage aid, not a prediction.** It tells you where to spend your time.
It doesn't forecast rankings — nothing honestly can.

Crawl sites you own or have permission to audit, and keep the delay sensible. A large
crawl is real traffic on someone's server.
