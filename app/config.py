AGENT_NAME = "Denisse"
COMPANY = "Inmobiliaria ABC"

CONTACT_FIELDS = {
    "required": ["name", "phone_number", "email"],  
    "optional": [],  
}

ALLOWED_ACTIONS = [
    "create_contact",
    "update_contact",
    "list_contacts",
]