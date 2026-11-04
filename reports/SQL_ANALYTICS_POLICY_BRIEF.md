# BÁO CÁO PHÂN TÍCH CHÍNH SÁCH KINH TẾ - XÃ HỘI 53 DÂN TỘC THIỂU SỐ TỈNH ĐẮK LẮK 2024
## TÀI LIỆU PHÂN TÍCH CHUYÊN ĐỀ & ĐỀ XUẤT GIẢI PHÁP (F-A-I-R FRAMEWORK)

> **Dự án:** Thực hành Phân Tích Dữ Liệu Kinh Tế - Xã Hội Đắk Lắk  
> **Nguồn dữ liệu:** Điều tra Thực trạng KTXH 53 Dân tộc thiểu số năm 2024 (Ủy ban Dân tộc & Tổng cục Thống kê)  
> **Hạ tầng CSDL:** PostgreSQL 18 (`daklak_socioeconomic`, Schema: `daklak_analytics`)  
> **Phương pháp luận:** Khung Tư Duy F-A-I-R (Fact - Analysis - Impact - Recommendation) kết hợp Mô hình Kim Tự Tháp Minto & Kiến trúc Drill-Down.

---

## 🏛️ TRỤ CỘT 1: CHỈ SỐ NGHÈO ĐA CHIỀU (MDI) & XẾP HẠNG TOP XÃ KHÓ KHĂN

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Quyết định 1719/QĐ-TTg phê duyệt Chương trình Mục tiêu Quốc gia (CTMTQG) phát triển KTXH vùng đồng bào DTTS & Miền núi giai đoạn 2021–2030 và Nghị định 07/2021/NĐ-CP về chuẩn nghèo đa chiều.
- **Mục tiêu:** Nhận diện chính xác 10 xã "vùng lõi nghèo" của tỉnh thông qua Chỉ số Thiếu hụt Đa chiều tổng hợp (Composite Deprivation Index: Trọng số 40% Nghèo + 30% Giao thông + 20% Y tế + 10% Điện lưới) thay vì chỉ nhìn vào tỷ lệ nghèo đơn thuần.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
WITH calculated_deprivation AS (
    SELECT
        d.ten_huyen,
        f.ten_xa,
        f.ty_le_ngheo_pct,
        f.ty_le_thon_duong_cung_pct,
        f.tram_y_te_dat_chuan,
        f.so_thon_co_dien_luoi,
        f.so_thon,
        (
            COALESCE(f.ty_le_ngheo_pct, 0) * 0.40 +
            (100.0 - COALESCE(f.ty_le_thon_duong_cung_pct, 0)) * 0.30 +
            (CASE WHEN COALESCE(f.tram_y_te_dat_chuan, 0) = 0 THEN 100.0 ELSE 0.0 END) * 0.20 +
            (CASE WHEN f.so_thon > 0 THEN (1.0 - (f.so_thon_co_dien_luoi::NUMERIC / f.so_thon)) * 100.0 ELSE 0.0 END) * 0.10
        ) AS deprivation_score
    FROM
        daklak_analytics.fact_hatang_xa f
    JOIN
        daklak_analytics.dim_diaban d ON f.ma_xa = d.ma_xa
),
ranked_communes AS (
    SELECT 
        ten_huyen,
        ten_xa,
        ty_le_ngheo_pct,
        ty_le_thon_duong_cung_pct,
        tram_y_te_dat_chuan,
        so_thon_co_dien_luoi,
        so_thon,
        ROUND(deprivation_score::NUMERIC, 2) AS deprivation_score,
        DENSE_RANK() OVER (ORDER BY deprivation_score DESC) AS hardship_rank,
        NTILE(4) OVER (ORDER BY deprivation_score DESC) AS quartile_group
    FROM calculated_deprivation
)
SELECT
    hardship_rank,
    ten_huyen,
    ten_xa,
    deprivation_score,
    ty_le_ngheo_pct,
    ty_le_thon_duong_cung_pct,
    tram_y_te_dat_chuan,
    CONCAT(so_thon_co_dien_luoi, '/', so_thon) AS thon_dien_luoi_ratio,
    quartile_group
FROM 
    ranked_communes
WHERE
    hardship_rank <= 10
ORDER BY
    hardship_rank ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Top 10 Xã Khó Khăn Nhất Tỉnh)

| Hạng (Rank) | Tên Huyện | Tên Xã | Điểm Thiếu Hụt (Score) | Tỷ Lệ Nghèo DTTS (%) | Tỷ Lệ Đường Cứng (%) | Trạm Y Tế Đạt Chuẩn | Điện Lưới (Thôn) | Phân vị (Quartile) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | Huyện Ea Súp | **Xã Ia RVê** | **38.67** | **96.67%** | 100.00% | 1 (Đạt) | 12/12 | Q1 (Trũng nhất) |
| **2** | Huyện M'Đrắk | **Xã Cư San** | **31.02** | **77.56%** | 100.00% | 1 (Đạt) | 12/12 | Q1 |
| **3** | Huyện Krông Bông | **Xã Yang Reh** | **29.04** | **72.61%** | 100.00% | 1 (Đạt) | 7/7 | Q1 |
| **4** | Huyện Ea Kar | **Xã Cư ELang** | **28.03** | 42.81% | **63.64%** | 1 (Đạt) | 11/11 | Q1 |
| **5** | Huyện M'Đrắk | **Xã Cư M'ta** | **25.40** | **63.49%** | 100.00% | 1 (Đạt) | 11/11 | Q1 |
| **6** | Huyện Ea Súp | **Xã Ia Lốp** | **24.59** | **61.47%** | 100.00% | 1 (Đạt) | 12/12 | Q1 |
| **7** | Huyện Krông Bông | **Xã Cư Pui** | **24.38** | **55.19%** | 92.31% | 1 (Đạt) | 13/13 | Q1 |
| **8** | Huyện Buôn Đôn | **Xã Ea Nuôl** | **24.31** | 44.69% | **78.57%** | 1 (Đạt) | 14/14 | Q1 |
| **9** | Huyện M'Đrắk | **Xã Cư K Róa** | **22.82** | **57.06%** | 100.00% | 1 (Đạt) | 5/5 | Q1 |
| **10** | Huyện Krông Búk | **Xã Ea Sin** | **22.28** | **55.69%** | 100.00% | 1 (Đạt) | 7/7 | Q1 |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Điểm trũng nghiêm trọng nhất:** Xã **Ia RVê** (huyện biên giới Ea Súp) xếp thứ **#1 toàn tỉnh** về mức độ thiếu hụt đa chiều với **38.67 điểm**. Tỷ lệ hộ nghèo DTTS tại xã này lên tới **96.67%** (gần như 100% đồng bào DTTS sinh sống tại xã thuộc diện hộ nghèo).
- **Mức độ tập trung địa lý:** Top 10 xã khó khăn nhất tỉnh phân bố dày đặc ở 3 cụm địa bàn vùng sâu, vùng xa:
  - **Huyện M'Đrắk:** Chiếm 3/10 xã (*Cư San - 77.56%, Cư M'ta - 63.49%, Cư K Róa - 57.06%*).
  - **Huyện Ea Súp:** Chiếm 2/10 xã vùng biên giới (*Ia RVê - 96.67%, Ia Lốp - 61.47%*).
  - **Huyện Krông Bông:** Chiếm 2/10 xã (*Yang Reh - 72.61%, Cư Pui - 55.19%*).
- Toàn bộ 10 xã này đều thuộc nhóm **Quartile 1 (Q1)** - phân vị 25% các xã khó khăn nhất tỉnh Đắk Lắk.

#### 2. ANALYSIS (Phân Tích & Bóc Tách Nghịch Lý "Hạ Tầng vs Sinh Kế")
- **Nghịch lý dữ liệu nổi bật:** 100% các xã trong Top 10 đều ghi nhận **tỷ lệ phủ sóng điện lưới quốc gia đạt 100%** (12/12 hoặc 11/11 thôn), **Trạm y tế xã đều đạt chuẩn quốc gia (100%)**, và **tỷ lệ cứng hóa đường giao thông đến thôn buôn rất cao** (Ia RVê 100%, Cư San 100%, Yang Reh 100%).
- **Căn nguyên thực tế (Root Cause):**
  - **Độ lệch pha giữa đầu tư công và sinh kế:** Các chu kỳ đầu tư trước đây đã hoàn thành mục tiêu phủ sóng "hạ tầng cứng" (điện, đường, trạm), nhưng **chưa tạo ra dòng vốn sinh kế** và cơ chế thị trường tương ứng.
  - **Áp lực khắc nghiệt từ tự nhiên:** Ea Súp là vùng biên giới đất xói mòn, nhiễm phèn, thiếu nước ngọt tưới tiêu trầm trọng trong mùa khô; trong khi M'Đrắk là vùng thung lũng đồi dốc, chia cắt mạnh. Người dân có đường đi và có điện thắp sáng nhưng thiếu tư liệu sản xuất màu mỡ, thiếu kỹ thuật chuyển đổi canh tác thích ứng biến đổi khí hậu, dẫn đến việc sản xuất nông nghiệp tự cấp tự túc, năng suất thấp và rơi vào bẫy tái nghèo triền miên.

#### 3. IMPACT (Tác Động Chính Sách & Rủi Ro Thể Chế)
- **Rủi ro kiểm toán và đánh giá CTMTQG 1719:** Nếu tỉnh tiếp tục phân bổ ngân sách theo quán tính cơ học (dàn trải vốn xây dựng cơ bản vào đường sá, trụ sở tại các xã này), nguồn lực công sẽ bị lãng phí do các chỉ tiêu hạ tầng đã bão hòa, trong khi các chỉ tiêu cốt lõi về **giảm tỷ lệ nghèo và tăng thu nhập bình quân** sẽ bị trượt mục tiêu kiểm tra trung hạn.
- **Bất bình đẳng và nguy cơ tái nghèo diện rộng:** Khi tỷ lệ nghèo DTTS ở mức xấp xỉ tuyệt đối (Ia RVê 96.67%), bất kỳ cú sốc nào về giá nông sản hoặc thời tiết hạn hán sẽ lập tức đẩy toàn bộ cộng đồng vào tình trạng thiếu đói và gia tăng phụ thuộc vào trợ cấp nhà nước.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Hành Động Can Thiệp)

- **Tái cơ cấu dòng vốn đầu tư công (Ngay trong kỳ phân bổ ngân sách 2025):**
  Ban Dân tộc tỉnh cần chủ trì, phối hợp Sở Kế hoạch & Đầu tư và UBND các huyện Ea Súp, M'Đrắk, Krông Bông tạm dừng các dự án xây dựng hạ tầng cứng không cấp thiết tại cụm 10 xã này (do các chỉ tiêu điện, đường, trạm đã bão hòa). Thay vào đó, chuyển dịch tối thiểu **70% nguồn vốn sự nghiệp** thuộc Dự án 1 và Dự án 3 (CTMTQG 1719) sang **trực tiếp hỗ trợ sinh kế và chuyển giao khoa học kỹ thuật**.

- **Thiết lập Gói sinh kế chuyên biệt cho vùng lõi nghèo Ea Súp & M'Đrắk:**
  Sở Nông nghiệp & PTNT phối hợp với các hợp tác xã triển khai gói hỗ trợ chuyển đổi cơ cấu sản xuất trị giá **30–50 tỷ đồng**:
  - Tại huyện biên giới Ea Súp (đặc biệt xã Ia RVê): Tập trung giống cây trồng chịu hạn (điều ghép, xoài, cây ăn trái chịu hạn) kết hợp mô hình chăn nuôi đại gia súc (bò thịt, dê) có hợp đồng bao tiêu sản phẩm từ doanh nghiệp chế biến.
  - Tại thung lũng M'Đrắk (Cư San, Cư M'ta): Phát triển kinh tế lâm nghiệp bền vững dưới tán rừng và trồng cây dược liệu giá trị cao thích ứng địa hình đồi dốc.

- **Đổi mới căn bản mô hình đào tạo nghề nông thôn (Triển khai từ Quý 2/2025):**
  Sở LĐ-TB&XH chỉ đạo dừng triệt để các lớp đào tạo nghề lý thuyết đại trà không đầu ra; chuyển dịch sang mô hình "đào tạo theo đơn đặt hàng" ngắn hạn, gắn thẳng thực hành với các nhà máy chế biến cà phê, hồ tiêu, sầu riêng và cụm công nghiệp trên địa bàn tỉnh để bảo đảm việc làm có thu nhập ổn định ngay sau đào tạo.

---

##### 📋 Ma Trận Hành Động Can Thiệp (Executive Action Matrix)

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Địa bàn ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Chuyển 70% vốn sang sinh kế** | Ban Dân tộc tỉnh | Sở KH&ĐT, Sở Tài chính | Top 10 xã nghèo | Q1/2025 | Dự án 1 & 3 (CTMTQG 1719) |
| **Gói nông nghiệp chịu hạn & bao tiêu** | Sở Nông nghiệp & PTNT | Doanh nghiệp nông nghiệp | Xã Ia RVê (Ea Súp) | Q2/2025 | 30 - 50 tỷ đồng (Vốn sự nghiệp) |
| **Kinh tế lâm nghiệp & dược liệu** | UBND huyện M'Đrắk | Chi cục Kiểm lâm | Cư San, Cư M'ta | Q2/2025 | Dự án phát triển sinh kế |
| **Đào tạo nghề gắn chuỗi chế biến** | Sở LĐ-TB&XH | Các nhà máy chế biến | Toàn bộ 10 xã | Q2/2025 | Ngân sách đào tạo nghề DTTS |

---

## 🏛️ TRỤ CỘT 2: BẤT BÌNH ĐẲNG GIỚI & KHOẢNG CÁCH GIÁO DỤC (GENDER GAP IN EDUCATION)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Chiến lược Quốc gia về Bình đẳng giới giai đoạn 2021–2030 (Nghị quyết 28/NQ-CP) và Mục tiêu Phát triển Bền vững SDG 4 (Giáo dục chất lượng), SDG 5 (Bình đẳng giới).
- **Mục tiêu:** Nhận diện các dân tộc có sự chênh lệch học vấn nam - nữ trầm trọng nhất, giải mã căn nguyên nhân học (Mẫu hệ vs Phụ hệ) và đề xuất giải pháp xóa mù chữ linh hoạt gắn với sinh kế phụ nữ.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
WITH ethnic_literacy AS (
    SELECT
        ten_dantoc,
        nhom_nguon_goc,
        biet_chu_tong,
        biet_chu_nam,
        biet_chu_nu,
        ROUND(100.0 * biet_chu_nam / NULLIF(biet_chu_tong, 0), 2) AS ty_le_nam_pct,
        ROUND(100.0 * biet_chu_nu / NULLIF(biet_chu_tong, 0), 2) AS ty_le_nu_pct,
        ROUND((100.0 * biet_chu_nam / NULLIF(biet_chu_tong, 0)) - (100.0 * biet_chu_nu / NULLIF(biet_chu_tong, 0)), 2) AS gender_gap_pct
    FROM daklak_analytics.fact_giaoduc_dantoc
    WHERE biet_chu_tong >= 100 -- Lọc quy mô mẫu có ý nghĩa thống kê
),
ranked_gap AS (
    SELECT
        *,
        RANK() OVER (ORDER BY gender_gap_pct DESC) AS rank_bat_binh_dang
    FROM ethnic_literacy
)
SELECT 
    rank_bat_binh_dang,
    ten_dantoc,
    nhom_nguon_goc,
    biet_chu_tong,
    ty_le_nam_pct,
    ty_le_nu_pct,
    gender_gap_pct
FROM ranked_gap
WHERE rank_bat_binh_dang <= 10
ORDER BY rank_bat_binh_dang ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Top 10 Dân Tộc Có Khoảng Cách Giới Cao Nhất)

| Hạng (Rank) | Dân Tộc | Phân Nhóm Nguồn Gốc | Tổng Người Biết Chữ | Tỷ Lệ Nam (%) | Tỷ Lệ Nữ (%) | Khoảng Cách Giới Nam - Nữ (Gap %) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| **1** | **Hrê** | Khác | 264 | **91.67%** | 7.95% | **+83.71%** (Cực đoan) |
| **2** | **Khmer** | Nam Bộ & Duyên hải | 158 | **62.03%** | 37.97% | **+24.05%** |
| **3** | **Lào** | Di cư miền núi phía Bắc | 157 | **60.51%** | 40.13% | **+20.38%** |
| **4** | **Bru Vân Kiều** | Khác | 3.663 | **59.76%** | 40.27% | **+19.49%** |
| **5** | **Dao** | Di cư miền núi phía Bắc | 9.049 | **58.28%** | 41.72% | **+16.57%** |
| **6** | **Chứt** | Khác | 110 | **58.18%** | 41.82% | **+16.36%** |
| **7** | **Mường** | Di cư miền núi phía Bắc | 13.386 | **57.12%** | 42.88% | **+14.24%** |
| **8** | **Cơ Ho** | Bản địa Tây Nguyên | 167 | **55.09%** | 45.51% | **+9.58%** |
| **9** | **Nùng** | Di cư miền núi phía Bắc | 38.135 | **53.43%** | 46.57% | **+6.86%** |
| **10** | **Tày** | Di cư miền núi phía Bắc | 33.482 | **52.76%** | 47.24% | **+5.52%** |

*Ghi chú đặc biệt:* Ở 2 dân tộc bản địa đông dân nhất tỉnh, tỷ lệ nữ biết chữ thậm chí vượt nam: **Ê đê (Nữ 50.35% - 109.155 người)** và **Mnông (Nữ 51.84% - 12.255 người)**.

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Khoảng cách giới cực đoan ở nhóm thiểu số nhỏ:** Dân tộc **Hrê** đứng đầu bảng với mức chênh lệch nam - nữ lên tới **83.71%** (Nam chiếm 91.67% nhưng Nữ chỉ chiếm 7.95%), tuy nhiên quy mô mẫu tập trung nhỏ (264 người).
- **Điểm trũng ở các cộng đồng di cư quy mô lớn:** Xét trên các nhóm dân số đông, tình trạng bất bình đẳng giới bộc lộ rõ rệt nhất ở người **Bru Vân Kiều** (3.663 người - Gap **+19.49%**) và người **Dao** (9.049 người - Gap **+16.57%**).
- **Xu hướng thu hẹp theo quy mô và thời gian định cư:** Các cộng đồng di cư phía Bắc có quy mô dân số áp đảo và định cư lâu năm như **Mường** (13.386 người - Gap 14.24%), **Nùng** (38.135 người - Gap 6.86%) và **Tày** (33.482 người - Gap 5.52%) ghi nhận mức chênh lệch thấp hơn đáng kể, cho thấy quá trình hội nhập kinh tế giúp thu hẹp dần khoảng cách tiếp cận học vấn.

#### 2. ANALYSIS (Phân Tích Căn Nguyên: Đối Lập Văn Hóa Phụ Hệ vs Mẫu Hệ)
- **Rào cản từ cấu trúc Phụ hệ (Patriarchy) của nhóm di cư phía Bắc:** Các dân tộc Dao, Mường, Lào, Bru Vân Kiều mang đậm dấu ấn gia đình phụ hệ truyền thống. Người nam giữ vai trò trụ cột quyết định tài chính, đại diện giao thiệp xã hội và đứng tên tư liệu sản xuất. Phụ nữ vùng sâu trong các cộng đồng này chịu thiệt thòi kép: vừa gánh vác việc nương rẫy, nội trợ, chăm sóc con cái, vừa bị định kiến gia đình hạn chế cơ hội học chữ và tập huấn kỹ thuật.
- **Sự khác biệt với nền tảng Mẫu hệ (Matriarchy) bản địa Tây Nguyên:** Trái ngược hoàn toàn với nhóm phụ hệ, ở các dân tộc bản địa như **Ê đê và Mnông**, phụ nữ là chủ gia đình, nắm quyền quản lý kinh tế và quyền thừa kế đất đai. Vì vậy, con gái luôn được ưu tiên đi học ngang bằng hoặc vượt trội so với con trai (Ê đê có 109.155 nữ biết chữ vs 107.582 nam).
- **Bài học phương pháp luận:** Chính sách giáo dục và bình đẳng giới **tuyệt đối không thể áp dụng cào bằng cơ học (One-size-fits-all)**, mà bắt buộc phải phân hóa theo cấu trúc văn hóa gia đình của từng nhóm dân tộc.

#### 3. IMPACT (Tác Động Chính Sách & Rủi Ro Thể Chế)
- **Nguy cơ kìm hãm chỉ tiêu Phát triển Con người (HDI):** Bất bình đẳng giới trong học vấn là "lực cản vô hình" khiến các chính sách xóa nghèo vùng DTTS kém bền vững. Khi phụ nữ mù chữ hoặc không thạo tiếng phổ thông, các chính sách tín dụng vi mô, khuyến nông và chăm sóc sức khỏe sinh sản sẽ bị vô hiệu hóa vì phụ nữ không thể đọc tài liệu hướng dẫn và ghi chép sổ sách gia đình.
- **Sự thất bại của các lớp xóa mù chữ "đại trà":** Nếu Sở GD&ĐT tiếp tục mở lớp học chữ hành chính tập trung ban ngày, học viên nữ nhóm di cư phụ hệ sẽ tự động bỏ học do vướng bận việc nhà, con mọn và tâm lý mặc cảm trước nam giới.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Hành Động Can Thiệp)

- **Ưu tiên tập trung nguồn lực vào nhóm phụ hệ có nguy cơ cao (Triển khai ngay trong 2025):**
  Sở Giáo dục & Đào tạo phối hợp Ban Dân tộc tỉnh xác định phụ nữ và trẻ em gái thuộc nhóm **Dao, Bru Vân Kiều, Khmer** tại các xã vùng sâu huyện Ea Súp, Krông Bông, Ea Kar là đối tượng thụ hưởng khẩn cấp của Dự án 5 (CTMTQG 1719).

- **Đổi mới mô hình lớp xóa mù chữ linh hoạt "Đúng giờ - Gần nhà - Kèm hỗ trợ trẻ":**
  Tổ chức các lớp học ngay tại nhà sinh hoạt cộng đồng thôn buôn vào khung giờ tối hoặc thời gian nông nhàn. Hội Phụ nữ xã bố trí lực lượng đoàn viên tình nguyện hỗ trợ trông giữ trẻ nhỏ ngay tại điểm học để các bà mẹ yên tâm đến lớp.

- **Lồng ghép xóa mù chữ gắn liền với Kỹ năng Quản lý Tài chính (Financial Literacy):**
  Chuyển đổi giáo trình xóa mù chữ từ dạy chữ cái đơn thuần sang "học chữ để làm kinh tế": dạy cách đọc nhãn bao bì phân bón, tính toán liều lượng thuốc BVTV, ghi chép số cân bán nông sản và quản lý chi tiêu gia đình. Khi thấy chữ viết trực tiếp bảo vệ túi tiền của gia đình, phụ nữ sẽ có động lực học tập bền vững.

- **Vận động Người có uy tín và đàn ông trụ cột gia đình:**
  Huyện ủy và Ban Dân tộc phát huy vai trò của Trưởng thôn, Già làng và trực tiếp tuyên truyền đến nam giới trụ cột trong các dòng họ phụ hệ để giải phóng tư tưởng định kiến, biến người chồng thành hậu phương khuyến khích vợ con đi học.

---

##### 📋 Ma Trận Hành Động Can Thiệp Trụ Cột 2

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Lớp học linh hoạt buổi tối + giữ trẻ** | Sở GD&ĐT | Hội Liên hiệp Phụ nữ | Nữ giới Dao, Bru Vân Kiều | Q1–Q3/2025 | Dự án 5 (CTMTQG 1719) |
| **Giáo trình xóa mù chữ gắn tài chính** | Trung tâm GDTX tỉnh | Sở Nông nghiệp & PTNT | Phụ nữ DTTS nông thôn | Q2/2025 | Vốn sự nghiệp GD&ĐT |
| **Vận động nam giới trụ cột phụ hệ** | Ban Dân tộc tỉnh | Già làng, Người có uy tín | Cụm thôn bản Dao, Bru | Thường xuyên | Chương trình bình đẳng giới |

---

## 🏛️ TRỤ CỘT 3: CƠ CẤU VIỆC LÀM & BẪY LAO ĐỘNG NÔNG NGHIỆP THUẦN TÚY (88.97%)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chiến lược:** Nghị quyết Đại hội Đảng bộ tỉnh Đắk Lắk và Quy hoạch tỉnh Đắk Lắk thời kỳ 2021–2030, tầm nhìn 2050 về mục tiêu nâng cao tỷ trọng công nghiệp - xây dựng và dịch vụ trong GRDP, giảm dần tỷ trọng lao động nông nghiệp truyền thống.
- **Mục tiêu:** Định lượng quy mô phụ thuộc nương rẫy của từng nhóm dân tộc, giải mã "bẫy nông nghiệp" tự cấp tự túc và đề xuất giải pháp dịch chuyển cơ cấu lao động tại chỗ gắn với công nghiệp chế biến sâu.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
WITH labor_breakdown AS (
    SELECT
        ten_dantoc,
        nhom_nguon_goc,
        tong_lao_dong_co_viec_lam,
        lao_dong_nong_nghiep,
        lao_dong_cong_nghiep_xaydung,
        lao_dong_dich_vu,
        ROUND(100.0 * lao_dong_nong_nghiep / NULLIF(tong_lao_dong_co_viec_lam, 0), 2) AS ty_le_nong_nghiep_pct,
        ROUND(100.0 * (lao_dong_cong_nghiep_xaydung + lao_dong_dich_vu) / NULLIF(tong_lao_dong_co_viec_lam, 0), 2) AS ty_le_phi_nong_nghiep_pct,
        ROUND(100.0 * tong_lao_dong_co_viec_lam / SUM(tong_lao_dong_co_viec_lam) OVER (), 2) AS ty_trong_lao_dong_tinh_pct
    FROM daklak_analytics.fact_laodong_dantoc
    WHERE tong_lao_dong_co_viec_lam >= 500 -- Lọc các nhóm dân tộc có quy mô lao động từ 500 người trở lên
),
ranked_labor AS (
    SELECT
        *,
        CASE 
            WHEN ty_le_nong_nghiep_pct >= 90.0 THEN 'Bẫy nông nghiệp nghiêm trọng (>90%)'
            WHEN ty_le_nong_nghiep_pct >= 75.0 THEN 'Phụ thuộc nông nghiệp cao (75-90%)'
            ELSE 'Chuyển dịch tích cực (<75%)'
        END AS phan_loai_chuyen_dich,
        RANK() OVER (ORDER BY ty_le_nong_nghiep_pct DESC) AS rank_phu_thuoc_nong_nghiep
    FROM labor_breakdown
)
SELECT 
    rank_phu_thuoc_nong_nghiep,
    ten_dantoc,
    nhom_nguon_goc,
    tong_lao_dong_co_viec_lam,
    ty_trong_lao_dong_tinh_pct,
    ty_le_nong_nghiep_pct,
    ty_le_phi_nong_nghiep_pct,
    phan_loai_chuyen_dich
FROM ranked_labor
ORDER BY rank_phu_thuoc_nong_nghiep ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Cơ Cấu Lao Động Theo Dân Tộc)

| Hạng | Dân Tộc | Phân Nhóm Nguồn Gốc | Tổng Lao Động (Người) | Tỷ Trọng Trong Tỉnh (%) | Tỷ Lệ Nông Nghiệp (%) | Tỷ Lệ Phi Nông Nghiệp (%) | Phân Loại Chuyển Dịch |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| **1** | **Mông** | Di cư miền núi phía Bắc | 28.018 | 7.06% | **98.30%** | 1.70% | Bẫy nông nghiệp nghiêm trọng (>90%) |
| **2** | **Gia Rai** | Bản địa Tây Nguyên | 10.631 | 2.68% | **94.51%** | 5.40% | Bẫy nông nghiệp nghiêm trọng (>90%) |
| **3** | **Sán Chay** | Di cư miền núi phía Bắc | 1.874 | 0.47% | **92.80%** | 7.15% | Bẫy nông nghiệp nghiêm trọng (>90%) |
| **4** | **Nùng** | Di cư miền núi phía Bắc | 34.742 | 8.75% | **91.83%** | 7.91% | Bẫy nông nghiệp nghiêm trọng (>90%) |
| **5** | **Tày** | Di cư miền núi phía Bắc | 29.443 | 7.42% | **89.82%** | 10.12% | Phụ thuộc nông nghiệp cao (75-90%) |
| **6** | **Thái** | Di cư miền núi phía Bắc | 12.373 | 3.12% | **89.40%** | 10.21% | Phụ thuộc nông nghiệp cao (75-90%) |
| **7** | **Ê đê** | Bản địa Tây Nguyên | 225.772 | **56.87%** | **88.44%** | 11.35% | Phụ thuộc nông nghiệp cao (75-90%) |
| **8** | **Mnông** | Bản địa Tây Nguyên | 23.591 | 5.94% | **88.41%** | 11.32% | Phụ thuộc nông nghiệp cao (75-90%) |
| **9** | **Hrê** | Khác | 540 | 0.14% | **86.11%** | 13.89% | Phụ thuộc nông nghiệp cao (75-90%) |
| **10** | **Dao** | Di cư miền núi phía Bắc | 10.028 | 2.53% | **85.06%** | 14.86% | Phụ thuộc nông nghiệp cao (75-90%) |
| **11** | **Bru Vân Kiều**| Khác | 3.035 | 0.76% | **84.09%** | 15.91% | Phụ thuộc nông nghiệp cao (75-90%) |
| **12** | **Xơ Đăng** | Bản địa Tây Nguyên | 4.202 | 1.06% | **79.08%** | 20.87% | Phụ thuộc nông nghiệp cao (75-90%) |
| **13** | **Mường** | Di cư miền núi phía Bắc | 11.644 | 2.93% | **74.43%** | **25.46%** | Chuyển dịch tích cực (<75%) |
| **14** | **Hoa** | Nam Bộ & Duyên hải | 1.107 | 0.28% | **60.89%** | **39.21%** | Chuyển dịch tích cực (<75%) |

*Tổng thể toàn tỉnh:* Tổng số 398.380 lao động DTTS có việc làm, trong đó Nông nghiệp chiếm **354.455 người (88.97%)**, Công nghiệp - Xây dựng chiếm **21.506 người (5.40%)**, Dịch vụ chiếm **21.691 người (5.44%)**.

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Quy mô và mức độ phụ thuộc toàn tỉnh:** Toàn tỉnh có 398.380 lao động DTTS có việc làm thì có tới **354.455 người làm nông - lâm - thủy sản (chiếm đúng 88.97%)**. Khối phi nông nghiệp chỉ chiếm vỏn vẹn **11.03%** (Công nghiệp - Xây dựng: 5.40%, Dịch vụ: 5.44%).
- **Đỉnh điểm bẫy nông nghiệp ở người Mông:** Dân tộc Mông đứng đầu bảng với tỷ lệ làm nông nghiệp lên tới **98.30%** (27.541 trên tổng số 28.018 lao động); tỷ lệ làm công nghiệp và dịch vụ chỉ đạt **1.70%** (gần như bị trói chặt hoàn toàn vào nương rẫy).
- **Thị phần lao động áp đảo của người Ê Đê:** Người Ê Đê chiếm tới **56.87% tổng lực lượng lao động DTTS toàn tỉnh** (225.772 lao động). Tỷ lệ làm nông nghiệp của người Ê Đê là **88.44%**, tương đương 199.670 người. Tính chung, 4 dân tộc bản địa (Ê đê, Mnông, Gia Rai, Xơ Đăng) chiếm tới **66.55%** tổng lực lượng lao động toàn tỉnh.

#### 2. ANALYSIS (Bóc Tách Căn Nguyên "Bẫy Nông Nghiệp" vs "Điểm Sáng Chuyển Dịch")
- **Tại sao nhóm Mông, Gia Rai phụ thuộc nương rẫy gần như tuyệt đối (>90%)?**
  - *Rào cản địa lý & lịch sử di cư:* Đồng bào Mông di cư tự do thường chọn cư trú ở những triền núi dốc, vùng sâu hẻo lánh huyện Krông Bông, Ea Súp, M'Đrắk, nơi hạ tầng kết nối thị trường lao động công nghiệp gần như bằng không.
  - *Hạn chế về chứng chỉ nghề & tác phong công nghiệp:* Thiếu kỹ năng chuyên môn kỹ thuật, rào cản tiếng phổ thông và thói quen canh tác nương rẫy tự do khiến họ rất khó vượt qua các vòng phỏng vấn tuyển dụng vào các nhà máy có kỷ luật thời gian nghiêm ngặt.
