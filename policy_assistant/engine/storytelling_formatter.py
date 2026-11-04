"""
==============================================================================
MODULE: STORYTELLING POLICY BRIEF FORMATTER (Dynamic Context-Aware F-A-I-R)
File: policy_assistant/engine/storytelling_formatter.py
Dự án: Trợ Lý Tham Mưu Dữ Liệu KTXH 53 Dân Tộc Thiểu Số Đắk Lắk
==============================================================================
"""

import decimal
from typing import Dict, Any, List, Optional
import pandas as pd
from .intent_router import PolicyIntent, ExtractedEntities
from ..core.catalog import BUDGET_STANDARDS, METRIC_CATALOG


def format_currency_vnd(val_in_billion: float) -> str:
    """Định dạng tiền tỷ/triệu VNĐ chuẩn kế toán Việt Nam."""
    val_float = float(val_in_billion)
    if val_float >= 1.0:
        return f"{val_float:,.2f} tỷ VNĐ".replace(",", "@").replace(".", ",").replace("@", ".")
    else:
        val_in_million = val_float * 1000.0
        return f"{val_in_million:,.1f} triệu VNĐ".replace(",", "@").replace(".", ",").replace("@", ".")


def format_dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 15) -> str:
    """Chuyển đổi DataFrame thành bảng Markdown hiển thị số liệu thực chứng thuần Python."""
    if df is None or df.empty:
        return "*Không có dữ liệu thực chứng phù hợp với tiêu chí lọc.*"

    display_df = df.head(max_rows).copy()
    headers = [str(c) for c in display_df.columns]

    rows = []
    for _, row in display_df.iterrows():
        formatted_row = []
        for val in row:
            if pd.isna(val):
                formatted_row.append("-")
            elif isinstance(val, (float, decimal.Decimal)):
                formatted_row.append(f"{float(val):,.2f}")
            elif isinstance(val, int):
                formatted_row.append(f"{val:,}")
            else:
                formatted_row.append(str(val))
        rows.append(formatted_row)

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if len(val) > col_widths[i]:
                col_widths[i] = len(val)

    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "| " + " | ".join("-" * max(3, col_widths[i]) for i in range(len(headers))) + " |"
    row_lines = [
        "| " + " | ".join(val.ljust(col_widths[i]) for i, val in enumerate(r)) + " |"
        for r in rows
    ]

    return "\n".join([header_line, sep_line] + row_lines)


