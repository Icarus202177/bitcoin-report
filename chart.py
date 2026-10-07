import requests
import statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
settings = {"vs_currency": "usd", "days": "365", "interval": "daily"}
answer = requests.get(url, params=settings, timeout=10).json()

dates = [datetime.fromtimestamp(p[0] / 1000) for p in answer["prices"]]
prices = [p[1] for p in answer["prices"]]

def moving_average(values, days):
    result = []
    for i in range(len(values)):
        if i + 1 < days:
            result.append(float("nan"))
        else:
            result.append(sum(values[i + 1 - days : i + 1]) / days)
    return result

ma50 = moving_average(prices, 50)
ma200 = moving_average(prices, 200)

ma20 = moving_average(prices, 20)
upper_band = []
lower_band = []
for i in range(len(prices)):
    if i + 1 < 20:
        upper_band.append(float("nan"))
        lower_band.append(float("nan"))
    else:
        spread = statistics.pstdev(prices[i - 19 : i + 1])
        upper_band.append(ma20[i] + 2 * spread)
        lower_band.append(ma20[i] - 2 * spread)

volumes = [v[1] / 1_000_000_000 for v in answer["total_volumes"]]

rsi_line = [float("nan")]
for i in range(1, len(prices)):
    if i < 14:
        rsi_line.append(float("nan"))
    else:
        recent = [prices[j] - prices[j - 1] for j in range(i - 13, i + 1)]
        gain = sum(c for c in recent if c > 0) / 14
        loss = sum(-c for c in recent if c < 0) / 14
        if loss == 0:
            rsi_line.append(100)
        else:
            rsi_line.append(100 - 100 / (1 + gain / loss))

fig, (top, middle, bottom) = plt.subplots(3, 1, figsize=(11, 9), sharex=True, gridspec_kw={"height_ratios": [3, 1, 1]})

top.plot(dates, prices, label="Bitcoin price", color="black")
top.plot(dates, ma50, label="50-day average", color="blue")
top.plot(dates, ma200, label="200-day average", color="orange")
top.fill_between(dates, lower_band, upper_band, color="grey", alpha=0.2, label="Bollinger Bands")
top.set_title("Bitcoin - last 12 months (USD)")
top.legend(loc="upper right")
top.grid(alpha=0.3)

middle.plot(dates, rsi_line, color="purple")
middle.axhline(70, color="red", linestyle="--")
middle.axhline(30, color="green", linestyle="--")
middle.set_ylabel("RSI")
middle.set_ylim(0, 100)
middle.grid(alpha=0.3)

bottom.bar(dates, volumes, color="steelblue")
bottom.set_ylabel("Volume ($bn)")
bottom.grid(alpha=0.3)

plt.savefig("bitcoin_chart.png", dpi=120, bbox_inches="tight")

print("Chart saved as bitcoin_chart.png")
print("Price today: $", round(prices[-1]))
print("50-day average: $", round(ma50[-1]))
print("200-day average: $", round(ma200[-1]))

kraken = requests.get(
    "https://api.kraken.com/0/public/OHLC",
    params={"pair": "XBTUSD", "interval": 10080},
    timeout=10,
).json()
weekly = kraken["result"]["XXBTZUSD"]
weekly_closes = [float(row[4]) for row in weekly]
ma200_week = sum(weekly_closes[-200:]) / 200
all_time_high = max(float(row[2]) for row in weekly)
drop_from_high = (prices[-1] / all_time_high - 1) * 100

fng30 = requests.get("https://api.alternative.me/fng/", params={"limit": 30}, timeout=10).json()
mood_30 = sum(int(d["value"]) for d in fng30["data"]) / len(fng30["data"])

print("200-week average: $", round(ma200_week))
print("All-time high: $", round(all_time_high))
print("Below all-time high by:", round(drop_from_high, 1), "%")
print("Average mood (30 days):", round(mood_30))

price = prices[-1]
bull_signs = []
bear_signs = []

if price > ma200[-1]:
    bull_signs.append(f"Price is above the 200-day average (${round(ma200[-1]):,})")
else:
    bear_signs.append(f"Price is below the 200-day average (${round(ma200[-1]):,})")

