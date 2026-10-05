import os
import time
from typing import Optional, List
from twilio.rest import Client
from config import config

class TwilioNotifier:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_phone = os.getenv("TWILIO_PHONE_NUMBER", "")
        
        # Load all target numbers from environment variable
        raw_targets = os.getenv("TARGET_PHONE_NUMBERS", "")
        self.target_numbers = [n.strip() for n in raw_targets.split(",") if n.strip()]
        self.client = None

        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)

    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_phone)

    def broadcast_voice_call(self, speech_text: str, repeat_count: int = 1, delay_between_calls: int = 15) -> bool:
        if not self.is_configured():
            return False

        twiml_speech = (
            f"<Response>"
            f"<Say voice='alice'>{speech_text}</Say>"
            f"<Pause length='1'/>"
            f"<Say voice='alice'>{speech_text}</Say>"
            f"</Response>"
        )

        for attempt in range(1, repeat_count + 1):
            print(f"[Voice Call Round {attempt}/{repeat_count}] Calling all verified numbers...")
            for target in self.target_numbers:
                try:
                    call = self.client.calls.create(
                        twiml=twiml_speech,
                        from_=self.from_phone,
                        to=target
                    )
                    print(f"  [Call Placed] SID: {call.sid} -> {target}")
                except Exception as e:
                    print(f"  [Call Error for {target}]: {e}")
            
            if attempt < repeat_count:
                print(f"Waiting {delay_between_calls}s before next call round...")
                time.sleep(delay_between_calls)

        return True
