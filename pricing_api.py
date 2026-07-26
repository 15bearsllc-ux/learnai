"""
Exercise 6: Full-Stack Quote Assistant with Supabase Integration

This version:
1. Queries Supabase for comparable deals
2. Analyzes pricing patterns in the comps
3. Passes comparable data to Claude
4. Returns pricing recommendations based on real data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from statistics import mean, stdev

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

# Initialize Claude client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

client = anthropic.Anthropic(api_key=api_key)

# Supabase connection string
DATABASE_URL = "postgresql://postgres:BearLearnAI$15@db.twduvxkhwexrrmwxyzzy.supabase.co:5432/postgres"

class CustomerDescription(BaseModel):
    description: str

def get_comparable_deals():
    """Query Supabase for comparable deals"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT q.customer, q.price, t.name as tenant_name
                FROM quotes q
                JOIN tenants t ON q.tenant_id = t.tenant_id
                ORDER BY q.price
            """)
            quotes = cur.fetchall()
            conn.close()
            
            if not quotes:
                return {
                    "total": 0,
                    "average_price": 0,
                    "min_price": 0,
                    "max_price": 0,
                    "std_deviation": 0,
                    "deals": []
                }
            
            # Calculate statistics
            prices = [float(q['price']) for q in quotes]
            
            analysis = {
                "total": len(quotes),
                "average_price": round(mean(prices), 2),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2),
                "deals": [
                    {"customer": q['customer'], "price": float(q['price'])}
                    for q in quotes
                ]
            }
            
            # Calculate std dev if we have enough data
            if len(prices) > 1:
                analysis["std_deviation"] = round(stdev(prices), 2)
            
            return analysis
    except Exception as e:
        print(f"Database error: {e}")
        return {
            "total": 0,
            "average_price": 0,
            "min_price": 0,
            "max_price": 0,
            "error": str(e),
            "deals": []
        }

@app.post("/analyze-customer")
def analyze_customer(input_data: CustomerDescription):
    """
    Full-stack quote analysis:
    1. Query comparable deals from Supabase
    2. Parse customer with Claude
    3. Claude recommends price based on comps
    4. Return recommendation
    """
    
    # Step 1: Get comparable deals from database
    comps = get_comparable_deals()
    
    # Step 2: Parse customer description
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
    
    # Step 3: Build comparable data summary
    comps_summary = f"""
Market Comparable Data:
- Total Deals Analyzed: {comps.get('total', 0)}
- Average Deal Size: ${comps.get('average_price', 0):,.2f}
- Price Range: ${comps.get('min_price', 0):,.2f} - ${comps.get('max_price', 0):,.2f}
- Standard Deviation: ${comps.get('std_deviation', 0):,.2f}

Recent Comparable Deals:
"""
    
    for deal in comps.get('deals', [])[:10]:  # Show last 10 deals
        comps_summary += f"\n- {deal['customer']}: ${deal['price']:,.2f}"
    
    # Step 4: Get price recommendation based on comps
    recommendation_prompt = f"""
You are a B2B pricing analyst. Based on comparable deals and this customer profile, provide a price recommendation.

Customer Profile:
- Segment: {factors.get('segment', 'unknown')}
- Industry: {factors.get('industry', 'unspecified')}
- Seats: {factors.get('seats', 0)}
- Modules: {', '.join(factors.get('modules', [])) or 'standard'}

{comps_summary}

Based on the actual comparable deals and customer profile, provide:
1. A recommended price point
2. The acceptable price range
3. Brief rationale (2-3 sentences) explaining your recommendation

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
    
    # Calculate price range based on comparables and customer segment
    if comps.get('total', 0) > 0:
        base_price = comps.get('average_price', 5000)
    else:
        base_price = 5000
    
    # Adjust based on segment
    if factors.get('segment') == 'enterprise':
        multiplier = 1.6
    elif factors.get('segment') == 'mid-market':
        multiplier = 1.1
    else:  # small-business
        multiplier = 0.7
    
    recommended_price = round(base_price * multiplier, 0)
    low_price = round(recommended_price * 0.85, 0)
    high_price = round(recommended_price * 1.15, 0)
    
    return {
        "segment": factors.get('segment', 'unknown'),
        "industry": factors.get('industry', 'unspecified'),
        "seats": factors.get('seats', 0),
        "modules": factors.get('modules', []),
        "confidence": factors.get('confidence', 0.0),
        "comparable_deals": {
            "total": comps.get('total', 0),
            "average_price": comps.get('average_price', 0),
            "price_range": f"${comps.get('min_price', 0):,.0f} - ${comps.get('max_price', 0):,.0f}"
        },
        "price_recommendation": recommendation_text,
        "price_range": {
            "low": int(low_price),
            "recommended": int(recommended_price),
            "high": int(high_price),
            "currency": "USD"
        }
    }

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"message": "Quote Assistant API with Supabase is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)