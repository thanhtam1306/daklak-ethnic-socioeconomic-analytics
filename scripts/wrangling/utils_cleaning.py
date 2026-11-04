"""
Module tiện ích dùng chung cho Data Wrangling dữ liệu khảo sát 53 DTTS Đắk Lắk 2024.
Dự án: daklak-ethnic-socioeconomic-analytics (Thực hành Data Analyst)
"""

import re
import unicodedata
import sys
import pandas as pd
from typing import Tuple, Optional, Any

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def normalize_vietnamese_text(text: Any) -> str:
    """
    Chuẩn hóa chuỗi tiếng Việt: loại bỏ khoảng trắng thừa, chuẩn hóa Unicode NFC dựng sẵn.
    """
    if text is None:
        return ""
    s = str(text).strip()
    s = unicodedata.normalize('NFC', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def clean_numeric_value(val: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Bóc tách giá trị số và cờ cảnh báo mẫu từ các cell thống kê phức tạp.
    
    Quy tắc nghiệp vụ:
    - Ký tự '-' hoặc '0' -> (0.0, None)
    - Ký tự '...' hoặc rỗng/None -> (None, 'MISSING')
    - Chứa '*' (25 <= mẫu <= 49) -> (float_val, 'CAUTION_25_49')
    - Chứa '**' (mẫu < 25) -> (float_val, 'UNRELIABLE_UNDER_25')
    - Số thông thường -> (float_val, None)
    
    Ví dụ:
        clean_numeric_value('15 (**)') -> (15.0, 'UNRELIABLE_UNDER_25')
        clean_numeric_value('39 (*)')  -> (39.0, 'CAUTION_25_49')
        clean_numeric_value('-')        -> (0.0, None)
        clean_numeric_value('24.62')    -> (24.62, None)
    """
    if val is None:
        return None, None
        
    s = normalize_vietnamese_text(val)
    if not s or s == '...':
        return None, 'MISSING'
    if s == '-':
        return 0.0, None
        
    flag = None
    if '**' in s:
        flag = 'UNRELIABLE_UNDER_25'
    elif '*' in s:
        flag = 'CAUTION_25_49'
        
    # Loại bỏ dấu ngoặc đơn và dấu sao
    clean_str = re.sub(r'[\*\(\)]', '', s).strip()
    # Nếu là chuỗi số có dấu phẩy thập phân hoặc khoảng cách ngàn
    clean_str = clean_str.replace(',', '.')
    
    try:
        num = float(clean_str)
        return num, flag
    except ValueError:
        return None, 'PARSE_ERROR'

def parse_num_only(val: Any, default: float = 0.0) -> float:
    """
    Hàm tiện ích nhanh chỉ lấy giá trị số thực float.
    """
    num, _ = clean_numeric_value(val)
    return num if num is not None else default

def match_commune_code(commune_name: str, master_diaban_df: pd.DataFrame) -> Optional[str]:
    """
    Khớp tên xã vào mã ma_xa chuẩn hóa trong dim_diaban_master.
    """
    clean_input = normalize_vietnamese_text(commune_name).lower()
    
    # 1. Khớp chính xác
    for _, row in master_diaban_df.iterrows():
        master_clean = normalize_vietnamese_text(row['ten_xa']).lower()
        if clean_input == master_clean:
            return row['ma_xa']
            
    # 2. Khớp bỏ tiền tố (Xã, Phường, Thị trấn)
    clean_input_core = re.sub(r'^(xã|phường|thị trấn)\s+', '', clean_input).strip()
    for _, row in master_diaban_df.iterrows():
        master_clean = normalize_vietnamese_text(row['ten_xa']).lower()
        master_clean_core = re.sub(r'^(xã|phường|thị trấn)\s+', '', master_clean).strip()
        if clean_input_core == master_clean_core:
            return row['ma_xa']
            
    return None

if __name__ == '__main__':
    # Unit tests kiểm tra tính chính xác của module
    test_cases = [
        ('15 (**)', (15.0, 'UNRELIABLE_UNDER_25')),
        ('39 (*)', (39.0, 'CAUTION_25_49')),
        ('-', (0.0, None)),
        ('...', (None, 'MISSING')),
        (' 160363 ', (160363.0, None)),
        ('24.6249', (24.6249, None)),
        (None, (None, None))
    ]
    print("--- KIỂM TRA ĐƠN VỊ (UNIT TESTS) CHO UTILS_CLEANING ---")
    all_passed = True
    for inp, expected in test_cases:
        res = clean_numeric_value(inp)
        status = "PASSED" if res == expected else "FAILED"
        if status == "FAILED": all_passed = False
        print(f"Input: {str(inp):<12} -> Output: {str(res):<35} | {status}")
    print(f"\nKết quả: {'100% KIỂM TRA ĐẠT TIÊU CHUẨN' if all_passed else 'CÓ LỖI'}")
