"""
Backtesting script for AI Financial Advisor strategy.
Tests MSTR weekly for the past year with portfolio tracking.
"""
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import tempfile
from dotenv import load_dotenv

from src.data.polygon_client import PolygonClient
from src.agents.cached_crew_setup import create_cached_financial_advisor_crew
from src.agents.cached_tools import setup_cache_for_backtest

class StrategyBacktester:
    def __init__(self, initial_capital: float = 10000):
        """Initialize backtester with starting capital."""
        self.initial_capital = initial_capital
        self.portfolio = {
            'cash': initial_capital,
            'shares': 0,
            'total_value': initial_capital
        }
        self.trades = []
        self.performance_history = []
        self.data_cache = {}
        
        # Load environment and setup clients
        load_dotenv()
        self.polygon_client = PolygonClient()
        self.crew = None  # Will be created with cache setup
        
    def cache_historical_data(self, ticker: str, start_date: str, end_date: str) -> str:
        """
        Fetch and cache historical data for the entire backtest period.
        This minimizes API calls by getting all data at once.
        """
        cache_key = f"{ticker}_{start_date}_{end_date}"
        
        if cache_key in self.data_cache:
            print(f"📦 Using cached data for {ticker} ({start_date} to {end_date})")
            return self.data_cache[cache_key]
        
        print(f"📡 Fetching historical data for {ticker} from {start_date} to {end_date}")
        print("⚠️  This will use 1 API call to get all historical data...")
        
        try:
            # Fetch all historical data at once - use 5y to ensure we have enough data
            result = self.polygon_client.fetch_ohlcv(ticker, '5y', '1d')  # Get 5 years to be extra safe
            csv_path = result['csv_path']
            
            # Load and filter the data to our date range
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            # Save filtered data to new cache file
            cache_dir = tempfile.gettempdir()
            cache_file = os.path.join(cache_dir, f"backtest_cache_{cache_key}.csv")
            df.to_csv(cache_file)
            
            self.data_cache[cache_key] = cache_file
            print(f"✅ Cached {len(df)} days of data")
            return cache_file
            
        except Exception as e:
            print(f"❌ Error caching data: {e}")
            raise
    
    def get_data_for_date(self, ticker: str, target_date: datetime, period_days: int = 180) -> str:
        """
        Extract data subset for a specific analysis date from cached data.
        This simulates what data would have been available on that date.
        """
        cache_key = f"{ticker}_full_history"
        cached_file = self.data_cache.get(cache_key)
        
        if not cached_file or not os.path.exists(cached_file):
            raise ValueError("Historical data not cached. Run cache_historical_data first.")
        
        # Load cached data
        df = pd.read_csv(cached_file, index_col=0, parse_dates=True)
        
        # Filter to data that would have been available on target_date
        # (i.e., only historical data up to that point)
        available_data = df[df.index < target_date]
        
        # Ensure we have enough data for analysis
        min_required_days = 50  # Minimum for technical indicators
        if len(available_data) < min_required_days:
            raise ValueError(f"Insufficient data for {target_date}: only {len(available_data)} days available, need at least {min_required_days}")
        
        # Take the last period_days of available data (more data = better analysis)
        if len(available_data) > period_days:
            available_data = available_data.tail(period_days)
        
        print(f"📊 Analysis data for {target_date.strftime('%Y-%m-%d')}: {len(available_data)} days ({available_data.index[0].strftime('%Y-%m-%d')} to {available_data.index[-1].strftime('%Y-%m-%d')})")
        
        # Save to temporary file for the crew to analyze
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"backtest_{ticker}_{target_date.strftime('%Y%m%d')}.csv")
        available_data.to_csv(temp_file)
        
        return temp_file
    
    def run_strategy_analysis(self, ticker: str, analysis_date: datetime) -> Dict[str, Any]:
        """
        Run the AI Financial Advisor crew analysis for a specific date.
        This simulates running the strategy on historical data using cached tools.
        """
        print(f"🤖 Running AI analysis for {ticker} on {analysis_date.strftime('%Y-%m-%d')}")
        
        try:
            # Get historical data available up to analysis_date
            data_file = self.get_data_for_date(ticker, analysis_date)
            
            # Create cached crew for this date
            target_date_str = analysis_date.strftime('%Y-%m-%d')
            cached_crew = create_cached_financial_advisor_crew(target_date=target_date_str)
            
            # Set up cache with the specific data file for this date
            from src.agents.cached_tools import _data_cache
            _data_cache.set_csv_data(ticker, data_file, '6mo', '1d')
            
            # Run the crew analysis with cached data (NO API CALLS)
            result = cached_crew.kickoff(inputs={
                'ticker': ticker,
                'period': '6mo',
                'interval': '1d',
            })
            
            # Parse the crew result - handle CrewOutput object
            try:
                # CrewAI returns a CrewOutput object, extract the actual result
                if hasattr(result, 'raw'):  # CrewOutput has a 'raw' attribute
                    result_content = result.raw
                elif hasattr(result, 'result'):  # Or sometimes 'result'
                    result_content = result.result
                else:
                    result_content = str(result)  # Fallback to string conversion
                
                # Try to parse as JSON first
                if isinstance(result_content, str):
                    try:
                        recommendation = json.loads(result_content)
                    except json.JSONDecodeError:
                        # If not JSON, extract action from text
                        result_str = result_content.upper()
                        if 'BUY' in result_str:
                            recommendation = {'action': 'BUY', 'confidence': 0.5}
                        elif 'SELL' in result_str:
                            recommendation = {'action': 'SELL', 'confidence': 0.5}
                        else:
                            recommendation = {'action': 'HOLD', 'confidence': 0.5}
                elif isinstance(result_content, dict):
                    recommendation = result_content
                else:
                    # Last resort - parse from string representation
                    result_str = str(result_content).upper()
                    if 'BUY' in result_str:
                        recommendation = {'action': 'BUY', 'confidence': 0.5}
                    elif 'SELL' in result_str:
                        recommendation = {'action': 'SELL', 'confidence': 0.5}
                    else:
                        recommendation = {'action': 'HOLD', 'confidence': 0.5}
                
                print(f"📋 Parsed recommendation: {recommendation}")
                return recommendation
                
            except Exception as e:
                print(f"⚠️  Error parsing crew result: {e}")
                print(f"🔍 Result type: {type(result)}")
                print(f"🔍 Result content: {result}")
                # Default fallback
                return {'action': 'HOLD', 'confidence': 0.0, 'error': str(e)}
            
        except Exception as e:
            print(f"⚠️  Error in strategy analysis: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'error': str(e)}
    
    def execute_trade(self, action: str, price: float, date: datetime, confidence: float = 1.0):
        """Execute a trade based on strategy recommendation."""
        if action == 'BUY' and self.portfolio['cash'] > 0:
            # Buy as many shares as possible with available cash
            shares_to_buy = int(self.portfolio['cash'] / price)
            if shares_to_buy > 0:
                cost = shares_to_buy * price
                self.portfolio['cash'] -= cost
                self.portfolio['shares'] += shares_to_buy
                
                trade = {
                    'date': date,
                    'action': 'BUY',
                    'shares': shares_to_buy,
                    'price': price,
                    'value': cost,
                    'confidence': confidence
                }
                self.trades.append(trade)
                print(f"📈 BUY: {shares_to_buy} shares at ${price:.2f} (Total: ${cost:.2f})")
        
        elif action == 'SELL' and self.portfolio['shares'] > 0:
            # Sell all shares
            shares_to_sell = self.portfolio['shares']
            proceeds = shares_to_sell * price
            self.portfolio['cash'] += proceeds
            self.portfolio['shares'] = 0
            
            trade = {
                'date': date,
                'action': 'SELL',
                'shares': shares_to_sell,
                'price': price,
                'value': proceeds,
                'confidence': confidence
            }
            self.trades.append(trade)
            print(f"📉 SELL: {shares_to_sell} shares at ${price:.2f} (Total: ${proceeds:.2f})")
        
        # Update total portfolio value
        self.portfolio['total_value'] = self.portfolio['cash'] + (self.portfolio['shares'] * price)
    
    def run_backtest(self, ticker: str = 'MSTR', weeks: int = 52) -> Dict[str, Any]:
        """
        Run the complete backtest simulation.
        Tests strategy weekly for the specified number of weeks.
        """
        print(f"🚀 Starting backtest for {ticker} over {weeks} weeks")
        print(f"💰 Initial capital: ${self.initial_capital:,.2f}")
        
        # Calculate backtest date range (go back 'weeks' weeks from today)
        backtest_end_date = datetime.now()
        backtest_start_date = backtest_end_date - timedelta(weeks=weeks)
        
        # Calculate data fetch range (need extra data for AI analysis)
        # Agents need ~6 months of historical data to analyze at each point
        data_buffer_weeks = 26  # 6 months buffer
        data_start_date = backtest_start_date - timedelta(weeks=data_buffer_weeks)
        
        print(f"📅 Backtest period: {backtest_start_date.strftime('%Y-%m-%d')} to {backtest_end_date.strftime('%Y-%m-%d')}")
        print(f"📊 Data fetch period: {data_start_date.strftime('%Y-%m-%d')} to {backtest_end_date.strftime('%Y-%m-%d')} (includes {data_buffer_weeks} week buffer)")
        
        # Cache all historical data with buffer (1 API call for OHLCV + 1 for news = 2 total)
        cache_file = self.cache_historical_data(
            ticker, 
            data_start_date.strftime('%Y-%m-%d'), 
            backtest_end_date.strftime('%Y-%m-%d')
        )
        self.data_cache[f"{ticker}_full_history"] = cache_file
        
        # Set up cached tools with historical data (1 additional API call for news)
        print(f"📦 Setting up cached tools for backtesting...")
        setup_cache_for_backtest(
            ticker=ticker,
            csv_path=cache_file,
            period='1y',
            interval='1d',
            start_date=data_start_date.strftime('%Y-%m-%d'),
            end_date=backtest_end_date.strftime('%Y-%m-%d')
        )
        
        # Load price data for trade execution
        price_data = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        
        # Run weekly analysis
        current_date = backtest_start_date
        week_count = 0
        
        while current_date <= backtest_end_date and week_count < weeks:
            week_count += 1
            print(f"\n📊 Week {week_count}/{weeks} - {current_date.strftime('%Y-%m-%d')}")
            
            # Get the price for this date (or closest trading day)
            available_prices = price_data[price_data.index <= current_date]
            if available_prices.empty:
                current_date += timedelta(weeks=1)
                continue
                
            current_price = available_prices['Close'].iloc[-1]
            actual_date = available_prices.index[-1]
            
            # Run strategy analysis
            recommendation = self.run_strategy_analysis(ticker, current_date)
            
            # Safely extract action and confidence
            if isinstance(recommendation, dict):
                action = recommendation.get('action', 'HOLD')
                confidence = recommendation.get('confidence', 0.0)
            else:
                print(f"⚠️  Unexpected recommendation type: {type(recommendation)}")
                action = 'HOLD'
                confidence = 0.0
            
            # Execute trade
            self.execute_trade(action, current_price, actual_date, confidence)
            
            # Record performance
            portfolio_value = self.portfolio['cash'] + (self.portfolio['shares'] * current_price)
            self.performance_history.append({
                'date': actual_date,
                'price': current_price,
                'portfolio_value': portfolio_value,
                'cash': self.portfolio['cash'],
                'shares': self.portfolio['shares'],
                'action': action,
                'confidence': confidence
            })
            
            print(f"💼 Portfolio: ${portfolio_value:,.2f} | Cash: ${self.portfolio['cash']:.2f} | Shares: {self.portfolio['shares']}")
            
            # Move to next week
            current_date += timedelta(weeks=1)
        
        # Final performance calculation
        final_price = price_data['Close'].iloc[-1]
        final_portfolio_value = self.portfolio['cash'] + (self.portfolio['shares'] * final_price)
        total_return = ((final_portfolio_value - self.initial_capital) / self.initial_capital) * 100
        
        # Buy and hold comparison
        initial_shares = self.initial_capital / price_data['Close'].iloc[0]
        buy_hold_value = initial_shares * final_price
        buy_hold_return = ((buy_hold_value - self.initial_capital) / self.initial_capital) * 100
        
        results = {
            'initial_capital': self.initial_capital,
            'final_portfolio_value': final_portfolio_value,
            'total_return_pct': total_return,
            'total_trades': len(self.trades),
            'buy_hold_value': buy_hold_value,
            'buy_hold_return_pct': buy_hold_return,
            'strategy_vs_buy_hold': total_return - buy_hold_return,
            'weeks_tested': week_count,
            'trades': self.trades,
            'performance_history': self.performance_history
        }
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted backtest results."""
        print("\n" + "="*60)
        print("📊 BACKTEST RESULTS")
        print("="*60)
        print(f"Initial Capital:      ${results['initial_capital']:>12,.2f}")
        print(f"Final Portfolio:      ${results['final_portfolio_value']:>12,.2f}")
        print(f"Total Return:         {results['total_return_pct']:>12.2f}%")
        print(f"Total Trades:         {results['total_trades']:>12}")
        print(f"Weeks Tested:         {results['weeks_tested']:>12}")
        print()
        print("📈 BENCHMARK COMPARISON")
        print("-"*30)
        print(f"Buy & Hold Return:    {results['buy_hold_return_pct']:>12.2f}%")
        print(f"Strategy Return:      {results['total_return_pct']:>12.2f}%")
        print(f"Alpha (vs B&H):       {results['strategy_vs_buy_hold']:>12.2f}%")
        print()
        
        if results['strategy_vs_buy_hold'] > 0:
            print("🎉 Strategy OUTPERFORMED buy & hold!")
        else:
            print("📉 Strategy UNDERPERFORMED buy & hold")
        
        print("\n💼 FINAL PORTFOLIO")
        print("-"*20)
        print(f"Cash:                 ${self.portfolio['cash']:>12,.2f}")
        print(f"Shares:               {self.portfolio['shares']:>12}")
        print(f"Total Value:          ${self.portfolio['total_value']:>12,.2f}")


def main():
    """Run the backtest."""
    if not os.getenv('POLYGON_API_KEY'):
        print("❌ POLYGON_API_KEY not set. Please set it in your .env file.")
        return
    
    # Create backtester
    backtester = StrategyBacktester(initial_capital=10000)
    
    # Run backtest
    try:
        results = backtester.run_backtest(ticker='MSTR', weeks=52)
        backtester.print_results(results)
        
        # Save results
        results_file = 'backtest_results.json'
        with open(results_file, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            json_results = json.loads(json.dumps(results, default=str))
            json.dump(json_results, f, indent=2)
        print(f"\n📁 Results saved to {results_file}")
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        raise


if __name__ == '__main__':
    main()