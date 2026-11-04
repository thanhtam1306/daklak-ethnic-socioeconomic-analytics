"""
==============================================================================
MODULE: SEMANTIC POLICY ANALYST & INTELLIGENT TEXT-TO-SQL ENGINE
File: policy_assistant/engine/semantic_analyst.py
Dự án: Hệ thống Hỗ trợ Ra Quyết định & Tham mưu Chính sách KTXH 53 DTTS Đắk Lắk
==============================================================================
Mô tả:
  - Khai thác sức mạnh mô hình Gemini 3.5 Flash để thấu hiểu ngôn ngữ tự nhiên KTXH.
  - Tự động sinh truy vấn SQL chuẩn xác (Text-to-SQL) trên CSDL Star Schema PostgreSQL (daklak_analytics).
  - Tự động tổng hợp báo cáo phân tích nghiệp vụ F-A-I-R sắc bén, đúng 100% trọng tâm câu hỏi.
  - Tích hợp cơ chế phòng thủ SQL Guardrails (Read-only, chống injection, giới hạn dòng).
  - Tự động chuyển đổi mượt mà (Graceful Fallback) về bộ định tuyến luật nếu gặp sự cố mạng/hết quota.
==============================================================================
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
from dotenv import load_dotenv
from google import genai

from ..core.db import execute_query
from ..core.sql_guardrails import validate_and_sanitize_sql

logger = logging.getLogger(__name__)

# Tải biến môi trường từ .env
load_dotenv()

SCHEMA_KNOWLEDGE_BASE = """
BỐI CẢNH CƠ SỞ DỮ LIỆU STAR SCHEMA KTXH 53 DÂN TỘC THIỂU SỐ ĐẮK LẮK (Schema: daklak_analytics):

1. BẢNG NHÂN KHẨU HỌC & CƠ CẤU TUỔI:
   - `fact_nhankhau_dantoc`: ma_ky ('KY_2019', 'KY_2024', 'KY_2026'), ma_dantoc, ten_dantoc (VD: 'Ê đê', 'Mông', 'Tày', 'Gia Rai'...), nhom_nguon_goc ('Bản địa Tây Nguyên', 'Di cư miền núi phía Bắc'...), tong_dan_so, dan_so_nam, dan_so_nu, dan_so_0_14, dan_so_15_59, dan_so_60_plus.
   - Công thức DAX:
     + Tỷ lệ trẻ em: ROUND((dan_so_0_14::numeric / NULLIF(tong_dan_so, 0)) * 100, 2) AS ty_le_0_14_pct
     + Tỷ lệ lao động: ROUND((dan_so_15_59::numeric / NULLIF(tong_dan_so, 0)) * 100, 2) AS ty_le_15_59_pct
     + Tỷ lệ người già: ROUND((dan_so_60_plus::numeric / NULLIF(tong_dan_so, 0)) * 100, 2) AS ty_le_60_plus_pct
     + Tỷ lệ phụ thuộc trẻ em: ROUND((dan_so_0_14::numeric / NULLIF(dan_so_15_59, 0)) * 100, 2) AS ty_le_phu_thuoc_tre_em_pct
     + Chỉ số già hóa: ROUND((dan_so_60_plus::numeric / NULLIF(dan_so_0_14, 0)) * 100, 2) AS chi_so_gia_hoa_pct

2. BẢNG DÂN SỐ ĐỊA BÀN:
   - `fact_danso_huyen_dantoc`: ma_ky, ma_huyen, ten_huyen, ma_dantoc, ten_dantoc, so_ho, nhom_nguon_goc.

3. BẢNG NHÀ Ở, ĐẤT ĐAI, TÍN DỤNG, LAO ĐỘNG & HỌC VẤN DÂN TỘC:
   - `fact_nhao_dantoc`: ma_ky, ten_dantoc, tong_so_ho_co_nha, nha_kien_co_ban_kien_co, nha_thieu_kien_co_don_so.
   - `fact_datsanxuat_dantoc`: ma_ky, ten_dantoc, dien_tich_dat_sx_bq_m2, dien_tich_dat_sx_bq_ha.
   - `fact_tindung_dantoc`: ma_ky, ten_dantoc, so_ho_da_vay_von, so_ho_co_nhu_cau_vay, so_ho_thieu_dat_sx.
   - `fact_laodong_dantoc`: ma_ky, ten_dantoc, tong_lao_dong_co_viec_lam, lao_dong_nong_nghiep, lao_dong_phi_nong_nghiep.
   - `fact_trinhdo_cmkt_dantoc`: ma_ky, ten_dantoc, tong_lao_dong, khong_co_cmkt, so_cap, trung_cap, cao_dang, dai_hoc_tro_len.
   - `fact_giaoduc_dantoc`: ma_ky, ten_dantoc, biet_chu_tong, biet_chu_nam, biet_chu_nu.

