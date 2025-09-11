"""
Test script to validate the resume tailor setup.
"""
import os
from dotenv import load_dotenv


def test_environment():
    """Test environment variables and dependencies."""
    print("🧪 Testing Resume Tailor Setup...\n")
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✅ OPENAI_API_KEY is set")
    else:
        print("❌ OPENAI_API_KEY is not set")
    
    # Test imports
    try:
        import crewai
        print("✅ CrewAI imported successfully")
    except ImportError:
        print("❌ CrewAI import failed - run: pip install crewai")
    
    try:
        import requests
        print("✅ Requests imported successfully") 
    except ImportError:
        print("❌ Requests import failed - run: pip install requests")
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup imported successfully")
    except ImportError:
        print("❌ BeautifulSoup import failed - run: pip install beautifulsoup4")
    
    # Test our modules
    try:
        from src.agents.crew_setup import create_resume_tailor_crew
        print("✅ Resume tailor crew setup imported successfully")
    except ImportError as e:
        print(f"❌ Resume tailor import failed: {e}")
    
    # Test LaTeX installation
    import subprocess
    try:
        result = subprocess.run(['pdflatex', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pdflatex is available")
        else:
            print("❌ pdflatex is not available - install LaTeX")
    except FileNotFoundError:
        print("❌ pdflatex is not available - install LaTeX")
    
    print("\n🎯 Setup test complete!")


if __name__ == '__main__':
    test_environment()