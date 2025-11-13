"""
Chat with Paper - ChatGPT-like Interface
Interactive chat with research papers using comprehensive analysis + RAG
"""

import streamlit as st

# Page Configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Chat with Paper",
    page_icon="💬",
    layout="wide"
)

import sys
sys.path.append('..')

from grok_client import GrokClient
import config
from rag_system.enhanced_rag import create_enhanced_rag_system

# Custom CSS for ChatGPT-like interface
st.markdown("""
<style>
    /* Chat container */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
    }

    /* Message bubbles */
    .user-message {
        background-color: #2b5278;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        text-align: left;
    }

    .assistant-message {
        background-color: #f0f0f0;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-right: auto;
        text-align: left;
    }

    .summary-message {
        background-color: #e8f4f8;
        border-left: 4px solid #2b5278;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }

    /* Chat input styling */
    .stTextInput > div > div > input {
        border-radius: 24px;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
    }

    /* Paper info card */
    .paper-info {
        background-color: #f8f9fa;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #2b5278;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'chat_paper_data' not in st.session_state:
    st.session_state.chat_paper_data = None

if 'chat_summary' not in st.session_state:
    st.session_state.chat_summary = None

if 'chat_initialized' not in st.session_state:
    st.session_state.chat_initialized = False

# Enhanced RAG session state
if 'enhanced_rag' not in st.session_state:
    st.session_state.enhanced_rag = None

if 'rag_initialized' not in st.session_state:
    st.session_state.rag_initialized = False

# Header
st.title("💬 Chat with Research Paper")
st.caption("ChatGPT-like interface for interactive paper discussion")

# Check if paper data is available
if st.session_state.chat_paper_data is None:
    st.warning("⚠️ No paper selected for chat. Please go back and click 'Chat with Paper' on a paper.")

    if st.button("← Go Back to Search"):
        st.switch_page("app.py")

    st.stop()

# Display paper information card
paper = st.session_state.chat_paper_data
st.markdown(f"""
<div class="paper-info">
    <h4>📄 {paper.get('title', 'Unknown Title')}</h4>
    <p><strong>Authors:</strong> {', '.join([a.get('name', 'Unknown') for a in paper.get('authors', [])][:3])}</p>
    <p><strong>Year:</strong> {paper.get('year', 'N/A')} | <strong>Citations:</strong> {paper.get('citations', 'N/A')}</p>
</div>
""", unsafe_allow_html=True)

# Initialize chat with comprehensive summary (first message)
if not st.session_state.chat_initialized and st.session_state.chat_summary:
    summary = st.session_state.chat_summary

    # Create first message with comprehensive summary
    first_message = f"""**📄 Comprehensive Paper Summary**

**🎯 Introduction & Research Context**
{summary.get('introduction', 'Summary not available.')}

**🔬 Methodology & Approach**
{summary.get('methodology', 'Summary not available.')}

**📊 Results & Key Findings**
{summary.get('results', 'Summary not available.')}

**💭 Discussion, Implications & Conclusions**
{summary.get('discussion', 'Summary not available.')}

---
*I'm ready to answer your questions about this paper! Ask me anything.*
"""

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": first_message
    })
    st.session_state.chat_initialized = True

# Initialize Enhanced RAG system (happens after first message)
if st.session_state.chat_summary and not st.session_state.rag_initialized:
    with st.spinner("🔍 Indexing paper for advanced search... (10-15 seconds)"):
        try:
            # Prepare paper data from summary
            paper_data = {
                'title': st.session_state.chat_paper_data.get('title', 'Unknown'),
                'sections': st.session_state.chat_summary
            }

            # Initialize Grok client
            grok = GrokClient(
                api_key=config.GROK_SETTINGS['api_key'],
                model="grok-4-fast-reasoning",
                validate=False
            )

            # Create enhanced RAG system
            st.session_state.enhanced_rag = create_enhanced_rag_system(paper_data, grok)
            st.session_state.rag_initialized = True

            st.success("✅ Paper indexed! Advanced RAG features active.")
        except Exception as e:
            st.warning(f"⚠️ Enhanced RAG not available: {str(e)}")
            st.session_state.rag_initialized = False

# Display chat history
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for message in st.session_state.chat_messages:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Assistant:** {message['content']}")
    st.markdown("---")

st.markdown("</div>", unsafe_allow_html=True)

# Chat input
col1, col2 = st.columns([6, 1])

with col1:
    user_question = st.text_input(
        "Ask a question about the paper...",
        key="chat_input",
        placeholder="E.g., What is the main contribution? How does it compare to prior work?",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("Send", type="primary", use_container_width=True)

# Handle user message
if send_button and user_question:
    # Add user message to chat
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_question
    })

    # Generate response using Grok-4
    with st.spinner("Thinking..."):
        try:
            # Check if enhanced RAG is available and initialized
            if st.session_state.enhanced_rag and st.session_state.rag_initialized:
                # Use enhanced RAG system
                rag_components = st.session_state.enhanced_rag

                # Check if this is a multi-hop question
                if rag_components['multi_hop_qa'].detect_multi_hop(user_question):
                    # Multi-hop QA for complex questions
                    result = rag_components['multi_hop_qa'].answer_multi_hop(
                        query=user_question,
                        paper_title=paper.get('title', 'Unknown')
                    )
                    response = result['answer']
                    confidence = result.get('confidence', None)
                    sources = result.get('evidence', [])
                else:
                    # Self-reflective RAG for single-hop questions
                    result = rag_components['self_reflective'].answer_with_reflection(
                        query=user_question,
                        paper_title=paper.get('title', 'Unknown'),
                        max_iterations=2
                    )
                    response = result['answer']
                    confidence = result['confidence']
                    sources = result.get('sources', [])

                # Add sources to response if available
                if sources and len(sources) > 0:
                    sources_text = "\n\n**📚 Sources:**"
                    for i, src in enumerate(sources[:3], 1):
                        section = src.get('section', 'Unknown')
                        score = src.get('score', 0)
                        sources_text += f"\n{i}. Section: `{section}` (Relevance: {score:.0%})"
                    response += sources_text

                # Add confidence indicator
                if confidence is not None:
                    if confidence >= 0.7:
                        confidence_icon = "🟢"
                        confidence_label = "High"
                    elif confidence >= 0.5:
                        confidence_icon = "🟡"
                        confidence_label = "Medium"
                    else:
                        confidence_icon = "🔴"
                        confidence_label = "Low"
                    response += f"\n\n{confidence_icon} **Confidence:** {confidence_label} ({confidence:.0%})"

                # Add assistant response to chat
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response
                })

            else:
                # Fallback to simple mode if RAG not initialized
                grok = GrokClient(
                    api_key=config.GROK_SETTINGS['api_key'],
                    model="grok-4-fast-reasoning",
                    validate=False
                )

                # Build context from paper data + summary
                paper_context = f"""
Paper Title: {paper.get('title', 'Unknown')}
Authors: {', '.join([a.get('name', 'Unknown') for a in paper.get('authors', [])])}
Year: {paper.get('year', 'N/A')}
Abstract: {paper.get('abstract', 'Not available')}

Comprehensive Analysis Summary:
{st.session_state.chat_summary.get('introduction', '')}
{st.session_state.chat_summary.get('methodology', '')}
{st.session_state.chat_summary.get('results', '')}
{st.session_state.chat_summary.get('discussion', '')}
"""

                # Build conversation history
                conversation_history = "\n".join([
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in st.session_state.chat_messages[-5:]
                ])

                # Create prompt for Grok
                prompt = f"""You are an AI assistant helping users understand a research paper.

Paper Context:
{paper_context}

Conversation History:
{conversation_history}

User Question: {user_question}

Instructions:
1. Answer based on the paper content if the information is available
2. If the paper doesn't contain the answer, use your general knowledge and indicate that
3. Be concise but informative (2-4 sentences)
4. If asked about specific details not in the summary, acknowledge the limitation
5. Maintain a helpful, conversational tone

Answer:"""

                # Get response from Grok
                response = grok.generate(
                    prompt=prompt,
                    max_tokens=400,
                    temperature=0.5
                ).strip()

                # Add assistant response to chat
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response
                })

        except Exception as e:
            error_message = f"Sorry, I encountered an error: {str(e)}"
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": error_message
            })

    # Rerun to update chat display
    st.rerun()

# Sidebar with chat controls
with st.sidebar:
    st.header("💬 Chat Controls")

    # Chat statistics
    st.metric("Messages", len(st.session_state.chat_messages))

    st.markdown("---")

    # RAG Status Indicator
    if st.session_state.rag_initialized and st.session_state.enhanced_rag:
        st.success("🚀 **Advanced RAG Active**")
        try:
            stats = st.session_state.enhanced_rag['rag'].get_paper_stats()
            st.caption(f"📊 {stats['total_chunks']} chunks indexed")
            st.caption(f"📑 {stats['sections']} sections")
            st.caption("🔍 Hybrid search enabled")
            st.caption("🧠 Self-reflection enabled")
        except Exception as e:
            # Fallback if stats retrieval fails
            print(f"Warning: Could not retrieve RAG stats: {e}")
            st.caption("🔍 Enhanced search enabled")
    else:
        st.info("💬 **Basic Chat Mode**")
        st.caption("Advanced RAG features loading...")

    st.markdown("---")

    # Export chat
    if st.button("📥 Export Chat", use_container_width=True):
        chat_export = "\n\n".join([
            f"{'You' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in st.session_state.chat_messages
        ])
        st.download_button(
            label="Download Chat History",
            data=chat_export,
            file_name=f"chat_{paper.get('title', 'paper')[:30]}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        # Keep first message (summary) and clear rest
        if len(st.session_state.chat_messages) > 0:
            first_msg = st.session_state.chat_messages[0]
            st.session_state.chat_messages = [first_msg]
            st.rerun()

    # New chat (go back)
    if st.button("← Back to Search", use_container_width=True):
        # Clear chat data
        st.session_state.chat_messages = []
        st.session_state.chat_paper_data = None
        st.session_state.chat_summary = None
        st.session_state.chat_initialized = False
        st.switch_page("app.py")

    st.markdown("---")

    # Tips
    st.markdown("""
    **💡 Tips for better questions:**
    - Ask about specific methods or results
    - Request comparisons with other work
    - Ask for clarifications on concepts
    - Inquire about limitations or future work
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>Powered by Grok-4 AI • Interactive Paper Discussion</p>
</div>
""", unsafe_allow_html=True)
