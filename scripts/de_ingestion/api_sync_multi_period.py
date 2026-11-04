"""
==============================================================================
ROLE: DATA ENGINEER (DE) - MULTI-PERIOD API INGESTION & DYNAMIC SCHEMA PIPELINE
File: scripts/de_ingestion/api_sync_multi_period.py
Dự án: Phân Tích Thực Trạng KTXH 53 Dân Tộc Thiểu Số Tỉnh Đắk Lắk
Mục tiêu:
  1. Thiết lập bảng chiều Thời gian động `dim_ky_baocao` (KY_2019, KY_2024, KY_2026)
     với khóa tuần tự `thu_tu_ky` (1, 2, 3...) và cờ `is_latest` tự động co giãn.
  2. Thiết lập bảng chiều Chỉ tiêu Kế hoạch & Định mức Ngân sách
     `dim_chitieu_kehoach_ngansach` theo từng giai đoạn chính sách (2016-2020,
     2021-2025, 2026-2030).
  3. Giả lập luồng đồng bộ REST API từ Cổng Dữ liệu Thống kê KTXH Dân tộc thiểu số,
     bơm dữ liệu 3 kỳ (`KY_2019`, `KY_2024` [100% Ground-Truth], `KY_2026` [Đầu GĐ
     2026-2030]) vào Parquet, PostgreSQL 18 (`daklak_analytics`) và DuckDB.
==============================================================================
"""

import os
import sys
import shutil
import json
from datetime import datetime
import numpy as np
import pandas as pd
import duckdb
import psycopg2
from sqlalchemy import create_engine, text

if sys.stdout and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Cấu hình kết nối PostgreSQL 18
DB_USER = os.getenv('PGUSER', 'postgres')
DB_PASS = os.getenv('PGPASSWORD', '123456')
DB_HOST = os.getenv('PGHOST', 'localhost')
DB_PORT = os.getenv('PGPORT', '5432')
DB_NAME = 'daklak_socioeconomic'
SCHEMA_NAME = 'daklak_analytics'

PROCESSED_DIR = 'data/processed'
BACKUP_2024_DIR = 'data/processed/single_period_2024_backup'
API_PAYLOAD_DIR = 'data/processed/api_payloads'

FACT_TABLES = [
    'fact_hatang_xa',
    'fact_danso_huyen_dantoc',
    'fact_giaoduc_dantoc',
    'fact_laodong_dantoc',
    'fact_dantocthiet_yeu_huyen',
    'fact_nhao_dantoc',
    'fact_mucsinh_dantoc',
    'fact_nhankhau_dantoc',
    'fact_matuy_hiv_xa',
    'fact_trinhdo_cmkt_dantoc',
    'fact_datsanxuat_dantoc',
    'fact_tindung_dantoc',
]


def backup_single_period_2024():
    """Sao lưu nguyên trạng bộ Parquet 2024 (1 kỳ) để đảm bảo tính Idempotent 100%."""
    os.makedirs(BACKUP_2024_DIR, exist_ok=True)
    os.makedirs(API_PAYLOAD_DIR, exist_ok=True)
    for tbl in FACT_TABLES:
        src = os.path.join(PROCESSED_DIR, f"{tbl}.parquet")
        dst = os.path.join(BACKUP_2024_DIR, f"{tbl}.parquet")
        if not os.path.exists(dst) and os.path.exists(src):
            df_check = pd.read_parquet(src)
            if 'ma_ky' not in df_check.columns:
                shutil.copy2(src, dst)
            else:
                df_2024 = df_check[df_check['ma_ky'] == 'KY_2024'].drop(columns=['ma_ky'])
                df_2024.to_parquet(dst, index=False)
    print(f"[DE-BACKUP] Đã khóa bản sao lưu chuẩn 2024 (Ground-Truth) tại: {BACKUP_2024_DIR}")


def build_dim_ky_baocao() -> pd.DataFrame:
    """
    Xây dựng bảng chiều Thời gian / Chu kỳ điều tra `dim_ky_baocao`.
    Sử dụng `thu_tu_ky` (1, 2, 3...) để SQL LAG() và DAX Time Intelligence
    tự động co giãn khi bước sang kỳ 2030-2034 mà không phụ thuộc khoảng cách năm.
    """
    rows = [
        {
            'ma_ky': 'KY_2019',
            'thu_tu_ky': 1,
            'ten_ky': 'Kỳ Điều tra 2019',
            'nam_moc': 2019,
            'giai_doan_chinh_sach': '2016-2020',
            'loai_dieu_tra': 'Điều tra 53 DTTS Lần II (UBDT & TCTK - Trước MTQG 1719)',
            'is_latest': False,
            'ngay_dong_bo_api': datetime(2020, 6, 15, 8, 30, 0),
        },
        {
            'ma_ky': 'KY_2024',
            'thu_tu_ky': 2,
            'ten_ky': 'Kỳ Điều tra 2024',
            'nam_moc': 2024,
            'giai_doan_chinh_sach': '2021-2025',
            'loai_dieu_tra': 'Điều tra 53 DTTS Lần III (UBDT & TCTK - Giữa kỳ MTQG 1719 GĐ I)',
            'is_latest': False,
            'ngay_dong_bo_api': datetime(2025, 1, 10, 9, 0, 0),
        },
        {
            'ma_ky': 'KY_2026',
            'thu_tu_ky': 3,
            'ten_ky': 'Kỳ Rà soát 2026 (GĐ 2026-2030)',
            'nam_moc': 2026,
            'giai_doan_chinh_sach': '2026-2030',
            'loai_dieu_tra': 'Rà soát Đầu kỳ MTQG 1719 Giai đoạn II (API Đồng bộ Liên thông)',
            'is_latest': True,
            'ngay_dong_bo_api': datetime(2026, 10, 23, 14, 15, 0),
        },
    ]
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(PROCESSED_DIR, 'dim_ky_baocao.parquet'), index=False)
    df.to_csv(os.path.join(PROCESSED_DIR, 'dim_ky_baocao.csv'), index=False, encoding='utf-8-sig')
    print(f"[DE-SCHEMA] Đã khởi tạo `dim_ky_baocao`: {len(df)} chu kỳ (KY_2019 -> KY_2024 -> KY_2026 [is_latest=True])")
    return df


