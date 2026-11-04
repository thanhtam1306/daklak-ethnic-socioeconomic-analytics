# WAREHOUSE & DATA MODELING SCHEMA
Thư mục này chứa các tệp định nghĩa kiến trúc **Kimball Star Schema**:

1. `01_create_dimensions.sql`: DDL tạo các bảng chiều `dim_diaban`, `dim_dantoc`, `dim_chitieu`.
2. `02_create_facts.sql`: DDL tạo các bảng sự kiện `fact_nhankhau_dantoc`, `fact_dieukien_sinhhoat`, `fact_hatang_khao_sat_xa`.
3. `erd_diagram.md`: Sơ đồ quan hệ thực thể quan hệ (ERD) và từ điển dữ liệu (Data Dictionary).
