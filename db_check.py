import os
import sys
print("Script started", flush=True)

from dotenv import load_dotenv
load_dotenv()

import psycopg2

url = os.getenv("DATABASE_URL")
print(f"URL: {url[:60]}...", flush=True)

conn = psycopg2.connect(url)
print("Connected!", flush=True)
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' LIMIT 5")
print(cur.fetchall())
conn.close()
