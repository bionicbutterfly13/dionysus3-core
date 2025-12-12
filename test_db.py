import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("DATABASE_URL")
print(f"Connecting...")

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' LIMIT 5")
    tables = cur.fetchall()
    print(f"SUCCESS! Tables: {[t[0] for t in tables]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