4. BẢNG HẠ TẦNG & TỆ NẠN XÃ:
   - `fact_hatang_xa`: ma_ky, ma_xa, ten_xa, ma_huyen, ten_huyen, so_thon.
   - `fact_matuy_hiv_xa`: ma_ky, ma_xa, ten_xa, ma_huyen, ten_huyen, nguoi_nghien_ma_tuy_tong, nguoi_nhiem_hiv_tong.

5. CÁC ANALYTICAL VIEWS TỔNG HỢP TOÀN DIỆN (NÊN ƯU TIÊN SỬ DỤNG CHO TRUY VẤN ĐA KỲ HOẶC TỔNG HỢP):
   - `v_xa_biendong_ngheo_da_ky`: ma_ky, ten_ky, ma_xa, ten_xa, ma_huyen, ten_huyen, km_den_trung_tam_huyen, ty_le_ngheo_pct, so_ho_ngheo, bien_dong_ty_le_ngheo_pct, du_toan_ngan_sach_sinh_ke_trieu_vnd.
   - `v_dantoc_chuyen_dich_da_ky`: ma_ky, ten_ky, ten_dantoc, nhom_nguon_goc, ty_le_ho_ngheo_pct, ty_le_nha_tam_pct, ty_le_chua_qua_dao_tao_pct, ty_le_khat_von_pct, so_ho_ngheo, so_ho_nha_tam.
   - `v_huyen_vesinh_chuyendoiso_da_ky`: ma_ky, ten_ky, ten_huyen, ty_le_ho_xi_hvs_pct, ty_le_internet_pct, ty_le_nuoc_hvs_pct, so_ho_chua_co_ho_xi_hvs, so_ho_chua_co_internet.
   - `v_diemnong_anninh_yte_da_ky`: ma_ky, ten_ky, phan_nhom_rui_ro, ma_doi_tuong, ten_doi_tuong, pham_vi_nhom ('CẤP XÃ' hoặc 'DÂN TỘC'), chi_so_rui_ro_chinh, chi_so_rui_ro_phu, bien_dong_rui_ro_chinh, ty_le_giam_rui_ro_pct.
   - `v_tong_hop_ngan_sach_chinh_sach_ky`: ma_ky, ten_ky, ma_chitieu, ten_chitieu, ten_chinh_sach, so_luong_doi_tuong_can_ho_tro, don_vi_tinh, don_gia_trieu_vnd, tong_kinh_phi_can_phan_bo_ty_vnd, can_cu_phap_ly_dinh_muc, bien_dong_kinh_phi_ty_vnd.

