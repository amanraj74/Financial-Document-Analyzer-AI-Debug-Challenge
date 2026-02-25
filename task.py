## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, read_financial_document

# ────────────────────────────────────────────────────────────────────────────
# Task 1: Document Verification
# ────────────────────────────────────────────────────────────────────────────
verification_task = Task(
    description=(
        "Read and verify the uploaded financial document.\n\n"
        "IMPORTANT: The document file path is: {file_path}\n"
        "You MUST use this exact file_path when calling the 'Read Financial Document' tool.\n\n"
        "1. Use the 'Read Financial Document' tool with file_path='{file_path}' to load the document.\n"
        "2. Confirm that this is a legitimate financial document (e.g., earnings report, "
        "annual report, balance sheet, income statement, SEC filing).\n"
        "3. Identify the document type, the company name, reporting period, and currency.\n"
        "4. Flag any data quality issues, missing sections, or formatting problems.\n"
        "5. Provide a brief summary of the document's structure and key sections found.\n"
        "If the document is not a valid financial document, clearly state this and explain why."
    ),
    expected_output=(
        "A verification report containing:\n"
        "- Document type (e.g., Quarterly Earnings, Annual Report, 10-K Filing)\n"
        "- Company name and reporting period\n"
        "- Confirmation of document legitimacy (Yes/No with reasons)\n"
        "- List of key sections found (Income Statement, Balance Sheet, Cash Flow, etc.)\n"
        "- Any data quality issues or warnings\n"
        "- Brief structural summary"
    ),
    agent=verifier,
    tools=[read_financial_document],
    async_execution=False,
)

# ────────────────────────────────────────────────────────────────────────────
# Task 2: Financial Analysis
# ────────────────────────────────────────────────────────────────────────────
analyze_document_task = Task(
    description=(
        "Perform a comprehensive financial analysis based on the user's query: {query}\n\n"
        "IMPORTANT: The document file path is: {file_path}\n"
        "You MUST use this exact file_path when calling the 'Read Financial Document' tool.\n\n"
        "1. Use the 'Read Financial Document' tool with file_path='{file_path}' to extract the document content.\n"
        "2. Identify and extract key financial metrics including:\n"
        "   - Revenue, net income, gross margin, operating margin\n"
        "   - Earnings per share (EPS)\n"
        "   - Cash flow from operations, free cash flow\n"
        "   - Year-over-year growth rates\n"
        "3. Analyze trends and patterns in the financial data.\n"
        "4. Directly address the user's specific query with data-backed insights.\n"
        "5. Search the internet for relevant market context if needed."
    ),
    expected_output=(
        "A concise financial analysis report containing:\n"
        "- Executive summary addressing the user's query\n"
        "- Key financial metrics with actual numbers from the document\n"
        "- Trend analysis (growth rates, margin changes)\n"
        "- Strengths and weaknesses identified from the financials"
    ),
    agent=financial_analyst,
    tools=[read_financial_document, search_tool],
    async_execution=False,
    context=[verification_task],
)

# ────────────────────────────────────────────────────────────────────────────
# Task 3: Investment Analysis & Recommendations
# ────────────────────────────────────────────────────────────────────────────
investment_analysis_task = Task(
    description=(
        "Based on the financial analysis results, provide investment recommendations.\n\n"
        "User's original query: {query}\n\n"
        "1. Review the financial analysis from the previous task.\n"
        "2. Evaluate the company's investment potential based on:\n"
        "   - Financial health and stability\n"
        "   - Growth prospects and market position\n"
        "   - Valuation metrics (P/E, P/B, EV/EBITDA if available)\n"
        "   - Competitive advantages and moat\n"
        "3. Provide a clear investment thesis (bullish, bearish, or neutral) with supporting data.\n"
        "4. Suggest appropriate investment strategies based on risk tolerance levels.\n"
        "5. Include relevant disclaimers about investment risks.\n"
        "6. Search the internet for analyst consensus and recent market sentiment."
    ),
    expected_output=(
        "A professional investment recommendation report containing:\n"
        "- Investment thesis with clear rationale backed by financial data\n"
        "- Buy/Hold/Sell recommendation with target price range if applicable\n"
        "- Key investment catalysts and potential headwinds\n"
        "- Suggested portfolio allocation strategies for different risk profiles\n"
        "- Important risk disclaimers\n"
        "- Disclaimer: This is for informational purposes only and not financial advice"
    ),
    agent=investment_advisor,
    tools=[search_tool],
    async_execution=False,
)

# ────────────────────────────────────────────────────────────────────────────
# Task 4: Risk Assessment
# ────────────────────────────────────────────────────────────────────────────
risk_assessment_task = Task(
    description=(
        "Conduct a risk assessment based on the financial analysis results.\n\n"
        "User's original query: {query}\n\n"
        "Use the financial data from the analysis task (do NOT re-read the PDF).\n\n"
        "1. Identify and categorize key risks:\n"
        "   - Financial risks (liquidity, solvency)\n"
        "   - Market risks (competition, market conditions)\n"
        "   - Operational risks (supply chain, regulatory)\n"
        "2. Assess each risk's probability and potential impact.\n"
        "3. Provide an overall risk rating and recommendations."
    ),
    expected_output=(
        "A concise risk assessment report containing:\n"
        "- Overall risk rating (Low / Medium / High) with justification\n"
        "- Top 5 key risk factors with probability and impact\n"
        "- Risk mitigation strategies\n"
        "- Recommendations for risk management"
    ),
    agent=risk_assessor,
    tools=[search_tool],
    async_execution=False,
    output_file="outputs/risk_assessment.md",
    context=[analyze_document_task],
)