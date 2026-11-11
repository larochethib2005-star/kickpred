#!/usr/bin/env python3
"""
Interactive demo — predicts whether a planned Kickstarter campaign will
reach its funding goal, using our tuned XGBoost model.

Run with:  streamlit run app.py
"""
import base64
import joblib
import nltk
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from PIL import Image

# Self-healing: Streamlit Community Cloud starts from a fresh container,
# so the VADER lexicon isn't pre-downloaded there like it is locally.
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

from nltk.sentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="KickPred", page_icon=Image.open("assets/logo.png"), layout="wide")

# ---------------------------------------------------------------
# Palette — dark modern SaaS / startup look
# ---------------------------------------------------------------
PRIMARY = "#6366F1"       # indigo (brightened for dark backgrounds)
PRIMARY_DARK = "#A5B4FC"  # light indigo, used as "dark" accent text on dark cards
VIOLET = "#8B5CF6"
TEAL = "#34D399"          # positive
AMBER = "#FBBF24"         # caution
RED_SOFT = "#F87171"      # low / danger
BG = "#0E0C21"            # page background — deep navy, not black or white
CARD = "#17142E"          # card background, one step lighter than page
CARD_ALT = "#201C44"      # secondary / muted bar color on dark cards
BORDER = "#2A2650"
TEXT = "#F3F4F6"
MUTED = "#9CA3AF"
HERO_FROM = "#1E1B4B"
HERO_TO = "#4F46E5"
BADGE_BG = "rgba(99,102,241,0.16)"
BADGE_BG_MUTED = "rgba(255,255,255,0.06)"

LOGO_PATH = "assets/logo.png"

