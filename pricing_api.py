"""
Exercise 6: Full-Stack Quote Assistant (Simplified)

This version focuses on Claude analysis without database queries.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import json
import os

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude client with explicit API key
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

client = anthropic.Anthropic(api_key=api_key)

class CustomerDescription(BaseModel):
    description: str

@app.post("/analyze-customer")
def analyze_customer(input_data: CustomerDescription):
    """
    Analyze customer and provide pricing recommendation.
    """
    
    # Step 1: Parse customer description
    parse_prompt = f"""
You are a pricing analyst. Extract structured pricing factors from this customer description.

Customer Description: {input_data.description}

Extract and return ONLY a JSON object (no other text) with these fields:
- segment: (enterprise, mid-market, or small-business)
- industry: (the industry if mentioned, otherwise "unspecified")
- seats: (estimated number of users, or 0 if unknown)
- modules: (list of features/modules requested, or empty list)
- confidence: (0.0 to 1.0 indicating how confident you are)

Return ONLY the JSON object, nothing else.
"""
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": parse_prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    # Strip markdown if present
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
            "confidence": 0.0
        }
    
    # Step 2: Get price recommendation from Claude
    recommendation_prompt = f"""
You are a B2B pricing analyst. Based on this customer profile, provide a price recommendation.

Customer Profile:
- Segment: {factors.get('segment', 'unknown')}
- Industry: {factors.get('industry', 'unspecified')}
- Seats: {factors.get('seats', 0)}
- Modules: {', '.join(factors.get('modules', [])) or 'standard'}

Market Context:
Based on typical B2B SaaS pricing:
- Small-business (< 100 seats): $2,000 - $5,000
- Mid-market (100-500 seats): $5,000 - $12,500
- Enterprise (500+ seats): $12,500+

Provide a price recommendation for this customer including:
1. Recommended price point
2. Price range
3. Brief rationale (2-3 sentences)

Format as a brief, actionable recommendation for a sales rep.
"""
    
    rec_message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[
            {"role": "user", "content": recommendation_prompt}
        ]
    )
    
    recommendation_text = rec_message.content[0].text.strip()
    
    # Estimate price based on segment
    if factors.get('segment') == 'enterprise':
        base_price = 15000
    elif factors.get('segment') == 'mid-market':
        base_price = 8000
    else:  # small-business or unknown
        base_price = 5000
    
    return {
        "segment": factors.get('segment', 'unknown'),
        "industry": factors.get('industry', 'unspecified'),
        "seats": factors.get('seats', 0),
        "modules": factors.get('modules', []),
        "confidence": factors.get('confidence', 0.0),
        "price_recommendation": recommendation_text,
        "price_range": {
            "low": int(base_price * 0.8),
            "recommended": int(base_price),
            "high": int(base_price * 1.2),
            "currency": "USD"
        }
    }

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"message": "Quote Assistant API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)