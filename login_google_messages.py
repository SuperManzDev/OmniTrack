import os
import time
import asyncio
from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "google_messages_profile")

async def open_login_window():
    print("=" * 60)
    print(" Google Messages for Web - Device Pairing")
    print("=" * 60)
    print("1. Opening Google Messages window on your screen...")
    print("2. Make sure 'Remember this computer' switch is ON.")
    print("3. Open Google Messages on your Android phone -> Tap Profile -> 'Device pairing' -> Scan QR code.")
    print("4. Once your conversations load, you can close the window.")
    print("=" * 60)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1050, "height": 800},
            args=["--no-sandbox"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://messages.google.com/web/authentication")

        print("\nWaiting for you to pair your phone (window will stay open)...")
        while True:
            await asyncio.sleep(2)
            if "conversations" in page.url:
                print("\n[SUCCESS] Google Messages paired successfully! Session saved.")
                await asyncio.sleep(3)
                break

        await context.close()

if __name__ == "__main__":
    asyncio.run(open_login_window())
