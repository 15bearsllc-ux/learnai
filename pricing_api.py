"""
Exercise 3: FastAPI + Claude API Integration

This API endpoint takes a customer description and uses Claude
to extract structured pricing factors from it.
"""

from fastapi import FastAPI
from pydantic import BaseModel
import anthropic
import json

app = FastAPI()
client = anthropic.Anthropic()

class CustomerDescription(BaseModel):
    description: str

@app.post("/analyze-customer")
def analyze_customer(input_data: CustomerDescription):
    """
    Endpoint that analyzes a customer description and extracts pricing factors.
    """
    
    prompt = f"""
You are a pricing analyst. Extract structured pricing factors from this customer description.

Customer Description: {input_data.description}

Return ONLY a JSON object (no markdown, no code blocks, no other text) with these fields:
- segment: (enterprise, mid-market, or small-business)
- industry: (the industry if mentioned, otherwise "unspecified")
- seats: (estimated number of users, or 0 if unknown)
- modules: (list of features/modules requested, or empty list)
- confidence: (0.0 to 1.0 indicating confidence in the extraction)

Return ONLY the JSON object, nothing else.
"""
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    response_text = response_text.strip()
    
    try:
        factors = json.loads(response_text)
    except json.JSONDecodeError:
        factors = {
            "segment": "unknown",
            "industry": "unspecified",
            "seats": 0,
            "modules": [],
            "confidence": 0.0,
            "raw_response": response_text
        }
    
    return factors


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"message": "Pricing API is running. POST to /analyze-customer with a customer description."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)