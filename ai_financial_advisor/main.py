"""
Main script for running the AI Financial Advisor.
"""
import os
import warnings
from dotenv import load_dotenv
from src.agents.crew_setup import create_financial_advisor_crew

warnings.filterwarnings('ignore')


def main():
    """Main function to run the financial advisor crew."""
    # Load environment variables
    load_dotenv()
    
    # Check for required API key
    if not os.getenv('POLYGON_API_KEY'):
        print('⚠️  Set POLYGON_API_KEY in your environment for data fetching.')
        return
    
    # Configuration
    TICKER = 'MSTR'      # Change as needed
    PERIOD = '1mo'        # e.g., '1y', '2y', '6mo'
    INTERVAL = '1h'    # e.g., '1h', '1wk', '60min', '1d'
    
    print(f"Starting analysis for {TICKER} ({PERIOD}, {INTERVAL})")
    print(f"Using model: {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
    
    # Create and run the crew
    crew = create_financial_advisor_crew()
    
    result = crew.kickoff(inputs={
        'ticker': TICKER,
        'period': PERIOD,
        'interval': INTERVAL,
    })
    
    print('\n===== FINAL RECOMMENDATION =====\n')
    print(result)


if __name__ == '__main__':
    main()