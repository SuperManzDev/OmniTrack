import os
import time
import asyncio
from typing import List, Optional
from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "google_messages_profile")
TARGET_CONVERSATION_URL = "https://messages.google.com/web/conversations/CghWnaLob5T8LhICMTM"

class GoogleMessagesDispatcher:
    def __init__(self, user_data_dir: str = USER_DATA_DIR, conversation_url: str = TARGET_CONVERSATION_URL):
        self.user_data_dir = user_data_dir
        self.conversation_url = conversation_url

    async def send_messages_to_adiran(self, messages: List[str]):
        print(f"[Google Messages] Opening ADIRAN chat: {self.conversation_url} ...")
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                channel="chrome",
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                await page.goto(self.conversation_url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for textarea input
                msg_input = page.locator('textarea[placeholder*="Text message"], textarea[aria-label*="Text message"], textarea, div[contenteditable="true"]').first
                await msg_input.wait_for(state="visible", timeout=20000)

                for msg in messages:
                    await msg_input.click()
                    await page.wait_for_timeout(300)
                    
                    # Fill text
                    await msg_input.fill(msg)
                    await page.wait_for_timeout(600)
                    
                    # Send
                    send_btn = page.locator('button[aria-label*="Send" i], button[data-e2e*="send" i], mws-message-send-button button').first
                    if await send_btn.is_visible():
                        await send_btn.click()
                    else:
                        await page.keyboard.press("Enter")
                        
                    await page.wait_for_timeout(1500)
                    print("[Google Messages] Sent text message to ADIRAN!")

            finally:
                await context.close()

    async def send_sms_to_chat(self, target_name: str, messages: List[str]):
        await self.send_messages_to_adiran(messages)

    def send_to_adiran(self, messages: List[str]):
        asyncio.run(self.send_messages_to_adiran(messages))
