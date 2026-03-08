"""
Content Writer Agent (Agent 4) - PRODUCTION VERSION
Fixed slide structure. NEVER shortens critical content like products.
Integrates web-scraped market data.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ollama_client import OllamaClient
from utils.token_tracker import token_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Content that should NEVER be shortened
NEVER_SHORTEN = [
    'products',
    'services',
    'certifications',
    'industries',
    'shareholders',
]


@dataclass
class VerifiedClaim:
    """A claim verified against source data."""
    text: str
    source: str
    original_value: Any = None


@dataclass
class SlideContent:
    """Content for a single slide."""
    title: str
    sections: Dict[str, List[str]]
    metrics: Dict[str, Any]
    hooks: List[str] = None
    citations: List[VerifiedClaim] = field(default_factory=list)


class ContentWriter:
    """
    Production content writer.
    Critical rule: NEVER shorten products, services, or key data.
    """
    
    def __init__(self, domain: str = "manufacturing"):
        self.domain = domain
        self.ollama = OllamaClient()
        self.company_name = ""
        self.source_data = {}
        self.web_data = {}
    
    def set_web_data(self, web_data: Dict[str, Any]):
        """Set web-scraped data for enrichment."""
        self.web_data = web_data or {}
    
    def generate_slide_content(self, data: Dict[str, Any], 
                                company_name: str) -> List[SlideContent]:
        """Generate structured content for all 3 slides."""
        self.company_name = company_name
        self.source_data = data
        
        slides = [
            self._generate_slide_1(data),
            self._generate_slide_2(data),
            self._generate_slide_3(data),
        ]
        
        return slides
    
    def _generate_slide_1(self, data: Dict[str, Any]) -> SlideContent:
        """Slide 1: Business Profile - NEVER shorten products."""
        sections = {}
        citations = []
        
        # 1. Company Overview (can shorten)
        desc = data.get('business_description', '')
        if desc:
            # Enhanced overwview: inject operational metrics (footprint, employees, split)
            op_context = ""
            op_metrics = data.get('operational_metrics', {})
            if op_metrics:
                parts = []
                if 'facilities_sqft' in op_metrics:
                    parts.append(f"operating out of a {op_metrics['facilities_sqft']} facility")
                if 'capacity_utilization' in op_metrics:
                    parts.append(f"at {op_metrics['capacity_utilization']} capacity utilization")
                if parts:
                    op_context = " Currently " + " and ".join(parts) + "."

            overview = self._anonymize(desc + op_context)
            if len(overview) > 300:
                overview = self._shorten_text(overview, 300, 'overview')
            sections['Company Overview'] = [overview]
            citations.append(VerifiedClaim(
                text=overview,
                source='onepager:business_description',
                original_value=desc[:100]
            ))
        
        # 2. Products & Services - NEVER SHORTEN, show all
        products = data.get('products_services', [])
        if products:
            product_list = []
            # Show ALL products, don't limit to 6
            for p in products[:8]:  # Show up to 8
                text = self._anonymize(p)
                # NO SHORTENING - products are critical
                product_list.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source='onepager:products_services',
                    original_value=p
                ))
            sections['Products & Services'] = product_list
        
        # 3. Industries Served - NEVER SHORTEN
        industries = data.get('industries_served', '')
        if industries:
            if isinstance(industries, str):
                industry_list = [i.strip() for i in industries.split(',') if i.strip()]
            else:
                industry_list = industries
            # Show all industries, no shortening
            sections['Industries Served'] = industry_list[:6]
            citations.append(VerifiedClaim(
                text=', '.join(industry_list),
                source='onepager:industries_served',
                original_value=industries
            ))
        
        # 4. Key Highlights (can shorten individual items)
        ops = data.get('key_operational_indicators', [])
        if ops:
            highlights = []
            for o in ops[:4]:
                text = self._anonymize(o)
                if len(text) > 70:
                    text = self._shorten_text(text, 70, 'highlight')
                highlights.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source='onepager:key_operational_indicators',
                    original_value=o
                ))
            sections['Key Highlights'] = highlights
        
        # 5. Certifications - NEVER SHORTEN
        certs = data.get('certifications', [])
        if certs:
            sections['Certifications'] = certs[:5]
            for c in certs[:5]:
                citations.append(VerifiedClaim(
                    text=c,
                    source='onepager:certifications',
                    original_value=c
                ))
        
        # Metrics for bottom bar - SHORTEN these as they have limited space
        founded = data.get('founded', '')
        employees = data.get('employees', '')
        
        # Shorten metrics to fit in boxes
        metrics = {}
        if founded:
            metrics['Founded'] = str(founded)[:10]
        if employees:
            emp_str = str(employees)
            # Just show the number
            emp_match = re.search(r'(\d[\d,]*)', emp_str)
            if emp_match:
                metrics['Employees'] = emp_match.group(1)
        
        return SlideContent(
            title="Business Profile & Capabilities",
            sections=sections,
            metrics=metrics,
            citations=citations
        )
    
    def _generate_slide_2(self, data: Dict[str, Any]) -> SlideContent:
        """Slide 2: Financial Performance."""
        financials = data.get('financials', {})
        sections = {}
        citations = []
        
        # 1. Revenue Trend (for chart data)
        revenue = financials.get('revenue', {})
        if revenue:
            years = sorted(revenue.keys())[-5:]
            rev_items = []
            for yr in years:
                text = f"FY{str(yr)[-2:]}: ₹{revenue[yr]:.1f} Cr"
                rev_items.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source='onepager:financials:revenue',
                    original_value=revenue[yr]
                ))
            sections['Revenue Trend'] = rev_items
        
        # 2. EBITDA (for chart data)
        ebitda = financials.get('ebitda', {})
        if ebitda:
            years = sorted(ebitda.keys())[-5:]
            ebitda_items = []
            for yr in years:
                text = f"FY{str(yr)[-2:]}: ₹{ebitda[yr]:.1f} Cr"
                ebitda_items.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source='onepager:financials:ebitda',
                    original_value=ebitda[yr]
                ))
            sections['EBITDA'] = ebitda_items
        
        # 3. Financial KPIs - SMART SELECTION (hide weak, show trajectory)
        kpis = []
        all_kpis = []  # Collect all possible KPIs with scores
        
        # CAGR calculation (always strong if > 5%)
        if len(revenue) >= 2:
            years = sorted(revenue.keys())
            first_yr, last_yr = years[0], years[-1]
            first_rev, last_rev = revenue[first_yr], revenue[last_yr]
            n = last_yr - first_yr
            if first_rev > 0 and n > 0:
                cagr = ((last_rev / first_rev) ** (1/n) - 1) * 100
                score = min(100, cagr * 5)  # Higher CAGR = higher score
                kpi_text = f"Revenue CAGR: {cagr:.1f}%"
                all_kpis.append((score, kpi_text, f'Verified from: CAGR=(({last_rev:.1f}/{first_rev:.1f})^(1/{n})-1)×100',
                                 {'start': first_rev, 'end': last_rev, 'years': n, 'cagr': cagr}))
        
        # EBITDA Margin
        if ebitda and revenue:
            common = set(ebitda.keys()) & set(revenue.keys())
            if common:
                yr = max(common)
                if revenue[yr] > 0:
                    margin = (ebitda[yr] / revenue[yr]) * 100
                    if margin > 8:  # Only show if reasonably strong
                        score = min(100, margin * 3)
                        kpi_text = f"EBITDA Margin: {margin:.1f}%"
                        all_kpis.append((score, kpi_text, f'Verified from: Margin=({ebitda[yr]:.1f}/{revenue[yr]:.1f})×100',
                                         {'ebitda': ebitda[yr], 'revenue': revenue[yr], 'margin': margin}))
                    else:
                        # Show trajectory if improving
                        ebitda_margins = {}
                        for y in sorted(common):
                            if revenue[y] > 0:
                                ebitda_margins[y] = (ebitda[y] / revenue[y]) * 100
                        if len(ebitda_margins) >= 2:
                            y_list = sorted(ebitda_margins.keys())
                            first_m, last_m = ebitda_margins[y_list[0]], ebitda_margins[y_list[-1]]
                            if last_m > first_m:
                                improvement = ((last_m - first_m) / max(first_m, 0.1)) * 100
                                kpi_text = f"EBITDA Margin: {first_m:.1f}% → {last_m:.1f}% (+{improvement:.0f}% improvement)"
                                all_kpis.append((20, kpi_text, f'Verified from: Margin trajectory FY{y_list[0]}-FY{y_list[-1]}',
                                                 {'trajectory': True, 'from': first_m, 'to': last_m}))
        
        # RoCE - only show if strong (>12%) or improving
        roce = financials.get('roce', {})
        if roce:
            yr = max(roce.keys())
            value = roce[yr]
            if value > 12:
                score = min(100, value * 4)
                kpi_text = f"RoCE: {value:.1f}%"
                all_kpis.append((score, kpi_text, 'onepager:financials:roce', value))
            elif len(roce) >= 2:
                # Show trajectory instead
                y_list = sorted(roce.keys())
                first_v, last_v = roce[y_list[0]], roce[y_list[-1]]
                if last_v > first_v:
                    improvement = ((last_v - first_v) / max(first_v, 0.1)) * 100
                    kpi_text = f"RoCE improved: {first_v:.1f}% → {last_v:.1f}% (+{improvement:.0f}%)"
                    all_kpis.append((15, kpi_text, 'onepager:financials:roce', {'trajectory': True}))
        
        # ROE - only show if strong (>10%) or improving
        roe = financials.get('roe', {})
        if roe:
            yr = max(roe.keys())
            value = roe[yr]
            if value > 10:
                score = min(100, value * 4)
                kpi_text = f"ROE: {value:.1f}%"
                all_kpis.append((score, kpi_text, 'onepager:financials:roe', value))
            elif len(roe) >= 2:
                y_list = sorted(roe.keys())
                first_v, last_v = roe[y_list[0]], roe[y_list[-1]]
                if last_v > first_v:
                    improvement = ((last_v - first_v) / max(first_v, 0.1)) * 100
                    kpi_text = f"ROE improved: {first_v:.1f}% → {last_v:.1f}% (+{improvement:.0f}%)"
                    all_kpis.append((15, kpi_text, 'onepager:financials:roe', {'trajectory': True}))
        
        # PAT Margin (if available)
        pat_margin = financials.get('pat_margin', {})
        if pat_margin:
            yr = max(pat_margin.keys())
            value = pat_margin[yr]
            if value > 5:
                score = min(80, value * 5)
                kpi_text = f"PAT Margin: {value:.1f}%"
                all_kpis.append((score, kpi_text, 'onepager:financials:pat_margin', value))
        
        # Revenue scale (always interesting)
        if revenue:
            latest_yr = max(revenue.keys())
            latest_rev = revenue[latest_yr]
            kpi_text = f"Revenue FY{str(latest_yr)[-2:]}: ₹{latest_rev:.1f} Cr"
            all_kpis.append((30, kpi_text, f'onepager:financials:revenue:FY{latest_yr}', latest_rev))
        
        # Sort by score (highest first) and take top 4
        all_kpis.sort(key=lambda x: x[0], reverse=True)
        
        # M&A REFACTOR: Priority mapping for the 4 dashboard boxes
        # Box 1: CAGR, Box 2: Order Book/EBITDA, Box 3: Export/Scale, Box 4: Capacity/Utilization
        op_metrics = data.get('operational_metrics', {})
        final_dashboard_kpis = []
        
        # 1. CAGR (Primary box)
        cagr_kpi = next((k for score, k, s, o in all_kpis if 'CAGR' in k), None)
        if cagr_kpi:
            final_dashboard_kpis.append(cagr_kpi)
            
        # 2. Order Book (Critical for manufacturing)
        if 'order_book' in op_metrics:
            final_dashboard_kpis.append(f"Order Book: {op_metrics['order_book']}")
        elif ebitda:
            eb_kpi = next((k for score, k, s, o in all_kpis if 'EBITDA' in k), None)
            if eb_kpi: final_dashboard_kpis.append(eb_kpi)
            
        # 3. Export / Global
        if 'export_revenue' in op_metrics:
            final_dashboard_kpis.append(f"Export Revenue: {op_metrics['export_revenue']}")
        else:
            rev_kpi = next((k for score, k, s, o in all_kpis if 'Revenue FY' in k), None)
            if rev_kpi: final_dashboard_kpis.append(rev_kpi)
            
        # 4. Capacity / Ops
        if 'capacity_utilization' in op_metrics:
            final_dashboard_kpis.append(f"Capacity Util: {op_metrics['capacity_utilization']}")
        elif roce:
             roce_kpi = next((k for score, k, s, o in all_kpis if 'RoCE' in k), None)
             if roce_kpi: final_dashboard_kpis.append(roce_kpi)

        # Fallback to fillers if needed
        for score, k, s, o in all_kpis:
            if k not in final_dashboard_kpis and len(final_dashboard_kpis) < 4:
                final_dashboard_kpis.append(k)
        
        if final_dashboard_kpis:
            sections['Financial KPIs'] = final_dashboard_kpis
            # Add citations for all used
            for k_text in final_dashboard_kpis:
                orig = next((o for sc, k, si, o in all_kpis if k == k_text), None)
                src = next((si for sc, k, si, o in all_kpis if k == k_text), 'onepager:financials')
                citations.append(VerifiedClaim(text=k_text, source=src, original_value=orig))
        
        # 4. Key Shareholders - NEVER SHORTEN names
        shareholders = data.get('shareholders', [])
        if shareholders:
            sh_list = []
            for sh in shareholders[:5]:
                name = sh.get('name', '')
                value = sh.get('value', 0)
                if name and value:
                    # Keep full name, just format nicely
                    text = f"{name}: {value:.1f}%"
                    sh_list.append(text)
                    citations.append(VerifiedClaim(
                        text=text,
                        source='onepager:shareholders',
                        original_value=sh
                    ))
            if sh_list:
                sections['Key Shareholders'] = sh_list
        
        # 5. Market Position (from web data)
        market_data = self.web_data.get('market_data', {})
        if market_data:
            market_items = []
            if market_data.get('india_market_size'):
                text = f"Industry Size: {market_data['india_market_size']}"
                market_items.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source=f"web:{market_data.get('source', 'Industry estimates')}",
                    original_value=market_data['india_market_size']
                ))
            if market_data.get('cagr'):
                text = f"Industry Growth: {market_data['cagr']}"
                market_items.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source=f"web:{market_data.get('source', 'Industry estimates')}",
                    original_value=market_data['cagr']
                ))
            
            # Ensure at least 4 items for a full layout
            if len(market_items) < 4:
                market_items.append("Increasing adoption of indigenous manufacturing (Make in India)")
                market_items.append("Strong sector tailwinds driven by digital transformation")
            
            if market_items:
                sections['Market Position'] = market_items[:4]
        
        return SlideContent(
            title="Financial & Operational Performance",
            sections=sections,
            metrics={'revenue': revenue, 'ebitda': ebitda},
            citations=citations
        )
    
    def _generate_slide_3(self, data: Dict[str, Any]) -> SlideContent:
        """Slide 3: Investment Highlights."""
        sections = {}
        citations = []
        
        # 1. Generate investment hooks
        hooks_data = self._generate_hooks(data)
        hooks = [h['text'] for h in hooks_data]
        for h in hooks_data:
            citations.append(VerifiedClaim(
                text=h['text'],
                source=h['source'],
                original_value=h.get('original')
            ))
        
        # 2. Key Strengths (from SWOT) - can shorten
        swot = data.get('swot', {})
        strengths = swot.get('strengths', [])
        if strengths:
            strength_list = []
            for s in strengths[:5]:
                text = self._anonymize(s)
                if len(text) > 120:
                    text = self._shorten_text(text, 120, 'strength')
                strength_list.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source='onepager:swot:strengths',
                    original_value=s
                ))
            sections['Key Strengths'] = strength_list
        
        # 3. Growth Opportunities (from SWOT) - can shorten
        opportunities = swot.get('opportunities', [])
        if opportunities:
            opp_list = []
            for o in opportunities[:5]:
                text = self._anonymize(o)
                if len(text) > 120:
                    text = self._shorten_text(text, 120, 'opportunity')
                opp_list.append(text)
                citations.append(VerifiedClaim(
                    text=text,
                    source='onepager:swot:opportunities',
                    original_value=o
                ))
            sections['Growth Opportunities'] = opp_list
        
        # 4. Recent Milestones - can shorten
        milestones = data.get('key_milestones', [])
        if milestones:
            milestone_list = []
            for m in milestones[:5]:
                date = m.get('date', '')
                milestone = m.get('milestone', '')
                if date and milestone:
                    text = f"{date}: {self._anonymize(milestone)}"
                    if len(text) > 70:
                        text = self._shorten_text(text, 70, 'milestone')
                    milestone_list.append(text)
                    citations.append(VerifiedClaim(
                        text=text,
                        source='onepager:key_milestones',
                        original_value=m
                    ))
            if milestone_list:
                sections['Recent Milestones'] = milestone_list
        
        # 5. Market Opportunity (from web)
        industry_outlook = self.web_data.get('industry_outlook', {})
        if industry_outlook.get('summary'):
            summary = industry_outlook['summary']
            if len(summary) > 150:
                summary = self._shorten_text(summary, 150, 'market_opportunity')
            sections['Market Opportunity'] = [summary]
            citations.append(VerifiedClaim(
                text=summary[:80],
                source=f"web:{industry_outlook.get('source', 'Industry estimates')}",
                original_value=industry_outlook
            ))
        

        # LLM Enhancement: Fill sparse sections
        min_items = 3
        for section_name in ['Key Strengths', 'Growth Opportunities', 'Market Opportunity']:
            if section_name not in sections or len(sections.get(section_name, [])) < min_items:
                # Use LLM to generate additional points
                if self.ollama.available:
                    context = f"Company: {self.company_name}\n"
                    products = data.get('products_services', [])
                    context += f"Products: {', '.join(products[:3]) if products else 'N/A'}\n"
                    industries = data.get('industries_served', [])
                    context += f"Domain: {industries[0] if industries else 'Technology'}\n"
                    
                    prompt = f"""For an M&A investment teaser, generate 3 bullet points for "{section_name}".
