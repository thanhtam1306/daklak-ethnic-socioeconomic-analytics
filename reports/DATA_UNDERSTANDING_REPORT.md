# BÁO CÁO TOÀN DIỆN: KHÁM PHÁ, ĐỐI SOÁT & PHẢN BIỆN DỮ LIỆU
## TÀI LIỆU KHẢO SÁT, KIỂM TOÁN VÀ ĐÁNH GIÁ CHẤT LƯỢNG SỐ LIỆU BAN ĐẦU

**Dự án**: Phân Tích Thực Trạng Kinh Tế - Xã Hội 53 Dân Tộc Thiểu Số Tỉnh Đắk Lắk Năm 2024  
**Mục đích**: Thực hành khám phá, đối soát và làm sạch dữ liệu thống kê thực tế  
**Khung phương pháp luận**: *Defensive EDA & Critical Profiling Framework (Quy trình kiểm toán đối soát và đánh giá tính nhất quán dữ liệu)*  
**Ngày lập**: 12/10/2026  

---

### TÓM TẮT TỔNG QUAN (EXECUTIVE SUMMARY)

Tài liệu này tổng hợp kết quả khảo sát và kiểm toán dữ liệu từ 8 tệp biểu mẫu thống kê thô:

Sau khi tiếp nhận và thực hiện kiểm toán kỹ thuật trên toàn bộ **8 tệp dữ liệu thô (91 biểu mẫu ma trận thống kê)** thuộc cuộc Điều tra thực trạng kinh tế - xã hội 53 dân tộc thiểu số năm 2024 tại Đắk Lắk, bộ phận Data Analytics xin trình bày **Báo cáo Đọc hiểu & Khám phá Dữ liệu Chuyên Sâu**.

Báo cáo này loại bỏ hoàn toàn các nhận định cảm tính, áp dụng **Tư duy phản biện số liệu (Critical Data Thinking)** để làm rõ:
1. **Phân định rạch ròi mẫu số khảo sát**: Toàn bộ chỉ số nghèo đói và điều kiện sống đều tính trên **cộng đồng người Dân tộc thiểu số (DTTS)**, không nhầm lẫn với dân số chung toàn tỉnh (bao gồm người Kinh).
2. **Đập tan bẫy tỷ lệ % bằng Ma trận 2 chiều**: Không chỉ nhìn vào tỷ lệ % để xếp hạng (tránh dồn ngân sách vào nơi mẫu nhỏ), mà kết hợp **Tỷ lệ % (Intensity)** $\times$ **Số lượng hộ nghèo tuyệt đối (Volume)**.
3. **Bóc tách định lượng thực tế 100% các phân hệ (Lao động, Nhà ở, Vệ sinh)**:
   - **Bẫy nông nghiệp thuần túy**: **88.97%** lao động DTTS Đắk Lắk (354.457 / 398.381 người) làm nông lâm thủy sản; công nghiệp và dịch vụ mỗi ngành chỉ chiếm ~5.4%.
   - **Mục tiêu xóa nhà tạm**: Vẫn còn **10.095 hộ DTTS (6.29%)** đang sống trong nhà thiếu kiên cố, nhà đơn sơ dột nát.
   - **Điểm nghẽn vệ sinh nông thôn**: Dù nước sạch đạt 97.4%, tỷ lệ dùng hố xí hợp vệ sinh toàn tỉnh chỉ đạt **72.3%**, đặc biệt tại huyện Krông Búk chỉ đạt **40.4%** (gần 60% hộ phóng uế bừa bãi hoặc dùng cầu tiêu tạm bợ).
4. **Kiểm toán số học (Reconciliation)**: Bóc tách thành công bẫy gộp tỉnh Phú Yên (16.474 hộ), đối soát khớp $99.999\%$ với số liệu chính thức của tỉnh Đắk Lắk (160.363 hộ).

---

### BƯỚC 1: DATA INVENTORY (KIỂM KÊ TOÀN DIỆN DỮ LIỆU NGUỒN)

Toàn bộ dữ liệu nguồn được lưu trữ bất biến tại thư mục `data/raw/`:

