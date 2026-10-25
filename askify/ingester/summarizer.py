
import os
import hashlib
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from groq import Groq


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def get_groq_client() -> Groq:
    """Create the Groq client on first use."""
    load_dotenv(ENV_PATH)

    api_key = os.getenv("GROQ_CLIENT")
    if not api_key:
        raise RuntimeError(
            "GROQ_CLIENT is missing. Add your Groq API key "
            "to the project's .env file."
        )

    return Groq(api_key=api_key)


@lru_cache(maxsize=1)
def get_client() -> Groq:
    """Cache the client so it is reused across summarization calls."""
    return get_groq_client()


def generate_file_summary(file: dict) -> dict:

    summary = get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a code summarizer. Given a file's content, write a concise technical summary of what the file does, its main functions, and its purpose.",
            },
            {
                "role": "user",
                "content": f"Summarize the following file:\nFilename: {file['source']}\n\nContent:\n{file['content']}",
            },
        ],
        max_tokens=512,
        temperature=0.1,
    )
    summary_text = summary.choices[0].message.content.strip()
    
    return {
        "content":f"FILE SUMMARY: {file['source']}\n\n{summary_text}",
        "source": file["source"],
        "type": file["type"],
        "hash": file["hash"],
        "source_hash": file["hash"]            
    }


def generate_project_summary(fil_summaries: list[dict])->dict:
    combined_summaries = "\n\n".join([f"{s['source']}:\n{s['content']}" for s in fil_summaries])
    
    summary = get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a project summarizer. Given summaries of all files in a project, write a concise technical summary of what the project does, its main components, and its purpose.",
            },
            {
                "role": "user",
                "content": f"Summarize the following project based on its file summaries:\n\n{combined_summaries}",
            },
        ],
        max_tokens=512,
        temperature=0.1,
    )
    summary_text = summary.choices[0].message.content.strip()
    
    return {
        "content":f"PROJECT SUMMARY:\n\n{summary_text}",
        "source": "project_summary",
        "type": "project_summary",
        "hash": hashlib.md5(summary_text.encode()).hexdigest(),
    }