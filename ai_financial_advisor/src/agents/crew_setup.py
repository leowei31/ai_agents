"""
Setup and configuration for the CrewAI financial advisor crew.
"""
from crewai import Crew, Process
from .crew_agents import (
    create_market_data_analyst, create_technical_strategist,
    create_risk_manager, create_portfolio_manager
)
from .crew_tasks import (
    create_data_collection_task, create_technical_analysis_task,
    create_risk_analysis_task, create_decision_task
)


def create_financial_advisor_crew() -> Crew:
    """
    Create and configure the financial advisor crew.
    
    Returns:
        Configured Crew instance
    """
    # Create agents
    market_analyst = create_market_data_analyst()
    technical_strategist = create_technical_strategist()
    risk_manager = create_risk_manager()
    portfolio_manager = create_portfolio_manager()
    
    # Create tasks
    data_task = create_data_collection_task(market_analyst)
    tech_task = create_technical_analysis_task(technical_strategist, data_task)
    risk_task = create_risk_analysis_task(risk_manager, data_task)
    decision_task = create_decision_task(portfolio_manager, data_task, tech_task, risk_task)
    
    # Create crew
    crew = Crew(
        agents=[market_analyst, technical_strategist, risk_manager, portfolio_manager],
        tasks=[data_task, tech_task, risk_task, decision_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew