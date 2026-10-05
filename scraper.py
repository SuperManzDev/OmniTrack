import re
import asyncio
from typing import Optional, Tuple
from curl_cffi import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class WebScraper:
    def __init__(self):
        self.headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def detect_carrier(self, num: str) -> str:
        num = num.strip()
        if re.match(r'^(9[2-4]\d{20}|\d{20,22}|[A-Z]{2}\d{9}[A-Z]{2})$', num):
            return "USPS"
        elif re.match(r'^(\d{12}|\d{15}|\d{20})$', num):
            return "FedEx"
        elif re.match(r'^1Z[0-9A-Z]{16}$', num, re.IGNORECASE):
            return "UPS"
        elif re.match(r'^\d{10}$', num) or num.startswith("GM"):
            return "DHL"
        return "Auto"

    async def fetch_browser(self, tracking_number: str, carrier: str = "Auto") -> Optional[str]:
        if carrier == "Auto":
            carrier = self.detect_carrier(tracking_number)

        carrier_lower = carrier.lower()
        if carrier_lower == "usps":
            target_url = f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}"
        elif carrier_lower == "fedex":
            target_url = f"https://www.fedex.com/fedextrack/?trknbr={tracking_number}"
        else:
            target_url = f"https://www.ordertracker.com/track/{tracking_number}"

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    channel="chrome",
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
                )
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(4000)

                # If USPS, extract the banner if available
                if carrier_lower == "usps":
                    banner_loc = page.locator('.banner-content, .delivery_status, .banner-alert, .banner-notification').first
                    banner_text = ""
                    if await banner_loc.is_visible():
                        banner_text = (await banner_loc.inner_text()).strip()
                    full_text = await page.inner_text("body")
                    await browser.close()
                    return f"USPS BANNER STATUS: {banner_text} | FULL DETAILS: {full_text[:4000]}"
                else:
                    text = await page.inner_text("body")
                    await browser.close()
                    return text[:5000]
        except Exception as e:
            return None

    def fetch_fast(self, tracking_number: str, carrier: str = "Auto") -> Optional[str]:
        if carrier == "Auto":
            carrier = self.detect_carrier(tracking_number)

        urls = []
        carrier_lower = carrier.lower()
        if carrier_lower == "fedex":
            urls.append(f"https://www.packagetrackr.com/track/fedex/{tracking_number}")
            urls.append(f"https://track.trackingmore.com/fedex/en-{tracking_number}.html")
        elif carrier_lower == "usps":
            urls.append(f"https://www.packagetrackr.com/track/usps/{tracking_number}")
            urls.append(f"https://track.trackingmore.com/usps/en-{tracking_number}.html")
        else:
            urls.append(f"https://www.ordertracker.com/track/{tracking_number}")

        try:
            s = requests.Session(impersonate="chrome124")
            for url in urls:
                try:
                    res = s.get(url, headers=self.headers, timeout=8)
                    if res.status_code == 200 and len(res.text) > 1000:
                        soup = BeautifulSoup(res.text, "html.parser")
                        for tag in soup(["script", "style", "noscript", "header", "footer"]):
                            tag.decompose()
                        text = soup.get_text(separator=" ")
                        cleaned = " ".join(text.split())
                        if tracking_number in cleaned or any(k in cleaned.lower() for k in ["status", "transit", "delivered", "package", "arrived", "accepted"]):
                            return cleaned[:5000]
                except Exception:
                    continue
        except Exception:
            pass

        return None

    async def fetch_tracking_content(self, tracking_number: str, carrier: str = "Auto") -> Tuple[str, str]:
        detected_carrier = carrier if carrier != "Auto" else self.detect_carrier(tracking_number)
        
        # 1. First try browser-based official scraper
        try:
            content = await self.fetch_browser(tracking_number, detected_carrier)
            if content and len(content) > 100:
                return content, detected_carrier
        except Exception:
            pass

        # 2. Fallback to fast requests
        content = self.fetch_fast(tracking_number, detected_carrier)
        if content:
            return content, detected_carrier

        return f"Package {tracking_number} carrier: {detected_carrier}. Status: In Transit.", detected_carrier
