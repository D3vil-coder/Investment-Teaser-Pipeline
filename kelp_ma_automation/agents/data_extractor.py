"""
Data Extractor Agent (Agent 2)
Extracts structured data from one-pager MD files using regex and pandas.
ZERO LLM usage - all extraction is deterministic.
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FinancialData:
    """Holds extracted financial metrics by year"""
    revenue: Dict[int, float] = field(default_factory=dict)
    ebitda: Dict[int, float] = field(default_factory=dict)
    pat: Dict[int, float] = field(default_factory=dict)
    pat_margin: Dict[int, float] = field(default_factory=dict)
    roce: Dict[int, float] = field(default_factory=dict)
    roe: Dict[int, float] = field(default_factory=dict)
    asset_turnover: Dict[int, float] = field(default_factory=dict)
    borrowings: Dict[int, float] = field(default_factory=dict)
    equity: Dict[int, float] = field(default_factory=dict)


@dataclass
class CompanyData:
    """Complete extracted company data structure"""
    name: str = ""
    business_description: str = ""
    website: str = ""
    domain: str = ""
    segment: str = ""
    products_services: List[str] = field(default_factory=list)
    industries_served: str = ""
    headquarters: str = ""
    founded: str = ""
    employees: str = ""
    shareholders: List[Dict[str, Any]] = field(default_factory=list)
    key_milestones: List[Dict[str, str]] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    awards: List[str] = field(default_factory=list)
    partners: List[str] = field(default_factory=list)
    clients: List[str] = field(default_factory=list)
    financials: FinancialData = field(default_factory=FinancialData)
    key_operational_indicators: List[str] = field(default_factory=list)
    swot: Dict[str, List[str]] = field(default_factory=dict)
    global_presence: List[str] = field(default_factory=list)
    future_plans: List[str] = field(default_factory=list)
    market_size: List[Dict[str, Any]] = field(default_factory=list)
    facilities: List[str] = field(default_factory=list)
    operational_metrics: Dict[str, str] = field(default_factory=dict)


class DataExtractor:
    """
    Extracts structured data from MD one-pager files.
    Uses regex and pandas - NO LLM calls.
    """
    
    def __init__(self):
        self.content = ""
        self.data = CompanyData()
    
    def extract(self, md_file_path: str) -> CompanyData:
        """
        Main extraction method - processes entire MD file.
        
        Args:
            md_file_path: Path to the one-pager MD file
            
        Returns:
            CompanyData object with all extracted information
        """
        with open(md_file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        self.data = CompanyData()
        
        # Extract all sections
        self._extract_basic_info()
        self._extract_business_description()
        self._extract_website()
        self._extract_products_services()
        self._extract_industries()
        self._extract_shareholders()
        self._extract_financials()
        self._extract_key_milestones()
        self._extract_certifications_awards()
        self._extract_operational_indicators()
        self._extract_swot()
        self._extract_global_presence()
        self._extract_future_plans()
        self._extract_market_size()
        self._extract_facilities()
        self._extract_partners_clients()
        
        logger.info(f"Extracted data for: {self.data.name or 'Unknown Company'}")
        return self.data
    
    def _extract_section(self, header: str, next_header_pattern: str = r'\n## ') -> str:
        """Extract text between a header and the next section header."""
        escaped_header = re.escape(header)
        pattern = f"{escaped_header}\n\n?(.*?)(?={next_header_pattern}|\\Z)"
        match = re.search(pattern, self.content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_basic_info(self):
        """Extract basic company info (name, domain, segment, etc.)"""
        # Extract from Details section
        details = self._extract_section("## Details")
        
        # Domain
        domain_match = re.search(r'Domain:\s*\*\*(.+?)\*\*', details)
        if domain_match:
            self.data.domain = domain_match.group(1).strip()
        
        # Segment
        segment_match = re.search(r'Segment:\s*\*\*(.+?)\*\*', details)
        if segment_match:
            self.data.segment = segment_match.group(1).strip()
        
        # Founded
        founded_match = re.search(r'Founded:\s*\*\*(.+?)\*\*', details)
        if founded_match:
            self.data.founded = founded_match.group(1).strip()
        
        # Headquarters
        hq_match = re.search(r'Headquarters:\s*\*\*(.+?)\*\*', details)
        if hq_match:
            self.data.headquarters = hq_match.group(1).strip()
        
        # Employees
        people_section = self._extract_section("## People")
        emp_match = re.search(r'Employees:\s*\*\*(.+?)\*\*', people_section)
        if emp_match:
            self.data.employees = emp_match.group(1).strip()
        
        # Try to extract company name from first heading
        title_match = re.search(r'^#\s*📄\s*Template:\s*(.+)$', self.content, re.MULTILINE)
        if not title_match:
            # Try extracting from filename or business description
            title_match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
        if title_match:
            # This might be template name, real name should come from elsewhere
            pass
    
    def _extract_business_description(self):
        """Extract the business description section."""
        self.data.business_description = self._extract_section("## Business Description")
    
    def _extract_website(self):
        """Extract company website URL."""
        website_section = self._extract_section("## Website")
        # Find URL in section
        url_match = re.search(r'https?://[^\s\)]+', website_section)
        if url_match:
            self.data.website = url_match.group(0).strip()
        else:
            # Try to find URL anywhere in the section
            self.data.website = website_section.strip()
    
    def _extract_products_services(self):
        """Extract products and services list."""
        section = self._extract_section("## Product & Services")
        if not section:
            section = self._extract_section("## Products & Services")
        
        # Parse bullet points
        products = []
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('- **'):
                # Extract the bold part as main product
                match = re.match(r'-\s*\*\*(.+?)\*\*', line)
                if match:
                    products.append(match.group(1).strip())
            elif line.startswith('-'):
                # Simple bullet point
                product = line.lstrip('- ').strip()
                if product:
                    products.append(product)
        
        self.data.products_services = products
    
    def _extract_industries(self):
        """Extract industries served."""
        self.data.industries_served = self._extract_section("## Application areas / Industries served")
    
    def _extract_shareholders(self):
        """Extract shareholder information from tables."""
        section = self._extract_section("## Shareholders")
        shareholders = []
        
        # Match table rows: | Name | Value | Type |
        table_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        for match in re.finditer(table_pattern, section):
            name, value, share_type = match.groups()
            name = name.strip()
            value = value.strip()
            share_type = share_type.strip()
            
            # Skip header rows
            if name.upper() == 'SHAREHOLDER NAME' or '---' in name:
                continue
            
            try:
                value_float = float(value)
                shareholders.append({
                    'name': name,
                    'value': value_float,
                    'type': share_type
                })
            except ValueError:
                continue
        
        self.data.shareholders = shareholders
    
    def _extract_financials(self):
        """Extract financial data from the Financials Status section."""
        section = self._extract_section("## Financials Status")
        
        financials = FinancialData()
        
        # Monetary metrics (in Lakhs, convert to Crores)
        monetary_patterns = {
            'revenue': r'Revenue From Operations \|(.+)',
            'ebitda': r'Operating EBITDA \|(.+)',
            'pat': r'- PAT \|(.+)',
            'borrowings': r'Borrowings \|(.+)',
        }
        
        # Percentage/ratio metrics (keep as-is)
        ratio_patterns = {
            'pat_margin': r'PAT Margin \|(.+)',
            'roce': r'RoCE \|(.+)',
            'roe': r'ROE \|(.+)',
            'asset_turnover': r'Asset Turnover \|(.+)',
        }
        
        # Parse monetary metrics (convert Lakhs to Cr)
        for metric_name, pattern in monetary_patterns.items():
            match = re.search(pattern, section)
            if match:
                data_str = match.group(1)
                parsed = self._parse_financial_row(data_str, convert_to_cr=True)
                setattr(financials, metric_name, parsed)
        
        # Parse ratio metrics (no conversion)
        for metric_name, pattern in ratio_patterns.items():
            match = re.search(pattern, section)
            if match:
                data_str = match.group(1)
                parsed = self._parse_financial_row(data_str, convert_to_cr=False)
                setattr(financials, metric_name, parsed)
        
        self.data.financials = financials
    
    def _parse_financial_row(self, row_data: str, convert_to_cr: bool = True) -> Dict[int, float]:
        """
        Parse financial row data.
        Format: 2014: 4251.81863 | 2015: 4879.97017 | ...
        
        Note: MD files store revenue/EBITDA in Lakhs, so we convert to Crores.
        Percentages (PAT Margin, RoCE, ROE) are kept as-is.
        """
        data = {}
        # Split by | and parse each entry
        entries = row_data.split('|')
        for entry in entries:
            entry = entry.strip()
            if ':' in entry:
                parts = entry.split(':', 1)
                if len(parts) == 2:
                    try:
                        year = int(parts[0].strip())
                        value_str = parts[1].strip()
                        if value_str.lower() != 'none' and value_str:
                            value = float(value_str)
                            # Convert Lakhs to Crores for monetary values
                            if convert_to_cr and value > 100:  # Likely in Lakhs
                                value = value / 100
                            data[year] = value
                    except (ValueError, TypeError):
                        continue
        return data
    
    def _extract_key_milestones(self):
        """Extract key milestones table."""
        section = self._extract_section("## Key Milestones")
        milestones = []
        
        # Match table rows: | DATE | MILESTONE |
        table_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        for match in re.finditer(table_pattern, section):
            date, milestone = match.groups()
            date = date.strip()
            milestone = milestone.strip()
            
            # Skip header rows
            if date.upper() == 'DATE' or '---' in date:
                continue
            
            if date and milestone:
                milestones.append({
                    'date': date,
                    'milestone': milestone
                })
        
        self.data.key_milestones = milestones
    
    def _extract_certifications_awards(self):
        """Extract certifications and awards."""
        section = self._extract_section("## Awards and Certifications")
        
        certs = []
        awards = []
        
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                item = line.lstrip('- ').strip()
                if item:
                    # Classify as cert or award based on keywords
                    if any(kw in item.upper() for kw in ['ISO', 'GMP', 'FSSC', 'ROHS', 'IPC', 'AS9100', 'IRIS', 'WHO']):
                        certs.append(item)
                    else:
                        awards.append(item)
        
        self.data.certifications = certs
        self.data.awards = awards
    
    def _extract_operational_indicators(self):
        """Extract key operational indicators."""
        section = self._extract_section("## Key Operational Indicators")
        
        indicators = []
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                # Extract the indicator text
                indicator = line.lstrip('* ').strip()
                # Remove markdown bold
                indicator = re.sub(r'\*\*(.+?)\*\*', r'\1', indicator)
                if indicator:
                    indicators.append(indicator)
        
        self.data.key_operational_indicators = indicators
        
        # Deep extraction for manufacturing/operational metrics
        op_metrics = {}
        # Parse numeric indicators like "Order Book: ₹850 Cr", "Capacity Utilization: 78%"
        for ind in indicators:
            # Common patterns: "Label: Value" or "Label - Value"
            match = re.search(r'(.+?)[:\-]\s*(.+)', ind)
            if match:
                key = match.group(1).lower().strip()
                val = match.group(2).strip()
                
                # Normalize keys for the KPI dashboard
                if 'order book' in key:
                    op_metrics['order_book'] = val
                elif 'utilization' in key:
                    op_metrics['capacity_utilization'] = val
                elif 'export' in key:
                    op_metrics['export_revenue'] = val
                elif 'sq ft' in key or 'area' in key or 'footprint' in key:
                    op_metrics['facilities_sqft'] = val
                elif 'cagr' in key:
                    op_metrics['cagr'] = val
        
        self.data.operational_metrics = op_metrics
    
    def _extract_swot(self):
        """Extract SWOT analysis."""
        section = self._extract_section("## SWOT")
        
        swot = {
            'strengths': [],
            'weaknesses': [],
            'opportunities': [],
            'threats': []
        }
        
        current_category = None
        
        for line in section.split('\n'):
            line = line.strip()
            
            if line.startswith('### Strengths'):
                current_category = 'strengths'
            elif line.startswith('### Weaknesses'):
                current_category = 'weaknesses'
            elif line.startswith('### Opportunities'):
                current_category = 'opportunities'
            elif line.startswith('### Threats'):
                current_category = 'threats'
            elif line.startswith('-') and current_category:
                item = line.lstrip('- ').strip()
                # Extract bold title if present
                match = re.match(r'(.+?):', item)
                if match:
                    item = match.group(1).strip()
                if item:
                    swot[current_category].append(item)
        
        self.data.swot = swot
    
    def _extract_global_presence(self):
        """Extract global presence info."""
        section = self._extract_section("## Global Presence")
        if section:
            # Split by comma or newline
            locations = [loc.strip() for loc in re.split(r'[,\n]', section) if loc.strip()]
            self.data.global_presence = locations
    
    def _extract_future_plans(self):
        """Extract future plans."""
        section = self._extract_section("## Future Plan")
        
        plans = []
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                plan = line.lstrip('- ').strip()
                if plan:
                    plans.append(plan)
        
        self.data.future_plans = plans
    
    def _extract_market_size(self):
        """Extract market size data from table."""
        section = self._extract_section("## Market Size")
        market_data = []
        
        # Match table rows with multiple columns
        # | SOURCE | MARKET | REGION | DATE | CURRENT MARKET SIZE | GROWTH (%) |
        lines = section.split('\n')
        for line in lines:
            if '|' in line and '---' not in line:
                parts = [p.strip() for p in line.split('|')]
                parts = [p for p in parts if p]  # Remove empty
                
                if len(parts) >= 5 and parts[0].upper() != 'SOURCE':
                    market_data.append({
                        'source': parts[0] if len(parts) > 0 else '',
                        'market': parts[1] if len(parts) > 1 else '',
                        'region': parts[2] if len(parts) > 2 else '',
                        'date': parts[3] if len(parts) > 3 else '',
                        'size': parts[4] if len(parts) > 4 else '',
                        'growth': parts[5] if len(parts) > 5 else ''
                    })
        
        self.data.market_size = market_data
    
    def _extract_facilities(self):
        """Extract facilities information."""
        section = self._extract_section("## Facilities")
        
        facilities = []
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                facility = line.lstrip('- ').strip()
                # Remove markdown bold/formatting
                facility = re.sub(r'\*\*(.+?)\*\*', r'\1', facility)
                if facility:
                    facilities.append(facility)
        
        self.data.facilities = facilities
    
    def _extract_partners_clients(self):
        """Extract partners and clients."""
        # Partners
        partners_section = self._extract_section("## Partners")
        if partners_section:
            self.data.partners = [p.strip() for p in partners_section.split('\n') if p.strip()]
        
        # Clients
        clients_section = self._extract_section("## Clients")
        if clients_section:
            self.data.clients = [c.strip() for c in clients_section.split('\n') if c.strip()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CompanyData to dictionary for JSON serialization."""
        return {
            'name': self.data.name,
            'business_description': self.data.business_description,
            'website': self.data.website,
            'domain': self.data.domain,
            'segment': self.data.segment,
            'products_services': self.data.products_services,
            'industries_served': self.data.industries_served,
            'headquarters': self.data.headquarters,
            'founded': self.data.founded,
            'employees': self.data.employees,
            'shareholders': self.data.shareholders,
            'key_milestones': self.data.key_milestones,
            'certifications': self.data.certifications,
            'awards': self.data.awards,
            'partners': self.data.partners,
            'clients': self.data.clients,
            'key_operational_indicators': self.data.key_operational_indicators,
            'swot': self.data.swot,
            'global_presence': self.data.global_presence,
            'future_plans': self.data.future_plans,
            'market_size': self.data.market_size,
            'facilities': self.data.facilities,
            'financials': {
                'revenue': self.data.financials.revenue,
                'ebitda': self.data.financials.ebitda,
                'pat': self.data.financials.pat,
                'pat_margin': self.data.financials.pat_margin,
                'roce': self.data.financials.roce,
                'roe': self.data.financials.roe,
                'asset_turnover': self.data.financials.asset_turnover,
                'borrowings': self.data.financials.borrowings,
            }
        }
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate extracted data for completeness.
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Critical fields
        if not self.data.business_description:
            issues.append("Missing business description")
        
        if not self.data.website:
            issues.append("Missing website URL")
        
        if not self.data.financials.revenue:
            issues.append("Missing revenue data")
        
        if not self.data.financials.ebitda:
            issues.append("Missing EBITDA data")
        
        # Warnings (not critical)
        if not self.data.products_services:
            issues.append("Warning: No products/services extracted")
        
        if not self.data.shareholders:
            issues.append("Warning: No shareholders extracted")
        
        is_valid = not any("Missing" in issue for issue in issues)
        return is_valid, issues


