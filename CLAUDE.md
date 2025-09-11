# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI agent project focused on building a financial advisor system that provides stock analysis and investment recommendations. The main component is an AI Financial Advisor using CrewAI with specialized agents for market data collection, technical analysis, risk assessment, and portfolio management.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (if not exists)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies for main financial advisor
cd ai_financial_advisor
pip install -r requirements.txt
```

### Running the Financial Advisor
```bash
# From ai_financial_advisor/ directory
python main.py

# Run backtesting strategy
python backtest_strategy.py

# Analyze backtest results
python analyze_backtest.py
```

### Testing
```bash
# From ai_financial_advisor/ directory
python test_polygon.py          # Test Polygon.io API connection
python test_cached_tools.py     # Test cached tools functionality
python test_crew_output.py      # Test crew output parsing
```

## Architecture

### Main Components

1. **ai_financial_advisor/** - Core financial analysis system
   - Multi-agent CrewAI system with specialized roles:
     - Market Data Analyst: Fetches OHLCV data and news via Polygon.io
     - Technical Strategist: Computes indicators (EMA, MACD, RSI, Bollinger Bands)
     - Risk Manager: Calculates volatility, VaR, drawdown metrics
     - Portfolio Manager: Makes final BUY/SELL/HOLD decisions
   
2. **code/** - Contains experimental Jupyter notebooks and CSV data files

3. **resume_tailor/** - Empty directory for future resume tailoring functionality

### Key Architecture Patterns

- **CrewAI Framework**: Uses sequential agent processing with task dependencies
- **Polygon.io Integration**: Real-time market data fetching with API key authentication
- **Caching System**: Optimized for backtesting to minimize API calls (`cached_crew_setup.py`, `cached_tools.py`)
- **Modular Structure**: Separated concerns across `data/`, `analysis/`, `agents/`, `utils/` directories

### Configuration

Environment variables required in `.env`:
- `OPENAI_API_KEY`: For CrewAI agent LLM calls
- `OPENAI_MODEL_NAME`: Default is `gpt-4o-mini`
- `POLYGON_API_KEY`: For market data fetching
- `ALPHAVANTAGE_API_KEY`: Alternative data source

### Data Flow

1. Market Data Analyst fetches historical OHLCV data and news
2. Technical Strategist calculates technical indicators and generates signals
3. Risk Manager computes risk metrics and position sizing recommendations
4. Portfolio Manager makes final decision based on all inputs
5. System outputs JSON recommendation with action, confidence, reasons, and risk parameters

### Entry Points

- `ai_financial_advisor/main.py`: Main analysis for single ticker
- `ai_financial_advisor/backtest_strategy.py`: Historical backtesting with portfolio tracking
- `ai_financial_advisor/analyze_backtest.py`: Performance analysis of backtest results

The system is designed for stock analysis with configurable ticker symbols, time periods, and intervals.