QUY TẮC SQL:
- Luôn chỉ dùng câu lệnh SELECT (Read-only).
- Tên bảng/view phải có prefix `daklak_analytics.` (ví dụ: `daklak_analytics.fact_nhankhau_dantoc`).
- Nếu câu hỏi không nhắc đến năm cụ thể (2019, 2024), mặc định chu kỳ mới nhất là: `ma_ky = 'KY_2026'`.
- Khi tìm kiếm tên dân tộc hoặc địa bàn, luôn dùng toán tử `ILIKE` với wildcard `%` (ví dụ: `ten_dantoc ILIKE '%Ê%Đê%'`, `ten_dantoc ILIKE '%Mông%'`).
- Luôn có ORDER BY và LIMIT hợp lý (tối đa 50 dòng).
"""


class SemanticPolicyAnalyst:
    """Bộ xử lý trí tuệ chính sách sử dụng Gemini 3.5 Flash."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Khởi tạo thành công Gemini Client với model {self.model_name}")
            except Exception as e:
                logger.error(f"Lỗi khởi tạo Gemini Client: {e}")

    def is_available(self) -> bool:
        """Kiểm tra xem Gemini API có khả dụng không."""
        return self.client is not None and bool(self.api_key)

    def generate_sql(self, question: str, default_period: str = "KY_2026") -> Optional[str]:
        """Tự động sinh câu lệnh SQL từ câu hỏi người dùng."""
        if not self.is_available():
            return None

        prompt = f"""
Bạn là Data Analyst phụ trách truy vấn CSDL Star Schema KTXH 53 Dân tộc thiểu số tỉnh Đắk Lắk (PostgreSQL schema daklak_analytics).

{SCHEMA_KNOWLEDGE_BASE}

Câu hỏi của người dùng: "{question}"
Chu kỳ mặc định nếu người dùng không chỉ định năm: {default_period}

Nhiệm vụ:
Viết DUY NHẤT một câu lệnh SQL SELECT an toàn (PostgreSQL) để lấy chính xác các trường dữ liệu cần thiết phục vụ trả lời câu hỏi trên.
YÊU CẦU BẮT BUỘC:
- Chỉ trả về đoạn code SQL thuần túy, TUYỆT ĐỐI KHÔNG dùng markdown fence (như ```sql hoặc ```), không viết lời giải thích mở đầu hay kết thúc.
"""
        try:
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=dict(
                    temperature=0.1,
                    max_output_tokens=1500
                )
            )
            raw_text = res.text.strip()
            # Xóa sạch các dấu markdown nếu có
            cleaned_sql = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
            cleaned_sql = re.sub(r"\n?```$", "", cleaned_sql).strip()
            return cleaned_sql
        except Exception as e:
            logger.error(f"Lỗi khi Gemini sinh SQL: {e}")
            return None

    def synthesize_analytical_brief(
        self,
        question: str,
        df: pd.DataFrame,
        sql_query: str
    ) -> Optional[Dict[str, Any]]:
        """Đọc kết quả CSDL và tổng hợp báo cáo phân tích theo chuẩn F-A-I-R trúng trọng tâm."""
        if not self.is_available() or df is None or df.empty:
            return None

        records_json = df.to_json(orient="records", force_ascii=False)

        prompt = f"""
Bạn là Data Analyst thực hiện phân tích số liệu thực trạng KTXH 53 Dân tộc thiểu số tỉnh Đắk Lắk.
Văn phong yêu cầu: Điềm đạm, rõ ràng, gãy gọn, trung thực với số liệu.
NGUYÊN TẮC:
1. ĐÚNG 100% TRỌNG TÂM CÂU HỎI: Người dùng hỏi gì trả lời thẳng cái đó (so sánh, căn nguyên, xu hướng, ngân sách).
2. TUYỆT ĐỐI KHÔNG vòng vo lý thuyết sách vở.
3. TUYỆT ĐỐI KHÔNG đưa ra hướng dẫn sử dụng phần mềm, không nhắc đến 'bấm slicer', 'lọc chéo' hay 'biểu đồ Power BI' trừ khi người dùng hỏi cách dùng phần mềm.
4. LUÔN CÓ SỐ LIỆU THỰC CHỨNG TỪ BẢNG DỮ LIỆU ĐƯỢC CẤP.

Câu hỏi của người dùng: "{question}"

Số liệu thực chứng vừa truy vấn từ PostgreSQL:
{records_json}

Hãy trả về duy nhất một chuỗi JSON hợp lệ theo cấu trúc sau (KHÔNG dùng markdown fence):
{{
  "intent_code": "Mã nghiệp vụ ngắn (VD: DEMOGRAPHIC_COMPARISON, COMMUNE_POVERTY, HOUSING_POLICY)",
  "intent_description": "Mô tả ngắn gọn trọng tâm phân tích",
  "lead_answer": "Câu trả lời trực diện 1-2 câu đi thẳng vào bản chất câu hỏi và số liệu quan trọng nhất",
  "bullet_points": [
    "Luận điểm 1: Dữ kiện thực chứng & So sánh số liệu cụ thể",
    "Luận điểm 2: Bóc tách căn nguyên gốc rễ (Root Cause) giải thích vì sao có số liệu đó",
    "Luận điểm 3: Tác động KTXH hoặc hệ quả đối với đời sống đồng bào"
  ],
  "takeaway": "1 câu kết luận điều hành sắc nét, gợi mở định hướng chỉ đạo",
  "fair_cards": {{
    "headline": {{
      "badge": "NHÃN CHUYÊN ĐỀ (VD: SO SÁNH NHÂN KHẨU HỌC)",
      "title": "Tiêu đề điều hành ngắn gọn sắc bén",
      "summary": "Tóm tắt kết luận cốt lõi nhất"
    }},
    "fact": {{
      "title": "Dữ kiện thực chứng",
      "points": [
        "Gạch đầu dòng dữ liệu thực tế 1",
        "Gạch đầu dòng dữ liệu thực tế 2"
      ]
    }},
    "analysis": {{
      "title": "Bóc tách căn nguyên",
      "points": [
        "Phân tích nguyên nhân sâu xa 1",
        "Phân tích nguyên nhân sâu xa 2"
      ]
    }},
    "impact": {{
      "title": "Tác động chính sách & rủi ro",
      "points": [
        "Tác động đến ngân sách, an sinh hoặc phát triển 1",
        "Rủi ro nếu không can thiệp kịp thời 2"
      ]
    }},
    "recommendation": {{
      "title": "Khuyến nghị hành động 4W1H",
      "points": [
        "Who & What: Cơ quan chủ trì và hành động can thiệp cụ thể",
        "Where, When & How much: Địa bàn trọng điểm, thời gian và nguồn lực ngân sách (tham chiếu QĐ 1719 / NĐ 28)"
      ]
    }}
  }}
}}
"""
        try:
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=dict(
                    temperature=0.2,
                    max_output_tokens=1500
                )
            )
            raw_text = res.text.strip()
            cleaned_json = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
            cleaned_json = re.sub(r"\n?```$", "", cleaned_json).strip()
            data = json.loads(cleaned_json)
            return data
        except Exception as e:
            logger.error(f"Lỗi khi Gemini tổng hợp báo cáo: {e}")
            return None


