"""
==============================================================================
MODULE: SEMANTIC METRIC & POLICY CATALOG (Từ Điển Nghiệp Vụ & Định Mức Ngân Sách)
File: policy_assistant/core/catalog.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

from typing import Dict, Any, List

# 1. BẢNG TỪ ĐIỂN CHỈ TIÊU KTXH & CHÍNH SÁCH
METRIC_CATALOG: Dict[str, Dict[str, Any]] = {
    "ty_le_ngheo": {
        "ten": "Tỷ lệ hộ nghèo bình quân",
        "don_vi": "%",
        "benchmark_muc_tieu": 15.0,
        "huong_tot": "giam",
        "bang_chinh": "v_xa_biendong_ngheo_da_ky",
        "cot": "ty_le_ngheo_pct",
        "cot_bien_dong": "chenh_lech_ky_truoc_pp",
        "phap_ly": "Chuẩn nghèo đa chiều 2021-2025 & 2026-2030 (Nghị định 07/2021/NĐ-CP)",
        "mo_ta": "Tỷ lệ hộ nghèo DTTS bình quân tại 146 xã/phường/thị trấn trên địa bàn tỉnh Đắk Lắk."
    },
    "nha_tam": {
        "ten": "Số hộ ở nhà tạm, đơn sơ",
        "don_vi": "Hộ",
        "benchmark_muc_tieu": 0,
        "huong_tot": "giam",
        "bang_chinh": "v_dantoc_chuyen_dich_da_ky",
        "cot": "so_ho_nha_tam",
        "cot_bien_dong": "bien_dong_nha_tam",
        "phap_ly": "Chương trình MTQG 1719 (Dự án 1) & Phong trào 'Xóa nhà tạm, dột nát' toàn quốc",
        "mo_ta": "Số hộ DTTS đang sinh sống trong các căn nhà tạm bợ, dột nát, vách nứa, mái tranh thiếu kiên cố."
    },
    "ho_xi_hvs": {
        "ten": "Tỷ lệ hộ có hố xí hợp vệ sinh",
        "don_vi": "%",
        "benchmark_muc_tieu": 70.0,
        "huong_tot": "tang",
        "bang_chinh": "v_huyen_vesinh_chuyendoiso_da_ky",
        "cot": "ty_le_ho_xi_hvs_pct",
        "cot_bien_dong": "bien_dong_ho_xi_pp",
        "phap_ly": "Bộ tiêu chí Quốc gia về Xã Nông thôn mới (Tiêu chí số 17.5 - Quyết định 318/QĐ-TTg)",
        "mo_ta": "Tỷ lệ hộ DTTS có nhà tiêu tự hoại, bán tự hoại hoặc hố xí hợp vệ sinh theo quy chuẩn Bộ Y tế."
    },
    "khat_von": {
        "ten": "Số hộ DTTS có nhu cầu vay vốn nhưng chưa được vay",
        "don_vi": "Hộ",
        "benchmark_muc_tieu": 0,
        "huong_tot": "giam",
        "bang_chinh": "v_dantoc_chuyen_dich_da_ky",
        "cot": "so_ho_khat_von",
        "cot_bien_dong": "bien_dong_khat_von",
        "phap_ly": "Nghị định 28/2022/NĐ-CP về chính sách tín dụng ưu đãi qua Ngân hàng CSXH",
        "mo_ta": "Số hộ nghèo và cận nghèo DTTS đang cần vốn sản xuất kinh doanh nhưng chưa tiếp cận được nguồn vốn ưu đãi."
    },
    "chua_dao_tao": {
        "ten": "Tỷ lệ lao động DTTS chưa qua đào tạo chuyên môn kỹ thuật",
        "don_vi": "%",
        "benchmark_muc_tieu": 75.0,
        "huong_tot": "giam",
        "bang_chinh": "v_dantoc_chuyen_dich_da_ky",
        "cot": "ty_le_chua_dao_tao_pct",
        "cot_bien_dong": "bien_dong_chua_dao_tao_pp",
        "phap_ly": "Chương trình MTQG 1719 (Dự án 5: Phát triển giáo dục nghề nghiệp và giải quyết việc làm)",
        "mo_ta": "Tỷ lệ lao động DTTS trong độ tuổi làm việc không có bằng cấp hoặc chứng chỉ đào tạo nghề."
    },
    "sinh_tai_nha": {
        "ten": "Số ca sinh con tại nhà",
        "don_vi": "Ca",
        "benchmark_muc_tieu": 0,
        "huong_tot": "giam",
        "bang_chinh": "v_diemnong_anninh_yte_da_ky",
        "cot": "so_ca_sinh_tai_nha",
        "cot_bien_dong": "bien_dong_ca_sinh_tai_nha",
        "phap_ly": "Chương trình MTQG 1719 (Dự án 7: Chăm sóc sức khỏe nhân dân, nâng cao thể trạng, tầm vóc người DTTS)",
        "mo_ta": "Số phụ nữ DTTS sinh con tại nhà không có cán bộ y tế trợ giúp hoặc chỉ có người đỡ vườn."
    },
    "ma_tuy_hiv": {
        "ten": "Số người nghiện ma túy và nhiễm HIV",
        "don_vi": "Người",
        "benchmark_muc_tieu": 0,
        "huong_tot": "giam",
        "bang_chinh": "v_diemnong_anninh_yte_da_ky",
        "cot": "so_nguoi_nghien_ma_tuy",
        "cot_bien_dong": "bien_dong_nghien_ma_tuy",
        "phap_ly": "Kế hoạch số 118/KH-UBND tỉnh Đắk Lắk về phòng, chống tệ nạn xã hội vùng đồng bào DTTS",
        "mo_ta": "Số lượng người DTTS nghiện ma túy và nhiễm HIV đang được theo dõi, quản lý trên địa bàn cấp xã."
    },
    "chuyen_doi_so": {
        "ten": "Tỷ lệ hộ DTTS tiếp cận Internet băng rộng",
        "don_vi": "%",
        "benchmark_muc_tieu": 80.0,
        "huong_tot": "tang",
        "bang_chinh": "v_huyen_vesinh_chuyendoiso_da_ky",
        "cot": "ty_le_co_internet_pct",
        "cot_bien_dong": "bien_dong_internet_pp",
        "phap_ly": "Đề án 06/QĐ-TTg & Chiến lược Chuyển đổi số quốc gia đến năm 2025, định hướng 2030",
        "mo_ta": "Tỷ lệ hộ gia đình DTTS có kết nối cáp quang hoặc 4G/5G phục vụ giao dịch dịch vụ công trực tuyến."
    },
    "dat_san_xuat": {
        "ten": "Diện tích đất canh tác bình quân",
        "don_vi": "ha/hộ",
        "benchmark_muc_tieu": 0.50,
        "huong_tot": "tang",
        "bang_chinh": "v_dantoc_chuyen_dich_da_ky",
        "cot": "dat_san_xuat_ha_per_ho",
        "cot_bien_dong": "bien_dong_dat_sx",
        "phap_ly": "Chương trình MTQG 1719 (Dự án 1 - Giải quyết tình trạng thiếu đất ở, nhà ở, đất sản xuất, nước sinh hoạt)",
        "mo_ta": "Diện tích đất nông nghiệp bình quân của mỗi hộ DTTS để bảo đảm sinh kế tự chủ."
    }
}

# 2. BẢNG ĐƠN GIÁ ĐỊNH MỨC DỰ TOÁN NGÂN SÁCH NHÀ NƯỚC (Theo QĐ 1719, NĐ 28 & dim_chitieu_kehoach_ngansach)
BUDGET_STANDARDS: Dict[str, Dict[str, Any]] = {
    "NHA_TAM": {
        "ten_hang_muc": "Hỗ trợ xây mới/xóa nhà tạm dột nát",
        "don_gia_trieu_vnd": {
            "KY_2019": 60.0,
            "KY_2024": 80.0,
            "KY_2026": 90.0  # Nâng định mức theo QĐ mới giai đoạn 2026-2030
        },
        "don_vi_tinh": "Triệu VNĐ/hộ",
        "can_cu_phap_ly": "Chương trình MTQG 1719 (Dự án 1, Tiểu dự án 1)"
    },
    "HO_XI": {
        "ten_hang_muc": "Hỗ trợ xây dựng công trình hố xí hợp vệ sinh",
        "don_gia_trieu_vnd": {
            "KY_2019": 8.0,
            "KY_2024": 10.0,
            "KY_2026": 12.0
        },
        "don_vi_tinh": "Triệu VNĐ/công trình",
        "can_cu_phap_ly": "Tiêu chí 17 NTM & QĐ 1719 (Dự án 1)"
    },
    "TIN_DUNG": {
        "ten_hang_muc": "Gói hạn mức tín dụng chính sách ưu đãi sản xuất",
        "don_gia_trieu_vnd": {
            "KY_2019": 40.0,
            "KY_2024": 50.0,
            "KY_2026": 65.0
        },
        "don_vi_tinh": "Triệu VNĐ/hộ",
        "can_cu_phap_ly": "Nghị định số 28/2022/NĐ-CP ngày 26/4/2022"
    },
    "DAO_TAO_NGHE": {
        "ten_hang_muc": "Hỗ trợ đào tạo nghề và giải quyết việc làm",
        "don_gia_trieu_vnd": {
            "KY_2019": 3.5,
            "KY_2024": 4.5,
            "KY_2026": 6.0
        },
        "don_vi_tinh": "Triệu VNĐ/lao động",
        "can_cu_phap_ly": "Chương trình MTQG 1719 (Dự án 5)"
    },
    "Y_TE_SINH_SAN": {
        "ten_hang_muc": "Hỗ trợ gói chăm sóc thai sản, y tế buôn làng & hỗ trợ sinh an toàn",
        "don_gia_trieu_vnd": {
            "KY_2019": 2.0,
            "KY_2024": 3.0,
            "KY_2026": 4.5
        },
        "don_vi_tinh": "Triệu VNĐ/ca",
        "can_cu_phap_ly": "Chương trình MTQG 1719 (Dự án 7)"
    },
    "HO_NGHEO": {
        "ten_hang_muc": "Hỗ trợ phát triển sản xuất, đa dạng hóa sinh kế hộ nghèo",
        "don_gia_trieu_vnd": {
            "KY_2019": 15.0,
            "KY_2024": 25.0,
            "KY_2026": 30.0
        },
        "don_vi_tinh": "Triệu VNĐ/hộ",
        "can_cu_phap_ly": "Chương trình MTQG 1719 (Dự án 3)"
    }
}

# 3. DANH MỤC 15 ĐƠN VỊ HÀNH CHÍNH CẤP HUYỆN & BẢNG ÁNH XẠ ALIAS
DISTRICT_ALIASES: Dict[str, str] = {
    # Buôn Ma Thuột
    "bmt": "Thành phố Buôn Ma Thuột",
    "buôn ma thuột": "Thành phố Buôn Ma Thuột",
    "buon ma thuot": "Thành phố Buôn Ma Thuột",
    "tp buôn ma thuột": "Thành phố Buôn Ma Thuột",
    "tp. buôn ma thuột": "Thành phố Buôn Ma Thuột",
    "thành phố buôn ma thuột": "Thành phố Buôn Ma Thuột",
    "tp bmt": "Thành phố Buôn Ma Thuột",
    # Ea Súp
    "ea súp": "Huyện Ea Súp",
    "ea sup": "Huyện Ea Súp",
    "easup": "Huyện Ea Súp",
    # Krông Búk
    "krông búk": "Huyện Krông Búk",
    "krong buk": "Huyện Krông Búk",
    "krongbuk": "Huyện Krông Búk",
    # Krông Bông
    "krông bông": "Huyện Krông Bông",
    "krong bong": "Huyện Krông Bông",
    "krongbong": "Huyện Krông Bông",
    # Krông Năng
    "krông năng": "Huyện Krông Năng",
    "krong nang": "Huyện Krông Năng",
    "krongnang": "Huyện Krông Năng",
    # Krông Pắc
    "krông pắc": "Huyện Krông Pắc",
    "krong pac": "Huyện Krông Pắc",
    "krong pak": "Huyện Krông Pắc",
    "krongpak": "Huyện Krông Pắc",
    # Krông A Na
    "krông ana": "Huyện Krông A Na",
    "krong ana": "Huyện Krông A Na",
    "krông a na": "Huyện Krông A Na",
    "krong a na": "Huyện Krông A Na",
    "krongana": "Huyện Krông A Na",
    # Cư M'gar
    "cư m'gar": "Huyện Cư M'gar",
    "cu m'gar": "Huyện Cư M'gar",
    "cu mgar": "Huyện Cư M'gar",
    "cumgar": "Huyện Cư M'gar",
    # Ea H'leo
    "ea h'leo": "Huyện Ea H'leo",
    "ea hleo": "Huyện Ea H'leo",
    "eahleo": "Huyện Ea H'leo",
    # Ea Kar
    "ea kar": "Huyện Ea Kar",
    "eakar": "Huyện Ea Kar",
    # Lắk
    "lắk": "Huyện Lắk",
    "lak": "Huyện Lắk",
    # M'Đrắk
    "m'đrắk": "Huyện M'Đrắk",
    "m'drak": "Huyện M'Đrắk",
    "m đrắk": "Huyện M'Đrắk",
    "mdrak": "Huyện M'Đrắk",
    # Buôn Đôn
    "buôn đôn": "Huyện Buôn Đôn",
    "buon don": "Huyện Buôn Đôn",
    "buondon": "Huyện Buôn Đôn",
    # Cư Kuin
    "cư kuin": "Huyện Cư Kuin",
    "cu kuin": "Huyện Cư Kuin",
    "cukuin": "Huyện Cư Kuin",
    # TX. Buôn Hồ
    "buôn hồ": "Thị Xã Buôn Hồ",
    "buon ho": "Thị Xã Buôn Hồ",
    "tx buôn hồ": "Thị Xã Buôn Hồ",
    "thị xã buôn hồ": "Thị Xã Buôn Hồ",
    "tx buon ho": "Thị Xã Buôn Hồ"
}

# 4. DANH MỤC 53 DÂN TỘC THIỂU SỐ VÀ NHÓM NGUỒN GỐC
ETHNIC_GROUPS: Dict[str, Dict[str, Any]] = {
    "ê đê": {"ten_chuan": "Ê đê", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "êđê": {"ten_chuan": "Ê đê", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "m'nông": {"ten_chuan": "Mnông", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "mnông": {"ten_chuan": "Mnông", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "m nông": {"ten_chuan": "Mnông", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "gia rai": {"ten_chuan": "Gia Rai", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "jrai": {"ten_chuan": "Gia Rai", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "mông": {"ten_chuan": "Mông", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "h'mông": {"ten_chuan": "Mông", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "hmông": {"ten_chuan": "Mông", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "tày": {"ten_chuan": "Tày", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "nùng": {"ten_chuan": "Nùng", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "dao": {"ten_chuan": "Dao", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "thái": {"ten_chuan": "Thái", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "mường": {"ten_chuan": "Mường", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "xơ đăng": {"ten_chuan": "Xơ Đăng", "nhom": "Bản địa Tây Nguyên", "chu_mau": False},
    "chơ ro": {"ten_chuan": "Chơ Ro", "nhom": "Nam Bộ & Duyên hải", "chu_mau": False, "rat_it_nguoi": True},
    "bru vân kiều": {"ten_chuan": "Bru Vân Kiều", "nhom": "Bắc Trung Bộ", "chu_mau": False},
    "vân kiều": {"ten_chuan": "Bru Vân Kiều", "nhom": "Bắc Trung Bộ", "chu_mau": False},
    "hoa": {"ten_chuan": "Hoa", "nhom": "Khác", "chu_mau": False},
    "sán chay": {"ten_chuan": "Sán Chay", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "cao lan": {"ten_chuan": "Sán Chay", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "sán dìu": {"ten_chuan": "Sán Dìu", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "ba na": {"ten_chuan": "Ba Na", "nhom": "Bản địa Tây Nguyên", "chu_mau": False},
    "cơ ho": {"ten_chuan": "Cơ Ho", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "chăm": {"ten_chuan": "Chăm", "nhom": "Nam Bộ & Duyên hải", "chu_mau": True},
    "khmer": {"ten_chuan": "Khmer", "nhom": "Nam Bộ & Duyên hải", "chu_mau": False},
    "thổ": {"ten_chuan": "Thổ", "nhom": "Bắc Trung Bộ", "chu_mau": False},
    "giáy": {"ten_chuan": "Giáy", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "cơ tu": {"ten_chuan": "Cơ Tu", "nhom": "Bản địa Tây Nguyên", "chu_mau": False},
    "gié triêng": {"ten_chuan": "Gié Triêng", "nhom": "Bản địa Tây Nguyên", "chu_mau": False},
    "mạ": {"ten_chuan": "Mạ", "nhom": "Bản địa Tây Nguyên", "chu_mau": False},
    "khơ mú": {"ten_chuan": "Khơ mú", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "co": {"ten_chuan": "Co", "nhom": "Nam Bộ & Duyên hải", "chu_mau": False},
    "tà ôi": {"ten_chuan": "Tà Ôi", "nhom": "Bắc Trung Bộ", "chu_mau": False},
    "xtiêng": {"ten_chuan": "Xtiêng", "nhom": "Nam Bộ & Duyên hải", "chu_mau": False},
    "kháng": {"ten_chuan": "Kháng", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "xinh mun": {"ten_chuan": "Xinh Mun", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "hà nhì": {"ten_chuan": "Hà Nhì", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "chu ru": {"ten_chuan": "Chu Ru", "nhom": "Bản địa Tây Nguyên", "chu_mau": True},
    "lào": {"ten_chuan": "Lào", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "la chí": {"ten_chuan": "La Chí", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "la ha": {"ten_chuan": "La Ha", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "phù lá": {"ten_chuan": "Phù Lá", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "la hủ": {"ten_chuan": "La Hủ", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "lự": {"ten_chuan": "Lự", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "lô lô": {"ten_chuan": "Lô Lô", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "chứt": {"ten_chuan": "Chứt", "nhom": "Bắc Trung Bộ", "chu_mau": False},
    "mảng": {"ten_chuan": "Mảng", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "pà thẻn": {"ten_chuan": "Pà Thẻn", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "cơ lao": {"ten_chuan": "Cơ Lao", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "cống": {"ten_chuan": "Cống", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "bố y": {"ten_chuan": "Bố Y", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "si la": {"ten_chuan": "Si La", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "pu péo": {"ten_chuan": "Pu Péo", "nhom": "Di cư phía Bắc", "chu_mau": False},
    "rơ măm": {"ten_chuan": "Rơ Măm", "nhom": "Bản địa Tây Nguyên", "chu_mau": False},
    "brâu": {"ten_chuan": "Brâu", "nhom": "Bản địa Tây Nguyên", "chu_mau": False},
    "ơ đu": {"ten_chuan": "Ơ Đu", "nhom": "Bắc Trung Bộ", "chu_mau": False},
    "hrê": {"ten_chuan": "Hrê", "nhom": "Nam Bộ & Duyên hải", "chu_mau": False},
    "raglay": {"ten_chuan": "Raglay", "nhom": "Nam Bộ & Duyên hải", "chu_mau": True},
    "ngái": {"ten_chuan": "Ngái", "nhom": "Di cư phía Bắc", "chu_mau": False}
}

# 5. DANH MỤC 5 ANALYTICAL VIEWS ĐA KỲ
VIEWS_CATALOG: Dict[str, Dict[str, Any]] = {
    "v_xa_biendong_ngheo_da_ky": {
        "so_dong": 438,
        "khoa_chinh": ["ma_xa", "ma_ky"],
        "noi_dung": "Biến động tỷ lệ nghèo của 146 xã x 3 chu kỳ báo cáo, phân loại bứt phá vs tái nghèo."
    },
    "v_dantoc_chuyen_dich_da_ky": {
        "so_dong": 159,
        "khoa_chinh": ["ma_dantoc", "ma_ky"],
        "noi_dung": "Chuyển dịch 6 trụ cột KTXH của 53 DTTS (Nhà tạm, CMKT, Tín dụng, Nữ biết chữ, Lao động, Đất canh tác)."
    },
    "v_huyen_vesinh_chuyendoiso_da_ky": {
        "so_dong": 45,
        "khoa_chinh": ["ma_huyen", "ma_ky"],
        "noi_dung": "Tiêu chí 17 Nông thôn mới (hố xí HVS) và chỉ số chuyển đổi số (Internet, điện lưới) của 15 huyện qua 3 kỳ."
    },
    "v_diemnong_anninh_yte_da_ky": {
        "so_dong": 597,
        "khoa_chinh": ["ma_xa_hoac_ma_dantoc", "ma_ky"],
        "noi_dung": "Giám sát tệ nạn ma túy, HIV cấp xã và tình hình sinh con tại nhà của 53 dân tộc qua 3 kỳ."
    },
    "v_tong_hop_ngan_sach_chinh_sach_ky": {
        "so_dong": 15,
        "khoa_chinh": ["ma_ky", "linh_vuc_can_thiep"],
        "noi_dung": "Dự toán tổng hợp ngân sách đầu tư công theo đơn giá định mức QĐ 1719 & NĐ 28/2022/NĐ-CP qua 3 kỳ."
    }
}
