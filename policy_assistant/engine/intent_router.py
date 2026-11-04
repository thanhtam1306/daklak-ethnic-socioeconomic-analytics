"""
==============================================================================
MODULE: DETERMINISTIC INTENT ROUTER & ENTITY EXTRACTOR
File: policy_assistant/engine/intent_router.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

import os
import re
import json
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from ..core.catalog import DISTRICT_ALIASES, ETHNIC_GROUPS, METRIC_CATALOG


def remove_accents(input_str: str) -> str:
    """Loại bỏ dấu tiếng Việt để đối chiếu alias không phân biệt dấu và hoa thường."""
    if not input_str:
        return ""
    # Chuyển đổi đ/Đ thành d/D vì NFKD không tách dấu gạch ngang của chữ đ
    s = input_str.replace("đ", "d").replace("Đ", "D")
    nfkd_form = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()


@dataclass
class ExtractedEntities:
    """Các thực thể nghiệp vụ được bóc tách từ câu hỏi."""
    ky_baocao: str = "KY_2026"  # Mặc định kỳ mới nhất 2026-2030
    so_sanh_da_ky: bool = False  # Cờ so sánh chuỗi thời gian 3 kỳ
    huyen: Optional[str] = None
    ma_huyen: Optional[str] = None
    xa: Optional[str] = None
    ma_xa: Optional[str] = None
    dantoc: Optional[str] = None
    ma_dantoc: Optional[str] = None
    dantoc_list: List[str] = field(default_factory=list)
    is_comparison: bool = False
    is_commune_query: bool = False
    metric_keys: List[str] = field(default_factory=list)
    limit: int = 10
    sort_order: str = "DESC"  # DESC | ASC
    nhom_dantoc_dac_thu: Optional[str] = None  # 'chơ ro' | 'bản địa' | 'di cư'
    guide_topic: Optional[str] = None  # 'general' | 'page_1' | 'page_2' | 'page_3' | 'page_4' | 'formulas_dax'


@dataclass
class PolicyIntent:
    """Ý định nghiệp vụ được định tuyến."""
    intent_code: str
    intent_description: str
    target_view_or_table: str
    entities: ExtractedEntities
    confidence: float = 1.0


# Bộ nhớ đệm danh mục 146 xã
_COMMUNES_CACHE: Optional[List[Dict[str, str]]] = None


def get_communes_catalog() -> List[Dict[str, str]]:
    """Tải và lưu cache danh mục 146 xã từ file JSON hoặc CSDL."""
    global _COMMUNES_CACHE
    if _COMMUNES_CACHE is None:
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "communes_list.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    _COMMUNES_CACHE = json.load(f)
            except Exception:
                _COMMUNES_CACHE = []
        else:
            _COMMUNES_CACHE = []
    return _COMMUNES_CACHE


def extract_period(question_raw: str) -> Tuple[str, bool]:
    """
    Xác định chu kỳ báo cáo và cờ so sánh đa kỳ:
    - Nhắc đến 2019 -> KY_2019
    - Nhắc đến 2024 -> KY_2024
    - Nhắc đến 2026 hoặc hiện nay/hiện tại/mới nhất -> KY_2026
    - Nhắc đến 'qua các kỳ', 'đa kỳ', 'biến động', 'xu hướng', '3 kỳ' -> multi-period comparison
    """
    q_norm = question_raw.lower()
    multi_period = False

    if any(k in q_norm for k in ["qua các kỳ", "đa kỳ", "ba kỳ", "3 kỳ", "biến động", "xu hướng", "chuyển dịch", "so với kỳ trước", "lịch sử"]):
        multi_period = True

    if "2019" in q_norm:
        return "KY_2019", multi_period
    elif "2024" in q_norm:
        return "KY_2024", multi_period
    elif "2026" in q_norm or "2030" in q_norm:
        return "KY_2026", multi_period
    
    # Mặc định kỳ mới nhất 2026
    return "KY_2026", multi_period


def extract_district(question_raw: str) -> Optional[str]:
    """Nhận diện tên huyện/thị xã/thành phố từ câu hỏi."""
    q_clean = question_raw.lower()
    q_no_accent = remove_accents(q_clean)

    # Loại bỏ cụm từ 'tinh dak lak', 'dak lak' để tránh chữ 'lak' khớp nhầm thành 'Huyện Lắk'
    q_no_accent = re.sub(r"\b(tinh\s+)?dak\s*lak\b", " ", q_no_accent)

    # Ưu tiên tìm khớp các alias dài trước để tránh khớp nhầm
    sorted_aliases = sorted(DISTRICT_ALIASES.keys(), key=lambda x: len(x), reverse=True)
    for alias in sorted_aliases:
        alias_no_accent = remove_accents(alias)
        # Khớp có ranh giới từ hoặc cụm từ
        pattern = r"\b" + re.escape(alias_no_accent) + r"\b"
        if re.search(pattern, q_no_accent):
            return DISTRICT_ALIASES[alias]

    return None


def extract_commune(question_raw: str, selected_district: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Nhận diện tên xã/phường/thị trấn từ danh mục 146 xã."""
    communes = get_communes_catalog()
    if not communes:
        return None

    q_clean = question_raw.lower()
    q_no_accent = remove_accents(q_clean)

    # 1. Nếu câu hỏi có cấu trúc rõ ràng "xã <tên>" hoặc "phường <tên>" hoặc "thị trấn <tên>"
    match_xa_prefix = re.search(r"\b(xa|phuong|thi tran)\s+([a-z0-9'\s]+?)(?=\s+(huyen|thi xa|tp|thanh pho|tinh|\?|,|\.|$))", q_no_accent)
    if match_xa_prefix:
        extracted_name = match_xa_prefix.group(2).strip()
        for c in communes:
            c_name_clean = c.get("ten_xa", "").replace("Xã", "").replace("Phường", "").replace("Thị trấn", "").strip().lower()
            if remove_accents(c_name_clean) == extracted_name:
                return c

    # 2. Loại bỏ tên huyện có tiền tố để tránh nhầm xã trùng tên huyện (như Huyện Ea H'leo vs Xã Ea H'leo)
    search_text = q_no_accent
    if selected_district:
        dist_no_acc = remove_accents(selected_district).replace("huyen ", "").replace("thi xa ", "").replace("tp. ", "").replace("tp ", "").strip()
        search_text = re.sub(r"\b(huyen|thi xa|tp|thanh pho)\s+" + re.escape(dist_no_acc) + r"\b", " ", search_text)

    # Lọc danh sách xã (nếu đã biết huyện thì ưu tiên tìm trong huyện đó)
    candidate_communes = communes
    if selected_district:
        matched_in_district = [c for c in communes if c.get("ten_huyen", "").lower() == selected_district.lower()]
        if matched_in_district:
            candidate_communes = matched_in_district + [c for c in communes if c not in matched_in_district]

    # Sắp xếp theo độ dài tên xã giảm dần
    for c in sorted(candidate_communes, key=lambda x: len(x.get("ten_xa", "")), reverse=True):
        ten_xa = c.get("ten_xa", "")
        ten_xa_clean = ten_xa.replace("Xã", "").replace("Phường", "").replace("Thị trấn", "").strip().lower()
        ten_xa_no_accent = remove_accents(ten_xa_clean)

        # Tránh các từ quá ngắn như 'ea', 'cư' gây dương tính giả
        if len(ten_xa_no_accent) < 4:
            continue

        pattern = r"\b" + re.escape(ten_xa_no_accent) + r"\b"
        if re.search(pattern, search_text):
            return c

    return None


