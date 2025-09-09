"""
Polygon.io data fetching functionality.
"""
import os
import json
import requests
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class PolygonClient:
    """Client for fetching data from Polygon.io API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError('POLYGON_API_KEY not set')
        self.base_url = 'https://api.polygon.io'
    
    def _make_request(self, url: str, params: dict = None) -> dict:
        """Make API request with error handling."""
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        if data.get('status') == 'ERROR':
            raise RuntimeError(f"Polygon.io API error: {data.get('error', 'Unknown error')}")
        return data
    
    def _sanitize_ticker(self, ticker: str) -> str:
        """Sanitize ticker for filename use."""
        return (str(ticker)
                .replace('/', '-').replace('\\', '-')
                .replace(' ', '').replace(':', '-').replace('.', '-'))
    
    def _normalize_interval(self, interval: str) -> tuple:
        """Normalize interval string to Polygon format."""
        il = (interval or "").strip().lower()
        if il in {"1d", "d"}:
            return (1, "day")
        elif il in {"1wk", "wk", "w"}:
            return (1, "week")
        elif il in {"1mo", "mo", "m"}:
            return (1, "month")
        elif il.endswith("min"):
            x = il.replace("min", "")
            minutes = int(x) if x in {'1','5','15','30','60'} else 60
            return (minutes, "minute")
        elif il.endswith("h") or il.endswith("hour"):
            x = il.replace("h", "").replace("hour", "")
            hours = int(x) if x.isdigit() else 1
            return (hours, "hour")
        return (1, "day")
    
    def _parse_period_to_dates(self, period: str, interval: str = '1d') -> tuple:
        """Convert period to start and end dates with smart intraday logic."""
        now = datetime.now()
        
        # For intraday intervals (minutes/hours), include today for day trading
        is_intraday = any(x in interval.lower() for x in ['min', 'hour', 'h'])
        
        if is_intraday:
            # For day trading, always include today
            end_date = now.date()
            print(f"DEBUG - Intraday trading mode: including today ({end_date})")
        else:
            # For daily+ intervals, use yesterday to avoid incomplete daily bars
            # Unless it's weekend, then use Friday
            if now.weekday() == 5:  # Saturday
                end_date = now.date() - timedelta(days=1)  # Friday
            elif now.weekday() == 6:  # Sunday
                end_date = now.date() - timedelta(days=2)  # Friday
            else:
                # Weekday: if before market close (4 PM ET), use yesterday
                # if after market close, can use today
                market_close_today = now.replace(hour=16, minute=0, second=0, microsecond=0)
                if now < market_close_today:
                    end_date = now.date() - timedelta(days=1)
                else:
                    end_date = now.date()
            print(f"DEBUG - Daily+ interval mode: end date = {end_date}")
        
        period_map = {
            '1d': 7,    # Get a week to ensure trading days
            '1w': 14,   
            '1mo': 45,  
            '3mo': 100,
            '6mo': 200,
            '1y': 380,
            '2y': 750,
            '5y': 1850
        }
        
        days = period_map.get(period, 200)  # Default to ~6 months
        start_date = end_date - timedelta(days=days)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def _polygon_to_df(self, data: dict) -> pd.DataFrame:
        """Convert Polygon.io aggregates data to DataFrame."""
        # Debug: Print the full response to understand the structure
        print(f"DEBUG - Full Polygon response: {json.dumps(data, indent=2)}")
        
        results = data.get('results', [])
        if not results:
            # More detailed error with response info
            status = data.get('status', 'unknown')
            count = data.get('resultsCount', 0)
            error_msg = f"No results in Polygon response. Status: {status}, Count: {count}, Response keys: {list(data.keys())}"
            raise ValueError(error_msg)
        
        records = []
        for bar in results:
            # Convert timestamp from milliseconds to datetime
            timestamp = pd.to_datetime(bar['t'], unit='ms', utc=True)
            # Convert to Eastern time and remove timezone info
            timestamp = timestamp.tz_convert('America/New_York').tz_localize(None)
            
            records.append({
                'Date': timestamp,
                'Open': bar['o'],
                'High': bar['h'],
                'Low': bar['l'],
                'Close': bar['c'],
                'Volume': bar['v'],
                'Adj Close': bar['c']  # Polygon data is already adjusted
            })
        
        df = pd.DataFrame(records)
        df = df.set_index('Date').sort_index()
        
        # Ensure numeric types
        for col in ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return self._ensure_df(df)
    
    def _ensure_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate DataFrame has required columns."""
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError('Price DataFrame is empty. Check ticker/period/interval.')
        
        for needed in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
            if needed not in df.columns:
                raise ValueError(f'Missing column: {needed}')
        return df
    
    def fetch_ohlcv(self, ticker: str, period: str = '6mo', interval: str = '1d') -> Dict[str, Any]:
        """
        Fetch OHLCV data using Polygon.io and save to CSV.
        Supports intraday trading with current day data for minute/hour intervals.
        
        Returns:
            Dict with csv_path, metadata, and summary stats
        """
        multiplier, timespan = self._normalize_interval(interval)
        start_date, end_date = self._parse_period_to_dates(period, interval)
        
        df = self._fetch_aggregates(ticker, multiplier, timespan, start_date, end_date)
        
        df = df.dropna(subset=['Close'])
        if df.empty:
            raise RuntimeError(f"Fetched empty dataframe for {ticker} ({interval}, {period}).")
        
        safe_ticker = self._sanitize_ticker(ticker)
        tmp_dir = tempfile.gettempdir()
        csv_path = os.path.join(tmp_dir, f"{safe_ticker}_{period}_{interval}.csv")
        df.to_csv(csv_path, index=True)
        
        return {
            'csv_path': os.path.abspath(csv_path),
            'rows_count': int(df.shape[0]),
            'start': str(pd.to_datetime(df.index[0]).date()),
            'end': str(pd.to_datetime(df.index[-1]).date()),
            'last_close': float(df['Close'].iloc[-1]),
            'period': period,
            'interval': interval,
            'ticker': ticker,
            'sanitized_ticker': safe_ticker
        }
    
    def _fetch_aggregates(self, ticker: str, multiplier: int, timespan: str, from_date: str, to_date: str) -> pd.DataFrame:
        """Fetch aggregated OHLCV data from Polygon."""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        print(f"DEBUG - Request URL: {url}")
        print(f"DEBUG - Request params: {params}")
        print(f"DEBUG - Date range: {from_date} to {to_date}")
        print(f"DEBUG - Interval: {multiplier} {timespan}")
        
        data = self._make_request(url, params)
        return self._polygon_to_df(data)
    
    def fetch_news(self, ticker: str, limit: int = 10) -> list:
        """
        Fetch recent news for a ticker using Polygon.io.
        
        Returns:
            List of news articles with title, publisher, link, time
        """
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'ticker': ticker,
            'limit': min(1000, max(1, limit)),
            'sort': 'published_utc'
        }
        
        try:
            data = self._make_request(url, params)
        except Exception:
            return []
        
        results = data.get('results', []) or []
        items = []
        
        for n in results[:limit]:
            publisher = n.get('publisher', {}).get('name', '') or ''
            
            items.append({
                'title': n.get('title', ''),
                'publisher': publisher,
                'link': n.get('article_url', ''),
                'time': n.get('published_utc', '')
            })
        
        return items