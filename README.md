# Collection Pulse — Faherty Brand

Weekly AI-powered merchandising signal aggregator. Combines Google Trends, Reddit cultural signals, and inventory data into a structured brief written by Claude.

---

## Setup (one time)

### 1. Make sure Python is installed
Open your terminal and run:
```
python --version
```
You need Python 3.10 or higher. If not installed, download from https://python.org.

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Mac / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```
You'll see `(venv)` at the start of your terminal line when it's active.

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Add your Anthropic API key
Copy the example env file:
```
cp .env.example .env
```
Open `.env` and replace `your-api-key-goes-here` with your real key from https://console.anthropic.com.

---

## Run the app

```
streamlit run app.py
```

A browser window will open automatically at http://localhost:8501.

Click **"Generate this week's pulse →"** and wait ~15 seconds for the brief to appear.

---

## File structure

```
collection-pulse/
├── app.py              # Streamlit dashboard — run this
├── data_fetchers.py    # Google Trends, Reddit, holiday calendar, inventory, scorer
├── ai_analyzer.py      # Claude API call and prompt
├── inventory.json      # Mock inventory data (replace with Shopify API in production)
├── requirements.txt    # Python dependencies
├── .env                # Your API key (never commit this)
└── .env.example        # Safe template to share
```

---

## Signal sources

| Source | What it provides | API key needed? |
|---|---|---|
| Google Trends (PyTrends) | Search interest for Faherty-relevant terms, past 7 days | No |
| Reddit (5 subreddits) | Cultural keyword mentions in fashion + travel communities | No |
| Holiday calendar | Days until next beach/resort holiday | No |
| Inventory feed | Sell-through rate, weeks of supply, units sold | No (mock file) |

---

## How demand scoring works

Before Claude sees any data, a Python scorer converts raw signals into demand flags:

- **HIGH** — sell-through ≥ 65%, OR a beach holiday within 21 days for warm-weather categories
- **MODERATE** — seasonal fit, no strong accelerator
- **LOW** — off-season category

Inventory flags:
- 🔴 **Reorder risk** — under 4 weeks of supply
- 🟡 **Markdown risk** — over 12 weeks of supply
- 🟢 **Healthy** — 4–12 weeks

This separation means every recommendation is traceable back to a rule, not just "the AI said so."

---

## Production upgrades

1. Replace `inventory.json` with a live Shopify or NetSuite API call
2. Add a competitor price-change feed (even a simple weekly scraper)
3. Add Instagram/TikTok hashtag volume via social listening API
4. Schedule the brief to run automatically every Monday morning
