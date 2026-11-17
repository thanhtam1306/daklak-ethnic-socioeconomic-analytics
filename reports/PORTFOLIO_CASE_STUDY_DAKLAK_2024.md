# CASE STUDY PORTFOLIO: HỆ THỐNG PHÂN TÍCH KINH TẾ - XÃ HỘI & THAM MƯU CHÍNH SÁCH 53 DÂN TỘC THIỂU SỐ TỈNH ĐẮK LẮK (ĐA KỲ 2019 - 2026)

> **Dự án**: `daklak-ethnic-socioeconomic-analytics`  
> **Người thực hiện**: Nguyễn Hoàng Thanh Tâm (Data Analyst)  
> **Email**: tamnguyen130620004@gmail.com | **GitHub**: [thanhtam1306](https://github.com/thanhtam1306/daklak-ethnic-socioeconomic-analytics)  
> **Lĩnh vực**: Phân tích Dữ liệu Chính sách Công (Public Policy Analytics) & Thống kê KTXH  
> **Ngăn xếp Công nghệ**: Python 3.10+ (Pandas, OpenpyXL, psycopg2) | PostgreSQL 18 & DuckDB (Star Schema) | Power BI Enterprise (100 Explicit DAX Measures) | Apache ECharts 5 | Vanilla JS Workbench  
> **Quy mô Dữ liệu**: 8 Tệp biểu mẫu thống kê ma trận thô (91 Sheets) $\rightarrow$ 3 Bảng Chiều (Dim) $\rightarrow$ 12 Bảng Sự Kiện (Fact) $\rightarrow$ 5 SQL Window Analytical Views $\rightarrow$ 3 Chu kỳ điều tra (Kỳ 2019, Kỳ 2024, Kỳ 2026 [Kế hoạch 2026–2030])  

---

## Executive Summary (Tóm Tắt Dành Cho Ban Lãnh Đạo)

Đắk Lắk là thủ phủ của vùng Tây Nguyên với cơ cấu dân cư đa dạng bậc nhất Việt Nam gồm 53 Dân tộc thiểu số (DTTS) sinh sống đan xen tại 15 huyện, thị xã, thành phố (146 xã, phường, thị trấn). Tuy nhiên, công tác hoạch định chính sách KTXH và phân bổ nguồn lực từ trước đến nay thường gặp phải hai rào cản chí mạng:
1. **Dữ liệu phân mảnh và bẫy thống kê ma trận**: Báo cáo tổng hợp dưới dạng hàng trăm bảng Excel ma trận ngang, các ô gộp (merged cells), phân cấp nhiều tầng, ký hiệu thống kê suy rộng phức tạp và dữ liệu gộp liên tỉnh (Đắk Lắk + Phú Yên), gây tốn kém hàng tháng trời đối soát thủ công và dễ sai lệch mẫu số.
2. **Thiếu liên kết giữa số liệu phân tích và dòng tiền ngân sách**: Các báo cáo truyền thống chỉ dừng lại ở mô tả định tính ("vùng sâu còn khó khăn", "chất lượng nhà ở thấp"), hoàn toàn thiếu vắng các mô hình kinh tế lượng đo lường ngưỡng tác động và không gắn kết với định mức đơn giá ngân sách Nhà nước theo các chương trình mục tiêu quốc gia (**QĐ 1719/QĐ-TTg, NĐ 28/2022/NĐ-CP, QĐ 318/QĐ-TTg**).

### Kết quả Cốt lõi Sau Khi Triển Khai Hệ Thống:
* **Tự động hóa 100% Pipeline Làm sạch & Tidy Data**: Quy chuẩn hóa 4 bước trích xuất 8 tệp Excel ma trận phức hợp thành 12 bảng Fact & 3 bảng Dim chuẩn mô hình Kimball Star Schema trên PostgreSQL 18 và DuckDB, loại bỏ 100% sai số mẫu số (đối soát khớp 99.999% quy mô 160.363 hộ DTTS).
* **Khai phá 14 Chuyên đề KTXH Thực Chiến**: Phát hiện và định lượng thành công:
  * *Nghịch lý Ea Súp*: Hạ tầng giao thông/điện lưới đạt 100% nhưng tỷ lệ nghèo lên đến 96.67% (bóc tách nguyên nhân từ cơ cấu 98.3% nông nghiệp tự cấp và thiếu đất sản xuất).
  * *Nghịch lý Giới tính Đối lập*: Gia đình Mẫu hệ bản địa (Ê Đê, Mnông) có nữ giới vượt trội về học vấn (+3.2% đến +5.4% so với nam), trái ngược hoàn toàn với nhóm Phụ hệ di cư (Mông, Dao, Thái) nơi nữ giới chịu bất bình đẳng giáo dục sâu sắc (nữ mù chữ cao gấp 2.1 lần nam).
  * *Điểm trũng Tiêu chí 17 Nông thôn mới*: Krông Bông (10.92%) và Lắk (12.64%) có tỷ lệ hố xí hợp vệ sinh thấp kỷ lục, đe dọa trực tiếp đến mục tiêu về đích NTM.
  * *Hiệu ứng Ngưỡng 20km*: Xác lập mô hình hồi quy kinh tế lượng: $\text{Tỷ lệ nghèo } (\%) = 13.10\% + 0.5132 \times \text{Khoảng cách } (km)$. Cứ cách trung tâm huyện lỵ thêm 10km, tỷ lệ nghèo tăng thêm 5.13 điểm %.
* **Kiến trúc Dữ liệu Động Đa Kỳ Tự Co Giãn (Multi-Period Scalable Architecture)**: Thiết lập hệ thống 3 chu kỳ (`KY_2019` $\rightarrow$ `KY_2024` $\rightarrow$ `KY_2026`) tự động lùi kỳ bằng SQL Window Functions (`LAG()`), tính toán động cơ dự toán ngân sách Nhà nước tăng từ **4.227,08 tỷ VNĐ** (2019) $\rightarrow$ **4.769,94 tỷ VNĐ** (2024) $\rightarrow$ **5.119,65 tỷ VNĐ** (2026–2030) với sai số 0.00 so với kho dữ liệu.
* **Hệ thống Power BI 4 Trang Chuẩn Enterprise & Bàn Thẩm Định Chính Sách (Workbench)**: Xây dựng 100 công thức DAX Explicit phân 10 Display Folders với cơ chế khóa ngữ cảnh chống Triple Counting, kết hợp ứng dụng Web Workbench chuẩn UX/UI Civic Dark/Light mode, ECharts 5 offline, sẵn sàng demo mọi lúc mọi nơi.

---

## 1. Bối Cảnh Nghiệp Vụ & Bài Toán Dữ Liệu (Business Context)

### 1.1. Phạm vi Địa bàn & Đối tượng Thụ hưởng
* **Địa bàn**: 15 đơn vị hành chính cấp Huyện/Thị xã/Thành phố của tỉnh Đắk Lắk gồm: TP. Buôn Ma Thuột, TX. Buôn Hồ và 13 huyện (Ea Súp, Buôn Đôn, Cư M'gar, Ea H'leo, Krông Búk, Krông Năng, Ea Kar, M'Đrắk, Krông Bông, Lắk, Krông Pắc, Krông Ana, Cư Kuin).
* **Cấp cơ sở**: 146 Xã/Phường/Thị trấn và 1.829 Thôn, Buôn, Tổ dân phố.
* **Đối tượng**: 53 Dân tộc thiểu số với 708.095 nhân khẩu (chiếm 38.2% dân số toàn tỉnh), trong đó nhóm bản địa Tây Nguyên lớn nhất là người Ê Đê (348.650 người) và Mnông (48.120 người).

### 1.2. Thách thức Dữ liệu Thực tế (Data Engineering Pitfalls)
Khi tiếp cận 8 file Excel từ cuộc tổng điều tra thống kê, nhóm phân tích đối mặt với 5 "cái bẫy" cấu trúc:
1. **Dữ liệu gộp 2 tỉnh trong 1 biểu**: Cơ quan thống kê gộp tỉnh Phú Yên (Vùng I: 16.474 hộ DTTS) và Đắk Lắk (Vùng II: 160.363 hộ DTTS) chung một sheet. Nếu không có thuật toán nhận diện địa danh, toàn bộ mẫu số toàn tỉnh sẽ bị thổi phồng sai 10.27%.
2. **Ký hiệu mẫu thống kê suy rộng (*, **, -, ...)**: Dữ liệu chứa các ký hiệu nghiệp vụ thống kê (`15 (*)` là mẫu nhỏ 25–49 quan sát; `39 (**)` là mẫu rất nhỏ <25 quan sát không suy rộng; `-` là không phát sinh; `...` là khuyết). Ép kiểu tự động sẽ gây lỗi `ValueError` hoặc chuyển thành `NaN` làm mất dữ liệu.
3. **Cấu trúc Stacked Blocks lồng nhau**: Bảng danh sách 53 dân tộc bị ngắt làm 2 khối dòng ngang (Khối 1: 35 dân tộc phổ biến; Khối 2: 18 dân tộc ít người).
4. **Lỗi khuyết ô thực tế (Data Defect)**: Biểu mẫu Internet viễn thông khuyết tên Huyện Cư Kuin tại dòng 27 (để trống nhưng số liệu tổng hộ là 7.714).
5. **Đa kỳ không đồng nhất (Data Drift)**: Khi cập nhật số liệu mới (Kỳ 2026), cấu trúc phân loại nghèo và chỉ tiêu kỹ thuật có độ dịch chuyển, đòi hỏi mô hình dữ liệu phải tự thích ứng mà không được sửa đổi mã nguồn.

---

## 2. Kiến Trúc Kỹ Thuật & Mô Hình Dữ Liệu (Technical Architecture)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          END-TO-END DATA PLATFORM ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [1. RAW SOURCES]         8 Tệp Excel Thống kê KTXH 53 DTTS (91 Sheets)                │
│                                      │                                                 │
│  [2. WRANGLING & QA]      scripts/wrangling/ (Regex Cleaning, Block Unstacking)        │
│                           scripts/quality_checks/ (100% Quality Tests Passed)          │
│                                      │                                                 │
│  [3. TIDY PARQUET]        12 Bảng Fact & 3 Bảng Dim (Parquet Snappy Compression)       │
│                                      │                                                 │
│  [4. DATA WAREHOUSE]      PostgreSQL 18 (daklak_socioeconomic) + DuckDB Engine         │
│                           ├── Schema: daklak_analytics                                 │
│                           ├── Kimball Star Schema (PK/FK Constraints, B-Tree Indexes)  │
│                           └── 5 Analytical Views (Window Functions LAG, DENSE_RANK)   │
│                                      ├─────────────────────────────┐                   │
│                                      ▼                             ▼                   │
│  [5. CONSUMPTION LAYER]   POWER BI DESKTOP             POLICY ASSISTANT WORKBENCH      │
│                           ├── 4 Enterprise Pages       ├── Python Flask Engine         │
│                           ├── 100 DAX Explicit         ├── SQL Guardrails (Read-Only)  │
│                           └── Anti-Triple Counting     └── ECharts 5 Offline / Bento   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Thiết kế Kimball Star Schema Chuẩn Enterprise
Hệ thống được thiết kế theo chuẩn Star Schema với 3 Bảng Chiều (Dimensions) và 12 Bảng Sự Kiện (Facts):

* **Bảng Chiều (Dimension Tables)**:
  1. `dim_diaban`: 146 xã, phân cấp huyện, vùng kinh tế, khoảng cách về trung tâm hành chính.
  2. `dim_dantoc`: 53 dân tộc thiểu số, nhóm nguồn gốc (Bản địa Tây Nguyên, Di cư phía Bắc, Nam Bộ), cờ DTTS rất ít người.
  3. `dim_ky_baocao`: Quản lý chu kỳ báo cáo (`KY_2019`, `KY_2024`, `KY_2026`), thứ tự kỳ (`thu_tu_ky`), giai đoạn chính sách và cờ `is_latest`.
  4. `dim_chitieu_kehoach_ngansach`: Định mức đơn giá ngân sách Nhà nước theo QĐ 1719/QĐ-TTg, NĐ 28/2022/NĐ-CP và QĐ 318/QĐ-TTg qua 3 giai đoạn.

* **Bảng Sự Kiện (Fact Tables - Đều có khóa ngoại `ma_ky`)**:
  * `fact_hatang_xa`: Điện lưới, đường ô tô, trạm y tế, trường học, tỷ lệ nghèo cấp xã.
  * `fact_danso_huyen_dantoc`: Dân số, số hộ, cơ cấu nam/nữ theo huyện và dân tộc.
  * `fact_giaoduc_dantoc`: Tỷ lệ biết chữ nam/nữ, tỷ lệ đi học đúng tuổi theo dân tộc.
  * `fact_laodong_dantoc`: Việc làm, phân bổ theo 3 ngành (Nông nghiệp, Công nghiệp, Dịch vụ).
  * `fact_trinhdo_cmkt_dantoc`: Trình độ chuyên môn kỹ thuật (Đại học, Cao đẳng, Trung cấp, Chưa đào tạo).
  * `fact_nhao_dantoc`: Chất lượng nhà ở (Kiên cố, Bán kiên cố, Thiếu kiên cố, Đơn sơ/Tạm).
  * `fact_dantocthiet_yeu_huyen`: Tiếp cận nước hợp vệ sinh, hố xí hợp vệ sinh, internet, điện thoại.
  * `fact_datsanxuat_dantoc`: Bình quân diện tích đất sản xuất nông nghiệp (ha/hộ).
  * `fact_tindung_dantoc`: Hộ vay vốn, nhu cầu vay chưa đáp ứng (khoảng trống tín dụng).
  * `fact_mucsinh_dantoc`: Tỷ suất sinh, sinh con thứ 3+, số ca sinh tại nhà không có cán bộ y tế.
  * `fact_nhankhau_dantoc`: Cơ cấu nhóm tuổi (0-14, 15-59, 60+), Tỷ lệ phụ thuộc, Chỉ số già hóa.
  * `fact_matuy_hiv_xa`: Tình hình tệ nạn xã hội (người nghiện ma túy, người nhiễm HIV) tại 146 xã.

---

## 3. Các Phát Hiện Phân Tích KTXH Trọng Tâm (Core Analytical Insights)

Mọi nhận định và phân tích trong dự án được tổ chức theo cấu trúc Kim tự tháp (The Pyramid Principle) và trình bày chuẩn **F-A-I-R (Fact - Analysis - Impact - Recommendation 4W1H)**. Lưu ý: Toàn bộ số liệu **Kỳ 2024** là dữ liệu khảo sát thực tế gốc (Ground-Truth); các mốc **Kỳ 2026** dưới đây là **kịch bản giả lập đa kỳ (Synthetic)** dùng để kiểm thử pipeline theo dõi tiến độ.

### 3.1. Trụ Cột 1: Nghịch Lý Nghèo Đa Chiều & Điểm Nghẽn Hạ Tầng Cứng
* **Fact**: Huyện Ea Súp đạt 100% xã có đường bê tông đến trung tâm và 100% trạm y tế kiên cố, nhưng tỷ lệ hộ nghèo DTTS bình quân lên tới **96.67%**, cao gấp 4.7 lần mức bình quân toàn tỉnh (20.63%).
* **Analysis**: Đầu tư công giai đoạn trước chỉ tập trung vào "hạ tầng cứng" (đường, trạm), hoàn toàn chưa giải quyết được "hạ tầng mềm" (sinh kế, nước tưới tiêu và chuyển giao khoa học kỹ thuật). Người dân có đường đi nhưng không có tư liệu sản xuất gia tăng giá trị.
* **Impact**: Nếu tiếp tục giải ngân dàn trải vào nâng cấp trụ sở, chỉ số nghèo sẽ trơ lỳ, gây lãng phí hàng trăm tỷ đồng vốn đầu tư công.
* **Recommendation**: Ban Quản lý CTMTQG 1719 chuyển đổi 60% cơ cấu vốn năm 2026 sang Tiểu dự án 2 (Hỗ trợ phát triển sản xuất theo chuỗi giá trị và giống cây trồng chịu hạn) cho 9 xã vùng sâu Ea Súp.

### 3.2. Trụ Cột 2: Đối Lập Nhân Học Giữa Gia Đình Mẫu Hệ & Phụ Hệ
* **Fact**: 
  * Ở nhóm DTTS bản địa theo chế độ Mẫu hệ (Ê Đê, Mnông), tỷ lệ phụ nữ biết chữ đạt **84.32%**, cao hơn nam giới (81.10%, chênh lệch nữ > nam là **+3.22 điểm %**).
  * Ngược lại, ở nhóm di cư phía Bắc theo chế độ Phụ hệ (Mông, Dao, Thái), tỷ lệ nữ biết chữ chỉ đạt **41.25%**, thấp hơn nam giới (68.40%, chênh lệch nam > nữ lên tới **-27.15 điểm %**). Riêng người Mông, tỷ lệ nữ mù chữ lên tới **62.80%**.
* **Analysis**: Văn hóa gia đình mẫu hệ trao quyền thừa kế và tiếng nói cho phụ nữ, khuyến khích con gái đi học. Nhóm phụ hệ vùng cao phía bắc vẫn tồn tại định kiến trọng nam khinh nữ và hủ tục kết hôn sớm.
* **Impact**: Bất bình đẳng giới trong giáo dục tạo ra cái bẫy đói nghèo liên thế hệ (Intergenerational Poverty Trap) ở các cụm dân cư người Mông (Ea Wy, Ea H'leo, Cư M'gar).
* **Recommendation**: Hội Liên hiệp Phụ nữ tỉnh phối hợp Sở GD&ĐT triển khai mô hình "Lớp học xóa mù chữ linh hoạt buổi tối tại điểm buôn làng", giảng dạy song ngữ Mông - Việt, có trợ cấp học phẩm từ Dự án 5 CTMTQG 1719.

### 3.3. Trụ Cột 3: Bẫy Lao Động Phổ Thông & Nghèo Kỹ Năng (Human Capital Trap)
* **Fact**: **87.36%** lao động DTTS toàn tỉnh (348.020 / 398.381 người) hoàn toàn không có bằng cấp, chứng chỉ chuyên môn kỹ thuật. Đỉnh điểm là người Mông: **96.98%** chưa qua đào tạo. Tỷ lệ lao động dồn vào nông nghiệp truyền thống chiếm **88.97%**.
* **Analysis**: Tỷ lệ lao động nông nghiệp thuần túy có mức tương quan tuyến tính rất cao ($R = 0.94$) với tỷ lệ không có chuyên môn kỹ thuật. Lao động DTTS khó có thể dịch chuyển sang các khu công nghiệp chế biến hay dịch vụ logistics nếu không được đào tạo nghề.
* **Impact**: Năng suất lao động thấp khiến thu nhập bình quân đầu người DTTS chỉ bằng 42% mức bình quân chung của tỉnh Đắk Lắk.
* **Recommendation**: Sở LĐ-TB&XH phối hợp các Hợp tác xã cà phê, sầu riêng mở các khóa đào tạo nghề ngắn hạn (3 tháng) cấp chứng chỉ vận hành máy nông nghiệp, kỹ thuật ủ phân hữu cơ vi sinh và sơ chế đạt chuẩn Xuất khẩu.

### 3.4. Trụ Cột 4: Điểm Trũng Vệ Sinh Dân Sinh Đe Dọa Tiêu Chí 17 Nông Thôn Mới
* **Fact**: Huyện Krông Bông chỉ có **10.92%** hộ DTTS có hố xí hợp vệ sinh; Huyện Lắk đạt **12.64%**; Huyện Krông Búk đạt **40.40%** (so với chuẩn nông thôn mới $\ge 70\%$ và TP. Buôn Ma Thuột là 94.30%).
* **Analysis**: Thói quen sinh hoạt truyền thống kết hợp với địa hình đồi dốc và nguồn nước ngầm khan hiếm vào mùa khô khiến việc xây dựng nhà vệ sinh tự hoại gặp nhiều trở ngại kỹ thuật.
* **Impact**: Nguy cơ thẩm thấu vi khuẩn gây ô nhiễm nguồn nước giếng khơi, bùng phát dịch bệnh đường tiêu hóa ở trẻ em và khiến 100% xã của Krông Bông, Lắk không thể về đích Nông thôn mới theo QĐ 318/QĐ-TTg.
* **Recommendation**: UBND các huyện Krông Bông, Lắk trích ngân sách vốn vay ưu đãi NHCSXH theo Nghị định 28/2022/NĐ-CP (gói 12 triệu đồng/hộ) kết hợp nguồn vốn xã hội hóa để hỗ trợ bồn chứa composite và mô hình hố xí sinh thái khô tự hoại.

### 3.5. Trụ Cột 5: Hiệu Ứng Ngưỡng Giao Thông 20km & Ma Trận Nghèo Khó Kép
* **Fact**: Thiết lập phương trình hồi quy OLS trên 146 xã:  
  $$\text{Tỷ lệ nghèo } (\%) = 13.10\% + 0.5132 \times \text{Khoảng cách đến Huyện } (km) \quad (R^2 = 0.485)$$
  Tất cả các xã cách trung tâm huyện lỵ $> 20km$ đều có tỷ lệ nghèo $> 30\%$.
* **Analysis**: Ma trận 4 góc phần tư bóc tách rõ nhóm "Khó khăn kép" gồm 28 xã (chiếm 42.81% tổng hộ nghèo toàn tỉnh), nằm tại các vành đai biên giới Ea Súp, Buôn Đôn và vùng sâu Krông Bông.
* **Impact**: Khoảng cách địa lý làm tăng chi phí vận chuyển nông sản lên 25–35%, khiến nông dân bị tư thương ép giá.
* **Recommendation**: Tỉnh ủy Đắk Lắk ban hành Nghị quyết chuyên đề ưu tiên kiên cố hóa các tuyến tỉnh lộ liên huyện kết nối 28 xã này vào trục Quốc lộ 14 và Quốc lộ 26.

### 3.6. Chuyên Đề 6: Bảo Tồn Khẩn Cấp Dân Tộc Rất Ít Người (Dân tộc Chơ Ro)
* **Fact (Thực tế Kỳ 2024)**: Tại kỳ 2024, toàn tỉnh ghi nhận duy nhất **4 hộ dân tộc Chơ Ro** (với 18 nhân khẩu sinh sống tại xã Krông Búk, huyện Krông Bách). 100% số hộ (4/4 hộ) sống trong nhà tạm dột nát, 0% phụ nữ biết chữ.
* **Kịch bản Giả lập Đa kỳ (Synthetic 2026 - Dùng kiểm thử Pipeline)**: Để kiểm thử khả năng theo dõi tiến độ mục tiêu theo Dự án 9 CTMTQG 1719, dữ liệu giả lập `KY_2026` mô phỏng kịch bản xóa 100% nhà tạm của người Chơ Ro (về 0 căn) và nâng tỷ lệ nữ biết chữ lên **50.0%**. *(Đây là kịch bản kiểm thử mô hình đa kỳ, không phải số liệu điều tra thực tế).*

### 3.7. Chuyên Đề 7: Tâm Chấn Tệ Nạn Ma Túy & HIV/AIDS Cấp Xã
* **Fact (Thực tế Kỳ 2024)**: Huyện Ea H'leo chiếm **32.1%** số người nghiện DTTS toàn tỉnh; Huyện Krông Năng chiếm **20.2%** số người nhiễm HIV. Đặc biệt, **Xã Ea Wy** (Ea H'leo) là điểm nóng cực đoan nhất toàn tỉnh với 42 người DTTS nghiện ma túy và 13 người DTTS nhiễm HIV.
* **Analysis**: Tuyến đường giáp ranh vùng kinh tế mới và dòng di cư tự do không kiểm soát tạo điều kiện cho các tụ điểm buôn bán ma túy len lỏi vào các thôn buôn vùng sâu.
* **Kịch bản Giả lập Đa kỳ (`2024 -> 2026`)**: Dữ liệu giả lập `KY_2026` mô phỏng mức giảm **-19.05%** tại Ea Wy nhằm kiểm thử truy vấn `LAG()` theo dõi điểm nóng an ninh xã hội.

### 3.8. Chuyên Đề 8: Mức Sinh Cực Đoan & Báo Động 1.023 Ca Sinh Con Tại Nhà
* **Fact (Thực tế Kỳ 2024)**: Kỳ 2024 ghi nhận **1.023 ca sinh con tại nhà** (không đến cơ sở y tế), trong đó người Mông chiếm tới 367 ca (và 131 ca hoàn toàn không có sự hỗ trợ của cán bộ y tế hay cô đỡ thôn bản). Toàn tỉnh có 46.044 phụ nữ DTTS sinh con thứ 3 trở lên.
* **Analysis**: Rào cản phong tục, khoảng cách đường đồi núi xa xôi và thiếu hụt mạng lưới y tế thôn bản am hiểu tiếng dân tộc.
* **Impact**: Nguy cơ tai biến sản khoa, tử vong mẹ và trẻ sơ sinh tăng cao tại các cụm dân cư vùng cao.
* **Recommendation & Kịch bản Giả lập (2026)**: Đề xuất đào tạo cô đỡ thôn bản người Mông tại chỗ, cấp gói đỡ đẻ sạch và trợ cấp dinh dưỡng 1,5 triệu đồng/ca khi đến trạm y tế sinh con. *(Trong kịch bản giả lập `KY_2026`, số ca sinh tại nhà ở người Mông được mô phỏng giảm từ 367 ca xuống 233 ca để kiểm thử chỉ báo mục tiêu trên Dashboard).*

---

## 4. Kiến Trúc Đa Kỳ Động & Động Cơ Dự Toán Ngân Sách Nhà Nước

### 4.1. Khung Logic Time Intelligence & Chống Double Counting
Khi mở rộng hệ thống sang kiến trúc đa kỳ (`KY_2019` $\rightarrow$ `KY_2024` $\rightarrow$ `KY_2026` [GĐ 2026–2030]), thách thức lớn nhất của một Data Analyst là: **Nếu người dùng không bấm chọn kỳ trên Slicer, làm thế nào để Dashboard không tự động cộng dồn số liệu của cả 3 kỳ lại với nhau?**

Giải pháp kiến trúc: Xây dựng **Anti-Triple Counting Gate** bằng DAX:
```dax
[Selected Period Order] = 
VAR _ExplicitOrder = SELECTEDVALUE('dim_ky_baocao'[thu_tu_ky])
VAR _LatestOrder = 
    CALCULATE(
        MAX('dim_ky_baocao'[thu_tu_ky]),
        REMOVEFILTERS('dim_ky_baocao'),
        'dim_ky_baocao'[is_latest] = TRUE()
    )
RETURN
    COALESCE(_ExplicitOrder, _LatestOrder)
```
*Tất cả 100 Explicit Measures đều được bao bọc bởi logic này: Khi mở báo cáo, hệ thống tự động khóa vào kỳ mới nhất (`thu_tu_ky = 3`, tức Kỳ 2026). Khi người dùng chọn Slicer, hệ thống linh hoạt chuyển đổi.*

### 4.2. Động Cơ Dự Toán Ngân Sách (Dynamic Policy Budgeting Engine)
Hệ thống không chỉ đếm số lượng, mà tự động liên kết số đối tượng cần hỗ trợ với đơn giá định mức của Nhà nước (`dim_chitieu_kehoach_ngansach`):

| Chỉ tiêu hỗ trợ | Định mức Ngân sách Nhà nước | Căn cứ Pháp lý |
|---|---|---|
| **Xóa nhà tạm, dột nát** | 44 triệu VNĐ / căn hộ | Dự án 1 - QĐ 1719/QĐ-TTg |
| **Nước sạch phân tán** | 3 triệu VNĐ / hộ | Dự án 1 - QĐ 1719/QĐ-TTg |
| **Hố xí hợp vệ sinh** | 12 triệu VNĐ / hộ | Vốn tín dụng ưu đãi NĐ 28/2022/NĐ-CP |
| **Đào tạo nghề CMKT ngắn hạn** | 4 triệu VNĐ / lao động | Dự án 5 - QĐ 1719/QĐ-TTg |
| **Hỗ trợ thiếu đất sản xuất** | 22,5 triệu VNĐ / hộ | Dự án 1 - QĐ 1719/QĐ-TTg |
| **Giải quyết khát vốn tín dụng** | 50 triệu VNĐ / hộ | Gói vay vi mô hộ nghèo NHCSXH |

### 4.3. Bảng Đối Soát Tổng Dự Toán Ngân Sách Qua 3 Kỳ (Khớp 100% CSDL)
* **Kỳ 2019 (Giai đoạn 2016–2020)**: **4.227,08 tỷ VNĐ**
* **Kỳ 2024 (Giai đoạn 2021–2025)**: **4.769,94 tỷ VNĐ**
* **Kỳ 2026 (Giai đoạn 2026–2030)**: **5.119,65 tỷ VNĐ**

*(Độ lệch giữa công thức DAX trên Power BI và View SQL `v_tong_hop_ngan_sach_chinh_sach_ky` trên PostgreSQL 18 là đúng **0.00 VNĐ**).*

---

## 5. Hệ Thống Power BI Dashboard 4 Trang Chuẩn Enterprise

Thiết kế tuân thủ nghiêm ngặt chuẩn **Gartner Visual Hierarchy** và nguyên tắc **F-A-I-R**:
1. **Trang 1: Bức Tranh Dân Số & Phân Bổ Địa Bàn (Demographics & Geography)**:
   * 4 Thẻ KPI: Tổng Dân số DTTS, Tổng Số Hộ, Tỷ số Giới tính, Tỷ lệ Tăng dân số.
   * Bản đồ nhiệt phân bổ mật độ dân cư DTTS tại 15 huyện.
   * Tháp tuổi kép (Nam/Nữ) và Scatter plot tương quan Tỷ lệ phụ thuộc vs Chỉ số già hóa.
2. **Trang 2: Nguồn Vốn Con Người & Bẫy Việc Làm (Education & Labor)**:
   * Đối chiếu Khoảng cách Giới trong biết chữ giữa các dòng họ Mẫu hệ vs Phụ hệ.
   * Biểu đồ tròn Donut phân tầng trình độ CMKT (87.36% chưa qua đào tạo).
   * 100% Stacked Bar cơ cấu 3 ngành kinh tế theo từng dân tộc.
3. **Trang 3: Điều Kiện Sống, Tư Liệu Sản Xuất & Tín Dụng (Living Conditions & Assets)**:
   * Cột điểm trũng vệ sinh kèm Reference Line chuẩn 70% Nông thôn mới.
   * Thanh đất sản xuất kèm Reference Line 0.5 ha/hộ (QĐ 1719).
   * 100% Stacked Bar phân loại kết cấu nhà ở theo từng dân tộc.
   * Clustered Bar thể hiện Khoảng trống tín dụng chính sách tại 15 huyện.
4. **Trang 4: Ma Trận Rủi Ro Xã Hội & Ưu Tiên Phân Bổ Nguồn Lực (Policy Matrix & Budget Allocation)**:
   * 4 KPI Cards dự toán ngân sách và hộ rủi ro cao.
   * Scatter Plot Ma trận 4 góc phần tư (Khoảng cách vs Tỷ lệ nghèo, 2 đường Reference Line X=20km, Y=30%).
   * Ma trận Giám sát Ma túy & HIV cấp xã (Conditional formatting cảnh báo đỏ).
   * Thẻ Báo cáo Tham mưu Động Đa Kịch Bản (`[Dynamic Policy Recommendation Text]`): Tự động ứng biến nội dung tham mưu theo 4 chế độ (Toàn tỉnh, Huyện, Dân tộc, Giao thoa Huyện x Dân tộc).

---

## 6. Trợ Lý Tham Mưu Chính Sách KTXH (`policy_assistant`)

Được thiết kế theo định vị **Hệ Thống Hỗ Trợ Ra Quyết Định (Decision Support System - DSS)**:
* **Kiến trúc Không Ảo Giác (Deterministic Intent Router + Parameterized SQL)**:
  * Không dùng LLM sinh truy vấn tự do (tránh rủi ro Hallucination trong số liệu Nhà nước).
  * 100% câu hỏi được ánh xạ vào 10 Intent nghiệp vụ đã được định nghĩa chặt chẽ.
* **Hàng rào Bảo mật SQL Guardrails (Read-Only Enterprise Gate)**:
  * Chặn 100% câu lệnh thay đổi dữ liệu (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`).
  * Chặn SQL Injection, stacked queries, chú thích ngụy trang (`--`, `/* */`), hàm hệ thống `pg_sleep`.
  * Tự động áp giới hạn trần `LIMIT 500`.
* **Giao diện Workbench (Civic Editorial Theme)**:
  * Chế độ Sáng/Tối (Light/Dark mode) lưu `localStorage`.
  * Lưu trạng thái bộ lọc vào URL Query Params (F5 không mất ngữ cảnh phân tích).
  * 5 KPI cards điều hành động theo vùng chọn (Scoped Dynamic KPIs).
  * Apache ECharts 5 nạp offline nội bộ 100% (chạy mượt mà kể cả khi ngắt internet).
  * Xuất báo cáo F-A-I-R theo thể thức tờ trình hành chính A4, hỗ trợ 1-Click Copy và xuất Markdown/CSV.

---

## 7. Bảng Đối Soát Tính Toàn Vẹn Số Liệu (Audit Reconciliation Matrix)

| Chỉ tiêu Kiểm toán | Số liệu File Thô (Ground Truth) | Số liệu Tidy Parquet | Số liệu PostgreSQL 18 | Số liệu Power BI DAX | Độ Lệch (Variance) | Đánh Giá |
|---|---|---|---|---|---|---|
| **Tổng số hộ DTTS (2024)** | 160.363 hộ | 160.363 hộ | 160.363 hộ | 160.363 hộ | **0** | Khớp tuyệt đối |
| **Lực lượng lao động DTTS** | 398.381 người | 398.381 người | 398.381 người | 398.381 người | **0** | Khớp tuyệt đối |
| **Dân số DTTS biết chữ** | 391.692 người | 391.692 người | 391.692 người | 391.692 người | **0** | Khớp tuyệt đối |
| **Số căn nhà tạm dột nát (2024)**| 10.095 căn | 10.095 căn | 10.095 căn | 10.095 căn | **0** | Khớp tuyệt đối |
| **Số hộ Chơ Ro xóa nhà tạm (2026)**| 0 căn | 0 căn | 0 căn | 0 căn | **0** | Khớp tuyệt đối |
| **Dự toán ngân sách Kỳ 2026**| 5.119,65 tỷ | 5.119,65 tỷ | 5.119,65 tỷ | 5.119,65 tỷ | **0.00** | Khớp tuyệt đối |

---

## 8. Bài Học Kinh Nghiệm & Kỹ Năng Rút Ra Qua Quá Trình Thực Hành

1. **Tư duy Chống Rác Số Liệu (Defensive Data Cleaning)**:
   * Thống kê hành chính luôn chứa bẫy gộp tỉnh, ô khuyết ngầm và footnote. Không bao giờ được tin tưởng dữ liệu trước khi thực hiện phép đối soát chéo (Reconciliation checks) giữa các biểu mẫu độc lập.
2. **Kỹ thuật Mô hình hóa Kimball trong Dữ liệu Chính sách**:
   * Việc tách bạch rõ `dim_diaban`, `dim_dantoc`, `dim_ky_baocao` và `dim_chitieu_kehoach_ngansach` giúp một truy vấn SQL phân tích có thể mở rộng từ 1 kỳ lên N kỳ chỉ bằng cách thêm điều kiện `ma_ky`, tiết kiệm 80% thời gian bảo trì code.
3. **Kỹ thuật DAX Context Transition Chuyên Sâu**:
   * Việc kết hợp `SELECTEDVALUE`, `COALESCE`, `REMOVEFILTERS` và `TREATAS` giải quyết triệt để lỗi cộng dồn sai khi dữ liệu mở rộng đa kỳ, đảm bảo trải nghiệm người dùng trên Power BI luôn mượt mà và chính xác.
4. **Văn hóa Báo cáo Dựa trên Bằng chứng & Định lượng Ngân sách (Evidence-Based Policy)**:
   * Làm phân tích dữ liệu không chỉ dừng lại ở việc vẽ biểu đồ đẹp, mà phải cố gắng trả lời được câu hỏi cốt lõi của bài toán thực tế: **"Vấn đề nằm ở đâu? Cần bao nhiêu tiền ngân sách để giải quyết? Và căn cứ vào điều khoản pháp lý nào?"**.

---
*Tài liệu thuộc hồ sơ thực hành và Portfolio cá nhân (`daklak-ethnic-socioeconomic-analytics`). Toàn bộ mã nguồn, dữ liệu chuẩn hóa, file PBIX và ứng dụng Workbench được lưu trữ tại kho lưu trữ dự án.*
