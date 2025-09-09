"""
Test script to debug CrewOutput object handling.
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.data.polygon_client import PolygonClient
from src.agents.cached_tools import setup_cache_for_backtest
from src.agents.cached_crew_setup import create_cached_financial_advisor_crew

def test_crew_output():
    """Test how CrewAI returns results."""
    load_dotenv()
    
    if not os.getenv('POLYGON_API_KEY'):
        print("❌ POLYGON_API_KEY not set")
        return
    
    print("🧪 Testing CrewOutput handling...")
    
    try:
        # Step 1: Set up minimal cache
        client = PolygonClient()
        ticker = 'AAPL'
        
        print("📊 Fetching minimal data for test...")
        result = client.fetch_ohlcv(ticker, '3mo', '1d')
        csv_path = result['csv_path']
        
        # Set up cache
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        setup_cache_for_backtest(
            ticker=ticker,
            csv_path=csv_path,
            period='3mo',
            interval='1d',
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Step 2: Test crew execution
        print("🤖 Creating and running cached crew...")
        target_date = (end_date - timedelta(days=7)).strftime('%Y-%m-%d')
        cached_crew = create_cached_financial_advisor_crew(target_date=target_date)
        
        print(f"🚀 Running crew for {ticker}...")
        result = cached_crew.kickoff(inputs={
            'ticker': ticker,
            'period': '3mo',
            'interval': '1d',
        })
        
        # Step 3: Debug the result
        print(f"\n🔍 DEBUGGING CREW RESULT:")
        print(f"Result type: {type(result)}")
        print(f"Result attributes: {dir(result)}")
        
        # Try different ways to extract content
        if hasattr(result, 'raw'):
            print(f"result.raw: {result.raw}")
        if hasattr(result, 'result'):
            print(f"result.result: {result.result}")
        if hasattr(result, 'output'):
            print(f"result.output: {result.output}")
        if hasattr(result, 'content'):
            print(f"result.content: {result.content}")
        
        print(f"String representation: {str(result)}")
        
        # Test our parsing logic
        print(f"\n🧪 Testing parsing logic...")
        
        # Extract content using our logic
        if hasattr(result, 'raw'):
            result_content = result.raw
        elif hasattr(result, 'result'):
            result_content = result.result
        else:
            result_content = str(result)
        
        print(f"Extracted content: {result_content}")
        print(f"Content type: {type(result_content)}")
        
        # Try to parse action
        if isinstance(result_content, str):
            result_str = result_content.upper()
            if 'BUY' in result_str:
                action = 'BUY'
            elif 'SELL' in result_str:
                action = 'SELL'
            else:
                action = 'HOLD'
        else:
            action = 'HOLD'
        
        print(f"✅ Extracted action: {action}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_crew_output()