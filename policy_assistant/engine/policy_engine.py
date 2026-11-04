"""
==============================================================================
MODULE: POLICY ANALYTICS ENGINE ORCHESTRATOR (Policy Decision Support System)
File: policy_assistant/engine/policy_engine.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

import time
import logging
from typing import Dict, Any, Optional
import pandas as pd

from .intent_router import route_policy_intent, PolicyIntent, ExtractedEntities
from .query_builder import build_policy_sql
from .storytelling_formatter import format_fair_policy_brief
from ..core.db import execute_query
from ..core.sql_guardrails import validate_and_sanitize_sql, SQLSecurityError

logger = logging.getLogger("PolicyAssistant.Engine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class PolicyAssistantEngine:
    """
    Hệ thống Hỗ trợ Ra Quyết định & Tham mưu Chính sách KTXH Đắk Lắk:
    - Điều phối toàn bộ chu trình: Nhận diện câu hỏi -> Bóc tách thực thể -> Sinh SQL an toàn
      -> Truy vấn CSDL đa kỳ (PostgreSQL/DuckDB) -> Xuất báo cáo tham mưu F-A-I-R.
    """

    def __init__(self):
        logger.info("Khởi tạo thành công Policy Assistant Engine (Decision Support System).")

    def query(self, question: str, forced_period: Optional[str] = None) -> Dict[str, Any]:
        """
        Xử lý câu hỏi tự nhiên tiếng Việt từ Lãnh đạo hoặc Chuyên viên:
        - question: Câu hỏi nghiệp vụ tự nhiên
        - forced_period: Khóa chu kỳ cụ thể ('KY_2019' | 'KY_2024' | 'KY_2026') nếu có bộ lọc trên giao diện
        """
        start_time = time.perf_counter()

        if not question or not question.strip():
            return {
                "question": "",
                "status": "ERROR",
                "error_message": "Vui lòng nhập câu hỏi phân tích hoặc tra cứu chính sách.",
                "latency_ms": 0.0
            }

        try:
            # 1. Bóc tách thực thể & Định tuyến ý định nghiệp vụ (Intent Routing)
            intent = route_policy_intent(question)
            if forced_period in ("KY_2019", "KY_2024", "KY_2026"):
                intent.entities.ky_baocao = forced_period

            # 2. Sinh câu truy vấn SQL phân tích động
            raw_sql = build_policy_sql(intent)

            # 3. Kiểm định an toàn SQL Guardrails (Read-Only & Auto-LIMIT)
            is_safe, error_msg, sanitized_sql = validate_and_sanitize_sql(raw_sql, max_limit=500)
            if not is_safe:
                raise SQLSecurityError(f"Truy vấn bị từ chối bởi SQL Guardrails: {error_msg}")

            # 4. Thực thi truy vấn trên CSDL (PostgreSQL 18 hoặc DuckDB Fallback)
            df = execute_query(sanitized_sql)
            backend_used = "postgres"  # execute_query tự động fallback

            # 5. Biên soạn báo cáo tham mưu chuẩn F-A-I-R
            report_md = format_fair_policy_brief(intent, df)

            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            return {
                "question": question,
                "status": "SUCCESS",
                "intent_code": intent.intent_code,
                "intent_description": intent.intent_description,
                "entities": {
                    "ky_baocao": intent.entities.ky_baocao,
                    "so_sanh_da_ky": intent.entities.so_sanh_da_ky,
                    "huyen": intent.entities.huyen,
                    "xa": intent.entities.xa,
                    "dantoc": intent.entities.dantoc,
                    "metric_keys": intent.entities.metric_keys,
                    "limit": intent.entities.limit,
                    "sort_order": intent.entities.sort_order
                },
                "sql_query": sanitized_sql,
                "dataframe": df,
                "records": df.to_dict(orient="records"),
                "total_rows": len(df),
                "report_markdown": report_md,
                "backend_used": backend_used,
                "latency_ms": latency_ms,
                "error_message": None
            }

        except Exception as e:
            logger.error("Lỗi xử lý câu hỏi '%s': %s", question, e, exc_info=True)
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return {
                "question": question,
                "status": "ERROR",
                "error_message": str(e),
                "sql_query": raw_sql if "raw_sql" in locals() else None,
                "latency_ms": latency_ms
            }


# Khởi tạo singleton instance
_engine_instance: Optional[PolicyAssistantEngine] = None


def get_policy_engine() -> PolicyAssistantEngine:
    """Trả về singleton instance của PolicyAssistantEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PolicyAssistantEngine()
    return _engine_instance


def ask_policy_assistant(question: str, forced_period: Optional[str] = None) -> Dict[str, Any]:
    """Hàm tiện ích cấp cao để tra cứu và nhận báo cáo tham mưu chính sách."""
    engine = get_policy_engine()
    return engine.query(question, forced_period=forced_period)
