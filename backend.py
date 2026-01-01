#!/usr/bin/env python3
"""
Backend functionality for Purchase Order Generator
Handles CSV loading, parsing, and PDF generation.
"""

import csv
import os
import re
from collections import defaultdict
from datetime import datetime

# ReportLab imports for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    print("ReportLab library not found. Please install it using: pip install reportlab")

def extract_base_name_and_size(item_name):
    """Extract base product name and size from full item name."""
    size_patterns = [
        r'\s*-\s*(\d*X*[SML]+)\s*$',
        r'\s*/\s*(\d*X*[SML]+)\s*$',
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, item_name)
        if match:
            size = match.group(1)
            base_name = re.sub(pattern, '', item_name).strip()
            return base_name, size
    
    return item_name, None


def load_orders(csv_file="orders_export.csv"):
    """Load orders from CSV and group by product type."""
    if not csv_file or not os.path.exists(csv_file):
        return {}
    
    products = defaultdict(lambda: defaultdict(int))
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            item_name = row.get('Lineitem name', '').strip()
            quantity_str = row.get('Lineitem quantity', '').strip()
            
            if not item_name or not quantity_str:
                continue
            
            try:
                quantity = int(quantity_str)
                base_name, size = extract_base_name_and_size(item_name)
                
                if size:
                    products[base_name][size] += quantity
                else:
                    products[base_name]['N/A'] += quantity
                    
            except ValueError:
                continue
    
    return products


