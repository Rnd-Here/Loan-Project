from google.adk.agents import Agent, SequentialAgent, LlmAgent
from google.adk.tools import AgentTool, FunctionTool, google_search
from google.adk.runners import InMemoryRunner
from typing import Any, Dict

from google.adk.agents import Agent, LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.models.google_llm import Gemini
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.genai import types


APP_NAME = "loan-screener"  # Application
USER_ID = "default"  # User
SESSION = "default"  # Session

MODEL_NAME = "gemini-2.5-flash-lite"
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

def get_user_confirmation()-> str:
    """
    Simulates getting user confirmation to proceed.
    In a real application, this would involve user interaction.
    """
    return "Please provide these details. to proceed ahead"

def calculate_debt_to_income(monthly_income: float, monthly_debt: float) -> str:
    """
    Calculates the critical Debt-to-Income (DTI) ratio.
    Args:
        monthly_income: The user's total gross monthly income.
        monthly_debt: The sum of all monthly debt payments.
    """
    if monthly_income <= 0:
        return "Error: Monthly income must be greater than zero."
    dti = (monthly_debt / monthly_income) * 100
    return f"DTI ratio calculated as {dti:.2f}%."

# Agent to calculate DTI (uses custom tool)
dti_calculator = Agent(
    name="DTICalculator",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Use the `calculate_debt_to_income` tool with the monthly income of individual and monthly debt of retrieved from user_info." \
    " Then, acknowledge the calculated result. Do not interact with the user directly."
    "Wait until you have the results from tools before proceeding to next agent.",

    tools=[FunctionTool(func=calculate_debt_to_income)],
    output_key="dti_ratio"
)

# Agent to fetch rates (uses a different tool)
rate_fetcher = Agent(
    name="RateFetcher",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Use the `GoogleSearchTool` tool to find current mortgage rates. " \
    "The agent must run this tool to proceed."
    "Do not interact with the user directly."
    "Wait until you have the results from tools before proceeding to next agent.",
    tools=[google_search],
    output_key="current_loan_rate"
)

# Agent to make a decision and summarize
decision_maker = Agent(
    name="DecisionMaker",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="""
    DTI: {dti_ratio}%, Current Rate: {current_loan_rate}%.
    If DTI is under 43%, the status is 'Approved'.
    If DTI is 43% or over, the status is 'Conditional Approval'.
    Summarize all the information (income, debt, DTI, rate, and final status) for the user in a clear format.
    Do not interact with the user directly.
    """,
    output_key="final_decision"
)


# Agent to collect information (uses LLM, no tools)
loan_screener_pipeline = SequentialAgent(
    name="LoanScreener",
    sub_agents=[
        dti_calculator, 
        rate_fetcher, 
        decision_maker],
                )

root_agent = Agent(
    name="InfoCollector",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="Greet the user!"
    "Collect the user's monthly income and total monthly debt."
    "Wait until you have both pieces of information before calling the sub agent loan_screener_pipeline.",
    tools=[AgentTool(loan_screener_pipeline)],
    output_key="user_info"
)

session_service = InMemorySessionService()



runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
