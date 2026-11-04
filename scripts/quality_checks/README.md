# DATA QUALITY & INTEGRITY CHECKS
Thư mục chứa các kịch bản kiểm tra chất lượng dữ liệu theo tiêu chuẩn `data-quality-governance.md`:

1. `check_hierarchy_reconciliation.py`: Đối soát logic tổng huyện = tổng các xã trực thuộc (chênh lệch tuyệt đối = 0).
2. `check_value_boundaries.py`: Kiểm định miền giá trị hợp lệ (các tỷ lệ % phải thuộc đoạn [0, 100], số lượng người >= 0).
3. `check_surrogate_keys.py`: Đảm bảo tính toàn vẹn tham chiếu (Referential Integrity) giữa Fact và Dimension.