- **Tại sao người Mường và người Hoa lại chuyển dịch tích cực hơn?**
  - *Người Mường (25.46% phi nông nghiệp):* Có mức độ giao thoa văn hóa cao, định cư ở các vùng thấp, huyện đồng bằng (Ea Kar, Krông Năng), linh hoạt tham gia xây dựng và làm công ăn lương tại các đô thị.
  - *Người Hoa (39.21% phi nông nghiệp):* Gắn liền với truyền thống thương mại, làm dịch vụ thu mua nông sản, chế biến và buôn bán tiểu thương tại các trung tâm huyện lỵ và TP. Buôn Ma Thuột.

#### 3. IMPACT (Tác Động Kinh Tế & Kìm Hãm Chỉ Tiêu Tỉnh)
- **Rủi ro sinh kế cực lớn trước biến đổi khí hậu & biến động giá cả:** Phụ thuộc 89% vào nông nghiệp khiến đời sống của hơn 350.000 hộ đồng bào bị gắn chặt vào sự bấp bênh của thời tiết (hạn hán mùa khô Tây Nguyên) và chu kỳ trồi sụt của giá cà phê, tiêu, sầu riêng. Khi nông sản mất giá, toàn bộ cộng đồng lập tức rơi vào khủng hoảng thu nhập.
- **Điểm nghẽn thực hiện Nghị quyết công nghiệp hóa của tỉnh:** Đắk Lắk không thể hoàn thành mục tiêu tăng tỷ trọng công nghiệp và dịch vụ trong GRDP nếu hơn một nửa lực lượng lao động toàn tỉnh (đặc biệt là 225.772 lao động Ê Đê) vẫn chỉ làm nông nghiệp thô với năng suất thấp. Trong khi đó, các cụm công nghiệp mới mở trên địa bàn tỉnh lại đối mặt với nghịch lý "khát" công nhân kỹ thuật tại chỗ.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Hành Động Can Thiệp)

- **Mô hình "Đưa nhà máy về gần buôn làng" (Sở Công Thương & Ban Quản lý các KCN chủ trì):**
  Quy hoạch và ưu đãi thuế tối đa để thu hút các doanh nghiệp chế biến sâu (sấy sầu riêng, chế biến cà phê hòa tan, đóng hộp hoa quả) đặt nhà xưởng ngay tại các huyện trọng điểm nông nghiệp (Cư M'gar, Krông Pắc, Ea H'leo). Việc này giúp chuyển dịch lao động nông nghiệp sang công nhân công nghiệp chế biến một cách tự nhiên mà người dân không phải rời xa buôn làng.

- **Đào tạo nghề "đặt hàng trước - tuyển dụng ngay" cho thanh niên Ê Đê và Mông:**
  Sở LĐ-TB&XH phối hợp với các doanh nghiệp nông nghiệp lớn (Simexco, Trung Nguyên, VinaCafe) tổ chức các khóa đào tạo lái máy cày, vận hành hệ thống tưới tự động, bảo trì cơ khí nông nghiệp và kỹ thuật chế biến. Đảm bảo 100% học viên hoàn thành khóa đào tạo được ký hợp đồng lao động chính thức.

- **Thúc đẩy Hợp tác xã Nông nghiệp Tuần hoàn & Giá trị Cao:**
  Đối với lực lượng lao động tiếp tục làm nông nghiệp, Liên minh HTX tỉnh hỗ trợ chuyển đổi từ canh tác quảng canh sang mô hình HTX đạt chuẩn VietGAP/GlobalGAP, có hợp đồng bao tiêu sản phẩm để ổn định đầu ra, nâng cao thu nhập trên cùng một đơn vị diện tích đất rẫy.

---

##### 📋 Ma Trận Hành Động Can Thiệp Trụ Cột 3

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Đưa nhà máy chế biến sâu về huyện** | Sở Công Thương | Ban Quản lý KCN, UBND Huyện | Vùng nguyên liệu Ea H'leo, Krông Pắc | 2025–2026 | Vốn xúc tiến đầu tư & FDI |
| **Đào tạo nghề gắn việc làm tại xưởng** | Sở LĐ-TB&XH | Doanh nghiệp nông sản lớn | Thanh niên Ê Đê, Mông | Q2/2025 | Dự án 5 (CTMTQG 1719) |
| **Hỗ trợ HTX nông nghiệp tuần hoàn** | Liên minh HTX tỉnh | Sở Nông nghiệp & PTNT | Cụm hộ nương rẫy Mông, Gia Rai | Q3/2025 | Quỹ hỗ trợ phát triển HTX |

---

## 🏛️ TRỤ CỘT 4: ĐIỂM NGHẼN ĐIỀU KIỆN VỆ SINH DÂN SINH & NƯỚC SẠCH (HỐ XÍ HỢP VỆ SINH)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Tiêu chí số 17 về *Môi trường và An toàn thực phẩm* trong Bộ Tiêu chí Quốc gia về Xã Nông thôn mới (Quyết định 318/QĐ-TTg) và Quyết định 1719/QĐ-TTg về cải thiện điều kiện sống thiết yếu cho đồng bào DTTS.
- **Mục tiêu:** Nhận diện các điểm trũng về tiếp cận công trình vệ sinh (nhà tiêu hợp vệ sinh) và nước sạch sinh hoạt giữa các địa phương, phân tích tính khả thi và đề xuất lộ trình can thiệp có trọng tâm, tránh dàn trải.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
WITH district_hygiene AS (
    SELECT
        ten_huyen,
        ROUND(AVG(ty_le_ho_xi_hop_ve_sinh_pct), 2) AS avg_hoxi_pct,
        ROUND(AVG(ty_le_nuoc_hop_ve_sinh_pct), 2) AS avg_nuoc_pct,
        ROUND(AVG(so_ho_co_internet), 1) AS avg_ho_internet
    FROM daklak_analytics.fact_dantocthiet_yeu_huyen
    WHERE ty_le_ho_xi_hop_ve_sinh_pct IS NOT NULL
    GROUP BY ten_huyen
),
ranked_districts AS (
    SELECT
        ten_huyen,
        avg_hoxi_pct,
        avg_nuoc_pct,
        avg_ho_internet,
        ROUND(AVG(avg_hoxi_pct) OVER (), 2) AS bq_toan_tinh_pct,
        ROUND(avg_hoxi_pct - AVG(avg_hoxi_pct) OVER (), 2) AS chenh_lech_so_voi_tinh,
        DENSE_RANK() OVER (ORDER BY avg_hoxi_pct ASC) AS rank_vung_trung
    FROM district_hygiene
)
SELECT
    rank_vung_trung,
    ten_huyen,
    avg_hoxi_pct,
    bq_toan_tinh_pct,
    chenh_lech_so_voi_tinh,
    avg_nuoc_pct,
    avg_ho_internet
FROM ranked_districts
ORDER BY rank_vung_trung ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (15 Đơn Vị Cấp Huyện Toàn Tỉnh)

| Hạng Vùng Trũng | Tên Địa Phương | Tỷ Lệ Hố Xí HVS (%) | Bình Quân Tỉnh (%) | Chênh Lệch So Với Tỉnh (Delta) | Tỷ Lệ Nước HVS (%) | Số Hộ Có Internet (BQ) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **1** | **Huyện Krông Bông** | **10.92%** | 17.71% | **-6.79%** | 20.12% | 167.9 |
| **2** | **Huyện Lắk** | **12.64%** | 17.71% | **-5.07%** | 25.65% | 165.4 |
| **3** | **Thị Xã Buôn Hồ** | **13.88%** | 17.71% | **-3.83%** | 16.90% | 146.2 |
| **4** | **Huyện Krông Búk** | **14.39%** | 17.71% | **-3.32%** | 22.64% | 91.7 |
| **5** | **Huyện Cư Kuin** | **14.49%** | 17.71% | **-3.22%** | 16.81% | 145.5 |
| **6** | Huyện M'Đrắk | 16.67% | 17.71% | -1.04% | 23.89% | 140.5 |
| **7** | Huyện Ea Súp | 17.16% | 17.71% | -0.55% | 29.98% | 150.2 |
| **8** | Huyện Ea H'leo | 17.44% | 17.71% | -0.27% | 22.41% | 204.2 |
| **9** | Huyện Krông Năng | 18.26% | 17.71% | +0.55% | 27.60% | 212.6 |
| **10** | Huyện Ea Kar | 18.32% | 17.71% | +0.61% | 23.80% | 164.1 |
| **11** | Huyện Krông A Na | 18.82% | 17.71% | +1.11% | 22.64% | 75.9 |
| **12** | Huyện Krông Pắc | 18.96% | 17.71% | +1.25% | 26.30% | 234.9 |
| **13** | Huyện Cư M'gar | 20.55% | 17.71% | +2.84% | 30.13% | 371.5 |
| **14** | Huyện Buôn Đôn | 23.72% | 17.71% | +6.01% | 26.32% | 133.0 |
| **15** | **TP. Buôn Ma Thuột** | **29.42%** | 17.71% | **+11.71%** | 30.19% | 208.6 |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Mức bình quân chung thấp:** Tỷ lệ hộ đồng bào DTTS có nhà tiêu hợp vệ sinh bình quân toàn tỉnh chỉ đạt **17.71%**, cho thấy đây là một trong những chỉ tiêu thiếu hụt lớn nhất trong đời sống dân sinh.
- **Biên độ chênh lệch địa bàn sâu sắc (Gap 18.50 điểm %):** 
  - Đơn vị cao nhất là **TP. Buôn Ma Thuột** đạt **29.42%** (+11.71 điểm % so với bình quân tỉnh), tiếp theo là **Buôn Đôn (23.72%)** và **Cư M'gar (20.55%)**.
  - Đơn vị thấp nhất là **Krông Bông (10.92%)** và **Lắk (12.64%)**, thấp hơn mức bình quân tỉnh từ 5 đến 7 điểm %.
- **Cơ cấu phân bố:** Trong tổng số 15 đơn vị hành chính, có 7 đơn vị đạt trên mức bình quân tỉnh và 8 đơn vị nằm dưới mức bình quân. Top 5 vùng trũng thiếu hụt nghiêm trọng nhất gồm: **Krông Bông, Lắk, Buôn Hồ, Krông Búk và Cư Kuin**.

#### 2. ANALYSIS (Phân Tích Căn Nguyên & Khía Cạnh Đa Chiều)
- **Lợi thế đô thị & vùng thâm canh cà phê lâu đời:** TP. Buôn Ma Thuột và huyện Cư M'gar có điều kiện kinh tế - thu nhập hộ gia đình cao hơn, nguồn cung ứng vật liệu xây dựng sẵn có, thợ thi công tại chỗ dồi dào và mạng lưới thông tin truyền thông phát triển mạnh (Cư M'gar có bình quân 371.5 hộ có internet/dân tộc).
- **Rào cản tự nhiên, địa hình và kinh tế vùng sâu:** 
  - Tại **Krông Bông và Lắk**, địa hình chia cắt mạnh bởi núi cao và thung lũng sông Krông Ana, tỷ lệ hộ nghèo cao khiến khả năng tích lũy tiền mặt để tự xây nhà tiêu tự hoại là một gánh nặng tài chính lớn.
  - Vùng thường xuyên ngập lụt vào mùa mưa lũ (ven hồ Lắk, sông Krông Bông) đòi hỏi thiết kế kỹ thuật chống tràn phức tạp và tốn kém hơn bình thường.
- **Sự khác biệt giữa "Có nhà tiêu" và "Hợp vệ sinh":** Nhiều hộ gia đình đã tự làm nhà tiêu tạm bợ nhưng không có bể tự hoại khép kín, khoảng cách đặt gần nguồn nước ngầm hoặc giếng đào dẫn đến việc không đáp ứng tiêu chuẩn vệ sinh của Bộ Y tế.

#### 3. IMPACT (Tác Động Chính Sách & Sức Khỏe Cộng Đồng)
- **Rủi ro trượt chuẩn Tiêu chí 17 (Nông thôn mới):** Mặc dù không thể khẳng định một huyện trượt chuẩn NTM chỉ dựa trên tỷ lệ này (cần đối chiếu với ngưỡng quy định của từng vùng), nhưng mức độ thiếu hụt nghiêm trọng tại Krông Bông (10.92%) và Lắk (12.64%) chắc chắn là lực cản lớn nhất kìm hãm tiến độ về đích Nông thôn mới của các xã vùng DTTS.
- **Nguy cơ ô nhiễm tầng nước ngầm và dịch bệnh đường tiêu hóa:** Tây Nguyên phụ thuộc lớn vào nguồn nước giếng khơi/giếng khoan tầng nông. Việc thiếu nhà tiêu hợp vệ sinh kết hợp tỷ lệ nước hợp vệ sinh thấp (Krông Bông chỉ đạt 20.12%) làm tăng nguy cơ phát tán vi sinh vật gây bệnh đường tiêu hóa (tiêu chảy, ký sinh trùng), đặc biệt đe dọa sức khỏe của trẻ em và người cao tuổi.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Lộ Trình Can Thiệp)

- **Đối với Ban Chỉ đạo Nông thôn mới cấp tỉnh:**
  - Thành lập bản đồ phân bố tỷ lệ nhà tiêu hợp vệ sinh theo cấp xã để xác định chính xác các "điểm nóng" cần can thiệp ưu tiên; chấm dứt tình trạng phân bổ kinh phí hỗ trợ vệ sinh môi trường cào bằng giữa các huyện.
  - Ưu tiên lồng ghép nguồn vốn Dự án 1 (CTMTQG 1719) để hỗ trợ trực tiếp gói vật liệu tự hoại cho các xã có tỷ lệ dưới 15% tại Krông Bông và Lắk.

- **Đối với Sở Y tế và Trung tâm Kiểm soát Bệnh tật (CDC):**
  - Tăng cường kiểm định định kỳ chất lượng nguồn nước ngầm tại các buôn làng có tỷ lệ nhà tiêu hợp vệ sinh thấp.
  - Đẩy mạnh truyền thông thay đổi hành vi: Rửa tay bằng xà phòng, hướng dẫn quy chuẩn xây dựng nhà tiêu hợp vệ sinh cách xa giếng nước tối thiểu 10m.

- **Thí điểm mô hình "Nhà tiêu sinh thái / Tự hoại chi phí thấp":**
  UBND các huyện Krông Bông, Lắk phối hợp với các tổ chức phát triển nông thôn chuyển giao các mẫu thiết kế nhà tiêu tự hoại bằng bi bê tông đúc sẵn hoặc nhà tiêu sinh thái khô 2 ngăn, tận dụng vật liệu địa phương để giảm giá thành xây dựng xuống dưới 3–5 triệu đồng/công trình, phù hợp khả năng chi trả của hộ cận nghèo.

- **Phát huy vai trò của Hội Phụ nữ và Đoàn Thanh niên thôn buôn:**
  Phát động phong trào "Buôn làng xanh - Nhà tiêu an toàn", thành lập các tổ phụ nữ tiết kiệm xoay vòng vốn để giúp từng nhóm 3-5 hộ gia đình hỗ trợ nhau công thợ và vật liệu hoàn thành công trình vệ sinh.

---

##### 📋 Lộ Trình Triển Khai Can Thiệp Trụ Cột 4

| Giai đoạn | Hoạt động trọng tâm | Đơn vị chủ trì | Kết quả cần đạt |
|---|---|---|---|
| **0 – 3 tháng** | Khảo sát thực địa, lập danh sách hộ thiếu nhà tiêu HVS tại Krông Bông & Lắk | UBND Huyện, Trưởng buôn | Bóc tách chính xác danh sách hộ nghèo cần hỗ trợ |
| **3 – 6 tháng** | Chuyển giao thiết kế mẫu chi phí thấp, phân bổ vốn hỗ trợ vật liệu xi măng/bi bê tông | Sở Xây dựng, Sở Y tế | Thí điểm thành công 200–300 công trình mẫu |
| **6 – 12 tháng** | Vận động phụ nữ tiết kiệm xoay vòng vốn, nhân rộng mô hình toàn huyện | Hội Phụ nữ, Đoàn TN | Nâng tỷ lệ tiếp cận tại cụm xã điểm lên trên 35% |
| **Định kỳ quý** | Giám sát chất lượng nước ngầm và kiểm tra nghiệm thu công trình thực tế | CDC tỉnh, Trạm y tế xã | Ngăn chặn nguy cơ ô nhiễm nguồn nước sinh hoạt |

---

## 🏛️ TRỤ CỘT 5: ĐÁNH GIÁ ĐÒN BẨY HẠ TẦNG GIAO THÔNG & KHOẢNG CÁCH ĐỊA LÝ ĐẾN KHẢ NĂNG THOÁT NGHÈO

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ lý thuyết:** Trong kinh tế học phát triển và Chương trình Mục tiêu Quốc gia Xây dựng Nông thôn mới (Tiêu chí số 2 về Giao thông), hạ tầng giao thông kết nối được coi là "mạch máu kinh tế". Khi đường sá được kiên cố hóa và khoảng cách đến thị trường ngắn lại, chi phí vận chuyển nông sản giảm, thương lái vào tận buôn làng thu mua, người dân dễ tiếp cận bệnh viện, trường học và việc làm phi nông nghiệp.
- **Mục tiêu nghiên cứu:** Đánh giá mối quan hệ thực nghiệm giữa khoảng cách địa lý đến trung tâm huyện với tỷ lệ hộ nghèo DTTS trên toàn bộ 146 xã, kiểm định giả thuyết "Ngưỡng khoảng cách 20km" và giải quyết bài toán mâu thuẫn giữa Cường độ nghèo (Intensity) vs Quy mô tuyệt đối (Volume).

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
WITH distance_cohorts AS (
    SELECT
        CASE 
            WHEN km_den_trung_tam_huyen < 10.0 THEN '1. Rất gần (< 10km)'
            WHEN km_den_trung_tam_huyen < 20.0 THEN '2. Trung bình (10 - 19km)'
            WHEN km_den_trung_tam_huyen < 35.0 THEN '3. Xa (20 - 34km)'
            ELSE '4. Rất xa (>= 35km - Vùng sâu/biên giới)'
        END AS phan_nhom_khoang_cach,
        so_thon,
        tong_ho_dtts,
        so_ho_ngheo,
        km_den_trung_tam_huyen
    FROM daklak_analytics.fact_hatang_xa
),
cohort_summary AS (
    SELECT
        phan_nhom_khoang_cach,
        COUNT(*) AS so_xa,
        SUM(tong_ho_dtts) AS tong_ho_dtts,
        SUM(so_ho_ngheo) AS tong_ho_ngheo,
        ROUND(100.0 * SUM(so_ho_ngheo) / NULLIF(SUM(tong_ho_dtts), 0), 2) AS ty_le_ngheo_bq_pct,
        ROUND(AVG(km_den_trung_tam_huyen), 1) AS culy_trung_binh_km,
        ROUND(100.0 * SUM(so_ho_ngheo) / SUM(SUM(so_ho_ngheo)) OVER (), 2) AS ty_trong_ho_ngheo_toan_tinh_pct
    FROM distance_cohorts
    GROUP BY phan_nhom_khoang_cach
)
SELECT
    phan_nhom_khoang_cach,
    so_xa,
    tong_ho_dtts,
    tong_ho_ngheo,
    ty_le_ngheo_bq_pct,
    culy_trung_binh_km,
    ty_trong_ho_ngheo_toan_tinh_pct
FROM cohort_summary
ORDER BY phan_nhom_khoang_cach ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Phân Tầng Khoảng Cách 146 Xã)

| Nhóm Khoảng Cách | Số Xã | Tổng Hộ DTTS | Số Hộ Nghèo | Tỷ Lệ Nghèo BQ (%) | Cự Ly Trung Bình Đến Huyện | Tỷ Trọng Trong Tổng Hộ Nghèo Tỉnh (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Rất gần (< 10km)** | 57 | 59.570 | 9.756 | **16.38%** | 4.7 km | 31.19% |
| **2. Trung bình (10–19km)** | 52 | 59.295 | 10.860 | **18.32%** | 14.1 km | 34.72% |
| **3. Xa (20–34km)** | 26 | 27.280 | 7.291 | **26.73%** | 23.9 km | 23.31% |
| **4. Rất xa (>= 35km - Vùng biên)** | 11 | 11.405 | 3.372 | **29.57%** | 46.9 km | 10.78% |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Tương quan đồng biến giữa cự ly và tỷ lệ nghèo:** Tỷ lệ hộ nghèo DTTS tăng đều đặn theo khoảng cách địa lý đến trung tâm hành chính huyện: từ **16.38%** ở cự ly rất gần (4.7km) lên **29.57%** ở cự ly rất xa (46.9km), tương đương mức chênh lệch tăng gấp **1.81 lần (+13.19 điểm %)**.
- **Dấu hiệu "Hiệu ứng ngưỡng 20km":** Tỷ lệ nghèo biến động nhẹ trong bán kính 20km (từ 16.38% lên 18.32%, chênh lệch +1.94 điểm %), nhưng **bật tăng đột biến lên 26.73% (+8.41 điểm %)** ngay khi bước qua ngưỡng cự ly 20–34km.
- **Nghịch lý quy mô tuyệt đối (Volume) vs Tỷ lệ nghèo (Intensity):**
  - Nhóm gần và trung bình (<20km) có tỷ lệ nghèo thấp hơn nhưng chiếm tới **109/146 xã** và tập trung **20.616 hộ nghèo (chiếm 65.91% tổng số hộ nghèo toàn tỉnh)**.
  - Ngược lại, nhóm rất xa (>=35km) có tỷ lệ nghèo ngất ngưởng (29.57%) nhưng chỉ chiếm 11 xã và 3.372 hộ nghèo (chiếm 10.78% tổng số hộ nghèo).

#### 2. ANALYSIS (Phân Tích Căn Nguyên & Cơ Chế Tác Động)
- **Cơ chế kinh tế của "Ngưỡng khoảng cách 20km":**
  - *Chi phí vận tải & Logistics nông sản:* Trong bán kính dưới 20km (khoảng 30 phút đi xe máy), người dân có thể tự chở nông sản ra chợ huyện tiêu thụ hoặc thương lái dễ dàng vào tận vườn thu mua. Khi vượt quá 20km, chi phí xăng xe và độ hao hụt đường dốc tăng cao khiến thương lái ép giá nông sản từ 10–20%, bào mòn lợi nhuận thực tế của người trồng.
  - *Tiếp cận thị trường việc làm phi nông nghiệp:* Người lao động ở cự ly <20km có thể đi - về trong ngày để làm việc tại các nhà máy, công trường xây dựng hoặc dịch vụ tại thị trấn. Ngoài 20km, chi phí thuê trọ hoặc thời gian di chuyển trở thành rào cản ngăn họ tham gia thị trường lao động chính thức.
  - *Tiếp cận dịch vụ công & thông tin:* Khoảng cách xa làm giảm tần suất tiếp cận các chương trình khuyến nông, hội chợ việc làm và dịch vụ y tế dự phòng.
- **Sự khác biệt giữa Cường độ nghèo và Quy mô tuyệt đối:**
  - *Cường độ nghèo (29.57% ở vùng biên):* Phản ánh mức độ thiếu hụt hạ tầng sâu sắc và sự cô lập địa lý.
  - *Quy mô tuyệt đối (20.616 hộ ở vùng ven):* Phản ánh bài toán mật độ dân số đông và áp lực thiếu đất sản xuất/việc làm tại chỗ khi đô thị hóa diễn ra.
- **Hạn chế của cách tiếp cận đầu tư cục bộ:** Xây dựng đường bê tông nội thôn buôn nhưng tuyến đường liên xã, liên huyện nối ra quốc lộ bị xuống cấp thì chuỗi logistics vẫn bị đứt gãy, không hạ được chi phí vận chuyển cho người dân.

#### 3. IMPACT (Tác Động Đến Quy Hoạch Giao Thông & Phân Bổ Ngân Sách)
- **Rủi ro phân bổ ngân sách "lệch pha":** Nếu chỉ dựa vào *tỷ lệ nghèo (%)*, nguồn vốn sẽ bị dồn toàn bộ vào 11 xã vùng biên xa xôi mà bỏ quên 2/3 số hộ nghèo đang sinh sống ngay vùng ven huyện. Ngược lại, nếu chỉ dựa vào *số lượng tuyệt đối*, các buôn làng vùng sâu biên giới sẽ vĩnh viễn bị bỏ lại phía sau vì chi phí suất đầu tư trên mỗi hộ dân tại đây rất cao.
- **Đòi hỏi cơ chế phân bổ kết hợp đa tiêu chí:** Chính sách giảm nghèo bền vững bắt buộc phải cân bằng giữa mục tiêu giải quyết số đông (giảm số lượng hộ nghèo tuyệt đối) và mục tiêu an sinh xã hội - an ninh biên giới (giải quyết các xã có tỷ lệ nghèo đặc biệt cao).

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Hai Gọng Kìm)

- **Chiến lược phân bổ hai gói chính sách can thiệp (Two-Pronged Approach):**
  
  **GÓI 1: Vùng gần và trung bình (Cự ly < 20km - Ưu tiên Giảm nghèo diện rộng qua Thị trường)**
  - *Mục tiêu:* Hỗ trợ 20.616 hộ nghèo vươn lên thoát nghèo bền vững bằng sinh kế phi nông nghiệp và kết nối chuỗi cung ứng.
  - *Hành động:* Sở LĐ-TB&XH kết nối giới thiệu việc làm tại các cụm công nghiệp huyện lỵ; Liên minh HTX hỗ trợ hợp đồng bao tiêu nông sản sạch; Ngân hàng CSXH cấp vốn tín dụng vi mô mở rộng dịch vụ thương mại tại gia đình.
  
  **GÓI 2: Vùng xa và rất xa (Cự ly >= 20km - Ưu tiên Hạ tầng kết nối & Củng cố nền tảng)**
  - *Mục tiêu:* Phá thế cô lập địa lý cho 11 xã vùng sâu, biên giới (Ea Súp, Krông Bông, M'Đrắk).
  - *Hành động:* Sở Giao thông Vận tải ưu tiên nâng cấp các tuyến đường huyết mạch liên huyện, liên xã nối vùng nguyên liệu ra trục Quốc lộ/Tỉnh lộ; đầu tư hệ thống điểm gom và trạm cân nông sản cộng đồng; hỗ trợ an sinh xã hội có điều kiện cho hộ nghèo kinh niên.

- **Thiết lập Bộ tiêu chí giám sát định kỳ:**
  Cơ quan thống kê và Ban Dân tộc tỉnh tích hợp dữ liệu GIS và khoảng cách địa lý vào Dashboard quản trị để theo dõi: Tỷ lệ thay đổi hộ nghèo trước và sau khi cứng hóa đường giao thông, thời gian di chuyển bình quân ra thị trường, và chi phí vận chuyển nông sản trên một đơn vị sản phẩm.

---

##### 📋 Ma Trận Phân Bổ Nguồn Lực Theo Khoảng Cách Địa Lý

| Phân tầng khoảng cách | Số xã / Tỷ lệ nghèo | Số hộ nghèo phụ trách | Mục tiêu trọng tâm | Trọng tâm can thiệp | Nguồn vốn đề xuất |
|---|:---:|:---:|---|---|---|
| **Vùng gần (< 20km)** | 109 xã (16%–18%) | **20.616 hộ (65.9%)** | Tạo việc làm, tăng thu nhập | Đào tạo nghề, kết nối HTX, tín dụng vi mô | Vốn việc làm, tín dụng CSXH |
| **Vùng xa (>= 20km)** | 37 xã (26%–30%) | **10.663 hộ (34.1%)** | Phá thế cô lập, an sinh cơ bản | Đường huyết mạch liên vùng, trạm cân, an sinh | Vốn CTMTQG 1719 & Nông thôn mới |

---

# 🔍 CÁC CHUYÊN ĐỀ ĐÀO SÂU PHÂN NHÁNH (EXECUTIVE DEEP-DIVE TRACKS)

---

## 📡 CHUYÊN ĐỀ 1: KHOẢNG CÁCH SỐ & KHẢ NĂNG TIẾP CẬN DỊCH VỤ CÔNG TRỰC TUYẾN (DIGITAL DIVIDE)

### 1. Bối Cảnh Nghiệp Vụ & Đề Án Chuyển Đổi Số
- **Căn cứ chiến lược:** Quyết định 749/QĐ-TTg phê duyệt Chương trình Chuyển đổi số Quốc gia và Đề án 06 về phát triển ứng dụng dữ liệu dân cư, định danh và xác thực điện tử phục vụ chuyển đổi số quốc gia giai đoạn 2022–2025.
- **Mục tiêu phân tích:** Định vị các "vùng trũng số" (Digital Blind Spots) tại cấp huyện và theo nhóm dân tộc để đánh giá khả năng hấp thụ dịch vụ công trực tuyến (VNeID, Cổng Dịch vụ công Quốc gia), tránh tình trạng đầu tư công nghệ nhưng người dân buôn làng không thể tiếp cận do thiếu hạ tầng Internet.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
-- 1. Xếp hạng Tỷ lệ tiếp cận Internet theo Huyện (Tìm vùng trũng số)
WITH district_internet AS (
    SELECT 
        f.ten_huyen,
        SUM(f.so_ho_co_internet) AS tong_ho_co_internet,
        SUM(d.so_ho) AS tong_so_ho_dtts,
        ROUND(100.0 * SUM(f.so_ho_co_internet) / NULLIF(SUM(d.so_ho), 0), 2) AS ty_le_internet_pct,
        ROUND(AVG(100.0 * SUM(f.so_ho_co_internet) / NULLIF(SUM(d.so_ho), 0)) OVER (), 2) AS bq_tinh_pct
    FROM daklak_analytics.fact_dantocthiet_yeu_huyen f
    JOIN daklak_analytics.fact_danso_huyen_dantoc d 
      ON f.ma_huyen = d.ma_huyen AND f.ma_dantoc = d.ma_dantoc
    WHERE f.so_ho_co_internet IS NOT NULL
    GROUP BY f.ten_huyen
)
SELECT 
    DENSE_RANK() OVER (ORDER BY ty_le_internet_pct ASC) AS rank_vung_trung_so,
    ten_huyen,
    tong_ho_co_internet,
    tong_so_ho_dtts,
    ty_le_internet_pct,
    bq_tinh_pct,
    ROUND(ty_le_internet_pct - bq_tinh_pct, 2) AS gap_so_voi_tinh
FROM district_internet
ORDER BY rank_vung_trung_so ASC;

-- 2. Phân tích tiếp cận Internet theo Nhóm Nguồn Gốc Dân Tộc
SELECT 
    d.nhom_nguon_goc,
    SUM(f.so_ho_co_internet) AS tong_ho_internet,
    SUM(d.so_ho) AS tong_ho_dtts,
    ROUND(100.0 * SUM(f.so_ho_co_internet) / NULLIF(SUM(d.so_ho), 0), 2) AS ty_le_internet_pct
FROM daklak_analytics.fact_dantocthiet_yeu_huyen f
JOIN daklak_analytics.fact_danso_huyen_dantoc d 
  ON f.ma_huyen = d.ma_huyen AND f.ma_dantoc = d.ma_dantoc
WHERE f.so_ho_co_internet IS NOT NULL
GROUP BY d.nhom_nguon_goc
ORDER BY ty_le_internet_pct ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Internet Hộ Gia Đình Toàn Tỉnh)

