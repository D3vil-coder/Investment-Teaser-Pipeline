"""
KELP M&A Automation - Streamlit GUI
Professional GUI with Kelp branding and animated progress.
"""

import streamlit as st
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import tempfile

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Kelp Brand Colors
KELP_COLORS = {
    'primary': '#4B0082',      # Dark Indigo/Violet
    'secondary': '#FF1493',    # Pink
    'accent': '#00CED1',       # Cyan Blue
    'background': '#FFFFFF',   # White
    'text_dark': '#333333',    # Dark Grey
    'gradient': 'linear-gradient(135deg, #4B0082 0%, #FF1493 100%)',
}

def get_custom_css():
    """Kelp-branded custom CSS."""
    return f"""
    <style>
    /* Main container */
    .main {{
        background-color: {KELP_COLORS['background']};
    }}
    
    /* Header */
    .kelp-header {{
        background: {KELP_COLORS['gradient']};
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }}
    
    .kelp-header h1 {{
        color: white;
        margin: 0;
        font-family: Arial, sans-serif;
    }}
    
    .kelp-header p {{
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
    }}
    
    /* Cards */
    .stCard {{
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    /* Buttons */
    .stButton>button {{
        background: {KELP_COLORS['gradient']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(75, 0, 130, 0.4);
    }}
    
    /* Progress section */
    .progress-step {{
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background: #f8f9fa;
        border-left: 4px solid #ccc;
        color: #000 !important;
    }}
    
    .progress-step span {{
        color: #000 !important;
    }}
    
    .progress-step.active {{
        border-left-color: {KELP_COLORS['accent']};
        background: #e8f7fa;
        color: #000 !important;
    }}
    
    .progress-step.complete {{
        border-left-color: #28a745;
        background: #e8f5e9;
        color: #000 !important;
    }}
    
    .progress-step.error {{
        border-left-color: #dc3545;
        background: #fdecea;
        color: #000 !important;
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background-color: #f8f9fa;
    }}
    
    /* Cards & White Boxes */
    .stCard, .output-card, .progress-step, .stCard *, .output-card *, .progress-step * {{
        color: #1a1a1a !important; /* Extremely dark for maximum contrast */
    }}
    
    /* Output cards */
    .output-card {{
        background: #ffffff !important;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 1px solid #eee;
        border-left: 6px solid {KELP_COLORS['primary']};
    }}
    
    /* Interactive Editor Border */
    .editor-section {{
        border-top: 3px solid #f0f2f6;
        padding-top: 2rem;
        margin-top: 3rem;
    }}

    /* Web Data Preview Container - Vertical & Readable */
    .web-preview {{
        height: 500px;
        overflow-y: scroll;
        padding: 1.5rem;
        background: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #222 !important;
        white-space: pre-wrap;
    }}
    
    /* Footer */
    .kelp-footer {{
        text-align: center;
        color: #666;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 1px solid #eee;
        font-size: 0.9rem;
    }}
    </style>
    """


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'processing': False,
        'current_step': 0,
        'step_status': {},
        'output_files': [],
        'error': None,
        'company_name': '',
        'llm_provider': 'ollama',
        'ollama_model': 'phi4-mini:latest',
        'gemini_api_key': '',
        'gemini_model': 'gemini-2.0-flash',
        'pipeline_result': None,
        'ppt_path': '',
        'citation_path': '',
        'webdata_path': '',
        'chat_history': [],
        'current_slides': None,
        'edit_provider': 'ollama',
        'edit_model': 'qwen2.5:latest',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header():
    """Render Kelp-branded header."""
    st.markdown("""
    <div class="kelp-header">
        <h1>🌊 KELP M&A Automation</h1>
        <p>AI-Powered Investment Teaser Generator</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render settings sidebar."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # LLM Provider Selection
        st.markdown("### LLM Provider")
        llm_provider = st.radio(
            "Choose LLM:",
            ["ollama", "gemini"],
            index=0 if st.session_state.llm_provider == 'ollama' else 1,
            horizontal=True
        )
        st.session_state.llm_provider = llm_provider
        
        if llm_provider == 'ollama':
            st.markdown("---")
            st.markdown("#### Ollama Settings")
            st.session_state.ollama_model = st.selectbox(
                "Model:",
                ["phi4-mini:latest", "llama3.2:latest", "qwen2.5:latest", "qwen2.5:3b", "mistral:latest"],
                key="ollama_model_select"
            )
            st.info("💡 Ollama runs locally - no API key needed!")
        
        else:
            st.markdown("---")
            st.markdown("#### Gemini Settings")
            st.session_state.gemini_api_key = st.text_input(
                "API Key:",
                value=st.session_state.gemini_api_key,
                type="password",
                help="Get from https://aistudio.google.com/apikey",
                key="gemini_key_input"
            )
            st.session_state.gemini_model = st.selectbox(
                "Model:",
                [
                    "gemini-2.0-flash", 
                    "gemini-2.0-flash-lite-preview-02-05", 
                    "gemini-1.5-pro", 
                    "gemini-1.5-flash"
                ],
                key="gemini_model_select"
            )
        
        st.markdown("---")
        st.markdown("### Output Settings")
        output_dir = st.text_input(
            "Output Directory:",
            value="data/output",
            help="Where to save generated files"
        )
        
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 1rem;">
            <p>Kelp M&A Automation v2.0</p>
            <p>© 2026 Kelp M&A Team</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Reset All", use_container_width=True):
            st.session_state.pipeline_result = None
            st.session_state.company_name = ''
            st.rerun()
            
        return output_dir


def render_progress(steps, current_step, step_status):
    """Render animated progress steps."""
    step_emojis = {
        'pending': '⏳',
        'processing': '🔄',
        'complete': '✅',
        'error': '❌'
    }
    
    for i, step_name in enumerate(steps):
        status = step_status.get(i, 'pending')
        if i == current_step and status == 'pending':
            status = 'processing'
        
        emoji = step_emojis.get(status, '⏳')
        css_class = status
        
        st.markdown(f"""
        <div class="progress-step {css_class}">
            <span style="margin-right: 0.5rem;">{emoji}</span>
            <span>{step_name}</span>
        </div>
        """, unsafe_allow_html=True)


def run_pipeline(company_name: str, md_file_path: str, output_dir: str):
    """Run the M&A automation pipeline with progress updates."""
    from main import MAAutomationPipeline
    
    steps = [
        "📄 Extracting data from one-pager",
        "🔍 Classifying industry domain",
        "🌐 Scraping web data",
        "✍️ Generating slide content",
        "🔎 Verifying citations",
        "📊 Assembling PowerPoint",
        "💾 Saving outputs"
    ]
    
    progress_placeholder = st.empty()
    status_text = st.empty()
    
    step_status = {}
    
    try:
        # Initialize pipeline
        pipeline = MAAutomationPipeline(
            llm_provider=st.session_state.llm_provider,
            model_name=st.session_state.ollama_model if st.session_state.llm_provider == 'ollama' else st.session_state.gemini_model,
            api_key=st.session_state.gemini_api_key if st.session_state.llm_provider == 'gemini' else None
        )
        
        for i, step_name in enumerate(steps):
            step_status[i] = 'processing'
            
            with progress_placeholder.container():
                render_progress(steps, i, step_status)
            
            status_text.markdown(f"**{step_name}**")
            time.sleep(0.3)  # Small delay for visual effect
            
            # Execute step (simulated - actual integration below)
            step_status[i] = 'complete'
        
        # Actually run the pipeline
        result = pipeline.process_company(company_name, md_file_path, output_dir)
        
        # Final update
        with progress_placeholder.container():
            render_progress(steps, len(steps) - 1, step_status)
        
        status_text.success("✅ Pipeline completed successfully!")
        
        return result
        
    except Exception as e:
        step_status[len([s for s in step_status.values() if s == 'complete'])] = 'error'
        status_text.error(f"❌ Error: {str(e)}")
        st.exception(e)
        return None


def render_output_section(result):
    """Render output files section."""
    if not result:
        return
    
    st.markdown("---")
    st.markdown("## 📁 Generated Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="output-card">
            <h4>📊 Investment Teaser</h4>
            <p>PowerPoint presentation ready for download</p>
        </div>
        """, unsafe_allow_html=True)
        
        if result.get('ppt_path') and os.path.exists(result['ppt_path']):
            with open(result['ppt_path'], 'rb') as f:
                st.download_button(
                    label="⬇️ Download PPT",
                    data=f.read(),
                    file_name=os.path.basename(result['ppt_path']),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
    
    with col2:
        st.markdown("""
        <div class="output-card">
            <h4>📋 Citation Report</h4>
            <p>Full source citations document</p>
        </div>
        """, unsafe_allow_html=True)
        
        if result.get('citation_path') and os.path.exists(result['citation_path']):
            with open(result['citation_path'], 'rb') as f:
                st.download_button(
                    label="⬇️ Download Citations",
                    data=f.read(),
                    file_name=os.path.basename(result['citation_path']),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    
    # Metrics
    if result.get('stats'):
        stats = result['stats']
        st.markdown("---")
        st.markdown("### 📈 Pipeline Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Verification Rate", f"{stats.get('verification_rate', 0):.1f}%")
        with col2:
            st.metric("Total Claims", stats.get('total_claims', 0))
        with col3:
            st.metric("Web Sources", stats.get('web_sources', 0))
        with col4:
            st.metric("LLM Tokens", f"{stats.get('tokens_used', 0):,}")
    
    # NEW: Result Explorer Tabs
    st.markdown("---")
    st.markdown("### 🔍 Result Explorer")
    
    tab1, tab2, tab3 = st.tabs(["📄 Citations & Verification", "🌐 Web Data & Insights", "🎯 Content Summary"])
    
    with tab1:
        st.markdown("#### Citation Verification Report")
        cit_path = st.session_state.citation_path
        if cit_path and os.path.exists(cit_path):
             st.success(f"Citations verified and saved to Word document.")
             st.info("The document contains full source mapping for every claim in the presentation.")
        
        # Show a summary table if possible
        if result.get('stats'):
            s = result['stats']
            st.table({
                "Metric": ["Total Claims", "Verified Claims", "Verification Rate", "Web Sources Used"],
                "Value": [str(s['total_claims']), str(s['verified']), f"{s['verification_rate']:.1f}%", str(s['web_sources'])]
            })

    with tab2:
        st.markdown("#### Scraped Company & News Data")
        # Try to find the MD file
        output_dir = os.path.dirname(st.session_state.ppt_path) if st.session_state.ppt_path else "data/output"
        files = os.listdir(output_dir)
        company_slug = result.get('company', '').replace(' ', '_')
        wd_file = next((f for f in files if company_slug in f and '_WebData_' in f), None)
        
        if wd_file:
            wd_path = os.path.join(output_dir, wd_file)
            st.session_state.webdata_path = wd_path
            with open(wd_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            st.markdown("#### Research Insights (Vertical Document)")
            st.markdown(f'''
                <div class="web-preview">
{md_content}
                </div>
            ''', unsafe_allow_html=True)
            
            with open(wd_path, 'rb') as f:
                st.download_button("⬇️ Download Full Web Data (.md)", f.read(), wd_file, mime="text/markdown")
        else:
            st.warning("Web data file not found in output directory.")

    with tab3:
        st.markdown(f"#### Content Overview: {result.get('company')}")
        st.write(f"**Industry Domain:** {result.get('domain', 'N/A')}")
        if result.get('stats') and 'token_usage' in result['stats']:
            t = result['stats']['token_usage']
            st.json(t)
    
    # AI Edit Assistant Section
    render_edit_chat(result)

def render_edit_chat(result):
    """Render the AI Chat Editor for real-time PPT updates."""
    st.markdown('<div class="editor-section">', unsafe_allow_html=True)
    st.markdown("### 💬 AI Edit Assistant")
    
    # Provider Settings for Edit Agent Specifically
    with st.expander("🛠️ Edit Agent Settings"):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.edit_provider = st.radio(
                "Chat Provider:", ["ollama", "gemini"], 
                index=0 if st.session_state.edit_provider == 'ollama' else 1,
                horizontal=True, key="edit_provider_radio"
            )
        with col2:
            if st.session_state.edit_provider == 'ollama':
                st.session_state.edit_model = st.selectbox(
                    "Chat Model:", 
                    ["qwen2.5:3b", "qwen2.5:latest", "phi4-mini:latest", "llama3.2:latest"],
                    key="edit_model_select"
                )
            else:
                st.session_state.edit_model = st.selectbox(
                    "Chat Model:", 
                    ["gemini-2.0-flash", "gemini-1.5-flash"],
                    key="edit_model_select_gem"
                )
    
    if not st.session_state.pipeline_result:
        st.warning("Please generate a teaser first to use the Edit Assistant.")
        return

    # Initialize slides in session state if not already there
    if st.session_state.current_slides is None:
        st.session_state.current_slides = result.get('stats', {}).get('verified_slides', [])

    # Chat Display
    chat_container = st.container(height=300)
    for msg in st.session_state.chat_history:
        with chat_container.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ex: 'Make the growth points more aggressive' or 'Summarize recent milestones'"):
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Call Edit Agent
        from agents.edit_agent import EditAgent
        from agents.ppt_assembler import PPTAssembler
        from types import SimpleNamespace
        
        agent = EditAgent(
            llm_provider=st.session_state.edit_provider,
            model_name=st.session_state.edit_model,
            api_key=st.session_state.gemini_api_key if st.session_state.edit_provider == 'gemini' else None
        )
        
        with st.spinner("AI is refining the content..."):
            stats = result.get('stats', {})
            updated_slides = agent.edit_content(
                prompt, 
                st.session_state.current_slides,
                stats.get('extracted_data', {}),
                stats.get('web_data', {})
            )
            
            if updated_slides:
                st.session_state.current_slides = updated_slides
                
                # RE-ASSEMBLE PPT
                try:
                    # Convert dicts to SimpleNamespace for PPTAssembler
                    obj_slides = [SimpleNamespace(**s) for s in updated_slides]
                    
                    # Output path - VERSIONED
                    old_path = st.session_state.ppt_path
                    # version based on timestamp + chat message count
                    v_suffix = f"_v{len(st.session_state.chat_history)}"
                    new_path = old_path.replace('.pptx', '').split('_v')[0] + f"{v_suffix}.pptx"
                    
                    assembler = PPTAssembler(domain=stats.get('domain', 'manufacturing'))
                    assembler.build(
                        obj_slides, 
                        stats.get('extracted_data', {}).get('financials', {}),
                        new_path
                    )
                    
                    st.session_state.ppt_path = new_path
                    response = f"✅ Content refined and PPT updated! Version saved as: **{os.path.basename(new_path)}**"
                    
                    with chat_container.chat_message("assistant"):
                        st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun() # Refresh to update download buttons
                    
                except Exception as e:
                    st.error(f"Failed to update PPT: {e}")
            else:
                st.error("AI failed to modify the content. Try again with a different instruction.")


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="KELP M&A Automation",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    # Render components
    render_header()
    output_dir = render_sidebar()
    
    # Main content
    st.markdown("### 📝 Input Details")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        company_name = st.text_input(
            "Company Name:",
            placeholder="e.g., Ksolves India Limited",
            help="Enter the target company name"
        )
    
    with col2:
        uploaded_file = st.file_uploader(
            "One-Pager (Markdown):",
            type=['md', 'txt'],
            help="Upload the company one-pager in Markdown format"
        )
    
    # Generate button
    st.markdown("")
    generate_btn = st.button(
        "🚀 Generate Investment Teaser",
        disabled=not (company_name and uploaded_file),
        use_container_width=True
    )
    
    if generate_btn and company_name and uploaded_file:
        st.session_state.processing = True
        st.session_state.pipeline_result = None # Clear old result
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        st.markdown("---")
        st.markdown("### 🔄 Processing")
        
        # Run pipeline
        result = run_pipeline(company_name, tmp_path, output_dir)
        st.session_state.pipeline_result = result
        st.session_state.ppt_path = result.get('ppt_path', '')
        st.session_state.citation_path = result.get('citation_path', '')
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Show outputs
        render_output_section(result)
    
    else:
        # Show persisted result on reload
        render_output_section(st.session_state.pipeline_result)
        st.session_state.processing = False
    
    # Sample data section
    with st.expander("📚 Sample Companies (for testing)"):
        st.markdown("""
        | Company | Domain | One-Pager |
        |---------|--------|-----------|
        | Centum Electronics | Manufacturing | Centum-OnePager.md |
        | Ksolves | Technology | Ksolves-OnePager.md |
        | Gati | Logistics | Gati-OnePager.md |
        | Connplex Cinemas | Consumer | Connplex-OnePager.md |
        | Ind Swift | Healthcare | Ind Swift-OnePager.md |
        | Kalyani Forge | Automotive | Kalyani Forge-OnePager.md |
        """)
    
    # Footer
    st.markdown("""
    <div class="kelp-footer">
        <p>Strictly Private & Confidential – Prepared by Kelp M&A Team</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
