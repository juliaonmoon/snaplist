"""
Backtest configuration — edit these values to tune the strategy.
"""

# ── API ────────────────────────────────────────────────────────────────────────
TWELVE_DATA_API_KEY = "e5eb42e0497a459f8a2586ee45f3e468"

# ── Universe ───────────────────────────────────────────────────────────────────
SYMBOL   = "TSLA"
INTERVAL = "1day"   # Twelve Data interval string

# ── Risk / trade management ────────────────────────────────────────────────────
HOLD_DAYS       = 5     # max days to hold a position
STOP_LOSS_PCT   = 0.03  # 3 %  — price moves against you
TAKE_PROFIT_PCT = 0.06  # 6 %  — price moves in your favour

# ── Data window ────────────────────────────────────────────────────────────────
FETCH_BARS   = 400   # bars to pull from API  (~1.5 yrs of daily data)
WINDOW_BARS  = 70    # trading days in the random 90-calendar-day slice
