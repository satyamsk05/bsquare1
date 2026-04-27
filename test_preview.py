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
STYLE_FILE = "post-style.md"
NEWS_SOURCES = [
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "http://feeds.bbci.co.uk/news/world/rss.xml"
]
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"

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

def get_latest_news():
    unique_news = []
    for url in NEWS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries:
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
        count = random.randint(1, 3)
        return sorted_pairs[:count]
    except Exception as e:
        print(f"❌ Error fetching gainers: {e}")
        return []

def clean_content(text):
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"\$([A-Z]+)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def limit_words_per_line(text, max_words=10):
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

def generate_test_posts():
    all_styles = load_styles()
    news_styles = all_styles[:10]
    gainer_styles = all_styles[10:20]

    llm = ChatOpenAI(
        model="meta/llama-3.3-70b-instruct",
        api_key=NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1",
        temperature=0.9,
    )

    results = []

    # Fetch fresh data
    news_items = get_latest_news()
    gainers_data = get_top_gainers()
    gainers_text = "\n".join([f"{g['symbol'].replace('USDT','')}: +{float(g['priceChangePercent']):.1f}%" for g in gainers_data])

    # 1. Generate all News Styles (1-10)
    print("✍️ Generating 10 News Posts with diverse topics and vocabulary...")
    for i, style_block in enumerate(news_styles):
        # Rotate news items so they don't all talk about the same thing
        current_news = news_items[i % len(news_items)]
        
        prompt = (
            f"News Context: {current_news}\n\n"
            "Task: Write a natural, human-sounding news post for Binance Square in English.\n"
            "Style Description: Follow the structure of the provided example strictly. Use the same number of sentences and paragraph breaks.\n"
            "Rules:\n"
            "- CRITICAL: DO NOT use the word 'Tension' or 'Escalating'. Use synonyms like 'Friction', 'Heat', 'Conflict', 'Drama', 'Standoff', etc.\n"
            "- DO NOT use bullet points or lists unless the style example explicitly uses them.\n"
            "- Every post must sound UNIQUE. Do not start every post with the same words.\n"
            "- Write like a real crypto trader sharing their personal take.\n"
            "- Complete natural sentences, MAX 10 words per line.\n"
            "- Use 2-3 emojis subtly. NO hashtags, NO dollar signs.\n"
            "- End with one line of your own opinion.\n"
            f"\nFollow this exact structure (Style {i+1}):\n```\n{style_block}\n```\n"
        )
        resp = llm.invoke(prompt)
        content = clean_content(limit_words_per_line(resp.content, max_words=10))
        results.append({"type": f"News Style {i+1}", "content": content})
        print(f"  ✅ Style {i+1} done")
        time.sleep(1) # Small delay to avoid rate limit

    # 2. Generate all Gainer Styles (11-20)
    print("✍️ Generating 10 Gainer Posts with varied tones...")
    for i, style_block in enumerate(gainer_styles):
        prompt = (
            f"Today's top movers:\n{gainers_text}\n\n"
            "Task: Write a punchy, natural gainer post for Binance Square in English.\n"
            "Style Description: Follow the structure of the provided example strictly. Use the same number of sentences and paragraph breaks.\n"
            "Rules:\n"
            "- CRITICAL: Avoid generic words like 'pumping'. Use 'soaring', 'flying', 'on fire', 'exploding', etc.\n"
            "- DO NOT use bullet points or lists unless the style example explicitly uses them.\n"
            "- Every post must sound UNIQUE. Do not start every post with the same words.\n"
            "- Complete natural sentences, MAX 10 words per line.\n"
            "- Only mention coins from the data provided.\n"
            "- No hashtags, No dollar signs. % can be used freely.\n"
            "- End with one line take.\n"
            f"\nFollow this exact structure (Style {i+11}):\n```\n{style_block}\n```\n"
        )
        resp = llm.invoke(prompt)
        content = clean_content(limit_words_per_line(resp.content, max_words=10))
        results.append({"type": f"Gainer Style {i+11}", "content": content})
        print(f"  ✅ Style {i+11} done")
        time.sleep(1)

    with open("test_output.json", "w") as f:
        json.dump(results, f, indent=4)
    
    print("\n🚀 All 20 test posts generated and saved to test_output.json")

if __name__ == "__main__":
    generate_test_posts()
