import re

def clean_content(text):
    text = re.sub(r"#\w+", "", text)       # remove #hashtags
    text = re.sub(r"\$([A-Z]+)", r"\1", text)  # remove $BTC → BTC
    # Ensure space between token and USDT (e.g., BTCUSDT -> BTC USDT)
    text = re.sub(r"([A-Z0-9]+)(USDT)", r"\1 \2", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def limit_words_per_line(text, max_words=12):
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        words = line.split()
        if not words:
            new_lines.append("")
            continue
        if len(words) <= max_words:
            new_lines.append(line)
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

# Test cases
test_outputs = [
    "APEUSDT is leading the market today with a 79.5% gain.",
    "BTCUSDT looks bullish while ETHUSDT follows closely behind.",
    "This is a very long line that should be broken eventually but only if it exceeds twelve words in total length.",
    "Short line.\nAnother short line.",
    "KATUSDT follows with 77.778 close behind."
]

print("--- Testing Token Spacing ---")
for text in test_outputs:
    cleaned = clean_content(text)
    print(f"Original: {text}")
    print(f"Cleaned:  {cleaned}")
    print("-" * 20)

print("\n--- Testing Line Breaking (max_words=12) ---")
long_text = "This is a very long sentence that contains more than twelve words and should be broken into two separate lines for better readability."
print(f"Original: {long_text}")
print(f"Limited:  {limit_words_per_line(long_text, 12)}")

print("\n--- Testing Natural Flow (not breaking short lines) ---")
natural_text = "APE USDT leads\nwith 79.5% gain\ntoday so far"
print(f"Original:\n{natural_text}")
print(f"Processed:\n{limit_words_per_line(natural_text, 12)}")
