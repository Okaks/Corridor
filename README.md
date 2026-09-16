# Corridor

What it costs to send money to Nigeria, who wins on price, and what customers say
about the apps that move it.

Two public datasets, one argument:

- **Rate log** — 305 readings. Five providers (LemFi, NALA, Sendwave, Taptap Send, Wise),
  two corridors (GBP-NGN, USD-NGN), twice daily, 19 August to 4 September 2026, on a
  fixed 100-unit send amount against a mid-market benchmark captured at the same moment.
- **App reviews** — 14,925 public app store reviews across the same five apps.

## Findings

1. The four Nigeria-focused providers price within 0.16pp of each other on GBP-NGN and
   0.20pp on USD-NGN. LemFi leads most often (40% of GBP-NGN readings, 55% of USD-NGN)
   but the lead turns over between the morning and afternoon reading.
2. LemFi holds the highest average rating in that set at 3.99, on a bimodal
   distribution: 69% five star, 21.5% one star.
3. Exchange rate is a praise theme, not a complaint theme — 4.30 average rating when
   mentioned, present in only 5% of one-star reviews. Delay and customer support appear
   in 37% of one-star reviews and carry averages of 1.47 and 1.88.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files

- `app.py` — the four-tab dashboard
- `loaders.py` — data loading, derived metrics, theme detection
- `data/` — the two source workbooks

Companion project: **Cadence**, a customer lifecycle and growth engine built on
simulated behavioural data.
