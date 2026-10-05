import json
import re
import requests
from typing import Optional, Dict, Any
from config import config

class AIParser:
    def __init__(self, api_key: str = config.openrouter_api_key, models: list = None):
        self.api_key = api_key
        self.models = models or config.openrouter_models
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def parse_tracking_text(self, tracking_number: str, raw_text: str, detected_carrier: str = "Auto") -> Dict[str, Any]:
        carrier_name = detected_carrier if detected_carrier != "Auto" else ("USPS" if tracking_number.startswith("9") else "FedEx")
        
        if not self.api_key:
            return self._heuristic_fallback(tracking_number, raw_text, carrier_name)

        prompt = (
            f"You are an expert package logistics data parser.\n"
            f"Extract the tracking status for package '{tracking_number}' (Carrier: {carrier_name}) from the text.\n"
            "If the package is newly created, label created, or awaiting carrier pickup, status is 'Pre-Shipment' and description is 'Shipping Label Created, Awaiting Item'.\n\n"
            "Return ONLY valid JSON matching this schema:\n"
            "{\n"
            f'  "carrier": "{carrier_name}",\n'
            f'  "tracking_number": "{tracking_number}",\n'
            '  "status": "In Transit | Out for Delivery | Delivered | Picked Up | Pre-Shipment | Exception",\n'
            '  "description": "Short summary of latest scan event",\n'
            '  "location": "City, State or Canton, MI if local, or null",\n'
            '  "timestamp": "Date/Time string or null",\n'
            '  "estimated_delivery": "Delivery ETA or null",\n'
            '  "is_delivered": true or false\n'
            "}\n\n"
            f"Tracking Content:\n{raw_text[:4000]}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/omnitrack",
            "X-Title": "OmniTrack Auto Checker"
        }

        for model in self.models:
            try:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }
                res = requests.post(self.endpoint, headers=headers, json=payload, timeout=15)
                if res.status_code == 200:
                    content = res.json()["choices"][0]["message"]["content"].strip()
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        parsed["tracking_number"] = tracking_number
                        parsed["carrier"] = carrier_name
                        
                        desc = parsed.get("description", "")
                        status = parsed.get("status", "")
                        
                        # Clean fallback phrases
                        if "provided raw content" in desc.lower() or status.lower() == "unknown" or not desc:
                            parsed["status"] = "Pre-Shipment"
                            parsed["description"] = f"Shipping Label Created, {carrier_name} Awaiting Item"
                            
                        return parsed
                elif res.status_code in (429, 404, 500):
                    continue
            except Exception:
                continue

        return self._heuristic_fallback(tracking_number, raw_text, carrier_name)

    def _heuristic_fallback(self, tracking_number: str, raw_text: str, carrier: str) -> Dict[str, Any]:
        text_lower = raw_text.lower()
        is_delivered = "delivered" in text_lower
        
        if is_delivered:
            status = "Delivered"
            desc = "Delivered to recipient address"
        elif "out for delivery" in text_lower:
            status = "Out for Delivery"
            desc = "Out for delivery on carrier vehicle"
        elif any(k in text_lower for k in ["in transit", "departed", "arrived", "moving", "sent to fedex"]):
            status = "In Transit"
            desc = "In transit to destination facility"
        else:
            status = "Pre-Shipment"
            desc = f"Shipping Label Created, {carrier} Awaiting Item"

        return {
            "carrier": carrier,
            "tracking_number": tracking_number,
            "status": status,
            "description": desc,
            "location": "CANTON, MI, US",
            "timestamp": None,
            "estimated_delivery": None,
            "is_delivered": is_delivered
        }