# ---------------------------------------------------------------
# Styling
# ---------------------------------------------------------------
st.markdown(f"""
<style>
.stApp {{ background-color: {BG}; }}
h1, h2, h3, h4 {{ font-family: Georgia, serif; color: {TEXT}; }}
.hero {{
    background: linear-gradient(135deg, {HERO_FROM} 0%, {HERO_TO} 100%);
    border-radius: 18px;
    padding: 32px 36px;
    margin-bottom: 22px;
    box-shadow: 0 8px 24px rgba(79,70,229,0.18);
}}
.card {{
    background-color: {CARD};
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 18px;
    border: 1px solid {BORDER};
    box-shadow: 0 2px 10px rgba(30,27,75,0.04);
}}
div[data-testid="stSidebar"] {{ background-color: {CARD}; border-right: 1px solid {BORDER}; }}
div.stButton > button {{
    background: linear-gradient(90deg, {PRIMARY} 0%, {VIOLET} 100%);
    color: white; border: none; border-radius: 10px;
    font-weight: 600; padding: 0.65em 0; font-size: 16px;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35);
}}
div.stButton > button:hover {{ opacity: 0.92; color: white; }}
hr {{ border-color: {BORDER}; }}
.badge {{
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 600; background: {BADGE_BG}; color: {PRIMARY_DARK};
}}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    return joblib.load("data/model.pkl")


@st.cache_data
def load_category_benchmarks():
    df = pd.read_csv("data/category_benchmarks.csv", index_col="category")
    return df["success_rate"].sort_values(ascending=False)


@st.cache_data
def logo_base64() -> str:
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_resource
def get_sentiment_analyzer():
    return SentimentIntensityAnalyzer()


# Approximate centroid for each country in our data, for the globe
COUNTRY_INFO = {
    "AT": ("Austria", 47.5, 14.5), "AU": ("Australia", -25.0, 133.0),
    "BE": ("Belgium", 50.8, 4.0), "CA": ("Canada", 56.0, -106.0),
    "CH": ("Switzerland", 46.8, 8.2), "DE": ("Germany", 51.0, 9.0),
    "DK": ("Denmark", 56.0, 10.0), "ES": ("Spain", 40.0, -4.0),
    "FR": ("France", 46.0, 2.0), "GB": ("United Kingdom", 54.0, -2.0),
    "GR": ("Greece", 39.0, 22.0), "HK": ("Hong Kong", 22.3, 114.2),
    "IE": ("Ireland", 53.0, -8.0), "IT": ("Italy", 42.8, 12.8),
    "JP": ("Japan", 36.0, 138.0), "LU": ("Luxembourg", 49.8, 6.1),
    "MX": ("Mexico", 23.0, -102.0), "NL": ("Netherlands", 52.3, 5.5),
    "NO": ("Norway", 62.0, 10.0), "NZ": ("New Zealand", -41.0, 174.0),
    "PL": ("Poland", 52.0, 20.0), "SE": ("Sweden", 62.0, 15.0),
    "SG": ("Singapore", 1.35, 103.8), "SI": ("Slovenia", 46.1, 14.8),
    "US": ("United States", 39.8, -98.6),
}

bundle = load_model()
model = bundle["model"]
feature_columns = bundle["feature_columns"]
cat_cols = bundle["cat_cols"]
cat_options = bundle["cat_options"]
num_ranges = bundle["num_ranges"]
test_accuracy = bundle["test_accuracy"]
vague_pitch_words = bundle["vague_pitch_words"]
category_benchmarks = load_category_benchmarks()
sia = get_sentiment_analyzer()


def predict(inputs: dict) -> float:
    row = pd.DataFrame([inputs])
    row = pd.get_dummies(row, columns=cat_cols)
    row = row.reindex(columns=feature_columns, fill_value=0)
    return float(model.predict_proba(row)[0, 1])


def generate_recommendations(base_inputs: dict, current_prob: float, num_ranges: dict) -> list:
    """Tests a few realistic changes one at a time (holding everything else
    fixed) and returns the ones that would meaningfully raise the odds,
    ranked by impact — i.e. the founder's biggest levers / weakest points."""
    candidates = []

    goal = base_inputs["goal"]
    lower_goal = max(num_ranges["goal"][0], goal / 2)
    if lower_goal < goal * 0.95:
        p = predict({**base_inputs, "goal": lower_goal, "staff_pick": 0})
        candidates.append({
            "factor": "Funding goal", "action": f"Lower your goal to ~${lower_goal:,.0f} (from ${goal:,.0f})",
            "prob": p,
        })

    duration = base_inputs["duration_days"]
    if duration > 15:
        p = predict({**base_inputs, "duration_days": 12, "staff_pick": 0})
        candidates.append({
            "factor": "Campaign duration", "action": f"Shorten your campaign to ~12 days (from {duration})",
            "prob": p,
        })

    current_month = base_inputs["month"]
    month_probs = {m: predict({**base_inputs, "month": m, "staff_pick": 0}) for m in range(1, 13)}
    best_month = max(month_probs, key=month_probs.get)
    if best_month != current_month and month_probs[best_month] > month_probs[current_month] + 0.01:
        month_name = pd.Timestamp(2026, best_month, 1).strftime("%B")
        candidates.append({
            "factor": "Launch month", "action": f"Launch in {month_name} instead",
            "prob": month_probs[best_month],
        })

    prep = base_inputs["prep_days"]
    longer_prep = min(prep + 45, num_ranges["prep_days"][2])
    if longer_prep > prep + 5:
        p = predict({**base_inputs, "prep_days": longer_prep, "staff_pick": 0})
        candidates.append({
            "factor": "Preparation time", "action": f"Spend ~{int(longer_prep)} days prepping before launch (from {prep})",
            "prob": p,
        })

    flagged_words = [w for w in vague_pitch_words if base_inputs.get(f"kw_{w}") == 1]
    if flagged_words:
        cleaned = {**base_inputs, **{f"kw_{w}": 0 for w in flagged_words}}
        p = predict({**cleaned, "staff_pick": 0})
        word_list = ", ".join(f'"{w}"' for w in flagged_words)
        candidates.append({
            "factor": "Tagline wording",
            "action": f"Rephrase your tagline to avoid vague words like {word_list} — be concrete about what you're making",
            "prob": p,
        })

    for c in candidates:
        c["delta"] = c["prob"] - current_prob
    candidates = [c for c in candidates if c["delta"] > 0.01]
    candidates.sort(key=lambda c: c["delta"], reverse=True)
    return candidates[:3]


def text_features(text: str) -> dict:
    """Live sentiment + keyword features, computed the same way as training."""
    text = text or ""
    sentiment = sia.polarity_scores(text)["compound"]
    lower = text.lower()
    kw = {f"kw_{w}": int(f" {w} " in f" {lower} " or lower.startswith(w) or lower.endswith(w))
          for w in vague_pitch_words}
    return {"sentiment": sentiment, **kw}


def make_gauge(value: float, title: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        number={"suffix": "%", "font": {"color": TEXT, "size": 44}},
        title={"text": title, "font": {"color": MUTED, "size": 13}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": MUTED, "tickfont": {"color": MUTED}},
            "bar": {"color": PRIMARY, "thickness": 0.3},
            "bgcolor": CARD,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "#3B1420"},
                {"range": [40, 70], "color": "#3B2F14"},
                {"range": [70, 100], "color": "#113B2C"},
            ],
        },
    ))
    fig.update_layout(
        height=230, margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)", font={"color": TEXT},
    )
    return fig


