import time
import subprocess
from typing import Optional, List
import uiautomator2 as u2
import adbutils
from config import config

class AndroidSnapchatDispatcher:
    def __init__(self, serial: Optional[str] = None):
        self.serial = serial
        self.d = None

    def connect(self):
        try:
            # First try connecting to LDPlayer ADB port
            try:
                subprocess.run(["adb", "connect", "127.0.0.1:5555"], capture_output=True, timeout=5)
            except Exception:
                pass

            devices = adbutils.adb.device_list()
            if not devices:
                raise RuntimeError("No Android device or emulator detected via ADB.")

            # Priority order: LDPlayer / Emulator / Any connected device
            target_serial = devices[0].serial
            for dev in devices:
                if "127.0.0.1" in dev.serial or "emulator" in dev.serial or "5555" in dev.serial:
                    target_serial = dev.serial
                    break
            
            self.d = u2.connect(target_serial)
            print(f"[Android] Connected successfully to: {target_serial} ({self.d.device_info.get('model', 'Android')})")
        except Exception as e:
            raise RuntimeError(f"Could not connect to Android device via ADB: {e}")

    def send_group_messages(self, group_name: str, messages: List[str], mention_user: Optional[str] = None):
        if not self.d:
            self.connect()

        print("[Android] Launching Snapchat app...")
        self.d.app_start("com.snapchat.android")
        time.sleep(3)

        # 1. Click Chat tab
        if self.d(descriptionContains="Chat").exists:
            self.d(descriptionContains="Chat").click()
            time.sleep(1)

        # 2. Find group chat
        print(f"[Android] Finding group '{group_name}'...")
        if self.d(textContains=group_name).exists(timeout=10):
            self.d(textContains=group_name).click()
            time.sleep(1.5)
        else:
            raise RuntimeError(f"Group chat '{group_name}' not found on screen.")

        clean_user = (mention_user or "").lstrip("@")

        # 3. Type and send messages
        for message in messages:
            chat_input = self.d(textContains="Send a Chat")
            if not chat_input.exists:
                chat_input = self.d(className="android.widget.EditText")

            if chat_input.exists:
                chat_input.click()
                time.sleep(0.4)

                if clean_user:
                    self.d.send_keys(f"@{clean_user}")
                    time.sleep(0.6)
                    # Click mention popup if present
                    if self.d(textContains=clean_user).exists:
                        self.d(textContains=clean_user).click()
                    else:
                        self.d.press("enter")
                    time.sleep(0.3)

                # Send message text
                self.d.send_keys(message)
                time.sleep(0.3)

                # Send
                send_btn = self.d(descriptionContains="Send")
                if send_btn.exists:
                    send_btn.click()
                else:
                    self.d.press("enter")
                time.sleep(0.8)

        print(f"[Android] Successfully sent {len(messages)} message(s) to '{group_name}'!")
