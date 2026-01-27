"""
Callbacks to inject the seller_email into the agent's context.
This acts as a guardrail to ensure data isolation between sellers.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from dotenv import load_dotenv

from .prompt import agent_prompt
from .config import AGENT_NAME, COMPANY

load_dotenv()

logger = logging.getLogger(__name__)

def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Executes BEFORE each LLM call.
    Purpose:
    - Reads seller_email from the session state.
    - Hydrates the prompt with the dynamic seller_email.
    - Ensures each seller only accesses their own data.
    """
    try:
        # Obtener seller_email del state de la sesión
        seller_email = callback_context.state.get("seller_email")
        
        # Fallback si no hay seller_email (para testing local)
        if not seller_email:
            seller_email = os.getenv("TEST_SELLER_EMAIL", "test@inmobiliaria.com")
            callback_context.state["seller_email"] = seller_email
        
        logger.info(f"🔐 [Callback] Seller email: {seller_email}")
        
         # Calcular el timestamp ACTUAL en cada request
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Hidratar el prompt con el seller_email dinámico
        final_instruction = agent_prompt.format(
            agent_name=AGENT_NAME,
            company=COMPANY,
            seller_email=seller_email,
            current_time=current_time
        )
        
        # Inyectar la instrucción en el request
        if llm_request.config:
            llm_request.config.system_instruction = final_instruction
        else:
            llm_request.config = types.GenerateContentConfig(
                system_instruction=final_instruction
            )
        
        # Retornar None para continuar con la llamada al LLM
        return None
        
    except Exception as e:
          logger.error(f"❌ [Callback Error] {str(e)}", exc_info=True)
          return None