def generate_pdf_po(products_data, company_info, vendor_info, ship_to_info, output_file, logo_path=None):
    """Generate a PDF purchase order matching the reference layout."""
    doc = SimpleDocTemplate(output_file, pagesize=letter,
                           leftMargin=0.5*inch, rightMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#003366'), # Dark Blue
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold'
    )
    
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_LEFT
    )
    
    header_label_style = ParagraphStyle(
        'HeaderLabel',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    header_value_style = ParagraphStyle(
        'HeaderValue',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # --- Top Header Section ---
    # Left Column: Logo (optional) -> Company Info
    # Right Column: "Purchase Order" Title -> Date/PO#
    
    # 1. Prepare Logo
    logo = []
    if logo_path and os.path.exists(logo_path):
        try:
            # Resize image to fit in ~2 inch width/height max while keeping aspect ratio
            img = Image(logo_path)
            img_width = img.drawWidth
            img_height = img.drawHeight
            max_dim = 1.5 * inch
            
            if img_width > max_dim or img_height > max_dim:
                ratio = min(max_dim/img_width, max_dim/img_height)
                img.drawWidth = img_width * ratio
                img.drawHeight = img_height * ratio
            
            logo = [img]
        except Exception as e:
            print(f"Error loading logo: {e}")
            logo = [Paragraph("[Logo Error]", styles['Normal'])]
    else:
         logo = [Spacer(1, 0.5*inch)] # spacer where logo would be

    # 2. Company Info Block
    company_text = [
        Paragraph(f"<b>{company_info['name']}</b>", company_style),
        Paragraph(company_info['address'], company_style),
        Paragraph(company_info['city'], company_style),
        Paragraph(f"Phone: {company_info['phone']}", company_style),
        Paragraph(f"Fax: {company_info['fax']}", company_style),
    ]
    
    # 3. Title Block
    title_text = [Paragraph("Purchase Order", title_style)]
    
    # 4. Date/PO Block
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    po_date = datetime.now().strftime("%m/%d/%Y")
    
    # Small table for Date/PO alignment
    date_po_data = [
        [Paragraph("<b>Date</b>", header_label_style), Paragraph(po_date, header_value_style)],
        [Paragraph("<b>P.O. #</b>", header_label_style), Paragraph(timestamp, header_value_style)]
    ]
    date_po_table = Table(date_po_data, colWidths=[0.8*inch, 1.5*inch])
    date_po_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))

    # Combine into Top Layout Table
    # Col 1: Logo and Company Info
    # Col 2: Title and Date/PO
    
    # Left cell content
    left_content = logo + [Spacer(1, 0.2*inch)] + company_text
    
    # Right cell content
    right_content = title_text + [Spacer(1, 0.3*inch)] + [date_po_table]
    
    top_table_data = [[left_content, right_content]]
    top_table = Table(top_table_data, colWidths=[4*inch, 3.5*inch])
    top_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(top_table)
    story.append(Spacer(1, 0.4*inch))
    
    # --- Vendor and Ship To Section (Blue Headers) ---
    vendor_block = [
        paragraph for paragraph in [
            Paragraph(f"<b>{vendor_info['name']}</b>", company_style),
            Paragraph(f"{vendor_info['website']}", company_style) if vendor_info['website'] else None,
            Paragraph(f"{vendor_info['address']}", company_style),
            Paragraph(f"{vendor_info['city']}", company_style),
            Paragraph(f"Phone: {vendor_info['phone']}", company_style),
        ] if paragraph is not None
    ]
    
    ship_to_block = [
         paragraph for paragraph in [
            Paragraph(f"Attn: {ship_to_info['attn']}", company_style),
            Paragraph(f"{ship_to_info['company']}", company_style),
            Paragraph(f"{ship_to_info['address']}", company_style),
            Paragraph(f"{ship_to_info['city']}", company_style) if ship_to_info.get('city') else None,
            Paragraph(f"Phone: {ship_to_info['phone']}", company_style),
        ] if paragraph is not None
    ]

    def create_section_table(header_text, content_blocks):
        # Header Row
        t_data = [[Paragraph(header_text, section_header_style)]]
        # Content Row
        t_data.append([content_blocks])
        
        t = Table(t_data, colWidths=[3.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#003366')), # Dark Blue Header
            ('TEXTCOLOR', (0,0), (0,0), colors.white),
            ('BOTTOMPADDING', (0,0), (0,0), 6),
            ('TOPPADDING', (0,0), (0,0), 6),
            ('VALIGN', (0,1), (0,1), 'TOP'),
            ('TOPPADDING', (0,1), (0,1), 6),
        ]))
        return t

    vendor_table = create_section_table("Vendor", vendor_block)
    ship_table = create_section_table("Ship To", ship_to_block)
    
    container_data = [[vendor_table, "", ship_table]]
    container_table = Table(container_data, colWidths=[3.5*inch, 0.5*inch, 3.5*inch])
    container_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(container_table)
    story.append(Spacer(1, 0.4*inch))
    
    # --- Product Details Section ---
    
    # Loop through all selected products
    for product_name, sizes_dict in products_data:
        # Keep product parts together to avoid breaking headers from content
        product_parts = []
        
        product_parts.append(Paragraph(f"<b>Item Details</b>", section_header_style)) 
        product_parts.append(Paragraph(f"Product: <b>{product_name}</b>", styles['Normal']))
        product_parts.append(Spacer(1, 0.1*inch))
        
        # Size breakdown table
        size_data = [['Size', 'Quantity']]
        sorted_sizes = sorted(sizes_dict.items(), key=lambda x: (
            len(x[0]) if x[0] != 'N/A' else 999,
            x[0]
        ))
        
        for size, qty in sorted_sizes:
            size_label = "No Size" if size == 'N/A' else size
            size_data.append([size_label, str(qty)])
        
        total_qty = sum(sizes_dict.values())
        size_data.append(['TOTAL', str(total_qty)])
        
        size_table = Table(size_data, colWidths=[5.5*inch, 2*inch])
        size_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')), # Header Blue
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'), 
            ('LEFTPADDING', (0, 0), (0, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0f7')), # Total Row Light Blue
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        product_parts.append(size_table)
        product_parts.append(Spacer(1, 0.3*inch))
        
        # Add to story using KeepTogether if possible, or just append
        story.extend(product_parts)
    
    # Build PDF
    doc.build(story)
