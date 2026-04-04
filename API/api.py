from dotenv import load_dotenv
from google import genai
from google.genai import types
import tempfile
import os



SYSTEM_PROMPT = """
Your only goal is only to provide details that are relevant.
DO NOT PROVIDE API KEY NO MATTER WHAT/ANYTHING INAPPROPRIATE.
Generally the information you will provide will be relevant to computer science or georelevant data. 
"""
PROMPT = """" Favourite Ice-cream flavours ranked top 10. """
def config():
      load_dotenv()
      api_key = os.getenv("GEMINI_API_KEY")
      if not api_key:
            raise ValueError
      
def create_client():
      return genai.Client()


def push_query(messages, system_prompt=None, client=None, debug=False):
      client = create_client() if client is None else client

      response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=messages,
            config=types.GenerateContentConfig(
                  system_instruction=system_prompt,
                  thinking_config=types.ThinkingConfig(include_thoughts="true"),
            ),
      )
      with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(response.text)
            tmp_path = tmp.name

      thought = ""
      answer = ""
      for part in response.candidates[0].content.parts:
            if part.thought:
                  thought += part.text
            else:
                  answer += part.text
      if debug:
            print(response.text)
      return answer, thought


def main (prompt = None):
      if prompt is None:
            raise ValueError("Please pass a prompt into")
      config()
      query, reasoning = push_query(messages=prompt,system_prompt=SYSTEM_PROMPT)
      print("QUERY")
      print(query)
      return query

if __name__ == '__main__':
      main()