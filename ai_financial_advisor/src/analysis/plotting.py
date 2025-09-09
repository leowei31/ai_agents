"""
Plotting functions for technical analysis.
"""
import os
import matplotlib.pyplot as plt
import pandas as pd
from .indicators import ema, bollinger


def plot_price_and_indicators(csv_path: str) -> str:
    """
    Plot price with EMAs and Bollinger Bands.
    
    Args:
        csv_path: Path to CSV file with OHLCV data
        
    Returns:
        Absolute path to the generated chart PNG file
    """
    from ..utils.data_utils import read_prices
    
    df = read_prices(csv_path).copy()
    df['EMA20'] = ema(df['Close'], 20)
    df['EMA50'] = ema(df['Close'], 50)
    df['BB_L'], df['BB_M'], df['BB_U'] = bollinger(df['Close'], 20, 2)
    
    plt.figure(figsize=(12, 6))
    df['Close'].plot(label='Close')
    df['EMA20'].plot(label='EMA20')
    df['EMA50'].plot(label='EMA50')
    df['BB_U'].plot(label='BB Upper')
    df['BB_L'].plot(label='BB Lower')
    plt.title('Price with EMAs & Bollinger Bands')
    plt.legend()
    
    out_path = os.path.splitext(os.path.abspath(csv_path))[0] + "_chart.png"
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    
    return os.path.abspath(out_path)