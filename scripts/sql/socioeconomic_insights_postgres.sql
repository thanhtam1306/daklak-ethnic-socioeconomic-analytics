-- BÀI TOÁN 1: TRỤ CỘT 1 - CHỈ SỐ NGHÈO ĐA CHIỀU & XẾP HẠNG TOP XÃ KHÓ KHĂN
with calculated_deprivation as (
	select
		d.ten_huyen,
		f.ten_xa,
		f.ty_le_ngheo_pct,
		f.ty_le_thon_duong_cung_pct,
        f.tram_y_te_dat_chuan,
        f.so_thon_co_dien_luoi,
        f.so_thon,
		-- Tính toán Điểm thiếu hụt đa chiều (Deprivation Score) tổng hợp
        -- Thang điểm chuẩn hóa từ 0 - 100 với trọng số giả định:
        -- 1. Tỷ lệ hộ nghèo DTTS: 40%
        -- 2. Tỷ lệ thiếu hụt đường giao thông cứng: 30%
        -- 3. Trạm y tế chưa đạt chuẩn (0: 100 điểm, 1: 0 điểm): 20%
        -- 4. Tỷ lệ thiếu hụt điện lưới thôn buôn: 10%
		(
			coalesce(f.ty_le_ngheo_pct, 0) * 0.40 +
			(100.0 - coalesce(f.ty_le_thon_duong_cung_pct, 0)) * 0.30 +
			(case when coalesce(f.tram_y_te_dat_chuan, 0) = 0 then 100.0 else 0.0 end) * 0.20 +
			(case when f.so_thon > 0 then (1.0 - (f.so_thon_co_dien_luoi::NUMERIC / f.so_thon)) * 100.0 else 0.0 end) * 0.10
		) as deprivation_score
	from
		daklak_analytics.fact_hatang_xa f
	join
		daklak_analytics.dim_diaban d on f.ma_xa = d.ma_xa
),
ranked_communes as (
	select 
		ten_huyen,
		ten_xa,
		ty_le_ngheo_pct,
		ty_le_thon_duong_cung_pct,
		tram_y_te_dat_chuan,
		so_thon_co_dien_luoi,
		so_thon,
		round(deprivation_score::NUMERIC, 2) as deprivation_score,
		-- Xếp hạng từ khó khăn nhất (điểm cao nhất) đến ít khó khăn nhất
		dense_rank() over (order by deprivation_score desc) as hardship_rank,
		-- Chia 146 xã thành 4 nhóm phân vị (Quartile 1: Đặc biệt khó khăn, Quartile 4: Thuận lợi)
		ntile(4) over (order by deprivation_score desc) as quartile_group
	from calculated_deprivation
)
select
	hardship_rank,
	ten_huyen,
	ten_xa,
	deprivation_score,
	ty_le_ngheo_pct,
	ty_le_thon_duong_cung_pct,
	tram_y_te_dat_chuan,
	concat(so_thon_co_dien_luoi, '/', so_thon) as thon_dien_luoi_ratio,
	quartile_group
from 
	ranked_communes
where
	hardship_rank <= 10
order by
	hardship_rank asc;


-- ==============================================================================
-- 🏛️ TRỤ CỘT 2: BẤT BÌNH ĐẲNG GIỚI & KHOẢNG CÁCH GIÁO DỤC (GENDER GAP IN EDUCATION)
-- Bài toán: Tìm Top 10 dân tộc có khoảng cách biết chữ Nam > Nữ lớn nhất (Gap %),
--           so sánh đối chứng giữa cấu trúc Phụ hệ (Di cư phía Bắc) vs Mẫu hệ (Bản địa Tây Nguyên).
-- Tiêu chuẩn: Lọc biet_chu_tong >= 100 để đảm bảo ý nghĩa thống kê, dùng RANK() OVER().
-- ==============================================================================

