"""
PDF Report Generator for PM2.5 Analysis Results

This module generates professional PDF reports containing:
- Analysis results and PM2.5 estimation
- AQI category and health advice
- Atmospheric features
- Visualizations and heatmaps
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image as RLImage, KeepTogether
)
from io import BytesIO
from datetime import datetime
import os


class PM25ReportGenerator:
    """Generate professional PDF reports for PM2.5 analysis results."""
    
    # Color palette
    PRIMARY = HexColor("#0F172A")
    SECONDARY = HexColor("#2563EB")
    ACCENT = HexColor("#38BDF8")
    SUCCESS = HexColor("#10B981")
    WARNING = HexColor("#F59E0B")
    ERROR = HexColor("#EF4444")
    
    def __init__(self):
        """Initialize the PDF generator."""
        self.page_width, self.page_height = A4
        self.margin = 0.5 * inch
        self.styles = self._create_styles()
    
    def _create_styles(self):
        """Create custom paragraph styles for the report."""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=self.PRIMARY,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.SECONDARY,
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.PRIMARY,
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderColor=self.SECONDARY,
            borderWidth=2,
            borderPadding=8,
            borderRadius=4
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=HexColor("#475569"),
            spaceAfter=6,
            leading=14,
            alignment=TA_LEFT
        ))
        
        # Label style
        styles.add(ParagraphStyle(
            name='Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor("#64748B"),
            fontName='Helvetica-Bold'
        ))
        
        return styles
    
    def generate_pdf(self, analysis_data, image_paths=None):
        """
        Generate PDF report from analysis data.
        
        Args:
            analysis_data (dict): Analysis results containing PM2.5, features, etc.
            image_paths (dict): Optional paths to images for embedding
            
        Returns:
            BytesIO: PDF file as bytes
        """
        if image_paths is None:
            image_paths = {}
        
        # Create PDF in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build document content
        story = []
        
        # Header section
        story.extend(self._create_header())
        story.append(Spacer(1, 0.3 * inch))
        
        # Summary section
        story.extend(self._create_summary_section(analysis_data))
        story.append(Spacer(1, 0.2 * inch))
        
        # Features section
        story.extend(self._create_features_section(analysis_data))
        story.append(Spacer(1, 0.2 * inch))
        
        # Images section
        story.extend(self._create_images_section(analysis_data, image_paths))
        
        # Footer section
        story.append(Spacer(1, 0.2 * inch))
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        # Reset buffer position to beginning
        pdf_buffer.seek(0)
        return pdf_buffer
    
    def _create_header(self):
        """Create report header."""
        story = []
        
        # Title
        story.append(Paragraph(
            "PM2.5 ESTIMATION SYSTEM",
            self.styles['CustomTitle']
        ))
        
        # Subtitle
        story.append(Paragraph(
            "Satellite Image Analysis Report",
            self.styles['CustomSubtitle']
        ))
        
        # Report info
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_text = f"<b>Report Generated:</b> {report_date} | <b>Version:</b> 1.0"
        story.append(Paragraph(
            info_text,
            self.styles['CustomBody']
        ))
        
        return story
    
    def _create_summary_section(self, data):
        """Create PM2.5 estimation summary section."""
        story = []
        
        story.append(Paragraph(
            "ANALYSIS RESULTS",
            self.styles['SectionHeading']
        ))
        
        # Main metrics table
        pm25_value = data.get('pm25', 0)
        confidence = data.get('confidence', 0)
        aqi_category = data.get('aqi_category', 'Unknown')
        timestamp = data.get('timestamp', 'N/A')
        
        metrics_data = [
            ['Metric', 'Value', 'Unit'],
            ['PM2.5 Concentration', f"{pm25_value:.2f}", 'µg/m³'],
            ['Confidence Level', f"{confidence:.1f}", '%'],
            ['AQI Category', aqi_category, ''],
            ['Analysis Timestamp', timestamp, '']
        ]
        
        metrics_table = Table(
            metrics_data,
            colWidths=[2.5*inch, 2.5*inch, 1.5*inch]
        )
        
        metrics_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Row styling
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#F1F5F9")),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.PRIMARY),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 1), (-1, -1), 10),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor("#F8FAFC")])
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.15 * inch))
        
        # Health advice
        health_advice = data.get('health_advice', 'No advice available')
        advice_text = f"<b>Health Advice:</b> {health_advice}"
        story.append(Paragraph(
            advice_text,
            self.styles['CustomBody']
        ))
        
        return story
    
    def _create_features_section(self, data):
        """Create atmospheric features section."""
        story = []
        
        story.append(Paragraph(
            "ATMOSPHERIC FEATURES",
            self.styles['SectionHeading']
        ))
        
        features = data.get('features', {})
        
        # Features table
        features_data = [
            ['Feature', 'Value', 'Level'],
            ['Haze Score', f"{features.get('haze_score', 0):.2f}", self._get_level(features.get('haze_score', 0))],
            ['Turbidity', f"{features.get('turbidity', 0):.2f}", self._get_level(features.get('turbidity', 0))],
            ['Visibility', f"{features.get('visibility', 0):.2f}", self._get_level(features.get('visibility', 0))],
            ['Contrast', f"{features.get('contrast', 0):.2f}", self._get_level(features.get('contrast', 0))],
            ['Brightness', f"{features.get('brightness', 0):.2f}", self._get_level(features.get('brightness', 0))],
            ['Saturation', f"{features.get('saturation', 0):.2f}", self._get_level(features.get('saturation', 0))],
        ]
        
        features_table = Table(
            features_data,
            colWidths=[2.2*inch, 2.2*inch, 2.1*inch]
        )
        
        features_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            
            # Rows
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#F1F5F9")),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.PRIMARY),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 1), (-1, -1), 8),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor("#F8FAFC")])
        ]))
        
        story.append(features_table)
        
        return story
    
    def _create_images_section(self, data, image_paths):
        """Create images/visualizations section."""
        story = []
        
        images_urls = data.get('images', {})
        
        # Add images if they exist
        for image_key, image_title in [
            ('original', 'Original Satellite Image'),
            ('heatmap', 'PM2.5 Spatial Distribution (Heatmap)'),
            ('before_after', 'Before & After Comparison'),
            ('dehazed', 'Dehazed Image'),
            ('features_chart', 'Feature Analysis Chart'),
        ]:
            if image_key in images_urls:
                story.append(PageBreak())
                story.append(Paragraph(
                    image_title.upper(),
                    self.styles['SectionHeading']
                ))
                
                try:
                    # Try to get image from static folder or use URL
                    image_url = images_urls[image_key]
                    
                    # Handle both web paths and file paths
                    if image_url.startswith('/'):
                        image_path = '.' + image_url  # Convert to relative path
                    else:
                        image_path = image_url
                    
                    # Check if file exists
                    if os.path.exists(image_path):
                        # Embed the image
                        img = RLImage(image_path, width=6*inch, height=4.5*inch)
                        story.append(img)
                        story.append(Spacer(1, 0.2 * inch))
                    
                except Exception as e:
                    # If image fails to load, add placeholder text
                    story.append(Paragraph(
                        f"<i>[Image: {image_title} - Unable to embed]</i>",
                        self.styles['CustomBody']
                    ))
        
        return story
    
    def _create_footer(self):
        """Create report footer."""
        story = []
        
        footer_text = """
        <b>PM2.5 Estimation System</b> | High-Resolution Satellite Image Analysis for Air Quality Assessment<br/>
        Final Year Engineering Project | 2026<br/>
        <br/>
        <font size=8><i>This report is generated automatically by the PM2.5 Analysis System.
        The values and estimates are based on image processing analysis and should be used as reference only.</i></font>
        """
        
        story.append(Paragraph(
            footer_text,
            ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=HexColor("#94A3B8"),
                alignment=TA_CENTER,
                spaceAfter=0
            )
        ))
        
        return story
    
    def _add_page_number(self, canvas, doc):
        """Add page numbers to PDF."""
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor("#94A3B8"))
        canvas.drawRightString(
            self.page_width - self.margin,
            self.margin / 2,
            text
        )
    
    def _get_level(self, value):
        """Convert numeric value to quality level."""
        if value < 25:
            return "Low"
        elif value < 50:
            return "Moderate"
        elif value < 75:
            return "High"
        else:
            return "Very High"


def generate_report_pdf(analysis_data, image_paths=None):
    """
    Convenience function to generate PDF report.
    
    Args:
        analysis_data (dict): Analysis results
        image_paths (dict): Optional image paths
        
    Returns:
        BytesIO: PDF file as bytes
    """
    generator = PM25ReportGenerator()
    return generator.generate_pdf(analysis_data, image_paths)
