# Sales Assistant CRM

Asistente de ventas conversacional construido con Google ADK (Agent Development Kit) y Gemini. Permite a vendedores gestionar contactos del CRM mediante lenguaje natural.

> **Nota:** Este es un proyecto real en producción. El código está disponible para revisión, pero requiere credenciales de la API del CRM para ejecutarse. Si quieres adaptarlo a otro backend, revisa `app/tools/crm.py`.

## Qué hace

El agente actúa como asistente personal para vendedores, permitiendo:

- **Crear contactos** - Con validación de email y teléfono
- **Actualizar contactos** - Busca por nombre o ID automáticamente
- **Listar contactos** - Con búsqueda y paginación

Cada vendedor solo ve sus propios contactos (aislamiento multi-tenant).

## Stack

- **Google ADK** - Framework para agentes conversacionales
- **Gemini 2.5 Flash** - Modelo de lenguaje
- **Spicy CRM API** - Backend de contactos
- **Python 3.11+**

## Instalación

```bash
# Clonar el repo
git clone https://github.com/tu-usuario/sales-assistant-asp.git
cd sales-assistant-asp

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

## Configuración

Edita el archivo `.env` con tus credenciales:

```bash
GOOGLE_API_KEY=tu_api_key_de_gemini
TEST_SELLER_EMAIL=tu_email@ejemplo.com
SPICY_API_BASE_URL=https://api.spicytool.net/spicyapi/v1
SPICY_API_TOKEN=tu_token_del_crm
```

Para obtener tu API key de Gemini: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Uso

```bash
# Ejecutar el agente localmente
adk run app

# O usando make
make playground
```

El agente responde en español y pide confirmación antes de crear o modificar contactos.

## Estructura del proyecto

```
app/
├── agent.py        # Configuración del agente y modelo
├── callbacks.py    # Inyección dinámica del contexto del vendedor
├── prompt.py       # Instrucciones del agente
├── config.py       # Configuración general
└── tools/
    └── crm.py      # Funciones para interactuar con el CRM
```

## Cómo funciona

1. El vendedor inicia una conversación
2. El callback `before_model_callback` inyecta el email del vendedor en el prompt
3. El agente usa ese email en todas las llamadas al CRM
4. Cada vendedor solo accede a sus propios contactos

El prompt se hidrata dinámicamente en cada request, incluyendo el timestamp actual.

## Testing local

Para probar localmente, el agente usa `TEST_SELLER_EMAIL` del `.env` como fallback cuando no hay sesión activa.

```bash
make install && make playground
```

## Producción

Para producción con Vertex AI, descomentar las líneas en `agent.py`:

```python
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
```

Y deployar con:

```bash
gcloud config set project <tu-project-id>
make deploy
```

## Tests

```bash
make test
```

## Notas

- El agente siempre pide confirmación antes de crear o modificar contactos
- Las validaciones de email y teléfono están en `tools/crm.py`
- Los logs usan el módulo `logging` de Python

---

Generado con [agent-starter-pack](https://github.com/GoogleCloudPlatform/agent-starter-pack) v0.29.3
