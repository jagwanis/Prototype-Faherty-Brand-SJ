from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_pulse_brief(trends, inventory, reddit, holiday, scored_signals):
    """
    Sends all pre-processed signals to Groq and returns a structured
    merchandising brief as a markdown string.
    """

    # Format scored signals for the prompt
    signal_lines = ""
    for s in scored_signals:
        signal_lines += (
            f"\n- {s['category']}: "
            f"demand={s['demand_signal']} | "
            f"{s['demand_reason']} | "
            f"inventory={s['inventory_flag']} "
            f"(WOS: {s['weeks_of_supply']}, "
            f"sell-through: {s['sell_through']:.0%}, "
            f"units last week: {s['units_last_week']})"
        )

    holiday_text = (
        f"{holiday['holiday']} is {holiday['days_away']} days away — demand accelerator active."
        if holiday else
        "No major beach or resort holiday in the next 60 days."
    )

    active_reddit = {k: v for k, v in reddit.items() if v > 0}
    if active_reddit:
        reddit_text = ", ".join(
            f"{k}: {v} mention{'s' if v > 1 else ''}"
            for k, v in sorted(active_reddit.items(), key=lambda x: -x[1])
        )
    else:
        reddit_text = "No significant keyword mentions detected this week."

    trends_text = ", ".join(
        f"{k}: {v:.0f}"
        for k, v in sorted(trends.items(), key=lambda x: -x[1])
    ) if trends else "Trends data unavailable."

    prompt = f"""You are a senior merchandising analyst at Faherty Brand — a premium coastal lifestyle apparel company known for quality linen, bold coastal color, and resort-ready aesthetics. ~40 retail stores, direct e-commerce, and wholesale partners. AOV ~$150. Core customer: affluent, 35-55, beach house weekends, Nantucket/Charleston/Malibu lifestyle.

This is an internal weekly brief. Be a sharp analyst, not a generic AI. Every recommendation must be something a real merchant could action on Monday morning.

Here are this week's pre-scored signals:

## Category signals (demand pre-scored from sell-through + holiday proximity)
{signal_lines}

## Holiday context
{holiday_text}

## Reddit cultural mentions (r/malefashionadvice, r/femalefashionadvice, r/travel, r/solotravel, r/preppy — past 7 days)
{reddit_text}

## Google Trends (US, 7-day avg, 0-100)
{trends_text}

---

Write the Collection Pulse brief using EXACTLY these four sections. No intro, no preamble, start directly with HEAT MAP.

**HEAT MAP**
2-3 sentences. Lead with the single strongest signal this week. Connect sell-through data to search trends and Reddit chatter — show you're synthesizing, not just listing. Name specific categories and specific numbers.

**INVENTORY FLAGS**
Bullet points only. Flag every REORDER RISK and MARKDOWN RISK. Be blunt: name the category, the weeks of supply, and a single decisive action with a timeframe. Example format: "Resort dresses — 3 WOS, reorder now before Memorial Day window closes."

**RECOMMENDED ACTIONS**
Exactly 5 items, numbered. Format each as: [Category] · [Channel] · [This week / Within X days]: [specific action]. 
Actions must be channel-specific and time-bound. Reference Faherty's customer and brand voice — not generic retail. 
Bad example: "Consider promoting swimwear on social media."
Good example: "Swim trunks · Instagram · This week: run a carousel featuring the Baja stripe colorway against a coastal backdrop, targeting the Memorial Day packing mindset surfacing in r/travel."

**BUILD VS BUY NOTE**
1 sentence naming the single data source that would most improve this analysis. 1 sentence on why — be specific about what decision it would change.

No sign-off. No "I hope this helps." End after the BUILD VS BUY NOTE."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1200
    )

    return response.choices[0].message.content
