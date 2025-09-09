"""
Simple test script for Polygon.io integration.
Run this to test the API connection with minimal calls.
"""
import os
from dotenv import load_dotenv
from src.data.polygon_client import PolygonClient

def test_polygon_client():
    """Test the Polygon client with a simple request."""
    load_dotenv()
    
    if not os.getenv('POLYGON_API_KEY'):
        print("❌ POLYGON_API_KEY not set in environment")
        return
    
    print("🧪 Testing Polygon.io client...")
    
    try:
        client = PolygonClient()
        print("✅ Client initialized successfully")
        
        # Test with intraday data for day trading
        print("\n📊 Testing INTRADAY fetch for AAPL, 1 day 5min data (for day trading)...")
        result = client.fetch_ohlcv('AAPL', '1d', '5min')
        
        print(f"✅ Success! Got {result['rows_count']} rows")
        print(f"📅 Date range: {result['start']} to {result['end']}")
        print(f"💰 Last close: ${result['last_close']:.2f}")
        print(f"📁 CSV saved to: {result['csv_path']}")
        
        print("\n📊 Testing DAILY fetch for AAPL, 1 week daily data...")
        result2 = client.fetch_ohlcv('AAPL', '1w', '1d')
        
        print(f"✅ Success! Got {result2['rows_count']} rows")
        print(f"📅 Date range: {result2['start']} to {result2['end']}")
        print(f"💰 Last close: ${result2['last_close']:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"🔍 Error type: {type(e).__name__}")

if __name__ == '__main__':
    test_polygon_client()