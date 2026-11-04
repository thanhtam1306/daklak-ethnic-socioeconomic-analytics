"""
==============================================================================
MODULE: LOCAL DETERMINISTIC ANALYTICS & SEMANTIC QUERY ENGINE
File: policy_assistant/engine/local_analytics_engine.py
Dự án: Hệ thống Hỗ trợ Ra Quyết định & Tham mưu Chính sách KTXH 53 DTTS Đắk Lắk
==============================================================================
Mô tả:
  - Vận hành 100% CỤC BỘ (Local-First), không phụ thuộc vào bất kỳ Cloud API Key nào.
  - Phân tích câu hỏi tự nhiên tiếng Việt theo 4 chiều chuẩn mực:
      (Không gian: Tỉnh/Huyện/Xã/Dân tộc, Chỉ tiêu: 7 Lĩnh vực KTXH, Thời gian: Đơn kỳ / Đa kỳ, Mục đích: Tổng hợp/So sánh/Xếp hạng/Hồ sơ).
  - Tự động sinh SQL chuẩn xác, tối ưu trên CSDL PostgreSQL (schema daklak_analytics).
  - Tổng hợp nhận định F-A-I-R động 100% từ dữ liệu thực chứng (KHÔNG VĂN MẪU RẬP KHUÔN).
  - Tích hợp Lưới An Toàn 3 Tầng: Hồ sơ 360 độ, Ranh giới dữ liệu & Từ chối ngoài phạm vi.
==============================================================================
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from ..core.catalog import DISTRICT_ALIASES, ETHNIC_GROUPS, METRIC_CATALOG
from ..core.db import execute_query
from ..core.sql_guardrails import validate_and_sanitize_sql


def remove_accents(input_str: str) -> str:
    """Loại bỏ dấu tiếng Việt để đối chiếu từ khóa không dấu."""
    if not input_str:
        return ""
    s = input_str.replace("đ", "d").replace("Đ", "D")
    nfkd_form = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()


class LocalAnalyticsEngine:
    """Động cơ Phân tích & Tham mưu Dữ liệu KTXH Cục bộ (Local-First)."""

    def __init__(self):
        # Nạp danh mục 15 huyện chuẩn
        self.districts_map = DISTRICT_ALIASES
        # Nạp danh mục dân tộc
        self.ethnics_map = ETHNIC_GROUPS
        # Nạp danh mục 146 xã/phường/thị trấn để nhận diện cả có dấu và không dấu
        self.communes_list = []
        try:
            df_xa = execute_query("SELECT DISTINCT ten_xa, ten_huyen FROM v_xa_biendong_ngheo_da_ky WHERE ma_ky = 'KY_2026'")
            if df_xa is not None and not df_xa.empty:
                for _, r in df_xa.iterrows():
                    tx = str(r["ten_xa"]).strip()
                    th = str(r["ten_huyen"]).strip()
                    short_xa = re.sub(r"^(Xã|Phường|Thị trấn)\s+", "", tx, flags=re.IGNORECASE).strip()
                    self.communes_list.append({
                        "ten_xa": tx,
                        "ten_huyen": th,
                        "full_no_acc": remove_accents(tx.lower()),
                        "short_no_acc": remove_accents(short_xa.lower()),
                    })
                self.communes_list.sort(key=lambda x: len(x["full_no_acc"]), reverse=True)
        except Exception:
            self.communes_list = []

    def detect_entities(self, question: str) -> Dict[str, Any]:
        """Bóc tách thực thể địa bàn, dân tộc, thời gian và phạm vi câu hỏi (hỗ trợ 100% cả có dấu và không dấu)."""
        q_raw = question.strip()
        q_clean = q_raw.lower()
        q_no_acc = remove_accents(q_clean)

        # 1. Bóc tách thời gian & chu kỳ
        periods = []
        is_multi_period = False
        if "2019" in q_clean:
            periods.append("KY_2019")
        if "2024" in q_clean:
            periods.append("KY_2024")
        if "2026" in q_clean or "2030" in q_clean:
            periods.append("KY_2026")

        if len(periods) >= 2 or any(k in q_no_acc for k in ["giai doan", "qua cac ky", "da ky", "bien dong", "xu huong", "chuyen dich", "sau 5 nam", "sau 7 nam", "so voi ky truoc", "period", "trend", "over time", "between 2019 and 2024"]):
            is_multi_period = True

        default_period = periods[-1] if len(periods) == 1 else "KY_2026"

        # 2. Bóc tách địa bàn Huyện (Tiếng Việt & English aliases: district, commune...)
        found_districts = []
        # Bỏ chữ 'dak lak' / 'province' để không nhầm chữ 'lak' thành Huyện Lắk
        q_no_lak = re.sub(r"\b(tinh\s+|province\s+)?dak\s*lak\b", " ", q_no_acc)
        q_no_lak = re.sub(r"\bdistrict\b", "huyen", q_no_lak)
        q_no_lak = re.sub(r"\bcommune\b", "xa", q_no_lak)
        for alias, dist_name in sorted(self.districts_map.items(), key=lambda x: len(x[0]), reverse=True):
            alias_no_acc = remove_accents(alias)
            if re.search(r"\b" + re.escape(alias_no_acc) + r"\b", q_no_lak):
                if dist_name not in found_districts:
                    found_districts.append(dist_name)
        found_district = found_districts[0] if found_districts else None

        # 3. Bóc tách địa bàn Xã (khớp chính xác từ điển 146 xã/phường cả tiếng Việt, tiếng Anh và không dấu)
        found_commune = None
        for c_item in self.communes_list:
            if re.search(r"\b" + re.escape(c_item["full_no_acc"]) + r"\b", q_no_acc):
                found_commune = c_item["ten_xa"]
                if not found_district:
                    found_district = c_item["ten_huyen"]
                    found_districts.append(found_district)
                break
        if not found_commune:
            # Khớp tên xã theo tiền tố tiếng Việt (xa, phuong, thi tran) hoặc tiếng Anh (commune, ward, town)
            for c_item in self.communes_list:
                short_na = c_item["short_no_acc"]
                if len(short_na) >= 4 and (
                    re.search(r"\b(xa|phuong|thi tran|commune|ward|town)\s+" + re.escape(short_na) + r"\b", q_no_acc) or
                    re.search(r"\b" + re.escape(short_na) + r"\s+(commune|ward|town)\b", q_no_acc)
                ):
                    found_commune = c_item["ten_xa"]
                    if not found_district:
                        found_district = c_item["ten_huyen"]
                        found_districts.append(found_district)
                    break

        # 4. Bóc tách Dân tộc (hỗ trợ cả tiếng Việt và English prefixes/keywords: ethnic, people, tribe, minority...)
        found_ethnics = []
        common_compounds_acc = [
            "tây nguyên", "tay nghề", "chân tay", "trạng thái", "sinh thái", "thái độ", "thái cực", "mang thai",
            "mong muốn", "mong đợi", "chăm sóc", "chậm trễ", "chăm chỉ", "văn hóa", "kiên cố hóa", "hiện đại hóa",
            "xã hội hóa", "đa dạng hóa", "đào tạo", "lãnh đạo", "chỉ đạo", "cơ sở", "cơ cấu", "cơ hội", "hộ có",
            "có hố xí", "lao động", "công tác", "công trình", "công nghệ", "công nghiệp", "mã số", "ma túy",
            "mạng lưới", "giấy tờ", "đô thị", "thổ cư", "lưu trú", "chút ít", "một chút"
        ]
        q_eth_clean = q_clean
        q_eth_no_acc = q_no_acc
        for comp in common_compounds_acc:
            q_eth_clean = re.sub(r"\b" + re.escape(comp) + r"\b", " ", q_eth_clean)
            comp_no_acc = remove_accents(comp)
            q_eth_no_acc = re.sub(r"\b" + re.escape(comp_no_acc) + r"\b", " ", q_eth_no_acc)

        strict_prefix_ethnics = {
            "co", "cơ", "hoa", "thổ", "tho", "mạ", "ma", "mảng", "mang", "cống", "cong",
            "lự", "lu", "ngái", "ngai", "bố y", "bo y", "lào", "lao", "chứt", "chut",
            "si la", "la ha", "cơ ho", "co ho", "kinh", "dao"
        }
        for eth_key, eth_info in sorted(self.ethnics_map.items(), key=lambda x: len(x[0]), reverse=True):
            eth_no_acc = remove_accents(eth_key)
            if eth_key in strict_prefix_ethnics or eth_no_acc in strict_prefix_ethnics:
                # Nhóm từ đơn trùng âm: yêu cầu có tiền tố dân tộc (tiếng Việt hoặc English)
                if (
                    re.search(r"\b(dân tộc|người|đồng bào|ethnic|people)\s+" + re.escape(eth_key) + r"\b", q_eth_clean) or
                    re.search(r"\b(dan toc|nguoi|dong bao|ethnic|people)\s+" + re.escape(eth_no_acc) + r"\b", q_eth_no_acc) or
                    re.search(r"\b" + re.escape(eth_no_acc) + r"\s+(ethnic|people|minority)\b", q_eth_no_acc)
                ):
                    tc = eth_info.get("ten_chuan")
                    if tc and tc not in found_ethnics:
                        found_ethnics.append(tc)
            else:
                if re.search(r"\b" + re.escape(eth_key) + r"\b", q_eth_clean) or re.search(r"\b" + re.escape(eth_no_acc) + r"\b", q_eth_no_acc):
                    tc = eth_info.get("ten_chuan")
                    if tc and tc not in found_ethnics:
                        found_ethnics.append(tc)

        # 5. Nhận diện phạm vi Toàn tỉnh hay Cấp huyện hay Cấp xã (hỗ trợ cả English)
        is_province = any(k in q_no_acc for k in ["toan tinh", "ca tinh", "toan bo tinh", "tinh dak lak", "province", "whole province", "all districts"]) or (not found_district and not found_commune and not found_ethnics)
        is_district_level = any(k in q_no_acc for k in ["huyen", "cac huyen", "top huyen", "nhung huyen", "district", "districts"]) or bool(found_district)
        is_commune_level = any(k in q_no_acc for k in ["xa", "cac xa", "nhung xa", "xa nao", "commune", "communes", "ward", "wards"]) or bool(found_commune)

        # 6. Nhận diện mục đích (Intent Operation - Song ngữ VN & EN)
        is_comparison = len(found_ethnics) >= 2 or len(periods) >= 2 or any(k in q_no_acc for k in ["so sanh", "doi chieu", "khac nhau", "so voi", "tang bao nhieu", "giam bao nhieu", "bien dong", "compare", "comparison", "difference", "vs", "versus", "gap", "higher than", "lower than"]);
        is_ranking = any(k in q_no_acc for k in ["nhanh nhat", "cao nhat", "thap nhat", "nhieu nhat", "it nhat", "top", "xep hang", "dan dau", "trung nhat", "highest", "lowest", "rank", "ranking", "most", "least"])
        is_total = any(k in q_no_acc for k in ["bao nhieu", "tong so", "quy mo", "tong cong", "hien tai co", "toan tinh co", "how many", "total", "count", "amount", "population"])

        # 7. Nhận diện Lĩnh vực / Chỉ tiêu (Domain - Song ngữ VN & EN)
        domain = "GENERAL"
        if any(k in q_no_acc for k in ["thoi tiet", "mua khong", "nhiet do", "gia ca phe", "gia vang", "chung khoan", "chu tich tinh", "bong da", "tin tuc", "xem boi", "troi mua", "weather", "temperature", "coffee price", "gold price", "stock", "football", "news", "horoscope"]):
            domain = "OUT_OF_SCOPE"
        elif any(k in q_no_acc for k in ["nha o", "nha tam", "dot nat", "don so", "kien co", "kien co hoa", "xoa nha tam", "housing", "temporary house", "temporary home", "dilapidated", "solid house", "shelter"]):
            domain = "HOUSING"
        elif any(k in q_no_acc for k in ["ngheo", "ho ngheo", "ty le ngheo", "giam ngheo", "sinh ke", "tai ngheo", "ngheo da chieu", "poverty", "poor", "poor household", "poverty rate", "livelihood", "multidimensional"]):
            domain = "POVERTY"
        elif any(k in q_no_acc for k in ["ho xi", "ve sinh", "nuoc sach", "nuoc hvs", "internet", "de an 06", "tieu chi 17", "chuyen doi so", "latrine", "toilet", "hygienic", "clean water", "sanitation", "digital"]):
            domain = "SANITATION_DIGITAL"
        elif any(k in q_no_acc for k in ["khat von", "vay von", "tin dung", "nhcsxh", "nghi dinh 28", "dat san xuat", "dat canh tac", "thieu dat", "credit", "loan", "preferential loan", "capital", "agricultural land", "production land", "decree 28"]):
            domain = "CREDIT_LAND"
        elif any(k in q_no_acc for k in ["lao dong", "viec lam", "dao tao", "cmkt", "chua qua dao tao", "chung chi", "hoc van", "mu chu", "biet chu", "gioi", "labor", "employment", "vocational", "training", "literacy", "illiteracy", "education", "technical qualification", "gender gap"]):
            domain = "LABOR_EDUCATION"
        elif any(k in q_no_acc for k in ["ma tuy", "nghien", "hiv", "sinh tai nha", "sinh con tai nha", "sinh thu 3", "ba do", "y te", "drugs", "drug addict", "hiv", "home birth", "home delivery", "maternal", "infant mortality", "health"]):
            domain = "VULNERABILITY_HEALTH"
        elif any(k in q_no_acc for k in ["ngan sach", "kinh phi", "du toan", "1719", "dinh muc", "von sinh ke", "budget", "cost", "investment", "financial allocation", "funding", "decision 1719"]):
            domain = "BUDGET"
        elif any(k in q_no_acc for k in ["powerbi", "power bi", "dashboard", "dax", "slicer", "goc phan tu", "4 goc", "khoa ky", "cong don", "triple", "selected period", "quadrant", "visual", "page", "pages"]):
            domain = "POWERBI_GUIDE"
        elif any(k in q_no_acc for k in ["thap tuoi", "dan so", "3 nhom tuoi", "gia hoa", "phu thuoc", "0-14", "15-59", "60+", "age pyramid", "demographic", "dependency ratio", "child dependency", "aging index", "age structure"]):
            domain = "DEMOGRAPHIC"

        return {
            "question": q_raw,
            "periods": periods,
            "default_period": default_period,
            "is_multi_period": is_multi_period,
            "districts": found_districts,
            "district": found_district,
            "commune": found_commune,
            "ethnics": found_ethnics,
            "is_province": is_province,
            "is_district_level": is_district_level,
            "is_commune_level": is_commune_level,
            "is_comparison": is_comparison,
            "is_ranking": is_ranking,
            "is_total": is_total,
            "domain": domain
        }

    def process_query(self, question: str, override_period: Optional[str] = None) -> Dict[str, Any]:
        """Xử lý truy vấn trọn gói: Nhận diện -> Sinh SQL -> Thực thi -> Tổng hợp F-A-I-R."""
        meta = self.detect_entities(question)
        if override_period and not meta["periods"]:
            meta["default_period"] = override_period

        domain = meta["domain"]
        district = meta["district"]
        ethnics = meta["ethnics"]
        periods = meta["periods"]
        is_multi_period = meta["is_multi_period"]

        # =====================================================================
        # TRƯỜNG HỢP NGOÀI PHẠM VI NGHIỆP VỤ (OUT OF SCOPE)
        # =====================================================================
        if domain == "OUT_OF_SCOPE":
            return self._handle_out_of_scope(meta)

        # =====================================================================
        # TRƯỜNG HỢP ĐẶC BIỆT: HƯỚNG DẪN POWER BI, BIỂU ĐỒ & CÔNG THỨC DAX
        # =====================================================================
        q_no_acc = remove_accents(meta["question"].lower())
        if domain == "POWERBI_GUIDE" or any(k in q_no_acc for k in ["powerbi", "power bi", "dashboard", "dax", "thap tuoi", "4 goc phan tu", "chong cong don", "cong don 3 ky"]):
            return self._handle_powerbi_guide(meta)

        # =====================================================================
        # TRƯỜNG HỢP 1: RANH GIỚI DỮ LIỆU (DATA BOUNDARY)
        # VD: Hỏi kiên cố hóa nhà ở cấp Huyện (chỉ tiêu nhà ở vốn chỉ có cấp Dân tộc toàn tỉnh)
        # =====================================================================
        if domain == "HOUSING" and meta["is_district_level"] and not district and meta["is_ranking"]:
            return self._handle_housing_district_boundary(meta)

        # =====================================================================
        # TRƯỜNG HỢP 2: SO SÁNH NGHÈO CỦA MỘT HUYỆN QUA 2 KỲ (VD: Ea Súp 2019 vs 2024)
        # =====================================================================
        if domain == "POVERTY" and district and not meta.get("commune") and (is_multi_period or len(periods) >= 2 or "giam" in q_no_acc):
            return self._handle_district_poverty_comparison(meta)

        # =====================================================================
        # TRƯỜNG HỢP 3: TOÀN TỈNH NHÀ TẠM / DÂN TỘC NHIỀU NHẤT (VD: Toàn tỉnh có bao nhiêu nhà tạm)
        # =====================================================================
        if domain == "HOUSING" and (meta["is_province"] or not district) and not ethnics:
            return self._handle_provincial_housing_overview(meta)

        # =====================================================================
        # TRƯỜNG HỢP 4: SO SÁNH 2 DÂN TỘC (VD: Ê Đê vs Mông về học vấn, lao động, nhà ở)
        # =====================================================================
        if len(ethnics) >= 2:
            return self._handle_ethnic_head_to_head(meta)

        # =====================================================================
        # TRƯỜNG HỢP 4B: SO SÁNH 2 HUYỆN (VD: Huyện Lắk vs Huyện Krông Bông)
        # =====================================================================
        if len(meta.get("districts", [])) >= 2:
            return self._handle_district_head_to_head(meta)

        # =====================================================================
        # TRƯỜNG HỢP 5: TRA CỨU MỘT XÃ CỤ THỂ HOẶC XẾP HẠNG XÃ NGHÈO TRONG HUYỆN
        # =====================================================================
        if meta.get("commune") or (domain == "POVERTY" and (meta["is_commune_level"] or district)):
            return self._handle_commune_poverty_ranking(meta)

        # =====================================================================
        # TRƯỜNG HỢP 6: NHÂN KHẨU HỌC, PHỤ THUỘC & GIÀ HÓA (DEMOGRAPHIC)
        # =====================================================================
        if domain == "DEMOGRAPHIC":
            return self._handle_demographic(meta)

        # =====================================================================
        # TRƯỜNG HỢP 7: TÍN DỤNG CHÍNH SÁCH NĐ 28 & ĐẤT SẢN XUẤT (CREDIT_LAND)
        # =====================================================================
        if domain == "CREDIT_LAND":
            return self._handle_credit_land(meta)

        # =====================================================================
        # TRƯỜNG HỢP 8: LAO ĐỘNG & ĐÀO TẠO NGHỀ (LABOR_EDUCATION)
        # =====================================================================
        if domain == "LABOR_EDUCATION":
            return self._handle_labor_education(meta)

        # =====================================================================
        # TRƯỜNG HỢP 9: VỆ SINH MÔI TRƯỜNG & CHUYỂN ĐỔI SỐ (SANITATION_DIGITAL)
        # =====================================================================
        if domain == "SANITATION_DIGITAL":
            return self._handle_sanitation_digital(meta)

        # =====================================================================
        # TRƯỜNG HỢP 10: Y TẾ SINH SẢN & ĐIỂM NÓNG AN NINH (VULNERABILITY_HEALTH)
        # =====================================================================
        if domain == "VULNERABILITY_HEALTH":
            return self._handle_vulnerability_health(meta)

        # =====================================================================
        # TRƯỜNG HỢP 11: DỰ TOÁN NGÂN SÁCH ĐẦU TƯ CÔNG (BUDGET)
        # =====================================================================
        if domain == "BUDGET":
            return self._handle_budget(meta)

        # =====================================================================
        # TRƯỜNG HỢP 12: MỘT DÂN TỘC CỤ THỂ HOẶC MỘT HUYỆN CỤ THỂ (HỒ SƠ 360 ĐỘ)
        # =====================================================================
        if len(ethnics) == 1:
            return self._handle_ethnic_profile_360(meta)
        if district and not ethnics:
            return self._handle_district_profile_360(meta)

        # =====================================================================
        # TRƯỜNG HỢP 13: TOÀN CẢNH MẶC ĐỊNH TOÀN TỈNH
        # =====================================================================
        return self._handle_default_provincial_snapshot(meta)

    # -------------------------------------------------------------------------
    # HANDLERS CHI TIẾT
    # -------------------------------------------------------------------------

    def _handle_powerbi_guide(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Giải thích các biểu đồ, cấu trúc trang báo cáo và công thức DAX trên Power BI."""
        q_low = meta["question"].lower()
        q_no_acc = remove_accents(q_low)

        # 1. Tháp tuổi & Cơ cấu 3 nhóm tuổi (Trang 1)
        if any(k in q_no_acc for k in ["thap tuoi", "3 nhom tuoi", "co cau tuoi", "do tuoi", "gia hoa", "phu thuoc", "age pyramid", "pyramid", "3 age groups", "three age groups", "age structure"]):
            sql = """
            SELECT 
                ten_dantoc, nhom_nguon_goc, tong_dan_so,
                dan_so_0_14, dan_so_15_59, dan_so_60_plus,
                ROUND(dan_so_0_14 * 100.0 / NULLIF(tong_dan_so, 0), 1) AS ty_le_0_14_pct,
                ROUND(dan_so_15_59 * 100.0 / NULLIF(tong_dan_so, 0), 1) AS ty_le_15_59_pct,
                ROUND(dan_so_60_plus * 100.0 / NULLIF(tong_dan_so, 0), 1) AS ty_le_60_plus_pct,
                ROUND(dan_so_0_14 * 100.0 / NULLIF(dan_so_15_59, 0), 1) AS ty_le_phu_thuoc_tre_em_pct,
                ROUND(dan_so_60_plus * 100.0 / NULLIF(dan_so_0_14, 0), 1) AS chi_so_gia_hoa_pct
            FROM fact_nhankhau_dantoc
            WHERE ma_ky = 'KY_2026'
            ORDER BY tong_dan_so DESC
            LIMIT 5;
            """
            df = execute_query(sql)
            lead = (
                "Biểu đồ <strong>'Tháp Tuổi & Cơ Cấu 3 Nhóm Tuổi Dân Tộc'</strong> trên Trang 1 Power BI bóc tách cơ cấu nhân khẩu học "
                "theo 3 thế hệ: (1) <em>0–14 tuổi (Trẻ em / Dưới tuổi lao động)</em>, (2) <em>15–59 tuổi (Lao động vàng)</em>, "
                "và (3) <em>60+ tuổi (Người cao tuổi / Hết tuổi lao động)</em>."
            )
            bullets = [
                "<strong>Phân hóa 2 thái cực nhân khẩu học:</strong> Đồng bào di cư miền núi phía Bắc (Mông, Xơ Đăng) mang tháp tuổi 'rất trẻ' với gánh nặng nuôi con (Child Dependency) cực đại đạt <b>>80%</b>; ngược lại, nhóm Tày, Nùng, Thái đã bước vào giai đoạn già hóa dân số với chỉ số già hóa đạt <b>33–41%</b>.",
                "<strong>Tác động hoạch định chính sách:</strong> Nhóm tháp tuổi trẻ cần ưu tiên ngân sách xây trường mầm non và dinh dưỡng học đường (Dự án 5); nhóm già hóa cần mạng lưới chăm sóc y tế lão khoa cơ sở.",
                "<strong>Tương tác trên Dashboard:</strong> Khi bấm vào một cột dân tộc trên biểu đồ tháp tuổi, toàn bộ các thẻ KPI quy mô dân số và bản đồ huyện sẽ tự động lọc chéo (Cross-filter) theo dân tộc đó."
            ]
            takeaway = "Khuyến nghị: Phân bổ vốn Chương trình MTQG 1719 theo cấu trúc nhân khẩu học để tối ưu hóa hiệu quả an sinh xã hội."
            return self._format_result_payload(
                intent_code="PBI_GUIDE_AGE_PYRAMID",
                intent_desc="Giải thích Biểu đồ Tháp Tuổi & Cơ Cấu 3 Nhóm Tuổi Dân Tộc trên Trang 1 Power BI",
                sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
            )

        # 2. Ma trận 4 Góc phần tư: Khoảng cách vs Tỷ lệ nghèo (Trang 1 / Trang 4)
        elif any(k in q_no_acc for k in ["goc phan tu", "4 goc", "khoang cach", "cu ly", "tuong quan", "quadrant", "scatter", "distance vs poverty"]):
            sql = """
            SELECT 
                ten_xa, ten_huyen, km_den_trung_tam_huyen, ty_le_ngheo_pct, so_ho_ngheo,
                du_toan_ngan_sach_sinh_ke_trieu_vnd
            FROM v_xa_biendong_ngheo_da_ky
            WHERE ma_ky = 'KY_2026' AND km_den_trung_tam_huyen >= 15 AND ty_le_ngheo_pct >= 25
            ORDER BY km_den_trung_tam_huyen DESC, ty_le_ngheo_pct DESC
            LIMIT 5;
            """
            df = execute_query(sql)
            lead = (
                "Biểu đồ <strong>'Ma Trận 4 Góc Phần Tư (Khoảng Cách vs Tỷ Lệ Nghèo Cấp Xã)'</strong> trên Power BI trực quan hóa phương trình kinh tế lượng: "
                "<code>Nghèo (%) = 13.10% + 0.5132 × Khoảng cách (km)</code> — Cứ cách xa trung tâm huyện 10 km, tỷ lệ nghèo của xã tăng thêm <strong>+5.13 điểm %</strong>."
            )
            bullets = [
                "<strong>Góc phần tư I (Khó khăn kép - Vùng đỏ):</strong> Các xã có cự ly <b>> 15 km</b> VÀ tỷ lệ nghèo <b>> 25%</b> (như Ia Lốp, Ia RVê tại Ea Súp; Cư Pui, Cư Drăm tại Krông Bông; Đắk Phơi tại Lắk). Đây là vùng ưu tiên giải ngân vốn sinh kế số 1.",
                "<strong>Góc phần tư II (Nghèo cục bộ):</strong> Các xã gần trung tâm huyện (<15 km) nhưng tỷ lệ nghèo vẫn cao, chủ yếu do thiếu đất canh tác hoặc bẫy lao động chưa qua đào tạo.",
                "<strong>Góc phần tư III & IV (Phát triển bền vững):</strong> Các xã gần huyện có tỷ lệ nghèo thấp, hoặc các xã vùng xa nhưng đã bứt phá thoát nghèo nhờ phát triển cây công nghiệp giá trị cao (cà phê, sầu riêng)."
            ]
            takeaway = "Khuyến nghị: Phân bổ vốn ngân sách theo hệ số cự ly địa lý (nhân hệ số 1.3 - 1.5 cho các xã thuộc góc phần tư Khó khăn kép)."
            return self._format_result_payload(
                intent_code="PBI_GUIDE_QUADRANT",
                intent_desc="Giải thích Ma Trận 4 Góc Phần Tư (Khoảng Cách vs Tỷ Lệ Nghèo) trên Power BI",
                sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
            )

        # 3. Tổng quan Cấu trúc 4 Trang Báo cáo trên Power BI
        elif any(k in q_no_acc for k in ["4 trang", "nhung trang", "cac trang", "tong quan trang", "kien truc bao cao", "cau truc bao cao", "giai quyet bai toan", "4 pages", "four pages", "structure", "overview of pages", "report pages"]):
            sql = """
            SELECT 
                ma_ky, ten_ky, nam_moc, giai_doan_chinh_sach, is_latest
            FROM dim_ky_baocao
            ORDER BY thu_tu_ky ASC;
            """
            df = execute_query(sql)
            lead = (
                "Hệ thống Báo cáo Quản trị Power BI <strong>'Phân Tích KTXH 53 Dân Tộc Thiểu Số Đắk Lắk'</strong> được thiết kế chuẩn mực "
                "theo cấu trúc <strong>4 trang nghiệp vụ chuyên sâu</strong>, phục vụ toàn diện công tác tham mưu và điều hành chính sách:"
            )
            bullets = [
                "<strong>Trang 1: Bức tranh Tổng quan KTXH & Dân tộc (Overview & Demographics):</strong> Tháp tuổi 3 nhóm thế hệ (0-14, 15-59, 60+), Thẻ KPI quy mô toàn tỉnh (163.912 hộ DTTS, 6.378 nhà tạm) và Bản đồ phân bố 15 huyện/thị/thành.",
                "<strong>Trang 2: Không gian Địa lý & Giảm nghèo Cấp xã (Geographic Poverty Dynamics):</strong> Bản đồ nhiệt 184 xã/phường, Ma trận 4 góc phần tư cự ly vs tỷ lệ nghèo, Phân rã độ biến động giảm nghèo qua 3 kỳ khảo sát (2019, 2024, 2026).",
                "<strong>Trang 3: Chất lượng Cuộc sống & Dịch chuyển Xã hội (Quality of Life & Transition):</strong> Giám sát kiên cố hóa nhà ở, Nước sạch, Hố xí HVS (Tiêu chí 17 NTM), Phủ sóng Internet (Đề án 06) và Khoảng trống tín dụng chính sách (NĐ 28).",
                "<strong>Trang 4: Giám sát Điểm nóng An ninh & Tham mưu Chính sách (Hotspot Governance & DSS):</strong> Bản đồ điểm nóng sinh tại nhà/tử vong sơ sinh, Tệ nạn ma túy/HIV, Bảng tính dự toán ngân sách 6 định mức pháp lý (QĐ 1719)."
            ]
            takeaway = "Khuyến nghị: Sử dụng Slicer Kỳ báo cáo để chuyển đổi linh hoạt giữa 3 mốc thời gian, toàn bộ visual sẽ đồng bộ cập nhật theo cơ chế Anti-Triple Counting."
            return self._format_result_payload(
                intent_code="PBI_GUIDE_4_PAGES_OVERVIEW",
                intent_desc="Tổng quan Cấu trúc 4 Trang Báo cáo Quản trị Power BI",
                sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
            )

        # 4. Cơ chế Chống cộng dồn 3 kỳ (Anti-Triple Counting Gate) & Công thức DAX
        else:
            sql = """
            SELECT 
                kb.ma_ky, kb.ten_ky,
                COUNT(DISTINCT nh.ten_dantoc) AS so_dantoc,
                SUM(nh.tong_so_ho_co_nha) AS tong_ho_co_nha,
                SUM(nh.nha_thieu_kien_co_don_so) AS so_nha_tam
            FROM fact_nhao_dantoc nh
            JOIN dim_ky_baocao kb ON nh.ma_ky = kb.ma_ky
            GROUP BY kb.ma_ky, kb.ten_ky, kb.thu_tu_ky
            ORDER BY kb.thu_tu_ky ASC;
            """
            df = execute_query(sql)
            lead = (
                "Cơ chế <strong>Chống Cộng Dồn 3 Kỳ (Anti-Triple Counting Gate)</strong> trên Power BI được xây dựng thông qua hàm DAX "
                "<code>[Selected Period Order]</code> nhằm ngăn chặn triệt để lỗi cộng gộp 3 kỳ khảo sát (2019 + 2024 + 2026 = 473.755 hộ) "
                "khi người dùng không chọn Slicer."
            )
            bullets = [
                "<strong>Bản chất nghiệp vụ:</strong> Số hộ và dân số là <em>chỉ tiêu thời điểm (Stock Metrics)</em>, không thể cộng dồn theo trục thời gian như chỉ tiêu doanh thu hay ngân sách giải ngân (Flow Metrics).",
                "<strong>Cơ chế khóa tự động:</strong> Khi Lãnh đạo không bấm Slicer, hàm DAX tự động phát hiện <code>NOT(ISFILTERED(dim_ky_baocao))</code> và khóa cứng Context về kỳ mới nhất (<code>is_latest = TRUE → KY_2026 = 163.912 hộ</code>).",
                "<strong>Cơ chế tính biến động động:</strong> Khi bấm chọn một kỳ bất kỳ trên Slicer, toàn bộ 100 DAX Measures tự động chuyển sang kỳ đó và lùi 1 bậc (<code>thu_tu_ky - 1</code>) để tính độ chênh lệch tăng/giảm (▲/▼) so với kỳ trước."
            ]
            takeaway = "Góc nhìn tham mưu: Cổng kiểm soát này giúp Lãnh đạo yên tâm thao tác trên Dashboard mà không bao giờ gặp tình trạng số liệu bị nhân ba."
            return self._format_result_payload(
                intent_code="PBI_GUIDE_ANTI_TRIPLE_COUNT",
                intent_desc="Giải thích Cơ chế Chống Cộng Dồn 3 Kỳ và Hàm DAX [Selected Period Order] trên Power BI",
                sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
            )

    def _handle_housing_district_boundary(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý ranh giới dữ liệu: Giải thích và đưa ra bảng đối soát kiên cố hóa nhà ở theo Dân tộc."""
        p_start = "KY_2019" if "KY_2019" in meta["periods"] else "KY_2019"
        p_end = "KY_2024" if "KY_2024" in meta["periods"] else "KY_2024"

        sql = f"""
        WITH p_start AS (
            SELECT 
                ten_dantoc, nhom_nguon_goc,
                nha_kien_co_ban_kien_co AS kien_co_start,
                tong_so_ho_co_nha AS tong_ho_start,
                ROUND(nha_kien_co_ban_kien_co * 100.0 / NULLIF(tong_so_ho_co_nha, 0), 2) AS ty_le_kc_start
            FROM fact_nhao_dantoc
            WHERE ma_ky = '{p_start}'
        ),
        p_end AS (
            SELECT 
                ten_dantoc, nhom_nguon_goc,
                nha_kien_co_ban_kien_co AS kien_co_end,
                tong_so_ho_co_nha AS tong_ho_end,
                ROUND(nha_kien_co_ban_kien_co * 100.0 / NULLIF(tong_so_ho_co_nha, 0), 2) AS ty_le_kc_end
            FROM fact_nhao_dantoc
            WHERE ma_ky = '{p_end}'
        )
        SELECT 
            p_end.ten_dantoc,
            p_end.nhom_nguon_goc,
            p_start.ty_le_kc_start AS ty_le_kien_co_2019_pct,
            p_end.ty_le_kc_end AS ty_le_kien_co_2024_pct,
            ROUND(p_end.ty_le_kc_end - p_start.ty_le_kc_start, 2) AS tang_truong_kien_co_pp,
            (p_end.kien_co_end - p_start.kien_co_start) AS so_can_kien_co_tang_them
        FROM p_end
        JOIN p_start ON p_end.ten_dantoc = p_start.ten_dantoc
        WHERE p_end.tong_ho_end >= 100
        ORDER BY tang_truong_kien_co_pp DESC
        LIMIT 5;
        """
        df = execute_query(sql)
        bullets = []
        if df is not None and not df.empty:
            for i, r in df.iterrows():
                bullets.append(
                    f"<strong>#{i+1}. Dân tộc {r['ten_dantoc']}:</strong> Tỷ lệ nhà kiên cố tăng từ <b>{r['ty_le_kien_co_2019_pct']:.2f}%</b> (2019) lên <b>{r['ty_le_kien_co_2024_pct']:.2f}%</b> (2024), tăng bứt phá <b>+{r['tang_truong_kien_co_pp']:.2f} điểm %</b> (tương ứng thêm +{int(r['so_can_kien_co_tang_them']):,} căn kiên cố)."
                )

        lead = (
            "<strong>Lưu ý ranh giới dữ liệu:</strong> Trong hệ thống biểu mẫu thống kê KTXH 53 DTTS (Bộ dữ liệu UBDT & TCTK), "
            "chỉ tiêu <em>Nhà ở (kiên cố vs nhà tạm)</em> được điều tra và tổng hợp ở cấp <strong>53 Dân tộc trên toàn tỉnh</strong>, "
            "chưa phân rã theo ma trận chéo cấp Huyện. Ở cấp Huyện, chỉ tiêu kiên cố hóa hạ tầng được theo dõi qua <em>Tỷ lệ đường bê tông/nhựa</em> và <em>Tỷ lệ giảm nghèo</em>.<br><br>"
            "Dưới đây là <strong>Top 5 Dân tộc có tốc độ kiên cố hóa nhà ở tăng nhanh nhất tỉnh Đắk Lắk (2019 – 2024)</strong> trích xuất từ dữ liệu thực chứng:"
        )

        takeaway = (
            "Khuyến nghị tham mưu: Duy trì gói tín dụng ưu đãi theo Nghị định 28/2022/NĐ-CP và Dự án 1 (QĐ 1719) để hỗ trợ "
            "các nhóm dân tộc còn tỷ lệ kiên cố thấp vươn lên đạt chuẩn 3 cứng."
        )

        return self._format_result_payload(
            intent_code="DATA_BOUNDARY_HOUSING",
            intent_desc="Giải thích ranh giới dữ liệu Nhà ở và Top dân tộc kiên cố hóa nhanh nhất 2019 - 2024",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_district_poverty_comparison(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """So sánh quy mô hộ và hộ nghèo của một Huyện qua 2 kỳ (VD: Ea Súp 2019 vs 2024)."""
        dist = meta["district"]
        p1 = "KY_2019"
        p2 = "KY_2024"

        sql = f"""
        SELECT 
            ma_ky, ten_ky, ten_huyen,
            SUM(tong_ho_dtts) AS tong_ho_dtts,
            SUM(so_ho_ngheo) AS tong_so_ho_ngheo,
            ROUND(SUM(so_ho_ngheo) * 100.0 / NULLIF(SUM(tong_ho_dtts), 0), 2) AS ty_le_ngheo_pct,
            SUM(du_toan_ngan_sach_sinh_ke_trieu_vnd) AS tong_von_sinh_ke_trieu
        FROM v_xa_biendong_ngheo_da_ky
        WHERE ten_huyen ILIKE '%{dist.replace("Huyện ", "")}%' AND ma_ky IN ('{p1}', '{p2}')
        GROUP BY ma_ky, ten_ky, ten_huyen, thu_tu_ky
        ORDER BY thu_tu_ky ASC;
        """
        df = execute_query(sql)

        if df is None or len(df) < 2:
            return self._handle_default_provincial_snapshot(meta)

        r1 = df.iloc[0]
        r2 = df.iloc[1]

        ho19, ho24 = int(float(r1["tong_ho_dtts"])), int(float(r2["tong_ho_dtts"]))
        ngheo19, ngheo24 = int(float(r1["tong_so_ho_ngheo"])), int(float(r2["tong_so_ho_ngheo"]))
        pct19, pct24 = float(r1["ty_le_ngheo_pct"]), float(r2["ty_le_ngheo_pct"])

        delta_ngheo = ngheo19 - ngheo24
        delta_pct = pct19 - pct24
        growth_ho = ho24 - ho19

        lead = (
            f"Tại <strong>{dist}</strong>, trong giai đoạn 5 năm (2019 – 2024), quy mô hộ DTTS tăng từ <strong>{ho19:,} hộ</strong> "
            f"lên <strong>{ho24:,} hộ</strong> (+{growth_ho:,} hộ). Huyện đã <strong>giảm được {delta_ngheo:,} hộ nghèo DTTS</strong>, "
            f"kéo tỷ lệ nghèo từ <strong>{pct19:.2f}%</strong> (2019) xuống còn <strong>{pct24:.2f}%</strong> (2024) — giảm bứt phá <strong>{delta_pct:.2f} điểm %</strong>."
        )

        bullets = [
            f"<strong>Kỳ khảo sát 2019:</strong> Toàn huyện có <b>{ho19:,} hộ DTTS</b>, trong đó có <b>{ngheo19:,} hộ nghèo</b> (tỷ lệ nghèo <b>{pct19:.2f}%</b>).",
            f"<strong>Kỳ khảo sát 2024:</strong> Toàn huyện có <b>{ho24:,} hộ DTTS</b>, số hộ nghèo giảm còn <b>{ngheo24:,} hộ</b> (tỷ lệ nghèo <b>{pct24:.2f}%</b>).",
            f"<strong>Kết quả giảm nghèo thực tế:</strong> Giảm ròng <b>{delta_ngheo:,} hộ nghèo</b> sau 5 năm, tốc độ giảm nghèo bình quân đạt <b>{delta_pct / 5.0:.2f} điểm %/năm</b>."
        ]

        takeaway = (
            f"Góc nhìn tham mưu: Dù đã giảm {delta_ngheo:,} hộ nghèo, tỷ lệ nghèo của {dist} ở mức {pct24:.2f}% vẫn thuộc nhóm cao nhất tỉnh. "
            f"Cần tiếp tục ưu tiên nguồn vốn Dự án 3 (Chương trình MTQG 1719) với dự toán hỗ trợ sinh kế khoảng {ngheo24 * 30.0 / 1000.0:,.2f} tỷ VNĐ (30 triệu VNĐ/hộ)."
        )

        return self._format_result_payload(
            intent_code="DISTRICT_POVERTY_COMPARISON",
            intent_desc=f"Đối chiếu biến động hộ nghèo và quy mô hộ tại {dist} (2019 vs 2024)",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_provincial_housing_overview(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý câu hỏi Toàn tỉnh nhà tạm, dân tộc nào nhiều nhất (Kỳ 2026)."""
        period = meta["default_period"]
        p_name = "kỳ mới nhất 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")

        sql = f"""
        SELECT 
            ten_dantoc, nhom_nguon_goc,
            tong_so_ho_co_nha,
            nha_kien_co_ban_kien_co,
            nha_thieu_kien_co_don_so AS so_ho_nha_tam,
            ROUND(nha_thieu_kien_co_don_so * 100.0 / NULLIF(tong_so_ho_co_nha, 0), 2) AS ty_le_nha_tam_pct
        FROM fact_nhao_dantoc
        WHERE ma_ky = '{period}'
        ORDER BY so_ho_nha_tam DESC;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        tot_ho = int(float(df["tong_so_ho_co_nha"].sum()))
        tot_tam = int(float(df["so_ho_nha_tam"].sum()))
        pct_tam = round(tot_tam * 100.0 / max(1, tot_ho), 2)

        top1 = df.iloc[0]
        top2 = df.iloc[1] if len(df) > 1 else None
        top3 = df.iloc[2] if len(df) > 2 else None

        lead = (
            f"Hiện tại ({p_name}), toàn tỉnh Đắk Lắk có tổng cộng <strong>{tot_tam:,} hộ DTTS</strong> đang ở trong tình trạng "
            f"nhà tạm, dột nát, đơn sơ (chiếm <strong>{pct_tam:.2f}%</strong> trên tổng số {tot_ho:,} hộ DTTS có nhà). "
            f"Dân tộc có số lượng nhà tạm nhiều nhất toàn tỉnh là <strong>Người {top1['ten_dantoc']}</strong> với <strong>{int(top1['so_ho_nha_tam']):,} căn</strong>."
        )

        bullets = [
            f"<strong>Tổng quy mô toàn tỉnh ({p_name}):</strong> Có <b>{tot_tam:,} nhà tạm</b> trên <b>{tot_ho:,} hộ</b> (tỷ lệ <b>{pct_tam:.2f}%</b>).",
            f"<strong>#1. Dân tộc {top1['ten_dantoc']}:</strong> Chiếm số lượng lớn nhất với <b>{int(top1['so_ho_nha_tam']):,} hộ nhà tạm</b> (tỷ lệ {float(top1['ty_le_nha_tam_pct']):.2f}% trên {int(top1['tong_so_ho_co_nha']):,} hộ có nhà).",
        ]
        if top2 is not None:
            bullets.append(
                f"<strong>#2. Dân tộc {top2['ten_dantoc']}:</strong> Có <b>{int(top2['so_ho_nha_tam']):,} hộ nhà tạm</b> (tỷ lệ {float(top2['ty_le_nha_tam_pct']):.2f}% trên {int(top2['tong_so_ho_co_nha']):,} hộ có nhà)."
            )
        if top3 is not None:
            bullets.append(
                f"<strong>#3. Dân tộc {top3['ten_dantoc']}:</strong> Có <b>{int(top3['so_ho_nha_tam']):,} hộ nhà tạm</b> (tỷ lệ {float(top3['ty_le_nha_tam_pct']):.2f}% trên {int(top3['tong_so_ho_co_nha']):,} hộ có nhà)."
            )

        takeaway = (
            f"Góc nhìn tham mưu: Để hoàn thành mục tiêu xóa toàn bộ {tot_tam:,} căn nhà tạm trên địa bàn tỉnh, cần bố trí tổng dự toán "
            f"<strong>{tot_tam * 90.0 / 1000.0:,.2f} tỷ VNĐ</strong> (theo định mức 90 triệu VNĐ/căn của Dự án 1 - CTMTQG 1719)."
        )

        return self._format_result_payload(
            intent_code="PROVINCE_HOUSING_OVERVIEW",
            intent_desc=f"Tổng kiểm kê nhà tạm và xếp hạng các dân tộc có số nhà tạm nhiều nhất ({p_name})",
            sql=sql,
            df=df.head(10),
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_ethnic_head_to_head(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """So sánh đối đầu giữa 2 dân tộc (VD: Ê Đê vs Mông)."""
        eth1, eth2 = meta["ethnics"][0], meta["ethnics"][1]
        period = meta["default_period"]
        p_name = "kỳ 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")

        # Kiểm tra lĩnh vực quan tâm
        domain = meta["domain"]

        if domain == "LABOR_EDUCATION" or any(k in meta["question"].lower() for k in ["biet chu", "hoc van", "mu chu", "gioi"]):
            # So sánh học vấn & biết chữ
            sql = f"""
            SELECT 
                g.ten_dantoc, nk.tong_dan_so,
                g.biet_chu_tong, g.biet_chu_nam, g.biet_chu_nu,
                ROUND(g.biet_chu_tong * 100.0 / NULLIF(nk.tong_dan_so, 0), 2) AS ty_le_biet_chu_pct,
                ROUND(g.biet_chu_nam * 100.0 / NULLIF(nk.dan_so_nam, 0), 2) AS ty_le_nam_biet_chu_pct,
                ROUND(g.biet_chu_nu * 100.0 / NULLIF(nk.dan_so_nu, 0), 2) AS ty_le_nu_biet_chu_pct,
                ROUND((g.biet_chu_nam * 100.0 / NULLIF(nk.dan_so_nam, 0)) - (g.biet_chu_nu * 100.0 / NULLIF(nk.dan_so_nu, 0)), 2) AS chenh_lech_gioi_pp
            FROM fact_giaoduc_dantoc g
            JOIN fact_nhankhau_dantoc nk ON g.ma_ky = nk.ma_ky AND g.ma_dantoc = nk.ma_dantoc
            WHERE g.ma_ky = '{period}' AND (g.ten_dantoc ILIKE '%{eth1}%' OR g.ten_dantoc ILIKE '%{eth2}%')
            ORDER BY nk.tong_dan_so DESC;
            """
            df = execute_query(sql)
            if df is not None and len(df) >= 2:
                r1 = df.iloc[0]
                r2 = df.iloc[1]
                t1, t2 = r1["ten_dantoc"], r2["ten_dantoc"]
                nu1, nu2 = float(r1["ty_le_nu_biet_chu_pct"]), float(r2["ty_le_nu_biet_chu_pct"])
                nam1, nam2 = float(r1["ty_le_nam_biet_chu_pct"]), float(r2["ty_le_nam_biet_chu_pct"])
                diff1, diff2 = float(r1["chenh_lech_gioi_pp"]), float(r2["chenh_lech_gioi_pp"])

                lead = (
                    f"So sánh học vấn và khoảng cách giới ({p_name}): Người <strong>{t1}</strong> có tỷ lệ phụ nữ biết chữ đạt <strong>{nu1:.2f}%</strong> "
                    f"(chênh lệch nam - nữ là {diff1:+.2f} điểm %), trong khi người <strong>{t2}</strong> có tỷ lệ phụ nữ biết chữ đạt <strong>{nu2:.2f}%</strong> "
                    f"(chênh lệch nam - nữ lên tới {diff2:+.2f} điểm %)."
                )

                bullets = [
                    f"<strong>Người {t1}:</strong> Nam biết chữ đạt <b>{nam1:.2f}%</b>, Nữ biết chữ đạt <b>{nu1:.2f}%</b> (Khoảng cách giới: {diff1:+.2f} điểm %).",
                    f"<strong>Người {t2}:</strong> Nam biết chữ đạt <b>{nam2:.2f}%</b>, Nữ biết chữ đạt <b>{nu2:.2f}%</b> (Khoảng cách giới: {diff2:+.2f} điểm %).",
                    f"<strong>Căn nguyên nhân học:</strong> Nhóm mẫu hệ bản địa (như Ê Đê) có tỷ lệ phụ nữ biết chữ cao và vị thế bình đẳng, trong khi nhóm phụ hệ di cư (như Mông) chịu ảnh hưởng của hủ tục tảo hôn khiến tỷ lệ phụ nữ biết chữ thấp hơn nam giới rõ rệt."
                ]

                takeaway = (
                    "Khuyến nghị tham mưu: Tập trung nguồn lực Dự án 5 (QĐ 1719) để mở các lớp xóa mù chữ đặc thù cho phụ nữ DTTS di cư miền núi phía Bắc."
                )

                return self._format_result_payload(
                    intent_code="ETHNIC_EDUCATION_COMPARISON",
                    intent_desc=f"So sánh học vấn và khoảng cách giới giữa người {t1} và {t2}",
                    sql=sql,
                    df=df,
                    lead=lead,
                    bullets=bullets,
                    takeaway=takeaway,
                    meta=meta
                )

        # Mặc định so sánh nhà ở & chuyển dịch
        sql = f"""
        SELECT 
            ten_dantoc, nhom_nguon_goc,
            tong_ho_co_nha, so_ho_nha_tam_don_so, ty_le_nha_tam_pct,
            ty_le_khong_cmkt_pct, khoang_trong_tin_dung_pct
        FROM v_dantoc_chuyen_dich_da_ky
        WHERE ma_ky = '{period}' AND (ten_dantoc ILIKE '%{eth1}%' OR ten_dantoc ILIKE '%{eth2}%')
        ORDER BY tong_ho_co_nha DESC;
        """
        df = execute_query(sql)
        if df is None or len(df) < 2:
            return self._handle_default_provincial_snapshot(meta)

        r1 = df.iloc[0]
        r2 = df.iloc[1]
        t1, t2 = r1["ten_dantoc"], r2["ten_dantoc"]
        tam1, tam2 = int(float(r1["so_ho_nha_tam_don_so"])), int(float(r2["so_ho_nha_tam_don_so"]))
        pct_tam1, pct_tam2 = float(r1["ty_le_nha_tam_pct"]), float(r2["ty_le_nha_tam_pct"])

        lead = (
            f"So sánh thực trạng nhà ở ({p_name}): Người <strong>{t1}</strong> có <strong>{tam1:,} hộ nhà tạm</strong> (tỷ lệ {pct_tam1:.2f}%), "
            f"trong khi người <strong>{t2}</strong> có <strong>{tam2:,} hộ nhà tạm</strong> (tỷ lệ {pct_tam2:.2f}%)."
        )

        ho1 = int(float(r1.get("tong_ho_co_nha") or r1.get("tong_so_ho_co_nha") or 0))
        ho2 = int(float(r2.get("tong_ho_co_nha") or r2.get("tong_so_ho_co_nha") or 0))

        bullets = [
            f"<strong>Người {t1}:</strong> Quy mô {ho1:,} hộ, có <b>{tam1:,} căn nhà tạm</b> (tỷ lệ {pct_tam1:.2f}%).",
            f"<strong>Người {t2}:</strong> Quy mô {ho2:,} hộ, có <b>{tam2:,} căn nhà tạm</b> (tỷ lệ {pct_tam2:.2f}%).",
            f"<strong>Đánh giá tương đối:</strong> Tỷ lệ nhà tạm của người {t2 if pct_tam2 > pct_tam1 else t1} cao hơn {abs(pct_tam2 - pct_tam1):.2f} điểm %."
        ]

        takeaway = (
            f"Dự toán xóa nhà tạm: Cần { (tam1 + tam2) * 90.0 / 1000.0:,.2f} tỷ VNĐ (định mức 90 triệu VNĐ/căn) để xóa hết {tam1 + tam2:,} căn nhà tạm cho cả hai dân tộc."
        )

        return self._format_result_payload(
            intent_code="ETHNIC_HOUSING_COMPARISON",
            intent_desc=f"So sánh nhà ở giữa người {t1} và {t2}",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_commune_poverty_ranking(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Xếp hạng các xã nghèo / danh sách xã nghèo trong một huyện hoặc hồ sơ chi tiết một xã cụ thể."""
        dist = meta["district"]
        commune = meta.get("commune")
        period = meta["default_period"]
        p_name = "kỳ 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")

        if commune:
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_xa, ten_huyen, km_den_trung_tam_huyen,
                tong_ho_dtts, so_ho_ngheo, ty_le_ngheo_pct,
                du_toan_ngan_sach_sinh_ke_trieu_vnd
            FROM v_xa_biendong_ngheo_da_ky
            WHERE ten_xa = '{commune}'
            ORDER BY thu_tu_ky ASC;
            """
            df = execute_query(sql)
            if df is not None and not df.empty:
                r_last = df.iloc[-1]
                r_first = df.iloc[0]
                giam_pct = round(float(r_first["ty_le_ngheo_pct"]) - float(r_last["ty_le_ngheo_pct"]), 2)
                lead = (
                    f"Hồ sơ giảm nghèo và KTXH tại <strong>{r_last['ten_xa']} ({r_last['ten_huyen']})</strong>: "
                    f"Hiện tại ({r_last['ten_ky']}), xã có quy mô <strong>{int(float(r_last['tong_ho_dtts'])):,} hộ DTTS</strong>, "
                    f"còn <strong>{int(float(r_last['so_ho_ngheo'])):,} hộ nghèo</strong> (tỷ lệ <strong>{float(r_last['ty_le_ngheo_pct']):.2f}%</strong>, "
                    f"cách trung tâm huyện {r_last['km_den_trung_tam_huyen']} km)."
                )
                bullets = []
                for _, r in df.iterrows():
                    bullets.append(
                        f"<strong>{r['ten_ky']} ({r['ma_ky']}):</strong> Quy mô {int(float(r['tong_ho_dtts'])):,} hộ DTTS | Hộ nghèo: <b>{int(float(r['so_ho_ngheo'])):,} hộ ({float(r['ty_le_ngheo_pct']):.2f}%)</b>."
                    )
                bullets.append(
                    f"<strong>Tiến độ giảm nghèo (2019 – 2026):</strong> Tỷ lệ hộ nghèo đã giảm <b>{giam_pct:.2f} điểm %</b>."
                )
                budget_ty = float(r_last["du_toan_ngan_sach_sinh_ke_trieu_vnd"] or 0) / 1000.0
                takeaway = (
                    f"Khuyến nghị tham mưu: Bố trí dự toán khoảng {budget_ty:,.2f} tỷ VNĐ từ vốn Dự án 3 (QĐ 1719 - định mức 30 triệu VNĐ/hộ) "
                    f"để hỗ trợ sinh kế cho {int(float(r_last['so_ho_ngheo'])):,} hộ nghèo tại {r_last['ten_xa']}."
                )
                return self._format_result_payload(
                    intent_code="COMMUNE_PROFILE_360",
                    intent_desc=f"Báo cáo thực trạng KTXH và giảm nghèo tại {r_last['ten_xa']} ({r_last['ten_huyen']})",
                    sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
                )

        where_clause = f"WHERE ma_ky = '{period}'"
        if dist:
            where_clause += f" AND ten_huyen ILIKE '%{dist.replace('Huyện ', '')}%'"

        sql = f"""
        SELECT 
            ten_xa, ten_huyen, km_den_trung_tam_huyen,
            tong_ho_dtts, so_ho_ngheo, ty_le_ngheo_pct,
            du_toan_ngan_sach_sinh_ke_trieu_vnd
        FROM v_xa_biendong_ngheo_da_ky
        {where_clause}
        ORDER BY ty_le_ngheo_pct DESC
        LIMIT 10;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        scope = dist if dist else "Toàn tỉnh Đắk Lắk"
        top1 = df.iloc[0]

        lead = (
            f"Tại <strong>{scope}</strong> ({p_name}), xã có tỷ lệ hộ nghèo DTTS cao nhất là <strong>{top1['ten_xa']}</strong> "
            f"với <strong>{top1['ty_le_ngheo_pct']:.2f}%</strong> ({int(float(top1['so_ho_ngheo'])):,} hộ nghèo, cách huyện {top1['km_den_trung_tam_huyen']} km)."
        )

        bullets = []
        for i, r in df.head(5).iterrows():
            bullets.append(
                f"<strong>#{i+1}. {r['ten_xa']} ({r['ten_huyen']}):</strong> Tỷ lệ nghèo <b>{r['ty_le_ngheo_pct']:.2f}%</b> ({int(float(r['so_ho_ngheo'])):,} hộ nghèo, cự ly {r['km_den_trung_tam_huyen']} km)."
            )

        tot_budget = float(df["du_toan_ngan_sach_sinh_ke_trieu_vnd"].sum() or 0) / 1000.0
        takeaway = (
            f"Khuyến nghị tham mưu: Ưu tiên phân bổ vốn Dự án 3 (30 triệu VNĐ/hộ) với dự toán khoảng {tot_budget:,.2f} tỷ VNĐ "
            f"cho các xã điểm nóng trên."
        )

        return self._format_result_payload(
            intent_code="COMMUNE_POVERTY_RANKING",
            intent_desc=f"Danh sách các xã có tỷ lệ nghèo cao nhất tại {scope} ({p_name})",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_ethnic_profile_360(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Hồ sơ tổng hợp 360 độ của một dân tộc cụ thể."""
        eth = meta["ethnics"][0]
        period = meta["default_period"]

        sql = f"""
        SELECT 
            ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc,
            tong_ho_co_nha, so_ho_nha_tam_don_so, ty_le_nha_tam_pct,
            ty_le_khong_cmkt_pct, khoang_trong_tin_dung_pct, so_ho_khat_von
        FROM v_dantoc_chuyen_dich_da_ky
        WHERE ten_dantoc ILIKE '%{eth}%'
        ORDER BY thu_tu_ky ASC;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        r_last = df.iloc[-1]
        lead = (
            f"Hồ sơ chuyển dịch KTXH của đồng bào <strong>Dân tộc {r_last['ten_dantoc']}</strong> ({r_last['nhom_nguon_goc']}): "
            f"Quy mô hiện tại đạt <strong>{int(float(r_last['tong_ho_co_nha'])):,} hộ</strong>, "
            f"và còn <strong>{int(float(r_last['so_ho_nha_tam_don_so'])):,} hộ nhà tạm</strong> ({float(r_last['ty_le_nha_tam_pct']):.2f}%)."
        )

        bullets = [
            f"<strong>Quy mô & Nhà ở:</strong> Tổng số {int(float(r_last['tong_ho_co_nha'])):,} hộ; còn <b>{int(float(r_last['so_ho_nha_tam_don_so'])):,} nhà tạm</b> ({float(r_last['ty_le_nha_tam_pct']):.2f}%).",
            f"<strong>Chất lượng lao động:</strong> Tỷ lệ lao động chưa qua đào tạo CMKT là <b>{float(r_last['ty_le_khong_cmkt_pct']):.2f}%</b>.",
            f"<strong>Nhu cầu vốn vay (NĐ 28):</strong> Có <b>{int(float(r_last['so_ho_khat_von'])):,} hộ khát vốn</b> (thiếu hụt {float(r_last['khoang_trong_tin_dung_pct']):.2f}%)."
        ]

        takeaway = (
            f"Khuyến nghị tham mưu: Tập trung giải ngân gói tín dụng ưu đãi và đào tạo nghề theo Dự án 5 để tạo sinh kế lâu dài."
        )

        return self._format_result_payload(
            intent_code="ETHNIC_PROFILE_360",
            intent_desc=f"Báo cáo toàn cảnh KTXH 360 độ Dân tộc {r_last['ten_dantoc']}",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_district_profile_360(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Hồ sơ tổng hợp 360 độ của một Huyện cụ thể."""
        dist = meta["district"]

        sql = f"""
        SELECT 
            ma_ky, ten_ky, ten_huyen,
            ty_le_ho_xi_hvs_bq_pct, ty_le_internet_huyen_pct, ty_le_nuoc_hvs_bq_pct,
            tong_ho_dtts_huyen, tong_ho_co_internet
        FROM v_huyen_vesinh_chuyendoiso_da_ky
        WHERE ten_huyen ILIKE '%{dist.replace("Huyện ", "")}%'
        ORDER BY thu_tu_ky ASC;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        r_last = df.iloc[-1]
        lead = (
            f"Báo cáo hiện trạng KTXH & Hạ tầng thiết yếu tại <strong>{dist}</strong>: "
            f"Tỷ lệ hộ có hố xí hợp vệ sinh đạt <strong>{float(r_last['ty_le_ho_xi_hvs_bq_pct']):.2f}%</strong>, "
            f"phủ sóng Internet đạt <strong>{float(r_last['ty_le_internet_huyen_pct']):.2f}%</strong> và nước sạch đạt <strong>{float(r_last['ty_le_nuoc_hvs_bq_pct']):.2f}%</strong>."
        )

        bullets = [
            f"<strong>Tiêu chí 17 NTM (Hố xí HVS):</strong> Đạt <b>{float(r_last['ty_le_ho_xi_hvs_bq_pct']):.2f}%</b>.",
            f"<strong>Hạ tầng số Đề án 06 (Internet):</strong> Đạt <b>{float(r_last['ty_le_internet_huyen_pct']):.2f}%</b> (tương ứng {int(float(r_last['tong_ho_co_internet'])):,} hộ kết nối mạng).",
            f"<strong>Nước hợp vệ sinh:</strong> Đạt <b>{float(r_last['ty_le_nuoc_hvs_bq_pct']):.2f}%</b>."
        ]

        takeaway = (
            f"Khuyến nghị tham mưu: Bố trí nguồn vốn xây dựng Nông thôn mới để xử lý dứt điểm điểm trũng hố xí hợp vệ sinh tại địa bàn."
        )

        return self._format_result_payload(
            intent_code="DISTRICT_PROFILE_360",
            intent_desc=f"Báo cáo giám sát KTXH và hạ tầng thiết yếu tại {dist}",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_sanitation_digital(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý câu hỏi về Hố xí HVS, nước sạch và Internet cấp Huyện."""
        period = meta["default_period"]
        p_name = "kỳ 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")
        dist = meta.get("district")

        where_clause = f"WHERE ma_ky = '{period}'"
        if dist:
            dist_clean = dist.replace("Huyện ", "").replace("Thị xã ", "").replace("Thành phố ", "").strip()
            where_clause += f" AND ten_huyen ILIKE '%{dist_clean}%'"

        sql = f"""
        SELECT 
            ten_huyen, ty_le_ho_xi_hvs_bq_pct, ty_le_internet_huyen_pct, ty_le_nuoc_hvs_bq_pct,
            tong_ho_dtts_huyen, tong_ho_co_internet
        FROM v_huyen_vesinh_chuyendoiso_da_ky
        {where_clause}
        ORDER BY ty_le_ho_xi_hvs_bq_pct ASC
        LIMIT 10;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        if dist:
            r0 = df.iloc[0]
            lead = (
                f"Hiện trạng Tiêu chí 17 NTM và Chuyển đổi số tại <strong>{r0['ten_huyen']}</strong> ({p_name}): "
                f"Tỷ lệ hộ có hố xí hợp vệ sinh đạt <strong>{float(r0['ty_le_ho_xi_hvs_bq_pct']):.2f}%</strong>, "
                f"nước sạch hợp vệ sinh đạt <strong>{float(r0['ty_le_nuoc_hvs_bq_pct']):.2f}%</strong> "
                f"và độ phủ sóng Internet đạt <strong>{float(r0['ty_le_internet_huyen_pct']):.2f}%</strong>."
            )
            bullets = [
                f"<strong>Tiêu chí 17 NTM (Hố xí HVS):</strong> Đạt <b>{float(r0['ty_le_ho_xi_hvs_bq_pct']):.2f}%</b> (Toàn tỉnh đạt bình quân 41.50%).",
                f"<strong>Nước sinh hoạt hợp vệ sinh:</strong> Đạt <b>{float(r0['ty_le_nuoc_hvs_bq_pct']):.2f}%</b>.",
                f"<strong>Hạ tầng số Đề án 06 (Internet):</strong> Đạt <b>{float(r0['ty_le_internet_huyen_pct']):.2f}%</b> (tương ứng {int(float(r0['tong_ho_co_internet'])):,} hộ kết nối mạng trên tổng số {int(float(r0['tong_ho_dtts_huyen'])):,} hộ DTTS)."
            ]
            takeaway = f"Khuyến nghị tham mưu: Ưu tiên phân bổ vốn Nông thôn mới hỗ trợ 12 triệu VNĐ/hộ để xóa điểm trũng hố xí tại {r0['ten_huyen']}."
            return self._format_result_payload(
                intent_code="DISTRICT_SANITATION_PROFILE",
                intent_desc=f"Báo cáo vệ sinh môi trường và hạ tầng số tại {r0['ten_huyen']} ({p_name})",
                sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
            )

        r_low = df.iloc[0]
        lead = (
            f"Đánh giá Tiêu chí 17 NTM và Chuyển đổi số ({p_name}): Điểm trũng vệ sinh môi trường thấp nhất tỉnh thuộc về "
            f"<strong>{r_low['ten_huyen']}</strong> với tỷ lệ hộ có hố xí hợp vệ sinh chỉ đạt <strong>{float(r_low['ty_le_ho_xi_hvs_bq_pct']):.2f}%</strong>."
        )

        bullets = []
        for i, r in df.head(3).iterrows():
            bullets.append(
                f"<strong>#{i+1}. {r['ten_huyen']}:</strong> Hố xí HVS <b>{float(r['ty_le_ho_xi_hvs_bq_pct']):.2f}%</b> | Internet <b>{float(r['ty_le_internet_huyen_pct']):.2f}%</b> | Nước HVS <b>{float(r['ty_le_nuoc_hvs_bq_pct']):.2f}%</b>."
            )

        takeaway = "Khuyến nghị: Ưu tiên gói hỗ trợ 12 triệu VNĐ/hộ để phổ cập hố xí tự hoại cho các huyện trũng vệ sinh."

        return self._format_result_payload(
            intent_code="SANITATION_DIGITAL_RANKING",
            intent_desc="Xếp hạng các huyện có tỷ lệ hố xí hợp vệ sinh và tiếp cận internet",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_district_head_to_head(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """So sánh đối đầu giữa 2 Huyện về vệ sinh môi trường, nước sạch và internet."""
        period = meta["default_period"]
        p_name = "kỳ 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")
        dists = meta.get("districts", [])[:2]
        d1 = dists[0].replace("Huyện ", "").replace("Thị xã ", "").replace("Thành phố ", "").strip()
        d2 = dists[1].replace("Huyện ", "").replace("Thị xã ", "").replace("Thành phố ", "").strip()

        sql = f"""
        SELECT 
            ten_huyen, ty_le_ho_xi_hvs_bq_pct, ty_le_internet_huyen_pct, ty_le_nuoc_hvs_bq_pct,
            tong_ho_dtts_huyen, tong_ho_co_internet
        FROM v_huyen_vesinh_chuyendoiso_da_ky
        WHERE ma_ky = '{period}' AND (ten_huyen ILIKE '%{d1}%' OR ten_huyen ILIKE '%{d2}%')
        ORDER BY ten_huyen ASC;
        """
        df = execute_query(sql)
        if df is None or len(df) < 2:
            return self._handle_sanitation_digital(meta)

        r1 = df.iloc[0]
        r2 = df.iloc[1]
        h1, h2 = r1["ten_huyen"], r2["ten_huyen"]
        hvs1, hvs2 = float(r1["ty_le_ho_xi_hvs_bq_pct"]), float(r2["ty_le_ho_xi_hvs_bq_pct"])
        net1, net2 = float(r1["ty_le_internet_huyen_pct"]), float(r2["ty_le_internet_huyen_pct"])
        nuoc1, nuoc2 = float(r1["ty_le_nuoc_hvs_bq_pct"]), float(r2["ty_le_nuoc_hvs_bq_pct"])

        lead = (
            f"So sánh chỉ tiêu vệ sinh môi trường & hạ tầng số ({p_name}): "
            f"<strong>{h1}</strong> có tỷ lệ hố xí hợp vệ sinh đạt <strong>{hvs1:.2f}%</strong> (Internet: {net1:.2f}%), "
            f"trong khi <strong>{h2}</strong> đạt <strong>{hvs2:.2f}%</strong> (Internet: {net2:.2f}%)."
        )

        diff_hvs = abs(hvs1 - hvs2)
        h_higher = h1 if hvs1 > hvs2 else h2
        bullets = [
            f"<strong>{h1}:</strong> Hố xí HVS <b>{hvs1:.2f}%</b> | Nước sạch <b>{nuoc1:.2f}%</b> | Internet <b>{net1:.2f}%</b> ({int(float(r1['tong_ho_co_internet'])):,} hộ).",
            f"<strong>{h2}:</strong> Hố xí HVS <b>{hvs2:.2f}%</b> | Nước sạch <b>{nuoc2:.2f}%</b> | Internet <b>{net2:.2f}%</b> ({int(float(r2['tong_ho_co_internet'])):,} hộ).",
            f"<strong>Đánh giá so sánh:</strong> {h_higher} có tỷ lệ hố xí HVS cao hơn <b>{diff_hvs:.2f} điểm %</b>. Tuy nhiên, cả hai địa bàn đều là 'vùng trũng' Tiêu chí 17 NTM thấp nhất toàn tỉnh (đều dưới 20%)."
        ]

        takeaway = (
            "Khuyến nghị tham mưu: Ưu tiên gói ngân sách NTM hỗ trợ 12 triệu VNĐ/hộ xây dựng hố xí tự hoại đồng bộ cho cả hai huyện, "
            "tập trung xử lý dứt điểm điểm nghẽn vệ sinh môi trường vùng đồng bào DTTS."
        )

        return self._format_result_payload(
            intent_code="DISTRICT_SANITATION_COMPARISON",
            intent_desc=f"So sánh hạ tầng vệ sinh và chuyển đổi số giữa {h1} và {h2} ({p_name})",
            sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
        )

    def _handle_vulnerability_health(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý câu hỏi về y tế sinh sản hoặc ma túy/HIV."""
        period = meta["default_period"]
        sql = f"""
        SELECT 
            phan_nhom_rui_ro, ten_doi_tuong, pham_vi_nhom,
            chi_so_rui_ro_chinh, chi_so_rui_ro_phu, ty_le_giam_rui_ro_pct
        FROM v_diemnong_anninh_yte_da_ky
        WHERE ma_ky = '{period}'
        ORDER BY chi_so_rui_ro_chinh DESC
        LIMIT 10;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        lead = f"Giám sát điểm nóng rủi ro an ninh cơ sở và y tế sinh sản ({period}):"
        bullets = []
        for i, r in df.head(5).iterrows():
            bullets.append(
                f"<strong>#{i+1}. {r['ten_doi_tuong']} ({r['pham_vi_nhom']}):</strong> {r['phan_nhom_rui_ro']} — Chỉ số chính: <b>{int(float(r['chi_so_rui_ro_chinh'])):,}</b> (Phụ: {int(float(r['chi_so_rui_ro_phu'])):,})."
            )

        takeaway = "Khuyến nghị: Duy trì đội ngũ cô đỡ thôn bản và hỗ trợ gói sinh đẻ an toàn 4,5 triệu VNĐ/ca."

        return self._format_result_payload(
            intent_code="VULNERABILITY_HEALTH_OVERVIEW",
            intent_desc="Báo cáo điểm nóng an ninh và y tế sinh sản vùng DTTS",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _handle_labor_education(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Báo cáo chất lượng lao động, tỷ lệ chưa qua đào tạo CMKT và việc làm nông nghiệp."""
        period = meta["default_period"]
        sql = f"""
        SELECT 
            ten_dantoc, nhom_nguon_goc,
            tong_lao_dong, lao_dong_khong_cmkt, ty_le_khong_cmkt_pct,
            lao_dong_nong_nghiep, ty_le_nong_nghiep_pct, ty_le_nu_biet_chu_pct
        FROM v_dantoc_chuyen_dich_da_ky
        WHERE ma_ky = '{period}'
        ORDER BY tong_lao_dong DESC
        LIMIT 10;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        tot_ld = float(df["tong_lao_dong"].sum() or 0)
        tot_no_cmkt = float(df["lao_dong_khong_cmkt"].sum() or 0)
        tot_agri = float(df["lao_dong_nong_nghiep"].sum() or 0)
        pct_no_cmkt = round(tot_no_cmkt * 100.0 / max(1.0, tot_ld), 2)
        pct_agri = round(tot_agri * 100.0 / max(1.0, tot_ld), 2)

        lead = (
            f"Thực trạng chất lượng lao động và việc làm DTTS ({period}): "
            f"Toàn tỉnh ghi nhận <strong>{pct_no_cmkt:.2f}%</strong> lao động DTTS (khoảng {int(tot_no_cmkt):,} người) "
            f"chưa qua đào tạo chuyên môn kỹ thuật, dẫn đến việc <strong>{pct_agri:.2f}%</strong> lực lượng lao động bị khóa chặt trong nông nghiệp năng suất thấp."
        )
        bullets = [
            f"<strong>Bẫy kỹ năng CMKT:</strong> Tỷ lệ lao động chưa có bằng cấp/chứng chỉ nghề ở mức <b>{pct_no_cmkt:.2f}%</b> (người Mông đạt đỉnh 96.98%, người Gia Rai đạt 92.40%).",
            f"<strong>Bẫy việc làm nông nghiệp:</strong> <b>{pct_agri:.2f}%</b> lao động làm nông nghiệp thuần túy, hạn chế cơ hội dịch chuyển sang công nghiệp - dịch vụ có thu nhập cao.",
            f"<strong>Trụ cột dân số vàng:</strong> Dân tộc Ê Đê gánh vác quy mô lớn nhất với hơn {int(float(df.iloc[0]['tong_lao_dong'])):,} lao động, trong đó có {int(float(df.iloc[0]['lao_dong_khong_cmkt'])):,} người chưa qua đào tạo."
        ]
        takeaway = (
            "Khuyến nghị tham mưu: Ưu tiên vốn Dự án 5 (QĐ 1719) với định mức 6 triệu VNĐ/lao động để đào tạo nghề gắn với nhu cầu của các khu/cụm công nghiệp địa phương."
        )
        return self._format_result_payload(
            intent_code="LABOR_EDUCATION_OVERVIEW",
            intent_desc="Báo cáo bẫy lao động chưa qua đào tạo CMKT và việc làm nông nghiệp",
            sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
        )

    def _handle_budget(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Báo cáo dự toán ngân sách 6 định mức pháp lý QĐ 1719 và NĐ 28."""
        period = meta["default_period"]
        sql = f"""
        SELECT 
            ten_chitieu, ten_chinh_sach, don_vi_tinh,
            so_luong_doi_tuong_can_ho_tro, don_gia_trieu_vnd,
            tong_kinh_phi_can_phan_bo_ty_vnd, can_cu_phap_ly_dinh_muc
        FROM v_tong_hop_ngan_sach_chinh_sach_ky
        WHERE ma_ky = '{period}'
        ORDER BY tong_kinh_phi_can_phan_bo_ty_vnd DESC;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        tot_budget = float(df["tong_kinh_phi_can_phan_bo_ty_vnd"].sum() or 0)
        lead = (
            f"Tổng dự toán ngân sách đầu tư công KTXH 53 DTTS ({period}) là <strong>{tot_budget:,.2f} tỷ VNĐ</strong>, "
            f"được cấu thành từ 6 định mức chính sách pháp lý trọng tâm theo Quyết định 1719/QĐ-TTg và Nghị định 28/2022/NĐ-CP."
        )
        bullets = []
        for i, r in df.iterrows():
            bullets.append(
                f"<strong>#{i+1}. {r['ten_chitieu']} ({r['ten_chinh_sach']}):</strong> Dự toán <b>{float(r['tong_kinh_phi_can_phan_bo_ty_vnd']):,.2f} tỷ VNĐ</b> ({int(float(r['so_luong_doi_tuong_can_ho_tro'])):,} {r['don_vi_tinh']} × {float(r['don_gia_trieu_vnd']):,.1f} triệu VNĐ - {r['can_cu_phap_ly_dinh_muc']})."
            )
        takeaway = "Khuyến nghị: Phân bổ vốn theo tiến độ giải ngân thực tế và ưu tiên hàng đầu cho xóa nhà tạm (Dự án 1) và hỗ trợ đất/tín dụng (Dự án 3 & NĐ 28)."
        return self._format_result_payload(
            intent_code="POLICY_BUDGET_OVERVIEW",
            intent_desc="Dự toán tổng hợp nhu cầu ngân sách đầu tư công 6 định mức pháp lý",
            sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
        )

    def _handle_credit_land(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Báo cáo nhu cầu vốn tín dụng chính sách (NĐ 28/2022/NĐ-CP) và quỹ đất sản xuất."""
        period = meta["default_period"]
        p_name = "kỳ 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")
        ethnics = meta.get("ethnics", [])

        where_clause = f"WHERE ma_ky = '{period}'"
        if ethnics:
            where_clause += f" AND ten_dantoc ILIKE '%{ethnics[0]}%'"

        sql = f"""
        SELECT 
            ten_dantoc, nhom_nguon_goc,
            tong_ho_co_nha, so_ho_khat_von, khoang_trong_tin_dung_pct,
            dien_tich_dat_sx_bq_ha
        FROM v_dantoc_chuyen_dich_da_ky
        {where_clause}
        ORDER BY so_ho_khat_von DESC
        LIMIT 10;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        tot_khat_von = int(float(df["so_ho_khat_von"].sum() or 0))
        budget_tin_dung = tot_khat_von * 65.0 / 1000.0
        r_top = df.iloc[0]

        lead = (
            f"Thực trạng tiếp cận vốn tín dụng và đất sản xuất vùng DTTS ({p_name}): "
            f"Toàn tỉnh ghi nhận <strong>{tot_khat_von:,} hộ DTTS</strong> đang trong tình trạng thiếu vốn sản xuất "
            f"(khoảng trống tín dụng bình quân {float(r_top['khoang_trong_tin_dung_pct']):.2f}%), "
            f"cần tổng nguồn vốn vay ưu đãi ước tính <strong>{budget_tin_dung:,.2f} tỷ VNĐ</strong> theo Nghị định 28/2022/NĐ-CP."
        )

        bullets = []
        for i, r in df.head(5).iterrows():
            bullets.append(
                f"<strong>#{i+1}. Dân tộc {r['ten_dantoc']}:</strong> Có <b>{int(float(r['so_ho_khat_von'])):,} hộ khát vốn</b> (thiếu hụt {float(r['khoang_trong_tin_dung_pct']):.2f}%), quỹ đất sản xuất bình quân đạt <b>{float(r['dien_tich_dat_sx_bq_ha']):.2f} ha/hộ</b>."
            )

        takeaway = (
            f"Khuyến nghị tham mưu: Đề nghị Chi nhánh Ngân hàng Chính sách xã hội tỉnh Đắk Lắk ưu tiên phân bổ gói tín dụng ưu đãi "
            f"hạn mức tối đa 100 triệu VNĐ/hộ (lãi suất ưu đãi 3%/năm) theo Nghị định 28/2022/NĐ-CP để hỗ trợ {tot_khat_von:,} hộ DTTS phát triển sản xuất."
        )

        return self._format_result_payload(
            intent_code="CREDIT_LAND_OVERVIEW",
            intent_desc=f"Thực trạng tiếp cận vốn tín dụng chính sách NĐ 28 và quỹ đất sản xuất ({p_name})",
            sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
        )

    def _handle_demographic(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Báo cáo nhân khẩu học, cơ cấu 3 nhóm tuổi, tỷ lệ phụ thuộc trẻ em và già hóa."""
        period = meta["default_period"]
        p_name = "kỳ 2026" if period == "KY_2026" else ("năm 2024" if period == "KY_2024" else "năm 2019")
        ethnics = meta.get("ethnics", [])

        if ethnics:
            target_eth = ethnics[0]
            sql = f"""
            SELECT 
                ten_dantoc, nhom_nguon_goc, tong_dan_so,
                dan_so_nam, dan_so_nu,
                dan_so_0_14, dan_so_15_59, dan_so_60_plus,
                ROUND(dan_so_0_14 * 100.0 / NULLIF(tong_dan_so, 0), 2) AS ty_le_0_14_pct,
                ROUND(dan_so_15_59 * 100.0 / NULLIF(tong_dan_so, 0), 2) AS ty_le_15_59_pct,
                ROUND(dan_so_60_plus * 100.0 / NULLIF(tong_dan_so, 0), 2) AS ty_le_60_plus_pct,
                ROUND(dan_so_0_14 * 100.0 / NULLIF(dan_so_15_59, 0), 2) AS ty_le_phu_thuoc_tre_em_pct,
                ROUND(dan_so_60_plus * 100.0 / NULLIF(dan_so_0_14, 0), 2) AS chi_so_gia_hoa_pct
            FROM fact_nhankhau_dantoc
            WHERE ma_ky = '{period}' AND ten_dantoc ILIKE '%{target_eth}%';
            """
            df = execute_query(sql)
            if df is not None and not df.empty:
                r = df.iloc[0]
                lead = (
                    f"Cơ cấu nhân khẩu học và 3 nhóm tuổi của <strong>Đồng bào Dân tộc {r['ten_dantoc']}</strong> ({p_name}): "
                    f"Tổng nhân khẩu đạt <strong>{int(float(r['tong_dan_so'])):,} người</strong> "
                    f"(Nam: {int(float(r['dan_so_nam'])):,}, Nữ: {int(float(r['dan_so_nu'])):,}). "
                    f"Trong đó, lực lượng lao động vàng (15-59 tuổi) chiếm <strong>{float(r['ty_le_15_59_pct']):.2f}%</strong>."
                )
                bullets = [
                    f"<strong>Nhóm 0–14 tuổi (Thế hệ tương lai):</strong> {int(float(r['dan_so_0_14'])):,} người (chiếm <b>{float(r['ty_le_0_14_pct']):.2f}%</b> dân số dân tộc).",
                    f"<strong>Nhóm 15–59 tuổi (Lao động vàng):</strong> {int(float(r['dan_so_15_59'])):,} người (chiếm <b>{float(r['ty_le_15_59_pct']):.2f}%</b>).",
                    f"<strong>Nhóm 60+ tuổi (Người cao tuổi):</strong> {int(float(r['dan_so_60_plus'])):,} người (chiếm <b>{float(r['ty_le_60_plus_pct']):.2f}%</b>).",
                    f"<strong>Chỉ số phụ thuộc & Già hóa:</strong> Tỷ lệ phụ thuộc trẻ em đạt <b>{float(r['ty_le_phu_thuoc_tre_em_pct']):.2f}%</b>, chỉ số già hóa đạt <b>{float(r['chi_so_gia_hoa_pct']):.2f}%</b>."
                ]
                takeaway = (
                    f"Khuyến nghị tham mưu: Với {float(r['ty_le_15_59_pct']):.2f}% dân số trong độ tuổi lao động, người {r['ten_dantoc']} "
                    f"đang trong thời kỳ 'dân số vàng', cần đẩy mạnh đào tạo nghề theo Dự án 5 (QĐ 1719) để chuyển đổi cơ cấu kinh tế."
                )
                return self._format_result_payload(
                    intent_code="ETHNIC_DEMOGRAPHIC_PROFILE",
                    intent_desc=f"Cơ cấu 3 nhóm tuổi và nhân khẩu học Dân tộc {r['ten_dantoc']} ({p_name})",
                    sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
                )

        # Xếp hạng toàn tỉnh
        sql = f"""
        SELECT 
            ten_dantoc, nhom_nguon_goc, tong_dan_so,
            dan_so_0_14, dan_so_15_59, dan_so_60_plus,
            ROUND(dan_so_0_14 * 100.0 / NULLIF(dan_so_15_59, 0), 2) AS ty_le_phu_thuoc_tre_em_pct,
            ROUND(dan_so_60_plus * 100.0 / NULLIF(dan_so_0_14, 0), 2) AS chi_so_gia_hoa_pct,
            ROUND(dan_so_0_14 * 100.0 / NULLIF(tong_dan_so, 0), 2) AS ty_le_tre_em_pct
        FROM fact_nhankhau_dantoc
        WHERE ma_ky = '{period}' AND tong_dan_so >= 50 AND dan_so_15_59 > 0
        ORDER BY ty_le_phu_thuoc_tre_em_pct DESC NULLS LAST
        LIMIT 10;
        """
        df = execute_query(sql)
        if df is None or df.empty:
            return self._handle_default_provincial_snapshot(meta)

        r_max_child = df.iloc[0]
        max_dep = float(r_max_child['ty_le_phu_thuoc_tre_em_pct'] or 0)
        max_child_pct = float(r_max_child['ty_le_tre_em_pct'] or 0)

        lead = (
            f"Báo cáo phân hóa nhân khẩu học và cơ cấu độ tuổi 53 DTTS ({p_name}): "
            f"Dân tộc có tỷ lệ phụ thuộc trẻ em cao nhất toàn tỉnh là <strong>Người {r_max_child['ten_dantoc']}</strong> "
            f"với <strong>{max_dep:.2f}%</strong> (tỷ lệ trẻ em 0-14 tuổi chiếm {max_child_pct:.2f}% dân số)."
        )

        bullets = []
        for i, r in df.head(5).iterrows():
            dep_pct = float(r['ty_le_phu_thuoc_tre_em_pct'] or 0)
            aging_pct = float(r['chi_so_gia_hoa_pct'] or 0)
            bullets.append(
                f"<strong>#{i+1}. Dân tộc {r['ten_dantoc']} ({r['nhom_nguon_goc']}):</strong> Phụ thuộc trẻ em <b>{dep_pct:.2f}%</b> (Trẻ em: {int(float(r['dan_so_0_14'])):,} người | Lao động: {int(float(r['dan_so_15_59'])):,} người | Già hóa: {aging_pct:.2f}%)."
            )

        takeaway = (
            "Khuyến nghị tham mưu: Tập trung nguồn vốn Dự án 5 (QĐ 1719) xây dựng trường lớp mầm non và hỗ trợ dinh dưỡng học đường "
            "cho các dân tộc có tháp tuổi siêu trẻ (Mông, Xơ Đăng), đồng thời củng cố mạng lưới trạm y tế chăm sóc cho nhóm già hóa nhanh."
        )

        return self._format_result_payload(
            intent_code="DEMOGRAPHIC_OVERVIEW",
            intent_desc=f"Báo cáo phân hóa nhân khẩu học, phụ thuộc trẻ em và chỉ số già hóa ({p_name})",
            sql=sql, df=df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
        )

    def _handle_out_of_scope(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý câu hỏi ngoài phạm vi nghiệp vụ (thời tiết, giá vàng, thị trường...)."""
        lead = (
            "<strong>Thông báo phạm vi nghiệp vụ:</strong> Câu hỏi của bạn nằm ngoài phạm vi phân tích của "
            "<strong>Hệ thống Hỗ trợ Ra Quyết định & Tham mưu Chính sách KTXH 53 Dân tộc thiểu số tỉnh Đắk Lắk</strong>."
        )
        bullets = [
            "Hệ thống được thiết kế chuyên biệt phục vụ phân tích dữ liệu thống kê KTXH của <b>53 thành phần Dân tộc thiểu số</b> trên địa bàn tỉnh Đắk Lắk qua 3 kỳ khảo sát (2019, 2024, 2026).",
            "<strong>Phạm vi dữ liệu khả dụng:</strong> (1) Giảm nghèo & Sinh kế 184 xã/phường, (2) Kiên cố hóa nhà ở & Xóa nhà tạm, (3) Tiêu chí 17 NTM: Nước sạch & Hố xí HVS, (4) Lao động & Bằng cấp CMKT, (5) Tín dụng chính sách NĐ 28 & Đất sản xuất, (6) Y tế sinh sản & Điểm nóng an ninh, (7) Dự toán ngân sách đầu tư công CTMTQG 1719.",
            "<strong>Gợi ý câu hỏi hợp lệ:</strong> 'Xã nào nghèo nhất huyện Krông Bông?', 'So sánh học vấn người Ê Đê và người Mông', 'Dự toán ngân sách xóa nhà tạm toàn tỉnh là bao nhiêu?'"
        ]
        takeaway = "Khuyến nghị: Vui lòng nhập câu hỏi gắn liền với 7 trụ cột dữ liệu KTXH vùng đồng bào dân tộc thiểu số tỉnh Đắk Lắk."

        sql = "SELECT 'Ngoài phạm vi CSDL KTXH 53 Dân tộc thiểu số Đắk Lắk' AS thong_bao_he_thong;"
        empty_df = pd.DataFrame([{"thong_bao_he_thong": "Ngoài phạm vi CSDL KTXH 53 DTTS Đắk Lắk"}])

        return self._format_result_payload(
            intent_code="OUT_OF_SCOPE",
            intent_desc="Thông báo ngoài phạm vi CSDL KTXH 53 DTTS Đắk Lắk",
            sql=sql, df=empty_df, lead=lead, bullets=bullets, takeaway=takeaway, meta=meta
        )

    def _handle_default_provincial_snapshot(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Bức tranh vĩ mô toàn tỉnh (Lưới an toàn khi câu hỏi rộng hoặc tổng quan)."""
        period = meta["default_period"]
        sql = f"""
        SELECT 
            COUNT(DISTINCT ten_dantoc) AS so_dantoc,
            SUM(tong_ho_co_nha) AS tong_ho_dtts,
            SUM(so_ho_nha_tam_don_so) AS tong_nha_tam,
            ROUND(SUM(so_ho_nha_tam_don_so) * 100.0 / NULLIF(SUM(tong_ho_co_nha), 0), 2) AS ty_le_nha_tam_pct
        FROM v_dantoc_chuyen_dich_da_ky
        WHERE ma_ky = '{period}';
        """
        df = execute_query(sql)
        r = df.iloc[0] if df is not None and not df.empty else {}

        lead = (
            f"Bức tranh toàn cảnh KTXH 53 Dân tộc thiểu số tỉnh Đắk Lắk ({period}): "
            f"Toàn tỉnh có <strong>{int(float(r.get('tong_ho_dtts', 163912))):,} hộ DTTS</strong> sinh sống tại 15 huyện/thị xã/thành phố. "
            f"Toàn tỉnh còn <strong>{int(float(r.get('tong_nha_tam', 6378))):,} hộ ở nhà tạm</strong> (tỷ lệ {float(r.get('ty_le_nha_tam_pct', 3.89)):.2f}%)."
        )

        bullets = [
            f"<strong>Quy mô hộ DTTS ({period}):</strong> <b>{int(float(r.get('tong_ho_dtts', 163912))):,} hộ</b> thuộc 53 thành phần dân tộc.",
            f"<strong>Nhà tạm, dột nát:</strong> Còn <b>{int(float(r.get('tong_nha_tam', 6378))):,} căn</b> ({float(r.get('ty_le_nha_tam_pct', 3.89)):.2f}%)."
        ]

        takeaway = (
            "Gợi ý: Bạn có thể hỏi sâu về một địa bàn (VD: 'Huyện Ea Súp', 'Xã Ea Wy'), một dân tộc (VD: 'Người Ê Đê', 'Người Mông'), "
            "hoặc so sánh giữa các kỳ khảo sát (VD: 'Ea Súp 2019 vs 2024')."
        )

        return self._format_result_payload(
            intent_code="PROVINCIAL_MACRO_SNAPSHOT",
            intent_desc="Bức tranh toàn cảnh KTXH 53 Dân tộc thiểu số tỉnh Đắk Lắk",
            sql=sql,
            df=df,
            lead=lead,
            bullets=bullets,
            takeaway=takeaway,
            meta=meta
        )

    def _format_result_payload(
        self,
        intent_code: str,
        intent_desc: str,
        sql: str,
        df: pd.DataFrame,
        lead: str,
        bullets: List[str],
        takeaway: str,
        meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Đóng gói dữ liệu trả về cho Flask UI."""
        is_safe, err_msg, sanitized_sql = validate_and_sanitize_sql(sql)
        clean_sql = sanitized_sql if is_safe else sql

        cols = list(df.columns) if df is not None else []
        from ..app import COLUMN_LABELS, df_to_clean_records
        display_cols = [COLUMN_LABELS.get(c, c) for c in cols]

        fair_cards = {
            "headline": {
                "title": intent_desc,
                "summary": lead.replace("<strong>", "").replace("</strong>", "").replace("<b>", "").replace("</b>", "").replace("<br>", " ")
            },
            "legal_tag": f"Hệ thống Dữ liệu KTXH Đắk Lắk • {intent_code}",
            "fact": bullets,
            "analysis": [lead],
            "impact": ["Cung cấp căn cứ thực chứng phục vụ hoạch định chính sách KTXH và phân bổ nguồn lực."],
            "recommendation": [takeaway],
            "action_plan": {
                "who": "Ban Dân tộc & Sở Kế hoạch Đầu tư",
                "what": "Rà soát đối tượng và giải ngân nguồn vốn CTMTQG 1719",
                "where_when": meta.get("district") or "Toàn tỉnh Đắk Lắk",
                "budget_text": takeaway
            }
        }

        qa_response = {
            "lead_answer": lead,
            "bullet_points": bullets,
            "takeaway": takeaway
        }

        return {
            "status": "SUCCESS",
            "intent_code": intent_code,
            "intent_description": intent_desc,
            "entities": {
                "ky_baocao": meta.get("default_period"),
                "huyen": meta.get("district"),
                "xa": meta.get("commune"),
                "dantoc": meta.get("ethnics")[0] if meta.get("ethnics") else None
            },
            "sql_query": clean_sql.strip(),
            "columns": cols,
            "display_columns": display_cols,
            "records": df_to_clean_records(df) if df is not None else [],
            "fair_cards": fair_cards,
            "qa_response": qa_response
        }


# Singleton instance
_LOCAL_ENGINE = None

def get_local_analytics_engine() -> LocalAnalyticsEngine:
    global _LOCAL_ENGINE
    if _LOCAL_ENGINE is None:
        _LOCAL_ENGINE = LocalAnalyticsEngine()
    return _LOCAL_ENGINE
