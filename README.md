# 🚀 Automated Viral News & Market Agent (Binance Square)

A high-performance, lightweight Python agent optimized for **AWS Free Tier**. This bot automates the process of fetching, analyzing, and posting viral global news and Binance top gainers to Binance Square with a professional journalistic touch.

## 🌟 Key Features

### 🌍 1. World News Analysis (4-6h)
- Scrapes trending headlines from global RSS feeds (Google News, BBC).
- Uses **NVIDIA Llama 3.3 AI** to write deep, analytical posts.
- **Custom Styles**: Chooses from 10+ attractive templates (Breaking News, Analyst Report, etc.).

### 📈 2. Binance Top Gainers (7-8h)
- Real-time data fetching via Binance Public API.
- Identifies the top 3 high-momentum USDT pairs.
- Explains market sentiment and momentum factors in plain text.

### 🤖 3. Intelligent Automation
- **Random Intervals**: Posts at unpredictable times to maintain a natural profile.
- **2-Minute Staggering**: Automatically delays consecutive posts for better feed spacing.
- **No-Spam Logic**: Remembers posted news to avoid duplicates.

### 🚨 4. Real-time Notifications
- Integrated **Telegram Bot** alerts for successful posts and API errors.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- AWS EC2 (t2.micro is perfect) or any Linux server.

### 2. Setup
```bash
git clone https://github.com/satyamsk05/bsquare1.git
cd bsquare1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration (.env)
Create a `.env` file in the root directory:
```env
NVIDIA_API_KEY=your_nvidia_key
BINANCE_API_KEY=your_square_openapi_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🚀 Execution

### Manual Run
```bash
python3 agent.py
```

### Automatic Scheduling (Cron)
We recommend running the script every 30 minutes. It will only post when the random interval is reached.
```bash
*/30 * * * * cd /path/to/bsquare1 && ./venv/bin/python3 agent.py >> bot_log.txt 2>&1
```

## 📁 File Structure
- `agent.py`: Core logic for scraping, AI, and posting.
- `post-style.md`: Library of attractive posting templates.
- `bot_state.json`: Local database for timing and history.
- `.gitignore`: Ensures security of your API keys.

---
## 🛡️ License & Security
This project is for educational and creator automation purposes. Always keep your `.env` private to protect your account.
