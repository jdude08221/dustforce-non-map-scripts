import asyncio
import os
import argparse
from playwright.async_api import async_playwright

AUTH_FILE = "auth.json"

async def ensure_auth_file(p):
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://atlas.dustforce.com/login")
    print("Please log in manually, then press Enter here...")
    input()
    await context.storage_state(path=AUTH_FILE)
    await browser.close()

async def process_urls(urls):
    async with async_playwright() as p:
        if not os.path.exists(AUTH_FILE):
            await ensure_auth_file(p)
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=AUTH_FILE)
        except Exception as e:
            print(f"Failed to load {AUTH_FILE}: {e}")
            print("Running login flow...")
            await ensure_auth_file(p)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=AUTH_FILE)

        page = await context.new_page()
        for url in urls:
            url = url.strip()
            if not url or not url.startswith("http"):
                continue
            print(f"Visiting: {url}")
            await page.goto(url)
            if await page.query_selector('input.button-links[value="reshow"]'):
                await page.click('input.button-links[value="reshow"]')
                print("Map Unhidden!")
            else:
                print("Can not find reshow button, map may already be visible or URL is invalid.")
        await browser.close()

def read_urls_from_file(filename):
    with open(filename, "r") as f:
        return f.readlines()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Press reshow button on Dustforce Atlas URLs.")
    parser.add_argument("urlfile", help="Path to text file with newline-separated URLs")
    args = parser.parse_args()
    urls = read_urls_from_file(args.urlfile)
    asyncio.run(process_urls(urls))