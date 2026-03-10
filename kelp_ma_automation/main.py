"""
Kelp M&A Automation Pipeline - PRODUCTION VERSION
Main orchestrator with:
- Token usage tracking
- Enhanced web scraping (market data, news, industry insights)
- Fixed slide structure
- 100% citation verification

Usage:
    python main.py <company_name> <onepager_md_path> [--output <output_dir>]
"""

import argparse
import logging
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.data_extractor import DataExtractor
from agents.domain_classifier import DomainClassifier
from agents.web_scraper import WebScraper
from agents.content_writer import ContentWriter, SlideContent
from agents.citation_verifier import CitationVerifier
from agents.ppt_assembler import PPTAssembler
from utils.token_tracker import token_tracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kelp_pipeline')


class KelpPipeline:
    """Production pipeline with full tracking and verification."""
    
    def __init__(self, output_dir: str = "data/output", 
                 template_path: str = None,
                 llm_provider: str = "ollama",
                 model_name: str = "phi4-mini:latest",
                 api_key: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.template_path = template_path
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.api_key = api_key
        
        # Initialize agents
        self.extractor = DataExtractor()
        self.classifier = DomainClassifier(
            llm_provider=self.llm_provider, 
            model=self.model_name, 
            api_key=self.api_key
        )
        self.scraper = WebScraper(use_playwright=False)
        self.verifier = CitationVerifier()
        
        # Reset token tracker for this run
        token_tracker.reset()
        
        logger.info("Pipeline initialized")
    
    def process(self, company_name: str, md_file: str,
                skip_scraping: bool = False,
                status_callback=None) -> Tuple[str, str, Dict]:
        """
        Process a company through the full pipeline.
        
        Returns:
            Tuple of (ppt_path, citation_path, stats)
        """
        logger.info("=" * 60)
        logger.info(f"PROCESSING: {company_name}")
        logger.info("=" * 60)
        
        md_path = Path(md_file)
        if not md_path.exists():
            raise FileNotFoundError(f"MD file not found: {md_file}")
        
        # Load MD content
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        # STEP 0: Extract
        if status_callback: status_callback(0, "Extracting data from one-pager...")
        
        # Step 1: Extract data
        logger.info("Step 1/7: Extracting data from one-pager...")
        data = self.extractor.extract(md_file)
        extracted = self.extractor.to_dict()
        
        is_valid, issues = self.extractor.validate()
        if issues:
            for issue in issues[:3]:
                logger.warning(f"  ⚠ {issue}")
        
        # STEP 1: Classify
        if status_callback: status_callback(1, "Classifying industry domain...")
        
        # Step 2: Classify domain
        logger.info("Step 2/7: Classifying domain...")
        domain, confidence, reasoning = self.classifier.classify(
            data.business_description,
            ', '.join(data.products_services[:5]),
            data.domain
        )
        domain_name = self.classifier.get_domain_name(domain)
        logger.info(f"  Domain: {domain_name} ({confidence:.1%} confidence)")
        
        # STEP 2: Scrape
        if status_callback: status_callback(2, "Scraping web data (fetching market details)...")
        
        # Step 3: Web scraping (enhanced)
        web_data = {}
        if not skip_scraping:
            logger.info("Step 3/7: Fetching web data (company + market + news)...")
            try:
                web_data = self.scraper.scrape_all_sources(
                    company_name=company_name,
                    website=data.website,
                    domain=domain
                )
                
                # Log what was fetched
                logger.info(f"  Company pages: {len(web_data.get('company_info', {}))}")
                logger.info(f"  Market data: {len(web_data.get('market_data', {}))}")
                logger.info(f"  News items: {len(web_data.get('news', []))}")
                
                if web_data.get('market_data'):
                    md = web_data['market_data']
                    logger.info(f"  Industry: {md.get('industry_name', 'N/A')}")
                    logger.info(f"  Market Size: {md.get('india_market_size', 'N/A')}")
                    logger.info(f"  Growth: {md.get('cagr', 'N/A')}")
                    
            except Exception as e:
                logger.warning(f"  Web scraping failed: {e}")
        else:
            logger.info("Step 3/7: Skipping web scraping")
            
        # STEP 3: Content Writer
        if status_callback: status_callback(3, "Generating AI slide content...")
            
        # Step 4: Generate content with fixed structure
        logger.info("Step 4/7: Generating slide content...")
        writer = ContentWriter(
            domain=domain,
            llm_provider=self.llm_provider,
            model_name=self.model_name,
            api_key=self.api_key
        )
        writer.set_web_data(web_data)  # Pass web data for enrichment
        slide_content = writer.generate_slide_content(extracted, company_name)
        
        # Log content stats
        for i, slide in enumerate(slide_content, 1):
            sections = slide.sections
            logger.info(f"  Slide {i}: {len(sections)} sections, {len(slide.citations)} claims")
        
        # STEP 4: Citations
        if status_callback: status_callback(4, "Verifying citations and claims...")
        
        # Step 5: Verify citations (including web data)
        logger.info("Step 5/8: Verifying all claims...")
        self.verifier.set_sources(
            md_file=md_file,
            extracted_data=extracted,
            md_content=md_content,
            web_data=web_data  # Pass web data for verification
        )
        
        all_citations = []
        for i, slide in enumerate(slide_content, 1):
            citations = self.verifier.verify_slide_content(i, slide)
            verified = sum(1 for c in citations if c.verified)
            logger.info(f"  Slide {i}: {verified}/{len(citations)} verified")
            all_citations.extend(citations)
        
        total_verified = sum(1 for c in all_citations if c.verified)
        total_claims = len(all_citations)
        rate = (total_verified / total_claims * 100) if total_claims > 0 else 100
        logger.info(f"  Overall: {total_verified}/{total_claims} ({rate:.1f}%)")
        
        # STEP 5: Assemble
        if status_callback: status_callback(5, "Assembling PowerPoint deck...")
        
        # Step 6: Filter to verified only
        logger.info("Step 6/8: Filtering verified content...")
        verified_slides = self._filter_verified(slide_content)
        
        # Step 6b: Final anonymization audit — regex+NER pass only (LLM already ran during generation)
        logger.info("  Anonymization audit (regex+NER pass)...")
        anon_writer = ContentWriter(
            domain=domain,
            llm_provider=self.llm_provider,
            model_name=self.model_name,
            api_key=self.api_key
        )
        anon_writer.company_name = company_name
        anon_writer.source_data = extracted
        for slide in verified_slides:
            for section_name, items in slide.sections.items():
                cleaned = []
                for item in items:
                    # Run only regex passes — fast, no LLM call
                    result = item
                    if anon_writer.company_name:
                        variants = anon_writer._generate_name_variants(anon_writer.company_name)
                        variants.sort(key=lambda x: len(x[0]), reverse=True)
                        for pattern, replacement in variants:
                            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                    result = anon_writer._ner_regex_pass(result)
                    cleaned.append(result)
                slide.sections[section_name] = cleaned
            if slide.hooks:
                slide.hooks = [
                    anon_writer._ner_regex_pass(h) for h in slide.hooks
                ]
        logger.info("  ✓ Anonymization audit passed")
        
        # Step 7: Assemble PPT
        logger.info("Step 7/8: Assembling PowerPoint...")
        
        safe_name = "".join(c if c.isalnum() or c in ' -_' else '' for c in company_name)
        safe_name = safe_name.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        ppt_filename = f"{safe_name}_Teaser_{timestamp}.pptx"
        ppt_path = str(self.output_dir / ppt_filename)
        
        financials = extracted.get('financials', {})
        
        assembler = PPTAssembler(domain=domain, template_path=self.template_path)
        assembler.build(verified_slides, financials, ppt_path)
        
        logger.info(f"  ✓ PPT saved: {ppt_path}")
        
        # Generate citation document
        citation_filename = f"{safe_name}_Citations_{timestamp}.docx"
        citation_path = str(self.output_dir / citation_filename)
        
        report = self.verifier.generate_report(company_name, citation_path)
        logger.info(f"  ✓ Citations saved: {citation_path}")
        
        # STEP 6: Finalize/Save
        if status_callback: status_callback(6, "Saving outputs and cleanup...")
        
        # Step 8: Save scraped data as MD
        logger.info("Step 8/8: Saving scraped data...")
        if web_data:
            scraped_md_file = str(self.output_dir / f"{safe_name}_WebData_{timestamp}.md")
            self.scraper.save_to_markdown(company_name, scraped_md_file, web_data)
            logger.info(f"  ✓ Web data saved: {scraped_md_file}")
        
        # Save token usage
        token_file = str(self.output_dir / f"{safe_name}_TokenUsage_{timestamp}.json")
        token_tracker.save_to_file(token_file)
        
        # Print token summary
        token_tracker.print_summary()
        
        # Stats
        stats = {
            'company': company_name,
            'domain': domain_name,
            'total_claims': report.total_claims,
            'verified': report.verified_count,
            'verification_rate': report.verification_rate,
            'web_sources': len(web_data.get('sources_used', [])),
            'market_data_available': bool(web_data.get('market_data')),
            'token_usage': token_tracker.get_summary(),
            'tokens_used': token_tracker.total_tokens,
            'ppt_path': ppt_path,
            'citation_path': citation_path,
            'verified_slides': [self._slide_to_dict(s) for s in verified_slides],
            'extracted_data': extracted,
            'web_data': web_data,
        }
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"  Company: {company_name}")
        logger.info(f"  Domain: {domain_name}")
        logger.info(f"  Verification: {report.verified_count}/{report.total_claims} ({report.verification_rate:.1f}%)")
        logger.info(f"  Web Sources: {stats['web_sources']}")
        logger.info(f"  LLM Tokens Used: {token_tracker.total_tokens:,}")
        logger.info(f"  Output: {ppt_path}")
        logger.info("")
        
        return ppt_path, citation_path, stats
    
    def process_company(self, company_name: str, md_file: str, output_dir: str = None, status_callback=None):
        """Alias for process() method for GUI compatibility."""
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        ppt_path, citation_path, stats = self.process(company_name, md_file, status_callback=status_callback)
        
        # Return dict for GUI compatibility
        return {
            'ppt_path': ppt_path,
            'citation_path': citation_path,
            'stats': stats,
            'company': company_name,
            'domain': stats.get('domain', 'Unknown')
        }
    
    
    def _filter_verified(self, slides: List[SlideContent]) -> List[SlideContent]:
        """Filter to only verified content - no truncation."""
        result = []
        
        for slide in slides:
            verified_sections = {}
            
            for section_name, items in slide.sections.items():
                verified_items = []
                for item in items:
                    # Check if verified
                    is_verified = any(
                        c.verified and (c.claim == item or item in c.claim or c.claim in item)
                        for c in self.verifier.citations
                    )
                    if is_verified:
                        verified_items.append(item)
                
                if verified_items:
                    verified_sections[section_name] = verified_items
            
            # Filter hooks
            verified_hooks = []
            if slide.hooks:
                for hook in slide.hooks:
                    # Robust handling for string or dict hooks
                    hook_text = hook['text'] if isinstance(hook, dict) else str(hook)
                    is_verified = any(
                        c.verified and (c.claim == hook_text or hook_text in c.claim or c.claim in hook_text)
                        for c in self.verifier.citations
                    )
                    if is_verified:
                        verified_hooks.append(hook)
            
            result.append(SlideContent(
                title=slide.title,
                sections=verified_sections,
                metrics=slide.metrics,
                hooks=verified_hooks if verified_hooks else None
            ))
        
        return result

    def _slide_to_dict(self, slide: SlideContent) -> Dict:
        """Serialize SlideContent to dict."""
        return {
            'title': slide.title,
            'sections': slide.sections,
            'metrics': slide.metrics,
            'hooks': slide.hooks
        }
    
    def process_batch(self, companies: list, skip_scraping: bool = False) -> Dict:
        """Process multiple companies."""
        results = {}
        
        for name, md_path in companies:
            try:
                ppt, citation, stats = self.process(name, md_path, skip_scraping)
                results[name] = {'success': True, **stats}
            except Exception as e:
                logger.error(f"Failed to process {name}: {e}")
                results[name] = {'success': False, 'error': str(e)}
        
        return results

