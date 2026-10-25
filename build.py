#!/usr/bin/env python3
"""Day1 Startup Media — tiny static-site generator (no dependencies).

Reads content/articles/*.md (front-matter + Markdown body) and writes the
whole site into ./site/ . Run:  python3 build.py
Settings live in config.json (site URL, WhatsApp number, socials).
"""
import html, json, os, re, shutil, sys
from datetime import datetime, timezone
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, "config.json")))
OUT = os.path.join(ROOT, "docs")  # GitHub Pages serves this folder (main branch, /docs)
BASE = CFG["site_url"].rstrip("/")
CATEGORIES = ["Funding", "Launch", "Founder Story", "Local Business"]
esc = html.escape


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------------------------------------------------------------- content
def parse_front_matter(text, path):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        sys.exit(f"ERROR: {path} has no --- front-matter --- block")
    meta = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip().lower()] = v
    tags = meta.get("tags", "").strip("[]")
    meta["tags"] = [t.strip().strip("\"'") for t in tags.split(",") if t.strip()]
    return meta, m.group(2)


def inline(s):
    s = esc(s, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def markdown(md):
    """Small Markdown subset: ## headings, paragraphs, - / 1. lists, > quotes,
    **bold**, *italic*, [links](url), ![img](url)."""
    out, para, lst, ltype = [], [], [], None

    def flush():
        nonlocal para, lst, ltype
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []
        if lst:
            out.append(f"<{ltype}>" + "".join(f"<li>{inline(i)}</li>" for i in lst) + f"</{ltype}>")
            lst, ltype = [], None

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            flush(); continue
        if re.match(r"^</?(div|section|figure|iframe|video|img|br|hr)\b.*>$", line):
            flush(); out.append(line); continue  # raw HTML line passes through
        h = re.match(r"^(#{2,4})\s+(.*)", line)
        if h:
            flush(); n = len(h.group(1)); out.append(f"<h{n}>{inline(h.group(2))}</h{n}>"); continue
        if line.startswith(">"):
            flush(); out.append("<blockquote>" + inline(line.lstrip("> ")) + "</blockquote>"); continue
        ul = re.match(r"^[-*]\s+(.*)", line); ol = re.match(r"^\d+[.)]\s+(.*)", line)
        if ul or ol:
            if para: flush()
            t = "ul" if ul else "ol"
            if ltype and ltype != t: flush()
            ltype = t; lst.append((ul or ol).group(1)); continue
        if lst: flush()
        para.append(line)
    flush()
    return "\n".join(out)


def load_articles():
    d = os.path.join(ROOT, "content", "articles")
    arts = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        meta, body = parse_front_matter(open(os.path.join(d, fn), encoding="utf-8").read(), fn)
        if meta.get("draft", "").lower() in ("true", "yes", "1"):
            continue
        for req in ("title", "date"):
            if not meta.get(req):
                sys.exit(f"ERROR: {fn} is missing '{req}'")
        meta["slug"] = meta.get("slug") or slugify(meta["title"])
        meta["category"] = meta.get("category") or "Launch"
        meta["author"] = meta.get("author") or CFG["site_name"]
        meta["dt"] = datetime.strptime(meta["date"][:10], "%Y-%m-%d")
        meta["body_html"] = markdown(body)
        words = len(re.findall(r"\w+", body))
        meta["read_min"] = max(1, -(-words // 200))
        meta["featured"] = meta.get("featured", "").lower() in ("true", "yes", "1")
        img = meta.get("image", "")
        meta["image_url"] = ("/" + img.lstrip("/")) if img else "/static/img/og-default.jpg"
        arts.append(meta)
    arts.sort(key=lambda a: (a["dt"], a.get("time", "")), reverse=True)
    return arts


def draft_images():
    """Cover paths of draft articles (draft: true). Their covers stay in content/images but are NOT copied to site/."""
    d = os.path.join(ROOT, "content", "articles"); out = set()
    for fn in os.listdir(d):
        if fn.endswith(".md"):
            meta, _ = parse_front_matter(open(os.path.join(d, fn), encoding="utf-8").read(), fn)
            if meta.get("draft", "").lower() in ("true", "yes", "1") and meta.get("image"):
                out.add(meta["image"].lstrip("/"))
    return out


# ---------------------------------------------------------------- templates
def fmt_date(dt):
    return dt.strftime("%-d %b %Y")


def wa_link(text):
    from urllib.parse import quote
    return f"https://wa.me/{CFG['whatsapp_number']}?text={quote(text)}"


SOCIAL_PATHS = json.load(open(os.path.join(ROOT, "static", "icons", "social-paths.json")))


def short_path(d):
    """Round SVG path numbers to 2 decimals (invisible at icon size, saves publish bytes)."""
    def r(m):
        s = m.group(0)
        if "." not in s or len(s.split(".")[1]) <= 2:
            return s
        v = f"{float(s):.2f}".rstrip("0")
        v = v + "0" if v.endswith(".") else v
        return v.replace("0.", ".", 1) if v.startswith("0.") else v.replace("-0.", "-.", 1)
    return re.sub(r"-?\d*\.\d+", r, d)


def social_icons(cls="socials"):
    """Row of social icon buttons from config.json "socials"."""
    out = []
    for sct in CFG.get("socials", []):
        d = short_path(SOCIAL_PATHS.get(sct["icon"], ""))
        out.append(f'<a class="si si-{sct["icon"]}" href="{esc(sct["url"])}" target="_blank" rel="noopener" '
                   f'aria-label="{esc(CFG["site_name"])} on {esc(sct["name"])}" title="{esc(sct["name"])}">'
                   f'<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false"><path fill="currentColor" d="{d}"/></svg></a>')
    return f'<div class="{cls}">' + "".join(out) + "</div>" if out else ""


def follow_block():
    if not CFG.get("socials"):
        return ""
    return f"""<section class="follow"><div><h2>Follow Day1 Startup Media</h2><p>Watch our startup-story videos on Instagram, Facebook, LinkedIn, Threads, X and YouTube.</p></div>{social_icons("socials big")}</section>"""


def org_ld():
    return json.dumps({"@context": "https://schema.org", "@type": "Organization", "name": CFG["site_name"],
                       "url": BASE + "/", "logo": BASE + "/static/img/logo.png",
                       "sameAs": [x["url"] for x in CFG.get("socials", [])]})


def page(title, desc, path, body, image="/static/img/og-default.jpg", og_type="website", extra_head=""):
    url = BASE + path
    full_title = title if title == CFG["site_name"] else f"{title} | {CFG['site_name']}"
    img = BASE + image
    cats = "".join(f'<a href="/category/{slugify(c)}/">{esc(c)}</a>' for c in CATEGORIES)
    year = datetime.now().year
    return f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{esc(CFG['site_name'])}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="{'675' if '/images/' in image else '630'}">
<meta property="og:locale" content="en_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{img}">
<meta name="theme-color" content="#0b0b0b">
<link rel="icon" href="/static/img/icon.png">
<link rel="apple-touch-icon" href="/static/img/icon.png">
<link rel="alternate" type="application/rss+xml" title="{esc(CFG['site_name'])}" href="/rss.xml">
<link rel="stylesheet" href="/static/style.css?v={CFG.get('css_version','1')}">
<script type="application/ld+json">{org_ld()}</script>
{extra_head}
</head>
<body translate="no" class="notranslate">
<header class="top">
  <div class="wrap top-in">
    <a class="brand" translate="no" href="/" aria-label="{esc(CFG['site_name'])} home"><img src="/static/img/logo.png" alt="Day1 logo" width="62" height="40"><span>Startup<b>Media</b></span></a>
    <nav class="mainnav"><a href="/">News</a><a href="/trending/">Trending</a><a href="/about/">About</a><a class="srch" href="/search/" aria-label="Search"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></a><a class="btn-feature" href="/post-your-story/">Post your story</a></nav>
  </div>
  <nav class="catbar"><div class="wrap"><a class="tr" href="/trending/">Trending</a>{cats}</div></nav>
</header>
<main class="wrap">
{body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <div><img src="/static/img/logo.png" alt="Day1 logo" width="93" height="60"><p>{esc(CFG['tagline'])}</p></div>
    <div class="foot-follow"><b>Follow us</b>{social_icons()}</div>
    <div class="foot-links"><a href="/">Latest news</a><a href="/about/">About us</a><a href="/post-your-story/">Post your story</a><a href="/rss.xml">RSS feed</a><a class="wfl" href="{CFG['whatsapp_channel']}" target="_blank" rel="noopener">WhatsApp Channel</a></div>
  </div>
  <div class="wrap copy">© {year} {esc(CFG['site_name'])}</div>
</footer>
</body>
</html>
"""


def card(a, cls="card"):
    city = f'<span class="city">{esc(a["city"])}</span>' if a.get("city") else ""
    return f"""<article class="{cls}">
  <a class="card-img" href="/news/{a['slug']}/"><img src="{a['image_url']}" alt="{esc(a['title'])}" loading="lazy"></a>
  <div class="card-body">
    <div class="meta"><a class="cat" href="/category/{slugify(a['category'])}/">{esc(a['category'])}</a>{city}</div>
    <h3><a href="/news/{a['slug']}/">{esc(a['title'])}</a></h3>
    <p>{esc(a.get('summary',''))}</p>
    <div class="date">{fmt_date(a['dt'])} · {a['read_min']} min read</div>
  </div>
</article>"""


def chips(active):
    out = [f'<a class="chip{" on" if active == "All" else ""}" href="/">All</a>']
    for c in CATEGORIES:
        out.append(f'<a class="chip{" on" if active == c else ""}" href="/category/{slugify(c)}/">{esc(c)}</a>')
    return '<div class="chips">' + "".join(out) + "</div>"


def feature_cta():
    return f"""<section class="cta">
  <div><h2>Building something new?</h2><p>Share your startup's story with Day1 Startup Media. Fill in a short form and our team will get back to you on WhatsApp.</p></div>
  <a class="btn" href="/post-your-story/">Post your story →</a>
</section>"""


def chart_html(ts):
    def mins(v):
        h, m = v.split(":")
        return int(h) * 60 + int(m)
    items = ts.get("items", [])
    top = max((mins(v) for _, v in items), default=1)
    bars = "".join(
        f'<div class="bar"><span class="bl">{esc(n)}</span><span class="bt"><i style="width:{mins(v) / top * 100:.1f}%"></i></span>'
        f'<span class="bv">{int(v.split(":")[0])}h {int(v.split(":")[1])}m</span></div>' for n, v in items)
    return f"""<div class="pl-chart">
   <h2><span aria-hidden="true">📊</span> Where Indians spend time online <small>hrs/week</small></h2>
   <div class="bars" role="img" aria-label="{esc(ts.get("title",""))}: {esc("; ".join(f"{n} {v}" for n, v in items))}">{bars}</div>
   <p class="psrc">Source: <a href="{esc(ts.get("source_url",""))}" target="_blank" rel="noopener nofollow">{esc(ts.get("source_short",""))}</a>. {esc(ts.get("note",""))}</p>
  </div>""" if items else ""


def pulse_block():
    """Homepage "India Pulse": trending topics (content/pulse.json -> trends, refresh with
    refresh_pulse.py) + a CSS bar chart of weekly time spent online (pulse.json -> time_spent)."""
    p = os.path.join(ROOT, "content", "pulse.json")
    if not os.path.exists(p):
        return ""
    d = json.load(open(p))
    tr, ts = d.get("trends") or {}, d.get("time_spent") or {}
    chips = ""
    for it in tr.get("items", []):
        cls = "biz" if it.get("category") in ("Business", "Tech", "Auto") else ""
        vol = esc(it.get("volume", ""))
        small = f"<small>{vol} searches</small>" if vol else ""
        tip = esc(f"{it.get('category', '')} · {it.get('volume', '')} searches in 24 h".strip(" ·"))
        chips += (f'<li><a class="{cls}" href="{esc(it["url"])}" target="_blank" rel="noopener nofollow" '
                  f'title="{tip}">{esc(it["label"])}{small}</a></li>')
    trend_part = f"""<div class="pl-trend">
   <h2><span aria-hidden="true">🔥</span> Trending in India today<small>Google searches, last 24 h</small></h2>
   <ul class="tchips">{chips}</ul>
   <p class="psrc">Updated {esc(tr.get("updated_ist",""))} · Source: <a href="{esc(tr.get("source_url",""))}" target="_blank" rel="noopener nofollow">{esc(tr.get("source","Google Trends"))}</a></p>
  </div>""" if chips else ""
    chart_part = chart_html(ts)
    return f"""<section class="pulse" aria-label="India Pulse">
 <div class="pl-head"><span class="pl-tag"><i></i>India Pulse</span></div>
 <div class="pl-grid">{trend_part}{chart_part}</div>
</section>"""


def home(arts):
    if not arts:
        return page(CFG["site_name"], CFG["description"], "/", "<p>No stories yet.</p>")
    feat = next((a for a in arts if a["featured"]), arts[0])
    rest = [a for a in arts if a is not feat]
    city = f' · {esc(feat["city"])}' if feat.get("city") else ""
    hero = f"""<section class="hero">
  <a class="hero-img" href="/news/{feat['slug']}/"><img src="{feat['image_url']}" alt="{esc(feat['title'])}"></a>
  <div class="hero-body">
    <span class="kicker">Top story · {esc(feat['category'])}{city}</span>
    <h1><a href="/news/{feat['slug']}/">{esc(feat['title'])}</a></h1>
    <p>{esc(feat.get('summary',''))}</p>
    <div class="date">{fmt_date(feat['dt'])} · {feat['read_min']} min read</div>
  </div>
</section>"""
    grid = "".join(card(a) for a in rest)
    body = f"""{pulse_block()}
{hero}
{follow_block()}
<h2 class="section-title">Latest startup news</h2>
{chips('All')}
<section class="grid">{grid}</section>
{feature_cta()}"""
    return page(CFG["site_name"], CFG["description"], "/", body)


def category_page(cat, arts):
    sel = [a for a in arts if a["category"].lower() == cat.lower()]
    grid = "".join(card(a) for a in sel) or '<p class="empty">No stories in this category yet. Check back soon.</p>'
    body = f"""<h1 class="page-title">{esc(cat)}</h1>
{chips(cat)}
<section class="grid">{grid}</section>
{feature_cta()}"""
    return page(f"{cat} news", f"{cat} stories about new Indian startups from {CFG['site_name']}.", f"/category/{slugify(cat)}/", body)


def article_page(a, arts):
    from urllib.parse import quote
    url = f"{BASE}/news/{a['slug']}/"
    t = quote(a["title"], safe=""); u = quote(url, safe="")
    share = f"""<div class="share"><span>Share</span>
  <a class="s-sh" href="#" data-share role="button">Share</a>
  <a class="s-wa" href="https://wa.me/?text={quote(a['title'] + ' ' + url, safe="")}" target="_blank" rel="noopener">WhatsApp</a>
  <a class="s-x" href="https://x.com/intent/post?text={t}&amp;url={u}" target="_blank" rel="noopener">X</a>
  <a class="s-li" href="https://www.linkedin.com/sharing/share-offsite/?url={u}" target="_blank" rel="noopener">LinkedIn</a>
  <a class="s-fb" href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Facebook</a>
  <a class="s-ig" href="#" data-igstory role="button">Instagram Story</a>
</div>"""
    tagset = set(x.lower() for x in a["tags"])
    others = [o for o in arts if o is not a]
    others.sort(key=lambda o: (o["category"] == a["category"], len(tagset & set(x.lower() for x in o["tags"])), o["dt"]), reverse=True)
    related = "".join(card(o, "card small") for o in others[3:6])
    readnext = '<nav class="rn"><b>Read next</b>' + "".join(f'<a href="/news/{o["slug"]}/">{esc(o["title"])}</a>' for o in others[:3]) + '</nav>'
    wachan = f'<div class="wac"><p>Get every new startup story on WhatsApp.</p><a class="wab" href="{CFG["whatsapp_channel"]}" target="_blank" rel="noopener">Join our WhatsApp Channel</a></div>'
    tags = "".join(f'<span class="tag">#{esc(x)}</span>' for x in a["tags"])
    city = f'<span class="city">{esc(a["city"])}</span>' if a.get("city") else ""
    cap = f'<figcaption>{esc(a["image_caption"])}</figcaption>' if a.get("image_caption") else ""
    ld = json.dumps({"@context": "https://schema.org", "@type": "NewsArticle", "headline": a["title"],
                     "datePublished": a["dt"].strftime("%Y-%m-%d"), "image": [BASE + a["image_url"]],
                     "author": {"@type": "Organization", "name": a["author"]},
                     "publisher": {"@type": "Organization", "name": CFG["site_name"]},
                     "description": a.get("summary", "")})
    body = f"""<article class="post">
  <div class="meta"><a class="cat" href="/category/{slugify(a['category'])}/">{esc(a['category'])}</a>{city}</div>
  <h1 translate="yes">{esc(a['title'])}</h1>
  <p class="dek" translate="yes">{esc(a.get('summary',''))}</p>
  <div class="byline">By <b>{esc(a['author'])}</b> · {fmt_date(a['dt'])} · {a['read_min']} min read</div>
  {LANG_SEL}
  <figure class="cover"><img src="{a['image_url']}" alt="{esc(a['title'])}">{cap}</figure>
  {share}
  <div class="body" translate="yes">{a['body_html']}</div>
  <div class="tags">{tags}</div>
  {wachan}
  {share}
  {readnext}
</article>
{feature_cta()}
<section class="related"><h2 class="section-title">Related stories</h2><div class="grid">{related}</div></section>"""
    head = f'<meta property="article:published_time" content="{a["dt"].strftime("%Y-%m-%d")}">\n<script type="application/ld+json">{ld}</script>\n<script src="/static/js/igstory.js?v={CFG.get("css_version","1")}" defer></script>'
    return page(a["title"], a.get("summary") or a["title"], f"/news/{a['slug']}/", body, image=a["image_url"], og_type="article", extra_head=head)


def static_md_page(name):
    meta, body = parse_front_matter(open(os.path.join(ROOT, "content", "pages", name + ".md"), encoding="utf-8").read(), name)
    html_body = markdown(body)
    btn = f'<a class="btn wa" href="{wa_link(CFG["whatsapp_message"])}" target="_blank" rel="noopener">Post your story on WhatsApp</a>'
    html_body = html_body.replace("<p>{{FOLLOW_US}}</p>", follow_block()).replace("{{FOLLOW_US}}", follow_block())
    html_body = html_body.replace("<p>{{WHATSAPP_BUTTON}}</p>", btn).replace("{{WHATSAPP_BUTTON}}", btn)
    if "{{FEATURE_FORM}}" in html_body:
        html_body = html_body.replace("<p>{{FEATURE_FORM}}</p>", feature_form()).replace("{{FEATURE_FORM}}", feature_form())
    body = f'<article class="post static"><h1>{esc(meta["title"])}</h1><div class="body">{html_body}</div></article>'
    return page(meta["title"], meta.get("summary", CFG["description"]), f"/{meta['slug']}/", body)


FEATURE_FIELDS = [("f", "Founder name", "Founder name", "input"), ("s", "Startup name", "Startup name", "input"),
                  ("c", "City", "City", "input"), ("l", "Website / Instagram link", "Link", "input"),
                  ("w", "What does your startup do? (1-2 lines)", "What it does", "textarea"), ("p", "Phone / WhatsApp number", "Phone/WhatsApp", "tel")]


def feature_form():
    """Lead form on /post-your-story/: no backend, builds a WhatsApp message to CFG whatsapp_number (JS inline, ~0.6 KB)."""
    rows = []
    for n, lab, key, kind in FEATURE_FIELDS:
        if kind == "textarea":
            ctl = f'<textarea id="{n}" name="{n}" data-k="{key}" rows="2" maxlength="240" required></textarea>'
        else:
            typ = ' type="tel" inputmode="tel"' if kind == "tel" else ""
            ctl = f'<input id="{n}" name="{n}" data-k="{key}"{typ} required>'
        rows.append(f'<label for="{n}">{lab} *</label>{ctl}')
    opts = "".join(f"<option>{o}</option>" for o in ["Bootstrapped", "Pre-seed", "Seed", "Series A+"])
    rows.append(f'<label for="g">Funding stage (optional)</label><select id="g" name="g" data-k="Funding stage"><option value="">Select</option>{opts}</select>')
    js = ("document.getElementById('ff').onsubmit=function(e){e.preventDefault();var ok=1,m='*Feature request: Day1 Startup Media*\\n';"
          "this.querySelectorAll('[name]').forEach(function(x){var v=x.value.trim();x.classList.remove('bad');"
          "if(x.required&&!v||x.name=='p'&&v.replace(/\\D/g,'').length<10){x.classList.add('bad');ok=0}"
          "else if(v)m+='\\n*'+x.dataset.k+':* '+v.replace(/\\s+/g,' ')});"
          "var r=document.getElementById('fe');if(!ok){r.textContent='Please fill in the fields marked in red (phone: at least 10 digits).';"
          "this.querySelector('.bad').focus();return}r.textContent='';"
          f"location.href='https://wa.me/{CFG['whatsapp_number']}?text='+encodeURIComponent(m)}}")
    return f"""<ul class="fp"><li><b>Article</b> on your startup and founder journey</li><li><b>Instagram reel</b> promotion on Day1's pages</li><li><b>WhatsApp</b> chat with our team, no long process</li></ul>
<form id="ff" class="ff" novalidate>{"".join(rows)}
<p id="fe" class="err" role="alert"></p><button type="submit">Send on WhatsApp →</button>
<p class="fnote">WhatsApp opens with your message ready. Just press Send.</p></form>
<script>{js}</script>"""


def rss(arts):
    items = []
    for a in arts[:30]:
        url = f"{BASE}/news/{a['slug']}/"
        pub = format_datetime(a["dt"].replace(hour=9, tzinfo=timezone.utc))
        items.append(f"""<item><title>{esc(a['title'])}</title><link>{url}</link><guid>{url}</guid><pubDate>{pub}</pubDate><category>{esc(a['category'])}</category><description>{esc(a.get('summary',''))}</description><enclosure url="{BASE}{a['image_url']}" type="image/jpeg" length="0"/></item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{esc(CFG['site_name'])}</title><link>{BASE}/</link><description>{esc(CFG['description'])}</description><language>en-in</language>
{''.join(items)}
</channel></rss>
"""


def sitemap(arts):
    urls = [("/", None), ("/trending/", None), ("/search/", None), ("/about/", None), ("/post-your-story/", None)]
    urls += [(f"/category/{slugify(c)}/", None) for c in CATEGORIES]
    urls += [(f"/news/{a['slug']}/", a["dt"].strftime("%Y-%m-%d")) for a in arts]
    body = "".join(f"<url><loc>{BASE}{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n'


def trending_page(arts):
    """/trending/: full India Pulse trend list + time-spent chart + 5 newest Day1 stories (no analytics, so not "most read")."""
    p = os.path.join(ROOT, "content", "pulse.json")
    d = json.load(open(p)) if os.path.exists(p) else {}
    tr, ts = d.get("trends") or {}, d.get("time_spent") or {}
    rows = "".join(
        f'<li><a href="{esc(it["url"])}" target="_blank" rel="noopener nofollow"><b>{esc(it["label"])}</b>'
        f'<small>{esc(it.get("category", ""))}{" · " + esc(it["volume"]) + " searches" if it.get("volume") else ""}</small></a></li>'
        for it in tr.get("items", []))
    trend = f"""<div class="pl-trend"><h2><span aria-hidden="true">🔥</span> Trending in India today<small>Google searches, last 24 h</small></h2>
<ol class="tlist">{rows}</ol>
<p class="psrc">Updated {esc(tr.get("updated_ist",""))} · Source: <a href="{esc(tr.get("source_url",""))}" target="_blank" rel="noopener nofollow">{esc(tr.get("source","Google Trends"))}</a></p></div>""" if rows else ""
    latest = "".join(sres(a) for a in arts[:5])
    body = f"""<h1 class="page-title">Trending</h1>
<section class="pulse" aria-label="Trending in India"><div class="pl-grid">{trend}{chart_html(ts)}</div></section>
<h2 class="section-title">Latest on Day1</h2>
<div class="slist">{latest}</div>
<p class="more"><a href="/">All startup news →</a></p>"""
    return page("Trending in India today", "What India is searching for right now, where Indians spend their time online, and the latest startup stories on Day1.", "/trending/", body)


def sres(a):
    return (f'<a class="sres" href="/news/{a["slug"]}/"><img src="{a["image_url"]}" alt="" loading="lazy" width="96" height="54">'
            f'<span><em>{esc(a["category"])} · {fmt_date(a["dt"])}</em><b>{esc(a["title"])}</b></span></a>')


# Article "Read in" selector: opens the page through Google Translate's website proxy (JS at end of static/js/igstory.js)
LANGS = [('en', 'English'), ('hi', 'हिन्दी (Hindi)'), ('bn', 'বাংলা (Bengali)'), ('mr', 'मराठी (Marathi)'), ('te', 'తెలుగు (Telugu)'), ('ta', 'தமிழ் (Tamil)'), ('gu', 'ગુજરાતી (Gujarati)'), ('ur', 'اردو (Urdu)'), ('kn', 'ಕನ್ನಡ (Kannada)'), ('ml', 'മലയാളം (Malayalam)'), ('pa', 'ਪੰਜਾਬੀ (Punjabi)')]
LANG_SEL = '<div class="lang"><label for="lg">🌐 Read in</label><select id="lg" translate="no"><option value="en">English</option></select></div>'  # other options added by JS from LANGS order below


SEARCH_CHIPS = [("All", ""), ("Funding", "Funding"), ("Startup Stories", "Founder Story|Local Business"), ("Launches", "Launch")]


def search_page():
    chips = "".join(f'<button type="button" data-c="{c}"{" class=on" if not c else ""}>{n}</button>' for n, c in SEARCH_CHIPS)
    body = f"""<h1 class="page-title">Search</h1>
<form class="sbox" role="search" action="/search/" onsubmit="return false"><input id="q" name="q" type="search" placeholder="Startup name, funding, city…" autocomplete="off" aria-label="Search stories" autofocus></form>
<div class="chips schips">{chips}</div>
<div id="sr" class="slist" aria-live="polite"></div>
<script src="/static/js/search.js?v={CFG.get('css_version','1')}" defer></script>"""
    return page("Search", "Search Day1 Startup Media: startup names, funding rounds, launches and founder stories.", "/search/", body)


def search_json(arts):
    """Compact index of PUBLISHED articles only (load_articles already skips draft: true)."""
    return json.dumps([{"t": a["title"], "s": (a.get("summary") or "")[:160], "c": a["category"],
                        "g": " ".join(a["tags"] + [a.get("city") or ""]).strip(), "u": a["slug"], "i": a["image_url"], "d": fmt_date(a["dt"])}
                       for a in arts], ensure_ascii=False, separators=(",", ":"))


def write(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if rel.endswith(".html"):  # light minify: drop indentation and blank lines (no <pre> on this site)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{2,}", "\n", text)
    open(p, "w", encoding="utf-8").write(text)


def main():
    arts = load_articles()
    slugs = [a["slug"] for a in arts]
    dup = {s for s in slugs if slugs.count(s) > 1}
    if dup:
        sys.exit(f"ERROR: duplicate slugs: {dup}")
    for a in arts:
        if a.get("image") and not os.path.exists(os.path.join(ROOT, "content", a["image"].lstrip("/"))):
            sys.exit(f"ERROR: {a['slug']}: image not found: content/{a['image'].lstrip('/')}")
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, "static"), os.path.join(OUT, "static"))
    shutil.copytree(os.path.join(ROOT, "content", "images"), os.path.join(OUT, "images"))
    live_imgs = {a.get("image", "").lstrip("/") for a in arts}
    for img in draft_images() - live_imgs:  # draft covers stay unpublished
        p = os.path.join(OUT, img)
        if os.path.exists(p):
            os.remove(p)
    write("index.html", home(arts))
    for a in arts:
        write(f"news/{a['slug']}/index.html", article_page(a, arts))
    for c in CATEGORIES:
        write(f"category/{slugify(c)}/index.html", category_page(c, arts))
    write("trending/index.html", trending_page(arts))
    write("search/index.html", search_page())
    write("search.json", search_json(arts))
    write("about/index.html", static_md_page("about"))
    write("post-your-story/index.html", static_md_page("post-your-story"))
    # old URLs keep working: /feature/ (Oct 24 lead form, merged into /post-your-story/) and /feature-your-startup/ are tiny redirects
    for old in ("feature", "feature-your-startup"):
        write(f"{old}/index.html", f'<!doctype html><meta charset="utf-8"><title>Post your story</title><link rel="canonical" href="{BASE}/post-your-story/"><meta http-equiv="refresh" content="0;url=/post-your-story/"><a href="/post-your-story/">Post your story</a>\n')
    write("404.html", page("Page not found", CFG["description"], "/404.html", '<div class="post static"><h1>Page not found</h1><p><a href="/">Back to the latest startup news →</a></p></div>'))
    write("rss.xml", rss(arts))
    write("sitemap.xml", sitemap(arts))
    write(".nojekyll", "")  # GitHub Pages: serve files as they are, no Jekyll
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    print(f"Built {len(arts)} articles -> {OUT}")
    for a in arts:
        print(f"  {a['dt']:%Y-%m-%d}  {a['category']:<14} {BASE}/news/{a['slug']}/")


if __name__ == "__main__":
    main()