def format_fair_policy_brief(intent: PolicyIntent, df: pd.DataFrame) -> str:
    """
    Biên soạn báo cáo tham mưu chính sách theo chuẩn F-A-I-R thích ứng linh hoạt
    với số liệu thực tế của từng Địa bàn (Tỉnh/Huyện/Xã) và Dân tộc.
    """
    code = intent.intent_code
    e = intent.entities
    period = e.ky_baocao
    period_title = "Kỳ 2026 (Giai đoạn 2026-2030)" if period == "KY_2026" else ("Kỳ 2024" if period == "KY_2024" else "Kỳ 2019")

    if df is None or df.empty:
        return f"""### BÁO CÁO THAM MƯU CHUYÊN ĐỀ
*Chu kỳ báo cáo: {period_title}*

**Thông báo:** Hệ thống CSDL không tìm thấy bản ghi phù hợp với điều kiện truy vấn (Huyện: {e.huyen or 'Toàn tỉnh'}, Xã: {e.xa or 'Tất cả'}, Dân tộc: {e.dantoc or 'Tất cả'}). Vui lòng kiểm tra lại danh mục hoặc nới lỏng bộ lọc.
"""

    table_md = format_dataframe_to_markdown(df)
    scope_label = e.xa or e.huyen or (f"Dân tộc {e.dantoc}" if e.dantoc else "Toàn tỉnh Đắk Lắk")

    # ==========================================================================
    # 0. DASHBOARD_GUIDE (Hướng dẫn sử dụng Power BI & Giải thích Chỉ số)
    # ==========================================================================
    if code == "DASHBOARD_GUIDE":
        topic = e.guide_topic or "general"
        if topic == "age_pyramid":
            return f"""### BÁO CÁO GIẢI THÍCH CHUYÊN ĐỀ: THÁP TUỔI & CƠ CẤU 3 NHÓM TUỔI DÂN TỘC (TRANG 1 POWER BI)
**Chu kỳ phân tích:** {period_title} | **Phạm vi:** 53 Dân tộc thiểu số tỉnh Đắk Lắk  
**Căn cứ thống kê:** Fact 8 - Nhân khẩu học & Cơ cấu nhóm tuổi dân tộc (Tổng cục Thống kê & CSDL Star Schema)

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Biểu đồ **'Tháp Tuổi & Cơ Cấu 3 Nhóm Tuổi Dân Tộc'** (Trang 1 Power BI) là biểu đồ thanh ngang xếp chồng 100% (100% Stacked Bar Chart) đo lường cấu trúc nhân khẩu học của 53 DTTS. Dữ liệu thực chứng phơi bày **hai thái cực nhân khẩu học đối lập**: Nhóm di cư phía Bắc (như *người Mông 41.0%*, *Xơ Đăng 42.5% trẻ em*) có đáy tháp tuổi phình to cực đại tạo áp lực nuôi con lớn (tỷ lệ phụ thuộc trẻ em >75–79%); trong khi nhóm bản địa (*Ê Đê 62.0%*, *Mnông 58.1%*) đang ở thời kỳ 'dân số vàng' và nhóm *Tày, Thái* bắt đầu bước sang giai đoạn già hóa (chỉ số già hóa >42%).

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Cơ cấu 3 nhóm tuổi:** (1) <em>0–14 tuổi (Dưới tuổi lao động / Trẻ em)</em> • (2) <em>15–59 tuổi (Độ tuổi lao động vàng)</em> • (3) <em>60+ tuổi (Hết tuổi lao động / Người cao tuổi)</em>.
- **Công thức DAX cốt lõi:**
  + `Tỷ Lệ Phụ Thuộc Trẻ Em` = `[Dân số 0-14] / [Dân số 15-59] × 100` (Người Mông: **75.1%**, Xơ Đăng: **79.2%**).
  + `Chỉ Số Già Hóa` = `[Dân số 60+] / [Dân số 0-14] × 100` (Người Tày: **42.7%**, Thái: **42.1%**).
- **Nhóm dân tộc chủ lực:** Đồng bào Ê Đê có hơn **251.000 người** nằm trong độ tuổi lao động vàng 15–59 (chiếm 62.0% dân số dân tộc).

---

#### 2. ANALYSIS (Phân Tích Bóc Tách Bản Chất Nhân Khẩu Học)
- **Tháp tuổi đáy rộng (Mức sinh cao):** Nhóm di cư phía Bắc (Mông, Xơ Đăng, Dao) vẫn duy trì tập quán kết hôn sớm và tỷ lệ sinh con thứ 3+ cao, khiến tỷ trọng trẻ em <15 tuổi vượt trên 40%. Điều này lý giải nguyên nhân gốc rễ của 'bẫy nghèo đông con' khi 100 lao động phải gánh tới gần 80 trẻ nhỏ.
- **Lợi thế dân số vàng của nhóm bản địa:** Dân tộc Ê Đê và Mnông đang sở hữu lực lượng lao động dồi dào nhất (>58–62%). Đây là thời kỳ thuận lợi nhất để bứt phá năng suất lao động nếu được trang bị kỹ năng chuyên môn kỹ thuật.

---

#### 3. IMPACT (Tác Động Đến Định Hướng Ngân Sách Đầu Tư Công)
- Nếu chỉ phân bổ ngân sách cào bằng giữa các dân tộc mà không xét tới tháp tuổi, chính sách sẽ bị trật đích: Nhóm trẻ hóa cần vốn trường lớp mầm non, tiểu học và dinh dưỡng học đường (Dự án 5 MTQG 1719); còn nhóm già hóa cần mạng lưới y tế dự phòng và bảo hiểm y tế.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị Hành Động 4W1H)
- **Who:** Ban Dân tộc tỉnh, Sở GD&ĐT, Sở Y tế và Sở LĐ-TB&XH tỉnh Đắk Lắk.
- **What:** Điều hành chính sách hai mũi nhọn: (1) Mở rộng phòng học mầm non, bán trú tại các cụm dân cư người Mông, Xơ Đăng; (2) Tập trung ngân sách đào tạo nghề nông thôn (định mức 6,0 triệu VNĐ/người) cho lực lượng lao động 15–59 tuổi dân tộc Ê Đê, Mnông.
- **Where & When:** Tích hợp vào Kế hoạch thực hiện Chương trình MTQG 1719 giai đoạn {period_title}.
- **How much:** Phân bổ ngân sách linh hoạt theo cơ cấu nhóm tuổi của từng địa bàn cư trú.
"""

    # ==========================================================================
    # 1. POLICY_BUDGET
    # ==========================================================================
    if code == "POLICY_BUDGET":
        tot_budget = float(df["tong_kinh_phi_can_phan_bo_ty_vnd"].sum()) if "tong_kinh_phi_can_phan_bo_ty_vnd" in df.columns else 0.0
        tot_obj = float(df["so_luong_doi_tuong_can_ho_tro"].sum()) if "so_luong_doi_tuong_can_ho_tro" in df.columns else 0.0

        sorted_items = df.sort_values(by="tong_kinh_phi_can_phan_bo_ty_vnd", ascending=False) if "tong_kinh_phi_can_phan_bo_ty_vnd" in df.columns else df
        top1 = sorted_items.iloc[0] if len(sorted_items) > 0 else None
        top2 = sorted_items.iloc[1] if len(sorted_items) > 1 else None

        top1_val = float(top1["tong_kinh_phi_can_phan_bo_ty_vnd"]) if top1 is not None and "tong_kinh_phi_can_phan_bo_ty_vnd" in top1 else 0.0
        top2_val = float(top2["tong_kinh_phi_can_phan_bo_ty_vnd"]) if top2 is not None and "tong_kinh_phi_can_phan_bo_ty_vnd" in top2 else 0.0
        top1_pct = (top1_val / tot_budget * 100.0) if tot_budget > 0 else 0.0
        top2_pct = (top2_val / tot_budget * 100.0) if tot_budget > 0 else 0.0

        return f"""### BÁO CÁO THAM MƯU: DỰ TOÁN NHU CẦU NGÂN SÁCH ĐẦU TƯ CÔNG ({scope_label.upper()})
**Chu kỳ trọng tâm:** {period_title} | **Phạm vi thẩm định:** {scope_label}  
**Căn cứ pháp lý:** Quyết định 1719/QĐ-TTg, Nghị định 28/2022/NĐ-CP, Quyết định 318/QĐ-TTg

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Tổng nhu cầu ngân sách đầu tư công cần phân bổ tại **{scope_label}** trong {period_title} là **{format_currency_vnd(tot_budget)}** nhằm can thiệp trực tiếp cho **{tot_obj:,.0f} lượt đối tượng** thụ hưởng. Nguồn lực tập trung lớn nhất vào **{top1['ten_chitieu'] if top1 is not None else 'Đào tạo nghề'}** ({top1_pct:.1f}%) và **{top2['ten_chitieu'] if top2 is not None else 'Tín dụng chính sách'}** ({top2_pct:.1f}%).

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Tổng dự toán phạm vi {scope_label}:** **{format_currency_vnd(tot_budget)}** ({tot_budget:,.2f} tỷ VNĐ).
- **Hạng mục ưu tiên số 1:** {top1['ten_chitieu'] if top1 is not None else '-'} — **{top1_val:,.2f} tỷ VNĐ** ({int(float(top1['so_luong_doi_tuong_can_ho_tro'])) if top1 is not None else 0:,} {top1['don_vi_tinh'] if top1 is not None else 'đối tượng'}).
- **Hạng mục ưu tiên số 2:** {top2['ten_chitieu'] if top2 is not None else '-'} — **{top2_val:,.2f} tỷ VNĐ** ({int(float(top2['so_luong_doi_tuong_can_ho_tro'])) if top2 is not None else 0:,} {top2['don_vi_tinh'] if top2 is not None else 'đối tượng'}).

---

#### 2. ANALYSIS (Phân Tích Cơ Cấu Nguồn Lực)
- **Trọng tâm chuyển dịch sang sinh kế bền vững:** Hai cấu phần Đào tạo nghề ({top1_pct:.1f}%) và Tín dụng ưu đãi ({top2_pct:.1f}%) chiếm **{top1_pct + top2_pct:.1f}%** tổng nhu cầu vốn tại {scope_label}, phản ánh định hướng chuyển từ hỗ trợ cho không sang trao "cần câu" sinh kế.
- **Định mức chuẩn hóa theo giai đoạn:** Đơn giá tính toán áp dụng sát định mức pháp lý của giai đoạn {period_title}, khắc phục triệt để tình trạng dự toán cào bằng giữa các địa bàn.

---

#### 3. IMPACT (Tác Động Nghiệp Vụ & Đánh Giá Rủi Ro)
- Nếu giải ngân tách rời giữa vốn vay NHCSXH (NĐ 28) và đào tạo kỹ thuật canh tác (Dự án 5), hiệu quả đồng vốn tại {scope_label} sẽ giảm sút, tiềm ẩn rủi ro nợ quá hạn khi nông sản biến động giá.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị Hành Động 4W1H)
- **Who:** Sở Kế hoạch & Đầu tư, Ban Dân tộc tỉnh, Chi nhánh NHCSXH và chính quyền {scope_label}.
- **What:** Thực thi cơ chế "Giải ngân tích hợp kép" — ưu tiên duyệt hồ sơ vay vốn NĐ 28 cho các hộ có lao động hoàn thành khóa tập huấn kỹ thuật nông nghiệp.
- **Where & When:** Tập trung giải ngân tại {scope_label} ngay từ Quý I–II của chu kỳ kế hoạch.
- **How much:** Tổng dự toán **{format_currency_vnd(tot_budget)}** (Ngân sách Trung ương 85%, Ngân sách địa phương đối ứng 15%).
"""

    # ==========================================================================
    # 2. VULNERABILITY_HEALTH (Tách rõ Ma túy/HIV vs Sinh con tại nhà)
    # ==========================================================================
    elif code == "VULNERABILITY_HEALTH":
        row = df.iloc[-1] if ((e.xa or e.dantoc) and len(df) > 0) else df.iloc[0]
        target_name = str(row.get("ten_doi_tuong", scope_label))
        risk_group = str(row.get("phan_nhom_rui_ro", ""))
        main_val = float(row.get("chi_so_rui_ro_chinh", 0) or 0)
        sub_val = float(row.get("chi_so_rui_ro_phu", 0) or 0)
        diff_val = float(row.get("bien_dong_rui_ro_chinh", 0) or 0)
        diff_pct = float(row.get("ty_le_giam_rui_ro_pct", 0) or 0)
        is_birth_topic = ("sinh" in risk_group.lower()) or ("y tế" in risk_group.lower()) or ("sinh_tai_nha" in e.metric_keys and "ma_tuy_hiv" not in e.metric_keys) or bool(e.dantoc)

        if is_birth_topic:
            budget_m = main_val * 4.5
            return f"""### BÁO CÁO CHUYÊN ĐỀ: GIÁM SÁT Y TẾ SINH SẢN & CAN THIỆP SINH CON TẠI NHÀ ({target_name.upper()})
**Đối tượng giám sát:** {target_name} | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Quyết định 1719/QĐ-TTg (Dự án 7 - Chăm sóc sức khỏe nhân dân vùng DTTS)

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Tại nhóm **{target_name}**, số ca sinh con tại nhà hiện ghi nhận **{main_val:,.0f} ca** (trong đó có **{sub_val:,.0f} ca không có cán bộ y tế đỡ**), biến động **{diff_val:+.0f} ca ({diff_pct:+.2f}%)** so với kỳ trước. Dù đã giảm nhờ mạng lưới y tế thôn bản, đây vẫn là rủi ro sản khoa cần can thiệp trực tiếp.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Số ca sinh tại nhà ({period_title}):** **{main_val:,.0f} ca** (biến động {diff_val:+.0f} ca so với kỳ trước).
- **Số ca sinh nguy cơ cao (không có bà đỡ chuyên môn):** **{sub_val:,.0f} ca** ({(sub_val/main_val*100.0) if main_val > 0 else 0.0:.1f}% tổng số ca sinh tại nhà).

---

#### 2. ANALYSIS (Phân Tích Nguyên Nhân Thực Tế)
- Tập quán sinh đẻ truyền thống tại gia đình, tâm lý e ngại khi đến cơ sở y tế tuyến huyện và rào cản giao tiếp tiếng phổ thông ở phụ nữ DTTS vùng sâu.
- Khoảng cách từ các cụm dân cư cư trú phân tán đến Trạm Y tế xã còn xa, đặc biệt khó khăn khi chuyển dạ vào ban đêm hoặc mùa mưa.

---

#### 3. IMPACT (Hệ Lụy Sức Khỏe Cộng Đồng)
- Đe dọa trực tiếp tính mạng sản phụ và trẻ sơ sinh do nguy cơ băng huyết sau sinh, nhiễm trùng uốn ván rốn và suy dinh dưỡng thể thấp còi đầu đời.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Sở Y tế (CDC Đắk Lắk), Trung tâm Y tế cấp huyện và Trạm Y tế xã.
- **What:** Cấp phát "Gói đỡ đẻ sạch", tăng phụ cấp cho đội ngũ Cô đỡ thôn bản người DTTS và hỗ trợ chi phí đi lại, ăn ở cho sản phụ nghèo đến sinh tại trạm y tế.
- **Where & When:** Rà soát danh sách thai phụ theo từng quý tại các thôn/buôn có đông đồng bào {target_name}.
- **How much:** Dự toán **{budget_m:,.1f} triệu VNĐ** cho nhóm {target_name} (theo định mức **4,5 triệu VNĐ/ca** của Dự án 7 - QĐ 1719).
"""
        else:
            return f"""### BÁO CÁO CHUYÊN ĐỀ: GIÁM SÁT ĐIỂM NÓNG AN NINH TRẬT TỰ — MA TÚY & HIV/AIDS ({target_name.upper()})
**Địa bàn trọng điểm:** {target_name} ({row.get('pham_vi_nhom', '')}) | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Kế hoạch 118/KH-UBND về phòng chống tệ nạn xã hội & Chương trình MTQG Phòng chống ma túy

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Địa bàn **{target_name}** hiện ghi nhận **{main_val:,.0f} người DTTS nghiện ma túy** và **{sub_val:,.0f} trường hợp nhiễm HIV**, biến động **{diff_val:+.0f} người ({diff_pct:+.2f}%)** so với kỳ trước. Mặc dù đà phát sinh mới đã được kiềm chế, đây vẫn là điểm nóng an ninh cơ sở cần duy trì tổ công tác cắm chốt.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Số người DTTS nghiện ma túy đang quản lý:** **{main_val:,.0f} người** (biến động {diff_val:+.0f} người so với kỳ trước).
- **Số trường hợp nhiễm HIV/AIDS trên địa bàn:** **{sub_val:,.0f} người**.
- **Thứ hạng rủi ro an ninh kỳ hiện tại:** Hạng **{int(float(row.get('xep_hang_diem_nong_ky', 1) or 1))}**.

---

#### 2. ANALYSIS (Phân Tích Nguyên Nhân Địa Bàn)
- Vị trí địa lý giáp ranh, có các trục giao thương liên huyện/liên tỉnh đi qua tạo điều kiện cho các đối tượng xấu lôi kéo thanh niên DTTS thiếu việc làm.
- Lao động trẻ tại địa bàn thiếu kỹ năng nghề, nhàn rỗi sau mùa vụ nông nghiệp nên dễ bị tổn thương trước tệ nạn xã hội.

---

#### 3. IMPACT (Hệ Lụy An Ninh & An Sinh)
- Tiềm ẩn nguy cơ tái nghiện, lây nhiễm HIV trong cộng đồng và phát sinh các hành vi vi phạm pháp luật (trộm cắp nông sản, xâm hại rừng) gây bất ổn buôn làng.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Công an tỉnh Đắk Lắk, Sở Lao động - TB&XH, Sở Y tế và UBND {row.get('pham_vi_nhom', target_name)}.
- **What:** Duy trì điểm cấp phát thuốc Methadone/ARV lưu động kết hợp mô hình "Cai nghiện cộng đồng gắn với đào tạo nghề và vay vốn tái hòa nhập".
- **Where & When:** Tập trung kiểm soát chặt tại **{target_name}**; rà soát hồ sơ quản lý sau cai định kỳ hàng tháng.
- **How much:** Phân bổ kinh phí nghiệp vụ phòng chống tệ nạn địa phương kết hợp gói đào tạo nghề **6,0 triệu VNĐ/lao động** (Dự án 5) cho thanh niên sau cai nghiện.
"""

    # ==========================================================================
    # 3. HOUSING_POVERTY (Phân nhánh rõ Đã xóa 100% = 0 căn vs Còn nhà tạm)
    # ==========================================================================
    elif code == "HOUSING_POVERTY":
        row = df.iloc[-1] if (e.dantoc and len(df) > 0) else df.iloc[0]
        if e.dantoc and len(df) > 0:
            cur_cnt = float(row.get("so_ho_nha_tam_don_so", 0) or 0)
            cur_pct = float(row.get("ty_le_nha_tam_pct", 0) or 0)
            first_cnt = float(df.iloc[0].get("so_ho_nha_tam_don_so", 0) or 0)
            tot_ho = float(row.get("tong_ho_co_nha", 0) or 0)
            nhom_goc = str(row.get("nhom_nguon_goc", ""))

            if cur_cnt == 0:
                return f"""### BÁO CÁO KẾT QUẢ: HOÀN THÀNH 100% XÓA NHÀ TẠM, DỘT NÁT — DÂN TỘC {e.dantoc.upper()}
**Đối tượng thẩm định:** Dân tộc {e.dantoc} ({nhom_goc}) | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Chương trình MTQG 1719 (Dự án 1 - Giải quyết tình trạng thiếu đất ở, nhà ở)

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Tính đến **{period_title}**, cộng đồng dân tộc **{e.dantoc}** ({tot_ho:,.0f} hộ) đã **xóa trắng hoàn toàn 100% nhà tạm, dột nát** (giảm từ {first_cnt:,.0f} căn ở các kỳ trước về đúng **0 căn**). Địa phương đã hoàn thành trọn vẹn mục tiêu nhà ở "3 cứng" cho nhóm dân tộc này, không phát sinh thêm nhu cầu ngân sách xây mới nhà tạm trong kỳ hiện tại.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Tổng số hộ dân tộc {e.dantoc}:** **{tot_ho:,.0f} hộ**.
- **Số nhà tạm, đơn sơ hiện còn ({period_title}):** **0 căn (0,00%)** — đã giải quyết dứt điểm 100%.

---

#### 2. ANALYSIS (Đánh Giá Hiệu Quả Chính Sách)
- Việc ưu tiên nguồn lực đầu tư công (Dự án 1 - QĐ 1719) kết hợp nguồn xã hội hóa của Ủy ban MTTQ tỉnh đã phát huy hiệu quả tối đa đối với nhóm đồng bào {e.dantoc}.
- Toàn bộ các hộ từng ở nhà tạm nay đã có nơi ở kiên cố/bán kiên cố đạt chuẩn an toàn trước thiên tai.

---

#### 3. IMPACT (Tác Động An Cư Lạc Nghiệp)
- Bảo đảm an toàn tuyệt đối cho người dân trong mùa mưa bão Tây Nguyên, hoàn thành sớm Tiêu chí số 9 (Nhà ở dân cư) trong xây dựng Nông thôn mới.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị Chuyển Tiếp Sau An Cư)
- **Who:** UBND cấp huyện/xã nơi đồng bào {e.dantoc} cư trú và Chi nhánh NHCSXH tỉnh.
- **What:** Chuyển trọng tâm từ "Hỗ trợ xây nhà" sang giai đoạn **"An cư gắn với Lạc nghiệp"** — hướng dẫn bà con duy tu nhà ở và tiếp cận vốn vay sản xuất (NĐ 28) cùng đào tạo nghề (Dự án 5).
- **Where & When:** Thực hiện lồng ghép trong các chương trình khuyến nông hàng năm.
- **How much:** Dự toán xây mới nhà tạm kỳ này: **0,00 tỷ VNĐ** (đã hoàn thành 100% mục tiêu).
"""
            else:
                budget_ty = cur_cnt * 90.0 / 1000.0
                cause_detail = (
                    "Đặc thù nhà sàn gỗ truyền thống qua nhiều năm sử dụng đã xuống cấp mục nát, trong khi hộ gia đình đông nhân khẩu và thiếu vốn đối ứng để kiên cố hóa."
                    if "bản địa" in nhom_goc.lower()
                    else "Nhiều hộ di cư cư trú phân tán tại các thôn/buôn vùng sâu còn vướng mắc về giấy tờ đất ở hợp pháp và chịu chi phí vận chuyển vật liệu xây dựng cao hơn 18–25%."
                )
                return f"""### BÁO CÁO THAM MƯU: TIẾN ĐỘ XÓA NHÀ TẠM, DỘT NÁT — DÂN TỘC {e.dantoc.upper()}
**Đối tượng thẩm định:** Dân tộc {e.dantoc} ({nhom_goc}) | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Chương trình MTQG 1719 (Dự án 1, Tiểu dự án 1) & Tiêu chí số 9 Nông thôn mới

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Cộng đồng dân tộc **{e.dantoc}** hiện còn **{cur_cnt:,.0f} hộ ở nhà tạm, đơn sơ** (chiếm **{cur_pct:.2f}%** trên tổng số {tot_ho:,.0f} hộ), giảm **{abs(first_cnt - cur_cnt):,.0f} căn** so với kỳ đầu. Cần bố trí **{budget_ty:,.2f} tỷ VNĐ** theo định mức 90 triệu VNĐ/căn để xóa dứt điểm số nhà tạm còn tồn đọng.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Quy mô nhà tạm còn tồn đọng ({e.dantoc}):** **{cur_cnt:,.0f} căn** (tỷ lệ **{cur_pct:.2f}%**).
- **Tiến độ lũy kế qua các kỳ:** Đã xóa được **{max(0.0, first_cnt - cur_cnt):,.0f} căn** (từ {first_cnt:,.0f} căn xuống {cur_cnt:,.0f} căn).

---

#### 2. ANALYSIS (Phân Tích Nguyên Nhân Tồn Đọng)
- {cause_detail}

---

#### 3. IMPACT (Hệ Lụy An Sinh & Thiên Tai)
- Các hộ còn ở nhà tạm vách ván/mái tôn cũ đối mặt với rủi ro mất an toàn trong mùa mưa lũ và gió lốc tại Tây Nguyên, ảnh hưởng trực tiếp đến sức khỏe người già và trẻ em.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Sở Xây dựng, Ủy ban MTTQ Việt Nam tỉnh, Ban Dân tộc và UBND các huyện.
- **What:** Rà soát cấp phép xây dựng trên đất ở hợp pháp, áp dụng mẫu nhà "3 cứng" lắp ghép bền vững và huy động lực lượng thanh niên/bộ đội hỗ trợ ngày công.
- **Where & When:** Tập trung giải quyết cho **{cur_cnt:,.0f} hộ dân tộc {e.dantoc}** trước mùa mưa bão (tháng 9 hàng năm).
- **How much:** Dự toán **{budget_ty:,.2f} tỷ VNĐ** (định mức **90,0 triệu VNĐ/hộ** giai đoạn 2026–2030).
"""
        else:
            tot_temporary = float(df["so_ho_nha_tam_don_so"].sum()) if "so_ho_nha_tam_don_so" in df.columns else float(df["tong_ho_nha_tam"].sum() if "tong_ho_nha_tam" in df.columns else 0.0)
            tot_budget_nha_tam = tot_temporary * 90.0 / 1000.0
            top_name = str(df.iloc[0].get("ten_dantoc", df.iloc[0].get("ten_huyen", ""))) if len(df) > 0 else ""
            top_cnt = float(df.iloc[0].get("so_ho_nha_tam_don_so", df.iloc[0].get("tong_ho_nha_tam", 0)) or 0) if len(df) > 0 else 0.0

            return f"""### BÁO CÁO THAM MƯU: TỔNG HỢP TIẾN ĐỘ XÓA NHÀ TẠM, DỘT NÁT ({scope_label.upper()})
**Phạm vi khảo sát:** {scope_label} | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Chương trình MTQG 1719 (Dự án 1) & Phong trào thi đua Xóa nhà tạm, nhà dột nát

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Trong danh sách khảo sát tại **{scope_label}** ({period_title}), tổng số nhà tạm, đơn sơ cần xử lý là **{tot_temporary:,.0f} căn** (tương ứng nhu cầu vốn **{tot_budget_nha_tam:,.2f} tỷ VNĐ**), trong đó tập trung nhiều nhất tại **{top_name} ({top_cnt:,.0f} căn)**.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

---

#### 2. ANALYSIS (Phân Tích Bóc Tách)
- Quy mô nhà tạm còn lại tập trung chủ yếu ở các dân tộc có quy mô dân số lớn hoặc cư trú tại địa bàn vùng sâu (như Ê Đê, M'nông, Gia Rai, Mông), trong khi các nhóm DTTS rất ít người (như Chơ Ro) đã hoàn thành xóa trắng 100% nhà tạm.
- Điểm nghẽn chính nằm ở thủ tục chuyển đổi mục đích sử dụng đất ở và chi phí vật liệu xây dựng tăng cao tại các xã khu vực III.

---

#### 3. IMPACT (Tác Động An Sinh)
- Việc xóa dứt điểm **{tot_temporary:,.0f} căn nhà tạm** là điều kiện tiên quyết để hoàn thành Tiêu chí số 9 Nông thôn mới và bảo đảm an toàn dân sinh mùa mưa lũ.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Sở Xây dựng chủ trì phối hợp Ủy ban MTTQ tỉnh và UBND các huyện.
- **What:** Phân bổ vốn ưu tiên theo thứ tự quy mô nhà tạm từ cao xuống thấp, kết hợp tháo gỡ thủ tục đất ở cho hộ nghèo.
- **Where & When:** Ưu tiên số 1 cho **{top_name}** và các địa bàn vùng trũng trước Quý III hàng năm.
- **How much:** Tổng dự toán **{tot_budget_nha_tam:,.2f} tỷ VNĐ** (định mức **90,0 triệu VNĐ/căn**).
"""

    # ==========================================================================
    # 4. SANITATION_DIGITAL (Phân nhánh Đạt chuẩn >=70% vs Vùng trũng <70%)
    # ==========================================================================
    elif code == "SANITATION_DIGITAL":
        row = df.iloc[-1] if (e.huyen and len(df) > 0) else df.iloc[0]
        dist_name = str(row.get("ten_huyen", scope_label))
        hoxi = float(row.get("ty_le_ho_xi_hvs_bq_pct", 0) or 0)
        nuoc = float(row.get("ty_le_nuoc_hvs_bq_pct", 0) or 0)
        net = float(row.get("ty_le_internet_huyen_pct", 0) or 0)
        diff_hoxi = float(row.get("bien_dong_ho_xi_hvs_pct", 0) or 0)
        ho_dtts = float(row.get("tong_ho_dtts_huyen", 0) or 0)

        if e.huyen and hoxi >= 70.0:
            return f"""### BÁO CÁO ĐÁNH GIÁ: HẠ TẦNG VỆ SINH NTM & CHUYỂN ĐỔI SỐ — {dist_name.upper()}
**Địa bàn:** {dist_name} ({ho_dtts:,.0f} hộ DTTS) | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Quyết định 318/QĐ-TTg (Tiêu chí 17 NTM), Đề án 06/QĐ-TTg

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Địa bàn **{dist_name}** là **điểm sáng hoàn thành vượt mức** cả hai chỉ tiêu hạ tầng thiết yếu: Tỷ lệ hố xí hợp vệ sinh đạt **{hoxi:.2f}%** (vượt ngưỡng chuẩn Nông thôn mới 70,0%) và tỷ lệ hộ kết nối Internet đạt **{net:.2f}%** (đáp ứng tốt hạ tầng số Đề án 06).

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Tỷ lệ Hố xí hợp vệ sinh ({dist_name}):** **{hoxi:.2f}%** (biến động **{diff_hoxi:+.2f} điểm %**, trạng thái: *{row.get('trang_thai_ntm_tc17', 'Đạt chuẩn')}*).
- **Tỷ lệ Nước sinh hoạt hợp vệ sinh:** **{nuoc:.2f}%**.
- **Tỷ lệ Phủ sóng Internet hộ DTTS:** **{net:.2f}%** (*{row.get('trang_thai_chuyendoiso_dean06', 'Sẵn sàng')}*).

---

#### 2. ANALYSIS (Đánh Giá Nguyên Nhân Thành Công)
- Nhờ lợi thế hạ tầng đô thị/cận đô thị đồng bộ và mặt bằng nhận thức dân cư cao, các hộ DTTS tại **{dist_name}** đã chủ động đầu tư công trình vệ sinh tự hoại khép kín và kết nối cáp quang/4G phục vụ đời sống.

---

#### 3. IMPACT (Tác Động Phát Triển)
- Tạo nền tảng vững chắc để duy trì chuẩn Nông thôn mới nâng cao và triển khai 100% dịch vụ công trực tuyến mức độ 3, 4 trên nền tảng VNeID.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị Duy Trì & Nâng Cao)
- **Who:** UBND {dist_name} phối hợp Tổ công nghệ số cộng đồng các thôn/buôn.
- **What:** Chuyển từ đầu tư xây dựng cơ bản sang hướng dẫn đồng bào DTTS sử dụng dịch vụ công trực tuyến, thanh toán không dùng tiền mặt và phân loại rác thải tại nguồn.
- **Where & When:** Triển khai thường xuyên tại các xã/phường thuộc {dist_name}.
"""
        else:
            gap_to_70 = max(0.0, 70.0 - hoxi)
            est_missing_households = int(round(ho_dtts * (gap_to_70 / 100.0)))
            est_cost_ty = est_missing_households * 12.0 / 1000.0
            return f"""### BÁO CÁO THAM MƯU: THÁO GỠ ĐIỂM TRŨNG VỆ SINH NTM & CHUYỂN ĐỔI SỐ ({dist_name.upper()})
**Địa bàn trọng tâm:** {dist_name} | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Quyết định 318/QĐ-TTg (Tiêu chí 17.5 NTM >= 70%), Đề án 06/QĐ-TTg (Internet >= 80%)

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Tại **{dist_name}**, trong khi hạ tầng Internet đã phủ tới **{net:.2f}%** số hộ thì tỷ lệ **Hố xí hợp vệ sinh mới chỉ đạt {hoxi:.2f}%** (còn thiếu **{gap_to_70:.2f} điểm %** so với ngưỡng chuẩn 70% của Tiêu chí 17 Nông thôn mới). Cần ưu tiên hỗ trợ khoảng **{est_missing_households:,} công trình vệ sinh** để kéo địa bàn thoát khỏi vùng trũng môi trường.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Hố xí hợp vệ sinh tại {dist_name}:** **{hoxi:.2f}%** (tăng **{diff_hoxi:+.2f} điểm %** so với kỳ trước, trạng thái: *{row.get('trang_thai_ntm_tc17', 'Chưa đạt')}*).
- **Nước sinh hoạt hợp vệ sinh:** **{nuoc:.2f}%** | **Kết nối Internet:** **{net:.2f}%**.

---

#### 2. ANALYSIS (Phân Tích Bóc Tách Điểm Nghẽn)
- **Độ vênh giữa hạ tầng số và vệ sinh cơ bản:** Sóng viễn thông 4G phủ nhanh đến tận buôn làng giúp tỷ lệ Internet đạt {net:.2f}%, nhưng thói quen sinh hoạt truyền thống và tâm lý ngại bỏ vốn xây nhà tiêu tự hoại khiến chỉ số hố xí HVS ({hoxi:.2f}%) bị bỏ lại phía sau.

---

#### 3. IMPACT (Hệ Lụy Môi Trường & Nông Thôn Mới)
- Trực tiếp cản trở các xã thuộc **{dist_name}** xét công nhận đạt chuẩn Nông thôn mới (kể cả khi điện, đường, trường, trạm đã đạt 100%) và gây nguy cơ ô nhiễm nguồn nước ngầm mùa mưa.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Sở Nông nghiệp & PTNT (VP Điều phối NTM), Sở Y tế và UBND {dist_name}.
- **What:** Cấp phát "Bể phốt tự hoại Composite đúc sẵn" (hỗ trợ vật tư, hộ dân đối ứng công lắp đặt) gắn với cam kết vệ sinh hộ gia đình thông qua Già làng, Trưởng buôn.
- **Where & When:** Thi công dứt điểm tại các thôn/buôn vùng trũng thuộc {dist_name} trong mùa khô.
- **How much:** Định mức **12,0 triệu VNĐ/công trình** (ước tính khoảng **{est_cost_ty:,.2f} tỷ VNĐ** để bù đắp đủ khoảng thiếu hụt lên ngưỡng chuẩn 70% tại {dist_name}).
"""

    # ==========================================================================
    # 5. POVERTY_COMMUNE (Phân nhánh rõ Xã đạt chuẩn / Xã bứt phá / Xã tái nghèo / Nhiều xã)
    # ==========================================================================
    elif code == "POVERTY_COMMUNE":
        row = df.iloc[-1] if (e.xa and len(df) > 0) else df.iloc[0]
        ten_xa = str(row.get("ten_xa", "Xã khảo sát"))
        ten_huyen = str(row.get("ten_huyen", ""))
        ty_le = float(row.get("ty_le_ngheo_pct", 0) or 0)
        so_ngheo = int(float(row.get("so_ho_ngheo", 0) or 0))
        bien_dong = float(row.get("bien_dong_ty_le_ngheo_pct", 0) or 0)
        km = float(row.get("km_den_trung_tam_huyen", 0) or 0)
        v_sinh_ke = float(row.get("du_toan_ngan_sach_sinh_ke_trieu_vnd", 0) or 0)

        if e.xa:
            if ty_le <= 15.0 and bien_dong < 0:
                status_summary = f"đã kiểm soát tỷ lệ hộ nghèo ở mức thấp (**{ty_le:.2f}%**, đạt chuẩn ngưỡng Khu vực III <= 15%) và tiếp tục giảm **{abs(bien_dong):.2f} điểm %** so với kỳ trước"
                cause_text = f"Khoảng cách từ {ten_xa} đến trung tâm {ten_huyen} ở mức **{km:.1f} km**, giao thương hàng hóa thuận lợi kết hợp hiệu quả từ các gói tín dụng ưu đãi giúp hộ dân ổn định thu nhập."
                impact_text = f"Đóng vai trò xã hạt nhân giảm nghèo bền vững của {ten_huyen}, tạo đà hoàn thành mục tiêu Nông thôn mới."
            elif bien_dong >= 0:
                status_summary = f"phát sinh **cảnh báo đỏ tái nghèo/dậm chân** khi tỷ lệ nghèo ở mức **{ty_le:.2f}%** ({so_ngheo:,} hộ nghèo), tăng **{bien_dong:+.2f} điểm %** so với kỳ trước"
                cause_text = f"Vị trí địa lý cách trung tâm {ten_huyen} tới **{km:.1f} km** (vượt ngưỡng 20km làm tăng chi phí vận tải nông sản), đồng thời các hộ cận nghèo bị rơi trở lại diện nghèo khi áp bộ tiêu chí đa chiều mới."
                impact_text = f"Nguy cơ tạo thành 'lõi nghèo kinh niên' tại {ten_xa} nếu chỉ hỗ trợ nhỏ lẻ mà thiếu mô hình hợp tác xã bao tiêu đầu ra."
            else:
                status_summary = f"đạt mức giảm nghèo tích cực (**{bien_dong:+.2f} điểm %** so với kỳ trước), tuy nhiên tỷ lệ nghèo hiện tại vẫn còn ở mức cao (**{ty_le:.2f}%**, tương ứng **{so_ngheo:,} hộ nghèo**)"
                cause_text = f"Địa bàn cách trung tâm huyện **{km:.1f} km**; dù hạ tầng cứng đã cải thiện nhưng sinh kế của {so_ngheo:,} hộ nghèo vẫn phụ thuộc vào canh tác nông nghiệp truyền thống năng suất thấp."
                impact_text = f"Cần duy trì đà can thiệp sinh kế trong 2 năm tới để kéo tỷ lệ nghèo của {ten_xa} xuống dưới ngưỡng 15%."

            return f"""### BÁO CÁO THẨM ĐỊNH CẤP XÃ: DIỄN BIẾN NGHÈO ĐA CHIỀU TẠI {ten_xa.upper()} ({ten_huyen.upper()})
**Địa bàn:** {ten_xa} — {ten_huyen} | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Nghị định 07/2021/NĐ-CP về chuẩn nghèo đa chiều & Dự án 3 - CTMTQG 1719

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Trong {period_title}, **{ten_xa} ({ten_huyen})** {status_summary}. Tổng nhu cầu vốn hỗ trợ phát triển sản xuất sinh kế cho {so_ngheo:,} hộ nghèo trên địa bàn là **{v_sinh_ke:,.0f} triệu VNĐ**.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Tỷ lệ hộ nghèo hiện tại ({ten_xa}):** **{ty_le:.2f}%** ({so_ngheo:,} hộ nghèo / {int(float(row.get('tong_ho_dtts', 0) or 0)):,} hộ DTTS).
- **Biến động so với kỳ trước:** **{bien_dong:+.2f} điểm %** (*{row.get('nhom_toc_do_giam_ngheo', '')}*).
- **Cự ly đến trung tâm hành chính huyện:** **{km:.1f} km**.

---

#### 2. ANALYSIS (Phân Tích Nguyên Nhân Thực Tế)
- {cause_text}

---

#### 3. IMPACT (Đánh Giá Tác Động)
- {impact_text}

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** UBND {ten_huyen}, UBND {ten_xa} và Phòng Nông nghiệp & PTNT.
- **What:** Giải ngân gói hỗ trợ giống cây trồng/vật nuôi và phân bón theo chuỗi liên kết tiêu thụ sản phẩm tại chỗ (Dự án 3).
- **Where & When:** Triển khai trực tiếp cho **{so_ngheo:,} hộ nghèo tại {ten_xa}** ngay đầu vụ mùa.
- **How much:** Dự toán **{v_sinh_ke:,.0f} triệu VNĐ** (định mức **30,0 triệu VNĐ/hộ nghèo**).
"""
        else:
            avg_p = float(df["ty_le_ngheo_pct"].mean()) if "ty_le_ngheo_pct" in df.columns else 0.0
            sum_ngheo_list = int(float(df["so_ho_ngheo"].sum())) if "so_ho_ngheo" in df.columns else 0
            stagnant_cnt = len(df[df["bien_dong_ty_le_ngheo_pct"] >= 0]) if "bien_dong_ty_le_ngheo_pct" in df.columns else 0
            tot_sinh_ke_ty = float(df["du_toan_ngan_sach_sinh_ke_trieu_vnd"].sum()) / 1000.0 if "du_toan_ngan_sach_sinh_ke_trieu_vnd" in df.columns else 0.0

            return f"""### BÁO CÁO THAM MƯU: PHÂN HÓA NGHÈO ĐA CHIỀU & RÀ SOÁT CẤP XÃ ({scope_label.upper()})
**Phạm vi rà soát:** {scope_label} ({len(df)} xã hiển thị) | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Nghị định 07/2021/NĐ-CP & Chương trình MTQG Giảm nghèo bền vững

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Rà soát **{len(df)} xã trọng điểm thuộc {scope_label}** ghi nhận tỷ lệ nghèo trung bình nhóm ở mức **{avg_p:.2f}%** (tổng cộng **{sum_ngheo_list:,} hộ nghèo**), trong đó đứng đầu là **{ten_xa} ({ten_huyen}) với {ty_le:.2f}%** và có **{stagnant_cnt} xã** xuất hiện dấu hiệu dậm chân/tái nghèo (biến động >= 0%).

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Xã có tỷ lệ nghèo cao nhất nhóm:** **{ten_xa} ({ten_huyen})** — **{ty_le:.2f}%** (cách trung tâm huyện {km:.1f} km).
- **Số xã dậm chân hoặc tăng tỷ lệ nghèo trong danh sách:** **{stagnant_cnt} xã**.
- **Tổng quy mô hộ nghèo của {len(df)} xã:** **{sum_ngheo_list:,} hộ** (cần **{tot_sinh_ke_ty:,.2f} tỷ VNĐ** vốn sinh kế).

---

#### 2. ANALYSIS (Phân Tích Căn Nguyên Phân Hóa)
- **Tương quan khoảng cách địa lý:** Phương trình hồi quy thực nghiệm cho thấy cứ mỗi 10 km xa trung tâm huyện, tỷ lệ nghèo cấp xã tăng thêm **+5,13 điểm %** do chi phí vận tải nông sản cao và hạn chế tiếp cận dịch vụ y tế, thị trường.

---

#### 3. IMPACT (Tác Động Điều Hành)
- Nếu phân bổ vốn cào bằng giữa các xã vùng ven đô và các xã vùng sâu (>20 km), các xã điểm nóng như **{ten_xa}** sẽ không đủ nguồn lực bứt phá khỏi bẫy nghèo đa chiều.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Ban Chỉ đạo các CTMTQG tỉnh, Sở NN&PTNT và UBND {e.huyen or 'các huyện vùng sâu'}.
- **What:** Ưu tiên phân bổ vốn sinh kế Dự án 3 theo hệ số khoảng cách và quy mô hộ nghèo thực tế của từng xã.
- **Where & When:** Tập trung xử lý dứt điểm tại **{ten_xa}** và nhóm {stagnant_cnt} xã có biến động nghèo dương.
- **How much:** Dự toán **{tot_sinh_ke_ty:,.2f} tỷ VNĐ** cho {sum_ngheo_list:,} hộ nghèo trong danh sách (định mức **30,0 triệu VNĐ/hộ**).
"""

    # ==========================================================================
    # 6. LABOR_EDUCATION (Vốn nhân lực CMKT & Giáo dục giới)
    # ==========================================================================
    elif code == "LABOR_EDUCATION":
        row = df.iloc[-1] if (e.dantoc and len(df) > 0) else df.iloc[0]
        dt_name = str(row.get("ten_dantoc", scope_label))
        cmkt = float(row.get("ty_le_khong_cmkt_pct", 0) or 0)
        nn = float(row.get("ty_le_nong_nghiep_pct", 0) or 0)
        nu_bc = float(row.get("ty_le_nu_biet_chu_pct", 0) or 0)
        ld_cnt = int(float(row.get("lao_dong_khong_cmkt", 0) or 0))
        budget_ty = ld_cnt * 6.0 / 1000.0

        return f"""### BÁO CÁO THAM MƯU: CHẤT LƯỢNG VỐN NHÂN LỰC & HỌC VẤN GIỚI ({dt_name.upper()})
**Đối tượng phân tích:** Dân tộc {dt_name} | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Quyết định 1719/QĐ-TTg (Dự án 5 - Phát triển giáo dục nghề nghiệp và giải quyết việc làm)

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Lực lượng lao động dân tộc **{dt_name}** hiện có **{cmkt:.2f}% chưa qua đào tạo chuyên môn kỹ thuật** ({ld_cnt:,} người), dẫn đến **{nn:.2f}%** lao động vẫn phụ thuộc vào nông nghiệp giản đơn; tỷ lệ phụ nữ biết chữ đạt **{nu_bc:.2f}%**.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Lao động chưa có chứng chỉ/bằng cấp nghề ({dt_name}):** **{ld_cnt:,} người ({cmkt:.2f}%)**.
- **Tỷ trọng lao động nông - lâm nghiệp:** **{nn:.2f}%**.
- **Tỷ lệ phụ nữ (15+ tuổi) biết chữ phổ thông:** **{nu_bc:.2f}%**.

---

#### 2. ANALYSIS (Phân Tích Chuyên Sâu)
- {"Tỷ lệ chưa qua đào tạo ở mức rất cao (>85%) tạo ra rào cản lớn khiến thanh niên khó tiếp cận các nhà máy chế biến nông sản hoặc xuất khẩu lao động." if cmkt > 85.0 else "Nhóm dân tộc này có nền tảng học vấn và tỷ lệ đào tạo nghề khá hơn mặt bằng chung, thuận lợi để đi đầu trong các mô hình nông nghiệp công nghệ cao."}
- {"Tỷ lệ nữ biết chữ đạt mức cao phản ánh vai trò tích cực của phụ nữ trong gia đình và khả năng tiếp thu tốt các chương trình khuyến nông." if nu_bc >= 85.0 else "Khoảng cách biết chữ ở phụ nữ còn thấp, đòi hỏi phải kết hợp lớp xóa mù chữ song ngữ trước khi đào tạo kỹ thuật nghề."}

---

#### 3. IMPACT (Tác Động Kinh Tế)
- Thiếu kỹ năng nghề khiến năng suất lao động nông hộ thấp, thu nhập bấp bênh khi giá nông sản biến động.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Sở Lao động - TB&XH, Trung tâm GDNN-GDTX các huyện và Doanh nghiệp nông nghiệp.
- **What:** Tổ chức các lớp đào tạo nghề thực hành ngắn hạn (<3 tháng) ngay tại vùng nguyên liệu (kỹ thuật ghép chồi, chăm sóc sầu riêng/cà phê VietGAP, vận hành máy nông nghiệp).
- **Where & When:** Tuyển sinh trực tiếp đối với **{ld_cnt:,} lao động dân tộc {dt_name}**.
- **How much:** Dự toán **{budget_ty:,.2f} tỷ VNĐ** (theo định mức **6,0 triệu VNĐ/lao động** của Dự án 5).
"""

    # ==========================================================================
    # 7. CREDIT_LAND & CÁC CHUYÊN ĐỀ TỔNG HỢP KHÁC
    # ==========================================================================
    else:
        row = df.iloc[-1] if (e.dantoc and len(df) > 0) else df.iloc[0]
        dt_name = str(row.get("ten_dantoc", row.get("ten_huyen", scope_label)))
        khat_von = int(float(row.get("so_ho_khat_von", 0) or 0))
        gap_pct = float(row.get("khoang_trong_tin_dung_pct", 0) or 0)
        dat_ha = float(row.get("dien_tich_dat_sx_bq_ha", 0) or 0)
        budget_ty = khat_von * 65.0 / 1000.0

        return f"""### BÁO CÁO THAM MƯU: {intent.intent_description.upper()} ({dt_name.upper()})
**Đối tượng / Phạm vi:** {dt_name} | **Chu kỳ:** {period_title}  
**Căn cứ pháp lý:** Nghị định 28/2022/NĐ-CP về tín dụng chính sách ưu đãi & Chương trình MTQG 1719

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
Trích xuất thực chứng tại **{dt_name}** ({period_title}) ghi nhận **{khat_von:,} hộ có nhu cầu vay vốn sản xuất** nhưng chưa tiếp cận được (khoảng trống tín dụng **{gap_pct:.2f}%**), với quỹ đất sản xuất bình quân đạt **{dat_ha:.2f} ha/hộ**.

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

- **Quy mô hộ cần vay vốn ưu đãi ({dt_name}):** **{khat_von:,} hộ** (Tỷ lệ thiếu hụt: **{gap_pct:.2f}%**).
- **Diện tích đất sản xuất bình quân:** **{dat_ha:.2f} ha/hộ** (Định mức tối thiểu QĐ 1719: 0,50 ha/hộ).

---

#### 2. ANALYSIS (Phân Tích Bóc Tách)
- {"Quỹ đất canh tác bình quân đạt dưới ngưỡng 0,50 ha/hộ khiến bà con thiếu tài sản thế chấp khi vay thương mại và cần được hỗ trợ chuyển đổi sang nghề phi nông nghiệp." if (dat_ha > 0 and dat_ha < 0.5) else "Các hộ dân có quỹ đất canh tác khá tốt nhưng thiếu vốn lưu động dài hạn để tái canh vườn cây công nghiệp và đầu tư hệ thống tưới tiết kiệm nước."}

---

#### 3. IMPACT (Hệ Lụy Tín Dụng)
- Khoảng trống tín dụng {gap_pct:.2f}% nếu không được NHCSXH lấp đầy kịp thời sẽ đẩy người dân vào cảnh phải vay lãi nặng bên ngoài hoặc bán nông sản non trước kỳ thu hoạch.

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị 4W1H & Dự Toán)
- **Who:** Chi nhánh Ngân hàng Chính sách Xã hội tỉnh Đắk Lắk và Tổ Tiết kiệm & Vay vốn cấp thôn/buôn.
- **What:** Bổ sung hạn mức tín dụng ưu đãi theo Nghị định 28/2022/NĐ-CP và đơn giản hóa quy trình thẩm định vay tín chấp.
- **Where & When:** Giải ngân trực tiếp cho **{khat_von:,} hộ thuộc {dt_name}**.
- **How much:** Dự toán hạn mức tín dụng **{budget_ty:,.2f} tỷ VNĐ** (định mức bình quân **65,0 triệu VNĐ/hộ**).
"""
