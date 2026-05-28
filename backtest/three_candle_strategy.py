"""
3-Candle Strategy Backtester for TSLA
Patterns: Three White Soldiers, Three Black Crows, Morning Star, Evening Star

Data source priority:
  1. Twelve Data API (use when running locally with a valid API key)
  2. Synthetic TSLA-like data (fallback for environments without network access)

Usage:
  python three_candle_strategy.py            # synthetic demo data
  python three_candle_strategy.py --live     # real data via Twelve Data API
"""

import argparse
import sys
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from tabulate import tabulate

from config import (
    TWELVE_DATA_API_KEY, SYMBOL, INTERVAL,
    HOLD_DAYS, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    FETCH_BARS, WINDOW_BARS,
)


# ── Data fetching ──────────────────────────────────────────────────────────────

def fetch_from_twelvedata() -> pd.DataFrame:
    """Fetch ~400 bars from Twelve Data API (requires live network + valid key)."""
    import requests
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": "1day",
        "outputsize": FETCH_BARS,
        "apikey": TWELVE_DATA_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "values" not in data:
        raise ValueError(f"Twelve Data error: {data.get('message', data)}")

    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df


def generate_synthetic_tsla(n_days: int = 600, seed=None) -> pd.DataFrame:
    """
    Simulate TSLA-like daily OHLCV bars.
    Parameters tuned to TSLA's historical volatility (~3 % daily, ~0.05 % drift).
    """
    rng = np.random.default_rng(seed)
    start_price = 250.0
    daily_vol   = 0.030
    daily_drift = 0.0005

    # Geometric Brownian Motion for the close
    log_returns = rng.normal(daily_drift - 0.5 * daily_vol**2, daily_vol, n_days)
    closes      = start_price * np.exp(np.cumsum(log_returns))

    rows = []
    base_date = datetime(2020, 1, 2)
    for i in range(n_days):
        c = closes[i]
        prev_c = closes[i - 1] if i > 0 else c

        # Intraday range driven by a separate vol draw
        intraday_range = abs(rng.normal(0, daily_vol * c)) + 0.5
        direction      = rng.choice([-1, 1])

        o = prev_c * (1 + rng.normal(0, 0.005))   # gap open
        h = max(o, c) + abs(rng.normal(0, intraday_range * 0.4))
        l = min(o, c) - abs(rng.normal(0, intraday_range * 0.4))

        rows.append({
            "datetime": base_date + timedelta(days=i + (i // 5) * 2),  # skip weekends roughly
            "open":  round(o, 2),
            "high":  round(max(h, o, c) + 0.01, 2),
            "low":   round(min(l, o, c) - 0.01, 2),
            "close": round(c, 2),
            "volume": int(rng.integers(20_000_000, 80_000_000)),
        })

    return pd.DataFrame(rows)


def pick_random_90day_slice(df: pd.DataFrame) -> pd.DataFrame:
    """Randomly select ~65 consecutive trading days (≈ 90 calendar days)."""
    if len(df) <= WINDOW_BARS + HOLD_DAYS:
        return df.reset_index(drop=True)
    max_start = len(df) - WINDOW_BARS - HOLD_DAYS
    start     = random.randint(0, max_start)
    return df.iloc[start: start + WINDOW_BARS + HOLD_DAYS].reset_index(drop=True)


# ── Candle helpers ─────────────────────────────────────────────────────────────

def body(r):       return abs(r["close"] - r["open"])
def upper_wick(r): return r["high"]  - max(r["open"], r["close"])
def lower_wick(r): return min(r["open"], r["close"]) - r["low"]
def is_bull(r):    return r["close"] > r["open"]
def is_bear(r):    return r["close"] < r["open"]


# ── Pattern detectors ──────────────────────────────────────────────────────────

def three_white_soldiers(c1, c2, c3) -> bool:
    """Three consecutive bullish candles, each closing higher with tiny upper wicks."""
    if not (is_bull(c1) and is_bull(c2) and is_bull(c3)):
        return False
    if not (c3["close"] > c2["close"] > c1["close"]):
        return False
    # Each candle opens within the prior candle's body
    if not (c1["open"] < c2["open"] < c1["close"]):
        return False
    if not (c2["open"] < c3["open"] < c2["close"]):
        return False
    # Small upper wicks (buying pressure right to the close)
    for c in (c1, c2, c3):
        if body(c) == 0 or upper_wick(c) > body(c) * 0.3:
            return False
    return True


def three_black_crows(c1, c2, c3) -> bool:
    """Three consecutive bearish candles, each closing lower with tiny lower wicks."""
    if not (is_bear(c1) and is_bear(c2) and is_bear(c3)):
        return False
    if not (c3["close"] < c2["close"] < c1["close"]):
        return False
    if not (c1["close"] < c2["open"] < c1["open"]):
        return False
    if not (c2["close"] < c3["open"] < c2["open"]):
        return False
    for c in (c1, c2, c3):
        if body(c) == 0 or lower_wick(c) > body(c) * 0.3:
            return False
    return True


def morning_star(c1, c2, c3) -> bool:
    """
    Bearish candle → small indecision candle (doji/spinning top) → strong bullish candle.
    Bullish reversal signal.
    """
    if not is_bear(c1) or body(c1) == 0:
        return False
    # Middle: small body (≤ 30 % of c1 body)
    if body(c2) > body(c1) * 0.30:
        return False
    if not is_bull(c3) or body(c3) == 0:
        return False
    # c3 closes above the midpoint of c1
    if c3["close"] <= (c1["open"] + c1["close"]) / 2:
        return False
    # c2 gaps down from c1 close
    if c2["open"] >= c1["close"]:
        return False
    return True


def evening_star(c1, c2, c3) -> bool:
    """
    Bullish candle → small indecision candle → strong bearish candle.
    Bearish reversal signal.
    """
    if not is_bull(c1) or body(c1) == 0:
        return False
    if body(c2) > body(c1) * 0.30:
        return False
    if not is_bear(c3) or body(c3) == 0:
        return False
    if c3["close"] >= (c1["open"] + c1["close"]) / 2:
        return False
    if c2["open"] <= c1["close"]:
        return False
    return True


PATTERNS: dict[str, tuple] = {
    "Three White Soldiers": (three_white_soldiers, "long"),
    "Three Black Crows":    (three_black_crows,    "short"),
    "Morning Star":         (morning_star,          "long"),
    "Evening Star":         (evening_star,          "short"),
}


# ── Backtesting engine ─────────────────────────────────────────────────────────

def simulate_trade(df: pd.DataFrame, entry_idx: int, direction: str) -> dict | None:
    """Simulate one trade from entry_idx+1 open, with SL/TP and max HOLD_DAYS exit."""
    if entry_idx + 1 >= len(df):
        return None

    entry_price = df.iloc[entry_idx + 1]["open"]
    exit_price  = None
    exit_day    = None

    for j in range(1, HOLD_DAYS + 1):
        if entry_idx + j >= len(df):
            break
        bar = df.iloc[entry_idx + j]

        if direction == "long":
            sl = entry_price * (1 - STOP_LOSS_PCT)
            tp = entry_price * (1 + TAKE_PROFIT_PCT)
            if bar["low"] <= sl:
                exit_price, exit_day = sl, j; break
            if bar["high"] >= tp:
                exit_price, exit_day = tp, j; break
            if j == HOLD_DAYS:
                exit_price, exit_day = bar["close"], j
        else:  # short
            sl = entry_price * (1 + STOP_LOSS_PCT)
            tp = entry_price * (1 - TAKE_PROFIT_PCT)
            if bar["high"] >= sl:
                exit_price, exit_day = sl, j; break
            if bar["low"] <= tp:
                exit_price, exit_day = tp, j; break
            if j == HOLD_DAYS:
                exit_price, exit_day = bar["close"], j

    if exit_price is None:
        return None

    raw_pnl = (exit_price - entry_price) if direction == "long" else (entry_price - exit_price)
    pnl_pct = raw_pnl / entry_price * 100

    return {
        "date":      df.iloc[entry_idx]["datetime"].strftime("%Y-%m-%d"),
        "entry":     round(entry_price, 2),
        "exit":      round(exit_price, 2),
        "exit_day":  exit_day,
        "direction": direction.upper(),
        "pnl_pct":   round(pnl_pct, 2),
        "result":    "WIN" if pnl_pct > 0 else "LOSS",
    }


def run_backtest(df: pd.DataFrame) -> dict[str, list[dict]]:
    results: dict[str, list] = {name: [] for name in PATTERNS}

    for i in range(2, len(df) - HOLD_DAYS - 1):
        c1, c2, c3 = df.iloc[i - 2], df.iloc[i - 1], df.iloc[i]
        for name, (detector, direction) in PATTERNS.items():
            if detector(c1, c2, c3):
                trade = simulate_trade(df, i, direction)
                if trade:
                    results[name].append(trade)

    return results


# ── Reporting ──────────────────────────────────────────────────────────────────

def build_summary(results: dict) -> list[dict]:
    rows = []
    for name, trades in results.items():
        direction = PATTERNS[name][1].upper()
        if not trades:
            rows.append({
                "Pattern": name, "Dir": direction,
                "Signals": 0, "Wins": 0, "Win%": "—",
                "Avg PnL": "—", "Total PnL": "—",
                "Best": "—", "Worst": "—",
            })
            continue
        pnls = [t["pnl_pct"] for t in trades]
        wins = sum(1 for p in pnls if p > 0)
        rows.append({
            "Pattern":   name,
            "Dir":       direction,
            "Signals":   len(trades),
            "Wins":      wins,
            "Win%":      f"{wins/len(trades)*100:.0f}%",
            "Avg PnL":   f"{np.mean(pnls):+.2f}%",
            "Total PnL": f"{sum(pnls):+.2f}%",
            "Best":      f"{max(pnls):+.2f}%",
            "Worst":     f"{min(pnls):+.2f}%",
        })
    return rows


def print_trade_log(results: dict):
    for name, trades in results.items():
        if not trades:
            continue
        print(f"\n  {name}:")
        rows = [
            [t["date"], t["direction"], f"${t['entry']:.2f}", f"${t['exit']:.2f}",
             f"day {t['exit_day']}", f"{t['pnl_pct']:+.2f}%", t["result"]]
            for t in trades
        ]
        print(tabulate(rows,
                       headers=["Signal Date", "Dir", "Entry", "Exit", "Held", "PnL %", "Result"],
                       tablefmt="simple"))


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true",
                        help="Fetch real data from Twelve Data API")
    parser.add_argument("--seed", type=int, default=None,
                        help="Fix random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
    else:
        random.seed()

    print(f"\n{'='*65}")
    print(f"  TSLA  |  3-Candle Strategy Backtest")
    print(f"  Hold: {HOLD_DAYS}d  |  SL: {STOP_LOSS_PCT*100:.0f}%  |  TP: {TAKE_PROFIT_PCT*100:.0f}%")
    print(f"{'='*65}")

    if args.live:
        print("\n  Fetching live TSLA data from Twelve Data...")
        try:
            full_df = fetch_from_twelvedata()
            data_note = "Twelve Data API"
        except Exception as exc:
            print(f"  [!] API fetch failed: {exc}")
            print("  Falling back to synthetic data.")
            full_df = generate_synthetic_tsla(600)
            data_note = "Synthetic (API unavailable)"
    else:
        print("\n  Generating synthetic TSLA-like data (run with --live for real data)...")
        full_df = generate_synthetic_tsla(600)
        data_note = "Synthetic TSLA-like"

    df = pick_random_90day_slice(full_df)
    start_str = df.iloc[0]["datetime"].strftime("%Y-%m-%d")
    end_str   = df.iloc[-1]["datetime"].strftime("%Y-%m-%d")

    print(f"  Source  : {data_note}")
    print(f"  Window  : {start_str}  →  {end_str}  ({len(df)} trading days)")
    print(f"  Price   : ${df.iloc[0]['close']:.2f}  →  ${df.iloc[-1]['close']:.2f}")

    print(f"\n  Scanning for 3-candle patterns...")
    results = run_backtest(df)

    total_signals = sum(len(v) for v in results.values())
    print(f"  {total_signals} signal(s) detected across all patterns.\n")

    summary = build_summary(results)
    print(tabulate(summary, headers="keys", tablefmt="rounded_outline"))

    if total_signals > 0:
        print_trade_log(results)

    # Overall equity curve (naive: sum of all pattern PnLs in chronological order)
    all_trades = sorted(
        [t for trades in results.values() for t in trades],
        key=lambda t: t["date"]
    )
    if all_trades:
        cum = 0.0
        print(f"\n  Chronological trade log (all patterns combined):")
        rows = []
        for t in all_trades:
            cum += t["pnl_pct"]
            rows.append([t["date"], t["direction"],
                         f"{t['pnl_pct']:+.2f}%", f"{cum:+.2f}%"])
        print(tabulate(rows,
                       headers=["Date", "Dir", "PnL%", "Cumulative%"],
                       tablefmt="simple"))

    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    main()