if ma50[-1] > ma200[-1]:
    bull_signs.append("The 50-day average is above the 200-day (golden cross)")
else:
    bear_signs.append("The 50-day average is below the 200-day (death cross)")

if price > ma200_week * 1.2:
    bull_signs.append(f"Price is well above the 200-week floor (${round(ma200_week):,})")
else:
    bear_signs.append(f"Price is close to or below the 200-week floor (${round(ma200_week):,})")

if drop_from_high > -20:
    bull_signs.append("Price is within 20% of the all-time high")
elif drop_from_high < -30:
    bear_signs.append(f"Price is still {round(-drop_from_high)}% below the all-time high")

if ma200[-1] > ma200[-31]:
    bull_signs.append("The 200-day average is rising")
else:
    bear_signs.append("The 200-day average is falling")

if mood_30 > 55:
    bull_signs.append(f"Mood has been positive for a month (average {round(mood_30)})")
elif mood_30 < 40:
    bear_signs.append(f"Mood has been fearful for a month (average {round(mood_30)})")

if len(bull_signs) >= 5:
    verdict = "BULL MARKET"
elif len(bear_signs) >= 5:
    verdict = "BEAR MARKET"
else:
    verdict = "TRANSITION (mixed signals)"

print()
print("THE BIG PICTURE:", verdict)
print("Bull signs:", len(bull_signs))
for sign in bull_signs:
    print("  + " + sign)
print("Bear signs:", len(bear_signs))
for sign in bear_signs:
    print("  - " + sign)

levels = [
    (all_time_high * 0.8, "Within 20% of the record high - bull market confirmed"),
    (all_time_high * 0.7, "Out of 'deep drop' territory"),
    (price, "<-- PRICE TODAY"),
    (ma50[-1], "50-day average - a normal pullback zone in an uptrend"),
    (ma200_week * 1.2, "Below here, the verdict likely drops to TRANSITION"),
    (ma200[-1], "200-day average - below here the long-term trend turns down"),
    (ma200_week, "200-week floor - past bear markets bottomed near or below it"),
]
levels.sort(reverse=True)

print()
print("KEY PRICE LEVELS (highest to lowest)")
for level, meaning in levels:
    print(f"  ${round(level):,}  {meaning}")

print()
print("IF A BEAR MARKET RETURNS - past falls from the peak, in today's dollars")
for fall, label in [(50, "a mild bear market"), (65, "a deep bear market"), (77, "like the 2022 bear market"), (84, "like the 2018 bear market")]:
    print(f"  -{fall}%: ${round(all_time_high * (1 - fall / 100)):,}  ({label})")

changes_30 = [prices[i] / prices[i - 30] - 1 for i in range(30, len(prices))]
pct = statistics.quantiles(changes_30, n=100)

print()
print("WHERE COULD WE BE IN 30 DAYS? (based on the past year, not a forecast)")
print(f"  Half the time: between ${round(price * (1 + pct[24])):,} and ${round(price * (1 + pct[74])):,}")
print(f"  1 in 4 times: lower than ${round(price * (1 + pct[24])):,}")
print(f"  1 in 4 times: higher than ${round(price * (1 + pct[74])):,}")
print(f"  Rare extremes (1 in 10): below ${round(price * (1 + pct[9])):,} or above ${round(price * (1 + pct[89])):,}")

updated = datetime.now().strftime("%A %d %B %Y at %H:%M")

if verdict == "BULL MARKET":
    summary = "Most long-term signals point up: Bitcoin is in an uptrend. Dips along the way are still normal."
elif verdict == "BEAR MARKET":
    summary = "Most long-term signals point down: Bitcoin is in a downtrend. Rallies may fade until the trend turns."
else:
    summary = "The signals are mixed. Markets often spend weeks or months here before choosing a direction."

bull_list = "".join(f"<li>{sign}</li>" for sign in bull_signs) or "<li>None</li>"
bear_list = "".join(f"<li>{sign}</li>" for sign in bear_signs) or "<li>None</li>"

