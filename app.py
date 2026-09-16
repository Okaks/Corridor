"""Corridor: Nigeria corridor pricing and customer sentiment."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from loaders import (
    ALL_PROVIDERS,
    FOCUS,
    NGN_PROVIDERS,
    THEMES,
    daily_spread,
    intraday_move,
    leadership,
    load_rates,
    load_reviews,
    provider_summary,
    sentiment_bands,
    theme_impact,
)

st.set_page_config(page_title="Corridor", page_icon="◈", layout="wide")

BG, PANEL, TEXT, MUTED, RULE = "#0E1116", "#161B22", "#E8ECEF", "#8B98A5", "#242C36"
GOOD, WARN, BAD, DIM = "#2DD4A7", "#F5B841", "#E5484D", "#5A6875"

# Hue-spaced and lightness-spaced so no two lines read alike on a dark ground.
# Five widely separated hues. No two neutrals, no two warms sitting next to each
# other, so each line is identifiable without checking the legend.
PROVIDER_COLOR = {
    "LemFi": "#2DD4A7",        # teal
    "Taptap Send": "#3B9EFF",  # blue
    "NALA": "#FFC94D",         # yellow
    "Sendwave": "#B388FF",     # violet
    "Wise": "#E6EAF0",         # near-white
}
BAND_COLOR = {"Detractors": BAD, "Neutral": DIM, "Advocates": GOOD}

st.markdown(
    f"""
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500;6..72,600&display=swap" rel="stylesheet">
    <style>
      html, body, .stApp, [data-testid="stAppViewContainer"],
      [data-testid="stMarkdownContainer"], .stMarkdown, p, li, td, th, label, input, select,
      button, .stTabs [data-baseweb="tab"], [data-testid="stDataFrame"] {{
        font-family: 'Newsreader', 'Times New Roman', Georgia, serif !important;
      }}
      .stApp {{ background: {BG}; color: {TEXT}; }}
      [data-testid="stHeader"] {{ background: transparent; }}
      .stApp h1, .stApp h2, .stApp h3,
      [data-testid="stMarkdownContainer"] h1,
      [data-testid="stMarkdownContainer"] h2,
      [data-testid="stMarkdownContainer"] h3 {{
        font-family: 'Newsreader', Georgia, serif !important;
        font-weight: 400 !important; color: {TEXT}; letter-spacing: -0.015em;
      }}
      .stApp h1 {{ font-size: 3.1rem !important; line-height: 1; margin-bottom: 1.2rem; }}
      .stApp h2 {{ font-size: 1.65rem !important; margin-top: 2.2rem; }}
      .stApp h3 {{ font-family: 'Newsreader', 'Times New Roman', Georgia, serif !important;
                   font-size: 0.92rem !important; font-weight: 500 !important;
                   margin: 2.2rem 0 0.45rem 0; padding-bottom: 0;
                   letter-spacing: 0.17em; color: {MUTED}; }}
      p, li, td, th, label {{ color: {TEXT}; }}
      .stTabs [data-baseweb="tab-list"] {{ gap: 2rem; border-bottom: 1px solid {RULE}; }}
      .stTabs [data-baseweb="tab"] {{ font-size: 1.05rem; padding: 0 0 0.7rem 0;
                                      color: {MUTED}; letter-spacing: 0.01em; }}
      .stTabs [aria-selected="true"] {{ color: {TEXT} !important; }}
      .kpi {{ background: {PANEL}; border: 1px solid {RULE}; border-radius: 4px;
              padding: 1.6rem 1rem 1.75rem; height: 100%; text-align: center; }}
      .kpi-top {{ display: flex; align-items: center; justify-content: center;
                  gap: 0.45rem; margin-bottom: 1.35rem; }}
      .kpi-icon {{ flex: 0 0 auto; display: flex; opacity: 0.8; }}
      .kpi-label {{ font-size: 0.78rem; color: {MUTED}; text-transform: uppercase;
                    letter-spacing: 0.11em; line-height: 1; white-space: nowrap;
                    max-width: none; }}
      .kpi-value {{ font-family: 'Newsreader', Georgia, serif; font-size: 2.7rem;
                    line-height: 1; color: {TEXT}; text-align: center; }}
      .kpi-value.good {{ color: {GOOD}; }}
      .kpi-value.bad {{ color: {BAD}; }}
      .read {{ font-size: 0.9rem; color: {MUTED}; line-height: 1.65; max-width: 70ch;
               margin-top: 0.4rem; }}
      .read strong {{ color: {TEXT}; font-weight: 500; }}
      .insight {{ background: {PANEL}; border: 1px solid {RULE}; border-left: 2px solid {GOOD};
                  padding: 1.1rem 1.4rem; margin: 0.2rem 0 1.4rem 0; }}
      .insight-body {{ font-size: 0.92rem; color: {MUTED}; line-height: 1.7; max-width: 88ch; }}
      .insight-body strong {{ color: {TEXT}; font-weight: 500; }}
      .insight-body ul {{ margin: 0; padding-left: 1.1rem; }}
      .insight-body li {{ color: {MUTED}; margin-bottom: 0.55rem; line-height: 1.65; }}
      .insight-body li:last-child {{ margin-bottom: 0; }}
      .insight-body li strong {{ color: {TEXT}; font-weight: 500; }}
      .rec {{ background: {PANEL}; border-left: 2px solid {GOOD}; padding: 1.1rem 1.4rem;
              margin-bottom: 0.9rem; }}
      .rec-head {{ font-family: 'Newsreader', Georgia, serif; font-size: 1.35rem;
                   color: {TEXT}; margin-bottom: 0.4rem; }}
      .rec-body {{ font-size: 0.92rem; color: {MUTED}; line-height: 1.65; max-width: 80ch; }}
      .rec-body strong {{ color: {GOOD}; font-weight: 500; }}
      .review-card {{ border-left: 1px solid {RULE}; padding: 0.1rem 0 0.1rem 1rem;
                      margin-bottom: 1rem; max-width: 82ch; }}
      .review-meta {{ font-size: 0.75rem; color: {MUTED}; letter-spacing: 0.03em; }}
      .review-body {{ font-size: 0.9rem; color: {TEXT}; line-height: 1.6; }}
      [data-testid="stDataFrame"] {{ border: 1px solid {RULE}; }}
      hr {{ border-color: {RULE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

rates = load_rates()
reviews = load_reviews()
lemfi = reviews[reviews["app"] == "LemFi"]
one_star = lemfi[lemfi["rating"] == 1]


TONE_COLOR = {"": MUTED, "good": GOOD, "bad": BAD, "warn": WARN}

ICONS = {
    "spread": "<path d='M3 12h18M7 8l-4 4 4 4M17 8l4 4-4 4'/>",
    "star": "<path d='M12 3l2.6 5.6 6.4.8-4.7 4.3 1.2 6.3L12 17l-5.5 3 1.2-6.3L3 9.4l6.4-.8z'/>",
    "alert": "<path d='M12 3l9 16H3z'/><path d='M12 10v4M12 17h.01'/>",
    "tag": "<path d='M20 12l-8 8-9-9V3h8z'/><path d='M7.5 7.5h.01'/>",
    "chat": "<path d='M21 12a8 8 0 0 1-8 8H7l-4 3V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z'/>",
    "up": "<path d='M7 14l5-5 5 5'/><path d='M12 19V9'/>",
    "down": "<path d='M17 10l-5 5-5-5'/><path d='M12 5v10'/>",
}


def kpi(col, label, value, tone="", icon=None):
    glyph = ""
    if icon:
        glyph = (
            f"<span class='kpi-icon'><svg width='17' height='17' viewBox='0 0 24 24' "
            f"fill='none' stroke='{TONE_COLOR.get(tone, MUTED)}' stroke-width='1.8' "
            f"stroke-linecap='round' stroke-linejoin='round'>{ICONS[icon]}</svg></span>"
        )
    col.markdown(
        f"<div class='kpi'><div class='kpi-top'>{glyph}"
        f"<div class='kpi-label'>{label}</div></div>"
        f"<div class='kpi-value {tone}'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def read(text):
    st.markdown(f"<div class='read'>{text}</div>", unsafe_allow_html=True)


def insight(text):
    st.markdown(f"<div class='insight'><div class='insight-body'>{text}</div></div>",
                unsafe_allow_html=True)


def dark(fig, height=380, ytitle=None, legend=True):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=34 if legend else 6, b=8),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Newsreader, Times New Roman, Georgia, serif", size=13, color=MUTED),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0, title=None,
                    font=dict(color=MUTED)),
        hoverlabel=dict(bgcolor=PANEL, bordercolor=RULE, font=dict(color=TEXT)),
    )
    fig.update_xaxes(showgrid=False, linecolor=RULE, tickcolor=RULE, automargin=True,
                     tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=RULE, zeroline=False, title=ytitle, automargin=True,
                     tickfont=dict(color=MUTED))
    return fig


st.markdown("# Corridor")

t1, t2, t3, t4 = st.tabs(["Overview", "Pricing", "Customer voice", "Recommendations"])

# ─────────────────────────────── Overview ───────────────────────────────
with t1:
    gbp = provider_summary(rates, "GBP-NGN")
    ngn_gbp = gbp[gbp["Provider"].isin(NGN_PROVIDERS)]
    spread_gbp = ngn_gbp["avg_value"].max() - ngn_gbp["avg_value"].min()
    delay_support = (one_star["Delay or money pending"] | one_star["Customer support"]).mean() * 100
    advocates = (lemfi["rating"] >= 4).mean() * 100

    c = st.columns(4)
    kpi(c[0], "Price spread", f"{spread_gbp:.2f}pp", icon="spread")
    kpi(c[1], "Advocates", f"{advocates:.0f}%", "good", icon="star")
    kpi(c[2], "Service one-stars", f"{delay_support:.0f}%", "bad", icon="alert")
    kpi(c[3], "Rate sentiment",
        f"{lemfi[lemfi['Exchange rate']]['rating'].mean():.2f}", icon="tag")

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### PRICE POSITION, GBP-NGN")
        d = ngn_gbp.sort_values("avg_value")
        fig = go.Figure(go.Bar(
            x=d["avg_value"], y=d["Provider"], orientation="h",
            marker=dict(color=[PROVIDER_COLOR[p] for p in d["Provider"]]),
            text=[f"{v:.2f}%" for v in d["avg_value"]], textposition="outside",
            textfont=dict(color=TEXT),
            hovertemplate="%{y}<br>%{x:.2f}% above mid-market<extra></extra>"))
        fig.update_xaxes(range=[0, d["avg_value"].max() * 1.22], visible=False)
        st.plotly_chart(dark(fig, 300, legend=False), width="stretch")
        read(f"Four providers inside <strong>{spread_gbp:.2f}pp</strong>. The distance from "
             f"first to fourth is worth about 300 naira on a £100 transfer.")

    with right:
        st.markdown("### SENTIMENT MIX")
        bands = sentiment_bands(reviews)
        fig = go.Figure()
        for band in ["Advocates", "Neutral", "Detractors"]:
            s = bands[bands["band"] == band]
            fig.add_trace(go.Bar(
                y=s["app"].astype(str), x=s["share"], name=band, orientation="h",
                marker_color=BAND_COLOR[band],
                text=[f"{v:.0f}%" if v > 8 else "" for v in s["share"]],
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color=BG, size=11),
                hovertemplate="%{y}<br>" + band + " %{x:.1f}%<extra></extra>"))
        fig.update_layout(barmode="stack")
        fig.update_xaxes(visible=False)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(dark(fig, 300), width="stretch")
        read(f"LemFi holds the strongest advocate base of the five at "
             f"<strong>{advocates:.0f}%</strong>, against a detractor block sitting on "
             f"service rather than price.")

    st.markdown("### WHAT MOVES THE RATING")
    impact = theme_impact(reviews, "LemFi")
    plot = impact[impact["Reviews"] >= 30].sort_values("Avg rating")
    fig = go.Figure(go.Bar(
        x=plot["Avg rating"], y=plot["Theme"], orientation="h",
        marker=dict(color=[BAD if v < 2.5 else GOOD if v > 4 else WARN
                           for v in plot["Avg rating"]]),
        text=[f"{v:.2f}" for v in plot["Avg rating"]], textposition="outside",
        textfont=dict(color=TEXT), customdata=plot[["Share of reviews"]],
        hovertemplate="%{y}<br>%{x:.2f} stars<br>%{customdata[0]}% of reviews<extra></extra>"))
    fig.update_xaxes(range=[0, 5.5], visible=False)
    st.plotly_chart(dark(fig, 400, legend=False), width="stretch")
    read("Rate is a praise theme. Delay and support are what produce one stars, and they "
         "carry a three-star penalty when they appear.")

    with st.expander("What this dashboard shows"):
        insight(
            "<ul>"
            "<li><strong>The competitive gap is smaller than it looks.</strong> LemFi is "
            "competing in a market where pricing differences are narrow and temporary. That "
            "makes the customer experience, particularly what happens when a transfer goes "
            "wrong, a more durable source of differentiation.</li>"
            "<li><strong>LemFi's strength is speed.</strong> The product earns strong "
            "sentiment when the transfer works as expected. Speed and exchange rates are "
            "clear strengths; the sharpest dissatisfaction comes when customers are waiting "
            "for money or waiting for help.</li>"
            "<li><strong>The problem isn't broad dissatisfaction.</strong> LemFi doesn't "
            "have a general sentiment problem; it has a concentrated service problem. Most "
            "customers are advocates, but a small set of failure points, particularly "
            "support, delays and account issues, pull the experience sharply downward.</li>"
            "<li><strong>The December improvement deserves investigation.</strong> The "
            "biggest unexplained signal in the data is the December turnaround. The "
            "improvement was large enough and persistent enough to suggest a real product or "
            "operational change, not ordinary month-to-month noise.</li>"
            "<li><strong>Price is already a positive part of the proposition.</strong> LemFi "
            "doesn't need to invent a pricing story. Customers already recognise the value. "
            "The bigger opportunity is making that advantage consistent and preserving it "
            "while improving the parts of the journey that generate dissatisfaction.</li>"
            "</ul>")

