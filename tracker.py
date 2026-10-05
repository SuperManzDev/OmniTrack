from scraper import WebScraper
from ai_parser import AIParser
from storage import PackageStore, PackageItem
from typing import Dict, Any, Tuple

class OmniTracker:
    def __init__(self):
        self.scraper = WebScraper()
        self.parser = AIParser()
        self.store = PackageStore()

    async def check_package(self, tracking_number: str, carrier: str = "Auto") -> Tuple[bool, PackageItem, Dict[str, Any]]:
        raw_text, detected_carrier = await self.scraper.fetch_tracking_content(tracking_number, carrier)
        parsed_result = self.parser.parse_tracking_text(tracking_number, raw_text, detected_carrier)
        has_changed, item = self.store.update_status(tracking_number, parsed_result)
        return has_changed, item, parsed_result

    async def check_all(self) -> list:
        results = []
        for item in self.store.list_all():
            has_changed, updated_item, raw = await self.check_package(item.tracking_number, item.carrier)
            results.append({
                "has_changed": has_changed,
                "item": updated_item,
                "raw": raw
            })
        return results
