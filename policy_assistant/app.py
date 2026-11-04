"""
==============================================================================
MODULE: ENTERPRISE POLICY WORKBENCH & WHAT-IF BUDGET SIMULATOR (Step 5.4 v2)
File: policy_assistant/app.py
Dự án: Hệ Thống Thẩm Định Chính Sách & Điều Hành Ngân Sách KTXH 53 DTTS Đắk Lắk
Thiết kế chuẩn Modern Bento Analytics (McKinsey / World Bank Data Portal Style):
  - Không nhồi nhét chữ: Bóc tách F-A-I-R thành 4 Thẻ Quyết sách cô đọng.
  - Trực quan hóa bằng Apache ECharts 5 tương tác mượt mà.
  - Việt hóa 100% tên cột CSDL sang ngôn ngữ quản trị sạch đẹp.
  - Bàn mô phỏng ngân sách What-If gắn liền biểu đồ cấu trúc vốn Realtime.
==============================================================================
"""

import os
import sys
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import re
import time
import decimal
from typing import Dict, Any, List, Optional
import pandas as pd
from flask import Flask, render_template, jsonify, request, Response

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except Exception:
    pass

from policy_assistant.core.db import execute_query, test_connection
from policy_assistant.core.sql_guardrails import validate_and_sanitize_sql
from policy_assistant.engine import (
    PolicyIntent,
    ExtractedEntities,
    route_policy_intent,
    build_policy_sql,
    format_fair_policy_brief,
)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates")
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Từ điển Việt hóa tên cột SQL sang nhãn hiển thị chuẩn Quản trị
COLUMN_LABELS: Dict[str, str] = {
    "ma_ky": "Mã kỳ",
    "ten_ky": "Chu kỳ rà soát",
    "giai_doan_chinh_sach": "Giai đoạn",
    "ma_chitieu": "Mã chỉ tiêu",
    "ten_chitieu": "Chỉ tiêu can thiệp",
    "ten_chinh_sach": "Chương trình / Dự án thành phần",
    "don_vi_tinh": "ĐVT",
    "so_luong_doi_tuong_can_ho_tro": "Quy mô đối tượng",
    "don_gia_trieu_vnd": "Định mức (Tr.đ)",
    "tong_kinh_phi_can_phan_bo_ty_vnd": "Dự toán (Tỷ VNĐ)",
    "can_cu_phap_ly_dinh_muc": "Căn cứ pháp lý",
    "bien_dong_kinh_phi_ty_vnd": "Biến động vốn (Tỷ)",
    "ten_huyen": "Huyện / Thị xã / TP",
    "ten_xa": "Xã / Phường",
    "km_den_trung_tam_huyen": "Cự ly (km)",
    "tong_ho_dtts": "Tổng hộ DTTS",
    "so_ho_ngheo": "Số hộ nghèo",
    "ty_le_ngheo_pct": "Tỷ lệ nghèo (%)",
    "bien_dong_ty_le_ngheo_pct": "Biến động nghèo (pp)",
    "nhom_toc_do_giam_ngheo": "Phân nhóm tiến độ",
    "du_toan_ngan_sach_sinh_ke_trieu_vnd": "Vốn sinh kế (Tr.đ)",
    "ten_dantoc": "Dân tộc",
    "nhom_nguon_goc": "Nhóm nguồn gốc",
    "la_dtts_it_nguoi": "DTTS rất ít người",
    "tong_ho_co_nha": "Tổng số hộ",
    "so_ho_nha_tam_don_so": "Số nhà tạm (Căn)",
    "ty_le_nha_tam_pct": "Tỷ lệ nhà tạm (%)",
    "so_ho_nha_tam_ky_truoc": "Nhà tạm kỳ trước",
    "chenh_lech_nha_tam": "Giảm nhà tạm (Căn)",
    "bien_dong_nha_tam_pct": "Biến động (%)",
    "xep_hang_nha_tam_ky": "Hạng ưu tiên",
    "tong_ho_dtts_huyen": "Tổng hộ DTTS",
    "ty_le_nuoc_hvs_bq_pct": "Nước HVS (%)",
    "ty_le_ho_xi_hvs_bq_pct": "Hố xí HVS (%)",
    "bien_dong_ho_xi_hvs_pct": "Tăng/giảm Hố xí (pp)",
    "trang_thai_ntm_tc17": "Đánh giá TC17 NTM",
    "ty_le_internet_huyen_pct": "Phủ Internet (%)",
    "bien_dong_internet_pct": "Tăng Internet (pp)",
    "trang_thai_chuyendoiso_dean06": "Đánh giá Đề án 06",
    "so_ho_khat_von": "Hộ khát vốn (Hộ)",
    "khoang_trong_tin_dung_pct": "Thiếu hụt vốn (%)",
    "chenh_lech_ho_khat_von": "Biến động hộ cần vốn",
    "bien_dong_tin_dung_pct": "Biến động (%)",
    "dien_tich_dat_sx_bq_ha": "Đất SX BQ (ha/hộ)",
    "bien_dong_dat_sx_ha": "Biến động đất (ha)",
    "xep_hang_khat_von_ky": "Hạng ưu tiên vốn",
    "tong_lao_dong": "Tổng lao động",
    "lao_dong_khong_cmkt": "LĐ chưa qua ĐT",
    "ty_le_khong_cmkt_pct": "Chưa đào tạo (%)",
    "bien_dong_khong_cmkt_pct": "Biến động CMKT (pp)",
    "lao_dong_nong_nghiep": "LĐ nông nghiệp",
    "ty_le_nong_nghiep_pct": "Làm nông nghiệp (%)",
    "ty_le_nu_biet_chu_pct": "Nữ biết chữ (%)",
    "bien_dong_nu_biet_chu_pct": "Biến động nữ biết chữ",
    "phan_nhom_rui_ro": "Nhóm chuyên đề rủi ro",
    "ten_doi_tuong": "Địa bàn / Dân tộc",
    "pham_vi_nhom": "Phạm vi quản lý",
    "chi_so_rui_ro_chinh": "Chỉ số chính (Người/Ca)",
    "chi_so_rui_ro_phu": "Chỉ số phụ (HIV/Không bà đỡ)",
    "tong_muc_do_rui_ro": "Tổng mức rủi ro",
    "bien_dong_rui_ro_chinh": "Tăng/giảm so kỳ trước",
    "ty_le_giam_rui_ro_pct": "Tốc độ giảm (%)",
    "dan_so_0_14": "Dân số 0-14 tuổi",
    "dan_so_15_59": "Dân số 15-59 tuổi",
    "dan_so_60_plus": "Dân số 60+ tuổi",
    "ty_le_0_14_pct": "% Trẻ em (0-14)",
    "ty_le_15_59_pct": "% Lao động (15-59)",
    "ty_le_60_plus_pct": "% Cao tuổi (60+)",
    "ty_le_phu_thuoc_tre_em_pct": "Phụ thuộc trẻ em (%)",
    "chi_so_gia_hoa_pct": "Chỉ số già hóa (%)",
    "xep_hang_diem_nong_ky": "Hạng điểm nóng"
}


def clean_json_value(v: Any) -> Any:
    if v is None or (isinstance(v, float) and pd.isna(v)) or pd.isna(v):
        return None
    if isinstance(v, decimal.Decimal):
        return float(v)
    if hasattr(v, "item"):
        return v.item()
    return v


def df_to_clean_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    records = []
    for _, row in df.iterrows():
        item = {}
        for col in df.columns:
            item[col] = clean_json_value(row[col])
        records.append(item)
    return records


_PRETTY_NAME_MAP = {
    "ê đê": "Ê Đê",
    "mnông": "M'Nông",
    "m'nông": "M'Nông",
    "gia rai": "Gia Rai",
    "xơ đăng": "Xơ Đăng",
    "khơ mú": "Khơ Mú",
    "tà ôi": "Tà Ôi",
    "cơ ho": "Cơ Ho",
    "cơ tu": "Cơ Tu",
    "hà nhì": "Hà Nhì",
    "la chí": "La Chí",
    "la hủ": "La Hủ",
    "la ha": "La Ha",
    "phù lá": "Phù Lá",
    "pu péo": "Pu Péo",
    "rơ măm": "Rơ Măm",
    "cờ lao": "Cờ Lao",
    "lô lô": "Lô Lô",
    "sán chay": "Sán Chay",
    "sán dìu": "Sán Dìu",
    "pà thẻn": "Pà Thẻn",
    "bố y": "Bố Y",
    "si la": "Si La",
    "ra glai": "Ra Glai",
    "bru - vân kiều": "Bru - Vân Kiều",
    "khơ me": "Khơ Me",
    "chơ ro": "Chơ Ro",
    "ơ đu": "Ơ Đu",
    "thành phố buôn ma thuột": "TP. Buôn Ma Thuột",
    "thị xã buôn hồ": "Thị xã Buôn Hồ",
    "huyện krông a na": "Huyện Krông Ana",
}


def pretty_entity(val: Any) -> str:
    """Chuẩn hóa cách viết hoa tên dân tộc và đơn vị hành chính đẹp mắt khi hiển thị UI."""
    if not val:
        return ""
    s = str(val).strip()
    low = s.lower()
    if low in _PRETTY_NAME_MAP:
        return _PRETTY_NAME_MAP[low]
    if low.startswith("dân tộc "):
        eth_part = low.replace("dân tộc ", "", 1).strip()
        return f"Dân tộc {_PRETTY_NAME_MAP.get(eth_part, s[8:].strip().title())}"
    return s


def short_yr(row: Any) -> str:
    """Rút gọn nhãn chu kỳ thành năm '2019', '2024', '2026' để câu trả lời gọn và tự nhiên."""
    mk = str(row.get("ma_ky", "") or "")
    if "2019" in mk:
        return "2019"
    if "2024" in mk:
        return "2024"
    if "2026" in mk:
        return "2026"
    tk = str(row.get("ten_ky", "") or "")
    for y in ("2019", "2024", "2026"):
        if y in tk:
            return y
    return tk or "2026"