# ──────────────────────────────── Pricing ────────────────────────────────
with t2:
    corridor = st.radio("Corridor", ["GBP-NGN", "USD-NGN"], horizontal=True,
                        label_visibility="collapsed")
    sub = rates[rates["Corridor"] == corridor]

    st.markdown("### VALUE ABOVE MID-MARKET, DAILY")
    daily = sub.pivot_table(index="Date", columns="Provider", values="value_vs_mid")
    fig = go.Figure()
    for p in ALL_PROVIDERS:
        if p not in daily:
            continue
        fig.add_trace(go.Scatter(
            x=daily.index, y=daily[p], name=p, mode="lines",
            line=dict(color=PROVIDER_COLOR[p], width=5 if p == FOCUS else 3,
                      shape="spline", smoothing=0.6),
            hovertemplate="%{y:.2f}%<extra>" + p + "</extra>"))
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(dark(fig, 420, "% above mid-market"), width="stretch")

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### SHARE OF READINGS LED")
        lead = leadership(rates, corridor).sort_values("share_of_readings")
        fig = go.Figure(go.Bar(
            x=lead["share_of_readings"], y=lead["Provider"], orientation="h",
            marker=dict(color=[PROVIDER_COLOR[p] for p in lead["Provider"]]),
            text=[f"{v:.0f}%" for v in lead["share_of_readings"]], textposition="outside",
            textfont=dict(color=TEXT), customdata=lead[["times_cheapest"]],
            hovertemplate="%{y}<br>Best on %{customdata[0]} readings<extra></extra>"))
        fig.update_xaxes(range=[0, lead["share_of_readings"].max() * 1.3], visible=False)
        st.plotly_chart(dark(fig, 290, legend=False), width="stretch")
        read("No provider holds the lead outright. It turns over between the morning and "
             "afternoon reading.")

    with right:
        st.markdown("### INTRADAY REPRICING")
        moves = intraday_move(rates, corridor).sort_values("avg_move")
        fig = go.Figure(go.Bar(
            x=moves["avg_move"], y=moves["Provider"], orientation="h",
            marker=dict(color=[PROVIDER_COLOR[p] for p in moves["Provider"]]),
            text=[f"{v:.2f}pp" for v in moves["avg_move"]], textposition="outside",
            textfont=dict(color=TEXT), customdata=moves[["max_move"]],
            hovertemplate="%{y}<br>Average move %{x:.2f}pp<br>"
                          "Largest %{customdata[0]:.2f}pp<extra></extra>"))
        fig.update_xaxes(range=[0, moves["avg_move"].max() * 1.35], visible=False)
        st.plotly_chart(dark(fig, 290, legend=False), width="stretch")
        top = moves.iloc[-1]
        read(f"<strong>{top['Provider']}</strong> moves furthest within the day at "
             f"{top['avg_move']:.2f}pp average. Repricing is an active lever on this "
             f"corridor, not a daily set-and-forget.")

    st.markdown("### DAILY GAP, BEST TO WORST")
    spread = daily_spread(rates, corridor)
    fig = go.Figure(go.Scatter(
        x=spread["Date"], y=spread["spread"], mode="lines",
        line=dict(color=GOOD, width=3.4, shape="spline", smoothing=0.6),
        fill="tozeroy", fillcolor="rgba(45,212,167,0.12)",
        hovertemplate="%{x|%d %b}<br>%{y:.2f}pp<extra></extra>"))
    st.plotly_chart(dark(fig, 260, "Percentage points", legend=False), width="stretch")

    insight(
        "<ul>"
        "<li><strong>There is no lasting price winner.</strong> Pricing leadership is a "
        "moving position, not a durable advantage. A provider can lead one reading and lose "
        "it a few hours later, which limits the value of trying to win the corridor through "
        "permanent price superiority.</li>"
        "<li><strong>GBP-NGN deserves more attention than USD-NGN.</strong> The two "
        "corridors behave differently. GBP-NGN shows more movement in competitive "
        "positioning, while USD-NGN is comparatively stable. Pricing intervention therefore "
        "shouldn't be treated as a single Nigeria-corridor strategy.</li>"
        "<li><strong>The market appears to move together.</strong> Competitors tend to "
        "reprice in the same direction, which limits the window created by moving alone. The "
        "advantage comes from responding well to market movements rather than simply moving "
        "rates more aggressively.</li>"
        "<li><strong>The average hides the moments that matter.</strong> Average pricing "
        "makes the corridor look tightly matched, but the daily gap shows that meaningful "
        "differences still emerge. The opportunity is therefore less about lowering the "
        "average rate and more about identifying when the competitive gap becomes large "
        "enough to matter.</li>"
        "</ul>")

    with st.expander("Provider averages and rate log"):
        st.dataframe(provider_summary(rates, corridor), hide_index=True, width="stretch")
        st.dataframe(
            sub[["Date", "Slot", "Provider", "Advertised Rate", "Transfer Fee",
                 "Amount Received", "Mid-Market Rate", "value_vs_mid"]]
            .rename(columns={"value_vs_mid": "% above mid-market"})
            .round({"Advertised Rate": 2, "Transfer Fee": 2, "Amount Received": 0,
                    "Mid-Market Rate": 2, "% above mid-market": 3}),
            hide_index=True, width="stretch", height=320)

