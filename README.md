# Day1 Startup Media

Website: https://day1startupmedia.github.io/

Ye Day1 Startup Media ki website hai. Ye GitHub Pages pe free chalti hai.
`docs/` folder hi live website hai. Usko haath se edit mat karna, wo `build.py` se banta hai.

## Naya article kaise post hota hai

### Sabse aasaan tareeka
Tab ko WhatsApp pe bhejo:
1. Startup ka naam aur city
2. Startup ke baare mein jo bhi info hai (ya unka link)
3. Ek photo (founder, logo ya reel ka screenshot)

Tab article likh ke, photo laga ke, website pe daal dega aur tumhe link bhej dega.

### Khud karna ho (computer se)
1. Article ka text ek `.md` file mein likho (jaise `body.md`).
2. Article banao (photo se cover apne aap ban jaata hai):
   ```
   python3 new_article.py --title "Startup ka title" --body-file body.md --image photo.jpg \
     --city Patna --category Launch --tags "naam,city" --summary "1-2 line ka summary"
   ```
   Category inme se ek: `Funding`, `Launch`, `Founder Story`, `Local Business`
3. Website banao: `python3 build.py`
4. GitHub pe bhejo:
   ```
   git add -A
   git commit -m "Naya article"
   git push
   ```
5. 1-2 minute mein article live: `https://day1startupmedia.github.io/news/<article-ka-naam>/`

## Kya kahan hai
- `content/articles/` : saare articles (har article ek `.md` file)
- `content/images/` : article ki cover photos
- `content/pages/` : About aur "Post your story" page
- `config.json` : site ka naam, WhatsApp number, Instagram/Facebook links
- `docs/` : bani hui website (ye live hoti hai)

## Article chhupana ho (delete kiye bina)
Article ki file mein upar `draft: true` likh do, phir step 3 aur 4.
