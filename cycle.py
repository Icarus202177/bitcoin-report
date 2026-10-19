import requests
from datetime import date

url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
settings = {
    "assets": "btc",
    "metrics": "PriceUSD,CapMrktCurUSD,CapMVRVCur,IssTotUSD",
    "frequency": "1d",
    "start_time": "2010-07-18",
    "page_size": 10000,
}
rows = requests.get(url, params=settings, timeout=60).json()["data"]

dates = [date.fromisoformat(row["time"][:10]) for row in rows]
prices = [float(row["PriceUSD"]) for row in rows]
today = dates[-1]
print("History:", len(prices), "days, from", dates[0], "to", today)

halvings = [date(2012, 11, 28), date(2016, 7, 9), date(2020, 5, 11), date(2024, 4, 20)]


def highest(start, end):
    best = None
    for d, p in zip(dates, prices):
        if start <= d <= end and (best is None or p > best[1]):
            best = (d, p)
    return best


def lowest(start, end):
    best = None
    for d, p in zip(dates, prices):
        if start <= d <= end and (best is None or p < best[1]):
            best = (d, p)
    return best


def price_on(day):
    return prices[dates.index(day)]


cycles = []
previous_peak = highest(dates[0], halvings[0])
for i, halving in enumerate(halvings):
    cycle_end = halvings[i + 1] if i + 1 < len(halvings) else today
    peak = highest(halving, min(cycle_end, date.fromordinal(halving.toordinal() + 1000)))
    bottom = lowest(previous_peak[0], peak[0])
    bear_low = lowest(peak[0], cycle_end)
    cycles.append({
        "halving": halving,
        "halving_price": price_on(halving),
        "peak": peak,
        "bottom": bottom,
        "bear_low": bear_low,
    })
    previous_peak = peak

days_now = (today - halvings[-1]).days
print()
print("Today is day", days_now, "after the", halvings[-1], "halving")
print()
for c in cycles:
    h = c["halving"]
    peak_date, peak_price = c["peak"]
    low_date, low_price = c["bear_low"]
    bottom_date, bottom_price = c["bottom"]
    print(f"Halving {h}  price ${c['halving_price']:,.0f}")
    print(f"   Cycle bottom before: ${bottom_price:,.0f} on {bottom_date}")
    print(f"   Peak: ${peak_price:,.0f} on {peak_date}  = {(peak_date - h).days} days after halving, {(peak_date - bottom_date).days} days after the bottom, x{peak_price / c['halving_price']:.1f} from halving")
    print(f"   Lowest after peak: ${low_price:,.0f} on {low_date}  = {(low_price / peak_price - 1) * 100:.0f}% from peak, {(low_date - peak_date).days} days after peak")
    same_day = h.fromordinal(h.toordinal() + days_now)
    if same_day <= today:
        print(f"   At day {days_now}: ${price_on(same_day):,.0f} = {(price_on(same_day) / c['halving_price'] - 1) * 100:+.0f}% vs halving price")
    print()

    import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

colors = ["tab:gray", "tab:blue", "tab:green", "tab:red"]

plt.figure(figsize=(11, 6))
for c, color in zip(cycles, colors):
    h = c["halving"]
    start = dates.index(h)
    end = min(start + 1460, len(prices))
    xs = list(range(0, end - start))
    ys = [prices[start + x] / c["halving_price"] * 100 for x in xs]
    current = c is cycles[-1]
    plt.plot(xs, ys, color=color, linewidth=3 if current else 1.5, label=f"{h.year} halving" + (" (current)" if current else ""))
    peak_date, peak_price = c["peak"]
    low_date, low_price = c["bear_low"]
    plt.scatter([(peak_date - h).days], [peak_price / c["halving_price"] * 100], color=color, marker="^", s=90, zorder=5)
    plt.scatter([(low_date - h).days], [low_price / c["halving_price"] * 100], color=color, marker="v", s=90, zorder=5)