def build_dim_chitieu_kehoach_ngansach() -> pd.DataFrame:
    """
    Xây dựng bảng chiều Chỉ tiêu Kế hoạch & Định mức Ngân sách Nhà nước
    qua 3 giai đoạn: 2016-2020, 2021-2025 và 2026-2030.
    """
    specs = [
        # 1. Tỷ lệ hộ nghèo DTTS
        ('TY_LE_HO_NGHEO', 'Tỷ lệ hộ nghèo vùng DTTS', 'CS_1719_DA3_NONGNGHIEP', '%', 'GIAM',
         [('2016-2020', 22.0, 15000000, 15.0), ('2021-2025', 15.0, 25000000, 25.0), ('2026-2030', 10.0, 30000000, 30.0)],
         'QĐ 1719/QĐ-TTg (Mục tiêu giảm nghèo vùng DTTS >3%/năm) & Chuẩn nghèo đa chiều 2026-2030 (Hỗ trợ sinh kế 25-30 tr.đ/hộ)'),
        # 2. Tỷ lệ nhà tạm, dột nát
        ('TY_LE_NHA_TAM', 'Tỷ lệ hộ DTTS ở nhà tạm, đơn sơ', 'CS_1719_DA1_NHAO', '%', 'GIAM',
         [('2016-2020', 8.0, 60000000, 60.0), ('2021-2025', 2.0, 80000000, 80.0), ('2026-2030', 0.0, 90000000, 90.0)],
         'Dự án 1 MTQG 1719 & NĐ 28/2022/NĐ-CP (GĐ 2021-2025: 40tr NSTW + 40tr vay = 80 tr.đ/hộ; GĐ 2026-2030 nâng lên 90 tr.đ/hộ)'),
        # 3. Tỷ lệ hố xí hợp vệ sinh (Tiêu chí 17 NTM)
        ('TY_LE_HO_XI_HVS', 'Tỷ lệ hộ DTTS có nhà tiêu hợp vệ sinh', 'CS_QD318_NTM_TC17', '%', 'TANG',
         [('2016-2020', 55.0, 8000000, 8.0), ('2021-2025', 70.0, 10000000, 10.0), ('2026-2030', 85.0, 12000000, 12.0)],
         'QĐ 318/QĐ-TTg Tiêu chí 17 Nông thôn mới & Vốn Nước sạch VSMT nông thôn (10-12 tr.đ/công trình)'),
        # 4. Tỷ lệ nước sinh hoạt hợp vệ sinh
        ('TY_LE_NUOC_HVS', 'Tỷ lệ hộ DTTS dùng nước sinh hoạt hợp vệ sinh', 'CS_1719_DA1_NUOCSH', '%', 'TANG',
         [('2016-2020', 85.0, 2500000, 2.5), ('2021-2025', 92.0, 3000000, 3.0), ('2026-2030', 98.0, 4000000, 4.0)],
         'Dự án 1 MTQG 1719 - Hỗ trợ nước sinh hoạt phân tán (3-4 tr.đ/hộ)'),
        # 5. Tỷ lệ lao động chưa qua đào tạo CMKT
        ('TY_LE_CHUA_DAO_TAO_CMKT', 'Tỷ lệ lao động DTTS chưa qua đào tạo CMKT', 'CS_1719_DA5_GIAODUC_NGHE', '%', 'GIAM',
         [('2016-2020', 85.0, 3500000, 3.5), ('2021-2025', 75.0, 4500000, 4.5), ('2026-2030', 60.0, 6000000, 6.0)],
         'Tiểu dự án 3 Dự án 5 MTQG 1719 & QĐ 46/2015/QĐ-TTg (Chi phí đào tạo nghề sơ cấp 4.5 - 6.0 tr.đ/lao động)'),
        # 6. Khoảng trống tín dụng chính sách
        ('KHOANG_TRONG_TIN_DUNG', 'Tỷ lệ hộ có nhu cầu vay vốn chưa được đáp ứng', 'CS_ND28_TINDUNG_CSXH', '%', 'GIAM',
         [('2016-2020', 40.0, 40000000, 40.0), ('2021-2025', 20.0, 50000000, 50.0), ('2026-2030', 10.0, 65000000, 65.0)],
         'Nghị định 28/2022/NĐ-CP qua NHCSXH (Hạn mức vay bình quân 50 tr.đ/hộ GĐ I; nâng lên 65 tr.đ/hộ GĐ 2026-2030)'),
        # 7. Diện tích đất sản xuất bình quân
        ('DAT_SX_BINH_QUAN', 'Diện tích đất sản xuất nông nghiệp tối thiểu', 'CS_1719_DA1_DATSX', 'ha/hộ', 'TANG',
         [('2016-2020', 0.40, 20000000, 20.0), ('2021-2025', 0.50, 30000000, 30.0), ('2026-2030', 0.60, 40000000, 40.0)],
         'Dự án 1 MTQG 1719 - Định mức đất sản xuất tối thiểu 0.5-0.6 ha/hộ hoặc hỗ trợ chuyển đổi nghề 30-40 tr.đ/hộ'),
        # 8. Tỷ lệ hộ kết nối Internet băng rộng
        ('TY_LE_INTERNET', 'Tỷ lệ hộ DTTS kết nối Internet băng rộng', 'CS_DEAN06_CHUYENDOI_SO', '%', 'TANG',
         [('2016-2020', 50.0, 1000000, 1.0), ('2021-2025', 80.0, 1500000, 1.5), ('2026-2030', 95.0, 2000000, 2.0)],
         'Đề án 06/QĐ-TTg & Quỹ Dịch vụ Viễn thông Công ích (Hạ tầng số thôn buôn & thiết bị đầu cuối 1.5-2.0 tr.đ/hộ)'),
        # 9. Số ca sinh con tại nhà (Làm mẹ an toàn)
        ('CA_SINH_TAI_NHA', 'Số ca phụ nữ DTTS sinh con tại nhà', 'CS_1719_DA7_YTE_DANSO', 'Ca', 'GIAM',
         [('2016-2020', 500.0, 2000000, 2.0), ('2021-2025', 100.0, 3000000, 3.0), ('2026-2030', 0.0, 4500000, 4.5)],
         'Dự án 7 MTQG 1719 - Gói đỡ đẻ an toàn & phụ cấp Cô đỡ thôn bản (3.0 - 4.5 tr.đ/ca can thiệp)'),
    ]

    rows = []
    for ma_ct, ten_ct, ma_cs, dvt, huong, stages, can_cu in specs:
        for gd, target, vnd, trieu in stages:
            gd_code = gd.replace('-', '_')
            rows.append({
                'ma_chitieu_kehoach': f"KH_{gd_code}_{ma_ct}",
                'ma_chitieu': ma_ct,
                'ten_chitieu': ten_ct,
                'giai_doan_chinh_sach': gd,
                'ma_chinh_sach': ma_cs,
                'don_vi_tinh': dvt,
                'chi_tieu_muc_tieu': float(target),
                'huong_tot': huong,
                'don_gia_dinh_muc_vnd': int(vnd),
                'don_gia_trieu_vnd': float(trieu),
                'can_cu_phap_ly_dinh_muc': can_cu,
            })

    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(PROCESSED_DIR, 'dim_chitieu_kehoach_ngansach.parquet'), index=False)
    df.to_csv(os.path.join(PROCESSED_DIR, 'dim_chitieu_kehoach_ngansach.csv'), index=False, encoding='utf-8-sig')
    print(f"[DE-SCHEMA] Đã khởi tạo `dim_chitieu_kehoach_ngansach`: {len(df)} dòng định mức kế hoạch & ngân sách")
    return df


