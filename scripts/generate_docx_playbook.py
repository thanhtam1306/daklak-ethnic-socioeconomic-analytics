import re
import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    """Set cell padding in twips (1/20 of a pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1"):
    """Apply clean, modern borders to table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="{color}"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/><w:insideV w:val="none"/><w:left w:val="none"/><w:right w:val="none"/></w:tblBorders>')
    tblPr.append(borders)

def add_callout(doc, text, title=""):
    """Add an executive callout box with a shaded background and accent border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=220, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="1E3A8A"/><w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    if title:
        run_t = p.add_run(f"📌 {title}\n")
        run_t.bold = True
        run_t.font.name = "Segoe UI"
        run_t.font.size = Pt(10.5)
        run_t.font.color.rgb = RGBColor(30, 58, 138)
        
    run = p.add_run(text)
    run.font.name = "Segoe UI"
    run.font.size = Pt(9.5)
    run.font.italic = True
    run.font.color.rgb = RGBColor(51, 65, 85)
    
    # spacing after table
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)

def format_inline_runs(paragraph, text, base_font="Segoe UI", base_size=10, base_color=RGBColor(30, 41, 59)):
    """Parse basic markdown inline tags: **bold**, *italic*, `code`."""
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

def convert_markdown_to_docx(md_path, docx_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    doc = Document()
    
    # Page setup (Letter / A4, 0.8 inch margins)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # Header
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("TÀI LIỆU NỘI BỘ - STRICTLY CONFIDENTIAL | NGUYỄN HOÀNG THANH TÂM - SENIOR DATA ANALYST")
        hrun.font.name = "Segoe UI"
        hrun.font.size = Pt(8)
        hrun.font.color.rgb = RGBColor(148, 163, 184)
        
        # Footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Dự án: daklak-ethnic-socioeconomic-analytics • Master Interview & Execution Playbook • Trang ")
        frun.font.name = "Segoe UI"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(148, 163, 184)
        
        # Add page field to footer
        f_xml = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
        fp._p.append(f_xml)

    i = 0
    in_code_block = False
    code_block_lines = []
    
    while i < len(lines):
        line = lines[i].rstrip('\r\n')
        
        # Check code blocks
        if line.startswith('```'):
            if in_code_block:
                # Flush code block
                tbl = doc.add_table(rows=1, cols=1)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = tbl.cell(0, 0)
                cell.width = Inches(6.5)
                set_cell_background(cell, "0F172A") # slate-900 dark background
                set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
                
                cp = cell.paragraphs[0]
                cp.paragraph_format.space_before = Pt(0)
                cp.paragraph_format.space_after = Pt(0)
                cp.paragraph_format.line_spacing = 1.05
                
                c_run = cp.add_run("\n".join(code_block_lines))
                c_run.font.name = "Consolas"
                c_run.font.size = Pt(8.5)
                c_run.font.color.rgb = RGBColor(226, 232, 240) # light code text
                
                doc.add_paragraph().paragraph_format.space_after = Pt(2)
                code_block_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_block_lines = []
            i += 1
            continue
            
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue
            
        # Blank line
        if not line.strip():
            i += 1
            continue
            
        # Horizontal rule
        if line.strip() in ['---', '***', '___']:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            p_border = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="E2E8F0"/></w:pBdr>')
            p._p.get_or_add_pPr().append(p_border)
            i += 1
            continue
            
        # Blockquote (Callout)
        if line.startswith('> '):
            quote_text = line[2:].strip()
            # collect consecutive quote lines
            while i + 1 < len(lines) and lines[i+1].startswith('> '):
                i += 1
                quote_text += "\n" + lines[i][2:].strip()
            add_callout(doc, quote_text, "LƯU Ý CHIẾN LƯỢC / QUY TẮC")
            i += 1
            continue
            
        # Title (Level 1 Header with #)
        if line.startswith('# '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(line[2:].strip())
            run.bold = True
            run.font.name = "Segoe UI"
            run.font.size = Pt(18)
            run.font.color.rgb = RGBColor(30, 58, 138) # Navy Primary
            i += 1
            continue
            
        # Heading 2 (##)
        if line.startswith('## '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(line[3:].strip())
            run.bold = True
            run.font.name = "Segoe UI"
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(194, 65, 12) # Earth Terracotta
            i += 1
            continue
            
        # Heading 3 (###)
        if line.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(9)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(line[4:].strip())
            run.bold = True
            run.font.name = "Segoe UI"
            run.font.size = Pt(11.5)
            run.font.color.rgb = RGBColor(15, 23, 42) # Slate Dark
            i += 1
            continue
            
        # Tables
        if line.startswith('|') and '|' in line[1:]:
            table_lines = [line]
            while i + 1 < len(lines) and lines[i+1].strip().startswith('|'):
                i += 1
                table_lines.append(lines[i].strip())
                
            # Parse table lines
            rows_data = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.split('|')[1:-1]]
                # Ignore separator lines like |---|:---:|---|
                if cells and all(re.match(r'^:?-+:?$', c) for c in cells):
                    continue
                rows_data.append(cells)
                
            if rows_data:
                num_cols = max(len(r) for r in rows_data)
                tbl = doc.add_table(rows=len(rows_data), cols=num_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl, "CBD5E1")
                
                for r_idx, row in enumerate(rows_data):
                    is_header = (r_idx == 0)
                    for c_idx, cell_value in enumerate(row):
                        if c_idx < num_cols:
                            cell = tbl.cell(r_idx, c_idx)
                            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
                            
                            if is_header:
                                set_cell_background(cell, "1E3A8A") # Navy header
                            else:
                                if r_idx % 2 == 1:
                                    set_cell_background(cell, "FFFFFF")
                                else:
                                    set_cell_background(cell, "F8FAFC") # light zebra stripe
                                    
                            p = cell.paragraphs[0]
                            p.paragraph_format.space_before = Pt(2)
                            p.paragraph_format.space_after = Pt(2)
                            
                            font_color = RGBColor(255, 255, 255) if is_header else RGBColor(30, 41, 59)
                            format_inline_runs(p, cell_value, base_size=9.5, base_color=font_color)
                            if is_header:
                                for r in p.runs:
                                    r.bold = True
                                    
                doc.add_paragraph().paragraph_format.space_after = Pt(4)
            i += 1
            continue
            
        # Bullet list (- or * )
        if line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            format_inline_runs(p, line[2:].strip(), base_size=10)
            i += 1
            continue
            
        # Numbered list (1. 2. ...)
        m_num = re.match(r'^(\d+)\.\s+(.*)', line)
        if m_num:
            num_str = m_num.group(1)
            content_str = m_num.group(2)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            format_inline_runs(p, content_str, base_size=10)
            i += 1
            continue
            
        # Regular paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        format_inline_runs(p, line.strip(), base_size=10)
        i += 1

    doc.save(docx_path)
    print(f"Successfully generated DOCX at: {docx_path}")

if __name__ == "__main__":
    src_md = r"c:\daklak-ethnic-socioeconomic-analytics\reports\private\CONFIDENTIAL_MASTER_PROJECT_AND_INTERVIEW_PLAYBOOK.md"
    dst_docx = r"c:\daklak-ethnic-socioeconomic-analytics\reports\private\CONFIDENTIAL_MASTER_PROJECT_AND_INTERVIEW_PLAYBOOK.docx"
    convert_markdown_to_docx(src_md, dst_docx)