plt.axvline(days_now, color="black", linestyle="--", linewidth=1, label=f"Today (day {days_now})")
plt.axhline(100, color="black", linewidth=0.8)
plt.yscale("log")
plt.title("Chart A - Each halving cycle, indexed to 100 on halving day  (^ = peak, v = low after peak)")
plt.xlabel("Days since halving")
plt.ylabel("Index (halving day = 100, log scale)")
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("cycle_compare.png", dpi=110, bbox_inches="tight")
plt.close()

plt.figure(figsize=(11, 6))
plt.plot(dates, prices, color="black", linewidth=1, label="Bitcoin price")
for c in cycles:
    first = c is cycles[0]
    plt.axvline(c["halving"], color="orange", linestyle="--", linewidth=1, label="Halving" if first else None)
    plt.scatter([c["peak"][0]], [c["peak"][1]], color="red", marker="^", s=90, zorder=5, label="Cycle peak" if first else None)
    plt.scatter([c["bottom"][0], c["bear_low"][0]], [c["bottom"][1], c["bear_low"][1]], color="green", marker="v", s=90, zorder=5, label="Cycle low" if first else None)
plt.scatter([today], [prices[-1]], color="blue", s=90, zorder=6, label="Today")
plt.yscale("log")
plt.title("Chart B - Bitcoin price history with halvings, peaks and lows")
plt.ylabel("Price (USD, log scale)")
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("cycle_timeline.png", dpi=110, bbox_inches="tight")
plt.close()
print("Charts saved: cycle_compare.png and cycle_timeline.png")

past_peak_days = [(c["peak"][0] - c["halving"]).days for c in cycles[:-1]]
past_low_gaps = [(c["bear_low"][0] - c["peak"][0]).days for c in cycles[:-1]]
current = cycles[-1]
peak_date, peak_price = current["peak"]
low_date, low_price = current["bear_low"]
price_now = prices[-1]

summary = []
summary.append(f"Today ({today}) is day {days_now} after the {current['halving']} halving. The price (${price_now:,.0f}) is {(price_now / current['halving_price'] - 1) * 100:+.0f}% compared with halving day.")

past = []
for c in cycles[:-1]:
    same_day = date.fromordinal(c["halving"].toordinal() + days_now)
    change = (price_on(same_day) / c["halving_price"] - 1) * 100
    stage = "already past its peak" if same_day > c["peak"][0] else "still before its peak"
    past.append(f"the {c['halving'].year} cycle was {change:+.0f}% ({stage})")
summary.append(f"At the same day after their halvings, " + "; ".join(past) + ".")

summary.append(f"This cycle's highest price so far is ${peak_price:,.0f} on {peak_date}, day {(peak_date - current['halving']).days}. Earlier cycles peaked on days {', '.join(str(d) for d in past_peak_days)} after their halving.")

if low_date > peak_date:
    first_low = date.fromordinal(peak_date.toordinal() + min(past_low_gaps))
    last_low = date.fromordinal(peak_date.toordinal() + max(past_low_gaps))
    summary.append(f"Since that high, the price fell {(low_price / peak_price - 1) * 100:.0f}% to ${low_price:,.0f} on {low_date}, and is now {(price_now / low_price - 1) * 100:+.0f}% above that low. In earlier cycles the bear-market low came {min(past_low_gaps)} to {max(past_low_gaps)} days after the peak; for this cycle that timing would be {first_low} to {last_low}.")
else:
    summary.append("The price is at or near its highest level of this cycle, so no bear-market fall has started yet.")

multiples = [f"{c['halving'].year}: x{c['peak'][1] / c['halving_price']:.1f}" for c in cycles]
summary.append("Peak gain from the halving-day price, by cycle: " + ", ".join(multiples) + ".")
summary.append("This compares timing with past cycles only. It shows what happened before, not what must happen now.")

print()
print("WHAT CHARTS A AND B SAY TODAY")
for sentence in summary:
    print("- " + sentence)

def moving_average(values, days):
    result = []
    for i in range(len(values)):
        if i + 1 < days:
            result.append(float("nan"))
        else:
            result.append(sum(values[i + 1 - days : i + 1]) / days)
    return result


ma111 = moving_average(prices, 111)
ma350x2 = [value * 2 for value in moving_average(prices, 350)]

