import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='daklak_socioeconomic', user='postgres', password='123456')
cur = conn.cursor()
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'daklak_analytics' AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = cur.fetchall()
print(f"Total base tables in daklak_analytics: {len(tables)}")
for t in tables:
    cur.execute(f"SELECT count(*) FROM daklak_analytics.{t[0]}")
    cnt = cur.fetchone()[0]
    print(f" - {t[0]}: {cnt} rows")

cur.execute("""
    SELECT table_name 
    FROM information_schema.views 
    WHERE table_schema = 'daklak_analytics'
    ORDER BY table_name;
""")
views = cur.fetchall()
print(f"Total views in daklak_analytics: {len(views)}")
for v in views:
    print(f" - view: {v[0]}")

cur.close()
conn.close()