class MockSocioeconomicAPIClient:
    """
    Giả lập Client gọi REST API từ Hệ thống Thông tin Dữ liệu vùng DTTS (UBDT & TCTK).
    Đảm bảo:
      - Kỳ `KY_2024`: Bảo toàn 100% số liệu thực tế từ 8 file Excel điều tra 2024.
      - Kỳ `KY_2019` (Baseline trước MTQG 1719) & Kỳ `KY_2026` (Đầu GĐ 2026-2030):
        Sinh chuỗi dữ liệu dọc (Longitudinal Panel Data) có tính nhất quán toán học,
        phản ánh sát thực tế giải ngân đầu tư công và sự phân hóa giữa các huyện/dân tộc.
    """

    def __init__(self, seed: int = 2024):
        self.rng = np.random.default_rng(seed)
        # Phân nhóm tốc độ giảm nghèo và hấp thụ vốn đầu tư công theo địa bàn huyện
        self.fast_improving_districts = {
            'Thành phố Buôn Ma Thuột', 'Thị xã Buôn Hồ', 'Huyện Cư M\'gar',
            'Huyện Krông Pắc', 'Huyện Cư Kuin', 'Huyện Ea Kar'
        }
        self.slow_stubborn_districts = {
            'Huyện Ea Súp', 'Huyện Lắk', 'Huyện M\'Drắk', 'Huyện Krông Bông'
        }

    def _load_2024_base(self, table_name: str) -> pd.DataFrame:
        path = os.path.join(BACKUP_2024_DIR, f"{table_name}.parquet")
        return pd.read_parquet(path).copy()

    def fetch_all_periods(self) -> dict[str, pd.DataFrame]:
        results = {}

        # 1. FACT_HATANG_XA (146 xã x 3 kỳ = 438 dòng)
        df24 = self._load_2024_base('fact_hatang_xa')
        df19 = df24.copy()
        df26 = df24.copy()

        # Kỳ 2019: Trước MTQG 1719 -> Hộ ít hơn ~7%, nghèo cao hơn +7% đến +15%, đường cứng thấp hơn
        hh_factor_19 = self.rng.uniform(0.91, 0.95, size=len(df24))
        df19['tong_ho_dtts'] = np.maximum(1, np.round(df24['tong_ho_dtts'] * hh_factor_19))
        pov_bump_19 = np.where(
            df24['ten_huyen'].isin(self.slow_stubborn_districts),
            self.rng.uniform(8.5, 14.5, size=len(df24)),
            self.rng.uniform(5.5, 10.5, size=len(df24))
        )
        df19['ty_le_ngheo_pct'] = np.round(np.clip(df24['ty_le_ngheo_pct'] + pov_bump_19, 1.5, 99.2), 2)
        df19['so_ho_ngheo'] = np.round(df19['tong_ho_dtts'] * df19['ty_le_ngheo_pct'] / 100.0)
        df19['ty_le_can_ngheo_pct'] = np.round(np.clip(df24['ty_le_can_ngheo_pct'] + self.rng.uniform(2.0, 5.5, size=len(df24)), 1.0, 65.0), 2)
        df19['so_ho_can_ngheo'] = np.round(df19['tong_ho_dtts'] * df19['ty_le_can_ngheo_pct'] / 100.0)
        df19['km_duong_nhua'] = np.round(df24['km_duong_nhua'] * self.rng.uniform(0.78, 0.90, size=len(df24)), 2)
        df19['km_duong_be_tong'] = np.round(df24['km_duong_be_tong'] * self.rng.uniform(0.72, 0.88, size=len(df24)), 2)
        df19['so_thon_co_duong_cung'] = np.maximum(0, np.round(df24['so_thon_co_duong_cung'] * self.rng.uniform(0.75, 0.90, size=len(df24))))
        df19['ty_le_thon_duong_cung_pct'] = np.round(np.where(df19['so_thon'] > 0, df19['so_thon_co_duong_cung'] * 100.0 / df19['so_thon'], 0.0), 2)
        df19['tram_y_te_co_bac_si'] = np.where(self.rng.uniform(0, 1, size=len(df24)) < 0.20, 0, df24['tram_y_te_co_bac_si'])

        # Kỳ 2026 (Đầu GĐ 2026-2030): Phân hóa mạnh giữa huyện giải ngân tốt vs vùng lõi nghèo xa >20km
        hh_factor_26 = self.rng.uniform(1.018, 1.028, size=len(df24))
        df26['tong_ho_dtts'] = np.maximum(1, np.round(df24['tong_ho_dtts'] * hh_factor_26))

        pov_delta_26 = []
        for _, r in df24.iterrows():
            huyen = r['ten_huyen']
            pov24 = float(r['ty_le_ngheo_pct'])
            km = float(r['km_den_trung_tam_huyen'])
            if huyen in self.fast_improving_districts:
                # Bứt phá giảm nghèo mạnh (-3.0 đến -6.2 điểm %)
                delta = -min(pov24 * 0.35, self.rng.uniform(3.0, 6.2))
            elif huyen in self.slow_stubborn_districts:
                if km > 24.0 and pov24 > 35.0:
                    # Bẫy nghèo vùng sâu + Áp chuẩn nghèo đa chiều mới 2026-2030 -> Dậm chân tại chỗ hoặc nhích tăng nhẹ!
                    delta = self.rng.uniform(-0.6, +1.1)
                else:
                    # Giảm rất chậm (-0.8 đến -2.1 điểm %)
                    delta = -min(pov24 * 0.08, self.rng.uniform(0.8, 2.1))
            else:
                # Nhóm huyện trung bình (-2.0 đến -4.2 điểm %)
                delta = -min(pov24 * 0.22, self.rng.uniform(2.0, 4.2))
            pov_delta_26.append(delta)

        df26['ty_le_ngheo_pct'] = np.round(np.clip(df24['ty_le_ngheo_pct'] + np.array(pov_delta_26), 0.2, 97.5), 2)
        df26['so_ho_ngheo'] = np.round(df26['tong_ho_dtts'] * df26['ty_le_ngheo_pct'] / 100.0)
        df26['ty_le_can_ngheo_pct'] = np.round(np.clip(df24['ty_le_can_ngheo_pct'] * self.rng.uniform(0.86, 0.96, size=len(df24)), 0.5, 60.0), 2)
        df26['so_ho_can_ngheo'] = np.round(df26['tong_ho_dtts'] * df26['ty_le_can_ngheo_pct'] / 100.0)
        df26['km_duong_nhua'] = np.round(df24['km_duong_nhua'] * self.rng.uniform(1.03, 1.12, size=len(df24)), 2)
        df26['km_duong_be_tong'] = np.round(df24['km_duong_be_tong'] * self.rng.uniform(1.05, 1.15, size=len(df24)), 2)
        df26['so_thon_co_duong_cung'] = np.minimum(df26['so_thon'], np.round(df24['so_thon_co_duong_cung'] + self.rng.choice([0, 1], size=len(df24), p=[0.4, 0.6])))
        df26['ty_le_thon_duong_cung_pct'] = np.round(np.where(df26['so_thon'] > 0, df26['so_thon_co_duong_cung'] * 100.0 / df26['so_thon'], 0.0), 2)
        df26['tram_y_te_dat_chuan'] = np.minimum(1, df24['tram_y_te_dat_chuan'] + self.rng.choice([0, 1], size=len(df24), p=[0.7, 0.3]))

        results['fact_hatang_xa'] = self._concat_periods(df19, df24, df26)

        # 2. FACT_NHAO_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_nhao_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()

        df19['tong_so_ho_co_nha'] = np.maximum(1, np.round(df24['tong_so_ho_co_nha'] * 0.932))
        df19['nha_thieu_kien_co_don_so'] = np.minimum(
            df19['tong_so_ho_co_nha'],
            np.round(df24['nha_thieu_kien_co_don_so'] * 1.45 + np.where(df24['tong_so_ho_co_nha'] > 500, 12, 0))
        )
        df19['nha_kien_co_ban_kien_co'] = df19['tong_so_ho_co_nha'] - df19['nha_thieu_kien_co_don_so']
        df19['ty_le_nha_tam_don_so_pct'] = np.round(
            np.where(df19['tong_so_ho_co_nha'] > 0, df19['nha_thieu_kien_co_don_so'] * 100.0 / df19['tong_so_ho_co_nha'], 0.0), 2
        )

        # Kỳ 2026: Chiến dịch xóa nhà tạm 2024-2025 giúp giảm ~36.8% số nhà tạm toàn tỉnh;
        # Đặc biệt 4 hộ dân tộc Chơ Ro được xóa 100% nhà tạm (về 0 hộ nhà tạm)!
        df26['tong_so_ho_co_nha'] = np.maximum(1, np.round(df24['tong_so_ho_co_nha'] * 1.022))
        df26['nha_thieu_kien_co_don_so'] = np.where(
            df24['ten_dantoc'] == 'Chơ Ro',
            0,
            np.round(df24['nha_thieu_kien_co_don_so'] * 0.632)
        )
        df26['nha_kien_co_ban_kien_co'] = df26['tong_so_ho_co_nha'] - df26['nha_thieu_kien_co_don_so']
        df26['ty_le_nha_tam_don_so_pct'] = np.round(
            np.where(df26['tong_so_ho_co_nha'] > 0, df26['nha_thieu_kien_co_don_so'] * 100.0 / df26['tong_so_ho_co_nha'], 0.0), 2
        )
        results['fact_nhao_dantoc'] = self._concat_periods(df19, df24, df26)

        # 3. FACT_DANSO_HUYEN_DANTOC (197 dòng x 3 kỳ = 591 dòng)
        df24 = self._load_2024_base('fact_danso_huyen_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()
        df19['so_ho'] = np.maximum(1, np.round(df24['so_ho'] * 0.932)).astype('int64')
        df26['so_ho'] = np.maximum(1, np.round(df24['so_ho'] * 1.022)).astype('int64')
        results['fact_danso_huyen_dantoc'] = self._concat_periods(df19, df24, df26)

        # 4. FACT_NHANKHAU_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_nhankhau_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()
        for col in ['tong_dan_so', 'dan_so_nam', 'dan_so_nu', 'dan_so_0_14', 'dan_so_15_59', 'dan_so_60_plus']:
            df19[col] = np.round(df24[col] * 0.935)
            df26[col] = np.round(df24[col] * 1.021)
        # Già hóa tăng nhẹ năm 2026
        df26['dan_so_60_plus'] = np.round(df24['dan_so_60_plus'] * 1.065)
        df26['tong_dan_so'] = df26['dan_so_nam'] + df26['dan_so_nu']
        results['fact_nhankhau_dantoc'] = self._concat_periods(df19, df24, df26)

        # 5. FACT_GIAODUC_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_giaoduc_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()
        for col in ['biet_chu_tong', 'biet_chu_nam', 'biet_chu_nu', 'biet_chu_thanh_thi', 'biet_chu_nong_thon']:
            df19[col] = np.round(df24[col] * 0.912)
            df26[col] = np.round(df24[col] * 1.038)
        df19['ty_le_nu_biet_chu_pct'] = np.round(np.clip(df24['ty_le_nu_biet_chu_pct'] - 3.8, 0.0, 100.0), 2)
        df19['ty_le_nong_thon_biet_chu_pct'] = np.round(np.clip(df24['ty_le_nong_thon_biet_chu_pct'] - 4.1, 0.0, 100.0), 2)
        # Kỳ 2026: Phụ nữ Chơ Ro được xóa mù chữ từ 0% lên 50.0%!
        df26['ty_le_nu_biet_chu_pct'] = np.where(
            df24['ten_dantoc'] == 'Chơ Ro',
            50.0,
            np.round(np.clip(df24['ty_le_nu_biet_chu_pct'] + 2.4, 0.0, 100.0), 2)
        )
        df26['ty_le_nong_thon_biet_chu_pct'] = np.round(np.clip(df24['ty_le_nong_thon_biet_chu_pct'] + 2.6, 0.0, 100.0), 2)
        results['fact_giaoduc_dantoc'] = self._concat_periods(df19, df24, df26)

        # 6. FACT_LAODONG_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_laodong_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()

        df19['tong_lao_dong_co_viec_lam'] = np.round(df24['tong_lao_dong_co_viec_lam'] * 0.935)
        df19['ty_le_nong_nghiep_pct'] = np.round(np.clip(df24['ty_le_nong_nghiep_pct'] + 3.2, 0.0, 99.5), 2)
        df19['lao_dong_nong_nghiep'] = np.round(df19['tong_lao_dong_co_viec_lam'] * df19['ty_le_nong_nghiep_pct'] / 100.0)
        rem19 = np.maximum(0, df19['tong_lao_dong_co_viec_lam'] - df19['lao_dong_nong_nghiep'])
        df19['lao_dong_cong_nghiep_xaydung'] = np.round(rem19 * 0.42)
        df19['lao_dong_dich_vu'] = rem19 - df19['lao_dong_cong_nghiep_xaydung']
        df19['lao_dong_nam'] = np.round(df24['lao_dong_nam'] * 0.935)
        df19['lao_dong_nu'] = df19['tong_lao_dong_co_viec_lam'] - df19['lao_dong_nam']

        # Kỳ 2026: Chuyển dịch cơ cấu lao động sang Công nghiệp chế biến & Dịch vụ (-3.8 điểm % nông nghiệp)
        df26['tong_lao_dong_co_viec_lam'] = np.round(df24['tong_lao_dong_co_viec_lam'] * 1.025)
        df26['ty_le_nong_nghiep_pct'] = np.round(np.clip(df24['ty_le_nong_nghiep_pct'] - 3.8, 0.0, 96.5), 2)
        df26['lao_dong_nong_nghiep'] = np.round(df26['tong_lao_dong_co_viec_lam'] * df26['ty_le_nong_nghiep_pct'] / 100.0)
        rem26 = np.maximum(0, df26['tong_lao_dong_co_viec_lam'] - df26['lao_dong_nong_nghiep'])
        df26['lao_dong_cong_nghiep_xaydung'] = np.round(rem26 * 0.46)
        df26['lao_dong_dich_vu'] = rem26 - df26['lao_dong_cong_nghiep_xaydung']
        df26['lao_dong_nam'] = np.round(df24['lao_dong_nam'] * 1.025)
        df26['lao_dong_nu'] = df26['tong_lao_dong_co_viec_lam'] - df26['lao_dong_nam']
        results['fact_laodong_dantoc'] = self._concat_periods(df19, df24, df26)

        # 7. FACT_TRINHDO_CMKT_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_trinhdo_cmkt_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()

        df19['tong_lao_dong'] = np.round(df24['tong_lao_dong'] * 0.935)
        df19['ty_le_khong_cmkt_pct'] = np.round(np.clip(df24['ty_le_khong_cmkt_pct'] + 4.5, 0.0, 99.5), 2)
        df19['khong_co_cmkt'] = np.round(df19['tong_lao_dong'] * df19['ty_le_khong_cmkt_pct'] / 100.0)
        trained19 = np.maximum(0, df19['tong_lao_dong'] - df19['khong_co_cmkt'])
        df19['cnkt_khong_bang'] = np.round(trained19 * 0.35)
        df19['so_cap'] = np.round(trained19 * 0.25)
        df19['trung_cap'] = np.round(trained19 * 0.20)
        df19['cao_dang_dai_hoc'] = np.maximum(0, trained19 - df19['cnkt_khong_bang'] - df19['so_cap'] - df19['trung_cap'])

        # Kỳ 2026: Nhờ Dự án 5 MTQG 1719 đào tạo nghề sơ cấp lưu động, tỷ lệ chưa qua đào tạo giảm từ 87.36% xuống ~82.4%
        df26['tong_lao_dong'] = np.round(df24['tong_lao_dong'] * 1.025)
        df26['ty_le_khong_cmkt_pct'] = np.round(np.clip(df24['ty_le_khong_cmkt_pct'] - 4.9, 0.0, 93.5), 2)
        df26['khong_co_cmkt'] = np.round(df26['tong_lao_dong'] * df26['ty_le_khong_cmkt_pct'] / 100.0)
        trained26 = np.maximum(0, df26['tong_lao_dong'] - df26['khong_co_cmkt'])
        df26['cnkt_khong_bang'] = np.round(trained26 * 0.30)
        df26['so_cap'] = np.round(trained26 * 0.32)
        df26['trung_cap'] = np.round(trained26 * 0.18)
        df26['cao_dang_dai_hoc'] = np.maximum(0, trained26 - df26['cnkt_khong_bang'] - df26['so_cap'] - df26['trung_cap'])
        results['fact_trinhdo_cmkt_dantoc'] = self._concat_periods(df19, df24, df26)

        # 8. FACT_DANTOCTHIET_YEU_HUYEN (795 dòng x 3 kỳ = 2,385 dòng)
        df24 = self._load_2024_base('fact_dantocthiet_yeu_huyen')
        df19 = df24.copy()
        df26 = df24.copy()

        df19['ty_le_nuoc_hop_ve_sinh_pct'] = np.round(np.clip(df24['ty_le_nuoc_hop_ve_sinh_pct'] - 8.5, 0.0, 100.0), 2)
        df19['ty_le_ho_xi_hop_ve_sinh_pct'] = np.round(np.clip(df24['ty_le_ho_xi_hop_ve_sinh_pct'] - 11.2, 0.0, 100.0), 2)
        df19['so_ho_co_internet'] = np.round(df24['so_ho_co_internet'] * 0.48)
        df19['so_ho_co_dien_luoi'] = np.round(df24['so_ho_co_dien_luoi'] * 0.91)

        # Kỳ 2026: Nước sạch, Internet, Hố xí tăng, nhưng Krông Bông & Lắk vẫn bị kẹt dưới 20% hố xí HVS
        lat_bump_26 = np.where(
            df24['ten_huyen'].isin(['Huyện Krông Bông', 'Huyện Lắk']),
            5.6,  # Tăng chậm tại vùng trũng vệ sinh
            8.4
        )
        df26['ty_le_nuoc_hop_ve_sinh_pct'] = np.round(np.clip(df24['ty_le_nuoc_hop_ve_sinh_pct'] + 4.2, 0.0, 100.0), 2)
        df26['ty_le_ho_xi_hop_ve_sinh_pct'] = np.round(np.clip(df24['ty_le_ho_xi_hop_ve_sinh_pct'] + lat_bump_26, 0.0, 100.0), 2)
        df26['so_ho_co_internet'] = np.round(df24['so_ho_co_internet'] * 1.18)
        df26['so_ho_co_dien_luoi'] = np.round(df24['so_ho_co_dien_luoi'] * 1.022)
        results['fact_dantocthiet_yeu_huyen'] = self._concat_periods(df19, df24, df26)

        # 9. FACT_DATSANXUAT_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_datsanxuat_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()
        # Quỹ đất bình quân năm 2019 cao hơn nhẹ do chưa tách hộ; năm 2026 các dân tộc <0.5ha được Dự án 1 cấp/hỗ trợ tăng nhẹ
        df19['dien_tich_dat_sx_bq_ha'] = np.round(df24['dien_tich_dat_sx_bq_ha'] * 1.04, 2)
        df19['dien_tich_dat_sx_bq_m2'] = np.round(df19['dien_tich_dat_sx_bq_ha'] * 10000.0)
        df26['dien_tich_dat_sx_bq_ha'] = np.where(
            (df24['dien_tich_dat_sx_bq_ha'] > 0) & (df24['dien_tich_dat_sx_bq_ha'] < 0.50),
            np.round(df24['dien_tich_dat_sx_bq_ha'] + 0.08, 2),
            np.round(df24['dien_tich_dat_sx_bq_ha'] * 0.99, 2)
        )
        df26['dien_tich_dat_sx_bq_m2'] = np.round(df26['dien_tich_dat_sx_bq_ha'] * 10000.0)
        results['fact_datsanxuat_dantoc'] = self._concat_periods(df19, df24, df26)

        # 10. FACT_TINDUNG_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_tindung_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()

        df19['tong_nhu_cau_ho'] = np.round(df24['tong_nhu_cau_ho'] * 0.94)
        df19['so_ho_da_vay_von'] = np.round(df24['so_ho_da_vay_von'] * 0.76)
        df19['so_ho_co_nhu_cau_vay'] = np.maximum(0, df19['tong_nhu_cau_ho'] - df19['so_ho_da_vay_von'])
        df19['ty_le_dap_ung_von_pct'] = np.round(
            np.where(df19['tong_nhu_cau_ho'] > 0, df19['so_ho_da_vay_von'] * 100.0 / df19['tong_nhu_cau_ho'], 0.0), 2
        )
        df19['khoang_trong_tin_dung_pct'] = np.round(
            np.where(df19['tong_nhu_cau_ho'] > 0, df19['so_ho_co_nhu_cau_vay'] * 100.0 / df19['tong_nhu_cau_ho'], 0.0), 2
        )

        # Kỳ 2026: NHCSXH giải ngân gói Nghị định 28 mở rộng -> giảm khoảng trống tín dụng từ 42.87% xuống ~33.2%
        df26['tong_nhu_cau_ho'] = np.round(df24['tong_nhu_cau_ho'] * 1.02)
        df26['so_ho_da_vay_von'] = np.minimum(df26['tong_nhu_cau_ho'], np.round(df24['so_ho_da_vay_von'] * 1.19))
        df26['so_ho_co_nhu_cau_vay'] = np.maximum(0, df26['tong_nhu_cau_ho'] - df26['so_ho_da_vay_von'])
        df26['ty_le_dap_ung_von_pct'] = np.round(
            np.where(df26['tong_nhu_cau_ho'] > 0, df26['so_ho_da_vay_von'] * 100.0 / df26['tong_nhu_cau_ho'], 0.0), 2
        )
        df26['khoang_trong_tin_dung_pct'] = np.round(
            np.where(df26['tong_nhu_cau_ho'] > 0, df26['so_ho_co_nhu_cau_vay'] * 100.0 / df26['tong_nhu_cau_ho'], 0.0), 2
        )
        results['fact_tindung_dantoc'] = self._concat_periods(df19, df24, df26)

        # 11. FACT_MUCSINH_DANTOC (53 dân tộc x 3 kỳ = 159 dòng)
        df24 = self._load_2024_base('fact_mucsinh_dantoc')
        df19 = df24.copy()
        df26 = df24.copy()

        for col in ['sinh_con_thu_3_tro_len', 'sinh_con_thu_3_thanh_thi', 'sinh_con_thu_3_nong_thon']:
            df19[col] = np.round(df24[col] * 1.14)
            df26[col] = np.round(df24[col] * 0.91)
        df19['sinh_tai_nha_co_ba_do'] = np.round(df24['sinh_tai_nha_co_ba_do'] * 1.35)
        df19['sinh_tai_nha_khong_ba_do'] = np.round(df24['sinh_tai_nha_khong_ba_do'] * 1.48)
        df19['sinh_tai_nha_tong'] = df19['sinh_tai_nha_co_ba_do'] + df19['sinh_tai_nha_khong_ba_do']

        df26['sinh_tai_nha_co_ba_do'] = np.round(df24['sinh_tai_nha_co_ba_do'] * 0.68)
        df26['sinh_tai_nha_khong_ba_do'] = np.round(df24['sinh_tai_nha_khong_ba_do'] * 0.55)
        df26['sinh_tai_nha_tong'] = df26['sinh_tai_nha_co_ba_do'] + df26['sinh_tai_nha_khong_ba_do']
        results['fact_mucsinh_dantoc'] = self._concat_periods(df19, df24, df26)

        # 12. FACT_MATUY_HIV_XA (146 xã x 3 kỳ = 438 dòng)
        df24 = self._load_2024_base('fact_matuy_hiv_xa')
        df19 = df24.copy()
        df26 = df24.copy()

        for col in ['nguoi_nghien_ma_tuy_tong', 'nguoi_dtts_nghien_ma_tuy', 'nguoi_nhiem_hiv_tong', 'nguoi_dtts_nhiem_hiv']:
            df19[col] = np.round(df24[col] * 0.85)
            # Kỳ 2026: Điểm nóng Ea H'leo & Krông Năng được kiềm chế giảm ~18% nhờ trạm Methadone
            df26[col] = np.round(df24[col] * 0.82)
        results['fact_matuy_hiv_xa'] = self._concat_periods(df19, df24, df26)

        return results

    @staticmethod
    def _concat_periods(df19: pd.DataFrame, df24: pd.DataFrame, df26: pd.DataFrame) -> pd.DataFrame:
        d1 = df19.copy()
        d2 = df24.copy()
        d3 = df26.copy()
        d1.insert(0, 'ma_ky', 'KY_2019')
        d2.insert(0, 'ma_ky', 'KY_2024')
        d3.insert(0, 'ma_ky', 'KY_2026')
        return pd.concat([d1, d2, d3], ignore_index=True)


def run_de_pipeline():
    print("=" * 80)
    print("🚀 BẮT ĐẦU PIPELINE ĐỒNG BỘ API ĐA KỲ (ROLE DE: KY_2019 -> KY_2024 -> KY_2026)")
    print("=" * 80)

    # 1. Sao lưu bản gốc 2024
    backup_single_period_2024()

    # 2. Tạo 2 bảng Dimension mới (dim_ky_baocao & dim_chitieu_kehoach_ngansach)
    df_ky = build_dim_ky_baocao()
    df_kh = build_dim_chitieu_kehoach_ngansach()

    # Đọc 3 bảng Dimension hiện hữu
    df_diaban = pd.read_csv(
        os.path.join(PROCESSED_DIR, 'dim_diaban_master.csv'), encoding='utf-8-sig'
    )[['ma_xa', 'ten_xa', 'loai_hinh', 'ma_huyen', 'ten_huyen', 'so_thon', 'tinh']]
    df_dantoc = pd.read_csv(
        os.path.join(PROCESSED_DIR, 'dim_dantoc_master.csv'), encoding='utf-8-sig'
    )[['ma_dantoc', 'ten_dantoc', 'ten_goc_bieu_mau', 'nhom_nguon_goc', 'la_dtts_it_nguoi']]
    df_chinhsach = pd.read_parquet(os.path.join(PROCESSED_DIR, 'dim_chinhsach_canthiep.parquet'))

    # 3. Gọi Mock REST API Client kéo dữ liệu 12 bảng Fact cho 3 kỳ
    api_client = MockSocioeconomicAPIClient(seed=2024)
    multi_period_facts = api_client.fetch_all_periods()

    sync_logs = []
    batch_code = f"API_SYNC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    for tbl_name, df_multi in multi_period_facts.items():
        parquet_out = os.path.join(PROCESSED_DIR, f"{tbl_name}.parquet")
        df_multi.to_parquet(parquet_out, index=False)

        # Lưu thêm snapshot JSON cho kỳ mới nhất KY_2026 mô phỏng payload REST API
        df_2026_only = df_multi[df_multi['ma_ky'] == 'KY_2026']
        json_out = os.path.join(API_PAYLOAD_DIR, f"{tbl_name}_KY_2026.json")
        df_2026_only.to_json(json_out, orient='records', force_ascii=False, indent=2)

        for ma_ky, grp in df_multi.groupby('ma_ky'):
            sync_logs.append({
                'batch_code': batch_code,
                'ma_ky': ma_ky,
                'table_name': tbl_name,
                'records_fetched': len(grp),
                'records_loaded': len(grp),
                'api_endpoint': f"https://api.ubdt-tctk.gov.vn/v2/daklak/{ma_ky.lower()}/{tbl_name}",
                'status': 'SUCCESS',
                'synced_at': datetime.now(),
            })

    df_sync_log = pd.DataFrame(sync_logs)
    print(f"[DE-API] Đã kéo thành công 12 bảng Fact x 3 kỳ ({len(df_sync_log)} API batches) và lưu Parquet + JSON Payload!")

    # 4. Thực thi DDL & nạp dữ liệu vào PostgreSQL 18
    print(f"\n[DE-POSTGRES] Đang cập nhật Schema & nạp dữ liệu vào PostgreSQL 18 ({DB_HOST}:{DB_PORT}/{DB_NAME})...")
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    cursor = conn.cursor()

    # Drop các analytical views cũ nếu có trước khi chạy lại DDL
    with open('warehouse/schema/postgres_star_schema.sql', 'r', encoding='utf-8') as f:
        ddl_sql = f.read()
    cursor.execute(ddl_sql)
    conn.commit()
    cursor.close()
    conn.close()

    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    dims_to_load = [
        ('dim_ky_baocao', df_ky),
        ('dim_diaban', df_diaban),
        ('dim_dantoc', df_dantoc),
        ('dim_chinhsach_canthiep', df_chinhsach),
        ('dim_chitieu_kehoach_ngansach', df_kh),
        ('etl_api_sync_log', df_sync_log),
    ]

    with engine.connect() as con:
        for tbl_name, df_dim in dims_to_load:
            df_dim.to_sql(tbl_name, con, schema=SCHEMA_NAME, if_exists='append', index=False)
            cnt = con.execute(text(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.{tbl_name}")).scalar()
            print(f"  -> [DIM/LOG] {tbl_name:<32}: {cnt:>6} dòng")

        for tbl_name, df_fact in multi_period_facts.items():
            df_fact.to_sql(tbl_name, con, schema=SCHEMA_NAME, if_exists='append', index=False)
            cnt = con.execute(text(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.{tbl_name}")).scalar()
            print(f"  -> [FACT]    {tbl_name:<32}: {cnt:>6} dòng (3 kỳ: KY_2019, KY_2024, KY_2026)")

        # Nạp lại View v_chinhsach_lien_ket nếu tồn tại
        if os.path.exists('warehouse/schema/v_chinhsach_lien_ket.sql'):
            with open('warehouse/schema/v_chinhsach_lien_ket.sql', 'r', encoding='utf-8') as vf:
                # Đồng bộ tên cột ma_chinh_sach trong view
                v_sql = vf.read().replace('cs.ma_chinhsach', 'cs.ma_chinh_sach').replace('cs.ten_chinhsach', 'cs.ten_chinh_sach')
                # Dùng các cột thực tế của dim_chinhsach_canthiep
            con.execute(text("""
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
            """))
        con.commit()

    # 5. Đồng bộ sang DuckDB (`warehouse/daklak_socioeconomic.duckdb`)
    print("\n[DE-DUCKDB] Đang đồng bộ toàn bộ Star Schema Đa Kỳ sang DuckDB...")
    con_duck = duckdb.connect('warehouse/daklak_socioeconomic.duckdb')
    for tbl_name, df_dim in dims_to_load:
        con_duck.register('tmp_df', df_dim)
        con_duck.execute(f"CREATE OR REPLACE TABLE {tbl_name} AS SELECT * FROM tmp_df")
    for tbl_name, df_fact in multi_period_facts.items():
        con_duck.register('tmp_df', df_fact)
        con_duck.execute(f"CREATE OR REPLACE TABLE {tbl_name} AS SELECT * FROM tmp_df")
    con_duck.close()
    print("[DE-DUCKDB] Đồng bộ DuckDB hoàn tất 100%!")

    print("\n" + "=" * 80)
    print("✅ HOÀN TẤT BƯỚC 1 (ROLE DE): ĐÃ BƠM DỮ LIỆU 3 KỲ (KY_2019, KY_2024, KY_2026) VÀO POSTGRESQL 18!")
    print("=" * 80)


if __name__ == '__main__':
    run_de_pipeline()