crosses = []
for i in range(1, len(prices)):
    if ma111[i - 1] <= ma350x2[i - 1] and ma111[i] > ma350x2[i]:
        crosses.append(dates[i])

print()
print("PI CYCLE TOP - every time the 111-day line crossed above 2 x 350-day line:")
for cross in crosses:
    top_date, top_price = highest(date.fromordinal(cross.toordinal() - 30), date.fromordinal(cross.toordinal() + 30))
    earlier = [h for h in halvings if h <= cross]
    since = f"{(cross - earlier[-1]).days} days after the {earlier[-1].year} halving" if earlier else "before the first halving"
    print(f"  {cross}: {since}; nearby price top ${top_price:,.0f} on {top_date} ({(top_date - cross).days:+d} days from the cross)")

caught = 0
for c in cycles:
    near = [x for x in crosses if abs((x - c["peak"][0]).days) <= 30]
    if near:
        caught += 1
        print(f"  {c['halving'].year} cycle peak {c['peak'][0]}: crossed {(near[0] - c['peak'][0]).days:+d} days from the peak")
    else:
        print(f"  {c['halving'].year} cycle peak {c['peak'][0]}: NO cross near the peak")

gap_now = (ma111[-1] / ma350x2[-1] - 1) * 100
gap_before = (ma111[-31] / ma350x2[-31] - 1) * 100
direction = "getting closer together" if abs(gap_now) < abs(gap_before) else "moving further apart"
crosses_this_cycle = [x for x in crosses if x >= halvings[-1]]

pi_summary = []
pi_summary.append(f"The 111-day average is ${ma111[-1]:,.0f} and twice the 350-day average is ${ma350x2[-1]:,.0f}. The fast line is {abs(gap_now):.0f}% {'below' if gap_now < 0 else 'above'} the slow line, and the two are {direction} compared with 30 days ago ({gap_before:+.0f}% then).")
if gap_now < 0:
    pi_summary.append("A Pi Cycle top signal needs the fast line to cross ABOVE the slow line, so there is no top signal today.")
else:
    pi_summary.append("The fast line is ABOVE the slow line - the condition seen around past cycle tops.")
if crosses_this_cycle:
    pi_summary.append(f"In this cycle it crossed on {', '.join(str(x) for x in crosses_this_cycle)}.")
else:
    pi_summary.append(f"It has not crossed at all since the {halvings[-1]} halving - including at the {cycles[-1]['peak'][0]} high - so this cycle's high was NOT flagged by this indicator.")
pi_summary.append(f"History: it crossed {len(crosses)} times, and was within 30 days of {caught} of the {len(cycles)} cycle peaks.")
pi_summary.append("The gap between the lines is not a countdown: in the past the lines closed at very different speeds.")

print()
print("WHAT THE PI CYCLE CHART SAYS TODAY")
for sentence in pi_summary:
    print("- " + sentence)

plt.figure(figsize=(11, 6))
plt.plot(dates, prices, color="lightgray", linewidth=1, label="Bitcoin price")
plt.plot(dates, ma111, color="tab:blue", linewidth=1.5, label="111-day average")
plt.plot(dates, ma350x2, color="tab:red", linewidth=1.5, label="2 x 350-day average")
for x in crosses:
    plt.axvline(x, color="purple", linestyle=":", linewidth=1.5, label="Cross (top signal)" if x == crosses[0] else None)
for c in cycles:
    plt.scatter([c["peak"][0]], [c["peak"][1]], color="red", marker="^", s=90, zorder=5, label="Cycle peak" if c is cycles[0] else None)
plt.yscale("log")
plt.title("Pi Cycle Top: 111-day average vs 2 x 350-day average")
plt.ylabel("Price (USD, log scale)")
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("pi_cycle.png", dpi=110, bbox_inches="tight")
plt.close()
print("Chart saved: pi_cycle.png")

month_dates = []
month_closes = []
for d, p in zip(dates, prices):
    if month_dates and (d.year, d.month) == (month_dates[-1].year, month_dates[-1].month):
        month_dates[-1] = d
        month_closes[-1] = p
    else:
        month_dates.append(d)
        month_closes.append(p)


