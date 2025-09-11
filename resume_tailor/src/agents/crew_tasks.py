"""
CrewAI tasks for resume tailoring workflow.
"""
from crewai import Task


def create_job_analysis_task(job_analyst) -> Task:
    """Create the job posting analysis task."""
    return Task(
        description=(
            "For the job posting URL: {job_url}\n"
            "1) Use the *Fetch job posting* tool to retrieve the complete job description\n"
            "2) Analyze the job posting to extract:\n"
            "   - Required technical skills and technologies\n"
            "   - Required experience level and years\n"
            "   - Educational requirements\n"
            "   - Key responsibilities and duties\n"
            "   - Important keywords and phrases for ATS optimization\n"
            "   - Company culture and values mentioned\n"
            "   - Preferred qualifications vs requirements\n\n"
            "3) Prioritize the requirements by importance (critical, important, preferred)\n"
            "4) Identify the top 10-15 keywords that should be emphasized in the resume\n\n"
            "**Return** JSON: {job_title, company, required_skills[], preferred_skills[], "
            "experience_years, education_requirements, key_responsibilities[], "
            "priority_keywords[], company_values[], job_summary}"
        ),
        expected_output="JSON object with comprehensive job analysis including prioritized requirements and keywords",
        agent=job_analyst,
    )


def create_resume_tailoring_task(resume_tailor, job_task) -> Task:
    """Create the resume tailoring task."""
    return Task(
        description=(
            "Using the job analysis results and the original resume file path: {resume_path}\n\n"
            "1) Use *Read LaTeX resume* tool to load the current resume content\n"
            "2) Analyze how well the current resume matches the job requirements\n"
            "3) Strategically tailor the resume by:\n"
            "   - Reordering sections to highlight most relevant experience first\n"
            "   - Incorporating priority keywords naturally into experience descriptions\n"
            "   - Emphasizing relevant skills and technologies from the job posting\n"
            "   - Adjusting the professional summary/objective to match the role\n"
            "   - Highlighting relevant projects and achievements\n"
            "   - Removing or de-emphasizing less relevant information\n"
            "   - Ensuring ATS-friendly formatting while maintaining LaTeX structure\n\n"
            "4) Use *Validate resume length* to ensure content will fit on one page\n"
            "5) Use *Write tailored resume* to save the customized version\n\n"
            "CRITICAL: Maintain proper LaTeX syntax and formatting. The output must be valid LaTeX.\n"
            "Focus on impact-driven bullet points with quantified achievements where possible.\n\n"
            "**Return** JSON: {tailored_resume_path, changes_made[], keywords_incorporated[], "
            "sections_reordered[], estimated_match_score, length_status}"
        ),
        expected_output="JSON with tailored resume path, detailed changes made, and optimization metrics",
        context=[job_task],
        agent=resume_tailor,
    )


def create_pdf_generation_task(pdf_finalizer, job_task, tailor_task) -> Task:
    """Create the PDF generation and finalization task.""" 
    return Task(
        description=(
            "Using the tailored resume from the previous task:\n\n"
            "1) Use *Compile LaTeX to PDF* tool to generate the final PDF\n"
            "2) Verify the PDF was created successfully\n"
            "3) Use *Validate resume length* on the final content to confirm one-page format\n"
            "4) If compilation fails, analyze the LaTeX errors and provide recommendations\n"
            "5) Check that all job requirements are adequately addressed in the final version\n\n"
            "**Return** JSON: {pdf_path, compilation_success, final_length_check, "
            "quality_score, recommendations[], job_match_summary}"
        ),
        expected_output="JSON with final PDF path, quality metrics, and completion status",
        context=[job_task, tailor_task],
        agent=pdf_finalizer,
    )