def make_world_globe() -> go.Figure:
    """Un-highlighted overview globe for the landing page."""
    codes = list(COUNTRY_INFO.keys())
    lats = [COUNTRY_INFO[c][1] for c in codes]
    lons = [COUNTRY_INFO[c][2] for c in codes]
    names = [COUNTRY_INFO[c][0] for c in codes]

    fig = go.Figure(go.Scattergeo(
        lon=lons, lat=lats, text=names, mode="markers",
        marker=dict(size=9, color=VIOLET, opacity=0.75, line=dict(width=1, color="white")),
        hoverinfo="text",
    ))
    fig.update_geos(
        projection_type="orthographic",
        projection_rotation=dict(lon=-20, lat=25, roll=0),
        showland=True, landcolor="#EEF2FF",
        showocean=True, oceancolor="#1E1B4B",
        showcountries=True, countrycolor="#C7D2FE",
        showframe=False, bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=360, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def make_globe(selected_country: str) -> go.Figure:
    codes = list(COUNTRY_INFO.keys())
    names = [COUNTRY_INFO[c][0] for c in codes]
    lats = [COUNTRY_INFO[c][1] for c in codes]
    lons = [COUNTRY_INFO[c][2] for c in codes]
    colors = [PRIMARY if c == selected_country else "#C7D2FE" for c in codes]
    sizes = [22 if c == selected_country else 7 for c in codes]

    sel_name, sel_lat, sel_lon = COUNTRY_INFO[selected_country]

    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon=lons, lat=lats, text=names, mode="markers",
        marker=dict(size=sizes, color=colors, line=dict(width=1, color="white")),
        hoverinfo="text",
    ))
    fig.update_geos(
        projection_type="orthographic",
        projection_rotation=dict(lon=sel_lon, lat=sel_lat, roll=0),
        showland=True, landcolor="#EEF2FF",
        showocean=True, oceancolor=BG,
        showcountries=True, countrycolor="#C7D2FE",
        showframe=False, bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=320, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.markdown(f"""
<div class="hero">
  <img src="data:image/png;base64,{logo_base64()}" style="max-width:280px; width:100%; height:auto; margin-bottom:12px;" />
  <p style="color:#C7D2FE; margin-bottom:0; font-size:15px;">AI for Business and Society · SKEMA BBA4 · Thibault & Khoubeybe
  — model trained on 598,740 past campaigns, {test_accuracy:.1%} test accuracy</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Sidebar — inputs
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("### Your Campaign")

    blurb_text = st.text_area(
        "Your campaign tagline (blurb)", placeholder="e.g. A modular, eco-friendly backpack for daily commuters.",
        height=80,
    )

    category = st.selectbox("Category", cat_options["category"])
    subcategory = st.selectbox("Subcategory", cat_options["subcategory"])
    country = st.selectbox("Country", cat_options["country"],
                             format_func=lambda c: f"{COUNTRY_INFO.get(c, (c,))[0]}")
    location_type = st.selectbox("Location type", cat_options["location_type"])

    goal_min, goal_med, goal_max = num_ranges["goal"]
    goal_input_max = min(goal_max, 1_000_000)
    goal = st.number_input(
        "Funding goal (USD)", min_value=0.0, max_value=float(goal_input_max),
        value=float(min(goal_med, 20000)), step=500.0,
    )

    dur_min, dur_med, dur_max = num_ranges["duration_days"]
    duration_days = st.slider(
        "Campaign duration (days)", min_value=int(dur_min), max_value=min(int(dur_max), 90),
        value=int(dur_med),
    )

    month = st.selectbox(
        "Launch month", list(range(1, 13)),
        format_func=lambda m: pd.Timestamp(2026, m, 1).strftime("%B"), index=5,
    )

    with st.expander("More details"):
        name_min, name_med, name_max = num_ranges["name_length"]
        name_length = st.slider("Project name length (words)", int(name_min),
                                  min(int(name_max), 20), int(name_med))
        prep_min, prep_med, prep_max = num_ranges["prep_days"]
        prep_days = st.slider("Days prepping before launch", int(prep_min),
                                min(int(prep_max), 365), int(min(prep_med, 30)))

    year = 2026  # most recent year in the training data
    run = st.button("Predict my chances", use_container_width=True)

# ---------------------------------------------------------------
# Results
# ---------------------------------------------------------------
if not run:
    lc, rc = st.columns([1, 1])
    with lc:
        st.markdown(f"""
        <div class="card" style="height:360px; display:flex; flex-direction:column; justify-content:center;">
          <span class="badge">GET STARTED</span>
          <h2 style="margin:14px 0 6px;">Know your odds before you launch</h2>
          <p style="color:{MUTED}; margin:0; font-size:15px;">Fill in your planned campaign on the left — including
          your tagline — and click <b style="color:{PRIMARY};">Predict my chances</b>. You'll get a success
          probability, how your goal and timing affect your odds, where you're launching from, how your category
          compares, and concrete recommendations to improve your chances.</p>
        </div>
        """, unsafe_allow_html=True)
    with rc:
        st.markdown(f"""<div class="card" style="padding:12px;">""", unsafe_allow_html=True)
        st.plotly_chart(make_world_globe(), use_container_width=True)
        st.markdown(f"""
        <p style="text-align:center; color:{MUTED}; font-size:13px; margin:-6px 0 6px;">
        598,740 campaigns across 25 countries, 2009–2026</p>
        </div>
        """, unsafe_allow_html=True)
else:
    blurb_feats = text_features(blurb_text)
    blurb_length = len(blurb_text.split()) if blurb_text else int(num_ranges.get("blurb_length", (0, 10, 10))[1])

    base_inputs = {
        "category": category, "subcategory": subcategory, "country": country,
        "location_type": location_type, "goal": goal, "duration_days": duration_days,
        "month": month, "blurb_length": blurb_length, "name_length": name_length,
        "prep_days": prep_days, "year": year, **blurb_feats,
    }
    prob_not_picked = predict({**base_inputs, "staff_pick": 0})
    prob_picked = predict({**base_inputs, "staff_pick": 1})

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(make_gauge(prob_not_picked, "WITHOUT A STAFF PICK"), use_container_width=True)
    with g2:
        st.plotly_chart(make_gauge(prob_picked, "IF KICKSTARTER FEATURES YOU"), use_container_width=True)

    st.caption(
        "We show both because `staff_pick` is decided by Kickstarter after you launch, not "
        "something you control — it's our model's single strongest predictor, worth seeing."
    )

    if prob_not_picked < 0.4:
        st.warning("Your realistic (non-featured) odds are on the lower side — see the chart below "
                    "for how lowering your goal could change that.")
    elif prob_not_picked > 0.6:
        st.success("Your realistic odds look solid — this plan compares well to similar past campaigns.")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        st.markdown("#### How your goal changes your odds")
        goal_sweep_max = min(goal_max, 200_000)
        goal_range = np.geomspace(max(goal_min, 100), max(goal_sweep_max, 1000), 25)
        probs_np = [predict({**base_inputs, "goal": g, "staff_pick": 0}) * 100 for g in goal_range]
        probs_sp = [predict({**base_inputs, "goal": g, "staff_pick": 1}) * 100 for g in goal_range]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=goal_range, y=probs_np, mode="lines", name="Without Staff Pick",
                                   line=dict(color=PRIMARY, width=3)))
        fig.add_trace(go.Scatter(x=goal_range, y=probs_sp, mode="lines", name="If Staff Pick",
                                   line=dict(color=VIOLET, width=2, dash="dot")))
        fig.add_vline(x=goal, line_dash="dash", line_color=MUTED,
                       annotation_text="You", annotation_font_color=MUTED)
        tick_vals = [100, 1000, 5000, 10000, 50000, 100000, 200000]
        tick_text = ["$100", "$1k", "$5k", "$10k", "$50k", "$100k", "$200k"]
        fig.update_layout(
            yaxis_title="Success probability (%)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=CARD, font={"color": TEXT},
            legend=dict(orientation="h", y=-0.3), margin=dict(l=10, r=10, t=10, b=10), height=300,
            yaxis=dict(gridcolor=BORDER, range=[0, 100]),
            xaxis=dict(type="log", title="Funding goal", gridcolor=BORDER,
                        tickmode="array", tickvals=tick_vals, ticktext=tick_text),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### Where you're launching from")
        st.plotly_chart(make_globe(country), use_container_width=True)
        st.caption(f"**{COUNTRY_INFO[country][0]}** highlighted — most campaigns in our data launch from the US and UK.")

    with c3:
        st.markdown("#### How your category compares")
        bench = category_benchmarks.copy() * 100
        colors = [PRIMARY if c == category else CARD_ALT for c in bench.index]
        fig2 = go.Figure(go.Bar(x=bench.values, y=bench.index, orientation="h", marker_color=colors))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=CARD, font={"color": TEXT, "size": 10},
            xaxis_title="Historical success rate (%)", margin=dict(l=10, r=10, t=10, b=10), height=300,
            xaxis=dict(gridcolor=BORDER, range=[0, 100]), yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(f"**{category}** historically succeeds {category_benchmarks[category]:.0%} of the time.")

    st.markdown("<br>", unsafe_allow_html=True)
    recommendations = generate_recommendations(
        {**base_inputs, "staff_pick": 0}, prob_not_picked, num_ranges
    )
    if recommendations:
        row_parts = []
        for i, rec in enumerate(recommendations):
            tag = "BIGGEST OPPORTUNITY" if i == 0 else "ALSO CONSIDER"
            badge_bg = BADGE_BG if i == 0 else BADGE_BG_MUTED
            badge_color = PRIMARY_DARK if i == 0 else MUTED
            row_parts.append(
                f'<div style="display:flex; justify-content:space-between; align-items:center; '
                f'padding:14px 0; border-bottom:1px solid {BORDER};">'
                f'<div style="max-width:78%;">'
                f'<span class="badge" style="background:{badge_bg}; color:{badge_color};">{tag}</span>'
                f'<p style="margin:8px 0 2px; font-weight:600; color:{TEXT};">{rec["factor"]}</p>'
                f'<p style="margin:0; color:{MUTED}; font-size:14px;">{rec["action"]}</p>'
                f'</div>'
                f'<div style="text-align:right;">'
                f'<p style="margin:0; font-size:22px; font-weight:700; color:{TEAL};">+{rec["delta"]*100:.0f} pts</p>'
                f'<p style="margin:0; color:{MUTED}; font-size:12px;">&rarr; {rec["prob"]:.0%}</p>'
                f'</div></div>'
            )
        rows = "".join(row_parts)
        card_html = (
            f'<div class="card"><span class="badge">RECOMMENDATIONS</span>'
            f'<p style="margin:10px 0 4px; color:{MUTED}; font-size:14px;">Changes to your plan that would most '
            f'improve your realistic (non-featured) odds, tested one at a time:</p>{rows}</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="card">
          <span class="badge">RECOMMENDATIONS</span>
          <p style="margin:10px 0 0; color:{MUTED};">We tested lowering your goal, shortening your duration,
          changing your launch month, and prepping longer — none would meaningfully raise your odds further.
          Your plan already looks well-optimized on the factors we can test.</p>
        </div>
        """, unsafe_allow_html=True)

    if blurb_text:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
          <span class="badge">TAGLINE ANALYSIS</span>
          <p style="margin:10px 0 0; color:{TEXT};">Sentiment score: <b>{blurb_feats['sentiment']:+.2f}</b>
          (-1 very negative, +1 very positive). Our research found that vague pitch language
          ("want", "create", "people"...) correlates with lower success — specific, concrete
          descriptions tend to do better.</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption(
    "Model: XGBoost (tuned), trained on Kaggle's Kickstarter Full Campaigns dataset, "
    "with sentiment + keyword features from the campaign tagline. "
    "Predictions are estimates based on historical patterns, not guarantees."
)
