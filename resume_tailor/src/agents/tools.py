"""
CrewAI tools for resume tailoring.
"""
import os
import re
import subprocess
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from crewai_tools import tool


@tool
def fetch_job_posting(url: str) -> Dict[str, Any]:
    """
    Fetch and parse a job posting from a URL.
    
    Args:
        url: The URL of the job posting
        
    Returns:
        Dictionary containing the job posting text and metadata
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return {
            "success": True,
            "url": url,
            "content": text,
            "length": len(text)
        }
        
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "content": ""
        }


@tool
def read_latex_resume(latex_file_path: str) -> Dict[str, Any]:
    """
    Read and parse a LaTeX resume file.
    
    Args:
        latex_file_path: Path to the LaTeX (.tex) resume file
        
    Returns:
        Dictionary containing the resume content and structure
    """
    try:
        if not os.path.exists(latex_file_path):
            return {
                "success": False,
                "error": f"File not found: {latex_file_path}",
                "content": ""
            }
        
        with open(latex_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extract key sections using regex patterns
        sections = {}
        
        # Common LaTeX resume sections
        section_patterns = {
            'name': r'\\name\{([^}]+)\}',
            'email': r'\\email\{([^}]+)\}',
            'phone': r'\\phone\{([^}]+)\}',
            'address': r'\\address\{([^}]+)\}',
            'summary': r'\\section\{(?:Summary|Profile|Objective)\}(.*?)(?=\\section|\Z)',
            'experience': r'\\section\{(?:Experience|Work Experience|Professional Experience)\}(.*?)(?=\\section|\Z)',
            'education': r'\\section\{(?:Education|Academic Background)\}(.*?)(?=\\section|\Z)',
            'skills': r'\\section\{(?:Skills|Technical Skills|Core Competencies)\}(.*?)(?=\\section|\Z)',
            'projects': r'\\section\{(?:Projects|Notable Projects)\}(.*?)(?=\\section|\Z)',
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
        
        return {
            "success": True,
            "file_path": latex_file_path,
            "content": content,
            "sections": sections,
            "length": len(content)
        }
        
    except Exception as e:
        return {
            "success": False,
            "file_path": latex_file_path,
            "error": str(e),
            "content": ""
        }


@tool
def write_tailored_resume(tailored_content: str, output_path: str) -> Dict[str, Any]:
    """
    Write the tailored resume content to a LaTeX file.
    
    Args:
        tailored_content: The tailored LaTeX resume content
        output_path: Path where to save the tailored resume
        
    Returns:
        Dictionary with operation status
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(tailored_content)
        
        return {
            "success": True,
            "output_path": output_path,
            "message": f"Tailored resume saved to {output_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "output_path": output_path,
            "error": str(e)
        }


@tool
def compile_latex_to_pdf(latex_file_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Compile a LaTeX file to PDF using pdflatex.
    
    Args:
        latex_file_path: Path to the LaTeX file to compile
        output_dir: Directory for output files (defaults to same as input)
        
    Returns:
        Dictionary with compilation status and PDF path
    """
    try:
        if not os.path.exists(latex_file_path):
            return {
                "success": False,
                "error": f"LaTeX file not found: {latex_file_path}",
                "pdf_path": ""
            }
        
        if output_dir is None:
            output_dir = os.path.dirname(latex_file_path)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Run pdflatex
        cmd = [
            'pdflatex',
            '-output-directory', output_dir,
            '-interaction=nonstopmode',
            latex_file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Determine PDF path
        base_name = os.path.splitext(os.path.basename(latex_file_path))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        if result.returncode == 0 and os.path.exists(pdf_path):
            return {
                "success": True,
                "pdf_path": pdf_path,
                "latex_output": result.stdout,
                "message": f"PDF compiled successfully: {pdf_path}"
            }
        else:
            return {
                "success": False,
                "error": f"LaTeX compilation failed. Return code: {result.returncode}",
                "latex_output": result.stdout,
                "latex_errors": result.stderr,
                "pdf_path": ""
            }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "LaTeX compilation timed out",
            "pdf_path": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "pdf_path": ""
        }


@tool 
def validate_resume_length(latex_content: str) -> Dict[str, Any]:
    """
    Estimate if the resume will fit on one page and provide metrics.
    
    Args:
        latex_content: The LaTeX resume content to analyze
        
    Returns:
        Dictionary with length analysis and recommendations
    """
    try:
        # Count different content types
        text_lines = len([line for line in latex_content.split('\n') if line.strip() and not line.strip().startswith('%')])
        
        # Count major sections
        section_count = len(re.findall(r'\\section\{', latex_content))
        
        # Count itemize items (bullet points)
        item_count = len(re.findall(r'\\item', latex_content))
        
        # Rough estimation (these are heuristics)
        estimated_length = "unknown"
        if text_lines < 50 and item_count < 15:
            estimated_length = "likely_one_page"
        elif text_lines < 80 and item_count < 25:
            estimated_length = "borderline_one_page"
        else:
            estimated_length = "likely_multiple_pages"
        
        recommendations = []
        if estimated_length == "likely_multiple_pages":
            recommendations.extend([
                "Consider removing less relevant experience",
                "Shorten bullet points",
                "Combine related sections",
                "Use more concise language"
            ])
        elif estimated_length == "borderline_one_page":
            recommendations.append("Monitor spacing and consider minor edits if needed")
        
        return {
            "success": True,
            "text_lines": text_lines,
            "section_count": section_count,
            "item_count": item_count,
            "estimated_length": estimated_length,
            "recommendations": recommendations
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "estimated_length": "unknown"
        }