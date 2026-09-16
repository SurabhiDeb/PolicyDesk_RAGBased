"""Does our gateway offer embeddings? Ask it, do not guess."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["AICREDITS_BASE_URL"],
    api_key=os.environ["AICREDITS_API_KEY"],
)

ids = sorted(m.id for m in client.models.list().data)
candidates = [i for i in ids if "embed" in i.lower() or "bge" in i.lower()]

print(f"{len(ids)} models total")
print(f"{len(candidates)} look like embedding models:")
for i in candidates:
    print(f"  {i}")

if not candidates:
    print("\nNone found by name. Trying a call anyway with a common id.")
    candidates = ["openai/text-embedding-3-small"]

print()
for model_id in candidates[:3]:
    try:
        r = client.embeddings.create(model=model_id, input="refund policy")
        print(f"WORKS  {model_id}  ({len(r.data[0].embedding)} numbers)")
    except Exception as e:
        print(f"FAILS  {model_id}  {type(e).__name__}: {str(e)[:120]}")