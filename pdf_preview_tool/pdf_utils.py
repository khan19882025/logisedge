"""
PDF Generation Utilities with Signature Integration
Provides functions to generate PDF documents with embedded user signatures/stamps
"""

import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from django.conf import settings
from .models import SignatureStamp


class PDFGenerator:
    """PDF generator with signature integration capabilities"""
    
    def __init__(self, user=None):
        self.user = user
        self.styles = getSampleStyleSheet()
        self.signature = None
        self.load_user_signature()
    
    def load_user_signature(self):
        """Load the user's signature/stamp if available"""
        if self.user:
            try:
                self.signature = SignatureStamp.objects.get(user=self.user)
            except SignatureStamp.DoesNotExist:
                self.signature = None
    
    def add_signature_to_pdf(self, story, page_width, page_height):
        """Add signature section to the PDF document"""
        if not self.signature:
            return story
        
        # Add spacer before signature section
        story.append(Spacer(1, 20))
        
        # Create signature table
        signature_data = [
            ['', 'Authorized Signatory'],
            ['', ''],  # Empty row for signature image
        ]
        
        # Create signature table with proper styling
        signature_table = Table(signature_data, colWidths=[page_width * 0.6, page_width * 0.4])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 10),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.black),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),  # No visible grid
        ]))
        
        story.append(signature_table)
        
        # Add signature image
        try:
            signature_path = self.signature.file.path
            if os.path.exists(signature_path):
                # Create signature image with proper dimensions (150x60 px equivalent)
                signature_img = Image(signature_path, width=1.5*inch, height=0.6*inch)
                signature_img.hAlign = 'RIGHT'
                
                # Position the signature image in the right column
                signature_img_table = Table([[signature_img]], colWidths=[page_width * 0.4])
                signature_img_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (0, 0), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0, colors.white),
                ]))
                
                story.append(signature_img_table)
        except Exception as e:
            # If signature image fails to load, add text placeholder
            story.append(Paragraph(
                f"<i>Signature image unavailable: {str(e)}</i>",
                self.styles['Italic']
            ))
        
        return story