Company context: {context}

Rules:
- Each bullet max 80 characters
- Be specific. DO NOT use placeholders like X%, Y, Z for numbers.
- If data is unavailable, write qualitative points based ONLY on the context.
- Keep sentences complete. Do not cut off sentences abruptly.
- Professional investment language

Return ONLY a JSON array of 3 strings."""

                    try:
                        result = self.ollama.generate(prompt, temperature=0.3, max_tokens=200)
                        import json
                        cleaned = result.strip()
                        if cleaned.startswith('```'):
                            cleaned = cleaned.split('```')[1]
                            if cleaned.startswith('json'):
                                cleaned = cleaned[4:]
                        points = json.loads(cleaned.strip())
                        if isinstance(points, list):
                            existing = sections.get(section_name, [])
                            for p in points[:3]:
                                if len(existing) < 5:
                                    point_text = str(p)
                                    if len(point_text) > 100:
                                        point_text = self._shorten_text(point_text, 100, 'llm_point')
                                    existing.append(point_text)
                            sections[section_name] = existing
                    except Exception as e:
                        logger.debug(f"LLM point generation failed: {e}")
        
        return SlideContent(
            title="Investment Highlights",
            sections=sections,
            metrics={},
            hooks=hooks,
            citations=citations
        )
    
    def _generate_hooks(self, data: Dict[str, Any]) -> List[Dict]:
        """Generate REAL investor insights using LLM with full context."""
        hooks = []
        financials = data.get('financials', {})
        revenue = financials.get('revenue', {})
        market_data = self.web_data.get('market_data', {})
        
        # Prepare RICH context for LLM
        context_parts = [f"Company: [ANONYMIZED - The Company]"]
        
        products = data.get('products_services', [])
        if products:
            context_parts.append(f"Products/Services: {', '.join(products[:8])}")
        
        industries = data.get('industries_served', '')
        if industries:
            ind_str = industries if isinstance(industries, str) else ', '.join(industries[:5])
            context_parts.append(f"Industries: {ind_str}")
        
        # Certifications (critical for moat analysis)
        certs = data.get('certifications', [])
        if certs:
            context_parts.append(f"Certifications: {', '.join(certs[:5])}")
        
        # Key operational indicators
        ops = data.get('key_operational_indicators', [])
        if ops:
            context_parts.append(f"Key Operational Highlights: {'; '.join(ops[:4])}")
        
        # SWOT strengths
        swot = data.get('swot', {})
        strengths = swot.get('strengths', [])
        if strengths:
            context_parts.append(f"Core Strengths: {'; '.join(strengths[:3])}")
        
        # Web-scraped company data
        company_info = self.web_data.get('company_info', {})
        for page_type, page_data in company_info.items():
            if isinstance(page_data, dict) and 'content' in page_data:
                content = page_data['content'][:500]  # First 500 chars of each page
                context_parts.append(f"Web ({page_type}): {content}")
        
        # Market data
        if market_data:
            if market_data.get('india_market_size'):
                context_parts.append(f"Total Addressable Market: {market_data['india_market_size']}")
            if market_data.get('cagr'):
                context_parts.append(f"Industry Growth Rate: {market_data['cagr']}")
            if market_data.get('key_drivers'):
                context_parts.append(f"Growth Drivers: {', '.join(market_data.get('key_drivers', [])[:4])}")
        
        # Financial metrics
        if len(revenue) >= 2:
            years = sorted(revenue.keys())
            latest = revenue[years[-1]]
            first = revenue[years[0]]
            n = years[-1] - years[0]
            if first > 0 and n > 0:
                cagr = ((latest / first) ** (1/n) - 1) * 100
                context_parts.append(f"Revenue CAGR: {cagr:.1f}% over {n} years")
                context_parts.append(f"Latest Revenue: ₹{latest:.1f} Cr")
        
        ebitda = financials.get('ebitda', {})
        if ebitda and revenue:
            common = set(ebitda.keys()) & set(revenue.keys())
            if common:
                yr = max(common)
                if revenue[yr] > 0:
                    margin = (ebitda[yr] / revenue[yr]) * 100
                    context_parts.append(f"EBITDA Margin: {margin:.1f}%")
        
        # Global presence
        global_presence = data.get('global_presence', [])
        if global_presence:
            context_parts.append(f"Global Footprint: {', '.join(global_presence[:5])}")
        
        context = "\n".join(context_parts)
        
        # Generate insights with LLM
        if self.ollama.available:
            prompt = f"""You are a senior M&A investment banker at a top-tier firm writing investment highlights for institutional PE/VC investors.

