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

def add_column_if_missing(table, column, col_type):
    cur.execute(f"SHOW COLUMNS FROM `{table}` LIKE '{column}'")
    if not cur.fetchone():
        print(f"Adding column `{column}` ({col_type}) to `{table}`...")
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_type}")
    else:
        print(f"Column `{column}` already exists in `{table}`.")

# Procurement centres
add_column_if_missing("procurement_centres", "daily_capacity_farmers", "INT DEFAULT 120")
add_column_if_missing("procurement_centres", "weighing_machines", "INT DEFAULT 2")
add_column_if_missing("procurement_centres", "quality_stations", "INT DEFAULT 2")
add_column_if_missing("procurement_centres", "staff_count", "INT DEFAULT 10")

# Farmers
add_column_if_missing("farmers", "primary_crop", "VARCHAR(100) NULL")
add_column_if_missing("farmers", "land_acres", "DECIMAL(8,2) NULL")
add_column_if_missing("farmers", "expected_quantity_quintals", "DECIMAL(10,2) NULL")
add_column_if_missing("farmers", "distance_to_nearest_centre_km", "DECIMAL(8,2) NULL")
add_column_if_missing("farmers", "preferred_language", "VARCHAR(20) DEFAULT 'hi'")
add_column_if_missing("farmers", "mobile_verified", "TINYINT(1) DEFAULT 1")

conn.commit()
conn.close()
print("Column migration completed successfully.")
