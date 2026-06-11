import sys
import os
import time
import json
import base64
import io
from pathlib import Path
import streamlit as st
import markdown

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import backend.config as cfg
from backend.database import (
    get_kb_documents, add_kb_document, delete_kb_document,
    get_kb_entries, get_conversations, create_conversation, 
    delete_conversation, rename_conversation, pin_conversation,
    add_chat_message, get_chat_messages
)
from backend.ingest import run_ingestion
from utils.styles import get_custom_css
from utils.export import export_to_pdf

st.set_page_config(
    page_title="Knowledge Base Chat | ResumeForge AI",
    page_icon="💬",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Auth Check ─────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in from the main page first.")
    st.stop()

user_id = st.session_state.user['id']
KB_DOCS_DIR = Path(__file__).parent.parent / "data" / "kb_docs" / str(user_id)
os.makedirs(KB_DOCS_DIR, exist_ok=True)


# ─── LLM Factory & Statistics Helpers ────────────────────────────────────────

def get_chat_model(model_name: str, temperature: float = 0.3, max_tokens: int = 1000):
    """Factory to get the appropriate LangChain model instance based on selection."""
    from langchain_openai import ChatOpenAI
    
    openai_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
    
    if model_name in openai_models:
        return ChatOpenAI(model=model_name, temperature=temperature, max_tokens=max_tokens)
        
    elif "claude" in model_name.lower():
        try:
            from langchain_anthropic import ChatAnthropic
            if os.getenv("ANTHROPIC_API_KEY"):
                c_model = "claude-3-5-sonnet-latest" if "sonnet" in model_name.lower() else "claude-3-opus-latest"
                return ChatAnthropic(model_name=c_model, temperature=temperature, max_tokens=max_tokens)
        except ImportError:
            pass
        st.sidebar.warning("Anthropic key missing or package not installed. Using GPT-4o.")
        return ChatOpenAI(model="gpt-4o", temperature=temperature, max_tokens=max_tokens)
        
    elif "gemini" in model_name.lower():
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
                if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
                    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
                return ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=temperature, max_output_tokens=max_tokens)
        except ImportError:
            pass
        st.sidebar.warning("Gemini key missing or package not installed. Using GPT-4o.")
        return ChatOpenAI(model="gpt-4o", temperature=temperature, max_tokens=max_tokens)
        
    elif "deepseek" in model_name.lower():
        if os.getenv("DEEPSEEK_API_KEY"):
            return ChatOpenAI(
                model="deepseek-chat",
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1"
            )
        st.sidebar.warning("DeepSeek API key missing. Using GPT-4o-mini.")
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature, max_tokens=max_tokens)

    elif "local" in model_name.lower():
        return ChatOpenAI(
            model="llama3",
            temperature=temperature,
            max_tokens=max_tokens,
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )
        
    return ChatOpenAI(model="gpt-4o-mini", temperature=temperature, max_tokens=max_tokens)


def get_token_usage_stats(response, model_name: str):
    """Extract token counts and estimate costs based on models."""
    input_tokens = 0
    output_tokens = 0
    
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        input_tokens = response.usage_metadata.get("input_tokens", 0)
        output_tokens = response.usage_metadata.get("output_tokens", 0)
    elif hasattr(response, "response_metadata") and response.response_metadata:
        token_usage = response.response_metadata.get("token_usage") or response.response_metadata.get("usage")
        if token_usage:
            input_tokens = token_usage.get("prompt_tokens", 0) or token_usage.get("input_tokens", 0)
            output_tokens = token_usage.get("completion_tokens", 0) or token_usage.get("output_tokens", 0)
            
    if input_tokens == 0:
        input_tokens = int(len(response.content) / 4)
    if output_tokens == 0:
        output_tokens = int(len(response.content) / 4)
        
    cost_rates = {
        "gpt-4o-mini": {"in": 0.15, "out": 0.60},
        "gpt-4o": {"in": 5.00, "out": 15.00},
        "gpt-3.5-turbo": {"in": 0.50, "out": 1.50},
        "claude": {"in": 3.00, "out": 15.00},
        "gemini": {"in": 0.075, "out": 0.30},
        "deepseek": {"in": 0.14, "out": 0.28},
        "local": {"in": 0.0, "out": 0.0}
    }
    
    rate = cost_rates.get("gpt-4o-mini")
    for k, v in cost_rates.items():
        if k in model_name.lower():
            rate = v
            break
            
    in_cost = (input_tokens / 1_000_000) * rate["in"]
    out_cost = (output_tokens / 1_000_000) * rate["out"]
    total_cost = in_cost + out_cost
    
    return input_tokens, output_tokens, total_cost


