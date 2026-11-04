"""
Script trích xuất và chuẩn hóa bảng sự kiện cấp xã: Fact_HaTang_Xa
Nguồn: Dak Lak_0. Phiếu xã.xlsx (TH_BIEU0_4, TH_BIEU0_5, TH_BIEU0_7, TH_BIEU0_8, TH_BIEU0_10, TH_BIEU0_12, TH_BIEU0_19)
Đích: data/processed/fact_hatang_xa.parquet (146 xã x Các chỉ số kinh tế - hạ tầng)
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

# 1. Đọc Master Địa Bàn để lấy danh sách chuẩn 146 xã
dim_diaban = pd.read_csv('c:/DA/data/processed/dim_diaban_master.csv')
print(f"Đã nạp Master Địa bàn: {len(dim_diaban)} xã.")

# Tạo dict ánh xạ: (tên_huyện_clean, tên_xã_clean) -> ma_xa
commune_lookup = {}
for _, row in dim_diaban.iterrows():
    h_clean = normalize_vietnamese_text(row['ten_huyen']).lower()
    x_clean = normalize_vietnamese_text(row['ten_xa']).lower()
    commune_lookup[(h_clean, x_clean)] = row['ma_xa']

# Khởi tạo khung dữ liệu 146 xã
fact_dict = {row['ma_xa']: {
    'ma_xa': row['ma_xa'],
    'ten_xa': row['ten_xa'],
    'ma_huyen': row['ma_huyen'],
    'ten_huyen': row['ten_huyen'],
    'so_thon': int(row['so_thon'])
} for _, row in dim_diaban.iterrows()}

wb = openpyxl.load_workbook('c:/DA/data/raw/Dak Lak_0. Phiếu xã.xlsx', data_only=True)

def parse_sheet_by_commune(sheet_name: str, col_idx_map: dict):
    """
    col_idx_map: dict ánh xạ {tên_field: số_thứ_tự_cột_1_based}
    """
    ws = wb[sheet_name]
    current_district = None
    is_daklak = False
    
    for r in range(4, ws.max_row + 1):
        loc = ws.cell(r, 2).value
        if not loc: continue
        loc_str = normalize_vietnamese_text(loc)
        
        if loc_str.upper() == 'ĐẮK LẮK':
            is_daklak = True
            continue
        if not is_daklak: continue
        
        if any(k in loc_str for k in ['Thành phố', 'Thị Xã', 'Huyện', 'Thị xã']):
            current_district = loc_str
        else:
            # Là cấp Xã
            h_clean = normalize_vietnamese_text(current_district).lower() if current_district else ""
            x_clean = loc_str.lower()
            ma_xa = commune_lookup.get((h_clean, x_clean))
            
            if not ma_xa:
                # Thử tìm khớp theo tên xã nếu unique
                matches = [v for k, v in commune_lookup.items() if k[1] == x_clean]
                if len(matches) == 1:
                    ma_xa = matches[0]
                    
            if ma_xa and ma_xa in fact_dict:
                for field_name, c_idx in col_idx_map.items():
                    val = ws.cell(r, c_idx).value
                    fact_dict[ma_xa][field_name] = parse_num_only(val)

# 2. Bóc tách từng biểu mẫu
print("1/6 Đang bóc tách TH_BIEU0_4 (Nghèo)...")
parse_sheet_by_commune('TH_BIEU0_4', {
    'tong_ho_dtts': 3,
    'so_ho_ngheo': 4,
    'ty_le_ngheo_pct': 5
})

print("2/6 Đang bóc tách TH_BIEU0_5 (Cận nghèo)...")
parse_sheet_by_commune('TH_BIEU0_5', {
    'so_ho_can_ngheo': 4,
    'ty_le_can_ngheo_pct': 5
})

print("3/6 Đang bóc tách TH_BIEU0_7 (Giao thông - Khoảng cách đến huyện)...")
parse_sheet_by_commune('TH_BIEU0_7', {
    'km_den_trung_tam_huyen': 3,
    'km_duong_nhua': 4,
    'km_duong_be_tong': 6
})

print("4/6 Đang bóc tách TH_BIEU0_8 (Cứng hóa đường thôn đến xã)...")
parse_sheet_by_commune('TH_BIEU0_8', {
    'so_thon_co_duong_cung': 4,
    'ty_le_thon_duong_cung_pct': 5
})

print("5/6 Đang bóc tách TH_BIEU0_10 (Điện lưới thôn)...")
parse_sheet_by_commune('TH_BIEU0_10', {
    'so_thon_co_dien_luoi': 4
})

print("6/6 Đang bóc tách TH_BIEU0_19 (Trạm y tế & Bác sĩ)...")
parse_sheet_by_commune('TH_BIEU0_19', {
    'co_tram_y_te': 3,
    'tram_y_te_dat_chuan': 4,
    'tram_y_te_co_bac_si': 5
})

# Chuyển đổi sang DataFrame
df_fact = pd.DataFrame(list(fact_dict.values()))

# Điền giá trị mặc định cho ô thiếu
fill_defaults = {
    'tong_ho_dtts': 0, 'so_ho_ngheo': 0, 'ty_le_ngheo_pct': 0.0,
    'so_ho_can_ngheo': 0, 'ty_le_can_ngheo_pct': 0.0,
    'km_den_trung_tam_huyen': 0.0, 'km_duong_nhua': 0.0, 'km_duong_be_tong': 0.0,
    'so_thon_co_duong_cung': 0, 'ty_le_thon_duong_cung_pct': 0.0,
    'so_thon_co_dien_luoi': 0,
    'co_tram_y_te': 0, 'tram_y_te_dat_chuan': 0, 'tram_y_te_co_bac_si': 0
}
df_fact = df_fact.fillna(value=fill_defaults)

# Tính thêm chỉ số phái sinh: Tỷ lệ thôn có điện lưới (%)
df_fact['ty_le_thon_co_dien_pct'] = (df_fact['so_thon_co_dien_luoi'] / df_fact['so_thon'].replace(0, 1) * 100).clip(0, 100).round(2)

# Xuất ra Parquet và CSV
output_parquet = 'c:/DA/data/processed/fact_hatang_xa.parquet'
output_csv = 'c:/DA/data/processed/fact_hatang_xa.csv'

df_fact.to_parquet(output_parquet, index=False)
df_fact.to_csv(output_csv, index=False, encoding='utf-8-sig')

print(f"\n================ THÀNH CÔNG ================")
print(f"Đã xuất: {output_parquet} ({len(df_fact)} dòng, {len(df_fact.columns)} cột)")
print(f"Kiểm tra 0% Missing Key: ma_xa null = {df_fact['ma_xa'].isnull().sum()}")
print(f"Tổng số hộ DTTS toàn bộ 146 xã: {int(df_fact['tong_ho_dtts'].sum()):,} hộ")
print(f"Tổng số hộ nghèo DTTS toàn bộ 146 xã: {int(df_fact['so_ho_ngheo'].sum()):,} hộ")
print(f"Tỷ lệ nghèo bình quân các xã: {df_fact['ty_le_ngheo_pct'].mean():.2f}%")
