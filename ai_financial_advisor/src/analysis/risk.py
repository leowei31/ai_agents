"""
Risk analysis functions.
"""
import math
import numpy as np
import pandas as pd
from typing import Dict, Any


def compute_risk_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute risk metrics from OHLCV data.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dict with risk metrics and conservative risk plan
    """
    rets = df['Close'].pct_change().dropna()
    
    if rets.empty:
        raise ValueError("Not enough return observations to compute risk metrics.")
    
    # Risk metrics
    vol_ann = float(rets.std() * math.sqrt(252))
    cum = (1 + rets).cumprod()
    dd = (cum / cum.cummax()) - 1.0
    max_dd = float(dd.min())
    var95 = float(np.percentile(rets, 5))
    
    # Conservative risk suggestions
    daily_vol = float(rets.std())
    stop_loss_pct = round(1.5 * daily_vol, 4)
    take_profit_pct = round(2.5 * daily_vol, 4)
    pos_size_pct = round(max(0.5, min(5.0, 1.0 / (daily_vol * 100 + 1e-9))), 2)
    
    return {
        'vol_annualized': vol_ann,
        'max_drawdown': max_dd,
        'hist_VaR_1d_95': var95,
        'n_days': int(len(rets)),
        'suggested': {
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct,
            'position_size_pct': pos_size_pct
        }
    }