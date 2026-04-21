# 🚀 Viral News Agent for Binance Square

An automated, lightweight AI news agent designed for **AWS Free Tier**. It fetches viral global news and Binance top gainers, summarizes them using AI, and publishes attractive posts to Binance Square.

## ✨ Features
- 🌍 **World News Aggregator**: Fetches latest stories from Google News and BBC.
- 📈 **Binance Gainers**: Real-time tracking of top 3 performing coins.
- 🤖 **AI Powered**: Uses NVIDIA Llama 3.3 for professional journalistic analysis.
- 🕒 **Smart Automation**: Random posting intervals (4-8 hours) to mimic human behavior.
- 🚨 **Telegram Notifications**: Real-time alerts for every post or error.
- 💎 **Custom Styles**: Follows specific attractive templates for high engagement.

## 🛠️ Setup Instructions

### 1. Installation
```bash
# Clone the repository and enter directory
cd bsqaure

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Edit the `.env` file with your API keys:
- `NVIDIA_API_KEY`: For AI summarization.
- `BINANCE_API_KEY`: Your Square OpenAPI Key (from Creator Center).
- `TELEGRAM_BOT_TOKEN`: From @BotFather.
- `TELEGRAM_CHAT_ID`: From @userinfobot.

### 3. Usage
**Manual Run:**
```bash
python3 agent.py
```

**Automated Run (Cron):**
Add this to your `crontab -e`:
```bash
*/30 * * * * cd /absolute/path/to/bsqaure && ./venv/bin/python3 agent.py >> bot_log.txt 2>&1
```

## 📁 File Structure
- `agent.py`: Main bot logic.
- `.env`: API keys and credentials.
- `post-style.md`: Custom attractive posting templates.
- `bot_state.json`: Tracks last post time and history.
- `requirements.txt`: Python dependencies.

## 🛡️ Security
Never share your `.env` file. It contains sensitive API keys.
