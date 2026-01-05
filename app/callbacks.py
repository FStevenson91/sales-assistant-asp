# from google.adk.agents.callback_context import CallbackContext
# from google.adk.models.llm_request import LlmRequest
# from .prompt import agent_prompt
# from .config import AGENT_NAME, COMPANY


# def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest):
#     """
#     Runs before each LLM call.
#     Gets seller_email from session state and hydrates the prompt.
#     """
    
#     # Get seller_email from session state
#     seller_email = callback_context.state.get("seller_email", None)
    
#     if not seller_email:
#         seller_email = callback_context.state.get("user_id", "vendedor@inmobiliaria.com")
    
#     print("🔐 Seller email from session:", seller_email)
    
#     # Hydrate prompt with dynamic seller_email
#     final_instruction = agent_prompt.format(
#         agent_name=AGENT_NAME,
#         company=COMPANY,
#         seller_email=seller_email
#     )
    
#     # Set the instruction
#     if llm_request.config:
#         llm_request.config.system_instruction = final_instruction
    
#     return None