def retrieve_filtered_chunks(user_id: int, query: str, selected_categories: list, selected_docs: list, k: int, embedding_model: str):
    """Retrieve and filter vector chunks based on user source selection."""
    from backend.retriever import retrieve_with_scores
    
    if not selected_categories and not selected_docs:
        return []
        
    try:
        # Retrieve more chunks to account for filter dropoffs
        raw_results = retrieve_with_scores(user_id, query, k=k * 4, embedding_model=embedding_model)
    except Exception as e:
        st.error(f"Vector search failed. Did you rebuild your Vector DB? Error: {e}")
        return []
        
    filtered = []
    for doc, score in raw_results:
        doc_type = doc.metadata.get("doc_type")
        doc_title = doc.metadata.get("title")
        
        is_match = False
        if doc_type == "document":
            if doc_title in selected_docs:
                is_match = True
        else:
            if doc_type in selected_categories:
                is_match = True
                
        if is_match:
            filtered.append((doc, score))
            if len(filtered) >= k:
                break
                
    return filtered


# ─── Sidebar: Conversation Logs ──────────────────────────────────────────────

st.sidebar.markdown("# Conversations")

conversations = get_conversations(user_id)

# Initialize selected conversation ID
if "current_conv_id" not in st.session_state:
    if conversations:
        st.session_state.current_conv_id = conversations[0]["id"]
    else:
        st.session_state.current_conv_id = None

# New Chat Button
if st.sidebar.button("➕ New Chat", use_container_width=True, type="primary"):
    new_id = create_conversation(user_id, f"New Chat {time.strftime('%Y-%m-%d %H:%M')}")
    st.session_state.current_conv_id = new_id
    st.rerun()

# List past conversations
st.sidebar.markdown("---")
if not conversations:
    st.sidebar.caption("No conversations yet.")
else:
    for conv in conversations:
        # Pin icon if pinned
        prefix = "📌 " if conv["is_pinned"] else "💬 "
        label = f"{prefix}{conv['title'][:20]}"
        
        col_label, col_act = st.sidebar.columns([4, 1])
        
        # Selection highlight logic
        is_selected = st.session_state.current_conv_id == conv["id"]
        btn_type = "primary" if is_selected else "secondary"
        
        if col_label.button(label, key=f"sel_{conv['id']}", use_container_width=True, type=btn_type):
            st.session_state.current_conv_id = conv["id"]
            st.rerun()
            
        with col_act:
            # Dropdown options or small actions
            with st.popover("⚙️", key=f"pop_{conv['id']}"):
                new_title = st.text_input("Rename Title", value=conv["title"], key=f"ren_in_{conv['id']}")
                if st.button("Save", key=f"ren_save_{conv['id']}"):
                    if new_title.strip():
                        rename_conversation(conv["id"], new_title.strip(), user_id)
                        st.rerun()
                
                pin_label = "Unpin" if conv["is_pinned"] else "Pin"
                if st.button(pin_label, key=f"pin_{conv['id']}"):
                    pin_conversation(conv["id"], not conv["is_pinned"], user_id)
                    st.rerun()
                    
                if st.button("🗑️ Delete", key=f"del_conv_{conv['id']}", type="primary"):
                    delete_conversation(conv["id"], user_id)
                    if st.session_state.current_conv_id == conv["id"]:
                        st.session_state.current_conv_id = None
                    st.rerun()