def extract_ethnic_groups(question_raw: str) -> List[Dict[str, Any]]:
    """Nhận diện TOÀN BỘ các dân tộc thiểu số được nhắc đến trong câu hỏi (hỗ trợ so sánh đa dân tộc)."""
    q_clean = question_raw.lower().strip()
    q_no_accent = remove_accents(q_clean)

    ambiguous_single_words = {
        "mạ", "mảng", "cống", "thổ", "co", "lự", "ngái", "bố y", "hoa", "lào", "chứt", "si la", "la ha"
    }

    q_clean_filtered = re.sub(
        r"\b(trạng thái|sinh thái|thái độ|biến thái|hình thái|chăm sóc|chăm lo|chăm chỉ|con dao|dao động|ca dao)\b",
        " ",
        q_clean,
    )

    sorted_ethnics = sorted(ETHNIC_GROUPS.keys(), key=lambda x: len(x), reverse=True)
    found = []
    seen_names = set()

    # Bước 1: Khớp khi có tiền tố tường minh (dân tộc / đồng bào / người / hộ <tên dân tộc>)
    for eth_key in sorted_ethnics:
        pattern_accent = r"\b(dân tộc|đồng bào|người|cộng đồng|hộ)\s+" + re.escape(eth_key) + r"\b"
        eth_no_acc = remove_accents(eth_key)
        pattern_no_acc = r"\b(dan toc|dong bao|nguoi|cong dong)\s+" + re.escape(eth_no_acc) + r"\b"
        if re.search(pattern_accent, q_clean) or re.search(pattern_no_acc, q_no_accent):
            res = ETHNIC_GROUPS[eth_key].copy()
            res["key"] = eth_key
            name_chuan = res.get("ten_chuan")
            if name_chuan not in seen_names:
                found.append(res)
                seen_names.add(name_chuan)

    # Bước 2: Khớp chính xác có dấu tiếng Việt
    for eth_key in sorted_ethnics:
        if eth_key in ambiguous_single_words and q_clean != eth_key:
            continue
        pattern = r"\b" + re.escape(eth_key) + r"\b"
        if re.search(pattern, q_clean_filtered):
            res = ETHNIC_GROUPS[eth_key].copy()
            res["key"] = eth_key
            name_chuan = res.get("ten_chuan")
            if name_chuan not in seen_names:
                found.append(res)
                seen_names.add(name_chuan)

    # Bước 3: Khớp không dấu cho các tên dân tộc đa âm tiết đặc trưng
    unambiguous_unaccented_keys = {
        "ê đê", "ede", "e de", "m'nông", "mnông", "mnong", "m nong",
        "gia rai", "jarai", "jrai", "chơ ro", "choro", "xơ đăng", "xodang",
        "khơ mú", "khomu", "h'mông", "hmông", "hmong", "sán chay", "sán dìu",
        "bru - vân kiều", "bru vân kiều", "vân kiều", "pà thẻn", "cơ ho", "cơ tu",
        "tà ôi", "hà nhì", "la chí", "la hủ", "phù lá", "pu péo", "rơ măm",
        "brâu", "xtiêng", "raglai", "ra glai", "khmer", "khơ me", "cờ lao", "lô lô", "hrê"
    }
    for eth_key in sorted_ethnics:
        if eth_key not in unambiguous_unaccented_keys:
            continue
        eth_no_accent = remove_accents(eth_key)
        pattern = r"\b" + re.escape(eth_no_accent) + r"\b"
        if re.search(pattern, q_no_accent):
            res = ETHNIC_GROUPS[eth_key].copy()
            res["key"] = eth_key
            name_chuan = res.get("ten_chuan")
            if name_chuan not in seen_names:
                found.append(res)
                seen_names.add(name_chuan)

    return found


