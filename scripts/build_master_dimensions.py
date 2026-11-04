import sys, openpyxl, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

# 1. Trích xuất Dim Địa Bàn (15 Huyện, 146 Xã)
wb0 = openpyxl.load_workbook('c:/DA/data/raw/Dak Lak_0. Phiếu xã.xlsx', data_only=True)
ws0 = wb0['TH_BIEU0_1']

diaban_records = []
current_district = None
dist_code_map = {}
dist_idx = 0
is_daklak = False
commune_idx = 0

for r in range(4, ws0.max_row+1):
    loc = ws0.cell(r, 2).value
    so_thon = ws0.cell(r, 4).value
    if not loc: continue
    loc_str = str(loc).strip()
    
    if loc_str.upper() == 'ĐẮK LẮK':
        is_daklak = True
        continue
    if not is_daklak: continue
    
    if any(k in loc_str for k in ['Thành phố', 'Thị Xã', 'Huyện', 'Thị xã']):
        current_district = loc_str
        dist_idx += 1
        dist_code = f"DL_DIST_{dist_idx:02d}"
        dist_code_map[current_district] = dist_code
    else:
        commune_idx += 1
        commune_code = f"DL_COMM_{commune_idx:03d}"
        try:
            thon_cnt = int(float(str(so_thon))) if so_thon is not None else 0
        except:
            thon_cnt = 0
            
        # Phân loại hình thái hành chính
        loai_hinh = 'Xã'
        if 'Phường' in loc_str: loai_hinh = 'Phường'
        elif 'Thị trấn' in loc_str: loai_hinh = 'Thị trấn'
        
        diaban_records.append({
            'ma_xa': commune_code,
            'ten_xa': loc_str,
            'loai_hinh': loai_hinh,
            'ma_huyen': dist_code_map[current_district],
            'ten_huyen': current_district,
            'so_thon': thon_cnt,
            'tinh': 'Đắk Lắk'
        })

df_diaban = pd.DataFrame(diaban_records)
df_diaban.to_csv('c:/DA/data/processed/dim_diaban_master.csv', index=False, encoding='utf-8-sig')
print(f"-> Đã xuất c:/DA/data/processed/dim_diaban_master.csv ({len(df_diaban)} xã, {df_diaban['ten_huyen'].nunique()} huyện).")

# 2. Trích xuất Dim Dân Tộc (53 DTTS với phân loại bản địa Tây Nguyên / Di cư phía Bắc / Khác)
wb1 = openpyxl.load_workbook('c:/DA/data/raw/Dak Lak_1. Dân số.xlsx', read_only=True)
ws1 = wb1['TH_BIEU1_2']

ethnic_raw = [ws1.cell(3, c).value.strip() for c in range(4, ws1.max_column+1) if ws1.cell(3, c).value]

# Nhóm bản địa Tây Nguyên (ngữ hệ Nam Đảo & Nam Á - Môn-Khmer)
tay_nguyen_native = ['Ê đê', 'Gia Rai', 'Mnông', 'Ba Na', 'Xơ Đăng', 'Cơ Ho', 'Gié Triêng', 'Mạ', 'Chu Ru', 'Brâu', 'Rơ Măm']
# Nhóm di cư từ miền núi phía Bắc (Tày-Thái, H'Mông-Dao, Việt-Mường, Tạng-Miến)
northern_migrant = ['Tày', 'Nùng', 'Thái', 'Mường', 'Mông', 'Dao', 'Sán Chay', 'Giáy', 'Khơ mú', 'Sán Dìu', 'Thổ', 'Lào', 'La Chí', 'La Ha', 'Cơ Lao', 'Pà Thẻn', 'Bố Y', 'Phù Lá', 'Hà Nhì', 'La Hủ', 'Lự', 'Lô Lô', 'Cống', 'Si La', 'Pu Péo']

dantoc_records = []
for idx, name in enumerate(ethnic_raw, 1):
    clean_name = name.replace('(1)', '').strip()
    
    if clean_name in tay_nguyen_native:
        nhom_nguon_goc = 'Bản địa Tây Nguyên'
    elif clean_name in northern_migrant:
        nhom_nguon_goc = 'Di cư miền núi phía Bắc'
    elif clean_name in ['Hoa', 'Khmer', 'Chăm']:
        nhom_nguon_goc = 'Nam Bộ & Duyên hải'
    else:
        nhom_nguon_goc = 'Khác'
        
    dantoc_records.append({
        'ma_dantoc': f"DT_{idx:02d}",
        'ten_dantoc': clean_name,
        'ten_goc_bieu_mau': name,
        'nhom_nguon_goc': nhom_nguon_goc,
        'la_dtts_it_nguoi': 1 if '(1)' in name else 0
    })

df_dantoc = pd.DataFrame(dantoc_records)
df_dantoc.to_csv('c:/DA/data/processed/dim_dantoc_master.csv', index=False, encoding='utf-8-sig')
print(f"-> Đã xuất c:/DA/data/processed/dim_dantoc_master.csv ({len(df_dantoc)} dân tộc).")
print("\nPhân bổ nguồn gốc 53 Dân tộc thiểu số:")
print(df_dantoc['nhom_nguon_goc'].value_counts())