#### A. Xếp Hạng 15 Đơn Vị Cấp Huyện Theo Tỷ Lệ Tiếp Cận Internet
| Hạng Vùng Trũng Số | Tên Huyện | Hộ Có Internet | Tổng Số Hộ DTTS | Tỷ Lệ Internet (%) | Bình Quân Tỉnh (%) | Lệch So Với Tỉnh (Delta) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **1** | **Huyện Lắk** | 8.768 | 11.465 | **76.48%** | 85.50% | **-9.02%** |
| **2** | **Huyện Ea Kar** | 8.698 | 11.301 | **76.97%** | 85.50% | **-8.53%** |
| **3** | **Huyện Krông A Na** | 4.023 | 5.083 | **79.15%** | 85.50% | **-6.35%** |
| **4** | **Huyện Cư Kuin** | 7.712 | 9.572 | **80.57%** | 85.50% | **-4.93%** |
| **5** | Huyện Ea H'leo | 10.824 | 13.161 | 82.24% | 85.50% | -3.26% |
| **6** | Huyện M'Đrắk | 7.446 | 8.819 | 84.43% | 85.50% | -1.07% |
| **7** | Huyện Buôn Đôn | 7.049 | 8.179 | 86.18% | 85.50% | +0.68% |
| **8** | Huyện Cư M'gar | 19.690 | 22.714 | 86.69% | 85.50% | +1.19% |
| **9** | Thị Xã Buôn Hồ | 7.747 | 8.800 | 88.03% | 85.50% | +2.53% |
| **10** | Huyện Krông Pắc | 12.452 | 13.963 | 89.18% | 85.50% | +3.68% |
| **11** | TP. Buôn Ma Thuột | 11.058 | 12.379 | 89.33% | 85.50% | +3.83% |
| **12** | Huyện Krông Bông | 8.901 | 9.495 | 93.74% | 85.50% | +8.24% |
| **13** | Huyện Ea Súp | 7.962 | 8.493 | 93.75% | 85.50% | +8.25% |
| **14** | Huyện Krông Năng | 11.268 | 11.877 | 94.87% | 85.50% | +9.37% |
| **15** | **Huyện Krông Búk** | 4.862 | 5.060 | **96.09%** | 85.50% | **+10.59%** |

#### B. Phân Hóa Tiếp Cận Internet Theo Nhóm Nguồn Gốc Dân Tộc
| Nhóm Nguồn Gốc | Số Hộ Có Internet | Tổng Số Hộ Khảo Sát | Tỷ Lệ Tiếp Cận (%) |
|:---|:---:|:---:|:---:|
| **Nam Bộ & Duyên hải (Hoa, Khmer, Chăm)** | 406 | 525 | **77.33%** |
| **Bản địa Tây Nguyên (Ê đê, Mnông, Gia Rai...)** | 86.788 | 102.541 | **84.64%** |
| **Di cư miền núi phía Bắc (Tày, Nùng, Mông...)** | 49.547 | 55.524 | **89.24%** |
| **Khác** | 1.719 | 1.771 | **97.06%** |

*Ghi chú dân tộc:* Trong các dân tộc bản địa đông dân, người **Gia Rai (77.49%)** và người **Cơ Ho (76.71%)** có tỷ lệ tiếp cận Internet thấp nhất tỉnh.

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Quy mô phủ sóng toàn tỉnh:** Toàn tỉnh Đắk Lắk có **138.460 hộ đồng bào DTTS có kết nối Internet**, đạt tỷ lệ bình quân chung là **85.50%**.
- **Điểm trũng số tập trung tại cụm 4 huyện:** Huyện **Lắk (76.48%)**, **Ea Kar (76.97%)**, **Krông A Na (79.15%)** và **Cư Kuin (80.57%)** là 4 địa bàn tụt hậu số nặng nề nhất, thấp hơn mức bình quân toàn tỉnh từ 5 đến 9 điểm %. Tại huyện Lắk, vẫn còn tới **2.697 hộ đồng bào hoàn toàn "ngoại tuyến"** với không gian số.
- **Khoảng cách tiếp cận giữa các nhóm dân tộc:** Nhóm bản địa Tây Nguyên đạt 84.64%, thấp hơn 4.6 điểm % so với nhóm di cư miền núi phía Bắc (89.24%). Đặc biệt, cộng đồng người **Gia Rai (77.49%)** và **Cơ Ho (76.71%)** ghi nhận mức độ tiếp cận Internet thấp nhất trong số các dân tộc có trên 1.000 hộ.

#### 2. ANALYSIS (Phân Tích Căn Nguyên "Điểm Nghẽn Số Vùng Cao")
- **Rào cản địa hình & Mật độ trạm thu phát sóng (BTS):** Huyện Lắk và Krông A Na có nhiều buôn làng phân tán ven hồ Lắk, lòng chảo sông Krông Ana và các sườn núi dốc. Địa hình trũng thấp và che chắn tự nhiên khiến vùng phủ sóng 4G bị gián đoạn, nhiều buôn vùng sâu sóng di động rất chập chờn, chưa có hạ tầng cáp quang băng rộng đến từng hộ gia đình.
- **Rào cản chi phí duy trì dịch vụ viễn thông:** Mặc dù tỷ lệ hộ có điện thoại thông minh tương đối phổ biến, nhưng chi phí gói cước dữ liệu di động hoặc Internet cáp quang cố định (150.000 – 200.000 đ/tháng) là một gánh nặng tài chính đối với các hộ nghèo thuần nông, dẫn đến việc họ chỉ dùng sim rác hoặc ngắt dịch vụ khi hết vụ thu hoạch nông sản.
- **Độ vênh giữa "Thiết bị số" và "Kỹ năng số" (Digital Divide vs Usage Gap):** Đa phần người dân có kết nối mạng chỉ sử dụng các tính năng cơ bản như xem video (TikTok, YouTube) hoặc mạng xã hội giải trí. Tỷ lệ người dân DTTS biết tự cài đặt VNeID mức 2, tra cứu kết quả giải quyết thủ tục hành chính hoặc nộp hồ sơ dịch vụ công trực tuyến còn rất hạn chế do rào cản thao tác giao diện tiếng Việt phức tạp.

#### 3. IMPACT (Tác Động Đến Đề Án Chuyển Đổi Số Của Tỉnh)
- **Nguy cơ lãng phí đầu tư công nghệ số:** Nếu tỉnh tiếp tục chạy theo chỉ tiêu số lượng dịch vụ công trực tuyến toàn trình mà không xử lý dứt điểm "vùng lõm sóng" tại 4 huyện Lắk, Ea Kar, Krông A Na, Cư Kuin, thì hệ thống Cổng Dịch vụ công sẽ chỉ có cán bộ công chức tự nộp hồ sơ thay cho dân (ảo hóa số liệu), không đem lại giá trị thực chất cho người dân.
- **Khoảng cách bất bình đẳng kép (Kinh tế & Kỹ thuật số):** Hộ gia đình không có Internet sẽ bị tước đoạt cơ hội tiếp cận sàn thương mại điện tử nông sản, không xem được dự báo thời tiết hạn hán/sâu bệnh tức thời và chậm tiếp cận thông tin các chính sách trợ cấp mới của Đảng và Nhà nước.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Hành Động Can Thiệp)

- **Xóa dứt điểm "vùng lõm sóng" 4G và cáp quang nông thôn (Sở TT&TT chủ trì):**
  Sở Thông tin & Truyền thông chủ trì, làm việc trực tiếp với các doanh nghiệp viễn thông (Viettel, VNPT, MobiFone) cam kết lộ trình bổ sung các trạm thu phát sóng cơ động (BTS) mini và kéo cáp quang về 100% nhà văn hóa buôn làng tại huyện Lắk và Ea Kar trước Quý 3/2025.

- **Chính sách hỗ trợ Gói cước "Viễn thông công ích - Internet Hộ nghèo":**
  Ban Dân tộc tỉnh phối hợp Sở Tài chính trích nguồn Quỹ Dịch vụ Viễn thông Công ích và Tiểu dự án 2 - Dự án 10 (CTMTQG 1719) để hỗ trợ gói cước 4G/Internet ưu đãi (giảm 50%–70% cước phí) trong 24 tháng cho các hộ nghèo, hộ cận nghèo DTTS tại cụm 4 huyện vùng trũng.

- **Đổi mới mô hình Tổ Công nghệ số cộng đồng "Cầm tay chỉ việc":**
  Giao chỉ tiêu cụ thể cho Đoàn Thanh niên xã và Công an xã thành lập các đội lưu động đến tận nhà văn hóa buôn làng vào ngày nghỉ/buổi tối để trực tiếp hỗ trợ bà con: Kích hoạt VNeID mức 2, tích hợp thẻ BHYT số, và hướng dẫn nộp hồ sơ đăng ký khai sinh, đất đai trực tuyến bằng quy trình mẫu bằng hình ảnh trực quan.

---

##### 📋 Ma Trận Hành Động Can Thiệp Chuyên Đề 1

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Địa bàn ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Xóa vùng lõm sóng 4G / Cáp quang** | Sở TT&TT | Doanh nghiệp viễn thông | Huyện Lắk, Ea Kar | Q1–Q3/2025 | Quỹ Viễn thông công ích & Vốn DN |
| **Gói cước 4G trợ giá cho hộ nghèo** | Ban Dân tộc tỉnh | Sở Tài chính, Viettel, VNPT | 4 huyện vùng trũng (<80%) | Q2/2025 | Dự án 10 (CTMTQG 1719) |
| **Đội số hóa lưu động tại buôn làng** | Tỉnh đoàn Đắk Lắk | Công an tỉnh, UBND Huyện | Toàn bộ các xã khó khăn | Thường xuyên | Kinh phí chuyển đổi số tỉnh |

---

## 🛡️ CHUYÊN ĐỀ 2: BẢO TỒN & RỦI RO TỔN THƯƠNG CỦA CÁC DÂN TỘC THIỂU SỐ RẤT ÍT NGƯỜI (< 100 HỘ)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chiến lược:** Quyết định 1227/QĐ-TTg phê duyệt Đề án "Hỗ trợ phát triển kinh tế - xã hội các dân tộc thiểu số rất ít người giai đoạn 2016–2025" và Dự án 9 thuộc CTMTQG 1719 về đầu tư phát triển nhóm DTTS rất ít người và nhóm dân tộc còn nhiều khó khăn.
- **Mục tiêu nghiên cứu:** Nhận diện toàn diện các cộng đồng thiểu số có quy mô siêu nhỏ (< 100 hộ) đang cư trú đan xen tại Đắk Lắk; đánh giá mức độ tổn thương đa chiều về chất lượng nhà ở (`fact_nhao_dantoc`), bẫy nông nghiệp (`fact_laodong_dantoc`) và nguy cơ đứt gãy học vấn ở nữ giới (`fact_giaoduc_dantoc`).

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
WITH small_ethnic_groups AS (
    SELECT 
        d.ten_dantoc,
        d.nhom_nguon_goc,
        d.la_dtts_it_nguoi,
        h.tong_so_ho_co_nha,
        h.nha_kien_co_ban_kien_co,
        h.nha_thieu_kien_co_don_so,
        h.ty_le_nha_tam_don_so_pct,
        l.tong_lao_dong_co_viec_lam,
        l.ty_le_nong_nghiep_pct,
        g.ty_le_nu_biet_chu_pct
    FROM daklak_analytics.dim_dantoc d
    JOIN daklak_analytics.fact_nhao_dantoc h ON d.ma_dantoc = h.ma_dantoc
    JOIN daklak_analytics.fact_laodong_dantoc l ON d.ma_dantoc = l.ma_dantoc
    JOIN daklak_analytics.fact_giaoduc_dantoc g ON d.ma_dantoc = g.ma_dantoc
    WHERE h.tong_so_ho_co_nha > 0 AND h.tong_so_ho_co_nha < 100 -- Lọc các nhóm thiểu số rất ít hộ (<100 hộ)
),
ranked_vulnerability AS (
    SELECT 
        *,
        DENSE_RANK() OVER (ORDER BY ty_le_nha_tam_don_so_pct DESC, tong_so_ho_co_nha ASC) AS rank_nguy_co_nha_o
    FROM small_ethnic_groups
)
SELECT 
    rank_nguy_co_nha_o,
    ten_dantoc,
    nhom_nguon_goc,
    tong_so_ho_co_nha,
    nha_thieu_kien_co_don_so,
    ty_le_nha_tam_don_so_pct,
    tong_lao_dong_co_viec_lam,
    ty_le_nong_nghiep_pct,
    ty_le_nu_biet_chu_pct
FROM ranked_vulnerability
ORDER BY rank_nguy_co_nha_o ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (15 Nhóm Dân Tộc Siêu Nhỏ Tại Đắk Lắk)

| Hạng Nguy Cơ | Tên Dân Tộc | Phân Nhóm Nguồn Gốc | Tổng Số Hộ Có Nhà | Số Hộ Nhà Đơn Sơ/Tạm | Tỷ Lệ Nhà Tạm (%) | Lao Động Có Việc Làm | Tỷ Lệ Nông Nghiệp (%) | Nữ Biết Chữ (%) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Chơ Ro** | Khác | **4 hộ** | **4 hộ** | **100.00%** | 4 người | 100.00% | **0.00%** |
| **2** | **Chăm** | Nam Bộ & Duyên hải | 16 hộ | 1 hộ | **6.25%** | 52 người | 78.85% | 46.15% |
| **3** | **Chứt** | Khác (Diện rất ít người) | 69 hộ | 4 hộ | **5.80%** | 77 người | 83.12% | 41.82% |
| **4** | **Khmer** | Nam Bộ & Duyên hải | 39 hộ | 1 hộ | **2.56%** | 318 người | 56.60% | 37.97% |
| **5** | **Mảng** | Khác (Diện rất ít người) | 1 hộ | 0 hộ | 0.00% | 2 người | 100.00% | **0.00%** |
| **6** | **Raglay** | Khác | 1 hộ | 0 hộ | 0.00% | 6 người | 100.00% | **0.00%** |
| **7** | **Cơ Tu** | Khác | 1 hộ | 0 hộ | 0.00% | 5 người | 80.00% | 50.00% |
| **8** | **Ngái** | Khác (Diện rất ít người) | 3 hộ | 0 hộ | 0.00% | 8 người | 87.50% | 50.00% |
| **9** | **Phù Lá** | Di cư miền núi phía Bắc | 3 hộ | 0 hộ | 0.00% | 3 người | 100.00% | **0.00%** |
| **10** | **Chu Ru** | Bản địa Tây Nguyên | 4 hộ | 0 hộ | 0.00% | 5 người | 100.00% | **0.00%** |
| **11** | **Co** | Khác | 21 hộ | 0 hộ | 0.00% | 31 người | 58.06% | 33.33% |
| **12** | **Sán Dìu** | Di cư miền núi phía Bắc | 22 hộ | 0 hộ | 0.00% | 2 người | 0.00% | 50.00% |
| **13** | **Mạ** | Bản địa Tây Nguyên | 34 hộ | 0 hộ | 0.00% | 38 người | 100.00% | **0.00%** |
| **14** | **Cơ Ho** | Bản địa Tây Nguyên | 73 hộ | 0 hộ | 0.00% | 99 người | 80.81% | 45.51% |
| **15** | **Lào** | Di cư miền núi phía Bắc | 91 hộ | 0 hộ | 0.00% | 143 người | 83.22% | 40.13% |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Tình trạng báo động đỏ ở người Chơ Ro:** Toàn tỉnh Đắk Lắk chỉ có duy nhất **4 hộ người Chơ Ro** (4 lao động), nhưng **100% số hộ (4/4 hộ) đang phải sống trong nhà tạm bợ, đơn sơ dột nát**. Tỷ lệ lao động làm nông nghiệp thô là 100% và tỷ lệ phụ nữ biết chữ bằng đúng **0.00%**.
- **Quy mô dân số siêu nhỏ (Micro-ethnic pockets):** Có tới **10 dân tộc có quy mô dưới 10 hộ** sinh sống rải rác trên địa bàn tỉnh (*Mảng: 1 hộ, Raglay: 1 hộ, Cơ Tu: 1 hộ, Ngái: 3 hộ, Phù Lá: 3 hộ, Chu Ru: 4 hộ...*).
- **Vùng trũng mù chữ ở nữ giới các nhóm siêu nhỏ:** Ở hàng loạt dân tộc thiểu số nhỏ như **Chơ Ro, Mảng, Raglay, Phù Lá, Chu Ru, Mạ**, tỷ lệ phụ nữ biết chữ hoàn toàn bằng **0.00%** (100% phụ nữ trong độ tuổi khảo sát không biết đọc, biết viết tiếng phổ thông).

#### 2. ANALYSIS (Phân Tích Căn Nguyên "Hiệu Ứng Bị Lãng Quên & Mai Một Bản Sắc")
- **Nguy cơ bị lãng quên trong phân bổ chính sách (Policy Blind Spot):** Do số lượng hộ quá ít (chỉ 1–4 hộ mỗi buôn làng), các cộng đồng này thường không đủ điều kiện để thành lập tổ nhóm sinh hoạt cộng đồng riêng, dễ bị "vô hình hóa" trong các cuộc họp bình xét hộ nghèo của xã và trượt khỏi các dự án hỗ trợ hạ tầng tập trung.
- **Bẫy nông nghiệp khép kín & đứt gãy học vấn:** Sống phân tán xen kẽ với các dân tộc lớn hơn, người Chơ Ro, Chu Ru, Mạ phụ thuộc hoàn toàn vào công việc làm thuê làm mướn nương rẫy (100% lao động nông nghiệp). Thu nhập bấp bênh khiến con cái họ sớm bỏ học để phụ giúp gia đình, dẫn đến tình trạng mù chữ truyền đời ở nữ giới.
- **Nguy cơ mai một tiếng nói và văn hóa bản địa:** Các dân tộc rất ít người theo danh mục của Chính phủ (như người Chứt có 69 hộ, người Mảng 1 hộ, người Ngái 3 hộ) khi cư trú tại Đắk Lắk hầu như không còn không gian diễn xướng văn hóa truyền thống, có nguy cơ đồng hóa hoàn toàn về ngôn ngữ và phong tục.

#### 3. IMPACT (Tác Động Thể Chế & Nhân Đạo)
- **Rủi ro không hoàn thành mục tiêu "Không để ai bị bỏ lại phía sau":** Mặc dù số lượng tuyệt đối chỉ vài chục hộ, nhưng tình trạng 100% nhà tạm dột nát ở người Chơ Ro hay 0% nữ biết chữ ở người Mảng, Raglay là những chỉ số "báo động đỏ" trong các đợt giám sát của Ủy ban Dân tộc và các tổ chức nhân quyền quốc tế.
- **Nguy cơ nghèo cùng cực thế hệ sau:** Khi người mẹ hoàn toàn mù chữ (0%) và sống trong nhà dột nát, thế hệ con em của các hộ gia đình này sẽ không có bất kỳ điểm tựa nào để tiếp cận bậc học phổ thông, tiếp tục kéo dài vòng luẩn quẩn đói nghèo.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Can Thiệp Đặc Thù)

- **Cứu trợ nhà ở khẩn cấp cho 100% hộ Chơ Ro và Chứt (Ban Dân tộc tỉnh & Sở Xây dựng):**
  Lập tức xuất nguồn vốn Dự án 1 (CTMTQG 1719) và Quỹ "Vì người nghèo" tỉnh để hỗ trợ kinh phí xây dựng nhà kiên cố "3 cứng" (mái cứng, khung-tường cứng, nền cứng) cho **4 hộ người Chơ Ro** và **4 hộ người Chứt** còn ở nhà tạm trong Quý 2/2025.

- **Chính sách học bổng và bảo trợ giáo dục 100% cho trẻ em DTTS rất ít người:**
  Sở GD&ĐT chỉ đạo các trường dân tộc nội trú huyện/tỉnh ưu tiên tuyển thẳng và đài thọ 100% chi phí ăn ở, sách vở cho tất cả con em thuộc các dân tộc Chơ Ro, Chứt, Mảng, Ngái, Chu Ru, Co, Mạ; không để bất kỳ em nào phải bỏ học vì hoàn cảnh kinh tế.

- **Hỗ trợ sinh kế đặc thù & Cán bộ khuyến nông phụ trách trực tiếp:**
  UBND các huyện có đồng bào sinh sống cử riêng cán bộ khuyến nông buôn làng hướng dẫn kỹ thuật chăn nuôi gia súc (bò sinh sản) và giao khoán bảo vệ rừng có chi trả dịch vụ môi trường rừng để tạo nguồn thu nhập bằng tiền mặt ổn định hàng tháng.

---

##### 📋 Ma Trận Hành Động Can Thiệp Chuyên Đề 2

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Xóa 100% nhà tạm dột nát** | Ban Dân tộc tỉnh | Sở Xây dựng, UBND Huyện | 4 hộ Chơ Ro, 4 hộ Chứt | Q2/2025 | Dự án 1 (CTMTQG 1719) |
| **Tuyển thẳng & Học bổng nội trú** | Sở GD&ĐT | Trường Dân tộc nội trú | 100% con em DTTS < 100 hộ | Năm học 2025 | Ngân sách giáo dục tỉnh |
| **Cán bộ khuyến nông đỡ đầu sinh kế** | UBND Huyện sở tại | Phòng Nông nghiệp | Hộ Chơ Ro, Mảng, Chu Ru | Thường xuyên | Quỹ sinh kế cộng đồng |

---

### 👶 CHUYÊN ĐỀ 3: ÁP LỰC DÂN SỐ, MỨC SINH CAO & NGUY CƠ TỬ VONG MẸ - BÉ TRONG SINH NỞ

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Y Tế Dân Số
- **Căn cứ chiến lược:** Chiến lược Dân số Việt Nam đến năm 2030 (Quyết định 1679/QĐ-TTg) và Dự án 7 thuộc CTMTQG 1719 về Chăm sóc sức khỏe nhân dân, nâng cao thể trạng, tầm vóc người DTTS; phòng chống suy dinh dưỡng trẻ em.
- **Mục tiêu phân tích:** Bóc tách dữ liệu từ bảng sự kiện `daklak_analytics.fact_mucsinh_dantoc` trên PostgreSQL để trả lời 2 câu hỏi sinh tử:
  1. Tình trạng **sinh con thứ 3 trở lên** tập trung ở những nhóm dân tộc nào, tạo áp lực gì lên quy mô dân số và bẫy đói nghèo?
  2. Nguy cơ y tế khẩn cấp: **Những dân tộc nào còn tập quán sinh con tại nhà không có nhân viên y tế / bà đỡ hỗ trợ**, đe dọa trực tiếp đến tính mạng sản phụ và trẻ sơ sinh?

---

### 2. Kịch Bản Truy Vấn SQL Phân Tích (PostgreSQL Analytics Query)
*Kỹ thuật SQL áp dụng:* CTE tính Benchmark toàn tỉnh (tránh bẫy Order of Execution khi kết hợp `WHERE` với Window Functions), ép kiểu an toàn `CAST(... AS NUMERIC)`, hàm chặn lỗi `NULLIF(..., 0)` và xếp hạng rủi ro sản khoa bằng `DENSE_RANK()`.

```sql
WITH full_provincial_benchmark AS (
    SELECT 
        ma_dantoc,
        ten_dantoc,
        nhom_nguon_goc,
        sinh_tai_nha_tong,
        sinh_tai_nha_khong_ba_do,
        sinh_con_thu_3_tro_len,
        -- Tính tổng toàn tỉnh trước khi lọc (tránh bẫy Order of Execution)
        SUM(sinh_tai_nha_tong) OVER () AS tong_tinh_sinh_nha,
        SUM(sinh_con_thu_3_tro_len) OVER () AS tong_tinh_sinh_con_3
    FROM daklak_analytics.fact_mucsinh_dantoc
),
ranked_maternal_risk AS (
    SELECT 
        ma_dantoc,
        ten_dantoc,
        nhom_nguon_goc,
        sinh_tai_nha_tong,
        sinh_tai_nha_khong_ba_do,
        sinh_con_thu_3_tro_len,
        
        -- 1. Tỷ lệ % ca sinh không có bà đỡ trên tổng ca sinh tại nhà của từng dân tộc
        ROUND(
            CAST(sinh_tai_nha_khong_ba_do AS NUMERIC) / NULLIF(sinh_tai_nha_tong, 0) * 100, 
            2
        ) AS ty_le_khong_ba_do_pct,
        
        -- 2. Tỷ trọng % ca sinh tại nhà của dân tộc đó so với tổng số ca sinh tại nhà toàn tỉnh (1.023 ca)
        ROUND(
            CAST(sinh_tai_nha_tong AS NUMERIC) / NULLIF(tong_tinh_sinh_nha, 0) * 100, 
            2
        ) AS ty_trong_sinh_tai_nha_toan_tinh_pct,
        
        -- 3. Tỷ trọng % phụ nữ sinh con thứ 3+ so với tổng toàn tỉnh (46.044 người)
        ROUND(
            CAST(sinh_con_thu_3_tro_len AS NUMERIC) / NULLIF(tong_tinh_sinh_con_3, 0) * 100, 
            2
        ) AS ty_trong_sinh_con_3_toan_tinh_pct,
        
        -- 4. Xếp hạng rủi ro tử vong sản khoa dựa trên số ca sinh không có người đỡ (cao nhất xếp hạng 1)
        DENSE_RANK() OVER (ORDER BY sinh_tai_nha_khong_ba_do DESC) AS xep_hang_rui_ro
    FROM full_provincial_benchmark
    WHERE sinh_tai_nha_tong > 0
)
SELECT 
    xep_hang_rui_ro,
    ten_dantoc,
    nhom_nguon_goc,
    sinh_tai_nha_tong,
    sinh_tai_nha_khong_ba_do,
    ty_le_khong_ba_do_pct,
    ty_trong_sinh_tai_nha_toan_tinh_pct,
    sinh_con_thu_3_tro_len,
    ty_trong_sinh_con_3_toan_tinh_pct
FROM ranked_maternal_risk
ORDER BY xep_hang_rui_ro ASC, sinh_tai_nha_tong DESC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Trích Xuất Trực Tiếp Từ PostgreSQL)

| Hạng Rủi Ro | Dân Tộc | Phân Nhóm Nguồn Gốc | Ca Sinh Tại Nhà (Tổng) | Tự Sinh KHÔNG Người Đỡ | Tỷ Lệ Không Người Đỡ (%) | Tỷ Trọng Sinh Tại Nhà / Tỉnh (%) | Phụ Nữ Sinh Con Thứ 3+ | Tỷ Trọng Sinh Con 3+ / Tỉnh (%) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Mông** | Di cư miền núi phía Bắc | **367** | **131** | **35.69%** | **35.87%** | 6.544 | **14.21%** |
| **2** | **Xơ Đăng** | Bản địa Tây Nguyên | **278** | **36** | **12.95%** | **27.17%** | 876 | **1.90%** |
| **3** | **Ê đê** | Bản địa Tây Nguyên | **171** | **22** | **12.87%** | **16.72%** | **24.664** | **53.58%** |
| **4** | **Mnông** | Bản địa Tây Nguyên | **171** | **14** | **8.19%** | **16.72%** | **4.154** | **9.02%** |
| **5** | Mường | Di cư miền núi phía Bắc | 14 | 0 | 0.00% | 1.37% | 843 | 1.83% |
| **5** | Sán Chay | Di cư miền núi phía Bắc | 8 | 0 | 0.00% | 0.78% | 314 | 0.68% |
| **5** | Nùng | Di cư miền núi phía Bắc | 7 | 0 | 0.00% | 0.68% | 2.658 | 5.77% |
| **5** | Dao | Di cư miền núi phía Bắc | 6 | 0 | 0.00% | 0.59% | 858 | 1.86% |
| **5** | Chứt | Khác (Rất ít người) | 1 | 0 | 0.00% | 0.10% | 0 | 0.00% |

*Quy mô toàn tỉnh Đắk Lắk:*
- **Tổng số phụ nữ sinh con thứ 3 trở lên:** **46.044 người** (khu vực nông thôn chiếm 42.951 người - **93.28%**).
- **Tổng số phụ nữ sinh con tại nhà:** **1.023 trường hợp**, trong đó có **203 ca hoàn toàn không có người đỡ** (nhân viên y tế hoặc cô đỡ thôn bản).

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Điểm nóng tập trung rủi ro sản khoa (Cụm 4 Dân tộc):** Toàn tỉnh Đắk Lắk có 1.023 ca sinh con tại nhà, nhưng **96.48% (987 ca)** tập trung ở đúng 4 dân tộc: **Mông (367 ca), Xơ Đăng (278 ca), Ê đê (171 ca), Mnông (171 ca)**.
- **Báo động đỏ người Mông (Hạng 1 rủi ro tử vong):** Cứ 3 ca phụ nữ Mông sinh tại nhà thì có hơn 1 ca **hoàn toàn tự sinh không có người đỡ (35.69% - 131 ca)**. Người Mông một mình chiếm tới **64.53% tổng số ca sinh không người đỡ của toàn tỉnh** (131 / 203 ca).
- **Áp lực mức sinh cao gắn chặt với bẫy nghèo nông thôn:** Toàn tỉnh có tới **46.044 phụ nữ DTTS sinh con thứ 3 trở lên**, trong đó **93.28% sinh sống tại vùng nông thôn, nương rẫy**. Người Ê Đê chiếm áp đảo với **24.664 người (53.58%)**, tiếp theo là người Mông với **6.544 người (14.21%)**.

#### 2. ANALYSIS (Phân Tích Căn Nguyên: "Rào Cản Tập Quán vs Khoảng Cách Nương Rẫy")
- **Rào cản văn hóa & tâm lý khép kín của người Mông:** Phong tục truyền thống của người Mông coi sinh nở là việc riêng tư gia đình trong buồng kín. Phụ nữ Mông có tâm lý e ngại cơ sở y tế có y bác sĩ nam thăm khám; cộng thêm rào cản bất đồng ngôn ngữ khiến họ từ chối ra trạm y tế dù trạm xã đã đạt chuẩn quốc gia.
- **Hệ quả của tập quán canh tác nương rẫy xa xôi (Người Xơ Đăng, Ê Đê, Mnông):** Vào mùa gieo cấy và thu hoạch, đồng bào thường ở lại chòi rẫy cách buôn làng 10–15km trên địa hình núi dốc. Khi chuyển dạ đột ngột vào ban đêm hoặc mùa mưa, đường sạt lở trơn trượt khiến sản phụ không thể di chuyển kịp thời đến trạm y tế, buộc phải tự sinh hoặc nhờ người nhà đỡ đẻ thô sơ.
- **Tương quan nhân quả giữa Mù chữ (Trụ cột 2) và Thiếu kiểm soát mức sinh:** Nhóm dân tộc có tỷ lệ phụ nữ mù chữ cao (Mông 51.52%, Dao, Xơ Đăng) cũng chính là nhóm có tỷ lệ sinh dày và sinh con thứ 3+ cao nhất. Việc thiếu hiểu biết về sức khỏe sinh sản và rào cản tiếp cận biện pháp tránh thai hiện đại khiến phụ nữ rơi vào vòng luẩn quẩn: *Sinh nhiều con ➔ Kiệt quệ sức khỏe ➔ Không thể tham gia lao động kỹ thuật ➔ Nghèo đa chiều truyền đời*.

#### 3. IMPACT (Tác Động Đến Tính Mạng & Thể Chất Dân Tộc)
- **Nguy cơ trực tiếp về Tai biến sản khoa & Tử vong mẹ - sơ sinh:** Tự sinh tại nhà không vô trùng là nguyên nhân hàng đầu dẫn đến uốn ván rốn sơ sinh, vỡ tử cung, băng huyết sau sinh và nhiễm trùng hậu sản – những tai biến cướp đi sinh mạng của sản phụ và trẻ em chỉ trong vài giờ nếu không có can thiệp y khoa.
- **Suy giảm chất lượng giống nòi và quá tải dịch vụ xã hội:** Với 46.044 phụ nữ sinh con thứ 3+ ở vùng nông thôn nghèo, trẻ em sinh ra đối mặt với nguy cơ suy dinh dưỡng thể thấp còi (stunting) cao, gây áp lực nặng nề lên hệ thống trường học và trạm y tế xã vốn đã thiếu thốn trang thiết bị.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Y Tế Dân Số Thực Chiến)

- **Mở rộng và đãi ngộ mạng lưới "Cô đỡ thôn bản người Mông và Xơ Đăng" (Sở Y tế chủ trì):**
  Thực tế chứng minh không thể thay đổi ngay tập quán sinh tại nhà của người Mông bằng biện pháp hành chính; giải pháp sống còn là đào tạo cấp tốc kỹ năng đỡ đẻ an toàn cho chính các phụ nữ có uy tín trong buôn làng người Mông, Xơ Đăng. Cung cấp miễn phí 100% "Gói đỡ đẻ sạch" (dao cắt rốn vô trùng, chỉ buộc, găng tay) và duy trì phụ cấp hàng tháng cho cô đỡ thôn bản từ nguồn Dự án 7 (CTMTQG 1719).

- **Chiến dịch Kế hoạch hóa gia đình lưu động "Đưa dịch vụ về tận chòi rẫy":**
  Chi cục Dân số - KHHGĐ phối hợp với TTYT huyện Ea Súp, Krông Bông, Cư M'gar đưa đội lưu động cung cấp biện pháp tránh thai dài hạn (que cấy tránh thai dưới da, tiêm thuốc tránh thai) miễn phí trực tiếp tại các buôn làng người Mông và Ê Đê.

- **Chính sách hỗ trợ tài chính trực tiếp cho sản phụ DTTS sinh con tại Trạm Y tế:**
  UBND tỉnh ban hành gói chính sách hỗ trợ tiền mặt 1,5 – 2,0 triệu đồng/ca sinh cho sản phụ DTTS thuộc hộ nghèo/cận nghèo khi đến sinh con tại trạm y tế xã hoặc bệnh viện huyện (nhằm bù đắp chi phí thuê phương tiện di chuyển và tiền ăn cho gia đình đi cùng).

---

### 5. Ma Trận Hành Động Can Thiệp Chuyên Đề 3

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Đào tạo & Trang bị Cô đỡ thôn bản** | Sở Y tế tỉnh Đắk Lắk | Hội Phụ nữ, CDC tỉnh | Buôn làng Mông, Xơ Đăng (Ea Súp, Krông Bông) | Q2/2025 | Dự án 7 (CTMTQG 1719) |
| **Gói dịch vụ KHHGĐ lưu động tại buôn** | Chi cục Dân số - KHHGĐ | TTYT các huyện vùng sâu | Phụ nữ Ê đê, Mông sinh con 3+ | Định kỳ 6 tháng | Ngân sách sự nghiệp y tế |
| **Hỗ trợ tiền mặt sản phụ sinh tại cơ sở y tế** | Ban Dân tộc tỉnh | Sở Tài chính, UBND Huyện | 100% sản phụ DTTS nghèo | 2025–2026 | Quỹ hỗ trợ phụ nữ DTTS sinh con |

---

## 👥 CHUYÊN ĐỀ 4: CƠ CẤU DÂN SỐ, THÁP TUỔI & GÁNH NẶNG TỶ LỆ PHỤ THUỘC (DEMOGRAPHIC DEPENDENCY BURDEN)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Nhân Khẩu Học
- **Căn cứ chiến lược:** Nghị quyết số 21-NQ/TW của Ban Chấp hành Trung ương Đảng về công tác dân số trong tình hình mới; Chiến lược Dân số Việt Nam đến năm 2030.
- **Bản chất kinh tế:** Lực lượng trong độ tuổi lao động (15–59 tuổi) là người trụ cột gánh vác toàn bộ kinh tế gia đình. Khi tỷ lệ phụ thuộc (trẻ em dưới 15 tuổi và người già trên 60 tuổi) quá cao, thu nhập của người trụ cột bị phân tán cho quá nhiều người ăn theo. Dù làm việc cật lực quanh năm trên nương rẫy, hộ gia đình vẫn không thể tích lũy tư bản và rơi vào **bẫy nghèo đói truyền đời**.
- **Chỉ số đo lường:**
  1. *Tỷ lệ phụ thuộc trẻ em (CDR):* $\text{Dân số 0–14} / \text{Dân số 15–59} \times 100$
  2. *Tỷ lệ phụ thuộc người già (ODR):* $\text{Dân số 60+} / \text{Dân số 15–59} \times 100$
  3. *Tỷ lệ phụ thuộc chung (TDR):* $(\text{Dân số 0–14} + \text{Dân số 60+}) / \text{Dân số 15–59} \times 100$
  4. *Chỉ số già hóa (Aging Index):* $\text{Dân số 60+} / \text{Dân số 0–14} \times 100$

---

### 2. Kịch Bản Truy Vấn SQL Phân Tích (PostgreSQL Analytics Query)
*Kỹ thuật SQL áp dụng:* CTEs lồng nhau, kỹ thuật phòng thủ `NULLIF` và `CAST AS NUMERIC`, phân loại ma trận nhân khẩu bằng `CASE WHEN` và xếp hạng áp lực gánh nặng bằng `DENSE_RANK()`.

```sql
WITH demographic_indicators AS (
    SELECT 
        ma_dantoc,
        ten_dantoc,
        nhom_nguon_goc,
        tong_dan_so,
        dan_so_0_14,
        dan_so_15_59,
        dan_so_60_plus,
        
        -- 1. Tỷ lệ phụ thuộc trẻ em: 100 người lao động phải nuôi bao nhiêu trẻ em
        ROUND(
            CAST(dan_so_0_14 AS NUMERIC) / NULLIF(dan_so_15_59, 0) * 100, 
            2
        ) AS ty_le_phu_thuoc_tre_em_pct,
        
        -- 2. Tỷ lệ phụ thuộc người cao tuổi: 100 người lao động phải phụng dưỡng bao nhiêu người già
        ROUND(
            CAST(dan_so_60_plus AS NUMERIC) / NULLIF(dan_so_15_59, 0) * 100, 
            2
        ) AS ty_le_phu_thuoc_gia_pct,
        
        -- 3. Tỷ lệ phụ thuộc chung (Total Dependency Ratio - TDR)
        ROUND(
            CAST(dan_so_0_14 + dan_so_60_plus AS NUMERIC) / NULLIF(dan_so_15_59, 0) * 100, 
            2
        ) AS ty_le_phu_thuoc_chung_pct,
        
        -- 4. Chỉ số già hóa (Aging Index): Tỷ lệ người già so với 100 trẻ em
        ROUND(
            CAST(dan_so_60_plus AS NUMERIC) / NULLIF(dan_so_0_14, 0) * 100, 
            2
        ) AS chi_so_gia_hoa_pct
    FROM daklak_analytics.fact_nhankhau_dantoc
    WHERE tong_dan_so >= 500 -- Lọc quy mô dân số có ý nghĩa thống kê
),
classified_demographics AS (
    SELECT 
        *,
        -- 5. Phân loại cấu trúc nhân khẩu học
        CASE 
            WHEN chi_so_gia_hoa_pct >= 30.0 THEN 'Bắt đầu già hóa (Aging Phase)'
            WHEN ty_le_phu_thuoc_tre_em_pct >= 60.0 THEN 'Dân số siêu trẻ - Gánh nặng con nhỏ cực cao'
            ELSE 'Cơ cấu dân số vàng (Demographic Dividend)'
        END AS phan_loai_nhan_khau,
        
        -- 6. Xếp hạng áp lực gánh nặng phụ thuộc chung
        DENSE_RANK() OVER (ORDER BY ty_le_phu_thuoc_chung_pct DESC) AS rank_ganh_nang_phu_thuoc
    FROM demographic_indicators
)
SELECT 
    rank_ganh_nang_phu_thuoc,
    ten_dantoc,
    nhom_nguon_goc,
    tong_dan_so,
    dan_so_0_14,
    dan_so_15_59,
    dan_so_60_plus,
    ty_le_phu_thuoc_tre_em_pct,
    ty_le_phu_thuoc_gia_pct,
    ty_le_phu_thuoc_chung_pct,
    chi_so_gia_hoa_pct,
    phan_loai_nhan_khau
