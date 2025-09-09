"""
Cached CrewAI tools that use pre-fetched data instead of making API calls.
These tools are designed for backtesting and scenarios where API rate limits are a concern.
"""
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from crewai.tools import tool
from ..utils.data_utils import read_prices
from ..analysis.indicators import compute_all_indicators
from ..analysis.risk import compute_risk_metrics
from ..analysis.signals import generate_rule_based_signal
from ..analysis.plotting import plot_price_and_indicators
from ..data.polygon_client import PolygonClient


class DataCache:
    """Manages cached data for tools."""
    
    def __init__(self):
        self.csv_cache = {}
        self.news_cache = {}
        self.polygon_client = None
    
    def set_csv_data(self, ticker: str, csv_path: str, period: str, interval: str):
        """Set cached CSV data for a ticker."""
        self.csv_cache[ticker] = {
            'csv_path': os.path.abspath(csv_path),
            'period': period,
            'interval': interval,
            'last_updated': datetime.now()
        }
        print(f"📦 Cached CSV data for {ticker}: {csv_path}")
    
    def get_csv_data(self, ticker: str) -> dict:
        """Get cached CSV data for a ticker."""
        if ticker not in self.csv_cache:
            raise ValueError(f"No cached data for {ticker}. Set cache first with set_csv_data()")
        return self.csv_cache[ticker]
    
    def set_historical_news(self, ticker: str, news_data: list, start_date: str, end_date: str):
        """Set cached historical news data."""
        cache_key = f"{ticker}_{start_date}_{end_date}"
        self.news_cache[cache_key] = {
            'news': news_data,
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'cached_at': datetime.now()
        }
        print(f"📦 Cached {len(news_data)} news articles for {ticker} ({start_date} to {end_date})")
    
    def get_historical_news(self, ticker: str, target_date: datetime, days_back: int = 7) -> list:
        """Get cached historical news around a target date."""
        start_date = (target_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
        end_date = target_date.strftime('%Y-%m-%d')
        cache_key = f"{ticker}_{start_date}_{end_date}"
        
        # Try exact match first
        if cache_key in self.news_cache:
            return self.news_cache[cache_key]['news']
        
        # Try to find overlapping cached data
        for key, cached in self.news_cache.items():
            if ticker in key:
                cached_start = datetime.strptime(cached['start_date'], '%Y-%m-%d')
                cached_end = datetime.strptime(cached['end_date'], '%Y-%m-%d')
                target_start = datetime.strptime(start_date, '%Y-%m-%d')
                target_end = datetime.strptime(end_date, '%Y-%m-%d')
                
                # Check if target range is within cached range
                if cached_start <= target_start and cached_end >= target_end:
                    # Filter news to target date range
                    filtered_news = []
                    for article in cached['news']:
                        article_date = article.get('time', '')[:10]  # Get YYYY-MM-DD part
                        if start_date <= article_date <= end_date:
                            filtered_news.append(article)
                    return filtered_news
        
        # No cached data found
        print(f"⚠️  No cached news data for {ticker} around {target_date.strftime('%Y-%m-%d')}")
        return []
    
    def fetch_and_cache_historical_news(self, ticker: str, start_date: str, end_date: str, limit: int = 1000):
        """Fetch and cache historical news for a date range (uses 1 API call)."""
        if not self.polygon_client:
            self.polygon_client = PolygonClient()
        
        print(f"📡 Fetching historical news for {ticker} from {start_date} to {end_date}")
        
        url = f"{self.polygon_client.base_url}/v2/reference/news"
        params = {
            'ticker': ticker,
            'published_utc.gte': start_date,
            'published_utc.lte': end_date,
            'limit': min(1000, limit),
            'sort': 'published_utc'
        }
        
        try:
            data = self.polygon_client._make_request(url, params)
            results = data.get('results', []) or []
            
            # Convert to our expected format
            news_items = []
            for article in results:
                publisher = article.get('publisher', {}).get('name', '') or ''
                news_items.append({
                    'title': article.get('title', ''),
                    'publisher': publisher,
                    'link': article.get('article_url', ''),
                    'time': article.get('published_utc', '')
                })
            
            # Cache the results
            self.set_historical_news(ticker, news_items, start_date, end_date)
            return news_items
            
        except Exception as e:
            print(f"❌ Error fetching historical news: {e}")
            return []


# Global cache instance
_data_cache = DataCache()


@tool("Fetch OHLCV price history (cached)")
def fetch_ohlcv_cached(ticker: str, period: str = '6mo', interval: str = '1d') -> str:
    """
    Fetch OHLCV data using cached CSV file (no API calls).
    Returns JSON with csv_path and metadata.
    """
    try:
        cached_data = _data_cache.get_csv_data(ticker)
        
        # Create response in expected format
        df = read_prices(cached_data['csv_path'])
        result = {
            'csv_path': cached_data['csv_path'],
            'rows_count': len(df),
            'start': str(df.index[0].date()),
            'end': str(df.index[-1].date()),
            'last_close': float(df['Close'].iloc[-1]),
            'period': cached_data['period'],
            'interval': cached_data['interval'],
            'ticker': ticker,
            'sanitized_ticker': ticker.replace('/', '-').replace('\\', '-').replace(' ', '').replace(':', '-').replace('.', '-')
        }
        
        print(f"✅ Using cached OHLCV data for {ticker}: {result['rows_count']} rows")
        return json.dumps(result)
        
    except Exception as e:
        print(f"❌ Error accessing cached OHLCV data: {e}")
        return json.dumps({'error': str(e)})


@tool("Fetch recent news (cached/historical)")
def fetch_news_cached(ticker: str, limit: int = 10, target_date: str = None) -> str:
    """
    Fetch news using cached historical data (no API calls).
    If target_date is provided, returns news around that date.
    Returns JSON list of {title, publisher, link, time}.
    """
    try:
        if target_date:
            # Parse target date
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        else:
            # Use current date
            target_dt = datetime.now()
        
        # Get cached historical news around the target date
        news_items = _data_cache.get_historical_news(ticker, target_dt, days_back=7)
        
        # Limit results
        limited_news = news_items[:limit]
        
        print(f"✅ Using cached news for {ticker} around {target_dt.strftime('%Y-%m-%d')}: {len(limited_news)} articles")
        return json.dumps(limited_news)
        
    except Exception as e:
        print(f"❌ Error accessing cached news data: {e}")
        return json.dumps([])


@tool("Compute technical indicators")
def compute_indicators_cached(csv_path: str) -> str:
    """
    Compute EMA20/EMA50, MACD, RSI, and Bollinger Bands from OHLCV CSV data.
    Detects crossovers and band breakouts, returning latest values and events as JSON.
    """
    try:
        df = read_prices(csv_path)
        result = compute_all_indicators(df)
        result['csv_path'] = os.path.abspath(csv_path)
        return json.dumps(result)
    except Exception as e:
        print(f"❌ Error computing indicators: {e}")
        return json.dumps({'error': str(e)})


@tool("Compute risk metrics")
def compute_risk_cached(csv_path: str) -> str:
    """
    Compute annualized volatility, max drawdown, and 1-day 95% VaR from OHLCV CSV data.
    Returns JSON with risk metrics and number of observations, plus conservative risk plan.
    """
    try:
        df = read_prices(csv_path)
        result = compute_risk_metrics(df)
        return json.dumps(result)
    except Exception as e:
        print(f"❌ Error computing risk metrics: {e}")
        return json.dumps({'error': str(e)})


@tool("Rule-based technical signal")
def rule_based_signal_cached(csv_path: str) -> str:
    """
    Generate a BUY/SELL/HOLD signal using simple rules on EMA, MACD, RSI, and Bollinger Bands.
    Returns JSON with signal, score, reasons, and indicator snapshot.
    """
    try:
        df = read_prices(csv_path)
        result = generate_rule_based_signal(df)
        return json.dumps(result)
    except Exception as e:
        print(f"❌ Error generating signal: {e}")
        return json.dumps({'error': str(e)})


@tool("Plot price & indicators")
def plot_price_indicators_cached(csv_path: str) -> str:
    """
    Plot closing price with EMA20/50 and Bollinger Bands, saving to PNG.
    Returns the absolute file path of the generated chart.
    """
    try:
        chart_path = plot_price_and_indicators(csv_path)
        return chart_path
    except Exception as e:
        print(f"❌ Error creating chart: {e}")
        return f"Error creating chart: {e}"


def setup_cache_for_backtest(ticker: str, csv_path: str, period: str, interval: str, 
                            start_date: str, end_date: str):
    """
    Set up cached data for backtesting.
    This should be called once before running the backtest.
    """
    # Set up CSV cache
    _data_cache.set_csv_data(ticker, csv_path, period, interval)
    
    # Fetch and cache historical news (1 API call)
    print(f"🗞️  Fetching historical news for {ticker}...")
    _data_cache.fetch_and_cache_historical_news(ticker, start_date, end_date)
    
    print(f"✅ Cache setup complete for {ticker}")


def get_cached_tools():
    """Return list of cached tools for crew configuration."""
    return [
        fetch_ohlcv_cached,
        fetch_news_cached,
        compute_indicators_cached,
        compute_risk_cached,
        rule_based_signal_cached,
        plot_price_indicators_cached
    ]