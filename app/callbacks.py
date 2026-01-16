# app/callbacks.py
"""
Callbacks para inyectar el seller_email en el contexto del agente.
Esto actúa como guardrail para asegurar aislamiento de datos entre vendedores.
"""

from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from .prompt import agent_prompt
from .config import AGENT_NAME, COMPANY


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Se ejecuta ANTES de cada llamada al LLM.
    
    Propósito:
    - Lee seller_email del state de la sesión
    - Hidrata el prompt con el seller_email dinámico
    - Garantiza que cada vendedor solo acceda a sus datos
    """
    
    # 1. Obtener seller_email del state de la sesión
    seller_email = callback_context.state.get("seller_email")
    
    # Fallback si no hay seller_email (para testing local)
    if not seller_email:
        seller_email = "test@inmobiliaria.com"
        callback_context.state["seller_email"] = seller_email
    
    print(f"🔐 [Callback] Seller email: {seller_email}")
    
    # 2. Hidratar el prompt con el seller_email dinámico
    final_instruction = agent_prompt.format(
        agent_name=AGENT_NAME,
        company=COMPANY,
        seller_email=seller_email
    )
    
    # 3. Inyectar la instrucción en el request
    if llm_request.config:
        llm_request.config.system_instruction = final_instruction
    else:
        llm_request.config = types.GenerateContentConfig(
            system_instruction=final_instruction
        )
    
    # 4. Retornar None para continuar con la llamada al LLM
    return None


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