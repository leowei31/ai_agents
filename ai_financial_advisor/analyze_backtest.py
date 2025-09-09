"""
Analysis and visualization script for backtest results.
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

def load_backtest_results(filename: str = 'backtest_results.json') -> dict:
    """Load backtest results from JSON file."""
    try:
        with open(filename, 'r') as f:
            results = json.load(f)
        print(f"✅ Loaded backtest results from {filename}")
        return results
    except FileNotFoundError:
        print(f"❌ Results file {filename} not found. Run backtest_strategy.py first.")
        return None
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return None

def calculate_advanced_metrics(results: dict) -> dict:
    """Calculate additional performance metrics."""
    if not results or 'performance_history' not in results:
        return {}
    
    # Convert performance history to DataFrame
    df = pd.DataFrame(results['performance_history'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    
    # Calculate returns
    df['returns'] = df['portfolio_value'].pct_change().fillna(0)
    
    # Performance metrics
    total_return = results['total_return_pct'] / 100
    num_weeks = len(df)
    
    # Annualized return (assuming 52 weeks per year)
    annualized_return = ((1 + total_return) ** (52 / num_weeks)) - 1
    
    # Volatility (annualized)
    volatility = df['returns'].std() * np.sqrt(52)
    
    # Sharpe ratio (assuming 0% risk-free rate)
    sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
    
    # Maximum drawdown
    df['peak'] = df['portfolio_value'].cummax()
    df['drawdown'] = (df['portfolio_value'] - df['peak']) / df['peak']
    max_drawdown = df['drawdown'].min()
    
    # Win rate
    trades = results.get('trades', [])
    if len(trades) >= 2:
        # Calculate P&L for each trade pair (buy -> sell)
        trade_pnl = []
        buy_price = None
        for trade in trades:
            if trade['action'] == 'BUY':
                buy_price = trade['price']
            elif trade['action'] == 'SELL' and buy_price:
                pnl = (trade['price'] - buy_price) / buy_price
                trade_pnl.append(pnl)
                buy_price = None
        
        if trade_pnl:
            win_rate = len([p for p in trade_pnl if p > 0]) / len(trade_pnl)
            avg_win = np.mean([p for p in trade_pnl if p > 0]) if any(p > 0 for p in trade_pnl) else 0
            avg_loss = np.mean([p for p in trade_pnl if p < 0]) if any(p < 0 for p in trade_pnl) else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
    
    metrics = {
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'total_trades': len(trades),
        'performance_df': df
    }
    
    return metrics

def create_performance_chart(results: dict, save_path: str = 'backtest_performance.png'):
    """Create performance visualization chart."""
    if not results or 'performance_history' not in results:
        print("❌ No performance data to chart")
        return
    
    # Prepare data
    df = pd.DataFrame(results['performance_history'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    
    # Calculate buy & hold performance
    initial_value = results['initial_capital']
    initial_price = df['price'].iloc[0]
    shares = initial_value / initial_price
    df['buy_hold_value'] = shares * df['price']
    
    # Create the plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
    
    # Plot 1: Portfolio Value vs Buy & Hold
    ax1.plot(df.index, df['portfolio_value'], label='AI Strategy', linewidth=2, color='blue')
    ax1.plot(df.index, df['buy_hold_value'], label='Buy & Hold', linewidth=2, color='orange')
    ax1.axhline(y=initial_value, color='gray', linestyle='--', alpha=0.7, label='Initial Capital')
    ax1.set_title('Portfolio Performance: AI Strategy vs Buy & Hold', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Stock Price with Trade Signals
    ax2.plot(df.index, df['price'], label='MSTR Price', linewidth=1, color='black')
    
    # Mark buy/sell signals
    buy_signals = df[df['action'] == 'BUY']
    sell_signals = df[df['action'] == 'SELL']
    
    ax2.scatter(buy_signals.index, buy_signals['price'], 
               color='green', marker='^', s=100, label='BUY', zorder=5)
    ax2.scatter(sell_signals.index, sell_signals['price'], 
               color='red', marker='v', s=100, label='SELL', zorder=5)
    
    ax2.set_title('MSTR Price with Trade Signals', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Price ($)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Drawdown
    df['peak'] = df['portfolio_value'].cummax()
    df['drawdown'] = (df['portfolio_value'] - df['peak']) / df['peak'] * 100
    
    ax3.fill_between(df.index, df['drawdown'], 0, alpha=0.3, color='red')
    ax3.plot(df.index, df['drawdown'], color='red', linewidth=1)
    ax3.set_title('Portfolio Drawdown', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Drawdown (%)')
    ax3.set_xlabel('Date')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"📊 Performance chart saved to {save_path}")

def print_detailed_analysis(results: dict, metrics: dict):
    """Print detailed analysis of backtest results."""
    print("\n" + "="*70)
    print("📈 DETAILED PERFORMANCE ANALYSIS")
    print("="*70)
    
    # Basic Results
    print(f"Initial Capital:           ${results['initial_capital']:>15,.2f}")
    print(f"Final Portfolio Value:     ${results['final_portfolio_value']:>15,.2f}")
    print(f"Total Return:              {results['total_return_pct']:>15.2f}%")
    print(f"Buy & Hold Return:         {results['buy_hold_return_pct']:>15.2f}%")
    print(f"Alpha (Strategy vs B&H):   {results['strategy_vs_buy_hold']:>15.2f}%")
    
    print(f"\n📊 RISK-ADJUSTED METRICS")
    print("-"*30)
    print(f"Annualized Return:         {metrics['annualized_return']*100:>15.2f}%")
    print(f"Annualized Volatility:     {metrics['volatility']*100:>15.2f}%")
    print(f"Sharpe Ratio:              {metrics['sharpe_ratio']:>15.2f}")
    print(f"Maximum Drawdown:          {metrics['max_drawdown']*100:>15.2f}%")
    
    print(f"\n🎯 TRADE ANALYSIS")
    print("-"*20)
    print(f"Total Trades:              {metrics['total_trades']:>15}")
    print(f"Win Rate:                  {metrics['win_rate']*100:>15.1f}%")
    print(f"Average Win:               {metrics['avg_win']*100:>15.2f}%")
    print(f"Average Loss:              {metrics['avg_loss']*100:>15.2f}%")
    
    # Trade details
    if results.get('trades'):
        print(f"\n📋 TRADE HISTORY")
        print("-"*50)
        for i, trade in enumerate(results['trades'], 1):
            date = trade['date'][:10]  # Just the date part
            action = trade['action']
            shares = trade['shares']
            price = trade['price']
            confidence = trade.get('confidence', 0)
            print(f"{i:2d}. {date} | {action:4s} | {shares:4d} shares @ ${price:8.2f} | Conf: {confidence:.2f}")

def main():
    """Main analysis function."""
    print("📊 Loading and analyzing backtest results...")
    
    # Load results
    results = load_backtest_results()
    if not results:
        return
    
    # Calculate advanced metrics
    print("🔍 Calculating advanced metrics...")
    metrics = calculate_advanced_metrics(results)
    
    # Print detailed analysis
    print_detailed_analysis(results, metrics)
    
    # Create performance chart
    print("\n📈 Creating performance charts...")
    create_performance_chart(results)
    
    # Performance summary
    total_return = results['total_return_pct']
    buy_hold_return = results['buy_hold_return_pct']
    alpha = results['strategy_vs_buy_hold']
    
    print(f"\n🎯 SUMMARY")
    print("="*40)
    if alpha > 0:
        print(f"🎉 The AI strategy OUTPERFORMED buy & hold by {alpha:.2f}%!")
        print(f"💰 Strategy generated {total_return:.2f}% vs {buy_hold_return:.2f}% for buy & hold")
    else:
        print(f"📉 The AI strategy UNDERPERFORMED buy & hold by {abs(alpha):.2f}%")
        print(f"💸 Strategy generated {total_return:.2f}% vs {buy_hold_return:.2f}% for buy & hold")
    
    print(f"\n🏆 Risk-adjusted performance (Sharpe): {metrics['sharpe_ratio']:.3f}")
    print(f"⚠️  Maximum drawdown: {metrics['max_drawdown']*100:.2f}%")
    print(f"🎯 Win rate: {metrics['win_rate']*100:.1f}%")

if __name__ == '__main__':
    main()