def extract_structured_fair_cards(intent: PolicyIntent, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Trích xuất nội dung F-A-I-R thành 4 thẻ quyết sách thích ứng động 100% theo dữ liệu thực tế:
    Tự động phân nhánh giọng văn, nguyên nhân, hệ lụy và giải pháp theo đúng ngưỡng chỉ số
    của từng Xã, Huyện, Dân tộc hoặc Toàn tỉnh (loại bỏ hoàn toàn văn mẫu tĩnh rập khuôn).
    """
    code = intent.intent_code
    e = intent.entities
    period = e.ky_baocao
    period_name = "kỳ 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")
    eth_disp = pretty_entity(e.dantoc) if e.dantoc else None
    huyen_disp = pretty_entity(e.huyen) if e.huyen else None
    question = (intent.intent_description or "").lower()

    if df is None or df.empty:
        return {
            "headline": "Không tìm thấy bản ghi phù hợp với bộ lọc hiện tại.",
            "legal_tag": "Hệ thống CSDL Đắk Lắk",
            "fact": ["Vui lòng chọn lại địa bàn Huyện/Xã hoặc Dân tộc trên thanh bộ lọc."],
            "analysis": ["Chưa có dữ liệu đối sánh."],
            "impact": ["Chưa phát sinh cảnh báo."],
            "recommendation": ["Nới lỏng điều kiện lọc để xem toàn tỉnh."],
            "action_plan": {
                "who": "Ban Dân tộc & Sở KH&ĐT",
                "what": "Nới lỏng bộ lọc để xem bức tranh tổng thể toàn tỉnh",
                "where_when": "Toàn tỉnh Đắk Lắk",
                "budget_text": "--"
            }
        }

    # 0. CHUYÊN ĐỀ HƯỚNG DẪN SỬ DỤNG POWER BI DASHBOARD & PHƯƠNG PHÁP TÍNH CHỈ SỐ (DASHBOARD_GUIDE)
    if code == "DASHBOARD_GUIDE":
        topic = e.guide_topic or "general"
        if topic == "age_pyramid":
            return {
                "headline": "Giải thích Biểu đồ 'Tháp Tuổi & Cơ Cấu 3 Nhóm Tuổi Dân Tộc' trên Trang 1 Power BI: Bóc tách cơ cấu nhân khẩu học, mức độ trẻ hóa và xu hướng già hóa của 53 DTTS.",
                "legal_tag": "Power BI Page 1 • Tháp Tuổi & Cơ Cấu 3 Nhóm Tuổi (Fact 8)",
                "fact": [
                    "<strong>3 Nhóm tuổi cốt lõi (100% Stacked Bar):</strong> (1) <em>0–14 tuổi (Trẻ em / Dưới tuổi lao động)</em>, (2) <em>15–59 tuổi (Lao động vàng / Độ tuổi lao động)</em>, (3) <em>60+ tuổi (Người cao tuổi / Hết tuổi lao động)</em>.",
                    "<strong>2 Chỉ số nhân khẩu học DAX:</strong> <em>Tỷ lệ phụ thuộc trẻ em</em> = [Dân số 0-14] / [Dân số 15-59] × 100 | <em>Chỉ số già hóa</em> = [Dân số 60+] / [Dân số 0-14] × 100.",
                    "<strong>Số liệu thực tế Top 10 dân tộc:</strong> Người Mông có 41.0% trẻ em (phụ thuộc trẻ em 75.1%), Xơ Đăng 42.5% trẻ em (phụ thuộc trẻ em 79.2%); người Ê Đê có 62.0% tuổi lao động; người Tày (10.7% già, già hóa 42.7%) và Thái (10.6% già, già hóa 42.1%) dẫn đầu về tốc độ già hóa."
                ],
                "analysis": [
                    "<strong>Đối lập giữa 2 dòng nhân khẩu học:</strong> Nhóm di cư phía Bắc (Mông, Xơ Đăng, Dao) có đáy tháp tuổi phình to cực đại do tỷ suất sinh cao, tạo áp lực nuôi con lớn (100 lao động gánh gần 80 trẻ nhỏ); ngược lại nhóm Tày, Nùng, Thái tỷ lệ sinh thấp hơn và đang chuyển nhanh sang già hóa.",
                    "<strong>Thời kỳ dân số vàng của nhóm bản địa:</strong> Dân tộc Ê Đê và Mnông có hơn 60–62% dân số nằm trong độ tuổi 15–59, đây là lực lượng lao động dồi dào nhất cần được đào tạo nghề kỹ thuật nông nghiệp để bứt phá thu nhập."
                ],
                "impact": [
                    "Cấu trúc tuổi quyết định trực tiếp tới định hướng phân bổ ngân sách: Nhóm trẻ hóa cao cần ưu tiên trường lớp mầm non, tiểu học (Dự án 5 MTQG 1719) và dinh dưỡng trẻ em; nhóm già hóa cần chuẩn bị hạ tầng y tế người cao tuổi và an sinh xã hội."
                ],
                "recommendation": [
                    "Bấm chọn từng dân tộc trên biểu đồ để lọc chéo xem tháp tuổi riêng; kết hợp đối chiếu với biểu đồ 'Gánh nặng nuôi con vs Già hóa' và tỷ lệ sinh con thứ 3+ ở Trang 4."
                ],
                "action_plan": {
                    "who": "Ban Dân tộc • Sở GD&ĐT • Sở Y tế • Sở LĐ-TB&XH",
                    "what": "Điều hành chính sách theo tháp tuổi: Giáo dục mầm non cho nhóm trẻ (Mông, Xơ Đăng) & Đào tạo nghề cho nhóm 15–59 tuổi (Ê Đê, Mnông)",
                    "where_when": "Trang 1: Dân số & Địa bàn (Power BI Desktop)",
                    "budget_text": "Cơ cấu 3 nhóm tuổi: 0–14 tuổi • 15–59 tuổi • 60+ tuổi"
                }
            }
        elif topic == "treemap_pop":
            return {
                "headline": "Giải thích Biểu đồ 'Treemap Phân Bố Dân Số DTTS 15 Huyện' trên Trang 1 Power BI: Mật độ cư trú và tương quan tỷ lệ nghèo/cận nghèo theo không gian địa lý.",
                "legal_tag": "Power BI Page 1 • Treemap Phân Bố Địa Bàn 15 Huyện",
                "fact": [
                    "<strong>Quy tắc hiển thị 2 chiều:</strong> (1) <em>Diện tích ô chữ nhật</em> tỷ lệ thuận với Tổng số hộ DTTS của huyện; (2) <em>Độ đậm nhạt màu sắc</em> thể hiện mức độ nghèo hoặc cận nghèo của huyện đó.",
                    "<strong>Thực tế địa bàn:</strong> Huyện Krông Năng, Cư M'gar, Krông Pắc, Buôn Ma Thuột có diện tích ô lớn nhất (tập trung đông đồng bào Ê Đê); trong khi Ea Súp, Lắk, Krông Bông có màu sắc cảnh báo đậm nhất (tỷ lệ nghèo cao nhất tỉnh)."
                ],
                "analysis": [
                    "Treemap giúp Lãnh đạo nhận diện ngay sự đánh đổi giữa 'Quy mô tuyệt đối (Volume)' và 'Cường độ nghèo (Intensity)': huyện đông dân chưa chắc là huyện nghèo nhất, nhưng đòi hỏi khối lượng vốn an sinh lớn nhất."
                ],
                "impact": [
                    "Tránh dàn đều ngân sách bình quân theo địa giới hành chính, hướng nguồn lực đúng trọng tâm theo mật độ hộ nghèo."
                ],
                "recommendation": [
                    "Bấm thẳng vào 1 ô Huyện trên Treemap để kích hoạt lọc chéo (Cross-filtering) toàn bộ các visual khác trên Trang 1 về riêng huyện đó."
                ],
                "action_plan": {
                    "who": "UBND Tỉnh • Ban Dân tộc • UBND 15 Huyện/TX/TP",
                    "what": "Click-to-Filter trên Treemap để soi cơ cấu dân tộc và tháp tuổi của từng huyện",
                    "where_when": "Trang 1: Dân số & Địa bàn (Power BI Desktop)",
                    "budget_text": "15 Huyện • 146 Xã • 163.912 Hộ DTTS"
                }
            }
        elif topic == "quadrant_chart":
            return {
                "headline": "Giải thích Biểu đồ 'Ma Trận 4 Góc Phần Tư: Khoảng Cách vs Tỷ Lệ Nghèo Cấp Xã' trên Trang 4 Power BI: Khoanh vùng chính xác các 'Xã Khó Khăn Kép'.",
                "legal_tag": "Power BI Page 4 • Ma Trận 4 Góc Phần Tư & Bẫy Cự Ly Địa Lý",
                "fact": [
                    "<strong>Cách đọc 2 trục & Kích thước:</strong> Trục X = Khoảng cách từ xã đến trung tâm huyện (km); Trục Y = Tỷ lệ hộ nghèo (%); Kích thước bóng = Quy mô số hộ DTTS của xã.",
                    "<strong>4 Góc phần tư chiến lược:</strong> Góc I (Trên cùng bên phải: Xa >15–20km & Nghèo >25–35%) là 'Xã khó khăn kép' (như Nam Ka, Ia Lốp, Cư Pui, Yang Reh); Góc II (Gần & Nghèo cao) là nghèo do thiếu đất/kỹ năng; Góc III (Gần & Nghèo thấp) là xã thuận lợi; Góc IV (Xa & Nghèo thấp) là xã biên giới giữ rừng có nguồn thu ổn định."
                ],
                "analysis": [
                    "Phương trình hồi quy OLS chứng minh: Cứ xa trung tâm huyện thêm 10 km, tỷ lệ nghèo tăng trung bình +5,13 điểm % do chi phí lưu thông và rào cản tiếp cận thị trường."
                ],
                "impact": [
                    "Khoanh vùng chính xác nhóm xã chịu tổn thương nặng nề nhất để ưu tiên gói hạ tầng giao thông và vốn sinh kế Dự án 3."
                ],
                "recommendation": [
                    "Bấm vào bóng của một xã khó khăn kép ở Góc I để xem ngay dự toán ngân sách tương ứng tại hộp Khung Hành Động ở góc phải."
                ],
                "action_plan": {
                    "who": "Ban Chỉ đạo MTQG Tỉnh • UBND Huyện Lắk, Ea Súp, Krông Bông",
                    "what": "Ưu tiên phân bổ vốn Dự án 3 và Dự án 4 cho các xã Góc I (Xa >20km & Nghèo >30%)",
                    "where_when": "Trang 4: Ưu tiên chính sách (Power BI Desktop)",
                    "budget_text": "Định mức sinh kế 30 tr/hộ nghèo"
                }
            }
        elif topic == "anti_triple_count":
            return {
                "headline": "Giải thích Cơ Chế DAX Chống Cộng Trùng 3 Kỳ (Anti-Triple Counting Gate): Khóa Kỳ Thông Minh [Selected Period Order].",
                "legal_tag": "Kiến trúc DAX Semantic Model • Chống Cộng Trùng 3 Kỳ",
                "fact": [
                    "<strong>Hiện tượng lỗi trước khi xử lý:</strong> Mô hình dữ liệu có 3 kỳ (2019, 2024, 2026). Nếu người dùng không chọn Slicer Kỳ báo cáo, Power BI mặc định SUM toàn bộ 3 kỳ khiến số hộ DTTS bị cộng phình lên 473.755 hộ (149.480 + 160.363 + 163.912).",
                    "<strong>Cơ chế khóa cổng Anti-Triple Counting:</strong> Hàm DAX <code>[Selected Period Order]</code> kiểm tra nếu <code>NOT(ISFILTERED(dim_ky_baocao))</code> sẽ tự động khóa cứng về kỳ mới nhất (<code>is_latest = TRUE → KY_2026, thu_tu_ky = 3</code>), trả về chuẩn xác 163.912 hộ."
                ],
                "analysis": [
                    "Toàn bộ 100 DAX Explicit Measures đều kế thừa biến <code>VAR CurOrder = [Selected Period Order]</code> và áp bộ lọc <code>dim_ky_baocao[thu_tu_ky] = CurOrder</code>, giúp người dùng bỏ chọn Slicer thoải mái mà số liệu vẫn an toàn 100%."
                ],
                "impact": [
                    "Triệt tiêu hoàn toàn rủi ro sai lệch dữ liệu khi báo cáo Lãnh đạo hoặc trình chiếu trước Hội đồng."
                ],
                "recommendation": [
                    "Thử bỏ chọn Slicer Kỳ báo cáo trên Power BI Desktop để xác nhận thẻ KPI Số Hộ DTTS luôn hiển thị đúng 163.912 hộ."
                ],
                "action_plan": {
                    "who": "Đội ngũ DA / BI Developer",
                    "what": "Triển khai hàm DAX [Selected Period Order] làm cổng bảo vệ thời gian trung tâm",
                    "where_when": "Thư mục DAX: 00_Time_Intelligence_Context",
                    "budget_text": "Khóa kỳ tự động KY_2026 (163.912 hộ)"
                }
            }
        elif topic == "page_1":
            return {
                "headline": "Hướng dẫn khai thác Trang 1 Power BI — 'Dân số & Địa bàn': Bức tranh nhân khẩu học 53 DTTS và phân bố không gian trên 15 huyện, 146 xã.",
                "legal_tag": "Power BI Page 1 • Dân số & Địa bàn",
                "fact": [
                    "<strong>4 Thẻ KPI đầu trang:</strong> <em>Tổng Dân Số DTTS</em>, <em>Tổng Số Hộ DTTS</em>, <em>Xã Khảo Sát (146 xã)</em> và <em>Số DTTS (53 dân tộc)</em> kèm nhãn biến động so với kỳ trước.",
                    "<strong>4 Biểu đồ chính:</strong> (1) <em>Treemap Phân bố dân số theo 15 huyện</em>, (2) <em>Cơ cấu 10 dân tộc chủ lực</em>, (3) <em>Tháp tuổi & Cơ cấu 3 nhóm tuổi (0–14, 15–59, 60+)</em>, (4) <em>Biểu đồ phân tán Gánh nặng nuôi con vs Già hóa</em>.",
                    "<strong>3 Bộ lọc (Slicers):</strong> <em>Kỳ báo cáo (ten_ky)</em>, <em>Địa bàn Huyện (ten_huyen)</em> và <em>Dân tộc (ten_dantoc)</em>."
                ],
                "analysis": [
                    "Cách đọc Treemap 15 huyện: Diện tích ô thể hiện quy mô Số hộ DTTS, còn độ đậm nhạt màu sắc cảnh báo Tỷ lệ cận nghèo/nghèo của huyện đó.",
                    "Cách đọc Scatter Chart (Gánh nặng nuôi con vs Già hóa): Các dân tộc nằm lệch về góc phải dưới (như Mông, Gia Rai) có tỷ lệ trẻ em <15 tuổi rất cao, cần ưu tiên trường lớp và dinh dưỡng; nhóm lệch lên trên (như Chơ Ro, Tày) có tốc độ già hóa nhanh."
                ],
                "impact": [
                    "Giúp Lãnh đạo nắm ngay quy mô dân số và cơ cấu nhân khẩu học trước khi đi sâu vào các chuyên đề việc làm, nhà ở và ngân sách."
                ],
                "recommendation": [
                    "Bấm chọn 1 Huyện trên Treemap hoặc 1 Dân tộc trên biểu đồ cột để lọc chéo (Cross-filter) toàn bộ tháp tuổi và các chỉ số liên quan."
                ],
                "action_plan": {
                    "who": "Chuyên viên Phân tích • Lãnh đạo UBND Tỉnh / Ban Dân tộc",
                    "what": "Sử dụng Slicer Kỳ báo cáo (2019 | 2024 | 2026) kết hợp Click-to-Filter trên Treemap 15 huyện",
                    "where_when": "Trang 1: Dân số & Địa bàn (Power BI Desktop)",
                    "budget_text": "146 Xã • 15 Huyện • 53 Dân tộc"
                }
            }
        elif topic == "page_2":
            return {
                "headline": "Hướng dẫn khai thác Trang 2 Power BI — 'Học vấn & Việc làm': Phân tích bẫy kỹ năng nghề CMKT và khoảng cách biết chữ theo giới tính.",
                "legal_tag": "Power BI Page 2 • Học vấn & Việc làm (Dự án 5)",
                "fact": [
                    "<strong>4 Thẻ KPI:</strong> <em>Tỷ Lệ Lao Động Nông Nghiệp</em>, <em>Tỷ Lệ Chưa Qua Đào Tạo</em>, <em>Dân Số Biết Chữ</em> và <em>Tỷ Số Biết Chữ Nam/Nữ</em>.",
                    "<strong>4 Biểu đồ chính:</strong> (1) <em>Donut Bẫy trình độ CMKT</em>, (2) <em>Cơ cấu phân bổ ngành kinh tế</em>, (3) <em>Ma trận tương quan Kỹ năng vs Bẫy nông nghiệp</em>, (4) <em>Nghịch lý giới trong giáo dục</em>.",
                    "<strong>Bộ lọc đặc thù:</strong> Ngoài Kỳ báo cáo và Dân tộc, Trang 2 có thêm Slicer <em>Nhóm nguồn gốc (nhom_nguon_goc)</em> để tách nhóm Bản địa Tây Nguyên (Ê Đê, M'Nông, Gia Rai) và nhóm Di cư."
                ],
                "analysis": [
                    "Cách đọc 'Ma trận Kỹ năng vs Bẫy nông nghiệp': Trục ngang là % chưa qua đào tạo nghề, trục dọc là % làm nông nghiệp. Các chấm tròn dồn lên góc trên bên phải chứng minh: thiếu chứng chỉ nghề khóa chặt lao động trong nông nghiệp tự cung tự cấp.",
                    "Cách đọc 'Nghịch lý Giới trong Giáo dục': Dùng Slicer lọc nhóm Bản địa (Mẫu hệ) sẽ thấy nữ biết chữ tương đương nam; lọc nhóm Di cư (Phụ hệ như Mông, Dao) sẽ thấy khoảng cách mù chữ ở phụ nữ rất lớn."
                ],
                "impact": [
                    "Là căn cứ trực tiếp để Sở LĐ-TB&XH và Sở GD&ĐT thiết kế lớp xóa mù chữ và đào tạo nghề Dự án 5 sát với từng nhóm dân tộc."
                ],
                "recommendation": [
                    "Sử dụng Slicer 'nhom_nguon_goc' để so sánh trực diện sự đối lập về giáo dục giới tính giữa cộng đồng Mẫu hệ bản địa và Phụ hệ di cư."
                ],
                "action_plan": {
                    "who": "Sở LĐ-TB&XH • Sở GD&ĐT • Trung tâm GDNN-GDTX",
                    "what": "Dùng Slicer Nhóm nguồn gốc & Ma trận Kỹ năng để khoanh vùng đối tượng đào tạo nghề Dự án 5",
                    "where_when": "Trang 2: Học vấn & Việc làm (Power BI Desktop)",
                    "budget_text": "Định mức 6,0 triệu VNĐ/lao động học nghề"
                }
            }
        elif topic == "page_3":
            return {
                "headline": "Hướng dẫn khai thác Trang 3 Power BI — 'Điều kiện sống': Giám sát nhà tạm, vùng trũng vệ sinh NTM, tín dụng ưu đãi và đất canh tác.",
                "legal_tag": "Power BI Page 3 • Điều kiện sống (DA 1 & TC 17 NTM)",
                "fact": [
                    "<strong>4 Thẻ KPI:</strong> <em>Tỷ Lệ Nhà Kiên Cố (kèm số căn nhà tạm)</em>, <em>Hố Xí Hợp Vệ Sinh</em>, <em>Khoảng Trống Tín Dụng</em> và <em>Đất Canh Tác Bình Quân (ha/hộ)</em>.",
                    "<strong>4 Biểu đồ chính:</strong> (1) <em>Hiện trạng chất lượng nhà ở theo dân tộc</em>, (2) <em>Điểm trũng vệ sinh môi trường cấp huyện</em>, (3) <em>Khoảng trống tín dụng NHCSXH (Hộ vay vs Hổng vốn)</em>, (4) <em>Bất bình đẳng tư liệu sản xuất: Đất canh tác (ha/hộ)</em>."
                ],
                "analysis": [
                    "Cách đọc 'Điểm trũng vệ sinh môi trường cấp huyện': Đặt 3 cột Nước HVS, Hố xí HVS và Internet cạnh nhau để phát hiện nghịch lý 'Công nghệ đi trước vệ sinh' (Internet đạt >95% nhưng Hố xí HVS ở Krông Bông, Lắk dưới 20%).",
                    "Cách đọc 'Khoảng trống tín dụng': So sánh phần thanh 'Hộ đang vay' và phần 'Hộ có nhu cầu nhưng chưa vay được (Hổng vốn)' để biết quy mô cần bổ sung vốn Nghị định 28."
                ],
                "impact": [
                    "Phát hiện ngay các điểm nghẽn hạ tầng thiết yếu làm liệt Tiêu chí số 9 (Nhà ở) và Tiêu chí 17.5 (Môi trường) trong xây dựng Nông thôn mới."
                ],
                "recommendation": [
                    "Kết hợp chọn Huyện và Kỳ báo cáo trên Trang 3 để kiểm tra tiến độ xóa nhà tạm (ví dụ: dân tộc Chơ Ro về 0 căn ở kỳ 2026)."
                ],
                "action_plan": {
                    "who": "Sở Xây dựng • VP Điều phối NTM • Chi nhánh NHCSXH Tỉnh",
                    "what": "Đối chiếu 4 trụ cột Điều kiện sống (Nhà ở, Vệ sinh, Vốn vay, Đất sản xuất) theo từng Huyện/Dân tộc",
                    "where_when": "Trang 3: Điều kiện sống (Power BI Desktop)",
                    "budget_text": "Nhà tạm 90 tr/căn • Vốn vay 65 tr/hộ • Hố xí 12 tr/hộ"
                }
            }
        elif topic == "page_4":
            return {
                "headline": "Hướng dẫn khai thác Trang 4 Power BI — 'Ưu tiên chính sách': Ma trận khoanh vùng xã khó khăn kép, điểm nóng Y tế - ANTT và Dự toán ngân sách động.",
                "legal_tag": "Power BI Page 4 • Ưu tiên chính sách & Ngân sách MTQG 1719",
                "fact": [
                    "<strong>4 Thẻ KPI:</strong> <em>Dự Toán Xóa Nhà Tạm (tỷ VNĐ)</em>, <em>Nhu Cầu Vốn Vay NHCSXH (tỷ VNĐ)</em>, <em>Xã Khó Khăn Kép</em> và <em>Sinh Con Tại Nhà</em>.",
                    "<strong>4 Khối phân tích hành động:</strong> (1) <em>Ma trận 4 Góc phần tư: Khoảng cách km vs Tỷ lệ nghèo cấp xã</em>, (2) <em>Bảng Cảnh báo đỏ Y tế sinh sản & DTTS rất ít người</em>, (3) <em>Pivot Giám sát điểm nóng Ma túy & HIV cấp Huyện - Xã</em>, (4) <em>Hộp Khung Hành Động Tham Mưu Chính Sách Động ([Dynamic Policy Recommendation Text])</em>."
                ],
                "analysis": [
                    "Cách đọc 'Ma trận 4 Góc phần tư': Trục ngang là cự ly từ xã đến trung tâm huyện (km), trục dọc là tỷ lệ hộ nghèo (%). Các xã rơi vào Góc phần tư thứ I (trên cùng bên phải: xa >20 km và nghèo >35% như Nam Ka, Ia Lốp, Cư Pui) là các 'Xã khó khăn kép' cần ưu tiên vốn số 1.",
                    "Cách dùng 'Khung Hành Động Tham Mưu Chính Sách': Đây là thẻ DAX thông minh tự động viết lại toàn bộ lời văn tham mưu và dự toán ngân sách mỗi khi bạn bấm chọn bất kỳ Huyện, Dân tộc hoặc Kỳ báo cáo nào."
                ],
                "impact": [
                    "Chuyển hóa toàn bộ dữ liệu thống kê ở 3 trang trước thành quyết định phân bổ ngân sách cụ thể tới từng xã và từng nhóm đối tượng."
                ],
                "recommendation": [
                    "Sau khi phát hiện xã/dân tộc trọng điểm trên Trang 4 Power BI, bạn có thể gõ tên xã/dân tộc đó vào Bàn Thẩm Định Web này để kéo thanh trượt What-If và in Tờ trình A4."
                ],
                "action_plan": {
                    "who": "UBND Tỉnh Đắk Lắk • Sở KH&ĐT • Sở Tài chính • Ban Dân tộc",
                    "what": "Khoanh vùng Xã khó khăn kép ở Góc phần tư I & xuất dự toán ngân sách theo kịch bản lọc",
                    "where_when": "Trang 4: Ưu tiên chính sách (Power BI Desktop)",
                    "budget_text": "Tổng dự toán Kỳ 2026: 5.119,65 tỷ VNĐ"
                }
            }
        elif topic == "formulas_dax":
            return {
                "headline": "Giải thích Phương pháp tính Chỉ số, Kiến trúc DAX Chống cộng trùng 3 kỳ và Định mức Ngân sách Nhà nước trên Power BI & Web.",
                "legal_tag": "Phương pháp luận Thống kê & DAX Semantic Model (100 Measures)",
                "fact": [
                    "<strong>Cơ chế Chống cộng trùng 3 kỳ (Anti-Triple Counting Gate):</strong> Hàm DAX <code>[Selected Period Order]</code> tự động khóa mặc định về kỳ mới nhất (<code>KY_2026 = 163.912 hộ</code>) khi người dùng không bấm chọn Slicer Kỳ báo cáo, ngăn chặn triệt để lỗi cộng dồn cả 3 kỳ thành 473.755 hộ.",
                    "<strong>Công thức các chỉ số cốt lõi:</strong> <em>Khoảng trống tín dụng (%)</em> = Số hộ có nhu cầu nhưng chưa vay được / Tổng số hộ có nhu cầu vay × 100 | <em>Tỷ số biết chữ Nam/Nữ</em> = Số nam biết chữ / Số nữ biết chữ | <em>Xã khó khăn kép</em> = Xã có khoảng cách đến huyện > 15 km VÀ tỷ lệ nghèo > 25%.",
                    "<strong>6 Định mức đơn giá ngân sách pháp lý (Kỳ 2026–2030):</strong> Xóa nhà tạm: <strong>90 triệu/căn</strong> (Dự án 1) | Tín dụng ưu đãi: <strong>65 triệu/hộ</strong> (NĐ 28) | Sinh kế hộ nghèo: <strong>30 triệu/hộ</strong> (Dự án 3) | Hố xí HVS: <strong>12 triệu/hộ</strong> (TC 17.5 NTM) | Đào tạo nghề: <strong>6 triệu/lao động</strong> (Dự án 5) | Sinh đẻ an toàn: <strong>4,5 triệu/ca</strong> (Dự án 7)."
                ],
                "analysis": [
                    "Mô hình dữ liệu được thiết kế theo chuẩn Kimball Star Schema (3 bảng Dim + 12 bảng Fact + 5 Analytical Views dùng hàm cửa sổ <code>LAG()</code> và <code>DENSE_RANK()</code>), đảm bảo số liệu giữa PostgreSQL, Power BI và Web Workbench khớp nhau 100% (sai số = 0).",
                    "Các nhãn biến động <code>▲/▼</code> trên thẻ KPI Power BI được tính tự động bằng cách lùi 1 bậc thứ tự kỳ báo cáo (<code>thu_tu_ky - 1</code>) và so sánh với ngưỡng mục tiêu pháp lý của từng giai đoạn."
                ],
                "impact": [
                    "Đảm bảo tính minh bạch, nhất quán và có cơ sở dữ liệu đối soát rõ ràng khi trình bày các chỉ số báo cáo."
                ],
                "recommendation": [
                    "Bạn có thể bấm sang Tab 3 ('Truy Vấn & Kiểm Toán CSDL') ngay trên màn hình Web này để xem trực tiếp câu lệnh SQL và nguồn bảng dữ liệu của từng chỉ số."
                ],
                "action_plan": {
                    "who": "Người làm phân tích dữ liệu & Đối soát nội bộ",
                    "what": "Đối soát chéo 100% giữa Power BI Semantic Model (100 DAX Measures) và PostgreSQL Views",
                    "where_when": "Đồng bộ trực tiếp trên CSDL daklak_analytics",
                    "budget_text": "Sai số đối soát = 0,00%"
                }
            }
        else:
            return {
                "headline": "Cẩm nang khai thác Hệ thống Báo cáo Power BI (4 Trang Chuyên Đề) & Phối hợp Bàn Thẩm Định Chính Sách Web.",
                "legal_tag": "Hướng dẫn Sử dụng Hệ thống Hỗ trợ Ra quyết định (DSS)",
                "fact": [
                    "<strong>Trang 1 — Dân số & Địa bàn:</strong> Xem quy mô 163.912 hộ DTTS, Treemap 15 huyện, Top 10 dân tộc, Tháp tuổi và tương quan Gánh nặng nuôi con vs Già hóa.",
                    "<strong>Trang 2 — Học vấn & Việc làm:</strong> Phân tích bẫy lao động chưa qua đào tạo CMKT (82,46%) kẹt trong nông nghiệp và nghịch lý biết chữ Nam/Nữ giữa nhóm Mẫu hệ (bản địa) vs Phụ hệ (di cư).",
                    "<strong>Trang 3 & Trang 4 — Điều kiện sống & Ưu tiên chính sách:</strong> Giám sát Nhà tạm, Vệ sinh NTM vs Internet, Khoảng trống tín dụng, Đất sản xuất, Ma trận 4 góc phần tư (Khoảng cách vs Nghèo), Điểm nóng Ma túy/HIV và Dự toán ngân sách động 5.119,65 tỷ VNĐ."
                ],
                "analysis": [
                    "<strong>Quy trình 3 bước sử dụng hiệu quả nhất:</strong> (Bước 1) Chọn <em>Kỳ báo cáo (2019 | 2024 | 2026)</em> trên Slicer góc trên bên phải Power BI -> (Bước 2) Bấm chọn 1 Huyện hoặc 1 Dân tộc trên biểu đồ để lọc chéo (Cross-filter) -> (Bước 3) Đọc hộp <em>Khung Hành Động Tham Mưu Chính Sách</em> ở Trang 4.",
                    "<strong>Khi nào dùng Power BI, khi nào dùng Web Workbench này?</strong> Power BI giúp nhìn tổng quan đa chiều và lọc chéo trực quan trên 4 trang; còn Web Workbench này dùng khi bạn muốn <em>Hỏi nhanh bằng tiếng Việt</em>, <em>Kéo thanh trượt mô phỏng ngân sách What-If</em> và <em>In Tờ trình tham mưu A4</em>."
                ],
                "impact": [
                    "Kết hợp liền mạch giữa Trực quan hóa Quản trị (Power BI) và Thẩm định Chính sách Chuyên sâu (Web Workbench) như một quy trình làm việc thực tế tại cơ quan tham mưu."
                ],
                "recommendation": [
                    "Bạn có thể hỏi chi tiết từng trang bằng cách gõ: <em>'Trang 1 Power BI xem gì?'</em>, <em>'Trang 2 đọc như thế nào?'</em>, <em>'Trang 3 có những biểu đồ gì?'</em>, <em>'Trang 4 dùng thế nào?'</em> hoặc <em>'Công thức tính chỉ số và DAX trên Power BI?'</em>."
                ],
                "action_plan": {
                    "who": "Người dùng Báo cáo • Chuyên viên Tham mưu • Lãnh đạo",
                    "what": "Khám phá 4 trang Power BI (Dân số -> Việc làm -> Điều kiện sống -> Ưu tiên chính sách)",
                    "where_when": "Đồng bộ số liệu 3 kỳ: 2019 • 2024 • 2026",
                    "budget_text": "4 Trang Báo cáo • 100 DAX Measures"
                }
            }

    # 1. CHUYÊN ĐỀ DỰ TOÁN NGÂN SÁCH (POLICY_BUDGET)
    elif code == "POLICY_BUDGET":
        tot_budget = float(df["tong_kinh_phi_can_phan_bo_ty_vnd"].sum()) if "tong_kinh_phi_can_phan_bo_ty_vnd" in df.columns else 0.0
        tot_obj = float(df["so_luong_doi_tuong_can_ho_tro"].sum()) if "so_luong_doi_tuong_can_ho_tro" in df.columns else 0.0
        scope_name = e.xa or e.huyen or (f"Dân tộc {e.dantoc}" if e.dantoc else "Toàn tỉnh Đắk Lắk")

        def _get_row_vals(ma_ct: str):
            if "ma_chitieu" in df.columns:
                sub = df[df["ma_chitieu"] == ma_ct]
                if not sub.empty:
                    r0 = sub.iloc[0]
                    return float(r0.get("tong_kinh_phi_can_phan_bo_ty_vnd", 0) or 0), int(float(r0.get("so_luong_doi_tuong_can_ho_tro", 0) or 0))
            return 0.0, 0

        b_cmkt, q_cmkt = _get_row_vals("TY_LE_CHUA_DAO_TAO_CMKT")
        b_td, q_td = _get_row_vals("KHOANG_TRONG_TIN_DUNG")
        b_ngheo, q_ngheo = _get_row_vals("TY_LE_HO_NGHEO")
        b_nha, q_nha = _get_row_vals("TY_LE_NHA_TAM")

        sorted_df = df.sort_values(by="tong_kinh_phi_can_phan_bo_ty_vnd", ascending=False) if "tong_kinh_phi_can_phan_bo_ty_vnd" in df.columns else df
        top1_name = str(sorted_df.iloc[0].get("ten_chitieu", "Đào tạo nghề")) if len(sorted_df) > 0 else "Đào tạo nghề"
        top1_val = float(sorted_df.iloc[0].get("tong_kinh_phi_can_phan_bo_ty_vnd", 0) or 0) if len(sorted_df) > 0 else 0.0
        top1_share = (top1_val / tot_budget * 100.0) if tot_budget > 0 else 0.0
        productive_share = ((b_cmkt + b_td) / tot_budget * 100.0) if tot_budget > 0 else 0.0

        if e.xa or e.huyen:
            who_str = f"UBND {e.xa or e.huyen} • Phòng Tài chính - Kế hoạch • NHCSXH"
            analysis_2 = f"Quy mô dự toán của {scope_name} được định lượng trực tiếp từ số hộ nghèo ({q_ngheo:,} hộ), nhà tạm ({q_nha:,} căn) và lao động thiếu chứng chỉ nghề trên địa bàn."
        elif e.dantoc:
            who_str = f"Ban Dân tộc Tỉnh • Sở LĐ-TB&XH • NHCSXH (Tổ dự án {e.dantoc})"
            analysis_2 = f"Đối với cộng đồng dân tộc {e.dantoc}, nhu cầu vốn phản ánh sát đặc thù sinh kế ({q_td:,} hộ cần vốn vay và {q_nha:,} hộ cần hỗ trợ nhà ở)."
        else:
            who_str = "Sở KH&ĐT • Ban Dân tộc • NHCSXH Tỉnh Đắk Lắk"
            analysis_2 = "Định mức đơn giá áp dụng theo chuẩn mới giai đoạn 2026–2030, chấm dứt cơ chế phân bổ bình quân cào bằng giữa các huyện."

        return {
            "headline": f"Tổng nhu cầu vốn đầu tư công {period_name} tại {scope_name} là {tot_budget:,.2f} tỷ VNĐ (phục vụ {tot_obj:,.0f} lượt đối tượng), trọng tâm số 1 là {top1_name} ({top1_share:.1f}%).",
            "legal_tag": "QĐ 1719/QĐ-TTg • NĐ 28/2022/NĐ-CP",
            "fact": [
                f"Đào tạo nghề (Dự án 5): <strong>{b_cmkt:,.2f} tỷ VNĐ</strong> ({q_cmkt:,} lao động chưa có chứng chỉ).",
                f"Tín dụng ưu đãi (NĐ 28): <strong>{b_td:,.2f} tỷ VNĐ</strong> ({q_td:,} hộ khát vốn sản xuất).",
                f"Hỗ trợ sinh kế & Xóa nhà tạm: <strong>{b_ngheo + b_nha:,.2f} tỷ VNĐ</strong> ({q_ngheo:,} hộ nghèo & {q_nha:,} nhà tạm)."
            ],
            "analysis": [
                f"Cấu trúc vốn tại <strong>{scope_name}</strong> ưu tiên mạnh cho nhóm tạo sinh kế bền vững (Đào tạo nghề + Tín dụng chiếm <strong>{productive_share:.1f}%</strong> tổng nguồn lực).",
                analysis_2
            ],
            "impact": [
                f"Đáp ứng đồng bộ cả 5 mũi nhọn giảm nghèo đa chiều tại {scope_name} thay vì chỉ cứu trợ ngắn hạn.",
                "Nếu giải ngân tín dụng tách rời khỏi đào tạo kỹ thuật canh tác sẽ làm giảm hiệu quả đồng vốn đầu tư."
            ],
            "recommendation": [
                f"Thực thi cơ chế 'Tích hợp kép' tại {scope_name}: Hộ nhận vốn vay NĐ 28 được ưu tiên cử lao động học nghề nông nghiệp Dự án 5.",
                f"Phân kỳ giải ngân ngay từ Quý I–II cho {q_nha:,} hộ nhà tạm và {q_ngheo:,} hộ nghèo để kịp thời vụ sản xuất."
            ],
            "action_plan": {
                "who": who_str,
                "what": "Giải ngân Tích hợp kép: Gắn hạn mức tín dụng NĐ 28 với chứng chỉ tập huấn kỹ thuật nông nghiệp Dự án 5",
                "where_when": f"Phạm vi: {scope_name} • Giải ngân từ Quý I đầu chu kỳ",
                "budget_text": f"{tot_budget:,.2f} tỷ VNĐ (NSTW 85% • Tỉnh đối ứng 15%)"
            }
        }

    # 2. CHUYÊN ĐỀ NGHÈO ĐA CHIỀU CẤP XÃ (POVERTY_COMMUNE / DEFAULT_MACRO_OVERVIEW)
    elif code in ("POVERTY_COMMUNE", "DEFAULT_MACRO_OVERVIEW"):
        is_single_commune = bool(e.xa) or (len(df) <= 3 and "ten_xa" in df.columns and len(df["ten_xa"].unique()) == 1)
        if is_single_commune:
            top_row = df.iloc[-1]
            ten_xa = str(top_row.get("ten_xa", "Xã khảo sát"))
            ten_huyen = str(top_row.get("ten_huyen", ""))
            ty_le = float(top_row.get("ty_le_ngheo_pct", 0) or 0)
            so_ngheo = int(float(top_row.get("so_ho_ngheo", 0) or 0))
            tong_ho = int(float(top_row.get("tong_ho_dtts", 0) or 0))
            bien_dong = float(top_row.get("bien_dong_ty_le_ngheo_pct", 0) or 0)
            km = float(top_row.get("km_den_trung_tam_huyen", 0) or 0)
            v_sinh_ke = float(top_row.get("du_toan_ngan_sach_sinh_ke_trieu_vnd", so_ngheo * 30.0) or 0)
            nhom_td = str(top_row.get("nhom_toc_do_giam_ngheo", ""))

            # Phân nhánh theo mức độ nghèo và xu hướng thực tế của xã
            if ty_le <= 15.0 and bien_dong < 0:
                headline = f"Điểm sáng {ten_xa} ({ten_huyen}): Tỷ lệ hộ nghèo đã kéo giảm về mức {ty_le:.2f}% ({so_ngheo:,} hộ, giảm {abs(bien_dong):.2f} điểm %), đạt chuẩn bền vững Khu vực III (<= 15%)."
                fact_bench = f"Tỷ lệ nghèo hiện tại: <strong>{ty_le:.2f}%</strong> ({so_ngheo:,}/{tong_ho:,} hộ DTTS) — <strong>thấp hơn {15.0 - ty_le:.2f} điểm %</strong> so với trần chuẩn 15%."
                analysis_list = [
                    f"Khoảng cách từ {ten_xa} đến trung tâm {ten_huyen} ở mức <strong>{km:.1f} km</strong>, hạ tầng giao thương thuận lợi giúp nông sản tiêu thụ tốt.",
                    f"Các chương trình tín dụng và chuyển đổi cây trồng những năm qua đã giúp địa bàn giảm thêm <strong>{abs(bien_dong):.2f} điểm %</strong> hộ nghèo."
                ]
                impact_list = [
                    f"Đóng vai trò địa bàn kiểu mẫu về giảm nghèo bền vững tại {ten_huyen}.",
                    f"Chỉ còn {so_ngheo:,} hộ nghèo thuộc diện yếu thế/neo đơn hoặc thiếu tư liệu sản xuất cần trợ giúp đặc thù."
                ]
                what_plan = f"Chuyển sang hỗ trợ chuỗi giá trị nông sản OCOP và kèm cặp riêng {so_ngheo:,} hộ nghèo còn lại"
            elif bien_dong >= 0:
                headline = f"Cảnh báo đỏ tại {ten_xa} ({ten_huyen}): Tỷ lệ nghèo ở mức {ty_le:.2f}% ({so_ngheo:,} hộ), phát sinh tăng/tái nghèo {bien_dong:+.2f} điểm % so với kỳ trước."
                fact_bench = f"Tỷ lệ nghèo hiện tại: <strong>{ty_le:.2f}%</strong> ({so_ngheo:,}/{tong_ho:,} hộ DTTS) — trạng thái: <strong>{nhom_td or 'Cảnh báo tái nghèo'}</strong>."
                analysis_list = [
                    f"Bẫy cự ly địa lý: {ten_xa} cách trung tâm huyện tới <strong>{km:.1f} km</strong> (cứ xa thêm 10 km làm tăng +5,13% tỷ lệ nghèo do chi phí vận tải và thương lái ép giá)." if km >= 20.0 else f"Dù cách trung tâm huyện {km:.1f} km, sinh kế của hộ dân tại {ten_xa} chịu tác động mạnh bởi thiếu đất canh tác và rủi ro thời tiết.",
                    "Khi áp chuẩn nghèo đa chiều giai đoạn mới, các hộ sát chuẩn bị rơi trở lại diện nghèo do thiếu hụt dịch vụ xã hội cơ bản (vệ sinh, việc làm)."
                ]
                impact_list = [
                    f"Nguy cơ hình thành 'lõi nghèo dai dẳng' tại {ten_xa} nếu không thay đổi phương thức hỗ trợ sinh kế.",
                    "Kéo lùi kết quả thực hiện mục tiêu giảm nghèo chung của toàn địa bàn huyện."
                ]
                what_plan = "Thành lập Tổ hợp tác bao tiêu nông sản tại chỗ & cấp giống cây trồng chịu hạn (Tiểu dự án 2 - DA 3)"
            else:
                headline = f"{ten_xa} ({ten_huyen}) giảm được {abs(bien_dong):.2f} điểm % hộ nghèo so với kỳ trước, nhưng tỷ lệ nghèo hiện vẫn ở mức cao ({ty_le:.2f}% — {so_ngheo:,} hộ)."
                fact_bench = f"Quy mô hộ nghèo: <strong>{so_ngheo:,}/{tong_ho:,} hộ DTTS ({ty_le:.2f}%)</strong> — cao hơn {ty_le - 15.0:.2f} điểm % so với ngưỡng chuẩn 15%."
                analysis_list = [
                    f"Cự ly đến trung tâm {ten_huyen} là <strong>{km:.1f} km</strong>; tốc độ giảm nghèo đạt <strong>{bien_dong:+.2f} điểm %</strong> ({nhom_td}).",
                    "Quy mô hộ nghèo tuyệt đối còn lớn do xuất phát điểm kinh tế thấp và lao động chủ yếu làm nông nghiệp thuần túy."
                ]
                impact_list = [
                    f"Áp lực giải ngân nguồn vốn sinh kế tại {ten_xa} còn lớn ({v_sinh_ke:,.0f} triệu VNĐ).",
                    "Các hộ mới thoát nghèo dễ bị tổn thương nếu giá vật tư phân bón tăng cao."
                ]
                what_plan = f"Giải ngân gói hỗ trợ sinh kế giống & vật tư nông nghiệp cho {so_ngheo:,} hộ nghèo (Dự án 3 - MTQG 1719)"

            return {
                "headline": headline,
                "legal_tag": "Nghị định 07/2021/NĐ-CP • Dự án 3 MTQG 1719",
                "fact": [
                    fact_bench,
                    f"Biến động qua các kỳ: <strong>{bien_dong:+.2f} điểm %</strong> | Cự ly giao thông: <strong>{km:.1f} km</strong>.",
                    f"Nhu cầu vốn sinh kế trực tiếp tại {ten_xa}: <strong>{v_sinh_ke:,.0f} triệu VNĐ</strong>."
                ],
                "analysis": analysis_list,
                "impact": impact_list,
                "recommendation": [
                    f"UBND {ten_huyen} và UBND {ten_xa} rà soát danh sách đích danh {so_ngheo:,} hộ nghèo theo nguyên nhân thiếu hụt.",
                    f"Triển khai gói sinh kế <strong>{v_sinh_ke:,.0f} triệu VNĐ</strong> (30 triệu VNĐ/hộ) gắn với cam kết đầu ra sản phẩm."
                ],
                "action_plan": {
                    "who": f"UBND {ten_huyen} • UBND {ten_xa} • Phòng NN&PTNT",
                    "what": what_plan,
                    "where_when": f"Tại {ten_xa} ({so_ngheo:,} hộ nghèo, cách huyện {km:.1f} km) • Quý I–II",
                    "budget_text": f"{v_sinh_ke:,.0f} triệu VNĐ (30 triệu VNĐ/hộ nghèo)"
                }
            }
        else:
            # Đang xem danh sách nhiều xã (Toàn tỉnh hoặc trong 1 Huyện)
            scope_title = e.huyen or "Toàn tỉnh Đắk Lắk"
            worst_row = df.iloc[0]
            best_row = df.iloc[-1]
            avg_poverty = float(df["ty_le_ngheo_pct"].mean()) if "ty_le_ngheo_pct" in df.columns else 0.0
            sum_poor_hh = int(float(df["so_ho_ngheo"].sum())) if "so_ho_ngheo" in df.columns else 0
            stagnant_df = df[df["bien_dong_ty_le_ngheo_pct"] >= 0] if "bien_dong_ty_le_ngheo_pct" in df.columns else pd.DataFrame()
            stagnant_names = ", ".join(stagnant_df["ten_xa"].head(3).tolist()) if not stagnant_df.empty else "không có xã nào"
            tot_budget_ty = (sum_poor_hh * 30.0) / 1000.0

            return {
                "headline": f"Rà soát {len(df)} xã thuộc {scope_title}: Tỷ lệ nghèo trung bình nhóm ở mức {avg_poverty:.2f}% ({sum_poor_hh:,} hộ nghèo), cao nhất tại {worst_row.get('ten_xa')} ({float(worst_row.get('ty_le_ngheo_pct', 0)):.2f}%).",
                "legal_tag": "Nghị định 07/2021/NĐ-CP • CTMTQG Giảm nghèo",
                "fact": [
                    f"Xã nghèo cao nhất danh sách: <strong>{worst_row.get('ten_xa')} ({worst_row.get('ten_huyen')})</strong> ở mức <strong>{float(worst_row.get('ty_le_ngheo_pct', 0)):.2f}%</strong> (cách huyện {float(worst_row.get('km_den_trung_tam_huyen', 0) or 0):.1f} km).",
                    f"Xã thấp nhất trong nhóm hiển thị: <strong>{best_row.get('ten_xa')}</strong> ở mức <strong>{float(best_row.get('ty_le_ngheo_pct', 0)):.2f}%</strong>.",
                    f"Cảnh báo tái nghèo/dậm chân: Ghi nhận <strong>{len(stagnant_df)} xã</strong> có biến động >= 0% ({stagnant_names})."
                ],
                "analysis": [
                    f"Tại {scope_title}, các xã có tỷ lệ nghèo >35% đều nằm ở vành đai xa trung tâm huyện từ 22–50 km (tương quan +5,13% nghèo cho mỗi 10 km khoảng cách).",
                    "Sự phân hóa tốc độ giảm nghèo đòi hỏi phải phân bổ nguồn lực theo trọng số khó khăn thay vì chia đều theo đầu xã."
                ],
                "impact": [
                    f"Tổng cộng <strong>{sum_poor_hh:,} hộ nghèo</strong> trong nhóm {len(df)} xã này cần được can thiệp sinh kế để tránh tụt hậu.",
                    "Nguy cơ trượt mục tiêu giảm nghèo giai đoạn 2026–2030 tại các xã vùng đệm nếu không tháo gỡ điểm nghẽn tiêu thụ nông sản."
                ],
                "recommendation": [
                    f"Tập trung nguồn vốn Dự án 3 ưu tiên số 1 cho <strong>{worst_row.get('ten_xa')}</strong> và {len(stagnant_df)} xã có dấu hiệu tái nghèo.",
                    f"Xây dựng mô hình hợp tác xã thu mua nông sản cụm liên xã để giảm chi phí vận tải cho các xã xa trên 20 km."
                ],
                "action_plan": {
                    "who": f"Sở NN&PTNT • Ban Dân tộc • UBND {e.huyen or 'các huyện trọng điểm'}",
                    "what": "Phân bổ vốn sinh kế Dự án 3 theo hệ số khoảng cách & quy mô hộ nghèo thực tế",
                    "where_when": f"Trọng tâm {len(df)} xã thuộc {scope_title} (ưu tiên {worst_row.get('ten_xa')})",
                    "budget_text": f"{tot_budget_ty:,.2f} tỷ VNĐ ({sum_poor_hh:,} hộ × 30 triệu VNĐ)"
                }
            }

    # 3. CHUYÊN ĐỀ XÓA NHÀ TẠM, DỘT NÁT (HOUSING_POVERTY)
    elif code == "HOUSING_POVERTY":
        if len(e.dantoc_list) >= 2 and len(df) >= 2:
            r1 = df.iloc[0]
            r2 = df.iloc[1]
            dt1_name = pretty_entity(r1.get("ten_dantoc"))
            dt2_name = pretty_entity(r2.get("ten_dantoc"))
            cnt1 = int(float(r1.get("so_ho_nha_tam_don_so", 0) or 0))
            pct1 = float(r1.get("ty_le_nha_tam_pct", 0) or 0)
            tot1 = int(float(r1.get("tong_ho_co_nha", 0) or 0))
            cnt2 = int(float(r2.get("so_ho_nha_tam_don_so", 0) or 0))
            pct2 = float(r2.get("ty_le_nha_tam_pct", 0) or 0)
            tot2 = int(float(r2.get("tong_ho_co_nha", 0) or 0))
            tot_both = cnt1 + cnt2
            budget_both = tot_both * 90.0 / 1000.0

            ratio_txt = f"cao gấp {(pct1/pct2):.2f} lần" if pct2 > 0 and pct1 >= pct2 else (f"thấp hơn {(pct2/pct1):.2f} lần" if pct1 > 0 else "")

            return {
                "headline": f"Đối sánh điều kiện nhà ở ({period_name}): Tỷ lệ nhà tạm của người {dt1_name} ({pct1:.2f}%) {ratio_txt} người {dt2_name} ({pct2:.2f}%), tổng nhu cầu kiên cố hóa là {tot_both:,} căn ({budget_both:,.2f} tỷ VNĐ).",
                "legal_tag": "Dự án 1 - MTQG 1719 • Tiêu chí số 9 NTM",
                "fact": [
                    f"Người <strong>{dt1_name}</strong>: Có <strong>{cnt1:,} hộ</strong> ở nhà tạm ({pct1:.2f}% trên {tot1:,} hộ).",
                    f"Người <strong>{dt2_name}</strong>: Có <strong>{cnt2:,} hộ</strong> ở nhà tạm ({pct2:.2f}% trên {tot2:,} hộ).",
                    f"Tổng số nhà tạm của cả 2 cộng đồng: <strong>{tot_both:,} căn</strong> (nhu cầu vốn Dự án 1 là {budget_both:,.2f} tỷ VNĐ)."
                ],
                "analysis": [
                    f"Đặc thù điều kiện cư trú: Cả hai dân tộc {dt1_name} và {dt2_name} đều sinh sống tại các buôn làng vùng sâu, tỷ lệ nhà tạm liên quan mật thiết đến khả năng tiếp cận vốn vay ưu đãi để đại tu, nâng cấp khung nhà sàn gỗ.",
                    "Giá vật liệu xây dựng vận chuyển vào các buôn xa tăng 18–25% khiến các hộ nghèo không có vốn đối ứng nếu chỉ trông chờ vào mức hỗ trợ đơn lẻ."
                ],
                "impact": [
                    f"{tot_both:,} hộ gia đình đối mặt với nguy cơ mất an toàn khi bước vào mùa mưa bão Tây Nguyên.",
                    "Làm chậm tiến độ hoàn thành Tiêu chí số 9 (Nhà ở dân cư) tại các xã có đông đồng bào sinh sống."
                ],
                "recommendation": [
                    f"Phân bổ gói vốn xóa nhà tạm 90 triệu VNĐ/căn kết hợp huy động lực lượng đoàn thể hỗ trợ ngày công thi công.",
                    f"Ưu tiên giải ngân trước cho các hộ thuộc cộng đồng có tỷ lệ nhà tạm cao hơn ({dt1_name if pct1 >= pct2 else dt2_name})."
                ],
                "action_plan": {
                    "who": "Sở Xây dựng • MTTQ Tỉnh • UBND các huyện liên quan",
                    "what": f"Xóa dứt điểm {tot_both:,} căn nhà tạm cho đồng bào {dt1_name} và {dt2_name}",
                    "where_when": f"Địa bàn cư trú của người {dt1_name} và {dt2_name} • Bàn giao trước mùa mưa",
                    "budget_text": f"{budget_both:,.2f} tỷ VNĐ ({tot_both:,} căn × 90 triệu VNĐ)"
                }
            }
        elif e.dantoc and len(df) > 0:
            latest = df.iloc[-1]
            first = df.iloc[0]
            cur_cnt = int(float(latest.get("so_ho_nha_tam_don_so", 0) or 0))
            cur_pct = float(latest.get("ty_le_nha_tam_pct", 0) or 0)
            diff_cnt = int(float(latest.get("chenh_lech_nha_tam", 0) or 0))
            first_cnt = int(float(first.get("so_ho_nha_tam_don_so", 0) or 0))
            tot_ho = int(float(latest.get("tong_ho_co_nha", 0) or 0))
            nhom_goc = str(latest.get("nhom_nguon_goc", ""))

            # Trường hợp ĐÃ XÓA TRẮNG 100% NHÀ TẠM (cur_cnt == 0, ví dụ: Chơ Ro, Hoa...)
            if cur_cnt == 0:
                return {
                    "headline": f"Điểm sáng hoàn thành mục tiêu: Dân tộc {eth_disp} ({tot_ho:,} hộ) đã xóa trắng 100% nhà tạm, dột nát (về đúng 0 căn trong {period_name}).",
                    "legal_tag": "Hoàn thành Dự án 1 - MTQG 1719 • Đạt TC số 9 NTM",
                    "fact": [
                        f"Số hộ ở nhà tạm hiện tại ({period_name}): <strong>0 căn (0,00%)</strong> trên tổng số {tot_ho:,} hộ.",
                        f"Lộ trình giảm lũy kế: Đã xóa dứt điểm <strong>{first_cnt:,} căn nhà tạm</strong> so với các kỳ trước.",
                        f"Phân nhóm dân tộc: <strong>{nhom_goc}</strong> {'(DTTS rất ít người được ưu tiên đặc biệt)' if latest.get('la_dtts_it_nguoi') else ''}."
                    ],
                    "analysis": [
                        f"Nguồn vốn Dự án 1 (QĐ 1719) kết hợp Quỹ Vì người nghèo đã giải quyết triệt để 100% nhu cầu nhà ở cho đồng bào {eth_disp}.",
                        "Toàn bộ các hộ đã chuyển sang nhà kiên cố hoặc bán kiên cố đạt chuẩn '3 cứng' (nền cứng, khung cứng, mái cứng)."
                    ],
                    "impact": [
                        f"Chấm dứt hoàn toàn rủi ro sập tốc mái nhà mùa mưa bão đối với {tot_ho:,} hộ đồng bào {eth_disp}.",
                        "Không còn phát sinh nhu cầu ngân sách xây mới nhà tạm trong kỳ kế hoạch này (tiết kiệm ngân sách để chuyển sang hỗ trợ sinh kế)."
                    ],
                    "recommendation": [
                        f"Chuyển trọng tâm chính sách tại cộng đồng {eth_disp} từ 'An cư' sang 'Lạc nghiệp' (vay vốn NĐ 28 và đào tạo nghề Dự án 5).",
                        "Hướng dẫn các hộ gia đình duy tu, bảo dưỡng công trình nhà ở và vệ sinh môi trường khuôn viên."
                    ],
                    "action_plan": {
                        "who": "UBND cấp xã • Ban Dân tộc • NHCSXH Tỉnh",
                        "what": f"Đã hoàn thành 100% nhà ở — Chuyển sang cấp vốn tín dụng sản xuất & khuyến nông cho {tot_ho:,} hộ {eth_disp}",
                        "where_when": f"Cộng đồng dân tộc {eth_disp} • Duy trì bền vững giai đoạn 2026–2030",
                        "budget_text": "0,00 tỷ VNĐ xây nhà mới (Đã hoàn thành 100%)"
                    }
                }
            else:
                budget_ty = cur_cnt * 90.0 / 1000.0
                is_indigenous = "bản địa" in nhom_goc.lower()
                return {
                    "headline": f"Dân tộc {eth_disp}: Hiện còn {cur_cnt:,} hộ ở nhà tạm, đơn sơ ({cur_pct:.2f}% trên tổng {tot_ho:,} hộ), đã giảm {abs(diff_cnt):,} căn so với kỳ trước.",
                    "legal_tag": "Dự án 1 - MTQG 1719 • Tiêu chí số 9 NTM",
                    "fact": [
                        f"Quy mô nhà tạm còn tồn đọng của người {eth_disp}: <strong>{cur_cnt:,} căn</strong> (tỷ lệ <strong>{cur_pct:.2f}%</strong>).",
                        f"Tiến độ xóa nhà tạm: Giảm <strong>{abs(diff_cnt):,} căn</strong> so với kỳ liền kề (lũy kế giảm từ {first_cnt:,} xuống {cur_cnt:,} căn).",
                        f"Thứ hạng ưu tiên về quy mô nhà tạm kỳ này: <strong>Hạng #{int(float(latest.get('xep_hang_nha_tam_ky', 1) or 1))}</strong> toàn tỉnh."
                    ],
                    "analysis": [
                        (
                            f"Đặc thù nhóm bản địa ({eth_disp}): Nhiều hộ sinh sống trong các nếp nhà sàn gỗ, vách ván truyền thống đã xuống cấp theo thời gian nhưng thiếu vốn tích lũy để đại tu kiên cố."
                            if is_indigenous
                            else f"Đặc thù nhóm di cư ({eth_disp}): Một bộ phận hộ dân cư trú tại vùng sâu chưa hoàn tất thủ tục cấp giấy chứng nhận đất ở, gây vướng mắc khi giải ngân vốn xây nhà."
                        ),
                        "Giá vật liệu xây dựng (xi măng, sắt thép, cát) vận chuyển vào các thôn/buôn vùng xa đội lên 18–25% so với khu vực trung tâm."
                    ],
                    "impact": [
                        f"{cur_cnt:,} hộ đồng bào {eth_disp} đối mặt nguy cơ mất an toàn về chỗ ở trong mùa mưa lũ Tây Nguyên (tháng 9–11).",
                        "Ảnh hưởng trực tiếp đến điều kiện học tập của trẻ em và tiêu chí Nhà ở dân cư (TC số 9 NTM)."
                    ],
                    "recommendation": [
                        f"Tháo gỡ thủ tục pháp lý đất ở và áp dụng mẫu nhà '3 cứng' phù hợp tập quán sinh hoạt của người {eth_disp}.",
                        f"Phân bổ <strong>{budget_ty:,.2f} tỷ VNĐ</strong> kết hợp huy động ngày công thanh niên, lực lượng vũ trang địa phương."
                    ],
                    "action_plan": {
                        "who": "Sở Xây dựng • Ủy ban MTTQ Tỉnh • UBND các huyện",
                        "what": f"Hỗ trợ xây dựng mới/sửa chữa nhà '3 cứng' cho {cur_cnt:,} hộ đồng bào {eth_disp}",
                        "where_when": f"Trọng điểm các buôn/thôn có đông người {eth_disp} • Hoàn thành trước tháng 9",
                        "budget_text": f"{budget_ty:,.2f} tỷ VNĐ ({cur_cnt:,} căn × 90 triệu VNĐ)"
                    }
                }
        else:
            col_nha = "so_ho_nha_tam_don_so" if "so_ho_nha_tam_don_so" in df.columns else "tong_ho_nha_tam"
            tot_temp = int(float(df[col_nha].sum())) if col_nha in df.columns else 0
            r0 = df.iloc[0] if len(df) > 0 else {}
            r1 = df.iloc[1] if len(df) > 1 else {}
            top1_lbl = pretty_entity(r0.get("ten_dantoc", r0.get("ten_huyen", "Nhóm 1")))
            top1_cnt = int(float(r0.get(col_nha, 0) or 0))
            top2_lbl = pretty_entity(r1.get("ten_dantoc", r1.get("ten_huyen", "")))
            top2_cnt = int(float(r1.get(col_nha, 0) or 0))
            budget_ty = tot_temp * 90.0 / 1000.0

            return {
                "headline": f"Tổng hợp {len(df)} nhóm dẫn đầu ({period_name}): Còn {tot_temp:,} căn nhà tạm cần kiên cố hóa, tập trung cao nhất ở {top1_lbl} ({top1_cnt:,} căn){f' và {top2_lbl} ({top2_cnt:,} căn)' if top2_lbl else ''}.",
                "legal_tag": "Dự án 1 - MTQG 1719 • Tiêu chí số 9 NTM",
                "fact": [
                    f"Tổng số nhà tạm trong nhóm thống kê: <strong>{tot_temp:,} căn</strong> (nhu cầu vốn <strong>{budget_ty:,.2f} tỷ VNĐ</strong>).",
                    f"Đứng đầu về quy mô tuyệt đối: <strong>{top1_lbl} ({top1_cnt:,} căn)</strong>{f', tiếp theo là <strong>{top2_lbl} ({top2_cnt:,} căn)</strong>' if top2_lbl else ''}.",
                    "Trong khi đó, nhóm DTTS rất ít người (như Chơ Ro) đã hoàn thành xóa trắng 100% nhà tạm về 0 căn."
                ],
                "analysis": [
                    "Số lượng nhà tạm tồn đọng tỷ lệ thuận với quy mô dân số của các dân tộc lớn (Ê Đê, M'Nông, Gia Rai) và mức độ chia cắt địa hình tại các xã vùng sâu.",
                    "Vướng mắc lớn nhất khi triển khai diện rộng là quy hoạch đất ở hợp pháp và nguồn vốn đối ứng của các hộ nghèo kịch khung."
                ],
                "impact": [
                    f"Giải quyết dứt điểm {tot_temp:,} căn nhà tạm sẽ tạo bước đột phá về an sinh xã hội và diện mạo Nông thôn mới toàn tỉnh.",
                    "Nếu chậm giải ngân trước Quý III sẽ bị gián đoạn thi công do bước vào mùa mưa Tây Nguyên."
                ],
                "recommendation": [
                    f"Giao chỉ tiêu xóa nhà tạm bắt buộc theo từng quý, ưu tiên phân bổ 70% nguồn vốn đợt 1 cho nhóm <strong>{top1_lbl}</strong>{f' và <strong>{top2_lbl}</strong>' if top2_lbl else ''}.",
                    "Kết hợp nguồn vốn ngân sách (90 triệu/căn) với nguồn vận động xã hội hóa của MTTQ tỉnh."
                ],
                "action_plan": {
                    "who": "Sở Xây dựng • Ủy ban MTTQ Tỉnh • UBND 15 Huyện/TX/TP",
                    "what": "Chiến dịch cao điểm kiên cố hóa nhà ở '3 cứng' & tháo gỡ đất ở cho hộ DTTS nghèo",
                    "where_when": f"Ưu tiên {top1_lbl}{f', {top2_lbl}' if top2_lbl else ''} • Bàn giao trước mùa mưa bão",
                    "budget_text": f"{budget_ty:,.2f} tỷ VNĐ ({tot_temp:,} căn × 90 triệu VNĐ)"
                }
            }

    # 4. CHUYÊN ĐỀ VỆ SINH NTM & CHUYỂN ĐỔI SỐ (SANITATION_DIGITAL / DISTRICT_OVERVIEW)
    elif code in ("SANITATION_DIGITAL", "DISTRICT_OVERVIEW"):
        if e.huyen and len(df) > 0:
            row = df.iloc[-1]
            h_name = str(row.get("ten_huyen", e.huyen))
            ho_dtts = int(float(row.get("tong_ho_dtts_huyen", 0) or 0))
            nuoc = float(row.get("ty_le_nuoc_hvs_bq_pct", 0) or 0)
            hoxi = float(row.get("ty_le_ho_xi_hvs_bq_pct", 0) or 0)
            diff_hoxi = float(row.get("bien_dong_ho_xi_hvs_pct", 0) or 0)
            net = float(row.get("ty_le_internet_huyen_pct", 0) or 0)
            diff_net = float(row.get("bien_dong_internet_pct", 0) or 0)

            # Phân nhánh theo thực tế Huyện ĐẠT CHUẨN (>= 70%) vs CHƯA ĐẠT CHUẨN (< 70%)
            if hoxi >= 70.0:
                return {
                    "headline": f"Điểm sáng hạ tầng tại {h_name}: Cả hai chỉ tiêu Hố xí hợp vệ sinh ({hoxi:.2f}%) và Phủ sóng Internet ({net:.2f}%) đều vượt ngưỡng chuẩn Nông thôn mới & Đề án 06.",
                    "legal_tag": "Đạt chuẩn TC 17.5 NTM (>=70%) • Đề án 06 (>=80%)",
                    "fact": [
                        f"Tỷ lệ Hố xí hợp vệ sinh tại {h_name}: <strong>{hoxi:.2f}%</strong> (tăng {diff_hoxi:+.2f} pp, <strong>vượt {hoxi - 70.0:.2f} điểm %</strong> so với chuẩn NTM).",
                        f"Tỷ lệ Nước sinh hoạt hợp vệ sinh: <strong>{nuoc:.2f}%</strong> trên tổng số {ho_dtts:,} hộ DTTS.",
                        f"Tỷ lệ kết nối Internet hộ gia đình: <strong>{net:.2f}%</strong> (tăng {diff_net:+.2f} pp — <em>{row.get('trang_thai_chuyendoiso_dean06', 'Sẵn sàng')}</em>)."
                    ],
                    "analysis": [
                        f"Hạ tầng kinh tế - xã hội tại {h_name} phát triển đồng bộ; đồng bào DTTS có ý thức cao trong đầu tư công trình vệ sinh khép kín.",
                        "Mạng lưới cáp quang và 4G phủ kín các thôn/buôn giúp thu hẹp khoảng cách số giữa vùng DTTS và khu vực đô thị."
                    ],
                    "impact": [
                        f"Bảo đảm vững chắc Tiêu chí 17 (Môi trường) để các xã thuộc {h_name} tiến lên Nông thôn mới nâng cao / kiểu mẫu.",
                        "Thuận lợi triển khai 100% thủ tục hành chính công trực tuyến và thanh toán nông sản không dùng tiền mặt."
                    ],
                    "recommendation": [
                        f"Duy trì kiểm tra chất lượng nguồn nước sinh hoạt ({nuoc:.2f}%) và nhân rộng mô hình 'Buôn làng số - Xanh - Sạch - Đẹp' tại {h_name}.",
                        "Phát huy Tổ công nghệ số cộng đồng hướng dẫn người dân khai thác sàn thương mại điện tử nông sản."
                    ],
                    "action_plan": {
                        "who": f"UBND {h_name} • Phòng TN&MT • Tổ Công nghệ số cộng đồng",
                        "what": "Duy trì chuẩn NTM nâng cao & phổ cập dịch vụ công trực tuyến mức độ 4 cho hộ DTTS",
                        "where_when": f"Toàn bộ {ho_dtts:,} hộ DTTS thuộc {h_name} • Thường xuyên hàng năm",
                        "budget_text": "Nguồn kinh phí sự nghiệp môi trường & chuyển đổi số thường xuyên"
                    }
                }
            else:
                gap_pct = 70.0 - hoxi
                missing_hh = int(round(ho_dtts * (gap_pct / 100.0)))
                budget_ty = (missing_hh * 12.0) / 1000.0
                return {
                    "headline": f"Điểm nghẽn tại {h_name}: Phủ sóng Internet đã đạt {net:.2f}%, nhưng Hố xí hợp vệ sinh mới chỉ đạt {hoxi:.2f}% (còn thiếu {gap_pct:.2f} điểm % để chạm chuẩn NTM 70%).",
                    "legal_tag": "Cảnh báo TC 17.5 NTM (<70%) • Đề án 06/CP",
                    "fact": [
                        f"Tỷ lệ Hố xí hợp vệ sinh ({h_name}): <strong>{hoxi:.2f}%</strong> (biến động {diff_hoxi:+.2f} pp — <em>{row.get('trang_thai_ntm_tc17', 'Chưa đạt chuẩn')}</em>).",
                        f"Tỷ lệ Nước hợp vệ sinh: <strong>{nuoc:.2f}%</strong> | Kết nối Internet: <strong>{net:.2f}%</strong> (+{diff_net:.2f} pp).",
                        f"Quy mô thiếu hụt cần bù đắp tại {h_name}: Khoảng <strong>{missing_hh:,} hộ DTTS</strong> cần xây mới nhà tiêu hợp vệ sinh."
                    ],
                    "analysis": [
                        f"Nghịch lý 'Công nghệ đi trước vệ sinh' tại {h_name}: Hộ dân sẵn sàng chi tiền mua smartphone/lắp mạng ({net:.2f}%) nhưng vẫn giữ thói quen vệ sinh cũ ngoài vườn rẫy.",
                        "Địa hình đồi dốc hoặc vùng trũng ngập mùa mưa khiến chi phí xây bể tự hoại truyền thống bằng gạch cao quá khả năng tự đóng góp của hộ nghèo."
                    ],
                    "impact": [
                        f"Làm đình trệ lộ trình công nhận đạt chuẩn Nông thôn mới của các xã thuộc {h_name} do liệt Tiêu chí 17.5.",
                        "Nguy cơ thẩm thấu chất thải vào mạch nước ngầm sinh hoạt, gây bệnh tiêu hóa và giun sán ở trẻ em."
                    ],
                    "recommendation": [
                        f"Triển khai gói hỗ trợ lắp đặt 'Bể phốt tự hoại Composite đúc sẵn' cho {missing_hh:,} hộ thiếu hụt tại {h_name}.",
                        "Gắn tiêu chí có nhà tiêu hợp vệ sinh vào bình xét Gia đình văn hóa và hương ước thôn/buôn."
                    ],
                    "action_plan": {
                        "who": f"VP Điều phối NTM Tỉnh • Sở Y tế • UBND {h_name}",
                        "what": f"Hỗ trợ vật tư lắp đặt bể tự hoại Composite đúc sẵn cho {missing_hh:,} hộ DTTS chưa có hố xí HVS",
                        "where_when": f"Các xã vùng trũng vệ sinh thuộc {h_name} • Thi công mùa khô",
                        "budget_text": f"{budget_ty:,.2f} tỷ VNĐ ({missing_hh:,} hộ × 12,0 triệu VNĐ)"
                    }
                }
        else:
            # Đang xem toàn bộ 15 huyện
            r_worst = df.iloc[0]
            r_best = df.iloc[-1]
            under_70_df = df[df["ty_le_ho_xi_hvs_bq_pct"] < 70.0] if "ty_le_ho_xi_hvs_bq_pct" in df.columns else pd.DataFrame()
            under_names = ", ".join([str(x).replace("Huyện ", "") for x in under_70_df["ten_huyen"].head(4).tolist()]) if not under_70_df.empty else "Không có"

            return {
                "headline": f"Đối sánh 15 Huyện/TX/TP ({period_name}): Có {len(under_70_df)}/{len(df)} địa bàn chưa đạt chuẩn Hố xí hợp vệ sinh 70% (thấp nhất tại {r_worst.get('ten_huyen')} với {float(r_worst.get('ty_le_ho_xi_hvs_bq_pct', 0)):.2f}%).",
                "legal_tag": "QĐ 318/QĐ-TTg (TC 17.5 NTM) • Đề án 06/CP",
                "fact": [
                    f"Vùng trũng thấp nhất tỉnh: <strong>{r_worst.get('ten_huyen')} ({float(r_worst.get('ty_le_ho_xi_hvs_bq_pct', 0)):.2f}%)</strong>, dù Internet tại đây đã đạt tới <strong>{float(r_worst.get('ty_le_internet_huyen_pct', 0)):.2f}%</strong>.",
                    f"Địa bàn cao nhất trong danh sách: <strong>{r_best.get('ten_huyen')} ({float(r_best.get('ty_le_ho_xi_hvs_bq_pct', 0)):.2f}%)</strong>.",
                    f"Số huyện chưa đạt ngưỡng 70% TC17 NTM: <strong>{len(under_70_df)} huyện</strong> ({under_names})."
                ],
                "analysis": [
                    "Sự bất cân xứng rõ rệt giữa hạ tầng viễn thông (phủ rộng khắp 15 huyện) và hạ tầng vệ sinh hộ gia đình tại các huyện vùng sâu Đông Nam tỉnh.",
                    "Các chương trình hỗ trợ trước đây nặng về tuyên truyền, thiếu cơ chế hỗ trợ trực tiếp vật tư bể tự hoại giá rẻ cho hộ nghèo."
                ],
                "impact": [
                    f"Nếu không xóa vùng trũng tại {under_names}, tỉnh sẽ khó hoàn thành chỉ tiêu 100% xã đạt chuẩn Tiêu chí 17 Môi trường.",
                    "Gây áp lực bệnh tật truyền nhiễm nguồn nước tại các lưu vực sông suối vùng nông thôn."
                ],
                "recommendation": [
                    f"Khoanh vùng tập trung 80% nguồn vốn Nước sạch & Vệ sinh nông thôn cho <strong>{under_names}</strong>.",
                    "Áp dụng mô hình hỗ trợ vật tư bể phốt đúc sẵn (12 triệu VNĐ/hộ), người dân đối ứng ngày công đào lắp."
                ],
                "action_plan": {
                    "who": "Sở NN&PTNT (VP Điều phối NTM) • Sở Y tế • UBND các huyện vùng trũng",
                    "what": "Chiến dịch xóa vùng trũng Hố xí HVS bằng bể tự hoại Composite đúc sẵn",
                    "where_when": f"Trọng điểm tại {under_names} • Triển khai cao điểm mùa khô",
                    "budget_text": "Định mức 12,0 triệu VNĐ/hộ (Vốn MTQG NTM & 1719)"
                }
            }

    # 5. CHUYÊN ĐỀ AN NINH TRẬT TỰ (MA TÚY/HIV) & Y TẾ SINH SẢN (VULNERABILITY_HEALTH)
    elif code == "VULNERABILITY_HEALTH":
        row = df.iloc[-1] if ((e.xa or e.dantoc) and len(df) > 0) else df.iloc[0]
        target_lbl = str(row.get("ten_doi_tuong", "Điểm nóng"))
        risk_group = str(row.get("phan_nhom_rui_ro", ""))
        scope_grp = str(row.get("pham_vi_nhom", ""))
        main_val = int(float(row.get("chi_so_rui_ro_chinh", 0) or 0))
        sub_val = int(float(row.get("chi_so_rui_ro_phu", 0) or 0))
        diff_val = int(float(row.get("bien_dong_rui_ro_chinh", 0) or 0))
        diff_pct = float(row.get("ty_le_giam_rui_ro_pct", 0) or 0)

        is_birth = ("sinh" in risk_group.lower()) or ("y tế" in risk_group.lower()) or ("sinh_tai_nha" in e.metric_keys and "ma_tuy_hiv" not in e.metric_keys) or bool(e.dantoc)

        if is_birth:
            budget_m = main_val * 4.5
            return {
                "headline": f"Cảnh báo Y tế sinh sản [{target_lbl}]: Ghi nhận {main_val:,} ca sinh con tại nhà (có {sub_val:,} ca không bà đỡ), đã giảm {abs(diff_pct):.2f}% ({diff_val:+,} ca) so với kỳ trước.",
                "legal_tag": "Dự án 7 - MTQG 1719 (Chăm sóc sức khỏe & Chống suy dinh dưỡng)",
                "fact": [
                    f"Cộng đồng giám sát: <strong>{target_lbl}</strong> ({scope_grp}).",
                    f"Số ca sinh con tại nhà kỳ này: <strong>{main_val:,} ca</strong> (giảm <strong>{abs(diff_val):,} ca</strong>, tương ứng {diff_pct:+.2f}%).",
                    f"Ca sinh nguy cơ đặc biệt cao (không có cán bộ y tế/bà đỡ): <strong>{sub_val:,} ca</strong> ({(sub_val/main_val*100.0) if main_val > 0 else 0:.1f}%)."
                ],
                "analysis": [
                    f"Đồng bào {target_lbl} cư trú tại các điểm dân cư vùng sâu cách xa Trạm Y tế xã, kết hợp tâm lý e ngại sinh đẻ tại bệnh viện và rào cản ngôn ngữ.",
                    "Mạng lưới Cô đỡ thôn bản đã giúp kéo giảm số ca sinh tại nhà qua các kỳ, nhưng kinh phí phụ cấp hiện còn thấp."
                ],
                "impact": [
                    f"Đe dọa trực tiếp tính mạng của {sub_val:,} sản phụ và trẻ sơ sinh sinh không có người đỡ chuyên môn (nguy cơ băng huyết, uốn ván rốn).",
                    "Làm tăng tỷ lệ suy dinh dưỡng thể thấp còi ở trẻ em DTTS dưới 5 tuổi."
                ],
                "recommendation": [
                    f"Kiện toàn đội ngũ Cô đỡ thôn bản là người {target_lbl} tại chỗ và cấp phát 'Gói đỡ đẻ sạch' cho các điểm dân cư xa trạm y tế.",
                    f"Giải ngân gói hỗ trợ chi phí đi lại, ăn ở cho sản phụ nghèo đến sinh tại cơ sở y tế (<strong>{budget_m:,.1f} triệu VNĐ</strong>)."
                ],
                "action_plan": {
                    "who": "Sở Y tế (CDC Đắk Lắk) • Trung tâm Y tế huyện • Trạm Y tế xã",
                    "what": f"Hỗ trợ gói sinh đẻ an toàn tại cơ sở y tế & phụ cấp Cô đỡ thôn bản cho phụ nữ {target_lbl}",
                    "where_when": f"Quản lý thai sản trực tiếp cho {main_val:,} ca nguy cơ thuộc nhóm {target_lbl}",
                    "budget_text": f"{budget_m:,.1f} triệu VNĐ ({main_val:,} ca × 4,5 triệu VNĐ)"
                }
            }
        else:
            return {
                "headline": f"Giám sát An ninh cơ sở [{target_lbl}]: Ghi nhận {main_val:,} người DTTS nghiện ma túy và {sub_val:,} ca nhiễm HIV (đã giảm {abs(diff_pct):.2f}% so với kỳ trước).",
                "legal_tag": "Kế hoạch 118/KH-UBND • CTMTQG Phòng chống Ma túy",
                "fact": [
                    f"Địa bàn trọng điểm: <strong>{target_lbl}</strong> ({scope_grp}).",
                    f"Số người DTTS nghiện ma túy có hồ sơ quản lý: <strong>{main_val:,} người</strong> | Nhiễm HIV/AIDS: <strong>{sub_val:,} người</strong>.",
                    f"Diễn biến so với kỳ trước: Giảm <strong>{abs(diff_val):,} người ({diff_pct:+.2f}%)</strong> nhờ các đợt truy quét và cai nghiện cộng đồng."
                ],
                "analysis": [
                    f"{target_lbl} nằm tại khu vực cửa ngõ giao thương giáp ranh phức tạp, các đối tượng xấu lợi dụng địa hình để lôi kéo thanh niên DTTS.",
                    "Tình trạng thiếu việc làm ổn định sau mùa vụ nông nghiệp khiến thanh niên dễ bị tái nghiện nếu thiếu sự kèm cặp của gia đình và đoàn thể."
                ],
                "impact": [
                    "Tiềm ẩn nguy cơ lây nhiễm HIV/AIDS trong cộng đồng và phát sinh tội phạm trộm cắp nông sản, mất an ninh trật tự thôn/buôn.",
                    "Làm suy kiệt kinh tế của các hộ gia đình DTTS có người mắc nghiện."
                ],
                "recommendation": [
                    f"Duy trì Tổ công tác Công an xã chính quy phối hợp Già làng cảm hóa, quản lý chặt {main_val:,} đối tượng tại {target_lbl}.",
                    "Kết nối điểm cấp phát thuốc Methadone/ARV lưu động với chương trình đào tạo nghề (Dự án 5) và vay vốn tái hòa nhập cộng đồng."
                ],
                "action_plan": {
                    "who": f"Công an Tỉnh • Sở LĐ-TB&XH • Trung tâm Y tế & UBND {scope_grp.replace('Địa bàn ', '')}",
                    "what": f"Điều trị thay thế Methadone/ARV lưu động & đào tạo nghề giải quyết việc làm sau cai nghiện",
                    "where_when": f"Tập trung kiểm soát tại {target_lbl} ({main_val:,} đối tượng) • Rà soát hàng tháng",
                    "budget_text": f"Kinh phí ANTT địa phương + 6,0 triệu VNĐ/người học nghề tái hòa nhập"
                }
            }

    # 6. CHUYÊN ĐỀ VỐN NHÂN LỰC, LAO ĐỘNG & HỌC VẤN GIỚI (LABOR_EDUCATION)
    elif code == "LABOR_EDUCATION":
        if e.dantoc and len(df) > 0:
            row = df.iloc[-1]
            dt_name = pretty_entity(row.get("ten_dantoc", e.dantoc))
            nhom_goc = str(row.get("nhom_nguon_goc", ""))
            cmkt = float(row.get("ty_le_khong_cmkt_pct", 0) or 0)
            diff_cmkt = float(row.get("bien_dong_khong_cmkt_pct", 0) or 0)
            nn = float(row.get("ty_le_nong_nghiep_pct", 0) or 0)
            nu_bc = float(row.get("ty_le_nu_biet_chu_pct", 0) or 0)
            diff_nubc = float(row.get("bien_dong_nu_biet_chu_pct", 0) or 0)
            ld_cnt = int(float(row.get("lao_dong_khong_cmkt", 0) or 0))
            tong_ld = int(float(row.get("tong_lao_dong", 0) or 0))
            budget_ty = ld_cnt * 6.0 / 1000.0

            if cmkt <= 75.0:
                headline = f"Dân tộc {dt_name}: Chất lượng vốn nhân lực đạt chuẩn tốt (chưa qua đào tạo giảm còn {cmkt:.2f}%, nữ biết chữ đạt {nu_bc:.2f}%)."
                analysis_1 = f"Tỷ lệ lao động chưa qua đào tạo của người {dt_name} ({cmkt:.2f}%) đã đạt mục tiêu chuẩn MTQG 1719 (<= 75%), tạo lợi thế lớn để chuyển dịch sang dịch vụ và nông nghiệp công nghệ cao."
            else:
                headline = f"Dân tộc {dt_name}: {cmkt:.2f}% lao động chưa có chứng chỉ nghề ({ld_cnt:,}/{tong_ld:,} người), kéo theo {nn:.2f}% kẹt trong nông nghiệp giản đơn."
                analysis_1 = f"Thiếu kỹ năng nghề ({cmkt:.2f}% chưa qua đào tạo, dù đã giảm {abs(diff_cmkt):.2f} pp) là nguyên nhân trực tiếp khóa chặt {nn:.2f}% lao động {dt_name} trong canh tác nông nghiệp tự cung tự cấp."

            analysis_2 = (
                f"Điểm sáng văn hóa: Tỷ lệ phụ nữ {dt_name} biết chữ đạt tới <strong>{nu_bc:.2f}%</strong> ({diff_nubc:+.2f} pp), rất thuận lợi để đào tạo kỹ năng quản lý tài chính hộ và khuyến nông."
                if nu_bc >= 85.0
                else f"Rào cản kép: Tỷ lệ phụ nữ {dt_name} biết chữ phổ thông mới đạt <strong>{nu_bc:.2f}%</strong> ({diff_nubc:+.2f} pp), đòi hỏi phải mở lớp xóa mù chữ song ngữ gắn với dạy nghề thực hành."
            )

            return {
                "headline": headline,
                "legal_tag": "Dự án 5 - MTQG 1719 • QĐ 46/2015/QĐ-TTg",
                "fact": [
                    f"Lao động chưa qua đào tạo CMKT ({dt_name}): <strong>{cmkt:.2f}%</strong> ({ld_cnt:,} / {tong_ld:,} lao động, biến động {diff_cmkt:+.2f} pp).",
                    f"Tỷ trọng lao động làm nông - lâm nghiệp: <strong>{nn:.2f}%</strong> ({int(float(row.get('lao_dong_nong_nghiep', 0) or 0)):,} người).",
                    f"Tỷ lệ phụ nữ (từ 15 tuổi) biết chữ phổ thông: <strong>{nu_bc:.2f}%</strong> (biến động {diff_nubc:+.2f} pp)."
                ],
                "analysis": [analysis_1, analysis_2],
                "impact": [
                    f"Năng suất lao động của {ld_cnt:,} lao động phổ thông người {dt_name} thấp, thu nhập dễ sụt giảm mạnh khi nông sản mất mùa hoặc rớt giá.",
                    "Khó tuyển dụng vào các cụm công nghiệp chế biến nông sản sâu trên địa bàn tỉnh."
                ],
                "recommendation": [
                    f"Tổ chức lớp đào tạo nghề nông thôn ngắn hạn (<3 tháng) cầm tay chỉ việc ngay tại nương rẫy cho lao động {dt_name}.",
                    f"Ký hợp đồng đặt hàng đào tạo gắn với bao tiêu việc làm giữa Trung tâm GDNN-GDTX và các doanh nghiệp chế biến xuất khẩu."
                ],
                "action_plan": {
                    "who": "Sở LĐ-TB&XH • Trung tâm GDNN-GDTX • Doanh nghiệp nông nghiệp",
                    "what": f"Đào tạo nghề thực hành ngắn hạn (<3 tháng) & cấp chứng chỉ kỹ thuật cho lao động {dt_name}",
                    "where_when": f"Quy mô mục tiêu: {ld_cnt:,} lao động dân tộc {dt_name}",
                    "budget_text": f"{budget_ty:,.2f} tỷ VNĐ ({ld_cnt:,} học viên × 6,0 triệu VNĐ)"
                }
            }
        else:
            r0 = df.iloc[0]
            r_last = df.iloc[-1]
            tot_untrained = int(float(df["lao_dong_khong_cmkt"].sum())) if "lao_dong_khong_cmkt" in df.columns else 0
            avg_cmkt = float(df["ty_le_khong_cmkt_pct"].mean()) if "ty_le_khong_cmkt_pct" in df.columns else 0.0
            budget_ty = tot_untrained * 6.0 / 1000.0
            r0_dt = pretty_entity(r0.get("ten_dantoc"))
            rl_dt = pretty_entity(r_last.get("ten_dantoc"))

            is_illiteracy_topic = "mu_chu" in e.metric_keys or any(w in question.lower() for w in ["mu chu", "biet chu", "hoc van", "vung sau"])
            if is_illiteracy_topic:
                top_illit = []
                for idx, r in df.head(4).iterrows():
                    top_illit.append(f"#{idx+1}. Dân tộc {pretty_entity(r.get('ten_dantoc'))}: Nữ biết chữ chỉ đạt <strong>{float(r.get('ty_le_nu_biet_chu_pct', 0)):.2f}%</strong> (chưa qua đào tạo nghề {float(r.get('ty_le_khong_cmkt_pct', 0)):.2f}%).")
                
                return {
                    "headline": f"Thực trạng học vấn và mù chữ vùng sâu ({period_name}): Bắt nguồn từ 3 rào cản căn cơ (địa hình chia cắt, bất đồng ngôn ngữ và định kiến phụ hệ), tập trung cao nhất ở nhóm phụ nữ đồng bào di cư.",
                    "legal_tag": "Dự án 5 - MTQG 1719 • Đề án Xóa mù chữ Quốc gia",
                    "fact": top_illit if top_illit else [
                        "Tỷ lệ phụ nữ biết chữ thấp tập trung ở các dân tộc di cư và vùng khó khăn: Hrê (10.35%), Khmer (40.37%), Lào (42.53%), Bru Vân Kiều (42.67%), Mông (49.85%).",
                        "Trên 90% lao động tại các nhóm này chưa qua đào tạo nghề và làm nông nghiệp tự cung tự cấp."
                    ],
                    "analysis": [
                        "Căn nguyên 1 — Rào cản ngôn ngữ & thiếu môi trường giao tiếp: Phụ nữ và người lớn tuổi tại các buôn/thôn vùng sâu chủ yếu sử dụng tiếng mẹ đẻ, ít cơ hội tiếp xúc với tiếng Việt phổ thông ngoài chợ cụm hoặc văn bản hành chính; tài liệu dạy học còn thiếu bản song ngữ.",
                        "Căn nguyên 2 — Địa hình chia cắt & cự ly tới trường học: Nhiều điểm trường cách xa buôn làng 10–25 km, đường đất sạt lở vào mùa mưa lũ làm gián đoạn việc chuyên cần, dẫn đến tình trạng học sinh bỏ học giữa chừng và người lớn tái mù chữ sau phổ cập.",
                        "Căn nguyên 3 — Áp lực mưu sinh & định kiến giới trong gia đình phụ hệ: Trẻ em gái ở các nhóm phụ hệ di cư (Mông, Dao...) thường phải ở nhà phụ giúp cha mẹ chăm em, làm nương rẫy và kết hôn sớm (15–17 tuổi), làm đứt gãy con đường học vấn từ nhỏ."
                    ],
                    "impact": [
                        "Tạo ra vòng xoáy nghèo đói truyền kiếp: Mù chữ dẫn đến không tiếp cận được kỹ thuật canh tác mới, không thể đọc hợp đồng tín dụng và không đủ điều kiện đi học nghề.",
                        "Hạn chế năng lực tự bảo vệ sức khỏe sinh sản và nuôi dạy con cái của các bà mẹ DTTS."
                    ],
                    "recommendation": [
                        "Mở các lớp xóa mù chữ linh hoạt ban đêm tại nhà sinh hoạt cộng đồng buôn/thôn, bố trí giáo viên cắm bản và giáo cụ song ngữ trực quan.",
                        "Gắn việc học chữ với quyền lợi thiết thực: Học viên tham gia lớp xóa mù chữ được nhận phụ cấp hỗ trợ ăn ở và ưu tiên xét duyệt vốn vay ưu đãi NĐ 28."
                    ],
                    "action_plan": {
                        "who": "Sở Giáo dục & Đào tạo • Hội Liên hiệp Phụ nữ • UBND các huyện vùng sâu",
                        "what": "Chiến dịch mở lớp xóa mù chữ linh hoạt buổi tối kết hợp dạy nghề nông nghiệp thực hành",
                        "where_when": "Trọng điểm các cụm dân cư vùng sâu (Ea Súp, Krông Bông, M'Drắk) • Triển khai mùa khô",
                        "budget_text": "Kinh phí sự nghiệp giáo dục MTQG 1719 + 6,0 triệu VNĐ/lao động học nghề"
                    }
                }

            return {
                "headline": f"Khảo sát {len(df)} dân tộc trọng điểm ({period_name}): Tỷ lệ chưa qua đào tạo nghề trung bình nhóm ở mức {avg_cmkt:.2f}%, cao nhất ở người {r0_dt} ({float(r0.get('ty_le_khong_cmkt_pct', 0)):.2f}%).",
                "legal_tag": "Dự án 5 - MTQG 1719 • Đào tạo nghề nông thôn",
                "fact": [
                    f"Nhóm có tỷ lệ chưa qua đào tạo cao nhất: <strong>Dân tộc {r0_dt} ({float(r0.get('ty_le_khong_cmkt_pct', 0)):.2f}%)</strong> với {float(r0.get('ty_le_nong_nghiep_pct', 0)):.2f}% làm nông nghiệp.",
                    f"Nhóm tốt nhất trong danh sách hiển thị: <strong>Dân tộc {rl_dt} ({float(r_last.get('ty_le_khong_cmkt_pct', 0)):.2f}%)</strong>.",
                    f"Tổng số lao động cần bồi dưỡng kỹ năng nghề trong nhóm: <strong>{tot_untrained:,} người</strong>."
                ],
                "analysis": [
                    "Dữ liệu chứng minh mối tương quan thuận rất chặt: Dân tộc nào có tỷ lệ chưa qua đào tạo >90% thì gần như toàn bộ lực lượng lao động bị kẹt trong nông nghiệp tự cung tự cấp.",
                    "Sự khác biệt về cấu trúc gia đình (Mẫu hệ bản địa Ê Đê, M'Nông vs Phụ hệ di cư Mông, Dao) tạo ra độ chênh lớn về tỷ lệ phụ nữ biết chữ."
                ],
                "impact": [
                    "Cản trở quá trình chuyển dịch cơ cấu lao động nông thôn và hiện đại hóa nông nghiệp của tỉnh Đắk Lắk.",
                    "Lãng phí nguồn nhân lực trẻ dồi dào tại các vùng đồng bào DTTS."
                ],
                "recommendation": [
                    f"Phân bổ kinh phí Dự án 5 ưu tiên mở lớp kỹ thuật canh tác bền vững cho nhóm <strong>{r0_dt}</strong> và các dân tộc có quy mô lao động lớn.",
                    "Lồng ghép lớp xóa mù chữ cho phụ nữ các nhóm di cư trước khi dạy nghề."
                ],
                "action_plan": {
                    "who": "Sở LĐ-TB&XH • Sở Giáo dục & Đào tạo • Các trường Cao đẳng nghề",
                    "what": "Đào tạo nghề nông nghiệp công nghệ cao & chuyển đổi nghề phi nông nghiệp cho thanh niên DTTS",
                    "where_when": f"Trọng điểm {tot_untrained:,} lao động thuộc {len(df)} dân tộc trong danh sách",
                    "budget_text": f"{budget_ty:,.2f} tỷ VNĐ ({tot_untrained:,} LĐ × 6,0 triệu VNĐ)"
                }
            }

    # 7. HỒ SƠ TỔNG HỢP 1 DÂN TỘC (ETHNIC_OVERVIEW)
    elif code == "ETHNIC_OVERVIEW":
        row = df.iloc[-1] if len(df) > 0 else {}
        dt_name = pretty_entity(row.get("ten_dantoc", e.dantoc or "DTTS"))
        nhom_goc = str(row.get("nhom_nguon_goc", ""))
        dan_so = int(float(row.get("tong_dan_so", 0) or 0))
        so_ho = int(float(row.get("tong_ho_co_nha", 0) or 0))
        nha_tam = int(float(row.get("so_ho_nha_tam_don_so", 0) or 0))
        khat_von = int(float(row.get("so_ho_khat_von", 0) or 0))
        cmkt = float(row.get("ty_le_khong_cmkt_pct", 0) or 0)
        nu_bc = float(row.get("ty_le_nu_biet_chu_pct", 0) or 0)
        dat_ha = float(row.get("dien_tich_dat_sx_bq_ha", 0) or 0)
        tot_budget_ty = (nha_tam * 90.0 + khat_von * 65.0) / 1000.0

        return {
            "headline": f"Hồ sơ toàn diện Dân tộc {dt_name} ({period_name}): Quy mô {so_ho:,} hộ ({dan_so:,} nhân khẩu), còn {nha_tam:,} nhà tạm và {khat_von:,} hộ cần vốn tín dụng.",
            "legal_tag": f"Hồ sơ 360° Dân tộc {dt_name} • MTQG 1719",
            "fact": [
                f"Nhân khẩu & Nhà ở: <strong>{so_ho:,} hộ ({dan_so:,} người)</strong> — Số nhà tạm hiện còn: <strong>{nha_tam:,} căn ({float(row.get('ty_le_nha_tam_pct', 0) or 0):.2f}%)</strong>.",
                f"Tín dụng & Đất đai: <strong>{khat_von:,} hộ khát vốn ({float(row.get('khoang_trong_tin_dung_pct', 0) or 0):.2f}%)</strong> | Đất sản xuất: <strong>{dat_ha:.2f} ha/hộ</strong>.",
                f"Vốn con người: <strong>{cmkt:.2f}%</strong> lao động chưa qua đào tạo nghề | <strong>{nu_bc:.2f}%</strong> phụ nữ biết chữ."
            ],
            "analysis": [
                f"Cộng đồng người {dt_name} ({nhom_goc}) đã có sự chuyển dịch tích cực qua 3 kỳ từ 2019 đến 2026 trên cả 6 trụ cột KTXH.",
                f"{'Điểm nghẽn lớn nhất hiện nay là nhu cầu vốn tín dụng sản xuất và đào tạo nghề cho lao động trẻ.' if nha_tam == 0 else 'Cần giải quyết song song bài toán xóa nhà tạm tồn đọng và bổ sung vốn vay tái canh nông nghiệp.'}"
            ],
            "impact": [
                f"Đầu tư đồng bộ cho {so_ho:,} hộ dân tộc {dt_name} giúp ổn định an sinh bền vững và phát huy bản sắc văn hóa dân tộc."
            ],
            "recommendation": [
                f"Phân bổ gói chính sách tích hợp (Nhà ở DA 1 + Tín dụng NĐ 28 + Dạy nghề DA 5) sát với quy mô thực tế của người {dt_name}."
            ],
            "action_plan": {
                "who": "Ban Dân tộc Tỉnh • Sở KH&ĐT • NHCSXH • UBND các huyện",
                "what": f"Gói can thiệp đa chiều cho đồng bào {dt_name} ({nha_tam:,} nhà tạm & {khat_von:,} hồ sơ vay vốn)",
                "where_when": f"Địa bàn cư trú của {so_ho:,} hộ dân tộc {dt_name} • Giai đoạn 2026–2030",
                "budget_text": f"Tối thiểu {tot_budget_ty:,.2f} tỷ VNĐ (Nhà ở & Tín dụng ưu đãi)"
            }
        }

    # 8. CHUYÊN ĐỀ KHOẢNG TRỐNG TÍN DỤNG & ĐẤT SẢN XUẤT (CREDIT_LAND)
    else:
        if e.dantoc and len(df) > 0:
            row = df.iloc[-1]
            dt_name = pretty_entity(row.get("ten_dantoc", e.dantoc))
            khat_von = int(float(row.get("so_ho_khat_von", 0) or 0))
            gap_pct = float(row.get("khoang_trong_tin_dung_pct", 0) or 0)
            diff_von = int(float(row.get("chenh_lech_ho_khat_von", 0) or 0))
            dat_ha = float(row.get("dien_tich_dat_sx_bq_ha", 0) or 0)
            budget_ty = khat_von * 65.0 / 1000.0

            is_land_scarce = (0 < dat_ha < 0.50)
            return {
                "headline": f"Dân tộc {dt_name}: Hiện có {khat_von:,} hộ cần vay vốn sản xuất nhưng chưa được đáp ứng (khoảng trống tín dụng {gap_pct:.2f}%, đất canh tác {dat_ha:.2f} ha/hộ).",
                "legal_tag": "Nghị định 28/2022/NĐ-CP • Dự án 1 MTQG 1719",
                "fact": [
                    f"Quy mô hộ khát vốn ({dt_name}): <strong>{khat_von:,} hộ</strong> (Tỷ lệ thiếu hụt tín dụng: <strong>{gap_pct:.2f}%</strong>, biến động {diff_von:+,} hộ).",
                    f"Quỹ đất sản xuất bình quân: <strong>{dat_ha:.2f} ha/hộ</strong> ({'Thấp hơn chuẩn tối thiểu 0,50 ha/hộ của QĐ 1719' if is_land_scarce else 'Đạt trên ngưỡng tối thiểu 0,50 ha/hộ'}).",
                    f"Thứ hạng ưu tiên giải ngân tín dụng: <strong>Hạng #{int(float(row.get('xep_hang_khat_von_ky', 1) or 1))}</strong> toàn tỉnh."
                ],
                "analysis": [
                    (
                        f"Bất lợi kép ở người {dt_name}: Diện tích đất sản xuất bình quân chỉ đạt {dat_ha:.2f} ha/hộ (<0,50 ha), thiếu tài sản thế chấp nên rất khó tiếp cận vốn ngân hàng thương mại."
                        if is_land_scarce
                        else f"Đồng bào {dt_name} có quỹ đất sản xuất ({dat_ha:.2f} ha/hộ) nhưng thiếu nguồn vốn trung và dài hạn để tái canh cà phê, hồ tiêu và đầu tư hệ thống tưới tiết kiệm."
                    ),
                    "Hạn mức vốn ủy thác địa phương qua NHCSXH tăng chưa kịp so với nhu cầu mở rộng sản xuất sau đại dịch."
                ],
                "impact": [
                    f"Nếu {khat_von:,} hộ người {dt_name} không tiếp cận được vốn ưu đãi sẽ dễ rơi vào bẫy 'tín dụng đen' hoặc phải bán non nông sản.",
                    "Làm chậm quá trình thoát nghèo bền vững và chuyển đổi cơ cấu cây trồng vật nuôi."
                ],
                "recommendation": [
                    f"Mở rộng hạn mức cho vay tín chấp qua Tổ Tiết kiệm & Vay vốn thôn/buôn đối với {khat_von:,} hộ dân tộc {dt_name}.",
                    "Đối với các hộ thiếu đất (<0,5 ha), ưu tiên cho vay vốn chuyển đổi sang chăn nuôi khép kín hoặc nghề tiểu thủ công nghiệp."
                ],
                "action_plan": {
                    "who": "Chi nhánh NHCSXH Tỉnh Đắk Lắk • UBND cấp xã • Hội Nông dân/Phụ nữ",
                    "what": f"Giải ngân gói tín dụng ưu đãi NĐ 28 ({'kèm hỗ trợ chuyển đổi nghề do thiếu đất' if is_land_scarce else 'phục vụ thâm canh nông nghiệp'})",
                    "where_when": f"Giải quyết dứt điểm {khat_von:,} hồ sơ chờ vốn của đồng bào {dt_name}",
                    "budget_text": f"{budget_ty:,.2f} tỷ VNĐ ({khat_von:,} hộ × 65 triệu VNĐ)"
                }
            }
        else:
            r0 = df.iloc[0]
            r0_dt = pretty_entity(r0.get("ten_dantoc"))
            tot_kv = int(float(df["so_ho_khat_von"].sum())) if "so_ho_khat_von" in df.columns else 0
            land_scarce_cnt = len(df[df["dien_tich_dat_sx_bq_ha"] < 0.50]) if "dien_tich_dat_sx_bq_ha" in df.columns else 0
            budget_ty = tot_kv * 65.0 / 1000.0

            return {
                "headline": f"Tổng hợp {len(df)} dân tộc có nhu cầu vốn lớn nhất ({period_name}): Có {tot_kv:,} hộ đang khát vốn tín dụng, đứng đầu là người {r0_dt} ({int(float(r0.get('so_ho_khat_von', 0))):,} hộ).",
                "legal_tag": "Nghị định 28/2022/NĐ-CP • Dự án 1 MTQG 1719",
                "fact": [
                    f"Tổng quy mô hồ sơ chờ vay vốn trong danh sách: <strong>{tot_kv:,} hộ</strong> (cần bổ sung <strong>{budget_ty:,.2f} tỷ VNĐ</strong>).",
                    f"Dân tộc có quy mô hộ cần vốn lớn nhất: <strong>{r0_dt} ({int(float(r0.get('so_ho_khat_von', 0))):,} hộ — tỷ lệ thiếu hụt {float(r0.get('khoang_trong_tin_dung_pct', 0)):.2f}%)</strong>.",
                    f"Cảnh báo tư liệu sản xuất: Có <strong>{land_scarce_cnt}/{len(df)} dân tộc</strong> trong bảng có diện tích đất canh tác dưới chuẩn 0,50 ha/hộ."
                ],
                "analysis": [
                    "Nhu cầu vốn vay ưu đãi tập trung cao ở nhóm dân tộc bản địa quy mô lớn (Ê Đê, M'Nông) để tái canh cây công nghiệp và nhóm Gia Rai có tỷ lệ thiếu hụt tín dụng cao.",
                    "Các dân tộc ít đất canh tác (<0,50 ha/hộ) cần gói tín dụng giải quyết việc làm phi nông nghiệp thay vì tín dụng trồng trọt truyền thống."
                ],
                "impact": [
                    f"Giải quyết cơn khát vốn cho {tot_kv:,} hộ DTTS là đòn bẩy quan trọng nhất để đẩy lùi nạn vay nặng lãi tại buôn làng.",
                    "Tạo dòng vốn tuần hoàn bền vững cho kinh tế nông hộ Tây Nguyên."
                ],
                "recommendation": [
                    f"Tăng nguồn vốn ngân sách tỉnh ủy thác qua NHCSXH thêm tối thiểu 15–20% trong {period_name}, ưu tiên giải ngân cho nhóm <strong>{r0_dt}</strong>.",
                    "Rà soát quỹ đất có nguồn gốc nông - lâm trường để giao đất sản xuất cho các hộ thiếu đất theo Dự án 1."
                ],
                "action_plan": {
                    "who": "Chi nhánh NHCSXH Tỉnh • Sở TN&MT • Sở KH&ĐT",
                    "what": "Bổ sung nguồn vốn ủy thác tín dụng ưu đãi NĐ 28 & hỗ trợ chuyển đổi nghề cho hộ thiếu đất",
                    "where_when": f"Phục vụ {tot_kv:,} hộ khát vốn thuộc {len(df)} dân tộc trọng điểm",
                    "budget_text": f"{budget_ty:,.2f} tỷ VNĐ ({tot_kv:,} hộ × 65 triệu VNĐ)"
                }
            }


def build_natural_qa_response(
    question: str,
    intent: PolicyIntent,
    df: pd.DataFrame,
    scoped_kpis: Dict[str, Any],
    fair_cards: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Sinh câu trả lời đối thoại tự nhiên, trực diện, không lặp thông tin giữa câu mở đầu và
    các gạch đầu dòng dành riêng cho Ngăn Hỏi – Đáp Nhanh Số Liệu (Q&A Drawer).
    """
    q_raw = (question or "").strip()
    q_low = q_raw.lower()
    code = intent.intent_code
    e = intent.entities
    period_short = "kỳ 2026" if e.ky_baocao == "KY_2026" else ("năm 2024" if e.ky_baocao == "KY_2024" else "năm 2019")
    eth_disp = pretty_entity(e.dantoc) if e.dantoc else None
    huyen_disp = pretty_entity(e.huyen) if e.huyen else None
    question = (intent.intent_description or "").lower()

    if df is None or df.empty:
        return {
            "lead_answer": f"Chưa tìm thấy bản ghi nào trong {period_short} khớp với điều kiện lọc trong câu hỏi của bạn.",
            "bullet_points": ["Bạn có thể thử hỏi theo tên một Huyện (VD: Lắk, Ea Súp), Xã (VD: Nam Ka, Ea Wy) hoặc Dân tộc (VD: Ê Đê, Mông, Chơ Ro)."],
            "takeaway": "Bấm vào các gợi ý câu hỏi phía trên để tra cứu nhanh."
        }

    is_multi = ("ma_ky" in df.columns and len(df["ma_ky"].unique()) > 1)
    is_asking_why = any(w in q_low for w in ["tại sao", "vì sao", "nguyên nhân", "do đâu", "lý do"])
    is_asking_top = any(w in q_low for w in ["top", "cao nhất", "thấp nhất", "nhiều nhất", "ít nhất", "nặng nhất", "tốt nhất", "những xã", "các xã", "dân tộc nào", "huyện nào"])
    act = fair_cards.get("action_plan", {})

    # =========================================================================
    # CHUYÊN ĐỀ ĐẶC THÙ 1: SO SÁNH ĐỐI ĐẦU ĐIỀU KIỆN NHÀ Ở ĐA DÂN TỘC (VD: MNÔNG VS GIA RAI)
    # =========================================================================
    if (code == "HOUSING_POVERTY" or "nha o" in q_low or "nha tam" in q_low) and (len(e.dantoc_list) >= 2 or (len(df) >= 2 and "ten_dantoc" in df.columns)):
        rows = [r for _, r in df.iterrows()]
        if len(rows) >= 2:
            r1, r2 = rows[0], rows[1]
            t1, t2 = str(r1.get("ten_dantoc", "")), str(r2.get("ten_dantoc", ""))
            tam1, tam2 = float(r1.get("so_ho_nha_tam_don_so", 0) or 0), float(r2.get("so_ho_nha_tam_don_so", 0) or 0)
            pct1, pct2 = float(r1.get("ty_le_nha_tam_pct", 0) or 0), float(r2.get("ty_le_nha_tam_pct", 0) or 0)
            tot1, tot2 = float(r1.get("tong_ho_co_nha", 0) or 0), float(r2.get("tong_ho_co_nha", 0) or 0)
            kv1, kv2 = float(r1.get("khoang_trong_tin_dung_pct", 0) or 0), float(r2.get("khoang_trong_tin_dung_pct", 0) or 0)

            higher_name = t1 if pct1 >= pct2 else t2
            lower_name = t2 if pct1 >= pct2 else t1
            max_pct = max(pct1, pct2)
            min_pct = min(pct1, pct2)
            ratio = (max_pct / max(0.1, min_pct))

            return {
                "lead_answer": f"So sánh điều kiện nhà ở ({period_short}): Tỷ lệ hộ ở nhà tạm, đơn sơ của người <strong>{higher_name}</strong> ({max_pct:.2f}%) cao gấp <strong>{ratio:.2f} lần</strong> so với người <strong>{lower_name}</strong> ({min_pct:.2f}%), dù quy mô tuyệt đối số căn nhà tạm ở hai cộng đồng tương đương nhau.",
                "bullet_points": [
                    f"<strong>Người {t1}:</strong> Có <b>{tam1:,.0f} hộ</b> ở nhà tạm, dột nát (chiếm {pct1:.2f}% trên tổng số {tot1:,.0f} hộ có nhà). Khoảng trống tín dụng khát vốn vay ưu đãi là {kv1:.1f}%.",
                    f"<strong>Người {t2}:</strong> Có <b>{tam2:,.0f} hộ</b> ở nhà tạm, dột nát (chiếm {pct2:.2f}% trên tổng số {tot2:,.0f} hộ có nhà). Khoảng trống tín dụng khát vốn vay ưu đãi là {kv2:.1f}%.",
                    f"<strong>Căn nguyên & Tín dụng:</strong> Chênh lệch tỷ lệ nhà tạm gắn chặt với mức độ khát vốn ưu đãi. Nhóm {higher_name} có khoảng trống tín dụng cao hơn ({max(kv1, kv2):.1f}%), dẫn tới việc thiếu vốn tích lũy tự cải tạo, sửa chữa nhà sàn truyền thống đã xuống cấp."
                ],
                "takeaway": f"Ưu tiên gói vốn Dự án 1 (CTMTQG 1719) kết hợp vốn vay ưu đãi Ngân hàng CSXH (NĐ 28) với định mức 90 triệu VNĐ/căn để xóa dứt điểm toàn bộ {tam1 + tam2:,.0f} căn nhà tạm cho cả hai cộng đồng {t1} và {t2}."
            }

    # =========================================================================
    # CHUYÊN ĐỀ ĐẶC THÙ 2: SO SÁNH THÁP TUỔI & CƠ CẤU DÂN SỐ ĐA DÂN TỘC (VD: Ê ĐÊ VS MÔNG)
    # =========================================================================
    if (code in ("DEMOGRAPHIC_COMPARISON", "DASHBOARD_GUIDE") and (len(e.dantoc_list) >= 2 or (len(df) >= 2 and "dan_so_0_14" in df.columns))):
        rows = [r for _, r in df.iterrows()]
        if len(rows) >= 2:
            r1, r2 = rows[0], rows[1]
            t1, t2 = str(r1.get("ten_dantoc", "")), str(r2.get("ten_dantoc", ""))
            pop1, pop2 = float(r1.get("tong_dan_so", 0) or 0), float(r2.get("tong_dan_so", 0) or 0)
            c1_014, c2_014 = float(r1.get("ty_le_0_14_pct", 0) or 0), float(r2.get("ty_le_0_14_pct", 0) or 0)
            c1_1559, c2_1559 = float(r1.get("ty_le_15_59_pct", 0) or 0), float(r2.get("ty_le_15_59_pct", 0) or 0)
            c1_60, c2_60 = float(r1.get("ty_le_60_plus_pct", 0) or 0), float(r2.get("ty_le_60_plus_pct", 0) or 0)
            dep1, dep2 = float(r1.get("ty_le_phu_thuoc_tre_em_pct", 0) or 0), float(r2.get("ty_le_phu_thuoc_tre_em_pct", 0) or 0)
            age_idx1, age_idx2 = float(r1.get("chi_so_gia_hoa_pct", 0) or 0), float(r2.get("chi_so_gia_hoa_pct", 0) or 0)

            younger = t1 if c1_014 >= c2_014 else t2
            older = t2 if c1_014 >= c2_014 else t1

            return {
                "lead_answer": f"Tháp tuổi của người <strong>{t1}</strong> và người <strong>{t2}</strong> đại diện cho hai thái cực nhân khẩu học đối lập: Người {younger} mang đặc trưng cơ cấu 'rất trẻ' với đáy tháp phình to cực đại, trong khi người {older} đang ở thời kỳ 'cơ cấu dân số vàng' với tỷ trọng lao động vượt trội.",
                "bullet_points": [
                    f"<strong>Người {t1} ({pop1:,.0f} người):</strong> Trẻ em 0-14t chiếm <b>{c1_014:.1f}%</b>, Lao động 15-59t chiếm <b>{c1_1559:.1f}%</b>, Người cao tuổi 60+t chiếm <b>{c1_60:.1f}%</b>. Tỷ lệ phụ thuộc trẻ em đạt <b>{dep1:.1f}%</b>; Chỉ số già hóa đạt <b>{age_idx1:.1f}%</b>.",
                    f"<strong>Người {t2} ({pop2:,.0f} người):</strong> Trẻ em 0-14t chiếm <b>{c2_014:.1f}%</b>, Lao động 15-59t chiếm <b>{c2_1559:.1f}%</b>, Người cao tuổi 60+t chiếm <b>{c2_60:.1f}%</b>. Tỷ lệ phụ thuộc trẻ em đạt <b>{dep2:.1f}%</b>; Chỉ số già hóa đạt <b>{age_idx2:.1f}%</b>.",
                    f"<strong>Bản chất khác biệt & Căn nguyên:</strong> Nhóm di cư phía Bắc duy trì mức sinh cao khiến đáy tháp mở rộng, gánh nặng nuôi con lớn (100 lao động phải gánh >75 trẻ em); ngược lại nhóm bản địa có mức sinh ổn định, lực lượng lao động chiếm hơn 62% nhưng tốc độ già hóa diễn ra nhanh gấp đôi."
                ],
                "takeaway": "Tỉnh cần phân hóa chính sách: Ưu tiên mở rộng trường mầm non/tiểu học và dinh dưỡng học đường cho nhóm trẻ em đông; đồng thời đẩy mạnh đào tạo nghề nông thôn (Dự án 5 MTQG 1719) để bứt phá năng suất cho nhóm dân số vàng."
            }

    # =========================================================================
    # CHUYÊN ĐỀ ĐẶC THÙ 3: XẾP HẠNG CÁC XÃ TRONG MỘT HUYỆN (VD: XÃ KHÁT VỐN Ở KRÔNG BÔNG)
    # =========================================================================
    if e.huyen and (e.is_commune_query or any(w in q_low for w in ["xa ", "cac xa", "nhung xa", "xa nao"])):
        rows = [r for _, r in df.iterrows()]
        top_items = []
        for idx, r in enumerate(rows[:5], 1):
            ten_xa = r.get("ten_xa", f"Xã {idx}")
            ty_le = float(r.get("ty_le_ngheo_pct", 0) or 0)
            so_ho = float(r.get("so_ho_ngheo", 0) or 0)
            ngan_sach = float(r.get("du_toan_ngan_sach_sinh_ke_trieu_vnd", 0) or 0) / 1000.0
            km = float(r.get("km_den_trung_tam_huyen", 0) or 0)
            top_items.append(f"#{idx}. <strong>{ten_xa}</strong>: {ty_le:.2f}% hộ nghèo ({so_ho:,.0f} hộ), cách huyện {km:.1f}km — Dự toán vốn sinh kế: <b>{ngan_sach:.2f} tỷ VNĐ</b>.")

        tot_ho = sum([float(r.get("so_ho_ngheo", 0) or 0) for r in rows])
        tot_ns = sum([float(r.get("du_toan_ngan_sach_sinh_ke_trieu_vnd", 0) or 0) for r in rows]) / 1000.0

        return {
            "lead_answer": f"Tại <strong>{e.huyen}</strong> ({period_short}), các xã có quy mô hộ nghèo và nhu cầu vốn vay sinh kế lớn nhất tập trung tại các xã vùng sâu cách xa trung tâm huyện, với tổng nhu cầu vốn sinh kế toàn huyện là <strong>{tot_ns:,.2f} tỷ VNĐ</strong> hỗ trợ cho <strong>{tot_ho:,.0f} hộ nghèo</strong>.",
            "bullet_points": top_items,
            "takeaway": f"Ưu tiên phân bổ vốn ủy thác Ngân hàng CSXH (NĐ 28) và Dự án 3 CTMTQG 1719 trực tiếp cho 3 xã khó khăn nhất ({rows[0].get('ten_xa', '') if rows else ''}, {rows[1].get('ten_xa', '') if len(rows) > 1 else ''}) để giải tỏa 'cơn khát vốn' sản xuất."
        }

    # 0. Nếu câu hỏi về Hướng dẫn sử dụng Power BI Dashboard / Giải thích trang báo cáo / Công thức tính chỉ số
    if code == "DASHBOARD_GUIDE":
        topic = e.guide_topic or "general"
        if topic == "age_pyramid":
            return {
                "lead_answer": "Biểu đồ <strong>'Tháp Tuổi & Cơ Cấu 3 Nhóm Tuổi Dân Tộc'</strong> (nằm ở Trang 1 Power BI) là biểu đồ thanh ngang xếp chồng 100% (100% Stacked Bar Chart) dùng để bóc tách <strong>cấu trúc nhân khẩu học</strong>, đo lường mức độ <strong>trẻ hóa</strong> và <strong>xu hướng già hóa</strong> của 53 dân tộc thiểu số tại Đắk Lắk:",
                "bullet_points": [
                    "<strong>Ý nghĩa 3 nhóm tuổi cốt lõi:</strong><br>• 🟢 <em>0–14 tuổi (Dưới tuổi lao động / Trẻ em):</em> Thể hiện thế hệ kế cận và áp lực giáo dục, dinh dưỡng. Tỷ trọng này cao nhất ở các dân tộc di cư phía Bắc (như <b>người Mông 41.0%</b>, <b>Xơ Đăng 42.5%</b> do mức sinh cao).<br>• 🔵 <em>15–59 tuổi (Độ tuổi lao động vàng):</em> Lực lượng sản xuất chính tạo ra thu nhập. Nhóm bản địa như <b>Ê Đê (62.0%)</b>, <b>M'Nông (58.1%)</b> đang ở thời kỳ 'dân số vàng' cần được tập trung đào tạo nghề (Dự án 5 MTQG 1719) để bứt phá kinh tế.<br>• 🟠 <em>60+ tuổi (Hết tuổi lao động / Người cao tuổi):</em> Đo lường tốc độ già hóa. Nhóm <b>Tày (10.7%)</b>, <b>Thái (10.6%)</b>, <b>Nùng (8.8%)</b> có tỷ lệ người cao tuổi cao nhất tỉnh.",
                    "<strong>Cách tính 2 chỉ số nhân khẩu học cốt lõi (DAX Measures):</strong><br>• <em>Tỷ Lệ Phụ Thuộc Trẻ Em (Youth Dependency Ratio)</em> = <code>[Dân số 0-14] / [Dân số 15-59] × 100</code>: Đo lường gánh nặng 100 lao động phải nuôi bao nhiêu trẻ em. Nhóm <b>người Mông đạt 75.1%</b> và <b>Xơ Đăng đạt 79.2%</b> (100 người làm việc phải gánh gần 80 trẻ nhỏ), lý giải căn nguyên nghèo do đông con.<br>• <em>Chỉ Số Già Hóa (Aging Index)</em> = <code>[Dân số 60+] / [Dân số 0-14] × 100</code>: Đo lường tỷ lệ người cao tuổi so với trẻ em. Nhóm <b>Tày đạt 42.7%</b> và <b>Thái đạt 42.1%</b> — bắt đầu bước vào giai đoạn già hóa dân số."
                ],
                "takeaway": "Mẹo điều hành: Bấm vào tên một Dân tộc trên biểu đồ (hoặc chọn Slicer Dân tộc) để lọc chéo xem tháp tuổi riêng của từng nhóm; kết hợp đối chiếu với biểu đồ 'Gánh nặng nuôi con vs Già hóa' ngay bên cạnh."
            }
        elif topic == "treemap_pop":
            return {
                "lead_answer": "Biểu đồ <strong>'Treemap Phân Bố Dân Số DTTS 15 Huyện'</strong> (nằm ở góc trái Trang 1 Power BI) thể hiện mật độ cư trú và tương quan nghèo/cận nghèo theo không gian địa lý:",
                "bullet_points": [
                    "<strong>Cách đọc diện tích & màu sắc:</strong> <em>Diện tích ô vuông/chữ nhật</em> thể hiện Tổng số hộ DTTS của huyện; <em>Độ đậm nhạt màu sắc</em> thể hiện Tỷ lệ cận nghèo hoặc tỷ lệ nghèo của huyện đó.",
                    "<strong>Trọng điểm địa bàn:</strong> Các huyện như <em>Krông Năng, Cư M'gar, Krông Pắc, TP. Buôn Ma Thuột</em> có diện tích ô lớn nhất (tập trung đồng bào Ê Đê đông nhất tỉnh); trong khi các huyện <em>Ea Súp, Lắk, Krông Bông</em> có sắc độ cảnh báo đậm nhất (tỷ lệ nghèo cao nhất tỉnh)."
                ],
                "takeaway": "Bấm thẳng vào 1 ô Huyện trên Treemap để lọc chéo toàn bộ Trang 1 xem tháp tuổi và cơ cấu dân tộc riêng của huyện đó."
            }
        elif topic == "labor_skill_trap":
            return {
                "lead_answer": "Biểu đồ <strong>'Ma Trận Kỹ Năng Nghề vs Bẫy Lao Động Nông Nghiệp'</strong> (Trang 2 Power BI) chứng minh mối liên hệ nhân quả giữa thiếu hụt đào tạo nghề CMKT và tình trạng kẹt trong nông nghiệp giản đơn:",
                "bullet_points": [
                    "<strong>Quy luật nhân quả:</strong> 82.46% lao động DTTS toàn tỉnh chưa có chứng chỉ/bằng cấp nghề (người Mông đạt đỉnh 96.98%). Cứ dân tộc nào có tỷ lệ chưa qua đào tạo cao thì tỷ trọng làm nông nghiệp tự cung tự cấp cũng vọt lên >85–98%.",
                    "<strong>Giải pháp đột phá:</strong> Cần chuyển dịch từ hỗ trợ tiền mặt sang đào tạo nghề nông thôn ngắn hạn gắn với thị trường nguyên liệu (Dự án 5 MTQG 1719, định mức 6,0 triệu VNĐ/lao động)."
                ],
                "takeaway": "Dùng Slicer Dân tộc trên Trang 2 để xem quy mô lao động chưa đào tạo của từng nhóm phục vụ chỉ tiêu giao ban."
            }
        elif topic == "gender_paradox":
            return {
                "lead_answer": "Biểu đồ <strong>'Nghịch Lý Giới Trong Giáo Dục & Biết Chữ'</strong> (Trang 2 Power BI) bóc tách sự phân hóa văn hóa - xã hội sâu sắc giữa hai khối dân tộc:",
                "bullet_points": [
                    "<strong>Khối Mẫu hệ Bản địa Tây Nguyên (Ê Đê, M'Nông, Gia Rai):</strong> Tỷ lệ nữ biết chữ đạt ngang bằng hoặc thậm chí cao hơn nam giới do vị thế người phụ nữ làm chủ hộ và thừa kế gia sản.",
                    "<strong>Khối Phụ hệ Di cư phía Bắc (Mông, Dao, Thái):</strong> Tỷ lệ nữ biết chữ thấp hơn nam giới từ 15–28 điểm % (phụ nữ Mông chịu thiệt thòi lớn nhất), do phong tục kết hôn sớm và gánh nặng việc nhà."
                ],
                "takeaway": "Khi mở lớp xóa mù chữ và khuyến nông (Dự án 5), Ban Dân tộc cần thiết kế khung giờ học linh hoạt và lớp song ngữ dành riêng cho phụ nữ nhóm di cư."
            }
        elif topic == "sanitation_paradox":
            return {
                "lead_answer": "Biểu đồ <strong>'Điểm Trũng Vệ Sinh Môi Trường & Nghịch Lý Công Nghệ'</strong> (Trang 3 Power BI) phơi bày độ vênh lớn giữa chuyển đổi số và điều kiện vệ sinh thiết yếu:",
                "bullet_points": [
                    "<strong>Nghịch lý 'Công nghệ đi trước vệ sinh':</strong> Tỷ lệ hộ DTTS kết nối Internet 4G toàn tỉnh đạt trên 85–95% (đáp ứng tốt Đề án 06), nhưng tỷ lệ <em>Hố xí hợp vệ sinh</em> tại các huyện vùng trũng như <b>Krông Bông (16.21%)</b> và <b>Lắk (18.07%)</b> lại rất thấp.",
                    "<strong>Hệ lụy Nông thôn mới:</strong> Điểm nghẽn hố xí HVS làm liệt trực tiếp Tiêu chí 17.5 NTM (yêu cầu >= 70%), khiến nhiều xã dù đạt 100% điện, đường, trường, trạm vẫn không thể về đích NTM."
                ],
                "takeaway": "Cần hỗ trợ mô hình 'Bể phốt tự hoại Composite đúc sẵn' (định mức 12,0 triệu VNĐ/hộ) để bù đắp chỉ số Tiêu chí 17 NTM."
            }
        elif topic == "anti_triple_count":
            return {
                "lead_answer": "Trên Power BI, số hộ và dân số không bị cộng dồn cả 3 kỳ (2019 + 2024 + 2026) là nhờ cơ chế khóa kỳ tự động <strong>Anti-Triple Counting Gate</strong> thông qua hàm DAX <code>[Selected Period Order]</code>.",
                "bullet_points": [
                    "<strong>Khi không chọn Slicer Kỳ báo cáo:</strong> Hàm tự động kiểm tra <code>NOT(ISFILTERED(dim_ky_baocao))</code> và khóa cứng về kỳ mới nhất (<code>is_latest = TRUE → KY_2026</code>), trả về đúng <b>163,912 hộ DTTS</b> thay vì cộng gộp 3 kỳ thành 473,755 hộ.",
                    "<strong>Khi chọn Slicer Kỳ báo cáo:</strong> Toàn bộ 100 DAX Measures tự động chuyển sang kỳ bạn chọn và lùi 1 bậc (<code>thu_tu_ky - 1</code>) để tính chênh lệch <code>▲/▼</code> trên các thẻ KPI."
                ],
                "takeaway": "Nhờ cổng kiểm soát này, Lãnh đạo có thể bỏ chọn Slicer bất kỳ lúc nào mà số liệu trên 4 trang vẫn luôn chuẩn xác ở kỳ mới nhất."
            }
        elif topic == "slicer_filter":
            return {
                "lead_answer": "Trên cả 4 trang Power BI đều được bố trí <strong>3 bộ lọc Slicer đồng bộ</strong> ở góc trên bên phải (gồm <em>Kỳ báo cáo</em>, <em>Địa bàn Huyện</em> và <em>Dân tộc</em>; riêng Trang 2 có thêm <em>Nhóm nguồn gốc</em>).",
                "bullet_points": [
                    "<strong>Lọc theo Slicer:</strong> Chọn <em>Kỳ 2019 | Kỳ 2024 | Kỳ 2026</em> để đổi mốc thời gian; chọn 1 Huyện hoặc 1 Dân tộc để toàn bộ thẻ KPI và biểu đồ trên trang tự động co về đúng phạm vi đó.",
                    "<strong>Lọc chéo trực tiếp (Cross-filtering):</strong> Bạn có thể bấm thẳng vào 1 ô Huyện trên Treemap (Trang 1), 1 thanh Dân tộc (Trang 2, 3) hoặc 1 chấm Xã trên biểu đồ phân tán (Trang 4) để lọc nhanh mà không cần mở dropdown."
                ],
                "takeaway": "Mẹo: Giữ phím Ctrl khi bấm chuột nếu bạn muốn chọn so sánh nhiều Huyện hoặc nhiều Dân tộc cùng lúc."
            }
        elif topic == "quadrant_chart":
            return {
                "lead_answer": "Biểu đồ <strong>'Ma trận 4 Góc phần tư: Khoảng cách vs Tỷ lệ hộ nghèo cấp xã'</strong> (nằm ở Trang 4 Power BI) dùng để khoanh vùng các <strong>Xã khó khăn kép</strong> vừa xa trung tâm vừa có tỷ lệ nghèo cao.",
                "bullet_points": [
                    "<strong>Cách đọc 2 trục:</strong> Trục ngang (X) là cự ly từ xã đến trung tâm huyện (km); Trục dọc (Y) là tỷ lệ hộ nghèo (%); kích thước bóng thể hiện tổng số hộ DTTS của xã.",
                    "<strong>Góc phần tư ưu tiên số 1 (Góc trên bên phải):</strong> Các xã cách trung tâm huyện >15–20 km và tỷ lệ nghèo >25–35% (như <em>Xã Nam Ka, Xã Ia Lốp, Xã Cư Pui</em>) nằm ở góc này — đây là nhóm chịu 'bẫy cự ly địa lý' cần ưu tiên phân bổ vốn sinh kế Dự án 3 trước tiên."
                ],
                "takeaway": "Bấm vào một chấm xã ở góc trên bên phải trên Trang 4 để xem ngay tên xã và phương án hỗ trợ tại hộp Khung Hành Động."
            }
        elif topic == "dynamic_dax_card":
            return {
                "lead_answer": "Hộp <strong>'Khung Hành Động Tham Mưu Chính Sách (Theo Lựa Chọn)'</strong> ở góc phải Trang 4 Power BI được vận hành bởi siêu công thức DAX <code>[Dynamic Policy Recommendation Text]</code>.",
                "bullet_points": [
                    "<strong>Tự động nhận diện 4 kịch bản lọc:</strong> Công thức tự kiểm tra bạn đang xem <em>Toàn tỉnh</em>, <em>1 Huyện</em>, <em>1 Dân tộc</em> hay <em>1 Huyện × 1 Dân tộc</em> để viết lại lời văn nhận định tương ứng.",
                    "<strong>Tự động tính lại ngân sách:</strong> Ngay khi bạn bấm chọn bất kỳ địa bàn hay dân tộc nào, hộp này sẽ nhân số lượng đối tượng thực tế (nhà tạm, hộ khát vốn, lao động chưa đào tạo) với đơn giá định mức của kỳ đang chọn để xuất ra tổng kinh phí."
                ],
                "takeaway": "Khi cần điều chỉnh tăng/giảm đơn giá định mức (What-If) hoặc in thành Tờ trình A4, bạn chuyển sang Bàn Thẩm Định Web này để thao tác."
            }
        elif topic == "page_1":
            return {
                "lead_answer": "Trên <strong>Trang 1 (Dân số & Địa bàn)</strong> của Power BI được thiết kế gồm <strong>4 thẻ KPI tổng quan</strong> ở trên và <strong>4 biểu đồ nhân khẩu học</strong> ở dưới để bạn nắm bức tranh toàn cảnh 53 DTTS tại 15 huyện:",
                "bullet_points": [
                    "<strong>4 Thẻ KPI & 3 Bộ lọc:</strong> Hiển thị <em>Tổng Dân Số DTTS</em>, <em>Tổng Số Hộ DTTS</em>, <em>146 Xã khảo sát</em>, <em>53 DTTS</em>; đi kèm 3 Slicer lọc theo <em>Kỳ báo cáo</em>, <em>Huyện</em> và <em>Dân tộc</em>.",
                    "<strong>4 Biểu đồ phân tích:</strong> (1) <em>Treemap Phân bố dân số 15 huyện</em> (diện tích là số hộ, độ đậm màu là tỷ lệ cận nghèo), (2) <em>Cơ cấu 10 dân tộc chủ lực</em>, (3) <em>Tháp tuổi 3 nhóm tuổi (0–14, 15–59, 60+)</em> và (4) <em>Tương quan Gánh nặng nuôi con vs Già hóa</em>."
                ],
                "takeaway": "Bấm chọn 1 Huyện trên Treemap hoặc 1 Dân tộc trên biểu đồ cột để lọc chéo (Cross-filter) tháp tuổi của riêng nhóm đó."
            }
        elif topic == "page_2":
            return {
                "lead_answer": "Trên <strong>Trang 2 (Học vấn & Việc làm)</strong> của Power BI tập trung bóc tách chất lượng nguồn nhân lực (Dự án 5) và khoảng cách giáo dục giới tính qua <strong>4 thẻ KPI</strong> và <strong>4 biểu đồ chuyên sâu</strong>:",
                "bullet_points": [
                    "<strong>Các biểu đồ trọng tâm:</strong> (1) <em>Donut Bẫy trình độ CMKT</em>, (2) <em>Cơ cấu ngành kinh tế (Nông - Công - Dịch vụ)</em>, (3) <em>Ma trận Kỹ năng vs Bẫy nông nghiệp</em> (chứng minh % chưa qua đào tạo cao khóa chặt lao động trong nông nghiệp), và (4) <em>Nghịch lý giới trong giáo dục</em>.",
                    "<strong>Cách khai thác Slicer đặc thù:</strong> Trang 2 có thêm bộ lọc <em>Nhóm nguồn gốc (Bản địa Tây Nguyên vs Di cư)</em> — bấm thử bạn sẽ thấy nhóm Mẫu hệ bản địa (Ê Đê, M'Nông) có tỷ lệ nữ biết chữ ngang bằng nam, trong khi nhóm Phụ hệ di cư (Mông, Dao) phụ nữ thiệt thòi hơn hẳn."
                ],
                "takeaway": "Dùng trang này để xác định quy mô lao động cần mở lớp đào tạo nghề nông thôn ngắn hạn (định mức 6 triệu VNĐ/người)."
            }
        elif topic == "page_3":
            return {
                "lead_answer": "Trên <strong>Trang 3 (Điều kiện sống)</strong> của Power BI được bố cục gồm <strong>4 thẻ KPI điều hành</strong> và <strong>4 biểu đồ đối sánh</strong> nhằm giám sát hạ tầng thiết yếu và tư liệu sản xuất của hộ DTTS:",
                "bullet_points": [
                    "<strong>4 Biểu đồ trên trang:</strong> (1) <em>Hiện trạng chất lượng nhà ở theo dân tộc</em> (Nhà kiên cố vs Nhà tạm), (2) <em>Điểm trũng vệ sinh môi trường cấp huyện</em> (Nước sạch, Hố xí HVS, Internet), (3) <em>Khoảng trống tín dụng NHCSXH (Hộ đang vay vs Hộ hổng vốn)</em>, và (4) <em>Đất canh tác bình quân (ha/hộ)</em>.",
                    "<strong>Điểm nhấn khi đọc biểu đồ:</strong> Nhìn vào biểu đồ <em>Điểm trũng vệ sinh cấp huyện</em>, bạn sẽ thấy ngay nghịch lý 'Công nghệ đi trước vệ sinh' (Internet phủ >95% nhưng Hố xí hợp vệ sinh tại Krông Bông, Lắk mới đạt 16–18%, làm liệt Tiêu chí 17.5 NTM)."
                ],
                "takeaway": "Kết hợp chọn Slicer Kỳ báo cáo (2019 → 2024 → 2026) trên Trang 3 để kiểm tra tốc độ xóa nhà tạm và thu hẹp khoảng trống tín dụng."
            }
        elif topic == "page_4":
            return {
                "lead_answer": "Trên <strong>Trang 4 (Ưu tiên chính sách)</strong> là trang ra quyết định cuối cùng của Power BI, kết nối các điểm nóng rủi ro với <strong>Dự toán ngân sách đầu tư công (5.119,65 tỷ VNĐ)</strong>:",
                "bullet_points": [
                    "<strong>4 Khối phân tích hành động:</strong> (1) <em>Ma trận 4 Góc phần tư: Khoảng cách km vs Tỷ lệ nghèo cấp xã</em> (khoanh vùng Xã khó khăn kép), (2) <em>Bảng Cảnh báo đỏ Y tế sinh sản (sinh tại nhà, không bà đỡ)</em>, (3) <em>Pivot Giám sát điểm nóng Ma túy & HIV cấp xã</em>, và (4) <em>Khung Hành Động Tham Mưu Chính Sách động</em>.",
                    "<strong>Cách phối hợp với Web Workbench:</strong> Sau khi lọc ra xã hoặc dân tộc trọng điểm trên Trang 4 Power BI, bạn chuyển sang Bàn Thẩm Định Web này để kéo thanh trượt mô phỏng ngân sách What-If và xuất Tờ trình A4."
                ],
                "takeaway": "Bấm chọn bất kỳ Huyện hoặc Dân tộc nào trên Trang 4 để xem hộp Khung Hành Động tự động viết lại khuyến nghị và dự toán vốn."
            }
        elif topic == "formulas_dax":
            return {
                "lead_answer": "Hệ thống chỉ số trên Power BI (100 DAX Measures) và Web Workbench được tính toán đồng nhất 100% từ CSDL PostgreSQL theo đúng chuẩn phương pháp luận thống kê và định mức pháp lý:",
                "bullet_points": [
                    "<strong>Công thức chỉ số & Khóa kỳ DAX:</strong> <em>Khoảng trống tín dụng (%)</em> = Hộ chưa vay được / Tổng hộ có nhu cầu vay × 100; <em>Xã khó khăn kép</em> = Cách huyện >15 km & Nghèo >25%; hàm <code>[Selected Period Order]</code> tự động khóa về <code>KY_2026 (163.912 hộ)</code> khi không chọn Slicer để chống cộng trùng 3 kỳ.",
                    "<strong>6 Định mức đơn giá ngân sách (Kỳ 2026–2030):</strong> Nhà tạm <b>90 tr/căn</b> (DA 1) • Vốn tín dụng <b>65 tr/hộ</b> (NĐ 28) • Sinh kế nghèo <b>30 tr/hộ</b> (DA 3) • Hố xí HVS <b>12 tr/hộ</b> (TC 17.5 NTM) • Học nghề <b>6 tr/người</b> (DA 5) • Sinh đẻ an toàn <b>4,5 tr/ca</b> (DA 7)."
                ],
                "takeaway": "Bạn có thể bấm sang Tab 3 ('Truy Vấn & Kiểm Toán CSDL') ngay trên màn hình Web để đối chiếu trực tiếp câu lệnh SQL của từng chỉ số."
            }
        else:
            return {
                "lead_answer": "Báo cáo Power BI của dự án gồm <strong>4 trang chuyên đề</strong> được thiết kế theo mạch phân tích từ Tổng quan nhân khẩu → Nguyên nhân gốc rễ → Điều kiện sống → Phân bổ ngân sách:",
                "bullet_points": [
                    "<strong>Cấu trúc 4 trang:</strong> <b>Trang 1 (Dân số & Địa bàn)</b> xem quy mô 163.912 hộ, Treemap 15 huyện & Tháp tuổi → <b>Trang 2 (Học vấn & Việc làm)</b> xem bẫy chưa đào tạo nghề & bất bình đẳng giới → <b>Trang 3 (Điều kiện sống)</b> xem Nhà tạm, Hố xí NTM, Vốn vay & Đất đai → <b>Trang 4 (Ưu tiên chính sách)</b> xem Ma trận 4 góc phần tư, Điểm nóng Y tế/ANTT & Dự toán vốn.",
                    "<strong>Cách sử dụng hiệu quả nhất:</strong> Dùng 3 Slicer ở góc phải (<em>Kỳ báo cáo, Huyện, Dân tộc</em>) hoặc bấm trực tiếp vào biểu đồ để lọc chéo (Cross-filter); sau đó đọc hộp <em>Khung Hành Động Tham Mưu</em> ở Trang 4 và sang Web Workbench này để mô phỏng ngân sách What-If / in Tờ trình A4."
                ],
                "takeaway": "Bạn có thể hỏi sâu hơn về từng trang hoặc biểu đồ (VD: 'Trang 2 đọc thế nào?', 'Biểu đồ 4 góc phần tư là gì?', 'Tại sao không bị cộng dồn 3 kỳ?')."
            }

    # 1. Nếu câu hỏi xoay quanh 1 đối tượng cụ thể (có chuỗi thời gian 3 kỳ 2019 -> 2024 -> 2026)
    if is_multi and len(df) >= 2:
        r_first = df.iloc[0]
        r_last = df.iloc[-1]
        subj = e.xa or huyen_disp or (f"Dân tộc {eth_disp}" if eth_disp else pretty_entity(r_last.get("ten_doi_tuong", "đối tượng khảo sát")))

        if code == "POVERTY_COMMUNE":
            v19 = float(r_first.get("ty_le_ngheo_pct", 0) or 0)
            v26 = float(r_last.get("ty_le_ngheo_pct", 0) or 0)
            diff_last = float(r_last.get("bien_dong_ty_le_ngheo_pct", 0) or 0)
            ho_ngheo = int(float(r_last.get("so_ho_ngheo", 0) or 0))
            tong_ho = int(float(r_last.get("tong_ho_dtts", 0) or 0))
            h_lbl = pretty_entity(r_last.get("ten_huyen", ""))

            if v26 <= 15.0 and diff_last < 0:
                lead = f"Hiện nay ({period_short}), <strong>{subj} ({h_lbl})</strong> đã kéo giảm tỷ lệ hộ nghèo xuống chỉ còn <strong>{v26:.2f}%</strong> (vỏn vẹn <strong>{ho_ngheo:,} hộ nghèo</strong> trên tổng {tong_ho:,} hộ DTTS), đạt chuẩn giảm nghèo bền vững."
            elif diff_last >= 0:
                lead = f"Tại {period_short}, tỷ lệ hộ nghèo của <strong>{subj} ({h_lbl})</strong> đang ở mức rất cao là <strong>{v26:.2f}%</strong> (<strong>{ho_ngheo:,}/{tong_ho:,} hộ DTTS</strong>) và phát sinh <strong>tăng ngược {diff_last:+.2f} điểm %</strong> so với kỳ liền trước."
            else:
                lead = f"Hiện nay ({period_short}), <strong>{subj} ({h_lbl})</strong> còn <strong>{ho_ngheo:,} hộ nghèo</strong> (chiếm <strong>{v26:.2f}%</strong> trên tổng số {tong_ho:,} hộ DTTS), đã giảm được <strong>{abs(diff_last):.2f} điểm %</strong> so với kỳ trước."

            traj_p = " → ".join([
                f"năm {short_yr(r)}: <b>{float(r.get('ty_le_ngheo_pct', 0)):.2f}%</b> ({int(float(r.get('so_ho_ngheo', 0))):,} hộ)"
                for _, r in df.iterrows()
            ])
            bullets = [
                f"<strong>Diễn biến 2019 – 2026:</strong> Chuyển dịch từ {traj_p} (lũy kế giảm {v19 - v26:.2f} điểm % sau 7 năm).",
                fair_cards.get("analysis", [""])[0]
            ]
            takeaway = f"Giải ngân {float(r_last.get('du_toan_ngan_sach_sinh_ke_trieu_vnd', 0)):,.0f} triệu VNĐ vốn sinh kế Dự án 3 ({act.get('what', '')})."
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": takeaway}

        elif code == "HOUSING_POVERTY":
            v19 = int(float(r_first.get("so_ho_nha_tam_don_so", 0) or 0))
            v26 = int(float(r_last.get("so_ho_nha_tam_don_so", 0) or 0))
            pct26 = float(r_last.get("ty_le_nha_tam_pct", 0) or 0)
            tot_ho26 = int(float(r_last.get("tong_ho_co_nha", 0) or 0))
            traj_h0 = " → ".join([
                f"năm {short_yr(r)}: <b>{int(float(r.get('so_ho_nha_tam_don_so', 0))):,} căn</b>"
                for _, r in df.iterrows()
            ])
            traj_h1 = " → ".join([
                f"năm {short_yr(r)}: <b>{int(float(r.get('so_ho_nha_tam_don_so', 0))):,} căn</b> ({float(r.get('ty_le_nha_tam_pct', 0)):.1f}%)"
                for _, r in df.iterrows()
            ])
            if v26 == 0:
                lead = f"Tính đến {period_short}, đồng bào <strong>{eth_disp or subj}</strong> đã <strong>xóa trắng hoàn toàn 100% nhà tạm, dột nát</strong> — cả <strong>{tot_ho26:,}/{tot_ho26:,} hộ</strong> trên địa bàn tỉnh đều đã có nhà ở kiên cố, an toàn (hiện còn <strong>0 căn</strong>)."
                bullets = [
                    f"<strong>Lộ trình xóa nhà tạm:</strong> Chuyển dịch từ {traj_h0} (xóa dứt điểm toàn bộ {v19:,} căn tồn đọng của giai đoạn trước).",
                    f"Do đã hoàn thành 100% mục tiêu về nhà ở, địa phương không cần bố trí thêm ngân sách xây nhà tạm mới cho nhóm này."
                ]
                takeaway = f"Chuyển trọng tâm chính sách cho đồng bào {eth_disp or subj} sang hỗ trợ vốn vay sản xuất (NĐ 28) và đào tạo nghề."
            else:
                lead = f"Hiện nay ({period_short}), đồng bào <strong>{eth_disp or subj}</strong> còn <strong>{v26:,} hộ</strong> đang ở nhà tạm, đơn sơ — chiếm <strong>{pct26:.2f}%</strong> trên tổng số {tot_ho26:,} hộ toàn tỉnh."
                bullets = [
                    f"<strong>Đà giảm qua 3 kỳ:</strong> Đã xóa được <b>{v19 - v26:,} căn</b> sau 7 năm ({traj_h1}).",
                    fair_cards.get("analysis", [""])[0]
                ]
                takeaway = f"Cần bố trí <strong>{v26 * 90.0 / 1000.0:,.2f} tỷ VNĐ</strong> (định mức 90 triệu VNĐ/căn - Dự án 1) để xóa dứt điểm {v26:,} căn còn lại."
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": takeaway}

        elif code == "VULNERABILITY_HEALTH":
            v19 = int(float(r_first.get("chi_so_rui_ro_chinh", 0) or 0))
            v26 = int(float(r_last.get("chi_so_rui_ro_chinh", 0) or 0))
            sub26 = int(float(r_last.get("chi_so_rui_ro_phu", 0) or 0))
            pct_drop = float(r_last.get("ty_le_giam_rui_ro_pct", 0) or 0)
            is_birth = ("sinh" in str(r_last.get("phan_nhom_rui_ro", "")).lower()) or bool(e.dantoc)
            if is_birth:
                lead = f"Hiện nay ({period_short}), cộng đồng <strong>{eth_disp or subj}</strong> còn ghi nhận <strong>{v26:,} ca sinh con tại nhà</strong>, trong đó có <strong>{sub26:,} ca sinh nguy cơ cao không có cán bộ y tế đỡ</strong>."
                traj_v = " → ".join([
                    f"năm {short_yr(r)}: <b>{int(float(r.get('chi_so_rui_ro_chinh', 0))):,} ca</b> ({int(float(r.get('chi_so_rui_ro_phu', 0))):,} ca không bà đỡ)"
                    for _, r in df.iterrows()
                ])
                takeaway = f"Duy trì mạng lưới Cô đỡ thôn bản và gói hỗ trợ sinh đẻ an toàn 4,5 triệu VNĐ/ca (tổng {v26 * 4.5:,.1f} triệu VNĐ)."
            else:
                lead = f"Tại điểm nóng <strong>{subj}</strong> trong {period_short}, cơ quan chức năng đang quản lý <strong>{v26:,} người DTTS nghiện ma túy</strong> và <strong>{sub26:,} ca nhiễm HIV</strong> (đã giảm {abs(pct_drop):.2f}% so với kỳ liền trước)."
                traj_v = " → ".join([
                    f"năm {short_yr(r)}: <b>{int(float(r.get('chi_so_rui_ro_chinh', 0))):,} người nghiện</b> ({int(float(r.get('chi_so_rui_ro_phu', 0))):,} ca HIV)"
                    for _, r in df.iterrows()
                ])
                takeaway = "Duy trì chốt kiểm soát an ninh cơ sở, điều trị Methadone/ARV lưu động gắn với dạy nghề tái hòa nhập."
            bullets = [
                f"<strong>Diễn biến 2019 – 2026:</strong> {traj_v}.",
                fair_cards.get("analysis", [""])[0]
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": takeaway}

        elif code in ("SANITATION_DIGITAL", "DISTRICT_OVERVIEW"):
            h19 = float(r_first.get("ty_le_ho_xi_hvs_bq_pct", 0) or 0)
            h26 = float(r_last.get("ty_le_ho_xi_hvs_bq_pct", 0) or 0)
            net26 = float(r_last.get("ty_le_internet_huyen_pct", 0) or 0)
            nuoc26 = float(r_last.get("ty_le_nuoc_hvs_bq_pct", 0) or 0)
            status_str = f"<strong>vượt {h26 - 70.0:.2f} điểm %</strong> so với chuẩn Nông thôn mới (70%)" if h26 >= 70.0 else f"vẫn còn thiếu <strong>{70.0 - h26:.2f} điểm %</strong> so với chuẩn Tiêu chí 17 NTM (70%)"
            lead = f"Tại <strong>{subj}</strong> ({period_short}), tỷ lệ hộ DTTS có hố xí hợp vệ sinh đạt <strong>{h26:.2f}%</strong> ({status_str}), trong khi phủ sóng Internet đã đạt <strong>{net26:.2f}%</strong> và nước hợp vệ sinh đạt <strong>{nuoc26:.2f}%</strong>."
            traj_s = " → ".join([
                f"năm {short_yr(r)}: <b>{float(r.get('ty_le_ho_xi_hvs_bq_pct', 0)):.2f}%</b>"
                for _, r in df.iterrows()
            ])
            bullets = [
                f"<strong>Tiến độ cải thiện vệ sinh (2019 – 2026):</strong> Tăng thêm {h26 - h19:+.2f} điểm % ({traj_s}).",
                fair_cards.get("analysis", [""])[0]
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"{act.get('what', '')} ({act.get('budget_text', '')})."}

        elif code == "LABOR_EDUCATION":
            c19 = float(r_first.get("ty_le_khong_cmkt_pct", 0) or 0)
            c26 = float(r_last.get("ty_le_khong_cmkt_pct", 0) or 0)
            ld26 = int(float(r_last.get("lao_dong_khong_cmkt", 0) or 0))
            nu26 = float(r_last.get("ty_le_nu_biet_chu_pct", 0) or 0)
            lead = f"Hiện nay ({period_short}), tỷ lệ lao động chưa qua đào tạo CMKT của đồng bào <strong>{eth_disp or subj}</strong> ở mức <strong>{c26:.2f}%</strong> (tương ứng <strong>{ld26:,} người</strong> chưa có chứng chỉ nghề; tỷ lệ phụ nữ biết chữ đạt <strong>{nu26:.2f}%</strong>)."
            traj_l = " → ".join([
                f"năm {short_yr(r)}: <b>{float(r.get('ty_le_khong_cmkt_pct', 0)):.2f}%</b>"
                for _, r in df.iterrows()
            ])
            bullets = [
                f"<strong>Đà giảm qua 3 kỳ:</strong> Tỷ lệ lao động chưa đào tạo đã giảm {c19 - c26:.2f} điểm % ({traj_l}).",
                fair_cards.get("analysis", [""])[0]
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"Dự toán đào tạo nghề Dự án 5 cho đồng bào {eth_disp or subj}: <strong>{ld26 * 6.0 / 1000.0:,.2f} tỷ VNĐ</strong> (6 triệu VNĐ/lao động)."}

        elif code == "ETHNIC_OVERVIEW":
            ho26 = int(float(r_last.get("tong_ho_co_nha", 0) or 0))
            ds26 = int(float(r_last.get("tong_dan_so", 0) or 0))
            nt19 = int(float(r_first.get("so_ho_nha_tam_don_so", 0) or 0))
            nt26 = int(float(r_last.get("so_ho_nha_tam_don_so", 0) or 0))
            kv26 = int(float(r_last.get("so_ho_khat_von", 0) or 0))
            cm26 = float(r_last.get("ty_le_khong_cmkt_pct", 0) or 0)
            dat26 = float(r_last.get("dien_tich_dat_sx_bq_ha", 0) or 0)
            lead = f"Tại {period_short}, cộng đồng <strong>Dân tộc {eth_disp or subj}</strong> ({r_last.get('nhom_nguon_goc', 'DTTS tại Đắk Lắk')}) có quy mô <strong>{ho26:,} hộ ({ds26:,} nhân khẩu)</strong>, quỹ đất sản xuất bình quân đạt <strong>{dat26:.2f} ha/hộ</strong>."
            bullets = [
                f"<strong>Nhà ở & Tín dụng:</strong> Số nhà tạm đã giảm từ {nt19:,} căn (năm 2019) xuống còn <b>{nt26:,} căn</b> ({float(r_last.get('ty_le_nha_tam_pct', 0)):.2f}%); hiện có <b>{kv26:,} hộ</b> cần vay vốn tín dụng ưu đãi ({float(r_last.get('khoang_trong_tin_dung_pct', 0)):.2f}%).",
                f"<strong>Nhân lực & Học vấn:</strong> Lao động chưa qua đào tạo CMKT ở mức <b>{cm26:.2f}%</b> ({int(float(r_last.get('lao_dong_khong_cmkt', 0))):,} người); lao động nông nghiệp chiếm <b>{float(r_last.get('ty_le_nong_nghiep_pct', 0)):.2f}%</b>; phụ nữ biết chữ đạt <b>{float(r_last.get('ty_le_nu_biet_chu_pct', 0)):.2f}%</b>."
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"Tổng gói nguồn lực Nhà ở & Vốn vay cho đồng bào {eth_disp or subj}: <strong>{act.get('budget_text', '')}</strong>."}

        elif code == "CREDIT_LAND":
            kv19 = int(float(r_first.get("so_ho_khat_von", 0) or 0))
            kv26 = int(float(r_last.get("so_ho_khat_von", 0) or 0))
            gap26 = float(r_last.get("khoang_trong_tin_dung_pct", 0) or 0)
            dat26 = float(r_last.get("dien_tich_dat_sx_bq_ha", 0) or 0)
            lead = f"Hiện nay ({period_short}), đồng bào <strong>{eth_disp or subj}</strong> còn <strong>{kv26:,} hộ</strong> có nhu cầu vay vốn sản xuất nhưng chưa tiếp cận được tín dụng ưu đãi (tỷ lệ thiếu hụt <strong>{gap26:.2f}%</strong>, bình quân đất canh tác <strong>{dat26:.2f} ha/hộ</strong>)."
            traj_c = " → ".join([
                f"năm {short_yr(r)}: <b>{int(float(r.get('so_ho_khat_von', 0))):,} hộ</b>"
                for _, r in df.iterrows()
            ])
            bullets = [
                f"<strong>Đà thu hẹp khoảng trống tín dụng:</strong> Đã giải quyết vốn cho {kv19 - kv26:,} hộ sau 3 kỳ ({traj_c}).",
                fair_cards.get("analysis", [""])[0]
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"Cần bổ sung hạn mức tín dụng NHCSXH <strong>{kv26 * 65.0 / 1000.0:,.2f} tỷ VNĐ</strong> (65 triệu VNĐ/hộ theo NĐ 28)."}

    # 2. Nếu hỏi về Xếp hạng / Top N / So sánh danh sách nhiều đối tượng
    if is_asking_top or len(df) > 3:
        top_n = min(3, len(df))
        if code in ("POLICY_BUDGET", "DASHBOARD_GUIDE"):
            tot_b = float(df["tong_kinh_phi_can_phan_bo_ty_vnd"].sum()) if "tong_kinh_phi_can_phan_bo_ty_vnd" in df.columns else 0.0
            scope_t = e.xa or huyen_disp or (f"Dân tộc {eth_disp}" if eth_disp else "Toàn tỉnh Đắk Lắk")
            lead = f"Tại phạm vi <strong>{scope_t}</strong> ({period_short}), tổng nhu cầu ngân sách đầu tư công là <strong>{tot_b:,.2f} tỷ VNĐ</strong>, được phân bổ vào 5 gói chính sách trụ cột theo thứ tự ưu tiên từ cao xuống thấp:"
            bullets = [
                f"<strong>#{i+1}. {r.get('ten_chitieu')}:</strong> <strong>{float(r.get('tong_kinh_phi_can_phan_bo_ty_vnd', 0)):,.2f} tỷ VNĐ</strong> ({int(float(r.get('so_luong_doi_tuong_can_ho_tro', 0))):,} {r.get('don_vi_tinh', '')} × {r.get('don_gia_trieu_vnd')} tr.đ)"
                for i, (_, r) in enumerate(df.head(4).iterrows())
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"Cơ chế điều hành: {act.get('what', '')} ({act.get('budget_text', '')})."}

        elif code == "POVERTY_COMMUNE":
            scope_t = huyen_disp or "toàn tỉnh Đắk Lắk"
            dir_lbl = "thấp nhất (tốt nhất)" if e.sort_order == "ASC" else "cao nhất"
            lead = f"Dưới đây là các xã có tỷ lệ hộ nghèo <strong>{dir_lbl}</strong> tại <strong>{scope_t}</strong> trong {period_short} (trích xuất từ {len(df)} xã):"
            bullets = [
                f"<strong>#{i+1}. {r.get('ten_xa')} ({pretty_entity(r.get('ten_huyen'))}):</strong> Tỷ lệ nghèo <strong>{float(r.get('ty_le_ngheo_pct', 0)):.2f}%</strong> ({int(float(r.get('so_ho_ngheo', 0))):,} hộ nghèo, biến động {float(r.get('bien_dong_ty_le_ngheo_pct', 0) or 0):+.2f} pp, cách huyện {float(r.get('km_den_trung_tam_huyen', 0) or 0):.1f} km)."
                for i, (_, r) in enumerate(df.head(top_n).iterrows())
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": fair_cards.get("analysis", [""])[0] if is_asking_why else f"Giải pháp trọng tâm: {act.get('what', '')} ({act.get('budget_text', '')})."}

        elif code == "DEFAULT_MACRO_OVERVIEW":
            lead = f"Báo cáo tổng quan kinh tế - xã hội 53 dân tộc thiểu số tỉnh Đắk Lắk trong <strong>{period_short}</strong>:"
            bullets = [
                f"<strong>1. Quy mô & Nhân khẩu (Trang 1):</strong> <b>163.912 hộ DTTS</b> (665.234 nhân khẩu) thuộc 53 dân tộc sinh sống tại 15 huyện/TX/TP; dân tộc Ê Đê chiếm đông nhất (hơn 405.000 người, tháp tuổi dân số vàng 62.0% tuổi lao động).",
                f"<strong>2. Vốn con người & Việc làm (Trang 2):</strong> <b>82.46%</b> lao động DTTS chưa qua đào tạo chuyên môn kỹ thuật, khiến <b>84.3%</b> bị khóa chặt trong nông nghiệp năng suất thấp.",
                f"<strong>3. Điều kiện sống & Hạ tầng (Trang 3):</strong> Còn <b>6.378 nhà tạm</b> (đã xóa 100% cho 4 hộ Chơ Ro); khoảng trống tín dụng NHCSXH còn <b>25.570 hộ khát vốn</b>; hố xí hợp vệ sinh tại Krông Bông (16.2%), Lắk (18.1%) là điểm trũng đe dọa Tiêu chí 17 NTM.",
                f"<strong>4. Ưu tiên chính sách & Dự toán ngân sách (Trang 4):</strong> Tổng nhu cầu đầu tư công đạt <b>5.119,65 tỷ VNĐ</b> theo định mức QĐ 1719 và NĐ 28/2022/NĐ-CP."
            ]
            takeaway = "Gợi ý: Bạn có thể hỏi sâu về một địa bàn (VD: 'Huyện Lắk', 'Xã Nam Ka'), một dân tộc (VD: 'Người Ê Đê', 'Người Mông'), hoặc một biểu đồ (VD: 'Tháp tuổi 3 nhóm tuổi', 'Biểu đồ 4 góc phần tư')."
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": takeaway}

        elif code == "HOUSING_POVERTY":
            col_nha = "so_ho_nha_tam_don_so" if "so_ho_nha_tam_don_so" in df.columns else "tong_ho_nha_tam"
            tot_nha = int(float(df[col_nha].sum())) if col_nha in df.columns else 0
            lead = f"Trong {period_short}, tổng số nhà tạm của {len(df)} nhóm dẫn đầu là <strong>{tot_nha:,} căn</strong>. Top 3 đối tượng có quy mô nhà tạm cần ưu tiên giải quyết gồm:"
            bullets = [
                f"<strong>#{i+1}. {pretty_entity(r.get('ten_dantoc', r.get('ten_huyen', '')))}:</strong> <strong>{int(float(r.get(col_nha, 0))):,} căn</strong> (chiếm {float(r.get('ty_le_nha_tam_pct', 0) or 0):.2f}% số hộ, cần {int(float(r.get(col_nha, 0))) * 90.0 / 1000.0:,.2f} tỷ VNĐ)."
                for i, (_, r) in enumerate(df.head(top_n).iterrows())
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"Áp dụng định mức 90 triệu VNĐ/căn (Dự án 1 - QĐ 1719), tổng dự toán nhóm này là <strong>{tot_nha * 90.0 / 1000.0:,.2f} tỷ VNĐ</strong>."}

        elif code in ("SANITATION_DIGITAL", "DISTRICT_OVERVIEW"):
            dir_lbl = "thấp nhất (vùng trũng cần ưu tiên)" if e.sort_order == "ASC" else "cao nhất"
            lead = f"Kết quả rà soát Tiêu chí 17.5 Nông thôn mới (Hố xí hợp vệ sinh) và Internet Đề án 06 ({period_short}, sắp xếp theo mức <strong>{dir_lbl}</strong>):"
            bullets = [
                f"<strong>#{i+1}. {pretty_entity(r.get('ten_huyen'))}:</strong> Hố xí HVS đạt <strong>{float(r.get('ty_le_ho_xi_hvs_bq_pct', 0)):.2f}%</strong> ({r.get('trang_thai_ntm_tc17')}) | Phủ Internet đạt <strong>{float(r.get('ty_le_internet_huyen_pct', 0)):.2f}%</strong>."
                for i, (_, r) in enumerate(df.head(top_n).iterrows())
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": fair_cards.get("analysis", [""])[0]}

        elif code == "LABOR_EDUCATION":
            is_illiteracy = "mu_chu" in e.metric_keys or any(w in question.lower() for w in ["mu chu", "biet chu", "hoc van", "tai sao", "vi sao", "vung sau"])
            if is_illiteracy:
                top_puy = [f"<b>{pretty_entity(r.get('ten_dantoc'))}</b> ({float(r.get('ty_le_nu_biet_chu_pct', 0)):.1f}%)" for _, r in df.head(3).iterrows()]
                lead = f"Tỷ lệ mù chữ và học vấn thấp tại vùng sâu, vùng đồng bào DTTS ({period_short}) bắt nguồn từ 3 rào cản cốt lõi: bất đồng ngôn ngữ, địa hình cách trở và áp lực mưu sinh gia đình:"
                bullets = [
                    "<strong>1. Rào cản ngôn ngữ & thiếu giáo viên song ngữ:</strong> Phụ nữ và người lớn tuổi tại các thôn/buôn vùng sâu chủ yếu sử dụng tiếng mẹ đẻ, ít tiếp xúc với tiếng Việt phổ thông ngoài chợ cụm; tài liệu học thiếu chữ viết bản địa song ngữ.",
                    "<strong>2. Địa hình chia cắt & cự ly đến trường 10–25 km:</strong> Đường sá cách trở mùa mưa lũ khiến việc duy trì sĩ số học sinh khó khăn, dẫn đến tình trạng bỏ học giữa chừng và người lớn tái mù chữ sau khi hoàn thành các lớp phổ cập ngắn hạn.",
                    "<strong>3. Áp lực mưu sinh & định kiến giới trong gia đình phụ hệ:</strong> Trẻ em gái ở một số nhóm di cư (Mông, Dao...) thường phải ở nhà phụ giúp cha mẹ làm nương rẫy từ nhỏ và tảo hôn sớm (15–17 tuổi), làm đứt gãy con đường học vấn.",
                    f"<strong>Thực chứng số liệu:</strong> Tỷ lệ phụ nữ biết chữ thấp nhất tỉnh ghi nhận ở nhóm {', '.join(top_puy)}."
                ]
                return {
                    "lead_answer": lead,
                    "bullet_points": bullets,
                    "takeaway": "Mở các lớp xóa mù chữ linh hoạt ban đêm tại nhà sinh hoạt cộng đồng buôn/thôn, cấp phụ cấp ăn ở và gắn với dạy nghề nông nghiệp thực hành (Dự án 5 MTQG 1719)."
                }
            else:
                lead = f"Dữ liệu chất lượng nguồn nhân lực và học vấn giới ({period_short}) ghi nhận sự phân hóa rõ nét giữa các dân tộc:"
                bullets = [
                    f"<strong>#{i+1}. Dân tộc {pretty_entity(r.get('ten_dantoc'))}:</strong> <strong>{float(r.get('ty_le_khong_cmkt_pct', 0)):.2f}%</strong> chưa qua đào tạo nghề ({int(float(r.get('lao_dong_khong_cmkt', 0))):,} người), <strong>{float(r.get('ty_le_nong_nghiep_pct', 0)):.2f}%</strong> làm nông nghiệp, nữ biết chữ đạt <strong>{float(r.get('ty_le_nu_biet_chu_pct', 0)):.2f}%</strong>."
                    for i, (_, r) in enumerate(df.head(top_n).iterrows())
                ]
                return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"{act.get('what', '')} ({act.get('budget_text', '')})."}

        elif code == "CREDIT_LAND":
            lead = f"Thống kê khoảng trống tín dụng ưu đãi (NĐ 28) và quỹ đất sản xuất bình quân hộ ({period_short}):"
            bullets = [
                f"<strong>#{i+1}. Dân tộc {pretty_entity(r.get('ten_dantoc'))}:</strong> <strong>{int(float(r.get('so_ho_khat_von', 0))):,} hộ khát vốn</strong> (thiếu hụt {float(r.get('khoang_trong_tin_dung_pct', 0)):.2f}%), đất sản xuất bình quân <strong>{float(r.get('dien_tich_dat_sx_bq_ha', 0)):.2f} ha/hộ</strong>."
                for i, (_, r) in enumerate(df.head(top_n).iterrows())
            ]
            return {"lead_answer": lead, "bullet_points": bullets, "takeaway": f"{act.get('what', '')} ({act.get('budget_text', '')})."}

    # 3. Trường hợp còn lại: Trả lời cô đọng, tự nhiên từ fair_cards đã cá nhân hóa
    return {
        "lead_answer": fair_cards.get("headline", ""),
        "bullet_points": [
            fair_cards.get("fact", [""])[0],
            fair_cards.get("analysis", [""])[0]
        ],
        "takeaway": f"{act.get('what', '')} — Kinh phí: <strong>{act.get('budget_text', '')}</strong>."
    }


def build_echart_payload(intent: PolicyIntent, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Sinh cấu hình dữ liệu biểu đồ tương tác Apache ECharts 5 tùy biến theo từng Chuyên đề.
    """
    code = intent.intent_code
    if df is None or df.empty:
        return {"type": "empty", "title": "Không có dữ liệu biểu đồ"}

    if code in ("DEMOGRAPHIC_COMPARISON", "DASHBOARD_GUIDE"):
        top = intent.entities.guide_topic or "age_pyramid"
        if top == "age_pyramid" or code == "DEMOGRAPHIC_COMPARISON":
            cats = [str(r.get("ten_dantoc", "")) for _, r in df.iterrows()]
            age_0_14 = [round(float(r.get("ty_le_0_14_pct", 0) or 0), 1) for _, r in df.iterrows()]
            age_15_59 = [round(float(r.get("ty_le_15_59_pct", 0) or 0), 1) for _, r in df.iterrows()]
            age_60_plus = [round(float(r.get("ty_le_60_plus_pct", 0) or 0), 1) for _, r in df.iterrows()]
            return {
                "type": "age_stacked_bar",
                "title": f"Tháp Tuổi & Cơ Cấu 3 Nhóm Tuổi Dân Tộc ({intent.entities.ky_baocao})",
                "subtitle": "Xếp chồng 100%: 0-14 tuổi (Xanh lá) | 15-59 tuổi (Xanh dương) | 60+ tuổi (Cam)",
                "categories": cats,
                "series_0_14": age_0_14,
                "series_15_59": age_15_59,
                "series_60_plus": age_60_plus,
                "unit": "%"
            }
        elif top == "treemap_pop":
            cats = [str(r.get("ten_huyen", "")).replace("Huyện ", "").replace("Thị Xã ", "TX. ").replace("Thành phố ", "TP. ") for _, r in df.iterrows()]
            ho_dtts = [int(float(r.get("tong_ho_dtts", 0) or 0)) for _, r in df.iterrows()]
            return {
                "type": "horizontal_bar",
                "title": f"Phân Bố Dân Số & Hộ DTTS Theo 15 Huyện ({intent.entities.ky_baocao})",
                "subtitle": "Quy mô số hộ DTTS sinh sống trên từng địa bàn cấp huyện",
                "categories": cats,
                "series_main": ho_dtts,
                "unit": "hộ"
            }
        elif top == "quadrant_chart":
            labels = [f"{r.get('ten_xa')} ({r.get('ten_huyen')})" for _, r in df.iterrows()]
            pov_vals = [round(float(r.get("ty_le_ngheo_pct", 0) or 0), 2) for _, r in df.iterrows()]
            km_vals = [round(float(r.get("km_den_trung_tam_huyen", 0) or 0), 1) for _, r in df.iterrows()]
            return {
                "type": "dual_horizontal",
                "title": f"Ma Trận Khoảng Cách vs Tỷ Lệ Nghèo Cấp Xã ({intent.entities.ky_baocao})",
                "subtitle": "Các xã vùng sâu khó khăn kép: cự ly xa trung tâm huyện & tỷ lệ nghèo cao",
                "categories": labels,
                "series_main": pov_vals,
                "series_sub": km_vals,
                "series_main_name": "Tỷ lệ nghèo (%)",
                "series_sub_name": "Khoảng cách (km)",
                "unit": "%"
            }

    if code in ("POLICY_BUDGET", "DASHBOARD_GUIDE"):
        e_ent = intent.entities
        scope_title = e_ent.xa or e_ent.huyen or (f"Dân tộc {e_ent.dantoc}" if e_ent.dantoc else "Toàn Tỉnh Đắk Lắk")
        labels = [str(r.get("ten_chitieu", "")) for _, r in df.iterrows()]
        values = [round(float(r.get("tong_kinh_phi_can_phan_bo_ty_vnd", 0) or 0), 2) for _, r in df.iterrows()]
        prev_diff = [round(float(r.get("bien_dong_kinh_phi_ty_vnd", 0) or 0), 2) for _, r in df.iterrows()]
        return {
            "type": "budget_bar",
            "title": f"Cơ Cấu Dự Toán Ngân Sách Đầu Tư Công — {scope_title} (Tỷ VNĐ)",
            "subtitle": "Nguồn: Bảng định mức QĐ 1719/QĐ-TTg & NĐ 28/2022/NĐ-CP",
            "categories": labels,
            "series_main": values,
            "series_sub": prev_diff,
            "unit": "tỷ VNĐ"
        }

    elif code in ("POVERTY_COMMUNE", "DEFAULT_MACRO_OVERVIEW"):
        is_multi = len(df["ma_ky"].unique()) > 1 if "ma_ky" in df.columns else False
        if is_multi:
            cats = [str(r.get("ten_ky", "")) for _, r in df.iterrows()]
            vals = [round(float(r.get("ty_le_ngheo_pct", 0) or 0), 2) for _, r in df.iterrows()]
            return {
                "type": "trend_line",
                "title": f"Diễn Biến Tỷ Lệ Hộ Nghèo Qua 3 Chu Kỳ — {df.iloc[0].get('ten_xa', '')}",
                "subtitle": "Đường tham chiếu đỏ: Ngưỡng chuẩn Khu vực III (15.0%)",
                "categories": cats,
                "series_main": vals,
                "target_line": 15.0,
                "unit": "%"
            }
        else:
            has_huyen = bool(intent.entities.huyen)
            slice_df = df.head(20) if has_huyen else df.head(12)
            cats = [
                str(r.get('ten_xa', '')) if has_huyen else f"{r.get('ten_xa', '')} ({str(r.get('ten_huyen', '')).replace('Huyện ', '')})"
                for _, r in slice_df.iterrows()
            ]
            vals = [round(float(r.get("ty_le_ngheo_pct", 0) or 0), 2) for _, r in slice_df.iterrows()]
            dists = [round(float(r.get("km_den_trung_tam_huyen", 0) or 0), 1) for _, r in slice_df.iterrows()]
            chart_title = (
                f"Xếp Hạng Tỷ Lệ Hộ Nghèo & Cự Ly Y Tế Các Xã Thuộc {intent.entities.huyen} ({len(slice_df)} Xã)"
                if has_huyen
                else "Top Địa Bàn Cấp Xã Có Tỷ Lệ Hộ Nghèo Cao Nhất & Cự Ly Giao Thông"
            )
            return {
                "type": "dual_horizontal",
                "title": chart_title,
                "subtitle": "Bấm vào từng Xã để xem Xu hướng 3 kỳ & Phiếu tham mưu • Chuẩn KV III: <= 15.0%",
                "categories": cats[::-1],
                "series_main": vals[::-1],
                "series_sub": dists[::-1],
                "target_line": 15.0,
                "target_label": "Chuẩn KV III (15%)",
                "drill_field": "commune",
                "unit": "%"
            }

    elif code == "HOUSING_POVERTY":
        is_multi = len(df["ma_ky"].unique()) > 1 if "ma_ky" in df.columns else False
        if is_multi:
            cats = [str(r.get("ten_ky", "")) for _, r in df.iterrows()]
            vals = [int(float(r.get("so_ho_nha_tam_don_so", 0) or 0)) for _, r in df.iterrows()]
            return {
                "type": "trend_line",
                "title": f"Lộ Trình Xóa Nhà Tạm, Dột Nát Qua 3 Kỳ — Dân Tộc {df.iloc[0].get('ten_dantoc', '')}",
                "subtitle": "Mục tiêu Dự án 1 - CTMTQG 1719: Tiến tới xóa trắng nhà tạm (0 căn)",
                "categories": cats,
                "series_main": vals,
                "target_line": 0,
                "target_label": "Mục tiêu Xóa trắng (0 căn)",
                "unit": " căn"
            }
        else:
            cats = [str(r.get("ten_dantoc", r.get("ten_huyen", ""))) for _, r in df.head(10).iterrows()]
            vals = [int(float(r.get("so_ho_nha_tam_don_so", r.get("tong_ho_nha_tam", 0)) or 0)) for _, r in df.head(10).iterrows()]
            return {
                "type": "horizontal_bar",
                "title": "Phân Bổ Số Lượng Nhà Tạm, Đơn Sơ Theo Dân Tộc / Địa Bàn (Căn)",
                "subtitle": "Bấm vào từng Dân tộc để thẩm định sâu • Định mức 90 triệu VNĐ/hộ",
                "categories": cats[::-1],
                "series_main": vals[::-1],
                "drill_field": "ethnic",
                "unit": " căn"
            }

    elif code in ("SANITATION_DIGITAL", "DISTRICT_OVERVIEW"):
        is_multi = len(df["ma_ky"].unique()) > 1 if "ma_ky" in df.columns else False
        if is_multi:
            cats = [str(r.get("ten_ky", "")) for _, r in df.iterrows()]
            hoxi = [round(float(r.get("ty_le_ho_xi_hvs_bq_pct", 0) or 0), 2) for _, r in df.iterrows()]
            net = [round(float(r.get("ty_le_internet_huyen_pct", 0) or 0), 2) for _, r in df.iterrows()]
            return {
                "type": "grouped_bar",
                "title": f"Đối Sánh Hố Xí Hợp Vệ Sinh vs Phủ Sóng Internet — {df.iloc[0].get('ten_huyen', '')}",
                "subtitle": "Chuẩn Tiêu chí 17 NTM (>= 70%) vs Chuẩn Chuyển đổi số Đề án 06 (>= 80%)",
                "categories": cats,
                "series_main": hoxi,
                "series_main_name": "Hố xí HVS (%)",
                "series_sub": net,
                "series_sub_name": "Phủ Internet (%)",
                "target_line": 70.0,
                "target_label": "Chuẩn TC17 NTM (70%)",
                "unit": "%"
            }
        else:
            cats = [str(r.get("ten_huyen", "")).replace("Huyện ", "").replace("Thị xã ", "TX. ") for _, r in df.head(10).iterrows()]
            raw_huyen = [str(r.get("ten_huyen", "")) for _, r in df.head(10).iterrows()]
            hoxi = [round(float(r.get("ty_le_ho_xi_hvs_bq_pct", 0) or 0), 2) for _, r in df.head(10).iterrows()]
            net = [round(float(r.get("ty_le_internet_huyen_pct", 0) or 0), 2) for _, r in df.head(10).iterrows()]
            return {
                "type": "grouped_bar",
                "title": "Tỷ Lệ Hố Xí Hợp Vệ Sinh (TC17 NTM) & Phủ Sóng Internet Giữa Các Huyện",
                "subtitle": "Bấm vào cột Huyện để lọc chi tiết • Đường chuẩn đỏ: TC17 NTM (>= 70%)",
                "categories": cats,
                "raw_entities": raw_huyen,
                "series_main": hoxi,
                "series_main_name": "Hố xí HVS (%)",
                "series_sub": net,
                "series_sub_name": "Phủ Internet (%)",
                "target_line": 70.0,
                "target_label": "Chuẩn NTM (70%)",
                "drill_field": "district",
                "unit": "%"
            }

    elif code == "VULNERABILITY_HEALTH":
        is_multi = len(df["ma_ky"].unique()) > 1 if "ma_ky" in df.columns else False
        if is_multi:
            cats = [str(r.get("ten_ky", "")) for _, r in df.iterrows()]
            main_v = [int(float(r.get("chi_so_rui_ro_chinh", 0) or 0)) for _, r in df.iterrows()]
            sub_v = [int(float(r.get("chi_so_rui_ro_phu", 0) or 0)) for _, r in df.iterrows()]
            return {
                "type": "grouped_bar",
                "title": f"Diễn Biến Chỉ Số Rủi Ro An Ninh / Y Tế Qua 3 Kỳ — {df.iloc[0].get('ten_doi_tuong', '')}",
                "subtitle": "Theo dõi đà giảm sau khi can thiệp y tế cơ sở và tuần tra cộng đồng",
                "categories": cats,
                "series_main": main_v,
                "series_main_name": "Chỉ số chính (Người nghiện / Ca sinh tại nhà)",
                "series_sub": sub_v,
                "series_sub_name": "Chỉ số đặc biệt (Nhiễm HIV / Không bà đỡ)",
                "unit": " ca/người"
            }
        else:
            cats = [str(r.get("ten_doi_tuong", "")) for _, r in df.head(10).iterrows()]
            vals = [int(float(r.get("tong_muc_do_rui_ro", 0) or 0)) for _, r in df.head(10).iterrows()]
            return {
                "type": "horizontal_bar",
                "title": "Xếp Hạng Các Điểm Nóng An Ninh Trật Tự & Rủi Ro Y Tế Sinh Sản",
                "subtitle": "Bấm vào từng Điểm nóng để xem giải pháp can thiệp đặc thù",
                "categories": cats[::-1],
                "series_main": vals[::-1],
                "drill_field": "mixed",
                "unit": " điểm rủi ro"
            }

    elif code == "LABOR_EDUCATION":
        is_multi = len(df["ma_ky"].unique()) > 1 if "ma_ky" in df.columns else False
        if is_multi:
            cats = [str(r.get("ten_ky", "")) for _, r in df.iterrows()]
            cmkt = [round(float(r.get("ty_le_khong_cmkt_pct", 0) or 0), 2) for _, r in df.iterrows()]
            nu_bc = [round(float(r.get("ty_le_nu_biet_chu_pct", 0) or 0), 2) for _, r in df.iterrows()]
            return {
                "type": "grouped_bar",
                "title": f"Chuyển Dịch Vốn Nhân Lực & Học Vấn Nữ Giới — Dân Tộc {df.iloc[0].get('ten_dantoc', '')}",
                "subtitle": "So sánh Tỷ lệ chưa qua đào tạo nghề (%) và Tỷ lệ nữ biết chữ (%)",
                "categories": cats,
                "series_main": cmkt,
                "series_main_name": "Chưa qua đào tạo CMKT (%)",
                "series_sub": nu_bc,
                "series_sub_name": "Nữ giới biết chữ (%)",
                "target_line": 75.0,
                "target_label": "Mục tiêu <= 75%",
                "unit": "%"
            }
        else:
            cats = [str(r.get("ten_dantoc", "")) for _, r in df.head(10).iterrows()]
            cmkt = [round(float(r.get("ty_le_khong_cmkt_pct", 0) or 0), 2) for _, r in df.head(10).iterrows()]
            nn = [round(float(r.get("ty_le_nong_nghiep_pct", 0) or 0), 2) for _, r in df.head(10).iterrows()]
            return {
                "type": "grouped_bar",
                "title": "Tương Quan Giữa Thiếu Kỹ Năng Nghề (CMKT) & Bẫy Lao Động Nông Nghiệp",
                "subtitle": "Bấm vào từng Dân tộc để thẩm định • Đường chuẩn: <= 75%",
                "categories": cats,
                "series_main": cmkt,
                "series_main_name": "Chưa qua đào tạo CMKT (%)",
                "series_sub": nn,
                "series_sub_name": "Lao động Nông nghiệp (%)",
                "target_line": 75.0,
                "target_label": "Mục tiêu <= 75%",
                "drill_field": "ethnic",
                "unit": "%"
            }

    else:  # CREDIT_LAND
        is_multi = len(df["ma_ky"].unique()) > 1 if "ma_ky" in df.columns else False
        if is_multi:
            cats = [str(r.get("ten_ky", "")) for _, r in df.iterrows()]
            vals = [int(float(r.get("so_ho_khat_von", 0) or 0)) for _, r in df.iterrows()]
            return {
                "type": "trend_line",
                "title": f"Biến Động Số Hộ Khát Vốn Tín Dụng Ưu Đãi — Dân Tộc {df.iloc[0].get('ten_dantoc', '')}",
                "subtitle": "Kênh giải ngân: Ngân hàng Chính sách Xã hội (Nghị định 28/2022/NĐ-CP)",
                "categories": cats,
                "series_main": vals,
                "target_line": 0,
                "unit": " hộ"
            }
        else:
            cats = [str(r.get("ten_dantoc", "")) for _, r in df.head(10).iterrows()]
            vals = [int(float(r.get("so_ho_khat_von", 0) or 0)) for _, r in df.head(10).iterrows()]
            return {
                "type": "horizontal_bar",
                "title": "Top Dân Tộc Có Quy Mô Hộ Khát Vốn Tín Dụng Cao Nhất (Số Hộ)",
                "subtitle": "Bấm vào từng Dân tộc để xem phương án vốn • Định mức 65 triệu VNĐ/hộ",
                "categories": cats[::-1],
                "series_main": vals[::-1],
                "drill_field": "ethnic",
                "unit": " hộ"
            }


def compute_benchmarks(period: str, district: Optional[str], commune: Optional[str], ethnic: Optional[str]) -> tuple:
    prov_defaults = {
        "KY_2019": {"ngheo": 29.10, "hoxi": 58.40, "internet": 61.20, "cmkt": 91.71},
        "KY_2024": {"ngheo": 20.63, "hoxi": 72.30, "internet": 83.50, "cmkt": 87.36},
        "KY_2026": {"ngheo": 18.54, "hoxi": 76.85, "internet": 89.40, "cmkt": 82.46},
    }
    p_avg = prov_defaults.get(period, prov_defaults["KY_2026"])

    actual_ngheo = p_avg["ngheo"]
    actual_hoxi = p_avg["hoxi"]
    actual_internet = p_avg["internet"]
    actual_cmkt = p_avg["cmkt"]
    scope_label = f"Toàn tỉnh Đắk Lắk ({period})"

    try:
        if commune:
            df_c = execute_query(
                f"SELECT ty_le_ngheo_pct FROM v_xa_biendong_ngheo_da_ky WHERE ten_xa ILIKE '{commune.replace(chr(39), chr(39)*2)}' AND ma_ky = '{period}' LIMIT 1"
            )
            if not df_c.empty:
                actual_ngheo = float(df_c["ty_le_ngheo_pct"].values[0])
            scope_label = f"{commune} ({district or 'Đắk Lắk'})"

        if district:
            df_d = execute_query(
                f"SELECT ty_le_ho_xi_hvs_bq_pct, ty_le_internet_huyen_pct FROM v_huyen_vesinh_chuyendoiso_da_ky WHERE ten_huyen ILIKE '{district.replace(chr(39), chr(39)*2)}' AND ma_ky = '{period}' LIMIT 1"
            )
            if not df_d.empty:
                actual_hoxi = float(df_d["ty_le_ho_xi_hvs_bq_pct"].values[0])
                actual_internet = float(df_d["ty_le_internet_huyen_pct"].values[0])
            if not commune:
                df_dp = execute_query(
                    f"SELECT AVG(ty_le_ngheo_pct) AS avg_ngheo FROM v_xa_biendong_ngheo_da_ky WHERE ten_huyen ILIKE '{district.replace(chr(39), chr(39)*2)}' AND ma_ky = '{period}'"
                )
                if not df_dp.empty and df_dp["avg_ngheo"].values[0] is not None:
                    actual_ngheo = float(df_dp["avg_ngheo"].values[0])
                scope_label = f"{district} ({period})"

        if ethnic:
            df_e = execute_query(
                f"SELECT ty_le_khong_cmkt_pct FROM v_dantoc_chuyen_dich_da_ky WHERE ten_dantoc ILIKE '{ethnic.replace(chr(39), chr(39)*2)}' AND ma_ky = '{period}' LIMIT 1"
            )
            if not df_e.empty:
                actual_cmkt = float(df_e["ty_le_khong_cmkt_pct"].values[0])
            scope_label = f"Dân tộc {ethnic} ({period})"
    except Exception:
        pass

    benchmarks = [
        {
            "label": "Tỷ lệ Hộ nghèo",
            "actual": round(actual_ngheo, 2),
            "provincial_avg": p_avg["ngheo"],
            "target": 15.0,
            "unit": "%",
            "direction": "lower_is_better",
            "legal_ref": "Chuẩn <= 15%"
        },
        {
            "label": "Hố xí Hợp vệ sinh",
            "actual": round(actual_hoxi, 2),
            "provincial_avg": p_avg["hoxi"],
            "target": 70.0,
            "unit": "%",
            "direction": "higher_is_better",
            "legal_ref": "TC17 NTM >= 70%"
        },
        {
            "label": "Hạ tầng Internet",
            "actual": round(actual_internet, 2),
            "provincial_avg": p_avg["internet"],
            "target": 80.0,
            "unit": "%",
            "direction": "higher_is_better",
            "legal_ref": "Đề án 06 >= 80%"
        },
        {
            "label": "Chưa qua Đào tạo nghề",
            "actual": round(actual_cmkt, 2),
            "provincial_avg": p_avg["cmkt"],
            "target": 75.0,
            "unit": "%",
            "direction": "lower_is_better",
            "legal_ref": "MTQG 1719 <= 75%"
        },
    ]
    return benchmarks, scope_label


def compute_scoped_kpis(period: str, district: Optional[str], commune: Optional[str], ethnic: Optional[str]) -> Dict[str, Any]:
    """
    Tính toán 5 chỉ số KPI và khối lượng đối tượng mô phỏng What-If linh hoạt (Scoped KPIs)
    theo đúng Địa bàn (Huyện / Xã) hoặc Dân tộc đang chọn.
    """
    macro_defaults = {
        "KY_2019": {
            "scope_tag": "Toàn tỉnh (15 Huyện • 146 Xã)",
            "tong_ho_dtts": 149480,
            "delta_ho_text": "Kỳ gốc 2019",
            "ty_le_ngheo_bq": 29.10,
            "so_ho_ngheo": 43500,
            "delta_ngheo_text": "Kỳ gốc",
            "so_ho_nha_tam": 14780,
            "delta_nha_tam_text": "Kỳ gốc",
            "so_ho_khat_von": 38018,
            "delta_khat_von_text": "Kỳ gốc",
            "ty_le_khong_cmkt": 91.71,
            "so_ld_chua_dt": 345200,
            "so_ca_sinh_tai_nha": 1409,
            "tong_ngan_sach_ty": 4227.08,
            "delta_ngan_sach_text": "GĐ 2016–2020"
        },
        "KY_2024": {
            "scope_tag": "Toàn tỉnh (15 Huyện • 146 Xã)",
            "tong_ho_dtts": 160363,
            "delta_ho_text": "+10,883 hộ",
            "ty_le_ngheo_bq": 20.63,
            "so_ho_ngheo": 33080,
            "delta_ngheo_text": "-8.47 pp",
            "so_ho_nha_tam": 10095,
            "delta_nha_tam_text": "-4,685 căn",
            "so_ho_khat_von": 32224,
            "delta_khat_von_text": "-5,794 hộ",
            "ty_le_khong_cmkt": 87.36,
            "so_ld_chua_dt": 348020,
            "so_ca_sinh_tai_nha": 1023,
            "tong_ngan_sach_ty": 4769.94,
            "delta_ngan_sach_text": "+542.86 tỷ"
        },
        "KY_2026": {
            "scope_tag": "Toàn tỉnh (15 Huyện • 146 Xã)",
            "tong_ho_dtts": 163912,
            "delta_ho_text": "+3,549 hộ",
            "ty_le_ngheo_bq": 18.54,
            "so_ho_ngheo": 28677,
            "delta_ngheo_text": "-2.09 pp",
            "so_ho_nha_tam": 6378,
            "delta_nha_tam_text": "-3,717 căn",
            "so_ho_khat_von": 25570,
            "delta_khat_von_text": "-6,654 hộ",
            "ty_le_khong_cmkt": 82.46,
            "so_ld_chua_dt": 336708,
            "so_ca_sinh_tai_nha": 671,
            "tong_ngan_sach_ty": 5119.65,
            "delta_ngan_sach_text": "+349.71 tỷ"
        }
    }

    base = dict(macro_defaults.get(period, macro_defaults["KY_2026"]))
    if not district and not commune and not ethnic:
        return base

    rates = (
        {"housing": 90.0, "credit": 65.0, "labor": 6.0, "poverty": 30.0}
        if period == "KY_2026"
        else (
            {"housing": 80.0, "credit": 50.0, "labor": 4.5, "poverty": 25.0}
            if period == "KY_2024"
            else {"housing": 60.0, "credit": 40.0, "labor": 3.5, "poverty": 15.0}
        )
    )

    try:
        # Trường hợp 1: Lọc theo Dân tộc
        if ethnic:
            safe_eth = ethnic.replace("'", "''")
            df_e = execute_query(
                f"""
                SELECT tong_ho_co_nha, so_ho_nha_tam_don_so, chenh_lech_nha_tam,
                       so_ho_khat_von, chenh_lech_ho_khat_von,
                       lao_dong_khong_cmkt, ty_le_khong_cmkt_pct, bien_dong_khong_cmkt_pct
                FROM v_dantoc_chuyen_dich_da_ky
                WHERE ten_dantoc ILIKE '{safe_eth}' AND ma_ky = '{period}'
                LIMIT 1
                """
            )
            if not df_e.empty:
                r = df_e.iloc[0]
                ho_dt = int(float(r.get("tong_ho_co_nha", 0) or 0))
                nha_tam = int(float(r.get("so_ho_nha_tam_don_so", 0) or 0))
                diff_nha = int(float(r.get("chenh_lech_nha_tam", 0) or 0))
                khat_von = int(float(r.get("so_ho_khat_von", 0) or 0))
                diff_von = int(float(r.get("chenh_lech_ho_khat_von", 0) or 0))
                ld_chua_dt = int(float(r.get("lao_dong_khong_cmkt", 0) or 0))
                ty_le_cmkt = round(float(r.get("ty_le_khong_cmkt_pct", 0) or 0), 2)

                share = max(0.0001, ho_dt / float(base["tong_ho_dtts"]))
                est_ho_ngheo = int(round(base["so_ho_ngheo"] * share))
                est_birth = int(round(base["so_ca_sinh_tai_nha"] * share))

                tot_ty = (
                    nha_tam * rates["housing"]
                    + khat_von * rates["credit"]
                    + ld_chua_dt * rates["labor"]
                    + est_ho_ngheo * rates["poverty"]
                    + est_birth * 4.5
                ) / 1000.0

                return {
                    "scope_tag": f"Dân tộc {ethnic}",
                    "tong_ho_dtts": ho_dt,
                    "delta_ho_text": f"Dân tộc {ethnic}",
                    "ty_le_ngheo_bq": base["ty_le_ngheo_bq"],
                    "so_ho_ngheo": est_ho_ngheo,
                    "delta_ngheo_text": f"Ước {est_ho_ngheo:,} hộ",
                    "so_ho_nha_tam": nha_tam,
                    "delta_nha_tam_text": f"{diff_nha:+,} căn",
                    "so_ho_khat_von": khat_von,
                    "delta_khat_von_text": f"{diff_von:+,} hộ",
                    "ty_le_khong_cmkt": ty_le_cmkt,
                    "so_ld_chua_dt": ld_chua_dt,
                    "so_ca_sinh_tai_nha": est_birth,
                    "tong_ngan_sach_ty": round(tot_ty, 2),
                    "delta_ngan_sach_text": f"Dự toán {ethnic}"
                }

        # Trường hợp 2: Lọc theo Xã hoặc Huyện
        where_clause = f"ma_ky = '{period}'"
        label_scope = ""
        if commune:
            safe_xa = commune.replace("'", "''")
            where_clause += f" AND ten_xa ILIKE '{safe_xa}'"
            label_scope = commune
        elif district:
            safe_huyen = district.replace("'", "''")
            where_clause += f" AND ten_huyen ILIKE '{safe_huyen}'"
            label_scope = district

        df_geo = execute_query(
            f"""
            SELECT COUNT(*) AS so_xa,
                   SUM(tong_ho_dtts) AS sum_ho,
                   SUM(so_ho_ngheo) AS sum_ngheo,
                   AVG(ty_le_ngheo_pct) AS avg_ty_le_ngheo,
                   AVG(bien_dong_ty_le_ngheo_pct) AS avg_delta_ngheo
            FROM v_xa_biendong_ngheo_da_ky
            WHERE {where_clause}
            """
        )
        if not df_geo.empty and df_geo.iloc[0]["sum_ho"] is not None:
            rg = df_geo.iloc[0]
            sum_ho = int(float(rg["sum_ho"] or 0))
            sum_ngheo = int(float(rg["sum_ngheo"] or 0))
            avg_ngheo = round(float(rg["avg_ty_le_ngheo"] or 0), 2)
            avg_delta = round(float(rg["avg_delta_ngheo"] or 0), 2)
            so_xa = int(float(rg["so_xa"] or 1))

            share = max(0.0001, sum_ho / float(base["tong_ho_dtts"]))
            est_nha_tam = int(round(base["so_ho_nha_tam"] * share))
            est_khat_von = int(round(base["so_ho_khat_von"] * share))
            est_ld = int(round(base["so_ld_chua_dt"] * share))
            est_birth = int(round(base["so_ca_sinh_tai_nha"] * share))

            tot_ty = (
                est_nha_tam * rates["housing"]
                + est_khat_von * rates["credit"]
                + est_ld * rates["labor"]
                + sum_ngheo * rates["poverty"]
                + est_birth * 4.5
            ) / 1000.0

            return {
                "scope_tag": f"{label_scope} ({so_xa} xã)",
                "tong_ho_dtts": sum_ho,
                "delta_ho_text": f"{so_xa} xã thuộc địa bàn",
                "ty_le_ngheo_bq": avg_ngheo,
                "so_ho_ngheo": sum_ngheo,
                "delta_ngheo_text": f"{avg_delta:+.2f} pp",
                "so_ho_nha_tam": est_nha_tam,
                "delta_nha_tam_text": f"Phân bổ ~{share*100:.1f}%",
                "so_ho_khat_von": est_khat_von,
                "delta_khat_von_text": f"Phân bổ ~{share*100:.1f}%",
                "ty_le_khong_cmkt": base["ty_le_khong_cmkt"],
                "so_ld_chua_dt": est_ld,
                "so_ca_sinh_tai_nha": est_birth,
                "tong_ngan_sach_ty": round(tot_ty, 2),
                "delta_ngan_sach_text": f"Vốn {label_scope}"
            }
    except Exception:
        pass

    return base


@app.route("/favicon.ico")
def favicon():
    svg_icon = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
        "<defs>"
        "<linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>"
        "<stop offset='0%' stop-color='#FB923C'/>"
        "<stop offset='100%' stop-color='#EA580C'/>"
        "</linearGradient>"
        "</defs>"
        "<rect width='32' height='32' rx='8' fill='url(#bg)'/>"
        "<text x='16' y='22' font-family='system-ui, -apple-system, sans-serif' "
        "font-size='15' font-weight='800' fill='#FFFFFF' text-anchor='middle'>ĐL</text>"
        "</svg>"
    )
    return Response(svg_icon, mimetype="image/svg+xml")


@app.route("/")
def index():
    return render_template("workbench.html")


@app.route("/api/init", methods=["GET"])
def api_init():
    health = test_connection()

    df_communes = execute_query(
        "SELECT DISTINCT ma_xa, ten_xa, ten_huyen FROM dim_diaban ORDER BY ten_huyen, ten_xa"
    )
    districts = sorted(df_communes["ten_huyen"].unique().tolist())

    df_ethnics = execute_query(
        "SELECT DISTINCT ten_dantoc, nhom_nguon_goc, la_dtts_it_nguoi FROM dim_dantoc ORDER BY la_dtts_it_nguoi DESC, ten_dantoc ASC"
    )

    macro_kpis = {
        "KY_2019": {
            "tong_ho_dtts": 149480,
            "delta_ho_text": "Kỳ gốc 2019",
            "ty_le_ngheo_bq": 29.10,
            "so_ho_ngheo": 43500,
            "delta_ngheo_text": "Kỳ gốc",
            "so_ho_nha_tam": 14780,
            "delta_nha_tam_text": "Kỳ gốc",
            "so_ho_khat_von": 38018,
            "delta_khat_von_text": "Kỳ gốc",
            "ty_le_khong_cmkt": 91.71,
            "so_ld_chua_dt": 345200,
            "so_ca_sinh_tai_nha": 1409,
            "tong_ngan_sach_ty": 4227.08,
            "delta_ngan_sach_text": "GĐ 2016–2020"
        },
        "KY_2024": {
            "tong_ho_dtts": 160363,
            "delta_ho_text": "+10,883 hộ",
            "ty_le_ngheo_bq": 20.63,
            "so_ho_ngheo": 33080,
            "delta_ngheo_text": "-8.47 pp",
            "so_ho_nha_tam": 10095,
            "delta_nha_tam_text": "-4,685 căn",
            "so_ho_khat_von": 32224,
            "delta_khat_von_text": "-5,794 hộ",
            "ty_le_khong_cmkt": 87.36,
            "so_ld_chua_dt": 348020,
            "so_ca_sinh_tai_nha": 1023,
            "tong_ngan_sach_ty": 4769.94,
            "delta_ngan_sach_text": "+542.86 tỷ"
        },
        "KY_2026": {
            "tong_ho_dtts": 163912,
            "delta_ho_text": "+3,549 hộ",
            "ty_le_ngheo_bq": 18.54,
            "so_ho_ngheo": 28677,
            "delta_ngheo_text": "-2.09 pp",
            "so_ho_nha_tam": 6378,
            "delta_nha_tam_text": "-3,717 căn",
            "so_ho_khat_von": 25570,
            "delta_khat_von_text": "-6,654 hộ",
            "ty_le_khong_cmkt": 82.46,
            "so_ld_chua_dt": 336708,
            "so_ca_sinh_tai_nha": 671,
            "tong_ngan_sach_ty": 5119.65,
            "delta_ngan_sach_text": "+349.71 tỷ"
        }
    }

    return jsonify({
        "health": health,
        "districts": districts,
        "communes": df_to_clean_records(df_communes),
        "ethnics": df_to_clean_records(df_ethnics),
        "macro_kpis": macro_kpis,
        "column_labels": COLUMN_LABELS
    })


@app.route("/api/investigate", methods=["POST"])
def api_investigate():
    start_t = time.perf_counter()
    body = request.get_json(force=True) or {}

    period = body.get("period", "KY_2026")
    topic = body.get("topic", "POLICY_BUDGET")
    district = body.get("district") or None
    commune = body.get("commune") or None
    ethnic = body.get("ethnic") or None
    question = (body.get("question") or "").strip()

    # =========================================================================
    # ĐỘNG CƠ PHÂN TÍCH & THAM MƯU DỮ LIỆU CỤC BỘ (LOCAL-FIRST DETERMINISTIC ENGINE)
    # Vận hành 100% trên PostgreSQL localhost:5432, không phụ thuộc Cloud API Key,
    # Không giới hạn lượt gọi, loại bỏ hoàn toàn văn mẫu cứng và bẫy if-else chắp vá.
    # =========================================================================
    if question:
        try:
            from policy_assistant.engine.local_analytics_engine import get_local_analytics_engine
            from policy_assistant.engine.semantic_analyst import build_smart_echart_payload
            local_engine = get_local_analytics_engine()
            payload = local_engine.process_query(question, override_period=period)
            if payload and payload.get("status") == "SUCCESS":
                benchmarks, scope_label = compute_benchmarks(period, district, commune, ethnic)
                scoped_kpis = compute_scoped_kpis(period, district, commune, ethnic)
                brief_dummy = {"fair_cards": payload.get("fair_cards", {})}
                
                df_temp = pd.DataFrame(payload.get("records", []))
                echart_data = build_smart_echart_payload(df_temp, brief_dummy)
                
                payload["benchmarks"] = benchmarks
                payload["scoped_kpis"] = scoped_kpis
                payload["scope_label"] = scope_label or "Toàn tỉnh Đắk Lắk"
                payload["echart"] = echart_data
                payload["latency_ms"] = round((time.perf_counter() - start_t) * 1000.0, 2)
                return jsonify(payload)
        except Exception as e:
            app.logger.error(f"Lỗi khi xử lý qua Local Analytics Engine: {e}")

    # =========================================================================
    # NHÁNH 2: BỘ ĐỊNH TUYẾN KHI CHỌN TRỰC TIẾP TRÊN DROPDOWN / BỘ LỌC
    # =========================================================================
    if question:
        intent = route_policy_intent(question)
        # Nếu câu hỏi không chỉ định năm cụ thể (2019, 2024, 2026) thì mới áp dụng chu kỳ từ bộ lọc
        q_low = question.lower()
        has_explicit_year = any(y in q_low for y in ["2019", "2024", "2026", "2030"])
        if not has_explicit_year and period in ("KY_2019", "KY_2024", "KY_2026"):
            intent.entities.ky_baocao = period
    else:
        topic_descriptions = {
            "POLICY_BUDGET": "Dự toán Ngân sách Đầu tư công & Phân bổ Nguồn lực (QĐ 1719 & NĐ 28)",
            "POVERTY_COMMUNE": "Phân hóa Nghèo Đa chiều & Cảnh báo Tái nghèo Cấp xã",
            "HOUSING_POVERTY": "Tiến độ Xóa Nhà tạm, Dột nát (Tiêu chuẩn 3 cứng - Dự án 1)",
            "SANITATION_DIGITAL": "Tiêu chí 17 NTM (Hố xí HVS) & Hạ tầng Chuyển đổi số Đề án 06",
            "CREDIT_LAND": "Khoảng trống Tín dụng Ưu đãi (NĐ 28) & Tư liệu Đất sản xuất",
            "LABOR_EDUCATION": "Chất lượng Vốn nhân lực (Dự án 5) & Khoảng cách Giáo dục Giới",
            "VULNERABILITY_HEALTH": "Giám sát Điểm nóng An ninh (Ma túy/HIV) & Y tế Sinh sản (Dự án 7)"
        }
        # Phương án 2: Giữ nguyên Chuyên đề 1 (POLICY_BUDGET) khi lọc Huyện/Xã/Dân tộc để vẽ 5 cột Ngân sách theo đúng phạm vi đó.
        # Chỉ tự động chuyển khi người dùng đang đứng ở Chuyên đề thuần Dân tộc (3, 5, 6) mà lại lọc Huyện/Xã, hoặc ngược lại.
        if (district or commune) and not ethnic and topic in ("HOUSING_POVERTY", "CREDIT_LAND", "LABOR_EDUCATION"):
            topic = "POVERTY_COMMUNE"
        elif ethnic and not (district or commune) and topic in ("POVERTY_COMMUNE", "SANITATION_DIGITAL"):
            topic = "HOUSING_POVERTY"

        # Chỉ bật so_sanh_da_ky (3 chu kỳ) khi đã chọn tới đơn vị hạt nhân của View đó:
        # - POLICY_BUDGET: luôn hiển thị 5 hạng mục ngân sách của kỳ đang chọn
        # - POVERTY_COMMUNE: chỉ khi đã chọn cụ thể 1 Xã (nếu mới chọn Huyện thì vẫn xếp hạng các xã trong huyện ở kỳ hiện tại)
        # - SANITATION_DIGITAL: khi đã chọn 1 Huyện
        # - Các chuyên đề Dân tộc: khi đã chọn 1 Dân tộc
        if topic == "POLICY_BUDGET":
            is_multi_period = False
        elif topic == "POVERTY_COMMUNE":
            is_multi_period = bool(commune)
        elif topic == "SANITATION_DIGITAL":
            is_multi_period = bool(district)
        elif topic in ("HOUSING_POVERTY", "CREDIT_LAND", "LABOR_EDUCATION"):
            is_multi_period = bool(ethnic)
        else:
            is_multi_period = bool(commune or ethnic)

        entities = ExtractedEntities(
            ky_baocao=period,
            so_sanh_da_ky=is_multi_period,
            huyen=district,
            xa=commune,
            dantoc=ethnic,
            limit=20 if district else 15,
            sort_order="ASC" if topic == "SANITATION_DIGITAL" else "DESC"
        )
        intent = PolicyIntent(
            intent_code=topic,
            intent_description=topic_descriptions.get(topic, "Phân tích Kinh tế - Xã hội"),
            target_view_or_table="",
            entities=entities
        )

    raw_sql = build_policy_sql(intent)
    is_safe, err_msg, sanitized_sql = validate_and_sanitize_sql(raw_sql, max_limit=500)
    if not is_safe:
        return jsonify({"status": "ERROR", "error_message": err_msg}), 400

    df = execute_query(sanitized_sql)
    scoped_kpis = compute_scoped_kpis(
        intent.entities.ky_baocao,
        intent.entities.huyen,
        intent.entities.xa,
        intent.entities.dantoc
    )

    # Nếu đang ở Chuyên đề 1 (POLICY_BUDGET) và có lọc theo Huyện / Xã / Dân tộc:
    # Cập nhật 5 dòng dự toán trong df theo đúng quy mô đối tượng của phạm vi đó
    if intent.intent_code == "POLICY_BUDGET" and (intent.entities.huyen or intent.entities.xa or intent.entities.dantoc) and df is not None and not df.empty:
        df = df.copy()
        qty_map = {
            "TY_LE_CHUA_DAO_TAO_CMKT": scoped_kpis.get("so_ld_chua_dt", 0),
            "KHOANG_TRONG_TIN_DUNG": scoped_kpis.get("so_ho_khat_von", 0),
            "TY_LE_HO_NGHEO": scoped_kpis.get("so_ho_ngheo", 0),
            "TY_LE_NHA_TAM": scoped_kpis.get("so_ho_nha_tam", 0),
            "CA_SINH_TAI_NHA": scoped_kpis.get("so_ca_sinh_tai_nha", 0),
        }
        for idx, row in df.iterrows():
            m_code = str(row.get("ma_chitieu", ""))
            if m_code in qty_map:
                q_val = float(qty_map[m_code])
                u_price = float(row.get("don_gia_trieu_vnd", 0) or 0)
                new_budget = round((q_val * u_price) / 1000.0, 2)
                df.at[idx, "so_luong_doi_tuong_can_ho_tro"] = int(q_val)
                df.at[idx, "tong_kinh_phi_can_phan_bo_ty_vnd"] = new_budget
                df.at[idx, "bien_dong_kinh_phi_ty_vnd"] = round(new_budget * 0.08, 2)
        df = df.sort_values(by="tong_kinh_phi_can_phan_bo_ty_vnd", ascending=False).reset_index(drop=True)

    report_md = format_fair_policy_brief(intent, df)
    fair_cards = extract_structured_fair_cards(intent, df)
    qa_response = build_natural_qa_response(question, intent, df, scoped_kpis, fair_cards)
    echart_data = build_echart_payload(intent, df)
    benchmarks, scope_label = compute_benchmarks(
        intent.entities.ky_baocao,
        intent.entities.huyen,
        intent.entities.xa,
        intent.entities.dantoc
    )

    cols = list(df.columns) if df is not None else []
    display_cols = [COLUMN_LABELS.get(c, c) for c in cols]

    latency_ms = round((time.perf_counter() - start_t) * 1000.0, 2)

    return jsonify({
        "status": "SUCCESS",
        "intent_code": intent.intent_code,
        "intent_description": intent.intent_description,
        "entities": {
            "ky_baocao": intent.entities.ky_baocao,
            "huyen": intent.entities.huyen,
            "xa": intent.entities.xa,
            "dantoc": intent.entities.dantoc,
        },
        "sql_query": sanitized_sql,
        "columns": cols,
        "display_columns": display_cols,
        "records": df_to_clean_records(df),
        "report_markdown": report_md,
        "fair_cards": fair_cards,
        "qa_response": qa_response,
        "echart": echart_data,
        "benchmarks": benchmarks,
        "scoped_kpis": scoped_kpis,
        "scope_label": scope_label,
        "latency_ms": latency_ms
    })


if __name__ == "__main__":
    cert_file = os.path.join(BASE_DIR, "certs", "cert.pem")
    key_file = os.path.join(BASE_DIR, "certs", "key.pem")
    use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)

    default_port = "443" if use_ssl else "80"
    port = int(os.getenv("PORT", default_port))

    scheme = "https" if use_ssl else "http"
    default_proto_port = 443 if use_ssl else 80

    if port == default_proto_port:
        url = f"{scheme}://dtts-daklak.com"
    else:
        url = f"{scheme}://dtts-daklak.com:{port}"

    try:
        print("=" * 72)
        print("HE THONG THAM DINH CHINH SACH & DIEU HANH NGAN SACH MTQG 1719 - DAK LAK")
        print(f"URL: {url}")
        if use_ssl:
            print("Che do: HTTPS (SSL Bao mat 100% - Co o khoa an toan)")
        print("=" * 72)
    except Exception:
        pass

    ssl_context = (cert_file, key_file) if use_ssl else None
    app.run(host="0.0.0.0", port=port, ssl_context=ssl_context, debug=False)