WITH ethnic_literacy AS (
    SELECT
        ten_dantoc,
        nhom_nguon_goc,
        biet_chu_tong,
        biet_chu_nam,
        biet_chu_nu,
        ROUND(100.0 * biet_chu_nam / NULLIF(biet_chu_tong, 0), 2) AS ty_le_nam_pct,
        ROUND(100.0 * biet_chu_nu / NULLIF(biet_chu_tong, 0), 2) AS ty_le_nu_pct,
        ROUND((100.0 * biet_chu_nam / NULLIF(biet_chu_tong, 0)) - (100.0 * biet_chu_nu / NULLIF(biet_chu_tong, 0)), 2) AS gender_gap_pct
    FROM daklak_analytics.fact_giaoduc_dantoc
    WHERE biet_chu_tong >= 100 -- Lọc quy mô mẫu có ý nghĩa thống kê
),
ranked_gap AS (
    SELECT
        *,
        RANK() OVER (ORDER BY gender_gap_pct DESC) AS rank_bat_binh_dang
    FROM ethnic_literacy
)
SELECT 
    rank_bat_binh_dang,
    ten_dantoc,
    nhom_nguon_goc,
    biet_chu_tong,
    ty_le_nam_pct,
    ty_le_nu_pct,
    gender_gap_pct
FROM ranked_gap
WHERE rank_bat_binh_dang <= 10
ORDER BY rank_bat_binh_dang ASC;


-- Phân tích đối soát tổng hợp theo Nhóm Nguồn Gốc (Phụ hệ vs Mẫu hệ):
SELECT 
    nhom_nguon_goc,
    COUNT(*) AS so_dantoc,
    SUM(biet_chu_tong) AS tong_biet_chu,
    SUM(biet_chu_nam) AS tong_nam_biet_chu,
    SUM(biet_chu_nu) AS tong_nu_biet_chu,
    ROUND(100.0 * SUM(biet_chu_nam) / NULLIF(SUM(biet_chu_tong), 0), 2) AS ty_le_nam_pct,
    ROUND(100.0 * SUM(biet_chu_nu) / NULLIF(SUM(biet_chu_tong), 0), 2) AS ty_le_nu_pct,
    ROUND(100.0 * (SUM(biet_chu_nam) - SUM(biet_chu_nu)) / NULLIF(SUM(biet_chu_tong), 0), 2) AS gap_pct
FROM daklak_analytics.fact_giaoduc_dantoc
GROUP BY nhom_nguon_goc
ORDER BY gap_pct DESC;

-- TRỤ CỘT 3: CƠ CẤU VIỆC LÀM & BẪY LAO ĐỘNG NÔNG NGHIỆP THUẦN TÚY
WITH labor_breakdown AS (
    SELECT
        ten_dantoc,
        nhom_nguon_goc,
        tong_lao_dong_co_viec_lam,
        lao_dong_nong_nghiep,
        lao_dong_cong_nghiep_xaydung,
        lao_dong_dich_vu,
		round(100.0 * lao_dong_nong_nghiep / nullif(tong_lao_dong_co_viec_lam, 0), 2) as ty_le_nong_nghiep_pct,
		round(100.0 * (lao_dong_cong_nghiep_xaydung + lao_dong_dich_vu) / nullif(tong_lao_dong_co_viec_lam, 0), 2) as ty_le_phi_nong_nghiep_pct,
		 -- Tính tỷ trọng đóng góp vào tổng lực lượng lao động DTTS toàn tỉnh (398.380 người):
		round(100.0 * tong_lao_dong_co_viec_lam / sum(tong_lao_dong_co_viec_lam) over(), 2) as ty_trong_lao_dong_tinh_pct
		from daklak_analytics.fact_laodong_dantoc
		where tong_lao_dong_co_viec_lam >= 500
),
ranked_labor as (
	select
		*,
		case 
			when ty_le_nong_nghiep_pct >= 90.0 then 'Bẫy nông nghiệp nghiêm trọng (>90%)'
			WHEN ty_le_nong_nghiep_pct >= 75.0 THEN 'Phụ thuộc nông nghiệp cao (75-90%)'
            ELSE 'Chuyển dịch tích cực (<75%)'
		end as phan_loai_chuyen_dich,
		rank() over (order by ty_le_nong_nghiep_pct desc) as rank_phu_thuoc_nong_nghiep
	from labor_breakdown
)
select
	rank_phu_thuoc_nong_nghiep,
	ten_dantoc,
    nhom_nguon_goc,
    tong_lao_dong_co_viec_lam,
    ty_trong_lao_dong_tinh_pct,
    ty_le_nong_nghiep_pct,
    ty_le_phi_nong_nghiep_pct,
    phan_loai_chuyen_dich
