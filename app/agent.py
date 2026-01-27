# ruff: noqa
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.models import Gemini
from google.genai import types

from .config import AGENT_NAME, COMPANY
from .tools import create_contact, update_contact, list_contacts
from .callbacks import before_model_callback

load_dotenv()

my_api_key = os.getenv("GOOGLE_API_KEY")
if not my_api_key:
    raise ValueError("❌ GOOGLE_API_KEY no está configurada en .env")

# Commented out to allow for local testing without GCP credentials.
# import google.auth

# _, project_id = google.auth.default()
# os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
# os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
# os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        # En producción, usar Default Credentials u otro metodo seguro para manejar API keys:
        api_key=my_api_key,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="", # Vacío - hidratado dinámicamente before_model_callback con seller_email y timestamp
    tools=[create_contact, update_contact, list_contacts],
    before_model_callback=[before_model_callback],
)

app = App(root_agent=root_agent, name="app")
