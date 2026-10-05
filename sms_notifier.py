import smtplib
from email.mime.text import MIMEText
from typing import List, Optional
from config import config

CARRIER_GATEWAYS = {
    "att": ["@txt.att.net", "@mms.att.net"],
    "verizon": ["@vtext.com", "@vzwpix.com"],
    "tmobile": ["@tmomail.net"],
    "sprint": ["@messaging.sprintpcs.com"],
    "cricket": ["@mms.cricketwireless.net"],
    "boost": ["@myboostmobile.com"]
}

class SMSNotifier:
    def __init__(self, sender: str = config.gmail_sender, app_password: str = config.gmail_app_password):
        self.sender = sender
        self.app_password = app_password.replace(" ", "")

    def is_configured(self) -> bool:
        return bool(self.sender and self.app_password)

    def get_recipient_emails(self, phone: str = config.sms_phone_number, carrier: str = config.sms_carrier) -> List[str]:
        clean_phone = "".join(filter(str.isdigit, phone))
        gateways = CARRIER_GATEWAYS.get(carrier.lower(), ["@txt.att.net", "@mms.att.net"])
        return [f"{clean_phone}{gw}" for gw in gateways]

    def send_sms(self, message: str, phone: Optional[str] = None, carrier: Optional[str] = None) -> bool:
        if not self.is_configured():
            print("[SMS] Sender credentials not configured in .env")
            return False

        recipients = self.get_recipient_emails(phone or config.sms_phone_number, carrier or config.sms_carrier)
        msg = MIMEText(message, "plain", "utf-8")
        msg["From"] = self.sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = "OmniTrack"

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
                server.login(self.sender, self.app_password)
                server.sendmail(self.sender, recipients, msg.as_string())
            print(f"[SMS Sent] Successfully texted {phone or config.sms_phone_number} via {carrier or config.sms_carrier.upper()}!")
            return True
        except Exception as e:
            print(f"[SMS Error] Failed to send text: {e}")
            return False
