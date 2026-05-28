# TSLA 3-Candle Strategy Backtester

Backtests four classic 3-candle candlestick patterns on TSLA daily data pulled from the **Twelve Data API**.  
A random 90-day window is chosen each run so you get a fresh slice of the market every time.

---

## Patterns

| Pattern | Type | Signal |
|---|---|---|
| **Three White Soldiers** | Continuation | 3 rising bullish candles, each opening inside the prior body with tiny upper wicks → **Long** |
| **Three Black Crows** | Continuation | 3 falling bearish candles, each opening inside the prior body with tiny lower wicks → **Short** |
| **Morning Star** | Reversal | Bearish candle → small doji/spinning top → strong bullish candle → **Long** |
| **Evening Star** | Reversal | Bullish candle → small doji/spinning top → strong bearish candle → **Short** |

---

## Trade Rules

- **Entry** — next bar's open after the 3rd candle confirms
- **Stop Loss** — 3 % against entry (configurable)
- **Take Profit** — 6 % in favour (configurable)
- **Max hold** — 5 trading days; exits at close if SL/TP not hit

---

## Quick Start

```bash
cd backtest

# Install dependencies
pip install -r requirements.txt

# Run with real Twelve Data API (recommended)
python three_candle_strategy.py --live

# Reproducible run (fix the random window)
python three_candle_strategy.py --live --seed 42

# Demo mode — synthetic TSLA-like data, no internet needed
python three_candle_strategy.py
```

### API key note
Your Twelve Data API key is pre-configured in `config.py`.  
If you get a **403 Forbidden**, log in to [twelvedata.com](https://twelvedata.com) → API Keys → remove any IP/host allowlist restrictions.

---

## Output

```
=================================================================
  TSLA  |  3-Candle Strategy Backtest
  Hold: 5d  |  SL: 3%  |  TP: 6%
=================================================================
  Source  : Twelve Data API
  Window  : 2023-04-03  →  2023-07-18  (70 trading days)
  Price   : $185.52  →  $269.80

╭──────────────────────┬───────┬─────────┬──────┬──────┬──────────┬────────────┬────────┬─────────╮
│ Pattern              │ Dir   │ Signals │ Wins │ Win% │ Avg PnL  │ Total PnL  │ Best   │ Worst   │
├──────────────────────┼───────┼─────────┼──────┼──────┼──────────┼────────────┼────────┼─────────┤
│ Three White Soldiers │ LONG  │       2 │    2 │ 100% │ +6.00%   │ +12.00%    │ +6.00% │ +6.00%  │
│ Three Black Crows    │ SHORT │       0 │    0 │  —   │  —       │  —         │  —     │  —      │
│ Morning Star         │ LONG  │       1 │    1 │ 100% │ +6.00%   │  +6.00%    │ +6.00% │ +6.00%  │
│ Evening Star         │ SHORT │       1 │    0 │   0% │ -3.00%   │  -3.00%    │ -3.00% │ -3.00%  │
╰──────────────────────┴───────┴─────────┴──────┴──────┴──────────┴────────────┴────────┴─────────╯
```

Followed by a per-pattern trade log and a combined chronological equity curve.

---

## Configuration

All parameters live in **`config.py`** — no need to touch the main script:

| Parameter | Default | Description |
|---|---|---|
| `SYMBOL` | `TSLA` | Ticker symbol |
| `HOLD_DAYS` | `5` | Max days to hold |
| `STOP_LOSS_PCT` | `0.03` | Stop loss (3 %) |
| `TAKE_PROFIT_PCT` | `0.06` | Take profit (6 %) |
| `FETCH_BARS` | `400` | Bars pulled from API |
| `WINDOW_BARS` | `70` | Trading days in random window |

---

## Files

```
backtest/
├── three_candle_strategy.py   # main backtest engine + CLI
├── config.py                  # all tunable parameters
├── requirements.txt           # pip dependencies
└── README.md                  # this file
```
