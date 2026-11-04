"""
Script tự động khởi tạo và nạp dữ liệu Star Schema Đa Kỳ vào PostgreSQL 18
Dự án: daklak-ethnic-socioeconomic-analytics
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from sqlalchemy import create_engine, text

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_USER = os.getenv('PGUSER', 'postgres')
DB_PASS = os.getenv('PGPASSWORD', '123456')
DB_HOST = os.getenv('PGHOST', 'localhost')
DB_PORT = os.getenv('PGPORT', '5432')
DB_NAME = 'daklak_socioeconomic'

print(f"=== KẾT NỐI POSTGRESQL TẠI {DB_HOST}:{DB_PORT} (User: {DB_USER}) ===")

# 1. Tạo Database nếu chưa tồn tại
conn_admin = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    dbname='postgres'
)
conn_admin.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor_admin = conn_admin.cursor()

cursor_admin.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
if not cursor_admin.fetchone():
    cursor_admin.execute(f"CREATE DATABASE {DB_NAME} WITH ENCODING 'UTF8';")
    print(f"✅ Đã tạo mới cơ sở dữ liệu: {DB_NAME}")
else:
    print(f"ℹ️ Cơ sở dữ liệu {DB_NAME} đã tồn tại.")

cursor_admin.close()
conn_admin.close()

# 2. Kết nối đến CSDL daklak_socioeconomic và thực thi DDL Schema
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    dbname=DB_NAME
)
cursor = conn.cursor()

ddl_file = 'warehouse/schema/postgres_star_schema.sql'
with open(ddl_file, 'r', encoding='utf-8') as f:
    ddl_sql = f.read()

cursor.execute(ddl_sql)
conn.commit()
print("✅ Đã thực thi DDL Star Schema Đa Kỳ (Tables, Foreign Keys, Indexes, Views)!")

cursor.close()
conn.close()

# 3. Nạp dữ liệu vào các bảng qua SQLAlchemy
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

tables_to_load = [
    ('dim_ky_baocao', 'data/processed/dim_ky_baocao.parquet', None),
    ('dim_diaban', 'data/processed/dim_diaban_master.csv', ['ma_xa', 'ten_xa', 'loai_hinh', 'ma_huyen', 'ten_huyen', 'so_thon', 'tinh']),
    ('dim_dantoc', 'data/processed/dim_dantoc_master.csv', ['ma_dantoc', 'ten_dantoc', 'ten_goc_bieu_mau', 'nhom_nguon_goc', 'la_dtts_it_nguoi']),
    ('dim_chinhsach_canthiep', 'data/processed/dim_chinhsach_canthiep.parquet', None),
    ('dim_chitieu_kehoach_ngansach', 'data/processed/dim_chitieu_kehoach_ngansach.parquet', None),
    ('fact_hatang_xa', 'data/processed/fact_hatang_xa.parquet', None),
    ('fact_danso_huyen_dantoc', 'data/processed/fact_danso_huyen_dantoc.parquet', None),
    ('fact_giaoduc_dantoc', 'data/processed/fact_giaoduc_dantoc.parquet', None),
    ('fact_laodong_dantoc', 'data/processed/fact_laodong_dantoc.parquet', None),
    ('fact_dantocthiet_yeu_huyen', 'data/processed/fact_dantocthiet_yeu_huyen.parquet', None),
    ('fact_nhao_dantoc', 'data/processed/fact_nhao_dantoc.parquet', None),
    ('fact_mucsinh_dantoc', 'data/processed/fact_mucsinh_dantoc.parquet', None),
    ('fact_nhankhau_dantoc', 'data/processed/fact_nhankhau_dantoc.parquet', None),
    ('fact_matuy_hiv_xa', 'data/processed/fact_matuy_hiv_xa.parquet', None),
    ('fact_trinhdo_cmkt_dantoc', 'data/processed/fact_trinhdo_cmkt_dantoc.parquet', None),
    ('fact_datsanxuat_dantoc', 'data/processed/fact_datsanxuat_dantoc.parquet', None),
    ('fact_tindung_dantoc', 'data/processed/fact_tindung_dantoc.parquet', None),
]

print("\n=== ĐANG NẠP DỮ LIỆU VÀO POSTGRESQL SCHEMA: daklak_analytics ===")
with engine.connect() as con:
    for tbl_name, file_path, cols in tables_to_load:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        else:
            df = pd.read_parquet(file_path)
            
        if cols:
            df = df[cols]
            
        df.to_sql(tbl_name, con, schema='daklak_analytics', if_exists='append', index=False)
        count = con.execute(text(f"SELECT COUNT(*) FROM daklak_analytics.{tbl_name}")).scalar()
        print(f"  -> {tbl_name:<30}: {count:>5} dòng")
    con.commit()

print("\n🎉 Nạp toàn bộ dữ liệu Đa Kỳ vào PostgreSQL hoàn tất 100%!")
