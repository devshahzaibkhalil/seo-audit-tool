#!/usr/bin/env python3
"""
SEO Audit Tool — one file, no installation, paste a URL.

  Double-click this file, or run:  python seo_tool.py

A page opens in your browser with a box for the website address. Everything runs
on your own computer; the only site contacted is the one you're auditing.

Command line, if you prefer:
  python seo_tool.py https://example.com --max-pages 500

Needs Python 3.9 or newer. Nothing else.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import gzip
import hashlib
import hmac
import secrets
import html as html_mod
import io
import json
import os
import re
import socket
import ssl
import statistics
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse as up
import urllib.request
import urllib.robotparser as robotparser
import webbrowser
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

__version__ = "2.0"

UA = ("Mozilla/5.0 (compatible; SEOAuditBot/2.0) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 70, 155
THIN_CONTENT_WORDS = 300
SLOW_TTFB_MS = 600
MAX_LINKS_PER_PAGE = 150
MAX_URL_LEN = 115
MAX_DEPTH_OK = 4

# Default report branding. The logo is embedded so the tool needs no extra files
# and the report stays a single portable HTML file.
DEFAULT_BRAND = {
    "brand_name": "Bmymarketer",
    "brand_primary": "#1F7EBC",     # core blue of the B My Marketer mark
    "brand_secondary": "#168FBC",   # lighter end of its gradient
    "brand_logo": "",
    "brand_logo_light": False,
}

DEFAULT_LOGO_DATA_URI = "data:image/png;base64,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"


SEVERITIES = ["critical", "high", "medium", "low", "opportunity"]
SEV_WEIGHT = {"critical": 10.0, "high": 6.0, "medium": 3.0, "low": 1.0, "opportunity": 0.0}

CATEGORIES = ["Indexability", "Crawl & Status", "On-Page", "Content",
              "Internal Links", "Performance", "Structured Data", "Off-Page"]

# ---------------------------------------------------------------------------
# Issue registry.  code -> (severity, category, title, why it matters, how to fix)
# ---------------------------------------------------------------------------

ISSUE_DEFS: dict[str, dict] = {
    # --- Crawl & status -----------------------------------------------------
    "STATUS_5XX": dict(sev="critical", cat="Crawl & Status",
        title="Server error (5xx)",
        why="Google drops pages that repeatedly return server errors, and a burst of 5xx responses throttles crawl rate site-wide.",
        fix="Check server/application logs for these URLs. Fix the underlying error or return a proper 404/410 if the page is gone."),
    "STATUS_4XX": dict(sev="critical", cat="Crawl & Status",
        title="Client error (4xx)",
        why="The URL is linked or listed somewhere but returns nothing. Link equity pointing at it is wasted and users hit a dead end.",
        fix="301-redirect to the closest relevant live page, or restore the content. Then fix the links that point here."),
    "BROKEN_INTERNAL_LINK": dict(sev="critical", cat="Crawl & Status",
        title="Internal link to a broken URL",
        why="Broken internal links waste crawl budget, leak PageRank into a dead end and are a direct UX failure.",
        fix="Update the <a href> on the linking pages to the correct destination."),
    "REDIRECT_LOOP": dict(sev="critical", cat="Crawl & Status",
        title="Redirect loop",
        why="The URL never resolves, so neither users nor crawlers can reach the content.",
        fix="Inspect the redirect rules (server config, CMS, plugins) and remove the circular rule."),
    "REDIRECT_CHAIN": dict(sev="medium", cat="Crawl & Status",
        title="Redirect chain (2+ hops)",
        why="Each hop adds latency and dilutes signals. Google follows chains but gives up after roughly 5 hops.",
        fix="Flatten the chain: point the first URL directly at the final destination."),
    "TEMP_REDIRECT": dict(sev="medium", cat="Crawl & Status",
        title="302/307 used for a permanent move",
        why="Temporary redirects tell Google to keep indexing the old URL, so the new URL never fully inherits the signals.",
        fix="Switch to a 301 (or 308) if the move is permanent."),
    "INTERNAL_LINK_TO_REDIRECT": dict(sev="low", cat="Crawl & Status",
        title="Internal link points at a redirect",
        why="Cheap fix with a real payoff: linking to the final URL saves a round trip on every crawl and every visit.",
        fix="Update internal links to the destination URL."),
    "BROKEN_EXTERNAL_LINK": dict(sev="low", cat="Crawl & Status",
        title="Broken external link",
        why="Outbound links to dead resources are a quality signal problem and a poor experience.",
        fix="Replace with a working source or remove the link."),
    "SLOW_RESPONSE": dict(sev="medium", cat="Performance",
        title="Slow server response (TTFB)",
        why="Time to first byte above ~600ms suppresses crawl rate and is the hardest part of LCP to recover from.",
        fix="Add full-page or object caching, tune database queries, or move to a faster host/CDN."),
    "NO_COMPRESSION": dict(sev="medium", cat="Performance",
        title="HTML served uncompressed",
        why="Gzip/Brotli typically cuts HTML transfer size by 70%+. Without it every page load is needlessly slow.",
        fix="Enable Brotli or gzip for text/html, text/css, application/javascript at the server or CDN."),
    "NO_CACHE_HEADERS": dict(sev="low", cat="Performance",
        title="No caching headers",
        why="Repeat visits re-download everything, hurting perceived speed and wasting bandwidth.",
        fix="Set Cache-Control on static assets (long max-age + immutable) and a sensible policy for HTML."),
    "LARGE_HTML": dict(sev="low", cat="Performance",
        title="Oversized HTML document",
        why="Very large HTML payloads delay first paint and can push important content past Google's parsing limits.",
        fix="Trim inline CSS/JS, remove hidden duplicate markup, and paginate very long pages."),

    # --- HTTPS / site config -----------------------------------------------
    "HTTPS_MISSING": dict(sev="critical", cat="Crawl & Status",
        title="Site not served over HTTPS",
        why="HTTPS is a confirmed ranking signal and browsers flag HTTP pages as 'Not secure'.",
        fix="Install a TLS certificate and 301-redirect all HTTP traffic to HTTPS."),
    "HTTP_NOT_REDIRECTED": dict(sev="high", cat="Crawl & Status",
        title="HTTP does not redirect to HTTPS",
        why="Two accessible protocols means duplicate content and split signals.",
        fix="Add a site-wide 301 from http:// to https://."),
    "WWW_DUPLICATE": dict(sev="high", cat="Indexability",
        title="www and non-www both resolve",
        why="The same content on two hostnames splits link equity and creates duplicate content.",
        fix="Pick one hostname and 301-redirect the other to it."),
    "MIXED_CONTENT": dict(sev="high", cat="Crawl & Status",
        title="Mixed content on an HTTPS page",
        why="HTTP subresources on an HTTPS page are blocked or downgraded by browsers, breaking layout and trust.",
        fix="Update the asset URLs to https:// (or protocol-relative paths)."),
    "NO_HSTS": dict(sev="low", cat="Crawl & Status",
        title="No HSTS header",
        why="Without HSTS the first request each session can still be intercepted over HTTP.",
        fix="Send Strict-Transport-Security with a max-age of at least 6 months once HTTPS is stable."),
    "NO_ROBOTS_TXT": dict(sev="medium", cat="Indexability",
        title="No robots.txt",
        why="You lose the ability to steer crawl budget and to declare sitemap locations.",
        fix="Publish /robots.txt with crawl rules and a Sitemap: line."),
    "ROBOTS_BLOCKS_ALL": dict(sev="critical", cat="Indexability",
        title="robots.txt blocks the whole site",
        why="A site-wide Disallow: / stops Google from crawling anything. Rankings collapse.",
        fix="Remove the blanket Disallow. This is almost always a staging config that shipped to production."),
    "ROBOTS_BLOCKED": dict(sev="high", cat="Indexability",
        title="URL blocked by robots.txt",
        why="Blocked URLs can't be crawled, so their content and outgoing links are invisible to Google.",
        fix="If the page should rank, remove the Disallow rule. If it shouldn't be indexed, allow the crawl and use noindex instead."),
    "NO_SITEMAP": dict(sev="medium", cat="Indexability",
        title="No XML sitemap found",
        why="Sitemaps speed up discovery of new and deep pages and give you coverage reporting in Search Console.",
        fix="Generate /sitemap.xml, reference it in robots.txt and submit it in Search Console."),
    "SITEMAP_BAD_URL": dict(sev="medium", cat="Indexability",
        title="Sitemap contains a non-200 URL",
        why="A sitemap is a statement that these URLs are canonical and indexable. Errors in it erode trust in the whole file.",
        fix="Regenerate the sitemap so it only lists live, canonical, indexable URLs."),
    "SITEMAP_NONCANONICAL": dict(sev="medium", cat="Indexability",
        title="Sitemap URL is non-canonical or noindexed",
        why="Sending mixed signals — 'index this' in the sitemap, 'don't' on the page — wastes crawl budget.",
        fix="Remove these URLs from the sitemap, or make them canonical and indexable."),
    "NOT_IN_SITEMAP": dict(sev="low", cat="Indexability",
        title="Indexable page missing from the sitemap",
        why="Slower discovery, and the page is invisible in sitemap-level coverage reporting.",
        fix="Include every canonical, indexable URL in the sitemap."),
    "SOFT_404": dict(sev="medium", cat="Crawl & Status",
        title="Missing pages return 200 (soft 404)",
        why="Google wastes crawl budget on empty pages and may index them as thin content.",
        fix="Return a real 404 or 410 status for missing URLs, with a helpful error page."),

    # --- Indexability -------------------------------------------------------
    "NOINDEX": dict(sev="high", cat="Indexability",
        title="Page set to noindex",
        why="The page cannot rank at all. Fine for utility pages, catastrophic if it's a money page.",
        fix="Remove the noindex directive from the meta robots tag or X-Robots-Tag header on pages that should rank."),
    "NOFOLLOW_PAGE": dict(sev="medium", cat="Indexability",
        title="Page-level nofollow",
        why="Every link on the page stops passing signals, orphaning whatever it links to.",
        fix="Remove the page-level nofollow unless you deliberately want to seal off this section."),
    "CANONICAL_MISSING": dict(sev="low", cat="Indexability",
        title="No canonical tag",
        why="Without a self-referencing canonical, parameter and tracking variants of the URL can be indexed separately.",
        fix="Add a self-referencing <link rel=\"canonical\"> with an absolute URL to every indexable page."),
    "CANONICAL_MULTIPLE": dict(sev="high", cat="Indexability",
        title="Multiple canonical tags",
        why="Conflicting canonicals are usually ignored entirely, so Google picks its own — often the wrong URL.",
        fix="Emit exactly one canonical tag. Check for a theme and a plugin both injecting one."),
    "CANONICAL_OTHER": dict(sev="medium", cat="Indexability",
        title="Canonical points to a different URL",
        why="The page is telling Google to rank something else. Correct for duplicates, a silent killer if unintended.",
        fix="Verify each of these is a genuine duplicate. If not, make the canonical self-referencing."),
    "CANONICAL_RELATIVE": dict(sev="low", cat="Indexability",
        title="Relative canonical URL",
        why="Relative canonicals resolve unpredictably behind proxies and CDNs.",
        fix="Use absolute URLs including the protocol and hostname."),
    "CANONICAL_TO_NON200": dict(sev="high", cat="Indexability",
        title="Canonical points to a broken or redirecting URL",
        why="Google has to guess the canonical, and often consolidates onto the wrong URL or none at all.",
        fix="Point the canonical at the final, 200-status destination."),
    "ORPHAN_PAGE": dict(sev="medium", cat="Internal Links",
        title="Orphan page (in sitemap, no internal links)",
        why="With no internal links the page receives almost no PageRank and reads as unimportant to Google.",
        fix="Link to it from relevant category, hub or navigation pages."),
    "NO_HREFLANG_RETURN": dict(sev="medium", cat="Indexability",
        title="hreflang without a return tag",
        why="hreflang annotations are only honoured when both pages reference each other. One-way tags are ignored.",
        fix="Add the reciprocal hreflang tag on every page in the cluster, including a self-reference."),

    # --- On-page ------------------------------------------------------------
    "TITLE_MISSING": dict(sev="critical", cat="On-Page",
        title="Missing or empty title tag",
        why="The title is still the single strongest on-page relevance signal and it's the headline in the SERP.",
        fix="Write a unique 30–60 character title with the primary keyword near the front."),
    "TITLE_DUPLICATE": dict(sev="high", cat="On-Page",
        title="Duplicate title tag",
        why="Identical titles across pages tell Google the pages are interchangeable, causing the wrong one to rank.",
        fix="Give every indexable page a title that reflects its specific content and search intent."),
    "TITLE_MULTIPLE": dict(sev="medium", cat="On-Page",
        title="More than one title tag",
        why="Only the first is used, and the extras suggest a template conflict that may affect other tags too.",
        fix="Output a single <title> element in <head>."),
    "TITLE_TOO_LONG": dict(sev="low", cat="On-Page",
        title="Title over 60 characters",
        why="Long titles get truncated or rewritten by Google, so the part you care about may never be shown.",
        fix="Front-load the keyword and trim to roughly 60 characters."),
    "TITLE_TOO_SHORT": dict(sev="low", cat="On-Page",
        title="Title under 30 characters",
        why="Short titles waste available SERP real estate and usually under-describe the page.",
        fix="Expand with a qualifier, benefit or brand suffix."),
    "DESC_MISSING": dict(sev="medium", cat="On-Page",
        title="Missing meta description",
        why="Not a ranking factor, but it controls the snippet and therefore click-through rate.",
        fix="Write a 70–155 character description with a clear benefit and an implicit call to action."),
    "DESC_DUPLICATE": dict(sev="medium", cat="On-Page",
        title="Duplicate meta description",
        why="Boilerplate descriptions get discarded and replaced with scraped page text.",
        fix="Write unique descriptions for at least your top-traffic templates and landing pages."),
    "DESC_LENGTH": dict(sev="low", cat="On-Page",
        title="Meta description length outside 70–155 characters",
        why="Too short wastes space, too long gets cut mid-sentence.",
        fix="Aim for 140–155 characters."),
    "H1_MISSING": dict(sev="high", cat="On-Page",
        title="Missing H1",
        why="The H1 confirms the page topic to both users and parsers, and supports the title tag.",
        fix="Add exactly one H1 that states what the page is about."),
    "H1_MULTIPLE": dict(sev="medium", cat="On-Page",
        title="Multiple H1 tags",
        why="Legal in HTML5 but it muddies the topical hierarchy and usually signals a sloppy template.",
        fix="Keep one H1 and demote the rest to H2."),
    "HEADING_SKIP": dict(sev="low", cat="On-Page",
        title="Heading levels skipped",
        why="A broken heading hierarchy hurts accessibility and makes content structure harder to parse.",
        fix="Use headings in order (H1 → H2 → H3) rather than for visual sizing."),
    "NO_VIEWPORT": dict(sev="high", cat="On-Page",
        title="No mobile viewport meta tag",
        why="Google indexes mobile-first. Without a viewport the page renders as desktop-width and fails mobile usability.",
        fix="Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">."),
    "NO_LANG": dict(sev="low", cat="On-Page",
        title="No lang attribute on <html>",
        why="Screen readers and language targeting both rely on it.",
        fix="Set <html lang=\"en\"> (or the correct locale)."),
    "NO_CHARSET": dict(sev="low", cat="On-Page",
        title="No charset declaration",
        why="Browsers guess the encoding, which can mangle characters and the text Google extracts.",
        fix="Add <meta charset=\"utf-8\"> as the first element in <head>."),
    "IMG_NO_ALT": dict(sev="medium", cat="On-Page",
        title="Images without alt text",
        why="Alt text is required for accessibility and is how images earn traffic from Image Search.",
        fix="Describe the image in context. Leave alt=\"\" only for genuinely decorative images."),
    "IMG_NO_DIMENSIONS": dict(sev="low", cat="Performance",
        title="Images without width/height",
        why="Undeclared dimensions cause layout shift, which is what CLS measures.",
        fix="Set explicit width and height attributes (or a CSS aspect-ratio)."),
    "URL_TOO_LONG": dict(sev="low", cat="On-Page",
        title="Excessively long URL",
        why="Long URLs get truncated in the SERP and are harder to share and link to.",
        fix="Shorten the slug. Redirect the old URL if it already has links."),
    "URL_UNDERSCORES": dict(sev="low", cat="On-Page",
        title="Underscores in URL",
        why="Google treats hyphens as word separators and underscores as joiners, so terms can be misread.",
        fix="Use hyphens in new URLs. Only rewrite existing ones if you can redirect cleanly."),
    "URL_UPPERCASE": dict(sev="low", cat="On-Page",
        title="Uppercase characters in URL",
        why="Most servers treat URL paths as case-sensitive, so casing variants become duplicate pages.",
        fix="Standardise on lowercase and 301-redirect the variants."),
    "URL_PARAMS": dict(sev="low", cat="Indexability",
        title="Crawlable URL with query parameters",
        why="Parameter URLs multiply into near-infinite duplicates and burn crawl budget.",
        fix="Canonicalise to the clean URL and avoid linking to parameterised versions internally."),

    # --- Content ------------------------------------------------------------
    "THIN_CONTENT": dict(sev="medium", cat="Content",
        title="Thin content (under 300 words)",
        why="Thin pages rarely satisfy informational intent and, at scale, drag down site quality assessments.",
        fix="Expand with genuinely useful detail, merge into a stronger page, or noindex if it's a utility page."),
    "DUPLICATE_CONTENT": dict(sev="high", cat="Content",
        title="Duplicate body content",
        why="Google picks one version to index and the others compete with it for nothing.",
        fix="Consolidate with 301s or canonicals, or rewrite so each page serves a distinct intent."),
    "LOW_TEXT_RATIO": dict(sev="low", cat="Content",
        title="Low text-to-HTML ratio",
        why="Usually a symptom of heavy inline scripts, template bloat or content injected client-side.",
        fix="Move inline CSS/JS to external files and confirm the main content exists in the raw HTML."),
    "TITLE_H1_MISMATCH": dict(sev="low", cat="Content",
        title="Title and H1 share no keywords",
        why="A disconnect between them usually means the page targets two different intents at once.",
        fix="Align both around the same primary topic, with the title written for the SERP."),

    # --- Internal links -----------------------------------------------------
    "TOO_DEEP": dict(sev="medium", cat="Internal Links",
        title="Page more than 4 clicks from the homepage",
        why="Click depth correlates strongly with crawl frequency and rankings. Deep pages get crawled rarely.",
        fix="Add links from hub pages, improve pagination, or flatten the category structure."),
    "FEW_INLINKS": dict(sev="low", cat="Internal Links",
        title="Fewer than 3 internal links pointing to the page",
        why="Internal links are how PageRank and topical context flow. Under-linked pages under-perform.",
        fix="Add contextual links from related articles and relevant hub pages."),
    "TOO_MANY_LINKS": dict(sev="low", cat="Internal Links",
        title="More than 150 links on the page",
        why="Each link splits the page's outgoing equity, and huge navs dilute the ones that matter.",
        fix="Trim mega-menus and footer link dumps to what users actually need."),
    "GENERIC_ANCHOR": dict(sev="low", cat="Internal Links",
        title="Generic anchor text",
        why="'Click here' and 'read more' describe nothing, so the link passes no topical relevance.",
        fix="Use descriptive anchor text that names the destination topic."),
    "NO_INTERNAL_LINKS": dict(sev="medium", cat="Internal Links",
        title="Page has no outgoing internal links",
        why="Dead-end pages trap crawlers and users, and hoard PageRank instead of circulating it.",
        fix="Add contextual links to related pages."),

    # --- Structured data & social ------------------------------------------
    "SCHEMA_MISSING": dict(sev="medium", cat="Structured Data",
        title="No structured data",
        why="Schema is how you qualify for rich results (reviews, FAQ, breadcrumbs, products) and it clarifies entities.",
        fix="Add JSON-LD appropriate to the page type: Organization and WebSite site-wide, plus Article/Product/LocalBusiness/FAQPage."),
    "SCHEMA_INVALID": dict(sev="medium", cat="Structured Data",
        title="Invalid JSON-LD",
        why="Malformed JSON-LD is discarded entirely, so you lose every rich result on the page.",
        fix="Fix the JSON syntax and validate with Google's Rich Results Test."),
    "SCHEMA_NO_TYPE": dict(sev="low", cat="Structured Data",
        title="JSON-LD block missing @type",
        why="Without @type the block describes nothing Google can act on.",
        fix="Add a valid schema.org @type and the properties that type requires."),
    "NO_ORG_SCHEMA": dict(sev="low", cat="Structured Data",
        title="No Organization/LocalBusiness schema on the homepage",
        why="Entity markup on the homepage feeds the knowledge panel and disambiguates your brand.",
        fix="Add Organization (or LocalBusiness) JSON-LD with name, logo, url and sameAs profiles."),
    "NO_OG": dict(sev="low", cat="Structured Data",
        title="Missing Open Graph tags",
        why="Without og: tags, social platforms scrape whatever they can find, so shares look broken.",
        fix="Add og:title, og:description, og:image and og:url."),

    # --- Performance (PSI) --------------------------------------------------
    "CWV_LCP": dict(sev="high", cat="Performance",
        title="Largest Contentful Paint above 2.5s",
        why="LCP is a Core Web Vital and the one users feel most: it's when the page looks loaded.",
        fix="Preload the hero image, serve it in AVIF/WebP at the right size, cut render-blocking CSS and improve TTFB."),
    "CWV_CLS": dict(sev="medium", cat="Performance",
        title="Cumulative Layout Shift above 0.1",
        why="Content jumping under the user's finger is a Core Web Vital failure and a conversion killer.",
        fix="Reserve space for images, ads and embeds; avoid injecting banners above existing content."),
    "CWV_INP": dict(sev="high", cat="Performance",
        title="Interaction to Next Paint above 200ms",
        why="INP replaced FID as the responsiveness Core Web Vital. High INP means taps feel laggy.",
        fix="Break up long JavaScript tasks, defer third-party scripts and reduce main-thread work."),
    "PSI_LOW": dict(sev="medium", cat="Performance",
        title="Lighthouse performance score below 50",
        why="A lab score this low almost always means real users are failing Core Web Vitals too.",
        fix="Work the Lighthouse opportunities in order: image formats, unused JS, render-blocking resources."),

    # --- Off-page / rankings ------------------------------------------------
    "HEAVY_PAGE": dict(sev="medium", cat="Performance",
        title="Very heavy page",
        why="Total page weight above 3MB means slow loads on mobile data and a poor LCP, which is a ranking signal.",
        fix="Compress and resize images, drop unused JavaScript, and lazy-load anything below the fold."),
    "RENDER_BLOCKING": dict(sev="medium", cat="Performance",
        title="Too many render-blocking resources",
        why="Every blocking stylesheet or script delays first paint — the browser can't show anything until they've all downloaded and run.",
        fix="Add defer or async to scripts, inline critical CSS, and load the rest asynchronously."),
    "IMG_LEGACY_FORMAT": dict(sev="medium", cat="Performance",
        title="Images in JPEG/PNG instead of WebP or AVIF",
        why="WebP is typically 25–35% smaller than JPEG at the same quality, and AVIF more again. On image-heavy pages this is usually the single biggest speed win available.",
        fix="Convert to WebP (with AVIF where you can) and serve the old format as a <picture> fallback. Most CDNs and CMS plugins do this automatically."),
    "IMG_OVERSIZED": dict(sev="medium", cat="Performance",
        title="Oversized image file",
        why="Images above 200KB dominate page weight and delay LCP, usually because the full-resolution original was uploaded straight from a camera or design tool.",
        fix="Resize to the largest size actually displayed, compress, and add srcset so phones get a smaller file."),
    "IMG_NO_LAZY": dict(sev="low", cat="Performance",
        title="Below-the-fold image loads eagerly",
        why="Images far down the page compete for bandwidth with content the user can actually see.",
        fix="Add loading=\"lazy\" to images below the fold — but never to your main hero image, which should stay eager."),
    "NO_SEARCH_CONSOLE": dict(sev="high", cat="Indexability",
        title="No Google Search Console verification found",
        why="Search Console is the only source of your real query, ranking and indexing data, and the only place Google reports manual actions. Without it you are working blind.",
        fix="Add the property at search.google.com/search-console and verify by DNS TXT record, which covers every subdomain and protocol at once."),
    "SITEMAP_NOT_DECLARED": dict(sev="low", cat="Indexability",
        title="Sitemap not declared in robots.txt",
        why="A Sitemap: line is how crawlers other than Google find your sitemap without being told.",
        fix="Add 'Sitemap: https://yoursite.com/sitemap.xml' to robots.txt."),
    "CANNIBALISATION": dict(sev="high", cat="Off-Page",
        title="Keyword cannibalisation",
        why="Multiple URLs ranking for the same query split clicks and confuse Google about which to serve.",
        fix="Pick the primary URL, consolidate the rest with 301s or canonicals, and re-point internal anchors at it."),
    "STRIKING_DISTANCE": dict(sev="opportunity", cat="Off-Page",
        title="Striking-distance keyword (position 11–20)",
        why="Page-two rankings are the cheapest wins available: small on-page and link gains move them to page one.",
        fix="Strengthen the ranking page — sharpen the title, expand coverage of the query, add internal links with matching anchors."),
    "LOW_CTR": dict(sev="opportunity", cat="Off-Page",
        title="Click-through rate below expectation for the position",
        why="You already rank; the snippet just isn't earning the click. Rewriting it is a same-day fix.",
        fix="Rewrite the title and meta description to match the query's intent and add a differentiator."),
    "ANCHOR_OVER_OPTIMISED": dict(sev="high", cat="Off-Page",
        title="Over-optimised backlink anchor text",
        why="An unnatural share of exact-match commercial anchors is the classic footprint of link manipulation.",
        fix="Dilute with branded and URL anchors; audit and disavow paid or spun links if you find them."),
    "LOW_REFERRING_DOMAINS": dict(sev="high", cat="Off-Page",
        title="Very few referring domains",
        why="Referring domain count is the strongest off-page correlate with ranking ability in competitive niches.",
        fix="Invest in digital PR, original research, and reclaiming unlinked brand mentions."),
    "NOFOLLOW_HEAVY": dict(sev="medium", cat="Off-Page",
        title="Backlink profile is mostly nofollow/UGC",
        why="Nofollow links help discovery and brand, but they don't build the authority that lifts competitive rankings.",
        fix="Target editorial placements on relevant sites."),
    "TOPIC_NOT_IN_TITLE": dict(sev="low", cat="Content",
        title="Page's main topic missing from its title",
        why="The phrase the page actually talks about most doesn't appear in the title, so the strongest on-page signal is pointing somewhere else.",
        fix="Work the dominant phrase into the title naturally, or rewrite the page if the title reflects the intent you actually want."),
    "HARD_TO_READ": dict(sev="low", cat="Content",
        title="Hard to read",
        why="Dense prose raises bounce rate and shortens dwell time. Most successful commercial pages sit around a 8th–10th grade reading level.",
        fix="Shorten sentences, cut clauses, and replace abstract nouns with plain verbs. Aim for a Flesch score above 50."),
    "LONG_SENTENCES": dict(sev="low", cat="Content",
        title="Very long average sentence length",
        why="Sentences over ~25 words are hard to follow on a phone, which is where most of your traffic reads them.",
        fix="Break compound sentences in two. Vary length deliberately — a short sentence after a long one carries weight."),
    "FILLER_HEAVY": dict(sev="medium", cat="Content",
        title="Heavy use of filler and hedging phrases",
        why="Phrases like 'in today's digital landscape' and 'it is important to note' fill space without adding information. Readers skim past them and reviewers read them as padding.",
        fix="Delete them. Almost every one can be cut with no loss of meaning, and what remains gets sharper."),
    "LOW_SPECIFICITY": dict(sev="medium", cat="Content",
        title="Generic content with little concrete detail",
        why="Pages with no numbers, names, dates or examples read as interchangeable with every competing page. This is the single biggest marker of content that fails to earn links or rankings.",
        fix="Add specifics only you have: prices, measurements, dates, named products, real examples, your own data or photos."),
    "REPETITIVE": dict(sev="low", cat="Content",
        title="Repetitive phrasing within the page",
        why="The same constructions recycled through a page signal padding to a reader long before any algorithm notices.",
        fix="Cut the repeated passages, or merge them into one stronger section."),
    "NO_ANALYTICS": dict(sev="low", cat="On-Page",
        title="No analytics tag detected",
        why="You can't audit what you don't measure, and missing tags on some templates skews every report.",
        fix="Verify GA4/GTM fires on every template, not just the homepage."),
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    code: str
    url: str
    detail: str = ""


@dataclass
class Page:
    url: str
    status: int = 0
    final_url: str = ""
    redirect_chain: list = field(default_factory=list)
    ttfb_ms: int = 0
    size_bytes: int = 0
    content_type: str = ""
    headers: dict = field(default_factory=dict)
    depth: int = 0
    title: str = ""
    title_count: int = 0
    description: str = ""
    h1s: list = field(default_factory=list)
    headings: list = field(default_factory=list)
    canonical: str = ""
    canonical_count: int = 0
    meta_robots: str = ""
    x_robots: str = ""
    word_count: int = 0
    text_ratio: float = 0.0
    lang: str = ""
    charset: bool = False
    viewport: bool = False
    images: int = 0
    images_no_alt: int = 0
    images_no_dim: int = 0
    internal_links: list = field(default_factory=list)   # (url, anchor, nofollow)
    external_links: list = field(default_factory=list)
    schema_types: list = field(default_factory=list)
    schema_errors: int = 0
    og: bool = False
    hreflang: list = field(default_factory=list)
    mixed_content: int = 0
    analytics: bool = False
    analytics_tools: list = field(default_factory=list)
    verification: list = field(default_factory=list)
    missing_alt_images: list = field(default_factory=list)
    paragraphs: int = 0
    image_details: list = field(default_factory=list)
    stylesheets: list = field(default_factory=list)
    scripts: list = field(default_factory=list)
    picture_types: list = field(default_factory=list)
    preloads: list = field(default_factory=list)
    render_blocking: int = 0
    content_hash: str = ""
    shingles: set = field(default_factory=set)
    text: str = ""
    inlinks: int = 0
    error: str = ""

    @property
    def indexable(self) -> bool:
        if self.status != 200:
            return False
        robots = (self.meta_robots + " " + self.x_robots).lower()
        return "noindex" not in robots


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def normalise(url: str) -> str:
    """Canonical form of a URL for de-duplication."""
    url = url.strip()
    if not url:
        return ""
    p = up.urlsplit(url)
    scheme = p.scheme.lower()
    host = p.netloc.lower()
    if (scheme == "http" and host.endswith(":80")) or (scheme == "https" and host.endswith(":443")):
        host = host.rsplit(":", 1)[0]
    path = up.quote(up.unquote(p.path), safe="/%:@&=+$,~*!'()")
    if not path:
        path = "/"
    query = p.query
    return up.urlunsplit((scheme, host, path, query, ""))


def registrable(host: str) -> str:
    return host.lower().removeprefix("www.")


def same_site(url: str, root_host: str) -> bool:
    try:
        h = up.urlsplit(url).netloc.lower()
    except ValueError:
        return False
    return bool(h) and registrable(h) == registrable(root_host)


def is_html_url(url: str) -> bool:
    path = up.urlsplit(url).path.lower()
    bad = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico",
           ".css", ".js", ".json", ".xml", ".pdf", ".zip", ".gz", ".rar",
           ".mp4", ".mp3", ".wav", ".avi", ".mov", ".woff", ".woff2", ".ttf",
           ".eot", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".dmg", ".exe")
    return not path.endswith(bad)


def rel_values(tag) -> list:
    """BeautifulSoup returns rel as a list or a bare string depending on the parser
    and the markup. Normalise it so link-relationship checks can't silently fail."""
    v = tag.get("rel")
    if not v:
        return []
    if isinstance(v, str):
        v = v.split()
    return [str(x).lower() for x in v]


