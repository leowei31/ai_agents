"""
CrewAI setup for resume tailoring.
"""
from crewai import Crew, Process
from .crew_agents import (
    create_job_posting_analyst,
    create_resume_tailor, 
    create_pdf_finalizer
)
from .crew_tasks import (
    create_job_analysis_task,
    create_resume_tailoring_task,
    create_pdf_generation_task
)


def create_resume_tailor_crew() -> Crew:
    """Create and configure the resume tailoring crew."""
    
    # Create agents
    job_analyst = create_job_posting_analyst()
    resume_tailor = create_resume_tailor()
    pdf_finalizer = create_pdf_finalizer()
    
    # Create tasks
    job_task = create_job_analysis_task(job_analyst)
    tailor_task = create_resume_tailoring_task(resume_tailor, job_task)
    pdf_task = create_pdf_generation_task(pdf_finalizer, job_task, tailor_task)
    
    # Create crew
    crew = Crew(
        agents=[job_analyst, resume_tailor, pdf_finalizer],
        tasks=[job_task, tailor_task, pdf_task],
        process=Process.sequential,
        verbose=True,
        memory=False,  # Disable memory for better performance
        embedder={
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small"
            }
        }
    )
    
    return crew