"""
Quick test to see actual Supabase signup error
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(f"Supabase URL: {supabase_url}")
print(f"Supabase Key: {supabase_key[:20]}...")

supabase = create_client(supabase_url, supabase_key)

print("\n🧪 Testing signup...")

try:
    response = supabase.auth.sign_up({
        "email": "test@example.com",
        "password": "testpassword123"
    })
    
    print("✅ Signup successful!")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}")
    print(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")

