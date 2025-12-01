from google.adk.tools import Tool, ToolContext, google_search

def calculate_debt_to_income(context: ToolContext, monthly_income: float, monthly_debt: float) -> str:
    """
    Calculates the critical Debt-to-Income (DTI) ratio.
    Args:
        monthly_income: The user's total gross monthly income.
        monthly_debt: The sum of all monthly debt payments.
    """
    if monthly_income <= 0:
        return "Error: Monthly income must be greater than zero."
    dti = (monthly_debt / monthly_income) * 100
    context.state["dti_ratio"] = dti
    context.state["income"] = monthly_income
    context.state["debt"] = monthly_debt
    return f"DTI ratio calculated as {dti:.2f}%."

dti_tool = Tool(calculate_debt_to_income)

# Google's built-in Search tool is directly available
rates_tool = google_search
