from google.adk.agents import SequentialAgent, LlmAgent
from .tools import dti_tool
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.runners import InMemoryRunner


# Agent to collect information (uses LLM, no tools)
info_collector = LlmAgent(
    name="InfoCollector",
    model="gemini-2.5-flash",
    instruction="Greet the user and collect their exact 'monthly income' and 'total monthly loan amount' required for a DTI calculation. Once both numbers are available, the agent is done.",
)

# Agent to calculate DTI (uses custom tool)
dti_calculator = LlmAgent(
    name="DTICalculator",
    model="gemini-2.5-flash",
    instruction="Use the `calculate_debt_to_income` tool with the monthly income of {income} and monthly debt of {debt} retrieved from the session state. Then, acknowledge the calculated result.",
    tools=[dti_tool],
    output_key="dti_ratio"
)

# Agent to fetch rates (uses a different tool)
rate_fetcher = LlmAgent(
    name="RateFetcher",
    model="gemini-2.5-flash",
    instruction="Use the `GoogleSearchTool` tool to find current mortgage rates. The agent must run this tool to proceed.",
    tools=[GoogleSearchTool],
    output_key="current_loan_rate"
)

# Agent to make a decision and summarize
decision_maker = LlmAgent(
    name="DecisionMaker",
    model="gemini-2.5-flash",
    instruction="""
    Based on the session state:
    DTI: {dti_ratio}%, Current Rate: {current_loan_rate}%.
    If DTI is under 43%, the status is 'Approved'.
    If DTI is 43% or over, the status is 'Conditional Approval'.
    Summarize all the information (income, debt, DTI, rate, and final status) for the user in a clear format.
    """,
)

# Orchestrator: Sequential Agent runs all sub-agents in order, without user prompts in between
root_agent = SequentialAgent(
    name="LoanApplicationPipeline",
    description="Manages the end-to-end loan pre-screening process from info collection to decision.",    
    sub_agents=[
        info_collector,
        dti_calculator,
        rate_fetcher,
        decision_maker
    ]
)

runner = InMemoryRunner(agent=root_agent)