def extract_ethnic_group(question_raw: str) -> Optional[Dict[str, Any]]:
    """Tương thích ngược: Lấy dân tộc đầu tiên."""
    groups = extract_ethnic_groups(question_raw)
    return groups[0] if groups else None


def extract_limit_and_order(question_raw: str) -> Tuple[int, str]:
    """Trích xuất giới hạn dòng (Top N) và thứ tự sắp xếp (cao nhất / thấp nhất)."""
    q_clean = question_raw.lower()
    
    # 1. Trích xuất top N
    limit = 10  # Mặc định
    match_top = re.search(r"\btop\s*(\d+)\b", q_clean)
    if match_top:
        limit = int(match_top.group(1))
    elif any(k in q_clean for k in ["danh sách các xã", "toàn bộ các xã", "tất cả"]):
        limit = 50

    # 2. Trích xuất thứ tự
    sort_order = "DESC"
    if any(k in q_clean for k in ["thấp nhất", "ít nhất", "giảm mạnh nhất", "tốt nhất", "tiến bộ nhất"]):
        sort_order = "ASC"
    elif any(k in q_clean for k in ["cao nhất", "nhiều nhất", "nặng nhất", "nghiêm trọng nhất", "lớn nhất"]):
        sort_order = "DESC"

    return limit, sort_order


