"""
Polygon.io data fetching functionality.
"""
import os
import json
import requests
import pandas as pd
import tempfile
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv
from functools import wraps

load_dotenv()


def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=30.0):
    """
    Decorator to retry API calls with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, requests.exceptions.Timeout, 
                        requests.exceptions.ConnectionError, RuntimeError) as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0.1, 0.3) * delay
                    total_delay = delay + jitter
                    
                    print(f"⚠️  API request failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    print(f"🔄 Retrying in {total_delay:.1f} seconds...")
                    time.sleep(total_delay)
            
            # If we get here, all retries failed
            print(f"❌ All retry attempts failed. Last error: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator


class PolygonClient:
    """Client for fetching data from Polygon.io API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError('POLYGON_API_KEY not set')
        self.base_url = 'https://api.polygon.io'
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests for rate limiting
    
    def _make_request(self, url: str, params: dict = None) -> dict:
        """Make API request with error handling and rate limiting."""
        # Rate limiting: ensure minimum interval between requests
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        try:
            r = requests.get(url, params=params, timeout=30)
            self._last_request_time = time.time()
            r.raise_for_status()
            data = r.json()
            
            # Check for various error conditions
            if data.get('status') == 'ERROR':
                error_msg = data.get('error', 'Unknown error')
                raise RuntimeError(f"Polygon.io API error: {error_msg}")
            
            # Check for rate limit indicators
            if data.get('status') == 'NOT_AUTHORIZED':
                raise RuntimeError(f"Polygon.io authentication error: Check API key")
            
            # Check for quota exceeded
            if 'rate limit' in str(data).lower() or 'quota' in str(data).lower():
                raise RuntimeError(f"Polygon.io rate limit exceeded")
            
            return data
            
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timeout after 30 seconds: {url}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RuntimeError(f"Rate limit exceeded (HTTP 429)")
            elif e.response.status_code == 401:
                raise RuntimeError(f"Unauthorized (HTTP 401): Check API key")
            elif e.response.status_code == 403:
                raise RuntimeError(f"Forbidden (HTTP 403): API quota exceeded or invalid permissions")
            else:
                raise RuntimeError(f"HTTP error {e.response.status_code}: {e}")
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response from API")
    
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
    
    @retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0)
    def fetch_news(self, ticker: str, limit: int = 10) -> list:
        """
        Fetch recent news for a ticker using Polygon.io with retry logic.
        
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
            
            # Validate response structure
            if not isinstance(data, dict):
                print(f"⚠️  Invalid response format for news API: {type(data)}")
                return []
            
            results = data.get('results', [])
            if results is None:
                print(f"⚠️  No results field in news API response")
                return []
            
            if not isinstance(results, list):
                print(f"⚠️  Results field is not a list: {type(results)}")
                return []
            
            items = []
            for n in results[:limit]:
                if not isinstance(n, dict):
                    print(f"⚠️  Skipping invalid news item: {type(n)}")
                    continue
                
                # Safely extract publisher name
                publisher_data = n.get('publisher', {})
                if isinstance(publisher_data, dict):
                    publisher = publisher_data.get('name', '') or ''
                else:
                    publisher = ''
                
                # Validate required fields exist
                title = n.get('title', '') or ''
                link = n.get('article_url', '') or ''
                time = n.get('published_utc', '') or ''
                
                # Only add if we have at least title and link
                if title and link:
                    items.append({
                        'title': title,
                        'publisher': publisher,
                        'link': link,
                        'time': time
                    })
            
            print(f"✅ Successfully fetched {len(items)} news articles for {ticker}")
            return items
            
        except Exception as e:
            print(f"❌ Failed to fetch news for {ticker}: {e}")
            # Re-raise the exception to trigger retry logic
            raise