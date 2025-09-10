"""
Cached crew setup that uses pre-fetched data instead of making API calls.
Perfect for backtesting and avoiding rate limits.
"""
from crewai import Agent, Task, Crew, Process
from .cached_tools import (
    fetch_ohlcv_cached, fetch_news_cached, compute_indicators_cached,
    compute_risk_cached, rule_based_signal_cached, plot_price_indicators_cached
)


def create_cached_market_data_analyst() -> Agent:
    """Create the Market Data Analyst agent with cached tools."""
    return Agent(
        role="Market Data Analyst",
        goal="Gather and validate OHLCV & headlines for {ticker}. Summarize trend and anomalies.",
        backstory="Meticulous about data quality, you verify timeframes and note gaps/splits. You work with cached historical data.",
        tools=[fetch_ohlcv_cached, fetch_news_cached],
        allow_delegation=False,
        verbose=True,
    )


def create_cached_technical_strategist() -> Agent:
    """Create the Technical Strategist agent with cached tools."""
    return Agent(
        role="Technical Strategist",
        goal="Transform price data into signals using EMA/RSI/MACD/Bollinger and explain rationale.",
        backstory="Disciplined technician balancing momentum and mean-reversion; you state both sides. You analyze historical data efficiently.",
        tools=[compute_indicators_cached, rule_based_signal_cached, plot_price_indicators_cached],
        allow_delegation=False,
        verbose=True,
    )


def create_cached_risk_manager() -> Agent:
    """Create the Risk Manager agent with cached tools."""
    return Agent(
        role="Risk Manager",
        goal="Quantify risk (vol, drawdown, VaR) and propose a conservative risk plan.",
        backstory="Capital preservation first; you recommend sensible stops, targets, and sizing. You work with historical data to assess risk.",
        tools=[compute_risk_cached],
        allow_delegation=False,
        verbose=True,
    )


def create_cached_portfolio_manager() -> Agent:
    """Create the Portfolio Manager agent."""
    return Agent(
        role="Portfolio Manager",
        goal="Integrate data/signals/risk and decide: BUY/SELL/HOLD for {ticker} now, with confidence.",
        backstory="Accountable decision-maker who weighs conflicting evidence and avoids bravado. You make decisions based on historical analysis.",
        tools=[],
        allow_delegation=False,
        verbose=True,
    )


def create_cached_data_collection_task(market_analyst, target_date: str = None) -> Task:
    """Create the data collection task with optional target date for historical analysis."""
    description = (
        "For ticker {ticker} with period {period} and interval {interval}:\n"
        "1) Use *Fetch OHLCV price history (cached)* and capture its returned `csv_path` (absolute), rows_count, date range, and last_close.\n"
        "2) Use *Fetch recent news (cached/historical)* (top 10)."
    )
    
    if target_date:
        description += f" Focus on news around {target_date}.\n"
    else:
        description += "\n"
    
    description += (
        "3) Summarize trend (up/down/sideways) and any data anomalies.\n\n"
        "**Return** JSON: {csv_path, rows_count, date_start, date_end, last_close, headlines[]}"
    )
    
    return Task(
        description=description,
        expected_output="JSON object with csv_path, rows_count, date_start, date_end, last_close, headlines[]",
        agent=market_analyst,
    )


def create_cached_technical_analysis_task(technical_strategist, data_task) -> Task:
    """Create the technical analysis task using cached tools."""
    return Task(
        description=(
            "Use the `csv_path` from the Market Data task output.\n"
            "- Call *Compute technical indicators* with that `csv_path`.\n"
            "- Call *Rule-based technical signal* with the same `csv_path`.\n"
            "- Optionally, call *Plot price & indicators* with the same `csv_path` to produce a chart.\n\n"
            "**Return** JSON: {close, ema20, ema50, macd, macd_signal, rsi, bb_lower, bb_middle, bb_upper, "
            "events[], rule_signal{signal, score, reasons[]}, chart_path?}"
        ),
        expected_output="JSON with indicators, notable events, a rule-based signal, and optional chart path",
        context=[data_task],
        agent=technical_strategist,
    )


def create_cached_risk_analysis_task(risk_manager, data_task) -> Task:
    """Create the risk analysis task using cached tools."""
    return Task(
        description=(
            "Use the `csv_path` from the Market Data task output.\n"
            "- Call *Compute risk metrics* with that `csv_path`.\n"
            "- Propose stop_loss %, take_profit %, position_size % based on volatility and drawdown (conservative).\n\n"
            "**Return** JSON: {vol_annualized, max_drawdown, hist_VaR_1d_95, n_days, suggested:{stop_loss_pct, "
            "take_profit_pct, position_size_pct}}"
        ),
        expected_output="JSON with risk metrics and a conservative risk plan",
        context=[data_task],
        agent=risk_manager,
    )


def create_cached_decision_task(portfolio_manager, data_task, tech_task, risk_task) -> Task:
    """Create the final decision task."""
    return Task(
        description=(
            "Synthesize all prior outputs into a single recommendation for {ticker}. Choose one: BUY / SELL / HOLD now. "
            "Provide 3–5 reasons (include indicators & risk), confidence (0–1), and restate the risk plan.\n\n"
            "**Return** FINAL JSON: {action, confidence, price, reasons[], key_signals[], "
            "risk{stop_loss_pct, take_profit_pct, position_size_pct}}"
        ),
        expected_output="A clean JSON object with action, confidence, reasons, key_signals, and risk plan",
        context=[data_task, tech_task, risk_task],
        agent=portfolio_manager,
    )


def create_cached_financial_advisor_crew(target_date: str = None) -> Crew:
    """
    Create and configure the financial advisor crew with cached tools.
    
    Args:
        target_date: Optional date string (YYYY-MM-DD) for historical analysis
    
    Returns:
        Configured Crew instance that uses cached data
    """
    # Create agents
    market_analyst = create_cached_market_data_analyst()
    technical_strategist = create_cached_technical_strategist()
    risk_manager = create_cached_risk_manager()
    portfolio_manager = create_cached_portfolio_manager()
    
    # Create tasks
    data_task = create_cached_data_collection_task(market_analyst, target_date)
    tech_task = create_cached_technical_analysis_task(technical_strategist, data_task)
    risk_task = create_cached_risk_analysis_task(risk_manager, data_task)
    decision_task = create_cached_decision_task(portfolio_manager, data_task, tech_task, risk_task)
    
    # Create crew
    crew = Crew(
        agents=[market_analyst, technical_strategist, risk_manager, portfolio_manager],
        tasks=[data_task, tech_task, risk_task, decision_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew