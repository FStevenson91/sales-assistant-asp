"""
Evals de Intent: ¿El agente entiende qué quiere el usuario?

Estas evaluaciones verifican que el agente interpreta correctamente
las intenciones del usuario (crear, actualizar, listar, etc.)
"""

import pytest
from .conftest import send_message, response_contains_any


# =============================================================================
# EVAL: El agente entiende intent de CREAR contacto
# =============================================================================

class TestCreateIntent:
    """
    Evalúa si el agente entiende cuando el usuario quiere CREAR un contacto.
    """

    def test_explicit_create_intent(self, agent_session_with_seller):
        """
        GIVEN: Usuario dice explícitamente "crear" o "agregar"
        WHEN: Enviamos el mensaje
        THEN: El agente debe entender y pedir los datos necesarios
        """
        response = send_message(
            agent_session_with_seller,
            "Quiero crear un nuevo contacto"
        )

        # El agente debería pedir los datos (nombre, teléfono, email)
        # o pedir confirmación si ya tiene los datos
        keywords_esperados = ["nombre", "teléfono", "email", "datos", "contacto"]

        assert response_contains_any(response["text"], keywords_esperados), \
            f"El agente no pareció entender el intent de crear. Respuesta: {response['text'][:200]}"

    def test_implicit_create_intent(self, agent_session_with_seller):
        """
        GIVEN: Usuario da datos sin decir "crear" explícitamente
        WHEN: Enviamos el mensaje
        THEN: El agente debería inferir que quiere crear un contacto
        """
        response = send_message(
            agent_session_with_seller,
            "Agrega a Juan Pérez, teléfono 555-1234, email juan@test.com"
        )

        # El agente debería pedir confirmación (porque tiene todos los datos)
        keywords_confirmacion = ["confirm", "seguro", "crear", "agregar", "correcto"]

        assert response_contains_any(response["text"], keywords_confirmacion), \
            f"El agente no pidió confirmación para crear. Respuesta: {response['text'][:200]}"


# =============================================================================
# EVAL: El agente entiende intent de LISTAR/BUSCAR contactos
# =============================================================================

class TestListIntent:
    """
    Evalúa si el agente entiende cuando el usuario quiere VER contactos.
    """

    def test_list_all_intent(self, agent_session_with_seller):
        """
        GIVEN: Usuario pide ver sus contactos
        WHEN: Enviamos el mensaje
        THEN: El agente debería mostrar la lista (o decir que no hay)
        """
        response = send_message(
            agent_session_with_seller,
            "Muéstrame mis contactos"
        )

        # El agente debería listar contactos o decir que no hay
        keywords_lista = ["contacto", "lista", "encontr", "no hay", "tienes"]

        assert response_contains_any(response["text"], keywords_lista), \
            f"El agente no pareció entender el intent de listar. Respuesta: {response['text'][:200]}"

    def test_search_intent(self, agent_session_with_seller):
        """
        GIVEN: Usuario busca un contacto específico
        WHEN: Enviamos el mensaje
        THEN: El agente debería buscar por ese término
        """
        response = send_message(
            agent_session_with_seller,
            "Busca a María"
        )

        # El agente debería buscar y mostrar resultados (o decir que no encontró)
        keywords_busqueda = ["María", "encontr", "result", "contacto", "no hay"]

        assert response_contains_any(response["text"], keywords_busqueda), \
            f"El agente no pareció buscar el contacto. Respuesta: {response['text'][:200]}"


# =============================================================================
# EVAL: El agente entiende intent de ACTUALIZAR contacto
# =============================================================================

class TestUpdateIntent:
    """
    Evalúa si el agente entiende cuando el usuario quiere MODIFICAR un contacto.
    """

    def test_update_intent(self, agent_session_with_seller):
        """
        GIVEN: Usuario quiere cambiar datos de un contacto
        WHEN: Enviamos el mensaje
        THEN: El agente debería buscar primero el contacto
        """
        response = send_message(
            agent_session_with_seller,
            "Cambia el teléfono de Pedro a 999-8888"
        )

        # El agente debería buscar a Pedro primero o pedir más info
        keywords_update = ["Pedro", "buscar", "encontr", "actualizar", "cambiar", "teléfono"]

        assert response_contains_any(response["text"], keywords_update), \
            f"El agente no pareció entender el intent de actualizar. Respuesta: {response['text'][:200]}"


# =============================================================================
# EVAL: El agente rechaza temas fuera de scope
# =============================================================================

class TestOutOfScopeIntent:
    """
    Evalúa si el agente rechaza temas que no son de CRM.
    """

    def test_rejects_offtopic(self, agent_session_with_seller):
        """
        GIVEN: Usuario pregunta algo fuera del tema CRM
        WHEN: Enviamos el mensaje
        THEN: El agente debería rechazar educadamente
        """
        response = send_message(
            agent_session_with_seller,
            "¿Cuál es la capital de Francia?"
        )

        # El agente NO debería responder sobre geografía
        # Debería redirigir al tema de CRM
        keywords_rechazo = ["CRM", "contacto", "ayudar", "asistente", "no puedo"]

        assert response_contains_any(response["text"], keywords_rechazo), \
            f"El agente respondió un tema fuera de scope. Respuesta: {response['text'][:200]}"
