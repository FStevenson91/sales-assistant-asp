
import os
import httpx
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from app.agent import root_agent

load_dotenv()

# Configuración
SPICY_API_TOKEN = os.getenv("SPICY_API_TOKEN")
SPICYTOOL_API_URL = os.getenv("SPICYTOOL_API_URL", "https://api.spicytool.net/api/webhooks/whatsApp/sendMessage")
TEST_SELLER_EMAIL = os.getenv("TEST_SELLER_EMAIL", "vendedor@inmobiliaria.com")
APP_NAME = "sales_assistant"

# Servicio de sesiones
session_service = InMemorySessionService()

# FastAPI app
webhook_app = FastAPI(title="Sales Assistant Webhook")


async def send_whatsapp_response(phone: str, message: str, spicy_token: str):
    """Envía respuesta de vuelta a WhatsApp."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SPICYTOOL_API_URL,
                headers={
                    "Authorization": spicy_token,
                    "Content-Type": "application/json"
                },
                json={"phone": phone, "message": message},
                timeout=30
            )
            print(f"📤 WhatsApp enviado: {response.status_code}")
            return response
    except Exception as e:
        print(f"❌ Error enviando WhatsApp: {e}")
        return None


async def get_or_create_session(user_id: str, seller_email: str):
    """
    Crea sesión con seller_email en el state.
    ⭐ EL CALLBACK LEE ESTO
    """
    try:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=user_id
        )
        if session:
            session.state["seller_email"] = seller_email
            return session
    except:
        pass
    
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=user_id,
        state={"seller_email": seller_email}  # ⭐ AQUÍ
    )
    print(f"✨ Sesión creada - seller: {seller_email}")
    return session


async def run_agent(user_id: str, message: str) -> str:
    """Ejecuta el agente con callback."""
    runner = Runner(
        agent=root_agent,  
        app_name=APP_NAME,
        session_service=session_service,
    )
    
    content = Content(role="user", parts=[Part(text=message)])
    
    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=user_id,
        new_message=content
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
    
    return response_text or "Lo siento, no pude procesar tu mensaje."


@webhook_app.post("/webhook")
async def webhook_handler(request: Request):
    """Maneja mensajes de WhatsApp via SpicyTool."""
    try:
        payload = await request.json()
        print(f"📥 Webhook: {payload}")
        
        phone = payload.get("phone", "")
        message = payload.get("message", "")
        seller_email = payload.get("userEmail", "") or TEST_SELLER_EMAIL
        spicy_token = payload.get("sppiccytokkenn", "") or SPICY_API_TOKEN
        
        if not phone or not message:
            return {"status": "error", "message": "Missing phone or message"}
        
        print(f"📱 Phone: {phone}")
        print(f"💬 Message: {message}")
        print(f"👤 Seller: {seller_email}")
        
        # Crear sesión con seller_email (el callback lo leerá)
        await get_or_create_session(user_id=phone, seller_email=seller_email)
        
        # Ejecutar agente (el callback inyecta seller_email)
        response = await run_agent(user_id=phone, message=message)
        print(f"🤖 Respuesta: {response}")
        
        await send_whatsapp_response(phone, response, spicy_token)
        
        return {"status": "success", "response": response}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "message": str(e)}


@webhook_app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(webhook_app, host="0.0.0.0", port=8080)