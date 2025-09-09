"""
CrewAI tasks for financial analysis workflow.
"""
from crewai import Task


def create_data_collection_task(market_analyst) -> Task:
    """Create the data collection task."""
    return Task(
        description=(
            "For ticker {ticker} with period {period} and interval {interval}:\n"
            "1) Use *Fetch OHLCV price history* and capture its returned `csv_path` (absolute), rows_count, date range, and last_close.\n"
            "2) Use *Fetch recent news* (top 10).\n"
            "3) Summarize trend (up/down/sideways) and any data anomalies.\n\n"
            "**Return** JSON: {csv_path, rows_count, date_start, date_end, last_close, headlines[]}"
        ),
        expected_output="JSON object with csv_path, rows_count, date_start, date_end, last_close, headlines[]",
        agent=market_analyst,
    )


def create_technical_analysis_task(technical_strategist, data_task) -> Task:
    """Create the technical analysis task."""
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


def create_risk_analysis_task(risk_manager, data_task) -> Task:
    """Create the risk analysis task."""
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


def create_decision_task(portfolio_manager, data_task, tech_task, risk_task) -> Task:
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