def wilder_rsi(values, period):
    result = [float("nan")] * len(values)
    gains = [max(values[i] - values[i - 1], 0) for i in range(1, len(values))]
    losses = [max(values[i - 1] - values[i], 0) for i in range(1, len(values))]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(values)):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        result[i] = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    return result


rsi_14m = wilder_rsi(month_closes, 14)
rsi_smooth = moving_average(rsi_14m, 3)

past_tops = []
past_bottoms = []
for i, c in enumerate(cycles[:-1]):
    top_end = date.fromordinal(c["halving"].toordinal() + 1000)
    tops = [r for d, r in zip(month_dates, rsi_14m) if c["halving"] <= d <= top_end and r == r]
    bottoms = [r for d, r in zip(month_dates, rsi_14m) if c["peak"][0] <= d <= halvings[i + 1] and r == r]
    past_tops.append(round(max(tops)))
    past_bottoms.append(round(min(bottoms)))
this_cycle_top = round(max(r for d, r in zip(month_dates, rsi_14m) if d >= halvings[-1]))

rsi_now = rsi_14m[-1]
rsi_3m_ago = rsi_14m[-4]
rsi_summary = []
rsi_summary.append(f"The 14-month RSI is {rsi_now:.0f} this month (it was {rsi_3m_ago:.0f} three months ago, so it is {'rising' if rsi_now > rsi_3m_ago else 'falling'}). This month is not finished, so today's reading can still change.")
rsi_summary.append(f"Past cycle tops reached {', '.join(str(t) for t in past_tops)}. This cycle's highest reading was {this_cycle_top} - {'lower than every previous top, a weaker peak' if this_cycle_top < min(past_tops) else 'similar to previous tops'}.")
rsi_summary.append(f"Past bear markets bottomed at {', '.join(str(b) for b in past_bottoms)}.")
if rsi_now <= max(past_bottoms) + 5:
    rsi_summary.append("Today's reading is in or near the zone where past bear markets ended - historically an accumulation zone, though it can stay low for months.")
elif rsi_now >= min(past_tops) - 5:
    rsi_summary.append("Today's reading is near the zone of past cycle tops - historically a time of elevated risk.")
else:
    rsi_summary.append("Today's reading is between the past bottom and top zones - a middle stage of the cycle.")
recent_low = min(rsi_14m[-6:])
if recent_low <= max(past_bottoms) + 3 and rsi_now > recent_low + 5:
    rsi_summary.append(f"In the last 6 months it fell to {recent_low:.0f}, inside the zone where past bear markets ended, and has since climbed to {rsi_now:.0f}. In past cycles, climbing out of that zone came near the start of a recovery - but it can also dip back.")
rsi_summary.append("Method: monthly closing prices, 14-month Wilder RSI, as labelled on PlanB's chart. The black line here is our own 3-month average; PlanB does not state how his line is smoothed.")

print()
print("WHAT PLANB'S 14-MONTH RSI CHART SAYS TODAY")
for sentence in rsi_summary:
    print("- " + sentence)

plt.figure(figsize=(11, 6))
plt.plot(month_dates, rsi_smooth, color="black", linewidth=2, label="3-month average (our smoothing)")
dots = plt.scatter(month_dates, rsi_14m, c=rsi_14m, cmap="jet", vmin=45, vmax=85, s=30, zorder=5)
plt.colorbar(dots, label="14-month RSI")
for h in halvings:
    plt.axvline(h, color="orange", linestyle="--", linewidth=1, label="Halving" if h == halvings[0] else None)
plt.ylim(30, 100)
plt.title("Bitcoin 14-month RSI (monthly) - after PlanB")
plt.ylabel("RSI (14 months)")
plt.legend(loc="lower left")
plt.grid(alpha=0.3)
plt.savefig("rsi_14m.png", dpi=110, bbox_inches="tight")
plt.close()
print("Chart saved: rsi_14m.png")

import math


def number(row, key):
    return float(row[key]) if row.get(key) else float("nan")