# ─── Left & Right Panels ──────────────────────────────────────────────────────

col_left, col_right = st.columns([1, 3], gap="large")

# ═══════════════════════════════════════════════════════════════════════════
# LEFT PANEL: Knowledge Base Management
# ═══════════════════════════════════════════════════════════════════════════
with col_left:
    st.markdown("## RAG Sources")
    st.markdown("Select categories and documents to query.")
    
    # ─── Ingestion check ───
    kb_docs = get_kb_documents(user_id)
    kb_entries = get_kb_entries(user_id)
    
    # Search Filter
    kb_search = st.text_input("Search Sources", placeholder="Filter sources...", key="kb_src_search").lower()
    
    st.markdown("### Structured Categories")
    selected_categories = []
    categories = ["projects", "experience", "skills", "education", "certifications", "personal"]
    
    for cat in categories:
        count = len([e for e in kb_entries if e["category"] == cat])
        label = f"{cat.capitalize()} ({count})"
        if kb_search in label.lower():
            if st.checkbox(label, value=True, key=f"cat_sel_{cat}"):
                selected_categories.append(cat)
                
    st.markdown("### Documents")
    selected_docs = []
    
    # Upload Document inline
    with st.expander("Upload Document"):
        new_doc_name = st.text_input("Document Name", placeholder="e.g. My Resume v2")
        new_doc_file = st.file_uploader("Select PDF/TXT/MD File", type=["pdf", "txt", "md"])
        if st.button("Upload & Index"):
            if not new_doc_name.strip() or not new_doc_file:
                st.error("Please provide both a name and a file.")
            else:
                import re
                safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', new_doc_file.name)
                unique_filename = f"chat_{int(time.time())}_{safe_name}"
                dest_path = KB_DOCS_DIR / unique_filename
                
                with open(dest_path, "wb") as f:
                    f.write(new_doc_file.getbuffer())
                    
                add_kb_document(user_id, new_doc_name.strip(), str(dest_path), new_doc_file.type)
                
                with st.spinner("Rebuilding Vector DB..."):
                    try:
                        run_ingestion(user_id, chunk_size=cfg.CHUNK_SIZE, chunk_overlap=cfg.CHUNK_OVERLAP, embedding_model=cfg.DEFAULT_EMBEDDING_MODEL)
                        st.success("Uploaded and indexed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ingestion failed: {e}")
                        
    # List uploaded docs
    if not kb_docs:
        st.caption("No documents uploaded.")
    else:
        for doc in kb_docs:
            label = f"{doc['file_name']} (Chunks: {doc['chunk_count']})"
            if kb_search in label.lower():
                col_chk, col_info, col_del = st.columns([4, 1, 1])
                
                with col_chk:
                    if st.checkbox(doc["file_name"], value=True, key=f"doc_sel_{doc['id']}"):
                        selected_docs.append(doc["file_name"])
                        
                with col_info:
                    # Show metadata popover
                    with st.popover("ℹ️", key=f"doc_meta_{doc['id']}"):
                        st.markdown(f"**File Name**: {os.path.basename(doc['file_path'])}")
                        st.markdown(f"**Upload Date**: {doc['created_at']}")
                        st.markdown(f"**File Type**: {doc['file_type']}")
                        st.markdown(f"**Chunks Created**: {doc['chunk_count']}")
                        st.markdown(f"**Embedding Model**: {doc['embedding_model'] or 'N/A'}")
                        
                with col_del:
                    if st.button("🗑️", key=f"del_doc_{doc['id']}", type="secondary"):
                        delete_kb_document(doc["id"], user_id)
                        with st.spinner("Updating Vector DB..."):
                            run_ingestion(user_id, chunk_size=cfg.CHUNK_SIZE, chunk_overlap=cfg.CHUNK_OVERLAP, embedding_model=cfg.DEFAULT_EMBEDDING_MODEL)
                        st.rerun()

    # ─── Summary Generator Button ───
    st.markdown("---")
    st.markdown("### KB Report")
    
    if st.button("Generate Full KB Summary", use_container_width=True, type="primary"):
        st.session_state.generate_summary_trigger = True
        
    if st.session_state.get("generate_summary_trigger"):
        # Compile selected text
        st.session_state.generate_summary_trigger = False # Reset
        
        with st.spinner("Analyzing selected sources..."):
            # Fetch all selected chunk contents
            compiled_texts = []
            
            # Fetch structured entries text
            for entry in kb_entries:
                if entry["category"] in selected_categories:
                    compiled_texts.append(f"Category: {entry['category']} | Title: {entry['title']}\n{entry['content']}")
                    
            # Fetch doc text
            for doc in kb_docs:
                if doc["file_name"] in selected_docs:
                    from backend.ingest import _extract_text_from_file
                    t = _extract_text_from_file(doc["file_path"], doc["file_type"])
                    if t:
                        compiled_texts.append(f"Document: {doc['file_name']}\n{t}")
                        
            if not compiled_texts:
                st.error("No source content found! Please select at least one source containing content.")
            else:
                combined_kb_data = "\n\n==================\n\n".join(compiled_texts)
                
                from backend.prompts import DEFAULT_SECTION_PROMPTS
                SUMMARY_PROMPT = """You are an expert career analyst. 
Your task is to analyze all the provided background information from the selected knowledge base sources and compile a structured, comprehensive Knowledge Base Summary.

Include the following sections in your summary:
1. Executive Summary: A high-level overview of the entire dataset.
2. Key Topics: Core themes and areas of expertise identified.
3. Important Concepts: Key terms, frameworks, or principles mentioned.
4. Skills Identified: Categorized list of technical skills, soft skills, and tools.
5. Entities Mentioned: Key companies, institutions, platforms, or systems.
6. Action Items: Recommended next actions for the user based on the content.
7. Recommendations: Suggestions for career growth, learning, or RAG optimization.
8. Missing Information: Any obvious gaps or missing files/information that would complete this background profile.

Provided Background Data:
{kb_data}

Generate a clear, professional, and well-structured markdown summary. Ensure it is detailed and thorough."""
                
                try:
                    from langchain_openai import ChatOpenAI
                    from langchain_core.messages import SystemMessage, HumanMessage
                    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
                    
                    sys_msg = SystemMessage(content="You are a meticulous professional summarizer.")
                    usr_msg = HumanMessage(content=SUMMARY_PROMPT.format(kb_data=combined_kb_data[:30000])) # Limit to ~30k chars
                    
                    res = llm.invoke([sys_msg, usr_msg])
                    st.session_state.kb_summary_text = res.content
                    st.success("Summary generated successfully!")
                except Exception as e:
                    st.error(f"Failed to generate summary: {e}")
                    
    if st.session_state.get("kb_summary_text"):
        with st.expander("View Generated Summary", expanded=True):
            st.markdown(st.session_state.kb_summary_text)
            
            # Export Options
            sum_txt = st.session_state.kb_summary_text
            
            col_ex1, col_ex2, col_ex3 = st.columns(3)
            col_ex1.download_button("Export TXT", sum_txt, "kb_summary.txt", "text/plain", use_container_width=True)
            col_ex2.download_button("Export Markdown", sum_txt, "kb_summary.md", "text/markdown", use_container_width=True)
            
            try:
                pdf_bytes = export_to_pdf(sum_txt)
                col_ex3.download_button("Export PDF", pdf_bytes, "kb_summary.pdf", "application/pdf", use_container_width=True)
            except Exception as e:
                col_ex3.error("PDF Fail")


