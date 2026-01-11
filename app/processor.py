import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

async def process_pdf(pdf_bytes):
    # Sends PDF directly to Gemini
    prompt = "Extract the Title, Author, and a 3-sentence summary of this document. Return the result strictly as a JSON object with keys: 'title', 'author', and 'summary'."
    
    response = model.generate_content([
        {'mime_type': 'application/pdf', 'data': pdf_bytes},
        prompt
    ])
    
    # Clean up the response (removes ```json ... ``` if Gemini adds it)
    text_response = response.text
    clean_json = re.sub(r'```json|```', '', text_response).strip()
    
    try:
        return json.loads(clean_json)
    except:
        return {"title": "Error", "author": "Error", "summary": "Could not parse AI response."}