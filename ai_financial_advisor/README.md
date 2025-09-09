# AI Financial Advisor

A modular financial analysis system using CrewAI agents to provide investment recommendations based on technical analysis and risk assessment.

## Features

- **Multi-Agent System**: Uses CrewAI with specialized agents for data collection, technical analysis, risk management, and portfolio decisions
- **Polygon.io Integration**: Fetches real-time market data and news
- **Technical Analysis**: EMA, MACD, RSI, Bollinger Bands with crossover detection
- **Risk Management**: Volatility, drawdown, VaR calculations with conservative position sizing
- **Automated Signals**: Rule-based BUY/SELL/HOLD recommendations
- **Visualization**: Price charts with technical indicators

## Project Structure

```
ai_financial_advisor/
├── src/
│   ├── data/
│   │   └── polygon_client.py     # Polygon.io API client
│   ├── analysis/
│   │   ├── indicators.py         # Technical indicators
│   │   ├── risk.py              # Risk metrics
│   │   ├── signals.py           # Trading signals
│   │   └── plotting.py          # Chart generation
│   ├── agents/
│   │   ├── tools.py             # CrewAI tools
│   │   ├── crew_agents.py       # Agent definitions
│   │   ├── crew_tasks.py        # Task definitions
│   │   └── crew_setup.py        # Crew configuration
│   └── utils/
│       └── data_utils.py        # Data utilities
├── main.py                      # Main execution script
├── requirements.txt             # Dependencies
└── .env.example                # Environment variables template
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Add your Polygon.io API key
   - Add your OpenAI API key

3. **Run the analysis**:
   ```bash
   python main.py
   ```

## Configuration

Edit `main.py` to change:
- `TICKER`: Stock symbol to analyze (default: 'MSTR')
- `PERIOD`: Historical data period (default: '1d')
- `INTERVAL`: Data interval (default: '5min')

## Agents

1. **Market Data Analyst**: Fetches OHLCV data and news
2. **Technical Strategist**: Computes indicators and generates signals
3. **Risk Manager**: Calculates risk metrics and position sizing
4. **Portfolio Manager**: Makes final BUY/SELL/HOLD decisions

## Output

The system provides a JSON recommendation with:
- Action (BUY/SELL/HOLD)
- Confidence level (0-1)
- Supporting reasons
- Key technical signals
- Risk management parameters (stop loss, take profit, position size)