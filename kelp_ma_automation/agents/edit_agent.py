"""
Edit Agent (Agent 8) - Interactive AI Editor for PPT Content
Capable of refining tone, adding content, and updating metrics based on user prompts.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

class EditAgent:
    def __init__(self, llm_provider='ollama', model_name='qwen2.5:latest', api_key=None):
        self.provider = llm_provider
        self.model = model_name
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

    def _to_serializable(self, obj: Any, depth: int = 0) -> Any:
        """Recursively convert and truncate for LLM context."""
        if isinstance(obj, str):
            # Truncate very long strings to keep context manageable for 3B/8B models
            return obj[:3000] + "..." if len(obj) > 3005 else obj
        if isinstance(obj, (int, float, bool, type(None))):
            return obj
        if isinstance(obj, dict):
            return {str(k): self._to_serializable(v, depth + 1) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._to_serializable(v, depth + 1) for v in obj]
        if hasattr(obj, '__dict__'):
            return self._to_serializable(obj.__dict__, depth + 1)
        return str(obj)

    def edit_content(self, user_prompt: str, slide_content: List[Dict], 
                     one_pager_data: Dict, web_data: Dict) -> List[Dict]:
        """
        Process user request to edit presentation content.
        """
        # Prepare context (Clean up and truncate)
        clean_web_data = self._to_serializable(web_data)
        clean_one_pager = self._to_serializable(one_pager_data)
        clean_slides = self._to_serializable(slide_content)
        
        prompt = f"""You are an elite M&A Analyst. Your task: Modify the PPT content based on: "{user_prompt}"

### INPUT DATA SOURCES:
1. ONE-PAGER (Internal): {json.dumps(clean_one_pager, default=str)}
2. WEB DATA (Research): {json.dumps(clean_web_data, default=str)}

### CURRENT PPT CONTENT (3 SLIDES):
{json.dumps(clean_slides, indent=2, default=str)}

### CRITICAL INSTRUCTIONS:
1. PRESERVE STRUCTURE: You MUST return exactly 3 slide objects in a JSON array.
2. PRESERVE DATA: Do NOT delete existing data keys (like "Key Shareholders" in Slide 2 "sections", or "metrics") unless explicitly asked. Slide 2 REQUIRES the "Key Shareholders" list for the Pie Chart to appear.
3. TONE: Professional M&A style. Use "The Company" or "The Target".
4. ENHANCEMENT: If the user asks to "enhance" or "add data", look through both sources and inject high-value bullet points.
5. NO HALLUCINATION: Only use provided facts.

Return ONLY the updated JSON array of 3 slides. No intro/outro.
"""
        
        result = self._call_llm(prompt)
        
        if result:
            try:
                # Extract JSON
                json_match = re.search(r'\[\s*\{.*\}\s*\]', result, re.DOTALL)
                if json_match:
                    updated_content = json.loads(json_match.group())
                else:
                    updated_content = json.loads(result)
                    
                if isinstance(updated_content, list) and len(updated_content) >= 3:
                    # Smart Merge: Prevent tiny models from accidentally deleting required data (like Pie Chart/Metrics)
                    for i in range(min(len(slide_content), len(updated_content))):
                        orig_slide = slide_content[i]
                        new_slide = updated_content[i]
                        
                        # Restore missing metrics (Chart Data)
                        if 'metrics' in orig_slide and 'metrics' not in new_slide:
                            new_slide['metrics'] = orig_slide['metrics']
                        
                        # Restore missing Critical Sections
                        if 'sections' in orig_slide:
                            if 'sections' not in new_slide:
                                new_slide['sections'] = orig_slide['sections']
                            else:
                                # Ensure Key Shareholders/KPIs aren't dropped in Slide 2
                                for crucial_key in ['Key Shareholders', 'Financial KPIs']:
                                    if crucial_key in orig_slide['sections'] and crucial_key not in new_slide['sections']:
                                        new_slide['sections'][crucial_key] = orig_slide['sections'][crucial_key]
                        
                        # Restore missing hooks in Slide 3
                        if 'hooks' in orig_slide and 'hooks' not in new_slide:
                            new_slide['hooks'] = orig_slide['hooks']
                            
                    return updated_content
            except Exception as e:
                self.logger.error(f"Failed to parse updated content: {e}")
                
        return slide_content

    def _call_llm(self, prompt: str) -> Optional[str]:
        if self.provider == 'ollama':
            try:
                import ollama
                response = ollama.generate(
                    model=self.model,
                    prompt=prompt,
                    options={"temperature": 0.2, "num_predict": 2048}
                )
                return response.get('response', '')
            except Exception as e:
                self.logger.error(f"Ollama call failed: {e}")
        elif self.provider == 'gemini':
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                self.logger.error(f"Gemini call failed: {e}")
        return None