from ranked_labor
order by rank_phu_thuoc_nong_nghiep asc;

-- TRỤ CỘT 4: ĐIỂM NGHẼN ĐIỀU KIỆN VỆ SINH DÂN SINH & NƯỚC SẠCH
with district_hygiene as (
	select
		ten_huyen,
		round(avg(ty_le_ho_xi_hop_ve_sinh_pct), 2) as avg_hoxi_pct,
		round(avg(ty_le_nuoc_hop_ve_sinh_pct), 2) as avg_nuoc_pct,
		round(avg(so_ho_co_internet), 1) as avg_ho_internet
	from daklak_analytics.fact_dantocthiet_yeu_huyen
	where ty_le_ho_xi_hop_ve_sinh_pct is not null
	group by ten_huyen
),
ranked_districts as (
	select
		ten_huyen,
		avg_hoxi_pct,
		avg_nuoc_pct,
		avg_ho_internet,
		round(avg(avg_hoxi_pct) over(), 2) as bq_toan_tinh_pct,
		round(avg_hoxi_pct - avg(avg_hoxi_pct) over(), 2) as chenh_lech_so_voi_tinh,
		dense_rank() over (order by avg_hoxi_pct desc) as rank_vung_trung
	from district_hygiene
)
select
	rank_vung_trung,
    ten_huyen,
    avg_hoxi_pct,
    bq_toan_tinh_pct,
    chenh_lech_so_voi_tinh,
    avg_nuoc_pct,
    avg_ho_internet
from ranked_districts
order by rank_vung_trung asc;

-- TRỤ CỘT 5: ĐÁNH GIÁ ĐÒN BẨY HẠ TẦNG GIAO THÔNG & KHOẢNG CÁCH ĐỊA LÝ ĐẾN KHẢ NĂNG THOÁT NGHÈO
with distance_cohorts as (
	select 
		case
			WHEN km_den_trung_tam_huyen < 10.0 THEN '1. Rất gần (< 10km)'
            WHEN km_den_trung_tam_huyen < 20.0 THEN '2. Trung bình (10 - 19km)'
            WHEN km_den_trung_tam_huyen < 35.0 THEN '3. Xa (20 - 34km)'
            ELSE '4. Rất xa (>= 35km - Vùng sâu/biên giới)'
		end as phan_nhom_khoang_cach,
		so_thon,
		tong_ho_dtts,
		so_ho_ngheo,
		km_den_trung_tam_huyen
	from daklak_analytics.fact_hatang_xa
),
cohort_summary as (
	select
		phan_nhom_khoang_cach,
		count(*) as so_xa,
		sum(tong_ho_dtts) as tong_ho_dtts,
		sum(so_ho_ngheo) as tong_ho_ngheo,
		round(100.0 * sum(so_ho_ngheo) / nullif (sum(tong_ho_dtts), 0), 2) as ty_le_ngheo_bq_pct,
		round(avg(km_den_trung_tam_huyen), 1) as culy_trung_binh_km,
		round(100.0 * sum(so_ho_ngheo) / sum(sum(so_ho_ngheo)) over (), 2) as ty_trong_ho_ngheo_toan_tinh_pct
	from distance_cohorts
	group by phan_nhom_khoang_cach
)
select
	phan_nhom_khoang_cach,
    so_xa,
    tong_ho_dtts,
    tong_ho_ngheo,
    ty_le_ngheo_bq_pct,
    culy_trung_binh_km,
    ty_trong_ho_ngheo_toan_tinh_pct
FROM cohort_summary
ORDER BY phan_nhom_khoang_cach ASC;