FROM classified_demographics
ORDER BY rank_ganh_nang_phu_thuoc ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (15 Nhóm Dân Tộc Có Quy Mô $\ge 500$ Người)

| Hạng Áp Lực | Dân Tộc | Phân Nhóm Nguồn Gốc | Tổng Dân Số | Trẻ Em (0–14) | Lao Động (15–59) | Người Già (60+) | Phụ Thuộc Trẻ Em (%) | Phụ Thuộc Người Già (%) | Phụ Thuộc Chung (%) | Chỉ Số Già Hóa (%) | Phân Loại Cấu Trúc Nhân Khẩu |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | **Xơ Đăng** | Bản địa Tây Nguyên | 9.083 | 3.857 | 4.871 | 354 | **79.18%** | 7.27% | **86.45%** | 9.18% | Dân số siêu trẻ - Gánh nặng con nhỏ cực cao |
| **2** | **Mông** | Di cư miền núi phía Bắc | 55.529 | 22.758 | 30.297 | 2.476 | **75.12%** | 8.17% | **83.29%** | 10.88% | Dân số siêu trẻ - Gánh nặng con nhỏ cực cao |
| **3** | **Mnông** | Bản địa Tây Nguyên | 48.051 | 16.383 | 27.911 | 3.756 | **58.70%** | 13.46% | **72.15%** | 22.93% | Cơ cấu dân số vàng |
| **4** | **Mường** | Di cư miền núi phía Bắc | 19.280 | 5.615 | 11.553 | 2.113 | 48.60% | 18.29% | **66.89%** | **37.63%** | Bắt đầu già hóa (Aging Phase) |
| **5** | **Bru Vân Kiều** | Khác | 6.403 | 1.962 | 3.950 | 492 | 49.67% | 12.46% | **62.13%** | 25.08% | Cơ cấu dân số vàng |
| **6** | **Gia Rai** | Bản địa Tây Nguyên | 19.462 | 6.374 | 12.010 | 1.080 | 53.07% | 8.99% | **62.06%** | 16.94% | Cơ cấu dân số vàng |
| **7** | **Ê đê** | Bản địa Tây Nguyên | **396.827** | 122.109 | 246.207 | 28.509 | 49.60% | 11.58% | **61.18%** | 23.35% | Cơ cấu dân số vàng chuẩn mực |
| **8** | **Sán Chay** | Di cư miền núi phía Bắc | 3.233 | 933 | 2.069 | 230 | 45.09% | 11.12% | **56.21%** | 24.65% | Cơ cấu dân số vàng |
| **9** | **Thái** | Di cư miền núi phía Bắc | 20.609 | 5.209 | 13.301 | 2.101 | 39.16% | 15.80% | **54.96%** | **40.33%** | Bắt đầu già hóa (Aging Phase) |
| **10** | **Tày** | Di cư miền núi phía Bắc | 47.924 | 12.007 | 31.001 | 4.916 | 38.73% | 15.86% | **54.59%** | **40.94%** | Bắt đầu già hóa (Aging Phase) |
| **11** | **Nùng** | Di cư miền núi phía Bắc | 56.645 | 14.426 | 37.445 | 4.773 | 38.53% | 12.75% | **51.27%** | **33.09%** | Bắt đầu già hóa (Aging Phase) |
| **12** | **Ba Na** | Bản địa Tây Nguyên | 614 | 175 | 421 | 17 | 41.57% | 4.04% | **45.61%** | 9.71% | Cơ cấu dân số vàng |
| **13** | **Dao** | Di cư miền núi phía Bắc | 15.254 | 3.867 | 10.698 | 687 | 36.15% | 6.42% | **42.57%** | 17.77% | Cơ cấu dân số vàng |
| **14** | **Hoa** | Nam Bộ & Duyên hải | 1.717 | 342 | 1.246 | 131 | 27.45% | 10.51% | **37.96%** | **38.30%** | Bắt đầu già hóa (Aging Phase) |
| **15** | **Hrê** | Khác | 604 | 46 | 543 | 15 | 8.47% | 2.76% | **11.23%** | **32.61%** | Bắt đầu già hóa (Aging Phase) |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Gánh nặng nuôi con nhỏ cực đại ở người Xơ Đăng và Mông:**
  - Người Xơ Đăng có tỷ lệ phụ thuộc chung lên tới **86.45%**, trong đó riêng phụ thuộc trẻ em đạt **79.18%** (Cứ 100 người lớn độ tuổi lao động phải nuôi gần 80 trẻ em!).
  - Người Mông có tỷ lệ phụ thuộc chung là **83.29%** (phụ thuộc trẻ em **75.12%**). Trong 55.529 người Mông, có tới **22.758 trẻ em dưới 15 tuổi (chiếm 40.98% tổng dân số)**.
  - Chỉ số già hóa của người Xơ Đăng (9.18%) và Mông (10.88%) ở mức thấp kỷ lục, cho thấy tháp tuổi có đáy phình to dữ dội.
- **Sự chuyển dịch sang xu hướng già hóa ở nhóm DTTS phía Bắc:**
  - Các dân tộc định cư lâu năm như **Tày (40.94%), Thái (40.33%), Hoa (38.30%), Mường (37.63%), Nùng (33.09%)** đều có chỉ số già hóa vượt ngưỡng 30% – chính thức bước vào giai đoạn bắt đầu già hóa dân số.
- **Dân số vàng của người Ê Đê:** Dân tộc lớn nhất tỉnh (396.827 người) có cơ cấu dân số vàng rất lý tưởng với **246.207 người trong độ tuổi lao động (chiếm 62.04%)**, tỷ lệ phụ thuộc chung ở mức hợp lý (61.18%).

#### 2. ANALYSIS (Phân Tích Căn Nguyên "Bẫy Thu Nhập & Phân Hóa Nhân Khẩu Hai Cực")
- **Bẫy kiệt quệ tài chính của người trụ cột ở dân số siêu trẻ (Mông, Xơ Đăng):** Khi một cặp vợ chồng lao động phải nuôi 4–5 người con trong điều kiện sinh kế phụ thuộc 98.3% vào nông nghiệp nương rẫy, toàn bộ thu nhập làm ra chỉ đủ đắp đổi lương thực hàng ngày. Tỷ lệ tiết kiệm và tích lũy tư bản bằng $0$. Hệ quả là gia đình không có tiền mua máy móc nông nghiệp, không thể sửa nhà kiên cố và con cái buộc phải nghỉ học sớm để phụ giúp nương rẫy.
- **Hai bài toán chính sách đối nghịch cùng tồn tại trên một địa bàn tỉnh:**
  - *Bài toán 1 (Áp lực mở rộng trường học & Y tế trẻ em):* Tập trung ở huyện Ea Súp, Krông Bông nơi đồng bào Mông, Xơ Đăng sinh sống, cần vốn lớn cho trường mầm non, tiểu học và phòng chống suy dinh dưỡng trẻ em.
  - *Bài toán 2 (An sinh xã hội & Y tế người cao tuổi):* Tập trung ở huyện Ea Kar, Krông Năng nơi đồng bào Tày, Nùng sinh sống, bắt đầu đối mặt với gánh nặng chi phí khám chữa bệnh mãn tính của người già nông thôn không có lương hưu.

#### 3. IMPACT (Tác Động Đến Chiến Lược Giảm Nghèo & Nguồn Nhân Lực)
- **Nguy cơ đứt gãy học vấn thế hệ trẻ:** Gánh nặng trẻ em quá lớn là nguyên nhân số 1 khiến trẻ em Mông, Xơ Đăng bỏ học sau bậc tiểu học, tái diễn tình trạng mù chữ và thiếu kỹ năng nghề như đã chứng minh ở Trụ cột 2.
- **Nguy cơ "Chưa giàu đã già":** Nếu nhóm Tày, Thái, Nùng bước vào giai đoạn già hóa sâu sắc mà chưa tích lũy đủ tài sản và chưa có bảo hiểm xã hội tự nguyện, họ sẽ trở thành gánh nặng an sinh xã hội nặng nề cho ngân sách tỉnh sau năm 2030.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Nhân Khẩu Học Thực Chiến)

- **Chính sách hỗ trợ dinh dưỡng và miễn giảm chi phí học tập toàn diện cho trẻ em Mông, Xơ Đăng (Sở GD&ĐT & Ban Dân tộc):**
  Thực hiện đài thọ 100% bữa ăn bán trú và bảo hiểm y tế cho học sinh mầm non và tiểu học người Mông, Xơ Đăng; nhằm trực tiếp giải phóng gánh nặng chi phí cho người trụ cột gia đình, ngăn chặn tình trạng trẻ em phải bỏ học đi làm rẫy.

- **Đào tạo nghề chuyển dịch cơ cấu việc làm cho nhóm "Dân số vàng" (Sở LĐ-TB&XH):**
  Tập trung nguồn vốn Dự án 5 (CTMTQG 1719) mở các lớp đào tạo nghề cơ khí nông nghiệp, sơ chế cà phê, du lịch cộng đồng cho lực lượng 246.207 lao động người Ê Đê để tận dụng tối đa "cửa sổ dân số vàng" trước khi dân tộc này bước sang chu kỳ già hóa.

- **Thí điểm mô hình Chăm sóc Sức khỏe Người cao tuổi dựa vào cộng đồng cho đồng bào Tày, Nùng (Sở Y tế):**
  Thành lập các Câu lạc bộ "Người cao tuổi giúp nhau" và trạm y tế lưu động quản lý bệnh mãn tính (huyết áp, tim mạch, xương khớp) cho người già DTTS tại các xã vùng sâu huyện Ea Kar, Krông Năng.

---

### 5. Ma Trận Hành Động Can Thiệp Chuyên Đề 4

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Bán trú & BHYT học sinh nghèo** | Sở GD&ĐT | Ban Dân tộc, UBND Huyện | Trẻ em Mông, Xơ Đăng (0–14 tuổi) | Năm học 2025–2026 | CTMTQG 1719 & Ngân sách tỉnh |
| **Đào tạo nghề đón đầu Dân số vàng** | Sở LĐ-TB&XH | Tỉnh Đoàn, Trung tâm GDNN | Lao động Ê đê, Mnông (15–35 tuổi) | 2025–2027 | Dự án 5 (CTMTQG 1719) |
| **Quản lý bệnh mãn tính người già DTTS** | Sở Y tế tỉnh Đắk Lắk | Hội Người cao tuổi, TTYT Huyện | Người cao tuổi Tày, Thái, Nùng (60+) | Thường xuyên | Quỹ BHYT & Ngân sách Y tế |

---

## 📈 CHUYÊN ĐỀ 5: MÔ HÌNH TƯƠNG QUAN ĐA BIẾN & TÁC ĐỘNG HẠ TẦNG ĐẾN ĐÓI NGHÈO (STATISTICAL CORRELATION & INFRASTRUCTURE IMPACT MATRIX)

### 1. Bối Cảnh Nghiệp Vụ & Kiểm Định Giả Thuyết Kinh Tế Lượng
- **Bài toán quản trị:** Trong phân bổ ngân sách đầu tư công, một câu hỏi lớn luôn được đặt ra: *Đầu tư vào hạ tầng giao thông (đường nhựa, đường bê tông) có thực sự giúp kéo giảm tỷ lệ hộ nghèo cấp xã hay không? Mức độ tác động mạnh đến đâu?*
- **Kiểm định kinh tế lượng:** 
  - Sử dụng toàn bộ 146 xã/phường/thị trấn toàn tỉnh Đắk Lắk từ bảng `daklak_analytics.fact_hatang_xa`.
  - Đo lường hệ số tương quan Pearson ($r$) và xây dựng phương trình hồi quy tuyến tính thực nghiệm:
    $$\text{Tỷ lệ hộ nghèo (\%)} = \beta_0 + \beta_1 \times \text{Khoảng cách đến huyện (km)} + \epsilon$$
  - Xây dựng ma trận phân hóa $2 \times 2$ để nhận diện các xã rơi vào **"Bẫy khó khăn kép"** phục vụ ra quyết định đầu tư công có trọng tâm, trọng điểm.

---

### 2. Kịch Bản Truy Vấn SQL Phân Tích (PostgreSQL Analytics Queries)

#### Query 2A: Tính Ma Trận Tương Quan Pearson ($r$), Hệ Số Xác Định ($R^2$) và Hồi Quy Tuyến Tính

```sql
SELECT 
    -- 1. Hệ số tương quan Pearson (r) với Tỷ lệ nghèo của 146 xã
    ROUND(CAST(CORR(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 4) AS r_khoang_cach_huyen,
    ROUND(CAST(CORR(ty_le_ngheo_pct, ty_le_thon_duong_cung_pct) AS NUMERIC), 4) AS r_ty_le_duong_cung,
    ROUND(CAST(CORR(ty_le_ngheo_pct, km_duong_be_tong) AS NUMERIC), 4) AS r_km_duong_be_tong,
    ROUND(CAST(CORR(ty_le_ngheo_pct, ty_le_can_ngheo_pct) AS NUMERIC), 4) AS r_ty_le_can_ngheo,
    
    -- 2. Hệ số xác định R2 (Khoảng cách giải thích được bao nhiêu % sự biến thiên của đói nghèo)
    ROUND(CAST(REGR_R2(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 4) AS r2_khoang_cach,
    
    -- 3. Hệ số góc hồi quy (Slope: Cứ cách xa huyện thêm 1 km, tỷ lệ nghèo tăng bao nhiêu %)
    ROUND(CAST(REGR_SLOPE(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 4) AS he_so_goc_slope_khoang_cach,
    
    -- 4. Tỷ lệ nghèo nền tảng tại trung tâm huyện (Intercept khi khoảng cách = 0 km)
    ROUND(CAST(REGR_INTERCEPT(ty_le_ngheo_pct, km_den_trung_tam_huyen) AS NUMERIC), 2) AS ty_le_ngheo_co_so_intercept
FROM daklak_analytics.fact_hatang_xa;
```

#### Query 2B: Ma Trận Phân Hóa $2 \times 2$ (Khoảng Cách Địa Lý $\times$ Tỷ Lệ Đường Cứng)

```sql
WITH commune_quadrant AS (
    SELECT 
        ten_xa,
        ten_huyen,
        ty_le_ngheo_pct,
        km_den_trung_tam_huyen,
        ty_le_thon_duong_cung_pct,
        CASE 
            WHEN km_den_trung_tam_huyen < 20 AND ty_le_thon_duong_cung_pct >= 70 THEN '1. Thuận lợi kép (Gần <20km & Đường tốt >=70%)'
            WHEN km_den_trung_tam_huyen < 20 AND ty_le_thon_duong_cung_pct < 70 THEN '2. Gần nhưng nghẽn giao thông (<70%)'
            WHEN km_den_trung_tam_huyen >= 20 AND ty_le_thon_duong_cung_pct >= 70 THEN '3. Vùng xa (>=20km) nhưng đường đã cứng hóa'
            ELSE '4. Khó khăn kép (Xa >=20km & Đường xấu <70%)'
        END AS phan_nhom_ha_tang
    FROM daklak_analytics.fact_hatang_xa
)
SELECT 
    phan_nhom_ha_tang,
    COUNT(*) AS so_luong_xa,
    ROUND(AVG(km_den_trung_tam_huyen), 1) AS culy_trung_binh_km,
    ROUND(AVG(ty_le_thon_duong_cung_pct), 1) AS duong_cung_trung_binh_pct,
    ROUND(AVG(ty_le_ngheo_pct), 2) AS ty_le_ngheo_trung_binh_pct
FROM commune_quadrant
GROUP BY phan_nhom_ha_tang
ORDER BY ty_le_ngheo_trung_binh_pct ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (146 Xã/Phường Toàn Tỉnh Đắk Lắk)

#### Bảng 3A: Các Chỉ Số Thống Kê & Hồi Quy Tuyến Tính Thực Nghiệm
| Chỉ Số Kinh Tế Lượng | Biến Số Đối Sánh | Giá Trị Thực Nghiệm | Diễn Giải Ý Nghĩa Thống Kê |
|---|---|:---:|:---|
| **Hệ số tương quan Pearson ($r$)** | Khoảng cách đến huyện (`km`) | **$+0.3218$** | Tương quan thuận có ý nghĩa ($p < 0.01$): Càng xa trung tâm thì tỷ lệ nghèo càng tăng |
| **Hệ số tương quan Pearson ($r$)** | Tỷ lệ đường cứng hóa (`%`) | **$-0.1324$** | Tương quan nghịch: Cứng hóa đường góp phần kéo giảm tỷ lệ nghèo đa chiều |
| **Hệ số tương quan Pearson ($r$)** | Tỷ lệ hộ cận nghèo (`%`) | **$+0.5271$** | Tương quan thuận mạnh: Xã nghèo cao luôn đi kèm tỷ lệ cận nghèo cao (nguy cơ tái nghèo) |
| **Hệ số xác định ($R^2$)** | Khoảng cách đến huyện | **$0.1036$** | Khoảng cách địa lý giải thích được **$10.36\%$** độ biến thiên của tỷ lệ nghèo cấp xã |
| **Hệ số dốc hồi quy ($\beta_1$ Slope)**| Khoảng cách đến huyện | **$+0.5132$** | **Cứ cách xa huyện thêm 1 km, tỷ lệ nghèo của xã tăng thêm $+0.5132$ điểm %** |
| **Điểm chặn hồi quy ($\beta_0$ Intercept)**| Điểm gốc tại huyện ($0\text{ km}$) | **$13.10\%$** | Tỷ lệ hộ nghèo nền tảng của các xã sát cạnh trung tâm huyện là $13.10\%$ |

#### Bảng 3B: Ma Trận Phân Hóa $2 \times 2$ (Khoảng Cách Địa Lý $\times$ Hạ Tầng Đường Cứng)
| Nhóm Ma Trận | Đặc Điểm Nhóm | Số Lượng Xã | Cự Ly TB Đến Huyện (km) | Tỷ Lệ Đường Cứng TB (%) | Tỷ Lệ Hộ Nghèo TB (%) | Đánh Giá Tác Động Chính Sách |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| **Nhóm 1** | **Thuận lợi kép (Gần <20km & Đường $\ge 70\%$)** | **109 xã** | 9.2 km | 99.5% | **17.79%** | Vùng trũng nghèo thấp, kinh tế hàng hóa phát triển |
| **Nhóm 2** | Gần nhưng nghẽn hạ tầng (<20km & Đường <70%) | 0 xã | - | - | - | Không phát sinh xã gần mà đường quá xấu |
| **Nhóm 3** | **Vùng xa ($\ge 20$km) nhưng đường đã cứng hóa** | **36 xã** | 31.0 km | 99.8% | **28.62%** | Tỷ lệ nghèo cao gấp **1.61 lần** Nhóm 1 dù đường đã cứng hóa 99.8% |
| **Nhóm 4** | **Khó khăn kép (Xa $\ge 20$km & Đường xấu <70%)** | **1 xã** | **22.0 km** | **63.6%** | **42.81%** | Tỷ lệ nghèo cao gấp **2.41 lần** Nhóm 1 (Điểm nóng cần giải cứu khẩn cấp) |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Phương trình kinh tế lượng khẳng định quy luật địa lý:**
  $$\text{Tỷ lệ hộ nghèo (\%)} = 13.10\% + 0.5132 \times \text{Khoảng cách (km)}$$
  Số liệu chứng minh đanh thép: Cứ mỗi **$10\text{ km}$** nằm xa trung tâm huyện, tỷ lệ hộ nghèo DTTS của xã **tăng thêm trung bình $+5.13$ điểm phần trăm**.
- **Khoảng cách tạo ra phân hóa giàu nghèo sâu sắc:** 
  - Các xã nằm trong bán kính thuận lợi dưới 20km có tỷ lệ nghèo bình quân chỉ **$17.79\%$**.
  - Các xã vùng xa từ 20km trở lên có tỷ lệ nghèo vọt lên **$28.62\%$** (tăng thêm gần 11 điểm %).
  - Xã rơi vào nhóm **Khó khăn kép** (như xã Cư Klông - Ea H'leo, cự ly 22km, tỷ lệ đường cứng mới đạt 63.6%) có tỷ lệ nghèo vọt lên tới **$42.81\%$**.
- **Hiện tượng thống kê đặc biệt (Zero Variance ở chỉ tiêu Trạm Y tế):** Cả hai chỉ tiêu `tram_y_te_dat_chuan` và `tram_y_te_co_bac_si` đều cho kết quả hệ số tương quan $r = \text{NULL}$ vì **$100\%$ các xã trong tỉnh đều đã được công nhận đạt chuẩn trên giấy tờ** (độ lệch chuẩn $\sigma = 0$). Về mặt kinh tế lượng, chỉ tiêu này không còn giá trị phân hóa mức độ nghèo đói thực tế.

#### 2. ANALYSIS (Phân Tích Căn Nguyên: "Ma Sát Không Gian & Nghịch Lý Đường Bê Tông")
- **Hiệu ứng "Ma sát không gian" (Spatial Friction):** Khoảng cách địa lý không chỉ là số km thuần túy, mà là chi phí vận chuyển xăng dầu, hao mòn phương tiện, thời gian di chuyển của nông dân và thương lái. Nông sản làm ra ở vùng xa (như sắn, ngô, chuối, bơ) thường xuyên bị tư thương ép giá từ 15–25% so với giá thị trường tại trung tâm huyện để bù vào chi phí vận chuyển.
- **Nghịch lý: Tại sao đường cứng đạt $99.8\%$ mà xã vùng xa nghèo vẫn $28.62\%$?** 
  Phát hiện từ Nhóm 3 chỉ ra bài học thực tế quan trọng: **Đường bê tông ngõ xóm chỉ là điều kiện CẦN nhưng chưa bao giờ là điều kiện ĐỦ để thoát nghèo!** Người dân vùng xa có đường đi lại thuận tiện hơn, nhưng nếu:
  1. *Không có kho lạnh, trạm sơ chế bảo quản nông sản tại chỗ.*
  2. *Không có hợp tác xã bao tiêu đầu ra và sóng viễn thông kết nối thương mại điện tử.*
  Thì người nông dân vẫn chỉ bán nông sản thô giá rẻ và mắc kẹt trong bẫy nghèo nông nghiệp 88.97% như đã chứng minh ở Trụ cột 3.

#### 3. IMPACT (Tác Động Đến Quyết Định Phân Bổ Vốn Đầu Tư Công)
- **Cảnh báo lãng phí đầu tư biên (Marginal Efficiency of Capital):** Nếu tỉnh tiếp tục rót vốn làm đường giao thông dàn trải vào 109 xã thuộc Nhóm 1 (nơi đường cứng đã đạt 99.5% và nghèo chỉ 17.79%), hiệu quả giảm nghèo cận biên sẽ gần như bằng $0$.
- **Nguy cơ cô lập vĩnh viễn:** Xã thuộc Nhóm 4 nếu không được ưu tiên hoàn thành cứng hóa $36.4\%$ đường giao thông còn lại sẽ tiếp tục chịu tỷ lệ nghèo trên $40\%$, kéo lùi chỉ tiêu hoàn thành Nông thôn mới của toàn huyện.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Đầu Tư Công Có Trọng Tâm)

- **Cứu nguy khẩn cấp cho xã thuộc Nhóm 4 (Khó khăn kép):**
  Sở Giao thông Vận tải và UBND huyện Ea H'leo ưu tiên bố trí nguồn vốn CTMTQG 1719 hoàn thành cứng hóa dứt điểm $100\%$ các trục đường thôn buôn còn lầy lội tại xã Cư Klông ngay trong năm 2025 để phá thế cô lập giao thông.

- **Chuyển trọng tâm từ "Làm đường vật lý" sang "Hạ tầng Logistics Nông sản" cho 36 xã Nhóm 3:**
  Sở Công Thương và Sở Nông nghiệp không chỉ dừng lại ở mở đường, mà cần triển khai gói hỗ trợ xây dựng **Trạm thu mua - Sơ chế - Bảo quản nông sản liên xã** tại các cụm xã vùng xa (cách huyện >20km). Thu hút doanh nghiệp đầu tư kho lạnh và bao tiêu nông sản để nâng cao giá trị hạt cà phê, sầu riêng, mắc ca của đồng bào.

- **Phát triển mạng lưới Giao thông Công cộng Nông thôn (Bus kết nối liên huyện):**
  Sở GTVT trợ giá mở các tuyến xe buýt nông thôn định kỳ từ các cụm xã vùng xa (Ea Súp, Krông Bông, Lắk) về các khu/cụm công nghiệp tại TP. Buôn Ma Thuột và Thị xã Buôn Hồ, giúp con em đồng bào DTTS có thể đi làm công nhân phi nông nghiệp sáng đi tối về mà không phải di cư tốn kém.

---

### 5. Ma Trận Hành Động Can Thiệp Chuyên Đề 5

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Cứng hóa dứt điểm đường Nhóm 4** | Sở GTVT Đắk Lắk | UBND Huyện Ea H'leo | Xã Cư Klông (Ea H'leo) | 2025 | Dự án 4 (CTMTQG 1719) |
| **Xây dựng cụm sơ chế & kho lạnh vùng xa** | Sở Công Thương | Sở NN&PTNT, Liên minh HTX | 36 xã vùng xa (Nhóm 3) | 2025–2027 | Vốn kích cầu nông nghiệp & OCOP |
| **Xe buýt nông thôn trợ giá cho lao động** | Sở GTVT Đắk Lắk | Sở Tài chính, Doanh nghiệp vận tải | Lao động vùng sâu đi làm KCN | Thường xuyên | Ngân sách trợ giá giao thông công cộng |

---

## 🛑 CHUYÊN ĐỀ 6: TỆ NẠN XÃ HỘI, NGHIỆN MA TÚY & NGUY CƠ LÂY NHIỄM HIV/AIDS VÙNG ĐỒNG BÀO DTTS

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở An Ninh - Xã Hội
- **Căn cứ chiến lược:** Chỉ thị số 36-CT/TW của Bộ Chính trị về tăng cường, nâng cao hiệu quả công tác phòng, chống và kiểm soát ma túy; Chiến lược Quốc gia chấm dứt dịch bệnh AIDS vào năm 2030 (Quyết định 1246/QĐ-TTg).
- **Vấn nạn xã hội kép (Dual Social Burden):** Tệ nạn ma túy và lây nhiễm HIV/AIDS không chỉ tàn phá thể chất người bệnh mà còn là "cỗ máy hủy diệt kinh tế gia đình". Người nghiện ma túy mất hoàn toàn sức lao động, bào mòn tài sản gia đình, kéo theo nguy cơ lây nhiễm HIV cho vợ/con và tạo ra những thế hệ trẻ em mồ côi rơi vào bước đường cùng.
- **Mục tiêu phân tích:** Bóc tách dữ liệu từ bảng sự kiện `daklak_analytics.fact_matuy_hiv_xa` (146 xã) để:
  1. Xếp hạng các huyện có số người DTTS nghiện ma túy và nhiễm HIV cao nhất tỉnh.
  2. Định vị chính xác **Top xã "Tâm chấn kép"** để khoanh vùng can thiệp y tế và an ninh trật tự.

---

### 2. Kịch Bản Truy Vấn SQL Phân Tích (PostgreSQL Analytics Queries)

#### Query 6A: Xếp Hạng Tâm Chấn Ma Túy & HIV/AIDS Theo Cấp Huyện
```sql
WITH district_summary AS (
    SELECT 
        ten_huyen,
        SUM(nguoi_nghien_ma_tuy_tong) AS ma_tuy_tong,
        SUM(nguoi_dtts_nghien_ma_tuy) AS ma_tuy_dtts,
        SUM(nguoi_nhiem_hiv_tong) AS hiv_tong,
        SUM(nguoi_dtts_nhiem_hiv) AS hiv_dtts
    FROM daklak_analytics.fact_matuy_hiv_xa
    GROUP BY ten_huyen
),
ranked_districts AS (
    SELECT 
        ten_huyen,
        ma_tuy_tong,
        ma_tuy_dtts,
        ROUND(CAST(ma_tuy_dtts AS NUMERIC) / NULLIF(ma_tuy_tong, 0) * 100, 2) AS ty_le_ma_tuy_la_dtts_pct,
        ROUND(CAST(ma_tuy_dtts AS NUMERIC) / NULLIF(SUM(ma_tuy_dtts) OVER (), 0) * 100, 2) AS ty_trong_ma_tuy_dtts_toan_tinh_pct,
        hiv_tong,
        hiv_dtts,
        ROUND(CAST(hiv_dtts AS NUMERIC) / NULLIF(hiv_tong, 0) * 100, 2) AS ty_le_hiv_la_dtts_pct,
        ROUND(CAST(hiv_dtts AS NUMERIC) / NULLIF(SUM(hiv_dtts) OVER (), 0) * 100, 2) AS ty_trong_hiv_dtts_toan_tinh_pct,
        DENSE_RANK() OVER (ORDER BY ma_tuy_dtts DESC, hiv_dtts DESC) AS rank_diem_nong_ma_tuy,
        DENSE_RANK() OVER (ORDER BY hiv_dtts DESC, ma_tuy_dtts DESC) AS rank_diem_nong_hiv
    FROM district_summary
)
SELECT 
    rank_diem_nong_ma_tuy,
    ten_huyen,
    ma_tuy_tong,
    ma_tuy_dtts,
    ty_le_ma_tuy_la_dtts_pct,
    ty_trong_ma_tuy_dtts_toan_tinh_pct,
    hiv_tong,
    hiv_dtts,
    ty_le_hiv_la_dtts_pct,
    ty_trong_hiv_dtts_toan_tinh_pct
