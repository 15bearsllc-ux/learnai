"""
Exercise 5: Query Supabase + Analyze Comparable Deals

This script connects to your Supabase database and analyzes
pricing patterns in your quotes data.

What you're learning:
- Connecting to PostgreSQL/Supabase from Python
- Running SQL queries
- Analyzing data (averages, ranges, grouping)
- Outputting insights as JSON
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from statistics import mean, stdev

# Your Supabase connection string
# Replace with your actual connection string from Supabase
DATABASE_URL = "postgresql://postgres:BearLearnAI$15@db.twduvxkhwexrrmwxyzzy.supabase.co:5432/postgres"

def connect_to_database():
    """Connect to Supabase PostgreSQL database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✓ Connected to Supabase")
        return conn
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None

def query_all_quotes(conn):
    """Query all quotes from the database"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT q.quote_id, q.customer, q.price, t.name as tenant_name
                FROM quotes q
                JOIN tenants t ON q.tenant_id = t.tenant_id
                ORDER BY q.price
            """)
            quotes = cur.fetchall()
            print(f"✓ Retrieved {len(quotes)} quotes")
            return quotes
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return []

def analyze_quotes(quotes):
    """Analyze pricing patterns in quotes"""
    if not quotes:
        print("✗ No quotes to analyze")
        return {}
    
    # Extract prices
    prices = [float(q['price']) for q in quotes]
    
    # Basic statistics
    analysis = {
        "total_quotes": len(quotes),
        "average_price": round(mean(prices), 2),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
        "price_range": round(max(prices) - min(prices), 2),
    }
    
    # Calculate standard deviation if we have enough data
    if len(prices) > 1:
        analysis["std_deviation"] = round(stdev(prices), 2)
    
    # Group by tenant (comparable analysis)
    by_tenant = {}
    for quote in quotes:
        tenant = quote['tenant_name']
        if tenant not in by_tenant:
            by_tenant[tenant] = []
        by_tenant[tenant].append(float(quote['price']))
    
    analysis["by_tenant"] = {}
    for tenant, tenant_prices in by_tenant.items():
        analysis["by_tenant"][tenant] = {
            "count": len(tenant_prices),
            "average": round(mean(tenant_prices), 2),
            "min": round(min(tenant_prices), 2),
            "max": round(max(tenant_prices), 2),
        }
    
    # Price bands (quartiles)
    sorted_prices = sorted(prices)
    analysis["price_bands"] = {
        "budget": f"${sorted_prices[0]} - ${sorted_prices[len(sorted_prices)//4]}",
        "mid_market": f"${sorted_prices[len(sorted_prices)//4]} - ${sorted_prices[len(sorted_prices)//2]}",
        "premium": f"${sorted_prices[len(sorted_prices)//2]} - ${sorted_prices[-1]}",
    }
    
    print("✓ Analysis complete")
    return analysis

def save_results(analysis, filename="comps_analysis.json"):
    """Save analysis results to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"✓ Results saved to {filename}")
        return True
    except Exception as e:
        print(f"✗ Save failed: {e}")
        return False

def main():
    """Main workflow"""
    print("\n" + "="*60)
    print("COMPS ENGINE: Quote Analysis")
    print("="*60 + "\n")
    
    # Connect
    conn = connect_to_database()
    if not conn:
        return
    
    # Query
    quotes = query_all_quotes(conn)
    conn.close()
    
    # Analyze
    analysis = analyze_quotes(quotes)
    
    # Output
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    print(json.dumps(analysis, indent=2))
    
    # Save
    save_results(analysis)
    
    print("\n✓ Exercise 5 complete!")

if __name__ == "__main__":
    main()