market_cap = [number(row, "CapMrktCurUSD") for row in rows]
mvrv = [number(row, "CapMVRVCur") for row in rows]
issuance = [number(row, "IssTotUSD") for row in rows]

realized_price = [p / m for p, m in zip(prices, mvrv)]
ma200 = moving_average(prices, 200)
ma730 = moving_average(prices, 730)
issuance_365 = moving_average(issuance, 365)

mayer = [p / m for p, m in zip(prices, ma200)]
two_year = [p / m for p, m in zip(prices, ma730)]
puell = [i / m for i, m in zip(issuance, issuance_365)]

z_score = []
count = 0
total = 0.0
total_sq = 0.0
for cap, ratio in zip(market_cap, mvrv):
    if cap == cap:
        count += 1
        total += cap
        total_sq += cap * cap
    spread = math.sqrt(max(total_sq / count - (total / count) ** 2, 0)) if count > 1 else 0
    z_score.append((cap - cap / ratio) / spread if spread > 0 and ratio == ratio else float("nan"))

week_index = list(range(len(prices) - 1, -1, -7))[::-1]
week_dates = [dates[i] for i in week_index]
week_rsi = wilder_rsi([prices[i] for i in week_index], 14)


def value_on(series_dates, series, day):
    last = float("nan")
    for d, v in zip(series_dates, series):
        if d > day:
            break
        last = v
    return last


def zone(value, limits):
    labels = ["UNDERVALUED", "NORMAL", "ELEVATED", "OVERHEATED"]
    for label, limit in zip(labels, limits):
        if value < limit:
            return label
    return labels[-1]


metrics = [
    ("MVRV", dates, mvrv, (1.0, 2.4, 3.7), "market value / what holders paid on average"),
    ("MVRV Z-Score", dates, z_score, (0.0, 3.0, 7.0), "how far market value is above what holders paid, in standard deviations"),
    ("Mayer Multiple", dates, mayer, (0.8, 1.5, 2.4), "price / 200-day average"),
    ("2-Year MA Multiplier", dates, two_year, (1.0, 3.0, 5.0), "price / 2-year average (5x has marked past tops)"),
    ("Puell Multiple", dates, puell, (0.5, 1.5, 2.5), "miners' daily income / its 1-year average"),
    ("Weekly RSI (14 weeks)", week_dates, week_rsi, (30, 70, 85), "medium-term momentum, 0 to 100"),
]

valuation_rows = []
valuation_summary = []
print()
print("VALUATION METRICS TODAY")
for name, series_dates, series, limits, meaning in metrics:
    now = series[-1]
    label = zone(now, limits)
    at_peaks = ", ".join(f"{value_on(series_dates, series, c['peak'][0]):.1f}" for c in cycles[:-1])
    at_lows = ", ".join(f"{value_on(series_dates, series, c['bear_low'][0]):.1f}" for c in cycles[:-1])
    valuation_rows.append((name, now, label))
    sentence = f"{name} ({meaning}) is {now:.2f}: {label}. At past cycle peaks it was   {at_peaks} (this cycle's high: {value_on(series_dates, series, cycles[-1]['peak'][0]):.1f});   at past bear-market lows {at_lows}."
    valuation_summary.append(sentence)
    print("- " + sentence)

valuation_summary.append(f"Realized Price (the average price holders paid) is ${realized_price[-1]:,.0f}; the price is {(prices[-1] / realized_price[-1] - 1) * 100:+.0f}% above it. Past bear markets bottomed near or below this level.")
print("- " + valuation_summary[-1])
counts = {label: sum(1 for row in valuation_rows if row[2] == label) for label in ["UNDERVALUED", "NORMAL", "ELEVATED", "OVERHEATED"]}
valuation_summary.append(f"Overall: {counts['UNDERVALUED']} undervalued, {counts['NORMAL']} normal, {counts['ELEVATED']} elevated, {counts['OVERHEATED']} overheated. Zone limits are commonly used rules of thumb, not guarantees.")
print("- " + valuation_summary[-1])

