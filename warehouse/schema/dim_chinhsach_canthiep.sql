-- ==============================================================================
-- BẢNG CHIỀU CHÍNH SÁCH CÔNG & CƠ SỞ PHÁP LÝ (EVIDENCE-BASED POLICY DIMENSION)
-- CSDL: daklak_socioeconomic | Schema: daklak_analytics
-- Dự án: Phân tích Thực trạng KTXH 53 Dân tộc thiểu số Đắk Lắk 2024
-- ==============================================================================

SET search_path TO daklak_analytics, public;

DROP TABLE IF EXISTS dim_chinhsach_canthiep CASCADE;

CREATE TABLE dim_chinhsach_canthiep (
    ma_chinhsach       VARCHAR(50) PRIMARY KEY,
    ten_chinhsach      VARCHAR(255) NOT NULL,
    nhom_chuyen_de     VARCHAR(100) NOT NULL,
    can_cu_phap_ly     TEXT NOT NULL,
    du_an_chuong_trinh TEXT NOT NULL,
    co_quan_chu_tri    VARCHAR(150) NOT NULL,
    co_che_nguon_von   TEXT NOT NULL,
    noi_dung_can_thiep TEXT NOT NULL,
    doi_tuong_uu_tien  TEXT NOT NULL
);

-- NẠP DỮ LIỆU DANH MỤC CHÍNH SÁCH CHUẨN QUỐC GIA & TỈNH ĐẮK LẮK
INSERT INTO dim_chinhsach_canthiep (
    ma_chinhsach, ten_chinhsach, nhom_chuyen_de, can_cu_phap_ly, 
    du_an_chuong_trinh, co_quan_chu_tri, co_che_nguon_von, 
    noi_dung_can_thiep, doi_tuong_uu_tien
) VALUES
(
    'CS_NHA_O_DAT_DAI',
    'Chính sách Hỗ trợ Đất ở, Nhà ở và Đất sản xuất vùng DTTS',
    'Nha_O_Dat_Dai',
    'Quyết định 1719/QĐ-TTg ngày 14/10/2021; Thông tư 02/2022/TT-UBDT của Ủy ban Dân tộc; Thông tư 55/2023/TT-BTC',
    'Dự án 1: Giải quyết tình trạng thiếu đất ở, nhà ở, đất sản xuất, nước sinh hoạt',
    'Ban Dân tộc tỉnh phối hợp Sở Tài nguyên & Môi trường, Sở Xây dựng',
    'Ngân sách Trung ương hỗ trợ trực tiếp (40 triệu/hộ nhà ở) + Ngân sách tỉnh đối ứng + Vốn vay ưu đãi NHCSXH',
    'Hỗ trợ kinh phí trực tiếp xóa nhà tạm dột nát; rà soát thu hồi quỹ đất lâm nghiệp kém hiệu quả giao đất sản xuất tối thiểu 0.5 ha/hộ hoặc hỗ trợ chuyển đổi nghề.',
    '10.095 hộ DTTS đang ở nhà tạm dột nát; 7 dân tộc sở hữu đất dưới 0.5 ha/hộ (Chăm, Thổ, Co, Mảng, Bru Vân Kiều, Thái, Chứt)'
),
(
    'CS_TIN_DUNG_CSXH',
    'Chính sách Tín dụng Ưu đãi thực hiện Chương trình MTQG 1719',
    'Tin_Dung_CSXH',
    'Nghị định 28/2022/NĐ-CP ngày 26/04/2022 của Chính phủ; Hướng dẫn nghiệp vụ Tổng Giám đốc NHCSXH',
    'Chính sách Tín dụng Ưu đãi MTQG 1719 qua Ngân hàng Chính sách Xã hội (NHCSXH)',
    'Chi nhánh Ngân hàng Chính sách Xã hội tỉnh Đắk Lắk phối hợp UBND các huyện',
    'Nguồn vốn tín dụng ưu đãi từ NHCSXH; lãi suất cho vay bằng 50% lãi suất cho vay hộ nghèo; thời hạn vay tối đa 10 năm',
    'Mở rộng hạn mức tín dụng hộ nghèo và cận nghèo; giải ngân gói tín dụng hỗ trợ đất sản xuất (tối đa 50 triệu/hộ), chuyển đổi nghề (tối đa 100 triệu/hộ), làm nhà ở (tối đa 40 triệu/hộ).',
    '32.227 hộ DTTS có nhu cầu vay vốn nhưng chưa được đáp ứng; ưu tiên đặc biệt người Gia Rai (69.2% khát vốn) và người Ê Đê (17.330 hộ)'
),
(
    'CS_HO_XI_NUOC_SACH',
    'Tiêu chí Vệ sinh Môi trường & Nước sạch Nông thôn mới',
    'Ho_Xi_Nuoc_Sach_NTM',
    'Quyết định 318/QĐ-TTg ngày 08/03/2022 ban hành Bộ tiêu chí Nông thôn mới 2021-2025; Quyết định 211/QĐ-TTg',
    'Chương trình MTQG Xây dựng Nông thôn mới - Tiêu chí số 17 (Môi trường & An toàn thực phẩm)',
    'Sở Nông nghiệp & Phát triển Nông thôn phối hợp Sở Y tế, Hội Phụ nữ tỉnh',
    'Lồng ghép nguồn vốn CTMTQG Nông thôn mới + Vốn Nước sạch & VSMT nông thôn NHCSXH',
    'Phát động Chiến dịch Hợp vệ sinh môi trường; hỗ trợ vay vốn ưu đãi 20 triệu/công trình nhà tiêu hợp vệ sinh; tập huấn thay đổi tập quán phóng uế bừa bãi.',
    'Các huyện có tỷ lệ nhà tiêu hợp vệ sinh dưới 50%, trọng tâm là Krông Bông (10.92%), Lắk (12.64%), Krông Búk (40.40%)'
),
(
    'CS_DAO_TAO_NGHE',
    'Chương trình Phát triển Giáo dục Nghề nghiệp & Giải quyết Việc làm',
    'Dao_Tao_Nghe_Viec_Lam',
    'Quyết định 1719/QĐ-TTg (Dự án 5); Quyết định 46/2015/QĐ-TTg về chính sách hỗ trợ đào tạo nghề sơ cấp, dưới 3 tháng',
    'Tiểu dự án 3 (Dự án 5 - MTQG 1719): Phát triển giáo dục nghề nghiệp và giải quyết việc làm vùng DTTS',
    'Sở Lao động - Thương binh & Xã hội phối hợp Trung tâm Giáo dục nghề nghiệp các huyện',
    'Ngân sách Trung ương hỗ trợ chi phí đào tạo, tiền ăn, tiền đi lại cho học viên DTTS',
    'Đào tạo nghề sơ cấp lưu động tại xã; gắn đào tạo kỹ thuật chế biến cà phê, sầu riêng, mắc ca và cơ khí sửa chữa máy nông nghiệp với nhu cầu tuyển dụng doanh nghiệp địa phương.',
    '348.020 lao động DTTS chưa qua đào tạo chuyên môn kỹ thuật (87.36%); đặc biệt nhóm thanh niên người Mông (96.98% chưa đào tạo)'
),
(
    'CS_BAO_TON_DTTS_IT_NGUOI',
    'Chính sách Đầu tư Bảo tồn & Phát triển Khẩn cấp Nhóm DTTS Rất Ít Người',
    'Bao_Ton_DTTS_It_Nguoi',
    'Quyết định 1719/QĐ-TTg (Dự án 9); Quyết định 1227/QĐ-TTg phê duyệt danh sách DTTS có khó khăn đặc thù',
    'Tiểu dự án 1 (Dự án 9 - MTQG 1719): Đầu tư phát triển nhóm DTTS rất ít người và nhóm có khó khăn đặc thù',
    'Ban Dân tộc tỉnh Đắk Lắk chủ trì phối hợp UBND các huyện cư trú',
    'Ngân sách Trung ương hỗ trợ trọn gói (đầu tư hạ tầng, y tế, giáo dục, sinh kế bảo tồn)',
    'Hỗ trợ đặc thù trọn gói 100%: Xóa dột nát nhà ở, trợ cấp học sinh đi học nội trú, bảo hiểm y tế miễn phí, mở lớp xóa mù chữ lưu động tiếng mẹ đẻ và tiếng Việt.',
    'Các dân tộc rất ít người có nguy cơ tổn thương cao: Dân tộc Chơ Ro (4 hộ, 100% nhà tạm dột nát), Co, Mảng, Ơ Đu, Rơ Măm, Brâu sinh sống tại Đắk Lắk'
),
(
    'CS_Y_TE_SINH_SAN',
    'Chương trình Làm Mẹ An Toàn & Chăm Sóc Sức Khỏe Sinh Sản Vùng DTTS',
    'Y_Te_Sinh_San',
    'Quyết định 1719/QĐ-TTg (Dự án 7); Kế hoạch hành động quốc gia về Chăm sóc sức khỏe sinh sản Bộ Y tế',
    'Dự án 7 (MTQG 1719): Chăm sóc sức khỏe nhân dân, nâng cao thể trạng, tầm vóc người DTTS',
    'Sở Y tế tỉnh Đắk Lắk chỉ đạo Trung tâm Y tế huyện và Trạm Y tế xã',
    'Ngân sách CTMTQG 1719 + Nguồn viện trợ y tế cộng đồng',
    'Duy trì và chi trả phụ cấp cho mạng lưới Cô đỡ thôn bản người DTTS; truyền thông vận động sản phụ sinh con tại trạm y tế; cung cấp gói chăm sóc mẹ và bé sơ sinh tại nhà miễn phí.',
    'Các địa bàn có tỷ lệ sinh tại nhà cao: Người Mông (367 ca sinh tại nhà, 131 ca không có cán bộ y tế), người Dao, Vân Kiều tại Krông Năng, Ea Súp, Ea H''leo'
),
(
    'CS_CHUYEN_DOI_SO',
    'Đề án Phát triển Ứng dụng Dữ liệu Dân cư & Thu hẹp Khoảng cách số',
    'Chuyen_Doi_So',
    'Quyết định 06/QĐ-TTg (Đề án 06/CP); Quyết định 1719/QĐ-TTg (Tiểu dự án 2 - Dự án 10)',
    'Tiểu dự án 2 (Dự án 10 - MTQG 1719) & Kế hoạch Chuyển đổi số tỉnh Đắk Lắk',
    'Sở Thông tin & Truyền thông phối hợp Công an tỉnh Đắk Lắk, Tập đoàn Viettel, VNPT',
    'Quỹ Dịch vụ Viễn thông Công ích Việt Nam + Doanh nghiệp viễn thông',
    'Xóa vùng lõm sóng di động tại thôn buôn vùng sâu; trang bị máy tính công cộng tại nhà văn hóa cộng đồng buôn; hướng dẫn người dân kích hoạt VNeID và nộp hồ sơ dịch vụ công trực tuyến.',
    'Các huyện trũng số: Lắk (76.48% hộ chưa internet), Ea Kar (76.97%), M''Drắk, Krông Bông'
),
(
    'CS_AN_NINH_TE_NAN',
    'Chương trình Phòng Chống Ma Túy & Kiểm Soát Dịch HIV/AIDS Vùng Đồng Bào DTTS',
    'An_Ninh_Te_Nan',
    'Luật Phòng, chống ma túy 2021; Chiến lược Quốc gia chấm dứt dịch bệnh AIDS vào năm 2030 (QĐ 1246/QĐ-TTg)',
    'Chương trình Mục tiêu Quốc gia Phòng chống Tội phạm & Ma túy - Tiểu đề án Y tế & Công an',
    'Công an tỉnh Đắk Lắk phối hợp Trung tâm Kiểm soát Bệnh tật (CDC) Sở Y tế',
    'Ngân sách đảm bảo an ninh trật tự địa phương + Quỹ Toàn cầu phòng chống AIDS',
    'Triệt phá các tụ điểm ma túy thẩm lậu vùng giáp ranh; mở điểm cấp phát thuốc điều trị thay thế nghiện các chất dạng thuốc phiện bằng Methadone tại trạm y tế cụm xã Ea Wy; cấp phát bơm kim tiêm và bao cao su miễn phí.',
    'Tâm chấn ma túy huyện Ea H''leo (32.1% người DTTS nghiện ma túy toàn tỉnh) và tâm chấn HIV huyện Krông Năng (20.2% ca nhiễm); trọng điểm xã Ea Wy'
),
(
    'CS_HA_TANG_KET_NOI',
    'Đầu tư Hạ tầng Giao thông Phá vỡ Thế Cô Lập Vùng Xa',
    'Ha_Tang_Giao_Thong',
    'Quyết định 1719/QĐ-TTg (Dự án 4); Nghị quyết Đảng bộ tỉnh Đắk Lắk nhiệm kỳ 2020-2025',
    'Dự án 4 (MTQG 1719): Đầu tư cơ sở hạ tầng thiết yếu phục vụ sản xuất và đời sống vùng DTTS',
    'Sở Giao thông Vận tải phối hợp UBND các huyện Ea Súp, Lắk, M''Drắk',
    'Vốn đầu tư công trung hạn Ngân sách Trung ương và địa phương',
    'Nhựa hóa / Bê tông hóa 100% đường trục liên xã và đường trục thôn buôn tại các xã cách trung tâm trên 20km; xây cầu dân sinh kết nối vùng sản xuất nông nghiệp.',
    'Nhóm xã cách trung tâm huyện trên 20km (nơi có tỷ lệ hộ nghèo tăng vọt theo mô hình OLS +5.13% mỗi 10km); tiêu biểu là cụm xã biên giới Ea Súp và vùng đệm Vườn Quốc gia Chư Yang Sin (Lắk)'
);