-- KHOẢNG CÁCH SỐ & KHẢ NĂNG TIẾP CẬN DỊCH VỤ CÔNG TRỰC TUYẾN
-- 1A: Xếp hạng Tỷ lệ tiếp cận Internet theo Huyện (Tìm vùng trũng số)
with district_internet as (
	select
		f.ten_huyen,
		sum(f.so_ho_co_internet) as tong_ho_co_internet,
		sum(d.so_ho) as tong_so_ho_dtts,
		round(100.0 * sum(f.so_ho_co_internet) / NULLIF(sum(d.so_ho), 0), 2) as ty_le_internet_pct,
		round(avg(100.0 * sum(f.so_ho_co_internet) / NULLIF(sum(d.so_ho), 0)) over(), 2) as bq_tinh_pct
	from daklak_analytics.fact_dantocthiet_yeu_huyen f
	join daklak_analytics.fact_danso_huyen_dantoc d on f.ma_huyen = d.ma_huyen and f.ma_dantoc = d.ma_dantoc
	where f.so_ho_co_internet is not null
	group by f.ten_huyen
)
select
	dense_rank() over(order by ty_le_internet_pct desc) as rank_vung_trung_so,
	ten_huyen,
    tong_ho_co_internet,
    tong_so_ho_dtts,
    ty_le_internet_pct,
    bq_tinh_pct,
	round(ty_le_internet_pct - bq_tinh_pct, 2) as gap_so_voi_tinh
from district_internet
order by rank_vung_trung_so asc;

-- 1B: Phân tích tiếp cận Internet theo Nhóm Nguồn Gốc & Top Dân Tộc
SELECT
	d.nhom_nguon_goc,
	sum(f.so_ho_co_internet) as tong_ho_co_internet,
	sum(d.so_ho) as tong_so_ho_dtts,
	round(100.0 * sum(f.so_ho_co_internet) / NULLIF(sum(d.so_ho), 0), 2) as ty_le_internet_pct
from daklak_analytics.fact_dantocthiet_yeu_huyen f
JOIN daklak_analytics.fact_danso_huyen_dantoc d on f.ma_huyen = d.ma_huyen and f.ma_dantoc = d.ma_dantoc
where f.so_ho_co_internet is not null
group by d.nhom_nguon_goc
order by ty_le_internet_pct asc;

-- BẢO TỒN VÀ RỦI RO TỔN THƯƠNG CỦA CÁC DÂN TỘC THIỂU SỐ RẤT ÍT NGƯỜI (< 10.000 NGƯỜI)
with small_ethnic_groups as (
	select 
		d.ten_dantoc,
		d.nhom_nguon_goc,
		d.la_dtts_it_nguoi,
		h.tong_so_ho_co_nha,
        h.nha_kien_co_ban_kien_co,
        h.nha_thieu_kien_co_don_so,
        h.ty_le_nha_tam_don_so_pct,
        l.tong_lao_dong_co_viec_lam,
        l.ty_le_nong_nghiep_pct,
        g.ty_le_nu_biet_chu_pct
	from daklak_analytics.dim_dantoc d
	join daklak_analytics.fact_nhao_dantoc h on d.ma_dantoc = h.ma_dantoc
	join daklak_analytics.fact_laodong_dantoc l on d.ma_dantoc = l.ma_dantoc
	join daklak_analytics.fact_giaoduc_dantoc g on d.ma_dantoc = g.ma_dantoc
	where h.tong_so_ho_co_nha > 0 and h.tong_so_ho_co_nha < 100
),
ranked_vulnerability as (
	select 
		*,
		dense_rank() over(order by ty_le_nha_tam_don_so_pct desc, tong_so_ho_co_nha asc) as rank_nguy_co_nha_o
	from small_ethnic_groups
)
select 
	rank_nguy_co_nha_o,
    ten_dantoc,
    nhom_nguon_goc,
    tong_so_ho_co_nha,
    nha_thieu_kien_co_don_so,
    ty_le_nha_tam_don_so_pct,
    tong_lao_dong_co_viec_lam,
    ty_le_nong_nghiep_pct,
    ty_le_nu_biet_chu_pct