fig, panels = plt.subplots(5, 1, figsize=(11, 15), sharex=True)
panels[0].plot(dates, prices, color="black", linewidth=1, label="Price")
panels[0].plot(dates, realized_price, color="tab:orange", linewidth=1.5, label="Realized price (avg paid)")
panels[0].plot(dates, ma730, color="tab:green", linewidth=1.5, label="2-year average")
panels[0].plot(dates, [m * 5 for m in ma730], color="tab:red", linewidth=1.5, label="5 x 2-year average")
panels[0].set_yscale("log")
panels[0].set_ylabel("Price (USD, log)")
panels[0].legend(loc="upper left")
panels[0].set_title("Valuation metrics  (red lines = cycle peaks, green dashed = cheap zone, red dashed = overheated zone)")

panel_specs = [
    (panels[1], dates, z_score, "MVRV Z-Score", 0, 7, "linear"),
    (panels[2], dates, mayer, "Mayer Multiple", 0.8, 2.4, "log"),
    (panels[3], dates, puell, "Puell Multiple", 0.5, 2.5, "log"),
    (panels[4], week_dates, week_rsi, "Weekly RSI", 30, 85, "linear"),
]
for ax, xs, ys, name, cheap, hot, scale in panel_specs:
    ax.plot(xs, ys, color="tab:blue", linewidth=1)
    ax.axhline(cheap, color="green", linestyle="--", linewidth=1)
    ax.axhline(hot, color="red", linestyle="--", linewidth=1)
    ax.set_yscale(scale)
    ax.set_ylabel(name)
panels[1].set_ylim(-2, 12)

for ax in panels:
    ax.grid(alpha=0.3)
    for c in cycles:
        ax.axvline(c["peak"][0], color="red", alpha=0.3, linewidth=2)

plt.savefig("valuation.png", dpi=100, bbox_inches="tight")
plt.close()
print("Chart saved: valuation.png")

if counts["OVERHEATED"] >= 2:
    valuation_meaning = "What this means: several measures are at levels seen near past cycle tops - historically a high-risk time."
elif counts["ELEVATED"] + counts["OVERHEATED"] >= 2:
    valuation_meaning = "What this means: some measures are getting expensive - caution is rising, though not yet at past top levels."
elif counts["UNDERVALUED"] >= 3:
    valuation_meaning = "What this means: most measures are at levels seen near past bottoms - historically a good long-term buying zone, though prices can stay low for months."
else:
    valuation_meaning = "What this means: Bitcoin looks fairly valued - not cheap like at past bottoms, and far from expensive like at past tops."
valuation_summary.append(valuation_meaning)
print("- " + valuation_meaning)

sections = [
    ("1. Where are we in the halving cycle?",
     "Every four years the reward for mining new bitcoin is cut in half (the 'halving'). Past cycles followed a similar rhythm: a peak about 1 to 1.5 years after the halving, then a bear market. Chart A starts every cycle at 100 on halving day so they can be compared fairly; Chart B shows the whole price history.",
     summary, ["cycle_compare.png", "cycle_timeline.png"]),
    ("2. Pi Cycle Top",
     "Two averages: a fast one (111 days, blue) and a slow one (2 x 350 days, red). When the blue line rose above the red one, the market was overheating - in 2013 and 2017 this happened within days of the top.",
     pi_summary, ["pi_cycle.png"]),
    ("3. PlanB's 14-month RSI",
     "A 'speedometer' for long-term momentum, from 0 to 100. Readings above about 90 came at past tops; readings in the low 40s came at past bear-market bottoms.",
     rsi_summary, ["rsi_14m.png"]),
    ("4. Valuation: is Bitcoin cheap or expensive?",
     "Six ways of comparing today's price with Bitcoin's own history. Green dashed lines show levels seen near past bottoms, red dashed lines levels seen near past tops.",
     valuation_summary, ["valuation.png"]),
]

style = """
body { font-family: Arial, sans-serif; max-width: 950px; margin: 30px auto; padding: 0 16px; color: #222; line-height: 1.5; }
.small { color: #777; }
.today { background: #f2f6ff; border-left: 4px solid #3366cc; padding: 8px 16px; border-radius: 6px; }
img { width: 100%; border: 1px solid #ddd; border-radius: 8px; margin: 8px 0; }
"""

