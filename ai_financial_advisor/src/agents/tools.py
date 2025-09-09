"""
CrewAI tools for the financial advisor system.
"""
import json
import os
from crewai.tools import tool
from ..data.polygon_client import PolygonClient
from ..utils.data_utils import read_prices
from ..analysis.indicators import compute_all_indicators
from ..analysis.risk import compute_risk_metrics
from ..analysis.signals import generate_rule_based_signal
from ..analysis.plotting import plot_price_and_indicators


@tool("Fetch OHLCV price history")
def fetch_ohlcv(ticker: str, period: str = '6mo', interval: str = '1d') -> str:
    """
    Fetch OHLCV using Polygon.io. Supports daily/weekly/monthly and intraday intervals.
    Returns JSON:
      {
        csv_path (absolute), rows_count, start, end, last_close,
        period, interval, ticker, sanitized_ticker
      }
    """
    client = PolygonClient()
    result = client.fetch_ohlcv(ticker, period, interval)
    return json.dumps(result)


@tool("Fetch recent news")
def fetch_news(ticker: str, limit: int = 10) -> str:
    """
    Fetch recent news using Polygon.io news endpoint.
    Returns JSON list of {title, publisher, link, time}.
    """
    client = PolygonClient()
    result = client.fetch_news(ticker, limit)
    return json.dumps(result)


@tool("Compute technical indicators")
def compute_indicators(csv_path: str) -> str:
    """
    Compute EMA20/EMA50, MACD, RSI, and Bollinger Bands from OHLCV CSV data.
    Detects crossovers and band breakouts, returning latest values and events as JSON.
    """
    df = read_prices(csv_path)
    result = compute_all_indicators(df)
    result['csv_path'] = os.path.abspath(csv_path)
    return json.dumps(result)


@tool("Compute risk metrics")
def compute_risk(csv_path: str) -> str:
    """
    Compute annualized volatility, max drawdown, and 1-day 95% VaR from OHLCV CSV data.
    Returns JSON with risk metrics and number of observations, plus conservative risk plan.
    """
    df = read_prices(csv_path)
    result = compute_risk_metrics(df)
    return json.dumps(result)


@tool("Rule-based technical signal")
def rule_based_signal(csv_path: str) -> str:
    """
    Generate a BUY/SELL/HOLD signal using simple rules on EMA, MACD, RSI, and Bollinger Bands.
    Returns JSON with signal, score, reasons, and indicator snapshot.
    """
    df = read_prices(csv_path)
    result = generate_rule_based_signal(df)
    return json.dumps(result)


@tool("Plot price & indicators")
def plot_price_indicators(csv_path: str) -> str:
    """
    Plot closing price with EMA20/50 and Bollinger Bands, saving to PNG.
    Returns the absolute file path of the generated chart.
    """
    chart_path = plot_price_and_indicators(csv_path)
    return chart_path