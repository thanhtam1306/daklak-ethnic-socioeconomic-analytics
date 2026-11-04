"""
Script tạo bảng Dimension thứ 3: dim_chinhsach_canthiep
Chứa danh mục Căn cứ Pháp lý, Chương trình can thiệp và Cơ chế ngân sách
Đồng bộ hóa vào Parquet, DuckDB và PostgreSQL 18
"""

import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
import duckdb
import psycopg2
from psycopg2 import sql

def create_dim_chinhsach():
    data = [
        {
            "ma_chinh_sach": "CS_1719_DA1_NHAO",
            "ten_chinh_sach": "Dự án 1 - Giải quyết tình trạng thiếu đất ở, nhà ở, đất sản xuất, nước sinh hoạt",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Nhà ở & Đất ở",
            "doi_tuong_thu_huong": "Hộ DTTS nghèo, cận nghèo sinh sống tại vùng DTTS&MN chưa có nhà hoặc nhà tạm bợ, dột nát",
            "nguon_von_thuc_hien": "Ngân sách Trung ương MTQG 1719 (Hỗ trợ 40 tr.đ/hộ) + Vốn vay NHCSXH theo NĐ 28 (tối đa 40 tr.đ/hộ)",
            "muc_tieu_dinh_luong": "Xóa 100% nhà tạm, dột nát cho 10.095 hộ DTTS; ưu tiên bảo tồn khẩn cấp 4 hộ Chơ Ro tại Cư M'gar"
        },
        {
            "ma_chinh_sach": "CS_1719_DA1_DATSX",
            "ten_chinh_sach": "Dự án 1 - Hỗ trợ đất sản xuất và chuyển đổi nghề",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Đất sản xuất & Tư liệu SX",
            "doi_tuong_thu_huong": "Hộ DTTS nghèo thiếu đất sản xuất (<0.5 ha đất nông nghiệp/hộ)",
            "nguon_von_thuc_hien": "Ngân sách Trung ương MTQG 1719 + Hỗ trợ chuyển đổi nghề (tối đa 10 tr.đ/hộ)",
            "muc_tieu_dinh_luong": "Giải quyết tình trạng thiếu đất sản xuất cho 7 dân tộc báo động đỏ (<0.5 ha/hộ: Chăm, Thổ, Co, Mảng, Bru Vân Kiều, Thái, Chứt) và nâng quy mô đất hộ Ê Đê (0.83 ha)"
        },
        {
            "ma_chinh_sach": "CS_1719_DA1_NUOCSH",
            "ten_chinh_sach": "Dự án 1 - Hỗ trợ nước sinh hoạt phân tán và tập trung",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Nước sạch & Vệ sinh",
            "doi_tuong_thu_huong": "Hộ DTTS vùng khó khăn chưa có nguồn nước sinh hoạt hợp vệ sinh",
            "nguon_von_thuc_hien": "Ngân sách Trung ương MTQG 1719 (3 tr.đ/hộ cho phân tán, đầu tư công cho trạm cấp nước)",
            "muc_tieu_dinh_luong": "Nâng tỷ lệ hộ DTTS sử dụng nước hợp vệ sinh toàn tỉnh lên trên 95%, đặc biệt các xã vùng sâu Ea Súp, Lắk"
        },
        {
            "ma_chinh_sach": "CS_1719_DA3_NONGNGHIEP",
            "ten_chinh_sach": "Dự án 3 - Phát triển sản xuất nông, lâm nghiệp bền vững, phát huy tiềm năng vùng DTTS",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Nông nghiệp & Chuỗi giá trị",
            "doi_tuong_thu_huong": "Hộ gia đình, hợp tác xã, doanh nghiệp liên kết bao tiêu sản phẩm nông lâm nghiệp vùng DTTS",
            "nguon_von_thuc_hien": "Ngân sách sự nghiệp MTQG 1719 + Vốn đối ứng HTX/Doanh nghiệp",
            "muc_tieu_dinh_luong": "Phá vỡ bẫy nông nghiệp độc canh tự cung tự cấp (88.97% lao động nông nghiệp), liên kết chế biến cà phê, hồ tiêu, sầu riêng xuất khẩu"
        },
        {
            "ma_chinh_sach": "CS_1719_DA4_HATANG",
            "ten_chinh_sach": "Dự án 4 - Đầu tư cơ sở hạ tầng thiết yếu phục vụ sản xuất và dân sinh",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Hạ tầng giao thông & Thủy lợi",
            "doi_tuong_thu_huong": "Các xã khu vực III, thôn/buôn đặc biệt khó khăn vùng DTTS&MN",
            "nguon_von_thuc_hien": "Vốn đầu tư phát triển ngân sách Trung ương MTQG 1719",
            "muc_tieu_dinh_luong": "Cứng hóa 100% đường giao thông đến trung tâm xã, kiên cố hóa đường trục thôn buôn, kéo giảm hệ số ma sát khoảng cách (>20km)"
        },
        {
            "ma_chinh_sach": "CS_1719_DA5_GIAODUC_NGHE",
            "ten_chinh_sach": "Dự án 5 - Phát triển giáo dục đào tạo nâng cao chất lượng nguồn nhân lực",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Giáo dục & Dạy nghề",
            "doi_tuong_thu_huong": "Thanh thiếu niên, lao động DTTS chưa có văn bằng chứng chỉ (đặc biệt học sinh tốt nghiệp THCS, THPT)",
            "nguon_von_thuc_hien": "Ngân sách sự nghiệp GD&ĐT MTQG 1719",
            "muc_tieu_dinh_luong": "Giải tỏa bẫy 87.36% lao động DTTS chưa qua đào tạo CMKT (348.020 người); xóa mù chữ người lớn cho nữ giới DTTS"
        },
        {
            "ma_chinh_sach": "CS_1719_DA7_YTE_DANSO",
            "ten_chinh_sach": "Dự án 7 - Chăm sóc sức khỏe nhân dân, nâng cao thể trạng, tầm vóc người DTTS; phòng chống suy dinh dưỡng",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Y tế & Sức khỏe sinh sản",
            "doi_tuong_thu_huong": "Phụ nữ mang thai, trẻ em dưới 5 tuổi vùng DTTS, người thuộc DTTS rất ít người",
            "nguon_von_thuc_hien": "Ngân sách y tế MTQG 1719",
            "muc_tieu_dinh_luong": "Chấm dứt nạn sinh con tại nhà không có đỡ đẻ (1.023 ca sinh tại nhà, 367 ca người Mông); giảm tỷ lệ sinh con thứ 3+ (46.044 ca)"
        },
        {
            "ma_chinh_sach": "CS_1719_DA9_DTTS_ITNGUOI",
            "ten_chinh_sach": "Dự án 9 - Đầu tư phát triển nhóm DTTS rất ít người và nhóm dân tộc còn nhiều khó khăn",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Bảo tồn & Phát triển đặc thù",
            "doi_tuong_thu_huong": "Các dân tộc rất ít người (<10.000 người trên toàn quốc) và dân tộc có nguy cơ suy giảm dân số",
            "nguon_von_thuc_hien": "Ngân sách Trung ương bố trí riêng cho Dự án 9 MTQG 1719",
            "muc_tieu_dinh_luong": "Bảo vệ khẩn cấp dân số học, hỗ trợ sinh kế và giáo dục cho 14 DTTS rất ít người có mặt tại Đắk Lắk (Chơ Ro, Ơ Đu, Rơ Măm, Si La, Pu Péo...)"
        },
        {
            "ma_chinh_sach": "CS_1719_DA10_THONGTIN",
            "ten_chinh_sach": "Dự án 10 - Truyền thông, tuyên truyền, vận động trong vùng DTTS&MN và kiểm tra, giám sát đánh giá",
            "can_cu_phap_ly": "Quyết định số 1719/QĐ-TTg ngày 14/10/2021 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Truyền thông & Giám sát",
            "doi_tuong_thu_huong": "Toàn thể đồng bào DTTS, cán bộ làm công tác dân tộc các cấp",
            "nguon_von_thuc_hien": "Ngân sách sự nghiệp MTQG 1719",
            "muc_tieu_dinh_luong": "Xóa bỏ các tập tục lạc hậu (tảo hôn, sinh đẻ không an toàn), phổ biến chính sách pháp luật bằng song ngữ Kinh - Ê Đê/Mnông"
        },
        {
            "ma_chinh_sach": "CS_ND28_TINDUNG_CSXH",
            "ten_chinh_sach": "Nghị định 28/2022/NĐ-CP - Chính sách tín dụng ưu đãi thực hiện MTQG 1719",
            "can_cu_phap_ly": "Nghị định số 28/2022/NĐ-CP ngày 26/04/2022 của Chính phủ",
            "nhom_linh_vuc": "Tín dụng chính sách",
            "doi_tuong_thu_huong": "Hộ DTTS nghèo, cận nghèo có phương án sản xuất kinh doanh khả thi",
            "nguon_von_thuc_hien": "Vốn vay qua Chi nhánh Ngân hàng Chính sách Xã hội tỉnh Đắk Lắk (Lãi suất ưu đãi 3%/năm)",
            "muc_tieu_dinh_luong": "Đáp ứng 32.227 hồ sơ hộ DTTS đang khát vốn (khoảng trống 42.87%); ưu tiên đặc biệt hộ Gia Rai (69.2% khát vốn) và hộ Ê Đê (17.330 hồ sơ)"
        },
        {
            "ma_chinh_sach": "CS_QD318_NTM_TC17",
            "ten_chinh_sach": "Tiêu chí số 17 (Môi trường & An toàn thực phẩm) - Chương trình MTQG Xây dựng NTM",
            "can_cu_phap_ly": "Quyết định số 318/QĐ-TTg ngày 08/03/2022 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Nước sạch & Vệ sinh môi trường",
            "doi_tuong_thu_huong": "Hộ dân và chính quyền các xã đăng ký về đích Nông thôn mới",
            "nguon_von_thuc_hien": "Ngân sách Chương trình MTQG Nông thôn mới + Vốn lồng ghép MTQG 1719 + Xã hội hóa",
            "muc_tieu_dinh_luong": "Kéo tỷ lệ hố xí hợp vệ sinh tại 2 huyện tâm chấn Krông Bông (10.92%) và Lắk (12.64%) vượt ngưỡng 70% để đạt chuẩn NTM"
        },
        {
            "ma_chinh_sach": "CS_DEAN06_CHUYENDOI_SO",
            "ten_chinh_sach": "Đề án 06 - Phát triển ứng dụng dữ liệu về dân cư, định danh và xác thực điện tử",
            "can_cu_phap_ly": "Quyết định số 06/QĐ-TTg ngày 06/01/2022 của Thủ tướng Chính phủ",
            "nhom_linh_vuc": "Chuyển đổi số & Dân cư",
            "doi_tuong_thu_huong": "Toàn bộ công dân DTTS đủ điều kiện cấp CCCD, kích hoạt định danh VNeID",
            "nguon_von_thuc_hien": "Ngân sách nhà nước theo Đề án 06 và Chương trình Chuyển đổi số quốc gia",
            "muc_tieu_dinh_luong": "Xóa điểm nghẽn hạ tầng số tại Lắk (chỉ 23.52% dùng internet) và Ea Kar (23.03%), phổ cập internet băng rộng tới 100% thôn buôn"
        },
        {
            "ma_chinh_sach": "CS_LUAT_PCTMT_YTE",
            "ten_chinh_sach": "Luật Phòng, chống ma túy và Kế hoạch can thiệp giảm hại lây nhiễm HIV/AIDS",
            "can_cu_phap_ly": "Luật Phòng, chống ma túy số 73/2021/QH14 và Quyết định số 140/QĐ-TTg ngày 02/02/2024",
            "nhom_linh_vuc": "An ninh trật tự & Y tế dự phòng",
            "doi_tuong_thu_huong": "Người nghiện ma túy, người nhiễm HIV và gia đình tại các địa bàn trọng điểm DTTS",
            "nguon_von_thuc_hien": "Ngân sách phòng chống ma túy, HIV/AIDS và Quỹ Hỗ trợ can thiệp cộng đồng",
            "muc_tieu_dinh_luong": "Thiết lập trạm cấp phát thuốc Methadone tại cụm Ea H'leo (tâm chấn 89 người nghiện DTTS) và Krông Năng (18 ca HIV); khoanh vùng dập dịch tại điểm nóng Ea Wy (42 người nghiện, 13 ca HIV)"
        }
    ]

    df = pd.DataFrame(data)
    
    # 1. Lưu Parquet và CSV
    parquet_path = "data/processed/dim_chinhsach_canthiep.parquet"
    csv_path = "data/processed/dim_chinhsach_canthiep.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Đã lưu {len(df)} dòng chính sách vào {parquet_path} và {csv_path}")

    # 2. Nạp vào DuckDB
    duck_path = "warehouse/daklak_socioeconomic.duckdb"
    con_duck = duckdb.connect(duck_path)
    con_duck.execute("DROP TABLE IF EXISTS dim_chinhsach_canthiep")
    con_duck.execute(f"CREATE TABLE dim_chinhsach_canthiep AS SELECT * FROM read_parquet('{parquet_path}')")
    cnt_duck = con_duck.execute("SELECT count(*) FROM dim_chinhsach_canthiep").fetchone()[0]
    print(f"[OK] DuckDB đã nạp thành công bảng dim_chinhsach_canthiep: {cnt_duck} dòng")
    con_duck.close()

    # 3. Nạp vào PostgreSQL 18
    try:
        db_pass = os.getenv("PGPASSWORD", "123456")
        db_user = os.getenv("PGUSER", "postgres")
        con_pg = psycopg2.connect(dbname="daklak_socioeconomic", user=db_user, password=db_pass, host="localhost", port=5432)
        cur = con_pg.cursor()
        
        cur.execute("""
            DROP TABLE IF EXISTS daklak_analytics.dim_chinhsach_canthiep CASCADE;
            CREATE TABLE daklak_analytics.dim_chinhsach_canthiep (
                ma_chinh_sach VARCHAR(50) PRIMARY KEY,
                ten_chinh_sach VARCHAR(255) NOT NULL,
                can_cu_phap_ly TEXT NOT NULL,
                nhom_linh_vuc VARCHAR(100) NOT NULL,
                doi_tuong_thu_huong TEXT,
                nguon_von_thuc_hien TEXT,
                muc_tieu_dinh_luong TEXT
            );
        """)
        
        insert_query = sql.SQL("""
            INSERT INTO daklak_analytics.dim_chinhsach_canthiep 
            (ma_chinh_sach, ten_chinh_sach, can_cu_phap_ly, nhom_linh_vuc, doi_tuong_thu_huong, nguon_von_thuc_hien, muc_tieu_dinh_luong)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """)
        
        for _, row in df.iterrows():
            cur.execute(insert_query, (
                row["ma_chinh_sach"],
                row["ten_chinh_sach"],
                row["can_cu_phap_ly"],
                row["nhom_linh_vuc"],
                row["doi_tuong_thu_huong"],
                row["nguon_von_thuc_hien"],
                row["muc_tieu_dinh_luong"]
            ))
            
        con_pg.commit()
        cur.execute("SELECT count(*) FROM daklak_analytics.dim_chinhsach_canthiep;")
        cnt_pg = cur.fetchone()[0]
        print(f"[OK] PostgreSQL 18 đã nạp thành công daklak_analytics.dim_chinhsach_canthiep: {cnt_pg} dòng")
        cur.close()
        con_pg.close()
    except Exception as e:
        print("[ERR] Lỗi khi nạp vào PostgreSQL:", e)

if __name__ == "__main__":
    create_dim_chinhsach()