body = ""
for title, explanation, sentences, images in sections:
    body += f"<h2>{title}</h2>\n<p>{explanation}</p>\n"
    body += "<div class='today'><b>What it says today</b><ul>" + "".join(f"<li>{s}</li>" for s in sentences) + "</ul></div>\n"
    body += "".join(f"<img src='{image}'>\n" for image in images)

cycle_page = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bitcoin Cycle Analysis</title>
<style>{style}</style>
</head>
<body>
<p><a href="report.html">&larr; Back to the daily report</a></p>
<h1>Bitcoin Cycle Analysis</h1>
<p class="small">Data up to {today} &middot; Price ${prices[-1]:,.0f} &middot; Source: Coin Metrics community data (free)</p>
{body}
<p class="small">This page describes history and current readings. It is not financial advice and cannot predict the future.</p>
</body>
</html>"""

with open("cycle.html", "w", encoding="utf-8") as file:
    file.write(cycle_page)
print("Page saved: cycle.html")

def extreme_between(series_dates, series, start, end, pick):
    values = [v for d, v in zip(series_dates, series) if start <= d <= end and v == v]
    return pick(values) if values else float("nan")


score_metrics = [(name, series_dates, series) for name, series_dates, series, limits, meaning in metrics]
score_metrics.append(("14-month RSI", month_dates, rsi_14m))

scores = []
for name, series_dates, series in score_metrics:
    tops = [extreme_between(series_dates, series, c["halving"], date.fromordinal(c["peak"][0].toordinal() + 30), max) for c in cycles[-2:]]
    lows = [extreme_between(series_dates, series, c["peak"][0], halvings[i + 1], min) for i, c in enumerate(cycles[:-1])]
    high = sum(tops) / len(tops)
    low = sum(lows) / len(lows)
    position = (series[-1] - low) / (high - low) * 100
    scores.append((name, max(0, min(100, position))))

risk = sum(s for n, s in scores) / len(scores)
if risk < 25:
    state, meaning = "STATE 1 - Accumulation / potential buy zone", "Most indicators look like past bear-market bottoms."
elif risk < 55:
    state, meaning = "STATE 2 - Early or mid-cycle", "Indicators are in the middle: not cheap like past bottoms, not hot like past tops. After a peak, this usually means recovery rather than overheating."
elif risk < 80:
    state, meaning = "STATE 3 - Late-cycle / elevated risk", "Several indicators are approaching levels seen near recent cycle tops."
else:
    state, meaning = "STATE 4 - Potential cycle top / distribution", "Most indicators look like recent cycle tops."

like_bottoms = [n for n, s in scores if s < 30]
middle = [n for n, s in scores if 30 <= s <= 70]
like_tops = [n for n, s in scores if s > 70]

gaps = [(halvings[i + 1] - halvings[i]).days for i in range(len(halvings) - 1)]
next_halving = date.fromordinal(halvings[-1].toordinal() + gaps[-1])
peak_days_all = sorted(past_peak_days + [(peak_date - current["halving"]).days])
window_start = date.fromordinal(next_halving.toordinal() + peak_days_all[0])
window_end = date.fromordinal(next_halving.toordinal() + peak_days_all[-1])
window_mid = date.fromordinal(next_halving.toordinal() + peak_days_all[len(peak_days_all) // 2])

answer_1 = (f"Day {days_now} after the {halvings[-1]:%B %Y} halving. This cycle's high (${peak_price:,.0f} on {peak_date:%d %B %Y}) came on day "
            f"{(peak_date - current['halving']).days}, in line with past peaks (days {', '.join(str(d) for d in past_peak_days)}). "
            f"Since then the price fell {(1 - low_price / peak_price) * 100:.0f}% and is now {(price_now / low_price - 1) * 100:+.0f}% above the {low_date:%B %Y} low. "
            f"At this stage, every earlier cycle was already past its peak.")
answer_2 = (f"If the {peak_date:%B %Y} high was this cycle's top - as the timing suggests - history points to the next cycle top around {window_mid:%B %Y} "
            f"(range {window_start:%B %Y} to {window_end:%B %Y}), 1 to 1.5 years after the next halving expected around {next_halving:%B %Y}. "
            f"If instead the price rises above ${peak_price:,.0f}, this cycle's top is still ahead. "
            f"The Pi Cycle is {abs(gap_now):.0f}% away from a top signal. This is based on only 4 cycles, so treat it as a rough guide, not a forecast.")
answer_3 = (f"Look like past bottoms (support accumulation): {', '.join(like_bottoms) or 'none'}. "
            f"In the middle (support holding): {', '.join(middle) or 'none'}. "
            f"Look like recent tops (call for caution): {', '.join(like_tops) or 'none'}.")

print()
print(f"CYCLE-RISK SCORE: {risk:.0f} / 100  ->  {state}")
for name, s in scores:
    print(f"  {name}: {s:.0f}")
print("Q1:", answer_1)
print("Q2:", answer_2)
print("Q3:", answer_3)

score_rows = "".join(f"<tr><td>{n}</td> <td>{s:.0f}</td><td>{'Like past bottoms' if s < 30 else 'In between' if s <= 70 else 'Like recent tops'}</td><td><div style='background:#eee;width:200px'><div style='background:{'#2e7d32' if s < 30 else '#f9a825' if s <= 70 else '#c62828'};width:{s * 2:.0f}px;height:12px'></div></div></td></tr>" for n, s in scores)
big_picture = f"""
<div style="background:#fff8e1;border:2px solid #f9a825;border-radius:10px;padding:12px 20px;margin:16px 0">
<h2>The big picture ({today:%d %B %Y})</h2>
<p style="font-size:20px"><b>Cycle-risk score: {risk:.0f} / 100 &middot; {state}</b><br>{meaning}</p>
<p><b>1. Where are we compared with past halving cycles?</b><br>{answer_1}</p>
<p><b>2. When could the next cycle top be?</b><br>{answer_2}</p>
<p><b>3. Which indicators support buying, holding or caution?</b><br>{answer_3}</p>
   <p><b>How to read the bars:</b> each indicator is scored from 0 (like past bear-market bottoms) to 100 (like recent cycle tops).<br><span style='color:#2e7d32'>&#9632; Green (0-29): looks cheap, like past bottoms</span> &middot; <span style='color:#f9a825'>&#9632; Amber (30-70): in between, normal</span> &middot; <span style='color:#c62828'>&#9632; Red (71-100): looks hot, like past tops</span></p><table>{score_rows}</table>
