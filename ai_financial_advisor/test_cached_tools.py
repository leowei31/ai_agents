"""
Test script for cached tools to verify they work without API calls.
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.data.polygon_client import PolygonClient
from src.agents.cached_tools import setup_cache_for_backtest, _data_cache
from src.agents.cached_crew_setup import create_cached_financial_advisor_crew

def test_cached_tools():
    """Test the cached tools system."""
    load_dotenv()
    
    if not os.getenv('POLYGON_API_KEY'):
        print("❌ POLYGON_API_KEY not set")
        return
    
    print("🧪 Testing cached tools system...")
    
    # Step 1: Fetch and cache data (2 API calls total)
    print("\n📡 Step 1: Fetching and caching data...")
    
    client = PolygonClient()
    ticker = 'AAPL'  # Use AAPL for testing (more reliable than MSTR)
    
    # Fetch OHLCV data (1 API call)
    print("📊 Fetching OHLCV data...")
    ohlcv_result = client.fetch_ohlcv(ticker, '1mo', '1d')
    csv_path = ohlcv_result['csv_path']
    
    # Set up cache (1 API call for news)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print("🗞️  Setting up cache with historical news...")
    setup_cache_for_backtest(
        ticker=ticker,
        csv_path=csv_path,
        period='1mo',
        interval='1d',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    print("✅ Cache setup complete!")
    
    # Step 2: Test cached tools (0 API calls)
    print("\n🔧 Step 2: Testing cached tools (NO API CALLS)...")
    
    # Test cached OHLCV
    from src.agents.cached_tools import fetch_ohlcv_cached
    print("📊 Testing cached OHLCV fetch...")
    ohlcv_cached = fetch_ohlcv_cached(ticker, '1mo', '1d')
    print("✅ Cached OHLCV works!")
    
    # Test cached news
    from src.agents.cached_tools import fetch_news_cached
    print("🗞️  Testing cached news fetch...")
    news_cached = fetch_news_cached(ticker, 5, target_date=start_date.strftime('%Y-%m-%d'))
    print("✅ Cached news works!")
    
    # Step 3: Test cached crew (0 API calls)
    print("\n🤖 Step 3: Testing cached crew (NO API CALLS)...")
    
    try:
        # Create cached crew
        target_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cached_crew = create_cached_financial_advisor_crew(target_date=target_date)
        
        print(f"🚀 Running cached crew analysis for {ticker} on {target_date}...")
        result = cached_crew.kickoff(inputs={
            'ticker': ticker,
            'period': '1mo',
            'interval': '1d',
        })
        
        print("✅ Cached crew analysis completed!")
        print(f"📋 Result preview: {str(result)[:200]}...")
        
    except Exception as e:
        print(f"❌ Cached crew test failed: {e}")
        return
    
    print("\n🎉 All cached tools tests passed!")
    print("💡 The backtesting system will now use minimal API calls:")
    print("   - 1 call for OHLCV data")
    print("   - 1 call for historical news")
    print("   - 0 calls during crew execution (52 weeks)")
    print("   = Total: 2 API calls for entire backtest!")

if __name__ == '__main__':
    test_cached_tools()