#!/usr/bin/env python3
"""Refresh the homepage "India Pulse" trending list from Google Trends (India, last 24 hours).

    python3 refresh_pulse.py && python3 build.py
then publish (see HOW_TO_POST.md). Only content/pulse.json -> "trends" is changed;
the time-spent chart ("time_spent") is fixed, sourced data and is never touched here.

Source: the data behind https://trends.google.com/trending?geo=IN (falls back to the
official RSS feed https://trends.google.com/trending/rss?geo=IN if that fails).
Business / tech / auto topics go first, then the biggest topics overall.
"""
import html, json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
PULSE = os.path.join(ROOT, "content", "pulse.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
MAX_ITEMS, MAX_BIZ = 8, 5
BIZ_CATS = {3: "Business", 18: "Tech", 1: "Auto"}           # Google Trends category ids
CAT_NAMES = {3: "Business", 18: "Tech", 1: "Auto", 17: "Sports", 4: "Entertainment", 16: "Shopping",
             7: "Health", 10: "Govt", 11: "Politics", 9: "Jobs & Education", 8: "Festivals", 19: "Travel", 20: "Weather"}
NOISE = [r"\bnational cricket team\b", r"\bnational football team\b", r"\btimeline\b", r"\bmatch scorecard\b"]
UPPER = {"ipo", "gmp", "iit", "ai", "sbi", "rbi", "lic", "nz", "ind", "ufc", "gst", "us", "uk", "ipl", "bse", "nse",
         "upi", "isro", "tcs", "hdfc", "icici", "idbi", "ssc", "upsc", "dazn", "wi", "afg", "zim", "sa", "eng", "aus"}
BRANDS = {"sonyliv": "SonyLIV", "jiohotstar": "JioHotstar", "youtube": "YouTube", "chatgpt": "ChatGPT",
          "openai": "OpenAI", "linkedin": "LinkedIn", "whatsapp": "WhatsApp", "phonepe": "PhonePe", "paytm": "Paytm",
          "oneplus": "OnePlus", "coloros": "ColorOS", "iqoo": "iQOO", "macbook": "MacBook", "ipad": "iPad"}
STOP = {"live", "today", "news", "rate", "price", "with", "from", "india", "indian", "match", "score", "date"}
# One-word searches that are too generic to mean anything as a headline on their own ("Bank", "Suv").
GENERIC = {"bank", "banks", "suv", "car", "cars", "bike", "gold", "silver", "weather", "rain", "holiday", "school",
           "college", "result", "results", "exam", "news", "market", "stock", "stocks", "share", "shares", "petrol",
           "diesel", "train", "flight", "mobile", "phone", "laptop", "tv", "ott", "movie", "song", "video", "game",
           "cricket", "football", "ipo", "loan", "tax", "salary", "job", "jobs", "sale", "offer", "app", "online"}
MIN_SOLO_VOLUME = 20000   # a lone one-word topic needs at least this many searches to be shown as is


def clean_label(t):
    t = html.unescape(t).strip()
    for n in NOISE:
        t = re.sub(n, " ", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    if t.isascii() and t == t.lower():
        t = " ".join(w.upper() if w in UPPER else w if w in ("vs", "of", "and", "in") else w[:1].upper() + w[1:]
                     for w in t.split())
    t = re.sub(r"\bi ?phone\b", "iPhone", t, flags=re.I)
    for k, v in BRANDS.items():
        t = re.sub(rf"\b{k}\b", v, t, flags=re.I)
    return t


def short(n):
    if n >= 1_000_000: return f"{n // 1_000_000}M+"
    if n >= 1000: return f"{n // 1000}K+"
    return f"{n}+"


def from_trends_page():
    freq = json.dumps([[["i0OFE", json.dumps([None, None, "IN", 0, "en-IN", 24, 1]), None, "generic"]]])
    req = urllib.request.Request("https://trends.google.com/_/TrendsUi/data/batchexecute",
                                 data=urllib.parse.urlencode({"f.req": freq}).encode(),
                                 headers={**UA, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
    raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    rows = json.loads(json.loads(raw.split("\n", 2)[2])[0][2])[1]
    out = []
    for r in rows:
        if r[5] is not None:      # trend has ended
            continue
        related = [q for q in (r[9] or []) if isinstance(q, str)] if len(r) > 9 else []
        out.append({"query": r[0], "volume": int(r[6] or 0), "cats": list(r[10] or []), "related": related})
    return out


def from_rss():
    req = urllib.request.Request("https://trends.google.com/trending/rss?geo=IN", headers=UA)
    xml = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    out = []
    for b in re.findall(r"<item>(.*?)</item>", xml, re.S):
        q = html.unescape(re.search(r"<title>(.*?)</title>", b, re.S).group(1))
        v = re.search(r"approx_traffic>([\d,]+)", b)
        out.append({"query": q, "volume": int(v.group(1).replace(",", "")) if v else 0, "cats": []})
    return out


def keywords(label):
    return {w for w in re.findall(r"[a-z]{4,}", label.lower()) if w not in STOP}


def better_title(r):
    """Return the search to show for a trend, or None to skip it.
    Multi-word trends are kept as they are. A one-word trend ("nta", "bank") is swapped for the
    first specific multi-word search Google lists under it ("jee mains 2027 registration");
    with none, it is kept only if it is a big, non-generic topic (a name), else dropped."""
    q = r["query"].strip()
    if len(q.split()) > 1:
        return q
    for rel in r.get("related") or []:
        rel = rel.strip()
        low = rel.lower()
        if (rel.isascii() and 2 <= len(rel.split()) <= 7 and low != q.lower()
                and not any(re.search(n, low) for n in NOISE)
                and not re.search(r"\b(tomorrow|today|yesterday|holiday|near me|kya hai|meaning)\b", low)):
            return rel
    if q.lower() in GENERIC or r["volume"] < MIN_SOLO_VOLUME:
        return None
    return q


def pick(rows):
    rows = [r for r in rows if r["query"].isascii()]      # site is in English
    rows = [dict(r, query=t) for r in rows for t in [better_title(r)] if t]
    rows.sort(key=lambda r: (-r["volume"], len(r["query"])))
    chosen, seen = [], []
    def add(r):
        label = clean_label(r["query"])
        kw = keywords(label)
        if not label or any(label.lower() == s[0] or (kw and kw & s[1]) for s in seen):
            return False
        seen.append((label.lower(), kw))
        cat = next((CAT_NAMES[c] for c in r["cats"] if c in CAT_NAMES), "")
        chosen.append({"label": label, "query": r["query"], "volume": short(r["volume"]) if r["volume"] else "",
                       "category": cat,
                       "url": "https://news.google.com/search?" + urllib.parse.urlencode(
                           {"q": r["query"], "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})})
        return True
    for r in rows:
        if len(chosen) >= MAX_BIZ:
            break
        if set(r["cats"]) & set(BIZ_CATS):
            add(r)
    per_cat = {}
    for r in rows:                         # biggest topics overall, max 2 per category
        if len(chosen) >= MAX_ITEMS:
            break
        c = r["cats"][0] if r["cats"] else None
        if c is not None and per_cat.get(c, 0) >= 2:
            continue
        if add(r):
            per_cat[c] = per_cat.get(c, 0) + 1
    return chosen


def main():
    # Any failure below exits non-zero BEFORE pulse.json is written, so a blocked or broken source
    # (e.g. Google answering 403/429 to a cloud server) keeps the previous list on the site.
    try:
        rows, via = from_trends_page(), "trending page"
        if len(rows) < 20:
            raise ValueError(f"only {len(rows)} trends came back")
    except Exception as e:
        print(f"trending page failed ({e}); using the RSS feed")
        try:
            rows, via = from_rss(), "rss"
        except Exception as e2:
            sys.exit(f"ERROR: could not fetch Google Trends: {e2} (pulse.json left unchanged)")
    items = pick(rows)
    if len(items) < 3:
        sys.exit(f"ERROR: only {len(items)} usable topics (pulse.json left unchanged)")
    data = json.load(open(PULSE)) if os.path.exists(PULSE) else {}
    old = (data.get("trends") or {}).get("items") or []
    if [(i.get("label"), i.get("volume")) for i in old] == [(i["label"], i["volume"]) for i in items]:
        print("Same list as last time; pulse.json left unchanged.")
        return
    ist = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30)))
    data["trends"] = {
        "updated_ist": ist.strftime("%-d %b %Y, %-I:%M %p IST"),
        "updated_iso": ist.isoformat(timespec="minutes"),
        "source": "Google Trends", "source_url": "https://trends.google.com/trending?geo=IN&hours=24",
        "fetched_via": via, "items": items,
    }
    json.dump(data, open(PULSE, "w"), ensure_ascii=False, indent=1)
    print(f"Updated content/pulse.json at {data['trends']['updated_ist']} (via {via}):")
    for it in items:
        print(f"  {it['volume']:>6}  {it['category']:<13} {it['label']}")


if __name__ == "__main__":
    main()
