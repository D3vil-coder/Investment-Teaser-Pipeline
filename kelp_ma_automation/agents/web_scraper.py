"""
Web Scraper Agent (Agent 3) - PRODUCTION VERSION v5
Uses Playwright for robust scraping with SMART PAGE DISCOVERY.
Fallbacks to Requests-based discovery if Playwright unavailable.
NO TRUNCATION - Captures full content.
"""

import re
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin, urlunparse
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedPage:
    """A scraped page with full URL and content."""
    url: str
    page_type: str
    content: str
    scraped_at: str
    success: bool


@dataclass
class MarketDataSource:
    """Market data with proper source URL."""
    metric: str
    value: str
    source_name: str
    source_url: str
    access_date: str


# Market data with ACTUAL source URLs
MARKET_DATA_SOURCES = {
    'manufacturing': {
        'industry_name': 'Electronics Manufacturing Services (EMS)',
        'india_market_size': '$15 billion (2024)',
        'global_market_size': '$672 billion (2024)',
        'cagr': '7-9% (2024-2030)',
        'key_drivers': ['PLI scheme', 'Make in India', 'Defense localization', 'EV adoption'],
        'sources': [
            MarketDataSource(
                metric='India EMS Market',
                value='$15 billion',
                source_name='IBEF Electronics Manufacturing Report',
                source_url='https://www.ibef.org/industry/electronics-system-design-manufacturing',
                access_date='2024-12'
            ),
            MarketDataSource(
                metric='Global EMS Market',
                value='$672 billion',
                source_name='Mordor Intelligence',
                source_url='https://www.mordorintelligence.com/industry-reports/electronics-manufacturing-services-market',
                access_date='2024-12'
            ),
        ]
    },
    'technology': {
        'industry_name': 'IT Services',
        'india_market_size': '$245 billion (2024)',
        'global_market_size': '$1.2 trillion (2024)',
        'cagr': '8-10% (2024-2028)',
        'key_drivers': ['Digital transformation', 'Cloud adoption', 'AI/ML demand', 'Remote work'],
        'sources': [
            MarketDataSource(
                metric='India IT Industry',
                value='$245 billion',
                source_name='NASSCOM Industry Performance Report',
                source_url='https://nasscom.in/knowledge-center/publications/technology-sector-india-2024-strategic-review',
                access_date='2024-12'
            ),
            MarketDataSource(
                metric='Global IT Services',
                value='$1.2 trillion',
                source_name='Gartner IT Spending Forecast',
                source_url='https://www.gartner.com/en/newsroom/press-releases/2024-01-17-gartner-forecasts-worldwide-it-spending',
                access_date='2024-12'
            ),
        ]
    },
    'logistics': {
        'industry_name': 'Logistics & Express Delivery',
        'india_market_size': '$250 billion (2024)',
        'global_market_size': '$3.2 trillion (2024)',
        'cagr': '10-12% (2024-2028)',
        'key_drivers': ['E-commerce growth', 'GST', 'Infrastructure investment', 'Last-mile innovation'],
        'sources': [
            MarketDataSource(
                metric='India Logistics Market',
                value='$250 billion',
                source_name='IBEF Logistics Report',
                source_url='https://www.ibef.org/industry/ecommerce-logistics',
                access_date='2024-12'
            ),
            MarketDataSource(
                metric='E-commerce Logistics',
                value='₹50,000 crore by 2025',
                source_name='RedSeer Consulting',
                source_url='https://redseer.com/reports/india-ecommerce-logistics-market',
                access_date='2024-12'
            ),
        ]
    },
    'consumer': {
        'industry_name': 'D2C / Consumer Brands',
        'india_market_size': '$12 billion (2024)',
        'global_market_size': '$250 billion (2024)',
        'cagr': '25-30% (2024-2028)',
        'key_drivers': ['Digital penetration', 'Rising incomes', 'Premiumization', 'Health consciousness'],
        'sources': [
            MarketDataSource(
                metric='India D2C Market',
                value='$12 billion',
                source_name='Bain & Company India Report',
                source_url='https://www.bain.com/insights/how-india-shops-online-2024/',
                access_date='2024-12'
            ),
        ]
    },
    'healthcare': {
        'industry_name': 'Pharmaceuticals',
        'india_market_size': '$50 billion (2024)',
        'global_market_size': '$1.6 trillion (2024)',
        'cagr': '9-11% (2024-2030)',
        'key_drivers': ['Generic demand', 'API manufacturing', 'PLI scheme', 'Biosimilars growth'],
        'sources': [
            MarketDataSource(
                metric='India Pharma Market',
                value='$50 billion',
                source_name='IBEF Pharmaceutical Report',
                source_url='https://www.ibef.org/industry/pharmaceutical-india',
                access_date='2024-12'
            ),
            MarketDataSource(
                metric='Global Pharma Market',
                value='$1.6 trillion',
                source_name='IQVIA Global Report',
                source_url='https://www.iqvia.com/insights/the-iqvia-institute/reports/global-trends-in-r-and-d-2024',
                access_date='2024-12'
            ),
        ]
    },
    'infrastructure': {
        'industry_name': 'Infrastructure & Construction',
        'india_market_size': '$200 billion (2024)',
        'global_market_size': '$15 trillion (2024)',
        'cagr': '8-10% (2024-2030)',
        'key_drivers': ['Govt spending', 'NIP', 'Urbanization', 'Housing demand'],
        'sources': [
            MarketDataSource(
                metric='India Infrastructure',
                value='$200 billion',
                source_name='IBEF Infrastructure Report',
                source_url='https://www.ibef.org/industry/infrastructure-sector-india',
                access_date='2024-12'
            ),
        ]
    },
    'chemicals': {
        'industry_name': 'Specialty Chemicals',
        'india_market_size': '$40 billion (2024)',
        'global_market_size': '$600 billion (2024)',
        'cagr': '10-12% (2024-2028)',
        'key_drivers': ['China+1', 'PLI scheme', 'Sustainability', 'Innovation'],
        'sources': [
            MarketDataSource(
                metric='India Chemicals',
                value='$40 billion',
                source_name='IBEF Chemicals Report',
                source_url='https://www.ibef.org/industry/chemicals-industry-india',
                access_date='2024-12'
            ),
        ]
    },
    'automotive': {
        'industry_name': 'Auto Components',
        'india_market_size': '$70 billion (2024)',
        'global_market_size': '$450 billion (2024)',
        'cagr': '8-10% (2024-2030)',
        'key_drivers': ['EV transition', 'Export growth', 'Localization', 'Premiumization'],
        'sources': [
            MarketDataSource(
                metric='India Auto Components',
                value='$70 billion',
                source_name='ACMA Annual Report',
                source_url='https://www.acma.in/uploads/annual-report-2024.pdf',
                access_date='2024-12'
            ),
        ]
    },
}


