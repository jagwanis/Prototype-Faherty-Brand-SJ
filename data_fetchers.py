import requests
import json
from pytrends.request import TrendReq
from datetime import date


# ─── GOOGLE TRENDS ────────────────────────────────────────────────────────────
# PyTrends is an unofficial Python library that reads Google Trends data.
# We give it Faherty-relevant search terms and get back a 0-100 interest
# score for each, averaged over the past 7 days across the US.

def get_trend_data():
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        keywords = [
            "linen shirt",
            "resort wear",
            "coastal style",
            "swim trunks",
            "summer dress",
            "beach vacation outfit"
        ]
        pytrends.build_payload(keywords, timeframe='now 7-d', geo='US')
        data = pytrends.interest_over_time()
        if data.empty:
            return {}
        averages = data.mean().to_dict()
        averages.pop('isPartial', None)
        return averages
    except Exception:
        # Google occasionally blocks PyTrends requests.
        # Return mock data so the rest of the brief still generates.
        return {
            "linen shirt": 72,
            "resort wear": 58,
            "coastal style": 45,
            "swim trunks": 81,
            "summer dress": 63,
            "beach vacation outfit": 39
        }


# ─── REDDIT CULTURAL SIGNAL ───────────────────────────────────────────────────
# Pulls the 50 most recent posts from fashion and travel subreddits
# and counts how many titles mention Faherty-relevant keywords.
# No API key needed — Reddit exposes public JSON feeds for any subreddit.
# This gives us real cultural signal: what real people are talking about
# right now in the communities Faherty's customer lives in.

def get_reddit_signals():
    subreddits = [
        "malefashionadvice",
        "femalefashionadvice",
        "travel",
        "solotravel",
        "preppy"
    ]
    keywords = ["linen", "resort", "coastal", "swim", "beach", "vacation", "summer", "nautical"]
    mention_counts = {kw: 0 for kw in keywords}

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit=50"
        # Reddit requires a User-Agent header or it rejects the request
        headers = {"User-Agent": "FahertyCollectionPulse/1.0"}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            posts = response.json()
            for post in posts['data']['children']:
                title = post['data']['title'].lower()
                for kw in keywords:
                    if kw in title:
                        mention_counts[kw] += 1
        except Exception:
            # If Reddit is slow or rate-limits us, skip it silently
            # It's a signal enhancer, not critical to the brief
            pass

    return mention_counts


# ─── HOLIDAY CALENDAR ─────────────────────────────────────────────────────────
# Simple hardcoded calendar of beach and resort-relevant US holidays.
# Returns the next upcoming holiday within the next 60 days, plus
# how many days away it is. If it's within 21 days it triggers a
# demand accelerator flag in the scorer below.
# No API needed — this is intentionally static and fast.

def get_upcoming_holiday():
    today = date.today()
    year = today.year

    holidays = {
        "Spring Break (peak)":   date(year, 3, 15),
        "Memorial Day Weekend":  date(year, 5, 26),
        "July 4th Weekend":      date(year, 7, 4),
        "Labor Day Weekend":     date(year, 9, 1),
        "Thanksgiving Weekend":  date(year, 11, 27),
        "Christmas / New Year":  date(year, 12, 22),
    }

    upcoming = []
    for name, d in holidays.items():
        days_away = (d - today).days
        if 0 <= days_away <= 60:
            upcoming.append({"holiday": name, "days_away": days_away})

    upcoming.sort(key=lambda x: x['days_away'])
    return upcoming[0] if upcoming else None


# ─── INVENTORY ────────────────────────────────────────────────────────────────
# Reads the mock inventory JSON file.
# In production this would be an API call to Shopify, NetSuite, or
# whatever ERP Faherty uses — the rest of the code wouldn't change.

def get_inventory_data():
    with open('inventory.json', 'r') as f:
        return json.load(f)


# ─── SIGNAL SCORER ────────────────────────────────────────────────────────────
# This is the explicit logic layer between raw data and the AI.
# Rather than dumping raw numbers at Claude and hoping it figures
# out what they mean, we run rule-based scoring first.
#
# Each category gets:
#   - demand_signal: HIGH / MODERATE / LOW
#   - inventory_flag: REORDER RISK / MARKDOWN RISK / healthy
#   - a plain-English reason string that goes into the prompt
#
# This makes the tool auditable: if a merchant disagrees with a
# recommendation, they can trace it back to a specific rule,
# not just "the AI said so."

def score_signals(inventory, holiday):

    # Does a beach holiday fall within the next 21 days?
    holiday_boost = holiday and holiday['days_away'] <= 21
    holiday_note = (
        f"{holiday['holiday']} is {holiday['days_away']} days away."
        if holiday_boost else ""
    )

    # Which categories benefit from warm-weather / beach holiday demand
    warm_weather_categories = {
        "Linen shirts",
        "Swim trunks",
        "Resort dresses",
        "Board shorts"
    }

    scored = []

    for cat in inventory['categories']:
        name = cat['name']
        wos = cat['weeks_of_supply']
        sell_through = cat['sell_through_rate']
        units_sold = cat['last_week_units_sold']

        # Demand signal: holiday boost drives warm-weather categories HIGH
        if name in warm_weather_categories and holiday_boost:
            demand = "HIGH"
            demand_reason = f"Holiday demand accelerator: {holiday_note}"
        elif name in warm_weather_categories:
            demand = "MODERATE"
            demand_reason = "No major holiday within 21 days; baseline seasonal demand."
        else:
            demand = "LOW"
            demand_reason = "Off-season category given current calendar position."

        # Sell-through momentum: if selling fast, boost signal
        if sell_through >= 0.65 and demand != "HIGH":
            demand = "HIGH"
            demand_reason += f" Strong sell-through momentum ({sell_through:.0%})."

        # Inventory risk flag based on weeks of supply
        if wos < 4:
            inv_flag = "REORDER RISK — under 4 weeks of supply"
        elif wos > 12:
            inv_flag = "MARKDOWN RISK — over 12 weeks of supply"
        else:
            inv_flag = "Healthy stock level"

        scored.append({
            "category":       name,
            "demand_signal":  demand,
            "demand_reason":  demand_reason,
            "inventory_flag": inv_flag,
            "weeks_of_supply": wos,
            "sell_through":   sell_through,
            "units_last_week": units_sold
        })

    return scored