from ranked_vulnerability
order by rank_nguy_co_nha_o asc;

-- ÁP LỰC DÂN SỐ, MỨC SINH CAO & NGUY CƠ TỬ VONG MẸ - BÉ TRONG SINH NỞ
WITH full_provincial_benchmark AS (
    SELECT 
        ma_dantoc,
        ten_dantoc,
        nhom_nguon_goc,
        sinh_tai_nha_tong,
        sinh_tai_nha_khong_ba_do,
        sinh_con_thu_3_tro_len,
        -- Tính tổng toàn tỉnh trước khi lọc (tránh bẫy Order of Execution)
        SUM(sinh_tai_nha_tong) OVER () AS tong_tinh_sinh_nha,
        SUM(sinh_con_thu_3_tro_len) OVER () AS tong_tinh_sinh_con_3
    FROM daklak_analytics.fact_mucsinh_dantoc
)
SELECT 
    DENSE_RANK() OVER (ORDER BY sinh_tai_nha_khong_ba_do DESC) AS xep_hang_rui_ro,
    ten_dantoc,
    nhom_nguon_goc,
    sinh_tai_nha_tong,
    sinh_tai_nha_khong_ba_do,
    ROUND(CAST(sinh_tai_nha_khong_ba_do AS NUMERIC) / NULLIF(sinh_tai_nha_tong, 0) * 100, 2) AS ty_le_khong_ba_do_pct,
    ROUND(CAST(sinh_tai_nha_tong AS NUMERIC) / NULLIF(tong_tinh_sinh_nha, 0) * 100, 2) AS ty_trong_sinh_tai_nha_toan_tinh_pct,
    sinh_con_thu_3_tro_len,
    ROUND(CAST(sinh_con_thu_3_tro_len AS NUMERIC) / NULLIF(tong_tinh_sinh_con_3, 0) * 100, 2) AS ty_trong_sinh_con_3_toan_tinh_pct
FROM full_provincial_benchmark
WHERE sinh_tai_nha_tong > 0
ORDER BY xep_hang_rui_ro ASC, sinh_tai_nha_tong DESC;

-- CƠ CẤU DÂN SỐ, THÁP TUỔI & GÁNH NẶNG PHỤ THUỘC
WITH demographic_indicators AS (
    SELECT 
        ma_dantoc,
        ten_dantoc,
        nhom_nguon_goc,
        tong_dan_so,
        dan_so_0_14,
        dan_so_15_59,
        dan_so_60_plus,
		round(cast(dan_so_0_14 as numeric) / NULLIF(dan_so_15_59, 0) * 100, 2) as ty_le_phu_thuoc_tre_em_pct,
		round(cast(dan_so_60_plus as numeric) / NULLIF(dan_so_15_59, 0) * 100, 2) as ty_le_phu_thuoc_gia_pct,
		round(cast(dan_so_0_14 + dan_so_60_plus as numeric) / NULLIF(dan_so_15_59, 0) * 100, 2) as ty_le_phu_thuoc_chung_pct,
		round(cast(dan_so_60_plus as numeric) / NULLIF(dan_so_0_14, 0) * 100, 2) as chi_so_gia_hoa_pct
	from daklak_analytics.fact_nhankhau_dantoc
	where tong_dan_so >= 500
),
classified_demographics as (
	select
		*,
		case
			when chi_so_gia_hoa_pct >= 30.0 then 'Bắt đầu già hoá'
			when ty_le_phu_thuoc_tre_em_pct >= 60.0 then 'Dân số siêu trẻ - Gánh nặng con nhỏ cực cao'
			else 'Cơ cấu dân số vàng'
		end as phan_loai_nhan_khau,
		dense_rank() over(order by ty_le_phu_thuoc_chung_pct desc) as rank_ganh_nang_phu_thuoc
	from demographic_indicators
)
SELECT
	rank_ganh_nang_phu_thuoc,
    ten_dantoc,
    nhom_nguon_goc,
    tong_dan_so,
    dan_so_0_14,
    dan_so_15_59,
    dan_so_60_plus,
    ty_le_phu_thuoc_tre_em_pct,
    ty_le_phu_thuoc_gia_pct,
    ty_le_phu_thuoc_chung_pct,
    chi_so_gia_hoa_pct,
    phan_loai_nhan_khau
