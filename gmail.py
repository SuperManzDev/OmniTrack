import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import config

class GmailNotifier:
    def __init__(self, sender: str = config.gmail_sender, app_password: str = config.gmail_app_password, recipient: str = config.gmail_recipient):
        self.sender = sender
        self.app_password = app_password.replace(" ", "")
        self.recipient = recipient or sender

    def is_configured(self) -> bool:
        return bool(self.sender and self.app_password and self.recipient)

    def send_alert(self, subject: str, body: str) -> bool:
        if not self.is_configured():
            print("[Gmail] Info: Gmail is not configured in .env (GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT)")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = self.recipient

            html_body = f"""
            <div style="font-family: Arial, sans-serif; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; max-width: 600px;">
                <h2 style="color: #1a73e8; margin-top: 0;">?? OmniTrack Package Alert</h2>
                <div style="font-size: 14px; color: #333; line-height: 1.6; white-space: pre-wrap;">{body}</div>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <small style="color: #888;">Dispatched automatically by OmniTrack</small>
            </div>
            """
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender, self.app_password)
                server.sendmail(self.sender, [self.recipient], msg.as_string())

            print(f"[Gmail Alert Sent] '{subject}' -> {self.recipient}")
            return True
        except Exception as e:
            print(f"[Gmail Error] Failed to send email alert: {e}")
            return False