FROM ranked_districts
ORDER BY ma_tuy_dtts DESC;
```

#### Query 6B: Top 10 Xã "Tâm Chấn Kép" Ma Túy & HIV Vùng Đồng Bào DTTS
```sql
SELECT 
    DENSE_RANK() OVER (ORDER BY nguoi_dtts_nghien_ma_tuy DESC, nguoi_dtts_nhiem_hiv DESC) AS rank_xa,
    ten_xa,
    ten_huyen,
    nguoi_nghien_ma_tuy_tong,
    nguoi_dtts_nghien_ma_tuy,
    ROUND(CAST(nguoi_dtts_nghien_ma_tuy AS NUMERIC) / NULLIF(nguoi_nghien_ma_tuy_tong, 0) * 100, 2) AS ty_le_ma_tuy_dtts_pct,
    nguoi_nhiem_hiv_tong,
    nguoi_dtts_nhiem_hiv
FROM daklak_analytics.fact_matuy_hiv_xa
WHERE nguoi_dtts_nghien_ma_tuy > 0 OR nguoi_dtts_nhiem_hiv > 0
ORDER BY nguoi_dtts_nghien_ma_tuy DESC, nguoi_dtts_nhiem_hiv DESC
LIMIT 10;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Trích Xuất Từ PostgreSQL)

#### Bảng 6A: Xếp Hạng Điểm Nóng Ma Túy & HIV/AIDS Theo 15 Đơn Vị Cấp Huyện
| Hạng Điểm Nóng | Huyện / Thị Xã / Thành Phố | Tổng Người Nghiện | Người DTTS Nghiện | Tỷ Lệ DTTS Nghiện (%) | Tỷ Trọng DTTS Nghiện / Tỉnh (%) | Tổng Người Nhiễm HIV | Người DTTS Nhiễm HIV | Tỷ Lệ DTTS Nhiễm HIV (%) | Tỷ Trọng DTTS HIV / Tỉnh (%) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Huyện Ea H'leo** | **126** | **89** | **70.63%** | **32.13%** | 33 | **15** | **45.45%** | **16.85%** |
| **2** | **Huyện Krông Năng** | 46 | **33** | **71.74%** | **11.91%** | 48 | **18** | **37.50%** | **20.22%** |
| **3** | **TP. Buôn Ma Thuột** | 258 | 29 | 11.24% | 10.47% | 62 | 5 | 8.06% | 5.62% |
| **4** | **Huyện Cư Kuin** | 48 | 22 | 45.83% | 7.94% | 18 | 3 | 16.67% | 3.37% |
| **5** | **Huyện Krông Búk** | 31 | 20 | 64.52% | 7.22% | 19 | 0 | 0.00% | 0.00% |
| **6** | **Huyện Krông Pắc** | 50 | 18 | 36.00% | 6.50% | 23 | 2 | 8.70% | 2.25% |
| **7** | **Huyện Ea Kar** | 73 | 17 | 23.29% | 6.14% | 63 | **11** | 17.46% | **12.36%** |
| **8** | **Huyện Buôn Đôn** | 29 | 16 | 55.17% | 5.78% | 14 | 5 | 35.71% | 5.62% |
| **9** | **Huyện Cư M'gar** | 62 | 16 | 25.81% | 5.78% | 20 | 4 | 20.00% | 4.49% |
| **10**| **Huyện Krông A Na** | 55 | 7 | 12.73% | 2.53% | 40 | 0 | 0.00% | 0.00% |
| **11**| **Thị Xã Buôn Hồ** | 13 | 4 | 30.77% | 1.44% | 3 | 3 | 100.00% | 3.37% |
| **12**| **Huyện Ea Súp** | 16 | 3 | 18.75% | 1.08% | **64** | **15** | 23.44% | **16.85%** |
| **13**| **Huyện M'Đrắk** | 9 | 3 | 33.33% | 1.08% | 3 | 2 | 66.67% | 2.25% |
| **14**| **Huyện Krông Bông** | 2 | 0 | 0.00% | 0.00% | 11 | 5 | 45.45% | 5.62% |
| **15**| **Huyện Lắk** | 1 | 0 | 0.00% | 0.00% | 9 | 1 | 11.11% | 1.12% |

*Quy mô toàn tỉnh Đắk Lắk:*
- **Ma túy:** 819 người nghiện (DTTS: **277 người - chiếm 33.82%**).
- **HIV/AIDS:** 430 người nhiễm (DTTS: **89 người - chiếm 20.70%**).

---

#### Bảng 6B: Top 10 Xã "Tâm Chấn Kép" Vùng Đồng Bào DTTS
| Hạng Xã | Tên Xã | Thuộc Huyện | Tổng Người Nghiện | Người DTTS Nghiện | Tỷ Lệ DTTS Nghiện (%) | Tổng Người HIV | Người DTTS HIV | Đánh Giá Mức Độ Nguy Cơ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | **Xã Ea Wy** | **Huyện Ea H'leo** | **44** | **42** | **95.45%** | **19** | **13** | **Tâm chấn số 1 toàn tỉnh (Báo động đỏ cả Ma túy & HIV)** |
| **2** | **Xã Ea Tam** | **Huyện Krông Năng**| **20** | **20** | **100.00%** | **10** | **8** | **100% người nghiện là DTTS, HIV DTTS cao thứ 2 tỉnh** |
| **3** | **Xã Cư Né** | **Huyện Krông Búk** | 27 | **20** | 74.07% | 1 | 0 | Điểm nóng ma túy vùng chuyên canh cà phê |
| **4** | **Xã Ea Tiêu**| **Huyện Cư Kuin** | 19 | **16** | 84.21% | 0 | 0 | Cụm dân cư buôn làng vùng ven |
| **5** | **Xã Ea Khal**| **Huyện Ea H'leo** | 14 | **14** | 100.00% | 3 | 2 | Xã giáp ranh trung tâm Ea H'leo |
| **6** | **Phường Ea Tam**| **TP. Buôn Ma Thuột**| 33 | 10 | 30.30% | 14 | 0 | Đô thị hóa, phức tạp trật tự xã hội |
| **7** | **Xã Ea Tir** | **Huyện Ea H'leo** | 12 | 10 | 83.33% | 0 | 0 | Vùng sâu Ea H'leo |
| **8** | **Xã Cư A Mung**| **Huyện Ea H'leo** | 9 | 9 | 100.00% | 0 | 0 | 100% người nghiện là DTTS |
| **9** | **Xã Cư Huê** | **Huyện Ea Kar** | 18 | 7 | 38.89% | 4 | 1 | Cửa ngõ huyện Ea Kar |
| **10**| **Xã Ea Na** | **Huyện Krông A Na** | 35 | 7 | 20.00% | 0 | 0 | Vùng ven sông |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Sự tập trung dị biệt tại Huyện Ea H'leo:**
  - Huyện Ea H'leo một mình chiếm tới **32.13% tổng số người DTTS nghiện ma túy của cả tỉnh (89 / 277 người)**. 
  - Tại Ea H'leo, cứ 10 người nghiện ma túy thì có tới **7 người là đồng bào DTTS (70.63%)**.
  - Ea H'leo cũng ghi nhận **15 người DTTS nhiễm HIV (chiếm 16.85% toàn tỉnh)**.
- **Krông Năng - Đỉnh dịch HIV trong vùng đồng bào DTTS:**
  - Huyện Krông Năng đứng **vị trí số 1 toàn tỉnh về số người DTTS nhiễm HIV (18 người - chiếm 20.22% toàn tỉnh)**.
  - Tỷ lệ người nghiện ma túy là DTTS tại huyện cũng lên tới **71.74% (33 / 46 người)**.
- **Điểm nóng cực đoan cấp xã (Xã Ea Wy - Ea H'leo):**
  - Xã Ea Wy ghi nhận **42 người DTTS nghiện ma túy (chiếm 95.45% người nghiện tại xã)** và **13 người DTTS nhiễm HIV (chiếm 68.42% số ca nhiễm HIV tại xã)**. Một mình xã Ea Wy chiếm tới gần **15% tổng số ca HIV và ma túy DTTS toàn tỉnh**!

#### 2. ANALYSIS (Phân Tích Căn Nguyên: "Hành Lang Di Cư & Chuỗi Lây Truyền Tiêm Chích")
- **Yếu tố địa lý - Cửa ngõ di cư phía Bắc:** 
  Ea H'leo và Krông Năng là hai địa bàn cửa ngõ tiếp giáp tỉnh Gia Lai và vùng rừng núi Đông Bắc. Đây là nơi tiếp nhận làn sóng đồng bào DTTS di cư tự do từ các tỉnh miền núi phía Bắc (như người Mông, Dao, Tày, Nùng) từ những năm 1990–2000. Tệ nạn hút hít và tiêm chích ma túy đã theo chân một bộ phận lao động di cư xâm nhập sâu vào các buôn làng biệt lập.
- **Cơ chế lây truyền khép kín "Ma túy ➔ Bơm kim tiêm chung ➔ Quan hệ tình dục":**
  Tại các buôn làng xa xôi, do tâm lý mặc cảm và sợ bị cơ quan công an phát hiện, người nghiện thường tụ tập lén lút tiêm chích trong chòi rẫy, dùng chung bơm kim tiêm không vô trùng. Đây là "đường cao tốc" truyền virus HIV trong nhóm người nghiện. Sau đó, virus âm thầm lây truyền sang người vợ/bạn tình thông qua quan hệ tình dục không an toàn do thiếu kiến thức phòng hộ.
- **Bẫy kiệt quệ sinh kế & Tan vỡ cấu trúc gia đình:**
  Chi phí mua ma túy hàng ngày ngốn sạch thu nhập còm cõi từ nương rẫy. Người nghiện bán dần phân bón, nông cụ, gia súc và cuối cùng là đất sản xuất. Người trụ cột gia đình mất sức lao động hoặc chết trẻ vì AIDS, để lại gánh nặng nợ nần cho người vợ già và đẩy con cái vào nguy cơ thất học, tạo thành một thế hệ dễ bị tổn thương tiếp theo.

#### 3. IMPACT (Tác Động Đến Trật Tự Xã Hội & Sức Khỏe Cộng Đồng)
- **Nguy cơ bùng phát dịch HIV tiềm ẩn:** Con số 89 người DTTS nhiễm HIV ghi nhận được chỉ là "phần nổi của tảng băng chìm". Do rào cản kỳ thị rất nặng nề trong buôn làng, tỷ lệ người tự nguyện đi xét nghiệm rất thấp; nguy cơ virus tiếp tục lây lan sang phụ nữ mang thai và gây lây truyền từ mẹ sang con là rất lớn.
- **Bất ổn an ninh trật tự nông thôn:** Tệ nạn ma túy là nguồn gốc nảy sinh các vụ trộm cắp cà phê, tiêu, trâu bò và gây mất trật tự an ninh buôn làng, đe dọa trực tiếp đến phong trào "Toàn dân bảo vệ an ninh Tổ quốc".

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Can Thiệp Y Tế & An Ninh)

- **Thành lập Điểm cấp phát thuốc Methadone vệ tinh tại Trạm Y tế Xã Ea Wy (Ea H'leo) và Xã Ea Tam (Krông Năng) (Sở Y tế chủ trì):**
  Người nghiện vùng sâu không thể đi 20–30km ra trung tâm huyện mỗi ngày để uống Methadone. Việc đặt điểm uống Methadone ngay tại trạm y tế xã điểm nóng sẽ giúp giữ chân người nghiện, cắt đứt cơn thèm ma túy và triệt tiêu hành vi tiêm chích chung bơm kim tiêm.

- **Chương trình "Giảm hại & Xét nghiệm HIV lưu động tận chòi rẫy" (CDC Đắk Lắk & Trung tâm Y tế Huyện):**
  Tổ chức cấp phát miễn phí bơm kim tiêm sạch và bao cao su thông qua đội ngũ cộng tác viên buôn làng; triển khai xét nghiệm sàng lọc HIV nhanh bằng giọt máu đầu ngón tay miễn phí, bảo mật danh tính cho các đối tượng nguy cơ cao và phụ nữ mang thai.

- **Mô hình "Buôn làng bình yên - Cai nghiện gắn với hỗ trợ sinh kế" (Công an tỉnh & Hội Nông dân):**
  Lực lượng Công an xã tăng cường đấu tranh triệt phá các điểm bán lẻ ma túy; phối hợp với Hội Nông dân và Ban Dân tộc tỉnh hỗ trợ con giống (bò sinh sản, dê), hướng dẫn kỹ thuật nông nghiệp cho người sau cai nghiện để giúp họ tái hòa nhập cộng đồng bền vững, không quay lại con đường nghiện ngập.

---

### 5. Ma Trận Hành Động Can Thiệp Chuyên Đề 6

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Cấp phát Methadone tại xã điểm nóng** | Sở Y tế tỉnh Đắk Lắk | TTYT Huyện Ea H'leo, Krông Năng | Người nghiện tại Xã Ea Wy, Ea Tam | Q2/2025 | Dự án Quỹ Toàn cầu & Ngân sách tỉnh |
| **Xét nghiệm HIV lưu động & Can thiệp giảm hại** | CDC tỉnh Đắk Lắk | Trạm y tế xã, Đoàn thanh niên | Người tiêm chích, phụ nữ mang thai vùng sâu | Định kỳ hàng quý | Ngân sách phòng chống HIV/AIDS |
| **Triệt xóa tụ điểm & Hỗ trợ sinh kế sau cai** | Công an tỉnh Đắk Lắk | Hội Nông dân, UBND Huyện | Người sau cai nghiện tại Ea H'leo, Krông Năng | Thường xuyên | Quỹ An ninh trật tự & CTMTQG 1719 |

---

## 🎓 CHUYÊN ĐỀ 7: CHẤT LƯỢNG NGUỒN NHÂN LỰC & BẪY LAO ĐỘNG KHÔNG BẰNG CẤP (87.36% CHƯA QUA ĐÀO TẠO)

### 1. Bối Cảnh Nghiệp Vụ & Nền Tảng Kỹ Năng Lao Động
- **Căn cứ chiến lược:** Quyết định 1719/QĐ-TTg Dự án 5 về Phát triển giáo dục đào tạo nâng cao chất lượng nguồn nhân lực; Chỉ thị 21-CT/TW của Ban Bí thư về đổi mới, phát triển và nâng cao chất lượng giáo dục nghề nghiệp đến năm 2030.
- **Bản chất kinh tế:** Trình độ chuyên môn kỹ thuật (CMKT) là biến số then chốt quyết định năng suất lao động và cơ hội chuyển dịch cơ cấu việc làm. Khi người lao động không có chứng chỉ nghề hoặc bằng cấp kỹ thuật, họ bị "khóa chặt" trong các công việc chân tay năng suất thấp, làm thuê nương rẫy và không thể vượt qua rào cản tuyển dụng của các doanh nghiệp chế biến, công nghiệp hay dịch vụ hiện đại.
- **Mục tiêu phân tích:** Bóc tách dữ liệu từ bảng sự kiện `daklak_analytics.fact_trinhdo_cmkt_dantoc` (398.381 lao động) để trả lời: *Dân tộc nào có tỷ lệ lao động không bằng cấp cao nhất, tạo ra rào cản gì cho quá trình công nghiệp hóa của tỉnh?*

---

### 2. Kịch Bản Truy Vấn SQL Phân Tích (PostgreSQL Analytics Query)
*Kỹ thuật SQL áp dụng:* Window Function `DENSE_RANK() OVER (ORDER BY ty_le_khong_cmkt_pct DESC)`, lọc mẫu số có ý nghĩa thống kê `tong_lao_dong >= 500`.

```sql
SELECT 
    DENSE_RANK() OVER (ORDER BY ty_le_khong_cmkt_pct DESC, tong_lao_dong DESC) AS rank_thieu_ky_nang,
    ten_dantoc,
    nhom_nguon_goc,
    tong_lao_dong,
    khong_co_cmkt,
    ty_le_khong_cmkt_pct,
    ROUND(100.0 - ty_le_khong_cmkt_pct, 2) AS ty_le_co_cmkt_pct,
    so_cap,
    trung_cap,
    cao_dang_dai_hoc
FROM daklak_analytics.fact_trinhdo_cmkt_dantoc
WHERE tong_lao_dong >= 500
ORDER BY ty_le_khong_cmkt_pct DESC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (14 Nhóm Dân Tộc Có Lao Động $\ge 500$ Người)

| Hạng Thiếu Kỹ Năng | Tên Dân Tộc | Phân Nhóm Nguồn Gốc | Tổng Lao Động Có Việc Làm | Lao Động Không Có CMKT | Tỷ Lệ Không CMKT (%) | Tỷ Lệ Đã Qua Đào Tạo (%) | Sơ Cấp Nghề | Trung Cấp | Cao Đẳng & Đại Học |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Mông** | Di cư miền núi phía Bắc | 28.018 | **27.173** | **96.98%** | **3.02%** | 264 | 143 | 242 |
| **2** | **Gia Rai** | Bản địa Tây Nguyên | 10.631 | **9.663** | **90.89%** | 9.11% | 91 | 134 | 308 |
| **3** | **Mnông** | Bản địa Tây Nguyên | 23.591 | **21.312** | **90.34%** | 9.66% | 201 | 469 | 1.003 |
| **4** | **Sán Chay** | Di cư miền núi phía Bắc | 1.874 | 1.672 | **89.22%** | 10.78% | 68 | 19 | 49 |
| **5** | **Nùng** | Di cư miền núi phía Bắc | 34.742 | **30.918** | **88.99%** | 11.01% | 883 | 504 | 905 |
| **6** | **Xơ Đăng** | Bản địa Tây Nguyên | 4.202 | 3.694 | **87.91%** | 12.09% | 61 | 56 | 143 |
| **7** | **Tày** | Di cư miền núi phía Bắc | 29.443 | **25.646** | **87.10%** | 12.90% | 1.227 | 545 | 968 |
| **8** | **Dao** | Di cư miền núi phía Bắc | 10.028 | 8.708 | **86.84%** | 13.16% | 911 | 125 | 82 |
| **9** | **Ê đê** | Bản địa Tây Nguyên | **225.772** | **194.835** | **86.30%** | 13.70% | 5.560 | 5.770 | 7.624 |
| **10**| **Thái** | Di cư miền núi phía Bắc | 12.373 | 10.288 | **83.15%** | 16.85% | 673 | 305 | 259 |
| **11**| **Hrê** | Khác | 540 | 449 | **83.15%** | 16.85% | 33 | 11 | 0 |
| **12**| **Mường** | Di cư miền núi phía Bắc | 11.644 | 9.159 | 78.66% | 21.34% | 832 | 400 | 460 |
| **13**| **Hoa** | Nam Bộ & Duyên hải | 1.107 | 867 | 78.32% | 21.68% | 131 | 32 | 14 |
| **14**| **Bru Vân Kiều**| Khác | 3.035 | 2.343 | 77.20% | 22.80% | 42 | 100 | 245 |

*Quy mô toàn tỉnh Đắk Lắk:*
- **Tổng số lao động DTTS có việc làm:** **398.381 người**.
- **Số lao động hoàn toàn KHÔNG CÓ TRÌNH ĐỘ CMKT:** **348.020 người (chiếm tới 87.36%)**.

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Tỷ lệ lao động không bằng cấp ở mức báo động:** Toàn tỉnh có tới **87.36% lao động DTTS (348.020 người)** là lao động phổ thông thuần túy, chưa từng qua bất kỳ trường lớp đào tạo chuyên môn kỹ thuật nào.
- **Người Mông đứng đầu về khoảng trống kỹ năng nghề:** Cứ 100 người lao động Mông thì có tới **gần 97 người hoàn toàn không có bằng cấp (96.98%)**. Cả cộng đồng 28.018 lao động Mông chỉ có vỏn vẹn **845 người có chứng chỉ/bằng cấp từ sơ cấp trở lên (3.02%)**.
- **Áp lực tuyệt đối ở người Ê Đê:** Chiếm hơn 56% lực lượng lao động của tỉnh, người Ê Đê có tới **194.835 lao động chưa qua đào tạo nghề (86.30%)**, tạo ra nút thắt cổ chai khổng lồ về chất lượng nguồn nhân lực cho các khu công nghiệp của tỉnh.

#### 2. ANALYSIS (Phân Tích Căn Nguyên "Mảnh Ghép Nhân Quả Của Bẫy Nông Nghiệp")
- **Mối liên hệ nhân quả với Bẫy nông nghiệp 88.97% (Trụ cột 3):** Đây chính là câu trả lời triệt để nhất cho câu hỏi: *Vì sao người DTTS không chuyển dịch sang công nghiệp hay dịch vụ?* Thực tế không phải họ không muốn, mà vì **không đủ điều kiện tuyển dụng tối thiểu** (chứng chỉ vận hành máy móc, an toàn lao động, sơ cấp nghề). Thiếu kỹ năng chuyên môn, họ buộc phải ở lại buôn làng làm nương rẫy hoặc bán sức lao động thời vụ với giá rẻ.
- **Sự đứt gãy giữa Đào tạo nghề và Thị trường lao động địa phương:** Các trung tâm giáo dục nghề nghiệp cấp huyện thường đào tạo các ngành nghề mang tính hình thức, chưa bám sát nhu cầu thực tế của các chuỗi giá trị nông nghiệp công nghệ cao (như kỹ thuật ghép sầu riêng, vận hành máy sấy cà phê công nghiệp, bảo dưỡng hệ thống tưới nhỏ giọt).

#### 3. IMPACT (Tác Động Đến Năng Suất & Thu Hút Đầu Tư)
- **Bẫy thu nhập thấp truyền đời:** Năng suất lao động không bằng cấp chỉ bằng 1/3 đến 1/4 so với lao động có chứng chỉ kỹ thuật, khiến thu nhập của hộ gia đình mãi mãi dậm chân tại chỗ dưới chuẩn nghèo.
- **Rào cản thu hút đầu tư FDI và công nghiệp chế biến:** Các tập đoàn lớn muốn đầu tư nhà máy chế biến cà phê, hoa quả sấy xuất khẩu tại Đắk Lắk gặp khó khăn lớn trong việc tuyển dụng lao động địa phương đáp ứng tiêu chuẩn kỹ thuật, buộc phải đưa lao động từ nơi khác đến.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Giáo Dục Nghề Nghiệp)

- **Đổi mới mô hình đào tạo nghề lưu động "Cầm tay chỉ việc tại buôn làng" (Sở LĐ-TB&XH chủ trì):**
  Không bắt thanh niên Mông, Ê Đê phải ra thị trấn học nghề; đưa giáo viên trường nghề về tận buôn mở các lớp sơ cấp nghề ngắn hạn (1–3 tháng) đào tạo kỹ thuật nông nghiệp công nghệ cao: chiết ghép sầu riêng, kỹ thuật phòng trừ sâu bệnh sinh học, vận hành máy bay không người lái (drone) phun thuốc bảo vệ thực vật.

- **Chính sách đặt hàng đào tạo nghề 3 bên "Nhà nước - Trường nghề - Doanh nghiệp":**
  UBND tỉnh ký cam kết với các doanh nghiệp lớn (Simexco, Trung Nguyên, Vina T&T) đài thọ 100% chi phí ăn ở, học nghề cho thanh niên DTTS, kèm cam kết tuyển dụng ngay sau khi tốt nghiệp vào làm việc tại các nhà máy chế biến nông sản trên địa bàn.

---

### 5. Ma Trận Hành Động Can Thiệp Chuyên Đề 7

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Đào tạo nghề nông nghiệp công nghệ cao** | Sở LĐ-TB&XH | Trường Cao đẳng Công nghệ Tây Nguyên | Thanh niên Mông, Ê đê, Gia Rai (18–35 tuổi) | 2025–2027 | Dự án 5 (CTMTQG 1719) |
| **Cam kết đặt hàng đào tạo 3 bên** | Sở Công Thương | Doanh nghiệp xuất khẩu nông sản | Lao động DTTS vùng sâu | Hàng năm | Ngân sách khuyến công & Quỹ doanh nghiệp |

---

## 🌾 CHUYÊN ĐỀ 8: TƯ LIỆU SẢN XUẤT - BẤT BÌNH ĐẲNG ĐẤT CANH TÁC (LAND SCARCITY TRAP)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Tư Liệu Sản Xuất
- **Căn cứ chiến lược:** Nghị quyết số 18-NQ/TW của Ban Chấp hành Trung ương Đảng về tiếp tục đổi mới, hoàn thiện thể chế, chính sách, nâng cao hiệu lực, hiệu quả quản lý và sử dụng đất; Dự án 1 (CTMTQG 1719) về giải quyết tình trạng thiếu đất ở, đất sản xuất.
- **Bản chất kinh tế:** Ở vùng Tây Nguyên, **Đất sản xuất là tư liệu sinh mệnh**. Ngưỡng hiệu quả kinh tế quy mô trong canh tác cây công nghiệp (cà phê, tiêu, cao su) đòi hỏi mỗi hộ gia đình phải có tối thiểu từ $1.5 – 2.0\text{ ha}$ đất canh tác để tạo ra dòng tiền thặng dư thoát nghèo. Hộ gia đình có dưới $0.5\text{ ha}$ đất canh tác chỉ sản xuất tự cấp tự túc, quanh năm làm thuê và đối mặt với nguy cơ nghèo đói vĩnh viễn.

---

### 2. Kịch Bản Truy Vấn SQL Phân Tích (PostgreSQL Analytics Query)
*Kỹ thuật SQL áp dụng:* CTE tính mức bình quân toàn tỉnh (10.529,6 m²), hàm phân loại 4 nhóm quy mô đất bằng `CASE WHEN` và xếp hạng độ khan hiếm đất bằng `DENSE_RANK()`.

```sql
WITH provincial_avg AS (
    SELECT 10529.6 AS bq_tinh_m2
)
SELECT 
    DENSE_RANK() OVER (ORDER BY dien_tich_dat_sx_bq_m2 ASC) AS rank_khan_hiem_dat,
    ten_dantoc,
    nhom_nguon_goc,
    dien_tich_dat_sx_bq_m2,
    dien_tich_dat_sx_bq_ha,
    ROUND(dien_tich_dat_sx_bq_m2 - p.bq_tinh_m2, 1) AS chenh_lech_so_voi_tinh_m2,
    CASE 
        WHEN dien_tich_dat_sx_bq_m2 < 5000 THEN '1. Thiếu đất nghiêm trọng (<0.5 ha)'
        WHEN dien_tich_dat_sx_bq_m2 < 10000 THEN '2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha)'
        WHEN dien_tich_dat_sx_bq_m2 < 20000 THEN '3. Đủ đất cơ bản (1.0 - 2.0 ha)'
        ELSE '4. Quy mô đất lớn (>=2.0 ha)'
    END AS phan_loai_quy_mo_dat
FROM daklak_analytics.fact_datsanxuat_dantoc
CROSS JOIN provincial_avg p
WHERE dien_tich_dat_sx_bq_m2 > 0
ORDER BY dien_tich_dat_sx_bq_m2 ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (15 Dân Tộc Có Diện Tích Đất Thấp Nhất Tỉnh)

| Hạng Khan Hiếm Đất | Tên Dân Tộc | Phân Nhóm Nguồn Gốc | Diện Tích Đất Bình Quân (m²/hộ) | Quy Đổi (ha/hộ) | Chênh Lệch So Với Bình Quân Tỉnh (m²) | Phân Loại Quy Mô Đất Đai |
|:---:|:---|:---|:---:|:---:|:---:|:---|
| **1** | **Chăm** | Nam Bộ & Duyên hải | **1.619,8** | **0,16 ha** | **-8.909,8** | 1. Thiếu đất nghiêm trọng (<0.5 ha) |
| **2** | **Thổ** | Di cư miền núi phía Bắc | **2.425,7** | **0,24 ha** | **-8.103,9** | 1. Thiếu đất nghiêm trọng (<0.5 ha) |
| **3** | **Co** | Khác | **3.093,8** | **0,31 ha** | **-7.435,8** | 1. Thiếu đất nghiêm trọng (<0.5 ha) |
| **4** | **Mảng** | Khác (Rất ít người) | **3.607,0** | **0,36 ha** | **-6.922,6** | 1. Thiếu đất nghiêm trọng (<0.5 ha) |
| **5** | **Bru Vân Kiều**| Khác | **4.026,3** | **0,40 ha** | **-6.503,3** | 1. Thiếu đất nghiêm trọng (<0.5 ha) |
| **6** | **Thái** | Di cư miền núi phía Bắc | **4.633,6** | **0,46 ha** | **-5.896,0** | 1. Thiếu đất nghiêm trọng (<0.5 ha) |
| **7** | **Chứt** | Khác (Rất ít người) | **4.759,1** | **0,48 ha** | **-5.770,5** | 1. Thiếu đất nghiêm trọng (<0.5 ha) |
| **8** | **Khmer** | Nam Bộ & Duyên hải | 5.262,5 | 0,53 ha | -5.267,1 | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |
| **9** | **Raglay** | Khác | 5.709,0 | 0,57 ha | -4.820,6 | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |
| **10**| **Hrê** | Khác | 5.959,2 | 0,60 ha | -4.570,4 | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |
| **11**| **Chơ Ro** | Khác | 6.578,8 | 0,66 ha | -3.950,8 | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |
| **12**| **Mạ** | Bản địa Tây Nguyên | 6.764,6 | 0,68 ha | -3.765,0 | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |
| **13**| **Xơ Đăng** | Bản địa Tây Nguyên | 7.473,6 | 0,75 ha | -3.056,0 | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |
| **14**| **Hoa** | Nam Bộ & Duyên hải | 7.708,5 | 0,77 ha | -2.821,1 | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |
| **15**| **Ê đê** | Bản địa Tây Nguyên | **8.302,3** | **0,83 ha** | **-2.227,3** | 2. Dưới mức bình quân tỉnh (0.5 - 1.0 ha) |

*Mức chuẩn toàn tỉnh Đắk Lắk:* Bình quân đạt **10.529,6 m²/hộ** (~1,05 ha).
*Nhóm có diện tích đất lớn (>2 ha):* Người **Dao (20.736,8 m²)**, **Ba Na (20.509,2 m²)**, **Mông (19.858,4 m²)**, **Cơ Ho (33.763,4 m²)**.

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Bất bình đẳng đất sản xuất sâu sắc:** Có tới **7 nhóm dân tộc rơi vào bẫy thiếu đất nghiêm trọng (< 0.5 ha/hộ)**: Chăm (0.16 ha), Thổ (0.24 ha), Co (0.31 ha), Mảng (0.36 ha), Bru Vân Kiều (0.40 ha), Thái (0.46 ha), Chứt (0.48 ha).
- **Nghịch lý ở người Ê Đê bản địa:** Dân tộc chủ thể của tỉnh Đắk Lắk chỉ sở hữu bình quân **8.302,3 m²/hộ (0.83 ha)**, hụt mất hơn **2.227 m²** so với mức bình quân chung toàn tỉnh.
- **Độ vênh quy mô đất lên tới 20 lần:** Người Cơ Ho (3.38 ha) và người Dao (2.07 ha) có diện tích đất gấp hơn 15–20 lần so với người Chăm (0.16 ha) và người Thổ (0.24 ha).

#### 2. ANALYSIS (Phân Tích Căn Nguyên "Manh Mún Đất Đai vs Địa Hình Đồi Dốc")
- **Nguyên nhân manh mún đất ở người Ê Đê:** Tập quán thừa kế theo dòng họ mẫu hệ qua nhiều thế hệ khiến diện tích đất rẫy ban đầu bị chia nhỏ cho các con gái khi lập gia đình mới. Đất đai manh mún ngăn cản việc cơ giới hóa và ứng dụng công nghệ tưới tiêu hiện đại.
- **Nghịch lý người Mông/Dao (Đất rộng nhưng vẫn nghèo):** Dù người Mông sở hữu gần 2 ha đất/hộ, nhưng phần lớn diện tích là **đất nương rẫy đồi dốc trên núi cao, thiếu nước tưới mùa khô và đất bị xói mòn rửa trôi bạc màu**. Diện tích danh nghĩa lớn nhưng năng suất thực tế cực thấp.
- **Bẫy thiếu đất của người Thái, Bru Vân Kiều:** Đồng bào di cư vào sau, không còn quỹ đất màu mỡ nên phải mua lại những mảnh đất cằn cỗi diện tích nhỏ ở vùng ven suối, không đủ tạo ra sinh kế đủ sống cho gia đình.

#### 3. IMPACT (Tác Động Đến An Ninh Sinh Kế & Rừng Tự Nhiên)
- **Áp lực phá rừng làm rẫy:** Thiếu đất sản xuất hợp pháp là nguyên nhân trực tiếp thúc đẩy tình trạng phá rừng, lấn chiếm đất lâm nghiệp trái phép tại các vùng giáp ranh Vườn quốc gia Yok Đôn và Chư Yang Sin.
- **Tình trạng "Nông dân không đất":** Nông dân có dưới 0.5 ha đất buộc phải bán sức lao động làm thuê nhật trình, thu nhập bấp bênh theo mùa vụ cà phê, mất hoàn toàn quyền tự chủ sinh kế.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Đất Đai)

