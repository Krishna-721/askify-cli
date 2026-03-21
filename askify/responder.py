from groq import Groq
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = Groq(api_key=os.getenv("GROQ_CLIENT"))
def get_llama_response(query:str, chunks: list[str], max_tokens=250, temperature=0.4):

        context="\n\n".join(chunks)
        user_message=f"Context:\n {context}\n \nQuestion:\n {query}"

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are master of work and the one who helps students. You should act like a calm, senior candidate of the big company and help students and people solve their problems. Be precise and direct no shortcuts and bluffs, and you should admit when the context does not have enough information. Never give blind or biased answers. Always answer from the given and provided context only. If some other ir-relevant this has ben asked, and politely say i don't know"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return resp.choices[0].message.content.strip()
    
