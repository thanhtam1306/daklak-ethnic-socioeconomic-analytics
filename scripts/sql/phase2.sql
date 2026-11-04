-- ==============================================================================
-- BƯỚC 2 (ROLE DA): KIỂM TOÁN DỮ LIỆU ĐA KỲ & HỆ THỐNG 5 ANALYTICAL VIEWS (LAG)
-- Dự án: Phân Tích Thực Trạng KTXH 53 Dân Tộc Thiểu Số Tỉnh Đắk Lắk
-- CSDL: PostgreSQL 18 (daklak_socioeconomic | Schema: daklak_analytics)
-- Báo cáo chi tiết: reports/SQL_ANALYTICS_POLICY_BRIEF.md (Phần II)
-- ==============================================================================

SET search_path TO daklak_analytics, public;

-- ==============================================================================
-- 🔍 PHẦN 1: TRUY VẤN KIỂM TOÁN DỮ LIỆU ĐA KỲ (SQL AUDIT GATE)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Bài tập 1.1: Kiểm tra tính đầy đủ của 3 kỳ báo cáo (Completeness Check)
-- Mục đích kỹ thuật: Đối soát số lượng xã (146 xã), tổng số hộ, số hộ nghèo và cờ is_latest
-- Bảng liên quan: dim_ky_baocao, fact_hatang_xa
-- ------------------------------------------------------------------------------
SELECT 
    k.ma_ky,
    k.thu_tu_ky,
    k.ten_ky,
    k.is_latest,
    COUNT(f.ma_xa)                   AS so_luong_xa,
    SUM(f.tong_ho_dtts)              AS tong_ho_dtts,
    SUM(f.so_ho_ngheo)               AS tong_ho_ngheo,
    ROUND(AVG(f.ty_le_ngheo_pct), 2) AS ty_le_ngheo_binh_quan_xa_pct
FROM dim_ky_baocao k
INNER JOIN fact_hatang_xa f 
    ON k.ma_ky = f.ma_ky
GROUP BY 
    k.ma_ky, 
    k.thu_tu_ky, 
    k.ten_ky, 
    k.is_latest
ORDER BY 
    k.thu_tu_ky ASC;

-- ------------------------------------------------------------------------------
-- Bài tập 1.2: Kiểm tra lỗi Logic & Ràng buộc toàn vẹn (Sanity Check)
-- Mục đích kỹ thuật: Kiểm tra biên tỷ lệ [0, 100] và đối soát cân bằng tổng thành phần nhà ở
-- Bảng liên quan: fact_nhao_dantoc
-- ------------------------------------------------------------------------------
SELECT 
    ma_ky,
    ma_dantoc,
    ten_dantoc,
    tong_so_ho_co_nha,
    nha_kien_co_ban_kien_co,
    nha_thieu_kien_co_don_so,
    (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so) AS tong_2_loai_nha,
    tong_so_ho_co_nha - (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so) AS do_lech_ho,
    ty_le_nha_tam_don_so_pct
FROM fact_nhao_dantoc
WHERE 
    ty_le_nha_tam_don_so_pct < 0 
    OR ty_le_nha_tam_don_so_pct > 100
    OR (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so) <> tong_so_ho_co_nha
ORDER BY 
    ma_ky, 
    ABS(tong_so_ho_co_nha - (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so)) DESC;