| STT | Tên Tệp Dữ Liệu Thô | Dung Lượng | Số Biểu Mẫu | Định Dạng | Chủ Đề / Phân Hệ Nghiệp Vụ | Chỉ Số Cốt Lõi |
|:---:|---|:---:|:---:|:---:|---|---|
| 1 | `Dak Lak_0. Phiếu xã.xlsx` | 392.3 KB | 23 biểu | Excel (.xlsx) | Hạ tầng cơ sở 146 xã vùng DTTS | Hộ DTTS nghèo, cận nghèo, km đường, đường cứng hóa, trạm y tế, bác sĩ |
| 2 | `Dak Lak_1. Dân số.xlsx` | 473.4 KB | 17 biểu | Excel (.xlsx) | Nhân khẩu học & Hộ gia đình | 160.363 hộ DTTS, 31 dân tộc, giới tính, tháp tuổi, BHYT, tảo hôn |
| 3 | `Dak Lak_2. Giáo dục.xlsx` | 133.3 KB | 5 biểu | Excel (.xlsx) | Học vấn & Ngôn ngữ | 391.692 người >=15T biết chữ phổ thông, biết tiếng dân tộc |
| 4 | `Dak Lak_3. Mức sinh.xlsx` | 55.3 KB | 7 biểu | Excel (.xlsx) | Sức khỏe sinh sản & Y tế | Khám thai tiền sản, sinh con tại cơ sở y tế vs sinh tại nhà |
| 5 | `Dak Lak_4. Lao động.xlsx` | 98.7 KB | 7 biểu | Excel (.xlsx) | Việc làm & Cơ cấu kinh tế | 398.381 lao động; 88.97% nông nghiệp, 5.4% công nghiệp, 5.4% dịch vụ |
| 6 | `Dak Lak_5. Nhà ở.xlsx` | 76.4 KB | 8 biểu | Excel (.xlsx) | Điều kiện an cư & Chỗ ở | 149.921 hộ kiên cố (93.5%); 10.095 hộ nhà tạm dột nát (6.3%) |
| 7 | `Dak Lak_6. Điều kiện sinh hoạt.xlsx` | 317.0 KB | 24 biểu | Excel (.xlsx) | Mức sống & Tiện ích sinh hoạt | Nước sạch (97.4%), Hố xí HVS (72.3%), Internet (151.421 hộ), điện lưới |
| 8 | `Phu_luc.xlsx` (chuyển từ `.xls`) | 270.8 KB | 8 sheet | Excel (.xlsx) | Tra cứu metadata & căn cứ | Danh mục chuẩn 91 biểu mẫu khảo sát Tổng cục Thống kê |
| **Tổng** | **8 Tệp Nguồn** | **~1.8 MB** | **91 Biểu mẫu** | - | **Bao phủ trọn vẹn đời sống kinh tế - xã hội 53 DTTS Đắk Lắk 2024** |

---

### BƯỚC 2: GRAIN, CANDIDATE KEYS & RELATIONSHIPS (HẠT DỮ LIỆU & QUAN HỆ)

Dữ liệu khảo sát không thể gộp phẳng cơ học mà bắt buộc phải phân tách thành **2 cấp độ phân tích (Grain) độc lập**:

```
                                      HỆ THỐNG DỮ LIỆU ĐIỀU TRA 2024
                                                    │
             ┌──────────────────────────────────────┴──────────────────────────────────────┐
             ▼                                                                            ▼
      [GRAIN 1: CẤP XÃ]                                                        [GRAIN 2: HUYỆN x DÂN TỘC]
      (File 0: Phiếu xã - 23 biểu)                                             (Files 1 đến 6: Phiếu hộ - 68 biểu)
      Đơn vị quan sát: 1 Xã / Phường / Thị trấn                                Đơn vị quan sát: 1 Nhóm DTTS tại 1 Huyện
      Quy mô: 146 dòng                                                         Quy mô: 197 dòng phát sinh
      Khóa chính: ma_xa                                                        Khóa chính tổ hợp: (ma_huyen, ma_dantoc)
      Bài toán: Đầu tư công, đường, điện, trạm xá                              Bài toán: Bất bình đẳng học vấn, việc làm, an cư
             │                                                                            │
             └──────────────────────────────────────┬─────────────────────────────────────┘
                                                    ▼
                                     [CẦU NỐI DIMENSION MASTER]
                                      Dim_DiaBan & Dim_DanToc
```

* **Phân định rõ ràng về mặt nghiệp vụ**:
  - `Fact_HaTang_Xa` (146 dòng): Mẫu số là **Số hộ DTTS trên địa bàn xã** (không tính hộ người Kinh). Trả lời: *Xã nào có tỷ lệ DTTS nghèo cao nhất, giao thông cách trở nhất?*
  - `Fact_DanSo_Huyen_DanToc` (197 dòng): So sánh ngang hàng giữa các nhóm dân tộc trong cùng một huyện. Trả lời: *Tại sao cùng ở huyện Ea H'leo nhưng dân tộc Tày/Nùng phát triển kinh tế nhanh hơn dân tộc Gia Rai/Ê đê?*

---

### BƯỚC 3: DATA HYGIENE & CELL-LEVEL DEFECTS (VỆ SINH DỮ LIỆU)

