"""
Unified LLM Client Utility
Supports both Ollama and Google Gemini.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Tuple, List

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from utils.token_tracker import token_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LlmClient:
    """
    Unified client for interacting with LLMs (Ollama or Gemini).
    """
    
    def __init__(self, provider: str = "ollama", model: str = "phi4-mini:latest", api_key: str = None):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if the selected provider is available."""
        if self.provider == "ollama":
            if not OLLAMA_AVAILABLE:
                logger.warning("Ollama package not installed")
                return False
            try:
                models_response = ollama.list()
                if hasattr(models_response, 'models'):
                    models = models_response.models
                    model_names = [str(m.model) if hasattr(m, 'model') else str(m) for m in models]
                elif isinstance(models_response, dict):
                    models = models_response.get('models', [])
                    model_names = [m.get('name', '') if isinstance(m, dict) else str(m) for m in models]
                else:
                    model_names = []
                
                available = any(self.model in name or name in self.model for name in model_names)
                if available:
                    logger.info(f"Ollama provider initialized with model: {self.model}")
                else:
                    logger.warning(f"Ollama model {self.model} not found in local models.")
                return available
            except Exception as e:
                logger.warning(f"Ollama unavailable: {e}")
                return False
        
        elif self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                logger.warning("Google Generative AI package not installed")
                return False
            if not self.api_key:
                logger.warning("Gemini API key not provided")
                return False
            try:
                genai.configure(api_key=self.api_key)
                logger.info(f"Gemini provider initialized with model: {self.model} (API Key present)")
                return True
            except Exception as e:
                logger.warning(f"Gemini configuration failed: {e}")
                return False
        
        return False

    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2048, task: str = "general") -> Optional[str]:
        """Generate text using the selected LLM."""
        if not self.available:
            logger.error(f"{self.provider.capitalize()} LLM not available")
            return None
        
        if self.provider == "ollama":
            try:
                response = ollama.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                )
                text = response.get('response', '').strip()
                # Use real counts if available
                p_tokens = response.get('prompt_eval_count', 0)
                c_tokens = response.get('eval_count', 0)
                if p_tokens > 0:
                    token_tracker.track(task, self.model, p_tokens, c_tokens)
                else:
                    token_tracker.track_from_response(task, self.model, prompt, text)
                return text
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
                return None
        
        elif self.provider == "gemini":
            try:
                model = genai.GenerativeModel(self.model)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                text = response.text.strip()
                # Use real counts if available
                if hasattr(response, 'usage_metadata'):
                    p_tokens = response.usage_metadata.prompt_token_count
                    c_tokens = response.usage_metadata.candidates_token_count
                    token_tracker.track(task, self.model, p_tokens, c_tokens)
                else:
                    token_tracker.track_from_response(task, self.model, prompt, text)
                return text
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}")
                return None
        
        return None

    def anonymize_text(self, text: str, company_name: str) -> str:
        """Anonymize text by removing company-identifying information."""
        prompt = f"""You are an M&A anonymization expert.
Rewrite the following text to remove all company-identifying information:
- Replace "{company_name}" with "The Company" or "The Target"
- Replace specific location names with generic regions ("Northern India", "Metropolitan area")
- Keep all numbers, percentages, and metrics EXACTLY as stated
- Maintain professional M&A investment memo tone

Original Text:
{text}

Anonymized Text:"""

        result = self.generate(prompt, temperature=0.1, max_tokens=len(text) + 200, task="anonymization")
        if result:
            return result
        
        # Fallback simple anonymization
        return text.replace(company_name, "The Company")

    def generate_investment_hooks(self, domain: str, key_metrics: Dict[str, Any]) -> List[str]:
        """Generate investment highlight statements."""
        metrics_str = json.dumps(key_metrics, indent=2, default=str)
        prompt = f"""You are an M&A investment banker writing investment hooks.
Domain: {domain}
Key Metrics: {metrics_str}

Generate 3 compelling investment highlight statements for this company.
Each statement should be:
- One sentence, max 15 words
- Quantitative where possible
- Professional M&A tone
- ONLY return a JSON array of 3 strings.

Example: ["Industry-leading margins with 25%+ EBITDA", "Diversified revenue across 8 end-user industries"]"""

        result = self.generate(prompt, temperature=0.4, max_tokens=300, task="hook_generation")
        if result:
            try:
                json_match = re.search(r'\[.*?\]', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())[:3]
            except:
                pass
        return ["Strong operational capabilities", "Scale-ready business model", "Attractive growth opportunity"]

    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key bullet points from text."""
        prompt = f"""Extract {num_points} key bullet points from the text below.
Keep point concise (under 15 words). Return as JSON array of strings.

Text: {text[:2000]}"""
        result = self.generate(prompt, temperature=0.2, max_tokens=500, task="point_extraction")
        if result:
            try:
                json_match = re.search(r'\[.*?\]', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())[:num_points]
            except:
                pass
        return [s.strip() for s in text.split('.')[:num_points] if s.strip()]
