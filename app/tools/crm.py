
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("SPICY_API_BASE_URL", "https://api.spicytool.net/spicyapi/v1")
SPICY_API_TOKEN = os.getenv("SPICY_API_TOKEN")


# Funciones de validación
def is_valid_email(email: str) -> bool:
    """Valida formato de email."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_phone(phone: str) -> bool:
    """Valida teléfono (al menos 7 dígitos)."""
    if not phone:
        return False
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 7


def is_valid_mongo_id(id_str: str) -> bool:
    """Valida si es un ID de MongoDB válido (24 caracteres hex)."""
    if not isinstance(id_str, str) or len(id_str) != 24:
        return False
    return all(c in '0123456789abcdefABCDEF' for c in id_str)


def _search_contact_internal(seller_email, term):
    """Busca un contacto internamente para obtener su ID real."""
    try:
        url = API_BASE_URL + "/contacts?page=1&limit=20"
        headers = {
            "Authorization": SPICY_API_TOKEN,
            "Content-Type": "application/json",
            "x-user-email": seller_email
        }
        body = {
            "userEmail": seller_email,
            "searchTerm": str(term).strip()
        }
        
        response = requests.post(url, headers=headers, json=body, timeout=10)
        data = response.json()
        
        if isinstance(data, dict):
            contacts = data.get('contacts') or data.get('docs') or []
        else:
            contacts = data
        
        if contacts and isinstance(contacts, list) and len(contacts) > 0:
            return contacts[0]
        
        return None
    except Exception as e:
        print("❌ Exception:", str(e))
        return None


def create_contact(seller_email: str, name: str, phone_number: str, email: str) -> dict:
    """Creates a new contact. Name, Phone AND Email are required."""
    try:
        # Validaciones
        if not name or not name.strip():
            return {"status": "error", "message": "El nombre no puede estar vacío."}
        
        if not is_valid_email(email):
            return {"status": "error", "message": f"Email inválido: {email}"}
        
        if not is_valid_email(seller_email):
            return {"status": "error", "message": f"Seller email inválido: {seller_email}"}
        
        if not is_valid_phone(phone_number):
            return {"status": "error", "message": f"Teléfono inválido: {phone_number}"}
        
        url = API_BASE_URL + "/contact"
        headers = {
            "Authorization": SPICY_API_TOKEN,
            "Content-Type": "application/json",
            "x-user-email": seller_email
        }
        
        body = {
            "name": name.strip(),
            "phoneNumber": phone_number,
            "userEmail": seller_email,
            "email": email 
        }
        
        response = requests.post(url, headers=headers, json=body, timeout=10)
        
        if response.status_code >= 400:
            return {"status": "error", "message": "Error API: " + str(response.text)}

        return {
            "status": "success",
            "message": "Contacto creado exitosamente.",
            "contact": response.json()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_contact(seller_email: str, identifier: str, name: str = None, email: str = None, phone_number: str = None) -> dict:
    """Updates a contact."""
    try:
        # Validar email si se proporciona
        if email and not is_valid_email(email):
            return {"status": "error", "message": f"Email inválido: {email}"}
        
        # Validar teléfono si se proporciona
        if phone_number and not is_valid_phone(phone_number):
            return {"status": "error", "message": f"Teléfono inválido: {phone_number}"}
        
        # Si es un ID de MongoDB válido, usarlo directo
        if is_valid_mongo_id(identifier):
            real_db_id = identifier
        else:
            # Buscar el contacto por nombre/email/teléfono
            real_contact = _search_contact_internal(seller_email, identifier)
            
            if not real_contact:
                return {
                    "status": "not_found",
                    "message": "No se encontró el contacto '" + str(identifier) + "' para actualizar."
                }
            
            real_db_id = real_contact.get('_id') or real_contact.get('id')
        
        if not real_db_id:
            return {"status": "error", "message": "Error crítico: El contacto no tiene ID."}

        url = API_BASE_URL + "/contact/" + str(real_db_id)
        
        headers = {
            "Authorization": SPICY_API_TOKEN,
            "Content-Type": "application/json",
            "x-user-email": seller_email
        }
        
        body = {"userEmail": seller_email}
        if name: body["name"] = name.strip()
        if email: body["email"] = email
        if phone_number: body["phoneNumber"] = phone_number
        
        response = requests.put(url, headers=headers, json=body, timeout=10)
        
        return {
            "status": "success",
            "message": "Actualizado correctamente",
            "contact": response.json()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_contacts(seller_email: str, search_term: str = None, page: int = 1, limit: int = 5) -> dict:
    """Lists contacts."""
    try:
        url = API_BASE_URL + "/contacts?page=" + str(page) + "&limit=" + str(limit)
        headers = {
            "Authorization": SPICY_API_TOKEN,
            "Content-Type": "application/json",
            "x-user-email": seller_email
        }
        body = {"userEmail": seller_email}
        if search_term:
            body["searchTerm"] = search_term
        
        response = requests.post(url, headers=headers, json=body, timeout=10)
        data = response.json()
        
        if isinstance(data, dict):
            contacts_list = data.get('contacts') or data.get('docs') or []
        else:
            contacts_list = data
        
        return {
            "status": "success",
            "contacts": contacts_list,
            "total": data.get('totalContacts', len(contacts_list)),
            "page": page,
            "limit": limit
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}