# Khởi tạo Singleton Instance
_analyst_instance: Optional[SemanticPolicyAnalyst] = None


def get_semantic_analyst() -> SemanticPolicyAnalyst:
    """Lấy hoặc khởi tạo bộ phân tích ngữ nghĩa Gemini."""
    global _analyst_instance
    if _analyst_instance is None:
        _analyst_instance = SemanticPolicyAnalyst()
    return _analyst_instance


def build_smart_echart_payload(df: pd.DataFrame, brief: Dict[str, Any]) -> Dict[str, Any]:
    """Tự động chọn loại biểu đồ ECharts tối ưu dựa trên dữ liệu thực tế."""
    if df is None or df.empty:
        return {"type": "empty", "title": "Không có dữ liệu biểu đồ"}

    cols = [c.lower() for c in df.columns]
    headline = brief.get("fair_cards", {}).get("headline", {})
    if isinstance(headline, dict):
        chart_title = headline.get("title", "Biểu Đồ Phân Tích Thực Chứng")
        chart_sub = headline.get("summary", "")
    else:
        chart_title = "Biểu Đồ Phân Tích Thực Chứng"
        chart_sub = str(headline)

    # 1. Biểu đồ Tháp tuổi / Cơ cấu 3 nhóm tuổi dân tộc
    has_dantoc = any("dantoc" in c for c in cols)
    has_age_cols = any("0_14" in c for c in cols) and any("15_59" in c for c in cols)
    if has_dantoc and has_age_cols:
        cat_col = next(c for c in df.columns if "dantoc" in c.lower())
        col_0_14 = next(c for c in df.columns if "0_14" in c.lower())
        col_15_59 = next(c for c in df.columns if "15_59" in c.lower())
        col_60 = next((c for c in df.columns if "60" in c.lower()), None)

        cats = [str(v) for v in df[cat_col]]
        s0_14 = [round(float(v or 0), 1) for v in df[col_0_14]]
        s15_59 = [round(float(v or 0), 1) for v in df[col_15_59]]
        s60 = [round(float(v or 0), 1) for v in df[col_60]] if col_60 else [0.0] * len(cats)

        # Nếu là số tuyệt đối (hàng nghìn người) thì quy đổi về %
        if max(s0_14 + s15_59) > 100.0:
            for i in range(len(cats)):
                tot = s0_14[i] + s15_59[i] + s60[i]
                if tot > 0:
                    s0_14[i] = round(s0_14[i] * 100.0 / tot, 1)
                    s15_59[i] = round(s15_59[i] * 100.0 / tot, 1)
                    s60[i] = round(s60[i] * 100.0 / tot, 1)

        return {
            "type": "age_stacked_bar",
            "title": chart_title,
            "subtitle": "Xếp chồng 100%: 0-14 tuổi (Xanh lá) | 15-59 tuổi (Xanh dương) | 60+ tuổi (Cam)",
            "categories": cats,
            "series_0_14": s0_14,
            "series_15_59": s15_59,
            "series_60_plus": s60,
            "unit": "%"
        }

    # 2. Biểu đồ Dự toán Ngân sách
    budget_col = next((c for c in df.columns if any(k in c.lower() for k in ["kinh_phi", "ngan_sach", "ty_vnd"])), None)
    if budget_col:
        cat_col = next((c for c in df.columns if any(k in c.lower() for k in ["chitieu", "chinh_sach", "huyen", "xa", "dantoc"])), df.columns[0])
        cats = [str(v) for v in df[cat_col]]
        vals = [round(float(v or 0), 2) for v in df[budget_col]]
        return {
            "type": "budget_bar",
            "title": chart_title,
            "subtitle": chart_sub or "Dự toán nhu cầu vốn theo định mức chính sách (Tỷ VNĐ)",
            "categories": cats,
            "series_main": vals,
            "unit": " tỷ"
        }

    # 3. Biểu đồ Đường Xu hướng Chuỗi thời gian (Đa kỳ)
    has_period = any("ky" in c or "nam" in c for c in cols)
    if has_period and len(df) >= 2:
        period_col = next(c for c in df.columns if "ky" in c.lower() or "nam" in c.lower())
        num_cols = [c for c in df.columns if df[c].dtype in ("float64", "int64", "numeric") and c != period_col]
        if num_cols:
            target_metric = num_cols[0]
            cats = [str(v) for v in df[period_col]]
            vals = [round(float(v or 0), 2) for v in df[target_metric]]
            return {
                "type": "trend_line",
                "title": chart_title,
                "subtitle": f"Biến động qua các chu kỳ khảo sát ({target_metric})",
                "categories": cats,
                "series_main": vals,
                "unit": "%" if "pct" in target_metric.lower() or "ty_le" in target_metric.lower() else ""
            }

    # 4. Biểu đồ Cột ngang mặc định cho bảng xếp hạng / so sánh chung
    cat_col = next((c for c in df.columns if df[c].dtype == "object"), df.columns[0])
    num_cols = [c for c in df.columns if df[c].dtype in ("float64", "int64", "numeric")]
    if num_cols:
        val_col = num_cols[0]
        cats = [str(v) for v in df[cat_col]]
        vals = [round(float(v or 0), 2) for v in df[val_col]]
        return {
            "type": "bar_horizontal",
            "title": chart_title,
            "subtitle": chart_sub,
            "categories": cats,
            "series_main": vals,
            "unit": "%" if "pct" in val_col.lower() or "ty_le" in val_col.lower() else ""
        }

    return {"type": "empty", "title": chart_title}