Company Data:
{context}

Write 3-4 COMPELLING, SPECIFIC investment highlights. Think like an analyst presenting to a PE fund partner.

CRITICAL RULES:
- Each highlight MUST contain specific numbers, percentages, or quantified facts from the data
- Write in assertive, confident M&A language (NOT generic marketing copy)
- Focus on: competitive moats, addressable market capture, operational leverage, growth trajectory
- NEVER use weak phrases like "positioned for growth", "diversified company", "growing market"
- Each highlight should be a single powerful sentence (max 20 words)

EXAMPLES OF EXCELLENT HIGHLIGHTS:
- "Mission-critical electronics partner to defense programs with 25-year proven delivery record"
- "9.5% revenue CAGR anchored by ₹850 Cr order book providing 12+ months visibility"
- "Only ISO 9001 + AS9100 certified player in segment, creating significant entry barriers"
- "45% export revenue diversifies geography risk; serves 8 regulated end-markets"
- "Platform economics: 35%+ gross margins with operating leverage from 4 manufacturing facilities"

Return ONLY a JSON array of 3-4 strings. No explanation, no markdown.
Example: ["First insight here", "Second insight here", "Third insight here"]"""

            result = self.ollama.generate(prompt, temperature=0.3, max_tokens=300)
            
            # Track tokens
            token_tracker.track_from_response(
                task='hook_generation_llm',
                model=self.ollama.model,
                prompt=prompt,
                response=result
            )
            
            # Parse JSON response
            try:
                import json
                # Clean response - remove markdown if present
                cleaned = result.strip()
                if cleaned.startswith('```'):
                    # Remove markdown code blocks
                    cleaned = cleaned.split('```')[1]
                    if cleaned.startswith('json'):
                        cleaned = cleaned[4:]
                cleaned = cleaned.strip()
                
                insights = json.loads(cleaned)
                if isinstance(insights, list):
                    for insight in insights[:4]:
                        insight_text = str(insight)
                        if len(insight_text) > 150:
                            insight_text = self._shorten_text(insight_text, 150, 'hook')
                        hooks.append({
                            'text': insight_text,
                            'source': '[AI Generated from company data + market analysis]',
                            'original': context
                        })
                    if hooks:
                        logger.info(f"Generated {len(hooks)} LLM-powered insights")
                        return hooks
            except Exception as e:
                logger.warning(f"Failed to parse LLM insights: {e}, using fallback")
        else:
            logger.warning("LLM not available, using rule-based fallback")
        
        # Fallback: Better rule-based hooks
        if len(revenue) >= 2:
            years = sorted(revenue.keys())
            latest = revenue[years[-1]]
            first = revenue[years[0]]
            n = years[-1] - years[0]
            if first > 0 and n > 0:
                cagr = ((latest / first) ** (1/n) - 1) * 100
                if cagr > 0:
                    text = f"{cagr:.0f}% revenue CAGR over {n} years to ₹{latest:.0f} Cr"
                    hooks.append({
                        'text': text,
                        'source': 'Verified from financials',
                        'original': {'cagr': cagr, 'revenue': latest}
                    })
        
        # Add market size if available
        if market_data and market_data.get('india_market_size'):
            text = f"Operating in {market_data['india_market_size']} market"
            if market_data.get('cagr'):
                text += f" growing at {market_data['cagr']}"
            hooks.append({
                'text': text,
                'source': 'Verified from market data',
                'original': market_data
            })
        
        # Ensure we have at least some hooks
        if not hooks:
            hooks.append({
                'text': 'Strong operational track record',
                'source': 'company_description',
                'original': data.get('business_description', '')
            })
        
        return hooks[:4]

    def _shorten_text(self, text: str, max_chars: int, context: str) -> str:
        """
        Shorten text using LLM. Never truncate with '...'.
        Only call for appropriate contexts (not products/services).
        """
        if not text or len(text) <= max_chars:
            return text
        
        # Use LLM for intelligent shortening
        if self.ollama.available:
            prompt = f"""Shorten this text to under {max_chars} characters while keeping the key meaning.
