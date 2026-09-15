"""Ask the provider which models it actually offers.

Model IDs differ between gateways, so we query rather than assume.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["AICREDITS_BASE_URL"],
    api_key=os.environ["AICREDITS_API_KEY"],
)

names = sorted(model.id for model in client.models.list().data)

print(f"{len(names)} models available")
print()
print("Models with 'claude' in the name:")
for name in names:
    if "claude" in name.lower():
        print(f"  {name}")