def format_gemini_report_markdown(brief: Dict[str, Any], df: pd.DataFrame) -> str:
    """Tạo báo cáo Markdown chuẩn F-A-I-R từ kết quả của Gemini."""
    cards = brief.get("fair_cards", {})
    headline = cards.get("headline", {})
    fact = cards.get("fact", {})
    analysis = cards.get("analysis", {})
    impact = cards.get("impact", {})
    rec = cards.get("recommendation", {})

    fact_bullets = "\n".join([f"- {p}" for p in fact.get("points", [])])
    analysis_bullets = "\n".join([f"- {p}" for p in analysis.get("points", [])])
    impact_bullets = "\n".join([f"- {p}" for p in impact.get("points", [])])
    rec_bullets = "\n".join([f"- {p}" for p in rec.get("points", [])])

    try:
        table_md = df.head(10).to_markdown(index=False) if df is not None and not df.empty else ""
    except Exception:
        # Fallback tạo bảng markdown thủ công không cần thư viện tabulate
        if df is not None and not df.empty:
            cols = list(df.columns)
            header = "| " + " | ".join(cols) + " |"
            sep = "| " + " | ".join(["---"] * len(cols)) + " |"
            rows = []
            for _, r in df.head(10).iterrows():
                rows.append("| " + " | ".join([str(r[c]) for c in cols]) + " |")
            table_md = "\n".join([header, sep] + rows)
        else:
            table_md = ""

    md = f"""### BÁO CÁO THAM MƯU: {headline.get('title', 'PHÂN TÍCH CHUYÊN ĐỀ KTXH').upper()}
**Chuyên đề:** {brief.get('intent_description', 'Khai phá dữ liệu KTXH 53 Dân tộc')} | **Cơ sở dữ liệu:** Star Schema PostgreSQL

---

#### 📌 KẾT LUẬN ĐIỀU HÀNH (EXECUTIVE HEADLINE)
{headline.get('summary', brief.get('lead_answer', ''))}

---

#### 1. FACT (Dữ Kiện Thực Chứng CSDL)
{table_md}

{fact_bullets}

---

#### 2. ANALYSIS (Phân Tích Bóc Tách Bản Chất & Căn Nguyên)
{analysis_bullets}

---

#### 3. IMPACT (Tác Động Nghiệp Vụ & Cảnh Báo Rủi Ro)
{impact_bullets}

---

#### 4. RECOMMENDATION & BUDGET (Khuyến Nghị Hành Động 4W1H)
{rec_bullets}
"""
    return md

