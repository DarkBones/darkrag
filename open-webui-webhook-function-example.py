"""
title: Rag Webhook
author: DarkBones
author_url: https://github.com/DarkBones
version: 0.1
"""

from typing import Optional

import requests
from pydantic import BaseModel, Field

RAG_TEMPLATE = (
    "**Generate Response to User Query**\n"
    "\n"
    "**Step 1: Parse Context Information**\n"
    "Extract and utilize relevant knowledge from the provided context "
    "within `<context></context>` XML tags.\n"
    "\n"
    "**Step 2: Analyze User Query**\n"
    "Carefully read and comprehend the user's query, pinpointing the key "
    "concepts, entities, and intent behind the question.\n"
    "\n"
    "**Step 3: Determine Response**\n"
    "If the answer to the user's query can be directly inferred from the "
    "context information, provide a concise and accurate response in the "
    "same language as the user's query.\n"
    "\n"
    "**Step 4: Handle Uncertainty**\n"
    "If the answer is not clear, ask the user for clarification to ensure "
    "an accurate response.\n"
    "\n"
    "**Step 5: Avoid Context Attribution**\n"
    "When formulating your response, do not indicate that the information "
    'was derived from the context or from "The information provided".\n'
    "\n"
    "**Step 6: Respond in User's Language and tone**\n"
    "Maintain consistency by ensuring the response is in the same language "
    "and tone as the user's query.\n"
    "\n"
    "**Step 7: Provide Response**\n"
    "Generate a clear, concise, and informative response to the user's "
    "query, adhering to the guidelines outlined above.\n"
    "Be aware that some or all of the information within "
    "`<context></context>` might not be relevant. Irrelevant data should "
    "be ignored.\n"
    "\n"
    "<context>\n"
    "{{knowledge}}\n"
    "</context>\n"
    "\n"
    "Again, don't mention you received this context or that this information "
    'has been "provided" to you.'
)

REG_TEMPLATE_DESCRIPTION = (
    "The prompt surrounding the RAG knowledge. The tag {{knowledge}} will be "
    "replaced with the actualy knowledge retrieved."
)

USER_MESSAGES_TO_PROMT = 5


class Filter:
    """
    RAG filter that intercepts user messages and retrieves data via a webhook
    """

    class Valves(BaseModel):
        """
        Global valves
        """

        priority: int = Field(
            default=0,
            description="Priority level for the filter operations.",
        )
        webhook_url: str = Field(
            default="http://n8n:5678/webhook/rag",
            description="Where RAG requests will be sent to.",
        )
        rag_template: str = Field(
            default=RAG_TEMPLATE,
            description=REG_TEMPLATE_DESCRIPTION,
        )
        user_messages_to_prompt: int = Field(
            default=USER_MESSAGES_TO_PROMT,
            description="Number of user messages to include when retrieving data"
        )

    class UserValves(BaseModel):
        """
        User valves
        """

        webhook_url: str = Field(
            default="http://n8n:5678/webhook-test/rag",
            description="Where RAG requests will be sent to.",
        )

    def __init__(self):
        # Initialize 'valves'
        self.valves = self.Valves()

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Send the user's prompt to the webhook for RAG retrieval.
        """

        print(f"inlet:{__name__}")
        print(f"inlet:body:{body}")
        print(f"inlet:user:{__user__}")

        if not __user__.get("role", "admin") in ["user", "admin"]:
            return None

        messages = body.get("messages", [])
        user_messages = [
            message["content"]
            for message in messages
            if message.get("role") in ["user", "admin"]
        ]

        nr_of_messages = self.valves.user_messages_to_prompt * -1
        user_message = "\n---\n".join(user_messages[nr_of_messages:])

        if user_message:
            try:
                # 1. Send POST request to webhook
                user_name = __user__.get("name", "User")
                response = requests.post(
                    self.valves.webhook_url,
                    json={"prompt": f"{user_name}: {user_message}"},
                )
                response.raise_for_status()

                # 2. Get knowledge from webhook response
                knowledge = response.json()
                # raise (Exception(webhook_data))
                # knowledge = webhook_data.get("knowledge")
                # 3. Insert knowledge as system message before the last user message
                system_message = {
                    "role": "system",
                    "content": self.valves.rag_template.replace(
                        "{{knowledge}}", str(knowledge)
                    ),
                }

                if knowledge:
                    # Find the index of the last user message
                    last_user_idx = len(messages) - 1
                    for idx, msg in reversed(list(enumerate(messages))):
                        if msg.get("role") in ["user", "admin"]:
                            last_user_idx = idx
                            break

                    # Insert the system message before the last user message
                    messages.insert(last_user_idx, system_message)
                    body["messages"] = messages

            except requests.RequestException as e:
                raise (Exception(f"Error making webhook request: {e}"))
            except Exception as e:
                raise (Exception(f"Error processing webhook response: {e}"))

        return body
