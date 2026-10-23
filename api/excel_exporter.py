"""
Excel (.xlsx) Exporter with Professional Styling and Formula Injection Mitigation.
Generates genuine Microsoft Excel workbooks using openpyxl.
"""
import io
from typing import List, Union
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from api.models import BusinessLead

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_excel_value(val: Union[str, int, float, None]) -> Union[str, int, float]:
    """
    Sanitize value to prevent spreadsheet formula execution.
    Prepends a single quote if string begins with =, +, -, @, tab, or carriage return.
    """
    if val is None:
        return ""
    if isinstance(val, (int, float)):
        return val
    
    val_str = str(val).strip()
    if not val_str:
        return ""
        
    if val_str.startswith(FORMULA_PREFIXES) or val_str.lstrip(" ").startswith(FORMULA_PREFIXES):
        return f"'{val_str}"
        
    return val_str


def generate_leads_excel(listings: List[BusinessLead], sheet_title: str = "Business Leads") -> bytes:
    """
    Builds a professionally styled Excel workbook in memory and returns binary bytes.
    Includes dark navy header row, subtle borders, auto-fitted column widths, and sanitized values.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]  # Excel limits sheet name to 31 chars

    # Clean grid lines
    ws.views.sheetView[0].showGridLines = True

    headers = [
        "Business Name",
        "Category",
        "Phone",
        "Website",
        "Email",
        "Full Address",
        "City",
        "Postal Code",
        "Latitude",
        "Longitude",
        "Data Source",
        "OpenStreetMap Link",
        "OSM Object ID",
        "Scraped Timestamp",
    ]

    # Styling definitions
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)

    data_font = Font(name="Calibri", size=10, color="0F172A")
    data_alignment = Alignment(horizontal="left", vertical="center")
    
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    # Write header
    ws.append(headers)
    ws.row_dimensions[1].height = 26

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Write data rows
    for row_idx, lead in enumerate(listings, start=2):
        row_values = [
            sanitize_excel_value(lead.name),
            sanitize_excel_value(lead.category_label or lead.category),
            sanitize_excel_value(lead.phone),
            sanitize_excel_value(lead.website),
            sanitize_excel_value(lead.email),
            sanitize_excel_value(lead.address),
            sanitize_excel_value(lead.city),
            sanitize_excel_value(lead.postcode),
            lead.lat if lead.lat is not None else "",
            lead.lon if lead.lon is not None else "",
            sanitize_excel_value(lead.data_source),
            sanitize_excel_value(lead.osm_url),
            sanitize_excel_value(lead.id),
            sanitize_excel_value(lead.search_timestamp),
        ]
        ws.append(row_values)
        ws.row_dimensions[row_idx].height = 20

        for col_num in range(1, len(row_values) + 1):
            cell = ws.cell(row=row_idx, column=col_num)
            cell.font = data_font
            cell.alignment = data_alignment
            cell.border = thin_border

    # Auto-adjust column widths with sensible min/max constraints
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        # Add padding and clamp
        adjusted_width = min(max(max_len + 3, 12), 45)
        ws.column_dimensions[col_letter].width = adjusted_width

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
