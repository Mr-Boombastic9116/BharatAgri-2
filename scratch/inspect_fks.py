import pymysql
from backend.app.core.config import settings

conn = pymysql.connect(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME
)
cur = conn.cursor()
cur.execute("""
    SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA=%s AND REFERENCED_TABLE_NAME IS NOT NULL
""", (settings.DB_NAME,))
fks = cur.fetchall()
print(f"Total Foreign Keys in {settings.DB_NAME}: {len(fks)}")
for fk in fks[:20]:
    print(" ", fk)
conn.close()
