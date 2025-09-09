"""
Trading signal generation.
"""
from typing import Dict, Any
from .indicators import compute_all_indicators


def generate_rule_based_signal(df) -> Dict[str, Any]:
    """
    Generate BUY/SELL/HOLD signal using simple rules.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dict with signal, score, reasons, and indicators
    """
    ind = compute_all_indicators(df)
    score = 0.0
    reasons = []
    
    # EMA trend
    if ind['ema20'] > ind['ema50']:
        score += 1
        reasons.append('EMA20 > EMA50 (uptrend)')
    else:
        score -= 1
        reasons.append('EMA20 < EMA50 (downtrend)')
    
    # MACD momentum
    if ind['macd'] > ind['macd_signal']:
        score += 1
        reasons.append('MACD > signal (bullish momentum)')
    else:
        score -= 1
        reasons.append('MACD < signal (bearish momentum)')
    
    # RSI overbought/oversold
    if ind['rsi'] < 30:
        score += 0.5
        reasons.append('RSI < 30 (oversold)')
    elif ind['rsi'] > 70:
        score -= 0.5
        reasons.append('RSI > 70 (overbought)')
    
    # Bollinger Bands mean reversion
    if ind['close'] < ind['bb_lower']:
        score += 0.5
        reasons.append('Below lower band (mean-reversion up)')
    if ind['close'] > ind['bb_upper']:
        score -= 0.5
        reasons.append('Above upper band (mean-reversion down)')
    
    # Generate signal
    signal = 'HOLD'
    if score >= 1.5:
        signal = 'BUY'
    elif score <= -1.5:
        signal = 'SELL'
    
    return {
        'signal': signal,
        'score': score,
        'reasons': reasons,
        'indicators': ind
    }