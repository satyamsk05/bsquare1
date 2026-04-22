import os
import json
import time
import random
import requests
import feedparser
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY") 
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NEWS_SOURCES = [
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "http://feeds.bbci.co.uk/news/world/rss.xml"
]

STATE_FILE = "bot_state.json"
BINANCE_SQUARE_URL = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "news_task": {"last_time": 0, "next_delay": 0},
        "gainers_task": {"last_time": 0, "next_delay": 0},
        "history": []
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_telegram_msg(text):
    """Sends notification to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def get_latest_news(history):
    unique_news = []
    for url in NEWS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.title not in history:
                unique_news.append(entry.title)
                if len(unique_news) >= 3: break
        if len(unique_news) >= 3: break
    return unique_news[:3]

def get_top_gainers():
    try:
        response = requests.get(BINANCE_TICKER_URL)
        tickers = response.json()
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)
        return sorted_pairs[:3]
    except Exception as e:
        print(f"❌ Error fetching gainers: {e}")
        return []

def post_to_square(content, task_name):
    if not BINANCE_API_KEY or "your" in BINANCE_API_KEY:
        print(f"⚠️ {task_name}: API Key missing in .env")
        return False

    headers = {
        "X-Square-OpenAPI-Key": BINANCE_API_KEY,
        "Content-Type": "application/json",
        "clienttype": "binanceSkill"
    }
    payload = {"bodyTextOnly": content}
    try:
        res = requests.post(BINANCE_SQUARE_URL, headers=headers, json=payload)
        result = res.json()
        if result.get("code") == "000000":
            post_id = result.get('data', {}).get('id')
            post_url = f"https://www.binance.com/square/post/{post_id}"
            msg = f"✅ *{task_name} Posted!*\n\nLink: {post_url}\n\n_Bot is running smoothly._"
            print(f"✅ {task_name} Posted! Link: {post_url}")
            send_telegram_msg(msg)
            return True
        else:
            send_telegram_msg(f"❌ *Binance Error ({task_name})*:\n{result.get('message')}")
            print(f"❌ {task_name} API Error: {result.get('message')}")
    except Exception as e:
        print(f"❌ {task_name} Connection Error: {e}")
        send_telegram_msg(f"❌ *Connection Error ({task_name})*:\n{e}")
    return False

def limit_words_per_line(text, max_words=12):
    """Ensures each line has a maximum number of words"""
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        words = line.split()
        if not words:
            new_lines.append("")
            continue
        
        current_line = []
        for word in words:
            current_line.append(word)
            if len(current_line) >= max_words:
                new_lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            new_lines.append(" ".join(current_line))
    return "\n".join(new_lines)

def main():
    print(f"🚀 Bot Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not NVIDIA_API_KEY:
        print("❌ NVIDIA_API_KEY missing!")
        return
    
    llm = ChatOpenAI(
        model="meta/llama-3.3-70b-instruct",
        api_key=NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1"
    )

    while True:
        print(f"\n--- Checking Tasks: {datetime.now().strftime('%H:%M:%S')} ---")
        state = load_state()
        current_time = time.time()
        news_posted_now = False

        # --- TASK 1: WORLD NEWS ---
        news_passed = current_time - state["news_task"]["last_time"]
        if news_passed >= state["news_task"]["next_delay"]:
            print("🌍 Time for World News...")
            news = get_latest_news(state["history"])
            if news:
                prompt = (
                    f"Global News Context:\n" + "\n".join(news) + "\n\n"
                    "Task: Write a crisp, no-nonsense world news post for Binance Square.\n"
                    "Style Instructions:\n"
                    "- Write like a real human trader/analyst, NOT a bot.\n"
                    "- Focus on facts and direct impact.\n"
                    "- Include 2-3 subtle emojis. NO bold, NO hashtags, NO dollar signs.\n"
                    "- Start with a strong, direct headline.\n"
                    "- CRITICAL: Use VERY SHORT LINES. Max 10 words per line.\n"
                    "- Break every sentence into 2-3 separate lines."
                )
                resp = llm.invoke(prompt)
                formatted_content = limit_words_per_line(resp.content, max_words=10)
                if post_to_square(formatted_content, "World News"):
                    state["news_task"]["last_time"] = time.time()
                    state["news_task"]["next_delay"] = random.randint(4*3600, 6*3600)
                    state["history"].extend(news)
                    news_posted_now = True
        else:
            wait_h = (state["news_task"]["next_delay"] - news_passed) / 3600
            print(f"⏳ World News: Waiting {wait_h:.1f} more hours.")

        if news_posted_now:
            print("⏳ Delaying 2 minutes before next check...")
            save_state(state)
            time.sleep(120)
            current_time = time.time() # Update time after sleep

        # --- TASK 2: TOP GAINERS ---
        gainers_passed = time.time() - state["gainers_task"]["last_time"]
        if gainers_passed >= state["gainers_task"]["next_delay"]:
            print("📈 Time for Gainer Analysis...")
            gainers = get_top_gainers()
            if gainers:
                gainers_text = "\n".join([f"{g['symbol']}: {g['priceChangePercent']}%" for g in gainers])
                prompt = (
                    f"Market Data:\n{gainers_text}\n\n"
                    "Task: Write a crisp, punchy market gainer analysis for Binance Square.\n"
                    "Style Instructions:\n"
                    "- Be direct. No fluff, no 'potential', no 'thrilling ride'.\n"
                    "- Focus on the momentum and price action only.\n"
                    "- No bold, No hashtags, No dollar signs.\n"
                    "- Use ONE of the attractive styles from post-style.md as a structural guide.\n"
                    "- CRITICAL: Use VERY SHORT LINES. Max 10 words per line.\n"
                    "- Break every sentence into 2-3 separate lines."
                )
                resp = llm.invoke(prompt)
                formatted_content = limit_words_per_line(resp.content, max_words=10)
                if post_to_square(formatted_content, "Top Gainers"):
                    state["gainers_task"]["last_time"] = time.time()
                    state["gainers_task"]["next_delay"] = random.randint(7*3600, 8*3600)
        else:
            wait_h = (state["gainers_task"]["next_delay"] - gainers_passed) / 3600
            print(f"⏳ Gainers task: Waiting {wait_h:.1f} more hours.")

        save_state(state)
        print("😴 Sleeping for 10 minutes before next cycle...")
        time.sleep(600) # Check every 10 minutes



if __name__ == "__main__":
    main()
