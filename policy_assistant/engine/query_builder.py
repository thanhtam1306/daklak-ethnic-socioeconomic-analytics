"""
==============================================================================
MODULE: POLICY SQL QUERY BUILDER (Dynamic Analytical Queries on Star Schema)
File: policy_assistant/engine/query_builder.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

import re
from typing import Dict, Any, Tuple
from .intent_router import PolicyIntent, ExtractedEntities


def escape_sql_string(val: str) -> str:
    """Xóa ký tự nguy hiểm và thoát dấu nháy đơn trong chuỗi tham số SQL."""
    if not val:
        return ""
    # Chỉ giữ lại chữ cái, số, khoảng trắng và ký tự tiếng Việt an toàn
    cleaned = val.replace("'", "''").strip()
    return cleaned


def build_policy_sql(intent: PolicyIntent) -> str:
    """
    Sinh câu truy vấn SQL an toàn, tối ưu trên 5 Analytical Views và Star Schema.
    Đảm bảo 100% tuân thủ tiêu chuẩn Read-Only và SQL Guardrails.
    """
    code = intent.intent_code
    e = intent.entities
    period = e.ky_baocao
    limit = max(1, min(e.limit, 100))
    sort_order = "ASC" if e.sort_order == "ASC" else "DESC"

    # ==========================================================================
    # 0. INTENT: DASHBOARD_GUIDE & DEMOGRAPHIC_COMPARISON
    # ==========================================================================
    if code in ("DEMOGRAPHIC_COMPARISON", "DASHBOARD_GUIDE"):
        topic = e.guide_topic or "general"
        if code == "DEMOGRAPHIC_COMPARISON" or topic == "age_pyramid":
            if e.dantoc_list and len(e.dantoc_list) >= 2:
                dt_where = "AND (" + " OR ".join([f"nk.ten_dantoc ILIKE '%{escape_sql_string(d)}%'" for d in e.dantoc_list]) + ")"
            elif e.dantoc:
                dt_where = f"AND nk.ten_dantoc ILIKE '%{escape_sql_string(e.dantoc)}%'"
            else:
                dt_where = ""
            sql = f"""
            SELECT 
                nk.ten_dantoc,
                nk.nhom_nguon_goc,
                nk.tong_dan_so,
                nk.dan_so_0_14,
                ROUND(nk.dan_so_0_14 * 100.0 / NULLIF(nk.tong_dan_so, 0), 1) AS ty_le_0_14_pct,
                nk.dan_so_15_59,
                ROUND(nk.dan_so_15_59 * 100.0 / NULLIF(nk.tong_dan_so, 0), 1) AS ty_le_15_59_pct,
                nk.dan_so_60_plus,
                ROUND(nk.dan_so_60_plus * 100.0 / NULLIF(nk.tong_dan_so, 0), 1) AS ty_le_60_plus_pct,
                ROUND(nk.dan_so_0_14 * 100.0 / NULLIF(nk.dan_so_15_59, 0), 1) AS ty_le_phu_thuoc_tre_em_pct,
                ROUND(nk.dan_so_60_plus * 100.0 / NULLIF(nk.dan_so_0_14, 0), 1) AS chi_so_gia_hoa_pct
            FROM fact_nhankhau_dantoc nk
            WHERE nk.ma_ky = '{period}' {dt_where}
            ORDER BY nk.tong_dan_so DESC
            LIMIT {limit}
            """
            return sql.strip()

        elif topic == "treemap_pop":
            sql = f"""
            SELECT 
                ds.ten_huyen,
                SUM(ds.so_ho) AS tong_ho_dtts,
                COUNT(DISTINCT ds.ma_dantoc) AS so_dantoc_sinh_song
            FROM fact_danso_huyen_dantoc ds
            WHERE ds.ma_ky = '{period}'
            GROUP BY ds.ten_huyen
            ORDER BY tong_ho_dtts DESC
            LIMIT {limit}
            """
            return sql.strip()

        elif topic == "quadrant_chart":
            sql = f"""
            SELECT 
                ten_xa, ten_huyen, km_den_trung_tam_huyen, ty_le_ngheo_pct, so_ho_ngheo,
                bien_dong_ty_le_ngheo_pct, du_toan_ngan_sach_sinh_ke_trieu_vnd
            FROM v_xa_biendong_ngheo_da_ky
            WHERE ma_ky = '{period}' AND km_den_trung_tam_huyen >= 15 AND ty_le_ngheo_pct >= 25
            ORDER BY km_den_trung_tam_huyen DESC, ty_le_ngheo_pct DESC
            LIMIT {limit}
            """
            return sql.strip()

        elif topic in ("labor_skill_trap", "gender_paradox", "page_2"):
            dt_where = f"AND ten_dantoc ILIKE '%{escape_sql_string(e.dantoc)}%'" if e.dantoc else ""
            sql = f"""
            SELECT 
                ten_dantoc, nhom_nguon_goc, tong_lao_dong, lao_dong_khong_cmkt, ty_le_khong_cmkt_pct,
                lao_dong_nong_nghiep, ty_le_nong_nghiep_pct, ty_le_nu_biet_chu_pct
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ma_ky = '{period}' {dt_where}
            ORDER BY tong_lao_dong DESC
            LIMIT {limit}
            """
            return sql.strip()

        elif topic in ("sanitation_paradox", "page_3"):
            sql = f"""
            SELECT 
                ten_huyen, tong_ho_dtts_huyen, ty_le_ho_xi_hvs_bq_pct, ty_le_nuoc_hvs_bq_pct,
                ty_le_internet_huyen_pct, trang_thai_ntm_tc17, trang_thai_chuyendoiso_dean06
            FROM v_huyen_vesinh_chuyendoiso_da_ky
            WHERE ma_ky = '{period}'
            ORDER BY ty_le_ho_xi_hvs_bq_pct ASC
            LIMIT {limit}
            """
            return sql.strip()

        else:
            # Topic formulas_dax, anti_triple_count, slicer_filter, dynamic_dax_card, page_4, general
            sql = f"""
            SELECT 
                ma_ky, ten_ky, giai_doan_chinh_sach, ma_chitieu, ten_chitieu, ten_chinh_sach,
                don_vi_tinh, so_luong_doi_tuong_can_ho_tro, don_gia_trieu_vnd,
                tong_kinh_phi_can_phan_bo_ty_vnd, can_cu_phap_ly_dinh_muc,
                bien_dong_kinh_phi_ty_vnd
            FROM v_tong_hop_ngan_sach_chinh_sach_ky
            WHERE ma_ky = '{period}'
            ORDER BY tong_kinh_phi_can_phan_bo_ty_vnd DESC
            LIMIT {limit}
            """
            return sql.strip()

    # ==========================================================================
    # 1. INTENT: POLICY_BUDGET (Dự toán ngân sách & cơ cấu nguồn lực đầu tư công)
    # ==========================================================================
    elif code == "POLICY_BUDGET":
        if e.so_sanh_da_ky:
            sql = f"""
            SELECT 
                ma_ky, ten_ky, giai_doan_chinh_sach, ma_chitieu, ten_chitieu, ten_chinh_sach,
                don_vi_tinh, so_luong_doi_tuong_can_ho_tro, don_gia_trieu_vnd,
                tong_kinh_phi_can_phan_bo_ty_vnd, can_cu_phap_ly_dinh_muc,
                bien_dong_kinh_phi_ty_vnd
            FROM v_tong_hop_ngan_sach_chinh_sach_ky
            ORDER BY thu_tu_ky ASC, tong_kinh_phi_can_phan_bo_ty_vnd DESC
            LIMIT {limit}
            """
        else:
            sql = f"""
            SELECT 
                ma_ky, ten_ky, giai_doan_chinh_sach, ma_chitieu, ten_chitieu, ten_chinh_sach,
                don_vi_tinh, so_luong_doi_tuong_can_ho_tro, don_gia_trieu_vnd,
                tong_kinh_phi_can_phan_bo_ty_vnd, can_cu_phap_ly_dinh_muc,
                bien_dong_kinh_phi_ty_vnd
            FROM v_tong_hop_ngan_sach_chinh_sach_ky
            WHERE ma_ky = '{period}'
            ORDER BY tong_kinh_phi_can_phan_bo_ty_vnd DESC
            LIMIT {limit}
            """
        return sql.strip()

    # ==========================================================================
    # 2. INTENT: VULNERABILITY_HEALTH (Điểm nóng Ma túy, HIV, Y tế sinh sản)
    # ==========================================================================
    elif code == "VULNERABILITY_HEALTH":
        # Lọc theo xã hoặc huyện hoặc dân tộc nếu có
        where_clauses = []
        if e.xa:
            clean_xa = escape_sql_string(e.xa)
            where_clauses.append(f"ten_doi_tuong ILIKE '{clean_xa}'")
        elif e.huyen:
            clean_huyen = escape_sql_string(e.huyen)
            where_clauses.append(f"(pham_vi_nhom ILIKE '%{clean_huyen}%' OR ten_doi_tuong ILIKE '%{clean_huyen}%')")
        elif e.dantoc:
            clean_dt = escape_sql_string(e.dantoc)
            where_clauses.append(f"ten_doi_tuong ILIKE '{clean_dt}'")

        if not e.so_sanh_da_ky and not (e.xa or e.dantoc):
            where_clauses.append(f"ma_ky = '{period}'")

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else f"WHERE ma_ky = '{period}'"

        sql = f"""
        SELECT 
            ma_ky, ten_ky, phan_nhom_rui_ro, ten_doi_tuong, pham_vi_nhom,
            chi_so_rui_ro_chinh, chi_so_rui_ro_phu, tong_muc_do_rui_ro,
            bien_dong_rui_ro_chinh, ty_le_giam_rui_ro_pct, xep_hang_diem_nong_ky
        FROM v_diemnong_anninh_yte_da_ky
        {where_str}
        ORDER BY {"thu_tu_ky ASC, " if e.so_sanh_da_ky or e.xa or e.dantoc else ""}tong_muc_do_rui_ro DESC
        LIMIT {limit}
        """
        return sql.strip()

    # ==========================================================================
    # 3. INTENT: HOUSING_POVERTY (Nhà tạm, nhà dột nát, Dự án 1 - CTMTQG 1719)
    # ==========================================================================
    elif code == "HOUSING_POVERTY":
        if e.dantoc_list and len(e.dantoc_list) >= 2:
            dt_where = " OR ".join([f"ten_dantoc ILIKE '%{escape_sql_string(d)}%'" for d in e.dantoc_list])
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc, la_dtts_it_nguoi,
                tong_ho_co_nha, so_ho_nha_tam_don_so, ty_le_nha_tam_pct,
                so_ho_khat_von, khoang_trong_tin_dung_pct
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ma_ky = '{period}' AND ({dt_where})
            ORDER BY ty_le_nha_tam_pct DESC
            """
        elif e.dantoc:
            clean_dt = escape_sql_string(e.dantoc)
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc, la_dtts_it_nguoi,
                tong_ho_co_nha, so_ho_nha_tam_don_so, ty_le_nha_tam_pct,
                so_ho_nha_tam_ky_truoc, chenh_lech_nha_tam, bien_dong_nha_tam_pct,
                xep_hang_nha_tam_ky
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ten_dantoc ILIKE '{clean_dt}'
            ORDER BY thu_tu_ky ASC
            """
        elif e.huyen:
            # Tra cứu tỷ lệ nhà tạm theo huyện
            clean_huyen = escape_sql_string(e.huyen)
            sql = f"""
            SELECT 
                f.ma_ky, k.ten_ky, d.ten_huyen,
                SUM(f.tong_so_ho) AS tong_ho_dtts,
                SUM(f.so_ho_nha_tam_don_so) AS tong_ho_nha_tam,
                ROUND(AVG(f.ty_le_nha_tam_don_so_pct)::numeric, 2) AS ty_le_nha_tam_pct
            FROM fact_nhao_dantoc f
            JOIN dim_diaban d ON f.ma_diaban = d.ma_diaban
            JOIN dim_ky_baocao k ON f.ma_ky = k.ma_ky
            WHERE d.ten_huyen = '{clean_huyen}' AND f.ma_ky = '{period}'
            GROUP BY f.ma_ky, k.ten_ky, d.ten_huyen, k.thu_tu_ky
            ORDER BY k.thu_tu_ky ASC
            LIMIT {limit}
            """
        else:
            # Bảng xếp hạng các dân tộc còn nhiều nhà tạm nhất
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc, la_dtts_it_nguoi,
                tong_ho_co_nha, so_ho_nha_tam_don_so, ty_le_nha_tam_pct,
                chenh_lech_nha_tam, xep_hang_nha_tam_ky
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ma_ky = '{period}' AND so_ho_nha_tam_don_so > 0
            ORDER BY so_ho_nha_tam_don_so {sort_order}
            LIMIT {limit}
            """
        return sql.strip()

    # ==========================================================================
    # 4. INTENT: SANITATION_DIGITAL (Tiêu chí 17 NTM hố xí & Chuyển đổi số Đề án 06)
    # ==========================================================================
    elif code == "SANITATION_DIGITAL":
        if e.huyen:
            clean_huyen = escape_sql_string(e.huyen)
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_huyen, tong_ho_dtts_huyen,
                ty_le_nuoc_hvs_bq_pct, ty_le_ho_xi_hvs_bq_pct, bien_dong_ho_xi_hvs_pct,
                trang_thai_ntm_tc17, ty_le_internet_huyen_pct, bien_dong_internet_pct,
                trang_thai_chuyendoiso_dean06
            FROM v_huyen_vesinh_chuyendoiso_da_ky
            WHERE ten_huyen ILIKE '{clean_huyen}'
            ORDER BY thu_tu_ky ASC
            """
        else:
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_huyen, tong_ho_dtts_huyen,
                ty_le_nuoc_hvs_bq_pct, ty_le_ho_xi_hvs_bq_pct, bien_dong_ho_xi_hvs_pct,
                trang_thai_ntm_tc17, ty_le_internet_huyen_pct, bien_dong_internet_pct,
                trang_thai_chuyendoiso_dean06
            FROM v_huyen_vesinh_chuyendoiso_da_ky
            WHERE ma_ky = '{period}'
            ORDER BY ty_le_ho_xi_hvs_bq_pct {sort_order}
            LIMIT {limit}
            """
        return sql.strip()

    # ==========================================================================
    # 5. INTENT: CREDIT_LAND (Khoảng trống tín dụng & Tư liệu đất sản xuất)
    # ==========================================================================
    elif code == "CREDIT_LAND":
        if e.dantoc:
            clean_dt = escape_sql_string(e.dantoc)
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc,
                so_ho_khat_von, khoang_trong_tin_dung_pct, chenh_lech_ho_khat_von,
                bien_dong_tin_dung_pct, dien_tich_dat_sx_bq_ha, bien_dong_dat_sx_ha,
                xep_hang_khat_von_ky
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ten_dantoc ILIKE '{clean_dt}'
            ORDER BY thu_tu_ky ASC
            """
        else:
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc,
                so_ho_khat_von, khoang_trong_tin_dung_pct, chenh_lech_ho_khat_von,
                dien_tich_dat_sx_bq_ha, xep_hang_khat_von_ky
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ma_ky = '{period}' AND so_ho_khat_von > 0
            ORDER BY so_ho_khat_von {sort_order}
            LIMIT {limit}
            """
        return sql.strip()

    # ==========================================================================
    # 6. INTENT: LABOR_EDUCATION (Lao động chưa đào tạo, CMKT, việc làm, giáo dục)
    # ==========================================================================
    elif code == "LABOR_EDUCATION":
        if e.dantoc:
            clean_dt = escape_sql_string(e.dantoc)
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc,
                tong_lao_dong, lao_dong_khong_cmkt, ty_le_khong_cmkt_pct,
                bien_dong_khong_cmkt_pct, lao_dong_nong_nghiep, ty_le_nong_nghiep_pct,
                ty_le_nu_biet_chu_pct, bien_dong_nu_biet_chu_pct
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ten_dantoc ILIKE '{clean_dt}'
            ORDER BY thu_tu_ky ASC
            """
        else:
            if "mu_chu" in e.metric_keys:
                order_col = "ty_le_nu_biet_chu_pct ASC"
            else:
                order_col = f"ty_le_khong_cmkt_pct {sort_order}"
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc,
                tong_lao_dong, lao_dong_khong_cmkt, ty_le_khong_cmkt_pct,
                lao_dong_nong_nghiep, ty_le_nong_nghiep_pct, ty_le_nu_biet_chu_pct
            FROM v_dantoc_chuyen_dich_da_ky
            WHERE ma_ky = '{period}' AND tong_lao_dong >= 100
            ORDER BY {order_col}
            LIMIT {limit}
            """
        return sql.strip()

    # ==========================================================================
    # 7. INTENT: POVERTY_COMMUNE (Phân hóa nghèo đa chiều cấp xã)
    # ==========================================================================
    elif code == "POVERTY_COMMUNE":
        if e.xa:
            clean_xa = escape_sql_string(e.xa)
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_huyen, ten_xa, km_den_trung_tam_huyen,
                tong_ho_dtts, so_ho_ngheo, ty_le_ngheo_pct,
                bien_dong_ty_le_ngheo_pct, nhom_toc_do_giam_ngheo,
                du_toan_ngan_sach_sinh_ke_trieu_vnd
            FROM v_xa_biendong_ngheo_da_ky
            WHERE ten_xa ILIKE '{clean_xa}'
            ORDER BY thu_tu_ky ASC
            """
        elif e.huyen:
            clean_huyen = escape_sql_string(e.huyen)
            order_col = "du_toan_ngan_sach_sinh_ke_trieu_vnd" if "xa_trong_huyen" in e.metric_keys else "ty_le_ngheo_pct"
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_huyen, ten_xa, km_den_trung_tam_huyen,
                tong_ho_dtts, so_ho_ngheo, ty_le_ngheo_pct,
                bien_dong_ty_le_ngheo_pct, nhom_toc_do_giam_ngheo,
                du_toan_ngan_sach_sinh_ke_trieu_vnd
            FROM v_xa_biendong_ngheo_da_ky
            WHERE ten_huyen ILIKE '%{clean_huyen}%' AND ma_ky = '{period}'
            ORDER BY {order_col} {sort_order}
            LIMIT {limit}
            """
        else:
            sql = f"""
            SELECT 
                ma_ky, ten_ky, ten_huyen, ten_xa, km_den_trung_tam_huyen,
                tong_ho_dtts, so_ho_ngheo, ty_le_ngheo_pct,
                bien_dong_ty_le_ngheo_pct, nhom_toc_do_giam_ngheo,
                du_toan_ngan_sach_sinh_ke_trieu_vnd
            FROM v_xa_biendong_ngheo_da_ky
            WHERE ma_ky = '{period}'
            ORDER BY ty_le_ngheo_pct {sort_order}
            LIMIT {limit}
            """
        return sql.strip()

    # ==========================================================================
    # 8. INTENT: ETHNIC_OVERVIEW (Hồ sơ chuyển dịch 6 trụ cột của 1 dân tộc)
    # ==========================================================================
    elif code == "ETHNIC_OVERVIEW":
        clean_dt = escape_sql_string(e.dantoc) if e.dantoc else "Ê đê"
        sql = f"""
        SELECT 
            ma_ky, ten_ky, giai_doan_chinh_sach, ten_dantoc, nhom_nguon_goc, la_dtts_it_nguoi,
            tong_dan_so, tong_ho_co_nha, so_ho_nha_tam_don_so, ty_le_nha_tam_pct,
            so_ho_khat_von, khoang_trong_tin_dung_pct,
            tong_lao_dong, lao_dong_khong_cmkt, ty_le_khong_cmkt_pct, ty_le_nong_nghiep_pct,
            ty_le_nu_biet_chu_pct, dien_tich_dat_sx_bq_ha
        FROM v_dantoc_chuyen_dich_da_ky
        WHERE ten_dantoc ILIKE '{clean_dt}'
        ORDER BY thu_tu_ky ASC
        """
        return sql.strip()

    # ==========================================================================
    # 9. INTENT: DISTRICT_OVERVIEW (Báo cáo KTXH tổng hợp cấp huyện)
    # ==========================================================================
    elif code == "DISTRICT_OVERVIEW":
        clean_huyen = escape_sql_string(e.huyen) if e.huyen else "Huyện Ea Súp"
        sql = f"""
        SELECT 
            ma_ky, ten_ky, ten_huyen, tong_ho_dtts_huyen,
            ty_le_nuoc_hvs_bq_pct, ty_le_ho_xi_hvs_bq_pct, bien_dong_ho_xi_hvs_pct,
            trang_thai_ntm_tc17, ty_le_internet_huyen_pct, bien_dong_internet_pct,
            trang_thai_chuyendoiso_dean06
        FROM v_huyen_vesinh_chuyendoiso_da_ky
        WHERE ten_huyen ILIKE '{clean_huyen}'
        ORDER BY thu_tu_ky ASC
        """
        return sql.strip()

    # ==========================================================================
    # 10. DEFAULT_MACRO_OVERVIEW
    # ==========================================================================
    else:
        sql = f"""
        SELECT 
            ma_ky, ten_ky, ten_huyen, ten_xa, tong_ho_dtts, so_ho_ngheo,
            ty_le_ngheo_pct, bien_dong_ty_le_ngheo_pct, nhom_toc_do_giam_ngheo
        FROM v_xa_biendong_ngheo_da_ky
        WHERE ma_ky = '{period}'
        ORDER BY ty_le_ngheo_pct DESC
        LIMIT {limit}
        """
        return sql.strip()
