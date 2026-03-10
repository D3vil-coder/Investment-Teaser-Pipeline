"""
Domain Classifier Agent (Agent 1)
Classifies companies into one of 8 domains using Ollama phi4-mini.
Falls back to keyword matching if LLM unavailable.
"""

import re
import json
import logging
from typing import Tuple, Dict, List, Optional
from pathlib import Path

from utils.llm_client import LlmClient
    
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Domain definitions with keywords for fallback matching
DOMAIN_KEYWORDS = {
    'manufacturing': {
        'name': 'Manufacturing & Industrials',
        'keywords': ['manufacturing', 'production', 'plant', 'facility', 'industrial', 
                     'oem', 'b2b', 'fabrication', 'assembly', 'machining', 'factory',
                     'electronics', 'components', 'hardware']
    },
    'technology': {
        'name': 'Technology & IT Services',
        'keywords': ['software', 'saas', 'platform', 'cloud', 'digital', 'ai', 'ml',
                     'development', 'consulting', 'integration', 'it services', 'tech',
                     'data', 'analytics', 'salesforce', 'odoo', 'erp', 'crm']
    },
    'logistics': {
        'name': 'Logistics & Supply Chain',
        'keywords': ['logistics', 'supply chain', 'warehousing', 'transportation',
                     'distribution', 'freight', '3pl', 'last mile', 'express', 'delivery',
                     'shipping', 'cargo', 'courier']
    },
    'consumer': {
        'name': 'Consumer Brands (D2C/B2C)',
        'keywords': ['brand', 'consumer', 'd2c', 'e-commerce', 'retail', 'wellness',
                     'fmcg', 'marketplace', 'lifestyle', 'personal care', 'food',
                     'beverage', 'fashion', 'beauty']
    },
    'healthcare': {
        'name': 'Healthcare & Pharma',
        'keywords': ['pharma', 'pharmaceutical', 'healthcare', 'medical', 'biotech',
                     'diagnostics', 'hospital', 'therapeutic', 'formulation', 'drug',
                     'medicine', 'clinical', 'api', 'generic']
    },
    'infrastructure': {
        'name': 'Infrastructure & Real Estate',
        'keywords': ['construction', 'infrastructure', 'real estate', 'developer',
                     'epc', 'project', 'contractor', 'builder', 'roads', 'bridges',
                     'housing', 'commercial']
    },
    'chemicals': {
        'name': 'Chemicals & Specialty Materials',
        'keywords': ['chemical', 'polymer', 'resin', 'specialty', 'formulation',
                     'additive', 'coating', 'petrochemical', 'industrial chemicals',
                     'paints', 'adhesives']
    },
    'automotive': {
        'name': 'Automotive & Components',
        'keywords': ['automotive', 'auto components', 'forging', 'casting', 'oem',
                     'tier-1', 'aftermarket', 'vehicle', 'car', 'truck', 'two-wheeler',
                     'engine', 'transmission']
    }
}


