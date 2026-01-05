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

from .tools import create_contact, update_contact, list_contacts
# from .callbacks import before_model_callback
from .prompt import agent_prompt
from .config import AGENT_NAME, COMPANY

load_dotenv()

my_api_key = os.getenv("GOOGLE_API_KEY")

# Commented out to allow for local testing without GCP credentials.
# import google.auth

# _, project_id = google.auth.default()
# os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
# os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
# os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# hydrate prompt with a test seller email for local testing
TEST_SELLER_EMAIL = os.getenv("TEST_SELLER_EMAIL", "vendedor@inmobiliaria.com")

instruction = agent_prompt.format(
    agent_name=AGENT_NAME,
    company=COMPANY,
    seller_email=TEST_SELLER_EMAIL
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        # model="gemini-3-flash-preview", it could not exist or fail:
        model="gemini-2.5-flash",
        # At production, use Default Credentials or another secure method to manage API keys:
        api_key=my_api_key,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction, # instruction will be set in callback if we use before_model_callback
    tools=[create_contact, update_contact, list_contacts],
    # before_model_callbacks=[before_model_callback],
)

app = App(root_agent=root_agent, name="app")