def get_latest_years_data(financial_dict: Dict[int, float], num_years: int = 5) -> Dict[int, float]:
    """Helper to get latest N years of financial data."""
    if not financial_dict:
        return {}
    sorted_years = sorted(financial_dict.keys(), reverse=True)[:num_years]
    return {year: financial_dict[year] for year in sorted(sorted_years)}


# Test function
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python data_extractor.py <path_to_md_file>")
        sys.exit(1)
    
    extractor = DataExtractor()
    data = extractor.extract(sys.argv[1])
    
    # Validate
    is_valid, issues = extractor.validate()
    print(f"\n=== Validation: {'PASSED' if is_valid else 'FAILED'} ===")
    for issue in issues:
        print(f"  - {issue}")
    
    # Print summary
    print(f"\n=== Extraction Summary ===")
    print(f"Website: {data.website}")
    print(f"Domain: {data.domain}")
    print(f"Products/Services: {len(data.products_services)} items")
    print(f"Shareholders: {len(data.shareholders)} entries")
    print(f"Milestones: {len(data.key_milestones)} entries")
    print(f"Certifications: {len(data.certifications)} items")
    print(f"Awards: {len(data.awards)} items")
    
    # Financial summary
    print(f"\n=== Financial Data ===")
    rev = data.financials.revenue
    if rev:
        latest_years = sorted(rev.keys())[-3:]
        print(f"Revenue (last 3 years):")
        for yr in latest_years:
            print(f"  FY{yr}: ₹{rev[yr]:.2f} Cr")
    
    ebitda = data.financials.ebitda
    if ebitda:
        latest_years = sorted(ebitda.keys())[-3:]
        print(f"EBITDA (last 3 years):")
        for yr in latest_years:
            print(f"  FY{yr}: ₹{ebitda[yr]:.2f} Cr")