-- ==============================================================================
-- 🚀 PHẦN 2: HỆ THỐNG 5 VIEW PHÂN TÍCH ĐA KỲ (WINDOW FUNCTIONS LAG) & NGÂN SÁCH
-- Bao phủ 100% 4 Trang Dashboard Power BI & 9 Chỉ tiêu Kế hoạch
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Bài tập 2.1: View 1 — `v_xa_biendong_ngheo_da_ky`
-- Cấp độ hạt (Grain): 146 Xã x 3 Kỳ = 438 dòng (Phục vụ Trang 1 & Trang 4 Power BI)
-- Kỹ thuật: LAG() PARTITION BY ma_xa ORDER BY thu_tu_ky, DENSE_RANK() theo từng kỳ
-- Bảng liên quan: fact_hatang_xa, dim_ky_baocao, dim_chitieu_kehoach_ngansach
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_xa_biendong_ngheo_da_ky AS
WITH base_lag AS (
    SELECT 
        f.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.nam_moc,
        k.giai_doan_chinh_sach,
        k.is_latest,
        f.ma_xa,
        f.ten_xa,
        f.ma_huyen,
        f.ten_huyen,
        f.km_den_trung_tam_huyen,
        f.tong_ho_dtts,
        f.so_ho_ngheo,
        f.ty_le_ngheo_pct,
        f.ty_le_can_ngheo_pct,
        f.ty_le_thon_duong_cung_pct,
        -- Lấy số liệu kỳ liền trước của từng xã bằng LAG() theo thu_tu_ky
        LAG(f.ty_le_ngheo_pct) OVER (
            PARTITION BY f.ma_xa ORDER BY k.thu_tu_ky
        ) AS ty_le_ngheo_ky_truoc,
        LAG(f.so_ho_ngheo) OVER (
            PARTITION BY f.ma_xa ORDER BY k.thu_tu_ky
        ) AS so_ho_ngheo_ky_truoc,
        LAG(f.ty_le_thon_duong_cung_pct) OVER (
            PARTITION BY f.ma_xa ORDER BY k.thu_tu_ky
        ) AS ty_le_duong_cung_ky_truoc,
        ct.chi_tieu_muc_tieu AS muc_tieu_ngheo_pct,
        ct.don_gia_trieu_vnd AS dinh_muc_ho_tro_trieu_vnd
    FROM fact_hatang_xa f
    INNER JOIN dim_ky_baocao k 
        ON f.ma_ky = k.ma_ky
    LEFT JOIN dim_chitieu_kehoach_ngansach ct 
        ON k.giai_doan_chinh_sach = ct.giai_doan_chinh_sach 
       AND ct.ma_chitieu = 'TY_LE_HO_NGHEO'
)
SELECT 
    *,
    -- 1. Biến động tỷ lệ nghèo (Số âm = Giảm nghèo tốt, Số dương = Tái nghèo/Tăng nghèo)
    ROUND(ty_le_ngheo_pct - ty_le_ngheo_ky_truoc, 2) AS bien_dong_ty_le_ngheo_pct,
    (so_ho_ngheo - so_ho_ngheo_ky_truoc)             AS bien_dong_so_ho_ngheo,
    ROUND(ty_le_thon_duong_cung_pct - ty_le_duong_cung_ky_truoc, 2) AS bien_dong_duong_cung_pct,
    -- 2. Khoảng cách so với mục tiêu kế hoạch giai đoạn (<= 0 là Đạt mục tiêu)
    ROUND(ty_le_ngheo_pct - muc_tieu_ngheo_pct, 2)   AS khoang_cach_muc_tieu_pct,
    -- 3. Phân loại trạng thái thực hiện kế hoạch & tốc độ cải thiện
    CASE 
        WHEN ty_le_ngheo_pct <= muc_tieu_ngheo_pct THEN 'Đạt mục tiêu giai đoạn'
        WHEN ty_le_ngheo_pct > 40.0                THEN 'Báo động đỏ (>40%)'
        ELSE 'Chưa đạt mục tiêu'
    END AS trang_thai_ke_hoach,
    CASE 
        WHEN ty_le_ngheo_ky_truoc IS NULL                   THEN 'Kỳ gốc (Baseline 2019)'
        WHEN (ty_le_ngheo_pct - ty_le_ngheo_ky_truoc) <= -4.0 THEN 'Bứt phá giảm nghèo mạnh (<= -4%)'
        WHEN (ty_le_ngheo_pct - ty_le_ngheo_ky_truoc) <  0.0  THEN 'Giảm nghèo chậm (0% đến -4%)'
        ELSE 'Cảnh báo dậm chân / Tái nghèo (>= 0%)'
    END AS nhom_toc_do_giam_ngheo,
    -- 4. Xếp hạng xã có tỷ lệ nghèo cao nhất trong từng kỳ
    DENSE_RANK() OVER (
        PARTITION BY ma_ky ORDER BY ty_le_ngheo_pct DESC
    ) AS xep_hang_ngheo_cao_nhat_ky,
    -- 5. Dự toán ngân sách hỗ trợ sinh kế (Triệu VNĐ)
    ROUND(so_ho_ngheo * dinh_muc_ho_tro_trieu_vnd, 2) AS du_toan_ngan_sach_sinh_ke_trieu_vnd