class WebScraper:
    """
    Production web scraper with Playwright and SMART PAGE DISCOVERY.
    """
    
    def __init__(self, use_playwright: bool = True):
        self.use_playwright = use_playwright
        self.scraped_pages: List[ScrapedPage] = []
        self.rate_limit_delay = 1.0  # Faster but safe
        self._playwright_available = None
        self._check_playwright()
    
    def _check_playwright(self) -> bool:
        """Check if Playwright is available."""
        if self._playwright_available is not None:
            return self._playwright_available
        try:
            from playwright.sync_api import sync_playwright
            self._playwright_available = True
        except ImportError:
            logger.warning("Playwright not installed. Using requests fallback.")
            self._playwright_available = False
        return self._playwright_available
    
    def scrape_all_sources(self, company_name: str, website: str, 
                           domain: str) -> Dict[str, Any]:
        """Scrape all sources with actual URLs."""
        results = {
            'company_info': {},
            'market_data': {},
            'news': [],
            'industry_outlook': {},
            'sources_used': [],
            'scraped_pages': []
        }
        
        # 1. Scrape company website (SMART DISCOVERY)
        if website:
            logger.info(f"Scraping company website: {website}")
            company_data = self._scrape_company_website_smart(website)
            results['company_info'] = company_data
            results['scraped_pages'] = [p.__dict__ for p in self.scraped_pages]
        
        # 2. Get market data with actual URLs
        logger.info(f"Fetching market data for domain: {domain}")
        market_data = self._get_market_data_with_urls(domain)
        results['market_data'] = market_data
        
        # 3. Get industry news
        logger.info(f"Fetching industry news for domain: {domain}")
        results['news'] = self._get_industry_news(domain)
        
        # 4. Compile industry outlook
        results['industry_outlook'] = self._compile_outlook(domain, market_data)
        
        # 5. Build sources list with actual URLs
        for source in market_data.get('sources', []):
            results['sources_used'].append({
                'url': source.source_url,
                'name': source.source_name,
                'type': 'market_data',
                'access_date': source.access_date
            })
        
        for page in self.scraped_pages:
            if page.success:
                results['sources_used'].append({
                    'url': page.url,
                    'name': f'Company Website - {page.page_type}',
                    'type': 'company',
                    'access_date': page.scraped_at
                })
        
        logger.info(f"Scraping complete: {len(results['sources_used'])} sources")
        return results
    
    def _scrape_company_website_smart(self, website: str) -> Dict[str, Any]:
        """Smartly discover and scrape relevant pages."""
        data = {}
        
        if not website:
            return data
        
        base_url = website.rstrip('/')
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        # Priority 1: Playwright Smart Discovery
        if self._playwright_available and self.use_playwright:
            try:
                logger.info("Discovering pages with Playwright...")
                discovered_pages = self._discover_pages_playwright(base_url)
                if discovered_pages:
                    return self._scrape_pages_playwright(base_url, discovered_pages)
                else:
                    logger.warning("Playwright discovery failed/empty. Trying requests fallback.")
            except Exception as e:
                logger.warning(f"Playwright discovery error: {e}")
        
        # Priority 2: Requests Smart Discovery
        logger.info("Discovering pages with Requests...")
        discovered_pages_req = self._discover_pages_requests(base_url)
        if discovered_pages_req:
             return self._scrape_with_requests(base_url, discovered_pages_req)

        # Priority 3: Blind Guessing (Last Resort)
        logger.warning("Smart discovery failed. Falling back to guessing commonly used paths.")
        defaults = {
            'about': ['/about-us', '/about', '/company'],
            'products': ['/products', '/services', '/solutions'],
            'investors': ['/investors', '/investor-relations'],
            'contact': ['/contact', '/contact-us']
        }
        return self._scrape_with_requests(base_url, defaults)

    def _get_page_categories_keywords(self):
        """Keywords for categorizing pages."""
        return {
            'about': ['about', 'company', 'who we are', 'profile', 'leadership', 'vision'],
            'products': ['product', 'service', 'solution', 'offering', 'capabilities', 'platform'],
            'investors': ['investor', 'financial', 'shareholder', 'annual report', 'quarterly', 'results'],
            'contact': ['contact', 'reach us', 'location', 'office'],
            'news': ['news', 'media', 'press', 'blog', 'insight', 'update']
        }

    def _discover_pages_playwright(self, base_url: str) -> Optional[Dict[str, List[str]]]:
        """Visit homepage and find actual links using Playwright."""
        from playwright.sync_api import sync_playwright
        
        categories = self._get_page_categories_keywords()
        discovered = {k: [] for k in categories.keys()}
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(base_url, wait_until='domcontentloaded', timeout=15000)
                
                # Extract all links
                links = page.query_selector_all('a')
                
                visited_urls = set()
                visited_urls.add(base_url)
                visited_urls.add(base_url + '/')
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        text = link.inner_text().lower().strip()
                        
                        if not href or href.startswith('#') or href.startswith('javascript'):
                            continue
                            
                        full_url = urljoin(base_url, href)
                        
                        # Only internal links
                        if urlparse(full_url).netloc != urlparse(base_url).netloc:
                            continue
                            
                        if full_url in visited_urls:
                            continue
                            
                        # Classify link
                        for cat, keywords in categories.items():
                            url_lower = full_url.lower()
                            if any(k in url_lower for k in keywords) or any(k in text for k in keywords):
                                discovered[cat].append(full_url)
                                visited_urls.add(full_url)
                                break 
                                
                    except Exception:
                        continue
                
                browser.close()
                
        except Exception as e:
            logger.error(f"Playwright Discovery error: {e}")
            return None
            
        return self._deduplicate_links(discovered)

    def _discover_pages_requests(self, base_url: str) -> Dict[str, List[str]]:
        """Visit homepage and find actual links using Requests + BeautifulSoup."""
        import requests
        import urllib3
        from bs4 import BeautifulSoup
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        categories = self._get_page_categories_keywords()
        discovered = {k: [] for k in categories.keys()}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            resp = requests.get(base_url, headers=headers, timeout=10, verify=False)
            if resp.status_code != 200:
                logger.warning(f"Homepage fetch failed: {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            visited_urls = set()
            visited_urls.add(base_url)
            visited_urls.add(base_url + '/')

            for link in links:
                href = link['href']
                text = link.get_text(separator=' ', strip=True).lower()
                
                if not href or href.startswith('#') or href.startswith('javascript') or href.startswith('mailto'):
                    continue
                    
                full_url = urljoin(base_url, href)
                
                # Only internal links
                try:
                    if urlparse(full_url).netloc != urlparse(base_url).netloc:
                        continue
                except Exception:
                    continue

                if full_url in visited_urls:
                    continue

                # Classify link
                for cat, keywords in categories.items():
                    url_lower = full_url.lower()
                    if any(k in url_lower for k in keywords) or any(k in text for k in keywords):
                        discovered[cat].append(full_url)
                        visited_urls.add(full_url)
                        break 

            return self._deduplicate_links(discovered)

        except Exception as e:
            logger.error(f"Requests Discovery error: {e}")
            return None

    def _deduplicate_links(self, discovered: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Clean up and sort discovered links."""
        final_discovered = {}
        for cat, urls in discovered.items():
            unique_urls = list(set(urls))
            # Sort by length (shorter is usually main page) but prioritize those without query params
            unique_urls.sort(key=lambda u: (len(urlparse(u).query), len(u)))
            final_discovered[cat] = unique_urls[:3] # Keep top 3 candidates to try
        
        found_count = sum(len(v) for v in final_discovered.values())
        logger.info(f"Smart Discovery found: {found_count} links")
        return final_discovered

    def _scrape_pages_playwright(self, base_url: str, pages_map: Dict[str, List[str]]) -> Dict[str, Any]:
        """Scrape specific pages using Playwright."""
        from playwright.sync_api import sync_playwright
        
        data = {}
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            # Scrape Homepage first
            try:
                page.goto(base_url, wait_until='domcontentloaded', timeout=15000)
                time.sleep(1)
                content = page.content()
                text = self._extract_text(content)
                
                scraped = ScrapedPage(
                    url=base_url,
                    page_type='homepage',
                    content=text,  # NO TRUNCATION
                    scraped_at=time.strftime('%Y-%m-%d %H:%M'),
                    success=True
                )
                self.scraped_pages.append(scraped)
                data['homepage'] = {
                    'url': base_url,
                    'content': text,
                    'scraped_at': scraped.scraped_at
                }
                logger.info(f"  ✓ Scraped: {base_url} ({len(text)} chars)")
            except Exception as e:
                logger.warning(f"  ✗ Failed to scrape homepage: {e}")
            
            # Scrape other categories
            for page_type, urls in pages_map.items():
                # Try candidates until one works
                for target_url in urls:
                    if target_url in [p.url for p in self.scraped_pages]:
                        continue
                        
                    try:
                        time.sleep(self.rate_limit_delay)
                        page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
                        
                        content = page.content()
                        text = self._extract_text(content)
                        
                        if text and len(text) > 200:
                            scraped = ScrapedPage(
                                url=target_url,
                                page_type=page_type,
                                content=text, # NO TRUNCATION
                                scraped_at=time.strftime('%Y-%m-%d %H:%M'),
                                success=True
                            )
                            self.scraped_pages.append(scraped)
                            data[page_type] = {
                                'url': target_url,
                                'content': text,
                                'scraped_at': scraped.scraped_at
                            }
                            logger.info(f"  ✓ Scraped: {target_url} ({len(text)} chars)")
                            break # Move to next category if successful
                    except Exception as e:
                        logger.warning(f"  ✗ Failed to scrape {target_url}: {e}")
                        continue
            
            browser.close()
            
        return data

    def _scrape_with_requests(self, base_url: str, pages: Dict[str, List[str]]) -> Dict[str, Any]:
        """Fallback scraping with requests (unlimited text)."""
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        data = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # Scrape main page if not already scraped
        if not any(p.page_type == 'homepage' for p in self.scraped_pages):
            try:
                resp = requests.get(base_url, headers=headers, timeout=10, verify=False)
                if resp.status_code == 200:
                    text = self._extract_text(resp.text)
                    scraped = ScrapedPage(
                        url=base_url,
                        page_type='homepage',
                        content=text, # NO TRUNCATION
                        scraped_at=time.strftime('%Y-%m-%d %H:%M'),
                        success=True
                    )
                    self.scraped_pages.append(scraped)
                    data['homepage'] = {
                        'url': base_url,
                        'content': text,
                        'scraped_at': scraped.scraped_at
                    }
                    logger.info(f"  ✓ Scraped: {base_url} ({len(text)} chars)")
            except Exception as e:
                logger.warning(f"  ✗ Failed: {e}")
        
        # Try subpages
        for page_type, paths in pages.items():
            for path in paths:
                # Handle full URLs vs paths
                url = path if path.startswith('http') else urljoin(base_url, path)
                
                if any(p.url == url for p in self.scraped_pages):
                    continue

                try:
                    time.sleep(self.rate_limit_delay)
                    resp = requests.get(url, headers=headers, timeout=10, verify=False)
                    if resp.status_code == 200:
                        text = self._extract_text(resp.text)
                        if text and len(text) > 200:
                            scraped = ScrapedPage(
                                url=url,
                                page_type=page_type,
                                content=text, # NO TRUNCATION
                                scraped_at=time.strftime('%Y-%m-%d %H:%M'),
                                success=True
                            )
                            self.scraped_pages.append(scraped)
                            data[page_type] = {
                                'url': url,
                                'content': text,
                                'scraped_at': scraped.scraped_at
                            }
                            logger.info(f"  ✓ Scraped: {url} ({len(text)} chars)")
                            break
                except Exception as e:
                    logger.debug(f"Failed to scrape {page_type}: {e}")
                    continue
        
        return data
    
    def _extract_text(self, html: str) -> str:
        """Extract clean text from HTML. No Truncation."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts, styles, nav, footer, ads
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())  # Clean whitespace
            return text
        except Exception as e:
            logger.debug(f"BeautifulSoup extraction failed: {e}")
            text = re.sub(r'<[^>]+>', ' ', html)
            text = ' '.join(text.split())
            return text
    
    def _get_market_data_with_urls(self, domain: str) -> Dict[str, Any]:
        """Get market data with actual source URLs."""
        domain_lower = domain.lower()
        if domain_lower in MARKET_DATA_SOURCES:
            return MARKET_DATA_SOURCES[domain_lower].copy()
            
        for key in MARKET_DATA_SOURCES:
            if key in domain_lower or domain_lower in key:
                return MARKET_DATA_SOURCES[key].copy()
        
        return {'industry_name': 'General Industry', 'sources': []}
    
    def _get_industry_news(self, domain: str) -> List[Dict]:
        """Get industry news - LIVE via Google News RSS, fallback to hardcoded."""
        
        # Try live news first
        live_news = self._fetch_live_news(domain)
        if live_news:
            return live_news
        
        # Fallback to hardcoded
        return self._get_hardcoded_news(domain)
    
    def _fetch_live_news(self, domain: str) -> List[Dict]:
        """Fetch live industry news from Google News RSS."""
        try:
            import requests
            import urllib.parse
            import urllib3
            import xml.etree.ElementTree as ET
            from datetime import datetime, timedelta
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Build search query focused on industry trends
            domain_queries = {
                'manufacturing': 'India manufacturing industry growth trends',
                'technology': 'India IT technology sector trends growth',
                'logistics': 'India logistics supply chain industry trends',
                'consumer': 'India consumer retail D2C brand trends',
                'healthcare': 'India pharma healthcare industry trends',
                'infrastructure': 'India infrastructure construction sector trends',
                'chemicals': 'India specialty chemicals industry trends',
                'automotive': 'India automotive EV industry trends',
                'electronics': 'India electronics manufacturing industry trends',
            }
            
            domain_lower = domain.lower()
            query = domain_queries.get(domain_lower, f'India {domain_lower} industry trends growth')
            
            # URL encode the query
            encoded_query = urllib.parse.quote(query)
            rss_url = f'https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en'
            
            response = requests.get(rss_url, timeout=10, verify=False, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.text)
            channel = root.find('channel')
            if channel is None:
                return []
            
            news = []
            cutoff = datetime.now() - timedelta(days=90)
            
            # Industry-relevance keywords
            relevance_keywords = [
                'growth', 'market', 'industry', 'sector', 'manufacturing',
                'revenue', 'investment', 'export', 'demand', 'trend',
                'billion', 'crore', 'GDP', 'policy', 'PLI', 'FDI',
                'startup', 'technology', 'digital', 'innovation',
                'supply chain', 'capacity', 'expansion', 'partnership'
            ]
            
            for item in channel.findall('item'):
                if len(news) >= 4:
                    break
                
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')
                
                if title is None or link is None:
                    continue
                
                headline = title.text or ''
                
                # Check relevance
                headline_lower = headline.lower()
                is_relevant = any(kw.lower() in headline_lower for kw in relevance_keywords)
                if not is_relevant:
                    continue
                
                # Parse date
                date_str = ''
                if pub_date is not None and pub_date.text:
                    try:
                        # RFC 822 format: "Sat, 08 Mar 2026 12:00:00 GMT"
                        parsed_date = datetime.strptime(pub_date.text.strip()[:25], '%a, %d %b %Y %H:%M:%S')
                        if parsed_date < cutoff:
                            continue  # Skip old news
                        date_str = parsed_date.strftime('%Y-%m')
                    except (ValueError, IndexError):
                        date_str = 'Recent'
                
                source_name = source.text if source is not None else 'Google News'
                
                news.append({
                    'headline': headline,
                    'source_name': source_name,
                    'source_url': link.text or '#',
                    'date': date_str,
                    'live': True
                })
            
            if news:
                logger.info(f"Fetched {len(news)} live news articles for {domain}")
            return news
            
        except Exception as e:
            logger.warning(f"Live news fetch failed: {e}")
            return []
    
    def _get_hardcoded_news(self, domain: str) -> List[Dict]:
        """Fallback hardcoded industry news."""
        news_sources = {
            'manufacturing': [
                {'headline': 'Electronics manufacturing sees 17% growth in FY24', 'source_name': 'Economic Times', 'source_url': 'https://economictimes.indiatimes.com/industry/cons-products/electronics', 'date': '2024-04'},
                {'headline': 'PLI scheme attracts ₹1 lakh crore investment commitments', 'source_name': 'Business Standard', 'source_url': 'https://www.business-standard.com/economy/news/pli-scheme', 'date': '2024-03'},
            ],
            'technology': [
                {'headline': 'Indian IT sector revenue crosses $250 billion', 'source_name': 'NASSCOM', 'source_url': 'https://nasscom.in/knowledge-center/publications/', 'date': '2024-04'},
                {'headline': 'AI services demand grows 40% year-on-year', 'source_name': 'Mint', 'source_url': 'https://www.livemint.com/technology/tech-news', 'date': '2024-03'},
            ],
            'logistics': [
                {'headline': 'E-commerce logistics market to reach ₹50,000 crore by 2025', 'source_name': 'RedSeer', 'source_url': 'https://redseer.com/reports/india-ecommerce-logistics-market', 'date': '2024-02'},
                {'headline': 'Express delivery segment grows 25% in FY24', 'source_name': 'Economic Times', 'source_url': 'https://economictimes.indiatimes.com/industry/transportation/shipping-transport', 'date': '2024-04'},
            ],
            'consumer': [
                {'headline': 'D2C brands capture 15% of online retail market', 'source_name': 'Inc42', 'source_url': 'https://inc42.com/datalab/indian-d2c-startups/', 'date': '2024-03'},
            ],
            'healthcare': [
                {'headline': 'India pharma exports grow 9% to $27.3 billion', 'source_name': 'Pharmexcil', 'source_url': 'https://pharmexcil.com/exports/', 'date': '2024-04'},
            ],
            'infrastructure': [
                 {'headline': 'Infra spending to double in 3 years', 'source_name': 'Economic Times', 'source_url': 'https://economictimes.indiatimes.com/', 'date': '2024-01'},
            ],
            'chemicals': [
                 {'headline': 'Specialty chemicals export rise 12%', 'source_name': 'Chemical Weekly', 'source_url': 'https://www.chemicalweekly.com/', 'date': '2024-02'},
            ],
            'automotive': [
                 {'headline': 'EV sales cross 1 million mark', 'source_name': 'Autocar Pro', 'source_url': 'https://www.autocarpro.in/', 'date': '2024-03'},
            ]
        }
        
        domain_lower = domain.lower()
        for key in news_sources:
            if key in domain_lower or domain_lower in key:
                return news_sources[key]
        return []

    def _compile_outlook(self, domain: str, market_data: Dict) -> Dict:
        """Compile industry outlook."""
        drivers = market_data.get('key_drivers', [])[:3]
        sources = market_data.get('sources', [])
        
        outlook = {
            'summary': f"{market_data.get('industry_name', 'Industry')} is expected to grow at "
                       f"{market_data.get('cagr', 'N/A')} CAGR, driven by {', '.join(drivers)}.",
            'drivers': drivers,
            'market_size': market_data.get('india_market_size', 'N/A'),
             'sources': [
                {'name': s.source_name, 'url': s.source_url} 
                for s in sources
            ] if sources else []
        }
        return outlook
    
    def save_to_markdown(self, company_name: str, output_path: str, results: Dict[str, Any]) -> str:
        """Save scraped data as markdown with actual URLs and FULL TEXT."""
        lines = [
            f"# Web Scraped Data: {company_name}",
            f"",
            f"*Generated: {time.strftime('%Y-%m-%d %H:%M')}*",
            "",
            "---",
            "",
        ]
        
        # Company Website Data
        lines.append("## Company Website Data")
        lines.append("")
        
        company_info = results.get('company_info', {})
        if company_info:
            for page_type, page_data in company_info.items():
                if isinstance(page_data, dict) and 'url' in page_data:
                    lines.append(f"### {page_type.replace('_', ' ').title()}")
                    lines.append(f"- **URL:** [{page_data['url']}]({page_data['url']})")
                    lines.append(f"- **Scraped:** {page_data.get('scraped_at', 'N/A')}")
                    lines.append("")
                    content = page_data.get('content', '')
                    if content:
                        lines.append(f"> {content}") # Full content no truncation
                    lines.append("")
        else:
            lines.append("*No company website data scraped*")
            lines.append("")
        
        # Market Data
        lines.append("---")
        lines.append("")
        lines.append("## Market Data")
        lines.append("")
        
        market_data = results.get('market_data', {})
        if market_data:
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Industry | {market_data.get('industry_name', 'N/A')} |")
            lines.append(f"| India Market Size | {market_data.get('india_market_size', 'N/A')} |")
            lines.append(f"| Global Market Size | {market_data.get('global_market_size', 'N/A')} |")
            lines.append(f"| CAGR | {market_data.get('cagr', 'N/A')} |")
            lines.append("")
            
            # Sources with actual URLs
            sources = market_data.get('sources', [])
            if sources:
                lines.append("### Data Sources")
                for src in sources:
                    lines.append(f"- [{src.source_name}]({src.source_url}) - {src.metric}")
            lines.append("")
        
        # Industry News
        lines.append("---")
        lines.append("")
        lines.append("## Industry News")
        lines.append("")
        
        news = results.get('news', [])
        if news:
            for article in news:
                lines.append(f"- **{article.get('headline', '')}**")
                lines.append(f"  - Source: [{article.get('source_name')}]({article.get('source_url', '#')})")
                lines.append(f"  - Date: {article.get('date', 'N/A')}")
            lines.append("")
        else:
            lines.append("*No news articles found*")
            lines.append("")
        
        # All Sources Used
        lines.append("---")
        lines.append("")
        lines.append("## All Sources Used")
        lines.append("")
        
        sources_used = results.get('sources_used', [])
        if sources_used:
            for src in sources_used:
                lines.append(f"- **{src.get('name', 'Unknown')}**")
                lines.append(f"  - URL: [{src.get('url')}]({src.get('url')})")
                lines.append(f"  - Type: {src.get('type', 'N/A')}")
                lines.append(f"  - Accessed: {src.get('access_date', 'N/A')}")
        else:
            lines.append("*No sources recorded*")
        lines.append("")
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Scraped data saved to: {output_path}")
        return output_path

if __name__ == "__main__":
    scraper = WebScraper(use_playwright=True)
    print("Testing Smart Page Discovery on Ksolves...")
    data = scraper.scrape_all_sources("Ksolves", "https://www.ksolves.com", "technology")
    print(f"\nScraped {len(data['company_info'])} pages.")
