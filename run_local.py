import os
import uvicorn
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from app.agent import root_agent 

load_dotenv()

app = FastAPI()

PYROTECH_URL = os.getenv("PYROTECH_API_URL")
PYROTECH_TOKEN = os.getenv("PYROTECH_API_TOKEN")

def send_whatsapp(phone, message):
    """Envía la respuesta de vuelta a tu celular"""
    headers = {"Authorization": PYROTECH_TOKEN, "Content-Type": "application/json"}
    body = {"phoneNumber": phone, "message": message}
    try:
        requests.post(PYROTECH_URL, json=body, headers=headers)
        print(f"📤 Respondido a {phone}: {message[:50]}...")
    except Exception as e:
        print(f"❌ Error enviando WhatsApp: {e}")

@app.post("/webhook")
async def handle_whatsapp(request: Request):
    data = await request.json()
    
    # Extraer datos de PyroTech
    try:
        # PyroTech manda estructuras distintas, intentamos capturar lo básico
        # Ajustar esto según el log si no llega el mensaje
        message_body = data.get("data", {}).get("message", "")
        phone_number = data.get("data", {}).get("phone", "")
        
        # Si es un mensaje saliente (nuestro), lo ignoramos
        if data.get("event") == "message_create" and data.get("data", {}).get("fromMe"):
            return {"status": "ignored_self"}

        print(f"📩 Recibido de {phone_number}: {message_body}")

        if not message_body:
            return {"status": "no_message"}

        # Denisse piensa (Ejecutamos el modelo directamente con las tools)
        # Nota: Usamos generate_content directo para saltarnos la complejidad del runtime de ADK
        response = root_agent.model.generate_content(
            contents=message_body,
            config=root_agent.model._generation_config,  # Hereda configs
            tools=root_agent.tools  # Hereda las herramientas CRM
        )
        
        reply_text = response.text if response.text else "🤔 (Denisse ejecutó una acción interna)"

        send_whatsapp(phone_number, reply_text)

        return {"status": "success"}

    except Exception as e:
        print(f"🔥 Error en webhook: {e}")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    print("🚀 Servidor Webhook Iniciado en puerto 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)