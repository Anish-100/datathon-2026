from dotenv import load_dotenv
from groq import Groq
from pathlib import Path
import os


SYSTEM_PROMPT = "Provide the most accurate answer possible."

def _get_client():
    # Load .env from project root (works locally; on Streamlit Cloud uses st.secrets via env vars)
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Add it to your .env file or Streamlit secrets.")
    return Groq(api_key=api_key)


def push_query(messages, system_prompt=None, client=None, debug=False):
    client = _get_client() if client is None else client
    system_prompt = system_prompt or SYSTEM_PROMPT

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": messages},
        ],
        temperature=0.3,
    )

    answer = response.choices[0].message.content.strip()
    if debug:
        print(answer)
    return answer, ""  # no separate "thought" with Groq; return empty string for compat


def main(prompt=None):
    if prompt is None:
        raise ValueError("Please enter a prompt.")
    query, _ = push_query(messages=prompt)
    print("QUERY")
    print(query)
    return query


if __name__ == '__main__':
    main()