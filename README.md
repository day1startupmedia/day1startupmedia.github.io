# Day1 Startup Media

Website: https://day1startupmedia.github.io/
Admin (phone se article daalo): https://day1startupmedia.github.io/admin/

Ye Day1 Startup Media ki website hai. Ye GitHub Pages pe free chalti hai.

## Phone se naya article kaise daalein

1. Phone pe ye kholo: day1startupmedia.github.io/admin
2. "Sign in with GitHub" dabao aur apne day1startupmedia GitHub account se login karo (agar GitHub "Authorize" pooche to Authorize dabao).
3. "Articles" kholo, phir upar wala green "+" button dabao (naya article).
4. Title, Date, Category bharo. "Cover photo" mein "Upload" dabake photo chuno (koi bhi photo/screenshot chalega). Summary (1-2 line) aur Tags bharo, aur neeche "Article" box mein poori khabar likho.
5. Upar right wala green Save button dabao.
6. Bas! Lagbhag 2 minute mein article website pe live: day1startupmedia.github.io

Badlaav ya delete: Articles list mein article pe tap karo, badlo, Save. Delete ke liye article ke aage "..." button > Delete. Article chhupana ho to "Hide from website (draft)" on kar do.

Ya phir Tab ko WhatsApp pe startup ka naam, info/link aur ek photo bhej do, Tab article bana ke daal dega.

## Ye kaise chalta hai (technical)
- Editor: Pages CMS (app.pagescms.org). Settings `.pages.yml` mein hain. Pages CMS sirf is ek repo pe install hai.
- Har Save ek commit hai `main` pe. Har push pe `.github/workflows/build.yml` chalta hai: Python + PyYAML + Pillow install, `python build.py`, aur `docs/` GitHub Pages pe deploy (Settings > Pages > Source: GitHub Actions). Build ~30 sec, live ~1-2 min.
- Cover photo: CMS se upload hui photo `content/images/` mein waise hi rehti hai; build usse 1200x675 JPEG cover banata hai (`new_article.py` wala crop/blur) sirf website ke liye.
- `docs/` ab git mein nahi hai, wo har build pe naya banta hai.

## Computer se (optional)
```
pip install pyyaml pillow
python3 new_article.py --title "Startup ka title" --body-file body.md --image photo.jpg \
  --city Patna --category Launch --tags "naam,city" --summary "1-2 line ka summary"
python3 build.py        # local preview: docs/ folder
git add -A && git commit -m "Naya article" && git push   # GitHub khud build + live karega
```
Category inme se ek: `Funding`, `Launch`, `Founder Story`, `Local Business`

## Kya kahan hai
- `content/articles/` : saare articles (har article ek `.md` file, upar YAML front-matter)
- `content/images/` : article ki photos
- `content/pages/` : About aur "Post your story" page
- `config.json` : site ka naam, WhatsApp number, Instagram/Facebook links
- `.pages.yml` : phone editor (Pages CMS) ki settings
- `.github/workflows/build.yml` : auto-build + deploy
