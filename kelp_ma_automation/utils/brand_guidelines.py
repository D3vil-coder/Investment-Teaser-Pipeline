"""
Brand Guidelines Utility
Constants and helpers for Kelp branding in PPT generation.
"""

from dataclasses import dataclass
from typing import Tuple
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor


@dataclass
class Color:
    """RGB Color with helper methods."""
    r: int
    g: int
    b: int
    
    @property
    def rgb(self) -> RGBColor:
        """Get pptx RGBColor."""
        return RGBColor(self.r, self.g, self.b)
    
    @property
    def hex(self) -> str:
        """Get hex color string."""
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"
    
    @property
    def tuple(self) -> Tuple[int, int, int]:
        """Get RGB tuple."""
        return (self.r, self.g, self.b)


class BrandGuidelines:
    """
    Kelp brand guidelines for PPT generation.
    Based on problem statement specifications.
    """
    
    # Colors
    PRIMARY = Color(75, 0, 130)       # Dark Indigo/Violet
    SECONDARY = Color(255, 20, 147)   # Pink
    ACCENT = Color(0, 206, 209)       # Cyan Blue
    TEXT_DARK = Color(50, 50, 50)     # Dark Grey
    TEXT_LIGHT = Color(255, 255, 255) # White
    BACKGROUND = Color(255, 255, 255) # Clean White
    
    # Additional colors for charts
    CHART_COLORS = [
        Color(75, 0, 130),    # Primary
        Color(255, 20, 147),  # Secondary
        Color(0, 206, 209),   # Accent
        Color(255, 140, 0),   # Orange
        Color(50, 205, 50),   # Green
    ]
    
    # Typography
    FONT_HEADING = "Arial"
    FONT_BODY = "Arial"
    HEADING_SIZE = Pt(26)
    HEADING_SIZE_SMALL = Pt(20)
    BODY_SIZE = Pt(12)
    BODY_SIZE_SMALL = Pt(10)
    FOOTER_SIZE = Pt(9)
    
    # Footer
    FOOTER_TEXT = "Strictly Private & Confidential – Prepared by Kelp M&A Team"
    
    # Logo
    LOGO_TEXT = "KELP"  # Use text placeholder if no image
    LOGO_SIZE = Pt(18)
    
    # Slide dimensions (standard 10" x 7.5")
    SLIDE_WIDTH = Inches(10)
    SLIDE_HEIGHT = Inches(7.5)
    
    # Margins
    MARGIN_LEFT = Inches(0.5)
    MARGIN_RIGHT = Inches(0.5)
    MARGIN_TOP = Inches(1.0)
    MARGIN_BOTTOM = Inches(0.5)
    
    # Content area
    CONTENT_WIDTH = Inches(9.0)
    CONTENT_HEIGHT = Inches(5.5)
    
    # Title bar
    TITLE_BAR_HEIGHT = Inches(0.8)
    
    @classmethod
    def get_chart_color(cls, index: int) -> RGBColor:
        """Get chart color by index (cycles through available colors)."""
        color = cls.CHART_COLORS[index % len(cls.CHART_COLORS)]
        return color.rgb
    
    @classmethod
    def position(cls, left: float, top: float, width: float, height: float):
        """Convert position tuple to Inches."""
        return (
            Inches(left),
            Inches(top),
            Inches(width),
            Inches(height)
        )


# Slide layout configurations by domain
SLIDE_LAYOUTS = {
    'manufacturing': {
        'slide_1': {
            'title': 'Business Profile & Infrastructure',
            'sections': [
                {'name': 'Product Portfolio', 'left': 0.5, 'top': 3.7, 'width': 2.8, 'height': 2.5},
                {'name': 'Manufacturing Footprint', 'left': 3.5, 'top': 3.7, 'width': 2.8, 'height': 2.5},
                {'name': 'Certifications & Compliance', 'left': 6.5, 'top': 3.7, 'width': 2.8, 'height': 2.5},
            ],
            'hero_image': {'left': 0.5, 'top': 1.0, 'width': 9.0, 'height': 2.5},
            'metrics_bar': {'left': 0.5, 'top': 6.7, 'width': 9.0, 'height': 0.3},
        },
        'slide_2': {
            'title': 'Financial & Operational Performance',
            'chart_1': {'left': 0.5, 'top': 1.2, 'width': 4.5, 'height': 3.5},
            'chart_2': {'left': 5.2, 'top': 1.2, 'width': 4.0, 'height': 3.5},
            'kpis': {'left': 0.5, 'top': 5.0, 'width': 9.0, 'height': 1.2},
        },
        'slide_3': {
            'title': 'Investment Highlights',
            'hooks': {'left': 1.0, 'top': 1.5, 'width': 8.0, 'height': 2.0},
            'moats': {'left': 0.5, 'top': 3.5, 'width': 4.0, 'height': 2.5},
            'drivers': {'left': 5.0, 'top': 3.5, 'width': 4.0, 'height': 2.5},
        },
    },
    'technology': {
        'slide_1': {
            'title': 'Technology Stack & Market Presence',
            'sections': [
                {'name': 'Service Offerings', 'left': 0.5, 'top': 3.7, 'width': 4.0, 'height': 2.5},
                {'name': 'Industry Verticals', 'left': 5.0, 'top': 3.7, 'width': 4.0, 'height': 2.5},
            ],
            'hero_image': {'left': 0.5, 'top': 1.0, 'width': 9.0, 'height': 2.5},
        },
        'slide_2': {
            'title': 'Growth & Unit Economics',
            'chart_1': {'left': 0.5, 'top': 1.2, 'width': 4.5, 'height': 3.0},
            'chart_2': {'left': 5.2, 'top': 1.2, 'width': 4.0, 'height': 3.0},
            'kpis': {'left': 0.5, 'top': 4.5, 'width': 9.0, 'height': 1.5},
        },
        'slide_3': {
            'title': 'Investment Highlights',
            'hooks': {'left': 1.0, 'top': 1.5, 'width': 8.0, 'height': 2.0},
            'sections': [
                {'name': 'Scalability Thesis', 'left': 0.5, 'top': 3.5, 'width': 4.0, 'height': 2.5},
                {'name': 'Competitive Positioning', 'left': 5.0, 'top': 3.5, 'width': 4.0, 'height': 2.5},
            ],
        },
    },
    # Add more domains as needed (logistics, consumer, healthcare, etc.)
}


# Test
if __name__ == "__main__":
    print("=== Kelp Brand Guidelines ===")
    print(f"Primary Color: {BrandGuidelines.PRIMARY.hex}")
    print(f"Secondary Color: {BrandGuidelines.SECONDARY.hex}")
    print(f"Accent Color: {BrandGuidelines.ACCENT.hex}")
    print(f"Heading Font: {BrandGuidelines.FONT_HEADING}")
    print(f"Footer: {BrandGuidelines.FOOTER_TEXT}")
    print(f"Slide Size: {BrandGuidelines.SLIDE_WIDTH} x {BrandGuidelines.SLIDE_HEIGHT}")