def shingle_set(text: str, k: int = 8) -> set:
    words = re.findall(r"[a-z0-9']+", text.lower())
    if len(words) < k:
        return set()
    return {hash(" ".join(words[i:i + k])) for i in range(0, len(words) - k, 3)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)


# ---------------------------------------------------------------------------
# Hosted mode
# ---------------------------------------------------------------------------
# Running on your own machine and running on a public server are different jobs.
# On a server the filesystem is wiped on every restart, the app sits behind an
# HTTPS proxy, and anyone on the internet can reach the login. HOSTED switches on
# the behaviour that difference requires.

HOSTED = bool(os.environ.get("PORT"))
BLOCK_PRIVATE = os.environ.get("ALLOW_PRIVATE_TARGETS", "").lower() not in ("1", "true", "yes") \
    and HOSTED

_HOST_CACHE = {}


def is_public_host(host: str) -> bool:
    """Reject private, loopback and link-local addresses.

    A crawler reachable from the internet is a way to reach whatever the server
    itself can reach — including cloud metadata endpoints and internal services.
    """
    if not host:
        return False
    host = host.split(":")[0].strip("[]")
    if host in _HOST_CACHE:
        return _HOST_CACHE[host]
    import ipaddress
    ok = False
    try:
        infos = socket.getaddrinfo(host, None)
        addrs = {i[4][0] for i in infos}
        ok = bool(addrs)
        for a in addrs:
            ip = ipaddress.ip_address(a)
            if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                    or ip.is_multicast or ip.is_unspecified):
                ok = False
                break
    except Exception:
        ok = False
    _HOST_CACHE[host] = ok
    return ok


class BlockedTarget(Exception):
    pass


# ---------------------------------------------------------------------------
# HTTP layer (stdlib only)
# ---------------------------------------------------------------------------

class CIDict(dict):
    """Headers, case-insensitively."""
    def __init__(self, pairs=()):
        super().__init__((str(k).lower(), v) for k, v in pairs)

    def get(self, key, default=None):
        return super().get(str(key).lower(), default)

    def __contains__(self, key):
        return super().__contains__(str(key).lower())

    def __getitem__(self, key):
        return super().__getitem__(str(key).lower())


class Resp:
    def __init__(self, url, status, headers, body: bytes, ttfb: int):
        self.url = url
        self.status_code = status
        self.headers = CIDict(headers)
        self.content = body
        self._ttfb = ttfb
        self._text = None

    @property
    def is_redirect(self):
        return 300 <= self.status_code < 400 and "location" in self.headers

    @property
    def text(self):
        if self._text is None:
            enc = None
            ctype = self.headers.get("content-type", "") or ""
            m = re.search(r"charset=([\w\-]+)", ctype, re.I)
            if m:
                enc = m.group(1)
            if not enc:
                head = self.content[:4096]
                m = re.search(br'charset=["\']?([\w\-]+)', head, re.I)
                if m:
                    enc = m.group(1).decode("ascii", "ignore")
            for cand in (enc, "utf-8", "cp1252"):
                if not cand:
                    continue
                try:
                    self._text = self.content.decode(cand)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            if self._text is None:
                self._text = self.content.decode("utf-8", "replace")
        return self._text


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Return None so urllib raises instead of following — we want the hops."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _decode_body(raw: bytes, encoding: str) -> bytes:
    enc = (encoding or "").lower()
    try:
        if "gzip" in enc:
            return gzip.decompress(raw)
        if "deflate" in enc:
            try:
                return zlib.decompress(raw)
            except zlib.error:
                return zlib.decompress(raw, -zlib.MAX_WBITS)
    except Exception:
        return raw
    return raw