class DomainClassifier:
    """
    Classifies companies into domains using LLM (phi4-mini via Ollama).
    Falls back to keyword matching if LLM is unavailable.
    """
    
    def __init__(self, llm_provider: str = "ollama", model: str = "phi4-mini:latest", api_key: str = None):
        self.llm = LlmClient(provider=llm_provider, model=model, api_key=api_key)
        self.ollama_available = self.llm.available if llm_provider == "ollama" else False
        self.gemini_available = self.llm.available if llm_provider == "gemini" else False
    
    def classify(self, business_description: str, products: str = "", 
                 domain_hint: str = "") -> Tuple[str, float, str]:
        """
        Classify company into a domain.
        
        Args:
            business_description: The company's business description
            products: Products/services offered
            domain_hint: Optional domain hint from MD file
            
        Returns:
            Tuple of (domain_key, confidence, reasoning)
        """
        # If we have a domain hint from the MD file, use it with high confidence
        if domain_hint:
            normalized = self._normalize_domain(domain_hint)
            if normalized:
                logger.info(f"Using domain from MD file: {normalized}")
                return normalized, 0.95, f"Domain specified in data pack: {domain_hint}"
        
        # Combine text for classification
        combined_text = f"{business_description}\n\nProducts/Services: {products}"
        
        if self.llm.available:
            return self._classify_with_llm(combined_text)
        else:
            return self._classify_with_keywords(combined_text)
    
    def _normalize_domain(self, domain_str: str) -> Optional[str]:
        """Normalize domain string to our domain key."""
        domain_lower = domain_str.lower()
        
        for key, info in DOMAIN_KEYWORDS.items():
            if key in domain_lower or any(kw in domain_lower for kw in info['keywords'][:3]):
                return key
        
        # Direct mappings
        mappings = {
            'manufacturing': 'manufacturing',
            'technology': 'technology',
            'it services': 'technology',
            'logistics': 'logistics',
            'consumer': 'consumer',
            'd2c': 'consumer',
            'healthcare': 'healthcare',
            'pharma': 'healthcare',
            'infrastructure': 'infrastructure',
            'real estate': 'infrastructure',
            'chemicals': 'chemicals',
            'automotive': 'automotive',
        }
        
        for pattern, key in mappings.items():
            if pattern in domain_lower:
                return key
        
        return None
    
    def _classify_with_llm(self, text: str) -> Tuple[str, float, str]:
        """Classify using Ollama LLM."""
        prompt = f"""You are a domain classifier for M&A due diligence.

Based on the company description below, classify the company into ONE of these domains:
1. manufacturing - Manufacturing & Industrials (production, facilities, B2B, OEM)
2. technology - Technology & IT Services (software, SaaS, cloud, digital)
3. logistics - Logistics & Supply Chain (warehousing, transportation, delivery)
4. consumer - Consumer Brands (D2C, e-commerce, retail, FMCG)
5. healthcare - Healthcare & Pharma (pharma, medical, biotech, diagnostics)
6. infrastructure - Infrastructure & Real Estate (construction, EPC, developer)
7. chemicals - Chemicals & Specialty Materials (polymers, resins, coatings)
8. automotive - Automotive & Components (auto parts, forging, casting, OEM)

Company Information:
{text[:2000]}

Respond ONLY with a JSON object (no markdown, no explanation):
{{"domain": "<domain_key>", "confidence": <0.0 to 1.0>, "reasoning": "<brief explanation>"}}"""

        try:
            response_text = self.llm.generate(prompt, temperature=0.1, max_tokens=200, task="domain_classification")
            if not response_text:
                return self._classify_with_keywords(text)
            
            # Try to parse JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                domain = result.get('domain', '').lower()
                confidence = float(result.get('confidence', 0.5))
                reasoning = result.get('reasoning', 'LLM classification')
                
                # Validate domain
                if domain in DOMAIN_KEYWORDS:
                    return domain, confidence, reasoning
            
            # Fallback to keyword if parsing fails
            logger.warning("LLM response parsing failed, using keywords")
            return self._classify_with_keywords(text)
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self._classify_with_keywords(text)
    
    def _classify_with_keywords(self, text: str) -> Tuple[str, float, str]:
        """Classify using keyword matching (fallback)."""
        text_lower = text.lower()
        
        scores = {}
        for domain_key, info in DOMAIN_KEYWORDS.items():
            score = 0
            matched_keywords = []
            for keyword in info['keywords']:
                count = text_lower.count(keyword.lower())
                if count > 0:
                    score += count
                    matched_keywords.append(keyword)
            scores[domain_key] = (score, matched_keywords)
        
        # Find best match
        best_domain = max(scores, key=lambda k: scores[k][0])
        best_score, matched = scores[best_domain]
        
        # Calculate confidence based on score distribution
        total_score = sum(s[0] for s in scores.values())
        if total_score > 0:
            confidence = min(0.9, best_score / total_score + 0.3)
        else:
            confidence = 0.5
        
        reasoning = f"Keyword matches: {', '.join(matched[:5])}"
        
        logger.info(f"Keyword classification: {best_domain} (confidence: {confidence:.2f})")
        return best_domain, confidence, reasoning
    
    def get_domain_info(self, domain_key: str) -> Dict:
        """Get full domain information."""
        return DOMAIN_KEYWORDS.get(domain_key, {})
    
    def get_domain_name(self, domain_key: str) -> str:
        """Get human-readable domain name."""
        return DOMAIN_KEYWORDS.get(domain_key, {}).get('name', domain_key.title())


# Test function
if __name__ == "__main__":
    import sys
    
    classifier = DomainClassifier()
    
    # Test with sample text
    test_cases = [
        ("Centum Electronics is a diversified electronics company specializing in high-technology solutions for defense, aerospace, and space sectors.", "Electronics Manufacturing Services", "Manufacturing"),
        ("Ksolves provides software development services including Salesforce, Data Science, and ERP implementations.", "Salesforce consulting, Data Engineering, AI/ML", ""),
        ("Gati provides express distribution and supply chain solutions across India.", "Express logistics, Warehousing, E-commerce logistics", ""),
        ("Ind-Swift manufactures pharmaceutical formulations and APIs.", "Generic medicines, API manufacturing", "Healthcare"),
        ("Kalyani Forge produces precision forged components for automotive industry.", "Forged components, Transmission parts, Engine components", ""),
    ]
    
    print("=== Domain Classification Test ===\n")
    for desc, products, hint in test_cases:
        domain, confidence, reasoning = classifier.classify(desc, products, hint)
        name = classifier.get_domain_name(domain)
        print(f"Input: {desc[:50]}...")
        print(f"Domain: {name} ({domain})")
        print(f"Confidence: {confidence:.2f}")
        print(f"Reasoning: {reasoning}")
        print("-" * 50)
