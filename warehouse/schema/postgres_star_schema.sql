-- ==============================================================================
-- POSTGRESQL DYNAMIC MULTI-PERIOD STAR SCHEMA DDL & DATA WAREHOUSE DEFINITION
-- Dự án: Phân Tích Thực Trạng Kinh Tế - Xã Hội 53 Dân Tộc Thiểu Số Đắk Lắk
-- Kiến trúc: Dynamic Multi-Period (KY_2019 -> KY_2024 -> KY_2026 [GĐ 2026-2030]...)
-- Schema: daklak_analytics
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS daklak_analytics;
SET search_path TO daklak_analytics, public;

-- ------------------------------------------------------------------------------
-- 1. BẢNG CHIỀU (DIMENSION TABLES - 5 BẢNG)
-- ------------------------------------------------------------------------------

-- Dim 1: Chu Kỳ Điều Tra & Báo Cáo (Dynamic Time Intelligence Dimension)
DROP TABLE IF EXISTS dim_ky_baocao CASCADE;
CREATE TABLE dim_ky_baocao (
    ma_ky                VARCHAR(20) PRIMARY KEY,
    thu_tu_ky            INTEGER NOT NULL UNIQUE,
    ten_ky               VARCHAR(100) NOT NULL,
    nam_moc              INTEGER NOT NULL,
    giai_doan_chinh_sach VARCHAR(50) NOT NULL,
    loai_dieu_tra        VARCHAR(150),
    is_latest            BOOLEAN DEFAULT FALSE,
    ngay_dong_bo_api     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dim 2: Địa Bàn Hành Chính Cấp Xã / Huyện (146 xã, 15 huyện)
DROP TABLE IF EXISTS dim_diaban CASCADE;
CREATE TABLE dim_diaban (
    ma_xa          VARCHAR(20) PRIMARY KEY,
    ten_xa         VARCHAR(100) NOT NULL,
    loai_hinh      VARCHAR(30),
    ma_huyen       VARCHAR(20) NOT NULL,
    ten_huyen      VARCHAR(100) NOT NULL,
    so_thon        INTEGER DEFAULT 0,
    tinh           VARCHAR(50) DEFAULT 'Đắk Lắk'
);

-- Dim 3: 53 Dân Tộc Thiểu Số
DROP TABLE IF EXISTS dim_dantoc CASCADE;
CREATE TABLE dim_dantoc (
    ma_dantoc          VARCHAR(20) PRIMARY KEY,
    ten_dantoc         VARCHAR(100) NOT NULL,
    ten_goc_bieu_mau   VARCHAR(100) NOT NULL,
    nhom_nguon_goc     VARCHAR(100) NOT NULL,
    la_dtts_it_nguoi   INTEGER DEFAULT 0
);

-- Dim 4: Căn Cứ Pháp Lý & Cơ Chế Chính Sách Ngân Sách Nhà Nước (13 chương trình/dự án)
DROP TABLE IF EXISTS dim_chinhsach_canthiep CASCADE;
CREATE TABLE dim_chinhsach_canthiep (
    ma_chinh_sach       VARCHAR(50) PRIMARY KEY,
    ten_chinh_sach      VARCHAR(255) NOT NULL,
    can_cu_phap_ly      TEXT NOT NULL,
    nhom_linh_vuc       VARCHAR(100) NOT NULL,
    doi_tuong_thu_huong TEXT,
    nguon_von_thuc_hien TEXT,
    muc_tieu_dinh_luong TEXT
);

-- Dim 5: Chỉ Tiêu Kế Hoạch & Định Mức Ngân Sách Theo Giai Đoạn Chính Sách
DROP TABLE IF EXISTS dim_chitieu_kehoach_ngansach CASCADE;
CREATE TABLE dim_chitieu_kehoach_ngansach (
    ma_chitieu_kehoach     VARCHAR(50) PRIMARY KEY,
    ma_chitieu             VARCHAR(50) NOT NULL,
    ten_chitieu            VARCHAR(150) NOT NULL,
    giai_doan_chinh_sach   VARCHAR(50) NOT NULL,
    ma_chinh_sach          VARCHAR(50) REFERENCES dim_chinhsach_canthiep(ma_chinh_sach),
    don_vi_tinh            VARCHAR(30) NOT NULL,
    chi_tieu_muc_tieu      NUMERIC(10, 2) NOT NULL,
    huong_tot              VARCHAR(20) NOT NULL, -- 'GIAM' (càng thấp càng tốt) hoặc 'TANG' (càng cao càng tốt)
    don_gia_dinh_muc_vnd   BIGINT DEFAULT 0,
    don_gia_trieu_vnd      NUMERIC(10, 2) DEFAULT 0.0,
    can_cu_phap_ly_dinh_muc TEXT
);

-- Bảng Nhật Ký Đồng Bộ Dữ Liệu API (DE Ingestion Audit Log)
DROP TABLE IF EXISTS etl_api_sync_log CASCADE;
CREATE TABLE etl_api_sync_log (
    sync_id         SERIAL PRIMARY KEY,
    batch_code      VARCHAR(50) NOT NULL,
    ma_ky           VARCHAR(20) NOT NULL REFERENCES dim_ky_baocao(ma_ky),
    table_name      VARCHAR(60) NOT NULL,
    records_fetched INTEGER NOT NULL,
    records_loaded  INTEGER NOT NULL,
    api_endpoint    VARCHAR(200),
    status          VARCHAR(30) DEFAULT 'SUCCESS',
    synced_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. BẢNG SỰ KIỆN ĐA KỲ (MULTI-PERIOD FACT TABLES - 12 BẢNG)
-- ------------------------------------------------------------------------------

-- Fact 1: Hạ Tầng Cơ Sở & Nghèo Đa Chiều Cấp Xã (146 xã x N kỳ)
DROP TABLE IF EXISTS fact_hatang_xa CASCADE;
CREATE TABLE fact_hatang_xa (
    ma_ky                      VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_xa                      VARCHAR(20) NOT NULL REFERENCES dim_diaban(ma_xa),
    ten_xa                     VARCHAR(100) NOT NULL,
    ma_huyen                   VARCHAR(20) NOT NULL,
    ten_huyen                  VARCHAR(100) NOT NULL,
    so_thon                    INTEGER DEFAULT 0,
    tong_ho_dtts               NUMERIC DEFAULT 0,
    so_ho_ngheo                NUMERIC DEFAULT 0,
    ty_le_ngheo_pct            NUMERIC(6, 2) DEFAULT 0.0,
    so_ho_can_ngheo            NUMERIC DEFAULT 0,
    ty_le_can_ngheo_pct        NUMERIC(6, 2) DEFAULT 0.0,
    km_den_trung_tam_huyen     NUMERIC(8, 2) DEFAULT 0.0,
    km_duong_nhua              NUMERIC(8, 2) DEFAULT 0.0,
    km_duong_be_tong           NUMERIC(8, 2) DEFAULT 0.0,
    so_thon_co_duong_cung      NUMERIC DEFAULT 0,
    ty_le_thon_duong_cung_pct  NUMERIC(6, 2) DEFAULT 0.0,
    so_thon_co_dien_luoi       NUMERIC DEFAULT 0,
    co_tram_y_te               NUMERIC DEFAULT 0,
    tram_y_te_dat_chuan        NUMERIC DEFAULT 0,
    tram_y_te_co_bac_si        NUMERIC DEFAULT 0,
    PRIMARY KEY (ma_ky, ma_xa)
);

-- Fact 2: Nhân Khẩu & Dân Số Cấp Huyện x Dân Tộc (197 cặp x N kỳ)
DROP TABLE IF EXISTS fact_danso_huyen_dantoc CASCADE;
CREATE TABLE fact_danso_huyen_dantoc (
    ma_ky          VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_huyen       VARCHAR(20) NOT NULL,
    ma_dantoc      VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    so_ho          BIGINT DEFAULT 0,
    ten_huyen      VARCHAR(100),
    ten_dantoc     VARCHAR(100),
    nhom_nguon_goc VARCHAR(100),
    PRIMARY KEY (ma_ky, ma_huyen, ma_dantoc)
);

-- Fact 3: Giáo Dục & Học Vấn Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_giaoduc_dantoc CASCADE;
CREATE TABLE fact_giaoduc_dantoc (
    ma_ky                        VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc                    VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    biet_chu_tong                NUMERIC DEFAULT 0,
    biet_chu_nam                 NUMERIC DEFAULT 0,
    biet_chu_nu                  NUMERIC DEFAULT 0,
    biet_chu_thanh_thi           NUMERIC DEFAULT 0,
    biet_chu_nong_thon           NUMERIC DEFAULT 0,
    ten_dantoc                   VARCHAR(100),
    nhom_nguon_goc               VARCHAR(100),
    la_dtts_it_nguoi             INTEGER DEFAULT 0,
    ty_le_nu_biet_chu_pct        NUMERIC(6, 2) DEFAULT 0.0,
    ty_le_nong_thon_biet_chu_pct NUMERIC(6, 2) DEFAULT 0.0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- Fact 4: Lao Động & Việc Làm Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_laodong_dantoc CASCADE;
CREATE TABLE fact_laodong_dantoc (
    ma_ky                        VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc                    VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    tong_lao_dong_co_viec_lam    NUMERIC DEFAULT 0,
    lao_dong_nong_nghiep         NUMERIC DEFAULT 0,
    lao_dong_cong_nghiep_xaydung NUMERIC DEFAULT 0,
    lao_dong_dich_vu             NUMERIC DEFAULT 0,
    lao_dong_nam                 NUMERIC DEFAULT 0,
    lao_dong_nu                  NUMERIC DEFAULT 0,
    ten_dantoc                   VARCHAR(100),
    nhom_nguon_goc               VARCHAR(100),
    ty_le_nong_nghiep_pct        NUMERIC(6, 2) DEFAULT 0.0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- Fact 5: Điều Kiện Sinh Hoạt Thiết Yếu Cấp Huyện x Dân Tộc (795 dòng x N kỳ)
DROP TABLE IF EXISTS fact_dantocthiet_yeu_huyen CASCADE;
CREATE TABLE fact_dantocthiet_yeu_huyen (
    ma_ky                            VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_huyen                         VARCHAR(20) NOT NULL,
    ma_dantoc                        VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    ty_le_nuoc_hop_ve_sinh_pct       NUMERIC(6, 2),
    ty_le_nuoc_hop_ve_sinh_pct_flag  VARCHAR(50),
    ty_le_ho_xi_hop_ve_sinh_pct      NUMERIC(6, 2),
    ty_le_ho_xi_hop_ve_sinh_pct_flag VARCHAR(50),
    so_ho_co_internet                NUMERIC,
    so_ho_co_internet_flag           VARCHAR(50),
    so_ho_co_dien_luoi               NUMERIC,
    so_ho_co_dien_luoi_flag          VARCHAR(50),
    ten_huyen                        VARCHAR(100),
    ten_dantoc                       VARCHAR(100),
    nhom_nguon_goc                   VARCHAR(100),
    PRIMARY KEY (ma_ky, ma_huyen, ma_dantoc)
);

-- Fact 6: Chất Lượng Nhà Ở Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_nhao_dantoc CASCADE;
CREATE TABLE fact_nhao_dantoc (
    ma_ky                     VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc                 VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    tong_so_ho_co_nha         NUMERIC DEFAULT 0,
    nha_kien_co_ban_kien_co   NUMERIC DEFAULT 0,
    nha_thieu_kien_co_don_so  NUMERIC DEFAULT 0,
    ten_dantoc                VARCHAR(100),
    nhom_nguon_goc            VARCHAR(100),
    ty_le_nha_tam_don_so_pct  NUMERIC(6, 2) DEFAULT 0.0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- Fact 7: Mức Sinh & Sức Khỏe Sinh Sản Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_mucsinh_dantoc CASCADE;
CREATE TABLE fact_mucsinh_dantoc (
    ma_ky                        VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc                    VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    ten_dantoc                   VARCHAR(100),
    nhom_nguon_goc               VARCHAR(100),
    sinh_con_thu_3_tro_len       NUMERIC DEFAULT 0,
    sinh_con_thu_3_thanh_thi     NUMERIC DEFAULT 0,
    sinh_con_thu_3_nong_thon     NUMERIC DEFAULT 0,
    sinh_tai_nha_tong            NUMERIC DEFAULT 0,
    sinh_tai_nha_co_ba_do        NUMERIC DEFAULT 0,
    sinh_tai_nha_khong_ba_do     NUMERIC DEFAULT 0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- Fact 8: Nhân Khẩu, Cơ Cấu Nhóm Tuổi & Giới Tính Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_nhankhau_dantoc CASCADE;
CREATE TABLE fact_nhankhau_dantoc (
    ma_ky                        VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc                    VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    ten_dantoc                   VARCHAR(100),
    nhom_nguon_goc               VARCHAR(100),
    tong_dan_so                  NUMERIC DEFAULT 0,
    dan_so_nam                   NUMERIC DEFAULT 0,
    dan_so_nu                    NUMERIC DEFAULT 0,
    dan_so_0_14                  NUMERIC DEFAULT 0,
    dan_so_15_59                 NUMERIC DEFAULT 0,
    dan_so_60_plus               NUMERIC DEFAULT 0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- Fact 9: Tình Trạng Nghiện Ma Túy & Nhiễm HIV/AIDS Cấp Xã (146 xã x N kỳ)
DROP TABLE IF EXISTS fact_matuy_hiv_xa CASCADE;
CREATE TABLE fact_matuy_hiv_xa (
    ma_ky                     VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_xa                     VARCHAR(20) NOT NULL REFERENCES dim_diaban(ma_xa),
    ten_xa                    VARCHAR(100),
    ma_huyen                  VARCHAR(20),
    ten_huyen                 VARCHAR(100),
    nguoi_nghien_ma_tuy_tong  NUMERIC DEFAULT 0,
    nguoi_dtts_nghien_ma_tuy  NUMERIC DEFAULT 0,
    nguoi_nhiem_hiv_tong      NUMERIC DEFAULT 0,
    nguoi_dtts_nhiem_hiv      NUMERIC DEFAULT 0,
    PRIMARY KEY (ma_ky, ma_xa)
);

-- Fact 10: Trình Độ Chuyên Môn Kỹ Thuật Lao Động Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_trinhdo_cmkt_dantoc CASCADE;
CREATE TABLE fact_trinhdo_cmkt_dantoc (
    ma_ky                  VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc              VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    ten_dantoc             VARCHAR(100),
    nhom_nguon_goc         VARCHAR(100),
    tong_lao_dong          NUMERIC DEFAULT 0,
    khong_co_cmkt          NUMERIC DEFAULT 0,
    ty_le_khong_cmkt_pct   NUMERIC(6, 2) DEFAULT 0,
    cnkt_khong_bang        NUMERIC DEFAULT 0,
    so_cap                 NUMERIC DEFAULT 0,
    trung_cap              NUMERIC DEFAULT 0,
    cao_dang_dai_hoc       NUMERIC DEFAULT 0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- Fact 11: Diện Tích Đất Sản Xuất Bình Quân Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_datsanxuat_dantoc CASCADE;
CREATE TABLE fact_datsanxuat_dantoc (
    ma_ky                  VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc              VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    ten_dantoc             VARCHAR(100),
    nhom_nguon_goc         VARCHAR(100),
    dien_tich_dat_sx_bq_m2 NUMERIC DEFAULT 0,
    dien_tich_dat_sx_bq_ha NUMERIC(8, 2) DEFAULT 0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- Fact 12: Tín Dụng Chính Sách & Nhu Cầu Vay Vốn Theo Dân Tộc (53 dân tộc x N kỳ)
DROP TABLE IF EXISTS fact_tindung_dantoc CASCADE;
CREATE TABLE fact_tindung_dantoc (
    ma_ky                     VARCHAR(20) NOT NULL DEFAULT 'KY_2024' REFERENCES dim_ky_baocao(ma_ky),
    ma_dantoc                 VARCHAR(20) NOT NULL REFERENCES dim_dantoc(ma_dantoc),
    ten_dantoc                VARCHAR(100),
    nhom_nguon_goc            VARCHAR(100),
    so_ho_da_vay_von          NUMERIC DEFAULT 0,
    so_ho_co_nhu_cau_vay      NUMERIC DEFAULT 0,
    tong_nhu_cau_ho           NUMERIC DEFAULT 0,
    ty_le_dap_ung_von_pct     NUMERIC(6, 2) DEFAULT 0,
    khoang_trong_tin_dung_pct NUMERIC(6, 2) DEFAULT 0,
    PRIMARY KEY (ma_ky, ma_dantoc)
);

-- ------------------------------------------------------------------------------
-- 3. CHỈ MỤC (INDEXES) TỐI ƯU HOÁ HIỆU NĂNG TRUY VẤN ĐA KỲ
-- ------------------------------------------------------------------------------
CREATE INDEX idx_ky_thutu ON dim_ky_baocao(thu_tu_ky);
CREATE INDEX idx_diaban_huyen ON dim_diaban(ma_huyen);
CREATE INDEX idx_hatang_ky_huyen ON fact_hatang_xa(ma_ky, ma_huyen);
CREATE INDEX idx_danso_ky_dantoc ON fact_danso_huyen_dantoc(ma_ky, ma_dantoc);
CREATE INDEX idx_thietyeu_ky_dantoc ON fact_dantocthiet_yeu_huyen(ma_ky, ma_dantoc);
CREATE INDEX idx_nhao_ky ON fact_nhao_dantoc(ma_ky);
CREATE INDEX idx_tindung_ky ON fact_tindung_dantoc(ma_ky);
CREATE INDEX idx_cmkt_ky ON fact_trinhdo_cmkt_dantoc(ma_ky);

-- ------------------------------------------------------------------------------
-- 4. VIEW PHÂN TÍCH TỔNG HỢP ĐA KỲ (INTEGRATED MULTI-PERIOD ANALYTICAL VIEW)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_dtts_tong_hop_dantoc AS
SELECT 
    k.ma_ky,
    k.thu_tu_ky,
    k.ten_ky,
    k.nam_moc,
    k.giai_doan_chinh_sach,
    k.is_latest,
    d.ma_dantoc,
    d.ten_dantoc,
    d.nhom_nguon_goc,
    d.la_dtts_it_nguoi,
    COALESCE(nk.tong_dan_so, 0) AS tong_dan_so,
    COALESCE(g.biet_chu_tong, 0) AS tong_nguoi_biet_chu,
    COALESCE(g.ty_le_nu_biet_chu_pct, 0) AS ty_le_nu_biet_chu_pct,
    COALESCE(l.tong_lao_dong_co_viec_lam, 0) AS tong_lao_dong,
    COALESCE(l.lao_dong_nong_nghiep, 0) AS lao_dong_nong_nghiep,
    COALESCE(l.ty_le_nong_nghiep_pct, 0) AS ty_le_nong_nghiep_pct,
    COALESCE(cm.khong_co_cmkt, 0) AS lao_dong_khong_cmkt,
    COALESCE(cm.ty_le_khong_cmkt_pct, 0) AS ty_le_khong_cmkt_pct,
    COALESCE(h.tong_so_ho_co_nha, 0) AS tong_ho_co_nha,
    COALESCE(h.nha_thieu_kien_co_don_so, 0) AS so_ho_nha_tam_don_so,
    COALESCE(h.ty_le_nha_tam_don_so_pct, 0) AS ty_le_nha_tam_pct,
    COALESCE(ds.dien_tich_dat_sx_bq_ha, 0) AS dien_tich_dat_sx_bq_ha,
    COALESCE(td.so_ho_co_nhu_cau_vay, 0) AS so_ho_khat_von,
    COALESCE(td.khoang_trong_tin_dung_pct, 0) AS khoang_trong_tin_dung_pct
FROM dim_ky_baocao k
CROSS JOIN dim_dantoc d
LEFT JOIN fact_nhankhau_dantoc nk ON k.ma_ky = nk.ma_ky AND d.ma_dantoc = nk.ma_dantoc
LEFT JOIN fact_giaoduc_dantoc g ON k.ma_ky = g.ma_ky AND d.ma_dantoc = g.ma_dantoc
LEFT JOIN fact_laodong_dantoc l ON k.ma_ky = l.ma_ky AND d.ma_dantoc = l.ma_dantoc
LEFT JOIN fact_trinhdo_cmkt_dantoc cm ON k.ma_ky = cm.ma_ky AND d.ma_dantoc = cm.ma_dantoc
LEFT JOIN fact_nhao_dantoc h ON k.ma_ky = h.ma_ky AND d.ma_dantoc = h.ma_dantoc
LEFT JOIN fact_datsanxuat_dantoc ds ON k.ma_ky = ds.ma_ky AND d.ma_dantoc = ds.ma_dantoc
LEFT JOIN fact_tindung_dantoc td ON k.ma_ky = td.ma_ky AND d.ma_dantoc = td.ma_dantoc;
