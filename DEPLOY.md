# Publishing this tool and getting a live URL

Two separate things happen here, and it helps to know that before you start:

- **GitHub** stores your code and gives you a page you can share.
- **A hosting service** actually runs the tool and gives you a live web address.

GitHub alone can't run it. GitHub Pages only serves fixed files — HTML, CSS, images. This
tool is a Python program that crawls websites, so it needs somewhere that runs Python.
Both steps below are free.

---

# Part 1 — Put the code on GitHub

No commands. Everything is done in your browser.

### 1. Make a GitHub account

Go to [github.com](https://github.com) and sign up. Free.

### 2. Create a repository

Click the **+** in the top right → **New repository**.

- **Repository name:** `seo-audit-tool`
- **Description:** *Full-site SEO auditor by B My Marketer*
- Choose **Public** (anyone can see the code) or **Private** (only you). Both work.
- Leave every checkbox unticked.
- Click **Create repository**.

### 3. Upload the files

On the next page click **uploading an existing file**.

Drag in all seven files:

```
seo_tool.py        the tool itself
README.md          the front page people see
USAGE.md           full instructions
DEPLOY.md          this guide
LICENSE            permission to use it
requirements.txt   tells hosts there's nothing to install
render.yaml        deployment settings
Dockerfile         for hosts that use containers
.gitignore         keeps reports and passwords out of the repo
```

Scroll down, click **Commit changes**.

Done. Your code lives at `github.com/YOUR-USERNAME/seo-audit-tool`, and anyone can
download it there.

> **Never commit your passwords.** `.gitignore` already excludes `auth.json` and `.env`.
> Keep it that way — anything you commit to a public repo is public forever, even if you
> delete it later.

---

# Part 2 — Get a live URL

We'll use **Render**. Free tier, connects straight to GitHub, gives you HTTPS
automatically, and no card required.

### 1. Sign up

Go to [render.com](https://render.com) → **Get Started** → **Sign in with GitHub**.
Authorise it to read your repositories.

### 2. Create the service

- Click **New +** → **Web Service**.
- Find `seo-audit-tool` in the list and click **Connect**.
- Render reads `render.yaml` and fills most of this in. Confirm:
  - **Runtime:** Python 3
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `python seo_tool.py`
  - **Instance Type:** **Free**

### 3. Set your login — do not skip this

Scroll to **Environment Variables** and add two:

| Key | Value |
|---|---|
| `SEO_USER` | a username you choose |
| `SEO_PASSWORD` | a strong password, at least 12 characters |

This matters more than it looks. Hosted servers wipe their disk every restart, so a
password saved inside the app would disappear and the tool would offer account setup to
whoever loaded the page next. Environment variables survive restarts, so your login stays
put.

Pick a real password. This URL is on the open internet.

### 4. Deploy

Click **Create Web Service**. First build takes 2–3 minutes. When the log shows
`SEO audit tool listening on port...`, you're live.

Your URL appears at the top of the page:

```
https://seo-audit-tool-XXXX.onrender.com
```

Open it, sign in with the username and password you set, and audit a site.

---

## Things to expect on the free tier

**It sleeps.** After 15 minutes of no traffic, Render shuts the service down. The next
visit takes 30–60 seconds to wake up. It looks broken; it isn't. Just wait.

**Keep crawls small.** Free instances get 512MB of memory. Stay at or under 100 pages.
Bigger crawls may be killed halfway.

**Reports don't persist.** When the service sleeps or restarts, saved reports are wiped.
Download the HTML and CSVs when the audit finishes — they're yours forever, but only if
you save them.

**Branding settings reset too.** The logo and colours are built into the code, so those
always survive. Only per-run overrides are lost.

If you want reports to stick around and no cold starts, Render's paid tier is around $7 a
month. For occasional client audits, free is genuinely fine.

---

## Other free hosts

| Host | Notes |
|---|---|
| **Render** | Recommended. Simplest GitHub connection, `render.yaml` already included. |
| **Hugging Face Spaces** | Also free and doesn't sleep as aggressively. Create a Space, choose **Docker**, upload the same files — the `Dockerfile` is ready. Set `SEO_USER` and `SEO_PASSWORD` under Settings → Secrets. |
| **Fly.io** | Generous free allowance, needs a card on file, more command-line work. |
| **Railway** | Clean interface, free credit runs out monthly. |
| **PythonAnywhere** | **Won't work.** Its free tier only allows outbound connections to a whitelist of sites, so the crawler can't reach client websites. |

---

## Security once it's public

The moment this has a public URL, it's a different risk from a tool on your laptop.
Hosted mode turns on protections automatically:

- **Login required** on every page, credentials taken from environment variables.
- **Private networks blocked.** A crawler on a public server could otherwise be pointed at
  the host's own internal services and cloud metadata endpoints. Hosted mode refuses any
  address that resolves to a private, loopback or link-local IP.
- **Secure cookies**, since Render terminates HTTPS for you.
- **Lockout keyed to the real visitor**, read from the proxy's forwarded address rather
  than the proxy itself.

Worth doing yourself:

1. **Use a strong password.** Everything else rests on that.
2. **Consider a private repo** if you'd rather not publish the code.
3. **Watch your usage.** If you notice audits you didn't start, change `SEO_PASSWORD` in
   the Render dashboard — it takes effect on the next restart.
4. **Don't share the URL casually.** Anyone with the address plus your login can crawl any
   site through your server, and that traffic carries your host's fingerprint.

## Updating the tool later

Edit `seo_tool.py` on GitHub (open it, click the pencil icon, commit), or upload a new
version the same way you did the first time. Render redeploys automatically within a
minute or two. Nothing else to do.