# ═══════════════════════════════════════════════════════════════════════════
# RIGHT PANEL: AI Chat Interface
# ═══════════════════════════════════════════════════════════════════════════
with col_right:
    if not st.session_state.current_conv_id:
        st.markdown("## AI Chat Workspace")
        st.info("Create a conversation using '➕ New Chat' in the sidebar or select an existing one to begin.")
        st.stop()
        
    messages = get_chat_messages(st.session_state.current_conv_id)
    conv_details = [c for c in conversations if c["id"] == st.session_state.current_conv_id]
    conv_title = conv_details[0]["title"] if conv_details else "AI Chat Workspace"
    
    st.markdown(f"## {conv_title}")
    
    # ─── Chat Settings & Advanced Parameters ───
    with st.expander("⚙️ Advanced Chat Configuration", expanded=False):
        c_p1, c_p2 = st.columns(2)
        
        with c_p1:
            st.markdown("**AI Model Settings**")
            chat_model_opt = st.selectbox(
                "AI Model",
                ["gpt-4o-mini (Default)", "gpt-4o", "gpt-3.5-turbo", 
                 "Claude Sonnet", "Claude Opus", "Gemini 2.5 Pro", 
                 "DeepSeek", "Local LLM"],
                key="chat_model_select"
            )
            chat_temp = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1, key="chat_temp_val")
            chat_max_tokens = st.number_input("Max Output Tokens", 100, 4000, 1000, 100, key="chat_max_toks")
            
        with c_p2:
            st.markdown("**Retrieval Settings**")
            chat_top_k = st.slider("Top K Chunks", 1, 20, 5, key="chat_top_k_val")
            chat_hybrid = st.toggle("Hybrid Search Mode", value=False, key="chat_hybrid_search")
            chat_streaming = st.toggle("Enable Streaming Responses", value=False, key="chat_stream_resp")
            
    # Shortcut Workflow Prompt Cards
    st.markdown("##### Quick Prompts")
    q_col1, q_col2, q_col3 = st.columns(3)
    
    q_prompts = {
        "Resume Analysis": "What are the core technical skills, projects, and strengths listed in my selected knowledge bases?",
        "Compare with JD": "Compare my resume content in the selected KBs with a target Job Description. Highlight the match percentage and missing skills.",
        "Interview Prep": "Generate 5 technical interview questions based on the projects and experiences in my selected knowledge bases."
    }
    
    if q_col1.button("Resume Analysis", use_container_width=True):
        st.session_state.quick_prompt_trigger = q_prompts["Resume Analysis"]
    if q_col2.button("Compare Resume vs JD", use_container_width=True):
        st.session_state.quick_prompt_trigger = q_prompts["Compare with JD"]
    if q_col3.button("Interview Questions", use_container_width=True):
        st.session_state.quick_prompt_trigger = q_prompts["Interview Prep"]

    # ─── Chat Message Display Area ───
    st.markdown("---")
    
    # Render historical messages
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        
        with st.chat_message(role):
            st.markdown(content)
            
            # Show auxiliary info under AI responses
            if role == "assistant":
                # Citation panel
                chunks_json = msg.get("retrieved_chunks")
                if chunks_json:
                    try:
                        retrieved_chunks = json.loads(chunks_json)
                        if retrieved_chunks:
                            with st.expander(f"View Citations ({len(retrieved_chunks)})"):
                                for chunk in retrieved_chunks:
                                    st.markdown(
                                        f"**Source**: `{chunk.get('title')}` | Rank: {chunk.get('rank')} | "
                                        f"Score: `{chunk.get('score')}`"
                                    )
                                    st.markdown(
                                        f"<div style='background:#F7F8FA; border:1px solid #E6E8EF; padding:8px 10px; border-radius:8px; "
                                        f"font-size:0.85rem; color:#555D72; margin-bottom:8px;'>{chunk.get('preview')}</div>",
                                        unsafe_allow_html=True
                                    )
                    except Exception:
                        pass
                
                # Usage & Cost dropdown
                col_act1, col_act2, col_act3 = st.columns([3, 1, 1])
                
                with col_act1:
                    with st.expander("Cost & Usage Metrics"):
                        st.markdown(f"**AI Model Used**: `{msg.get('model_used', 'gpt-4o-mini')}`")
                        st.markdown(f"**Input Tokens**: `{msg.get('input_tokens', 0)}`")
                        st.markdown(f"**Output Tokens**: `{msg.get('output_tokens', 0)}`")
                        st.markdown(f"**Cost Estimator**: `${msg.get('cost', 0.0):.6f}`")
                        
                with col_act2:
                    st.download_button("Download MD", content, f"message_{msg['id']}.md", "text/markdown", key=f"dl_msg_{msg['id']}")
                    
                with col_act3:
                    # Copy as Markdown script block
                    if st.button("Copy", key=f"cpy_msg_{msg['id']}"):
                        st.toast("Copied message to clipboard!")
                        st.session_state.copy_text = content
                        
    # ─── Chat Input Handler ───
    user_query = st.chat_input("Ask a question about your knowledge bases...")
    
    # Override query if quick prompt clicked
    if st.session_state.get("quick_prompt_trigger"):
        user_query = st.session_state.quick_prompt_trigger
        st.session_state.quick_prompt_trigger = None # reset
        
    if user_query:
        # 1. Save user query to DB
        add_chat_message(
            conversation_id=st.session_state.current_conv_id,
            role="user",
            content=user_query
        )
        
        # Display user bubble instantly
        with st.chat_message("user"):
            st.markdown(user_query)
            
        # 2. Retrieve chunks based on selections
        with st.spinner("Retrieving facts..."):
            retrieved_results = retrieve_filtered_chunks(
                user_id=user_id,
                query=user_query,
                selected_categories=selected_categories,
                selected_docs=selected_docs,
                k=chat_top_k,
                embedding_model=cfg.DEFAULT_EMBEDDING_MODEL
            )
            
        # Organize context
        context_parts = []
        citations_list = []
        for i, (doc, score) in enumerate(retrieved_results):
            source_title = doc.metadata.get("title")
            doc_type = doc.metadata.get("doc_type")
            context_parts.append(f"--- SOURCE: {source_title} (Category: {doc_type}) ---\n{doc.page_content}")
            
            citations_list.append({
                "rank": i + 1,
                "title": source_title,
                "doc_type": doc_type,
                "score": round(score, 4),
                "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            })
            
        context_str = "\n\n".join(context_parts)
        
        # 3. Call LLM
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Prepare LLM Prompts
            SYSTEM_CHAT_PROMPT = """You are a helpful AI assistant. 
Your goal is to answer the user's questions truthfully and accurately using ONLY the provided knowledge base context retrieved from their personal files.

Instructions:
- Base your answers strictly on the facts and information provided in the Context below.
- Do not invent facts or assume details not present in the context.
- If the context does not contain the answer, politely explain that you cannot find the answer in the selected knowledge base files.
- Cite the files/categories where relevant.

Context Data:
{context}"""
            
            formatted_system = SYSTEM_CHAT_PROMPT.format(context=context_str)
            from langchain_core.messages import SystemMessage, HumanMessage
            
            messages_payload = [
                SystemMessage(content=formatted_system),
                HumanMessage(content=user_query)
            ]
            
            model = get_chat_model(chat_model_opt, chat_temp, chat_max_tokens)
            
            try:
                # Execution
                start_time = time.time()
                response = model.invoke(messages_payload)
                elapsed_time = (time.time() - start_time) * 1000
                
                answer = response.content
                message_placeholder.markdown(answer)
                
                # Calculate costs & usage
                in_tok, out_tok, cost = get_token_usage_stats(response, chat_model_opt)
                
                # Save Assistant response to DB
                add_chat_message(
                    conversation_id=st.session_state.current_conv_id,
                    role="assistant",
                    content=answer,
                    model_used=chat_model_opt,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost=cost,
                    retrieved_chunks=json.dumps(citations_list)
                )
                
                # Refresh page to render citations/expanders properly
                st.rerun()
                
            except Exception as e:
                st.error(f"LLM Generation failed: {e}")