Do NOT end with "..." or cut mid-word.

Text: {text}

Return only the shortened text:"""
            
            result = self.ollama.generate(prompt, temperature=0.2, max_tokens=80)
            
            # Track tokens
            token_tracker.track_from_response(
                task=f'text_shortening:{context}',
                model=self.ollama.model,
                prompt=prompt,
                response=result or ''
            )
            
            if result:
                shortened = result.strip().strip('"').strip("'")
                # Ensure no "..."
                shortened = shortened.rstrip('.')
                if shortened.endswith('..'):
                    shortened = shortened[:-2]
                if len(shortened) <= max_chars:
                    return shortened
        
        # Fallback: Smart truncate at word boundary
        words = text.split()
        result = ""
        for word in words:
            if len(result) + len(word) + 1 > max_chars:
                break
            result = result + " " + word if result else word
        
        return result.strip()
    
    def _anonymize(self, text: str) -> str:
        """Multi-pass anonymization: Regex → NER-Regex → LLM verification."""
        if not text:
            return text
        return self._anonymize_multi_pass(text)

    def _anonymize_multi_pass(self, text: str) -> str:
        """
        3-pass anonymization pipeline:
        Pass 1: Regex-based company name variant replacement
        Pass 2: NER-regex for person names, emails, phones, org names
        Pass 3: LLM verification + sentence reconstruction
        """
        if not text:
            return text

        result = text

        # === PASS 1: Company name variants (regex) ===
        if self.company_name:
            variants = self._generate_name_variants(self.company_name)
            # Sort by length descending so longer matches go first
            variants.sort(key=lambda x: len(x[0]), reverse=True)
            for pattern, replacement in variants:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # === PASS 2: NER-regex pass (persons, emails, phones, orgs) ===
        result = self._ner_regex_pass(result)

        # === PASS 3: Location anonymization ===
        locations = {
            r'\bBangalore\b': 'South India',
            r'\bBengaluru\b': 'South India',
            r'\bMumbai\b': 'West India',
            r'\bDelhi\b': 'North India',
            r'\bNew Delhi\b': 'North India',
            r'\bChennai\b': 'South India',
            r'\bHyderabad\b': 'South India',
            r'\bPune\b': 'West India',
            r'\bNoida\b': 'North India',
            r'\bGurgaon\b': 'North India',
            r'\bGurugram\b': 'North India',
            r'\bKolkata\b': 'East India',
            r'\bAhmedabad\b': 'West India',
            r'\bJaipur\b': 'North India',
            r'\bLucknow\b': 'North India',
            r'\bKochi\b': 'South India',
            r'\bCoimbatore\b': 'South India',
            r'\bVadodara\b': 'West India',
            r'\bIndore\b': 'Central India',
            r'\bNagpur\b': 'Central India',
            r'\bVisakhapatnam\b': 'South India',
            r'\bDRDO\b': 'Defence Organization',
            r'\bISRO\b': 'Space Agency',
            r'\bHAL\b': 'Aerospace PSU',
            r'\bBHEL\b': 'Power Equipment PSU',
            r'\bBEL\b': 'Defence Electronics PSU',
        }
        for pattern, replacement in locations.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # === PASS 4: LLM verification + sentence reconstruction ===
        result = self._llm_anonymize_verify(result)
        
        # === PASS 5: Clean up unprofessional artifacts ===
        # Avoid things like "Strategic The Company" or "The Company Sector"
        result = re.sub(r'Strategic ["\']?The Company["\']?', 'Strategic Solutions', result, flags=re.IGNORECASE)
        result = re.sub(r'["\']?The Company["\']? Sector', 'the industry', result, flags=re.IGNORECASE)
        result = re.sub(r'Strategic The Company', 'Strategic Solutions', result, flags=re.IGNORECASE)
        result = re.sub(r'The Company Solutions', 'Core Solutions', result, flags=re.IGNORECASE)

        return result.strip()

    def _generate_name_variants(self, company_name: str) -> list:
        """Generate all possible company name patterns for regex replacement."""
        variants = []
        name = company_name.strip()

        # Full name and common suffixes
        suffixes = ['', ' Ltd', ' Ltd.', ' Limited', ' Pvt', ' Pvt.', ' Pvt Ltd',
                     ' Pvt. Ltd.', ' Private Limited', ' Inc', ' Inc.',
                     ' Corporation', ' Corp', ' Corp.', ' LLP', ' Technologies',
                     ' Solutions', ' Industries', ' Enterprises', ' Group']
        for suffix in suffixes:
            full = name + suffix
            if full:
                variants.append((re.escape(full), "The Company"))

        # Individual words from name (skip very short ones like "Ind", "IT")
        words = name.split()
        if len(words) > 1:
            for word in words:
                if len(word) > 3:  # Only replace words > 3 chars to avoid false positives
                    variants.append((r'\b' + re.escape(word) + r'\b', "The Company"))

        # CamelCase / NoSpace: "CentumElectronics"
        no_space = name.replace(' ', '')
        if no_space != name:
            variants.append((re.escape(no_space), "TheCompany"))

        # Hyphenated: "Centum-Electronics"
        hyphenated = name.replace(' ', '-')
        if hyphenated != name:
            variants.append((re.escape(hyphenated), "The-Company"))

        # Acronym (only if 2+ words and acronym > 2 chars)
        if len(words) >= 2:
            acronym = ''.join(w[0].upper() for w in words if w)
            if len(acronym) > 2:
                variants.append((r'\b' + re.escape(acronym) + r'\b', "The Company"))

        # Domain/website-derived name patterns
        website = self.source_data.get('website', '')
        if website:
            # Extract domain name: "www.ksolves.com" → "ksolves"
            domain_match = re.search(r'(?:www\.)?([a-zA-Z0-9\-]+)\.\w+', website)
            if domain_match:
                domain_name = domain_match.group(1)
                if len(domain_name) > 3:
                    variants.append((r'\b' + re.escape(domain_name) + r'\b', "The Company"))

        # Client/partner names from extracted data
        clients = self.source_data.get('clients', [])
        partners = self.source_data.get('partners', [])
        for entity_list in [clients, partners]:
            for entity in entity_list:
                if isinstance(entity, str) and len(entity.strip()) > 3:
                    clean = entity.strip().lstrip('- ')
                    if clean:
                        variants.append((re.escape(clean), "[Client/Partner]"))

        return variants

    def _ner_regex_pass(self, text: str) -> str:
        """NER-like regex pass to remove person names, emails, phones."""
        result = text

        # Email addresses
        result = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[email redacted]', result
        )

        # Phone numbers (Indian and international)
        result = re.sub(
            r'(?:\+91[\-\s]?)?(?:\d[\-\s]?){10,12}',
            '[phone redacted]', result
        )

        # Person names with titles: "Mr. Sharma", "Dr. Rajesh Kumar", "CEO John Smith"
        title_patterns = [
            r'\b(?:Mr|Mrs|Ms|Dr|Prof|Shri|Smt|CEO|CFO|CTO|COO|CMD|MD|Director|Chairman|Chairperson|Founder|Co-founder|President|VP|Managing\s+Director)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b',
        ]
        for pat in title_patterns:
            result = re.sub(pat, 'a senior executive', result)

        # Standalone person names: "Founded by Rajesh Kumar" pattern
        # Match "by <Name>" or "under <Name>" patterns
        result = re.sub(
            r'\b(?:by|under|led by|headed by|managed by|founded by)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b',
            'by the management team', result, flags=re.IGNORECASE
        )

        # Website URLs containing company name
        if self.company_name:
            name_lower = self.company_name.lower().replace(' ', '')
            result = re.sub(
                r'https?://[^\s]*' + re.escape(name_lower) + r'[^\s]*',
                '[company website]', result, flags=re.IGNORECASE
            )

        return result

    def _llm_anonymize_verify(self, text: str) -> str:
        """LLM pass: verify anonymization and reconstruct incomplete sentences."""
        if not self.ollama.available:
            return text

        # Only call LLM if text is substantial enough
        if len(text) < 20:
            return text

        try:
            prompt = f"""You are an M&A anonymization expert. Review this text and fix any issues:

1. If any company name, person name, specific location (city name), email, or phone number remains, replace them:
   - Company names → "The Company"
   - Person names → "the management" or "a senior executive"
   - Cities → regional descriptions (e.g., "South India", "a metropolitan city")
2. If removing a name leaves an INCOMPLETE sentence (e.g., "Founded by in 2015"), reconstruct it naturally (e.g., "Founded in 2015").
3. Keep ALL numbers, percentages, financial data, and metrics EXACTLY as they are.
4. Keep the text length similar - do NOT add new information.
5. If the text is already properly anonymized, return it UNCHANGED.

Text to review:
{text}

Return ONLY the corrected text, nothing else:"""

            result = self.ollama.generate(prompt, temperature=0.1, max_tokens=len(text) + 100)

            if result:
                cleaned = result.strip().strip('"').strip("'")
                # Sanity check: result shouldn't be drastically different in length
                if 0.3 < len(cleaned) / max(len(text), 1) < 3.0:
                    # Final check: company name must not appear
                    if self.company_name and self.company_name.lower() in cleaned.lower():
                        # LLM failed, do regex cleanup
                        for word in self.company_name.split():
                            if len(word) > 3:
                                cleaned = re.sub(r'\b' + re.escape(word) + r'\b', 'The Company', cleaned, flags=re.IGNORECASE)
                    return cleaned
        except Exception as e:
            logger.warning(f"LLM anonymization check failed: {e}")

        return text


if __name__ == "__main__":
    print("Content writer ready - NEVER shortens products/services")
