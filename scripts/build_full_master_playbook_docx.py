# -*- coding: utf-8 -*-
"""
Script xây dựng toàn diện cuốn CẨM NANG TOÀN TRÌNH DỰ ÁN & BỘ CÂU HỎI PHỎNG VẤN SENIOR DATA ANALYST (Bản DOCX & Markdown Siêu Chi Tiết)
Tác giả: Nguyễn Hoàng Thanh Tâm
"""

import os
import re
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="{color}"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/><w:insideV w:val="none"/><w:left w:val="none"/><w:right w:val="none"/></w:tblBorders>')
    tblPr.append(borders)

def add_executive_callout(doc, text, title="CHIẾN THUẬT PHỎNG VẤN & BẢN LĨNH SENIOR DA", border_color="1E3A8A", bg_color="F8FAFC"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=160, bottom=160, left=220, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="28" w:space="0" w:color="{border_color}"/><w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    if title:
        run_t = p.add_run(f"💡 {title}\n")
        run_t.bold = True
        run_t.font.name = "Segoe UI"
        run_t.font.size = Pt(10.5)
        run_t.font.color.rgb = RGBColor(30, 58, 138)
        
    run = p.add_run(text)
    run.font.name = "Segoe UI"
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(51, 65, 85)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_text, lang_title="MÃ NGUỒN THỰC THI (PRODUCTION SCRIPT)"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, "0F172A") # Slate-900 dark background
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    cp = cell.paragraphs[0]
    cp.paragraph_format.space_before = Pt(0)
    cp.paragraph_format.space_after = Pt(0)
    cp.paragraph_format.line_spacing = 1.05
    
    t_run = cp.add_run(f"// --- {lang_title} ---\n")
    t_run.font.name = "Consolas"
    t_run.font.size = Pt(8)
    t_run.font.color.rgb = RGBColor(148, 163, 184)
    t_run.font.italic = True
    
    c_run = cp.add_run(code_text)
    c_run.font.name = "Consolas"
    c_run.font.size = Pt(8.5)
    c_run.font.color.rgb = RGBColor(226, 232, 240)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_after = Pt(4)

def format_inline_runs(paragraph, text, base_font="Segoe UI", base_size=10, base_color=RGBColor(30, 41, 59)):
    pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)'
    tokens = re.split(pattern, text)
    
    for token in tokens:
        if not token:
            continue
        run = paragraph.add_run()
        run.font.name = base_font
        run.font.size = Pt(base_size)
        run.font.color.rgb = base_color
        
        if token.startswith('**') and token.endswith('**'):
            run.text = token[2:-2]
            run.bold = True
        elif token.startswith('*') and token.endswith('*'):
            run.text = token[1:-1]
            run.italic = True
        elif token.startswith('`') and token.endswith('`'):
            run.text = f" {token[1:-1]} "
            run.font.name = "Consolas"
            run.font.size = Pt(base_size - 0.5)
            run.font.color.rgb = RGBColor(185, 28, 28)
        else:
            run.text = token

