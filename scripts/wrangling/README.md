# DATA WRANGLING & CLEANING SCRIPTS
Thư mục chứa các module Python bóc tách và chuẩn hóa 8 tệp biểu mẫu thống kê Excel thành bảng phẳng Tidy Data:

- `clean_phieu_xa.py`: Bóc tách 23 biểu mẫu hạ tầng, điện, đường, trạm y tế, trường học từ `Dak Lak_0. Phiếu xã.xlsx`.
- `clean_dan_so.py`: Bóc tách 17 biểu mẫu dân số, độ tuổi, giới tính, dân tộc từ `Dak Lak_1. Dân số.xlsx`.
- `clean_giao_duc.py`: Bóc tách 5 biểu mẫu tỷ lệ đi học, trình độ học vấn từ `Dak Lak_2. Giáo dục.xlsx`.
- `clean_muc_sinh.py`: Bóc tách 7 biểu mẫu tỷ suất sinh, phụ nữ trong độ tuổi sinh đẻ từ `Dak Lak_3. Mức sinh.xlsx`.
- `clean_lao_dong.py`: Bóc tách 7 biểu mẫu việc làm, thất nghiệp, ngành nghề từ `Dak Lak_4. Lao động.xlsx`.
- `clean_nha_o.py`: Bóc tách 8 biểu mẫu phân loại chất lượng nhà ở từ `Dak Lak_5. Nhà ở.xlsx`.
- `clean_sinh_hoat.py`: Bóc tách 24 biểu mẫu điều kiện sinh hoạt (nước, vệ sinh, internet) từ `Dak Lak_6. Điều kiện sinh hoạt.xlsx`.
- `clean_dimensions.py`: Bóc tách danh mục địa bàn và danh mục dân tộc từ `Phụ lục.xls`.
- `utils.py`: Hàm tiện ích dùng chung (xử lý merged cells, forward fill hierarchy, chuẩn hóa tên cột).
