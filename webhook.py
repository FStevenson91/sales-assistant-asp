import os
import httpx
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from google.genai.types import Content, Part

from app.tools import create_contact, update_contact, list_contacts
from app.prompt import agent_prompt
from app.config import AGENT_NAME, COMPANY

load_dotenv()

# Config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SPICY_API_TOKEN = os.getenv("SPICY_API_TOKEN")
SPICYTOOL_API_URL = os.getenv("SPICYTOOL_API_URL", "https://api.spicytool.net/api/webhooks/whatsApp/sendMessage")
APP_NAME = "sales_assistant"

# FastAPI app
webhook_app = FastAPI(title="Sales Assistant Webhook")

# Session service (in production, use a persistent one)
session_service = InMemorySessionService()


def create_agent_for_seller(seller_email: str) -> Agent:
    """Creates an agent with the seller_email hydrated in the prompt."""
    instruction = agent_prompt.format(
        agent_name=AGENT_NAME,
        company=COMPANY,
        seller_email=seller_email
    )
    
    return Agent(
        name="sales_assistant",
        model=Gemini(
            model="gemini-2.5-flash",
            api_key=GOOGLE_API_KEY,
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        tools=[create_contact, update_contact, list_contacts],
    )


async def send_whatsapp_response(phone: str, message: str, spicy_token: str):
    """Sends a message back to WhatsApp via SpicyTool."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SPICYTOOL_API_URL,
                headers={
                    "Authorization": spicy_token,
                    "Content-Type": "application/json"
                },
                json={
                    "phone": phone,
                    "message": message
                },
                timeout=30
            )
            print("📤 WhatsApp response sent: " + str(response.status_code))
            return response
    except Exception as e:
        print("❌ Error sending WhatsApp message: " + str(e))
        return None


async def get_or_create_session(user_id: str, seller_email: str):
    """Gets existing session or creates a new one."""
    try:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=user_id
        )
        if session:
            return session
    except:
        pass
    
    # Create new session
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=user_id,
        state={"seller_email": seller_email}
    )
    return session


async def run_agent(agent: Agent, user_id: str, message: str) -> str:
    """Runs the agent and returns the response."""
    runner = Runner(
        agent=agent,
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
    """Handles incoming WhatsApp messages from SpicyTool."""
    try:
        payload = await request.json()
        print("📥 Webhook received: " + str(payload))
        
        # Extract data from payload
        phone = payload.get("phone", "")
        message = payload.get("message", "")
        seller_email = payload.get("userEmail", "")
        spicy_token = payload.get("sppiccytokkenn", "") or SPICY_API_TOKEN
        
        # Validate required fields
        if not phone or not message:
            print("❌ Missing phone or message")
            return {"status": "error", "message": "Missing phone or message"}
        
        if not seller_email:
            print("⚠️ No seller_email in payload, using default")
            seller_email = os.getenv("TEST_SELLER_EMAIL", "vendedor@inmobiliaria.com")
        
        print("📱 Phone: " + phone)
        print("💬 Message: " + message)
        print("👤 Seller: " + seller_email)
        
        # Get or create session
        await get_or_create_session(user_id=phone, seller_email=seller_email)
        
        # Create agent for this seller
        agent = create_agent_for_seller(seller_email)
        
        # Run agent
        response = await run_agent(agent, user_id=phone, message=message)
        print("🤖 Agent response: " + response)
        
        # Send response back to WhatsApp
        await send_whatsapp_response(phone, response, spicy_token)
        
        return {
            "status": "success",
            "response": response
        }
        
    except Exception as e:
        print("❌ Webhook error: " + str(e))
        return {"status": "error", "message": str(e)}


@webhook_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Sales Assistant Webhook"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(webhook_app, host="0.0.0.0", port=8080)