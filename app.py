import streamlit as st
import pandas as pd
from data_fetchers import (
    get_trend_data,
    get_reddit_signals,
    get_upcoming_holiday,
    get_inventory_data,
    score_signals,
)
from ai_analyzer import generate_pulse_brief

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Collection Pulse — Faherty Brand",
    page_icon="🌊",
    layout="wide"
)

# ─── FAHERTY BRAND STYLING ────────────────────────────────────────────────────
# Faherty's palette: warm sand, coral, ocean teal, deep navy
st.markdown("""
<style>
    /* Main background and text */
    .stApp {
        background-color: #FAFAF7;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1B3A4B;
    }
    [data-testid="stSidebar"] * {
        color: #E8DFD0 !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #F5EDD9 !important;
    }

    /* Primary button — Faherty coral */
    .stButton > button[kind="primary"] {
        background-color: #C75B3A;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        letter-spacing: 0.03em;
        padding: 0.6rem 1.4rem;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #A84A2D;
        color: white;
    }

    /* Page title */
    h1 {
        color: #1B3A4B !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Section headers */
    h2, h3 {
        color: #1B3A4B !important;
        font-weight: 600 !important;
    }

    /* Brief output box */
    .brief-box {
        background-color: #FFFFFF;
        border: 1px solid #E2D9C8;
        border-left: 4px solid #C75B3A;
        border-radius: 6px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        color: #1B3A4B;
        line-height: 1.7;
    }

    /* Holiday alert */
    .holiday-banner {
        background-color: #FDF3E7;
        border: 1px solid #E8C88A;
        border-radius: 6px;
        padding: 0.75rem 1.2rem;
        margin-bottom: 1rem;
        color: #7A4A0A;
        font-weight: 500;
    }

    /* Divider */
    hr {
        border-color: #E2D9C8 !important;
    }

    /* Dataframe headers */
    .stDataFrame {
        border: 1px solid #E2D9C8;
        border-radius: 6px;
    }

    /* Caption text */
    .stCaption {
        color: #8A7E6E !important;
    }

    /* Status box */
    [data-testid="stStatus"] {
        background-color: #EEF6F4;
        border-color: #2E8B6E;
    }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown("# 🌊 Collection Pulse")
    st.markdown("<p style='color:#6B5E4E; margin-top:-0.5rem; font-size:0.95rem;'>Weekly AI-powered merchandising signal aggregator &nbsp;·&nbsp; Faherty Brand</p>", unsafe_allow_html=True)
with col_badge:
    st.markdown("<div style='text-align:right; padding-top:1rem;'><span style='background:#1B3A4B; color:#E8DFD0; padding:4px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; letter-spacing:0.05em;'>INTERNAL TOOL</span></div>", unsafe_allow_html=True)

st.divider()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Signal sources")
    st.markdown("""
| Source | Type |
|---|---|
| Google Trends | Live |
| Reddit (5 subreddits) | Live |
| Holiday calendar | Static |
| Inventory feed | Mock |
""")
    st.caption("Production upgrade: replace inventory feed with Shopify / NetSuite API.")
    st.divider()
    st.markdown("### How demand signals work")
    st.markdown("""
Each category is pre-scored before the AI sees it:

- **HIGH** — sell-through ≥65% OR beach holiday within 21 days for warm-weather categories
- **MODERATE** — seasonal fit, no strong accelerator
- **LOW** — off-season category

Inventory flags:
- 🔴 **Reorder risk** — under 4 weeks of supply
- 🟡 **Markdown risk** — over 12 weeks of supply
- 🟢 **Healthy** — 4–12 weeks
""")
    st.divider()
    st.markdown("### About")
    st.caption("Built as a prototype to demonstrate AI-assisted merchandising intelligence. Scoring logic is explicit and auditable — every recommendation traces back to a specific rule, not a black box.")

# ─── MAIN BUTTON ──────────────────────────────────────────────────────────────
col_btn, col_spacer = st.columns([2, 5])
with col_btn:
    run = st.button("Generate this week's pulse →", type="primary", use_container_width=True)

if run:
    with st.status("Pulling signals...", expanded=True) as status:
        st.write("📈 Fetching Google Trends data...")
        trends = get_trend_data()

        st.write("💬 Pulling Reddit mentions...")
        reddit = get_reddit_signals()

        st.write("📅 Checking holiday calendar...")
        holiday = get_upcoming_holiday()

        st.write("📦 Loading inventory feed...")
        inventory = get_inventory_data()

        st.write("⚡ Scoring signals...")
        scored = score_signals(inventory, holiday)

        status.update(label="Signals ready — generating brief...", state="running")

        brief = generate_pulse_brief(trends, inventory, reddit, holiday, scored)

        status.update(label="✓ Brief ready.", state="complete")

    st.session_state['brief']     = brief
    st.session_state['trends']    = trends
    st.session_state['reddit']    = reddit
    st.session_state['holiday']   = holiday
    st.session_state['inventory'] = inventory
    st.session_state['scored']    = scored

# ─── RESULTS ──────────────────────────────────────────────────────────────────
if 'brief' in st.session_state:

    st.subheader("This week's brief")

    # Holiday banner
    holiday = st.session_state['holiday']
    if holiday:
        days = holiday['days_away']
        icon = "🔴" if days <= 14 else "🟡"
        st.markdown(
            f"<div class='holiday-banner'>{icon} &nbsp;<strong>{holiday['holiday']}</strong> is <strong>{days} days away</strong> — demand accelerator active for warm-weather categories.</div>",
            unsafe_allow_html=True
        )

    # Brief output
    st.markdown(
        f"<div class='brief-box'>{st.session_state['brief'].replace(chr(10), '<br>')}</div>",
        unsafe_allow_html=True
    )

    st.divider()

    # ── Raw Signals ───────────────────────────────────────────────────────────
    st.subheader("Raw signals")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Google Trends** &nbsp;·&nbsp; 0–100, US, 7-day avg", unsafe_allow_html=True)
        trends = st.session_state['trends']
        if trends:
            trend_df = pd.DataFrame(
                sorted(trends.items(), key=lambda x: -x[1]),
                columns=["Search term", "Interest"]
            )
            trend_df["Interest"] = trend_df["Interest"].round(1)
            st.dataframe(trend_df, hide_index=True, use_container_width=True)
        else:
            st.caption("Using mock trend data (Google rate-limited).")

    with col2:
        st.markdown("**Reddit mentions** &nbsp;·&nbsp; 5 subreddits, 50 posts each", unsafe_allow_html=True)
        reddit = st.session_state['reddit']
        reddit_df = pd.DataFrame(
            sorted(reddit.items(), key=lambda x: -x[1]),
            columns=["Keyword", "Mentions"]
        )
        st.dataframe(reddit_df, hide_index=True, use_container_width=True)

    with col3:
        st.markdown("**Inventory** &nbsp;·&nbsp; scored signals", unsafe_allow_html=True)
        scored = st.session_state['scored']
        inv_rows = []
        for s in scored:
            wos = s['weeks_of_supply']
            if wos < 4:
                flag = "🔴 Reorder"
            elif wos > 12:
                flag = "🟡 Markdown"
            else:
                flag = "🟢 Healthy"
            inv_rows.append({
                "Category":  s['category'],
                "Demand":    s['demand_signal'],
                "WOS":       wos,
                "Sell-thru": f"{s['sell_through']:.0%}",
                "Flag":      flag
            })
        st.dataframe(pd.DataFrame(inv_rows), hide_index=True, use_container_width=True)

    st.divider()
    st.caption("Sources: Google Trends (PyTrends) · Reddit public JSON API · Static holiday calendar · Mock inventory feed")
    st.caption("AI analysis: LLaMA 3.3 70B via Groq API · Demand scoring: rule-based Python logic")
