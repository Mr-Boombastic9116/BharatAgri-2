import sys
import os
import re
import importlib
from pathlib import Path
from sqlalchemy.orm import declarative_base

# Add backend to path
sys.path.insert(0, os.path.abspath('.'))

from backend.app.core.database import Base
import backend.app.models

# Import all models
import backend.app.models.user
import backend.app.models.farmer
import backend.app.models.agent
import backend.app.models.centre
import backend.app.models.booking
import backend.app.models.procurement
import backend.app.models.crop
import backend.app.models.inventory
import backend.app.models.logistics
import backend.app.models.price
import backend.app.models.queue
import backend.app.models.complaint
import backend.app.models.audit
import backend.app.models.ai
import backend.app.models.alert
import backend.app.models.geography

print("=== SQLAlchemy Models Audited ===")
model_tables = {}
for mapper in Base.registry.mappers:
    cls = mapper.class_
    tname = mapper.local_table.name
    cols = {c.name: str(c.type) for c in mapper.local_table.columns}
    model_tables[tname] = {
        "class": cls.__name__,
        "columns": cols
    }

print(f"Total SQLAlchemy Tables: {len(model_tables)}")
for tname, info in sorted(model_tables.items()):
    print(f"  Model: {info['class']} -> Table: `{tname}` ({len(info['columns'])} cols)")

# Parse SQL file
sql_file = Path('database/bharatagri_iteration2.sql')
sql_tables = {}
if sql_file.exists():
    with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
        sql_content = f.read()
    
    # Match CREATE TABLE statements
    matches = re.finditer(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([a-zA-Z0-9_]+)`?\s*\((.*?)\)\s*(?:ENGINE|;)', sql_content, re.DOTALL | re.IGNORECASE)
    for m in matches:
        tname = m.group(1)
        body = m.group(2)
        cols = {}
        for line in body.split('\n'):
            line = line.strip().rstrip(',')
            if not line or line.startswith('--') or line.startswith('/*'):
                continue
            col_match = re.match(r'^`?([a-zA-Z0-9_]+)`?\s+([a-zA-Z0-9_]+(?:\([^)]+\))?)', line)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                upper = col_name.upper()
                if upper not in ('PRIMARY', 'KEY', 'INDEX', 'UNIQUE', 'CONSTRAINT', 'FOREIGN', 'CHECK'):
                    cols[col_name] = col_type
        sql_tables[tname] = cols

print(f"\nTotal SQL Dump Tables: {len(sql_tables)}")

# Connect to local DB
import pymysql
local_tables = {}
try:
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='bharatagri_iteration2')
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        t_list = [r[0] for r in cur.fetchall()]
        for t in t_list:
            cur.execute(f"SHOW COLUMNS FROM `{t}`")
            local_tables[t] = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()
    print(f"Total Local MySQL Tables: {len(local_tables)}")
except Exception as e:
    print(f"Local DB connection failed: {e}")

print("\n" + "="*70)
print("COMPARING: SQLAlchemy Models vs SQL Dump (database/bharatagri_iteration2.sql)")
print("="*70)

missing_tables_in_sql = []
tables_with_missing_cols_in_sql = {}

for tname, minfo in sorted(model_tables.items()):
    if tname not in sql_tables:
        missing_tables_in_sql.append((tname, minfo['class']))
    else:
        sql_cols = sql_tables[tname]
        missing_cols = []
        for cname in minfo['columns']:
            if cname not in sql_cols:
                missing_cols.append(cname)
        if missing_cols:
            tables_with_missing_cols_in_sql[tname] = missing_cols

print(f"\nTables expected by SQLAlchemy Models but MISSING in SQL Dump ({len(missing_tables_in_sql)}):")
for tname, cname in missing_tables_in_sql:
    print(f"  - `{tname}` (Model: {cname})")

print(f"\nTables present in SQL Dump but MISSING columns expected by SQLAlchemy ({len(tables_with_missing_cols_in_sql)}):")
for tname, mcols in sorted(tables_with_missing_cols_in_sql.items()):
    print(f"  - `{tname}`: Missing columns: {mcols}")

print("\n" + "="*70)
print("COMPARING: SQLAlchemy Models vs Local MySQL DB")
print("="*70)

missing_tables_in_local = []
tables_with_missing_cols_in_local = {}

for tname, minfo in sorted(model_tables.items()):
    if tname not in local_tables:
        missing_tables_in_local.append((tname, minfo['class']))
    else:
        db_cols = local_tables[tname]
        missing_cols = []
        for cname in minfo['columns']:
            if cname not in db_cols:
                missing_cols.append(cname)
        if missing_cols:
            tables_with_missing_cols_in_local[tname] = missing_cols

print(f"\nTables expected by SQLAlchemy Models but MISSING in Local MySQL DB ({len(missing_tables_in_local)}):")
for tname, cname in missing_tables_in_local:
    print(f"  - `{tname}` (Model: {cname})")

print(f"\nTables present in Local DB but MISSING columns expected by SQLAlchemy ({len(tables_with_missing_cols_in_local)}):")
for tname, mcols in sorted(tables_with_missing_cols_in_local.items()):
    print(f"  - `{tname}`: Missing columns: {mcols}")

print("\n" + "="*70)
print("COMPARING: Local MySQL DB vs SQL Dump")
print("="*70)
extra_tables_in_local = [t for t in local_tables if t not in sql_tables]
print(f"Tables in Local DB but NOT in SQL Dump ({len(extra_tables_in_local)}):")
for t in sorted(extra_tables_in_local):
    print(f"  - `{t}` ({len(local_tables[t])} cols)")
