"""
CrewAI agents for financial analysis.
"""
from crewai import Agent
from .tools import (
    fetch_ohlcv, fetch_news, compute_indicators, 
    rule_based_signal, plot_price_indicators, compute_risk
)


def create_market_data_analyst() -> Agent:
    """Create the Market Data Analyst agent."""
    return Agent(
        role="Market Data Analyst",
        goal="Gather and validate OHLCV & headlines for {ticker}. Summarize trend and anomalies.",
        backstory="Meticulous about data quality, you verify timeframes and note gaps/splits.",
        tools=[fetch_ohlcv, fetch_news],
        allow_delegation=False,
        verbose=True,
    )


def create_technical_strategist() -> Agent:
    """Create the Technical Strategist agent."""
    return Agent(
        role="Technical Strategist",
        goal="Transform price data into signals using EMA/RSI/MACD/Bollinger and explain rationale.",
        backstory="Disciplined technician balancing momentum and mean-reversion; you state both sides.",
        tools=[compute_indicators, rule_based_signal, plot_price_indicators],
        allow_delegation=False,
        verbose=True,
    )


def create_risk_manager() -> Agent:
    """Create the Risk Manager agent."""
    return Agent(
        role="Risk Manager",
        goal="Quantify risk (vol, drawdown, VaR) and propose a conservative risk plan.",
        backstory="Capital preservation first; you recommend sensible stops, targets, and sizing.",
        tools=[compute_risk],
        allow_delegation=False,
        verbose=True,
    )


def create_portfolio_manager() -> Agent:
    """Create the Portfolio Manager agent."""
    return Agent(
        role="Portfolio Manager",
        goal="Integrate data/signals/risk and decide: BUY/SELL/HOLD for {ticker} now, with confidence.",
        backstory="Accountable decision-maker who weighs conflicting evidence and avoids bravado.",
        tools=[],
        allow_delegation=False,
        verbose=True,
    )