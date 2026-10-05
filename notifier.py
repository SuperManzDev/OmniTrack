import time
import asyncio
from datetime import datetime
from typing import Optional, List
from config import config
from storage import PackageItem
from twilio_notifier import TwilioNotifier
from google_messages import GoogleMessagesDispatcher
from gmail import GmailNotifier

class NotificationManager:
    def __init__(self):
        self.twilio = TwilioNotifier()
        self.google_messages = GoogleMessagesDispatcher()
        self.gmail = GmailNotifier()

    def get_tracking_links(self, tracking_number: str, carrier: str) -> tuple[str, str]:
        carrier_lower = carrier.lower()
        if "fedex" in carrier_lower:
            direct = f"https://fedex.com/fedextrack/?trknbr={tracking_number}"
        elif "usps" in carrier_lower:
            direct = f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}"
        elif "ups" in carrier_lower:
            direct = f"https://ups.com/track?tracknum={tracking_number}"
        elif "dhl" in carrier_lower:
            direct = f"https://dhl.com/en/express/tracking.html?AWB={tracking_number}"
        else:
            direct = f"https://parcelsapp.com/en/tracking/{tracking_number}"
            
        backup = f"https://17track.net/en/track#nums={tracking_number}"
        return direct, backup

    def format_sms_message(self, item: PackageItem) -> str:
        carrier = item.carrier.upper() if item.carrier else "CARRIER"
        last4 = item.tracking_number[-4:]
        nick = item.nickname or f"{carrier} Package"
        status = item.last_status.upper() if item.last_status else "IN TRANSIT"
        desc = item.last_description or "Package in transit"
        loc = item.last_location or "CANTON, MI"
        current_time = datetime.now().strftime("%b %d - %I:%M %p")
        direct_link, backup_link = self.get_tracking_links(item.tracking_number, carrier)

        if item.is_delivered:
            return (
                f"====================================\n"
                f"-- PACKAGE DELIVERED! --\n"
                f"====================================\n"
                f"* Item: {nick} ({carrier} #{last4})\n"
                f"* Carrier: {carrier}\n"
                f"* Status: DELIVERED\n"
                f"* Location: {loc}\n"
                f"* Details: {desc}\n"
                f"* Direct Link: {direct_link}\n"
                f"* 17Track Link: {backup_link}\n"
                f"* Timestamp: {current_time}\n"
                f"* Tracking #: {item.tracking_number}\n"
                f"===================================="
            )
        elif "out for delivery" in status.lower():
            return (
                f"====================================\n"
                f"-- OUT FOR DELIVERY TODAY --\n"
                f"====================================\n"
                f"* Item: {nick} ({carrier} #{last4})\n"
                f"* Carrier: {carrier}\n"
                f"* Status: OUT FOR DELIVERY\n"
                f"* Area: {loc}\n"
                f"* Details: {desc}\n"
                f"* Direct Link: {direct_link}\n"
                f"* Tracking #: {item.tracking_number}\n"
                f"===================================="
            )
        else:
            return (
                f"====================================\n"
                f"-- PACKAGE UPDATE: {carrier} --\n"
                f"====================================\n"
                f"* Item: {nick} (#{last4})\n"
                f"* Carrier: {carrier}\n"
                f"* Status: {status}\n"
                f"* Details: {desc}\n"
                f"* Location: {loc}\n"
                f"* Direct Link: {direct_link}\n"
                f"* 17Track Link: {backup_link}\n"
                f"* Last Updated: {current_time}\n"
                f"* Tracking #: {item.tracking_number}\n"
                f"===================================="
            )

    async def notify_package_update(self, item: PackageItem, force: bool = False):
        sms_body = self.format_sms_message(item)
        carrier = item.carrier.upper() if item.carrier else "Package"
        nick = item.nickname or "Package"
        last4 = item.tracking_number[-4:]

        # 1. Send SMS Texts directly into chat named 'ADIRAN'
        messages_to_send = [sms_body]
        if item.is_delivered:
            messages_to_send.extend([
                f"?? WAKE UP! Your package ({nick}) has been DELIVERED to your front door! Go grab it outside!",
                f"?? DELIVERY CONFIRMED! Check your porch right now!"
            ])

        print(f"[Google Messages] Posting update for {nick} into chat 'ADIRAN'...")
        try:
            await self.google_messages.send_sms_to_chat("ADIRAN", messages_to_send)
        except Exception as e_gm:
            print(f"[Google Messages Error]: {e_gm}")

        # 2. Place Automated Voice Calls via Twilio
        if item.is_delivered:
            # 3-Round Delivery Call Spam Loop
            print("[DELIVERY ARRIVAL EVENT] Placing 3-round repeat voice calls to Adi & Manas...")
            delivery_speech = (
                f"Attention Adi and Manas! This is OmniTrack Package Tracker. "
                f"Your {nick} from {carrier} has just been DELIVERED to your front door! "
                f"Please go check your porch right now and grab your package before anyone takes it!"
            )
            self.twilio.broadcast_voice_call(delivery_speech, repeat_count=3, delay_between_calls=20)
        else:
            # Voice status update call
            print(f"[STATUS UPDATE EVENT] Placing voice update call for {nick}...")
            status_speech = (
                f"Hello! This is OmniTrack. Your {nick} from {carrier} has updated to: "
                f"{item.last_status}. Current location: {item.last_location or 'in transit'}."
            )
            self.twilio.broadcast_voice_call(status_speech, repeat_count=1)

        # 3. Encrypted Email Backup
        if self.gmail.is_configured():
            self.gmail.send_alert(
                subject=f"[OmniTrack Update] {nick} ({carrier} #{last4}) - {item.last_status}",
                body=sms_body
            )
