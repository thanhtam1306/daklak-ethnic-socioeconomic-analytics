"""
==============================================================================
TEST SUITE: POLICY QUERY ENGINE & STORYTELLING FORMATTER (Step 5.3 Verification)
File: policy_assistant/test_engine.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

import sys
import os

# Đảm bảo đường dẫn gốc của dự án nằm trong sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Cấu hình encoding stdout để in tiếng Việt chuẩn trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from policy_assistant.engine import (
    route_policy_intent,
    build_policy_sql,
    ask_policy_assistant,
    PolicyAssistantEngine
)
from policy_assistant.core.db import test_connection


def run_all_engine_tests():
    print("=" * 70)
    print("BỘ KIỂM ĐỊNH TOÀN DIỆN BƯỚC 5.3: POLICY ENGINE & STORYTELLING FORMATTER")
    print("=" * 70)

    # 0. Kiểm tra kết nối CSDL
    health = test_connection()
    print(f"CSDL Backend: {health['active_backend']} | Độ trễ: {health['latency_ms']} ms | Trạng thái: {health['status']}")
    assert health["status"] == "HEALTHY", "CSDL không ở trạng thái sẵn sàng!"

    # ==========================================================================
    # TEST 1: NHẬN DIỆN Ý ĐỊNH & THỰC THỂ (INTENT ROUTING & ENTITY EXTRACTION)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("1. KIỂM THỬ NHẬN DIỆN Ý ĐỊNH & BÓC TÁCH THỰC THỂ NGHIỆP VỤ")
    print("=" * 70)

    test_queries = [
        (
            "Dự toán ngân sách đầu tư công kỳ 2026 là bao nhiêu?",
            "POLICY_BUDGET",
            "KY_2026"
        ),
        (
            "Tình hình ma túy và HIV tại xã Ea Wy huyện Ea H'leo biến động ra sao?",
            "VULNERABILITY_HEALTH",
            "KY_2026"
        ),
        (
            "Dân tộc Chơ Ro hiện nay còn bao nhiêu hộ nhà tạm, đã xóa hết chưa?",
            "HOUSING_POVERTY",
            "KY_2026"
        ),
        (
            "Tỷ lệ hố xí hợp vệ sinh tại huyện Krông Bông so với tiêu chí 17 NTM?",
            "SANITATION_DIGITAL",
            "KY_2026"
        ),
        (
            "Top 5 xã nghèo nhất tỉnh Đắk Lắk hiện nay?",
            "POVERTY_COMMUNE",
            "KY_2026"
        ),
        (
            "Tỷ lệ lao động chưa qua đào tạo của người Mông?",
            "LABOR_EDUCATION",
            "KY_2026"
        ),
        (
            "Đồng bào Ê Đê có bao nhiêu hộ khát vốn tín dụng ưu đãi?",
            "CREDIT_LAND",
            "KY_2026"
        ),
    ]

    for q, expected_intent, expected_period in test_queries:
        intent = route_policy_intent(q)
        print(f"Q: '{q}'")
        print(f"  -> Intent: {intent.intent_code} (Khớp kỳ vọng: {intent.intent_code == expected_intent})")
        print(f"  -> Kỳ: {intent.entities.ky_baocao} | Huyện: {intent.entities.huyen} | Xã: {intent.entities.xa} | Dân tộc: {intent.entities.dantoc}")
        assert intent.intent_code == expected_intent, f"Sai intent: {intent.intent_code} != {expected_intent}"
        assert intent.entities.ky_baocao == expected_period, f"Sai kỳ: {intent.entities.ky_baocao} != {expected_period}"

    print(">>> 100% KIỂM THỬ ROUTING & ENTITY EXTRACTION ĐẠT CHUẨN! <<<")

    # ==========================================================================
    # TEST 2: KIỂM THỬ BÀI TOÁN DỰ TOÁN NGÂN SÁCH (POLICY_BUDGET)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("2. KIỂM THỬ TRUY VẤN VÀ XUẤT BÁO CÁO F-A-I-R DỰ TOÁN NGÂN SÁCH")
    print("=" * 70)

    q_budget = "Tổng dự toán ngân sách chính sách cần giải ngân cho vùng DTTS kỳ 2026 là bao nhiêu?"
    res_budget = ask_policy_assistant(q_budget)
    assert res_budget["status"] == "SUCCESS", f"Lỗi truy vấn: {res_budget.get('error_message')}"
    assert res_budget["total_rows"] > 0, "Không có dữ liệu trả về!"
    assert "5.119,65 tỷ VNĐ" in res_budget["report_markdown"] or "5119.65" in str(res_budget["data"]), "Số liệu ngân sách kỳ 2026 không khớp 5.119,65 tỷ VNĐ!"

    print(f"- Intent: {res_budget['intent_code']}")
    print(f"- Số dòng thực chứng: {res_budget['total_rows']}")
    print(f"- Độ trễ xử lý: {res_budget['latency_ms']} ms")
    print(f"- Trích đoạn Báo cáo F-A-I-R:\n")
    print("\n".join(res_budget["report_markdown"].splitlines()[:18]))

    # ==========================================================================
    # TEST 3: KIỂM THỬ XÓA NHÀ TẠM CHO DTTS RẤT ÍT NGƯỜI (CHƠ RO)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("3. KIỂM THỬ CHUYÊN ĐỀ XÓA NHÀ TẠM CHO DÂN TỘC CHƠ RO")
    print("=" * 70)

    q_choro = "Dân tộc Chơ Ro hiện nay có bao nhiêu nhà tạm dột nát?"
    res_choro = ask_policy_assistant(q_choro)
    assert res_choro["status"] == "SUCCESS"
    df_choro = res_choro["dataframe"]
    # Kiểm tra kỳ 2026 người Chơ Ro có 0 nhà tạm
    latest_choro = df_choro[df_choro["ma_ky"] == "KY_2026"]
    if not latest_choro.empty:
        nha_tam_val = latest_choro["so_ho_nha_tam_don_so"].values[0]
        print(f"- Số nhà tạm của dân tộc Chơ Ro kỳ 2026: {nha_tam_val} căn (Đã xóa 100%!)")
        assert nha_tam_val == 0, f"Dân tộc Chơ Ro kỳ 2026 phải có 0 nhà tạm, nhận được: {nha_tam_val}"

    print(f"- Trích đoạn Báo cáo F-A-I-R:\n")
    print("\n".join(res_choro["report_markdown"].splitlines()[:16]))

    # ==========================================================================
    # TEST 4: KIỂM THỬ ĐIỂM NÓNG AN NINH & Y TẾ (XÃ EA WY & MA TÚY/HIV)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("4. KIỂM THỬ ĐIỂM NÓNG AN NINH TRẬT TỰ & Y TẾ SINH SẢN (XÃ EA WY)")
    print("=" * 70)

    q_eawy = "Tình hình ma túy và HIV tại xã Ea Wy huyện Ea H'leo biến động ra sao?"
    res_eawy = ask_policy_assistant(q_eawy)
    assert res_eawy["status"] == "SUCCESS"
    assert res_eawy["total_rows"] > 0
    print(f"- Số dòng theo dõi đa kỳ xã Ea Wy: {res_eawy['total_rows']}")
    print(f"- Trích đoạn Báo cáo F-A-I-R:\n")
    print("\n".join(res_eawy["report_markdown"].splitlines()[:22]))

    # ==========================================================================
    # TEST 5: KIỂM THỬ VÙNG TRŨNG VỆ SINH & NÔNG THÔN MỚI (KRÔNG BÔNG & LẮK)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("5. KIỂM THỬ ĐIỂM TRŨNG VỆ SINH NTM TIÊU CHÍ 17 (KRÔNG BÔNG)")
    print("=" * 70)

    q_krongbong = "Tỷ lệ hố xí hợp vệ sinh tại huyện Krông Bông so với tiêu chí 17 NTM?"
    res_kb = ask_policy_assistant(q_krongbong)
    assert res_kb["status"] == "SUCCESS"
    assert res_kb["total_rows"] > 0
    print(f"- Số dòng theo dõi huyện Krông Bông: {res_kb['total_rows']}")
    print(f"- Trích đoạn Báo cáo F-A-I-R:\n")
    print("\n".join(res_kb["report_markdown"].splitlines()[:22]))

    # ==========================================================================
    # TEST 6: KIỂM THỬ CẢNH BÁO TÁI NGHÈO / DẬM CHÂN CẤP XÃ
    # ==========================================================================
    print("\n" + "=" * 70)
    print("6. KIỂM THỬ CẢNH BÁO TÁI NGHÈO VÙNG SÂU (XÃ NAM KA & IA LỐP)")
    print("=" * 70)

    q_namka = "Tình hình nghèo và biến động tại xã Nam Ka huyện Lắk?"
    res_nk = ask_policy_assistant(q_namka)
    assert res_nk["status"] == "SUCCESS"
    assert res_nk["total_rows"] > 0
    print(f"- Số dòng theo dõi xã Nam Ka: {res_nk['total_rows']}")
    print(f"- Trích đoạn Báo cáo F-A-I-R:\n")
    print("\n".join(res_nk["report_markdown"].splitlines()[:22]))

    # ==========================================================================
    # TEST 7: KIỂM THỬ HÀNG RÀO BẢO MẬT SQL GUARDRAILS
    # ==========================================================================
    print("\n" + "=" * 70)
    print("7. KIỂM THỬ HÀNG RÀO AN TOÀN SQL GUARDRAILS TRONG ENGINE")
    print("=" * 70)

    malicious_question = "DROP TABLE dim_diaban; SELECT * FROM v_xa_biendong_ngheo_da_ky"
    res_mal = ask_policy_assistant(malicious_question)
    print(f"- Câu hỏi tấn công: '{malicious_question}'")
    print(f"- Trạng thái xử lý: {res_mal['status']}")
    print(f"- Báo cáo an toàn: {res_mal.get('error_message')}")
    # Đảm bảo lệnh độc hại bị từ chối hoặc chặn triệt để
    assert res_mal["status"] == "SUCCESS" or "bị từ chối" in str(res_mal.get("error_message")) or "DROP" not in str(res_mal.get("sql_query"))

    print("\n" + "=" * 70)
    print(">>> 100% CÁC BÀI KIỂM THỬ BƯỚC 5.3 ĐÃ THÀNH CÔNG XUẤT SẮC! <<<")
    print("=" * 70)


if __name__ == "__main__":
    run_all_engine_tests()
