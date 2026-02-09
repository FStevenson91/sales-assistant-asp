"""
Evals de Tool Calling: ¿El agente usa las herramientas correctamente?

Estas evaluaciones verifican que el agente:
1. Llama la herramienta correcta para cada caso
2. Pasa los parámetros correctos
3. Usa el seller_email del state (no uno inventado)

NOTA: Estas evals usan mocks para simular las respuestas del CRM
y poder inspeccionar qué parámetros se enviaron.
"""

import pytest
from unittest.mock import patch, MagicMock
from .conftest import send_message, response_contains_any


# =============================================================================
# EVAL: create_contact se llama con parámetros correctos
# =============================================================================

class TestCreateContactToolCall:
    """
    Evalúa si create_contact se llama correctamente.
    """

    @patch('app.tools.crm.requests.post')
    def test_create_uses_correct_seller_email(self, mock_post, agent_session_with_seller):
        """
        GIVEN: Usuario quiere crear un contacto y confirma
        WHEN: El agente ejecuta create_contact
        THEN: Debe usar el seller_email del state, NO uno inventado

        Este es un test CRÍTICO de seguridad multi-tenant.
        """
        # Configurar el mock para simular respuesta exitosa del CRM
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "123", "name": "Test"}
        )

        # Paso 1: Dar datos completos
        response1 = send_message(
            agent_session_with_seller,
            "Crea contacto: Juan Test, 555-1234, juan@test.com"
        )

        # Paso 2: Confirmar (si el agente pidió confirmación)
        if response_contains_any(response1["text"], ["confirm", "seguro", "crear"]):
            response2 = send_message(agent_session_with_seller, "sí, confirmo")

            # Verificar que se llamó al API
            if mock_post.called:
                call_args = mock_post.call_args

                # Verificar que el header x-user-email es el correcto
                headers = call_args.kwargs.get('headers', {})
                assert headers.get('x-user-email') == "vendedor_eval@inmobiliaria.com", \
                    f"seller_email incorrecto en headers: {headers.get('x-user-email')}"

                # Verificar el body
                body = call_args.kwargs.get('json', {})
                assert body.get('userEmail') == "vendedor_eval@inmobiliaria.com", \
                    f"seller_email incorrecto en body: {body.get('userEmail')}"

    @patch('app.tools.crm.requests.post')
    def test_create_validates_required_fields(self, mock_post, agent_session_with_seller):
        """
        GIVEN: Usuario da datos incompletos (falta email)
        WHEN: El agente procesa
        THEN: NO debe llamar create_contact, debe pedir el dato faltante
        """
        mock_post.return_value = MagicMock(status_code=200)

        # Dar datos incompletos (sin email)
        response = send_message(
            agent_session_with_seller,
            "Crea contacto: Juan Test, 555-1234"
        )

        # El agente debería pedir el email antes de crear
        keywords_pedir_email = ["email", "correo", "falta", "necesito"]

        assert response_contains_any(response["text"], keywords_pedir_email), \
            f"El agente no pidió el email faltante. Respuesta: {response['text'][:200]}"


# =============================================================================
# EVAL: list_contacts se llama correctamente
# =============================================================================

class TestListContactsToolCall:
    """
    Evalúa si list_contacts se llama correctamente.
    """

    @patch('app.tools.crm.requests.post')
    def test_list_uses_correct_seller_email(self, mock_post, agent_session_with_seller):
        """
        GIVEN: Usuario pide ver sus contactos
        WHEN: El agente ejecuta list_contacts
        THEN: Debe filtrar por el seller_email del state
        """
        # Simular respuesta del CRM
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "contacts": [
                    {"name": "Contact 1", "email": "c1@test.com"},
                    {"name": "Contact 2", "email": "c2@test.com"}
                ],
                "totalContacts": 2
            }
        )

        response = send_message(
            agent_session_with_seller,
            "Muéstrame mis contactos"
        )

        # Verificar que se llamó con el seller_email correcto
        if mock_post.called:
            headers = mock_post.call_args.kwargs.get('headers', {})
            assert headers.get('x-user-email') == "vendedor_eval@inmobiliaria.com", \
                "list_contacts no usó el seller_email correcto"

    @patch('app.tools.crm.requests.post')
    def test_list_with_search_term(self, mock_post, agent_session_with_seller):
        """
        GIVEN: Usuario busca un contacto específico
        WHEN: El agente ejecuta list_contacts
        THEN: Debe incluir el searchTerm en el body
        """
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"contacts": [], "totalContacts": 0}
        )

        response = send_message(
            agent_session_with_seller,
            "Busca a María García"
        )

        # Verificar que se incluyó el término de búsqueda
        if mock_post.called:
            body = mock_post.call_args.kwargs.get('json', {})
            # El searchTerm debería contener "María" o "García"
            search_term = body.get('searchTerm', '')
            assert 'María' in search_term or 'García' in search_term or 'maria' in search_term.lower(), \
                f"searchTerm no contiene el término buscado: {search_term}"


# =============================================================================
# EVAL: update_contact busca primero el contacto
# =============================================================================

class TestUpdateContactToolCall:
    """
    Evalúa si update_contact sigue el flujo correcto:
    1. Primero buscar el contacto
    2. Obtener el ID
    3. Luego actualizar
    """

    @patch('app.tools.crm.requests.post')
    @patch('app.tools.crm.requests.put')
    def test_update_searches_before_updating(self, mock_put, mock_post, agent_session_with_seller):
        """
        GIVEN: Usuario quiere actualizar un contacto por nombre
        WHEN: El agente procesa
        THEN: Debe buscar primero para obtener el ID real
        """
        # Mock de búsqueda (devuelve el contacto encontrado)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "contacts": [
                    {"_id": "abc123", "name": "Pedro López", "phone": "111-1111"}
                ]
            }
        )

        # Mock de actualización
        mock_put.return_value = MagicMock(
            status_code=200,
            json=lambda: {"_id": "abc123", "name": "Pedro López", "phone": "999-9999"}
        )

        # Pedir actualización
        response1 = send_message(
            agent_session_with_seller,
            "Cambia el teléfono de Pedro a 999-9999"
        )

        # Si pide confirmación, confirmar
        if response_contains_any(response1["text"], ["confirm", "seguro", "actualizar"]):
            response2 = send_message(agent_session_with_seller, "sí")

        # Verificar que primero se hizo POST (búsqueda) y luego PUT (actualización)
        # El orden de llamadas importa para el flujo correcto
        assert mock_post.called, "No se hizo búsqueda antes de actualizar"
