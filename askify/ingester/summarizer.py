import os
from dotenv import load_dotenv
from groq import Groq
import hashlib

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_CLIENT"))

def generate_file_summary(file: dict) -> dict:

    summary = client.chat.completions.create(
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
    }


def generate_project_summary(fil_summaries: list[dict])->dict:
    combined_summaries = "\n\n".join([f"{s['source']}:\n{s['content']}" for s in fil_summaries])
    
    summary = client.chat.completions.create(
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