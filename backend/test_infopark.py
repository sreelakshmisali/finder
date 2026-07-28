import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://infopark.in/companies-job")
        
        # Wait for the job listings to load
        await page.wait_for_timeout(5000) 
        
        content = await page.content()
        with open("infopark_rendered.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Length of rendered HTML:", len(content))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
