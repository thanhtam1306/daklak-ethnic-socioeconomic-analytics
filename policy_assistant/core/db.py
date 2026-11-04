"""
==============================================================================
MODULE: DATABASE CONNECTION & QUERY EXECUTION (PostgreSQL 18 + DuckDB Fallback)
File: policy_assistant/core/db.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import psycopg2
from psycopg2 import pool
import duckdb

from .sql_guardrails import validate_and_sanitize_sql, SQLSecurityError

logger = logging.getLogger("PolicyAssistant.DB")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Cấu hình CSDL PostgreSQL 18
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "123456")
PG_NAME = os.getenv("PGDATABASE", "daklak_socioeconomic")
PG_SCHEMA = os.getenv("PGSCHEMA", "daklak_analytics")

# Cấu hình DuckDB
DUCKDB_PATH = os.getenv("DUCKDB_PATH", os.path.join("warehouse", "daklak_socioeconomic.duckdb"))
FORCE_DUCKDB = (os.getenv("DB_BACKEND", "").lower() == "duckdb") or (os.getenv("RENDER") is not None and "PGHOST" not in os.environ)

_pg_pool: Optional[pool.SimpleConnectionPool] = None


def get_pg_pool() -> Optional[pool.SimpleConnectionPool]:
    """Khởi tạo hoặc trả về connection pool PostgreSQL 18."""
    global _pg_pool
    if _pg_pool is None or _pg_pool.closed:
        try:
            _pg_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASS,
                dbname=PG_NAME,
                options=f"-c search_path={PG_SCHEMA},public"
            )
            logger.info("Khởi tạo thành công PostgreSQL 18 Connection Pool (schema: %s)", PG_SCHEMA)
        except Exception as e:
            logger.warning("Không thể kết nối PostgreSQL 18 (%s). Sẽ sử dụng DuckDB làm fallback.", e)
            _pg_pool = None
    return _pg_pool


def get_db_connection() -> Tuple[str, Any]:
    """
    Lấy kết nối CSDL (ưu tiên PostgreSQL 18, fallback sang DuckDB).
    Trả về tuple: (backend_type: 'postgres' | 'duckdb', connection_object)
    """
    if not FORCE_DUCKDB:
        pg_pool = get_pg_pool()
        if pg_pool:
            try:
                conn = pg_pool.getconn()
                return "postgres", conn
            except Exception as e:
                logger.warning("Lỗi lấy kết nối từ PostgreSQL Pool: %s. Chuyển sang DuckDB.", e)

    # Fallback / Direct DuckDB
    if os.path.exists(DUCKDB_PATH):
        try:
            dconn = duckdb.connect(DUCKDB_PATH, read_only=True)
            return "duckdb", dconn
        except Exception as e:
            logger.error("Lỗi kết nối DuckDB tại %s: %s", DUCKDB_PATH, e)
            raise ConnectionError(f"Không thể kết nối cả PostgreSQL lẫn DuckDB: {e}")
    else:
        raise FileNotFoundError(f"Không tìm thấy DuckDB tại {DUCKDB_PATH} và PostgreSQL không khả dụng.")


def release_db_connection(backend: str, conn: Any):
    """Giải phóng kết nối an toàn về pool."""
    if backend == "postgres":
        global _pg_pool
        if _pg_pool and not _pg_pool.closed and conn:
            try:
                _pg_pool.putconn(conn)
            except Exception:
                pass
    elif backend == "duckdb":
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def execute_query(sql: str, params: Optional[Tuple] = None, use_guardrails: bool = True, max_limit: int = 500) -> pd.DataFrame:
    """
    Thực thi truy vấn SQL an toàn với hàng rào bảo mật (SQL Guardrails).
    
    Args:
        sql: Câu lệnh SQL (bắt buộc là câu lệnh SELECT/CTE).
        params: Tuple các tham số truyền vào query (nếu có).
        use_guardrails: Bật kiểm định chống phá hoại dữ liệu (mặc định True).
        max_limit: Số dòng tối đa cho phép trả về.
        
    Returns:
        pd.DataFrame chứa kết quả truy vấn.
    """
    start_time = time.time()
    sanitized_sql = sql
    
    if use_guardrails:
        is_safe, error_msg, sanitized_sql = validate_and_sanitize_sql(sql, max_limit=max_limit)
        if not is_safe:
            logger.error("SQL Security Violation: %s | Query: %s", error_msg, sql)
            raise SQLSecurityError(f"Cảnh báo An toàn Dữ liệu: {error_msg}")
            
    backend, conn = get_db_connection()
    try:
        if backend == "postgres":
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {PG_SCHEMA}, public;")
                if params:
                    cur.execute(sanitized_sql, params)
                else:
                    cur.execute(sanitized_sql)
                
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall() if cur.description else []
                df = pd.DataFrame(rows, columns=columns)
        else: # duckdb
            # Chuẩn hóa nếu câu query có tiền tố daklak_analytics. thì loại bỏ cho DuckDB
            duck_sql = sanitized_sql.replace(f"{PG_SCHEMA}.", "")
            if params:
                df = conn.execute(duck_sql, params).fetchdf()
            else:
                df = conn.execute(duck_sql).fetchdf()
                
        duration = time.time() - start_time
        logger.debug("Truy vấn thành công [%s] trong %.3f giây: %d dòng.", backend, duration, len(df))
        return df
    except Exception as e:
        logger.error("Lỗi thực thi SQL trên [%s]: %s\nQuery: %s", backend, e, sanitized_sql)
        raise e
    finally:
        release_db_connection(backend, conn)


def test_connection() -> Dict[str, Any]:
    """Kiểm tra tình trạng sẵn sàng của hệ thống CSDL phục vụ Copilot."""
    results = {
        "status": "UNKNOWN",
        "primary_backend": "postgres",
        "active_backend": None,
        "latency_ms": 0.0,
        "views_available": [],
        "total_views": 0,
        "error": None
    }
    
    start = time.time()
    try:
        backend, conn = get_db_connection()
        results["active_backend"] = backend
        
        test_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE 'v_%'
        ORDER BY table_name;
        """
        if backend == "postgres":
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {PG_SCHEMA}, public;")
                cur.execute(test_sql)
                views = [r[0] for r in cur.fetchall()]
        else:
            views_df = conn.execute("SHOW TABLES").fetchdf()
            views = [t for t in views_df['name'].tolist() if t.startswith('v_') or t.startswith('fact_')]
            
        release_db_connection(backend, conn)
        results["latency_ms"] = round((time.time() - start) * 1000, 2)
        results["views_available"] = views
        results["total_views"] = len(views)
        results["status"] = "HEALTHY"
    except Exception as e:
        results["status"] = "ERROR"
        results["error"] = str(e)
        results["latency_ms"] = round((time.time() - start) * 1000, 2)
        
    return results