style = """
body { font-family: Arial, sans-serif; max-width: 950px; margin: 30px auto; padding: 0 16px; color: #222; line-height: 1.5; }
.updated { color: #777; }
.verdict { font-size: 26px; font-weight: bold; padding: 16px; border-radius: 8px; background: #f2f2f2; }
.bull { color: #1a7f37; }
.bear { color: #c62828; }
img { width: 100%; border: 1px solid #ddd; border-radius: 8px; }
"""

page = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
   <meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bitcoin Report</title>
<style>{style}</style>
</head>
<body>
<h1>Bitcoin Report</h1>
<p class="updated">Last updated: {updated} &middot; Price: ${round(price):,}</p>

<div class="verdict">The big picture: {verdict}</div>
<p>{summary}</p>

<h2 class="bull">Bull signs ({len(bull_signs)})</h2>
<ul>{bull_list}</ul>
<h2 class="bear">Bear signs ({len(bear_signs)})</h2>
<ul>{bear_list}</ul>

<h2>The chart</h2>
<img src="bitcoin_chart.png">
</body>
</html>"""

levels_rows = "".join(f"<tr><td>${round(level):,}</td><td>{meaning}</td></tr>" for level, meaning in levels)

bear_rows = ""
for fall, label in [(50, "a mild bear market"), (65, "a deep bear market"), (77, "like the 2022 bear market"), (84, "like the 2018 bear market")]:
    bear_rows += f"<tr><td>-{fall}%</td><td>${round(all_time_high * (1 - fall / 100)):,}</td><td>{label}</td></tr>"

low_25 = round(price * (1 + pct[24]))
high_75 = round(price * (1 + pct[74]))
low_10 = round(price * (1 + pct[9]))
high_90 = round(price * (1 + pct[89]))

extra = f"""
<style>td {{ padding: 6px 14px; border-bottom: 1px solid #eee; }}</style>

<h2>Key price levels</h2>
<p>Levels <b>above</b> today's price are targets. Levels <b>below</b> are warning lines.</p>
<table>{levels_rows}</table>

<h2>Where could we be in 30 days?</h2>
<p>Based on every 30-day period in the past year. This is history, not a forecast.</p>
<ul>
<li><b>Half the time:</b> between ${low_25:,} and ${high_75:,}</li>
<li><b>1 in 4 times:</b> lower than ${low_25:,}</li>
<li><b>1 in 4 times:</b> higher than ${high_75:,}</li>
<li><b>Rare extremes (1 in 10):</b> below ${low_10:,} or above ${high_90:,}</li>
</ul>

<h2>If a bear market returns</h2>
<p>How far past bear markets fell from their peak, applied to today's record high of ${round(all_time_high):,}. Bitcoin is currently {round(-drop_from_high)}% below its record.</p>
<table>{bear_rows}</table>

<h2>How to read this report</h2>
<ul>
<li><b>Moving average:</b> the average price over the last X days, drawn as a smooth line. It shows the trend without the daily noise.</li>
<li><b>Golden cross:</b> the 50-day line rises above the 200-day line. Recent prices are beating the long-term trend, which has often come before or during bull runs.</li>
<li><b>Death cross:</b> the 50-day line falls below the 200-day line. A warning that has often come before longer declines.</li>
<li><b>200-week floor:</b> the average price over about 4 years. Past bear markets bottomed near or below it, so it is seen as deep support.</li>
<li><b>Bollinger Bands (grey area):</b> the normal range for the price. Touching the top means stretched high; the bottom means stretched low; a very narrow band often comes before a big move.</li>
<li><b>RSI (purple line):</b> 0 to 100. Above 70 means it rose fast and may pause; below 30 means it fell fast and may bounce.</li>
<li><b>Volume (blue bars):</b> how much was traded. Big moves on high volume are more convincing than moves on low volume.</li>
<li><b>Mood (Fear &amp; Greed):</b> how emotional the market is. Extreme fear has often been near bottoms, extreme greed near tops.</li>
</ul>
<p class="updated">This report describes trends and history. It is not financial advice and cannot predict the future.</p>
"""

page = page.replace("</body>", extra + "</body>")
with open("report.html", "w", encoding="utf-8") as file:
    file.write(page)
print("Report saved as report.html")