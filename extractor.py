import os
import json
from groq import Groq
from dotenv import load_dotenv

def extract_parameters(prompt: str) -> dict:
    load_dotenv()
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    system_prompt = """
    You are an expert real estate and business location scout. 
    A user will give you a description of a business they want to open.
    Your job is to extract the ideal demographic and geographic parameters for this business.
    
    You must return a JSON object with the following exact structure:
    {
      "target_median_income": integer (e.g. 50000 to 150000),
      "target_median_age": float (e.g. 25.0 to 55.0),
      "target_home_value": integer (e.g. 300000 to 1500000),
      "commercial_focus": boolean (true if the business needs a highly commercial area, false if residential/neighborhood),
      "high_education_required": boolean (true if the business specifically targets highly educated populations),
      "importance_weights": {
          "income": float (0.0 to 1.0),
          "age": float (0.0 to 1.0),
          "home_value": float (0.0 to 1.0),
          "commercial": float (0.0 to 1.0),
          "education": float (0.0 to 1.0)
      }
    }
    
    Make the weights sum roughly to 1.0 or 1.5, prioritizing the most critical factors for the business described.
    Make sure to provide reasonable estimates based on the business type. 
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.1-8b-instant",
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    response = chat_completion.choices[0].message.content
    return json.loads(response)

if __name__ == "__main__":
    # Test script
    res = extract_parameters("I want to open a high-end luxury coffee shop targeting young affluent professionals in a bustling commercial area.")
    print(json.dumps(res, indent=2))