# ───────────────────────────── Customer voice ─────────────────────────────
with t3:
    app = st.selectbox("App", sorted(reviews["app"].unique()),
                       index=sorted(reviews["app"].unique()).index("LemFi"))
    sub = reviews[reviews["app"] == app]

    c = st.columns(4)
    kpi(c[0], "Reviews", f"{len(sub):,}", icon="chat")
    kpi(c[1], "Average rating", f"{sub['rating'].mean():.2f}", icon="star")
    kpi(c[2], "Advocates", f"{(sub['rating'] >= 4).mean() * 100:.0f}%", "good", icon="up")
    kpi(c[3], "Detractors", f"{(sub['rating'] <= 2).mean() * 100:.0f}%", "bad", icon="down")

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### THEME IMPACT")
        imp = theme_impact(reviews, app)
        imp = imp[imp["Reviews"] >= 20].sort_values("Avg rating")
        fig = go.Figure(go.Bar(
            x=imp["Avg rating"], y=imp["Theme"], orientation="h",
            marker=dict(color=[BAD if v < 2.5 else GOOD if v > 4 else WARN
                               for v in imp["Avg rating"]]),
            text=[f"{v:.2f}" for v in imp["Avg rating"]], textposition="outside",
            textfont=dict(color=TEXT), customdata=imp[["Share of reviews"]],
            hovertemplate="%{y}<br>%{x:.2f} stars<br>%{customdata[0]}% of reviews<extra></extra>"))
        fig.update_xaxes(range=[0, 5.5], visible=False)
        st.plotly_chart(dark(fig, 360, legend=False), width="stretch")
        read("Sorted by damage. Anything under 2.5 is a churn driver, not a complaint.")

    with right:
        st.markdown("### RATING TREND")
        monthly = (sub[sub["date"] >= "2024-01-01"].groupby("month")
                   .agg(avg=("rating", "mean"), n=("rating", "size")).reset_index())
        monthly = monthly[monthly["n"] >= 15]
        fig = go.Figure(go.Scatter(
            x=monthly["month"], y=monthly["avg"], mode="lines",
            line=dict(color=GOOD, width=3.4, shape="spline", smoothing=0.6),
            fill="tozeroy", fillcolor="rgba(45,212,167,0.10)",
            customdata=monthly[["n"]],
            hovertemplate="%{x|%b %Y}<br>%{y:.2f} stars<br>"
                          "%{customdata[0]} reviews<extra></extra>"))
        fig.update_yaxes(range=[1, 5])
        st.plotly_chart(dark(fig, 360, "Average rating", legend=False), width="stretch")
        read("Movement here is the earliest read on whether a service change landed.")

    st.markdown("### REVIEWS")
    f1, f2, f3 = st.columns([2, 1, 1])
    theme_pick = f1.selectbox("Theme", ["Any"] + list(THEMES))
    rating_pick = f2.multiselect("Rating", [1, 2, 3, 4, 5], default=[1])
    n_show = f3.slider("Show", 5, 50, 10)

    filtered = sub[sub["rating"].isin(rating_pick)] if rating_pick else sub
    if theme_pick != "Any":
        filtered = filtered[filtered[theme_pick]]

    for _, r in filtered.sort_values("date", ascending=False).head(n_show).iterrows():
        body = str(r["review"])[:600] if pd.notna(r["review"]) else ""
        st.markdown(
            f"<div class='review-card'><div class='review-meta'>"
            f"{'★' * int(r['rating'])}{'☆' * (5 - int(r['rating']))} &nbsp;·&nbsp; "
            f"{r['date']:%d %b %Y} &nbsp;·&nbsp; {r['country']}</div>"
            f"<div class='review-body'>{body}</div></div>",
            unsafe_allow_html=True)

