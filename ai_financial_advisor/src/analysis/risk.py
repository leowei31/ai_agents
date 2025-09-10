"""
Risk analysis functions.
"""
import math
import numpy as np
import pandas as pd
from typing import Dict, Any


def compute_risk_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute risk metrics from OHLCV data with robust error handling.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dict with risk metrics and conservative risk plan
        
    Raises:
        ValueError: If DataFrame is invalid or insufficient data
    """
    # Validate input DataFrame
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected DataFrame, got {type(df)}")
    
    if df.empty:
        raise ValueError("DataFrame is empty - cannot compute risk metrics")
    
    if 'Close' not in df.columns:
        raise ValueError("DataFrame missing 'Close' column required for risk computation")
    
    # Check for valid close prices
    close_prices = df['Close'].dropna()
    if close_prices.empty:
        raise ValueError("No valid close prices found in DataFrame")
    
    if len(close_prices) < 2:
        raise ValueError(f"Need at least 2 price observations for risk metrics, got {len(close_prices)}")
    
    # Compute returns with validation
    try:
        rets = close_prices.pct_change().dropna()
    except Exception as e:
        raise ValueError(f"Failed to compute returns: {e}")
    
    if rets.empty:
        raise ValueError("No valid returns computed - insufficient price data")
    
    if len(rets) < 2:
        raise ValueError(f"Need at least 2 return observations, got {len(rets)}")
    
    # Check for invalid returns (inf, extremely large values)
    if not np.isfinite(rets).all():
        print("⚠️  Found non-finite returns, filtering...")
        rets = rets[np.isfinite(rets)]
        if rets.empty:
            raise ValueError("No finite returns after filtering")
    
    # Check for extremely large returns (likely data errors)
    abs_rets = np.abs(rets)
    if abs_rets.max() > 10.0:  # 1000% daily return is likely an error
        print("⚠️  Found extremely large returns (>1000%), likely data error")
        rets = rets[abs_rets <= 10.0]
        if rets.empty:
            raise ValueError("No valid returns after filtering extreme values")
    
    try:
        # Risk metrics with safe calculations
        daily_vol = float(rets.std())
        if daily_vol == 0 or not np.isfinite(daily_vol):
            # Handle zero volatility case
            vol_ann = 0.0
            daily_vol = 1e-6  # Small value to prevent division by zero
        else:
            vol_ann = float(daily_vol * math.sqrt(252))
        
        # Drawdown calculation with error handling
        try:
            cum = (1 + rets).cumprod()
            if cum.empty or not np.isfinite(cum).all():
                max_dd = 0.0
            else:
                cummax = cum.cummax()
                dd = (cum / cummax) - 1.0
                max_dd = float(dd.min()) if not dd.empty else 0.0
        except Exception as e:
            print(f"⚠️  Drawdown calculation failed: {e}")
            max_dd = 0.0
        
        # VaR calculation with error handling
        try:
            if len(rets) >= 20:  # Need sufficient observations for percentile
                var95 = float(np.percentile(rets, 5))
            else:
                var95 = float(rets.min())  # Use worst return if insufficient data
        except Exception as e:
            print(f"⚠️  VaR calculation failed: {e}")
            var95 = float(rets.min()) if not rets.empty else 0.0
        
        # Conservative risk suggestions with bounds checking
        stop_loss_pct = max(0.001, min(0.5, round(1.5 * daily_vol, 4)))  # 0.1% to 50%
        take_profit_pct = max(0.002, min(1.0, round(2.5 * daily_vol, 4)))  # 0.2% to 100%
        pos_size_pct = max(0.1, min(10.0, round(1.0 / (daily_vol * 100 + 1e-6), 2)))  # 0.1% to 10%
        
        result = {
            'vol_annualized': vol_ann if np.isfinite(vol_ann) else 0.0,
            'max_drawdown': max_dd if np.isfinite(max_dd) else 0.0,
            'hist_VaR_1d_95': var95 if np.isfinite(var95) else 0.0,
            'n_days': int(len(rets)),
            'suggested': {
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': take_profit_pct,
                'position_size_pct': pos_size_pct
            }
        }
        
        return result
        
    except Exception as e:
        raise ValueError(f"Risk calculation failed: {e}")