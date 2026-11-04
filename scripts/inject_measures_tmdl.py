import os
import re
import sys
import uuid

if sys.stdout and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

DAX_FILE = "dashboards/dax/daklak_enterprise_measures.dax"
TMDL_PATHS = [
    "dashboards/pbix/Dashboard.SemanticModel/definition/tables/_Measures.tmdl",
]


def det_uuid(seed_str: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"daklak.pbi.{seed_str}"))


def extract_existing_measure_lineage_tags(measures_tmdl_path: str) -> dict:
    tags = {}
    if not os.path.exists(measures_tmdl_path):
        return tags
    with open(measures_tmdl_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    pattern = re.compile(
        r"measure\s+'([^']+)'\s*=.*?lineageTag:\s*([0-9a-fA-F\-]{36})",
        re.DOTALL,
    )
    for m in pattern.finditer(content):
        tags[m.group(1)] = m.group(2)
    return tags


def parse_dax_file(dax_path: str) -> list:
    with open(dax_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    measures = []
    current_folder = "01_Executive_KPIs"
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        folder_match = re.search(r"DISPLAY FOLDER:\s*([A-Za-z0-9_]+)", stripped)
        if folder_match:
            current_folder = folder_match.group(1)
            i += 1
            continue

        if stripped.startswith("// 10. SIÊU CÔNG THỨC"):
            current_folder = "08_Policy_Intervention_Allocation"
            i += 1
            continue

        m_start = re.match(r"^\[([^\]]+)\]\s*=\s*(.*)$", stripped)
        if m_start:
            m_name = m_start.group(1).strip()
            first_expr = m_start.group(2).strip()
            expr_lines = []
            if first_expr:
                expr_lines.append(first_expr)
            fmt_str = None
            i += 1
            while i < n:
                cur_line = lines[i]
                cur_strip = cur_line.strip()
                fmt_match = re.match(r"^/\*\s*Format String:\s*(.+?)\s*\*/$", cur_strip)
                if fmt_match:
                    fmt_str = fmt_match.group(1).strip()
                    i += 1
                    break
                if re.match(r"^\[([^\]]+)\]\s*=", cur_strip) or re.search(
                    r"DISPLAY FOLDER:", cur_strip
                ):
                    break
                expr_lines.append(cur_line.rstrip("\r\n"))
                i += 1

            while expr_lines and (
                expr_lines[-1].strip() == ""
                or expr_lines[-1].strip().startswith("//")
            ):
                expr_lines.pop()

            measures.append(
                {
                    "name": m_name,
                    "folder": current_folder,
                    "expression": "\n".join(expr_lines),
                    "format_string": fmt_str,
                }
            )
        else:
            i += 1

    return measures


def write_measures_tmdl(measures: list, existing_tags: dict, out_path: str):
    lines = [
        "table _Measures",
        "\tlineageTag: 6930d131-3a6c-4289-8845-0dd1bee87397",
        "",
    ]

    for m in measures:
        name = m["name"]
        folder = m["folder"]
        expr = m["expression"]
        fmt = m["format_string"]
        ltag = existing_tags.get(name, det_uuid(f"measure.{name}"))

        lines.append(f"\tmeasure '{name}' =")
        lines.append("\t\t\t")
        for eline in expr.split("\n"):
            lines.append(f"\t\t\t{eline}")

        is_custom_fmt = False
        if fmt:
            if '"' in fmt:
                is_custom_fmt = True
            lines.append(f"\t\tformatString: {fmt}")

        lines.append(f"\t\tdisplayFolder: {folder}")
        lines.append(f"\t\tlineageTag: {ltag}")
        if is_custom_fmt:
            lines.append("")
            lines.append('\t\tannotation PBI_FormatHint = {"isCustom":true}')
        lines.append("")

    lines.extend(
        [
            "\tcolumn Status",
            "\t\tisHidden",
            "\t\tlineageTag: bd13d250-2b45-4250-ae9f-8991b0dcedea",
            "\t\tsummarizeBy: none",
            "\t\tisNameInferred",
            "\t\tsourceColumn: [Status]",
            "",
            "\t\tannotation SummarizationSetBy = Automatic",
            "",
            "\tpartition _Measures = calculated",
            "\t\tmode: import",
            '\t\tsource = ROW("Status", "Active")',
            "",
            "\tannotation PBI_Id = 97dd234fcfb14e2ea9506c2bf7382e35",
            "",
        ]
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    merged_tags = {}
    for p in reversed(TMDL_PATHS):
        merged_tags.update(extract_existing_measure_lineage_tags(p))

    measures = parse_dax_file(DAX_FILE)
    for p in TMDL_PATHS:
        write_measures_tmdl(measures, merged_tags, p)
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        bad = any(x in txt for x in ["Æ°", "á»", "Ã¢", "Ä‘", "ðŸ"])
        print(f"Updated {p}: {len(measures)} measures | Mojibake={bad}")

