#!/usr/bin/env python3
"""Create a new article (Markdown + 1200x675 cover) for Day1 Startup Media.

python3 new_article.py --title "..." --body-file body.md --image photo.jpg \
    --city Patna --category Launch --tags "rentals,patna" --summary "One line"

Writes content/articles/<date>-<slug>.md and content/images/<slug>.jpg.
Then run: python3 build.py   (and publish).
Any image shape works: vertical reel frames get a blurred-fill 16:9 cover.
Needs Pillow only (python3 -c "import PIL").
"""
import argparse, os, re, sys
from datetime import date, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CATS = ["Funding", "Launch", "Founder Story", "Local Business"]


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:70].strip("-")


def make_cover(src, out, W=1200, H=675):
    from PIL import Image, ImageFilter, ImageOps
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    r = im.width / im.height
    if abs(r - W / H) < 0.12 or r > W / H:  # landscape-ish: centre crop
        canvas = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.4))
    else:  # portrait: blurred background + whole image centred
        canvas = ImageOps.fit(im, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        canvas = Image.blend(canvas, Image.new("RGB", (W, H), (0, 0, 0)), 0.35)
        fg_h = H; fg_w = round(fg_h * r)
        fg = im.resize((fg_w, fg_h), Image.LANCZOS)
        canvas.paste(fg, ((W - fg_w) // 2, 0))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.save(out, "JPEG", quality=84, optimize=True, progressive=True)


def q(s):
    return '"' + s.replace('"', "'") + '"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--body-file", help="Markdown body file (no front-matter)")
    g.add_argument("--body", help="Markdown body as a string")
    ap.add_argument("--image", help="any jpg/png; becomes the 16:9 cover")
    ap.add_argument("--city", default="")
    ap.add_argument("--category", default="Launch", choices=CATS)
    ap.add_argument("--tags", default="", help="comma separated")
    ap.add_argument("--summary", default="", help="1-2 sentences; used on cards + share previews")
    ap.add_argument("--slug")
    ap.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD")
    ap.add_argument("--caption", default="", help="optional image caption/credit")
    ap.add_argument("--featured", action="store_true", help="pin as the homepage top story")
    ap.add_argument("--force", action="store_true", help="overwrite an existing article with the same slug")
    a = ap.parse_args()

    slug = a.slug or slugify(a.title)
    body = open(a.body_file, encoding="utf-8").read() if a.body_file else a.body
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", body, flags=re.S).strip() + "\n"
    adir = os.path.join(ROOT, "content", "articles")
    existing = [f for f in os.listdir(adir) if re.search(rf"(^|\d-){re.escape(slug)}\.md$", f)]
    if existing and not a.force:
        sys.exit(f"ERROR: an article with slug '{slug}' exists: {existing}. Use --slug or --force.")
    for f in existing:
        os.remove(os.path.join(adir, f))
    img_rel = ""
    if a.image:
        img_rel = f"images/{slug}.jpg"
        make_cover(a.image, os.path.join(ROOT, "content", img_rel))
    summary = a.summary or re.sub(r"[*#>\[\]()]", "", body.strip().split("\n\n")[0])[:180]
    fm = ["---", f"title: {q(a.title)}", f"slug: {slug}", f"date: {a.date}", f"time: {datetime.now().strftime('%H:%M')}", f"city: {a.city}",
          f"category: {a.category}", f"tags: [{', '.join(t.strip() for t in a.tags.split(',') if t.strip())}]",
          f"image: {img_rel}", f"image_caption: {q(a.caption)}", f"summary: {q(summary)}",
          "author: Day1 Startup Media", f"featured: {'true' if a.featured else 'false'}", "---", ""]
    path = os.path.join(adir, f"{a.date}-{slug}.md")
    open(path, "w", encoding="utf-8").write("\n".join(fm) + body)
    print(f"Wrote {path}")
    if img_rel:
        print(f"Cover  {os.path.join(ROOT, 'content', img_rel)}")
    print(f"URL after build + git push: https://day1startupmedia.github.io/news/{slug}/")


if __name__ == "__main__":
    main()