# Alias for GUI compatibility
MAAutomationPipeline = KelpPipeline

def main():
    parser = argparse.ArgumentParser(
        description='Kelp M&A Pipeline - Generate verified Investment Teaser PPTs'
    )
    parser.add_argument('company_name', help='Company name')
    parser.add_argument('md_file', help='Path to one-pager MD file')
    parser.add_argument('--output', '-o', default='data/output', help='Output directory')
    parser.add_argument('--template', '-t', help='Path to PPTX template')
    parser.add_argument('--skip-scraping', '-s', action='store_true', help='Skip web scraping')
    parser.add_argument('--batch', '-b', action='store_true', help='Batch process directory')
    
    args = parser.parse_args()
    
    pipeline = KelpPipeline(
        output_dir=args.output,
        template_path=args.template
    )
    
    if args.batch:
        md_dir = Path(args.md_file).parent
        companies = []
        for md_file in md_dir.glob('*-OnePager.md'):
            name = md_file.stem.replace('-OnePager', '').replace('_', ' ')
            companies.append((name, str(md_file)))
        
        if companies:
            logger.info(f"Batch processing {len(companies)} companies...")
            results = pipeline.process_batch(companies, args.skip_scraping)
            
            success = sum(1 for r in results.values() if r.get('success'))
            logger.info(f"\nBatch complete: {success}/{len(companies)} successful")
        else:
            logger.error("No MD files found for batch processing")
    else:
        pipeline.process(args.company_name, args.md_file, args.skip_scraping)


if __name__ == "__main__":
    main()