# ───────────────────────────── Recommendations ─────────────────────────────
with t4:
    gbp = provider_summary(rates, "GBP-NGN")
    ngn_gbp = gbp[gbp["Provider"].isin(NGN_PROVIDERS)]
    spread_gbp = ngn_gbp["avg_value"].max() - ngn_gbp["avg_value"].min()
    flag = one_star["Delay or money pending"] | one_star["Customer support"]
    lead_gbp = leadership(rates, "GBP-NGN")
    lemfi_lead = lead_gbp[lead_gbp["Provider"] == "LemFi"]["share_of_readings"].iloc[0]
    advocates = (lemfi["rating"] >= 4).mean() * 100

    recs = [
        ("Turn happy customers into a reason to stay",
         f"LemFi has a strong base of advocates, with <strong>{advocates:.1f}% of reviewers "
         f"classified positively</strong>. Rather than giving everyone a discount, identify "
         f"the customers who consistently use the service and have a good experience, and "
         f"give them reasons to keep choosing LemFi: recognition, useful perks, or early "
         f"access to relevant features."),
        ("Don't sell everyone the same next product",
         f"A customer's transaction behaviour should determine what they are shown next. "
         f"Someone sending regularly may be a good candidate for a different offer from "
         f"someone with occasional, low-value transfers. <strong>Use actual customer "
         f"behaviour to decide who gets which offer</strong>, instead of pushing every "
         f"product to everyone."),
        ("Make KYC problems easier to recover from",
         f"Verification is where the experience falls apart most sharply: <strong>KYC "
         f"averages just 1.23 stars and account-blocking 1.25</strong>. When something goes "
         f"wrong, the customer should not have to figure out what happened. Tell them what "
         f"is missing, what they need to submit, and what happens next, directly in the "
         f"app, with a clear follow-up path."),
        ("Bring back people who started but didn't finish",
         f"There is a group of potential customers the review data cannot see: people who "
         f"started registration but never completed it. <strong>They have already shown "
         f"intent.</strong> A simple reminder that tells them exactly where they stopped and "
         f"what remains could recover some of that lost demand."),
        ("Don't make customers do the maths",
         f"LemFi is already competitive on exchange rates, and customers notice it: "
         f"<strong>exchange rate sentiment is 4.30/5 and fees score 3.94/5</strong>. Make "
         f"that advantage obvious when customers are deciding whether to send: show the "
         f"amount they will receive and, where useful, how it compares with alternatives."),
        ("The UK needs its own investigation",
         f"The UK stands out from the other markets. <strong>LemFi's UK rating is 3.16, "
         f"compared with 3.46+ elsewhere</strong>, and almost half of UK reviews are "
         f"detractors. This is especially important because the UK is a major GBP corridor. "
         f"Before trying to solve this with more acquisition or cheaper pricing, find out "
         f"what UK customers are experiencing differently."),
        ("Find out what changed in December, and protect it",
         f"Something important happened in December. Ratings were very low from September "
         f"through November, then <strong>jumped sharply in December and stayed around 4.0 "
         f"afterwards</strong>. That is one of the clearest signals in the data: something "
         f"improved, and customers noticed. Identify what changed, whether it was "
         f"operational, product or support-related, and make sure the improvement becomes "
         f"the new baseline."),
    ]

    for head, body in recs:
        st.markdown(
            f"<div class='rec'><div class='rec-head'>{head}</div>"
            f"<div class='rec-body'>{body}</div></div>",
            unsafe_allow_html=True)
