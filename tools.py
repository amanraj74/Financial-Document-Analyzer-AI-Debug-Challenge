## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai.tools import tool
from crewai_tools import SerperDevTool
from langchain_community.document_loaders import PyPDFLoader

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool using @tool decorator
@tool("Read Financial Document")
def read_financial_document(file_path: str = "data/sample.pdf") -> str:
    """Tool to read and extract text content from a PDF financial document.

    Args:
        file_path (str, optional): Path of the PDF file. Defaults to 'data/sample.pdf'.

    Returns:
        str: Extracted text from the financial document (truncated to key sections).
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at path '{file_path}'. Please provide a valid file path."

    try:
        loader = PyPDFLoader(file_path=file_path)
        docs = loader.load()

        full_report = ""
        for page in docs:
            content = page.page_content

            # Clean up extra whitespace while preserving structure
            while "\n\n\n" in content:
                content = content.replace("\n\n\n", "\n\n")

            full_report += content + "\n"

        result = full_report.strip()

        # Truncate to stay within LLM token limits (free tier)
        MAX_CHARS = 4000
        if len(result) > MAX_CHARS:
            result = result[:MAX_CHARS] + "\n\n[... Document truncated. Key financial data shown above ...]"

        return result
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"