FROM base_lag;


-- ------------------------------------------------------------------------------
-- Bài tập 2.2: View 2 — `v_dantoc_chuyen_dich_da_ky`
-- Cấp độ hạt (Grain): 53 Dân tộc x 3 Kỳ = 159 dòng (Phục vụ Trang 1, 2, 3 Power BI)
-- Kỹ thuật: LAG() PARTITION BY ma_dantoc ORDER BY thu_tu_ky cho 6 trụ cột KTXH
-- View nền tảng: v_dtts_tong_hop_dantoc
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_dantoc_chuyen_dich_da_ky AS
WITH dantoc_lag AS (
    SELECT 
        v.*,
        -- 1. Trụ cột Nhà ở (Xóa nhà tạm, dột nát)
        LAG(v.so_ho_nha_tam_don_so) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS so_ho_nha_tam_ky_truoc,
        LAG(v.ty_le_nha_tam_pct)    OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_nha_tam_ky_truoc,
        -- 2. Trụ cột Đào tạo nghề CMKT (Vốn nhân lực)
        LAG(v.ty_le_khong_cmkt_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_khong_cmkt_ky_truoc,
        -- 3. Trụ cột Tín dụng chính sách (Khát vốn NHCSXH)
        LAG(v.so_ho_khat_von)            OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS so_ho_khat_von_ky_truoc,
        LAG(v.khoang_trong_tin_dung_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS khoang_trong_tin_dung_ky_truoc,
        -- 4. Trụ cột Giáo dục giới (Tỷ lệ nữ biết chữ)
        LAG(v.ty_le_nu_biet_chu_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_nu_biet_chu_ky_truoc,
        -- 5. Trụ cột Việc làm (Bẫy lao động nông nghiệp)
        LAG(v.ty_le_nong_nghiep_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_nong_nghiep_ky_truoc,
        -- 6. Trụ cột Đất sản xuất bình quân (ha/hộ)
        LAG(v.dien_tich_dat_sx_bq_ha) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS dien_tich_dat_sx_ky_truoc
    FROM v_dtts_tong_hop_dantoc v
)
SELECT 
    *,
    -- Tính biến động giữa kỳ hiện tại và kỳ liền trước (Delta)
    (so_ho_nha_tam_don_so - so_ho_nha_tam_ky_truoc)                   AS chenh_lech_nha_tam,
    ROUND(ty_le_nha_tam_pct - ty_le_nha_tam_ky_truoc, 2)              AS bien_dong_nha_tam_pct,
    ROUND(ty_le_khong_cmkt_pct - ty_le_khong_cmkt_ky_truoc, 2)        AS bien_dong_khong_cmkt_pct,
    (so_ho_khat_von - so_ho_khat_von_ky_truoc)                        AS chenh_lech_ho_khat_von,
    ROUND(khoang_trong_tin_dung_pct - khoang_trong_tin_dung_ky_truoc, 2) AS bien_dong_tin_dung_pct,
    ROUND(ty_le_nu_biet_chu_pct - ty_le_nu_biet_chu_ky_truoc, 2)      AS bien_dong_nu_biet_chu_pct,
    ROUND(ty_le_nong_nghiep_pct - ty_le_nong_nghiep_ky_truoc, 2)      AS bien_dong_nong_nghiep_pct,
    ROUND(dien_tich_dat_sx_bq_ha - dien_tich_dat_sx_ky_truoc, 2)      AS bien_dong_dat_sx_ha,
    -- Xếp hạng quy mô nhà tạm và hộ khát vốn trong từng kỳ
    DENSE_RANK() OVER (
        PARTITION BY ma_ky ORDER BY so_ho_nha_tam_don_so DESC
    ) AS xep_hang_nha_tam_ky,
    DENSE_RANK() OVER (
        PARTITION BY ma_ky ORDER BY so_ho_khat_von DESC
    ) AS xep_hang_khat_von_ky
FROM dantoc_lag;


-- ------------------------------------------------------------------------------
-- Bài tập 2.3: View 3 — `v_huyen_vesinh_chuyendoiso_da_ky`
-- Cấp độ hạt (Grain): 15 Huyện x 3 Kỳ = 45 dòng (Phục vụ Trang 3 NTM & Trang 4 Đề án 06)
-- Kỹ thuật: Tổng hợp cấp huyện, LAG() PARTITION BY ma_huyen ORDER BY thu_tu_ky
-- Bảng liên quan: fact_dantocthiet_yeu_huyen, dim_ky_baocao, fact_danso_huyen_dantoc, dim_chitieu_kehoach_ngansach
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_huyen_vesinh_chuyendoiso_da_ky AS
WITH huyen_agg AS (
    SELECT 
        t.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.nam_moc,
        k.giai_doan_chinh_sach,
        k.is_latest,
        t.ma_huyen,
        MAX(t.ten_huyen) AS ten_huyen,
        COALESCE(ds.tong_ho_dtts_huyen, 0) AS tong_ho_dtts_huyen,
        ROUND(AVG(t.ty_le_nuoc_hop_ve_sinh_pct), 2)  AS ty_le_nuoc_hvs_bq_pct,
        ROUND(AVG(t.ty_le_ho_xi_hop_ve_sinh_pct), 2) AS ty_le_ho_xi_hvs_bq_pct,
        SUM(COALESCE(t.so_ho_co_internet, 0))        AS tong_ho_co_internet,
        SUM(COALESCE(t.so_ho_co_dien_luoi, 0))       AS tong_ho_co_dien_luoi,
        LEAST(
            100.00,
            ROUND(
                SUM(COALESCE(t.so_ho_co_internet, 0)) * 100.0 
                / NULLIF(SUM(COALESCE(t.so_ho_co_dien_luoi, 0)), 0), 
                2
            )
        ) AS ty_le_internet_huyen_pct
    FROM fact_dantocthiet_yeu_huyen t
    INNER JOIN dim_ky_baocao k 
        ON t.ma_ky = k.ma_ky
    LEFT JOIN (
        SELECT ma_ky, ma_huyen, SUM(so_ho) AS tong_ho_dtts_huyen
        FROM fact_danso_huyen_dantoc
        GROUP BY ma_ky, ma_huyen
    ) ds ON t.ma_ky = ds.ma_ky AND t.ma_huyen = ds.ma_huyen
    GROUP BY 
        t.ma_ky, k.thu_tu_ky, k.ten_ky, k.nam_moc, k.giai_doan_chinh_sach, k.is_latest,
        t.ma_huyen, ds.tong_ho_dtts_huyen
),
huyen_lag AS (
    SELECT 
        h.*,
        LAG(h.ty_le_nuoc_hvs_bq_pct)     OVER (PARTITION BY h.ma_huyen ORDER BY h.thu_tu_ky) AS nuoc_hvs_ky_truoc_pct,
        LAG(h.ty_le_ho_xi_hvs_bq_pct)    OVER (PARTITION BY h.ma_huyen ORDER BY h.thu_tu_ky) AS ho_xi_hvs_ky_truoc_pct,
        LAG(h.ty_le_internet_huyen_pct)  OVER (PARTITION BY h.ma_huyen ORDER BY h.thu_tu_ky) AS internet_ky_truoc_pct,
        ct_vs.chi_tieu_muc_tieu AS muc_tieu_ho_xi_ntm_pct,
        ct_so.chi_tieu_muc_tieu AS muc_tieu_internet_dean06_pct
    FROM huyen_agg h
    LEFT JOIN dim_chitieu_kehoach_ngansach ct_vs 
        ON h.giai_doan_chinh_sach = ct_vs.giai_doan_chinh_sach AND ct_vs.ma_chitieu = 'TY_LE_HO_XI_HVS'
    LEFT JOIN dim_chitieu_kehoach_ngansach ct_so 
        ON h.giai_doan_chinh_sach = ct_so.giai_doan_chinh_sach AND ct_so.ma_chitieu = 'TY_LE_INTERNET'
)
SELECT 
    *,
    ROUND(ty_le_nuoc_hvs_bq_pct - nuoc_hvs_ky_truoc_pct, 2)    AS bien_dong_nuoc_hvs_pct,
    ROUND(ty_le_ho_xi_hvs_bq_pct - ho_xi_hvs_ky_truoc_pct, 2)  AS bien_dong_ho_xi_hvs_pct,
    ROUND(ty_le_internet_huyen_pct - internet_ky_truoc_pct, 2) AS bien_dong_internet_pct,
    CASE 
        WHEN ty_le_ho_xi_hvs_bq_pct >= muc_tieu_ho_xi_ntm_pct THEN 'Đạt chuẩn Tiêu chí 17 NTM'
        WHEN ty_le_ho_xi_hvs_bq_pct < 30.0                    THEN 'Vùng trũng VSMT nghiêm trọng (<30%)'
        ELSE 'Chưa đạt chuẩn NTM'
    END AS trang_thai_ntm_tc17,
    CASE 
        WHEN ty_le_internet_huyen_pct >= muc_tieu_internet_dean06_pct THEN 'Đạt mục tiêu Hạ tầng số Đề án 06'
        WHEN ty_le_internet_huyen_pct < 80.0                          THEN 'Vùng lõm sóng / Trũng số (<80%)'
        ELSE 'Đang tiệm cận mục tiêu Đề án 06'
    END AS trang_thai_chuyendoiso_dean06
FROM huyen_lag;


-- ------------------------------------------------------------------------------
-- Bài tập 2.4: View 4 — `v_diemnong_anninh_yte_da_ky`
-- Cấp độ hạt (Grain): Tích hợp 146 Xã (Ma túy/HIV) & 53 Dân tộc (Sinh con tại nhà) x 3 Kỳ
-- Kỹ thuật: UNION ALL đồng nhất schema, LAG() theo từng phân nhóm và đối tượng
-- Bảng liên quan: fact_matuy_hiv_xa, fact_mucsinh_dantoc, dim_ky_baocao
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_diemnong_anninh_yte_da_ky AS
WITH unified_risks AS (
    -- Khối 1: Điểm nóng Ma túy & HIV/AIDS cấp Xã (146 xã x 3 kỳ)
    SELECT 
        m.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.giai_doan_chinh_sach,
        k.is_latest,
        'AN_NINH_MA_TUY_HIV_XA'::VARCHAR(40) AS phan_nhom_rui_ro,
        m.ma_xa                              AS ma_doi_tuong,
        m.ten_xa                             AS ten_doi_tuong,
        m.ten_huyen                          AS pham_vi_nhom,
        m.nguoi_dtts_nghien_ma_tuy           AS chi_so_rui_ro_chinh,
        m.nguoi_dtts_nhiem_hiv               AS chi_so_rui_ro_phu,
        (m.nguoi_dtts_nghien_ma_tuy + m.nguoi_dtts_nhiem_hiv) AS tong_muc_do_rui_ro
    FROM fact_matuy_hiv_xa m
    INNER JOIN dim_ky_baocao k ON m.ma_ky = k.ma_ky

    UNION ALL

    -- Khối 2: Điểm nóng Sinh con tại nhà & Không bà đỡ theo Dân tộc (53 dân tộc x 3 kỳ)
    SELECT 
        s.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.giai_doan_chinh_sach,
        k.is_latest,
        'Y_TE_SINH_TAI_NHA_DANTOC'::VARCHAR(40) AS phan_nhom_rui_ro,
        s.ma_dantoc                             AS ma_doi_tuong,
        s.ten_dantoc                            AS ten_doi_tuong,
        s.nhom_nguon_goc                        AS pham_vi_nhom,
        s.sinh_tai_nha_tong                     AS chi_so_rui_ro_chinh,
        s.sinh_tai_nha_khong_ba_do              AS chi_so_rui_ro_phu,
        s.sinh_tai_nha_tong                     AS tong_muc_do_rui_ro
    FROM fact_mucsinh_dantoc s
    INNER JOIN dim_ky_baocao k ON s.ma_ky = k.ma_ky
),
risk_lag AS (
    SELECT 
        r.*,
        LAG(r.chi_so_rui_ro_chinh) OVER (
            PARTITION BY r.phan_nhom_rui_ro, r.ma_doi_tuong ORDER BY r.thu_tu_ky
        ) AS chi_so_chinh_ky_truoc,
        LAG(r.chi_so_rui_ro_phu) OVER (
            PARTITION BY r.phan_nhom_rui_ro, r.ma_doi_tuong ORDER BY r.thu_tu_ky
        ) AS chi_so_phu_ky_truoc
    FROM unified_risks r
)
SELECT 
    *,
    (chi_so_rui_ro_chinh - chi_so_chinh_ky_truoc) AS bien_dong_rui_ro_chinh,
    (chi_so_rui_ro_phu - chi_so_phu_ky_truoc)     AS bien_dong_rui_ro_phu,
    CASE 
        WHEN chi_so_chinh_ky_truoc > 0 
        THEN ROUND((chi_so_rui_ro_chinh - chi_so_chinh_ky_truoc) * 100.0 / chi_so_chinh_ky_truoc, 2)
        ELSE 0.0
    END AS ty_le_giam_rui_ro_pct,
    DENSE_RANK() OVER (
        PARTITION BY ma_ky, phan_nhom_rui_ro ORDER BY tong_muc_do_rui_ro DESC
    ) AS xep_hang_diem_nong_ky
FROM risk_lag;


-- ------------------------------------------------------------------------------
-- Bài tập 2.5: View 5 — `v_tong_hop_ngan_sach_chinh_sach_ky`
-- Cấp độ hạt (Grain): 5 Nhóm Chỉ tiêu Ngân sách Cốt lõi x 3 Kỳ = 15 dòng
-- Kỹ thuật: UNION ALL 5 chỉ tiêu, tính tổng dự toán vốn theo định mức chính sách, LAG() tính biến động ngân sách
-- Bảng liên quan: fact_hatang_xa, fact_nhao_dantoc, fact_tindung_dantoc, fact_trinhdo_cmkt_dantoc, fact_mucsinh_dantoc, dim_chitieu_kehoach_ngansach, dim_chinhsach_canthiep
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_tong_hop_ngan_sach_chinh_sach_ky AS
WITH raw_metrics_by_period AS (
    -- 1. Hỗ trợ sinh kế hộ nghèo DTTS (Dự án 3 MTQG 1719)
    SELECT 
        ma_ky,
        'TY_LE_HO_NGHEO'::VARCHAR(50) AS ma_chitieu,
        SUM(so_ho_ngheo)              AS so_luong_doi_tuong_can_ho_tro,
        ROUND(AVG(ty_le_ngheo_pct), 2) AS gia_tri_thuc_te_hien_tai
    FROM fact_hatang_xa
    GROUP BY ma_ky

    UNION ALL

    -- 2. Hỗ trợ xóa nhà tạm, dột nát (Dự án 1 MTQG 1719 & NĐ 28/2022/NĐ-CP)
    SELECT 
        ma_ky,
        'TY_LE_NHA_TAM'::VARCHAR(50) AS ma_chitieu,
        SUM(nha_thieu_kien_co_don_so) AS so_luong_doi_tuong_can_ho_tro,
        ROUND(SUM(nha_thieu_kien_co_don_so) * 100.0 / NULLIF(SUM(tong_so_ho_co_nha), 0), 2) AS gia_tri_thuc_te_hien_tai
    FROM fact_nhao_dantoc
    GROUP BY ma_ky

    UNION ALL

    -- 3. Giải ngân vốn vay tín dụng ưu đãi NHCSXH (Nghị định 28/2022/NĐ-CP)
    SELECT 
        ma_ky,
        'KHOANG_TRONG_TIN_DUNG'::VARCHAR(50) AS ma_chitieu,
        SUM(so_ho_co_nhu_cau_vay)            AS so_luong_doi_tuong_can_ho_tro,
        ROUND(SUM(so_ho_co_nhu_cau_vay) * 100.0 / NULLIF(SUM(tong_nhu_cau_ho), 0), 2) AS gia_tri_thuc_te_hien_tai
    FROM fact_tindung_dantoc
    GROUP BY ma_ky

    UNION ALL

    -- 4. Đào tạo nghề sơ cấp cho lao động chưa có CMKT (Dự án 5 MTQG 1719)
    SELECT 
        ma_ky,
        'TY_LE_CHUA_DAO_TAO_CMKT'::VARCHAR(50) AS ma_chitieu,
        SUM(khong_co_cmkt)                     AS so_luong_doi_tuong_can_ho_tro,
        ROUND(SUM(khong_co_cmkt) * 100.0 / NULLIF(SUM(tong_lao_dong), 0), 2) AS gia_tri_thuc_te_hien_tai
    FROM fact_trinhdo_cmkt_dantoc
    GROUP BY ma_ky

    UNION ALL

    -- 5. Gói đỡ đẻ an toàn & Chăm sóc sức khỏe bà mẹ trẻ em (Dự án 7 MTQG 1719)
    SELECT 
        ma_ky,
        'CA_SINH_TAI_NHA'::VARCHAR(50) AS ma_chitieu,
        SUM(sinh_tai_nha_tong)         AS so_luong_doi_tuong_can_ho_tro,
        SUM(sinh_tai_nha_tong)         AS gia_tri_thuc_te_hien_tai
    FROM fact_mucsinh_dantoc
    GROUP BY ma_ky
),
budget_calc AS (
    SELECT 
        k.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.nam_moc,
        k.giai_doan_chinh_sach,
        k.is_latest,
        m.ma_chitieu,
        ct.ten_chitieu,
        ct.ma_chinh_sach,
        cs.ten_chinh_sach,
        ct.don_vi_tinh,
        ct.huong_tot,
        ct.chi_tieu_muc_tieu,
        m.gia_tri_thuc_te_hien_tai,
        m.so_luong_doi_tuong_can_ho_tro,
        ct.don_gia_trieu_vnd,
        ROUND(m.so_luong_doi_tuong_can_ho_tro * ct.don_gia_trieu_vnd / 1000.0, 2) AS tong_kinh_phi_can_phan_bo_ty_vnd,
        ct.can_cu_phap_ly_dinh_muc
    FROM raw_metrics_by_period m
    INNER JOIN dim_ky_baocao k 
        ON m.ma_ky = k.ma_ky
    INNER JOIN dim_chitieu_kehoach_ngansach ct 
        ON k.giai_doan_chinh_sach = ct.giai_doan_chinh_sach 
       AND m.ma_chitieu = ct.ma_chitieu
    LEFT JOIN dim_chinhsach_canthiep cs 
        ON ct.ma_chinh_sach = cs.ma_chinh_sach
)
SELECT 
    b.*,
    LAG(b.so_luong_doi_tuong_can_ho_tro) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    ) AS doi_tuong_ky_truoc,
    (b.so_luong_doi_tuong_can_ho_tro - LAG(b.so_luong_doi_tuong_can_ho_tro) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    )) AS bien_dong_so_luong_doi_tuong,
    LAG(b.tong_kinh_phi_can_phan_bo_ty_vnd) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    ) AS kinh_phi_ky_truoc_ty_vnd,
    ROUND(b.tong_kinh_phi_can_phan_bo_ty_vnd - LAG(b.tong_kinh_phi_can_phan_bo_ty_vnd) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    ), 2) AS bien_dong_kinh_phi_ty_vnd
FROM budget_calc b
ORDER BY b.ma_chitieu, b.thu_tu_ky;
