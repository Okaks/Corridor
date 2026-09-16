"""Data loading and derived metrics for Corridor."""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"

NGN_PROVIDERS = ["LemFi", "NALA", "Sendwave", "Taptap Send"]
ALL_PROVIDERS = NGN_PROVIDERS + ["Wise"]
FOCUS = "LemFi"

PROVIDER_COLOR = {
    "LemFi": "#0F6F5C",
    "NALA": "#7C8C9B",
    "Sendwave": "#A8927D",
    "Taptap Send": "#9B8AA6",
    "Wise": "#C2C8C5",
}

THEMES = {
    "Delay or money pending": r"\b(?:delay|delayed|slow|pending|stuck|still waiting)\b",
    "Customer support": r"\b(?:support|customer service|customer care|agent|respond|responded|chat)\b",
    "Failed transaction": r"\b(?:fail|failed|failing|declin|rejected|error)\b",
    "Account blocked": r"\b(?:block|blocked|freeze|frozen|suspend|suspended|locked|restrict)\b",
    "Exchange rate": r"\b(?:rate|rates|exchange|taux|tasa|cambio)\b",
    "Fees and charges": r"\b(?:fee|fees|charge|charges|hidden)\b",
    "Verification or KYC": r"\b(?:verif|kyc|document|identity|selfie)\b",
    "Speed": r"\b(?:fast|quick|instant|seconds|minutes|prompt|swift|speedy)\b",
    "Trust and safety": r"\b(?:trust|reliable|reliability|scam|fraud|safe|secure)\b",
    "App experience": r"\b(?:interface|update|login|log in|crash|bug|glitch)\b",
}

POSITIVE_THEMES = {"Speed", "Exchange rate", "Trust and safety"}


@st.cache_data(show_spinner=False)
def load_rates() -> pd.DataFrame:
    df = pd.read_excel(DATA / "FX_Corridor_Tracker.xlsx", sheet_name="Rate Log", header=1)
    df = df[df["Date"].notna()].copy()

    df["Date"] = pd.to_datetime(df["Date"])
    gross = df["Send Amount"] * df["Mid-Market Rate"]

    df["value_vs_mid"] = (df["Amount Received"] / gross - 1) * 100
    df["fx_margin"] = (df["Advertised Rate"] / df["Mid-Market Rate"] - 1) * 100
    df["fee_pct"] = df["Transfer Fee"] / df["Send Amount"] * 100

    return df[
        [
            "Date", "Slot", "Provider", "Corridor", "Send Amount",
            "Advertised Rate", "Transfer Fee", "Amount Received", "Mid-Market Rate",
            "value_vs_mid", "fx_margin", "fee_pct", "Notes",
        ]
    ]


@st.cache_data(show_spinner=False)
def load_reviews() -> pd.DataFrame:
    df = pd.read_excel(DATA / "app_reviews_v2.xlsx", sheet_name="reviews")
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["text"] = (df["title"].fillna("") + " " + df["review"].fillna("")).str.lower()

    for name, pattern in THEMES.items():
        df[name] = df["text"].str.contains(pattern, regex=True, na=False)

    return df


@st.cache_data(show_spinner=False)
def provider_summary(rates: pd.DataFrame, corridor: str) -> pd.DataFrame:
    sub = rates[rates["Corridor"] == corridor]
    out = (
        sub.groupby("Provider")
        .agg(
            readings=("value_vs_mid", "size"),
            avg_value=("value_vs_mid", "mean"),
            best_day=("value_vs_mid", "max"),
            worst_day=("value_vs_mid", "min"),
            volatility=("value_vs_mid", "std"),
            avg_fee=("fee_pct", "mean"),
        )
        .round(2)
        .sort_values("avg_value", ascending=False)
    )
    return out.reset_index()