<p class="small">How the score works: each indicator is placed between its average level at past bear-market lows (0) and its average peak in the last two bull runs (100), then all are averaged. This is a rule-of-thumb score, not tested statistically, and not the probability of a crash or a top.</p>
</div>
"""
cycle_page = cycle_page.replace("<h2>1. Where are we", big_picture + "<h2>1. Where are we")
with open("cycle.html", "w", encoding="utf-8") as file:
    file.write(cycle_page)
print("Page updated with the big picture: cycle.html")

def remove_between(text, start, end):
    while start in text and end in text:
        before, rest = text.split(start, 1)
        text = before + rest.split(end, 1)[1]
    return text


with open("report.html", encoding="utf-8") as file:
    report = file.read()

report = remove_between(report, "<!-- BIG START -->", "<!-- BIG END -->")
report = remove_between(report, "<!-- CYCLE START -->", "<!-- CYCLE END -->")
report = report.replace('<div class="verdict">', "<!-- BIG START -->" + big_picture + "<!-- BIG END -->\n" + '<div class="verdict">', 1)
report = report.replace("</body>", "<!-- CYCLE START -->\n<style>" + style + "</style>\n<hr>\n<h1>Cycle analysis</h1>\n" + body + "<!-- CYCLE END -->\n</body>", 1)

with open("report.html", "w", encoding="utf-8") as file:
    file.write(report)
print("Daily report updated with the cycle analysis: report.html")