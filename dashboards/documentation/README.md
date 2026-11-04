# HƯỚNG DẪN VẬN HÀNH BÁO CÁO POWER BI & TÍCH HỢP ỨNG DỤNG TRA CỨU

## 1. Cấu trúc Tài nguyên Dashboards
* `pbix/Dashboard.pbix`: Tệp báo cáo Power BI Desktop hoàn chỉnh (4 trang, 60 visuals).
* `pbix/Dashboard.Report/`: Mã nguồn PBIR lưu vết phiên bản của toàn bộ các trang và visual.
* `pbix/Dashboard.SemanticModel/`: Định nghĩa mô hình dữ liệu (TMDL).
* `dax/daklak_enterprise_measures.dax`: 100 công thức DAX Explicit tổ chức theo 10 Display Folders.
* `daklak_enterprise_theme.json`: Bảng màu giao diện (Slate Blue & Navy).
* `POWERBI_DASHBOARD_DESIGN_SPEC.md`: Bản đặc tả chi tiết bố cục, visual hierarchy và hệ tọa độ của 4 trang.

## 2. Hướng dẫn Tạo Nút Bấm Tích Hợp Ứng Dụng Tra Cứu KTXH
Trên giao diện Power BI Desktop:
1. Chọn Ribbon **Insert** $\rightarrow$ **Buttons** $\rightarrow$ **Blank**.
2. Đặt nút tại góc trên bên phải thanh Header (kế bên Slicer Chu kỳ báo cáo).
3. Tại ngăn **Format Button**:
   * **Text**: `Tra Cứu Số Liệu KTXH` (Font: *Segoe UI Semibold*, cỡ 10 pt, màu trắng `#FFFFFF`).
   * **Fill**: Bật màu nền Xanh Navy (`#1E3A8A`) hoặc Teal (`#0D9488`), bo góc 4–6 px.
   * **Action**:
     * Bật `Action` sang **On**.
     * **Type**: `Web URL`.
     * **Web URL**: `https://dtts-daklak.com`.
     * **Tooltip**: `Mở Bàn Phân Tích & Tra Cứu Số Liệu KTXH`.
4. Copy nút này sang thanh Header của cả 4 trang để liên kết nhanh sang ứng dụng web.