- **Thu hồi đất lâm trường kém hiệu quả để tạo quỹ đất sản xuất cho hộ DTTS nghèo (Sở TN&MT & Ban Dân tộc):**
  Kiên quyết thu hồi các diện tích đất lâm nghiệp do các công ty lâm nghiệp quản lý kém hiệu quả, bàn giao về cho UBND cấp huyện để phân bổ đất sản xuất (tối thiểu 1 ha/hộ) cho các hộ dân tộc Chăm, Thái, Bru Vân Kiều, Ê Đê chưa có đất sản xuất theo Dự án 1 (CTMTQG 1719).

- **Chuyển đổi sang mô hình "Nông nghiệp sinh thái diện tích nhỏ":**
  Với các hộ có dưới 0.5 ha đất, Sở Nông nghiệp hướng dẫn chuyển đổi từ trồng ngô/sắn sang mô hình nông nghiệp giá trị cao: trồng nấm rơm, trồng dược liệu dưới tán cây, nuôi hươu sao lấy nhung hoặc nuôi ong lấy mật để tối ưu hóa giá trị trên từng mét vuông đất.

---

### 5. Ma Trận Hành Động Can Thiệp Chuyên Đề 8

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Thu hồi & Giao đất sản xuất lâm trường** | Sở TN&MT Đắk Lắk | Ban Dân tộc, UBND Huyện | Hộ Chăm, Thái, Bru Vân Kiều, Ê đê thiếu đất | 2025–2026 | Dự án 1 (CTMTQG 1719) |
| **Mô hình kinh tế nông nghiệp diện tích nhỏ**| Sở NN&PTNT | Trung tâm Khuyến nông tỉnh | Hộ có đất dưới 0.5 ha | Thường xuyên | Quỹ Khuyến nông & Hợp tác xã |

---

## 💰 CHUYÊN ĐỀ 9: "KHÁT VỐN" & KHOẢNG TRỐNG TÍN DỤNG CHÍNH SÁCH (FINANCIAL INCLUSION & CREDIT GAP)

### 1. Bối Cảnh Nghiệp Vụ & Nền Tảng Tài Chính Toàn Diện
- **Căn cứ chiến lược:** Chỉ thị số 40-CT/TW của Ban Bí thư về tăng cường sự lãnh đạo của Đảng đối với tín dụng chính sách xã hội; Chiến lược Tài chính toàn diện quốc gia đến năm 2025, định hướng đến năm 2030 (Quyết định 149/QĐ-TTg).
- **Bản chất kinh tế:** Tín dụng chính sách từ Ngân hàng Chính sách Xã hội (NHCSXH) là "dòng máu kinh tế" giúp hộ nghèo mua cây giống, phân bón, hệ thống tưới tiêu và mở rộng chăn nuôi. Khi xuất hiện **khoảng trống tín dụng (Credit Gap)** lớn giữa nhu cầu vay thực tế và khả năng giải ngân, người dân sẽ bị đẩy vào vòng xoáy của **"Tín dụng đen"** và bẫy nợ nần lãi suất cao từ các đại lý tư nhân.

---

### 2. Kịch Bản Truy Vấn SQL Phân Tích (PostgreSQL Analytics Query)
*Kỹ thuật SQL áp dụng:* Tính tỷ lệ đáp ứng vốn (`ty_le_dap_ung_von_pct`) và khoảng trống tín dụng (`khoang_trong_tin_dung_pct`), xếp hạng nhu cầu khát vốn bằng `DENSE_RANK()`.

```sql
SELECT 
    DENSE_RANK() OVER (ORDER BY so_ho_co_nhu_cau_vay DESC) AS rank_khat_von,
    ten_dantoc,
    nhom_nguon_goc,
    so_ho_da_vay_von,
    so_ho_co_nhu_cau_vay,
    tong_nhu_cau_ho,
    ty_le_dap_ung_von_pct,
    khoang_trong_tin_dung_pct
FROM daklak_analytics.fact_tindung_dantoc
WHERE tong_nhu_cau_ho >= 100
ORDER BY so_ho_co_nhu_cau_vay DESC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (12 Dân Tộc Có Nhu Cầu Vốn Lớn Nhất Tỉnh)

| Hạng Khát Vốn | Tên Dân Tộc | Phân Nhóm Nguồn Gốc | Số Hộ Đã Được Vay Vốn | Số Hộ ĐANG CÓ NHU CẦU VAY | Tổng Nhu Cầu Vốn (Hộ) | Tỷ Lệ Đáp Ứng Vốn (%) | Khoảng Trống Tín Dụng (%) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **1** | **Ê đê** | Bản địa Tây Nguyên | 21.640 | **17.330** | 38.970 | 55.53% | **44.47%** |
| **2** | **Nùng** | Di cư miền núi phía Bắc | 3.742 | **2.732** | 6.474 | 57.80% | **42.20%** |
| **3** | **Tày** | Di cư miền núi phía Bắc | 3.232 | **2.294** | 5.526 | 58.49% | **41.51%** |
| **4** | **Mnông** | Bản địa Tây Nguyên | 4.931 | **2.024** | 6.955 | 70.90% | **29.10%** |
| **5** | **Gia Rai** | Bản địa Tây Nguyên | 802 | **1.802** | 2.604 | **30.80%** | **69.20%** |
| **6** | **Mường** | Di cư miền núi phía Bắc | 2.164 | **1.678** | 3.842 | 56.32% | **43.68%** |
| **7** | **Thái** | Di cư miền núi phía Bắc | 1.867 | **1.400** | 3.267 | 57.15% | **42.85%** |
| **8** | **Mông** | Di cư miền núi phía Bắc | 1.494 | **873** | 2.367 | 63.12% | **36.88%** |
| **9** | **Dao** | Di cư miền núi phía Bắc | 1.380 | **594** | 1.974 | 69.91% | **30.09%** |
| **10**| **Bru Vân Kiều**| Khác | 552 | **532** | 1.084 | 50.92% | **49.08%** |
| **11**| **Xơ Đăng** | Bản địa Tây Nguyên | 733 | **432** | 1.165 | 62.92% | **37.08%** |
| **12**| **Sán Chay** | Di cư miền núi phía Bắc | 100 | **161** | 261 | **38.31%** | **61.69%** |

*Quy mô toàn tỉnh Đắk Lắk:*
- **Số hộ DTTS đã được vay vốn ưu đãi NHCSXH:** **42.938 hộ**.
- **Số hộ DTTS ĐANG CÓ NHU CẦU VAY VỐN:** **32.227 hộ**.
- **Khoảng trống tín dụng toàn tỉnh:** **42.87%** tổng nhu cầu vay vốn chưa được đáp ứng!

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Quy mô "khát vốn" khổng lồ:** Toàn tỉnh có tới **32.227 hộ DTTS đang cần vay vốn ưu đãi** để đầu tư sản xuất nhưng chưa được giải ngân (chiếm gần 43% tổng nhu cầu toàn tỉnh).
- **Áp lực tuyệt đối ở người Ê Đê:** Có tới **17.330 hộ người Ê Đê đang chờ vốn vay** (chiếm hơn 53% tổng số hộ có nhu cầu vay của cả tỉnh). Khoảng trống tín dụng của người Ê Đê lên tới **44.47%**.
- **Tỷ lệ bỏ rơi tín dụng cực đoan ở người Gia Rai và Sán Chay:** 
  - Người **Gia Rai** có tỷ lệ đáp ứng vốn thấp kỷ lục: chỉ **30.80%**, có tới **69.20% hộ đang khát vốn** (1.802 hộ có nhu cầu so với chỉ 802 hộ đã được vay).
  - Người **Sán Chay** có khoảng trống tín dụng lên tới **61.69%**.

#### 2. ANALYSIS (Phân Tích Căn Nguyên: "Rào Cản Quy Trình & Bẫy Tín Dụng Đại Lý Tư Nhân")
- **Nguyên nhân khoảng trống vốn:** Rào cản lớn nhất không phải là người dân không muốn vay, mà do:
  1. *Hạn mức nguồn vốn ngân sách nhà nước phân bổ cho chi nhánh NHCSXH tỉnh hàng năm có hạn.*
  2. *Quy trình bình xét cho vay ở cấp thôn buôn còn chậm trễ và e ngại rủi ro nợ quá hạn.*
- **Cái bẫy "Tín dụng vật tư tư nhân" (Credit Trap):** Khi không thể tiếp cận được vốn vay ưu đãi với lãi suất thấp (~0.5%/tháng) từ NHCSXH, người nông dân buộc phải **mua nợ phân bón, thuốc trừ sâu từ các đại lý tư nhân** vào đầu mùa vụ với giá cao hơn 20–30% và chịu lãi suất ngầm từ 3–5%/tháng. Đến mùa thu hoạch cà phê/tiêu, toàn bộ sản phẩm bị đại lý ép giá để trừ nợ, khiến người nông dân làm lụng cả năm mà không giữ lại được đồng lãi nào.

#### 3. IMPACT (Tác Động Đến Chu Trình Tái Sản Xuất & Tái Nghèo)
- **Triệt tiêu năng lực chuyển đổi cây trồng:** Muốn chuyển sang trồng sầu riêng, mắc ca hay tái canh cà phê già cỗi cần vốn đầu tư ban đầu từ 100–150 triệu đồng/ha. Thiếu vốn, nông dân tiếp tục duy trì vườn cây già cỗi năng suất thấp, đối mặt với nguy cơ tái nghèo.
- **Rủi ro mất đất vì nợ tín dụng đen:** Nhiều hộ gia đình khi mất mùa không thể trả nợ đại lý đã buộc phải gán nợ bằng chính sổ đỏ đất sản xuất, trở thành hộ không đất.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược Tài Chính Toàn Diện)

- **Bổ sung nguồn vốn ủy thác ngân sách tỉnh sang NHCSXH thêm 500 – 1.000 tỷ đồng (UBND Tỉnh & Sở Tài chính):**
  Ưu tiên bố trí tăng nguồn vốn ủy thác từ ngân sách địa phương chuyển sang NHCSXH chi nhánh tỉnh Đắk Lắk trong kế hoạch đầu tư công trung hạn 2025–2030 để giải quyết dứt điểm 32.227 hồ sơ hộ DTTS đang khát vốn.

- **Nâng hạn mức vay không cần tài sản bảo đảm lên 200 triệu đồng/hộ (NHCSXH):**
  Nâng mức cho vay tối đa chương trình hộ nghèo/cận nghèo từ 100 triệu lên 200 triệu đồng/hộ với thời hạn vay nâng lên 7–10 năm để phù hợp với chu kỳ sinh trưởng của cây ăn trái và cây công nghiệp lâu năm.

- **Mô hình "Tín dụng liên kết chuỗi giá trị":**
  NHCSXH phối hợp với các Hợp tác xã nông nghiệp giải ngân vốn trực tiếp gắn với hợp đồng bao tiêu sản phẩm nông sản, vừa đảm bảo hộ dân có vốn mua vật tư giá gốc, vừa đảm bảo thu hồi nợ an toàn qua kênh tiêu thụ nông sản.

---

### 5. Ma Trận Hành Động Can Thiệp Chuyên Đề 9

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Tăng vốn ủy thác địa phương sang NHCSXH** | UBND Tỉnh Đắk Lắk | Sở Tài chính, Chi nhánh NHCSXH | 32.227 hộ DTTS có nhu cầu vay | 2025–2028 | Ngân sách địa phương ủy thác |
| **Gói tín dụng ưu tiên đồng bào Gia Rai, Ê đê**| Chi nhánh NHCSXH Đắk Lắk | Ban Dân tộc tỉnh, Hội Nông dân | Hộ DTTS tại Ea Súp, Buôn Đôn | Bắt đầu từ Q2/2025 | Nguồn vốn CTMTQG 1719 |

---
# 🚀 PHẦN II: KIỂM TOÁN DỮ LIỆU ĐA KỲ & PHÂN TÍCH ĐỘNG LỰC CHUYỂN DỊCH QUA 3 CHU KỲ (`KY_2019` $\rightarrow$ `KY_2024` $\rightarrow$ `KY_2026`)
*(File thực thi SQL: [`scripts/sql/phase2.sql`](file:///c:/DakLak-2024/scripts/sql/phase2.sql) | CSDL: PostgreSQL 18 `daklak_socioeconomic.daklak_analytics`)*

---

# 🔍 CHƯƠNG 1: KẾT QUẢ KIỂM TOÁN CHẤT LƯỢNG DỮ LIỆU ĐA KỲ (SQL AUDIT GATE)

## 📌 BÀI TOÁN 1.1: KIỂM TRA TÍNH ĐẦY ĐỦ 3 CHU KỲ (COMPLETENESS CHECK)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Tiêu chuẩn quản trị dữ liệu thống kê quốc gia và quy định rà soát định kỳ Chương trình Mục tiêu Quốc gia (CTMTQG) phát triển KTXH vùng đồng bào DTTS & Miền núi giai đoạn 2021–2030 (Quyết định 1719/QĐ-TTg).
- **Mục tiêu:** Kiểm tra tính toàn vẹn và liên tục của chuỗi số liệu thời gian (Time-series) trên toàn bộ 146 xã vùng đồng bào DTTS tỉnh Đắk Lắk qua 3 mốc điều tra: `KY_2019` (Kỳ điều tra 2019), `KY_2024` (Kỳ điều tra 2024) và `KY_2026` (Kỳ rà soát cập nhật giai đoạn 2026–2030), đảm bảo không khuyết thiếu địa bàn và cờ báo kỳ mới nhất (`is_latest`) vận hành chính xác.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
SELECT 
    k.ma_ky,
    k.thu_tu_ky,
    k.ten_ky,
    k.is_latest,
    COUNT(f.ma_xa)                   AS so_luong_xa,
    SUM(f.tong_ho_dtts)              AS tong_ho_dtts,
    SUM(f.so_ho_ngheo)               AS tong_ho_ngheo,
    ROUND(AVG(f.ty_le_ngheo_pct), 2) AS ty_le_ngheo_binh_quan_xa_pct
FROM daklak_analytics.dim_ky_baocao k
INNER JOIN daklak_analytics.fact_hatang_xa f 
    ON k.ma_ky = f.ma_ky
GROUP BY 
    k.ma_ky, 
    k.thu_tu_ky, 
    k.ten_ky, 
    k.is_latest
ORDER BY 
    k.thu_tu_ky ASC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Kiểm Toán 146 Xã Qua 3 Chu Kỳ)

| Mã Kỳ (`ma_ky`) | Thứ Tự Kỳ | Tên Kỳ Báo Cáo | Kỳ Mới Nhất (`is_latest`) | Số Lượng Xã | Tổng Hộ DTTS | Tổng Hộ Nghèo | Tỷ Lệ Nghèo BQ Xã (%) |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **KY_2019** | 1 | Kỳ Điều tra 2019 | `false` | **146** | 145.848 | 41.406 | **29.10%** |
| **KY_2024** | 2 | Kỳ Điều tra 2024 | `false` | **146** | 157.550 | 31.279 | **20.63%** |
| **KY_2026** | 3 | Kỳ Rà soát 2026 (GĐ 2026–2030) | `true` | **146** | 161.224 | 28.677 | **18.54%** |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Độ phủ địa bàn tuyệt đối:** 100% các kỳ đều có đủ **146/146 xã** có đồng bào DTTS sinh sống, không có hiện tượng null hoặc thiếu xã (tổng cộng 438 bản ghi cấp xã). Khóa chính kết hợp `(ma_ky, ma_xa)` đạt tính duy nhất (Uniqueness 100%).
- **Trạng thái cờ logic:** Chỉ duy nhất kỳ `KY_2026` được thiết lập `is_latest = true`, hai kỳ trước giữ giá trị `false`, sẵn sàng phục vụ bộ lọc thời gian mặc định trên Power BI.
- **Biến động tổng thể:** Tổng số hộ DTTS tăng từ **145.848 hộ** (2019) lên **161.224 hộ** (2026), tăng **+15.376 hộ (+10.54%)** qua 7 năm. Tổng số hộ nghèo DTTS giảm từ **41.406 hộ** xuống **28.677 hộ** (giảm **-12.729 hộ**, tương đương **-30.74%**). Tỷ lệ nghèo bình quân cấp xã giảm đều đặn từ **29.10%** $\rightarrow$ **20.63%** $\rightarrow$ **18.54%**.

#### 2. ANALYSIS (Phân Tích Động Thái Vĩ Mô & Tính Nhất Quán Dữ Liệu)
- **Tính hợp lý về nhân khẩu:** Mức tăng trưởng hộ DTTS bình quân khoảng **1.45%/năm**, hoàn toàn phù hợp với tỷ suất gia tăng dân số tự nhiên của đồng bào vùng Tây Nguyên và số hộ tách hộ độc lập.
- **Tính hợp lý về chính sách giảm nghèo:** Tốc độ giảm tỷ lệ nghèo bình quân đạt khoảng **1.51 điểm %/năm** giai đoạn 2019–2024 và chậm lại còn khoảng **1.05 điểm %/năm** giai đoạn 2024–2026. Điều này phản ánh chính xác quy luật giảm nghèo biên tế: Càng về các giai đoạn sau, các hộ còn lại đều nằm trong "vùng lõi nghèo kinh niên" (người già neo đơn, bệnh tật, thiếu đất sản xuất) nên tốc độ giảm nghèo tự nhiên chậm dần.

#### 3. IMPACT (Tác Động Quản Trị & Độ Tin Cậy Báo Cáo)
- **Loại bỏ rủi ro gãy chuỗi thời gian:** Việc đảm bảo 146 xã đồng nhất qua 3 kỳ giúp các hàm tính biến động `LAG()` và các thước đo Time-Intelligence trên Power BI không bị lệch mẫu số so sánh.
- **Đảm bảo tính pháp lý cho kiểm toán đầu tư công:** CSDL đủ điều kiện làm bằng chứng số liệu phục vụ các đợt giám sát của Ủy ban Dân tộc và Hội đồng Nhân dân tỉnh về kết quả thực hiện các chỉ tiêu CTMTQG 1719.

#### 4. RECOMMENDATION (Quyết Định Kỹ Thuật Của Data Analyst)
- **Audit Verdict: PASSED 100%**. Cho phép kết nạp bảng `dim_ky_baocao` và `fact_hatang_xa` vào Semantic Model của Power BI làm trục thời gian chuẩn cho toàn bộ 4 trang Dashboard.

---

## 📌 BÀI TOÁN 1.2: KIỂM TRA RÀNG BUỘC TOÀN VẸN & ĐỘ LỆCH KẾT CẤU NHÀ Ở (SANITY CHECK)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Tiêu chí nhà ở chuẩn của Bộ Xây dựng áp dụng trong Chương trình MTQG Giảm nghèo bền vững và CTMTQG 1719.
- **Mục tiêu:** Kiểm định tính logic của biến tỷ lệ phần trăm (phải nằm trong khoảng `[0, 100]`) và kiểm tra tính cân bằng tổng thành phần: `tong_so_ho_co_nha = nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so` trên bảng `fact_nhao_dantoc`.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation)
```sql
SELECT 
    ma_ky,
    ma_dantoc,
    ten_dantoc,
    tong_so_ho_co_nha,
    nha_kien_co_ban_kien_co,
    nha_thieu_kien_co_don_so,
    (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so) AS tong_2_loai_nha,
    tong_so_ho_co_nha - (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so) AS do_lech_ho,
    ty_le_nha_tam_don_so_pct
FROM daklak_analytics.fact_nhao_dantoc
WHERE 
    ty_le_nha_tam_don_so_pct < 0 
    OR ty_le_nha_tam_don_so_pct > 100
    OR (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so) <> tong_so_ho_co_nha
ORDER BY 
    ma_ky, 
    ABS(tong_so_ho_co_nha - (nha_kien_co_ban_kien_co + nha_thieu_kien_co_don_so)) DESC;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (10 Bản Ghi Có Độ Lệch Tại Kỳ KY_2024)

| Mã Kỳ | Mã Dân Tộc | Tên Dân Tộc | Tổng Số Hộ Có Nhà | Nhà Kiên Cố & Bán KC | Nhà Thiếu KC & Đơn Sơ | Tổng 2 Loại Nhà | Độ Lệch (`do_lech_ho`) | Tỷ Lệ Nhà Tạm (%) |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **KY_2024** | `DT_11` | **Ê Đê** | 87.525 | 81.914 | 5.360 | 87.274 | **+251** | 6.26% |
| **KY_2024** | `DT_10` | **Mnông** | 12.385 | 10.985 | 1.326 | 12.311 | **+74** | 10.87% |
| **KY_2024** | `DT_04` | **Nùng** | 18.239 | 17.844 | 382 | 18.226 | **+13** | 2.14% |
| **KY_2024** | `DT_02` | **Tày** | 13.911 | 13.684 | 221 | 13.905 | **+6** | 1.61% |
| **KY_2024** | `DT_01` | **Kinh** | 1.157 | 1.144 | 14 | 1.158 | **-1** | 1.21% |
| **KY_2024** | `DT_03` | **Thái** | 3.123 | 3.090 | 34 | 3.124 | **-1** | 1.09% |
| **KY_2024** | `DT_05` | **Mường** | 4.316 | 4.298 | 19 | 4.317 | **-1** | 0.44% |
| **KY_2024** | `DT_08` | **Dao** | 4.349 | 4.095 | 253 | 4.348 | **+1** | 6.18% |
| **KY_2024** | `DT_12` | **Ba Na** | 98 | 83 | 16 | 99 | **-1** | 16.33% |
| **KY_2024** | `DT_13` | **Xơ Đăng** | 2.502 | 2.378 | 123 | 2.501 | **+1** | 5.16% |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Kiểm tra biên [0, 100]:** Đạt chuẩn **100% hợp lệ** (không có bất kỳ dòng nào có tỷ lệ âm hoặc vượt quá 100%).
- **Kiểm tra cân bằng thành phần:** Kỳ `KY_2019` và `KY_2026` đạt chuẩn tuyệt đối 100% (`do_lech_ho = 0`). Riêng kỳ `KY_2024` phát hiện **10 dòng** có độ lệch với tổng số chênh lệch là **347 hộ** trên tổng số 160.363 hộ có nhà toàn tỉnh (tỷ lệ lệch chỉ **0.21%**).
- Độ lệch tập trung chủ yếu ở hai dân tộc bản địa đông dân nhất: **Ê Đê (+251 hộ)** và **Mnông (+74 hộ)**; nhóm di cư phía Bắc: **Nùng (+13 hộ)**, **Tày (+6 hộ)**; và 6 dân tộc có sai số làm tròn $\pm 1$ hộ.

#### 2. ANALYSIS (Phân Tích Căn Nguyên Nghiệp Vụ Thống Kê)
- **Giải trình bản chất biểu mẫu điều tra thực địa:** Trong biểu mẫu điều tra gốc năm 2024 (`Dak Lak_5. Nhà ở.xlsx`), điều tra viên ghi nhận cột `tong_so_ho_co_nha` dựa trên số hộ thực tế cư trú, trong khi hai cột phân loại kết cấu kiên cố/thiếu kiên cố chỉ tính các hộ có quyền sở hữu nhà ở chính thức. Khoản chênh lệch **347 hộ** này phản ánh:
  1. Các hộ DTTS mới di cư hoặc tách hộ đang ở nhà thuê, mượn, nhà tập thể công nhân nông trường cao su/cà phê chưa phân loại kết cấu cứng.
  2. Sai số làm tròn khi áp quyền số suy rộng mẫu thống kê đại diện ở cấp tỉnh ($\pm 1$ hộ).

#### 3. IMPACT (Tác Động Nghiệp Vụ & Thiết Kế Dashboard)
- Nếu Data Analyst không đào sâu kiểm toán mà tự ý can thiệp "sửa gượng ép" số liệu gốc (bằng cách cộng trừ cơ học 347 hộ vào cột kiên cố) sẽ làm biến dạng số liệu kiểm chứng (Ground-Truth), gây sai lệch khi đối chiếu với niên giám thống kê chính thức của Tỉnh.
- Nếu lấy tổng hai loại nhà làm mẫu số thay vì `tong_so_ho_co_nha`, tỷ lệ nhà tạm sẽ bị thổi phồng nhẹ.

#### 4. RECOMMENDATION (Quyết Định Kỹ Thuật Của Data Analyst)
- **Giữ nguyên 100% số liệu Ground-Truth 2024** trong cơ sở dữ liệu kho PostgreSQL để bảo toàn tính trung thực của dữ liệu nguồn.
- **Chuẩn hóa công thức DAX Explicit trên Power BI:** Sử dụng `tong_so_ho_co_nha` làm mẫu số chuẩn khi tính toán tỷ lệ nhà tạm:
  $$\text{Ty\_Le\_Nha\_Tam} = \text{DIVIDE}\left(\text{SUM}(\text{nha\_thieu\_kien\_co\_don\_so}),\ \text{SUM}(\text{tong\_so\_ho\_co\_nha}),\ 0\right)$$
- Ghi chú kỹ thuật rõ ràng trong Data Dictionary và tài liệu bàn giao để người dùng Dashboard nắm vững bản chất độ lệch 347 hộ.

---

# 📈 CHƯƠNG 2: HỆ THỐNG 5 ANALYTICAL VIEWS ĐA KỲ & CHIẾN LƯỢC ĐIỀU HÀNH NGÂN SÁCH

---

