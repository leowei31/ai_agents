"""
Technical analysis indicators.
"""
import pandas as pd
import numpy as np
from typing import Tuple


def ema(series: pd.Series, span: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-12)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
    """Calculate MACD and signal line."""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


def bollinger(series: pd.Series, period: int = 20, std_mult: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    mid = series.rolling(window=period).mean()
    sd = series.rolling(window=period).std()
    upper = mid + std_mult * sd
    lower = mid - std_mult * sd
    return lower, mid, upper


def compute_all_indicators(df: pd.DataFrame) -> dict:
    """
    Compute all technical indicators for a DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dict with latest indicator values and events
    """
    df = df.copy()
    
    # Compute indicators
    df['EMA20'] = ema(df['Close'], 20)
    df['EMA50'] = ema(df['Close'], 50)
    macd_line, sig_line = macd(df['Close'])
    df['MACD'] = macd_line
    df['MACD_SIG'] = sig_line
    df['BB_L'], df['BB_M'], df['BB_U'] = bollinger(df['Close'], 20, 2)
    df['RSI'] = rsi(df['Close'], 14)
    
    if len(df) < 2:
        raise ValueError("Not enough rows to compute crossovers (need ≥ 2 rows).")
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    events = []
    
    # Detect crossovers and events
    if prev['EMA20'] < prev['EMA50'] and latest['EMA20'] > latest['EMA50']:
        events.append('Bullish EMA20/50 golden cross today')
    if prev['EMA20'] > prev['EMA50'] and latest['EMA20'] < latest['EMA50']:
        events.append('Bearish EMA20/50 death cross today')
    if prev['MACD'] < prev['MACD_SIG'] and latest['MACD'] > latest['MACD_SIG']:
        events.append('Bullish MACD cross above signal')
    if prev['MACD'] > prev['MACD_SIG'] and latest['MACD'] < prev['MACD_SIG']:
        events.append('Bearish MACD cross below signal')
    if latest['Close'] < latest['BB_L']:
        events.append('Price closed below lower Bollinger band (oversold)')
    if latest['Close'] > latest['BB_U']:
        events.append('Price closed above upper Bollinger band (overbought)')
    
    return {
        'close': float(latest['Close']),
        'ema20': float(latest['EMA20']),
        'ema50': float(latest['EMA50']),
        'macd': float(latest['MACD']),
        'macd_signal': float(latest['MACD_SIG']),
        'rsi': float(latest['RSI']),
        'bb_lower': float(latest['BB_L']),
        'bb_middle': float(latest['BB_M']),
        'bb_upper': float(latest['BB_U']),
        'events': events,
    }