def http_get(url, method="GET", timeout=20, ua=UA, max_bytes=5_000_000):
    """One request, no redirect following. Returns Resp or raises."""
    if BLOCK_PRIVATE and not is_public_host(up.urlsplit(url).netloc):
        raise BlockedTarget("target resolves to a private or local address")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # audit sites with broken certs rather than crash
    opener = urllib.request.build_opener(_NoRedirect,
                                         urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(url, method=method, headers={
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close",
    })
    t0 = time.perf_counter()
    try:
        r = opener.open(req, timeout=timeout)
        raw = r.read(max_bytes) if method != "HEAD" else b""
        ttfb = int((time.perf_counter() - t0) * 1000)
        return Resp(r.geturl(), r.status, r.headers.items(),
                    _decode_body(raw, r.headers.get("Content-Encoding", "")), ttfb)
    except urllib.error.HTTPError as e:
        # 3xx/4xx/5xx all arrive here; they are responses, not failures.
        raw = b""
        try:
            raw = e.read(max_bytes)
        except Exception:
            pass
        ttfb = int((time.perf_counter() - t0) * 1000)
        return Resp(url, e.code, e.headers.items(),
                    _decode_body(raw, e.headers.get("Content-Encoding", "")), ttfb)


# ---------------------------------------------------------------------------
# HTML parsing (stdlib only)
# ---------------------------------------------------------------------------

SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "iframe"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class DOM(HTMLParser):
    """A single pass over the markup, collecting only what the checks need."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_count = 0
        self.title = ""
        self.description = ""
        self.meta_robots = ""
        self.viewport = False
        self.charset = False
        self.og_title = False
        self.lang = ""
        self.canonicals = []          # raw href strings
        self.hreflang = []            # (lang, href)
        self.headings = []            # (level, text)
        self.images = []              # (has_alt, has_dims, src, alt)
        self.links = []               # (href, anchor, rel_list, in_chrome)
        self.verification = []        # site-verification meta tags
        self.paragraphs = 0
        self.stylesheets = []         # href
        self.scripts = []             # (src, async, defer, module)
        self.picture_types = []       # <source type="image/webp"> etc
        self.preloads = []
        self.jsonld = []              # raw strings
        self.has_itemtype = False
        self.body_text = []

        self._skip = 0
        self._in_body = False
        self._title_buf = None
        self._h_buf = None
        self._h_level = 0
        self._a_buf = None
        self._a_href = None
        self._a_rel = []
        self._ld_buf = None
        self._chrome = 0              # inside nav / header / footer / aside

    # -- helpers
    @staticmethod
    def _d(attrs):
        return {(k or "").lower(): (v if v is not None else "") for k, v in attrs}

    @staticmethod
    def _rel(d):
        return [x.lower() for x in (d.get("rel") or "").split()]

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        d = self._d(attrs)

        if tag in SKIP_TAGS:
            if tag == "script":
                if "ld+json" in d.get("type", "").lower():
                    self._ld_buf = []
                elif d.get("src"):
                    self.scripts.append((d["src"], "async" in d, "defer" in d,
                                         d.get("type", "") == "module"))
            self._skip += 1
            return
        if self._skip:
            return

        if "itemtype" in d:
            self.has_itemtype = True

        if tag in ("nav", "header", "footer", "aside"):
            self._chrome += 1
        elif tag == "p":
            self.paragraphs += 1

        if tag == "html":
            self.lang = d.get("lang", "")
        elif tag == "body":
            self._in_body = True
        elif tag == "title":
            self.title_count += 1
            if self.title_count == 1:
                self._title_buf = []
        elif tag == "meta":
            name = d.get("name", "").lower()
            prop = d.get("property", "").lower()
            content = d.get("content", "")
            if "charset" in d or "content-type" in d.get("http-equiv", "").lower():
                self.charset = True
            if name == "description" and not self.description:
                self.description = " ".join(content.split())
            elif name in ("robots", "googlebot"):
                self.meta_robots = (self.meta_robots + " " + content).strip()
            elif name == "viewport":
                self.viewport = True
            if prop == "og:title":
                self.og_title = True
            if "verification" in name or name in ("google-site-verification", "msvalidate.01",
                                                  "yandex-verification", "p:domain_verify"):
                self.verification.append(name)
        elif tag == "link":
            rel = self._rel(d)
            href = d.get("href", "")
            if "canonical" in rel and href:
                self.canonicals.append(href)
            if "alternate" in rel and d.get("hreflang"):
                self.hreflang.append((d["hreflang"], href))
            if "stylesheet" in rel and href:
                self.stylesheets.append((href, d.get("media", "").lower()))
            if "preload" in rel and href:
                self.preloads.append((href, d.get("as", "").lower()))
        elif tag in HEADINGS:
            self._h_level = int(tag[1])
            self._h_buf = []
        elif tag == "img":
            self.images.append({
                "has_alt": "alt" in d,
                "has_dims": bool(d.get("width") and d.get("height"))
                            or "aspect-ratio" in d.get("style", ""),
                "src": d.get("src", "") or d.get("data-src", ""),
                "alt": d.get("alt", ""),
                "loading": d.get("loading", "").lower(),
                "srcset": bool(d.get("srcset") or d.get("data-srcset")),
                "fetchpriority": d.get("fetchpriority", "").lower(),
            })
            if self._a_buf is not None and d.get("alt"):
                self._a_buf.append(d["alt"])
        elif tag == "source":
            if d.get("type", "").startswith("image/"):
                self.picture_types.append(d["type"])
            srcset = d.get("srcset") or d.get("data-srcset") or ""
            for cand in srcset.split(","):
                url = cand.strip().split(" ")[0]
                if url:
                    self.images.append({
                        "has_alt": True,        # <source> carries no alt; the <img> does
                        "has_dims": True, "src": url, "alt": "", "loading": "lazy",
                        "srcset": True, "fetchpriority": "", "from_picture": True})
        elif tag == "a":
            self._a_href = d.get("href", "")
            self._a_rel = self._rel(d)
            self._a_buf = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in ("img", "meta", "link", "br", "hr", "input", "source"):
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in SKIP_TAGS:
            if tag == "script" and self._ld_buf is not None:
                self.jsonld.append("".join(self._ld_buf))
                self._ld_buf = None
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return

        if tag in ("nav", "header", "footer", "aside"):
            self._chrome = max(0, self._chrome - 1)

        if tag == "title" and self._title_buf is not None:
            self.title = " ".join("".join(self._title_buf).split())
            self._title_buf = None
        elif tag in HEADINGS and self._h_buf is not None:
            text = " ".join("".join(self._h_buf).split())
            self.headings.append((self._h_level, text))
            self._h_buf = None
        elif tag == "a" and self._a_buf is not None:
            anchor = " ".join("".join(self._a_buf).split())
            if self._a_href:
                self.links.append((self._a_href, anchor[:160], self._a_rel, self._chrome > 0))
            self._a_buf, self._a_href, self._a_rel = None, None, []

    def handle_data(self, data):
        if self._ld_buf is not None:
            self._ld_buf.append(data)
            return
        if self._skip:
            return
        if self._title_buf is not None:
            self._title_buf.append(data)
        if self._h_buf is not None:
            self._h_buf.append(data)
        if self._a_buf is not None:
            self._a_buf.append(data)
        if self._in_body:
            self.body_text.append(data)

    def error(self, message):  # HTMLParser in older versions
        pass


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------

class Crawler:
    def __init__(self, cfg):
        self.cfg = cfg
        self.pages: dict[str, Page] = {}
        self.robots = None
        self.robots_txt = ""
        self.robots_status = 0
        self.sitemap_urls: list[str] = []
        self.sitemap_entries: list[str] = []
        self.link_graph: dict[str, set] = defaultdict(set)
        self.anchors: dict[str, list] = defaultdict(list)
        self.external_status: dict[str, int] = {}
        self.progress = None          # optional callback(msg)

    def request(self, url: str, method: str = "GET"):
        """Follow redirects by hand so the whole chain stays visible."""
        chain, current, seen = [], url, set()
        for _ in range(10):
            if current in seen:
                return None, chain, "loop"
            seen.add(current)
            try:
                r = http_get(current, method, self.cfg.timeout, self.cfg.user_agent)
            except urllib.error.URLError as e:
                return None, chain, getattr(e, "reason", None).__class__.__name__ \
                    if getattr(e, "reason", None) else "URLError"
            except BlockedTarget:
                return None, chain, "blocked-private"
            except (socket.timeout, TimeoutError):
                return None, chain, "timeout"
            except Exception as e:
                return None, chain, type(e).__name__
            if r.is_redirect:
                loc = r.headers.get("location", "")
                if not loc:
                    return r, chain, ""
                nxt = normalise(up.urljoin(current, loc))
                chain.append((current, r.status_code, nxt))
                current = nxt
                continue
            return r, chain, ""
        return None, chain, "too many redirects"

    # -- robots & sitemaps -------------------------------------------------
    def load_robots(self, root: str):
        url = up.urljoin(root, "/robots.txt")
        r, _, err = self.request(url)
        self.robots = robotparser.RobotFileParser()
        if r is not None and r.status_code == 200:
            self.robots_status = 200
            self.robots_txt = r.text[:200000]
            self.robots.parse(self.robots_txt.splitlines())
            for line in self.robots_txt.splitlines():
                if line.lower().startswith("sitemap:"):
                    sm = line.split(":", 1)[1].strip()
                    if sm:
                        self.sitemap_urls.append(sm)
        else:
            self.robots_status = r.status_code if r is not None else 0
            self.robots.parse([])
        if not self.sitemap_urls:
            for guess in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"):
                g = up.urljoin(root, guess)
                rr, _, _ = self.request(g)
                if rr is not None and rr.status_code == 200 and "<" in rr.text[:200]:
                    self.sitemap_urls.append(g)
                    break

    def load_sitemaps(self):
        seen, queue = set(), list(self.sitemap_urls)
        while queue and len(self.sitemap_entries) < 50000:
            sm = queue.pop(0)
            if sm in seen:
                continue
            seen.add(sm)
            r, _, _ = self.request(sm)
            if r is None or r.status_code != 200:
                continue
            body = r.text
            locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", body, re.I | re.S)
            if "<sitemapindex" in body[:2000].lower():
                queue.extend(html_mod.unescape(l) for l in locs[:200])
            else:
                self.sitemap_entries.extend(normalise(html_mod.unescape(l)) for l in locs)
        self.sitemap_entries = list(dict.fromkeys(self.sitemap_entries))

    # -- parsing -----------------------------------------------------------
    def parse(self, page: Page, r: Resp) -> None:
        raw = r.text
        page.size_bytes = len(r.content)
        dom = DOM()
        try:
            dom.feed(raw)
            dom.close()
        except Exception:
            pass  # malformed markup must not abort the crawl

        page.title = dom.title
        page.title_count = dom.title_count
        page.description = dom.description
        page.meta_robots = dom.meta_robots.strip()
        page.x_robots = r.headers.get("x-robots-tag", "") or ""
        page.lang = dom.lang
        page.charset = dom.charset
        page.viewport = dom.viewport
        page.og = dom.og_title
        page.headings = dom.headings
        page.h1s = [t for lv, t in dom.headings if lv == 1]

        page.canonical_count = len(dom.canonicals)
        if dom.canonicals:
            page._canonical_raw = dom.canonicals[0]
            if dom.canonicals[0]:
                page.canonical = normalise(up.urljoin(page.final_url, dom.canonicals[0]))

        for lang, href in dom.hreflang:
            if href:
                page.hreflang.append((lang, normalise(up.urljoin(page.final_url, href))))

        page.images = len(dom.images)
        page.images_no_alt = sum(1 for i in dom.images if not i["has_alt"])
        page.images_no_dim = sum(1 for i in dom.images if not i["has_dims"])
        page.missing_alt_images = [
            normalise(up.urljoin(page.final_url, i["src"])) if i["src"]
            else "(inline/unknown source)"
            for i in dom.images if not i["has_alt"]][:60]
        for i in dom.images:
            if i["src"]:
                i.setdefault("from_picture", False)
                i["url"] = normalise(up.urljoin(page.final_url, i["src"]))
                page.image_details.append(i)
        page.picture_types = dom.picture_types
        page.preloads = [(normalise(up.urljoin(page.final_url, h)), a) for h, a in dom.preloads]
        page.stylesheets = [(normalise(up.urljoin(page.final_url, h)), m)
                            for h, m in dom.stylesheets]
        page.scripts = [(normalise(up.urljoin(page.final_url, s)), a, d, m)
                        for s, a, d, m in dom.scripts]
        # Blocking = stylesheets for screen plus scripts without async or defer.
        page.render_blocking = (
            sum(1 for _, media in page.stylesheets if media in ("", "all", "screen"))
            + sum(1 for _, is_async, is_defer, _ in page.scripts if not (is_async or is_defer)))
        page.paragraphs = dom.paragraphs
        page.verification = dom.verification

        low = raw.lower()
        page.analytics_tools = detect_tracking(low)
        page.analytics = bool(page.analytics_tools)
        if page.final_url.startswith("https://"):
            page.mixed_content = len(re.findall(r'(?:src|href)=["\']http://', raw, re.I))

        for href, anchor, rel, in_chrome in dom.links:
            href = href.strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "sms:")):
                continue
            target = normalise(up.urljoin(page.final_url, href))
            if not target.startswith(("http://", "https://")):
                continue
            nofollow = any(x in rel for x in ("nofollow", "sponsored", "ugc"))
            if same_site(target, self.cfg.root_host):
                page.internal_links.append((target, anchor, nofollow, in_chrome))
            else:
                page.external_links.append((target, anchor, nofollow, in_chrome))

        for block in dom.jsonld:
            try:
                data = json.loads(block)
            except Exception:
                page.schema_errors += 1
                continue
            for node in (data if isinstance(data, list) else [data]):
                if not isinstance(node, dict):
                    continue
                graph = node.get("@graph")
                nodes = graph if isinstance(graph, list) else [node]
                for n in nodes:
                    if isinstance(n, dict):
                        t = n.get("@type")
                        if isinstance(t, list):
                            page.schema_types.extend(str(x) for x in t)
                        elif t:
                            page.schema_types.append(str(t))
                        else:
                            page.schema_types.append("__notype__")
        if not page.schema_types and dom.has_itemtype:
            page.schema_types.append("Microdata")

        text = " ".join("".join(dom.body_text).split())
        page.word_count = len(text.split())
        page.text_ratio = round(len(text) / max(len(raw), 1) * 100, 1)
        page.content_hash = hashlib.md5(text.lower().encode("utf-8", "ignore")).hexdigest()
        page.shingles = shingle_set(text)
        page.text = text[:60000]   # kept for keyword and readability analysis

    # -- loop --------------------------------------------------------------
    def crawl(self, start: str):
        cfg = self.cfg
        queue = deque([(normalise(start), 0)])
        queued = {normalise(start)}
        n = 0
        while queue and len(self.pages) < cfg.max_pages:
            url, depth = queue.popleft()
            if cfg.respect_robots and self.robots and not self.robots.can_fetch(cfg.user_agent, url):
                p = Page(url=url, depth=depth, error="blocked-by-robots")
                p.status = -1
                self.pages[url] = p
                continue
            page = self.fetch_page(url, depth)
            self.pages[url] = page
            n += 1
            if self.progress and n % 5 == 0:
                self.progress(f"crawled {n} · {len(queue)} queued")
            elif not cfg.quiet:
                sys.stderr.write(f"\r  crawled {n:>5}  queue {len(queue):>5}  {url[:64]:<64}")
                sys.stderr.flush()
            if page.status == 200 and depth < cfg.max_depth:
                for target, anchor, nofollow, _ in page.internal_links:
                    self.link_graph[target].add(page.final_url or url)
                    self.anchors[target].append(anchor)
                    if target not in queued and is_html_url(target) and len(queued) < cfg.max_pages * 3:
                        queued.add(target)
                        queue.append((target, depth + 1))
            time.sleep(cfg.delay)
        if not cfg.quiet:
            sys.stderr.write("\r" + " " * 100 + "\r")

    def fetch_page(self, url: str, depth: int) -> Page:
        page = Page(url=url, depth=depth)
        r, chain, err = self.request(url)
        page.redirect_chain = chain
        if r is None:
            page.error = err or "request failed"
            page.status = 0 if err != "loop" else -2
            return page
        page.status = r.status_code
        page.final_url = normalise(chain[-1][2] if chain else r.url)
        page.ttfb_ms = r._ttfb
        page.headers = dict(r.headers)
        page.content_type = page.headers.get("content-type", "")
        page.size_bytes = len(r.content)
        if r.status_code == 200 and "html" in page.content_type.lower():
            try:
                self.parse(page, r)
            except Exception as e:
                page.error = f"parse error: {e}"
        return page

    def check_external_links(self, limit: int = 300):
        targets = []
        for p in self.pages.values():
            for url, _, _, _ in p.external_links:
                if url not in self.external_status:
                    self.external_status[url] = 0
                    targets.append(url)
        targets = targets[:limit]

        def probe(u):
            try:
                r = http_get(u, "HEAD", self.cfg.timeout, self.cfg.user_agent)
                if r.status_code in (403, 405, 501):
                    r = http_get(u, "GET", self.cfg.timeout, self.cfg.user_agent)
                return u, r.status_code
            except Exception:
                return u, 0

        with cf.ThreadPoolExecutor(max_workers=self.cfg.threads) as ex:
            for u, st in ex.map(probe, targets):
                self.external_status[u] = st

# ---------------------------------------------------------------------------
# Check engine
# ---------------------------------------------------------------------------

GENERIC_ANCHORS = {"click here", "here", "read more", "more", "link", "this",
                   "learn more", "more info", "details", "continue", "click"}


class Auditor:
    def __init__(self, crawler: Crawler, cfg):
        self.c = crawler
        self.cfg = cfg
        self.issues: list[Issue] = []
        self.notes: dict = {}

    def add(self, code: str, url: str, detail: str = ""):
        self.issues.append(Issue(code, url, detail))

    # ---- site level ------------------------------------------------------
    def check_site(self):
        c, cfg = self.c, self.cfg
        root = cfg.start_url

        if up.urlsplit(root).scheme != "https":
            self.add("HTTPS_MISSING", root)
        else:
            http_url = "http://" + up.urlsplit(root).netloc + "/"
            r, chain, _ = c.request(http_url)
            if r is not None and r.status_code == 200 and not chain:
                self.add("HTTP_NOT_REDIRECTED", http_url, "HTTP returned 200 without redirecting")
            home = c.pages.get(normalise(root))
            if home and home.status == 200 and "strict-transport-security" not in home.headers:
                self.add("NO_HSTS", root)

        # www / non-www duplication
        host = up.urlsplit(root).netloc
        other = host.removeprefix("www.") if host.startswith("www.") else "www." + host
        alt = f"{up.urlsplit(root).scheme}://{other}/"
        r, chain, _ = c.request(alt)
        if r is not None and r.status_code == 200 and not chain:
            self.add("WWW_DUPLICATE", alt, f"{other} serves 200 instead of redirecting to {host}")

        # robots.txt
        if c.robots_status != 200:
            self.add("NO_ROBOTS_TXT", up.urljoin(root, "/robots.txt"),
                     f"returned status {c.robots_status or 'no response'}")
        else:
            lines = [l.strip().lower() for l in c.robots_txt.splitlines()]
            ua_all, blocked_all = False, False
            for l in lines:
                if l.startswith("user-agent:"):
                    ua_all = l.split(":", 1)[1].strip() == "*"
                elif ua_all and l.startswith("disallow:") and l.split(":", 1)[1].strip() == "/":
                    blocked_all = True
            if blocked_all:
                self.add("ROBOTS_BLOCKS_ALL", up.urljoin(root, "/robots.txt"),
                         "Disallow: / for User-agent: *")

        # sitemaps
        if not c.sitemap_entries:
            self.add("NO_SITEMAP", root, "no sitemap found in robots.txt or at the usual paths")

        # soft 404
        probe = up.urljoin(root, "/this-page-should-not-exist-%s" % int(time.time()))
        r, chain, _ = c.request(probe)
        if r is not None and r.status_code == 200:
            self.add("SOFT_404", probe, "a random missing URL returned 200 instead of 404")
        self.notes["404_status"] = r.status_code if r is not None else "no response"

        # homepage entity markup
        home = c.pages.get(normalise(root))
        if home and home.status == 200:
            if not any(t in ("Organization", "LocalBusiness", "Corporation", "NGO", "OnlineStore",
                             "Store", "Restaurant", "ProfessionalService")
                       for t in home.schema_types):
                self.add("NO_ORG_SCHEMA", home.final_url or root)

    # ---- page level ------------------------------------------------------
    def check_pages(self):
        c = self.c
        pages = c.pages
        indexable = [p for p in pages.values() if p.indexable and "html" in p.content_type.lower()]

        # inlink counts
        for p in pages.values():
            p.inlinks = len(c.link_graph.get(p.url, set()) | c.link_graph.get(p.final_url, set()))

        titles, descs, hashes = defaultdict(list), defaultdict(list), defaultdict(list)

        for p in pages.values():
            u = p.final_url or p.url

            if p.error == "blocked-by-robots":
                self.add("ROBOTS_BLOCKED", p.url, "disallowed in robots.txt but linked internally")
                continue
            if p.status == -2:
                self.add("REDIRECT_LOOP", p.url)
                continue
            if p.status == 0:
                self.add("STATUS_5XX", p.url, p.error or "no response")
                continue
            if 500 <= p.status < 600:
                self.add("STATUS_5XX", p.url, f"HTTP {p.status}")
                continue
            if 400 <= p.status < 500:
                self.add("STATUS_4XX", p.url, f"HTTP {p.status}")
                srcs = sorted(c.link_graph.get(p.url, set()))[:5]
                if srcs:
                    self.add("BROKEN_INTERNAL_LINK", p.url,
                             f"HTTP {p.status} · linked from {len(c.link_graph.get(p.url, set()))} page(s), e.g. {srcs[0]}")
                continue

            # redirects
            if len(p.redirect_chain) >= 2:
                path = " → ".join(f"{s}" for _, s, _ in p.redirect_chain)
                self.add("REDIRECT_CHAIN", p.url, f"{len(p.redirect_chain)} hops ({path}) ending at {p.final_url}")
            if p.redirect_chain:
                if any(s in (302, 307) for _, s, _ in p.redirect_chain):
                    self.add("TEMP_REDIRECT", p.url, f"302/307 → {p.final_url}")
                if c.link_graph.get(p.url):
                    self.add("INTERNAL_LINK_TO_REDIRECT", p.url,
                             f"{len(c.link_graph[p.url])} internal link(s) point here instead of {p.final_url}")

            if p.status != 200:
                continue

            # A URL that redirects is audited at its destination, not twice. Without this
            # every 301 would raise phantom duplicate-title and duplicate-content findings.
            if p.redirect_chain and normalise(p.final_url) != normalise(p.url) \
                    and normalise(p.final_url) in pages:
                continue

            # performance-ish header checks
            if p.ttfb_ms > SLOW_TTFB_MS:
                self.add("SLOW_RESPONSE", u, f"{p.ttfb_ms} ms")
            enc = p.headers.get("content-encoding", "")
            if "html" in p.content_type.lower() and not enc and p.size_bytes > 4096:
                self.add("NO_COMPRESSION", u, f"{p.size_bytes // 1024} KB uncompressed")
            if "cache-control" not in p.headers and "expires" not in p.headers:
                self.add("NO_CACHE_HEADERS", u)
            if p.size_bytes > 500_000:
                self.add("LARGE_HTML", u, f"{p.size_bytes // 1024} KB")
            if p.mixed_content:
                self.add("MIXED_CONTENT", u, f"{p.mixed_content} http:// subresource(s)")

            if "html" not in p.content_type.lower():
                continue

            # indexability
            robots = (p.meta_robots + " " + p.x_robots).lower()
            if "noindex" in robots:
                self.add("NOINDEX", u, p.meta_robots or p.x_robots)
            if "nofollow" in robots:
                self.add("NOFOLLOW_PAGE", u, p.meta_robots or p.x_robots)

            if p.canonical_count == 0:
                if "noindex" not in robots:
                    self.add("CANONICAL_MISSING", u)
            elif p.canonical_count > 1:
                self.add("CANONICAL_MULTIPLE", u, f"{p.canonical_count} canonical tags")
            if p.canonical:
                raw = getattr(p, "_canonical_raw", "")
                if raw and not raw.lower().startswith(("http://", "https://")):
                    self.add("CANONICAL_RELATIVE", u, raw)
                if normalise(p.canonical) != normalise(u):
                    self.add("CANONICAL_OTHER", u, f"→ {p.canonical}")
                    tgt = pages.get(normalise(p.canonical))
                    if tgt and (tgt.status != 200 or tgt.redirect_chain):
                        self.add("CANONICAL_TO_NON200", u,
                                 f"canonical → {p.canonical} (HTTP {tgt.status})")

            # URL hygiene
            path = up.urlsplit(u).path
            if len(u) > MAX_URL_LEN:
                self.add("URL_TOO_LONG", u, f"{len(u)} characters")
            if "_" in path:
                self.add("URL_UNDERSCORES", u)
            if any(ch.isupper() for ch in path):
                self.add("URL_UPPERCASE", u)
            if up.urlsplit(u).query:
                self.add("URL_PARAMS", u, "?" + up.urlsplit(u).query)
            if p.depth > MAX_DEPTH_OK:
                self.add("TOO_DEEP", u, f"{p.depth} clicks from the homepage")

            # title
            if not p.title:
                self.add("TITLE_MISSING", u)
            else:
                titles[p.title.lower()].append(u)
                if len(p.title) > TITLE_MAX:
                    self.add("TITLE_TOO_LONG", u, f"{len(p.title)} chars: {p.title[:80]}")
                elif len(p.title) < TITLE_MIN:
                    self.add("TITLE_TOO_SHORT", u, f"{len(p.title)} chars: {p.title}")
            if p.title_count > 1:
                self.add("TITLE_MULTIPLE", u, f"{p.title_count} title tags")

            # description
            if not p.description:
                self.add("DESC_MISSING", u)
            else:
                descs[p.description.lower()].append(u)
                if not (DESC_MIN <= len(p.description) <= DESC_MAX):
                    self.add("DESC_LENGTH", u, f"{len(p.description)} chars")

            # headings
            if not p.h1s:
                self.add("H1_MISSING", u)
            elif len(p.h1s) > 1:
                self.add("H1_MULTIPLE", u, f"{len(p.h1s)} H1s: " + " | ".join(p.h1s[:3])[:120])
            levels = [lv for lv, _ in p.headings]
            for a, b in zip(levels, levels[1:]):
                if b - a > 1:
                    self.add("HEADING_SKIP", u, f"H{a} followed by H{b}")
                    break
            if p.title and p.h1s:
                tw = set(re.findall(r"[a-z]{4,}", p.title.lower()))
                hw = set(re.findall(r"[a-z]{4,}", p.h1s[0].lower()))
                if tw and hw and not (tw & hw):
                    self.add("TITLE_H1_MISMATCH", u, f"title “{p.title[:50]}” vs H1 “{p.h1s[0][:50]}”")

            # mobile / html basics
            if not p.viewport:
                self.add("NO_VIEWPORT", u)
            if not p.lang:
                self.add("NO_LANG", u)
            if not p.charset:
                self.add("NO_CHARSET", u)
            if not p.og:
                self.add("NO_OG", u)
            if not p.analytics:
                self.add("NO_ANALYTICS", u)

            # images
            if p.images_no_alt:
                self.add("IMG_NO_ALT", u, f"{p.images_no_alt} of {p.images} images")
            if p.images_no_dim:
                self.add("IMG_NO_DIMENSIONS", u, f"{p.images_no_dim} of {p.images} images")

            # content
            if p.word_count < THIN_CONTENT_WORDS and "noindex" not in robots:
                self.add("THIN_CONTENT", u, f"{p.word_count} words")
                hashes[p.content_hash].append(u)
            else:
                hashes[p.content_hash].append(u)
            if p.text_ratio < 5 and p.word_count > 0:
                self.add("LOW_TEXT_RATIO", u, f"{p.text_ratio}% text")

            # links
            internal = [l for l in p.internal_links]
            if not internal:
                self.add("NO_INTERNAL_LINKS", u)
            elif p.inlinks < 3 and p.depth > 0:
                self.add("FEW_INLINKS", u, f"{p.inlinks} internal link(s) point here")
            if len(p.internal_links) + len(p.external_links) > MAX_LINKS_PER_PAGE:
                self.add("TOO_MANY_LINKS", u, f"{len(p.internal_links) + len(p.external_links)} links")
            generic = [a for _, a, _, _ in p.internal_links if a.lower().strip(" .:!→>") in GENERIC_ANCHORS]
            if generic:
                self.add("GENERIC_ANCHOR", u, f"{len(generic)} generic anchor(s): " + ", ".join(sorted(set(generic))[:4]))

            # structured data
            if not p.schema_types:
                self.add("SCHEMA_MISSING", u)
            if p.schema_errors:
                self.add("SCHEMA_INVALID", u, f"{p.schema_errors} JSON-LD block(s) failed to parse")
            if "__notype__" in p.schema_types:
                self.add("SCHEMA_NO_TYPE", u)

            # external link health
            for ext, _, _, _ in p.external_links:
                st = c.external_status.get(ext)
                if st is not None and (st == 0 or st >= 400):
                    self.add("BROKEN_EXTERNAL_LINK", u, f"{ext} → {st or 'no response'}")

        # duplicates
        for t, urls in titles.items():
            if len(urls) > 1:
                for u in urls:
                    self.add("TITLE_DUPLICATE", u, f"shared by {len(urls)} pages: “{t[:60]}”")
        for d, urls in descs.items():
            if len(urls) > 1:
                for u in urls:
                    self.add("DESC_DUPLICATE", u, f"shared by {len(urls)} pages")
        for h, urls in hashes.items():
            if len(urls) > 1:
                for u in urls:
                    self.add("DUPLICATE_CONTENT", u, f"byte-identical body text on {len(urls)} URLs")

        # near-duplicates (sampled to keep this O(n·k) rather than O(n²) on big crawls)
        cand = [p for p in indexable if p.shingles][:400]
        reported = set()
        for i, a in enumerate(cand):
            for b in cand[i + 1:]:
                ua, ub = a.final_url or a.url, b.final_url or b.url
                if (ua, ub) in reported or a.content_hash == b.content_hash:
                    continue
                if jaccard(a.shingles, b.shingles) > 0.85:
                    reported.add((ua, ub))
                    self.add("DUPLICATE_CONTENT", ua, f"~{int(jaccard(a.shingles, b.shingles)*100)}% similar to {ub}")

        # hreflang reciprocity
        for p in pages.values():
            if not p.hreflang:
                continue
            for lang, target in p.hreflang:
                t = pages.get(normalise(target))
                if t is not None and t.hreflang:
                    if not any(normalise(x) == normalise(p.final_url or p.url) for _, x in t.hreflang):
                        self.add("NO_HREFLANG_RETURN", p.final_url or p.url, f"{lang} → {target} has no return tag")

        # sitemap cross-checks
        sm = set(c.sitemap_entries)
        if sm:
            for s in list(sm)[:2000]:
                pg = pages.get(s)
                if pg is None:
                    continue
                if pg.status != 200:
                    self.add("SITEMAP_BAD_URL", s, f"HTTP {pg.status} but listed in the sitemap")
                elif not pg.indexable:
                    self.add("SITEMAP_NONCANONICAL", s, "listed in sitemap but noindexed")
                elif pg.canonical and normalise(pg.canonical) != normalise(pg.final_url or s):
                    self.add("SITEMAP_NONCANONICAL", s, f"canonical points to {pg.canonical}")
            for p in indexable:
                u = p.final_url or p.url
                if u not in sm and normalise(u) not in sm:
                    self.add("NOT_IN_SITEMAP", u)
            for s in sm:
                if s in pages and pages[s].status == 200 and not c.link_graph.get(s):
                    if normalise(s) != normalise(self.cfg.start_url):
                        self.add("ORPHAN_PAGE", s, "in the sitemap but no internal links point to it")


# ---------------------------------------------------------------------------
# Search Console CSV (optional) — rankings, cannibalisation, CTR
# ---------------------------------------------------------------------------

CTR_CURVE = {1: .28, 2: .15, 3: .11, 4: .08, 5: .06, 6: .05, 7: .04,
             8: .033, 9: .028, 10: .025}


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(f, dialect=dialect))


def col(row, *names):
    lowered = {k.lower().strip(): v for k, v in row.items() if k}
    for n in names:
        for k, v in lowered.items():
            if n in k:
                return v
    return ""


def analyse_gsc(path, auditor: Auditor):
    rows = read_csv_rows(path)
    if not rows:
        return {}
    recs = []
    for r in rows:
        q = col(r, "query", "keyword", "search term")
        page = col(r, "landing page", "page", "url", "address")
        try:
            pos = float(col(r, "position", "rank") or 0)
            clicks = float((col(r, "click") or "0").replace(",", ""))
            imps = float((col(r, "impression") or "0").replace(",", ""))
        except ValueError:
            continue
        if not q or not pos:
            continue
        recs.append({"query": q, "page": page, "pos": pos, "clicks": clicks, "impressions": imps})
    if not recs:
        return {}

    striking = sorted([r for r in recs if 10.5 <= r["pos"] <= 20.5 and r["impressions"] >= 10],
                      key=lambda r: -r["impressions"])[:40]
    for r in striking:
        auditor.add("STRIKING_DISTANCE", r["page"] or "(page not in export)",
                    f"“{r['query']}” · position {r['pos']:.1f} · {int(r['impressions'])} impressions/mo")

    low_ctr = []
    for r in recs:
        p = int(round(r["pos"]))
        if p in CTR_CURVE and r["impressions"] >= 100:
            ctr = r["clicks"] / r["impressions"]
            if ctr < CTR_CURVE[p] * 0.5:
                low_ctr.append((r, ctr))
    for r, ctr in sorted(low_ctr, key=lambda x: -x[0]["impressions"])[:25]:
        auditor.add("LOW_CTR", r["page"] or "(page not in export)",
                    f"“{r['query']}” · position {r['pos']:.1f} · CTR {ctr*100:.1f}% vs ~{CTR_CURVE[int(round(r['pos']))]*100:.0f}% expected")

    by_query = defaultdict(set)
    for r in recs:
        if r["page"] and r["impressions"] >= 20:
            by_query[r["query"].lower()].add(r["page"])
    cannibal = {q: ps for q, ps in by_query.items() if len(ps) > 1}
    for q, ps in sorted(cannibal.items(), key=lambda kv: -len(kv[1]))[:30]:
        auditor.add("CANNIBALISATION", sorted(ps)[0],
                    f"“{q}” ranks with {len(ps)} URLs: " + ", ".join(sorted(ps)[:3]))

    return {
        "queries": len(recs),
        "clicks": int(sum(r["clicks"] for r in recs)),
        "impressions": int(sum(r["impressions"] for r in recs)),
        "avg_pos": round(statistics.mean(r["pos"] for r in recs), 1),
        "top3": sum(1 for r in recs if r["pos"] <= 3),
        "page1": sum(1 for r in recs if r["pos"] <= 10),
        "striking": len([r for r in recs if 10.5 <= r["pos"] <= 20.5]),
        "cannibal": len(cannibal),
        "top_queries": sorted(recs, key=lambda r: -r["clicks"])[:15],
        "striking_list": striking[:15],
    }


# ---------------------------------------------------------------------------
# Backlink CSV (optional) — off-page profile
# ---------------------------------------------------------------------------

BRAND_STOP = {"http", "https", "www", "com", "the", "and"}


def analyse_backlinks(path, root_host, auditor, brand_name="", keyword_terms=None):
    """Full off-page profile from any Ahrefs / Semrush / Majestic / GSC links export."""
    rows = read_csv_rows(path)
    if not rows:
        return {}
    keyword_terms = keyword_terms or set()
    brand_tokens = set(re.findall(r"[a-z0-9]{3,}",
                                  (brand_name or registrable(root_host).split(".")[0]).lower()))
    links = []
    for r in rows:
        src_url = col(r, "source url", "referring page url", "source", "from url",
                      "url from", "backlink", "linking page")
        dom = col(r, "referring domain", "source domain", "domain", "linking site", "site")
        if not (src_url or dom):
            continue
        anchor = col(r, "anchor", "link text")
        target = col(r, "target url", "destination", "to url", "url to", "target page",
                     "linked page", "top linked page")
        nofollow_raw = str(col(r, "nofollow", "follow", "link type", "type", "rel")).lower()
        auth = col(r, "domain rating", "authority score", "domain authority", "trust flow",
                   "rating", "dr", "as")
        first_seen = col(r, "first seen", "first indexed", "date found", "seen")
        count_raw = col(r, "backlinks", "links", "count", "number of links")
        host = registrable(dom or up.urlsplit(src_url).netloc)
        if not host:
            continue
        try:
            authv = float(re.sub(r"[^\d.]", "", auth)) if auth else None
        except ValueError:
            authv = None
        try:
            n_links = max(1, int(re.sub(r"[^\d]", "", count_raw))) if count_raw else 1
        except ValueError:
            n_links = 1
        links.append({
            "host": host, "anchor": anchor.strip(), "target": target.strip(),
            "nofollow": ("nofollow" in nofollow_raw or "ugc" in nofollow_raw
                         or "sponsored" in nofollow_raw),
            "auth": authv, "first_seen": first_seen.strip(), "n": n_links,
            "tld": host.rsplit(".", 1)[-1] if "." in host else "",
        })
    if not links:
        return {}

    total = sum(l["n"] for l in links)
    domains = Counter()
    for l in links:
        domains[l["host"]] += l["n"]
    rd = len(domains)
    nofollow_n = sum(l["n"] for l in links if l["nofollow"])
    follow_n = total - nofollow_n

    anchor_types = Counter()
    anchors = Counter()
    for l in links:
        a = l["anchor"]
        if a:
            anchors[a] += l["n"]
        anchor_types[classify_anchor(a, l["target"] or root_host,
                                     brand_tokens, keyword_terms)] += l["n"]

    targets = Counter()
    for l in links:
        if l["target"]:
            targets[l["target"]] += l["n"]

    tlds = Counter()
    for l in links:
        if l["tld"]:
            tlds[l["tld"]] += 1

    auths = [l["auth"] for l in links if l["auth"] is not None]
    buckets = Counter()
    for a in auths:
        buckets["0–20" if a <= 20 else "21–40" if a <= 40 else "41–60" if a <= 60
                else "61–80" if a <= 80 else "81–100"] += 1
    domain_auth = {}
    for l in links:
        if l["auth"] is not None:
            domain_auth[l["host"]] = max(domain_auth.get(l["host"], 0), l["auth"])

    exact_share = anchor_types["Exact match"] / max(total, 1)
    branded_share = anchor_types["Branded"] / max(total, 1)
    nofollow_share = nofollow_n / max(total, 1)

    if auditor:
        if rd < 25:
            auditor.add("LOW_REFERRING_DOMAINS", root_host,
                        f"{rd} referring domains across {total} links")
        if nofollow_share > 0.75:
            auditor.add("NOFOLLOW_HEAVY", root_host,
                        f"{nofollow_share*100:.0f}% of links are nofollow, UGC or sponsored")
        if exact_share > 0.20 and total > 30:
            top = ", ".join(f"“{a}” ({n})" for a, n in anchors.most_common(3))
            auditor.add("ANCHOR_OVER_OPTIMISED", root_host,
                        f"{exact_share*100:.0f}% exact-match anchors "
                        f"(natural profiles sit under 10%) · most common: {top}")
        if branded_share < 0.30 and total > 30:
            auditor.add("ANCHOR_OVER_OPTIMISED", root_host,
                        f"only {branded_share*100:.0f}% branded anchors — healthy profiles are "
                        f"usually 40–70% branded")

    return {
        "links": total, "rows": len(links), "domains": rd,
        "follow": follow_n, "nofollow": nofollow_n,
        "nofollow_share": round(nofollow_share * 100),
        "exact_share": round(exact_share * 100),
        "branded_share": round(branded_share * 100),
        "avg_auth": round(statistics.mean(auths), 1) if auths else None,
        "auth_buckets": [(k, buckets[k]) for k in ("81–100", "61–80", "41–60", "21–40", "0–20")
                         if buckets.get(k)],
        "top_domains": [(d, n, domain_auth.get(d)) for d, n in domains.most_common(20)],
        "top_anchors": [(a, n, classify_anchor(a, root_host, brand_tokens, keyword_terms))
                        for a, n in anchors.most_common(20)],
        "anchor_types": anchor_types,
        "top_targets": targets.most_common(15),
        "tlds": tlds.most_common(10),
    }


# ---------------------------------------------------------------------------
# Keyword extraction & content quality
# ---------------------------------------------------------------------------

STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be because been
before being below between both but by can cannot can't could couldn't did didn't do
does doesn't doing don't down during each few for from further had hadn't has hasn't
have haven't having he her here hers herself him himself his how i if in into is isn't
it its itself just let's me more most mustn't my myself no nor not of off on once only
or other ought our ours ourselves out over own same shan't she should shouldn't so some
such than that the their theirs them themselves then there these they this those through
to too under until up very was wasn't we were weren't what when where which while who
whom why with won't would wouldn't you your yours yourself yourselves us via new get got
also may might must shall will one two three make made using use used need needs want
like well much many best top good great see read find know take give go come look use
day time way year years today home page site website click here menu skip content
""".split())

# Phrases that add length without adding information. Not a style opinion: each one
# can be deleted from a sentence with no loss of meaning.
FILLER_PHRASES = [
    "in today's digital landscape", "in today's digital age", "in today's fast-paced",
    "in the ever-evolving", "ever-evolving landscape", "in the world of", "when it comes to",
    "it is important to note", "it's important to note", "it is worth noting",
    "it should be noted", "needless to say", "at the end of the day", "in conclusion",
    "last but not least", "first and foremost", "plays a crucial role", "plays a vital role",
    "plays a key role", "a testament to", "the power of", "unlock the", "harness the",
    "delve into", "dive deep into", "navigate the", "a wide range of", "a variety of",
    "wide array of", "in order to", "due to the fact that", "for the purpose of",
    "with that being said", "that being said", "it goes without saying",
    "whether you're a", "look no further", "the key to", "one of the most important",
    "in this article", "in this blog post", "we will explore", "let's explore",
    "game-changer", "cutting-edge", "state-of-the-art", "seamless integration",
    "robust solution", "take your", "to the next level", "elevate your", "revolutionize",
    "unparalleled", "unlock the potential", "comprehensive guide", "ultimate guide",
    "everything you need to know",
]

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]+")


def syllables(word: str) -> int:
    w = word.lower().strip("'-")
    if not w:
        return 1
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def readability(text: str):
    """Flesch Reading Ease and Flesch–Kincaid grade level."""
    sents = [s for s in SENT_SPLIT.split(text) if s.strip()]
    words = WORD_RE.findall(text)
    if len(words) < 30 or not sents:
        return None
    syl = sum(syllables(w) for w in words)
    wps = len(words) / len(sents)
    spw = syl / len(words)
    flesch = 206.835 - 1.015 * wps - 84.6 * spw
    grade = 0.39 * wps + 11.8 * spw - 15.59
    lengths = [len(WORD_RE.findall(s)) for s in sents]
    return {
        "flesch": round(flesch, 1),
        "grade": round(max(grade, 0), 1),
        "sentences": len(sents),
        "avg_sentence": round(wps, 1),
        "longest_sentence": max(lengths) if lengths else 0,
        "sentence_variation": round(statistics.pstdev(lengths), 1) if len(lengths) > 1 else 0.0,
    }