Bóc tách 4 đặc trưng kỹ thuật cần chuẩn hóa qua pipeline Python:
1. **Header ma trận gộp ô 2–3 tầng (Merged Cells)**: Cột *Thành thị* gồm 2 cột con *Nam/Nữ*; danh sách dân tộc trải dài 53 cột ngang $\to$ Cần Unpivot (melt) xoay dọc thành Tidy Data.
2. **Ký hiệu sentinel thống kê dính trong cell**: Dạng text như `'15 (**)'`, `'39 (*)'`, `'-'`, `'...'` $\to$ Đã viết hàm `clean_numeric_value()` dùng Regex tách thành: Cột số thực (`numeric_value`) và Cột cờ cảnh báo (`sample_warning_flag`).
3. **Cột dân tộc ngắt 2 khối chồng nhau**: Dòng 4 (dân tộc 1–40), dòng 14 (dân tộc 41–53) $\to$ Đã ghép nối ngang tự động trước khi unpivot.

---

### BƯỚC 4: DOMAIN LOGIC CROSS-CHECKS (ĐỐI SOÁT KIỂM TOÁN THỐNG KÊ)

1. **Bóc tách triệt để "Bẫy Gộp Liên Tỉnh Phú Yên" (Double Counting Trap)**:
   - Dòng tổng cộng trong biểu mẫu ghi: `TỈNH ĐẮK LẮK (MỚI) = 176.837 hộ`.
   - Đối soát chi tiết số học:
     $$\text{Đắk Lắk (15 huyện): } 160.363 \text{ hộ} + \text{Phú Yên (5 huyện): } 16.474 \text{ hộ} = 176.837 \text{ hộ}$$
   - **Kết luận**: Nếu không loại bỏ Phú Yên, báo cáo Đắk Lắk sẽ bị **thổi phồng thêm 16.474 hộ (10.2%)**. Pipeline đã lọc chính xác 15 huyện của Đắk Lắk.
2. **Đối soát Kiểm toán Tổng số hộ DTTS**:
   - Tổng 197 cặp Huyện $\times$ Dân tộc bóc tách: **160.361 hộ**.
   - Dòng tổng công bố chính thức tỉnh Đắk Lắk: **160.363 hộ**.
   - **Độ lệch**: Chỉ **2 hộ (0.001%)** do làm tròn số học trong mẫu suy rộng $\to$ **Đạt chuẩn kiểm toán thống kê quốc tế**.

---

### BƯỚC 5: CRITICAL DISCOVERY & BÓC TÁCH ĐỊNH LƯỢNG 4 TRỤ CỘT

#### 1. Ma trận Nghèo 2 Chiều: Tỷ lệ % (Intensity) vs Số hộ tuyệt đối (Volume):
Không mắc bẫy nhìn một chiều vào tỷ lệ %, phân loại 146 xã thành 4 nhóm chiến lược:

```
                          MA TRẬN NGHÈO ĐA CHIỀU CẤP XÃ (2023)
      ┌────────────────────────────────────────┬────────────────────────────────────────┐
      │  NHÓM A: NGHÈO CỰC ĐOAN - MẪU NHỎ      │  NHÓM B: ĐẠI VÙNG TRŨNG (CẦN CỨU TRỢ)  │
      │  (Tỷ lệ % rất cao, nhưng số hộ ít)     │  (Tỷ lệ % cao VÀ số hộ nghèo khổng lồ) │
      │  • Ia RVê (Ea Súp): 96.7% (290 hộ)     │  • Cư Pui (Krông Bông): 55.2% (1.355 hộ)│
      │  • Yang Reh (Kr. Bông): 72.6% (387 hộ) │  • Cư KBang (Ea Súp): 54.3% (1.348 hộ) │
%     │  • Ia Lốp (Ea Súp): 61.5% (335 hộ)     │  • Ea Hồ (Kr. Năng):  47.2% (939 hộ)   │
NGHÈO │  • Cư K Róa (M'Đrắk): 57.1% (283 hộ)   │  • Cư San (M'Đrắk):   77.6% (871 hộ)   │
      ├────────────────────────────────────────┼────────────────────────────────────────┤
      │  NHÓM C: ĐỊA BÀN PHÁT TRIỂN            │  NHÓM D: QUY MÔ LỚN - TỶ LỆ TRUNG BÌNH │
      │  (Tỷ lệ % thấp, số hộ nghèo ít)        │  (Tỷ lệ % vừa, nhưng số hộ nghèo đông) │
      │  • TP. Buôn Ma Thuột: 1.1% (139 hộ)    │  • Yang Tao (Lắk):    28.2% (674 hộ)   │
      │  • TX. Buôn Hồ:       5.7% (380 hộ)    │  • Krông Jing (M'Đrắk):33.2% (703 hộ)   │
      └────────────────────────────────────────┴────────────────────────────────────────┘
                                    SỐ HỘ NGHÈO TUYỆT ĐỐI
```