class InvoicePDFGenerator(PDFGenerator):
    """Generate invoice PDFs with signature integration"""
    
    def generate_invoice_pdf(self, invoice_data, output_path=None):
        """Generate an invoice PDF with embedded signature"""
        if output_path is None:
            output_path = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Page dimensions
        page_width, page_height = A4
        
        # Header
        story.append(Paragraph("INVOICE", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Company and invoice details
        company_info = [
            ['Company Name:', invoice_data.get('company_name', 'Your Company')],
            ['Address:', invoice_data.get('company_address', 'Company Address')],
            ['Phone:', invoice_data.get('company_phone', 'Phone Number')],
            ['Email:', invoice_data.get('company_email', 'email@company.com')],
        ]
        
        company_table = Table(company_info, colWidths=[page_width * 0.3, page_width * 0.7])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(company_table)
        story.append(Spacer(1, 20))
        
        # Invoice details
        invoice_details = [
            ['Invoice Number:', invoice_data.get('invoice_number', 'INV-001')],
            ['Date:', invoice_data.get('invoice_date', '2024-01-01')],
            ['Due Date:', invoice_data.get('due_date', '2024-02-01')],
        ]
        
        invoice_table = Table(invoice_details, colWidths=[page_width * 0.3, page_width * 0.7])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 20))
        
        # Customer information
        story.append(Paragraph("Bill To:", self.styles['Heading2']))
        customer_info = [
            ['Name:', invoice_data.get('customer_name', 'Customer Name')],
            ['Address:', invoice_data.get('customer_address', 'Customer Address')],
            ['Email:', invoice_data.get('customer_email', 'customer@email.com')],
        ]
        
        customer_table = Table(customer_info, colWidths=[page_width * 0.3, page_width * 0.7])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(customer_table)
        story.append(Spacer(1, 20))
        
        # Items table
        story.append(Paragraph("Items:", self.styles['Heading2']))
        
        items_data = [['Description', 'Quantity', 'Unit Price', 'Total']]
        items = invoice_data.get('items', [])
        
        for item in items:
            items_data.append([
                item.get('description', 'Item Description'),
                str(item.get('quantity', 1)),
                f"${item.get('unit_price', 0):.2f}",
                f"${item.get('total', 0):.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[page_width * 0.4, page_width * 0.2, page_width * 0.2, page_width * 0.2])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals
        subtotal = invoice_data.get('subtotal', 0)
        tax = invoice_data.get('tax', 0)
        total = invoice_data.get('total', 0)
        
        totals_data = [
            ['Subtotal:', f"${subtotal:.2f}"],
            ['Tax:', f"${tax:.2f}"],
            ['Total:', f"${total:.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[page_width * 0.8, page_width * 0.2])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(totals_table)
        
        # Add signature
        story = self.add_signature_to_pdf(story, page_width, page_height)
        
        # Build PDF
        doc.build(story)
        return output_path


class DeliveryNotePDFGenerator(PDFGenerator):
    """Generate delivery note PDFs with signature integration"""
    
    def generate_delivery_note_pdf(self, delivery_data, output_path=None):
        """Generate a delivery note PDF with embedded signature"""
        if output_path is None:
            output_path = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Page dimensions
        page_width, page_height = A4
        
        # Header
        story.append(Paragraph("DELIVERY NOTE", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Company and delivery details
        company_info = [
            ['Company Name:', delivery_data.get('company_name', 'Your Company')],
            ['Address:', delivery_data.get('company_address', 'Company Address')],
            ['Phone:', delivery_data.get('company_phone', 'Phone Number')],
        ]
        
        company_table = Table(company_info, colWidths=[page_width * 0.3, page_width * 0.7])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(company_table)
        story.append(Spacer(1, 20))
        
        # Delivery details
        delivery_details = [
            ['Delivery Note Number:', delivery_data.get('delivery_number', 'DN-001')],
            ['Date:', delivery_data.get('delivery_date', '2024-01-01')],
            ['Customer PO:', delivery_data.get('customer_po', 'PO-001')],
        ]
        
        delivery_table = Table(delivery_details, colWidths=[page_width * 0.3, page_width * 0.7])
        delivery_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(delivery_table)
        story.append(Spacer(1, 20))
        
        # Customer information
        story.append(Paragraph("Deliver To:", self.styles['Heading2']))
        customer_info = [
            ['Name:', delivery_data.get('customer_name', 'Customer Name')],
            ['Address:', delivery_data.get('customer_address', 'Customer Address')],
            ['Contact:', delivery_data.get('customer_contact', 'Contact Person')],
        ]
        
        customer_table = Table(customer_info, colWidths=[page_width * 0.3, page_width * 0.7])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(customer_table)
        story.append(Spacer(1, 20))
        
        # Items table
        story.append(Paragraph("Items Delivered:", self.styles['Heading2']))
        
        items_data = [['Description', 'Quantity', 'Unit', 'Remarks']]
        items = delivery_data.get('items', [])
        
        for item in items:
            items_data.append([
                item.get('description', 'Item Description'),
                str(item.get('quantity', 1)),
                item.get('unit', 'PCS'),
                item.get('remarks', '')
            ])
        
        items_table = Table(items_data, colWidths=[page_width * 0.4, page_width * 0.2, page_width * 0.2, page_width * 0.2])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Delivery conditions
        story.append(Paragraph("Delivery Conditions:", self.styles['Heading2']))
        conditions = [
            '• Goods received in good condition',
            '• Delivery completed as per specifications',
            '• Customer signature required for receipt',
        ]
        
        for condition in conditions:
            story.append(Paragraph(condition, self.styles['Normal']))
        
        # Add signature
        story = self.add_signature_to_pdf(story, page_width, page_height)
        
        # Build PDF
        doc.build(story)
        return output_path


class PurchaseOrderPDFGenerator(PDFGenerator):
    """Generate purchase order PDFs with signature integration"""
    
    def generate_purchase_order_pdf(self, po_data, output_path=None):
        """Generate a purchase order PDF with embedded signature"""
        if output_path is None:
            output_path = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Page dimensions
        page_width, page_height = A4
        
        # Header
        story.append(Paragraph("PURCHASE ORDER", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Company and PO details
        company_info = [
            ['Company Name:', po_data.get('company_name', 'Your Company')],
            ['Address:', po_data.get('company_address', 'Company Address')],
            ['Phone:', po_data.get('company_phone', 'Phone Number')],
            ['Email:', po_data.get('company_email', 'email@company.com')],
        ]
        
        company_table = Table(company_info, colWidths=[page_width * 0.3, page_width * 0.7])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(company_table)
        story.append(Spacer(1, 20))
        
        # PO details
        po_details = [
            ['Purchase Order Number:', po_data.get('po_number', 'PO-001')],
            ['Date:', po_data.get('po_date', '2024-01-01')],
            ['Required Date:', po_data.get('required_date', '2024-02-01')],
        ]
        
        po_table = Table(po_details, colWidths=[page_width * 0.3, page_width * 0.7])
        po_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(po_table)
        story.append(Spacer(1, 20))
        
        # Supplier information
        story.append(Paragraph("Supplier:", self.styles['Heading2']))
        supplier_info = [
            ['Name:', po_data.get('supplier_name', 'Supplier Name')],
            ['Address:', po_data.get('supplier_address', 'Supplier Address')],
            ['Contact:', po_data.get('supplier_contact', 'Contact Person')],
            ['Phone:', po_data.get('supplier_phone', 'Phone Number')],
        ]
        
        supplier_table = Table(supplier_info, colWidths=[page_width * 0.3, page_width * 0.7])
        supplier_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(supplier_table)
        story.append(Spacer(1, 20))
        
        # Items table
        story.append(Paragraph("Items Ordered:", self.styles['Heading2']))
        
        items_data = [['Description', 'Quantity', 'Unit', 'Unit Price', 'Total']]
        items = po_data.get('items', [])
        
        for item in items:
            items_data.append([
                item.get('description', 'Item Description'),
                str(item.get('quantity', 1)),
                item.get('unit', 'PCS'),
                f"${item.get('unit_price', 0):.2f}",
                f"${item.get('total', 0):.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[page_width * 0.35, page_width * 0.15, page_width * 0.15, page_width * 0.15, page_width * 0.2])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals
        subtotal = po_data.get('subtotal', 0)
        tax = po_data.get('tax', 0)
        total = po_data.get('total', 0)
        
        totals_data = [
            ['Subtotal:', f"${subtotal:.2f}"],
            ['Tax:', f"${tax:.2f}"],
            ['Total:', f"${total:.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[page_width * 0.8, page_width * 0.2])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        story.append(totals_table)
        
        # Terms and conditions
        story.append(Spacer(1, 20))
        story.append(Paragraph("Terms and Conditions:", self.styles['Heading2']))
        terms = [
            '• Payment terms: Net 30 days',
            '• Delivery: As specified above',
            '• Quality: Must meet company standards',
            '• Returns: Subject to company policy',
        ]
        
        for term in terms:
            story.append(Paragraph(term, self.styles['Normal']))
        
        # Add signature
        story = self.add_signature_to_pdf(story, page_width, page_height)
        
        # Build PDF
        doc.build(story)
        return output_path


# Utility functions for easy PDF generation
def generate_invoice_with_signature(user, invoice_data, output_path=None):
    """Generate invoice PDF with user's signature"""
    generator = InvoicePDFGenerator(user)
    return generator.generate_invoice_pdf(invoice_data, output_path)


def generate_delivery_note_with_signature(user, delivery_data, output_path=None):
    """Generate delivery note PDF with user's signature"""
    generator = DeliveryNotePDFGenerator(user)
    return generator.generate_delivery_note_pdf(delivery_data, output_path)


def generate_purchase_order_with_signature(user, po_data, output_path=None):
    """Generate purchase order PDF with user's signature"""
    generator = PurchaseOrderPDFGenerator(user)
    return generator.generate_purchase_order_pdf(po_data, output_path)


def get_user_signature_status(user):
    """Check if user has uploaded a signature"""
    try:
        signature = SignatureStamp.objects.get(user=user)
        return {
            'has_signature': True,
            'file_url': signature.file.url,
            'uploaded_at': signature.uploaded_at,
            'file_size_mb': signature.file_size_mb
        }
    except SignatureStamp.DoesNotExist:
        return {
            'has_signature': False,
            'file_url': None,
            'uploaded_at': None,
            'file_size_mb': 0
        }
