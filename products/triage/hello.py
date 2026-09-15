"""Smallest possible check that we can reach the model provider.

Deliberately separate from the classifier. If the classifier misbehaves later,
this having passed means the connection is not the problem, so the fault is in
the prompt or the code. Debugging one unknown at a time is the whole point.
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "anthropic/claude-haiku-4.5"

for name in ("AICREDITS_API_KEY", "AICREDITS_BASE_URL"):
    if not os.environ.get(name):
        print(f"Missing {name}. Check your .env file.")
        sys.exit(1)

client = OpenAI(
    base_url=os.environ["AICREDITS_BASE_URL"],
    api_key=os.environ["AICREDITS_API_KEY"],
)

response = client.chat.completions.create(
    model=MODEL,
    max_tokens=1000,
    messages=[{"role": "user", "content": "Reply with exactly: connection working"}],
)

print(response.choices[0].message.content)
print()
print(f"model returned: {response.model}")
print(f"finish reason:  {response.choices[0].finish_reason}")
print(f"input tokens:   {response.usage.prompt_tokens}")
print(f"output tokens:  {response.usage.completion_tokens}")