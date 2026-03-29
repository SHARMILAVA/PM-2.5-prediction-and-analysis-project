"""
PDF Report Generator for PM2.5 Analysis Results

This module generates professional PDF reports containing:
- Analysis results and PM2.5 estimation
- AQI category and health advice
- Atmospheric features
- Visualizations and heatmaps
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image as RLImage
)
from io import BytesIO
from datetime import datetime
import os


class PM25ReportGenerator:
    """Generate professional PDF reports for PM2.5 analysis results."""
    
    # Color palette
    PRIMARY = HexColor("#1E3A8A")
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
            fontSize=24,
            textColor=self.PRIMARY,
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.SECONDARY,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.PRIMARY,
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            backColor=HexColor("#EFF6FF"),
            borderColor=HexColor("#DBEAFE"),
            borderWidth=1,
            borderPadding=6,
            borderRadius=3
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=9.5,
            textColor=HexColor("#475569"),
            spaceAfter=5,
            leading=13,
            alignment=TA_LEFT
        ))

        styles.add(ParagraphStyle(
            name='ImageCaption',
            parent=styles['BodyText'],
            fontSize=8.5,
            textColor=HexColor("#64748B"),
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=6
        ))

        styles.add(ParagraphStyle(
            name='KpiLabel',
            parent=styles['Normal'],
            fontSize=8.5,
            textColor=HexColor("#64748B"),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='KpiValue',
            parent=styles['Normal'],
            fontSize=16,
            textColor=self.PRIMARY,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
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

        # Cover page
        story.extend(self._create_cover_page(analysis_data))
        story.append(PageBreak())
        
        # Header section
        story.extend(self._create_header())
        story.append(Spacer(1, 0.2 * inch))
        story.extend(self._section_divider())
        
        # Summary section
        story.extend(self._create_summary_section(analysis_data))
        story.append(Spacer(1, 0.2 * inch))
        story.extend(self._section_divider())
        
        # Features section
        story.extend(self._create_features_section(analysis_data))
        story.append(Spacer(1, 0.2 * inch))
        
        # Images section
        story.extend(self._create_images_section(analysis_data, image_paths))
        
        # Footer section
        story.extend(self._section_divider())
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
        info_text = f"<b>Report Generated:</b> {report_date}  |  <b>Version:</b> 1.0"
        story.append(Paragraph(
            info_text,
            self.styles['CustomBody']
        ))
        
        return story

    def _create_cover_page(self, data):
        """Create an official-style cover page with compact KPI tiles."""
        story = []

        story.append(Spacer(1, 0.6 * inch))
        story.append(Paragraph("PM2.5 ESTIMATION SYSTEM", self.styles['CustomTitle']))
        story.append(Paragraph("Official Analysis Report", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.15 * inch))

        report_date = datetime.now().strftime("%d %b %Y, %H:%M")
        cover_note = (
            "This document presents PM2.5 estimation, atmospheric indicators, "
            "health suggestions, and visualization outputs generated from the uploaded satellite imagery."
        )
        story.append(Paragraph(f"<b>Generated On:</b> {report_date}", self.styles['CustomBody']))
        story.append(Paragraph(cover_note, self.styles['CustomBody']))
        story.append(Spacer(1, 0.18 * inch))

        pm25_value = data.get('pm25', 0)
        confidence = data.get('confidence', 0)
        aqi_category = data.get('aqi_category', 'Unknown')
        timestamp = data.get('timestamp', 'N/A')

        kpi_cells = [
            [
                Paragraph("PM2.5", self.styles['KpiLabel']),
                Paragraph("AQI Category", self.styles['KpiLabel'])
            ],
            [
                Paragraph(f"{pm25_value:.1f} ug/m3", self.styles['KpiValue']),
                Paragraph(aqi_category, self.styles['KpiValue'])
            ],
            [
                Paragraph("Confidence", self.styles['KpiLabel']),
                Paragraph("Analysis Time", self.styles['KpiLabel'])
            ],
            [
                Paragraph(f"{confidence:.0f}%", self.styles['KpiValue']),
                Paragraph(timestamp, self.styles['Label'])
            ]
        ]

        kpi_table = Table(kpi_cells, colWidths=[3.25 * inch, 3.25 * inch], hAlign='CENTER')
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [HexColor("#EFF6FF"), colors.white, HexColor("#EFF6FF"), colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, HexColor("#DBEAFE")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(kpi_table)

        story.append(Spacer(1, 0.2 * inch))
        story.extend(self._create_document_control(report_date, timestamp))

        story.append(Spacer(1, 0.28 * inch))
        story.append(Paragraph(
            "Prepared for academic and decision-support reference. Values are image-derived estimates.",
            self.styles['ImageCaption']
        ))
        return story

    def _create_document_control(self, report_date, analysis_time):
        """Create formal document control table."""
        report_id = f"PM25-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        control_data = [
            ['Document Control', ''],
            ['Report ID', report_id],
            ['Version', '1.0'],
            ['Prepared By', 'PM2.5 Estimation System'],
            ['Generated On', report_date],
            ['Analysis Timestamp', analysis_time]
        ]

        control_table = Table(control_data, colWidths=[2.2 * inch, 4.3 * inch], hAlign='CENTER')
        control_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), HexColor('#E8F0FF')),
            ('TEXTCOLOR', (0, 0), (1, 0), self.PRIMARY),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 10),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('BACKGROUND', (0, 1), (0, -1), HexColor('#F8FAFC')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#334155')),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#DBEAFE'))
        ]))

        return [control_table]

    def _section_divider(self):
        """Create subtle section divider for visual hierarchy."""
        divider = Table([['']], colWidths=[self.page_width - (2 * self.margin)])
        divider.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 0.8, HexColor("#DBEAFE")),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2)
        ]))
        return [divider, Spacer(1, 0.1 * inch)]
    
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
            colWidths=[2.6*inch, 2.2*inch, 1.2*inch],
            hAlign='LEFT'
        )
        
        metrics_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Row styling
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#F1F5F9")),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.PRIMARY),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
            
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
            colWidths=[2.4*inch, 1.8*inch, 1.8*inch],
            hAlign='LEFT'
        )
        
        features_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Rows
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#F1F5F9")),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.PRIMARY),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor("#F8FAFC")])
        ]))
        
        story.append(features_table)
        
        return story
    
    def _resolve_image_path(self, image_url):
        """Resolve static web path to local file path."""
        if not image_url:
            return None
        if image_url.startswith('/'):
            path = '.' + image_url
        else:
            path = image_url
        if os.path.exists(path):
            return path
        return None

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
                    image_url = images_urls[image_key]
                    image_path = self._resolve_image_path(image_url)

                    if image_path:
                        reader = ImageReader(image_path)
                        width_px, height_px = reader.getSize()
                        max_width = self.page_width - (2 * self.margin)
                        max_height = 5.9 * inch

                        width_ratio = max_width / float(width_px)
                        height_ratio = max_height / float(height_px)
                        scale = min(width_ratio, height_ratio)

                        img = RLImage(
                            image_path,
                            width=width_px * scale,
                            height=height_px * scale
                        )
                        img.hAlign = 'CENTER'
                        story.append(img)
                        story.append(Paragraph(
                            f"Visualization: {image_title}",
                            self.styles['ImageCaption']
                        ))

                except Exception as e:
                    story.append(Paragraph(
                        f"<i>[Image: {image_title} - Unable to embed]</i>",
                        self.styles['CustomBody']
                    ))
        
        return story
    
    def _create_footer(self):
        """Create report footer."""
        story = []
        
        footer_text = """
        <b>PM2.5 Estimation System</b> | High-Resolution Satellite Image Analysis Report<br/>
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