def specificity(text: str) -> dict:
    """Concrete detail: numbers, money, dates, proper nouns, quotes."""
    words = WORD_RE.findall(text)
    n = max(len(words), 1)
    numbers = len(re.findall(r"\b\d[\d,.]*\b", text))
    money = len(re.findall(r"[$£€¥]\s?\d|\b\d+\s?(?:USD|GBP|EUR|%)", text))
    dates = len(re.findall(r"\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                           r"[a-z]*\s+\d{1,2}\b", text))
    # Capitalised words that aren't sentence-initial are a decent proper-noun proxy.
    proper = len(re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b", text))
    quotes = len(re.findall(r"[\"“”]", text)) // 2
    total = numbers + money * 2 + dates * 2 + proper + quotes * 2
    return {"numbers": numbers, "dates": dates, "proper_nouns": proper, "quotes": quotes,
            "per_100_words": round(total / n * 100, 1)}


def filler_hits(text: str):
    low = text.lower()
    hits = [(p, low.count(p)) for p in FILLER_PHRASES if p in low]
    return sorted(hits, key=lambda x: -x[1])


def repetition(text: str) -> float:
    """Share of 5-word sequences that appear more than once."""
    words = [w.lower() for w in WORD_RE.findall(text)]
    if len(words) < 60:
        return 0.0
    grams = [" ".join(words[i:i + 5]) for i in range(len(words) - 5)]
    c = Counter(grams)
    repeated = sum(v for v in c.values() if v > 1)
    return round(repeated / max(len(grams), 1) * 100, 1)


def ngrams(text: str, nmax: int = 3):
    """Keyword candidates: 1–3 word phrases that don't start or end on a stopword."""
    tokens = [w.lower() for w in WORD_RE.findall(text)]
    out = Counter()
    for n in range(1, nmax + 1):
        for i in range(len(tokens) - n + 1):
            gram = tokens[i:i + n]
            if gram[0] in STOPWORDS or gram[-1] in STOPWORDS:
                continue
            if any(len(t) < 3 for t in gram):
                continue
            if n == 1 and len(gram[0]) < 4:
                continue
            out[" ".join(gram)] += 1
    return out


def analyse_content(crawler, auditor=None):
    """Extract topic keywords and measure content quality across the crawl."""
    pages = [p for p in crawler.pages.values()
             if p.status == 200 and "html" in p.content_type.lower() and p.indexable and p.text]
    if not pages:
        return {}

    N = len(pages)
    body_counts = {}
    df = Counter()
    for p in pages:
        c = ngrams(p.text)
        body_counts[p.final_url or p.url] = c
        for term in c:
            df[term] += 1

    import math
    page_terms = {}
    for url, counts in body_counts.items():
        total = sum(counts.values()) or 1
        scored = []
        for term, n in counts.items():
            if n < 2 and N > 3:
                continue
            idf = math.log((N + 1) / (df[term] + 0.5))
            scored.append((term, (n / total) * idf * math.log(1 + n)))
        scored.sort(key=lambda x: -x[1])
        # Drop 1-grams already contained in a higher-ranked phrase.
        picked = []
        for term, s in scored:
            if any(term in kept and term != kept for kept, _ in picked):
                continue
            picked.append((term, s))
            if len(picked) == 6:
                break
        page_terms[url] = picked

    # Site-level seed keywords come from titles, H1s and descriptions: high-signal
    # text that isn't repeated navigation and footer boilerplate.
    seed = Counter()
    seed_pages = defaultdict(set)
    for p in pages:
        u = p.final_url or p.url
        for field_text in [p.title, p.description] + list(p.h1s):
            if not field_text:
                continue
            for term, n in ngrams(field_text).items():
                seed[term] += n
                seed_pages[term].add(u)
    # Multi-word phrases are far more useful as seed keywords than bare nouns, so
    # weight by length, then drop any term wholly contained in a stronger phrase.
    ranked_seed = sorted(
        ((t, c, len(seed_pages[t])) for t, c in seed.items()),
        key=lambda x: -(x[1] * (1 + math.log(1 + x[2])) * (1 + 0.6 * (x[0].count(" ")))))
    site_keywords = []
    for term, c, npages in ranked_seed:
        if any(term in kept and term != kept for kept, _, _ in site_keywords):
            continue
        site_keywords.append((term, c, npages))
        if len(site_keywords) == 22:
            break

    # Per-page quality
    quality = {}
    for p in pages:
        u = p.final_url or p.url
        r = readability(p.text)
        spec = specificity(p.text)
        fill = filler_hits(p.text)
        rep = repetition(p.text)
        quality[u] = {"read": r, "spec": spec, "filler": fill, "repetition": rep,
                      "words": p.word_count, "terms": [t for t, _ in page_terms.get(u, [])]}

        if auditor and p.word_count >= 150:
            top = page_terms.get(u, [])
            if top and p.title and N >= 10 and p.depth > 0:
                hay = (p.title + " " + " ".join(p.h1s)).lower()
                top3 = [t for t, _ in top[:3]]
                if not any(any(w in hay for w in term.split()) for term in top3):
                    auditor.add("TOPIC_NOT_IN_TITLE", u,
                                f"page reads as being about “{top3[0]}” but the title says "
                                f"“{p.title[:60]}”")
            if r:
                if r["flesch"] < 30:
                    auditor.add("HARD_TO_READ", u,
                                f"Flesch {r['flesch']} · reading level grade {r['grade']}")
                if r["avg_sentence"] > 25:
                    auditor.add("LONG_SENTENCES", u,
                                f"{r['avg_sentence']} words per sentence on average, "
                                f"longest {r['longest_sentence']}")
            filler_total = sum(n for _, n in fill)
            if filler_total >= 3 and filler_total / max(p.word_count, 1) * 1000 > 3:
                auditor.add("FILLER_HEAVY", u,
                            f"{filler_total} filler phrases: " +
                            ", ".join(f"“{ph}”" for ph, _ in fill[:3]))
            if spec["per_100_words"] < 2.0 and p.word_count >= 150:
                auditor.add("LOW_SPECIFICITY", u,
                            f"{spec['numbers']} numbers, {spec['dates']} dates, "
                            f"{spec['proper_nouns']} proper nouns in {p.word_count} words")
            if rep > 12:
                auditor.add("REPETITIVE", u, f"{rep}% of five-word sequences repeat")

    return {"site_keywords": site_keywords, "pages": quality, "page_terms": page_terms}

# ---------------------------------------------------------------------------
# Tracking & analytics detection
# ---------------------------------------------------------------------------

TRACKERS = [
    ("Google Analytics 4", ["gtag/js?id=g-", "googletagmanager.com/gtag/js", '"g-', "gtag('config', 'g-"]),
    ("Universal Analytics (retired)", ["google-analytics.com/analytics.js", "ua-", "ga('create'"]),
    ("Google Tag Manager", ["googletagmanager.com/gtm.js", "gtm-"]),
    ("Google Ads conversion", ["googleadservices.com", "gtag('config', 'aw-", "aw-"]),
    ("Meta (Facebook) Pixel", ["connect.facebook.net", "fbq('init'", "fbevents.js"]),
    ("Microsoft Clarity", ["clarity.ms"]),
    ("Hotjar", ["static.hotjar.com", "hjid"]),
    ("Microsoft Bing UET", ["bat.bing.com", "uetq"]),
    ("LinkedIn Insight", ["snap.licdn.com", "_linkedin_partner_id"]),
    ("TikTok Pixel", ["analytics.tiktok.com", "ttq.load"]),
    ("Pinterest Tag", ["pintrk("]),
    ("X (Twitter) Pixel", ["static.ads-twitter.com"]),
    ("Matomo", ["matomo.js", "piwik.js"]),
    ("Plausible", ["plausible.io/js"]),
    ("Fathom", ["cdn.usefathom.com"]),
    ("Simple Analytics", ["scripts.simpleanalyticscdn.com"]),
    ("PostHog", ["posthog.com/static", "posthog.init"]),
    ("Mixpanel", ["cdn.mxpnl.com"]),
    ("Amplitude", ["amplitude.com/libs", "cdn.amplitude.com"]),
    ("Segment", ["segment.com/analytics.js", "analytics.load("]),
    ("Heap", ["cdn.heapanalytics.com"]),
    ("FullStory", ["fullstory.com/s/fs.js"]),
    ("Crazy Egg", ["script.crazyegg.com"]),
    ("Yandex Metrica", ["mc.yandex.ru/metrika"]),
    ("Cloudflare Web Analytics", ["static.cloudflareinsights.com"]),
    ("Vercel Analytics", ["/_vercel/insights"]),
]

# What a site should normally have, and why.
TRACKING_ADVICE = [
    ("Google Analytics 4", "Non-negotiable. It's free and it's the only way to see which pages "
                           "earn conversions rather than just traffic."),
    ("Google Tag Manager", "Lets you add and change tags without a developer. Worth installing "
                           "before you need your third or fourth tag."),
    ("Microsoft Clarity", "Free heatmaps and session recordings. Shows you where people stop "
                          "reading, which no rank tracker will tell you."),
    ("Meta (Facebook) Pixel", "Only if you run or plan to run Meta ads — it needs to be "
                              "collecting data before the campaign starts, not after."),
    ("Microsoft Bing UET", "Only if you run Microsoft Ads. Bing traffic converts well in B2B."),
]


def detect_tracking(low_html: str) -> list:
    found = []
    for name, sigs in TRACKERS:
        if any(s in low_html for s in sigs):
            found.append(name)
    # GA4 loaded via GTM shouldn't double-report the retired UA library.
    if "Google Analytics 4" in found and "Universal Analytics (retired)" in found:
        if "google-analytics.com/analytics.js" not in low_html:
            found.remove("Universal Analytics (retired)")
    return found


def analyse_tracking(crawler):
    pages = [p for p in crawler.pages.values()
             if p.status == 200 and "html" in p.content_type.lower()]
    if not pages:
        return {}
    counts = Counter()
    for p in pages:
        for t in p.analytics_tools:
            counts[t] += 1
    total = len(pages)
    verification = Counter()
    for p in pages:
        for v in p.verification:
            verification[v] += 1
    untagged = [p.final_url or p.url for p in pages if not p.analytics_tools]
    partial = [(t, n) for t, n in counts.items() if 0 < n < total * 0.9]
    missing = [(name, why) for name, why in TRACKING_ADVICE if name not in counts]
    return {"found": counts.most_common(), "total_pages": total, "untagged": untagged,
            "partial": partial, "missing": missing, "verification": verification.most_common()}


# ---------------------------------------------------------------------------
# Internal link & anchor text profile
# ---------------------------------------------------------------------------

ANCHOR_TYPES = ["Branded", "Exact match", "Partial match", "Generic", "Naked URL",
                "Image / empty", "Long-tail", "Other"]


def classify_anchor(anchor: str, target: str, brand_tokens: set, keyword_terms: set) -> str:
    a = (anchor or "").strip().lower().strip(" .:!?→>»-")
    if not a:
        return "Image / empty"
    if a.startswith(("http://", "https://", "www.")) or a.rstrip("/") == target.rstrip("/").lower():
        return "Naked URL"
    if a in GENERIC_ANCHORS:
        return "Generic"
    tokens = set(re.findall(r"[a-z0-9]{3,}", a))
    if tokens & brand_tokens:
        return "Branded"
    if a in keyword_terms:
        return "Exact match"
    if len(a.split()) > 6:
        return "Long-tail"
    if any(t in keyword_terms for t in tokens) or any(
            k in a for k in list(keyword_terms)[:40] if " " in k):
        return "Partial match"
    return "Other"


def analyse_links(crawler, cfg, content=None):
    """Anchor text classification, contextual vs navigation links, and the ratios."""
    pages = [p for p in crawler.pages.values()
             if p.status == 200 and "html" in p.content_type.lower()]
    if not pages:
        return {}
    total_pages = len(pages)

    # Branded anchors are judged against the audited site's own name, taken from its
    # domain — not the agency name on the report cover.
    brand_source = registrable(cfg.root_host).split(".")[0]
    brand_tokens = set(re.findall(r"[a-z0-9]{3,}", brand_source.lower()))
    brand_tokens |= {w for w in re.findall(r"[a-z0-9]{3,}", brand_source.lower())}
    keyword_terms = {t for t, _, _ in (content or {}).get("site_keywords", [])}

    # A target linked from nearly every page is site furniture, not a contextual link.
    target_sources = defaultdict(set)
    for p in pages:
        for target, _, _, _ in p.internal_links:
            target_sources[target].add(p.final_url or p.url)
    boilerplate = {t for t, srcs in target_sources.items()
                   if len(srcs) >= max(3, total_pages * 0.7)}

    anchors = defaultdict(lambda: {"count": 0, "type": "", "targets": Counter(),
                                   "sources": set(), "contextual": 0})
    type_counts = Counter()
    per_page = {}
    total_internal = total_contextual = total_nofollow = total_external = 0

    for p in pages:
        u = p.final_url or p.url
        ctx = nav = 0
        for target, anchor, nofollow, in_chrome in p.internal_links:
            is_ctx = not in_chrome and target not in boilerplate
            ctx += is_ctx
            nav += (not is_ctx)
            total_internal += 1
            total_contextual += is_ctx
            total_nofollow += nofollow
            key = (anchor or "").strip()[:120]
            rec = anchors[key]
            rec["count"] += 1
            rec["targets"][target] += 1
            rec["sources"].add(u)
            rec["contextual"] += is_ctx
            if not rec["type"]:
                rec["type"] = classify_anchor(key, target, brand_tokens, keyword_terms)
        total_external += len(p.external_links)
        per_page[u] = {"out_total": len(p.internal_links), "out_contextual": ctx,
                       "out_nav": nav, "external": len(p.external_links),
                       "inlinks": len(target_sources.get(u, set())),
                       "inlinks_contextual": sum(
                           1 for s in target_sources.get(u, set())
                           if u not in boilerplate)}

    for key, rec in anchors.items():
        type_counts[rec["type"]] += rec["count"]

    inlink_counts = [v["inlinks"] for v in per_page.values()]
    ratios = {
        "internal_links": total_internal,
        "contextual": total_contextual,
        "navigational": total_internal - total_contextual,
        "contextual_share": round(total_contextual / max(total_internal, 1) * 100),
        "external_links": total_external,
        "internal_external_ratio": (f"{total_internal / max(total_external, 1):.1f} : 1"
                                    if total_external else "no outbound links"),
        "nofollow_internal": total_nofollow,
        "avg_out_per_page": round(total_internal / max(total_pages, 1), 1),
        "avg_in_per_page": round(statistics.mean(inlink_counts), 1) if inlink_counts else 0,
        "median_in_per_page": round(statistics.median(inlink_counts), 1) if inlink_counts else 0,
        "unique_targets": len(target_sources),
        "boilerplate_targets": len(boilerplate),
        "pages_without_contextual": sum(1 for v in per_page.values() if v["out_contextual"] == 0),
        "pages_under_3_inlinks": sum(1 for v in per_page.values() if v["inlinks"] < 3),
    }

    top_anchors = sorted(anchors.items(), key=lambda kv: -kv[1]["count"])
    return {"anchors": top_anchors, "types": type_counts, "ratios": ratios,
            "per_page": per_page, "boilerplate": boilerplate,
            "target_sources": target_sources, "brand": brand_source}


# ---------------------------------------------------------------------------
# Keyword cannibalisation from the crawl itself
# ---------------------------------------------------------------------------

def analyse_cannibalisation(crawler, content, auditor=None):
    """Pages competing for the same topic, detected without Search Console data."""
    if not content:
        return []
    pages = {p.final_url or p.url: p for p in crawler.pages.values()
             if p.status == 200 and p.indexable and "html" in p.content_type.lower()}
    page_terms = content.get("page_terms", {})

    groups = defaultdict(list)
    for u, terms in page_terms.items():
        if u in pages and terms:
            groups[terms[0][0]].append(u)

    # Titles that target the same phrase are the other half of the picture.
    title_groups = defaultdict(list)
    for u, p in pages.items():
        if p.title:
            key = " ".join(sorted(w for w in re.findall(r"[a-z]{4,}", p.title.lower())
                                  if w not in STOPWORDS))[:80]
            if key:
                title_groups[key].append(u)

    clashes = []
    seen = set()
    for term, urls in groups.items():
        if len(urls) > 1:
            clashes.append({"term": term, "urls": sorted(urls), "basis": "same dominant topic"})
            seen.add(frozenset(urls))
    for key, urls in title_groups.items():
        if len(urls) > 1 and frozenset(urls) not in seen:
            titles = pages[urls[0]].title
            clashes.append({"term": titles[:60], "urls": sorted(urls),
                            "basis": "near-identical title targeting"})

    clashes.sort(key=lambda c: -len(c["urls"]))
    if auditor:
        for c in clashes[:25]:
            auditor.add("CANNIBALISATION", c["urls"][0],
                        f"“{c['term']}” — {len(c['urls'])} pages compete ({c['basis']}): "
                        + ", ".join(c["urls"][:3]))
    return clashes


# ---------------------------------------------------------------------------
# Off-page signals visible from the site itself
# ---------------------------------------------------------------------------

SOCIAL_HOSTS = {
    "facebook.com": "Facebook", "instagram.com": "Instagram", "twitter.com": "X / Twitter",
    "x.com": "X / Twitter", "linkedin.com": "LinkedIn", "youtube.com": "YouTube",
    "tiktok.com": "TikTok", "pinterest.com": "Pinterest", "yelp.com": "Yelp",
    "trustpilot.com": "Trustpilot", "g.page": "Google Business Profile",
    "goo.gl/maps": "Google Business Profile", "maps.google": "Google Business Profile",
    "github.com": "GitHub", "medium.com": "Medium", "reddit.com": "Reddit",
    "crunchbase.com": "Crunchbase", "wikipedia.org": "Wikipedia",
}


def analyse_offpage_onsite(crawler, cfg):
    """What the crawl can legitimately say about off-page presence."""
    pages = [p for p in crawler.pages.values()
             if p.status == 200 and "html" in p.content_type.lower()]
    socials, outbound_domains, nofollow_out = {}, Counter(), 0
    for p in pages:
        for url, anchor, nofollow, _ in p.external_links:
            host = registrable(up.urlsplit(url).netloc)
            outbound_domains[host] += 1
            nofollow_out += nofollow
            for key, name in SOCIAL_HOSTS.items():
                if key in host or key in url:
                    socials.setdefault(name, url)

    home = crawler.pages.get(normalise(cfg.start_url))
    same_as, org_schema = [], []
    if home:
        org_schema = [t for t in home.schema_types
                      if t in ("Organization", "LocalBusiness", "Corporation", "OnlineStore",
                               "Store", "Restaurant", "ProfessionalService", "NGO")]
    total_out = sum(outbound_domains.values())
    return {
        "socials": socials,
        "missing_socials": [n for n in ("Facebook", "Instagram", "LinkedIn", "X / Twitter",
                                        "YouTube", "Google Business Profile")
                            if n not in socials],
        "outbound_domains": outbound_domains.most_common(15),
        "outbound_total": total_out,
        "outbound_unique": len(outbound_domains),
        "nofollow_out": nofollow_out,
        "org_schema": org_schema,
        "verification": sorted({v for p in pages for v in p.verification}),
    }

# ---------------------------------------------------------------------------
# Page speed measured from the crawl itself
# ---------------------------------------------------------------------------

MODERN_FORMATS = {"webp", "avif"}
LEGACY_FORMATS = {"jpg", "jpeg", "png", "gif", "bmp", "tiff"}


def asset_ext(url: str) -> str:
    path = up.urlsplit(url).path.lower()
    ext = os.path.splitext(path)[1].lstrip(".")
    return ext.split("?")[0][:5]


def probe_assets(urls, cfg, limit=220):
    """HEAD each asset for its real transfer size and content type."""
    urls = list(dict.fromkeys(urls))[:limit]
    out = {}

    def one(u):
        try:
            r = http_get(u, "HEAD", min(cfg.timeout, 15), cfg.user_agent)
            if r.status_code in (403, 405, 501) or "content-length" not in r.headers:
                r = http_get(u, "GET", min(cfg.timeout, 15), cfg.user_agent, max_bytes=3_000_000)
                size = len(r.content)
            else:
                try:
                    size = int(r.headers.get("content-length") or 0)
                except ValueError:
                    size = 0
            return u, {"status": r.status_code, "bytes": size,
                       "type": (r.headers.get("content-type") or "").split(";")[0].strip(),
                       "encoding": r.headers.get("content-encoding", ""),
                       "cache": r.headers.get("cache-control", "")}
        except Exception:
            return u, {"status": 0, "bytes": 0, "type": "", "encoding": "", "cache": ""}

    with cf.ThreadPoolExecutor(max_workers=cfg.threads) as ex:
        for u, d in ex.map(one, urls):
            out[u] = d
    return out


def analyse_speed(crawler, cfg, auditor=None, sample=5):
    """Real page weight and blocking-resource counts, no API needed."""
    pages = [p for p in crawler.pages.values()
             if p.status == 200 and "html" in p.content_type.lower()]
    if not pages:
        return {}

    ttfbs = sorted(p.ttfb_ms for p in pages if p.ttfb_ms)
    targets = sorted(pages, key=lambda p: (p.depth, -p.inlinks))[:sample]
    wanted = []
    for p in targets:
        wanted += [u for u, _ in p.stylesheets]
        wanted += [u for u, _, _, _ in p.scripts]
        wanted += [i["url"] for i in p.image_details if i.get("url")]
    assets = probe_assets(wanted, cfg)

    per_page = {}
    for p in targets:
        u = p.final_url or p.url
        groups = {"HTML": p.size_bytes, "CSS": 0, "JavaScript": 0, "Images": 0}
        for a, _ in p.stylesheets:
            groups["CSS"] += assets.get(a, {}).get("bytes", 0)
        for a, _, _, _ in p.scripts:
            groups["JavaScript"] += assets.get(a, {}).get("bytes", 0)
        for i in p.image_details:
            groups["Images"] += assets.get(i.get("url", ""), {}).get("bytes", 0)
        total = sum(groups.values())
        per_page[u] = {"groups": groups, "total": total, "ttfb": p.ttfb_ms,
                       "blocking": p.render_blocking, "requests":
                           1 + len(p.stylesheets) + len(p.scripts) + len(p.image_details)}
        if auditor:
            if total > 3_000_000:
                auditor.add("HEAVY_PAGE", u, f"{total/1_048_576:.1f} MB total page weight")
            if p.render_blocking > 5:
                auditor.add("RENDER_BLOCKING", u,
                            f"{p.render_blocking} blocking stylesheets/scripts")

    weights = [v["total"] for v in per_page.values() if v["total"]]
    uncompressed = [u for u, d in assets.items()
                    if d.get("type", "").startswith(("text/", "application/javascript",
                                                     "application/json"))
                    and not d.get("encoding") and d.get("bytes", 0) > 10240]
    nocache = [u for u, d in assets.items()
               if d.get("bytes", 0) > 10240 and "max-age" not in (d.get("cache") or "")]
    return {
        "ttfb": {"median": int(statistics.median(ttfbs)) if ttfbs else 0,
                 "p90": int(ttfbs[int(len(ttfbs) * 0.9)]) if ttfbs else 0,
                 "slowest": [(p.final_url or p.url, p.ttfb_ms)
                             for p in sorted(pages, key=lambda x: -x.ttfb_ms)[:10]]},
        "per_page": per_page,
        "median_weight": int(statistics.median(weights)) if weights else 0,
        "assets": assets,
        "largest": sorted(((u, d["bytes"], d["type"]) for u, d in assets.items() if d["bytes"]),
                          key=lambda x: -x[1])[:15],
        "uncompressed": uncompressed[:20],
        "nocache": nocache[:20],
        "sampled": [p.final_url or p.url for p in targets],
    }


# ---------------------------------------------------------------------------
# Image format audit
# ---------------------------------------------------------------------------

def analyse_images(crawler, speed, auditor=None):
    pages = [p for p in crawler.pages.values()
             if p.status == 200 and "html" in p.content_type.lower()]
    assets = (speed or {}).get("assets", {})
    formats = Counter()
    total_bytes = Counter()
    seen = {}
    no_lazy = []
    no_srcset = 0
    total_imgs = 0
    modern_pages = sum(1 for p in pages if p.picture_types)

    for p in pages:
        for i, img in enumerate(p.image_details):
            u = img.get("url", "")
            if not u:
                continue
            total_imgs += 1
            ext = asset_ext(u) or "unknown"
            ctype = assets.get(u, {}).get("type", "")
            if ctype.startswith("image/"):
                ext = ctype.split("/")[1].replace("jpeg", "jpg").split("+")[0]
            formats[ext] += 1
            size = assets.get(u, {}).get("bytes", 0)
            total_bytes[ext] += size
            if u not in seen:
                seen[u] = {"ext": ext, "bytes": size, "pages": set(), "srcset": img["srcset"],
                           "loading": img["loading"]}
            seen[u]["pages"].add(p.final_url or p.url)
            # Images beyond the first two are almost certainly below the fold.
            if i >= 2 and img["loading"] != "lazy" and not img.get("from_picture"):
                no_lazy.append(u)
            if not img["srcset"]:
                no_srcset += 1

    legacy = {u: d for u, d in seen.items() if d["ext"] in LEGACY_FORMATS}
    modern = sum(n for e, n in formats.items() if e in MODERN_FORMATS)
    oversized = sorted(((u, d) for u, d in seen.items() if d["bytes"] > 200_000),
                       key=lambda x: -x[1]["bytes"])

    if auditor:
        if legacy:
            biggest = sorted(legacy.items(), key=lambda x: -x[1]["bytes"])[:3]
            for u, d in list(legacy.items())[:80]:
                auditor.add("IMG_LEGACY_FORMAT", sorted(d["pages"])[0],
                            f"{u} is {d['ext'].upper()}"
                            + (f" · {d['bytes']//1024} KB" if d["bytes"] else ""))
        for u, d in oversized[:40]:
            auditor.add("IMG_OVERSIZED", sorted(d["pages"])[0],
                        f"{u} weighs {d['bytes']//1024} KB")
        for u in list(dict.fromkeys(no_lazy))[:60]:
            auditor.add("IMG_NO_LAZY", sorted(seen[u]["pages"])[0],
                        f"{u} loads eagerly below the fold")

    return {
        "formats": formats.most_common(),
        "bytes_by_format": total_bytes,
        "total": total_imgs,
        "unique": len(seen),
        "modern": modern,
        "modern_share": round(modern / max(total_imgs, 1) * 100),
        "legacy": sorted(legacy.items(), key=lambda x: -x[1]["bytes"])[:60],
        "legacy_count": len(legacy),
        "oversized": oversized[:30],
        "no_lazy": len(set(no_lazy)),
        "no_srcset": no_srcset,
        "picture_pages": modern_pages,
        "potential_saving": int(sum(d["bytes"] for d in legacy.values()) * 0.30),
    }


# ---------------------------------------------------------------------------
# Search Console connection check
# ---------------------------------------------------------------------------

def dns_txt(domain: str, timeout: int = 10):
    """TXT records over DNS-over-HTTPS. Returns (records, lookup_succeeded)."""
    out = []
    ok = False
    for endpoint in ("https://dns.google/resolve?name={}&type=TXT",
                     "https://cloudflare-dns.com/dns-query?name={}&type=TXT"):
        try:
            req = urllib.request.Request(
                endpoint.format(up.quote(domain)),
                headers={"Accept": "application/dns-json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            ok = True
            for ans in data.get("Answer", []):
                out.append(str(ans.get("data", "")).strip('"'))
            if out:
                break
        except Exception:
            continue
    return out, ok


def check_search_console(crawler, cfg, auditor=None):
    """Verification can be a meta tag, a DNS record or an HTML file. Check what we can."""
    host = cfg.root_host
    root = registrable(host)
    meta_tags = sorted({v for p in crawler.pages.values() for v in p.verification})
    txt, dns_ok = dns_txt(root)
    dns_google = [t for t in txt if "google-site-verification" in t.lower()]
    dns_bing = [t for t in txt if "msvalidate" in t.lower() or "bing" in t.lower()]

    # The HTML-file method leaves a googleXXXX.html at the root, but the token is
    # unguessable, so absence here proves nothing.
    verified_meta = any("google" in m.lower() for m in meta_tags)
    connected = bool(verified_meta or dns_google)

    sitemap_declared = any("sitemap" in l.lower() for l in crawler.robots_txt.splitlines())
    gsc_data_supplied = bool(getattr(cfg, "gsc_csv", ""))

    # Only claim it's missing when the DNS lookup actually worked. A failed lookup
    # proves nothing, and a false "not connected" would send someone re-verifying
    # a property that was fine all along.
    if auditor and not connected and dns_ok and not gsc_data_supplied:
        auditor.add("NO_SEARCH_CONSOLE", cfg.start_url,
                    "no Google verification meta tag and no google-site-verification DNS record")
    if auditor and not sitemap_declared and crawler.robots_status == 200:
        auditor.add("SITEMAP_NOT_DECLARED", up.urljoin(cfg.start_url, "/robots.txt"),
                    "robots.txt has no Sitemap: line")

    return {"connected": connected, "dns_ok": dns_ok,
            "meta_tags": meta_tags, "dns_google": dns_google,
            "dns_bing": dns_bing, "txt_records": txt[:12],
            "sitemap_declared": sitemap_declared, "gsc_data": gsc_data_supplied,
            "domain": root}


# ---------------------------------------------------------------------------
# Authority: Moz DA/PA if you have a key, internal PageRank either way
# ---------------------------------------------------------------------------

def fetch_moz(targets, token="", access_id="", secret="", timeout=30):
    """Moz Links API v3. DA and PA are Moz metrics — only Moz can supply them."""
    if not (token or (access_id and secret)):
        return {}
    import base64
    body = json.dumps({"targets": list(targets)[:50]}).encode()
    req = urllib.request.Request("https://lsapi.seomoz.com/v2/url_metrics", data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    if token:
        req.add_header("x-moz-token", token)
    else:
        cred = base64.b64encode(f"{access_id}:{secret}".encode()).decode()
        req.add_header("Authorization", "Basic " + cred)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        out = {}
        for row in data.get("results", []):
            out[row.get("page", "")] = {
                "da": row.get("domain_authority"), "pa": row.get("page_authority"),
                "spam": row.get("spam_score"),
                "linking_domains": row.get("root_domains_to_page"),
                "backlinks": row.get("external_pages_to_page"),
            }
        return out
    except urllib.error.HTTPError as e:
        return {"__error__": f"Moz API returned HTTP {e.code}. Check the key and your quota."}
    except Exception as e:
        return {"__error__": f"Could not reach the Moz API ({type(e).__name__})."}


def internal_authority(crawler, damping=0.85, rounds=25):
    """PageRank across the crawled site: which of your own pages hold the most link equity."""
    pages = [p.final_url or p.url for p in crawler.pages.values()
             if p.status == 200 and "html" in p.content_type.lower()]
    idx = {u: i for i, u in enumerate(pages)}
    if not idx:
        return {}
    n = len(idx)
    outlinks = defaultdict(list)
    for p in crawler.pages.values():
        u = p.final_url or p.url
        if u not in idx:
            continue
        for target, _, nofollow, _ in p.internal_links:
            if not nofollow and target in idx and target != u:
                outlinks[u].append(target)

    rank = {u: 1.0 / n for u in idx}
    for _ in range(rounds):
        nxt = {u: (1 - damping) / n for u in idx}
        sink = 0.0
        for u, r in rank.items():
            outs = outlinks.get(u)
            if not outs:
                sink += r
                continue
            share = damping * r / len(outs)
            for t in outs:
                nxt[t] += share
        if sink:
            spread = damping * sink / n
            for u in nxt:
                nxt[u] += spread
        rank = nxt

    top = max(rank.values()) or 1
    return {u: round(r / top * 100, 1) for u, r in rank.items()}

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

CAT_WEIGHT = {"Indexability": 1.3, "Crawl & Status": 1.2, "On-Page": 1.2,
              "Content": 1.0, "Internal Links": 0.8, "Performance": 1.0,
              "Structured Data": 0.6, "Off-Page": 1.0}


def score(issues, total_pages):
    by_code = defaultdict(set)
    for i in issues:
        by_code[i.code].add(i.url)
    penalties = defaultdict(float)
    worst = {}
    for code, urls in by_code.items():
        d = ISSUE_DEFS.get(code)
        if not d or d["sev"] == "opportunity":
            continue
        share = min(len(urls) / max(total_pages, 1), 1.0)
        # Severity sets the floor, prevalence scales it: one critical URL still costs
        # 5 points, a critical affecting every page costs 20.
        penalties[d["cat"]] += SEV_WEIGHT[d["sev"]] * (0.5 + 1.5 * share)
        rank = SEVERITIES.index(d["sev"])
        worst[d["cat"]] = min(worst.get(d["cat"], 9), rank)

    # A single unresolved critical should never leave a category looking healthy,
    # however small a share of the site it touches.
    CAP = {0: 50, 1: 75, 2: 90}

    cats = {}
    for cat in CATEGORIES:
        if cat == "Off-Page" and not any(ISSUE_DEFS[c]["cat"] == "Off-Page"
                                         for c in by_code if c in ISSUE_DEFS):
            continue
        s = max(0, round(100 - penalties.get(cat, 0)))
        cats[cat] = min(s, CAP.get(worst.get(cat, 9), 100))
    if not cats:
        return 100, {}
    num = sum(v * CAT_WEIGHT.get(k, 1) for k, v in cats.items())
    den = sum(CAT_WEIGHT.get(k, 1) for k in cats)
    overall = round(num / den)
    site_worst = min(worst.values()) if worst else 9
    return min(overall, CAP.get(site_worst, 100) + 15), cats


def grade(s):
    return ("A", "Strong") if s >= 85 else ("B", "Solid, with gaps") if s >= 70 else \
           ("C", "Needs work") if s >= 55 else ("D", "Serious problems") if s >= 40 else ("F", "Critical")


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

CSS = """
:root{
  --ink:#10222B; --ink-2:#3C5561; --ink-3:#6E858F;
  --paper:#EEF1F2; --panel:#FFFFFF; --rule:#D2DADE; --rule-2:#E7ECEE;
  --accent:#0E6E8C;
  --critical:#A61B3D; --high:#C25A00; --medium:#8A6A00; --low:#4E6E7E; --opportunity:#1F7A5C;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
     font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1140px;margin:0 auto;padding:0 24px 96px}
a{color:var(--accent)}
.label{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;
       color:var(--ink-3);font-weight:600}
.mono{font-family:var(--mono)}

/* masthead */
header.top{border-bottom:2px solid var(--ink);margin-bottom:34px;padding:34px 0 18px}
header.top .kicker{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}
h1{font-family:var(--mono);font-size:clamp(24px,4vw,38px);font-weight:600;letter-spacing:-.02em;
   margin:10px 0 6px;word-break:break-all}
header.top .sub{color:var(--ink-2);font-size:14px}

/* scorecard */
.score-grid{display:grid;grid-template-columns:260px 1fr;gap:26px;margin-bottom:34px}
@media(max-width:820px){.score-grid{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--rule);padding:22px}
.bigscore{display:flex;flex-direction:column;justify-content:center;align-items:flex-start}
.bigscore .num{font-family:var(--mono);font-size:72px;line-height:.9;font-weight:600;letter-spacing:-.04em}
.bigscore .grade{font-family:var(--mono);font-size:13px;letter-spacing:.1em;margin-top:12px;color:var(--ink-2)}
.meters{display:grid;grid-template-columns:1fr 1fr;gap:16px 30px}
@media(max-width:560px){.meters{grid-template-columns:1fr}}
.meter .row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}
.meter .val{font-family:var(--mono);font-size:14px;font-weight:600}
.track{height:6px;background:var(--rule-2);position:relative}
.fill{height:6px;background:var(--ink)}
.fill.warn{background:var(--medium)} .fill.bad{background:var(--critical)}

/* signature: issue mass bar */
.mass{display:flex;height:56px;width:100%;border:1px solid var(--rule);background:var(--panel)}
.mass .seg{position:relative;overflow:hidden;border-right:1px solid rgba(255,255,255,.55)}
.mass .seg:last-child{border-right:0}
.mass .seg span{position:absolute;left:6px;bottom:5px;font-family:var(--mono);font-size:9.5px;
  color:#fff;letter-spacing:.04em;white-space:nowrap;opacity:.95}
.masskey{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px}
.masskey i{display:inline-block;width:9px;height:9px;margin-right:6px}

/* stats strip */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1px;background:var(--rule);
  border:1px solid var(--rule);margin:34px 0}
.stat{background:var(--panel);padding:14px 16px}
.stat .v{font-family:var(--mono);font-size:22px;font-weight:600;letter-spacing:-.02em}
.stat .k{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);margin-top:3px}

h2{font-family:var(--mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase;font-weight:600;
   border-bottom:1px solid var(--ink);padding-bottom:8px;margin:52px 0 20px}
h2 .n{color:var(--ink-3);margin-right:10px}

/* priority cards */
.fix{background:var(--panel);border:1px solid var(--rule);border-left:4px solid var(--rule);
     padding:18px 20px;margin-bottom:12px}
.fix.critical{border-left-color:var(--critical)} .fix.high{border-left-color:var(--high)}
.fix.medium{border-left-color:var(--medium)} .fix.low{border-left-color:var(--low)}
.fix.opportunity{border-left-color:var(--opportunity)}
.fix .hd{display:flex;justify-content:space-between;gap:14px;align-items:baseline;flex-wrap:wrap}
.fix h3{font-size:16px;margin:0 0 8px;font-weight:600}
.fix .rank{font-family:var(--mono);font-size:11px;color:var(--ink-3);margin-right:8px}
.fix p{margin:0 0 8px;color:var(--ink-2);font-size:14px}
.fix .todo{font-size:14px;border-top:1px dashed var(--rule);padding-top:9px;margin-top:10px}
.fix .todo b{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);
  display:block;margin-bottom:3px;font-weight:600}
.tag{font-family:var(--mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;padding:3px 7px;
     color:#fff;white-space:nowrap}
.tag.critical{background:var(--critical)} .tag.high{background:var(--high)}
.tag.medium{background:var(--medium)} .tag.low{background:var(--low)}
.tag.opportunity{background:var(--opportunity)}
.tag.cat{background:transparent;color:var(--ink-3);border:1px solid var(--rule)}

/* issue list */
details.issue{background:var(--panel);border:1px solid var(--rule);margin-bottom:8px}
details.issue>summary{cursor:pointer;padding:12px 16px;display:flex;align-items:center;gap:12px;
  list-style:none;flex-wrap:wrap}
details.issue>summary::-webkit-details-marker{display:none}
details.issue>summary::before{content:"+";font-family:var(--mono);color:var(--ink-3);width:12px}
details.issue[open]>summary::before{content:"–"}
details.issue .name{flex:1;font-weight:600;font-size:14.5px;min-width:200px}
details.issue .cnt{font-family:var(--mono);font-size:12px;color:var(--ink-2)}
.issue-body{padding:4px 16px 18px 40px;border-top:1px solid var(--rule-2)}
.issue-body .why{color:var(--ink-2);font-size:14px;margin:12px 0 6px}
.issue-body .how{font-size:14px;margin-bottom:14px}
.issue-body .how b,.issue-body .why b{font-family:var(--mono);font-size:10px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink-3);display:block;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:12.5px;font-family:var(--mono)}
th{text-align:left;font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);
   border-bottom:1px solid var(--rule);padding:6px 8px;font-weight:600}
td{padding:5px 8px;border-bottom:1px solid var(--rule-2);vertical-align:top;word-break:break-all}
td.d{color:var(--ink-2);font-family:var(--sans);font-size:12.5px;word-break:normal}
.more{font-family:var(--mono);font-size:11px;color:var(--ink-3);padding-top:8px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.filters button{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;
  background:var(--panel);border:1px solid var(--rule);padding:6px 11px;cursor:pointer;color:var(--ink-2)}
.filters button[aria-pressed=true]{background:var(--ink);color:#fff;border-color:var(--ink)}
.filters button:focus-visible,details>summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.note{font-size:13.5px;color:var(--ink-2);background:var(--panel);border:1px solid var(--rule);
  border-left:4px solid var(--accent);padding:14px 18px;margin:16px 0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:820px){.two{grid-template-columns:1fr}}
pre.robots{font-family:var(--mono);font-size:11.5px;background:var(--panel);border:1px solid var(--rule);
  padding:14px;overflow:auto;max-height:280px;white-space:pre-wrap;word-break:break-all;color:var(--ink-2)}
footer{margin-top:60px;border-top:1px solid var(--rule);padding-top:16px;color:var(--ink-3);font-size:12px}
.ok{color:var(--opportunity)} .bad{color:var(--critical)}
.kws{display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 20px}
.kw{font-family:var(--mono);font-size:12px;background:var(--panel);border:1px solid var(--rule);
padding:6px 10px;white-space:nowrap}
.kw b{font-weight:600} .kw span{color:var(--ink-3);margin-left:7px;font-size:10.5px}
.kw.lead{background:var(--ink);color:#fff;border-color:var(--ink)}
.kw.lead span{color:#9db6c0}
@media print{
  body{background:#fff} .filters{display:none} details.issue{break-inside:avoid}
  details.issue>summary::before{content:""}
}
@media(prefers-reduced-motion:no-preference){
  .fill{transition:width .6s ease}
}
"""

JS = """
(function(){
  var btns=document.querySelectorAll('.filters button');
  btns.forEach(function(b){
    b.addEventListener('click',function(){
      var sev=b.dataset.sev;
      btns.forEach(function(x){x.setAttribute('aria-pressed', x===b);});
      document.querySelectorAll('details.issue').forEach(function(d){
        d.style.display=(sev==='all'||d.dataset.sev===sev)?'':'none';
      });
    });
  });
})();
"""


def esc(s):
    return html_mod.escape(str(s), quote=True)


def _darken(hex_colour: str, factor: float = 0.34) -> str:
    """A deep tone derived from the brand colour, for panels behind a light logo."""
    h = (hex_colour or "").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return "#0E2C42"
    return "#%02X%02X%02X" % (max(int(r * factor), 8), max(int(g * factor), 20),
                              max(int(b * factor), 32))


def brand_assets(cfg):
    """Logo as a data URI plus a palette override, so the report stays one portable file."""
    data_uri = ""
    path = getattr(cfg, "brand_logo", "") or ""
    if path and os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}.get(ext)
        if mime:
            try:
                import base64
                with open(path, "rb") as f:
                    data_uri = f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")
            except Exception:
                data_uri = ""
    if not data_uri:
        data_uri = DEFAULT_LOGO_DATA_URI

    light_logo = bool(getattr(cfg, "brand_logo_light", True))
    logo_html = ""
    if data_uri:
        logo_html = (f'<div class="logoplate{"" if light_logo else " plain"}">'
                     f'<img class="logo" src="{data_uri}" alt=""></div>')

    primary = (getattr(cfg, "brand_primary", "") or "").strip() or DEFAULT_BRAND["brand_primary"]
    secondary = (getattr(cfg, "brand_secondary", "") or "").strip() or DEFAULT_BRAND["brand_secondary"]
    plate = _darken(primary)
    css = (":root{--accent:" + primary + ";--brand:" + primary +
           ";--brand-2:" + secondary + ";--brand-plate:" + plate + "}"
           "header.top{border-bottom-color:var(--brand)}"
           "h2{border-bottom-color:var(--brand)}"
           "h2 .n{color:var(--brand)}"
           ".kw.lead{background:var(--brand);border-color:var(--brand)}"
           ".bigscore .num{color:var(--brand)}"
           ".brandbar{height:6px;background:linear-gradient(90deg,var(--brand) 0%,"
           "var(--brand-2) 100%)}"
           # A white wordmark needs a dark panel behind it or it vanishes on paper.
           ".logoplate{display:inline-block;background:var(--brand-plate);"
           "padding:15px 20px;margin-bottom:16px;line-height:0}"
           ".logoplate.plain{background:none;padding:0}"
           ".logo{max-height:44px;max-width:230px;display:block}"
           ".masthead{display:flex;justify-content:space-between;align-items:flex-start;"
           "gap:20px;flex-wrap:wrap}"
           ".byline{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;"
           "text-transform:uppercase;color:var(--ink-3);text-align:right}"
           ".byline b{display:block;font-size:14px;letter-spacing:.02em;text-transform:none;"
           "color:var(--brand);margin-top:3px}"
           "footer b{color:var(--brand)}"
           "@media print{.logoplate{-webkit-print-color-adjust:exact;print-color-adjust:exact}"
           ".brandbar{-webkit-print-color-adjust:exact;print-color-adjust:exact}}")
    return logo_html, css


def build_report(cfg, crawler: Crawler, auditor: Auditor, psi, gsc, backlinks,
                 overall, cats, content=None, extras=None):
    pages = crawler.pages
    html_pages = [p for p in pages.values() if p.status == 200 and "html" in p.content_type.lower()]
    indexable = [p for p in html_pages if p.indexable]
    by_code = defaultdict(list)
    for i in auditor.issues:
        by_code[i.code].append(i)

    def sev_of(code):
        return ISSUE_DEFS.get(code, {}).get("sev", "low")

    ranked = sorted(by_code.items(),
                    key=lambda kv: -(SEV_WEIGHT[sev_of(kv[0])] * (1 + len({i.url for i in kv[1]}) ** 0.5)))
    g, gtext = grade(overall)
    host = up.urlsplit(cfg.start_url).netloc
    extras = extras or {}
    links_data = extras.get("links") or {}
    tracking = extras.get("tracking") or {}
    cannibal = extras.get("cannibal") or []
    offpage = extras.get("offpage") or {}

    _sec = [0]

    def H(title):
        _sec[0] += 1
        return f'<h2><span class="n">{_sec[0]:02d}</span>{title}</h2>' 
    out = []
    A = out.append

    logo_html, brand_css = brand_assets(cfg)
    brand_name = getattr(cfg, "brand_name", "") or ""
    A(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEO audit — {esc(host)}{" · " + esc(brand_name) if brand_name else ""}</title>
<style>{CSS}</style><style>{brand_css}</style></head><body>
<div class="brandbar"></div><div class="wrap">
<header class="top">
  <div class="masthead">
    <div>{logo_html}
      <span class="label">Technical SEO audit</span>
      <h1>{esc(host)}</h1>
    </div>
    <div class="byline">{esc(datetime.now(timezone.utc).strftime('%d %b %Y'))}
      {"<b>" + esc(brand_name) + "</b>" if brand_name else ""}</div>
  </div>
  <div class="sub">{len(pages)} URLs crawled · {len(indexable)} indexable HTML pages ·
  {len(auditor.issues)} findings across {len(by_code)} issue types · crawl depth {cfg.max_depth}</div>
</header>""")

    # scorecard
    A('<div class="score-grid"><div class="panel bigscore">'
      f'<div class="label">Overall health</div><div class="num">{overall}</div>'
      f'<div class="grade">GRADE {g} — {esc(gtext.upper())}</div></div>'
      '<div class="panel"><div class="label" style="margin-bottom:16px">Category scores</div><div class="meters">')
    for cat, s in cats.items():
        cls = "" if s >= 70 else "warn" if s >= 45 else "bad"
        A(f'<div class="meter"><div class="row"><span class="label">{esc(cat)}</span>'
          f'<span class="val">{s}</span></div><div class="track">'
          f'<div class="fill {cls}" style="width:{s}%"></div></div></div>')
    A('</div></div></div>')

    # signature: issue mass
    mass = [(code, len({i.url for i in items}), sev_of(code)) for code, items in by_code.items()]
    mass = [m for m in mass if m[2] != "opportunity"]
    total_mass = sum(m[1] for m in mass) or 1
    if mass:
        A(H("Where the problems are"))
        A('<p style="margin:-6px 0 14px;color:var(--ink-2);font-size:14px">Each block is one issue type, '
          'sized by how many URLs it affects and coloured by severity. Wide red blocks are where the site is losing the most.</p>')
        A('<div class="mass">')
        for code, n, sev in sorted(mass, key=lambda m: (-SEV_WEIGHT[m[2]], -m[1])):
            w = max(n / total_mass * 100, 0.4)
            lbl = ISSUE_DEFS[code]["title"] if w > 9 else ""
            A(f'<div class="seg" style="width:{w:.2f}%;background:var(--{sev})" '
              f'title="{esc(ISSUE_DEFS[code]["title"])} — {n} URLs"><span>{esc(lbl)}</span></div>')
        A('</div><div class="masskey label">')
        for sev in SEVERITIES[:-1]:
            n = sum(m[1] for m in mass if m[2] == sev)
            A(f'<span><i style="background:var(--{sev})"></i>{sev} · {n} URLs</span>')
        A('</div>')

    # stats
    codes = Counter(p.status for p in pages.values())
    ttfbs = sorted(p.ttfb_ms for p in html_pages if p.ttfb_ms)
    words = [p.word_count for p in indexable] or [0]
    A('<div class="stats">')
    stats = [
        (len(pages), "URLs crawled"),
        (len(indexable), "Indexable"),
        (sum(v for k, v in codes.items() if 300 <= k < 400) + sum(1 for p in pages.values() if p.redirect_chain), "Redirects"),
        (sum(v for k, v in codes.items() if 400 <= k < 500), "4xx errors"),
        (sum(v for k, v in codes.items() if k >= 500 or k <= 0), "5xx / failed"),
        (f"{statistics.median(ttfbs):.0f}ms" if ttfbs else "—", "Median TTFB"),
        (f"{statistics.median(words):.0f}" if words else "—", "Median words"),
        (f"{statistics.mean([p.depth for p in html_pages]):.1f}" if html_pages else "—", "Avg click depth"),
    ]
    for v, k in stats:
        A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
    A('</div>')

    # priority fixes
    A(H("Fix these first"))
    prio = [kv for kv in ranked if sev_of(kv[0]) in ("critical", "high", "medium")][:8]
    if not prio:
        A('<div class="note">No critical, high or medium-severity issues were found. '
          'Work the remaining low-severity items below when convenient.</div>')
    for rank, (code, items) in enumerate(prio, 1):
        d = ISSUE_DEFS[code]
        urls = {i.url for i in items}
        A(f'<div class="fix {d["sev"]}"><div class="hd"><h3><span class="rank">{rank:02d}</span>{esc(d["title"])}</h3>'
          f'<div><span class="tag {d["sev"]}">{d["sev"]}</span> <span class="tag cat">{esc(d["cat"])}</span></div></div>'
          f'<p><b class="mono" style="font-size:12px">{len(urls)} URL{"s" if len(urls)!=1 else ""} affected.</b> {esc(d["why"])}</p>'
          f'<div class="todo"><b>What to do</b>{esc(d["fix"])}</div>'
          '<div class="todo"><b>Affected URLs</b><table><tbody>' +
          "".join(f'<tr><td><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></td>'
                  f'<td class="d">{esc(det)}</td></tr>'
                  for u, det in sorted({(i.url, i.detail) for i in items})[:8]) +
          '</tbody></table>' +
          (f'<div class="more">+ {len(urls)-8} more in the register below</div>'
           if len(urls) > 8 else "") + '</div></div>')

    # full issue register
    A(H("Full issue register"))
    A('<div class="filters"><button data-sev="all" aria-pressed="true">All</button>')
    for sev in SEVERITIES:
        n = sum(1 for c in by_code if sev_of(c) == sev)
        if n:
            A(f'<button data-sev="{sev}" aria-pressed="false">{sev} ({n})</button>')
    A('</div>')
    for code, items in ranked:
        d = ISSUE_DEFS.get(code)
        if not d:
            continue
        urls = sorted({(i.url, i.detail) for i in items})
        A(f'<details class="issue" data-sev="{d["sev"]}"><summary>'
          f'<span class="tag {d["sev"]}">{d["sev"]}</span><span class="name">{esc(d["title"])}</span>'
          f'<span class="tag cat">{esc(d["cat"])}</span><span class="cnt">{len(urls)}</span></summary>'
          f'<div class="issue-body"><div class="why"><b>Why it matters</b>{esc(d["why"])}</div>'
          f'<div class="how"><b>How to fix</b>{esc(d["fix"])}</div>'
          '<table><thead><tr><th style="width:58%">URL</th><th>Detail</th></tr></thead><tbody>')
        for u, det in urls[:200]:
            A(f'<tr><td><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></td>'
              f'<td class="d">{esc(det)}</td></tr>')
        A('</tbody></table>')
        if len(urls) > 200:
            A(f'<div class="more">+ {len(urls)-200} more — see issues.csv</div>')
        A('</div></details>')

    # content & keywords
    if content and content.get("site_keywords"):
        A(H("Content &amp; keywords"))
        A('<p style="margin:-6px 0 6px;color:var(--ink-2);font-size:14px">'
          'The phrases this site actually talks about, pulled from its titles, headings and '
          'descriptions. If your target keywords aren\'t in this list, the site isn\'t saying '
          'what you think it\'s saying.</p>')
        A('<div class="kws">')
        for i, (term, count, npages) in enumerate(content["site_keywords"]):
            A(f'<span class="kw{" lead" if i < 3 else ""}"><b>{esc(term)}</b>'
              f'<span>{count}× · {npages} page{"s" if npages != 1 else ""}</span></span>')
        A('</div>')

        q = content.get("pages", {})
        if q:
            reads = [v["read"]["grade"] for v in q.values() if v.get("read")]
            specs = [v["spec"]["per_100_words"] for v in q.values() if v.get("spec")]
            fillers = sum(sum(n for _, n in v.get("filler", [])) for v in q.values())
            A('<div class="stats">')
            for v, k in [(f"{statistics.median(reads):.1f}" if reads else "—", "Median reading grade"),
                         (f"{statistics.median(specs):.1f}" if specs else "—", "Detail per 100 words"),
                         (fillers, "Filler phrases"),
                         (f"{statistics.median([v['words'] for v in q.values()]):.0f}", "Median words")]:
                A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
            A('</div>')

            A('<div class="label" style="margin:24px 0 8px">Page by page</div>')
            A('<table><thead><tr><th style="width:30%">URL</th><th>What it\'s about</th>'
              '<th>Words</th><th>Grade</th><th>Detail</th><th>Filler</th></tr></thead><tbody>')
            for u, v in sorted(q.items(), key=lambda kv: -(kv[1]["words"]))[:60]:
                r = v.get("read") or {}
                sp = v.get("spec", {}).get("per_100_words", 0)
                fl = sum(n for _, n in v.get("filler", []))
                A(f'<tr><td>{esc(u)}</td>'
                  f'<td class="d">{esc(", ".join(v["terms"][:3]) or "—")}</td>'
                  f'<td>{v["words"]}</td>'
                  f'<td>{r.get("grade", "—")}</td>'
                  f'<td class="{"bad" if sp < 2 else ""}">{sp}</td>'
                  f'<td class="{"bad" if fl >= 3 else ""}">{fl or "—"}</td></tr>')
            A('</tbody></table>')

        A('<div class="note"><b>How to read this.</b> '
          '<b>Grade</b> is the US school year needed to read the page comfortably; 8–10 suits '
          'most commercial writing, above 14 is heavy going. '
          '<b>Detail</b> counts concrete specifics — numbers, dates, names, prices — per 100 '
          'words. Below 2 means the page could have been written about any company in your '
          'sector, which is the real reason generic pages fail. '
          '<b>Filler</b> counts stock phrases that can be deleted without losing meaning.'
          '<br><br>'
          'There is deliberately no "AI-written" score here. Detectors of that kind are '
          'unreliable — they flag plenty of human writing and miss plenty of machine writing — '
          'and Google ranks pages on whether they help the reader, not on how they were '
          'produced. Thin, generic, hedging content is a problem whoever wrote it, and the '
          'three columns above measure that directly.</div>')

    # ---- indexability: what is and isn't in the index --------------------
    A(H("Which pages can be indexed"))
    idx_rows = []
    for p in sorted(pages.values(), key=lambda x: (x.depth, x.url)):
        u = p.final_url or p.url
        if p.error == "blocked-by-robots":
            idx_rows.append((p.url, "No", "Blocked by robots.txt"))
        elif p.status == -2:
            idx_rows.append((p.url, "No", "Redirect loop"))
        elif p.status == 0:
            idx_rows.append((p.url, "No", f"No response ({esc(p.error)})"))
        elif 400 <= p.status < 600:
            idx_rows.append((p.url, "No", f"HTTP {p.status}"))
        elif p.redirect_chain and normalise(p.final_url) != normalise(p.url):
            idx_rows.append((p.url, "No", f"Redirects to {p.final_url}"))
        elif "html" not in p.content_type.lower():
            continue
        else:
            robots = (p.meta_robots + " " + p.x_robots).lower()
            if "noindex" in robots:
                idx_rows.append((u, "No", f"noindex — {esc(p.meta_robots or p.x_robots)}"))
            elif p.canonical and normalise(p.canonical) != normalise(u):
                idx_rows.append((u, "No", f"Canonical points to {p.canonical}"))
            else:
                idx_rows.append((u, "Yes", "Indexable"))
    blocked = [r for r in idx_rows if r[1] == "No"]
    ok_rows = [r for r in idx_rows if r[1] == "Yes"]
    A('<div class="stats">')
    for v, k in [(len(ok_rows), "Can be indexed"), (len(blocked), "Cannot be indexed"),
                 (len(crawler.sitemap_entries), "URLs in sitemap"),
                 (sum(1 for r in blocked if "noindex" in r[2]), "Noindex tags")]:
        A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
    A('</div>')
    if blocked:
        A('<div class="label" style="margin:22px 0 8px">Pages that will not appear in Google</div>')
        A('<table><thead><tr><th style="width:55%">URL</th><th>Why not</th></tr></thead><tbody>')
        for u, _, why in blocked[:200]:
            A(f'<tr><td><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></td>'
              f'<td class="d">{why}</td></tr>')
        A('</tbody></table>')
        if len(blocked) > 200:
            A(f'<div class="more">+ {len(blocked)-200} more — see indexability.csv</div>')
    if ok_rows:
        A('<details class="issue" style="margin-top:14px"><summary>'
          f'<span class="name">Pages that can be indexed</span><span class="cnt">{len(ok_rows)}</span>'
          '</summary><div class="issue-body"><table><tbody>')
        for u, _, _ in ok_rows[:200]:
            A(f'<tr><td><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></td></tr>')
        A('</tbody></table></div></details>')

    # ---- heading structure ------------------------------------------------
    A(H("Heading structure, page by page"))
    A('<p style="margin:-6px 0 14px;color:var(--ink-2);font-size:14px">'
      'Every page\'s outline as a crawler reads it. Open a page to see its headings in order. '
      'Problems are called out at the top of each row.</p>')
    hpages = [p for p in pages.values()
              if p.status == 200 and "html" in p.content_type.lower() and p.headings]
    for p in sorted(hpages, key=lambda x: (x.depth, x.url))[:80]:
        u = p.final_url or p.url
        flags = []
        if not p.h1s:
            flags.append("no H1")
        elif len(p.h1s) > 1:
            flags.append(f"{len(p.h1s)} H1s")
        levels = [lv for lv, _ in p.headings]
        if any(b - a > 1 for a, b in zip(levels, levels[1:])):
            flags.append("skipped level")
        if len(p.headings) < 3 and p.word_count > 600:
            flags.append("few headings for the length")
        badge = (f'<span class="tag medium">{esc(", ".join(flags))}</span>'
                 if flags else '<span class="tag cat">ok</span>')
        A('<details class="issue"><summary>' + badge +
          f'<span class="name mono" style="font-size:12.5px">{esc(u)}</span>'
          f'<span class="cnt">{len(p.headings)} headings</span></summary>'
          '<div class="issue-body"><table><tbody>')
        for lv, text in p.headings[:120]:
            indent = (lv - 1) * 22
            cls = "bad" if lv == 1 and len(p.h1s) > 1 else ""
            A(f'<tr><td style="padding-left:{indent}px" class="{cls}">'
              f'<b>H{lv}</b> &nbsp; {esc(text[:150]) or "<i>(empty heading)</i>"}</td></tr>')
        A('</tbody></table></div></details>')
    if len(hpages) > 80:
        A(f'<div class="more">+ {len(hpages)-80} more pages — see headings.csv</div>')

    # ---- images missing alt text -----------------------------------------
    alt_pages = [p for p in pages.values() if p.missing_alt_images]
    A(H("Images missing alt text"))
    if not alt_pages:
        A('<div class="note">Every image found in the crawl has an alt attribute. '
          'Spot-check that the text is descriptive rather than a filename.</div>')
    else:
        total_missing = sum(len(p.missing_alt_images) for p in alt_pages)
        A('<div class="stats">')
        for v, k in [(total_missing, "Images without alt"), (len(alt_pages), "Pages affected"),
                     (sum(p.images for p in pages.values()), "Images found")]:
            A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
        A('</div>')
        A('<p style="margin:16px 0 12px;color:var(--ink-2);font-size:14px">'
          'Alt text is how blind users experience an image and how Google Images understands it. '
          'Describe what the image shows in context; use <span class="mono">alt=""</span> only '
          'when the image is purely decorative.</p>')
        for p in sorted(alt_pages, key=lambda x: -len(x.missing_alt_images))[:60]:
            u = p.final_url or p.url
            A('<details class="issue"><summary><span class="tag medium">'
              f'{len(p.missing_alt_images)} missing</span>'
              f'<span class="name mono" style="font-size:12.5px">{esc(u)}</span>'
              f'<span class="cnt">of {p.images} images</span></summary>'
              '<div class="issue-body"><table><thead><tr><th>Image file</th></tr></thead><tbody>')
            for img in p.missing_alt_images:
                A(f'<tr><td>{esc(img)}</td></tr>')
            A('</tbody></table></div></details>')

    # ---- internal links & anchor text ------------------------------------
    if links_data:
        r = links_data["ratios"]
        A(H("Internal links &amp; anchor text"))
        A('<div class="stats">')
        for v, k in [(r["internal_links"], "Internal links"),
                     (f'{r["contextual_share"]}%', "Contextual"),
                     (r["avg_out_per_page"], "Links out per page"),
                     (r["median_in_per_page"], "Median links in"),
                     (r["internal_external_ratio"], "Internal : external"),
                     (r["pages_under_3_inlinks"], "Pages under 3 links in")]:
            A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
        A('</div>')
        A('<div class="note"><b>Contextual vs navigation.</b> '
          f'{r["contextual"]} of your {r["internal_links"]} internal links sit inside page '
          f'content; {r["navigational"]} come from menus, headers and footers that repeat '
          'site-wide. Google discounts repeated navigation heavily, so contextual links are '
          'what actually move authority between pages. '
          f'{r["pages_without_contextual"]} page(s) have no contextual outbound links at all.</div>')

        A('<div class="label" style="margin:24px 0 8px">Anchor text types</div>')
        A('<table><thead><tr><th>Type</th><th>Links</th><th>Share</th>'
          '<th>What it means</th></tr></thead><tbody>')
        type_meaning = {
            "Branded": "Uses your brand name. Safe, and the backbone of a natural profile.",
            "Exact match": "Exactly matches a target keyword. Powerful, but overuse looks manipulative.",
            "Partial match": "Contains keyword words in a natural phrase. The healthiest type to grow.",
            "Generic": "'Click here', 'read more'. Passes no topical meaning — rewrite these.",
            "Naked URL": "The raw address as the anchor. Neutral; fine in moderation.",
            "Image / empty": "Link wrapped around an image with no alt text. Invisible to Google.",
            "Long-tail": "A full phrase or sentence. Natural and usually descriptive.",
            "Other": "Descriptive text that doesn't match your tracked keywords.",
        }
        tot = sum(links_data["types"].values()) or 1
        for t in ANCHOR_TYPES:
            n = links_data["types"].get(t, 0)
            if not n:
                continue
            A(f'<tr><td><b>{esc(t)}</b></td><td>{n}</td><td>{n/tot*100:.0f}%</td>'
              f'<td class="d">{esc(type_meaning.get(t, ""))}</td></tr>')
        A('</tbody></table>')

        A('<div class="label" style="margin:24px 0 8px">Most used anchors, and where they appear</div>')
        A('<table><thead><tr><th style="width:22%">Anchor text</th><th>Type</th><th>Used</th>'
          '<th>Points to</th><th>Used on these pages</th></tr></thead><tbody>')
        for anchor, rec in links_data["anchors"][:40]:
            tgt = ", ".join(t for t, _ in rec["targets"].most_common(2))
            srcs = sorted(rec["sources"])
            src_txt = ", ".join(srcs[:3]) + (f" +{len(srcs)-3} more" if len(srcs) > 3 else "")
            A(f'<tr><td class="d">{esc(anchor or "(image or empty)")}</td>'
              f'<td>{esc(rec["type"])}</td><td>{rec["count"]}</td>'
              f'<td>{esc(tgt)}</td><td>{esc(src_txt)}</td></tr>')
        A('</tbody></table>')

        A('<div class="label" style="margin:24px 0 8px">Link counts per page</div>')
        A('<table><thead><tr><th style="width:42%">URL</th><th>Links in</th>'
          '<th>Contextual out</th><th>Navigation out</th><th>External out</th></tr></thead><tbody>')
        for u, v in sorted(links_data["per_page"].items(), key=lambda kv: kv[1]["inlinks"])[:120]:
            A(f'<tr><td><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></td>'
              f'<td class="{"bad" if v["inlinks"] < 3 else ""}">{v["inlinks"]}</td>'
              f'<td class="{"bad" if v["out_contextual"] == 0 else ""}">{v["out_contextual"]}</td>'
              f'<td>{v["out_nav"]}</td><td>{v["external"]}</td></tr>')
        A('</tbody></table>')

    # ---- keyword cannibalisation -----------------------------------------
    A(H("Keyword cannibalisation"))
    if not cannibal and not (gsc and gsc.get("cannibal")):
        A('<div class="note">No two pages appear to target the same topic. '
          'If you have Search Console data, add the export to confirm this against real '
          'queries rather than page content alone.</div>')
    else:
        A('<p style="margin:-6px 0 14px;color:var(--ink-2);font-size:14px">'
          'Pages competing with each other for the same topic. Google picks one and the '
          'others dilute it. Decide which URL should own each topic, then consolidate the '
          'rest with 301s or canonicals and re-point your internal anchors at the winner.</p>')
        A('<table><thead><tr><th style="width:26%">Topic</th><th>Detected from</th>'
          '<th>Competing URLs</th></tr></thead><tbody>')
        for c in cannibal[:40]:
            urls = "<br>".join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a>'
                               for u in c["urls"][:6])
            A(f'<tr><td class="d"><b>{esc(c["term"])}</b></td>'
              f'<td class="d">{esc(c["basis"])}</td><td>{urls}</td></tr>')
        A('</tbody></table>')
        if gsc and gsc.get("cannibal"):
            A(f'<div class="note">Search Console shows {gsc["cannibal"]} queries where more than '
              'one of your URLs ranks. Those are listed in the issue register under '
              '"Keyword cannibalisation" with the query attached.</div>')

    # ---- analytics & tracking --------------------------------------------
    if tracking:
        A(H("Analytics &amp; tracking tags"))
        if tracking["found"]:
            A('<div class="label" style="margin-bottom:8px">Installed</div>')
            A('<table><thead><tr><th>Tag</th><th>Pages</th><th>Coverage</th></tr></thead><tbody>')
            for name, n in tracking["found"]:
                pct = n / max(tracking["total_pages"], 1) * 100
                A(f'<tr><td><b>{esc(name)}</b></td><td>{n} of {tracking["total_pages"]}</td>'
                  f'<td class="{"bad" if pct < 90 else "ok"}">{pct:.0f}%'
                  f'{" — not on every page" if pct < 90 else ""}</td></tr>')
            A('</tbody></table>')
        else:
            A('<div class="note bad"><b>No analytics or tag manager found anywhere on the site.</b> '
              'You currently have no measurement at all, which means no way to tell whether any '
              'SEO work is paying off.</div>')

        if tracking["untagged"]:
            A('<div class="label" style="margin:22px 0 8px">Pages with no tracking tag</div>')
            A('<table><tbody>')
            for u in tracking["untagged"][:80]:
                A(f'<tr><td><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></td></tr>')
            A('</tbody></table>')
            if len(tracking["untagged"]) > 80:
                A(f'<div class="more">+ {len(tracking["untagged"])-80} more</div>')

        if tracking["missing"]:
            A('<div class="label" style="margin:24px 0 8px">Worth adding</div>')
            A('<table><thead><tr><th style="width:26%">Tag</th><th>Why</th></tr></thead><tbody>')
            for name, why in tracking["missing"]:
                A(f'<tr><td><b>{esc(name)}</b></td><td class="d">{esc(why)}</td></tr>')
            A('</tbody></table>')

        if tracking["verification"]:
            A('<div class="note">Site-verification tags found: ' +
              esc(", ".join(f"{v} ({n} pages)" for v, n in tracking["verification"])) + '</div>')
        else:
            A('<div class="note">No search-engine verification meta tag was found. That doesn\'t '
              'mean Search Console isn\'t connected — DNS and file verification are both common — '
              'but confirm the property is verified, because without it you have no query data.</div>')

    # ---- site speed & Core Web Vitals ------------------------------------
    speed = extras.get("speed") or {}
    images_d = extras.get("images") or {}
    gsc_link = extras.get("gsc_link") or {}
    authority = extras.get("authority") or {}
    moz = extras.get("moz") or {}

    if speed or psi:
        A(H("Site speed &amp; Core Web Vitals"))
        if speed:
            t = speed["ttfb"]
            A('<div class="stats">')
            for v, k in [(f'{t["median"]} ms', "Median server response"),
                         (f'{t["p90"]} ms', "Slowest 10% respond in"),
                         (f'{speed["median_weight"]/1_048_576:.2f} MB', "Median page weight"),
                         (len(speed["uncompressed"]), "Uncompressed files"),
                         (len(speed["nocache"]), "Files without caching")]:
                A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
            A('</div>')

        if psi and any("error" not in d for d in psi.values()):
            A('<div class="label" style="margin:24px 0 8px">Core Web Vitals</div>')
            A('<table><thead><tr><th style="width:36%">URL</th><th>LCP</th><th>CLS</th>'
              '<th>INP</th><th>Speed</th><th>SEO</th><th>Access.</th></tr></thead><tbody>')
            for u, d in psi.items():
                if "error" in d:
                    continue
                lcp = d["field_lcp"] or d["lcp"]
                cls_ = d["field_cls"] or d["cls"]
                A(f'<tr><td>{esc(u)}</td>'
                  f'<td class="{"bad" if lcp > 2.5 else "ok"}">{lcp:.1f}s</td>'
                  f'<td class="{"bad" if cls_ > 0.1 else "ok"}">{cls_:.2f}</td>'
                  f'<td class="{"bad" if d["field_inp"] and d["field_inp"] > 200 else ""}">'
                  f'{int(d["field_inp"]) if d["field_inp"] else "—"}</td>'
                  f'<td class="{"ok" if d["perf"] >= 90 else "bad" if d["perf"] < 50 else ""}">'
                  f'{d["perf"]}</td><td>{d["seo"]}</td><td>{d["a11y"]}</td></tr>')
            A('</tbody></table>')
            A('<div class="note"><b>Pass marks:</b> LCP under 2.5s, CLS under 0.1, INP under '
              '200ms. Where Google has enough real Chrome traffic for the page these are field '
              'measurements from actual visitors; otherwise they come from a lab test.</div>')
            opps = Counter()
            for d in psi.values():
                for title_, ms in d.get("opportunities", []):
                    opps[title_] += ms
            if opps:
                A('<div class="label" style="margin:22px 0 8px">Biggest wins available</div>'
                  '<table><tbody>')
                for title_, ms in opps.most_common(8):
                    A(f'<tr><td class="d">{esc(title_)}</td>'
                      f'<td style="text-align:right">up to {ms/1000:.1f}s</td></tr>')
                A('</tbody></table>')
        elif psi:
            A('<div class="note">Core Web Vitals could not be fetched from Google this time — '
              'the free quota is shared and often busy. Add a PageSpeed Insights API key on the '
              'form for reliable results. The measurements below were taken directly by the '
              'crawler and do not need any key.</div>')

        if speed:
            A('<div class="label" style="margin:24px 0 8px">Page weight, measured directly</div>')
            A('<table><thead><tr><th style="width:34%">URL</th><th>Total</th><th>HTML</th>'
              '<th>CSS</th><th>JS</th><th>Images</th><th>Requests</th><th>Blocking</th>'
              '</tr></thead><tbody>')
            for u, v in sorted(speed["per_page"].items(), key=lambda kv: -kv[1]["total"]):
                g = v["groups"]
                A(f'<tr><td>{esc(u)}</td>'
                  f'<td class="{"bad" if v["total"] > 3_000_000 else ""}">'
                  f'{v["total"]/1_048_576:.2f} MB</td>'
                  f'<td>{g["HTML"]//1024} KB</td><td>{g["CSS"]//1024} KB</td>'
                  f'<td>{g["JavaScript"]//1024} KB</td><td>{g["Images"]//1024} KB</td>'
                  f'<td>{v["requests"]}</td>'
                  f'<td class="{"bad" if v["blocking"] > 5 else ""}">{v["blocking"]}</td></tr>')
            A('</tbody></table>')

            if speed["largest"]:
                A('<div class="label" style="margin:24px 0 8px">Heaviest files on the site</div>')
                A('<table><thead><tr><th style="width:62%">File</th><th>Size</th>'
                  '<th>Type</th></tr></thead><tbody>')
                for u, b, ctype in speed["largest"]:
                    A(f'<tr><td>{esc(u)}</td>'
                      f'<td class="{"bad" if b > 500_000 else ""}">{b//1024} KB</td>'
                      f'<td class="d">{esc(ctype)}</td></tr>')
                A('</tbody></table>')

            A('<div class="label" style="margin:24px 0 8px">Slowest pages to respond</div>')
            A('<table><tbody>')
            for u, ms in speed["ttfb"]["slowest"]:
                A(f'<tr><td>{esc(u)}</td>'
                  f'<td style="text-align:right" class="{"bad" if ms > 600 else ""}">{ms} ms</td></tr>')
            A('</tbody></table>')

    # ---- image formats ----------------------------------------------------
    if images_d and images_d.get("total"):
        A(H("Image formats &amp; optimisation"))
        A('<div class="stats">')
        for v, k in [(images_d["unique"], "Unique images"),
                     (f'{images_d["modern_share"]}%', "WebP or AVIF"),
                     (images_d["legacy_count"], "Still JPEG/PNG"),
                     (len(images_d["oversized"]), "Over 200 KB"),
                     (images_d["no_lazy"], "Not lazy-loaded"),
                     (f'{images_d["potential_saving"]/1_048_576:.1f} MB',
                      "Saving from WebP")]:
            A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
        A('</div>')

        A('<div class="label" style="margin:24px 0 8px">Formats in use</div>')
        A('<table><thead><tr><th>Format</th><th>Images</th><th>Total size</th>'
          '<th>Verdict</th></tr></thead><tbody>')
        verdicts = {
            "webp": "Modern and well supported everywhere. Keep using it.",
            "avif": "The smallest option. Serve with a WebP fallback for older browsers.",
            "svg": "Right choice for logos and icons — resolution independent and tiny.",
            "jpg": "Convert to WebP. Expect roughly 25–35% smaller at the same quality.",
            "png": "Convert to WebP unless you need lossless transparency — savings are often larger than JPEG's.",
            "gif": "Replace animated GIFs with MP4 or WebM; they are frequently 10× smaller.",
        }
        for ext, n in images_d["formats"]:
            b = images_d["bytes_by_format"].get(ext, 0)
            good = ext in MODERN_FORMATS or ext == "svg"
            A(f'<tr><td><b>{esc(ext.upper())}</b></td><td>{n}</td>'
              f'<td>{b//1024 if b else "—"} KB</td>'
              f'<td class="{"ok" if good else "bad"}">'
              f'{esc(verdicts.get(ext, "Check whether a modern format suits this file."))}</td></tr>')
        A('</tbody></table>')

        if images_d["legacy"]:
            A('<div class="note"><b>Converting these to WebP would save roughly '
              f'{images_d["potential_saving"]//1024} KB</b> across the site, based on the '
              'typical 30% reduction. If you use WordPress, a plugin will do it in bulk; on a '
              'CDN like Cloudflare or Fastly, format conversion is usually a single setting.</div>')
            A('<div class="label" style="margin:22px 0 8px">Images to convert</div>')
            A('<table><thead><tr><th style="width:52%">Image</th><th>Format</th><th>Size</th>'
              '<th>Used on</th></tr></thead><tbody>')
            for u, d in images_d["legacy"][:60]:
                pg = sorted(d["pages"])
                A(f'<tr><td>{esc(u)}</td><td>{esc(d["ext"].upper())}</td>'
                  f'<td class="{"bad" if d["bytes"] > 200_000 else ""}">'
                  f'{d["bytes"]//1024 if d["bytes"] else "—"} KB</td>'
                  f'<td class="d">{esc(pg[0])}{f" +{len(pg)-1}" if len(pg) > 1 else ""}</td></tr>')
            A('</tbody></table>')

        extras_note = []
        if images_d["no_srcset"]:
            extras_note.append(f'{images_d["no_srcset"]} image tags have no srcset, so phones '
                               'download the same file as desktops')
        if images_d["no_lazy"]:
            extras_note.append(f'{images_d["no_lazy"]} images below the fold load eagerly')
        if not images_d["picture_pages"]:
            extras_note.append('no page uses a &lt;picture&gt; element, which is how you serve '
                               'WebP with a JPEG fallback')
        if extras_note:
            A('<div class="note"><b>Also worth fixing:</b> ' + "; ".join(extras_note) + '.</div>')

    # ---- Search Console ---------------------------------------------------
    if gsc_link:
        A(H("Search Console &amp; verification"))
        state = ("ok" if gsc_link["connected"]
                 else "bad" if gsc_link.get("dns_ok") else "")
        A('<table><thead><tr><th style="width:30%">Check</th><th>Result</th></tr></thead><tbody>')
        A(f'<tr><td><b>Google verification</b></td><td class="{state}">' +
          ("Verified — " + esc(", ".join(gsc_link["meta_tags"] or ["DNS record found"]))
           if gsc_link["connected"] else
           "No verification meta tag and no google-site-verification DNS record found"
           if gsc_link.get("dns_ok") else
           "No meta tag found. DNS records could not be checked from this machine, "
           "so verification by DNS can't be ruled out.") +
          '</td></tr>')
        A('<tr><td><b>DNS TXT records</b></td><td class="d">' +
          (esc("; ".join(gsc_link["dns_google"])) if gsc_link["dns_google"]
           else f'No Google record among {len(gsc_link["txt_records"])} TXT record(s) found'
                if gsc_link.get("dns_ok")
                else "DNS lookup unavailable — check your connection or firewall") +
          '</td></tr>')
        A('<tr><td><b>Bing Webmaster Tools</b></td><td class="d">' +
          ("Verification found" if gsc_link["dns_bing"] else
           "Not detected. Bing drives ChatGPT and Copilot results, so it's worth 5 minutes.") +
          '</td></tr>')
        A('<tr><td><b>Sitemap in robots.txt</b></td>'
          f'<td class="{"ok" if gsc_link["sitemap_declared"] else "bad"}">' +
          ("Declared" if gsc_link["sitemap_declared"] else "Missing a Sitemap: line") +
          '</td></tr>')
        A('</tbody></table>')
        if not gsc_link["connected"] and gsc_link.get("dns_ok"):
            A('<div class="note"><b>Verification could not be confirmed — but this is not proof '
              'it is missing.</b> Google offers three methods and only two are visible from '
              'outside: a meta tag in the HTML and a DNS TXT record. The third uploads a file '
              'with an unguessable name, which nobody can detect by crawling.<br><br>'
              'If the site genuinely is not connected, add it at search.google.com/search-console '
              'and verify by <b>DNS TXT record</b> — that covers www and non-www, http and https, '
              'and every subdomain in one go, and it survives site redesigns.</div>')

    # ---- authority --------------------------------------------------------
    if authority or moz:
        A(H("Authority"))
        if moz and not moz.get("__error__"):
            home_key = next((k for k in moz if registrable(up.urlsplit(k).netloc or k)
                             == registrable(host)), None)
            home = moz.get(home_key, {})
            A('<div class="stats">')
            for v, k in [(home.get("da", "—"), "Domain Authority"),
                         (home.get("pa", "—"), "Page Authority (home)"),
                         (home.get("spam", "—"), "Spam score"),
                         (home.get("linking_domains", "—"), "Linking domains")]:
                A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
            A('</div>')
            A('<div class="label" style="margin:24px 0 8px">Page Authority by page</div>')
            A('<table><thead><tr><th style="width:56%">URL</th><th>PA</th><th>DA</th>'
              '<th>Linking domains</th></tr></thead><tbody>')
            for u, d in sorted(moz.items(), key=lambda kv: -(kv[1].get("pa") or 0)):
                if u == "__error__":
                    continue
                A(f'<tr><td>{esc(u)}</td><td>{esc(d.get("pa", "—"))}</td>'
                  f'<td>{esc(d.get("da", "—"))}</td>'
                  f'<td>{esc(d.get("linking_domains", "—"))}</td></tr>')
            A('</tbody></table>')
        elif moz.get("__error__"):
            A(f'<div class="note bad">{esc(moz["__error__"])}</div>')
        else:
            A('<div class="note"><b>Domain Authority and Page Authority are Moz\'s own metrics, '
              'not Google\'s.</b> No tool can calculate them — they can only be read from Moz\'s '
              'API, which needs an account. Add your Moz key on the form and they will appear '
              'here. Ahrefs\' Domain Rating and Semrush\'s Authority Score work the same way.'
              '<br><br>Neither number is used by Google. They are third-party estimates of link '
              'strength, useful for comparing yourself with competitors and for judging whether '
              'a link is worth chasing — nothing more.</div>')

        if authority:
            ranked = sorted(authority.items(), key=lambda kv: -kv[1])
            A('<div class="label" style="margin:24px 0 8px">Internal authority — where your own '
              'link equity actually sits</div>')
            A('<p style="margin:0 0 12px;color:var(--ink-2);font-size:14px">'
              'PageRank calculated across your internal links, scored against your strongest '
              'page at 100. This is the part of authority you control directly: if a page you '
              'need to rank sits near the bottom, link to it from the pages near the top.</p>')
            A('<div class="two"><div>'
              '<div class="label" style="margin-bottom:8px">Strongest pages</div>'
              '<table><tbody>')
            for u, s in ranked[:12]:
                A(f'<tr><td>{esc(u)}</td><td style="text-align:right"><b>{s}</b></td></tr>')
            A('</tbody></table></div><div>'
              '<div class="label" style="margin-bottom:8px">Weakest pages</div><table><tbody>')
            for u, s in ranked[-12:]:
                A(f'<tr><td>{esc(u)}</td><td style="text-align:right" class="bad">{s}</td></tr>')
            A('</tbody></table></div></div>')

    # search performance
    if gsc:
        A(H("Rankings &amp; search performance"))
        A('<div class="stats">')
        for v, k in [(f"{gsc['clicks']:,}", "Clicks"), (f"{gsc['impressions']:,}", "Impressions"),
                     (gsc["avg_pos"], "Avg position"), (gsc["top3"], "Top-3 queries"),
                     (gsc["page1"], "Page-1 queries"), (gsc["striking"], "Position 11–20"),
                     (gsc["cannibal"], "Cannibalised queries")]:
            A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
        A('</div><div class="two"><div><div class="label" style="margin-bottom:8px">Top queries by clicks</div>'
          '<table><thead><tr><th>Query</th><th>Pos</th><th>Clicks</th></tr></thead><tbody>')
        for r in gsc["top_queries"]:
            A(f'<tr><td class="d">{esc(r["query"])}</td><td>{r["pos"]:.1f}</td><td>{int(r["clicks"])}</td></tr>')
        A('</tbody></table></div><div><div class="label" style="margin-bottom:8px">Striking distance (page 2)</div>'
          '<table><thead><tr><th>Query</th><th>Pos</th><th>Impr.</th></tr></thead><tbody>')
        for r in gsc["striking_list"]:
            A(f'<tr><td class="d">{esc(r["query"])}</td><td>{r["pos"]:.1f}</td><td>{int(r["impressions"])}</td></tr>')
        A('</tbody></table></div></div>')

    # off-page
    A(H("Off-page profile"))
    if backlinks:
        A('<div class="stats">')
        for v, k in [(f'{backlinks["links"]:,}', "Backlinks"),
                     (f'{backlinks["domains"]:,}', "Referring domains"),
                     (f'{backlinks["follow"]:,}', "Follow links"),
                     (f'{backlinks["nofollow_share"]}%', "Nofollow"),
                     (f'{backlinks["branded_share"]}%', "Branded anchors"),
                     (f'{backlinks["exact_share"]}%', "Exact-match anchors"),
                     (backlinks["avg_auth"] if backlinks["avg_auth"] is not None else "—",
                      "Avg authority")]:
            A(f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>')
        A('</div>')

        A('<div class="note"><b>How to read the anchor split.</b> A natural profile is '
          'dominated by branded and URL anchors — roughly 40–70% branded — with exact-match '
          'commercial anchors under about 10%. Yours is '
          f'{backlinks["branded_share"]}% branded and {backlinks["exact_share"]}% exact match. '
          'A high exact-match share is the pattern manual reviewers look for.</div>')

        A('<div class="label" style="margin:24px 0 8px">Anchor text breakdown</div>')
        A('<table><thead><tr><th>Type</th><th>Links</th><th>Share</th></tr></thead><tbody>')
        tot = sum(backlinks["anchor_types"].values()) or 1
        for t in ANCHOR_TYPES:
            n = backlinks["anchor_types"].get(t, 0)
            if n:
                A(f'<tr><td><b>{esc(t)}</b></td><td>{n}</td><td>{n/tot*100:.0f}%</td></tr>')
        A('</tbody></table>')

        A('<div class="two" style="margin-top:24px"><div>'
          '<div class="label" style="margin-bottom:8px">Top referring domains</div>'
          '<table><thead><tr><th>Domain</th><th>Links</th><th>DR</th></tr></thead><tbody>')
        for d, n, auth in backlinks["top_domains"]:
            A(f'<tr><td>{esc(d)}</td><td>{n}</td><td>{auth if auth is not None else "—"}</td></tr>')
        A('</tbody></table></div><div>'
          '<div class="label" style="margin-bottom:8px">Most used anchors</div>'
          '<table><thead><tr><th>Anchor</th><th>Type</th><th>n</th></tr></thead><tbody>')
        for a, n, t in backlinks["top_anchors"]:
            A(f'<tr><td class="d">{esc(a[:60] or "(empty)")}</td><td>{esc(t)}</td><td>{n}</td></tr>')
        A('</tbody></table></div></div>')

        if backlinks["top_targets"]:
            A('<div class="label" style="margin:24px 0 8px">Your most linked-to pages</div>')
            A('<table><thead><tr><th style="width:70%">URL</th><th>Links</th></tr></thead><tbody>')
            for t, n in backlinks["top_targets"]:
                A(f'<tr><td>{esc(t)}</td><td>{n}</td></tr>')
            A('</tbody></table>')

        if backlinks["auth_buckets"]:
            A('<div class="two" style="margin-top:24px"><div>'
              '<div class="label" style="margin-bottom:8px">Link quality spread</div>'
              '<table><tbody>')
            for band, n in backlinks["auth_buckets"]:
                A(f'<tr><td>Authority {esc(band)}</td><td style="text-align:right">{n}</td></tr>')
            A('</tbody></table></div><div>'
              '<div class="label" style="margin-bottom:8px">Domain endings</div><table><tbody>')
            for tld, n in backlinks["tlds"]:
                A(f'<tr><td>.{esc(tld)}</td><td style="text-align:right">{n}</td></tr>')
            A('</tbody></table></div></div>')
    else:
        A('<div class="note"><b>No backlink data was supplied, so this section is based only on '
          'what the crawl can see.</b> Who links to you cannot be discovered by crawling your own '
          'site — that data belongs to Google and to the link indexes. Two ways to fill it in:'
          '<br><br><b>Free:</b> Search Console → Links → Top linking sites → Export. Save the CSV '
          'and upload it in the backlink slot on the form. It gives you referring domains, your '
          'most-linked pages and top anchor text.'
          '<br><b>Paid:</b> any Ahrefs, Semrush or Majestic backlink export works as-is.</div>')

    if offpage:
        A('<div class="label" style="margin:24px 0 8px">Brand presence found on the site</div>')
        A('<table><thead><tr><th style="width:26%">Signal</th><th>Status</th></tr></thead><tbody>')
        socials = offpage.get("socials", {})
        for name, url in socials.items():
            A(f'<tr><td><b>{esc(name)}</b></td><td class="ok">Linked — {esc(url[:80])}</td></tr>')
        for name in offpage.get("missing_socials", []):
            A(f'<tr><td><b>{esc(name)}</b></td><td class="d">Not linked from the site. '
              'If the profile exists, link it and add it to your Organization schema so Google '
              'connects it to your brand.</td></tr>')
        org = offpage.get("org_schema")
        A('<tr><td><b>Organization schema</b></td><td class="' + ("ok" if org else "d") + '">' +
          (esc(", ".join(org)) + " on the homepage" if org else
           "Missing. This is how you tell Google which entity the site belongs to — add it with "
           "name, logo, url and sameAs links to every profile above.") + '</td></tr>')
        A(f'<tr><td><b>Outbound links</b></td><td class="d">'
          f'{offpage.get("outbound_total", 0)} links to '
          f'{offpage.get("outbound_unique", 0)} external domains'
          f'{", " + str(offpage["nofollow_out"]) + " nofollowed" if offpage.get("nofollow_out") else ""}. '
          'Linking out to credible sources is a quality signal, not a leak.</td></tr>')
        A('</tbody></table>')
        if offpage.get("outbound_domains"):
            A('<div class="label" style="margin:22px 0 8px">Domains you link out to</div>'
              '<table><tbody>')
            for d, n in offpage["outbound_domains"]:
                A(f'<tr><td>{esc(d)}</td><td style="text-align:right">{n}</td></tr>')
            A('</tbody></table>')

    # appendix
    A(H("Crawl appendix") + '<div class="two"><div>'
      '<div class="label" style="margin-bottom:8px">robots.txt</div>')
    A(f'<pre class="robots">{esc(crawler.robots_txt[:4000]) if crawler.robots_txt else "Not found."}</pre></div><div>'
      '<div class="label" style="margin-bottom:8px">Sitemaps</div><pre class="robots">' +
      (esc("\n".join(crawler.sitemap_urls) + f"\n\n{len(crawler.sitemap_entries)} URLs listed")
       if crawler.sitemap_urls else "None found.") + '</pre>'
      f'<div class="label" style="margin:14px 0 6px">Missing-page probe</div>'
      f'<pre class="robots">Random missing URL returned: {esc(auditor.notes.get("404_status","—"))}</pre></div></div>')

    A(H("Method &amp; limits") +
      '<div class="note">This audit is based on the raw HTML response for each URL, the same way Googlebot '
      'first sees a page. Content injected purely by client-side JavaScript will not be counted — if the site '
      'is a SPA, verify key pages with Search Console\'s URL Inspection tool.<br><br>'
      'Off-page authority and live rankings cannot be measured by crawling: they come from the optional '
      'Search Console and backlink exports. Sections you don\'t see here simply had no data supplied.<br><br>'
      'Scores are computed from issue severity weighted by the share of crawled pages affected. '
      'They are a triage aid, not a ranking prediction.</div>')

    A('<footer>' + (f'Audit prepared by <b style="color:var(--brand)">{esc(brand_name)}</b> · '
                    if brand_name else "") +
      f'{esc(cfg.start_url)} · {datetime.now(timezone.utc).strftime("%d %B %Y")}</footer>')
    A(f'</div><script>{JS}</script></body></html>')
    return "".join(out)


# ---------------------------------------------------------------------------
# CSV exports
# ---------------------------------------------------------------------------

def _content_cols(content, url):
    """Keyword and readability columns for pages.csv; blanks when analysis is unavailable."""
    q = (content or {}).get("pages", {}).get(url)
    if not q:
        return ["", "", "", "", "", "", ""]
    r = q.get("read") or {}
    return ["|".join(q.get("terms", [])[:5]), r.get("flesch", ""), r.get("grade", ""),
            r.get("avg_sentence", ""), q.get("spec", {}).get("per_100_words", ""),
            sum(n for _, n in q.get("filler", [])), q.get("repetition", "")]


def write_csvs(outdir, crawler, auditor, content=None, extras=None):
    pages_path = os.path.join(outdir, "pages.csv")
    with open(pages_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "status", "final_url", "redirects", "depth", "ttfb_ms", "size_bytes",
                    "indexable", "title", "title_len", "meta_description", "desc_len", "h1",
                    "h1_count", "word_count", "text_ratio", "canonical", "meta_robots",
                    "internal_links_out", "external_links_out", "inlinks", "images", "images_no_alt",
                    "schema_types", "lang", "viewport", "top_keywords", "flesch", "reading_grade",
                    "avg_sentence_words", "specificity_per_100w", "filler_phrases", "repetition_pct",
                    "internal_authority", "render_blocking", "css_files", "js_files"])
        for p in sorted(crawler.pages.values(), key=lambda x: (x.depth, x.url)):
            w.writerow([p.url, p.status, p.final_url, len(p.redirect_chain), p.depth, p.ttfb_ms,
                        p.size_bytes, int(p.indexable), p.title, len(p.title), p.description,
                        len(p.description), p.h1s[0] if p.h1s else "", len(p.h1s), p.word_count,
                        p.text_ratio, p.canonical, p.meta_robots, len(p.internal_links),
                        len(p.external_links), p.inlinks, p.images, p.images_no_alt,
                        "|".join(sorted(set(p.schema_types))), p.lang, int(p.viewport)]
                       + _content_cols(content, p.final_url or p.url)
                       + [(extras or {}).get("authority", {}).get(p.final_url or p.url, ""),
                          p.render_blocking, len(p.stylesheets), len(p.scripts)])

    issues_path = os.path.join(outdir, "issues.csv")
    with open(issues_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["severity", "category", "issue", "url", "detail", "why_it_matters", "how_to_fix"])
        order = {s: i for i, s in enumerate(SEVERITIES)}
        for i in sorted(auditor.issues, key=lambda x: (order.get(ISSUE_DEFS.get(x.code, {}).get("sev", "low"), 9), x.code, x.url)):
            d = ISSUE_DEFS.get(i.code, {})
            w.writerow([d.get("sev", ""), d.get("cat", ""), d.get("title", i.code), i.url,
                        i.detail, d.get("why", ""), d.get("fix", "")])
    extras = extras or {}

    with open(os.path.join(outdir, "headings.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "position", "level", "heading_text"])
        for p in sorted(crawler.pages.values(), key=lambda x: (x.depth, x.url)):
            for i, (lv, text) in enumerate(p.headings, 1):
                w.writerow([p.final_url or p.url, i, f"H{lv}", text])

    with open(os.path.join(outdir, "images-missing-alt.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["page_url", "image_url", "images_on_page", "images_missing_alt"])
        for p in crawler.pages.values():
            for img in p.missing_alt_images:
                w.writerow([p.final_url or p.url, img, p.images, p.images_no_alt])

    lp = (extras.get("links") or {}).get("per_page", {})
    with open(os.path.join(outdir, "internal-links.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_url", "target_url", "anchor_text", "anchor_type",
                    "link_type", "nofollow"])
        anchors = {a: rec for a, rec in (extras.get("links") or {}).get("anchors", [])}
        boiler = (extras.get("links") or {}).get("boilerplate", set())
        for p in crawler.pages.values():
            for target, anchor, nofollow, in_chrome in p.internal_links:
                rec = anchors.get((anchor or "").strip()[:120])
                contextual = not in_chrome and target not in boiler
                w.writerow([p.final_url or p.url, target, anchor,
                            rec["type"] if rec else "", 
                            "contextual" if contextual else "navigation", int(nofollow)])

    with open(os.path.join(outdir, "indexability.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "can_be_indexed", "reason", "status", "canonical", "meta_robots"])
        for p in sorted(crawler.pages.values(), key=lambda x: (x.depth, x.url)):
            u = p.final_url or p.url
            robots = (p.meta_robots + " " + p.x_robots).lower()
            if p.error == "blocked-by-robots":
                yes, why = "no", "blocked by robots.txt"
            elif p.status == 0:
                yes, why = "no", f"no response ({p.error})"
            elif 400 <= p.status < 600:
                yes, why = "no", f"HTTP {p.status}"
            elif p.redirect_chain and normalise(p.final_url) != normalise(p.url):
                u = p.url          # the URL that redirects, not where it lands
                yes, why = "no", f"redirects to {p.final_url}"
            elif "noindex" in robots:
                yes, why = "no", "noindex"
            elif p.canonical and normalise(p.canonical) != normalise(u):
                yes, why = "no", f"canonical points to {p.canonical}"
            else:
                yes, why = "yes", "indexable"
            w.writerow([u, yes, why, p.status, p.canonical, p.meta_robots])

    with open(os.path.join(outdir, "tracking.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "tags_found"])
        for p in crawler.pages.values():
            if p.status == 200 and "html" in p.content_type.lower():
                w.writerow([p.final_url or p.url, "|".join(p.analytics_tools) or "NONE"])

    return pages_path, issues_path


# ---------------------------------------------------------------------------
# PageSpeed Insights (optional)
# ---------------------------------------------------------------------------

def run_psi(urls, api_key, strategy="mobile", quiet=False):
    out = {}
    for i, u in enumerate(urls, 1):
        q = [("url", u), ("key", api_key), ("strategy", strategy)]
        q += [("category", c) for c in ("performance", "seo", "accessibility", "best-practices")]
        endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + up.urlencode(q)
        try:
            req = urllib.request.Request(endpoint, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode("utf-8", "replace"))
            lh = d.get("lighthouseResult", {})
            cats = lh.get("categories", {})
            audits = lh.get("audits", {})
            crux = d.get("loadingExperience", {}).get("metrics", {})
            out[u] = {
                "perf": round((cats.get("performance", {}).get("score") or 0) * 100),
                "seo": round((cats.get("seo", {}).get("score") or 0) * 100),
                "a11y": round((cats.get("accessibility", {}).get("score") or 0) * 100),
                "bp": round((cats.get("best-practices", {}).get("score") or 0) * 100),
                "lcp": audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000,
                "cls": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
                "tbt": audits.get("total-blocking-time", {}).get("numericValue", 0),
                "field_lcp": crux.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile", 0) / 1000,
                "field_cls": crux.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile", 0) / 100,
                "field_inp": crux.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile", 0),
                "opportunities": [
                    (a.get("title", ""), round(a.get("details", {}).get("overallSavingsMs", 0)))
                    for a in audits.values()
                    if isinstance(a, dict) and a.get("details", {}).get("type") == "opportunity"
                    and a.get("details", {}).get("overallSavingsMs", 0) > 150][:6],
            }
        except Exception as e:
            out[u] = {"error": f"{type(e).__name__}: {e}"}
        if not quiet:
            sys.stderr.write(f"\r  PageSpeed {i}/{len(urls)}")
            sys.stderr.flush()
    if not quiet:
        sys.stderr.write("\r" + " " * 40 + "\r")
    return out


def psi_issues(psi: dict, auditor):
    for u, d in psi.items():
        if "error" in d:
            continue
        lcp = d["field_lcp"] or d["lcp"]
        cls = d["field_cls"] or d["cls"]
        if lcp > 2.5:
            auditor.add("CWV_LCP", u, f"LCP {lcp:.1f}s ({'field' if d['field_lcp'] else 'lab'})")
        if cls > 0.1:
            auditor.add("CWV_CLS", u, f"CLS {cls:.2f}")
        if d["field_inp"] and d["field_inp"] > 200:
            auditor.add("CWV_INP", u, f"INP {int(d['field_inp'])}ms")
        if d["perf"] and d["perf"] < 50:
            auditor.add("PSI_LOW", u, f"Lighthouse performance {d['perf']}/100")


# ---------------------------------------------------------------------------
# Audit runner shared by the browser interface and the command line
# ---------------------------------------------------------------------------

FRIENDLY_ERRORS = {
    "gaierror": "that address doesn't seem to exist, so check the spelling",
    "ConnectionRefusedError": "nothing answered at that address",
    "ConnectionResetError": "the server closed the connection, which often means it blocks crawlers",
    "timeout": "the site took too long to respond",
    "TimeoutError": "the site took too long to respond",
    "SSLError": "there was a security-certificate problem",
    "SSLCertVerificationError": "there was a security-certificate problem",
    "RemoteDisconnected": "the server hung up, which often means it blocks crawlers",
    "blocked-private": ("that address is on a private or internal network, which this "
                        "hosted version won't crawl for security reasons"),
    "loop": "the address redirects around in a circle",
    "too many redirects": "the address redirects too many times",
    "URLError": "the connection failed",
}


def friendly_error(err):
    return FRIENDLY_ERRORS.get(str(err), f"the connection failed ({err or 'no response'})")


def run_audit(cfg, log=lambda m: None):
    t0 = time.time()
    os.makedirs(cfg.out, exist_ok=True)

    crawler = Crawler(cfg)
    log("Reading robots.txt and sitemaps…")
    crawler.load_robots(cfg.start_url)
    crawler.load_sitemaps()
    log(f"robots.txt: {'found' if crawler.robots_status == 200 else 'not found'} · "
        f"sitemaps: {len(crawler.sitemap_urls)} ({len(crawler.sitemap_entries)} URLs)")

    probe, _, perr = crawler.request(cfg.start_url)
    if probe is None and cfg.start_url.startswith("https://"):
        # Plenty of small sites are still http-only. Try that before giving up.
        alt = normalise("http://" + cfg.start_url[len("https://"):])
        log("No answer over https — trying http…")
        probe2, _, perr2 = crawler.request(alt)
        if probe2 is not None:
            cfg.start_url = alt
            cfg.root_host = up.urlsplit(alt).netloc
            crawler.load_robots(cfg.start_url)
            crawler.load_sitemaps()
            probe, perr = probe2, perr2
    if probe is None:
        raise RuntimeError(f"Could not reach {cfg.start_url} — {friendly_error(perr)}.")
    if probe.status_code >= 400:
        log(f"! Start URL returned HTTP {probe.status_code} — continuing anyway.")

    log("Crawling…")
    crawler.progress = log
    crawler.crawl(cfg.start_url)
    room = max(0, cfg.max_pages - len(crawler.pages))
    extra = [u for u in crawler.sitemap_entries
             if u not in crawler.pages and same_site(u, cfg.root_host)][:room]
    for u in extra:
        crawler.pages[u] = crawler.fetch_page(u, 99)
    log(f"{len(crawler.pages)} URLs crawled ({len(extra)} added from the sitemap)")

    if cfg.check_external:
        log("Checking outbound links…")
        crawler.check_external_links()

    log("Running checks…")
    auditor = Auditor(crawler, cfg)
    auditor.check_site()
    auditor.check_pages()

    log("Analysing keywords and content quality…")
    content = analyse_content(crawler, auditor)
    log("Measuring page speed and assets…")
    speed = analyse_speed(crawler, cfg, auditor)
    images = analyse_images(crawler, speed, auditor)
    log("Checking Search Console connection…")
    gsc_link = check_search_console(crawler, cfg, auditor)
    authority = internal_authority(crawler)
    moz = {}
    if getattr(cfg, "moz_token", "") or getattr(cfg, "moz_id", ""):
        log("Querying Moz for DA/PA…")
        top_urls = [cfg.start_url] + [u for u, _ in sorted(authority.items(),
                                                           key=lambda kv: -kv[1])[:24]]
        moz = fetch_moz(top_urls, getattr(cfg, "moz_token", ""),
                        getattr(cfg, "moz_id", ""), getattr(cfg, "moz_secret", ""))
        if moz.get("__error__"):
            log("! " + moz["__error__"])

    log("Mapping internal links and anchor text…")
    links = analyse_links(crawler, cfg, content)
    tracking = analyse_tracking(crawler)
    cannibal = analyse_cannibalisation(crawler, content, auditor)
    offpage_onsite = analyse_offpage_onsite(crawler, cfg)

    psi = {}
    if getattr(cfg, "psi_key", "") or not getattr(cfg, "skip_psi", False):
        log("Fetching Core Web Vitals from Google…")
        top = [p.final_url or p.url for p in
               sorted((p for p in crawler.pages.values()
                       if p.status == 200 and "html" in p.content_type.lower()),
                      key=lambda p: (p.depth, -p.inlinks))][:cfg.psi_pages]
        psi = run_psi(top, cfg.psi_key, quiet=cfg.quiet)
        if all("error" in d for d in psi.values()) and not cfg.psi_key:
            log("! Google's free quota is busy — add a PageSpeed API key for reliable Core Web Vitals.")
        psi_issues(psi, auditor)

    gsc = {}
    if getattr(cfg, "gsc_csv", ""):
        log("Reading Search Console export…")
        try:
            gsc = analyse_gsc(cfg.gsc_csv, auditor)
        except Exception as e:
            log(f"! Could not read the Search Console file: {e}")

    backlinks = {}
    if getattr(cfg, "backlinks_csv", ""):
        log("Reading backlink export…")
        try:
            backlinks = analyse_backlinks(
                cfg.backlinks_csv, cfg.root_host, auditor,
                brand_name=registrable(cfg.root_host).split(".")[0],
                keyword_terms={t for t, _, _ in (content or {}).get("site_keywords", [])})
        except Exception as e:
            log(f"! Could not read the backlink file: {e}")

    html_pages = [p for p in crawler.pages.values()
                  if p.status == 200 and "html" in p.content_type.lower()]
    overall, cats = score(auditor.issues, max(len(html_pages), 1))

    extras = {"links": links, "tracking": tracking, "cannibal": cannibal,
              "offpage": offpage_onsite, "speed": speed, "images": images,
              "gsc_link": gsc_link, "authority": authority, "moz": moz}
    report = build_report(cfg, crawler, auditor, psi, gsc, backlinks, overall, cats,
                          content, extras)
    report_path = os.path.join(cfg.out, "seo-report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    pages_csv, issues_csv = write_csvs(cfg.out, crawler, auditor, content, extras)

    counts = Counter(ISSUE_DEFS.get(i.code, {}).get("sev", "low") for i in auditor.issues)
    log(f"Health score: {overall}/100 (grade {grade(overall)[0]})")
    for s in SEVERITIES:
        if counts.get(s):
            log(f"  {s}: {counts[s]}")
    log(f"Finished in {time.time() - t0:.0f}s")
    return {"overall": overall, "cats": cats, "report": report_path,
            "pages_csv": pages_csv, "issues_csv": issues_csv, "counts": counts}


def make_cfg(url, **kw):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    cfg = argparse.Namespace(
        url=url, start_url=normalise(url), max_pages=250, max_depth=6, delay=0.15,
        timeout=20, threads=8, user_agent=UA, ignore_robots=False, check_external=False,
        psi_key="", psi_pages=5, gsc_csv="", backlinks_csv="", out="seo-report", quiet=True,
        brand_name=DEFAULT_BRAND["brand_name"], brand_logo="",
        brand_primary=DEFAULT_BRAND["brand_primary"],
        brand_secondary=DEFAULT_BRAND["brand_secondary"], brand_logo_light=True,
        moz_token="", moz_id="", moz_secret="", skip_psi=False)
    for k, v in kw.items():
        # An empty string from a blank form field or an unset flag must not wipe a default.
        if v == "" and k in DEFAULT_BRAND:
            continue
        setattr(cfg, k, v)
    cfg.root_host = up.urlsplit(cfg.start_url).netloc
    cfg.respect_robots = not cfg.ignore_robots
    return cfg


# ---------------------------------------------------------------------------
# Browser interface
# ---------------------------------------------------------------------------

HOME = os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv and sys.argv[0] else "."))
OUTDIR = os.path.join(HOME or ".", "seo-reports")

BRAND_FILE = os.path.join(OUTDIR, "brand.json")


def load_brand():
    try:
        with open(BRAND_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return dict(DEFAULT_BRAND)


def save_brand(d):
    try:
        os.makedirs(OUTDIR, exist_ok=True)
        with open(BRAND_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


STATE = {"running": False, "log": [], "done": False, "error": "", "dir": "", "score": None}
LOCK = threading.Lock()

UI_CSS = """
:root{--ink:#10222B;--ink-2:#3C5561;--ink-3:#6E858F;--paper:#EEF1F2;--panel:#fff;
--rule:#D2DADE;--accent:#0E6E8C;--ok:#1F7A5C;--bad:#A61B3D;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55}
.wrap{max-width:700px;margin:0 auto;padding:44px 22px 80px}
.label{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;
color:var(--ink-3);font-weight:600}
h1{font-family:var(--mono);font-size:30px;font-weight:600;letter-spacing:-.02em;margin:10px 0 4px}
.sub{color:var(--ink-2);font-size:15px;margin-bottom:30px}
.panel{background:var(--panel);border:1px solid var(--rule);padding:24px}
label.f{display:block;margin-bottom:7px}
input[type=url],input[type=number],input[type=text],input[type=file]{width:100%;font-family:var(--mono);
font-size:15px;padding:13px 14px;border:1px solid var(--rule);background:#fff;color:var(--ink)}
input[type=file]{font-size:13px;padding:10px}
input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.row{display:flex;gap:14px;margin-top:18px;flex-wrap:wrap}
.row>div{flex:1;min-width:140px}
.opts{margin-top:18px;display:flex;gap:20px;flex-wrap:wrap}
.opts label{font-size:14px;color:var(--ink-2);display:flex;align-items:center;gap:7px;cursor:pointer}
button{margin-top:24px;width:100%;font-family:var(--mono);font-size:12px;letter-spacing:.16em;
text-transform:uppercase;font-weight:600;background:var(--ink);color:#fff;border:0;padding:16px;cursor:pointer}
button:hover{background:#1b3a47}
details.adv{margin-top:20px;border-top:1px solid var(--rule);padding-top:16px}
details.adv summary{cursor:pointer;font-size:14px;color:var(--accent)}
.hint{font-size:13px;color:var(--ink-3);margin-top:7px}
pre.log{font-family:var(--mono);font-size:12.5px;background:var(--panel);border:1px solid var(--rule);
padding:16px;max-height:320px;overflow:auto;white-space:pre-wrap;color:var(--ink-2);margin-top:22px}
.done{background:var(--panel);border:1px solid var(--rule);border-left:4px solid var(--ok);padding:22px;margin-top:22px}
.done.err{border-left-color:var(--bad)}
a.btn{display:inline-block;margin:14px 10px 0 0;font-family:var(--mono);font-size:11.5px;
letter-spacing:.12em;text-transform:uppercase;background:var(--accent);color:#fff;
text-decoration:none;padding:12px 18px}
a.btn.sec{background:transparent;color:var(--accent);border:1px solid var(--rule)}
.score{font-family:var(--mono);font-size:46px;font-weight:600;letter-spacing:-.03em;line-height:1}
footer{margin-top:36px;color:var(--ink-3);font-size:12.5px;border-top:1px solid var(--rule);padding-top:14px}
.spin{display:inline-block;width:9px;height:9px;background:var(--accent);margin-right:8px;
animation:p 1s steps(2) infinite}
@keyframes p{0%{opacity:1}50%{opacity:.2}}
@media(prefers-reduced-motion:reduce){.spin{animation:none}}
"""


def ui_page(body_html, title="SEO audit", refresh=False):
    meta = '<meta http-equiv="refresh" content="2">' if refresh else ""
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>" + html_mod.escape(title) + "</title>" + meta +
            "<style>" + UI_CSS + "</style></head><body><div class=\"wrap\">" +
            body_html + "</div></body></html>")


FORM_TEMPLATE = """
<span class="label">Website auditor</span>
<h1>Audit a website</h1>
<div class="sub">Paste the address and press the button. Everything runs on this computer.</div>
<form method="post" action="/run" enctype="multipart/form-data" class="panel">
  <input type="hidden" name="csrf" value="__CSRF__">
  <label class="f label" for="url">Website address</label>
  <input id="url" name="url" type="url" placeholder="https://example.com" required autofocus>
  <div class="hint">Include https:// — audit sites you own or have permission to crawl.</div>
  <div class="row">
    <div><label class="f label" for="max">Pages to check</label>
      <input id="max" name="max_pages" type="number" value="100" min="1" max="10000"></div>
    <div><label class="f label" for="delay">Pause between pages</label>
      <input id="delay" name="delay" type="text" value="0.15"></div>
  </div>
  <div class="opts">
    <label><input type="checkbox" name="check_external" value="1"> Check outbound links</label>
    <label><input type="checkbox" name="ignore_robots" value="1"> Ignore robots.txt</label>
  </div>
  <details class="adv">
    <summary>Add rankings and backlink data (optional)</summary>
    <div class="row"><div>
      <label class="f label" for="gsc">Search Console query export (.csv)</label>
      <input id="gsc" name="gsc_csv" type="file" accept=".csv">
      <div class="hint">Search Console → Performance → Queries → Export. Adds rankings,
      striking-distance keywords and cannibalisation.</div></div></div>
    <div class="row"><div>
      <label class="f label" for="bl">Backlink export (.csv)</label>
      <input id="bl" name="backlinks_csv" type="file" accept=".csv">
      <div class="hint">Any Ahrefs, Semrush or Majestic export. Adds the off-page section.</div></div></div>
    <div class="row"><div>
      <label class="f label" for="psi">PageSpeed Insights API key</label>
      <input id="psi" name="psi_key" type="text"
             placeholder="optional — makes Core Web Vitals reliable">
      <div class="hint">Core Web Vitals are fetched without a key, but Google's free quota
      is shared and often busy. A key is free and takes two minutes.</div></div></div>
    <div class="row">
      <div><label class="f label" for="mozid">Moz access ID</label>
        <input id="mozid" name="moz_id" type="text" placeholder="optional — adds DA and PA"></div>
      <div><label class="f label" for="mozsec">Moz secret key</label>
        <input id="mozsec" name="moz_secret" type="password" placeholder="optional"></div>
    </div>
  </details>
  <details class="adv">
    <summary>Report branding</summary>
    <div class="row"><div>
      <label class="f label" for="brand">Your business name</label>
      <input id="brand" name="brand_name" type="text" value="__BRAND__"></div></div>
    <div class="row"><div>
      <label class="f label" for="logo">Logo image</label>
      <input id="logo" name="brand_logo" type="file" accept="image/*">
      <div class="hint">__LOGO_STATUS__ PNG, JPG or SVG. It's embedded in the report,
      so the file you send a client still shows it.</div>
      <div class="opts"><label><input type="checkbox" name="brand_logo_light" value="1" __LIGHTCHK__>
      Logo is white or light-coloured (sits on a dark panel)</label></div></div></div>
    <div class="row">
      <div><label class="f label" for="c1">Main brand colour</label>
        <input id="c1" name="brand_primary" type="color" value="__C1__"
               style="height:48px;padding:4px"></div>
      <div><label class="f label" for="c2">Second colour</label>
        <input id="c2" name="brand_secondary" type="color" value="__C2__"
               style="height:48px;padding:4px"></div>
    </div>
    <div class="hint">Saved for next time.</div>
  </details>
  <button type="submit">Start audit</button>
</form>
<footer>Signed in as <b>__USER__</b> · <a href="/password">Change password</a> ·
<a href="/logout">Sign out</a><br>Nothing is uploaded anywhere. The only site contacted is
the one you audit.</footer>
"""


def form_body(csrf="", user=""):
    b = load_brand()
    logo = b.get("brand_logo", "")
    status = ("Current: " + os.path.basename(logo) + " — upload a new file to replace it."
              if logo and os.path.isfile(logo) else "No logo saved yet.")
    return (FORM_TEMPLATE
            .replace("__BRAND__", html_mod.escape(b.get("brand_name", ""), quote=True))
            .replace("__LOGO_STATUS__", html_mod.escape(status))
            .replace("__C1__", html_mod.escape(b.get("brand_primary",
                                                      DEFAULT_BRAND["brand_primary"]), quote=True))
            .replace("__C2__", html_mod.escape(b.get("brand_secondary",
                                                      DEFAULT_BRAND["brand_secondary"]), quote=True))
            .replace("__LIGHTCHK__", "checked" if b.get("brand_logo_light", False) else "")
            .replace("__CSRF__", html_mod.escape(csrf, quote=True))
            .replace("__USER__", html_mod.escape(user)))


# ---------------------------------------------------------------------------
# Authentication for the browser interface
# ---------------------------------------------------------------------------
#
# Threat model, stated plainly: this server binds to 127.0.0.1, so it is not
# reachable from the network or the internet. The realistic risks are another
# user or process on the same machine reaching it, a malicious web page in your
# browser posting to it (CSRF), and someone reading the credentials file.
# Everything below targets those. Notably absent is a CAPTCHA: there is no
# public form to spam, and adding one would ship your traffic to a third party
# and break the tool offline. Rate limiting plus slow hashing covers the actual
# risk, which is someone guessing at a local prompt.

AUTH_FILE = os.path.join(OUTDIR, "auth.json")
PBKDF2_ROUNDS = 600_000          # OWASP guidance for PBKDF2-HMAC-SHA256
SESSION_HOURS = 8
MAX_FAILURES = 5
LOCKOUT_SECONDS = 900

SESSIONS = {}                    # sid -> {user, expires, csrf, ip}
FAILURES = defaultdict(lambda: {"count": 0, "until": 0.0})
AUTH_LOCK = threading.Lock()


def hash_password(password: str, salt: bytes = None, rounds: int = PBKDF2_ROUNDS):
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return salt.hex(), dk.hex(), rounds


_ENV_AUTH = None


def load_auth():
    """On a host the disk is wiped on restart, so credentials come from environment
    variables set in the dashboard instead of a file."""
    global _ENV_AUTH
    env_user = os.environ.get("SEO_USER", "").strip()
    env_pw = os.environ.get("SEO_PASSWORD", "")
    if env_user and env_pw:
        if _ENV_AUTH is None or _ENV_AUTH.get("user") != env_user:
            salt, digest, rounds = hash_password(env_pw)
            _ENV_AUTH = {"user": env_user, "salt": salt, "hash": digest,
                         "rounds": rounds, "from_env": True}
        return _ENV_AUTH
    try:
        with open(AUTH_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_auth(username: str, password: str):
    salt, digest, rounds = hash_password(password)
    data = {"user": username, "salt": salt, "hash": digest, "rounds": rounds,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    os.makedirs(OUTDIR, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        os.chmod(AUTH_FILE, 0o600)       # owner-only, so other local users can't read it
    except Exception:
        pass
    return data


def verify_password(password: str, record: dict) -> bool:
    if not record:
        return False
    try:
        _, digest, _ = hash_password(password, bytes.fromhex(record["salt"]),
                                     int(record.get("rounds", PBKDF2_ROUNDS)))
    except Exception:
        return False
    return hmac.compare_digest(digest, record.get("hash", ""))


def password_problem(pw: str, username: str = ""):
    """Rejects the passwords that actually get broken, without silly rules."""
    if len(pw) < 12:
        return "Use at least 12 characters. Length beats complexity."
    if pw.lower() in ("password1234", "administrator", "letmein12345", "qwertyuiop12"):
        return "That's one of the most guessed passwords in existence."
    if username and username.lower() in pw.lower():
        return "Don't put your username in your password."
    if len(set(pw)) < 5:
        return "Too few different characters."
    return ""


def new_session(user: str, ip: str) -> tuple:
    sid = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    with AUTH_LOCK:
        # Drop anything expired while we're here.
        now = time.time()
        for k in [k for k, v in SESSIONS.items() if v["expires"] < now]:
            SESSIONS.pop(k, None)
        SESSIONS[sid] = {"user": user, "csrf": csrf, "ip": ip,
                         "expires": now + SESSION_HOURS * 3600}
    return sid, csrf


def get_session(cookie_header: str):
    if not cookie_header:
        return None
    sid = ""
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == "sid":
            sid = v
    if not sid:
        return None
    with AUTH_LOCK:
        s = SESSIONS.get(sid)
        if not s:
            return None
        if s["expires"] < time.time():
            SESSIONS.pop(sid, None)
            return None
        return dict(s, sid=sid)


def record_failure(ip: str):
    with AUTH_LOCK:
        f = FAILURES[ip]
        f["count"] += 1
        if f["count"] >= MAX_FAILURES:
            f["until"] = time.time() + LOCKOUT_SECONDS
            f["count"] = 0


def lockout_remaining(ip: str) -> int:
    with AUTH_LOCK:
        return max(0, int(FAILURES[ip]["until"] - time.time()))


def clear_failures(ip: str):
    with AUTH_LOCK:
        FAILURES.pop(ip, None)


LOGIN_CSS_EXTRA = """
.auth{max-width:420px;margin:8vh auto 0}
.auth .panel{padding:30px}
.auth h1{font-size:24px;margin:6px 0 4px}
.auth .sub{margin-bottom:24px}
.auth input[type=text],.auth input[type=password]{margin-bottom:16px}
.msg{border-left:4px solid var(--bad);background:var(--panel);border:1px solid var(--rule);
padding:13px 16px;margin-bottom:18px;font-size:14px}
.msg.ok{border-left-color:var(--ok)}
.authlogo{max-height:40px;margin-bottom:18px;display:block}
"""


def auth_page(title, body, message="", ok=False):
    logo = f'<img class="authlogo" src="{DEFAULT_LOGO_DATA_URI}" alt="">'
    msg = f'<div class="msg{" ok" if ok else ""}">{html_mod.escape(message)}</div>' if message else ""
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html_mod.escape(title)}</title><style>{UI_CSS}{LOGIN_CSS_EXTRA}</style>'
            '</head><body><div class="wrap auth">' + logo + msg + body + '</div></body></html>')


LOGIN_FORM = """
<span class="label">Sign in</span><h1>SEO audit tool</h1>
<div class="sub">This tool is private to you.</div>
<form method="post" action="/login" class="panel">
  <label class="f label" for="u">Username</label>
  <input id="u" name="username" type="text" autocomplete="username" required autofocus>
  <label class="f label" for="p">Password</label>
  <input id="p" name="password" type="password" autocomplete="current-password" required>
  <button type="submit">Sign in</button>
</form>
"""

SETUP_FORM = """
<span class="label">First run</span><h1>Create your login</h1>
<div class="sub">Nobody can use the tool until you set this. It is stored only on this
computer, hashed — not as readable text.</div>
<form method="post" action="/setup" class="panel">
  <label class="f label" for="u">Choose a username</label>
  <input id="u" name="username" type="text" autocomplete="username" required autofocus>
  <label class="f label" for="p">Choose a password</label>
  <input id="p" name="password" type="password" autocomplete="new-password" required>
  <label class="f label" for="p2">Repeat the password</label>
  <input id="p2" name="password2" type="password" autocomplete="new-password" required>
  <div class="hint">At least 12 characters. A short phrase you'll remember beats a
  scramble you'll write on a note.</div>
  <button type="submit">Create login</button>
</form>
"""

PASSWORD_FORM = """
<span class="label">Account</span><h1>Change password</h1>
<div class="sub">You'll stay signed in on this browser.</div>
<form method="post" action="/password" class="panel">
  <input type="hidden" name="csrf" value="__CSRF__">
  <label class="f label" for="c">Current password</label>
  <input id="c" name="current" type="password" autocomplete="current-password" required autofocus>
  <label class="f label" for="p">New password</label>
  <input id="p" name="password" type="password" autocomplete="new-password" required>
  <label class="f label" for="p2">Repeat the new password</label>
  <input id="p2" name="password2" type="password" autocomplete="new-password" required>
  <button type="submit">Update password</button>
</form>
<div class="hint" style="margin-top:16px"><a href="/">Back to the tool</a></div>
"""


def parse_multipart(body: bytes, boundary: str):
    """Minimal multipart/form-data reader: {name: str or (filename, bytes)}."""
    out = {}
    sep = ("--" + boundary).encode()
    for part in body.split(sep):
        if not part.strip() or part.strip() == b"--":
            continue
        if b"\r\n\r\n" not in part:
            continue
        head, _, data = part.partition(b"\r\n\r\n")
        data = data.rstrip(b"\r\n")
        headtxt = head.decode("utf-8", "replace")
        m = re.search(r'name="([^"]*)"', headtxt)
        if not m:
            continue
        name = m.group(1)
        fm = re.search(r'filename="([^"]*)"', headtxt)
        if fm:
            if fm.group(1) and data:
                out[name] = (fm.group(1), data)
        else:
            out[name] = data.decode("utf-8", "replace").strip()
    return out


def uilog(msg):
    with LOCK:
        for line in str(msg).replace("\r", "\n").splitlines():
            if line.strip():
                STATE["log"].append(line.strip())


def audit_thread(cfg):
    with LOCK:
        STATE.update(running=True, done=False, error="", log=[], dir=cfg.out, score=None)
    try:
        res = run_audit(cfg, log=uilog)
        with LOCK:
            STATE["score"] = f"{res['overall']}/100 · grade {grade(res['overall'])[0]}"
    except Exception as e:
        with LOCK:
            STATE["error"] = str(e) if isinstance(e, RuntimeError) else traceback.format_exc(limit=3)
    finally:
        with LOCK:
            STATE["running"] = False
            STATE["done"] = True


class Handler(BaseHTTPRequestHandler):
    server_version = "SEOAudit"      # don't advertise the Python version
    sys_version = ""

    def _security_headers(self):
        # The UI and the report both use inline <style> and data: images, so the
        # policy allows those and nothing else — no remote scripts, no framing.
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; img-src 'self' data:; "
                         "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
                         "form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")

    def _send(self, body, ctype="text/html; charset=utf-8", code=200, cookie=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self._security_headers()
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            pass

    def _redirect(self, location, cookie=None):
        self.send_response(303)
        self.send_header("Location", location)
        self._security_headers()
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    @property
    def client_ip(self):
        # Behind a proxy the socket address is the proxy, so rate limiting must
        # key on the forwarded client address instead.
        fwd = self.headers.get("X-Forwarded-For", "")
        if HOSTED and fwd:
            return fwd.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "local"

    def _cookie(self, value, max_age):
        secure = "; Secure" if (
            self.headers.get("X-Forwarded-Proto", "").lower() == "https" or HOSTED) else ""
        return f"sid={value}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Strict{secure}"

    def _session(self):
        return get_session(self.headers.get("Cookie", ""))

    def _same_origin(self):
        """Block cross-site form posts even before the CSRF token is checked."""
        origin = self.headers.get("Origin") or self.headers.get("Referer") or ""
        if not origin:
            return True          # curl and similar send neither; the token still applies
        host = self.headers.get("Host", "")
        return up.urlsplit(origin).netloc == host

    def do_GET(self):
        path = self.path.split("?")[0]
        account = load_auth()

        if account is None and path != "/setup":
            return self._redirect("/setup")
        if path == "/setup":
            if account is not None:
                return self._redirect("/login")
            return self._send(auth_page("Set up", SETUP_FORM))
        if path == "/login":
            if self._session():
                return self._redirect("/")
            return self._send(auth_page("Sign in", LOGIN_FORM))
        if path == "/logout":
            s = self._session()
            if s:
                with AUTH_LOCK:
                    SESSIONS.pop(s["sid"], None)
            return self._redirect("/login",
                                  self._cookie("", 0))

        session = self._session()
        if not session:
            return self._redirect("/login")

        if path == "/password":
            return self._send(auth_page("Change password",
                                        PASSWORD_FORM.replace("__CSRF__", session["csrf"])))
        if path == "/":
            return self._send(ui_page(form_body(session["csrf"], session["user"])))
        if path == "/status":
            return self._send(self.status_page())
        downloads = {"/report": "seo-report.html", "/pages.csv": "pages.csv",
                     "/issues.csv": "issues.csv", "/headings.csv": "headings.csv",
                     "/images.csv": "images-missing-alt.csv",
                     "/links.csv": "internal-links.csv",
                     "/indexability.csv": "indexability.csv",
                     "/tracking.csv": "tracking.csv"}
        if path in downloads:
            name = downloads[path]
            fp = os.path.join(STATE["dir"], name)
            if not os.path.isfile(fp):
                return self._send(ui_page("<h1>Not ready</h1><p><a href='/status'>Back</a></p>"), code=404)
            ctype = "text/html; charset=utf-8" if name.endswith("html") else "text/csv"
            with open(fp, "rb") as f:
                return self._send(f.read(), ctype)
        self._send(ui_page("<h1>Not found</h1><p><a href='/'>Start over</a></p>"), code=404)

    def _read_form(self):
        ctype = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > 60_000_000:
            return {}
        raw = self.rfile.read(length) if length else b""
        if "multipart/form-data" in ctype and "boundary=" in ctype:
            return parse_multipart(raw, ctype.split("boundary=")[1].strip().strip('"'))
        return {k: v[0] for k, v in up.parse_qs(raw.decode("utf-8", "replace")).items()}

    def do_POST(self):
        path = self.path.split("?")[0]
        account = load_auth()

        if not self._same_origin():
            return self._send(auth_page("Blocked", "<div class='panel'>Request blocked: it did "
                                        "not come from this page.</div>"), code=403)

        # -- first-run account creation
        if path == "/setup":
            if account is not None:
                return self._redirect("/login")
            form = self._read_form()
            user = str(form.get("username", "")).strip()
            pw = str(form.get("password", ""))
            pw2 = str(form.get("password2", ""))
            if not user or len(user) < 3:
                return self._send(auth_page("Set up", SETUP_FORM, "Pick a username of at least 3 characters."))
            if pw != pw2:
                return self._send(auth_page("Set up", SETUP_FORM, "The two passwords don't match."))
            problem = password_problem(pw, user)
            if problem:
                return self._send(auth_page("Set up", SETUP_FORM, problem))
            save_auth(user, pw)
            sid, _ = new_session(user, self.client_ip)
            return self._redirect("/", self._cookie(sid, SESSION_HOURS * 3600))

        # -- login
        if path == "/login":
            wait = lockout_remaining(self.client_ip)
            if wait:
                return self._send(auth_page("Sign in", LOGIN_FORM,
                                            f"Too many failed attempts. Try again in "
                                            f"{wait // 60 + 1} minute(s)."), code=429)
            form = self._read_form()
            user = str(form.get("username", "")).strip()
            pw = str(form.get("password", ""))
            time.sleep(0.4)      # blunt the speed of repeated guesses
            ok_user = hmac.compare_digest(user, (account or {}).get("user", ""))
            if account and ok_user and verify_password(pw, account):
                clear_failures(self.client_ip)
                sid, _ = new_session(account["user"], self.client_ip)
                return self._redirect("/", f"sid={sid}; Path=/; Max-Age={SESSION_HOURS*3600}; "
                                           "HttpOnly; SameSite=Strict")
            record_failure(self.client_ip)
            return self._send(auth_page("Sign in", LOGIN_FORM,
                                        "Username or password is wrong."), code=401)

        session = self._session()
        if not session:
            return self._redirect("/login")

        form = self._read_form()
        if not hmac.compare_digest(str(form.get("csrf", "")), session["csrf"]):
            return self._send(auth_page("Blocked", "<div class='panel'>Session expired or the "
                                        "request was forged. <a href='/'>Go back</a>.</div>"),
                              code=403)

        # -- password change
        if path == "/password":
            cur = str(form.get("current", ""))
            pw = str(form.get("password", ""))
            pw2 = str(form.get("password2", ""))
            page = PASSWORD_FORM.replace("__CSRF__", session["csrf"])
            if not verify_password(cur, account):
                time.sleep(0.4)
                return self._send(auth_page("Change password", page, "Current password is wrong."))
            if pw != pw2:
                return self._send(auth_page("Change password", page, "The new passwords don't match."))
            problem = password_problem(pw, session["user"])
            if problem:
                return self._send(auth_page("Change password", page, problem))
            if (account or {}).get("from_env"):
                return self._send(auth_page("Change password", page,
                                            "This copy takes its login from environment "
                                            "variables. Change SEO_PASSWORD in your hosting "
                                            "dashboard instead."))
            save_auth(session["user"], pw)
            with AUTH_LOCK:
                for k in [k for k, v in SESSIONS.items() if k != session["sid"]]:
                    SESSIONS.pop(k, None)      # sign out every other browser
            return self._send(auth_page("Change password", page,
                                        "Password updated. Other sessions were signed out.",
                                        ok=True))

        if path != "/run":
            return self._send("", code=404)
        ctype = self.headers.get("Content-Type", "")
        if STATE["running"]:
            self.send_response(303); self.send_header("Location", "/status"); self.end_headers(); return

        url = form.get("url", "")
        if not isinstance(url, str) or not url.strip():
            return self._send(ui_page("<h1>Enter an address</h1><p><a href='/'>Back</a></p>"))

        host = "".join(c if c.isalnum() else "-" for c in up.urlsplit(
            url if "://" in url else "https://" + url).netloc)[:60] or "site"
        outdir = os.path.join(OUTDIR, host)
        os.makedirs(outdir, exist_ok=True)

        def num(key, default, cast):
            try:
                return cast(str(form.get(key, "")).strip() or default)
            except (ValueError, TypeError):
                return cast(default)

        def savefile(key):
            v = form.get(key)
            if isinstance(v, tuple):
                fp = os.path.join(outdir, "input-" + key + ".csv")
                with open(fp, "wb") as f:
                    f.write(v[1])
                return fp
            return ""

        brand = load_brand()
        if isinstance(form.get("brand_name"), str):
            brand["brand_name"] = form["brand_name"].strip()
        brand["brand_logo_light"] = bool(form.get("brand_logo_light"))
        for key in ("brand_primary", "brand_secondary"):
            if isinstance(form.get(key), str) and form[key].strip():
                brand[key] = form[key].strip()
        logo = form.get("brand_logo")
        if isinstance(logo, tuple):
            ext = os.path.splitext(logo[0])[1].lower() or ".png"
            lp = os.path.join(OUTDIR, "brand-logo" + ext)
            try:
                os.makedirs(OUTDIR, exist_ok=True)
                with open(lp, "wb") as f:
                    f.write(logo[1])
                brand["brand_logo"] = lp
            except Exception:
                pass
        save_brand(brand)

        cfg = make_cfg(url.strip(), max_pages=num("max_pages", 100, int),
                       delay=num("delay", 0.15, float), out=outdir,
                       check_external=bool(form.get("check_external")),
                       ignore_robots=bool(form.get("ignore_robots")),
                       psi_key=str(form.get("psi_key", "") or "").strip(),
                       moz_id=str(form.get("moz_id", "") or "").strip(),
                       moz_secret=str(form.get("moz_secret", "") or "").strip(),
                       gsc_csv=savefile("gsc_csv"), backlinks_csv=savefile("backlinks_csv"),
                       brand_name=brand.get("brand_name", ""),
                       brand_logo=brand.get("brand_logo", ""),
                       brand_primary=brand.get("brand_primary", ""),
                       brand_secondary=brand.get("brand_secondary", ""),
                       brand_logo_light=brand.get("brand_logo_light", True))
        threading.Thread(target=audit_thread, args=(cfg,), daemon=True).start()
        self.send_response(303)
        self.send_header("Location", "/status")
        self.end_headers()

    def status_page(self):
        with LOCK:
            running, done, err = STATE["running"], STATE["done"], STATE["error"]
            logtext = "\n".join(STATE["log"][-200:]) or "Starting…"
            score = STATE["score"]
            outdir = STATE["dir"]
        pre = '<pre class="log">' + html_mod.escape(logtext) + "</pre>"
        if running or not done:
            return ui_page(
                '<span class="label">In progress</span><h1>Checking the site…</h1>'
                '<div class="sub"><span class="spin"></span>This page updates itself. '
                'A hundred pages takes a minute or two.</div>' + pre,
                "Auditing…", refresh=True)
        if err:
            return ui_page(
                '<span class="label">Stopped</span><h1>The audit stopped</h1>'
                '<div class="done err">' + html_mod.escape(err)[:600] +
                '<div><a class="btn sec" href="/">Try again</a></div></div>' + pre,
                "Stopped")
        head = ('<div class="label">Health score</div><div class="score">' +
                html_mod.escape(score or "") + "</div>") if score else "<b>Finished.</b>"
        box = ('<div class="done">' + head +
               '<div><a class="btn" href="/report" target="_blank">Open the report</a></div>'
               '<div class="label" style="margin-top:18px">Spreadsheets</div><div>'
               '<a class="btn sec" href="/issues.csv">issues</a>'
               '<a class="btn sec" href="/pages.csv">pages</a>'
               '<a class="btn sec" href="/indexability.csv">indexability</a>'
               '<a class="btn sec" href="/headings.csv">headings</a>'
               '<a class="btn sec" href="/images.csv">missing alt</a>'
               '<a class="btn sec" href="/links.csv">internal links</a>'
               '<a class="btn sec" href="/tracking.csv">tracking</a></div>'
               '<div class="hint">Saved in ' + html_mod.escape(outdir) + "</div></div>")
        return ui_page('<span class="label">Complete</span><h1>Audit finished</h1>' + box + pre +
                       '<footer><a href="/">Audit another site</a></footer>', "Finished")

    def log_message(self, *a):
        pass


def free_port(start=8756):
    for p in range(start, start + 40):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start


def serve():
    os.makedirs(OUTDIR, exist_ok=True)
    if HOSTED:
        port = int(os.environ["PORT"])
        bind = "0.0.0.0"                     # the host's proxy needs to reach us
        url = os.environ.get("PUBLIC_URL", f"http://0.0.0.0:{port}/")
    else:
        port = free_port()
        bind = "127.0.0.1"                   # local only: nothing else can connect
        url = f"http://127.0.0.1:{port}/"
    server = ThreadingHTTPServer((bind, port), Handler)
    if HOSTED:
        acct = load_auth()
        if not acct:
            print("  WARNING: set SEO_USER and SEO_PASSWORD environment variables, "
                  "or anyone who finds this URL can create the first account.", flush=True)
        print(f"  SEO audit tool listening on port {port} (hosted mode).", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return
    account = load_auth()
    print("\n  SEO audit tool is running.\n"
          + ("  First run — the page will ask you to create a username and password.\n"
             if not account else f"  Sign in as: {account['user']}\n")
          + f"  If your browser didn't open, go to:  {url}\n"
          f"  Reports are saved in: {OUTDIR}\n"
          "  Leave this window open. Press Ctrl+C here when you're done.\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("  Stopped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if argv and argv[0] == "--set-password":
        # Recovery path: run this from a terminal if the password is forgotten.
        import getpass
        acct = load_auth()
        user = (acct or {}).get("user", "") or input("Username: ").strip()
        pw = getpass.getpass("New password: ")
        if pw != getpass.getpass("Repeat: "):
            sys.exit("  Passwords don't match.")
        problem = password_problem(pw, user)
        if problem:
            sys.exit("  " + problem)
        save_auth(user, pw)
        with AUTH_LOCK:
            SESSIONS.clear()
        print(f"  Password updated for {user}.")
        return 0

    if not argv:
        serve()
        return 0

    ap = argparse.ArgumentParser(
        description="SEO audit: technical, on-page, content, links, structured data, "
                    "Core Web Vitals, rankings and backlinks. Run with no arguments "
                    "to open the browser interface instead.")
    ap.add_argument("url")
    ap.add_argument("--max-pages", type=int, default=250)
    ap.add_argument("--max-depth", type=int, default=6)
    ap.add_argument("--delay", type=float, default=0.15)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--user-agent", default=UA)
    ap.add_argument("--ignore-robots", action="store_true")
    ap.add_argument("--check-external", action="store_true")
    ap.add_argument("--psi-key", default="")
    ap.add_argument("--psi-pages", type=int, default=5)
    ap.add_argument("--skip-psi", action="store_true",
                    help="don't call Google for Core Web Vitals")
    ap.add_argument("--moz-token", default="", help="Moz Links API token (for DA/PA)")
    ap.add_argument("--moz-id", default="", help="Moz access ID")
    ap.add_argument("--moz-secret", default="", help="Moz secret key")
    ap.add_argument("--gsc-csv", default="")
    ap.add_argument("--backlinks-csv", default="")
    ap.add_argument("--brand-name", default="", help="name shown on the report")
    ap.add_argument("--brand-logo", default="", help="path to a logo image")
    ap.add_argument("--brand-primary", default="", help="main brand colour, e.g. #1A73E8")
    ap.add_argument("--brand-secondary", default="", help="secondary brand colour")
    ap.add_argument("--light-logo", action="store_true",
                    help="your logo is white or light, so place it on a dark panel")
    ap.add_argument("-o", "--out", default="seo-report")
    ap.add_argument("-q", "--quiet", action="store_true")
    a = ap.parse_args(argv)

    cfg = make_cfg(a.url, max_pages=a.max_pages, max_depth=a.max_depth, delay=a.delay,
                   timeout=a.timeout, threads=a.threads, user_agent=a.user_agent,
                   ignore_robots=a.ignore_robots, check_external=a.check_external,
                   psi_key=a.psi_key, psi_pages=a.psi_pages, gsc_csv=a.gsc_csv,
                   backlinks_csv=a.backlinks_csv, out=a.out, quiet=a.quiet,
                   brand_name=a.brand_name, brand_logo=a.brand_logo,
                   brand_primary=a.brand_primary, brand_secondary=a.brand_secondary,
                   brand_logo_light=a.light_logo, skip_psi=a.skip_psi,
                   moz_token=a.moz_token, moz_id=a.moz_id, moz_secret=a.moz_secret)
    try:
        res = run_audit(cfg, log=lambda m: None if a.quiet else print("  " + str(m), file=sys.stderr))
    except RuntimeError as e:
        sys.exit(f"\n  {e}\n")
    print(res["report"])
    print(res["pages_csv"])
    print(res["issues_csv"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