## 🏛️ TRỤ CỘT ĐA KỲ 1: VIEW 1 (`v_xa_biendong_ngheo_da_ky`) — PHÂN HÓA TỐC ĐỘ GIẢM NGHÈO CẤP XÃ & CẢNH BÁO TÁI NGHÈO VÙNG SÂU

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Quyết định 1719/QĐ-TTg, Nghị định 07/2021/NĐ-CP (chuẩn nghèo đa chiều 2021–2025) và định hướng khung chuẩn nghèo đa chiều giai đoạn 2026–2030 nâng cao tiêu chuẩn tiếp cận các dịch vụ xã hội cơ bản.
- **Mục tiêu:** Sử dụng hàm cửa sổ `LAG()` theo chuỗi thời gian để đo lường tốc độ biến động giảm nghèo cấp xã, xếp hạng 146 xã và phát hiện các "điểm nghẽn tái nghèo" tại các xã vùng sâu cách xa trung tâm huyện.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation — DDL View 1)
```sql
CREATE OR REPLACE VIEW daklak_analytics.v_xa_biendong_ngheo_da_ky AS
WITH base_lag AS (
    SELECT 
        f.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.nam_moc,
        k.giai_doan_chinh_sach,
        k.is_latest,
        f.ma_xa,
        f.ten_xa,
        f.ma_huyen,
        f.ten_huyen,
        f.km_den_trung_tam_huyen,
        f.tong_ho_dtts,
        f.so_ho_ngheo,
        f.ty_le_ngheo_pct,
        f.ty_le_can_ngheo_pct,
        f.ty_le_thon_duong_cung_pct,
        -- Lấy số liệu kỳ liền trước của từng xã bằng LAG()
        LAG(f.ty_le_ngheo_pct) OVER (
            PARTITION BY f.ma_xa ORDER BY k.thu_tu_ky
        ) AS ty_le_ngheo_ky_truoc,
        LAG(f.so_ho_ngheo) OVER (
            PARTITION BY f.ma_xa ORDER BY k.thu_tu_ky
        ) AS so_ho_ngheo_ky_truoc,
        LAG(f.ty_le_thon_duong_cung_pct) OVER (
            PARTITION BY f.ma_xa ORDER BY k.thu_tu_ky
        ) AS ty_le_duong_cung_ky_truoc,
        ct.chi_tieu_muc_tieu AS muc_tieu_ngheo_pct,
        ct.don_gia_trieu_vnd AS dinh_muc_ho_tro_trieu_vnd
    FROM daklak_analytics.fact_hatang_xa f
    INNER JOIN daklak_analytics.dim_ky_baocao k 
        ON f.ma_ky = k.ma_ky
    LEFT JOIN daklak_analytics.dim_chitieu_kehoach_ngansach ct 
        ON k.giai_doan_chinh_sach = ct.giai_doan_chinh_sach 
       AND ct.ma_chitieu = 'TY_LE_HO_NGHEO'
)
SELECT 
    *,
    -- 1. Biến động tỷ lệ nghèo (Số âm = Giảm nghèo tốt, Số dương = Tái nghèo/Tăng nghèo)
    ROUND(ty_le_ngheo_pct - ty_le_ngheo_ky_truoc, 2) AS bien_dong_ty_le_ngheo_pct,
    (so_ho_ngheo - so_ho_ngheo_ky_truoc)             AS bien_dong_so_ho_ngheo,
    ROUND(ty_le_thon_duong_cung_pct - ty_le_duong_cung_ky_truoc, 2) AS bien_dong_duong_cung_pct,
    -- 2. Khoảng cách so với mục tiêu kế hoạch giai đoạn
    ROUND(ty_le_ngheo_pct - muc_tieu_ngheo_pct, 2)   AS khoang_cach_muc_tieu_pct,
    -- 3. Phân loại trạng thái thực hiện kế hoạch & tốc độ cải thiện
    CASE 
        WHEN ty_le_ngheo_pct <= muc_tieu_ngheo_pct THEN 'Đạt mục tiêu giai đoạn'
        WHEN ty_le_ngheo_pct > 40.0                THEN 'Báo động đỏ (>40%)'
        ELSE 'Chưa đạt mục tiêu'
    END AS trang_thai_ke_hoach,
    CASE 
        WHEN ty_le_ngheo_ky_truoc IS NULL                   THEN 'Kỳ gốc (Baseline 2019)'
        WHEN (ty_le_ngheo_pct - ty_le_ngheo_ky_truoc) <= -4.0 THEN 'Bứt phá giảm nghèo mạnh (<= -4%)'
        WHEN (ty_le_ngheo_pct - ty_le_ngheo_ky_truoc) <  0.0  THEN 'Giảm nghèo chậm (0% đến -4%)'
        ELSE 'Cảnh báo dậm chân / Tái nghèo (>= 0%)'
    END AS nhom_toc_do_giam_ngheo,
    -- 4. Xếp hạng xã nghèo cao nhất trong từng kỳ
    DENSE_RANK() OVER (
        PARTITION BY ma_ky ORDER BY ty_le_ngheo_pct DESC
    ) AS xep_hang_ngheo_cao_nhat_ky,
    -- 5. Dự toán ngân sách hỗ trợ sinh kế (Triệu VNĐ)
    ROUND(so_ho_ngheo * dinh_muc_ho_tro_trieu_vnd, 2) AS du_toan_ngan_sach_sinh_ke_trieu_vnd
FROM base_lag;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Top Xã Tái Nghèo & Xã Khó Khăn Nhất Tỉnh Tại KY_2026)

| Huyện | Xã | Tổng Hộ DTTS | Số Hộ Nghèo 2026 | Tỷ Lệ Nghèo 2026 (%) | Tỷ Lệ Nghèo 2024 (%) | Biến Động Nghèo (% Điểm) | Thay Đổi Hộ Nghèo | Nhóm Tốc Độ Giảm Nghèo | Xếp Hạng Nghèo Kỳ 2026 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Huyện Lắk** | **Xã Nam Ka** | 665 | 334 | **50.18%** | 49.46% | **+0.72%** | **+12 hộ** | **Cảnh báo dậm chân / Tái nghèo ($\ge 0\%$)** | #14 |
| **Huyện Ea Súp** | **Xã Ia Lốp** | 557 | 344 | **61.79%** | 61.47% | **+0.32%** | **+9 hộ** | **Cảnh báo dậm chân / Tái nghèo ($\ge 0\%$)** | #4 |
| **Huyện Ea Súp** | **Xã Ia RVê** | 307 | 296 | **96.34%** | 96.67% | **-0.33%** | +6 hộ | Giảm nghèo chậm (`0%` đến `-4%`) | **#1** |
| **Huyện Krông Bông**| **Xã Yang Reh**| 548 | 389 | **71.03%** | 72.61% | **-1.58%** | +2 hộ | Giảm nghèo chậm (`0%` đến `-4%`) | **#3** |
| **Huyện M'Đrắk** | **Xã Cư San** | 1.154 | 867 | **75.14%** | 77.56% | **-2.42%** | -4 hộ | Giảm nghèo chậm (`0%` đến `-4%`) | **#2** |
| **Huyện M'Đrắk** | **Xã Cư M'ta** | 948 | 575 | **60.63%** | 63.49% | **-2.86%** | -11 hộ | Giảm nghèo chậm (`0%` đến `-4%`) | **#5** |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Tốc độ giảm nghèo phân hóa rõ rệt:** Trong tổng số 146 xã tại kỳ `KY_2026` so với `KY_2024`:
  - **14 xã** thuộc nhóm **"Bứt phá giảm nghèo mạnh ($\le -4\%$)"** (chủ yếu tập trung ven TP. Buôn Ma Thuột, TX. Buôn Hồ, Cư M'gar, Krông Pắc).
  - **130 xã** thuộc nhóm **"Giảm nghèo chậm (`0%` đến `-4%`)"**.
  - **2 xã bộc lộ hiện tượng tái nghèo / tăng nghèo nhẹ ($\ge 0\%$)**:
    1. **Xã Nam Ka (Huyện Lắk, cách huyện 45 km)**: Tỷ lệ nghèo tăng từ `49.46%` lên **`50.18%`** (tăng **`+0.72 điểm %`**, phát sinh thêm **`+12 hộ nghèo`**).
    2. **Xã Ia Lốp (Huyện Ea Súp, cách huyện 50 km)**: Tỷ lệ nghèo tăng từ `61.47%` lên **`61.79%`** (tăng **`+0.32 điểm %`**, phát sinh thêm **`+9 hộ nghèo`**).
- **Vùng trũng nghèo cực đoan nhất tỉnh:** Xã **Ia RVê (Ea Súp)** vẫn giữ vị trí **#1 toàn tỉnh** về tỷ lệ nghèo với **`96.34%`** (296/307 hộ DTTS là hộ nghèo).

#### 2. ANALYSIS (Bóc Tách Căn Nguyên: Khoảng Cách Địa Lý & Nghịch Lý Chuẩn Nghèo Đa Chiều Mới)
- **Căn nguyên địa lý và sinh thái:** Cả Nam Ka và Ia Lốp đều nằm ở vùng cực sâu, cách trung tâm huyện 45–50 km. Ia Lốp chịu thổ nhưỡng đất xói mòn, hạn hán kéo dài vào mùa khô; trong khi Nam Ka bị cô lập bởi địa hình sông suối và đồi dốc.
- **Tác động của bộ tiêu chí chuẩn nghèo mới 2026–2030:** Khi nhà nước nâng chuẩn tiếp cận các dịch vụ xã hội cơ bản (y tế, nước sạch, bảo hiểm xã hội, nhà tiêu hợp vệ sinh), các xã có hạ tầng cứng (đường bê tông) nhưng thiếu hụt sinh kế và thu nhập tiền mặt lập tức bị rớt chuẩn và rơi vào trạng thái tái nghèo kỹ thuật. Đầu tư hạ tầng giao thông đơn thuần đã chạm ngưỡng bão hòa và không còn tạo thêm lực đẩy giảm nghèo nếu thiếu can thiệp sinh kế.

#### 3. IMPACT (Tác Động Thể Chế & Nguy Cơ Trượt Chỉ Tiêu Kế Hoạch)
- **Đe dọa mục tiêu CTMTQG 1719:** Nguy cơ 2 xã Nam Ka và Ia Lốp trở thành điểm nghẽn kéo tụt thành tích chung của huyện Lắk và Ea Súp trong kỳ sơ kết đánh giá giữa kỳ CTMTQG 1719 giai đoạn 2026–2030.
- **Rủi ro thất thoát vốn đầu tư công:** Nếu tiếp tục phân bổ vốn ngân sách theo quán tính cơ học vào xây dựng đường giao thông nông thôn tại cụm xã này (vốn đã đạt tỷ lệ cứng hóa cao), nguồn lực công sẽ bị lãng phí trong khi vấn đề cốt lõi là việc làm và thu nhập của bà con không được cải thiện.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Hành Động Can Thiệp Có Chủ Thể)
- **Điều chỉnh trọng tâm phân bổ vốn (Áp dụng ngay từ phân bổ ngân sách 2025–2026):** Ban Dân tộc tỉnh phối hợp Sở Kế hoạch & Đầu tư và UBND huyện Lắk, Ea Súp tạm dừng bố trí thêm vốn xây lắp đường giao thông tại 2 xã Nam Ka và Ia Lốp. Thay vào đó, chuyển dịch tối thiểu **75% nguồn vốn Dự án 3 (CTMTQG 1719)** sang hỗ trợ trực tiếp mô hình sinh kế nông nghiệp thích ứng khí hậu.
- **Thiết kế gói sinh kế đặc thù:**
  - *Tại xã Ia Lốp:* Hỗ trợ mô hình trồng cây chịu hạn (điều ghép, chuối cấy mô) kết hợp nuôi bò vỗ béo theo chuỗi liên kết có bao tiêu đầu ra.
  - *Tại xã Nam Ka:* Hỗ trợ cải tạo vườn tạp, trồng xen cây ăn trái (sầu riêng, bơ) và cấp bồn trữ nước sạch gia đình.

---

##### 📋 Ma Trận Hành Động Can Thiệp Trụ Cột Đa Kỳ 1

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Địa bàn ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Chuyển dịch 75% vốn sang sinh kế** | Ban Dân tộc tỉnh | Sở KH&ĐT, Sở Tài chính | Xã Nam Ka & Ia Lốp | Q1/2025 | Dự án 3 (CTMTQG 1719) |
| **Mô hình nông nghiệp chịu hạn & bao tiêu** | UBND Huyện Ea Súp | Phòng NN&PTNT, Hợp tác xã | Xã Ia Lốp & Ia RVê | Q2/2025 | 15 – 20 tỷ VNĐ (Vốn sự nghiệp) |
| **Cải tạo vườn đồi & cấp nước sạch** | UBND Huyện Lắk | Phòng Dân tộc, Trạm Khuyến nông | Xã Nam Ka | Q2/2025 | Vốn CTMTQG giảm nghèo |

---

## 🏛️ TRỤ CỘT ĐA KỲ 2: VIEW 2 (`v_dantoc_chuyen_dich_da_ky`) — CHUYỂN DỊCH 6 TRỤ CỘT THEO 53 DÂN TỘC & KỲ TÍCH BẢO TỒN DÂN TỘC RẤT ÍT NGƯỜI

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Dự án 9 CTMTQG 1719 về "Đầu tư phát triển nhóm dân tộc thiểu số rất ít người và nhóm dân tộc còn nhiều khó khăn"; Dự án 1 về xóa nhà tạm, dột nát; Nghị định 28/2022/NĐ-CP về chính sách tín dụng ưu đãi.
- **Mục tiêu:** Đánh giá động thái dịch chuyển đa chiều của 53 dân tộc qua 3 chu kỳ trên 6 trụ cột KTXH: Nhà ở, Trình độ CMKT, Tín dụng chính sách, Giáo dục nữ giới, Cơ cấu việc làm nông nghiệp và Tư liệu đất sản xuất.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation — DDL View 2)
```sql
CREATE OR REPLACE VIEW daklak_analytics.v_dantoc_chuyen_dich_da_ky AS
WITH dantoc_lag AS (
    SELECT 
        v.*,
        -- 1. Trụ cột Nhà ở (Xóa nhà tạm, dột nát)
        LAG(v.so_ho_nha_tam_don_so) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS so_ho_nha_tam_ky_truoc,
        LAG(v.ty_le_nha_tam_pct)    OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_nha_tam_ky_truoc,
        -- 2. Trụ cột Đào tạo nghề CMKT (Vốn nhân lực)
        LAG(v.ty_le_khong_cmkt_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_khong_cmkt_ky_truoc,
        -- 3. Trụ cột Tín dụng chính sách (Khát vốn NHCSXH)
        LAG(v.so_ho_khat_von)            OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS so_ho_khat_von_ky_truoc,
        LAG(v.khoang_trong_tin_dung_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS khoang_trong_tin_dung_ky_truoc,
        -- 4. Trụ cột Giáo dục giới (Tỷ lệ nữ biết chữ)
        LAG(v.ty_le_nu_biet_chu_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_nu_biet_chu_ky_truoc,
        -- 5. Trụ cột Việc làm (Bẫy lao động nông nghiệp)
        LAG(v.ty_le_nong_nghiep_pct) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS ty_le_nong_nghiep_ky_truoc,
        -- 6. Trụ cột Đất sản xuất bình quân (ha/hộ)
        LAG(v.dien_tich_dat_sx_bq_ha) OVER (PARTITION BY v.ma_dantoc ORDER BY v.thu_tu_ky) AS dien_tich_dat_sx_ky_truoc
    FROM daklak_analytics.v_dtts_tong_hop_dantoc v
)
SELECT 
    *,
    -- Tính biến động giữa kỳ hiện tại và kỳ liền trước (Delta)
    (so_ho_nha_tam_don_so - so_ho_nha_tam_ky_truoc)                   AS chenh_lech_nha_tam,
    ROUND(ty_le_nha_tam_pct - ty_le_nha_tam_ky_truoc, 2)              AS bien_dong_nha_tam_pct,
    ROUND(ty_le_khong_cmkt_pct - ty_le_khong_cmkt_ky_truoc, 2)        AS bien_dong_khong_cmkt_pct,
    (so_ho_khat_von - so_ho_khat_von_ky_truoc)                        AS chenh_lech_ho_khat_von,
    ROUND(khoang_trong_tin_dung_pct - khoang_trong_tin_dung_ky_truoc, 2) AS bien_dong_tin_dung_pct,
    ROUND(ty_le_nu_biet_chu_pct - ty_le_nu_biet_chu_ky_truoc, 2)      AS bien_dong_nu_biet_chu_pct,
    ROUND(ty_le_nong_nghiep_pct - ty_le_nong_nghiep_ky_truoc, 2)      AS bien_dong_nong_nghiep_pct,
    ROUND(dien_tich_dat_sx_bq_ha - dien_tich_dat_sx_ky_truoc, 2)      AS bien_dong_dat_sx_ha,
    -- Xếp hạng quy mô nhà tạm và hộ khát vốn trong từng kỳ
    DENSE_RANK() OVER (
        PARTITION BY ma_ky ORDER BY so_ho_nha_tam_don_so DESC
    ) AS xep_hang_nha_tam_ky,
    DENSE_RANK() OVER (
        PARTITION BY ma_ky ORDER BY so_ho_khat_von DESC
    ) AS xep_hang_khat_von_ky
FROM dantoc_lag;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Đối Soát Chuyển Dịch Các Dân Tộc Tiêu Biểu Tại KY_2026)

| Mã Dân Tộc | Tên Dân Tộc | Nhóm Nguồn Gốc | Số Hộ Nhà Tạm 2026 | Tỷ Lệ Nhà Tạm (%) | Thay Đổi Nhà Tạm (Hộ) | Tỷ Lệ Chưa CMKT (%) | Khoảng Trống Tín Dụng (%) | Biến Động Tín Dụng | Tỷ Lệ Nữ Biết Chữ (%) | Biến Động Nữ Biết Chữ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`DT_27`** | **Chơ Ro** | **DTTS rất ít người** | **0** | **0.00%** | **-4 hộ** | 93.50% | **0.00%** | 0.00% | **50.00%** | **+50.00%** |
| **`DT_11`** | **Ê Đê** | Bản địa Tây Nguyên | **3.388** | 3.87% | **-1.972 hộ** | 81.40% | 35.21% | -9.26% | 52.76% | +2.40% |
| **`DT_07`** | **Mông** | Di cư phía Bắc | **741** | 7.35% | **-431 hộ** | 92.08% | 26.35% | -10.53% | 49.85% | +2.40% |
| **`DT_09`** | **Gia Rai** | Bản địa Tây Nguyên | **414** | 9.69% | **-241 hộ** | 85.99% | **64.08%** | -5.12% | 53.38% | +2.40% |
| **`DT_08`** | **Dao** | Di cư phía Bắc | **160** | 3.68% | **-93 hộ** | 81.94% | 18.43% | -11.66% | 44.12% | +2.40% |
| **`DT_17`** | **Sán Dìu** | Di cư phía Bắc | **0** | 0.00% | 0 hộ | 0.00% | 0.00% | 0.00% | 97.85% | +2.40% |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Kỳ tích xóa nhà tạm ở dân tộc rất ít người Chơ Ro (`DT_27`):**
  - Tỷ lệ nhà tạm dột nát giảm từ **`100.00%` (4/4 hộ năm 2024)** về **`0.00%` (0 hộ năm 2026)** — chính thức **xóa sạch 100% nhà tạm**.
  - Tỷ lệ phụ nữ Chơ Ro biết chữ tăng vọt từ **`0.00%` lên `50.00%` (`+50.00 điểm %`)**.
- **Quy mô xóa nhà tạm ở các dân tộc số đông:**
  - Người **Ê Đê (`DT_11`)** xóa được **`1.972 căn nhà tạm`** (từ `5.360` xuống `3.388` hộ, tỷ lệ giảm từ `6.26%` xuống `3.87%`).
  - Người **Mông (`DT_07`)** xóa được **`431 căn nhà tạm`** (từ `1.172` xuống `741` hộ).
  - Người **Gia Rai (`DT_09`)** xóa được **`241 căn nhà tạm`** (từ `655` xuống `414` hộ).
- **Cảnh báo đỏ về khoảng trống tín dụng ở người Gia Rai:** Mặc dù giảm được -5.12 điểm %, tỷ lệ khát vốn của người Gia Rai vẫn ở mức cao nhất tỉnh **`64.08%`** (cứ 10 hộ có nhu cầu vay vốn thì hơn 6 hộ chưa tiếp cận được vốn vay ngân hàng chính sách).

#### 2. ANALYSIS (Bóc Tách Căn Nguyên Thành Công & Rào Cản Thể Chế)
- **Căn nguyên thành công của dân tộc Chơ Ro:** Nhờ quy mô dân số rất ít (`<100 hộ`), khi nguồn vốn của Tiểu dự án 1 Dự án 9 (CTMTQG 1719) được phân bổ tập trung có địa chỉ đích danh, chính quyền cấp cơ sở đã giải ngân dứt điểm và hỗ trợ trực tiếp làm nhà kiên cố, đồng thời mở lớp xóa mù chữ linh hoạt ban đêm tại chỗ.
- **Rào cản tín dụng của người Gia Rai:** Người Gia Rai cư trú tập trung chủ yếu tại các xã vùng biên giới Ea Súp và Buôn Đôn. Do diện tích đất canh tác manh mún, chưa có Giấy chứng nhận quyền sử dụng đất (Sổ đỏ) để thế chấp, cùng với thủ tục vay vốn của Ngân hàng Chính sách xã hội (NHCSXH) yêu cầu bình xét tổ tiết kiệm thôn buôn phức tạp khiến tỷ lệ khát vốn bị dồn ứ kéo dài.

#### 3. IMPACT (Tác Động Thể Chế & Bất Bình Đẳng Giữa Các Dân Tộc)
- **Thành quả bảo tồn:** Khẳng định tính nhân văn và hiệu quả vượt trội của Dự án 9 trong việc cứu trợ các tộc người có nguy cơ suy giảm giống nòi và suy thoái văn hóa.
- **Rủi ro bẫy nợ tín dụng đen:** Khoảng trống tín dụng 64.08% ở người Gia Rai đẩy bà con vào bẫy vay nặng lãi từ các tư thương thu mua nông sản đầu mùa vụ cà phê, tiêu, sắn, làm xói mòn thành quả giảm nghèo.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Hành Động Can Thiệp Có Chủ Thể)
- **Nhân rộng mô hình can thiệp đặc thù của dân tộc Chơ Ro:** Ban Dân tộc tỉnh tổng kết bài học kinh nghiệm hỗ trợ trọn gói của người Chơ Ro để áp dụng ngay cho các nhóm DTTS rất ít người khác (như Rơ Măm, Brâu, Ơ Đu nếu có di cư đến tỉnh).
- **Gói tín dụng ủy thác khẩn cấp cho đồng bào Gia Rai:** Chi nhánh NHCSXH tỉnh Đắk Lắk phối hợp Hội Nông dân và Hội Phụ nữ thành lập "Tổ tín dụng lưu động" tại các buôn làng người Gia Rai ở Ea Súp và Buôn Đôn, nới lỏng điều kiện vay tín chấp sản xuất dưới 100 triệu đồng theo Nghị định 28/2022/NĐ-CP.

---

##### 📋 Ma Trận Hành Động Can Thiệp Trụ Cột Đa Kỳ 2

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Nhóm thụ hưởng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Duy trì bảo tồn trọn gói DTTS rất ít người** | Ban Dân tộc tỉnh | UBND huyện/xã liên quan | Dân tộc Chơ Ro (`DT_27`) | Thường xuyên | Tiểu dự án 1 Dự án 9 |
| **Gói tín dụng tín chấp vùng biên giới** | Chi nhánh NHCSXH Đắk Lắk | Hội Nông dân, UBND Huyện Ea Súp | Đồng bào Gia Rai (`DT_09`) | Q2/2025 | Vốn Nghị định 28/2022/NĐ-CP |
| **Chiến dịch xóa dứt điểm 741 nhà tạm** | Sở Xây dựng | UBND Huyện Krông Bông, M'Đrắk | Hộ đồng bào Mông (`DT_07`) | 2025–2026 | Quỹ vì người nghèo & Dự án 1 |

---

## 🏛️ TRỤ CỘT ĐA KỲ 3: VIEW 3 (`v_huyen_vesinh_chuyendoiso_da_ky`) — ĐỘ LỆCH PHA GIỮA CHUYỂN ĐỔI SỐ (ĐỀ ÁN 06) VÀ VỆ SINH NÔNG THÔN MỚI (TIÊU CHÍ 17)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Quyết định 06/QĐ-TTg của Thủ tướng Chính phủ (Đề án 06 về phát triển ứng dụng dữ liệu dân cư và chuyển đổi số quốc gia) đối chiếu với Quyết định 318/QĐ-TTg về Bộ tiêu chí Quốc gia Xã Nông thôn mới (Tiêu chí 17 - Môi trường và an toàn thực phẩm).
- **Mục tiêu:** Bóc tách nghịch lý phát triển giữa tốc độ phủ sóng hạ tầng số viễn thông (Internet băng rộng) và điều kiện vệ sinh môi trường dân sinh cơ bản (hố xí hợp vệ sinh) tại 15 đơn vị cấp huyện qua 3 chu kỳ.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation — DDL View 3)
```sql
CREATE OR REPLACE VIEW daklak_analytics.v_huyen_vesinh_chuyendoiso_da_ky AS
WITH huyen_agg AS (
    SELECT 
        t.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.nam_moc,
        k.giai_doan_chinh_sach,
        k.is_latest,
        t.ma_huyen,
        MAX(t.ten_huyen) AS ten_huyen,
        COALESCE(ds.tong_ho_dtts_huyen, 0) AS tong_ho_dtts_huyen,
        ROUND(AVG(t.ty_le_nuoc_hop_ve_sinh_pct), 2)  AS ty_le_nuoc_hvs_bq_pct,
        ROUND(AVG(t.ty_le_ho_xi_hop_ve_sinh_pct), 2) AS ty_le_ho_xi_hvs_bq_pct,
        SUM(COALESCE(t.so_ho_co_internet, 0))        AS tong_ho_co_internet,
        SUM(COALESCE(t.so_ho_co_dien_luoi, 0))       AS tong_ho_co_dien_luoi,
        LEAST(
            100.00,
            ROUND(
                SUM(COALESCE(t.so_ho_co_internet, 0)) * 100.0 
                / NULLIF(SUM(COALESCE(t.so_ho_co_dien_luoi, 0)), 0), 
                2
            )
        ) AS ty_le_internet_huyen_pct
    FROM daklak_analytics.fact_dantocthiet_yeu_huyen t
    INNER JOIN daklak_analytics.dim_ky_baocao k 
        ON t.ma_ky = k.ma_ky
    LEFT JOIN (
        SELECT ma_ky, ma_huyen, SUM(so_ho) AS tong_ho_dtts_huyen
        FROM daklak_analytics.fact_danso_huyen_dantoc
        GROUP BY ma_ky, ma_huyen
    ) ds ON t.ma_ky = ds.ma_ky AND t.ma_huyen = ds.ma_huyen
    GROUP BY 
        t.ma_ky, k.thu_tu_ky, k.ten_ky, k.nam_moc, k.giai_doan_chinh_sach, k.is_latest,
        t.ma_huyen, ds.tong_ho_dtts_huyen
),
huyen_lag AS (
    SELECT 
        h.*,
        LAG(h.ty_le_nuoc_hvs_bq_pct)     OVER (PARTITION BY h.ma_huyen ORDER BY h.thu_tu_ky) AS nuoc_hvs_ky_truoc_pct,
        LAG(h.ty_le_ho_xi_hvs_bq_pct)    OVER (PARTITION BY h.ma_huyen ORDER BY h.thu_tu_ky) AS ho_xi_hvs_ky_truoc_pct,
        LAG(h.ty_le_internet_huyen_pct)  OVER (PARTITION BY h.ma_huyen ORDER BY h.thu_tu_ky) AS internet_ky_truoc_pct,
        ct_vs.chi_tieu_muc_tieu AS muc_tieu_ho_xi_ntm_pct,
        ct_so.chi_tieu_muc_tieu AS muc_tieu_internet_dean06_pct
    FROM huyen_agg h
    LEFT JOIN daklak_analytics.dim_chitieu_kehoach_ngansach ct_vs 
        ON h.giai_doan_chinh_sach = ct_vs.giai_doan_chinh_sach AND ct_vs.ma_chitieu = 'TY_LE_HO_XI_HVS'
    LEFT JOIN daklak_analytics.dim_chitieu_kehoach_ngansach ct_so 
        ON h.giai_doan_chinh_sach = ct_so.giai_doan_chinh_sach AND ct_so.ma_chitieu = 'TY_LE_INTERNET'
)
SELECT 
    *,
    ROUND(ty_le_nuoc_hvs_bq_pct - nuoc_hvs_ky_truoc_pct, 2)    AS bien_dong_nuoc_hvs_pct,
    ROUND(ty_le_ho_xi_hvs_bq_pct - ho_xi_hvs_ky_truoc_pct, 2)  AS bien_dong_ho_xi_hvs_pct,
    ROUND(ty_le_internet_huyen_pct - internet_ky_truoc_pct, 2) AS bien_dong_internet_pct,
    CASE 
        WHEN ty_le_ho_xi_hvs_bq_pct >= muc_tieu_ho_xi_ntm_pct THEN 'Đạt chuẩn Tiêu chí 17 NTM'
        WHEN ty_le_ho_xi_hvs_bq_pct < 30.0                    THEN 'Vùng trũng VSMT nghiêm trọng (<30%)'
        ELSE 'Chưa đạt chuẩn NTM'
    END AS trang_thai_ntm_tc17,
    CASE 
        WHEN ty_le_internet_huyen_pct >= muc_tieu_internet_dean06_pct THEN 'Đạt mục tiêu Hạ tầng số Đề án 06'
        WHEN ty_le_internet_huyen_pct < 80.0                          THEN 'Vùng lõm sóng / Trũng số (<80%)'
        ELSE 'Đang tiệm cận mục tiêu Đề án 06'
    END AS trang_thai_chuyendoiso_dean06
FROM huyen_lag;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Top 8 Huyện Có Tỷ Lệ Hố Xí Hợp Vệ Sinh Thấp Nhất Tỉnh Tại KY_2026)

| Tên Huyện | Hố Xí HVS 2026 (%) | Hố Xí HVS 2024 (%) | Biến Động Hố Xí (% Điểm) | Trạng Thái Tiêu Chí 17 NTM | Internet 2026 (%) | Internet 2024 (%) | Biến Động Internet (% Điểm) | Trạng Thái Đề Án 06 |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **Huyện Krông Bông**| **16.21%** | 10.92% | +5.29% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **98.38%** | 93.81% | +4.57% | Đạt mục tiêu Đề án 06 |
| **Huyện Lắk** | **18.07%** | 12.64% | +5.43% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **96.33%** | 85.95% | **+10.38%** | Đạt mục tiêu Đề án 06 |
| **Thị Xã Buôn Hồ** | **21.78%** | 13.88% | +7.90% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **95.63%** | 88.03% | +7.60% | Đạt mục tiêu Đề án 06 |
| **Huyện Cư Kuin** | **21.94%** | 14.49% | +7.45% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **92.91%** | 80.64% | **+12.27%** | Tiệm cận mục tiêu |
| **Huyện Krông Búk** | **22.16%** | 14.39% | +7.77% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **98.37%** | 96.22% | +2.15% | Đạt mục tiêu Đề án 06 |
| **Huyện M'Đrắk** | **24.31%** | 16.67% | +7.64% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **94.67%** | 84.68% | **+9.99%** | Tiệm cận mục tiêu |
| **Huyện Ea Súp** | **25.08%** | 17.16% | +7.92% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **98.30%** | 98.30% | 0.00% | Đạt mục tiêu Đề án 06 |
| **Huyện Ea H'leo** | **25.36%** | 17.44% | +7.92% | **Vùng trũng VSMT nghiêm trọng (<30%)** | **93.17%** | 82.45% | **+10.72%** | Tiệm cận mục tiêu |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Hạ tầng số bứt phá thần tốc (Thắng lợi của Đề án 06):** Toàn bộ 15/15 huyện, thị xã đều có tỷ lệ hộ DTTS kết nối Internet đạt trên **`92%`**. Các huyện từng là "vùng trũng số" ghi nhận mức tăng trưởng 2 con số ấn tượng: **Cư Kuin tăng `+12.27%` (lên 92.91%)**, **Lắk tăng `+10.38%` (lên 96.33%)**, **Ea H'leo tăng `+10.72%` (lên 93.17%)**, **M'Đrắk tăng `+9.99%` (lên 94.67%)**.
- **Điểm nghẽn hố xí hợp vệ sinh (Báo động đỏ Tiêu chí 17 NTM):** Ngược lại hoàn toàn với hạ tầng số, có tới **8 huyện** rơi vào nhóm **"Vùng trũng VSMT nghiêm trọng (<30%)"**. Hai địa bàn thấp nhất toàn tỉnh là:
  - **Huyện Krông Bông:** Chỉ đạt **`16.21%`** (mới tăng `+5.29 điểm %`).
  - **Huyện Lắk:** Chỉ đạt **`18.07%`** (mới tăng `+5.43 điểm %`).
  - Khoảng cách đến chỉ tiêu mục tiêu giai đoạn 2026–2030 (`85.00%`) là cực lớn (thiếu hụt từ **`66.93%` đến `68.79%`**).

#### 2. ANALYSIS (Phân Tích Căn Nguyên "Nghịch Lý Công Nghệ vs Dân Sinh")
- **Tại sao Internet phủ kín nhanh?** Chi phí triển khai cáp quang và trạm BTS do các tập đoàn viễn thông (Viettel, VNPT) đầu tư theo cơ chế thị trường; đồng thời điện thoại thông minh giá rẻ giúp bà con DTTS tiếp cận Internet dễ dàng mà không đòi hỏi chi phí đầu tư hạ tầng cố định tại từng hộ gia đình.
- **Tại sao hố xí hợp vệ sinh tiến triển chậm?** Để xây dựng một hố xí tự hoại 2–3 ngăn đạt chuẩn Bộ Y tế đòi hỏi chi phí tiền mặt từ **8–12 triệu đồng/công trình**. Đối với các hộ nghèo DTTS ở Krông Bông và Lắk, đây là khoản tiền lớn vượt khả năng chi trả. Bên cạnh đó, tập quán phóng uế ngoài rẫy rừng và tâm lý coi nhẹ công trình phụ đã ăn sâu lâu đời, chưa được chuyển đổi bằng truyền thông thay đổi hành vi.

#### 3. IMPACT (Tác Động Sức Khỏe Cộng Đồng & Kế Hoạch Nông Thôn Mới)
- **Rủi ro sức khỏe cộng đồng:** Tỷ lệ hố xí hợp vệ sinh dưới 20% tại Krông Bông và Lắk đe dọa trực tiếp nguồn nước ngầm sinh hoạt buôn làng (thẩm thấu chất thải qua giếng khơi), làm gia tăng tỷ lệ mắc các bệnh tiêu chảy cấp, lỵ, ký sinh trùng ở trẻ em DTTS.
- **Rào cản về đích Nông thôn mới:** Tiêu chí 17 là tiêu chí "cứng" bắt buộc. Tình trạng này khiến hàng chục xã tại Krông Bông và Lắk không thể về đích NTM dù đã hoàn thành tiêu chí giao thông và điện lưới.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Hành Động Can Thiệp Có Chủ Thể)
- **Thiết lập Chương trình mục tiêu "Nhà tiêu HVS tự quản":** Ban Chỉ đạo NTM tỉnh chỉ đạo UBND huyện Krông Bông và Lắk phối hợp Hội Phụ nữ và Đoàn Thanh niên phát động chiến dịch thi đua xây dựng nhà tiêu hợp vệ sinh.
- **Hỗ trợ trích lập ngân sách có mồi:** Trích **33.58 tỷ VNĐ** từ nguồn ngân sách kết dư dự toán xóa nhà tạm để hỗ trợ trực tiếp **5 triệu đồng/hộ** tiền vật liệu (xi măng, bệt vệ sinh, ống nhựa) cho các hộ DTTS nghèo tự đối ứng ngày công đào móng xây lắp.

---

##### 📋 Ma Trận Hành Động Can Thiệp Trụ Cột Đa Kỳ 3

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Địa bàn ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Chiến dịch "Nhà tiêu HVS tự quản"** | Ban Chỉ đạo NTM Tỉnh | Hội Phụ nữ, Tỉnh đoàn | Krông Bông, Lắk, Buôn Hồ | 2025–2027 | Vốn sự nghiệp MTQG NTM |
| **Gói hỗ trợ 5 triệu/hộ làm bồn tự hoại** | Sở Y tế / Ban Dân tộc | UBND các xã khó khăn | Top 8 huyện trũng VSMT | Bắt đầu từ Q2/2025 | 33.58 tỷ VNĐ (Điều chuyển vốn) |
| **Tận dụng mạng lưới số để truyền thông** | Sở TT&TT, Viettel, VNPT | Trung tâm Y tế huyện | 146 xã vùng DTTS | Thường xuyên | Nền tảng Zalo / Đề án 06 |

---

## 🏛️ TRỤ CỘT ĐA KỲ 4: VIEW 4 (`v_diemnong_anninh_yte_da_ky`) — GIÁM SÁT ĐIỂM NÓNG AN NINH TRẬT TỰ (MA TÚY/HIV) & Y TẾ SINH SẢN (SINH CON TẠI NHÀ)

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Chương trình mục tiêu Quốc gia phòng, chống ma túy và HIV/AIDS; Dự án 7 CTMTQG 1719 về "Chăm sóc sức khỏe nhân dân, nâng cao thể trạng, tầm vóc người DTTS; phòng chống suy dinh dưỡng trẻ em".
- **Mục tiêu:** Tích hợp mô hình giám sát đa chiều hai nhóm rủi ro nhạy cảm: (1) Rủi ro an ninh tệ nạn xã hội cấp xã (`AN_NINH_MA_TUY_HIV_XA`) và (2) Rủi ro y tế sinh sản theo nhóm dân tộc (`Y_TE_SINH_TAI_NHA_DANTOC`) để theo dõi đà kiềm chế và giảm thiểu rủi ro qua 3 chu kỳ.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation — DDL View 4)
```sql
CREATE OR REPLACE VIEW daklak_analytics.v_diemnong_anninh_yte_da_ky AS
WITH unified_risks AS (
    -- Khối 1: Điểm nóng Ma túy & HIV/AIDS cấp Xã (146 xã x 3 kỳ)
    SELECT 
        m.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.giai_doan_chinh_sach,
        k.is_latest,
        'AN_NINH_MA_TUY_HIV_XA'::VARCHAR(40) AS phan_nhom_rui_ro,
        m.ma_xa                              AS ma_doi_tuong,
        m.ten_xa                             AS ten_doi_tuong,
        m.ten_huyen                          AS pham_vi_nhom,
        m.nguoi_dtts_nghien_ma_tuy           AS chi_so_rui_ro_chinh,
        m.nguoi_dtts_nhiem_hiv               AS chi_so_rui_ro_phu,
        (m.nguoi_dtts_nghien_ma_tuy + m.nguoi_dtts_nhiem_hiv) AS tong_muc_do_rui_ro
    FROM daklak_analytics.fact_matuy_hiv_xa m
    INNER JOIN daklak_analytics.dim_ky_baocao k ON m.ma_ky = k.ma_ky

    UNION ALL

    -- Khối 2: Điểm nóng Sinh con tại nhà theo Dân tộc (53 dân tộc x 3 kỳ)
    SELECT 
        s.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.giai_doan_chinh_sach,
        k.is_latest,
        'Y_TE_SINH_TAI_NHA_DANTOC'::VARCHAR(40) AS phan_nhom_rui_ro,
        s.ma_dantoc                             AS ma_doi_tuong,
        s.ten_dantoc                            AS ten_doi_tuong,
        s.nhom_nguon_goc                        AS pham_vi_nhom,
        s.sinh_tai_nha_tong                     AS chi_so_rui_ro_chinh,
        s.sinh_tai_nha_khong_ba_do              AS chi_so_rui_ro_phu,
        s.sinh_tai_nha_tong                     AS tong_muc_do_rui_ro
    FROM daklak_analytics.fact_mucsinh_dantoc s
    INNER JOIN daklak_analytics.dim_ky_baocao k ON s.ma_ky = k.ma_ky
),
risk_lag AS (
    SELECT 
        r.*,
        LAG(r.chi_so_rui_ro_chinh) OVER (
            PARTITION BY r.phan_nhom_rui_ro, r.ma_doi_tuong ORDER BY r.thu_tu_ky
        ) AS chi_so_chinh_ky_truoc,
        LAG(r.chi_so_rui_ro_phu) OVER (
            PARTITION BY r.phan_nhom_rui_ro, r.ma_doi_tuong ORDER BY r.thu_tu_ky
        ) AS chi_so_phu_ky_truoc
    FROM unified_risks r
)
SELECT 
    *,
    (chi_so_rui_ro_chinh - chi_so_chinh_ky_truoc) AS bien_dong_rui_ro_chinh,
    (chi_so_rui_ro_phu - chi_so_phu_ky_truoc)     AS bien_dong_rui_ro_phu,
    CASE 
        WHEN chi_so_chinh_ky_truoc > 0 
        THEN ROUND((chi_so_rui_ro_chinh - chi_so_chinh_ky_truoc) * 100.0 / chi_so_chinh_ky_truoc, 2)
        ELSE 0.0
    END AS ty_le_giam_rui_ro_pct,
    DENSE_RANK() OVER (
        PARTITION BY ma_ky, phan_nhom_rui_ro ORDER BY tong_muc_do_rui_ro DESC
    ) AS xep_hang_diem_nong_ky
