import sys, openpyxl, json
sys.stdout.reconfigure(encoding='utf-8')

files = [
    ('Dak Lak_0. Phiếu xã.xlsx', 'Phân hệ 0: Phiếu Xã (Hạ tầng 146 xã)'),
    ('Dak Lak_1. Dân số.xlsx', 'Phân hệ 1: Dân số (Nhân khẩu & Quy mô hộ)'),
    ('Dak Lak_2. Giáo dục.xlsx', 'Phân hệ 2: Giáo dục (Học vấn & Ngôn ngữ)'),
    ('Dak Lak_3. Mức sinh.xlsx', 'Phân hệ 3: Mức sinh (Y tế sinh sản)'),
    ('Dak Lak_4. Lao động.xlsx', 'Phân hệ 4: Lao động (Việc làm & Ngành nghề)'),
    ('Dak Lak_5. Nhà ở.xlsx', 'Phân hệ 5: Nhà ở (Chất lượng an cư)'),
    ('Dak Lak_6. Điều kiện sinh hoạt.xlsx', 'Phân hệ 6: Điều kiện sinh hoạt (Nước sạch, Vệ sinh, Đời sống)')
]

data_catalog = []

for fname, desc in files:
    path = f'c:/DA/data/raw/{fname}'
    wb = openpyxl.load_workbook(path, read_only=True)
    file_info = {
        'file_name': fname,
        'description': desc,
        'total_sheets': len(wb.sheetnames),
        'sheets': []
    }
    
    for idx, sname in enumerate(wb.sheetnames, 1):
        ws = wb[sname]
        
        # Extract title from first 4 rows
        title = None
        unit = None
        for r in range(1, 5):
            for c in range(1, 6):
                val = ws.cell(r, c).value
                if val:
                    val_str = str(val).strip()
                    if 'Đơn vị' in val_str or 'Đơn vị tính' in val_str:
                        unit = val_str
                    elif any(k in val_str.upper() for k in ['BIỂU', 'DANH SÁCH', 'TỔNG SỐ', 'TỶ LỆ', 'SỐ LƯỢNG', 'DIỆN TÍCH', 'CƠ CẤU']) and not title:
                        title = val_str.replace('\n', ' ')
        
        # Sample header row
        header_sample = []
        for c in range(1, min(12, ws.max_column+1)):
            v = ws.cell(3, c).value or ws.cell(4, c).value
            if v:
                header_sample.append(str(v).replace('\n', ' ').strip())
                
        file_info['sheets'].append({
            'sheet_index': idx,
            'sheet_name': sname,
            'max_row': ws.max_row,
            'max_column': ws.max_column,
            'unit': unit if unit else 'N/A',
            'title': title if title else 'N/A',
            'columns_sample': header_sample[:8]
        })
        
    data_catalog.append(file_info)

with open('c:/DA/data/data_catalog_full.json', 'w', encoding='utf-8') as f:
    json.dump(data_catalog, f, ensure_ascii=False, indent=2)

print("Exported full catalog to c:/DA/data/data_catalog_full.json successfully!")
