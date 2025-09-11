"""
Main script for running the Resume Tailor AI Crew.
"""
import os
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv
from src.agents.crew_setup import create_resume_tailor_crew

warnings.filterwarnings('ignore')


def main():
    """Main function to run the resume tailor crew."""
    # Load environment variables
    load_dotenv()
    
    # Check for required API key
    if not os.getenv('OPENAI_API_KEY'):
        print('⚠️  Set OPENAI_API_KEY in your environment for AI processing.')
        return
    
    # Get inputs from command line arguments or user input
    if len(sys.argv) >= 3:
        job_url = sys.argv[1]
        resume_path = sys.argv[2]
    else:
        print("Resume Tailor AI - Customize your resume for any job posting\n")
        job_url = input("Enter the job posting URL: ").strip()
        resume_path = input("Enter the path to your LaTeX resume file: ").strip()
    
    # Validate inputs
    if not job_url:
        print("❌ Job posting URL is required")
        return
    
    if not os.path.exists(resume_path):
        print(f"❌ Resume file not found: {resume_path}")
        return
    
    if not resume_path.endswith('.tex'):
        print("❌ Resume file must be a LaTeX (.tex) file")
        return
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n🎯 Starting resume tailoring process...")
    print(f"📋 Job posting: {job_url}")
    print(f"📄 Original resume: {resume_path}")
    print(f"🤖 Using model: {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
    print(f"📁 Output directory: {output_dir.absolute()}\n")
    
    # Create and run the crew
    try:
        crew = create_resume_tailor_crew()
        
        result = crew.kickoff(inputs={
            'job_url': job_url,
            'resume_path': os.path.abspath(resume_path),
        })
        
        print('\n🎉 ===== RESUME TAILORING COMPLETE =====\n')
        print(result)
        print('\n✅ Check the output directory for your tailored resume and PDF!')
        
    except Exception as e:
        print(f"\n❌ Error during resume tailoring: {str(e)}")
        print("Please check your inputs and try again.")


if __name__ == '__main__':
    main()