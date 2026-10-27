# Investment Teaser Pipeline

An experimental document-generation pipeline that turns a company one-pager into a three-slide investment teaser. The project combines structured extraction, industry classification, website discovery, optional local language-model generation, citation matching, and PowerPoint assembly. It was developed for the KELP AI General Championship at IIT Bombay.

**Example:** The repository includes [a sample PowerPoint](Sample%20Output.pptx) and company one-pagers such as [Centum](Centum-OnePager.md). The sample is an illustration, not an independently validated financial report.

## Pipeline

```text
Markdown company one-pager
  -> extract company and financial fields
  -> classify the industry and collect website/market context
  -> draft slide sections and investment highlights
  -> match claims to input, calculations or stored web references
  -> assemble a PowerPoint and citation report
```

The entry point is [`kelp_ma_automation/main.py`](kelp_ma_automation/main.py). It orchestrates the modules in [`agents/`](kelp_ma_automation/agents): extraction, classification, scraping, content writing, citation matching, and presentation assembly. The output consists of a `.pptx`, a citation report in `.docx`, and token-usage metadata. When available, scraped data is also saved as Markdown. The repository includes domain-specific image directories and PowerPoint templates.

The main pipeline initializes the scraper with Playwright disabled, so its normal path uses Requests-based discovery and fallback URL guesses. The scraper module also contains a Playwright path, but it is not enabled by the current main entry point. Some market data and associated source references are hard-coded in the scraper rather than retrieved live.

## Scope and limitations

- **Human review is required.** The citation module uses heuristic matching and marks some calculations or market claims as verified without proving that the text or value is correct. Its report is an aid for tracing claims, not independent fact-checking. Check financial figures, generated text, references, and the final presentation against primary sources before use.
- The content writer initializes the default Ollama client and falls back to rule-based text when the model is unavailable. Although the GUI offers provider and model controls, the current main pipeline does not pass those settings into the content writer. Do not assume selecting Gemini in the GUI changes the model used for generation.
- Local LLM inference does not make the whole workflow offline: website retrieval can send network requests. Avoid using sensitive or confidential one-pagers until the complete data flow, generated artifacts, and deployment environment have been reviewed.
- The repository includes minimum dependency versions but no locked environment. A fresh installation and complete end-to-end generation have not been independently reproduced for this README. The `requirements.txt` omits Streamlit even though the GUI imports it.

## Getting started

These commands describe the repository's intended setup and entry points; they have not been verified as a clean end-to-end run. Python, `pip`, and Git are required. Ollama and the `phi4-mini:latest` model are needed for the local LLM path. A network connection is needed to install dependencies and, unless scraping is skipped, for website retrieval.

```bash
git clone https://github.com/D3vil-coder/Investment-Teaser-Pipeline.git
cd Investment-Teaser-Pipeline/kelp_ma_automation
python -m pip install -r requirements.txt
```

For the Streamlit interface, install Streamlit separately because it is not currently listed in the requirements file:

```bash
python -m pip install streamlit
python -m streamlit run gui/app.py
```

The CLI accepts a company name and path to a Markdown one-pager. From the application directory, an included example is referenced by `../Centum-OnePager.md`:

```bash
python main.py "Centum" "../Centum-OnePager.md" --output data/output --skip-scraping
```

Omit `--skip-scraping` to allow website and market-context retrieval. Run `python main.py --help` for the arguments defined by the script. Both the GUI and CLI write files, and generation can take time depending on the selected model and available hardware.

## Repository guide

| Path | Purpose |
| --- | --- |
| [`kelp_ma_automation/main.py`](kelp_ma_automation/main.py) | Pipeline orchestration and CLI |
| [`kelp_ma_automation/gui/app.py`](kelp_ma_automation/gui/app.py) | Streamlit interface |
| [`kelp_ma_automation/agents/`](kelp_ma_automation/agents) | Extraction, scraping, content, citations and slide assembly |
| [`kelp_ma_automation/config/`](kelp_ma_automation/config) | Industry and model configuration |
| [`kelp_ma_automation/templates/`](kelp_ma_automation/templates) | Presentation templates |
| [`kelp_ma_automation/requirements.txt`](kelp_ma_automation/requirements.txt) | Declared Python dependencies |

## Next improvements

Wire provider and model selection through the full pipeline, add a locked and tested environment, compare generated claims against explicit source spans and values, replace or date hard-coded market data, and add end-to-end tests with public sample inputs and expected outputs.

