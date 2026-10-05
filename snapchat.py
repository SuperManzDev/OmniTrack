import os
import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright
from config import config

class SnapchatAuthExpiredError(Exception):
    pass

class SnapchatDispatcher:
    def __init__(self, auth_file: str = config.snap_auth_path):
        self.auth_file = auth_file

    def has_auth(self) -> bool:
        return os.path.exists(self.auth_file)

    async def auto_login(self, username: str = "mnzbot", password: str = "Zimmer@1218"):
        print("\n=== Performing Automated Snapchat Login ===")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--enable-webgl",
                    "--enable-accelerated-2d-canvas",
                    "--no-sandbox"
                ]
            )
            context = await browser.new_context(
                permissions=["camera", "microphone", "notifications", "clipboard-read", "clipboard-write"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            
            await page.goto("https://www.snapchat.com", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Enter username
            user_input = page.locator('input[type="text"]').first
            await user_input.fill(username)
            await page.locator('button:has-text("Log in"), button[type="submit"]').first.click()
            await page.wait_for_timeout(3000)
            
            # Enter password
            pass_input = page.locator('input[type="password"]').first
            await pass_input.fill(password)
            await page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Log In")').first.click()
            await page.wait_for_timeout(5000)
            
            # Dismiss intro dialogs
            for _ in range(3):
                btn = page.locator('button:has-text("Next"), button:has-text("Get Started"), button:has-text("Skip")').first
                if await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    
            await page.wait_for_timeout(3000)
            await context.storage_state(path=self.auth_file)
            print(f"[SUCCESS] Saved authenticated session to {self.auth_file}!")
            await browser.close()

    async def send_group_message(self, group_name: str, message: str, mention_user: Optional[str] = None):
        return await self.send_group_messages(group_name, [message], mention_user=mention_user)

    async def send_group_messages(self, group_name: str, messages: List[str], mention_user: Optional[str] = None):
        if not self.has_auth():
            await self.auto_login()

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--enable-webgl",
                    "--enable-accelerated-2d-canvas",
                    "--no-sandbox"
                ]
            )
            context = await browser.new_context(
                storage_state=self.auth_file,
                permissions=["camera", "microphone", "notifications", "clipboard-read", "clipboard-write"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            try:
                await page.goto("https://web.snapchat.com", wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(3000)
            except Exception:
                pass

            # Dismiss modals if any appear
            for _ in range(3):
                btn = page.locator('button:has-text("Next"), button:has-text("Get Started"), button:has-text("Skip")').first
                if await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(1500)

            # Check if redirected to login
            if "accounts.snapchat.com" in page.url.lower():
                print("[Warning] Session expired. Attempting auto-login...")
                await browser.close()
                await self.auto_login()
                return await self.send_group_messages(group_name, messages, mention_user)

            # Find group chat
            try:
                chat_group = page.locator(f'text="{group_name}"').first
                await chat_group.wait_for(timeout=10000)
                await chat_group.click()
                await page.wait_for_timeout(1500)
            except Exception as e:
                await browser.close()
                raise RuntimeError(f"Could not locate group chat '{group_name}': {e}")

            # Locate chat box
            try:
                input_box = page.locator('div[contenteditable="true"], div[role="textbox"]').last
                await input_box.wait_for(timeout=6000)
            except Exception as e:
                await browser.close()
                raise RuntimeError(f"Could not locate chat input box: {e}")

            clean_user = (mention_user or "").lstrip("@")

            # Send all messages in sequence
            for idx, message in enumerate(messages):
                await input_box.click()
                
                # Create True Blue Mention Chip via Downshift keyboard navigation
                if clean_user:
                    await page.keyboard.type(f"@{clean_user}", delay=80)
                    await asyncio.sleep(0.7)
                    await page.keyboard.press("ArrowDown")
                    await asyncio.sleep(0.2)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.3)
                    await page.keyboard.down("Shift")
                    await page.keyboard.press("Enter")
                    await page.keyboard.up("Shift")

                # Insert message lines cleanly
                lines = message.split("\n")
                for i, line in enumerate(lines):
                    if line.strip():
                        await page.evaluate("(text) => document.execCommand('insertText', false, text)", line)
                    if i < len(lines) - 1:
                        await page.keyboard.down("Shift")
                        await page.keyboard.press("Enter")
                        await page.keyboard.up("Shift")

                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.8)

            await asyncio.sleep(1)
            await context.storage_state(path=self.auth_file)
            await browser.close()
            print(f"[Snapchat] Successfully dispatched {len(messages)} message(s) with TRUE mention chip to '{group_name}'!")