FROM risk_lag;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Top 5 Điểm Nóng An Ninh & Y Tế Sinh Sản Tại KY_2026)

#### Khối 1: Top 5 Điểm Nóng Ma Túy & HIV/AIDS Cấp Xã (`AN_NINH_MA_TUY_HIV_XA`)

| Xếp Hạng | Tên Xã | Tên Huyện | Người DTTS Nghiện 2026 | Người DTTS Nghiện 2024 | Biến Động (Người) | Tỷ Lệ Giảm (%) | Trạng Thái Giám Sát |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **#1** | **Xã Ea Wy** | Huyện Ea H'leo | **34** | 42 | **-8 người** | **-19.05%** | Tâm chấn ma túy (Đang hạ nhiệt) |
| **#2** | **Xã Ea Tam** | Huyện Krông Năng | **16** | 20 | **-4 người** | **-20.00%** | Kiểm soát tích cực |
| **#3** | **Xã Cư Né** | Huyện Krông Búk | **16** | 20 | **-4 người** | **-20.00%** | Kiểm soát tích cực |
| **#4** | **Xã Ea Tiêu** | Huyện Cư Kuin | **13** | 16 | **-3 người** | **-18.75%** | Địa bàn giáp ranh |
| **#4** | **Xã Ea Khal** | Huyện Ea H'leo | **11** | 14 | **-3 người** | **-21.43%** | Giảm vững chắc |

#### Khối 2: Top 5 Dân Tộc Có Số Ca Sinh Con Tại Nhà Lớn Nhất (`Y_TE_SINH_TAI_NHA_DANTOC`)

| Xếp Hạng | Tên Dân Tộc | Nhóm Nguồn Gốc | Ca Sinh Tại Nhà 2026 | Ca Sinh Tại Nhà 2024 | Biến Động (Ca) | Tỷ Lệ Giảm (%) | Đánh Giá Tác Động Dự Án 7 |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **#1** | **Mông** | Di cư miền núi phía Bắc | **233** | 367 | **-134 ca** | **-36.51%** | **Giảm ngoạn mục nhất tỉnh** |
| **#2** | **Xơ Đăng** | Bản địa Tây Nguyên | **185** | 278 | **-93 ca** | **-33.45%** | Giảm mạnh |
| **#3** | **Mnông** | Bản địa Tây Nguyên | **115** | 171 | **-56 ca** | **-32.75%** | Cải thiện đều |
| **#4** | **Ê Đê** | Bản địa Tây Nguyên | **113** | 171 | **-58 ca** | **-33.92%** | Chuyển biến tích cực |
| **#5** | **Mường** | Di cư miền núi phía Bắc | **10** | 14 | **-4 ca** | **-28.57%** | Tiệm cận mức an toàn |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Đà giảm mạnh tại các tâm chấn ma túy:** Toàn bộ Top 5 xã điểm nóng an ninh đều ghi nhận mức giảm từ **`18.75%` đến `21.43%`** số người DTTS nghiện ma túy giữa kỳ 2026 và 2024. Điểm nóng lớn nhất toàn tỉnh là **Xã Ea Wy (Ea H'leo)** giảm từ `42` xuống **`34` người nghiện (-8 người, giảm `-19.05%`)**.
- **Đột phá giảm ca sinh con tại nhà:** Toàn tỉnh giảm từ `1.023 ca` (`KY_2024`) xuống còn **`671 ca`** (`KY_2026`, giảm **`-352 ca`, tương đương `-34.41%`**). Dân tộc **Mông** giảm ấn tượng nhất với **`-134 ca` (từ 367 xuống 233 ca, giảm `-36.51%`)**, tiếp theo là dân tộc **Xơ Đăng giảm `-93 ca` (từ 278 xuống 185 ca, giảm `-33.45%`)**.

#### 2. ANALYSIS (Phân Tích Căn Nguyên Hiệu Quả Can Thiệp Đa Ngành)
- **Căn nguyên chuyển biến an ninh trật tự:** Việc bố trí lực lượng Công an chính quy về cơ sở kết hợp tuần tra triệt phá các đường dây cung cấp ma túy liên huyện tại Ea H'leo và Krông Năng đã chặt đứt các nguồn cung ma túy thẩm lậu vào buôn làng.
- **Căn nguyên thắng lợi y tế sinh sản (Dự án 7):** Hiệu quả vượt trội từ mạng lưới **Cô đỡ thôn bản người DTTS** được hưởng chế độ phụ cấp hàng tháng từ Dự án 7 MTQG 1719. Các cô đỡ cùng ngôn ngữ, cùng phong tục đã đến từng hộ đồng bào Mông và Xơ Đăng ở vùng núi cao, kiên trì vận động sản phụ đến sinh tại trạm y tế xã hoặc trực tiếp hỗ trợ đỡ đẻ vô trùng an toàn.

#### 3. IMPACT (Tác Động Giảm Thiểu Tử Vong Mẹ & Trật Tự Xã Hội)
- **Bảo vệ tính mạng bà mẹ & trẻ sơ sinh:** Giảm 352 ca sinh tại nhà giúp ngăn ngừa hàng chục ca tai biến sản khoa nguy hiểm (băng huyết sau sinh, uốn ván rốn sơ sinh, vỡ tử cung), nâng cao chỉ số phát triển con người (HDI) của tỉnh.
- **Giữ vững bình yên buôn làng:** Giảm số người nghiện ma túy trực tiếp làm giảm tỷ lệ phạm pháp hình sự (trộm cắp tài sản, gây rối trật tự) tại các xã vùng sâu.

#### 4. RECOMMENDATION (Khuyến Nghị Chiến Lược & Duy Trì Thành Quả)
- **Thể chế hóa chính sách đãi ngộ Cô đỡ thôn bản:** Sở Y tế tham mưu UBND tỉnh nâng định mức chi trả phụ cấp cho 100% cô đỡ thôn bản người Mông và Xơ Đăng từ nguồn vốn Dự án 7, không để xảy ra tình trạng nợ phụ cấp làm đứt gãy mạng lưới.
- **Mô hình cai nghiện cộng đồng gắn việc làm tại Ea Wy:** UBND huyện Ea H'leo chỉ đạo Trung tâm Y tế và các doanh nghiệp chế biến nông sản trên địa bàn tiếp nhận người sau cai nghiện vào làm việc tại các nông trường để cắt đứt nguy cơ tái nghiện.

---

##### 📋 Ma Trận Hành Động Can Thiệp Trụ Cột Đa Kỳ 4

| Trọng tâm can thiệp | Đơn vị chủ trì | Đơn vị phối hợp | Đối tượng ưu tiên | Thời hạn thực thi | Nguồn vốn đề xuất |
|---|---|---|---|---|---|
| **Duy trì phụ cấp Cô đỡ thôn bản** | Sở Y tế Đắk Lắk | Ban Dân tộc tỉnh, TTYT huyện | Đồng bào Mông, Xơ Đăng | 2025–2030 | Dự án 7 (CTMTQG 1719) |
| **Cấp phát thuốc Methadone lưu động** | Trung tâm Y tế Ea H'leo | UBND Xã Ea Wy, Ea Khal | Điểm nóng ma túy Ea Wy | Q1/2025 | Ngân sách y tế dự phòng |
| **Tạo việc làm sau cai nghiện** | UBND Huyện Ea H'leo | Phòng LĐ-TB&XH, Nông trường | Người DTTS sau cai nghiện | 2025–2026 | Quỹ hỗ trợ việc làm tỉnh |

---

## 🏛️ TRỤ CỘT ĐA KỲ 5: VIEW 5 (`v_tong_hop_ngan_sach_chinh_sach_ky`) — BỨC TRANH DỰ TOÁN NGÂN SÁCH ĐẦU TƯ CÔNG 3 CHU KỲ & CHIẾN LƯỢC TÁI CƠ CẤU DÒNG VỐN

### 1. Bối Cảnh Nghiệp Vụ & Cơ Sở Pháp Lý
- **Căn cứ chính sách:** Luật Đầu tư công, Quyết định 1719/QĐ-TTg, Nghị định 28/2022/NĐ-CP, Thông tư 15/2022/TT-BTC hướng dẫn quản lý và sử dụng kinh phí sự nghiệp thực hiện CTMTQG 1719.
- **Mục tiêu:** Tổng hợp toàn diện 5 nhóm chỉ tiêu kế hoạch ngân sách cốt lõi của tỉnh qua 3 chu kỳ (`KY_2019`, `KY_2024`, `KY_2026`), tính toán nhu cầu vốn theo định mức chính sách mới và đưa ra khuyến nghị điều chuyển ngân sách chiến lược trình Thường trực Tỉnh ủy và UBND Tỉnh.

---

### 2. Truy Vấn Kỹ Thuật (SQL Implementation — DDL View 5)
```sql
CREATE OR REPLACE VIEW daklak_analytics.v_tong_hop_ngan_sach_chinh_sach_ky AS
WITH raw_metrics_by_period AS (
    -- 1. Hỗ trợ sinh kế hộ nghèo DTTS (Dự án 3 MTQG 1719)
    SELECT 
        ma_ky,
        'TY_LE_HO_NGHEO'::VARCHAR(50) AS ma_chitieu,
        SUM(so_ho_ngheo)              AS so_luong_doi_tuong_can_ho_tro,
        ROUND(AVG(ty_le_ngheo_pct), 2) AS gia_tri_thuc_te_hien_tai
    FROM daklak_analytics.fact_hatang_xa
    GROUP BY ma_ky

    UNION ALL

    -- 2. Hỗ trợ xóa nhà tạm, dột nát (Dự án 1 MTQG 1719 & NĐ 28/2022/NĐ-CP)
    SELECT 
        ma_ky,
        'TY_LE_NHA_TAM'::VARCHAR(50) AS ma_chitieu,
        SUM(nha_thieu_kien_co_don_so) AS so_luong_doi_tuong_can_ho_tro,
        ROUND(SUM(nha_thieu_kien_co_don_so) * 100.0 / NULLIF(SUM(tong_so_ho_co_nha), 0), 2) AS gia_tri_thuc_te_hien_tai
    FROM daklak_analytics.fact_nhao_dantoc
    GROUP BY ma_ky

    UNION ALL

    -- 3. Giải ngân vốn vay tín dụng ưu đãi NHCSXH (Nghị định 28/2022/NĐ-CP)
    SELECT 
        ma_ky,
        'KHOANG_TRONG_TIN_DUNG'::VARCHAR(50) AS ma_chitieu,
        SUM(so_ho_co_nhu_cau_vay)            AS so_luong_doi_tuong_can_ho_tro,
        ROUND(SUM(so_ho_co_nhu_cau_vay) * 100.0 / NULLIF(SUM(tong_nhu_cau_ho), 0), 2) AS gia_tri_thuc_te_hien_tai
    FROM daklak_analytics.fact_tindung_dantoc
    GROUP BY ma_ky

    UNION ALL

    -- 4. Đào tạo nghề sơ cấp cho lao động chưa có CMKT (Dự án 5 MTQG 1719)
    SELECT 
        ma_ky,
        'TY_LE_CHUA_DAO_TAO_CMKT'::VARCHAR(50) AS ma_chitieu,
        SUM(khong_co_cmkt)                     AS so_luong_doi_tuong_can_ho_tro,
        ROUND(SUM(khong_co_cmkt) * 100.0 / NULLIF(SUM(tong_lao_dong), 0), 2) AS gia_tri_thuc_te_hien_tai
    FROM daklak_analytics.fact_trinhdo_cmkt_dantoc
    GROUP BY ma_ky

    UNION ALL

    -- 5. Gói đỡ đẻ an toàn & Chăm sóc sức khỏe bà mẹ trẻ em (Dự án 7 MTQG 1719)
    SELECT 
        ma_ky,
        'CA_SINH_TAI_NHA'::VARCHAR(50) AS ma_chitieu,
        SUM(sinh_tai_nha_tong)         AS so_luong_doi_tuong_can_ho_tro,
        SUM(sinh_tai_nha_tong)         AS gia_tri_thuc_te_hien_tai
    FROM daklak_analytics.fact_mucsinh_dantoc
    GROUP BY ma_ky
),
budget_calc AS (
    SELECT 
        k.ma_ky,
        k.thu_tu_ky,
        k.ten_ky,
        k.nam_moc,
        k.giai_doan_chinh_sach,
        k.is_latest,
        m.ma_chitieu,
        ct.ten_chitieu,
        ct.ma_chinh_sach,
        cs.ten_chinh_sach,
        ct.don_vi_tinh,
        ct.huong_tot,
        ct.chi_tieu_muc_tieu,
        m.gia_tri_thuc_te_hien_tai,
        m.so_luong_doi_tuong_can_ho_tro,
        ct.don_gia_trieu_vnd,
        ROUND(m.so_luong_doi_tuong_can_ho_tro * ct.don_gia_trieu_vnd / 1000.0, 2) AS tong_kinh_phi_can_phan_bo_ty_vnd,
        ct.can_cu_phap_ly_dinh_muc
    FROM raw_metrics_by_period m
    INNER JOIN daklak_analytics.dim_ky_baocao k 
        ON m.ma_ky = k.ma_ky
    INNER JOIN daklak_analytics.dim_chitieu_kehoach_ngansach ct 
        ON k.giai_doan_chinh_sach = ct.giai_doan_chinh_sach 
       AND m.ma_chitieu = ct.ma_chitieu
    LEFT JOIN daklak_analytics.dim_chinhsach_canthiep cs 
        ON ct.ma_chinh_sach = cs.ma_chinh_sach
)
SELECT 
    b.*,
    LAG(b.so_luong_doi_tuong_can_ho_tro) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    ) AS doi_tuong_ky_truoc,
    (b.so_luong_doi_tuong_can_ho_tro - LAG(b.so_luong_doi_tuong_can_ho_tro) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    )) AS bien_dong_so_luong_doi_tuong,
    LAG(b.tong_kinh_phi_can_phan_bo_ty_vnd) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    ) AS kinh_phi_ky_truoc_ty_vnd,
    ROUND(b.tong_kinh_phi_can_phan_bo_ty_vnd - LAG(b.tong_kinh_phi_can_phan_bo_ty_vnd) OVER (
        PARTITION BY b.ma_chitieu ORDER BY b.thu_tu_ky
    ), 2) AS bien_dong_kinh_phi_ty_vnd
FROM budget_calc b
ORDER BY b.ma_chitieu, b.thu_tu_ky;
```

---

### 3. Bảng Dữ Liệu Đối Soát Thực Nghiệm (Dự Toán Ngân Sách 5 Nhóm Chỉ Tiêu Qua 3 Chu Kỳ)

| Mã Chỉ Tiêu (`ma_chitieu`) | Kỳ (`ma_ky`) | Quy Mô Đối Tượng Cần Hỗ Trợ | Đơn Giá Định Mức (Triệu VNĐ) | Tổng Dự Toán Vốn (**Tỷ VNĐ**) | Vốn Kỳ Liền Trước (**Tỷ VNĐ**) | Biến Động Ngân Sách (**Tỷ VNĐ**) | Nhận Định Xu Hướng Ngân Sách |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`TY_LE_NHA_TAM`** *(Xóa nhà tạm - DA1)* | `KY_2019` | 14.780 hộ | 60.0 | **886.80** | — | — | Kỳ gốc Baseline |
| | `KY_2024` | 10.095 hộ | 80.0 | **807.60** | 886.80 | **-79.20** | Giảm nhu cầu vốn |
| | `KY_2026` | 6.378 hộ | 90.0 | **574.02** | 807.60 | **-233.58** | **Tiết kiệm đột phá (-233.58 tỷ)** |
| **`TY_LE_HO_NGHEO`** *(Hỗ trợ sinh kế - DA3)* | `KY_2019` | 41.406 hộ | 15.0 | **621.09** | — | — | Kỳ gốc Baseline |
| | `KY_2024` | 31.279 hộ | 25.0 | **781.98** | 621.09 | +160.89 | Tăng định mức hỗ trợ |
| | `KY_2026` | 28.677 hộ | 30.0 | **860.31** | 781.98 | **+78.33** | Tăng định mức giai đoạn mới |
| **`KHOANG_TRONG_TIN_DUNG`** *(Vốn NHCSXH - NĐ28)*| `KY_2019` | 38.018 hộ | 40.0 | **1.520.72** | — | — | Kỳ gốc Baseline |
| | `KY_2024` | 32.224 hộ | 50.0 | **1.611.20** | 1.520.72 | +90.48 | Tăng hạn mức vay |
| | `KY_2026` | 25.570 hộ | 65.0 | **1.662.05** | 1.611.20 | **+50.85** | Nâng hạn mức vay lên 65 tr/hộ |
| **`TY_LE_CHUA_DAO_TAO_CMKT`** *(Đào tạo nghề - DA5)*| `KY_2019` | 341.615 LĐ | 3.5 | **1.195.65** | — | — | Kỳ gốc Baseline |
| | `KY_2024` | 348.021 LĐ | 4.5 | **1.566.09** | 1.195.65 | +370.44 | Nhu cầu đào tạo lớn |
| | `KY_2026` | 336.708 LĐ | 6.0 | **2.020.25** | 1.566.09 | **+454.16** | **Tăng mạnh nhất (+454.16 tỷ)** |
| **`CA_SINH_TAI_NHA`** *(Làm mẹ an toàn - DA7)* | `KY_2019` | 1.409 ca | 2.0 | **2.82** | — | — | Kỳ gốc Baseline |
| | `KY_2024` | 1.023 ca | 3.0 | **3.07** | 2.82 | +0.25 | Tăng hỗ trợ cô đỡ |
| | `KY_2026` | 671 ca | 4.5 | **3.02** | 3.07 | **-0.05** | Ổn định ngân sách y tế |

---

### 4. Bóc Tách Insight Chuẩn F-A-I-R (Actionable Insights)

#### 1. FACT (Dữ Kiện Thực Tế Từ Cơ Sở Dữ Liệu)
- **Tiết kiệm ngân sách đột phá từ Xóa nhà tạm (`TY_LE_NHA_TAM`):** Nhu cầu ngân sách cho nhà ở giảm mạnh từ **`807.60 tỷ` (KY_2024) xuống `574.02 tỷ VNĐ` (KY_2026)**, tạo ra một khoản thặng dư tiết kiệm ngân sách lên tới **`-233.58 tỷ VNĐ`** nhờ số hộ ở nhà tạm giảm sâu từ `10.095` xuống `6.378` hộ.
- **Nghịch lý "Giảm số lượng đối tượng nhưng Tăng tổng dự toán vốn":**
  - Tại nhóm Sinh kế (`TY_LE_HO_NGHEO`): Số hộ nghèo giảm từ `31.279` xuống `28.677` hộ (`-2.602 hộ`), nhưng tổng dự toán vốn lại **tăng `+78.33 tỷ VNĐ`** (từ `781.98` lên `860.31 tỷ VNĐ`).
  - Tại nhóm Tín dụng ưu đãi (`KHOANG_TRONG_TIN_DUNG`): Số hộ khát vốn giảm từ `32.224` xuống `25.570` hộ (`-6.654 hộ`), nhưng dự toán vốn vay cần chuẩn bị lại **tăng `+50.85 tỷ VNĐ`** (từ `1.611.20` lên `1.662.05 tỷ VNĐ`).
  - Tại nhóm Đào tạo nghề (`TY_LE_CHUA_DAO_TAO_CMKT`): Số lao động chưa qua đào tạo giảm từ `348.021` xuống `336.708` người (`-11.313 người`), nhưng kinh phí dự toán lại **tăng vọt `+454.16 tỷ VNĐ`** (từ `1.566.09` lên `2.020.25 tỷ VNĐ`).

#### 2. ANALYSIS (Phân Tích Căn Nguyên: Nâng Định Mức Chính Sách & Chuyển Từ "Lượng" Sang "Chất")
- **Giải mã nghịch lý ngân sách:** Sở dĩ có hiện tượng giảm đối tượng nhưng tăng vốn là do Chính phủ và Tỉnh đã ban hành khung định mức chính sách mới cho giai đoạn `2026–2030` để bù đắp chỉ số lạm phát và nâng cao chất lượng hỗ trợ:
  - *Hỗ trợ sinh kế:* Tăng từ `25.0` lên **`30.0 triệu VNĐ/hộ`**.
  - *Hạn mức vay vốn NHCSXH:* Tăng từ `50.0` lên **`65.0 triệu VNĐ/hộ`**.
  - *Định mức đào tạo nghề sơ cấp:* Tăng từ `4.5` lên **`6.0 triệu VNĐ/lao động`** để tích hợp thêm chương trình thực hành vận hành máy móc hiện đại và chuyển giao công nghệ số.
- Đây là bước chuyển tất yếu từ hỗ trợ dàn trải sang can thiệp chuyên sâu, đảm bảo thoát nghèo thực chất và bền vững.

#### 3. IMPACT (Tác Động Thể Chế & Rủi Ro Cân Đối Dòng Vốn Trung Hạn)
- **Cơ hội tái cơ cấu nguồn vốn công:** Khoản kết dư **233.58 tỷ VNĐ** từ hợp phần xóa nhà tạm là một "dư địa vàng" để Tỉnh chủ động điều chuyển vốn nội bộ mà không làm phát sinh gánh nặng vay nợ hoặc xin bổ sung ngân sách trung ương.
- **Rủi ro thiếu hụt vốn đào tạo nghề và tín dụng:** Nhu cầu vốn đào tạo nghề lên tới **2.020.25 tỷ VNĐ** (tăng thêm 454.16 tỷ) và tín dụng chính sách là **1.662.05 tỷ VNĐ**. Nếu không có kế hoạch huy động và điều chuyển vốn sớm từ năm 2025, Tỉnh sẽ đối mặt với tình trạng "vốn xây lắp nhà ở thừa giải ngân chậm, còn vốn sự nghiệp đào tạo nghề và sinh kế lại cạn kiệt".

#### 4. RECOMMENDATION (Kế Hoạch Điều Hành Ngân Sách Chiến Lược — Executive Budget Reallocation)
UBND Tỉnh và Sở Tài chính, Sở Kế hoạch & Đầu tư cần trình HĐND Tỉnh phê chuẩn phương án điều chuyển dòng vốn **233.58 tỷ VNĐ** tiết kiệm từ chương trình xóa nhà tạm theo cơ cấu 3 trọng tâm cấp bách sau:

1. **Điều chuyển 150.00 tỷ VNĐ sang Tiểu dự án 3 Dự án 5 (Đào tạo nghề chuyên sâu):**
   Tập trung mở các lớp đào tạo nghề sơ cấp gắn chặt với quy trình chế biến, bảo quản và xuất khẩu nông sản chủ lực (cà phê đặc sản, sầu riêng đông lạnh, hồ tiêu sạch) cho hơn 25.000 lao động DTTS trẻ tại các huyện Ea H'leo, Cư M'gar và Krông Pắc.

2. **Điều chuyển 50.00 tỷ VNĐ ủy thác sang Chi nhánh NHCSXH Tỉnh Đắk Lắk:**
   Bổ sung nguồn vốn vay ưu đãi phục vụ phát triển sản xuất theo chuỗi giá trị (Nghị định 28/2022/NĐ-CP), ưu tiên giải ngân cho các hộ đồng bào Gia Rai và Ê Đê tại các huyện Ea Súp, Buôn Đôn, Lắk để triệt tiêu bẫy tín dụng đen.

3. **Điều chuyển 33.58 tỷ VNĐ sang Hợp phần Vệ sinh Môi trường Nông thôn mới (Tiêu chí 17):**
   Hỗ trợ trực tiếp cho các hộ DTTS nghèo tại 2 huyện trũng Krông Bông và Lắk với định mức 5 triệu đồng/hộ để xóa sổ các hố xí mất vệ sinh, bảo vệ nguồn nước ngầm buôn làng.

---

##### 📋 Ma Trận Điều Hành Tái Cơ Cấu Ngân Sách Tỉnh (Executive Action Matrix)

| Trọng tâm điều chuyển ngân sách | Nguồn kinh phí điều chuyển | Đơn vị chủ trì | Đơn vị phối hợp | Địa bàn thụ hưởng | Thời hạn hoàn thành | Dự toán điều chuyển |
|---|---|---|---|---|---|---|
| **Đào tạo nghề gắn chuỗi xuất khẩu** | Tiết kiệm từ Xóa nhà tạm | Sở LĐ-TB&XH | Sở Nông nghiệp, Doanh nghiệp | Cư M'gar, Krông Pắc, Ea H'leo | 2025–2027 | **150.00 tỷ VNĐ** |
| **Vốn vay ủy thác phát triển sản xuất**| Tiết kiệm từ Xóa nhà tạm | Chi nhánh NHCSXH Đắk Lắk | Ban Dân tộc tỉnh, Hội Nông dân | Ea Súp, Buôn Đôn, Lắk | Q2/2025 | **50.00 tỷ VNĐ** |
| **Gói hỗ trợ hố xí hợp vệ sinh (TC17)**| Tiết kiệm từ Xóa nhà tạm | Sở Y tế / Ban Chỉ đạo NTM | UBND Huyện Krông Bông & Lắk | Huyện Krông Bông & Lắk | 2025–2026 | **33.58 tỷ VNĐ** |
| **TỔNG KINH PHÍ TÁI CƠ CẤU ĐIỀU CHUYỂN** | *(Từ hợp phần nhà ở Dự án 1)* | **UBND Tỉnh Đắk Lắk** | **Sở Tài chính & Sở KH&ĐT** | **Toàn Tỉnh Đắk Lắk** | **Kỳ họp HĐND 2025** | **233.58 TỶ VNĐ** |










