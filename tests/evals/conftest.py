"""
Configuración compartida para todas las evals.

Este archivo contiene "fixtures" - funciones que preparan el entorno
para correr las evaluaciones. pytest los detecta automáticamente.
"""

import pytest
from unittest.mock import MagicMock, patch
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


# =============================================================================
# FIXTURE: Crear una sesión del agente
# =============================================================================
# Un "fixture" es código que se ejecuta ANTES de cada test.
# @pytest.fixture le dice a pytest que esta función prepara algo reutilizable.

@pytest.fixture
def agent_session():
    """
    Crea una sesión limpia del agente para cada eval.

    Retorna un diccionario con:
    - runner: El ejecutor del agente
    - session: La sesión actual
    - session_service: El servicio de sesiones

    Uso en tests:
        def test_algo(agent_session):
            runner = agent_session["runner"]
            # ... usar el runner
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(
        user_id="eval_user",
        app_name="eval_app"
    )
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        app_name="eval_app"
    )

    return {
        "runner": runner,
        "session": session,
        "session_service": session_service
    }


@pytest.fixture
def agent_session_with_seller():
    """
    Crea una sesión con seller_email ya configurado en el state.

    Esto simula una sesión real donde el webhook ya inyectó
    el email del vendedor.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(
        user_id="eval_user",
        app_name="eval_app",
        state={"seller_email": "vendedor_eval@inmobiliaria.com"}  # ← Pre-configurado
    )
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        app_name="eval_app"
    )

    return {
        "runner": runner,
        "session": session,
        "session_service": session_service,
        "seller_email": "vendedor_eval@inmobiliaria.com"
    }


# =============================================================================
# HELPER: Función para enviar mensajes al agente
# =============================================================================
# Esta función simplifica el envío de mensajes en las evals.

def send_message(agent_session: dict, message_text: str) -> dict:
    """
    Envía un mensaje al agente y retorna la respuesta estructurada.

    Args:
        agent_session: El fixture con runner y session
        message_text: El texto del usuario (ej: "Crea un contacto")

    Returns:
        dict con:
        - text: El texto de respuesta del agente
        - tool_calls: Lista de herramientas que el agente llamó
        - events: Todos los eventos raw (para debug)
    """
    runner = agent_session["runner"]
    session = agent_session["session"]

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message_text)]
    )

    events = list(runner.run(
        new_message=message,
        user_id="eval_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ))

    # Extraer texto de respuesta
    response_text = ""
    tool_calls = []

    for event in events:
        # Capturar texto de respuesta
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text

        # Capturar tool calls (llamadas a herramientas)
        if hasattr(event, 'tool_calls') and event.tool_calls:
            tool_calls.extend(event.tool_calls)

    return {
        "text": response_text,
        "tool_calls": tool_calls,
        "events": events
    }


# =============================================================================
# HELPERS: Funciones para verificar respuestas
# =============================================================================

def response_contains_any(response_text: str, keywords: list[str]) -> bool:
    """
    Verifica si la respuesta contiene alguna de las keywords.

    Útil para verificar que el agente pidió confirmación, rechazó algo, etc.

    Ejemplo:
        assert response_contains_any(response["text"], ["confirmar", "seguro", "deseas"])
    """
    response_lower = response_text.lower()
    return any(kw.lower() in response_lower for kw in keywords)


def response_is_in_spanish(response_text: str) -> bool:
    """
    Verificación básica de que la respuesta está en español.

    Busca palabras comunes en español que no existen en inglés.
    Limpia puntuación antes de verificar.
    """
    import re

    # Limpiar puntuación y convertir a minúsculas
    clean_text = re.sub(r'[^\w\s]', '', response_text.lower())
    words = clean_text.split()

    # Palabras comunes en español
    spanish_indicators = [
        "hola", "el", "la", "de", "que", "por", "para", "con", "es", "un", "una",
        "soy", "tu", "en", "puedo", "ayudarte", "qué", "cómo", "contacto", "asistente"
    ]

    matches = sum(1 for word in spanish_indicators if word in words)
    return matches >= 2  # Al menos 2 palabras en español