@st.cache_data(show_spinner=False)
def leadership(rates: pd.DataFrame, corridor: str) -> pd.DataFrame:
    sub = rates[(rates["Corridor"] == corridor) & (rates["Provider"].isin(NGN_PROVIDERS))]
    wide = sub.pivot_table(index=["Date", "Slot"], columns="Provider", values="value_vs_mid")
    wide = wide.dropna(how="all")

    winners = wide.idxmax(axis=1).value_counts()
    total = len(wide)

    out = pd.DataFrame({"Provider": NGN_PROVIDERS})
    out["times_cheapest"] = out["Provider"].map(winners).fillna(0).astype(int)
    out["share_of_readings"] = (out["times_cheapest"] / total * 100).round(1)
    return out.sort_values("times_cheapest", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def daily_spread(rates: pd.DataFrame, corridor: str) -> pd.DataFrame:
    sub = rates[(rates["Corridor"] == corridor) & (rates["Provider"].isin(NGN_PROVIDERS))]
    wide = sub.pivot_table(index="Date", columns="Provider", values="value_vs_mid")
    return pd.DataFrame(
        {"Date": wide.index, "spread": (wide.max(axis=1) - wide.min(axis=1)).values}
    )


@st.cache_data(show_spinner=False)
def theme_impact(reviews: pd.DataFrame, app: str) -> pd.DataFrame:
    sub = reviews[reviews["app"] == app]
    one_star = sub[sub["rating"] == 1]

    rows = []
    for name in THEMES:
        flagged = sub[sub[name]]
        rows.append(
            {
                "Theme": name,
                "Reviews": len(flagged),
                "Share of reviews": round(len(flagged) / len(sub) * 100, 1),
                "Avg rating": round(flagged["rating"].mean(), 2) if len(flagged) else float("nan"),
                "Share of 1-star": round(one_star[name].sum() / max(len(one_star), 1) * 100, 1),
                "Direction": "Praise" if name in POSITIVE_THEMES else "Complaint",
            }
        )
    return pd.DataFrame(rows).sort_values("Avg rating").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def intraday_move(rates: pd.DataFrame, corridor: str) -> pd.DataFrame:
    """How much each provider repriced between the morning and afternoon reading."""
    sub = rates[rates["Corridor"] == corridor]
    wide = sub.pivot_table(index=["Date", "Provider"], columns="Slot", values="value_vs_mid")
    wide = wide.dropna()
    if wide.empty or wide.shape[1] < 2:
        return pd.DataFrame(columns=["Provider", "avg_move", "max_move", "days_moved"])

    a, b = wide.columns[0], wide.columns[1]
    wide["move"] = (wide[b] - wide[a]).abs()
    out = (
        wide.reset_index()
        .groupby("Provider")
        .agg(avg_move=("move", "mean"), max_move=("move", "max"),
             days_moved=("move", lambda s: (s > 0.02).sum()))
        .round(3)
        .sort_values("avg_move", ascending=False)
        .reset_index()
    )
    return out


@st.cache_data(show_spinner=False)
def sentiment_bands(reviews: pd.DataFrame) -> pd.DataFrame:
    r = reviews.copy()
    r["band"] = pd.cut(r["rating"], [0, 2, 3, 5],
                       labels=["Detractors", "Neutral", "Advocates"])
    counts = r.groupby(["app", "band"], observed=True).size().rename("n").reset_index()
    counts["share"] = counts["n"] / counts.groupby("app")["n"].transform("sum") * 100
    out = counts.drop(columns="n")
    order = (out[out["band"] == "Advocates"].sort_values("share", ascending=False)["app"]
             .tolist())
    out["app"] = pd.Categorical(out["app"], categories=order, ordered=True)
    return out.sort_values("app")


@st.cache_data(show_spinner=False)
def app_benchmark(reviews: pd.DataFrame) -> pd.DataFrame:
    out = (
        reviews.groupby("app")
        .agg(
            reviews=("rating", "size"),
            avg_rating=("rating", "mean"),
            five_star=("rating", lambda s: (s == 5).mean() * 100),
            one_star=("rating", lambda s: (s == 1).mean() * 100),
        )
        .round(2)
        .sort_values("avg_rating", ascending=False)
    )
    return out.reset_index()
