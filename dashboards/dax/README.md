# EXPLICIT DAX MEASURES REPOSITORY (PHASE 2: DYNAMIC MULTI-PERIOD & BUDGET ENGINE)

Toàn bộ **92 Explicit DAX Measures** của dự án được quản lý tập trung tại [`daklak_enterprise_measures.dax`](file:///c:/DakLak-2024/dashboards/dax/daklak_enterprise_measures.dax) và đồng bộ trực tiếp sang Semantic Model [`_Measures.tmdl`](file:///c:/DakLak-2024/dashboards/pbix/Dashboard.pbix.SemanticModel/definition/tables/_Measures.tmdl), phân chia thành **10 Display Folders** theo từng nhóm nghiệp vụ:

1. **`00_Time_Intelligence_Context` (8 measures)**:
   - Bộ điều khiển ngữ cảnh chu kỳ điều tra (`[Selected Period Order]`, `[Previous Period Order]`, `[Selected Period Code]`, `[Selected Period Name]`, `[Selected Policy Stage]`, `[Active Period Header Title]`).
   - **Cơ chế Chống Cộng Dồn Sai (Anti-Triple Counting)**: Tự động khóa vào kỳ mới nhất (`is_latest = TRUE` $\rightarrow$ `KY_2026`, `thu_tu_ky = 3`) khi người dùng không chọn Slicer hoặc chọn tất cả các kỳ.
2. **`01_Executive_KPIs` (9 measures)**:
   - Quy mô dân số, tổng số hộ DTTS, hộ nghèo, hộ cận nghèo, tỷ lệ nghèo bình quân cấp xã (đã bọc Context-Aware theo `[Selected Period Order]`).
3. **`02_Demographics_Dependency` (10 measures)**:
   - Cơ cấu giới tính, 3 nhóm tuổi (`0-14`, `15-59`, `60+`), tỷ số phụ thuộc trẻ em, tỷ số phụ thuộc người già và chỉ số già hóa (`[Aging Index %]`).
4. **`03_Education_Human_Capital` (8 measures)**:
   - Dân số biết chữ, tỷ lệ nữ biết chữ, tỷ số giới tính biết chữ (Mẫu hệ vs Phụ hệ), tỷ lệ lao động chưa qua đào tạo CMKT (`[Untrained Labor Rate %]`).
5. **`04_Labor_Economy` (7 measures)**:
   - Lao động có việc làm, cơ cấu 3 khu vực kinh tế (Nông - Lâm - Thủy sản, Công nghiệp - Xây dựng, Thương mại - Dịch vụ) và tỷ trọng đóng góp lao động của người Ê Đê.
6. **`05_Living_Conditions_Sanitation` (8 measures)**:
   - Nhà kiên cố, nhà tạm dột nát, tỷ lệ hố xí hợp vệ sinh (Tiêu chí 17 NTM), nước hợp vệ sinh, kết nối Internet (Đề án 06) và điện lưới quốc gia (hỗ trợ lọc chéo `TREATAS`).
7. **`06_Productive_Assets_Land_Credit` (6 measures)**:
   - Quỹ đất sản xuất nông nghiệp bình quân (`ha/hộ`), cảnh báo thiếu đất `< 0.5 ha/hộ` và khoảng trống tín dụng chính sách NHCSXH (`[Credit Gap Rate %]`).
8. **`07_Social_Vulnerabilities_Healthcare` (6 measures)**:
   - Giám sát điểm nóng người DTTS nghiện ma túy, nhiễm HIV/AIDS, phụ nữ sinh con thứ 3+ và số ca sinh con tại nhà không có cô đỡ thôn bản.
9. **`08_Policy_Intervention_Allocation` (14 measures)**:
   - **Động cơ Dự toán Ngân sách Động (`Dynamic Policy Budgeting Engine`)**: Tự động tra cứu đơn giá định mức (`don_gia_trieu_vnd`) từ bảng `dim_chitieu_kehoach_ngansach` theo từng giai đoạn chính sách (`2016-2020`, `2021-2025`, `2026-2030`) cho 5 chương trình mục tiêu (`[Total Policy Budget Needed (Billion VND)]`).
   - **Công thức `[Dynamic Policy Recommendation Text]`**: Tự động ứng biến theo 4 chế độ (`Toàn tỉnh`, `Huyện`, `Dân tộc`, `Giao thoa Huyện x Dân tộc`) kết hợp báo cáo biến động so với kỳ liền trước (`▲/▼`) và dự toán vốn giải ngân.
10. **`09_Multi_Period_Variance_Targets` (16 measures)**:
    - Bộ thước đo Custom Time Intelligence lùi kỳ tự động (`thu_tu_ky - 1`), tính chênh lệch tuyệt đối/điểm phần trăm (`▲/▼`), đối chiếu chỉ tiêu kế hoạch (`[Stage Target ...]`) và hiển thị chuỗi trạng thái trên KPI Cards.
