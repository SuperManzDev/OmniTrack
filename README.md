# 📦 OmniTrack 24/7 — Autonomous Multi-Channel Package Tracker

An autonomous delivery tracking daemon that monitors incoming messages across multiple channels (Gmail, Google Messages SMS, and Snapchat), extracts tracking numbers using an AI parser, scrapes carrier delivery updates, and dispatches real-time alerts.

---

## ⚡ Features

- **🤖 AI-Powered Extraction**: Uses LLM parsing (`ai_parser.py`) to automatically detect carrier names and tracking codes from unstructured shipping emails and SMS notifications.
- **📱 Multi-Channel Ingestion**:
  - **Gmail (`gmail.py`)**: Monitors inbox for order confirmations and shipping updates via IMAP/API.
  - **Google Messages (`google_messages.py`)**: Connects to web sessions to read inbound carrier SMS text messages.
- **🚚 Multi-Carrier Scraper (`scraper.py`)**: Checks real-time delivery estimates, out-for-delivery statuses, and delivery confirmations (USPS, UPS, FedEx, DHL, Amazon Logistics).
- **🔔 Notification Engine (`notifier.py`)**: Broadcasts rich delivery status alerts to Discord webhooks, Snapchat, or terminal panels.
- **⏰ 24/7 Background Runner**: Includes automated loop scripts (`run_247.bat`, `run_background.vbs`) for persistent background operation.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
# Requires: rich, requests, beautifulsoup4, openai, python-dotenv
```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

```env
# Gmail Credentials
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here

# AI Parsing
OPENAI_API_KEY=sk-your-openai-api-key

# Notification Webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your/webhook

# Loop Interval
CHECK_INTERVAL_SECONDS=300
```

### 3. Run the Tracker
```bash
python main.py
```
Or launch in background mode:
```bash
run_247.bat
```

---

## 📂 Project Architecture

```
omnitrack/
├── main.py                 # Core orchestration daemon & CLI dashboard
├── ai_parser.py            # AI / regex tracking number extractor
├── scraper.py              # Carrier web scrapers & status normalizer
├── gmail.py                # Gmail IMAP inbox listener
├── google_messages.py      # Headless Google Messages web session handler
├── notifier.py             # Multi-channel notification dispatcher
├── config.py               # Settings loader
└── .env.example            # Configuration template
```

---

## 📜 License
MIT License.
