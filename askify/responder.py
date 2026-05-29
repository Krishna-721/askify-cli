from groq import Groq
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = Groq(api_key=os.getenv("GROQ_CLIENT"))


def get_llama_response(
    query: str,
    chunks: list[str],
    metadata: list[dict],
    max_tokens=4028,
    temperature=0.4,
):
    source_context = ""

    for chunk, meta in zip(chunks, metadata):
        source_context += f"\nSOURCE: {meta['source']}\n{chunk}\n"

    user_message = f"""
Context:

{source_context}

Question:
{query}
"""

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
                    You are Askify, a retrieval-augmented assistant.

                    Answer ONLY using the provided context.

                    If the answer cannot be found in the context,
                    say "I don't know based on the indexed files."

                    Rules:
                    - Do not invent files.
                    - Do not invent functions.
                    - Do not invent behavior.
                    - Mention relevant source filenames when useful.
                    - Be concise and technically accurate.
                    """,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    answer = resp.choices[0].message.content.strip()

    sources = sorted(set(m["source"] for m in metadata))

    citation_block = "\n\nSources:\n"

    for source in sources:
        citation_block += f"- {source}\n"

    return answer + citation_block
