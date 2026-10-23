"""
CSV Exporter with Formula Injection Mitigation and Unicode Support.
"""
import csv
import io
from typing import List, Union
from api.models import BusinessLead

# Formula triggers according to OWASP CSV Injection guidelines
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell_value(val: Union[str, int, float, None]) -> str:
    """
    Sanitize value to prevent CSV formula injection in spreadsheet software.
    Prepends a single quote if string begins with =, +, -, @, tab, or carriage return.
    Never invents data for missing values; returns empty string for None.
    """
    if val is None:
        return ""
    
    val_str = str(val)
    if not val_str:
        return ""
    
    # If starts with any formula prefix or whitespace followed by formula prefix
    if val_str.startswith(FORMULA_PREFIXES) or val_str.lstrip(" ").startswith(FORMULA_PREFIXES):
        return f"'{val_str}"
        
    return val_str.strip()


def generate_leads_csv(listings: List[BusinessLead]) -> bytes:
    """
    Generates a UTF-8 with BOM (utf-8-sig) encoded CSV byte string.
    BOM ensures Excel on Windows and other platforms renders multilingual characters properly.
    """
    output = io.StringIO()
    writer = csv.writer(output, dialect="excel", quoting=csv.QUOTE_MINIMAL)
    
    # Headers
    headers = [
        "Business Name",
        "Category",
        "Phone",
        "Website",
        "Full Address",
        "City",
        "Postal Code",
        "Latitude",
        "Longitude",
        "OpenStreetMap Link",
        "OSM Object ID",
    ]
    writer.writerow(headers)
    
    for lead in listings:
        row = [
            sanitize_cell_value(lead.name),
            sanitize_cell_value(lead.category_label or lead.category),
            sanitize_cell_value(lead.phone),
            sanitize_cell_value(lead.website),
            sanitize_cell_value(lead.address),
            sanitize_cell_value(lead.city),
            sanitize_cell_value(lead.postcode),
            str(lead.lat) if lead.lat is not None else "",
            str(lead.lon) if lead.lon is not None else "",
            sanitize_cell_value(lead.osm_url),
            sanitize_cell_value(lead.id),
        ]
        writer.writerow(row)
        
    # Encode with UTF-8 BOM
    return output.getvalue().encode("utf-8-sig")
