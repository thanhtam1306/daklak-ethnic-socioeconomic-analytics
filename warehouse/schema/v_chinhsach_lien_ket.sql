-- ==============================================================================
-- VIEW TỔNG HỢP ÁNH XẠ NGUỒN LỰC CHÍNH SÁCH THEO ĐỊA BÀN VÀ DÂN TỘC
-- CSDL: daklak_socioeconomic | Schema: daklak_analytics
-- ==============================================================================

SET search_path TO daklak_analytics, public;

CREATE OR REPLACE VIEW v_chinhsach_lien_ket AS
SELECT 
    'DANTOC' AS loai_doi_tuong,
    d.ma_dantoc AS ma_doi_tuong,
    d.ten_dantoc AS ten_doi_tuong,
    cs.ma_chinh_sach,
    cs.ten_chinh_sach,
    cs.can_cu_phap_ly,
    cs.nhom_linh_vuc,
    cs.doi_tuong_thu_huong,
    cs.nguon_von_thuc_hien,
    cs.muc_tieu_dinh_luong
FROM dim_dantoc d
JOIN dim_chinhsach_canthiep cs ON (
    (d.ten_dantoc = 'Gia Rai' AND cs.ma_chinh_sach = 'CS_ND28_TINDUNG_CSXH') OR
    (d.ten_dantoc = 'Chơ Ro' AND cs.ma_chinh_sach IN ('CS_1719_DA9_DTTS_ITNGUOI', 'CS_1719_DA1_NHAO')) OR
    (d.ten_dantoc = 'Mông' AND cs.ma_chinh_sach IN ('CS_1719_DA5_GIAODUC_NGHE', 'CS_1719_DA7_YTE_DANSO')) OR
    (d.ten_dantoc IN ('Chăm', 'Thổ', 'Co', 'Mảng', 'Bru - Vân Kiều', 'Thái', 'Chứt') AND cs.ma_chinh_sach = 'CS_1719_DA1_DATSX') OR
    (d.ten_dantoc = 'Ê Đê' AND cs.ma_chinh_sach IN ('CS_ND28_TINDUNG_CSXH', 'CS_1719_DA5_GIAODUC_NGHE', 'CS_1719_DA3_NONGNGHIEP'))
)

UNION ALL

SELECT 
    'DIABAN' AS loai_doi_tuong,
    db.ma_huyen AS ma_doi_tuong,
    db.ten_huyen AS ten_doi_tuong,
    cs.ma_chinh_sach,
    cs.ten_chinh_sach,
    cs.can_cu_phap_ly,
    cs.nhom_linh_vuc,
    cs.doi_tuong_thu_huong,
    cs.nguon_von_thuc_hien,
    cs.muc_tieu_dinh_luong
FROM (SELECT DISTINCT ma_huyen, ten_huyen FROM dim_diaban) db
JOIN dim_chinhsach_canthiep cs ON (
    (db.ten_huyen IN ('Huyện Krông Bông', 'Huyện Lắk', 'Huyện Krông Búk') AND cs.ma_chinh_sach = 'CS_QD318_NTM_TC17') OR
    (db.ten_huyen IN ('Huyện Ea H''leo', 'Huyện Krông Năng') AND cs.ma_chinh_sach = 'CS_LUAT_PCTMT_YTE') OR
    (db.ten_huyen IN ('Huyện Lắk', 'Huyện Ea Kar', 'Huyện M''Drắk') AND cs.ma_chinh_sach = 'CS_DEAN06_CHUYENDOI_SO') OR
    (db.ten_huyen IN ('Huyện Ea Súp', 'Huyện Lắk', 'Huyện M''Drắk') AND cs.ma_chinh_sach = 'CS_1719_DA4_HATANG')
);