def route_policy_intent(question: str) -> PolicyIntent:
    """
    Phân tích câu hỏi tự nhiên tiếng Việt và định tuyến vào Intent nghiệp vụ chính xác.
    Đảm bảo 100% tính tất định (Deterministic), bóc tách đầy đủ thực thể và chỉ tiêu.
    """
    q_clean = question.strip()
    q_norm = q_clean.lower()
    q_no_accent = remove_accents(q_norm)

    # 1. Bóc tách các thực thể cơ sở
    period, multi_period = extract_period(q_clean)
    district = extract_district(q_clean)
    commune_info = extract_commune(q_clean, district)
    commune = commune_info.get("ten_xa") if commune_info else None
    if not district and commune_info:
        district = commune_info.get("ten_huyen")

    ethnic_groups = extract_ethnic_groups(q_clean)
    ethnic_names = [eg.get("ten_chuan") for eg in ethnic_groups if eg.get("ten_chuan")]
    ethnic_name = ethnic_names[0] if ethnic_names else None

    # Nhận diện cờ so sánh đối đầu và truy vấn cấp xã
    is_comparison = len(ethnic_names) >= 2 or any(k in q_no_accent for k in ["so sanh", "khac nhau", "khac gi", "doi chieu", "so voi", "hon kem", "ben nao"])
    is_commune_query = any(w in q_no_accent for w in ["xa ", "cac xa", "nhung xa", "xa nao", "thon", "buon", "dia phuong"])

    limit, sort_order = extract_limit_and_order(q_clean)

    entities = ExtractedEntities(
        ky_baocao=period,
        so_sanh_da_ky=multi_period,
        huyen=district,
        xa=commune,
        dantoc=ethnic_name,
        dantoc_list=ethnic_names,
        is_comparison=is_comparison,
        is_commune_query=is_commune_query,
        limit=limit,
        sort_order=sort_order
    )

    # =========================================================================
    # ƯU TIÊN ĐẶC BIỆT 1: CÂU HỎI VỀ CÁC XÃ TRONG MỘT HUYỆN (VD: XÃ KHÁT VỐN Ở KRÔNG BÔNG)
    # =========================================================================
    if district and is_commune_query and not commune and not any(k in q_no_accent for k in ["ma tuy", "hiv", "nghien", "te nan", "sinh con", "sinh tai nha", "nha tam", "khat von", "tin dung", "cmkt"]):
        entities.metric_keys.append("xa_trong_huyen")
        return PolicyIntent(
            intent_code="POVERTY_COMMUNE",
            intent_description=f"Danh sách và xếp hạng các xã khó khăn, nhu cầu vốn sinh kế tại {district}",
            target_view_or_table="v_xa_biendong_ngheo_da_ky",
            entities=entities
        )

    # =========================================================================
    # ƯU TIÊN ĐẶC BIỆT 2: SO SÁNH ĐỐI ĐẦU ĐA DÂN TỘC (VD: MNÔNG VS GIA RAI, Ê ĐÊ VS MÔNG)
    # =========================================================================
    if is_comparison and len(ethnic_names) >= 2:
        # 1. So sánh nhà ở & nhà tạm
        if any(k in q_no_accent for k in ["nha tam", "nha o", "dot nat", "don so", "kien co"]):
            entities.metric_keys.append("nha_tam")
            return PolicyIntent(
                intent_code="HOUSING_POVERTY",
                intent_description=f"So sánh thực trạng nhà tạm và điều kiện nhà ở giữa các dân tộc: {', '.join(ethnic_names)}",
                target_view_or_table="v_dantoc_chuyen_dich_da_ky",
                entities=entities
            )
        # 2. So sánh tháp tuổi / nhân khẩu học
        elif any(k in q_no_accent for k in ["thap tuoi", "thap dan so", "3 nhom tuoi", "co cau tuoi", "nhom tuoi", "tre em", "lao dong", "gia hoa", "phu thuoc", "0-14", "15-59", "60+"]):
            entities.guide_topic = "age_pyramid"
            return PolicyIntent(
                intent_code="DEMOGRAPHIC_COMPARISON",
                intent_description=f"So sánh cơ cấu tháp tuổi và nhân khẩu học giữa các dân tộc: {', '.join(ethnic_names)}",
                target_view_or_table="fact_nhankhau_dantoc",
                entities=entities
            )
        # 3. So sánh lao động / học vấn / việc làm
        elif any(k in q_no_accent for k in ["lao dong", "viec lam", "dao tao", "cmkt", "hoc van", "mu chu", "biet chu", "nong nghiep"]):
            entities.metric_keys.append("chua_dao_tao")
            return PolicyIntent(
                intent_code="LABOR_EDUCATION",
                intent_description=f"So sánh chất lượng lao động và giáo dục giữa các dân tộc: {', '.join(ethnic_names)}",
                target_view_or_table="v_dantoc_chuyen_dich_da_ky",
                entities=entities
            )
        # 4. So sánh tín dụng & đất sản xuất
        elif any(k in q_no_accent for k in ["khat von", "vay von", "tin dung", "nhcsxh", "dat"]):
            entities.metric_keys.append("khat_von")
            return PolicyIntent(
                intent_code="CREDIT_LAND",
                intent_description=f"So sánh nhu cầu vốn vay và đất sản xuất giữa các dân tộc: {', '.join(ethnic_names)}",
                target_view_or_table="v_dantoc_chuyen_dich_da_ky",
                entities=entities
            )
        # 5. So sánh tổng hợp
        else:
            return PolicyIntent(
                intent_code="COMPARATIVE_ANALYTICS",
                intent_description=f"So sánh tổng quan các chỉ số KTXH giữa các dân tộc: {', '.join(ethnic_names)}",
                target_view_or_table="v_dantoc_chuyen_dich_da_ky",
                entities=entities
            )

    # 2. Phân loại Ý định Nghiệp vụ (Intent Routing) theo thứ tự ưu tiên chuyên đề

    # INTENT 0: DASHBOARD_GUIDE (Hướng dẫn sử dụng Power BI Dashboard, cấu trúc 4 trang & Giải thích công thức tính chỉ số / DAX)
    guide_keywords = [
        "powerbi", "power bi", "dashboard", "trang 1", "trang 2", "trang 3", "trang 4",
        "may trang", "co nhung trang nao", "gom nhung trang nao", "cach su dung", "huong dan",
        "cach dung", "cach doc", "cach xem", "bo loc", "slicer", "loc cheo", "cross filter",
        "drill down", "drilldown", "cong thuc tinh", "cach tinh", "phuong phap tinh",
        "tinh the nao", "tinh nhu the nao", "y nghia chi so", "giai thich chi so",
        "cong don", "cong trung", "4 goc phan tu", "goc phan tu", "xa kho khan kep", "khung hanh dong",
        "bay trinh do", "bay cmkt", "nghich ly gioi", "nghich ly ve sinh"
    ]
    # Chỉ vào DASHBOARD_GUIDE nếu không hỏi số liệu cụ thể của dân tộc hoặc địa bàn
    is_pure_guide = any(k in q_no_accent for k in guide_keywords)
    if is_pure_guide and not is_comparison and not (ethnic_name and any(w in q_no_accent for w in ["so sanh", "khac nhau", "bao nhieu", "the nao", "tai sao", "vi sao"])):
        target_table = "v_tong_hop_ngan_sach_chinh_sach_ky"
        # 1. Tháp tuổi & Cơ cấu 3 nhóm tuổi (Demographic Age Pyramid)
        if any(p in q_no_accent for p in ["thap tuoi", "thap dan so", "3 nhom tuoi", "co cau tuoi", "nhom tuoi", "gia hoa", "phu thuoc", "0-14", "15-59", "60+"]):
            entities.guide_topic = "age_pyramid"
            target_table = "fact_nhankhau_dantoc"
        # 2. Treemap Phân bố dân số cấp huyện & dân tộc
        elif any(p in q_no_accent for p in ["treemap", "phan bo dan so", "phan bo dan cu", "mat do dan so"]):
            entities.guide_topic = "treemap_pop"
            target_table = "fact_danso_huyen_dantoc"
        # 3. Chống cộng dồn 3 kỳ
        elif any(p in q_no_accent for p in ["cong don", "cong trung", "triple", "473.755", "selected period", "khoa ky"]):
            entities.guide_topic = "anti_triple_count"
            target_table = "v_tong_hop_ngan_sach_chinh_sach_ky"
        # 4. Slicer & Bộ lọc chéo
        elif any(p in q_no_accent for p in ["bo loc", "slicer", "loc cheo", "cross filter", "cach loc", "drill down", "drilldown"]):
            entities.guide_topic = "slicer_filter"
            target_table = "v_tong_hop_ngan_sach_chinh_sach_ky"
        # 5. Ma trận 4 Góc phần tư (Khoảng cách vs Tỷ lệ nghèo)
        elif any(p in q_no_accent for p in ["4 goc phan tu", "goc phan tu", "xa kho khan kep", "bay cu ly"]):
            entities.guide_topic = "quadrant_chart"
            target_table = "v_xa_biendong_ngheo_da_ky"
        # 6. Hộp Khung hành động chính sách động
        elif any(p in q_no_accent for p in ["khung hanh dong", "dynamic policy", "hop khuyen nghi", "hop tham muu"]):
            entities.guide_topic = "dynamic_dax_card"
            target_table = "v_tong_hop_ngan_sach_chinh_sach_ky"
        # 7. Bẫy trình độ chuyên môn kỹ thuật & Ma trận kỹ năng
        elif any(p in q_no_accent for p in ["bay trinh do", "bay cmkt", "chua qua dao tao", "ma tran ky nang"]):
            entities.guide_topic = "labor_skill_trap"
            target_table = "v_dantoc_chuyen_dich_da_ky"
        # 8. Nghịch lý giới trong giáo dục
        elif any(p in q_no_accent for p in ["nghich ly gioi", "khoang cach gioi", "mau he", "phu he"]):
            entities.guide_topic = "gender_paradox"
            target_table = "v_dantoc_chuyen_dich_da_ky"
        # 9. Nghịch lý vệ sinh môi trường NTM
        elif any(p in q_no_accent for p in ["nghich ly ve sinh", "cong nghe di truoc ve sinh", "diem trung ve sinh"]):
            entities.guide_topic = "sanitation_paradox"
            target_table = "v_huyen_vesinh_chuyendoiso_da_ky"
        # 10. Các trang cụ thể
        elif re.search(r"\btrang\s*(1|mot)\b", q_no_accent) or any(p in q_no_accent for p in ["dan so & dia ban", "dan so va dia ban"]):
            entities.guide_topic = "page_1"
            target_table = "fact_nhankhau_dantoc"
        elif re.search(r"\btrang\s*(2|hai)\b", q_no_accent) or any(p in q_no_accent for p in ["hoc van & viec lam", "hoc van va viec lam"]):
            entities.guide_topic = "page_2"
            target_table = "v_dantoc_chuyen_dich_da_ky"
        elif re.search(r"\btrang\s*(3|ba)\b", q_no_accent) or any(p in q_no_accent for p in ["dieu kien song"]):
            entities.guide_topic = "page_3"
            target_table = "v_huyen_vesinh_chuyendoiso_da_ky"
        elif re.search(r"\btrang\s*(4|bon|tu)\b", q_no_accent) or any(p in q_no_accent for p in ["uu tien chinh sach"]):
            entities.guide_topic = "page_4"
            target_table = "v_tong_hop_ngan_sach_chinh_sach_ky"
        elif any(p in q_no_accent for p in ["cong thuc", "cach tinh", "phuong phap tinh", "tinh the nao", "dax", "dinh muc", "y nghia chi so", "giai thich chi so"]):
            entities.guide_topic = "formulas_dax"
            target_table = "v_tong_hop_ngan_sach_chinh_sach_ky"
        else:
            entities.guide_topic = "general"
            target_table = "v_tong_hop_ngan_sach_chinh_sach_ky"

        return PolicyIntent(
            intent_code="DASHBOARD_GUIDE",
            intent_description="Hướng dẫn khai thác Hệ thống Báo cáo Power BI (4 Trang) & Giải thích Phương pháp tính Chỉ số / DAX",
            target_view_or_table=target_table,
            entities=entities
        )

    # INTENT 1: POLICY_BUDGET (Dự toán ngân sách, kinh phí, đầu tư công)
    is_pop_distribution = any(w in q_no_accent for w in ["phan bo dan so", "phan bo dan cu", "phan bo dia ban", "phan bo 15 huyen"])
    budget_keywords = ["ngan sach", "kinh phi", "du toan", "dinh muc", "dau tu cong", "trieu dong", "ty dong", "giai ngan", "goi von", "chi phi"]
    is_budget_query = any(k in q_no_accent for k in budget_keywords) or (
        ("phan bo" in q_no_accent or "phan chia" in q_no_accent)
        and not is_pop_distribution
        and any(w in q_no_accent for w in ["von", "tien", "nguon luc", "chinh sach", "1719", "ngan sach", "kinh phi"])
    )
    if is_budget_query and not (district and not any(w in q_no_accent for w in ["ngan sach", "kinh phi", "du toan"])):
        entities.metric_keys.append("ngan_sach")
        return PolicyIntent(
            intent_code="POLICY_BUDGET",
            intent_description="Dự toán nhu cầu ngân sách đầu tư công và cơ chế phân bổ nguồn lực chính sách",
            target_view_or_table="v_tong_hop_ngan_sach_chinh_sach_ky",
            entities=entities
        )

    # INTENT 2: VULNERABILITY_HEALTH (Điểm nóng tệ nạn Ma túy, HIV và Y tế sinh sản / sinh tại nhà)
    health_keywords = ["ma tuy", "nghien", "hiv", "aids", "sinh tai nha", "sinh con tai nha", "te nan", "ba do", "y te sinh san"]
    if any(k in q_no_accent for k in health_keywords):
        if "sinh" in q_no_accent:
            entities.metric_keys.append("sinh_tai_nha")
        if any(k in q_no_accent for k in ["ma tuy", "nghien", "hiv", "aids", "te nan"]):
            entities.metric_keys.append("ma_tuy_hiv")
        return PolicyIntent(
            intent_code="VULNERABILITY_HEALTH",
            intent_description="Giám sát điểm nóng an ninh trật tự (ma túy, HIV) và rủi ro y tế sinh sản vùng DTTS",
            target_view_or_table="v_diemnong_anninh_yte_da_ky",
            entities=entities
        )

    # INTENT 3: HOUSING_POVERTY (Nhà tạm, nhà dột nát, phong trào xóa nhà tạm)
    housing_keywords = ["nha tam", "dot nat", "don so", "xoa nha tam", "nha o", "nha thieu kien co", "nha kien co"]
    if any(k in q_no_accent for k in housing_keywords):
        entities.metric_keys.append("nha_tam")
        return PolicyIntent(
            intent_code="HOUSING_POVERTY",
            intent_description="Thực trạng nhà tạm, nhà dột nát và tiến độ triển khai Dự án 1 - CTMTQG 1719",
            target_view_or_table="v_dantoc_chuyen_dich_da_ky" if ethnic_name else "fact_nhao_dantoc",
            entities=entities
        )

    # INTENT 4: SANITATION_DIGITAL (Tiêu chí 17 Nông thôn mới - Hố xí HVS và Chuyển đổi số Đề án 06)
    sanitation_keywords = ["ho xi", "ve sinh", "tieu chi 17", "ntm", "nong thon moi", "nuoc sach", "nuoc hvs", "internet", "mang", "chuyen doi so", "de an 06", "so hoa"]
    if any(k in q_no_accent for k in sanitation_keywords):
        if any(k in q_no_accent for k in ["ho xi", "ve sinh", "tieu chi 17", "nuoc"]):
            entities.metric_keys.append("ho_xi_hvs")
        if any(k in q_no_accent for k in ["internet", "chuyen doi so", "de an 06"]):
            entities.metric_keys.append("chuyen_doi_so")
        return PolicyIntent(
            intent_code="SANITATION_DIGITAL",
            intent_description="Đánh giá thực hiện Tiêu chí 17 NTM (Hố xí HVS) và tiếp cận Internet Đề án 06",
            target_view_or_table="v_huyen_vesinh_chuyendoiso_da_ky",
            entities=entities
        )

    # INTENT 5: CREDIT_LAND (Khoảng trống tín dụng, khát vốn vay ưu đãi và thiếu đất canh tác)
    credit_land_keywords = ["khat von", "vay von", "tin dung", "ngan hang chinh sach", "nhcsxh", "nghi dinh 28", "dat canh tac", "dat san xuat", "thieu dat"]
    if any(k in q_no_accent for k in credit_land_keywords):
        if any(k in q_no_accent for k in ["von", "vay", "tin dung", "nhcsxh"]):
            entities.metric_keys.append("khat_von")
        if "dat" in q_no_accent:
            entities.metric_keys.append("dat_san_xuat")
        return PolicyIntent(
            intent_code="CREDIT_LAND",
            intent_description="Khoảng trống tín dụng chính sách ưu đãi và bất bình đẳng tư liệu đất sản xuất",
            target_view_or_table="v_dantoc_chuyen_dich_da_ky",
            entities=entities
        )

    # INTENT 6: LABOR_EDUCATION (Lao động chưa qua đào tạo, việc làm, nông nghiệp, học vấn, bình đẳng giới)
    labor_edu_keywords = ["lao dong", "viec lam", "dao tao", "chua qua dao tao", "chung chi", "cmkt", "chuyen mon ky thuat", "hoc van", "biet chu", "mu chu", "nong nghiep", "mau he", "phu he", "du an 5"]
    if any(k in q_no_accent for k in labor_edu_keywords):
        if any(k in q_no_accent for k in ["mu chu", "biet chu", "hoc van", "xoa mu"]):
            entities.metric_keys.append("mu_chu")
        else:
            entities.metric_keys.append("chua_dao_tao")
        return PolicyIntent(
            intent_code="LABOR_EDUCATION",
            intent_description="Chất lượng vốn nhân lực, bẫy việc làm nông nghiệp và khoảng cách giáo dục giới tính",
            target_view_or_table="v_dantoc_chuyen_dich_da_ky",
            entities=entities
        )

    # INTENT 7: POVERTY_COMMUNE (Tỷ lệ nghèo, biến động nghèo cấp xã, dậm chân, tái nghèo, top nghèo)
    poverty_keywords = ["ngheo", "ho ngheo", "ty le ngheo", "giam ngheo", "tai ngheo", "dam chan", "kho khan", "vung sau", "xa ngheo"]
    if any(k in q_no_accent for k in poverty_keywords) or (commune and not any(k in q_no_accent for k in ["ma tuy", "hiv"])):
        entities.metric_keys.append("ty_le_ngheo")
        return PolicyIntent(
            intent_code="POVERTY_COMMUNE",
            intent_description="Thực trạng phân hóa nghèo đa chiều cấp xã, biến động bứt phá vs tái nghèo",
            target_view_or_table="v_xa_biendong_ngheo_da_ky",
            entities=entities
        )

    # INTENT 8: ETHNIC_OVERVIEW (Hỏi tổng quan về một dân tộc thiểu số cụ thể)
    if ethnic_name and not district:
        return PolicyIntent(
            intent_code="ETHNIC_OVERVIEW",
            intent_description=f"Hồ sơ chuyển dịch kinh tế - xã hội tổng hợp dân tộc thiểu số {ethnic_name}",
            target_view_or_table="v_dantoc_chuyen_dich_da_ky",
            entities=entities
        )

    # INTENT 9: DISTRICT_OVERVIEW (Hỏi tổng quan về một huyện cụ thể)
    if district:
        return PolicyIntent(
            intent_code="DISTRICT_OVERVIEW",
            intent_description=f"Báo cáo giám sát kinh tế - xã hội và hạ tầng vùng DTTS {district}",
            target_view_or_table="v_huyen_vesinh_chuyendoiso_da_ky",
            entities=entities
        )

    # INTENT 10: DEFAULT_MACRO_OVERVIEW (Toàn cảnh KTXH tỉnh)
    return PolicyIntent(
        intent_code="DEFAULT_MACRO_OVERVIEW",
        intent_description="Bức tranh toàn cảnh kinh tế - xã hội và tiến độ các Chương trình MTQG tỉnh Đắk Lắk",
        target_view_or_table="v_xa_biendong_ngheo_da_ky",
        entities=entities
    )
