import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Supabase credentials not found in .env file")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print(f"Connecting to Supabase at {supabase_url}...")

try:
    supabase.table("recipes").select("id").limit(1).execute()
    print("Database connection verified successfully!")
    
    print("\nYour Supabase database is properly configured and connected.")
except Exception as e:
    print(f"Error connecting to database: {e}")
    print("\nMake sure the following tables exist in your Supabase database:")
    print("- recipes: For storing recipe information")
    print("- generated_images: For storing information about generated images")
    exit(1)
