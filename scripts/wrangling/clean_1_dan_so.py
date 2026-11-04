"""
Script trích xuất và unpivot bảng sự kiện nhân khẩu: Fact_DanSo_Huyen_DanToc
Nguồn: Dak Lak_1. Dân số.xlsx (TH_BIEU1_2: Số hộ, TH_BIEU1_7: Số nhân khẩu & giới tính)
Đích: data/processed/fact_danso_huyen_dantoc.parquet (Tidy Data dọc: ma_huyen x ma_dantoc x metrics)
"""

import sys
import openpyxl
import pandas as pd
from utils_cleaning import normalize_vietnamese_text, parse_num_only

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 1. Đọc Master Dimensions
dim_diaban = pd.read_csv('c:/DA/data/processed/dim_diaban_master.csv')
dim_dantoc = pd.read_csv('c:/DA/data/processed/dim_dantoc_master.csv')

# Unique 15 huyện
districts_unique = dim_diaban[['ma_huyen', 'ten_huyen']].drop_duplicates().reset_index(drop=True)
district_map = {normalize_vietnamese_text(row['ten_huyen']).lower(): row['ma_huyen'] for _, row in districts_unique.iterrows()}

# Ethnic map: ten_goc_bieu_mau (clean) -> ma_dantoc
ethnic_map = {normalize_vietnamese_text(row['ten_goc_bieu_mau']).lower(): row['ma_dantoc'] for _, row in dim_dantoc.iterrows()}

wb = openpyxl.load_workbook('c:/DA/data/raw/Dak Lak_1. Dân số.xlsx', data_only=True)

# 2. Xử lý TH_BIEU1_2 (Số hộ theo Huyện x Dân tộc)
ws_ho = wb['TH_BIEU1_2']

# Lấy danh sách tên dân tộc trên Row 3
ethnic_cols_ho = {}
for c in range(4, ws_ho.max_column + 1):
    val = ws_ho.cell(3, c).value
    if val:
        c_name = normalize_vietnamese_text(val).lower()
        if c_name in ethnic_map:
            ethnic_cols_ho[c] = ethnic_map[c_name]

print(f"Số cột dân tộc nhận diện được trong TH_BIEU1_2: {len(ethnic_cols_ho)}")

records_ho = []
current_district = None
is_daklak = False

for r in range(4, ws_ho.max_row + 1):
    loc = ws_ho.cell(r, 2).value
    if not loc: continue
    loc_clean = normalize_vietnamese_text(loc).lower()
    
    if loc_clean == 'đắk lắk':
        is_daklak = True
        continue
    if not is_daklak: continue
    
    ma_huyen = district_map.get(loc_clean)
    if not ma_huyen:
        # Match bỏ tiền tố
        for h_name, h_code in district_map.items():
            if h_name in loc_clean or loc_clean in h_name:
                ma_huyen = h_code
                break
                
    if ma_huyen:
        for col_idx, ma_dantoc in ethnic_cols_ho.items():
            so_ho = parse_num_only(ws_ho.cell(r, col_idx).value)
            if so_ho > 0:
                records_ho.append({
                    'ma_huyen': ma_huyen,
                    'ma_dantoc': ma_dantoc,
                    'so_ho': int(so_ho)
                })

df_ho = pd.DataFrame(records_ho)
print(f"Đã trích xuất {len(df_ho)} dòng dữ liệu số hộ (các cặp Huyện x Dân tộc có phát sinh số liệu).")
print(f"Tổng số hộ DTTS đối soát: {df_ho['so_ho'].sum():,} hộ (Kỳ vọng: ~160,363 hộ).")

# 3. Xử lý TH_BIEU1_7 (Nhân khẩu & Nam/Nữ theo Huyện x Dân tộc)
ws_nk = wb['TH_BIEU1_7']
# Cấu trúc TH_BIEU1_7 tương tự nhưng mỗi dân tộc có thể gồm 3 cột: Tổng số, Nam, Nữ
# Kiểm tra headers của TH_BIEU1_7
print("\nĐang kiểm tra cấu trúc TH_BIEU1_7...")
r3_vals = [ws_nk.cell(3, c).value for c in range(1, 15)]
r4_vals = [ws_nk.cell(4, c).value for c in range(1, 15)]
print("Row 3:", r3_vals[:6])
print("Row 4:", r4_vals[:6])

# Kết hợp dữ liệu và xuất
output_parquet = 'c:/DA/data/processed/fact_danso_huyen_dantoc.parquet'
output_csv = 'c:/DA/data/processed/fact_danso_huyen_dantoc.csv'

# Merge thông tin tên để kiểm tra
df_ho = df_ho.merge(districts_unique, on='ma_huyen', how='left')
df_ho = df_ho.merge(dim_dantoc[['ma_dantoc', 'ten_dantoc', 'nhom_nguon_goc']], on='ma_dantoc', how='left')

df_ho.to_parquet(output_parquet, index=False)
df_ho.to_csv(output_csv, index=False, encoding='utf-8-sig')

print(f"\n================ THÀNH CÔNG ================")
print(f"Đã xuất: {output_parquet} ({len(df_ho)} dòng, {len(df_ho.columns)} cột)")
