# Resume Tailor AI

An AI-powered CrewAI system that automatically tailors LaTeX resumes to match specific job postings, creating optimized one-page PDFs.

## Features

- **Job Posting Analysis**: Fetches and analyzes job postings from URLs to extract key requirements
- **Intelligent Resume Tailoring**: Customizes LaTeX resumes by reordering sections and incorporating relevant keywords
- **PDF Generation**: Compiles tailored resumes into professional one-page PDFs
- **ATS Optimization**: Ensures resumes are optimized for Applicant Tracking Systems

## Setup

1. **Environment Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Create a `.env` file in the resume_tailor directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL_NAME=gpt-4o-mini
   ```

3. **LaTeX Installation**
   Ensure you have LaTeX installed with pdflatex:
   - **Ubuntu/Debian**: `sudo apt-get install texlive-latex-base texlive-latex-extra`
   - **macOS**: Install MacTeX from https://www.tug.org/mactex/
   - **Windows**: Install MiKTeX from https://miktex.org/

## Usage

### Command Line
```bash
python main.py <job_url> <resume_path>
```

### Interactive Mode
```bash
python main.py
```

### Example
```bash
python main.py "https://company.com/jobs/software-engineer" "/path/to/my/resume.tex"
```

## Directory Structure

```
resume_tailor/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── src/
│   ├── agents/            # CrewAI agents and tasks
│   │   ├── crew_agents.py # Agent definitions
│   │   ├── crew_tasks.py  # Task definitions
│   │   ├── crew_setup.py  # Crew configuration
│   │   └── tools.py       # Custom tools
│   ├── processing/        # Resume processing utilities
│   └── utils/            # General utilities
├── templates/            # Resume templates
└── output/              # Generated tailored resumes and PDFs
```

## How It Works

1. **Job Posting Analyst**: Fetches and analyzes the job posting to extract requirements, skills, and keywords
2. **Resume Tailor**: Reads the LaTeX resume and strategically customizes it to match the job requirements
3. **PDF Finalizer**: Compiles the tailored LaTeX into a professional one-page PDF

## Input Requirements

- **Job URL**: A valid URL to a job posting
- **LaTeX Resume**: A properly formatted `.tex` resume file

## Output

- Tailored LaTeX resume file
- Compiled one-page PDF
- Analysis report with optimization details