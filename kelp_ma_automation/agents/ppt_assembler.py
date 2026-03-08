"""
PPT Assembler Agent (Agent 7) - PRODUCTION VERSION
Fixed grid layout. No overflow. Properly sized metrics bar.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import ChartData

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.brand_guidelines import BrandGuidelines

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Fixed layout grid (all positions in inches)
# Slide is 10" x 7.5" (standard widescreen)
LAYOUT = {
    'slide_width': 10.0,
    'slide_height': 7.5,
    'margin_left': 0.4,
    'margin_right': 0.4,
    'margin_top': 0.3,
    'margin_bottom': 0.5,  # Increased for footer
    'content_width': 9.2,
    'title_height': 0.5,
    'footer_height': 0.25,
    
    # Grid rows
    'title_top': 0.2,
    'content_start': 0.85,
    'footer_top': 7.15,
    
    # Metrics bar - above footer, controlled height
    'metrics_bar_top': 6.6,
    'metrics_bar_height': 0.35,
    
    # Column widths for 2-column layout
    'col2_width': 4.4,
    'col2_gap': 0.4,
    
    # Column widths for 3-column layout
    'col3_width': 2.9,
    'col3_gap': 0.25,
}


class PPTAssembler:
    """
    PPT Assembler with fixed grid-based layout.
    No overflow - everything fits within bounds.
    """
    
    def __init__(self, domain: str = "manufacturing", 
                 template_path: Optional[str] = None):
        self.domain = domain
        self.template_path = template_path
        self.brand = BrandGuidelines
        self.prs = None
    
    def build(self, slide_content: List[Any], financials: Dict[str, Any],
              output_path: str, images: Dict[str, str] = None) -> str:
        """Build PPT with fixed layout."""
        # Create new presentation
        self.prs = Presentation()
        self.prs.slide_width = Inches(LAYOUT['slide_width'])
        self.prs.slide_height = Inches(LAYOUT['slide_height'])
        
        # Build slides
        if len(slide_content) >= 1:
            self._build_slide_1(slide_content[0])
        
        if len(slide_content) >= 2:
            self._build_slide_2(slide_content[1], financials)
        
        if len(slide_content) >= 3:
            self._build_slide_3(slide_content[2])
        
        # Save
        self.prs.save(output_path)
        logger.info(f"Presentation saved: {output_path}")
        
        return output_path
    
    def _build_slide_1(self, content: Any):
        """Slide 1: Business Profile - Left half text, Right half image."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        
        # Title
        self._add_title(slide, content.title if content else "Business Profile")
        
        sections = content.sections if content else {}
        
        # LEFT HALF: Two sections stacked
        left_width = 4.5  # inches
        
        # Section 1: Company Overview (top-left)
        overview = sections.get('Company Overview', [])
        if overview:
            self._add_text_box(
                slide, overview[0],
                left=LAYOUT['margin_left'],
                top=LAYOUT['content_start'] - 0.2,  # Move UP (1.0)
                width=left_width,
                height=1.5,
                font_size=10,
                is_paragraph=True
            )
        
        # Section 2: Products & Services (bottom-left)  
        products = sections.get('Products & Services', [])
        if products:
            self._add_section_box(
                slide, "Products & Services", products,
                left=LAYOUT['margin_left'],
                top=LAYOUT['content_start'] + 1.4,  # Move UP tighter
                width=left_width,
                height=2.5,
                max_items=6,
                font_size=9
            )
        
        # Section 3: Industries Served (below products)
        industries = sections.get('Industries Served', [])
        if industries:
            self._add_section_box(
                slide, "Industries Served", industries,
                left=LAYOUT['margin_left'],
                top=LAYOUT['content_start'] + 4.0,  # Move UP tighter
                width=left_width,
                height=1.5,
                max_items=4,
                font_size=9
            )
        
        # RIGHT HALF: Image (3:2 ratio, 576x384 pixels = 6x4 inches at 96dpi)
        try:
            from pathlib import Path
            from agents.image_pipeline import ImagePipeline
            
            img_pipeline = ImagePipeline()
            img_path = img_pipeline.find_image(self.domain, slide_num=1)
            
            if not img_path:
                fallback = Path("images/fallback.png")
                if fallback.exists():
                    img_path = str(fallback)
            
            if img_path:
                # Place image on right half: 384x256 pixels = 4x2.67 inch box (3:2 ratio)
                # Position: right side, vertically centered
                img_pipeline.add_image_to_slide_pixels(
                    slide, img_path,
                    left_inches=5.5, top_inches=2.0,
                    width_pixels=384, height_pixels=256
                )
        except Exception as e:
            import logging
            logging.warning(f"Could not add image: {e}")
        
        # Bottom: Key Highlights + Certifications in metrics bar style
        highlights = sections.get('Key Highlights', [])
        certs = sections.get('Certifications', [])
        
        # Metrics bar at bottom
        if content and content.metrics:
            self._add_metrics_bar(slide, content.metrics)
        
        # Footer
        self._add_footer(slide)
    
    def _build_slide_2(self, content: Any, financials: Dict[str, Any]):
        """Slide 2: Financials - Charts + KPIs."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        
        # Title
        self._add_title(slide, content.title if content else "Financial Performance")
        
        sections = content.sections if content else {}
        
        # ROW 1: Charts (Revenue left, EBITDA right)
        chart_top = LAYOUT['content_start']
        chart_height = 2.5
        
        revenue = financials.get('revenue', {})
        ebitda = financials.get('ebitda', {})
        
        if revenue:
            self._add_column_chart(
                slide, "Revenue (₹ Cr)", revenue,
                left=LAYOUT['margin_left'],
                top=chart_top,
                width=LAYOUT['col2_width'],
                height=chart_height
            )
        
        if ebitda:
            self._add_column_chart(
                slide, "EBITDA (₹ Cr)", ebitda,
                left=LAYOUT['margin_left'] + LAYOUT['col2_width'] + LAYOUT['col2_gap'],
                top=chart_top,
                width=LAYOUT['col2_width'],
                height=chart_height
            )
        
        # ROW 2: KPIs (left) + Shareholders (right)
        row2_top = chart_top + chart_height + 0.2
        
        kpis = sections.get('Financial KPIs', [])
        if kpis:
            self._add_section_box(
                slide, "Financial KPIs", kpis,
                left=LAYOUT['margin_left'],
                top=row2_top,
                width=LAYOUT['col2_width'],
                height=1.8,
                max_items=5,
                font_size=10
            )
        
        shareholders = sections.get('Key Shareholders', [])
        if shareholders:
            self._add_shareholder_pie_chart(
                slide, shareholders,
                left=LAYOUT['margin_left'] + LAYOUT['col2_width'] + LAYOUT['col2_gap'],
                top=row2_top,
                width=LAYOUT['col2_width'],
                height=1.8
            )
        
        # ROW 3: Market Position
        market = sections.get('Market Position', [])
        if market:
            row3_top = row2_top + 2.0
            self._add_section_box(
                slide, "Market Position", market,
                left=LAYOUT['margin_left'],
                top=row3_top,
                width=LAYOUT['content_width'],
                height=0.7,
                max_items=2,
                font_size=10
            )
        
        # Footer
        self._add_footer(slide)
    
    def _build_slide_3(self, content: Any):
        """Slide 3: Investment Highlights."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        
        # Title
        self._add_title(slide, "Investment Highlights")
        
        sections = content.sections if content else {}
        
        # ROW 1: Investment Hooks (full width, boxes)
        if content and content.hooks:
            self._add_hook_boxes(slide, content.hooks)
        
        # ROW 2: Strengths (left) + Opportunities (right)
        row2_top = LAYOUT['content_start'] + 1.3
        
        strengths = sections.get('Key Strengths', [])
        if strengths:
            self._add_section_box(
                slide, "Key Strengths", strengths,
                left=LAYOUT['margin_left'],
                top=row2_top,
                width=LAYOUT['col2_width'],
                height=2.0,
                max_items=5,
                font_size=9
            )
        
        opportunities = sections.get('Growth Opportunities', [])
        if opportunities:
            self._add_section_box(
                slide, "Growth Opportunities", opportunities,
                left=LAYOUT['margin_left'] + LAYOUT['col2_width'] + LAYOUT['col2_gap'],
                top=row2_top,
                width=LAYOUT['col2_width'],
                height=2.0,
                max_items=5,
                font_size=9
            )
        
        # ROW 3: Milestones (left) + Market Opportunity (right)
        row3_top = row2_top + 2.1
        
        milestones = sections.get('Recent Milestones', [])
        if milestones:
            self._add_section_box(
                slide, "Recent Milestones", milestones,
                left=LAYOUT['margin_left'],
                top=row3_top,
                width=LAYOUT['col2_width'],
                height=1.6,
                max_items=5,
                font_size=9
            )
        
        market_opp = sections.get('Market Opportunity', [])
        if market_opp:
            self._add_section_box(
                slide, "Market Opportunity", market_opp,
                left=LAYOUT['margin_left'] + LAYOUT['col2_width'] + LAYOUT['col2_gap'],
                top=row3_top,
                width=LAYOUT['col2_width'],
                height=1.6,
                max_items=2,
                font_size=9
            )
        
        # Footer
        self._add_footer(slide)
    
    def _add_title(self, slide, text: str):
        """Add slide title - Arial Bold 26pt."""
        shape = slide.shapes.add_textbox(
            Inches(LAYOUT['margin_left']),
            Inches(LAYOUT['title_top']),
            Inches(LAYOUT['content_width'] - 1.5),
            Inches(LAYOUT['title_height'])
        )
        tf = shape.text_frame
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.name = self.brand.FONT_HEADING
        p.font.color.rgb = self.brand.PRIMARY.rgb
        
        # Logo
        logo = slide.shapes.add_textbox(
            Inches(LAYOUT['slide_width'] - 1.3),
            Inches(LAYOUT['title_top']),
            Inches(1.0),
            Inches(0.4)
        )
        logo_tf = logo.text_frame
        logo_tf.paragraphs[0].text = "KELP"
        logo_tf.paragraphs[0].font.size = Pt(14)
        logo_tf.paragraphs[0].font.bold = True
        logo_tf.paragraphs[0].font.color.rgb = self.brand.PRIMARY.rgb
        logo_tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
    
    def _add_section_box(self, slide, title: str, items: List[str],
                          left: float, top: float, width: float, height: float,
                          max_items: int = 6, font_size: int = 11):
        """Add a section with title and bullet points."""
        shape = slide.shapes.add_textbox(
            Inches(left), Inches(top), Inches(width), Inches(height)
        )
        
        # Light background
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(248, 249, 252)
        
        tf = shape.text_frame
        tf.word_wrap = True
        
        # Section Title - Arial Bold 14pt
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.name = self.brand.FONT_HEADING
        p.font.color.rgb = self.brand.PRIMARY.rgb
        p.space_after = Pt(4)
        
        # Items - word-wrap-aware, generous char limit
        for item in items[:max_items]:
            p = tf.add_paragraph()
            display_text = item
            # Use generous limit: ~18 chars per inch at 11pt with word wrap
            max_chars = int(width * 18)
            if len(display_text) > max_chars:
                # Truncate at sentence/phrase boundary
                words = display_text.split()
                display_text = ""
                for word in words:
                    if len(display_text) + len(word) + 1 > max_chars:
                        break
                    display_text = display_text + " " + word if display_text else word
                # Ensure we don't end mid-phrase with dangling prepositions
                if display_text and display_text.split()[-1].lower() in ('to', 'for', 'in', 'of', 'and', 'the', 'a', 'an', 'with', 'by'):
                    display_text = ' '.join(display_text.split()[:-1])
            
            p.text = f"• {display_text}"
            p.font.size = Pt(font_size)
            p.font.name = self.brand.FONT_BODY
            p.font.color.rgb = self.brand.TEXT_DARK.rgb
            p.space_before = Pt(2)
    
    def _add_text_box(self, slide, text: str, left: float, top: float,
                       width: float, height: float, font_size: int = 12,
                       is_paragraph: bool = False):
        """Add a simple text box - Arial Regular 12pt default."""
        shape = slide.shapes.add_textbox(
            Inches(left), Inches(top), Inches(width), Inches(height)
        )
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.name = self.brand.FONT_BODY
        p.font.color.rgb = self.brand.TEXT_DARK.rgb
    
    def _add_hook_boxes(self, slide, hooks: List[str]):
        """Add investment hook callout boxes."""
        n = min(4, len(hooks))
        if n == 0:
            return
        
        box_width = (LAYOUT['content_width'] - (n - 1) * 0.15) / n
        top = LAYOUT['content_start']
        
        for i, hook in enumerate(hooks[:n]):
            left = LAYOUT['margin_left'] + i * (box_width + 0.15)
            
            shape = slide.shapes.add_textbox(
                Inches(left), Inches(top), Inches(box_width), Inches(0.9)
            )
            
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.brand.PRIMARY.rgb
            
            tf = shape.text_frame
            tf.word_wrap = True
            tf.paragraphs[0].text = hook
            tf.paragraphs[0].font.size = Pt(11)
            tf.paragraphs[0].font.bold = True
            tf.paragraphs[0].font.name = self.brand.FONT_BODY
            tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            tf.anchor = MSO_ANCHOR.MIDDLE
    
    def _add_metrics_bar(self, slide, metrics: Dict[str, str]):
        """Add metrics bar - FIXED SIZE, SHORT VALUES ONLY."""
        n = min(3, len(metrics))  # Max 3 metrics to prevent overflow
        if n == 0:
            return
        
        bar_top = LAYOUT['metrics_bar_top']
        bar_width = (LAYOUT['content_width'] - (n - 1) * 0.15) / n
        bar_height = LAYOUT['metrics_bar_height']
        
        for i, (name, value) in enumerate(list(metrics.items())[:n]):
            left = LAYOUT['margin_left'] + i * (bar_width + 0.15)
            
            # Ensure value is short
            display_value = str(value)[:15]  # Max 15 chars
            display_text = f"{name}: {display_value}"
            
            shape = slide.shapes.add_textbox(
                Inches(left), Inches(bar_top),
                Inches(bar_width), Inches(bar_height)
            )
            
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.brand.ACCENT.rgb
            
            tf = shape.text_frame
            tf.paragraphs[0].text = display_text
            tf.paragraphs[0].font.size = Pt(10)
            tf.paragraphs[0].font.bold = True
            tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            tf.anchor = MSO_ANCHOR.MIDDLE
    
    def _add_column_chart(self, slide, title: str, data: Dict[int, float],
                           left: float, top: float, width: float, height: float):
        """Add a native PPT column chart with data table, axis labels, source footnote."""
        sorted_years = sorted(data.keys())
        chart_data = ChartData()
        chart_data.categories = [f"FY{str(y)[-2:]}" for y in sorted_years]
        chart_data.add_series('', [data[y] for y in sorted_years])
        
        chart_frame = slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            Inches(left), Inches(top),
            Inches(width), Inches(height),
            chart_data
        )
        chart = chart_frame.chart
        
        # Style
        chart.has_legend = False
        chart.has_title = True
        chart.chart_title.text_frame.paragraphs[0].text = title
        chart.chart_title.text_frame.paragraphs[0].font.size = Pt(12)
        chart.chart_title.text_frame.paragraphs[0].font.bold = True
        chart.chart_title.text_frame.paragraphs[0].font.name = self.brand.FONT_HEADING
        chart.chart_title.text_frame.paragraphs[0].font.color.rgb = self.brand.PRIMARY.rgb
        
        # Enable data table below chart (python-pptx sets the flag; no direct styling API)
        chart.has_data_table = True
        
        # Axis labels
        try:
            value_axis = chart.value_axis
            value_axis.has_title = True
            value_axis.axis_title.text_frame.paragraphs[0].text = "₹ Crores"
            value_axis.axis_title.text_frame.paragraphs[0].font.size = Pt(9)
            value_axis.axis_title.text_frame.paragraphs[0].font.name = self.brand.FONT_BODY
            value_axis.tick_labels.font.size = Pt(8)
            value_axis.tick_labels.font.name = self.brand.FONT_BODY
            
            category_axis = chart.category_axis
            category_axis.has_title = True
            category_axis.axis_title.text_frame.paragraphs[0].text = "Financial Year"
            category_axis.axis_title.text_frame.paragraphs[0].font.size = Pt(9)
            category_axis.axis_title.text_frame.paragraphs[0].font.name = self.brand.FONT_BODY
            category_axis.tick_labels.font.size = Pt(8)
            category_axis.tick_labels.font.name = self.brand.FONT_BODY
        except Exception:
            pass  # Axis configuration may fail on some chart types
        
        # Color bars
        series = chart.series[0]
        for point in series.points:
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = self.brand.PRIMARY.rgb
        
        # Source footnote below chart
        fy_start = f"FY{str(sorted_years[0])[-2:]}" if sorted_years else ""
        fy_end = f"FY{str(sorted_years[-1])[-2:]}" if sorted_years else ""
        footnote_text = f"Source: Company Financials {fy_start}-{fy_end}"
        footnote = slide.shapes.add_textbox(
            Inches(left), Inches(top + height + 0.02),
            Inches(width), Inches(0.2)
        )
        fn_tf = footnote.text_frame
        fn_tf.paragraphs[0].text = footnote_text
        fn_tf.paragraphs[0].font.size = Pt(7)
        fn_tf.paragraphs[0].font.italic = True
        fn_tf.paragraphs[0].font.name = self.brand.FONT_BODY
        fn_tf.paragraphs[0].font.color.rgb = RGBColor(128, 128, 128)
    
    def _add_pie_chart(self, slide, title: str, data: Dict[str, float],
                        left: float, top: float, width: float, height: float):
        """Add a native PPT pie chart for shareholders."""
        if not data:
            return
        
        chart_data = ChartData()
        chart_data.categories = list(data.keys())[:5]  # Max 5 slices
        chart_data.add_series('', [data[k] for k in list(data.keys())[:5]])
        
        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.PIE,
            Inches(left), Inches(top),
            Inches(width), Inches(height),
            chart_data
        ).chart
        
        chart.has_legend = False
        chart.has_title = True
        chart.chart_title.text_frame.paragraphs[0].text = title
        chart.chart_title.text_frame.paragraphs[0].font.size = Pt(10)
        chart.chart_title.text_frame.paragraphs[0].font.bold = True
        chart.chart_title.text_frame.paragraphs[0].font.color.rgb = self.brand.PRIMARY.rgb
        
        # Color slices
        colors = [
            self.brand.PRIMARY.rgb,
            self.brand.SECONDARY.rgb,
            self.brand.ACCENT.rgb,
            RGBColor(100, 149, 237),  # Cornflower blue
            RGBColor(147, 112, 219),  # Medium purple
        ]
        
        series = chart.series[0]
        # Show data labels with percentages and category names
        series.has_data_labels = True
        data_labels = series.data_labels
        data_labels.show_category_name = True
        data_labels.show_percentage = True
        data_labels.show_value = False
        data_labels.font.size = Pt(9)
        data_labels.font.bold = True
        
        for i, point in enumerate(series.points):
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = colors[i % len(colors)]
    

    def _add_shareholder_pie_chart(self, slide, shareholders: List[str],
                                    left: float, top: float, width: float, height: float):
        """Parse shareholder list and create pie chart."""
        import re as regex_module
        parsed_data = {}
        
        for item in shareholders[:5]:  # Max 5 slices
            match = regex_module.search(r'(.+?)[\:\-\(]\s*(\d+\.?\d*)%', item)
            if match:
                name = match.group(1).strip()
                pct = float(match.group(2))
                parsed_data[name] = pct
            else:
                parsed_data[item[:30]] = 100.0 / len(shareholders)
        
        if parsed_data:
            self._add_pie_chart(slide, "Key Shareholders", parsed_data, left, top, width, height)

    def _add_footer(self, slide):
        """Add footer - Arial Regular 9pt."""
        footer = slide.shapes.add_textbox(
            Inches(0), Inches(LAYOUT['footer_top']),
            Inches(LAYOUT['slide_width']), Inches(LAYOUT['footer_height'])
        )
        tf = footer.text_frame
        tf.paragraphs[0].text = "Strictly Private & Confidential – Kelp Strategic Partners"
        tf.paragraphs[0].font.size = Pt(9)
        tf.paragraphs[0].font.name = self.brand.FONT_BODY
        tf.paragraphs[0].font.color.rgb = RGBColor(128, 128, 128)
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER


if __name__ == "__main__":
    print("PPT Assembler ready - no overflow")