FROM classified_demographics
ORDER BY rank_ganh_nang_phu_thuoc ASC;

-- MA TRẬN TƯƠNG QUAN PEARSON & HỒI QUY TUYẾN TÍNH GIỮA HẠ TẦNG VÀ NGHÈO ĐÓI
SELECT 
    -- 1. Hệ số tương quan Pearson (r) với Tỷ lệ nghèo của 146 xã
    ROUND(CAST(CORR(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 4) AS r_khoang_cach_huyen,
    ROUND(CAST(CORR(ty_le_ngheo_pct, ty_le_thon_duong_cung_pct) AS NUMERIC), 4) AS r_ty_le_duong_cung,
    ROUND(CAST(CORR(ty_le_ngheo_pct, km_duong_be_tong) AS NUMERIC), 4) AS r_km_duong_be_tong,
    ROUND(CAST(CORR(ty_le_ngheo_pct, ty_le_can_ngheo_pct) AS NUMERIC), 4) AS r_ty_le_can_ngheo,
    
    -- 2. Hệ số xác định R2 (Khoảng cách giải thích được bao nhiêu % sự biến thiên của đói nghèo)
    ROUND(CAST(REGR_R2(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 4) AS r2_khoang_cach,
    
    -- 3. Hệ số góc hồi quy (Slope: Cứ cách xa huyện thêm 1 km, tỷ lệ nghèo tăng bao nhiêu %)
    ROUND(CAST(REGR_SLOPE(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 4) AS he_so_goc_slope_khoang_cach,
    
    -- 4. Tỷ lệ nghèo nền tảng tại trung tâm huyện (Intercept khi khoảng cách = 0 km)
    ROUND(CAST(REGR_INTERCEPT(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 2) AS ty_le_ngheo_co_so_intercept
FROM daklak_analytics.fact_hatang_xa;

-- MA TRẬN PHÂN HÓA 2X2 (KHOẢNG CÁCH ĐỊA LÝ X HẠ TẦNG ĐƯỜNG CỨNG)
WITH commune_quadrant AS (
    SELECT 
        ten_xa,
        ten_huyen,
        ty_le_ngheo_pct,
        km_den_trung_tam_huyen,
        ty_le_thon_duong_cung_pct,
        CASE 
            WHEN km_den_trung_tam_huyen < 20 AND ty_le_thon_duong_cung_pct >= 70 THEN '1. Thuận lợi kép (Gần <20km & Đường tốt >=70%)'
            WHEN km_den_trung_tam_huyen < 20 AND ty_le_thon_duong_cung_pct < 70 THEN '2. Gần nhưng nghẽn giao thông (<70%)'
            WHEN km_den_trung_tam_huyen >= 20 AND ty_le_thon_duong_cung_pct >= 70 THEN '3. Vùng xa (>=20km) nhưng đường đã cứng hóa'
            ELSE '4. Khó khăn kép (Xa >=20km & Đường xấu <70%)'
        END AS phan_nhom_ha_tang
    FROM daklak_analytics.fact_hatang_xa
)
SELECT 
    phan_nhom_ha_tang,
    COUNT(*) AS so_luong_xa,
    ROUND(AVG(km_den_trung_tam_huyen), 1) AS culy_trung_binh_km,
    ROUND(AVG(ty_le_thon_duong_cung_pct), 1) AS duong_cung_trung_binh_pct,
    ROUND(AVG(ty_le_ngheo_pct), 2) AS ty_le_ngheo_trung_binh_pct
FROM commune_quadrant
GROUP BY phan_nhom_ha_tang
ORDER BY ty_le_ngheo_trung_binh_pct ASC;

-- ==============================================================================
-- 🔬 CHUYÊN ĐỀ 6: TỆ NẠN XÃ HỘI, NGHIỆN MA TÚY & NGUY CƠ LÂY NHIỄM HIV/AIDS VÙNG DTTS
-- Bài toán: Phân tích 15 huyện và 146 xã để định vị "Tâm chấn ma túy & HIV/AIDS"
-- Kỹ thuật: GROUP BY huyện, Window functions SUM OVER, DENSE_RANK, Top 10 Xã
-- ==============================================================================

-- 6A: XẾP HẠNG TÂM CHẤN MA TÚY & HIV/AIDS THEO HUYỆN
WITH district_summary AS (
    SELECT 
        ten_huyen,
        SUM(nguoi_nghien_ma_tuy_tong) AS ma_tuy_tong,
        SUM(nguoi_dtts_nghien_ma_tuy) AS ma_tuy_dtts,
        SUM(nguoi_nhiem_hiv_tong) AS hiv_tong,
        SUM(nguoi_dtts_nhiem_hiv) AS hiv_dtts
    FROM daklak_analytics.fact_matuy_hiv_xa
    GROUP BY ten_huyen
),
ranked_districts AS (
    SELECT 
        ten_huyen,
        ma_tuy_tong,
        ma_tuy_dtts,
        ROUND(CAST(ma_tuy_dtts AS NUMERIC) / NULLIF(ma_tuy_tong, 0) * 100, 2) AS ty_le_ma_tuy_la_dtts_pct,
        ROUND(CAST(ma_tuy_dtts AS NUMERIC) / NULLIF(SUM(ma_tuy_dtts) OVER (), 0) * 100, 2) AS ty_trong_ma_tuy_dtts_toan_tinh_pct,
        hiv_tong,
        hiv_dtts,
        ROUND(CAST(hiv_dtts AS NUMERIC) / NULLIF(hiv_tong, 0) * 100, 2) AS ty_le_hiv_la_dtts_pct,
        ROUND(CAST(hiv_dtts AS NUMERIC) / NULLIF(SUM(hiv_dtts) OVER (), 0) * 100, 2) AS ty_trong_hiv_dtts_toan_tinh_pct,
        DENSE_RANK() OVER (ORDER BY ma_tuy_dtts DESC, hiv_dtts DESC) AS rank_diem_nong_ma_tuy,
        DENSE_RANK() OVER (ORDER BY hiv_dtts DESC, ma_tuy_dtts DESC) AS rank_diem_nong_hiv
    FROM district_summary
)
SELECT 
    rank_diem_nong_ma_tuy,
    ten_huyen,
    ma_tuy_tong,
    ma_tuy_dtts,
    ty_le_ma_tuy_la_dtts_pct,
    ty_trong_ma_tuy_dtts_toan_tinh_pct,
    hiv_tong,
    hiv_dtts,
    ty_le_hiv_la_dtts_pct,
    ty_trong_hiv_dtts_toan_tinh_pct
FROM ranked_districts
ORDER BY ma_tuy_dtts DESC;

-- 6B: TOP 10 XÃ "TÂM CHẤN KÉP" MA TÚY & HIV/AIDS VÙNG ĐỒNG BÀO DTTS
SELECT 
    DENSE_RANK() OVER (ORDER BY nguoi_dtts_nghien_ma_tuy DESC, nguoi_dtts_nhiem_hiv DESC) AS rank_xa,
    ten_xa,
    ten_huyen,
    nguoi_nghien_ma_tuy_tong,
    nguoi_dtts_nghien_ma_tuy,
    ROUND(CAST(nguoi_dtts_nghien_ma_tuy AS NUMERIC) / NULLIF(nguoi_nghien_ma_tuy_tong, 0) * 100, 2) AS ty_le_ma_tuy_dtts_pct,
    nguoi_nhiem_hiv_tong,
    nguoi_dtts_nhiem_hiv
FROM daklak_analytics.fact_matuy_hiv_xa
WHERE nguoi_dtts_nghien_ma_tuy > 0 OR nguoi_dtts_nhiem_hiv > 0
ORDER BY nguoi_dtts_nghien_ma_tuy DESC, nguoi_dtts_nhiem_hiv DESC
LIMIT 10;

-- ==============================================================================
-- 🔬 CHUYÊN ĐỀ 7: CHẤT LƯỢNG NGUỒN NHÂN LỰC & BẪY LAO ĐỘNG KHÔNG BẰNG CẤP (87.36%)
-- Bài toán: Bóc tách trình độ CMKT của 398.381 lao động DTTS toàn tỉnh,
--           tìm Top dân tộc có tỷ lệ lao động phổ thông không bằng cấp cao nhất.
-- ==============================================================================

SELECT 
    DENSE_RANK() OVER (ORDER BY ty_le_khong_cmkt_pct DESC, tong_lao_dong DESC) AS rank_thieu_ky_nang,
    ten_dantoc,
    nhom_nguon_goc,
    tong_lao_dong,
    khong_co_cmkt,
    ty_le_khong_cmkt_pct,
    ROUND(100.0 - ty_le_khong_cmkt_pct, 2) AS ty_le_co_cmkt_pct,
    so_cap,
    trung_cap,
    cao_dang_dai_hoc
FROM daklak_analytics.fact_trinhdo_cmkt_dantoc
WHERE tong_lao_dong >= 500
ORDER BY ty_le_khong_cmkt_pct DESC;

-- ==============================================================================
-- 🔬 CHUYÊN ĐỀ 8: TƯ LIỆU SẢN XUẤT - BẤT BÌNH ĐẲNG ĐẤT CANH TÁC (LAND SCARCITY)
-- Bài toán: Phân tích diện tích đất sản xuất bình quân của 53 dân tộc tại Đắk Lắk,
--           phân loại 4 nhóm quy mô và so sánh với mức bình quân tỉnh (10.529,6 m2).
-- ==============================================================================

WITH provincial_avg AS (
    SELECT 10529.6 AS bq_tinh_m2
)
SELECT 
    DENSE_RANK() OVER (ORDER BY dien_tich_dat_sx_bq_m2 ASC) AS rank_khan_hiem_dat,
    ten_dantoc,
    nhom_nguon_goc,
    dien_tich_dat_sx_bq_m2,
    dien_tich_dat_sx_bq_ha,
    ROUND(dien_tich_dat_sx_bq_m2 - p.bq_tinh_m2, 1) AS chenh_lech_so_voi_tinh_m2,
    CASE 
        WHEN dien_tich_dat_sx_bq_m2 < 5000 THEN '1. Thiếu đất nghiêm trọng (<0.5 ha)'
        WHEN dien_tich_dat_sx_bq_m2 < 10000 THEN '2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha)'
        WHEN dien_tich_dat_sx_bq_m2 < 20000 THEN '3. Đủ đất cơ bản (1.0 - 2.0 ha)'
        ELSE '4. Quy mô đất lớn (>=2.0 ha)'
    END AS phan_loai_quy_mo_dat
FROM daklak_analytics.fact_datsanxuat_dantoc
CROSS JOIN provincial_avg p
WHERE dien_tich_dat_sx_bq_m2 > 0
ORDER BY dien_tich_dat_sx_bq_m2 ASC;

-- ==============================================================================
-- 🔬 CHUYÊN ĐỀ 9: "KHÁT VỐN" & KHOẢNG TRỐNG TÍN DỤNG CHÍNH SÁCH (CREDIT GAP)
-- Bài toán: Phân tích số hộ đã vay vs số hộ có nhu cầu vay vốn Ngân hàng CSXH,
--           đo lường tỷ lệ đáp ứng vốn và khoảng trống tín dụng chưa được phủ sóng.
-- ==============================================================================

SELECT 
    DENSE_RANK() OVER (ORDER BY so_ho_co_nhu_cau_vay DESC) AS rank_khat_von,
    ten_dantoc,
    nhom_nguon_goc,
    so_ho_da_vay_von,
    so_ho_co_nhu_cau_vay,
    tong_nhu_cau_ho,
    ty_le_dap_ung_von_pct,
    khoang_trong_tin_dung_pct
FROM daklak_analytics.fact_tindung_dantoc
WHERE tong_nhu_cau_ho >= 100
ORDER BY so_ho_co_nhu_cau_vay DESC;