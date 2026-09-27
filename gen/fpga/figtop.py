import asyncio, os, pathlib, sys
from playwright.async_api import async_playwright
async def main():
    d=sys.argv[1]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for w in (1440, 1024):
            for pg in ('arty-z7-20.html','cora-z7-07s.html','de25-nano.html'):
                page=await b.new_page(viewport={'width':w,'height':900})
                await page.goto(pathlib.Path(d, pg).resolve().as_uri()); await page.evaluate('document.fonts.ready'); await page.wait_for_timeout(200)
                r=await page.evaluate('''()=>{const f=document.querySelector("figure.fig");const l=document.querySelector(".lede");const lh=parseFloat(getComputedStyle(l).lineHeight);return [f.getBoundingClientRect().top, l.getBoundingClientRect().height, lh]}''')
                print(w, pg, 'figure top', round(r[0],1), 'lede height', round(r[1],1), 'line', r[2])
                await page.close()
        await b.close()
asyncio.run(main())