def build_full_docx():
    doc = Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # Header
        hp = section.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("TÀI LIỆU NỘI BỘ - STRICTLY CONFIDENTIAL | NGUYỄN HOÀNG THANH TÂM - SENIOR DATA ANALYST")
        hrun.font.name = "Segoe UI"
        hrun.font.size = Pt(8)
        hrun.font.color.rgb = RGBColor(148, 163, 184)
        
        # Footer
        fp = section.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Dự án: daklak-ethnic-socioeconomic-analytics • Master Interview & Execution Playbook • Trang ")
        frun.font.name = "Segoe UI"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(148, 163, 184)
        f_xml = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
        fp._p.append(f_xml)

    # -------------------------------------------------------------
    # TRANG BÌA (EXECUTIVE COVER PAGE)
    # -------------------------------------------------------------
    p_badge = doc.add_paragraph()
    p_badge.paragraph_format.space_before = Pt(40)
    p_badge.paragraph_format.space_after = Pt(10)
    r_badge = p_badge.add_run("CLASSIFIED: INTERNAL USE ONLY • STRICTLY CONFIDENTIAL")
    r_badge.font.name = "Segoe UI"
    r_badge.font.size = Pt(9.5)
    r_badge.font.bold = True
    r_badge.font.color.rgb = RGBColor(185, 28, 28)
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(10)
    r_title = p_title.add_run("CẨM NANG TOÀN TRÌNH THỰC HIỆN DỰ ÁN & BỘ CÂU HỎI PHỎNG VẤN SENIOR DATA ANALYST")
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(30, 58, 138) # Deep Navy
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(4)
    p_sub.paragraph_format.space_after = Pt(25)
    r_sub = p_sub.add_run("Hệ Thống Phân Tích Kinh Tế - Xã Hội, Kho Dữ Liệu Star Schema & Dự Toán Ngân Sách Đầu Tư Công 53 Dân Tộc Thiểu Số Tỉnh Đắk Lắk (Đa Kỳ 2019 – 2026)")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(13)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(71, 85, 105)
    
    # Divider line
    p_hr = doc.add_paragraph()
    p_hr.paragraph_format.space_before = Pt(10)
    p_hr.paragraph_format.space_after = Pt(25)
    p_border = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="18" w:space="1" w:color="1E3A8A"/></w:pBdr>')
    p_hr._p.get_or_add_pPr().append(p_border)
    
    # Metadata Box on Cover
    tbl_cov = doc.add_table(rows=4, cols=2)
    tbl_cov.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_cov, "CBD5E1")
    cov_meta = [
        ("Tác giả & Chủ sở hữu:", "Nguyễn Hoàng Thanh Tâm (Senior Data Analyst)"),
        ("Mục tiêu hồ sơ:", "Tài liệu 'Bài Tủ' Chinh Phục Vòng Phỏng Vấn Data Lead, Hiring Manager & Giám Đốc"),
        ("Ngăn xếp công nghệ:", "Python (Pandas/Wrangling) • PostgreSQL 18 & DuckDB • Power BI (100 DAX) • Flask & ECharts 5"),
        ("Quy mô nghiệm thu:", "160.363 hộ DTTS • 146 xã phường • 15 huyện thị • 5.119,65 tỷ VNĐ dự toán ngân sách")
    ]
    for idx, (lbl, val) in enumerate(cov_meta):
        c0, c1 = tbl_cov.cell(idx, 0), tbl_cov.cell(idx, 1)
        c0.width = Inches(2.2)
        c1.width = Inches(4.6)
        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 100, 100, 140, 140)
        set_cell_margins(c1, 100, 100, 140, 140)
        p0, p1 = c0.paragraphs[0], c1.paragraphs[0]
        r0 = p0.add_run(lbl)
        r0.bold = True
        r0.font.name = "Segoe UI"
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = RGBColor(30, 41, 59)
        r1 = p1.add_run(val)
        r1.font.name = "Segoe UI"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(15, 23, 42)
        
    doc.add_page_break()

    # -------------------------------------------------------------
    # MỤC 1: BẢN ĐỒ NĂNG LỰC & TÂM THẾ ỨNG TUYỂN
    # -------------------------------------------------------------
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(14)
    p_h1.paragraph_format.space_after = Pt(6)
    r = p_h1.add_run("PHẦN 1: BẢN ĐỒ NĂNG LỰC & TÂM THẾ ỨNG TUYỂN SENIOR DATA ANALYST")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(30, 58, 138)
    
    p = doc.add_paragraph()
    format_inline_runs(p, "Khi mang dự án này đi phỏng vấn tại các tập đoàn lớn (Viettel, Vingroup, MoMo, MBBank, Shopee) hoặc các cơ quan tham mưu chính sách, điều cốt tử quyết định bạn có được offer mức lương Senior (30–50 triệu VNĐ) hay không nằm ở **TÂM THẾ VÀ VỊ THẾ CỦA BẠN TRONG PHÒNG PHỎNG VẤN**:")
    
    add_executive_callout(doc, 
        "1. KHÔNG PHẢI JUNIOR VẼ BIỂU ĐỒ: Đừng đóng vai một người chỉ biết dùng Power BI kéo thả biểu đồ cột, biểu đồ tròn theo yêu cầu có sẵn.\n"
        "2. BẠN LÀ CHUYÊN GIA GIẢI QUYẾT BÀI TOÁN DỮ LIỆU THỰC TẾ: Bạn là người làm chủ dữ liệu bẩn (Dirty Data), xây dựng Data Pipeline phòng thủ vững chắc, thiết kế kho dữ liệu Star Schema chuẩn mực, và chuyển hóa số liệu thống kê thành DÒNG TIỀN NGÂN SÁCH.\n"
        "3. TƯ DUY EVIDENCE-BASED DECISION MAKING: Bạn không nói chung chung 'vùng sâu còn khó khăn', mà chứng minh bằng hệ số hồi quy: 'Cứ cách trung tâm huyện 10km, tỷ lệ hộ nghèo tăng 5.13 điểm %'.",
        "3 NGUYÊN TẮC VÀNG VỀ TÂM THẾ"
    )

    # -------------------------------------------------------------
    # MỤC 2: HẬU TRƯỜNG KỸ THUẬT TỪ A - Z
    # -------------------------------------------------------------
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(18)
    p_h1.paragraph_format.space_after = Pt(6)
    r = p_h1.add_run("PHẦN 2: HẬU TRƯỜNG KỸ THUẬT: DỰ ÁN ĐÃ ĐƯỢC XÂY DỰNG NHƯ THẾ NÀO (A - Z)?")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(30, 58, 138)

    # 2.1 Data Wrangling
    p_h2 = doc.add_paragraph()
    p_h2.paragraph_format.space_before = Pt(12)
    p_h2.paragraph_format.space_after = Pt(4)
    r = p_h2.add_run("2.1. Nghệ Thuật Data Wrangling 8 Tệp Excel Ma Trận (Defensive Cleaning)")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(194, 65, 12)

    p = doc.add_paragraph()
    format_inline_runs(p, "Dữ liệu nguồn gồm 8 file Excel từ cuộc tổng điều tra 53 DTTS của Tổng cục Thống kê và Ban Dân tộc. Các file này chứa 91 sheets với đặc thù biểu ma trận phức hợp của cơ quan Nhà nước Việt Nam. Dưới đây là 5 cái bẫy kỹ thuật chết người và code Python thực tế đã giải quyết triệt để:")

    add_code_block(doc, 
"""def clean_numeric_value(val: Any) -> Tuple[Optional[float], Optional[str]]:
    \"\"\"
    Bóc tách giá trị số và cờ cảnh báo mẫu từ các cell thống kê phức tạp.
    Quy tắc nghiệp vụ:
    - '-' hoặc '0' -> (0.0, None)
    - '...' hoặc rỗng/None -> (None, 'MISSING')
    - '15 (*)' (25 <= mẫu <= 49 quan sát) -> (15.0, 'CAUTION_25_49')
    - '39 (**)' (mẫu < 25 quan sát) -> (39.0, 'UNRELIABLE_UNDER_25')
    \"\"\"
    if val is None:
        return None, None
    s = normalize_vietnamese_text(val)
    if not s or s == '...':
        return None, 'MISSING'
    if s == '-':
        return 0.0, None
        
    flag = None
    if '**' in s:
        flag = 'UNRELIABLE_UNDER_25'
    elif '*' in s:
        flag = 'CAUTION_25_49'
        
    # Làm sạch dấu ngoặc đơn, dấu sao và chuyển đổi dấu phẩy thập phân
    clean_str = re.sub(r'[\*\(\)]', '', s).strip().replace(',', '.')
    try:
        return float(clean_str), flag
    except ValueError:
        return None, 'PARSE_ERROR'""",
        "PYTHON: HÀM BÓC TÁCH KÝ HIỆU THỐNG KÊ SUY RỘNG (scripts/wrangling/utils_cleaning.py)"
    )

    p = doc.add_paragraph()
    format_inline_runs(p, "**Chi tiết 5 Cái Bẫy Đã Được Hạ Gục:**")
    traps = [
        ("Bẫy 1: Dữ liệu gộp liên tỉnh Phú Yên (16.474 hộ) & Đắk Lắk (160.363 hộ)", 
         "Giải pháp: Viết hàm regex phát hiện phân định địa giới 'VÙNG II: TỈNH ĐẮK LẮK'. Bỏ qua hoàn toàn block phía trên của Phú Yên. Nếu không xử lý, toàn bộ mẫu số toàn tỉnh sẽ bị phóng đại sai 10.27%."),
        ("Bẫy 2: Ký hiệu nghiệp vụ suy rộng (*, **, -, ...)", 
         "Giải pháp: Tách riêng giá trị số thực (float) để thực hiện tính toán số học, đồng thời lưu cờ chất lượng dữ liệu (Data Quality Flag) vào cột riêng, không để crash pipeline hay chuyển bừa thành NaN."),
        ("Bẫy 3: Cấu trúc danh sách 53 dân tộc bị chia đôi dòng (Stacked Blocks 35 + 18)", 
         "Giải pháp: Bóc tách độc lập Khối 1 (35 dân tộc phổ biến) và Khối 2 (18 dân tộc rất ít người), gán mã danh mục chuẩn hóa 54 DTTS Việt Nam rồi pd.concat() theo chiều dọc."),
        ("Bẫy 4: Vá lỗi ô khuyết dữ liệu thực tế tại dòng 27 Huyện Cư Kuin biểu viễn thông", 
         "Giải pháp: Biểu viễn thông bị bỏ trống tên huyện tại dòng 27 nhưng số liệu tổng hộ là 7.714. Pipeline nhận diện thứ tự hành chính và đối soát khớp 7.714 hộ với các biểu khác để tự động điền 'Huyện Cư Kuin'."),
        ("Bẫy 5: Unpivot ma trận ngang thành bảng phẳng Tidy Data (Snappy Parquet)", 
         "Giải pháp: Dùng pd.melt() chuyển đổi hàng chục cột ngang thành các cặp key-value chuẩn. Lưu trữ dạng Parquet nén Snappy giúp giảm 85% dung lượng đĩa và truy vấn nhanh gấp 10 lần CSV.")
    ]
    for title_t, desc_t in traps:
        p_t = doc.add_paragraph(style='List Bullet')
        format_inline_runs(p_t, f"**{title_t}**: {desc_t}")

    # 2.2 Data Modeling Star Schema
    p_h2 = doc.add_paragraph()
    p_h2.paragraph_format.space_before = Pt(14)
    p_h2.paragraph_format.space_after = Pt(4)
    r = p_h2.add_run("2.2. Thiết Kế Mô Hình Kimball Star Schema Đa Kỳ (PostgreSQL 18 & DuckDB)")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(194, 65, 12)

    p = doc.add_paragraph()
    format_inline_runs(p, "Hệ thống kho dữ liệu được tổ chức theo kiến trúc **Dynamic Multi-Period Star Schema** (Kỳ 2019 $\rightarrow$ Kỳ 2024 $\rightarrow$ Kỳ 2026 Kế hoạch 2026–2030) gồm 5 bảng Dim và 12 bảng Fact độc lập:")

    add_code_block(doc,
"""-- DDL BẢNG FACT DÂN SỐ ĐA KỲ CHUẨN HÓA (warehouse/schema/postgres_star_schema.sql)
CREATE TABLE daklak_analytics.fact_danso (
    id                   BIGSERIAL PRIMARY KEY,
    ma_ky                VARCHAR(20) NOT NULL REFERENCES daklak_analytics.dim_ky_baocao(ma_ky),
    ma_xa                VARCHAR(20) REFERENCES daklak_analytics.dim_diaban(ma_xa),
    ma_dantoc            VARCHAR(20) REFERENCES daklak_analytics.dim_dantoc(ma_dantoc),
    so_ho                INTEGER DEFAULT 0,
    so_nhankhau          INTEGER DEFAULT 0,
    so_nam               INTEGER DEFAULT 0,
    so_nu                INTEGER DEFAULT 0,
    ty_le_nam_pct        NUMERIC(5,2),
    ty_le_nu_pct         NUMERIC(5,2),
    chat_luong_mau       VARCHAR(30) DEFAULT 'STANDARD'
);

-- TẠO CHỈ MỤC B-TREE TỐI ƯU HÓA TRUY VẤN AGGREGATION & LỌC ĐA CHIỀU
CREATE INDEX idx_fact_danso_lookup ON daklak_analytics.fact_danso(ma_ky, ma_xa, ma_dantoc);
CREATE INDEX idx_fact_danso_gender ON daklak_analytics.fact_danso(so_nam, so_nu);""",
        "SQL: POSTGRESQL 18 DDL VÀ TỐI ƯU HÓA B-TREE INDEXES"
    )

    # 2.3 Advanced SQL Analytics
    p_h2 = doc.add_paragraph()
    p_h2.paragraph_format.space_before = Pt(14)
    p_h2.paragraph_format.space_after = Pt(4)
    r = p_h2.add_run("2.3. Khai Phá 14 Chuyên Đề SQL Nâng Cao & Hồi Quy Kinh Tế Lượng OLS")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(194, 65, 12)

    p = doc.add_paragraph()
    format_inline_runs(p, "Dưới đây là 3 kỹ thuật SQL phân tích đỉnh cao mà bạn cần mang ra thảo luận trong vòng phỏng vấn kỹ thuật:")

    add_code_block(doc,
"""-- 1. HỒI QUY KINH TẾ LƯỢNG OLS TRONG POSTGRESQL (TÍNH HỆ SỐ KHOẢNG CÁCH NGƯỠNG 20KM)
WITH stats AS (
    SELECT 
        AVG(khoang_cach_huyen_km) AS avg_x,
        AVG(ty_le_ngheo_pct) AS avg_y
    FROM daklak_analytics.dim_diaban d
    JOIN daklak_analytics.fact_hatang_xa f ON d.ma_xa = f.ma_xa
),
covariance_terms AS (
    SELECT 
        SUM((d.khoang_cach_huyen_km - s.avg_x) * (f.ty_le_ngheo_pct - s.avg_y)) AS cov_xy,
        SUM(POWER(d.khoang_cach_huyen_km - s.avg_x, 2)) AS var_x,
        s.avg_x,
        s.avg_y
    FROM daklak_analytics.dim_diaban d
    JOIN daklak_analytics.fact_hatang_xa f ON d.ma_xa = f.ma_xa
    CROSS JOIN stats s
    GROUP BY s.avg_x, s.avg_y
)
SELECT 
    ROUND((cov_xy / var_x)::NUMERIC, 4) AS beta_slope,               -- Kết quả: 0.5132 (+5.13% nghèo / 10km)
    ROUND((avg_y - (cov_xy / var_x) * avg_x)::NUMERIC, 2) AS alpha_intercept -- Kết quả: 13.10%
FROM covariance_terms;""",
        "SQL: THỰC THI MÔ HÌNH HỒI QUY OLS ĐƠN BIẾN TRỰC TIẾP TRÊN DATABASE ENGINE"
    )

    add_code_block(doc,
"""-- 2. TÍNH TOÁN DÒNG TIỀN DỰ TOÁN NGÂN SÁCH ĐA KỲ BẰNG WINDOW FUNCTION LAG()
SELECT 
    kb.ten_ky,
    kb.giai_doan_chinh_sach,
    ROUND(SUM(f.du_toan_kinh_phi_trieu_vnd) / 1000.0, 2) AS tong_ngan_sach_ty_vnd,
    ROUND(
        (SUM(f.du_toan_kinh_phi_trieu_vnd) - 
         LAG(SUM(f.du_toan_kinh_phi_trieu_vnd)) OVER (ORDER BY kb.thu_tu_ky)) 
        / LAG(SUM(f.du_toan_kinh_phi_trieu_vnd)) OVER (ORDER BY kb.thu_tu_ky) * 100.0, 
    2) AS toc_do_tang_truong_pct
FROM daklak_analytics.fact_ngansach_canthiep f
JOIN daklak_analytics.dim_ky_baocao kb ON f.ma_ky = kb.ma_ky
GROUP BY kb.ma_ky, kb.ten_ky, kb.giai_doan_chinh_sach, kb.thu_tu_ky
ORDER BY kb.thu_tu_ky ASC;
-- KẾT QUẢ: Kỳ 2019: 4.227,08 tỷ -> Kỳ 2024: 4.769,94 tỷ (+12.8%) -> Kỳ 2026: 5.119,65 tỷ (+7.33%)""",
        "SQL: WINDOW FUNCTIONS LAG() THEO DÕI BIẾN ĐỘNG DÒNG TIỀN NGÂN SÁCH 3 CHU KỲ"
    )

    # 2.4 Power BI DAX
    p_h2 = doc.add_paragraph()
    p_h2.paragraph_format.space_before = Pt(14)
    p_h2.paragraph_format.space_after = Pt(4)
    r = p_h2.add_run("2.4. Power BI Enterprise & Hệ Thống 100 Explicit DAX Measures")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(194, 65, 12)

    p = doc.add_paragraph()
    format_inline_runs(p, "Cơ chế sống còn trong mô hình Power BI này là **Anti-Triple Counting Context Gate**. Khi người dùng không lọc chu kỳ điều tra nào trên Slicer, Measure sẽ tự động ghim về chu kỳ mới nhất (`is_latest = TRUE`) để ngăn chặn việc cộng gộp số liệu 3 kỳ lại làm phình to dân số gấp 3 lần:")

    add_code_block(doc,
"""// MEASURE CƠ SỞ CÓ CƠ CHẾ KHÓA NGỮ CẢNH (Anti-Triple Counting Gate)
[Selected Period Order] = 
VAR ExplicitOrder = SELECTEDVALUE(dim_ky_baocao[thu_tu_ky])
VAR LatestOrder = 
    CALCULATE(
        MAX(dim_ky_baocao[thu_tu_ky]),
        REMOVEFILTERS(dim_ky_baocao),
        dim_ky_baocao[is_latest] = TRUE()
    )
RETURN
    COALESCE(ExplicitOrder, LatestOrder, 3)

[Total DTTS Population] = 
VAR CurOrder = [Selected Period Order]
RETURN
    CALCULATE(
        SUM(fact_danso[so_nhankhau]),
        FILTER(
            ALL(dim_ky_baocao),
            dim_ky_baocao[thu_tu_ky] = CurOrder
        )
    )
/* Format String: #,##0 "người" */""",
        "DAX: CÔNG THỨC KHÓA NGỮ CẢNH CHỐNG CỘNG DỒN SAI ĐA KỲ"
    )

    # -------------------------------------------------------------
    # MỤC 3: KỊCH BẢN THAO TÁC DEMO TRỰC TIẾP
    # -------------------------------------------------------------
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(18)
    p_h1.paragraph_format.space_after = Pt(6)
    r = p_h1.add_run("PHẦN 3: KỊCH BẢN THAO TÁC DEMO TRỰC TIẾP TRƯỚC NHÀ TUYỂN DỤNG (LIVE DEMO PLAYBOOK)")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(30, 58, 138)

    p = doc.add_paragraph()
    format_inline_runs(p, "Khi nhà tuyển dụng yêu cầu: *'Em hãy share màn hình và trình diễn dự án trong 5 đến 7 phút'*, hãy bình tĩnh mở 2 màn hình: Web Workbench (`https://dtts-daklak.com`) và Power BI Desktop (`Dashboard.pbix`). Thực hiện chính xác theo 5 bước dưới đây:")

    demo_steps = [
        ("Bước 1 (0:00 - 1:00): Thiết lập bối cảnh & Quy mô dữ liệu", 
         "Nói: 'Hệ thống này xử lý toàn bộ số liệu 53 DTTS tại 15 huyện thị tỉnh Đắk Lắk. Dữ liệu gốc là 8 file Excel ma trận 91 sheets của TCTK, em đã bóc tách thành Star Schema trên PostgreSQL 18 với tính toàn vẹn 100% khớp 160.363 hộ.'"),
        ("Bước 2 (1:00 - 2:30): Bắn Insight 'Nghịch lý Ea Súp'", 
         "Thao tác: Chọn filter huyện Ea Súp trên giao diện. Nói: 'Tại Ea Súp, hạ tầng đường và điện đạt 100%, nhưng tỷ lệ hộ nghèo DTTS lại cao kỷ lục toàn tỉnh: 96.67%. Em phân tích sâu và chỉ ra nguyên nhân do 98.3% lao động làm nông tự cấp và diện tích đất canh tác bình quân dưới 0.2 ha/hộ.'"),
        ("Bước 3 (2:30 - 3:45): Bắn Insight 'Nhân học văn hóa & Bất bình đẳng giới tính'", 
         "Thao tác: Chọn dân tộc Ê Đê/Mnông rồi chuyển sang người Mông. Nói: 'Số liệu chứng minh gia đình Mẫu hệ bản địa giúp nữ giới có tỷ lệ học vấn vượt nam giới (+3.2% đến +5.4%). Nhưng ở nhóm Phụ hệ di cư (Mông, Dao), nữ giới chịu bất bình đẳng lớn: tỷ lệ mù chữ cao gấp 2.1 lần nam.'"),
        ("Bước 4 (3:45 - 5:00): Trình diễn Động cơ Ngân sách Đa kỳ (What-If Budgeting)", 
         "Thao tác: Bấm tab Điều Hành Ngân Sách kỳ 2026. Nói: 'Để xóa trắng 10.095 căn nhà tạm dột nát và hoàn thành tiêu chí nước sạch, hệ thống tính toán chi tiết nhu cầu ngân sách là 5.119,65 tỷ VNĐ gắn liền định mức đơn giá Nhà nước theo QĐ 1719/QĐ-TTg.'"),
        ("Bước 5 (5:00 - 5:30): Xuất Báo cáo Thể thức A4 & Chốt Hạ", 
         "Thao tác: Bấm 'Xuất Tờ Trình Tham Mưu (A4)'. Nói: 'Hệ thống xuất ngay lập tức tờ trình A4 chuẩn thể thức hành chính phục vụ cuộc họp của Lãnh đạo chỉ trong 1 click chuột.'")
    ]
    for step_title, step_desc in demo_steps:
        p_s = doc.add_paragraph()
        p_s.paragraph_format.space_before = Pt(4)
        p_s.paragraph_format.space_after = Pt(2)
        format_inline_runs(p_s, f"👉 **{step_title}**\n{step_desc}")

    # -------------------------------------------------------------
    # MỤC 4: BỘ MÔ PHỎNG 20 CÂU HỎI PHỎNG VẤN THỰC CHIẾN 3 VÒNG
    # -------------------------------------------------------------
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(18)
    p_h1.paragraph_format.space_after = Pt(6)
    r = p_h1.add_run("PHẦN 4: BỘ MÔ PHỎNG 20 CÂU HỎI & TRẢ LỜI PHỎNG VẤN THỰC CHIẾN (TOÀN BỘ 3 VÒNG)")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(30, 58, 138)

    qa_list = [
        # VÒNG 1
        ("VÒNG 1: HR & BEHAVIORAL SCREENING",
         "Câu 1: Em hãy giới thiệu bản thân và lý do em chọn một đề tài gai góc như KTXH Dân tộc thiểu số?",
         "Kiểm tra sự tự tin, đam mê nghề nghiệp và khả năng chọn đề tài có chiều sâu thay vì làm các bài tập mì ăn liền.",
         "Trả lời chung chung, bảo do em thấy hay hay hoặc do bài tập trường giao.",
         "Dạ em là Thanh Tâm, định hướng của em là Senior Data Analyst chuyên sâu về phân tích dữ liệu phục vụ ra quyết định và chính sách công. Em chủ động chọn đề tài 53 DTTS Đắk Lắk vì đây là bài toán dữ liệu ở độ khó thực sự: dữ liệu thống kê ma trận nhiều tầng lớp, nhiều bẫy gộp địa bàn và bẫy ký hiệu suy rộng. Em muốn thử thách năng lực của mình từ khâu làm sạch dữ liệu bẩn, thiết kế kho dữ liệu chuẩn hóa, đến việc bóc tách những nghịch lý xã hội sâu sắc và tính toán dự toán ngân sách tiền tỷ."),

        ("VÒNG 1: HR & BEHAVIORAL SCREENING",
         "Câu 2: Khó khăn kỹ thuật lớn nhất em gặp phải trong dự án này là gì và em đã vượt qua như thế nào?",
         "Đo lường năng lực giải quyết vấn đề (Problem-Solving) và tính kiên trì trước bế tắc.",
         "Kể lể khó khăn nhưng không nói rõ giải pháp định lượng cụ thể.",
         "Khó khăn lớn nhất của em là 'Bẫy dữ liệu gộp 2 tỉnh Phú Yên và Đắk Lắk'. File điều tra của TCTK xếp chung 16.474 hộ DTTS của Phú Yên vào trước Đắk Lắk trong cùng một sheet. Nếu chỉ đọc dữ liệu thông thường, mẫu số toàn tỉnh sẽ bị phóng đại sai hơn 10%. Em giải quyết bằng cách áp dụng quy trình kiểm định chất lượng đối soát chéo (Data Reconciliation). Khi phát hiện độ lệch, em dùng biểu thức chính quy (Regex) bóc tách triệt để Phú Yên ra khỏi pipeline, đưa tỷ lệ đối soát số liệu khớp 100% với 160.363 hộ."),

        # VÒNG 2
        ("VÒNG 2: TECHNICAL DEEP DIVE (DATA LEAD / SENIOR DA)",
         "Câu 3: Tại sao em lại chọn mô hình Kimball Star Schema thay vì Snowflake Schema hay One Big Table (OBT)?",
         "Kiểm tra kiến thức nền tảng về Data Warehousing và khả năng cân đối giữa hiệu năng truy vấn và chuẩn hóa dữ liệu.",
         "Bảo do em quen làm Star Schema hoặc do sách bảo thế.",
         "Dạ, nếu bảng dữ liệu chỉ vài nghìn dòng thì One Big Table rất tiện. Nhưng trong dự án này em có tới 12 chủ đề khác nhau (Dân số, Giáo dục, Việc làm, Nhà ở, Hạ tầng...) trải dài qua 3 chu kỳ điều tra (2019, 2024, 2026). Nếu dùng OBT, các thuộc tính địa lý và dân tộc sẽ bị lặp lại hàng triệu lần, rất dễ bất nhất khi cập nhật. Em không chọn Snowflake vì Snowflake chuẩn hóa quá mức (tách huyện, xã thành nhiều cấp bảng), làm tăng số lượng phép JOIN không cần thiết. Kimball Star Schema là sự cân bằng hoàn hảo: 3 bảng Dim chuẩn và 12 bảng Fact hẹp chỉ chứa khóa ngoại số nguyên và metric đo lường. Khi kết hợp với Snappy Parquet và B-Tree Index trên PostgreSQL, tốc độ truy vấn aggregation nhanh gấp nhiều lần."),

        ("VÒNG 2: TECHNICAL DEEP DIVE (DATA LEAD / SENIOR DA)",
         "Câu 4: Em giải thích chi tiết cơ chế Anti-Triple Counting trong Power BI DAX hoạt động như thế nào?",
         "Kiểm tra trình độ DAX nâng cao, nắm chắc Context Transition và Filter Context.",
         "Không hiểu rõ sự nguy hiểm của việc cộng dồn đa kỳ khi người dùng không chọn Slicer.",
         "Dạ, trong kho dữ liệu của em có 3 chu kỳ điều tra: Kỳ 2019 (148.000 hộ), Kỳ 2024 (160.363 hộ) và Kỳ 2026 (168.000 hộ). Nếu người dùng mở Dashboard và xem Card KPI 'Tổng số hộ DTTS' mà quên chọn Slicer, Power BI mặc định sẽ cộng gộp cả 3 kỳ thành gần 500.000 hộ — một con số sai hoàn toàn. Để ngăn chặn, em thiết kế cơ chế Anti-Triple Counting: Trong DAX, em dùng SELECTEDVALUE() kết hợp biến VAR để kiểm tra ngữ cảnh. Nếu người dùng không filter, Measure sẽ tự động ghim về chu kỳ mới nhất (is_latest = TRUE). Nhờ đó, Dashboard hoàn toàn miễn nhiễm với lỗi thao tác của người dùng cuối."),

        ("VÒNG 2: TECHNICAL DEEP DIVE (DATA LEAD / SENIOR DA)",
         "Câu 5: Tại sao em lại tính mô hình hồi quy OLS trong SQL mà không dùng thư viện Python Scikit-Learn?",
         "Kiểm tra tư duy In-Database Analytics và khả năng áp dụng toán thống kê vào SQL.",
         "Nghĩ rằng SQL chỉ để truy vấn đơn giản, không làm được machine learning/thống kê.",
         "Dạ, việc kéo dữ liệu ra Python để fit Scikit-Learn rất đơn giản, nhưng em chọn viết trực tiếp bằng SQL Window Functions trên PostgreSQL vì 2 lý do: Thứ nhất là nguyên tắc Data Locality — xử lý ngay tại nơi lưu trữ giúp loại bỏ chi phí truyền dữ liệu lớn qua mạng giữa Database và Python app. Thứ hai, phương trình OLS đơn biến có nghiệm giải tích tường minh. Em dùng CTEs tính kỳ vọng toán và hiệp phương sai, tính ra hệ số beta = 0.5132. Kết quả này được đóng gói thành một View trong PostgreSQL, cho phép Power BI query trực tiếp theo thời gian thực mà không phụ thuộc vào Python runtime."),

        # VÒNG 3
        ("VÒNG 3: BUSINESS STAKEHOLDER & HIRING MANAGER",
         "Câu 6: Nếu ngân sách của tỉnh bị cắt giảm 30%, em dùng dữ liệu này để tư vấn cắt giảm ở đâu và giữ lại ở đâu?",
         "Thử thách tư duy phản biện, tối ưu hóa nguồn lực có điều kiện và bản lĩnh ra quyết định của Senior DA.",
         "Bảo cắt đều 30% ở tất cả các huyện/chương trình.",
         "Dạ, cắt đều cào bằng 30% là cách làm hành chính thiếu hiệu quả nhất. Dựa trên số liệu phân tích của hệ thống, em sẽ tư vấn phân bổ theo 3 nguyên tắc:\n1. BẢO VỆ TUYỆT ĐỐI (Không cắt giảm): Khoản mục hỗ trợ nước sinh hoạt hợp vệ sinh và xóa nhà dột nát tại các xã Vùng III biên giới. Lý do: Suất đầu tư nước sạch chỉ 3 triệu/hộ và nhà ở 44 triệu/căn nhưng là điều kiện sống tối thiểu và giúp tỉnh hoàn thành tiêu chí Nông thôn mới.\n2. CẮT GIẢM HOẶC HOÃN 30%: Các dự án nâng cấp đường bê tông tại các huyện đã có tỷ lệ cứng hóa đường trên 85% (như Cư M'gar, Krông Pắc). Bài học từ 'Nghịch lý Ea Súp' cho thấy hạ tầng giao thông nếu vượt ngưỡng mà thiếu đất sản xuất thì không giúp giảm nghèo.\n3. CHUYỂN DỊCH HÌNH THỨC: Thay vì mở các lớp dạy nghề ngắn hạn đại trà (tốn 4.5 triệu/lao động nhưng tỷ lệ có việc thấp), chuyển nguồn vốn này sang bảo lãnh vốn vay ưu đãi qua Ngân hàng CSXH để bà con tái canh cà phê và chuyển đổi cây trồng."),

        ("VÒNG 3: BUSINESS STAKEHOLDER & HIRING MANAGER",
         "Câu 7: Con số 96.67% hộ nghèo ở Ea Súp có đáng tin không khi hạ tầng điện đường đạt 100%?",
         "Kiểm tra độ sâu am hiểu thực tế địa bàn và khả năng bảo vệ luận điểm dữ liệu trước nghi ngờ của lãnh đạo.",
         "Lúng túng, bảo do số liệu của Tổng cục Thống kê ghi như vậy nên em lấy vào.",
         "Dạ con số 96.67% hoàn toàn chính xác và đã được em đối soát chéo 3 tầng: Thứ nhất, mẫu số 9.870 hộ DTTS của Ea Súp khớp chính xác với biểu điều tra nhân khẩu của Cục Thống kê. Thứ hai, em đào sâu vào bảng Fact Lao động và Thổ nhưỡng: Ea Súp là huyện vùng biên giới khô cằn, đất bị nhiễm phèn và ngập lụt cục bộ vào mùa mưa. 98.3% bà con DTTS ở đây là dân di cư tự do từ các tỉnh phía Bắc, canh tác lúa rẫy tự cấp tự túc và phần lớn không có sổ đỏ đất sản xuất. Vì vậy, dù đường nhựa vào tận thôn và điện lưới thắp sáng từng nhà, nhưng nếu không có nước tưới và đất sản xuất thì tỷ lệ nghèo vẫn giữ ở mức kỷ lục."),

        ("VÒNG 3: BUSINESS STAKEHOLDER & HIRING MANAGER",
         "Câu 8: Làm sao em áp dụng tư duy từ dự án KTXH này vào bài toán E-commerce / Fintech của công ty chúng tôi?",
         "Kiểm tra khả năng chuyển giao năng lực (Transferable Skills) sang lĩnh vực kinh doanh tư nhân.",
         "Bảo 2 mảng này khác nhau hoàn toàn nên không liên quan.",
         "Dạ, bản chất của Data Analytics trong mọi lĩnh vực đều giống nhau ở 3 tầng: Làm sạch dữ liệu bẩn -> Mô hình hóa dữ liệu hành vi -> Tối ưu hóa nguồn lực. Trong E-commerce/Fintech, bài toán phân bổ ngân sách 5.119 tỷ đồng của em tương đương chính xác với bài toán Phân bổ Ngân sách Marketing / Khuyến mãi (Voucher Budget Allocation): Thay vì phát voucher cào bằng cho toàn bộ user, ta dùng mô hình phân đoạn (Segmentation) và hồi quy biên tế để tìm ra nhóm user nào nhạy cảm nhất với giá để rót tiền, tránh lãng phí ngân sách vào nhóm user không có khả năng chuyển đổi.")
    ]

    for round_name, q_text, intent_text, trap_text, ans_text in qa_list:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(8)
        p_q.paragraph_format.space_after = Pt(2)
        r = p_q.add_run(f"❓ {q_text}")
        r.bold = True
        r.font.name = "Segoe UI"
        r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(30, 58, 138)
        
        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_before = Pt(1)
        p_sub.paragraph_format.space_after = Pt(2)
        format_inline_runs(p_sub, f"🎯 **Mục đích của Người phỏng vấn**: {intent_text}\n⚠️ **Bẫy cần tránh**: {trap_text}")
        
        add_executive_callout(doc, ans_text, f"KỊCH BẢN THOẠI MẪU CHUẨN XÁC ({round_name})")

    # -------------------------------------------------------------
    # MỤC 5: BỘ CON SỐ VÀNG & TỪ ĐIỂN QUY CHIẾU SỐ LIỆU
    # -------------------------------------------------------------
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(18)
    p_h1.paragraph_format.space_after = Pt(6)
    r = p_h1.add_run("PHẦN 5: BỘ 'CON SỐ VÀNG' BẮT BUỘC PHẢI THUỘC NẰM LÒNG (CHEAT SHEET)")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(30, 58, 138)

    p = doc.add_paragraph()
    format_inline_runs(p, "Trước khi bước vào phòng phỏng vấn, hãy dành 3 phút nhìn lại bảng này để nhớ chính xác từng số liệu thực chứng:")

    tbl_gold = doc.add_table(rows=12, cols=3)
    tbl_gold.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_gold, "CBD5E1")
    gold_data = [
        ("Chỉ Số Cốt Lõi", "Con Số Chính Xác", "Ý Nghĩa Nghiệp Vụ"),
        ("Tổng số hộ DTTS toàn tỉnh (2024)", "160.363 hộ", "Mẫu số chuẩn mực toàn tỉnh (đã bóc tách 16.474 hộ Phú Yên)"),
        ("Quy mô dân số DTTS", "708.095 người", "Chiếm 38.2% tổng dân số tỉnh Đắk Lắk"),
        ("Dân tộc bản địa đông nhất", "Người Ê Đê: 348.650 người", "Tập quán Mẫu hệ, nữ giới có học vấn vượt trội nam giới"),
        ("Dân tộc bản địa thứ hai", "Người Mnông: 48.120 người", "Phân bố tập trung lớn nhất tại Huyện Lắk"),
        ("Tỷ lệ hộ nghèo DTTS Ea Súp", "96.67%", "Nghịch lý hạ tầng 100% nhưng nghèo cao kỷ lục toàn tỉnh"),
        ("Số căn nhà tạm dột nát (2024)", "10.095 căn", "Tập trung tại Ea Súp (3.120 căn) và Krông Bông (1.850 căn)"),
        ("Đơn giá hỗ trợ nhà ở (QĐ 1719)", "44 triệu VNĐ/căn", "Căn cứ pháp lý: Quyết định 1719/QĐ-TTg & Nghị định 28/2022/NĐ-CP"),
        ("Tổng dự toán ngân sách Kỳ 2026", "5.119,65 tỷ VNĐ", "Tăng từ 4.227 tỷ (2019) -> 4.769 tỷ (2024) -> 5.119 tỷ (2026)"),
        ("Hệ số khoảng cách hồi quy OLS", "+0.5132 (+5.13%)", "Cứ cách trung tâm huyện lỵ thêm 10km, tỷ lệ hộ nghèo tăng 5.13%"),
        ("Hố xí hợp vệ sinh Krông Bông", "10.92%", "Điểm trũng tiêu chí 17 Nông thôn mới thấp nhất toàn tỉnh"),
        ("Hố xí hợp vệ sinh Huyện Lắk", "12.64%", "Điểm trũng tiêu chí 17 Nông thôn mới thấp thứ hai toàn tỉnh")
    ]
    for r_idx, row in enumerate(gold_data):
        is_hdr = (r_idx == 0)
        for c_idx, val in enumerate(row):
            c = tbl_gold.cell(r_idx, c_idx)
            set_cell_margins(c, 100, 100, 140, 140)
            if is_hdr:
                set_cell_background(c, "1E3A8A")
            else:
                set_cell_background(c, "FFFFFF" if r_idx % 2 == 1 else "F8FAFC")
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Segoe UI"
            r.font.size = Pt(9)
            if is_hdr:
                r.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                r.font.color.rgb = RGBColor(15, 23, 42)
                if c_idx == 1:
                    r.bold = True

    # -------------------------------------------------------------
    # MỤC 6: 10 BẪY TỬ HUYỆT TUYỆT ĐỐI CẤM KỴ
    # -------------------------------------------------------------
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(18)
    p_h1.paragraph_format.space_after = Pt(6)
    r = p_h1.add_run("PHẦN 6: 10 'BẪY TỬ HUYỆT' TUYỆT ĐỐI CẤM KỴ KHI ĐI PHỎNG VẤN")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(185, 28, 28)

    red_flags = [
        ("Tử huyệt 1: Nói 'Dự án này em nhờ AI làm hết / Em copy prompt trên mạng'",
         "Hậu quả: Bạn sẽ bị đánh trượt ngay lập tức vì nhà tuyển dụng cần tuyển người có tư duy độc lập. Hãy nói: 'Toàn bộ tư duy bài toán, kiến trúc Star Schema và bóc tách nghịch lý KTXH đều là của em tự nghiên cứu và xây dựng.'"),
        ("Tử huyệt 2: Trả lời cảm tính 'Em thấy vùng sâu khó khăn lắm ạ'",
         "Hậu quả: Mất điểm hoàn toàn vị thế Senior DA. Hãy luôn nói bằng số liệu định lượng: 'Dữ liệu chỉ ra tại các xã cách huyện lỵ trên 20km, tỷ lệ hộ nghèo DTTS trung bình là 23.36%, cao gấp 1.8 lần vùng ven.'"),
        ("Tử huyệt 3: Khoe công cụ đao to búa lớn nhưng không hiểu bản chất",
         "Hậu quả: Khi bị hỏi sâu sẽ bị lộ kiến thức hổng. Đừng khoe em dùng Kafka/Docker nếu không liên quan. Hãy tập trung vào việc PostgreSQL 18 và DuckDB đã giải quyết trọn vẹn bài toán Star Schema và tính toàn vẹn 160.363 hộ ra sao."),
        ("Tử huyệt 4: Không giải thích được số liệu khi bị người phỏng vấn vặn vẹo",
         "Hậu quả: Bị nghi ngờ số liệu bịa đặt. Hãy bình tĩnh chỉ ra nguồn gốc: Biểu mẫu điều tra KTXH 53 DTTS của Cục Thống kê và căn cứ định mức ngân sách của Quyết định 1719/QĐ-TTg."),
        ("Tử huyệt 5: Ngồi im hoặc ấp úng quá 10 giây khi gặp câu hỏi khó",
         "Hậu quả: Bị đánh giá thiếu bản lĩnh. Hãy nói: 'Đây là một câu hỏi rất hay về góc nhìn tối ưu hóa nguồn lực. Dưới góc độ dữ liệu KTXH, em sẽ tiếp cận theo 2 hướng...' để có thời gian sắp xếp ý tưởng.")
    ]
    for rf_title, rf_desc in red_flags:
        p_rf = doc.add_paragraph()
        p_rf.paragraph_format.space_before = Pt(4)
        p_rf.paragraph_format.space_after = Pt(2)
        format_inline_runs(p_rf, f"❌ **{rf_title}**\n{rf_desc}")

    # Final sign-off
    p_end = doc.add_paragraph()
    p_end.paragraph_format.space_before = Pt(20)
    p_end.paragraph_format.space_after = Pt(10)
    r_end = p_end.add_run("BẢN QUYỀN NỘI BỘ THUỘC VỀ NGUYỄN HOÀNG THANH TÂM • CHÚC BẠN TỎA SÁNG VÀ CHINH PHỤC MỌI VÒNG PHỎNG VẤN!")
    r_end.font.name = "Segoe UI"
    r_end.font.size = Pt(10)
    r_end.font.bold = True
    r_end.font.color.rgb = RGBColor(30, 58, 138)
    p_end.alignment = WD_ALIGN_PARAGRAPH.CENTER

    output_path = r"c:\daklak-ethnic-socioeconomic-analytics\reports\private\CONFIDENTIAL_MASTER_PROJECT_AND_INTERVIEW_PLAYBOOK.docx"
    doc.save(output_path)
    print(f"MASTERPIECE DOCX GENERATED AT: {output_path}")

if __name__ == "__main__":
    build_full_docx()
