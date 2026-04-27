import os
import re
import json
import time
import random
import requests
import feedparser
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NEWS_SOURCES = [
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "http://feeds.bbci.co.uk/news/world/rss.xml"
]

STATE_FILE = "bot_state.json"
POST_LOG_FILE = "post_log.jsonl"
BINANCE_SQUARE_URL = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
STYLE_FILE = "post-style.md"

def load_styles():
    if not os.path.exists(STYLE_FILE):
        return []
    with open(STYLE_FILE, "r") as f:
        content = f.read()
    blocks = re.split(r"\*\*Style\s+\d+[^*]*\*\*", content)
    styles = []
    for block in blocks:
        match = re.search(r"```(.*?)```", block, re.DOTALL)
        if match:
            styles.append(match.group(1).strip())
    return styles

NEWS_STYLES, GAINER_STYLES = [], []

def init_styles():
    global NEWS_STYLES, GAINER_STYLES
    all_styles = load_styles()
    if all_styles:
        NEWS_STYLES = all_styles[:10] if len(all_styles) >= 10 else all_styles
        GAINER_STYLES = all_styles[10:] if len(all_styles) > 10 else all_styles
    print(f"📋 Loaded {len(NEWS_STYLES)} news styles, {len(GAINER_STYLES)} gainer styles")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "news_task": {"last_time": time.time(), "next_delay": 300},
        "gainers_task": {"last_time": time.time(), "next_delay": 300},
        "history": [],
        "last_news_style_idx": -1,
        "last_gainer_style_idx": -1,
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def log_post(task_name, content, post_url):
    entry = {
        "time": datetime.now().isoformat(),
        "task": task_name,
        "url": post_url,
        "content": content[:300]
    }
    with open(POST_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def send_telegram_msg(text):
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
            if entry.title not in history and entry.title not in unique_news:
                summary = getattr(entry, 'summary', '')[:200]
                text = f"{entry.title}. {summary}" if summary else entry.title
                unique_news.append(text)
            if len(unique_news) >= 3:
                break
        if len(unique_news) >= 3:
            break
    return unique_news[:3]

def get_top_gainers():
    try:
        response = requests.get(BINANCE_TICKER_URL, timeout=10)
        tickers = response.json()
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)
        # Random 1, 2, or 3 tokens
        count = random.randint(1, 3)
        return sorted_pairs[:count]
    except Exception as e:
        print(f"❌ Error fetching gainers: {e}")
        return []

