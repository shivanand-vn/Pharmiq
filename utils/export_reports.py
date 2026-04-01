"""
Utility functions to export reports to PDF and Excel.
"""

import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def export_to_excel(columns, data, file_path):
    """
    Export the given data rows to an Excel file using pandas.
    columns: list of human-readable column titles.
    data: list of dicts or tuples containing the row data.
    """
    # If data is list of dicts, we should convert to list of lists based on column keys
    # Assuming the caller has pre-formatted the data into a list of lists 
    # matching the order of 'columns'.
    
    try:
        df = pd.DataFrame(data, columns=columns)
        df.to_excel(file_path, index=False, engine='openpyxl')
        return True, "Export to Excel successful"
    except Exception as e:
        return False, str(e)


def export_to_pdf(title, columns, data, file_path, orientation='landscape'):
    """
    Export the given data rows to a PDF document using reportlab.
    title: Title of the report.
    columns: list of column headers.
    data: list of lists representing rows.
    """
    try:
        pagesize = landscape(letter) if orientation == 'landscape' else letter
        doc = SimpleDocTemplate(file_path, pagesize=pagesize, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Add custom title style
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=15,
            textColor=colors.HexColor('#1B4F6B'),
            alignment=1 # Center
        )
        
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 15))
        
        if not data:
            elements.append(Paragraph("No data found for the selected filters.", styles['Normal']))
            doc.build(elements)
            return True, "Exported empty report"
            
        # Convert data everything to strings to prevent reportlab errors
        str_data = []
        for row in data:
            str_data.append([str(item) if item is not None else "" for item in row])
            
        table_data = [columns] + str_data
        
        # Calculate dynamic column widths roughly based on page size and number of columns
        page_width = pagesize[0] - 60 # Account for margins
        col_width = page_width / len(columns)
        
        t = Table(table_data, colWidths=[col_width] * len(columns))
        
        # Add style
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Row styles
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#4B5563')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(t)
        doc.build(elements)
        
        return True, "Export to PDF successful"
        
    except Exception as e:
        return False, str(e)
