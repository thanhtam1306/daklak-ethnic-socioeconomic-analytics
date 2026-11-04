"""
==============================================================================
MODULE: SQL SECURITY GUARDRAILS (Enterprise Read-Only Policy Enforcement)
File: policy_assistant/core/sql_guardrails.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

import re
from typing import Tuple


class SQLSecurityError(Exception):
    """Ngoại lệ khi phát hiện câu lệnh SQL vi phạm quy chuẩn an toàn CSDL."""
    pass


# Danh sách các từ khóa DDL, DML biến đổi dữ liệu bị cấm tuyệt đối
FORBIDDEN_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
    r"\bVACUUM\b",
    r"\bREINDEX\b",
    r"\bCOPY\b",
    r"\bLOCK\b",
    r"\bINTO\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
    r"\bPRAGMA\b",
]

# Các hàm hệ thống nguy hiểm có thể gây DoS hoặc leo thang đặc quyền
DANGEROUS_SYSTEM_PATTERNS = [
    r"\bpg_sleep\b",
    r"\bpg_terminate_backend\b",
    r"\bpg_cancel_backend\b",
    r"\bdblink\b",
    r"\bpg_read_file\b",
    r"\bpg_write_file\b",
    r"\bcurrent_setting\b",
]


def strip_sql_comments(sql: str) -> str:
    """Loại bỏ chú thích dòng (-- ...) và khối (/* ... */) để tránh che giấu mã độc."""
    # Xóa comment nhiều dòng
    sql_clean = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # Xóa comment một dòng
    sql_clean = re.sub(r"--[^\n]*", " ", sql_clean)
    return sql_clean.strip()


def validate_and_sanitize_sql(sql: str, max_limit: int = 500) -> Tuple[bool, str, str]:
    """
    Kiểm duyệt và chuẩn hóa câu lệnh SQL:
    1. Kiểm tra câu lệnh chỉ được bắt đầu bằng SELECT hoặc WITH (CTE).
    2. Chặn đa câu lệnh (stacked queries via ';').
    3. Chặn từ khóa ghi/xóa/sửa đổi schema.
    4. Tự động kiểm soát mệnh đề LIMIT (tránh tràn RAM/bộ nhớ máy chủ).
    
    Returns:
        (is_safe, error_message, sanitized_sql)
    """
    if not sql or not sql.strip():
        return False, "Câu lệnh SQL rỗng.", ""

    clean_sql = strip_sql_comments(sql).strip()

    # 1. Chặn câu lệnh kép (semicolon bên trong thân lệnh)
    # Tách theo dấu chấm phẩy, loại trừ dấu chấm phẩy cuối cùng
    statements = [s.strip() for s in clean_sql.split(";") if s.strip()]
    if len(statements) > 1:
        return False, "Cấm thực thi nhiều câu lệnh SQL đồng thời (Stacked Queries).", ""

    target_sql = statements[0]

    # 2. Kiểm tra câu lệnh bắt đầu bằng SELECT hoặc WITH
    first_token = target_sql.split()[0].upper() if target_sql.split() else ""
    if first_token not in ("SELECT", "WITH"):
        return False, f"Chỉ cho phép câu lệnh đọc dữ liệu (SELECT hoặc WITH). Nhận được: '{first_token}'.", ""

    # 3. Quét các từ khóa biến đổi dữ liệu (DML/DDL)
    for pattern in FORBIDDEN_KEYWORDS:
        match = re.search(pattern, target_sql, flags=re.IGNORECASE)
        if match:
            forbidden_word = match.group(0).upper()
            return False, f"Từ khóa bị cấm trong truy vấn phân tích: '{forbidden_word}'.", ""

    # 4. Quét các hàm hệ thống nguy hiểm
    for pattern in DANGEROUS_SYSTEM_PATTERNS:
        match = re.search(pattern, target_sql, flags=re.IGNORECASE)
        if match:
            danger_word = match.group(0)
            return False, f"Hàm hệ thống bị hạn chế bảo mật: '{danger_word}'.", ""

    # 5. Kiểm tra và bổ sung LIMIT nếu chưa có hoặc vượt quá giới hạn
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", target_sql, flags=re.IGNORECASE)
    if limit_match:
        existing_limit = int(limit_match.group(1))
        if existing_limit > max_limit:
            # Thu nhỏ limit về max_limit
            target_sql = re.sub(
                r"\bLIMIT\s+\d+\b",
                f"LIMIT {max_limit}",
                target_sql,
                flags=re.IGNORECASE
            )
    else:
        # Tự động gắn thêm LIMIT để bảo vệ bộ nhớ
        target_sql = f"{target_sql.rstrip()} LIMIT {max_limit}"

    return True, "", target_sql