def clean_content(text):
    text = re.sub(r"#\w+", "", text)       # remove #hashtags
    text = re.sub(r"\$([A-Z]+)", r"\1", text)  # remove $BTC → BTC
    # Ensure space between token and USDT (e.g., BTCUSDT -> BTC USDT)
    text = re.sub(r"([A-Z0-9]+)(USDT)", r"\1 \2", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def limit_words_per_line(text, max_words=12):
    """
    Prevents extremely long lines while trying to maintain natural flow.
    If a line is already reasonably short (< max_words), it is left untouched.
    """
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        words = line.split()
        if not words:
            new_lines.append("")
            continue
        
        # If line is already within a reasonable limit, keep it as is
        if len(words) <= max_words:
            new_lines.append(line)
            continue
            
        # Otherwise, break it mechanically
        current_line = []
        for word in words:
            current_line.append(word)
            if len(current_line) >= max_words:
                new_lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            new_lines.append(" ".join(current_line))
    return "\n".join(new_lines)

def pick_style(styles_list, last_idx):
    if not styles_list:
        return "", -1
    if len(styles_list) == 1:
        return styles_list[0], 0
    available = [i for i in range(len(styles_list)) if i != last_idx]
    idx = random.choice(available)
    return styles_list[idx], idx

def post_to_square(content, task_name):
    if not BINANCE_API_KEY or "your" in BINANCE_API_KEY:
        print(f"⚠️ {task_name}: API Key missing in .env")
        return False, None
    headers = {
        "X-Square-OpenAPI-Key": BINANCE_API_KEY,
        "Content-Type": "application/json",
        "clienttype": "binanceSkill"
    }
    payload = {"bodyTextOnly": content}
    try:
        res = requests.post(BINANCE_SQUARE_URL, headers=headers, json=payload, timeout=15)
        result = res.json()
        if result.get("code") == "000000":
            post_id = result.get('data', {}).get('id')
            post_url = f"https://www.binance.com/square/post/{post_id}"
            send_telegram_msg(f"✅ *{task_name} Posted!*\n\nLink: {post_url}")
            print(f"✅ {task_name} Posted! Link: {post_url}")
            return True, post_url
        else:
            send_telegram_msg(f"❌ *Binance Error ({task_name})*:\n{result.get('message')}")
            print(f"❌ {task_name} API Error: {result.get('message')}")
    except Exception as e:
        print(f"❌ {task_name} Connection Error: {e}")
        send_telegram_msg(f"❌ *Connection Error ({task_name})*:\n{e}")
    return False, None

def main():
    print(f"🚀 Bot Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if not NVIDIA_API_KEY:
        print("❌ NVIDIA_API_KEY missing!")
        return

    init_styles()

    llm = ChatOpenAI(
        model="meta/llama-3.3-70b-instruct",
        api_key=NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1",
        temperature=0.9,
        max_tokens=600,
    )

    while True:
        print(f"\n--- Checking Tasks: {datetime.now().strftime('%H:%M:%S')} ---")
        state = load_state()
        current_time = time.time()
        news_posted_now = False

        # TASK 1: WORLD NEWS
        news_passed = current_time - state["news_task"]["last_time"]
        if news_passed >= state["news_task"]["next_delay"]:
            print("🌍 Time for World News...")
            news = get_latest_news(state["history"])
            if news:
                style_block, style_idx = pick_style(NEWS_STYLES, state.get("last_news_style_idx", -1))
                style_instruction = (
                    f"\nIs structure ko follow karo (sirf format, content apna likho):\n```\n{style_block}\n```\n"
                    if style_block else ""
                )
                prompt = (
                    f"News Context:\n" + "\n".join(news) + "\n\n"
                    "Task: Write a natural, human-sounding news post for Binance Square in English.\n"
                    "Style Description: Follow the structure of the provided example strictly. Use the same number of sentences and paragraph breaks.\n"
                    "Rules:\n"
                    "- CRITICAL: DO NOT use the word 'Tension' or 'Escalating'. Use synonyms like 'Friction', 'Heat', 'Conflict', 'Drama', 'Standoff', etc.\n"
                    "- DO NOT use bullet points or lists unless the style example explicitly uses them.\n"
                    "- Every post must sound UNIQUE. Do not start every post with the same words.\n"
                    "- Write like a real crypto trader sharing their personal take.\n"
                    "- USE COMPLETE NATURAL SENTENCES. Avoid breaking lines in the middle of a phrase.\n"
                    "- Each line should ideally have 7-12 words. Do not make lines too short (like 2-3 words).\n"
                    "- Use 2-3 emojis subtly. NO hashtags, NO dollar signs.\n"
                    "- If mentioning tokens, always put a space before USDT (e.g., BTC USDT).\n"
                    "- End with one line of your own opinion.\n"
                    f"\nFollow this exact structure (Style {style_idx + 1}):\n```\n{style_block}\n```\n"
                )
                resp = llm.invoke(prompt)
                content = clean_content(limit_words_per_line(resp.content, max_words=12))
                success, post_url = post_to_square(content, "World News")
                if success:
                    log_post("World News", content, post_url)
                    state["news_task"]["last_time"] = time.time()
                    state["news_task"]["next_delay"] = random.randint(4 * 3600, 6 * 3600)
                    # Store only titles in history (not full text with summary)
                    state["history"].extend([n.split('.')[0] for n in news])
                    state["last_news_style_idx"] = style_idx
                    state["history"] = state["history"][-100:]
                    news_posted_now = True
        else:
            wait_h = (state["news_task"]["next_delay"] - news_passed) / 3600
            print(f"⏳ World News: Waiting {wait_h:.1f} more hours.")

        if news_posted_now:
            print("⏳ Delaying 2 minutes before next check...")
            save_state(state)
            time.sleep(120)

        # TASK 2: TOP GAINERS
        gainers_passed = time.time() - state["gainers_task"]["last_time"]
        if gainers_passed >= state["gainers_task"]["next_delay"]:
            print("📈 Time for Gainer Analysis...")
            gainers = get_top_gainers()
            if gainers:
                count = len(gainers)
                gainers_text = "\n".join([
                    f"{g['symbol'].replace('USDT',' USDT')}: +{float(g['priceChangePercent']):.1f}%"
                    for g in gainers
                ])
                style_block, style_idx = pick_style(GAINER_STYLES, state.get("last_gainer_style_idx", -1))
                style_instruction = (
                    f"\nIs structure ko follow karo (coin names/numbers apne data se replace karo):\n```\n{style_block}\n```\n"
                    if style_block else ""
                )
                prompt = (
                    f"Today's top {count} gainer{'s' if count > 1 else ''}:\n{gainers_text}\n\n"
                    "Task: Write a punchy, natural gainer post for Binance Square in English.\n"
                    "Style Description: Follow the structure of the provided example strictly. Use the same number of sentences and paragraph breaks.\n"
                    "Rules:\n"
                    "- CRITICAL: Avoid generic words like 'pumping'. Use 'soaring', 'flying', 'on fire', 'exploding', etc.\n"
                    "- ALWAYS put a space between the token name and USDT (e.g., BTC USDT, APE USDT).\n"
                    "- DO NOT use bullet points or lists unless the style example explicitly uses them.\n"
                    "- Every post must sound UNIQUE. Do not start every post with the same words.\n"
                    "- Write like an active trader watching the market live.\n"
                    "- USE COMPLETE NATURAL SENTENCES. Each line should have 7-12 words.\n"
                    "- Avoid mechanical line breaks; let the sentences flow naturally.\n"
                    "- Only mention coins from the data provided.\n"
                    "- No hashtags, No dollar signs. % can be used freely.\n"
                    "- End with one line take — bullish, cautious, or neutral.\n"
                    f"\nFollow this exact structure (Style {style_idx + 11}):\n```\n{style_block}\n```\n"
                )
                resp = llm.invoke(prompt)
                content = clean_content(limit_words_per_line(resp.content, max_words=12))
                success, post_url = post_to_square(content, "Top Gainers")
                if success:
                    log_post("Top Gainers", content, post_url)
                    state["gainers_task"]["last_time"] = time.time()
                    state["gainers_task"]["next_delay"] = random.randint(7 * 3600, 8 * 3600)
                    state["last_gainer_style_idx"] = style_idx
        else:
            wait_h = (state["gainers_task"]["next_delay"] - gainers_passed) / 3600
            print(f"⏳ Gainers task: Waiting {wait_h:.1f} more hours.")

        save_state(state)
        print("😴 Sleeping for 10 minutes before next cycle...")
        time.sleep(600)


if __name__ == "__main__":
    main()