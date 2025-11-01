import psycopg2

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="InboxGuardian10",
    host="db.pukuygcgtiedngxiracr.supabase.co",
    port="5432",
    sslmode="require"
)
print("✅ Connection successful")
conn.close()