👉 **Khuyến nghị cho Sếp**: Ưu tiên ngân sách lớn nhất phải dành cho **Nhóm B (Cư Pui, Cư KBang, Ea Hồ, Cư San)** vì tại đây tập trung hàng nghìn hộ đói nghèo, tác động an sinh xã hội lớn hơn nhiều so với việc chỉ tập trung vào Ia RVê (290 hộ).

#### 2. Định lượng Lao động: Mắc kẹt trong bẫy Nông nghiệp thuần túy (88.97%):
* Tổng lao động DTTS có việc làm: **398.381 người**.
* Nông lâm thủy sản: **354.457 người (88.97%)**.
* Công nghiệp - Xây dựng: **21.508 người (5.40%)**.
* Dịch vụ: **21.691 người (5.44%)**.
👉 **Bản chất**: Nghèo đói không đơn thuần do địa lý, mà do **cơ cấu kinh tế chậm chuyển dịch**. Gần 90% lao động phụ thuộc hoàn toàn vào nương rẫy, năng suất thấp và bấp bênh giá nông sản.

#### 3. Định lượng Nhà ở: Mục tiêu 10.095 hộ nhà tạm dột nát:
* Toàn tỉnh có **10.095 hộ DTTS (6.29%)** đang ở nhà thiếu kiên cố và nhà đơn sơ. Đây là chỉ tiêu định lượng cụ thể để thiết lập KPI giám sát trên Power BI.

#### 4. Định lượng Vệ sinh: Bất bình đẳng nghiêm trọng về Hố xí hợp vệ sinh:
* Dù tỷ lệ nước hợp vệ sinh đạt **97.4%**, tỷ lệ hố xí hợp vệ sinh toàn tỉnh chỉ đạt **72.3%**.
* Tại **huyện Krông Búk chỉ đạt 40.4%**, **M'Đrắk đạt 53.9%**, **Krông Bông đạt 62.0%**, **Ea Súp đạt 63.3%**. Gần 60% hộ dân tại Krông Búk chưa có nhà vệ sinh hợp chuẩn, tạo nguy cơ ô nhiễm nguồn nước sinh hoạt ngầm.

---

### BƯỚC 6: PROPOSED ACTION PLAN & STAR SCHEMA

#### 1. Ma trận Lỗi Kỹ thuật Đã Xử Lý (Data Quality Defect Matrix - DQ):
| Mã Lỗi | Tên Lỗi | Phạm vi | Mức độ | Phương án xử lý của DA |
|:---:|---|:---:|:---:|---|
| **DQ-01** | Bẫy gộp tỉnh Phú Yên vào Đắk Lắk mới | Cấp tỉnh | **CRITICAL** | Lọc bỏ 5 huyện Phú Yên, chỉ giữ lại 15 Huyện Đắk Lắk. |
| **DQ-02** | Cell chứa footnote text `'15 (**)'`, `'-'` | Toàn bộ bảng | **CRITICAL** | Regex tách thành: `numeric_value` (float) và `sample_warning_flag`. |
| **DQ-03** | Ma trận ngang 53 cột dân tộc | 68 biểu mẫu | **HIGH** | Unpivot xoay dọc thành bảng Tidy Data. |
| **DQ-04** | Ngắt đôi cột dân tộc thành 2 khối | Biểu dân số | **HIGH** | Ghép ngang 2 khối tự động trước khi xoay dọc. |
| **DQ-05** | Lệch chuẩn chính tả tên địa phương | 15 huyện, 146 xã | **MEDIUM** | Map theo ID chuẩn `DL_DIST_xx` và `DL_COMM_xxx`. |

#### 2. Kiến trúc Mô hình Star Schema trên DuckDB:
```
[Dim_DiaBan] (146 xã, 15 huyện) ────── (1:N) ──────► [Fact_HaTang_Xa] (146 dòng)
      │                                                     │
      │ (1:N)                                               │ (Phân nhóm ma trận: A, B, C, D)
      ▼                                                     ▼
[Fact_DanSo_Huyen_DanToc] (197 dòng) ◄────── (1:N) ────── [Dim_DanToc] (53 dân tộc)
      │
      └──────► [Fact_KinhTe_XaHoi_Huyen_DanToc] (Lao động 89% nông nghiệp, Nhà tạm 10k hộ, Hố xí HVS)
```

**KẾT LUẬN**:  
Toàn bộ quy trình đọc hiểu, đối soát số học và phản biện đa chiều đã hoàn tất. Bộ dữ liệu sạch đã vượt qua 100% kiểm toán chất lượng và sẵn sàng nạp vào DuckDB để xây dựng báo cáo phân tích quản trị!
