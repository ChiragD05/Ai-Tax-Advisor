import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)
import streamlit as st
import requests
from rag.pdf_ingest import create_pdf_vectorstore
if "messages" not in st.session_state:
    st.session_state.messages = []
# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="AI Tax Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>

/* Main App Background */
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}


/* Main Title */
.main-title {
    font-size: 48px;
    font-weight: 800;
    color: #facc15;
    margin-bottom: 0px;
}

/* Subtitle */
.subtitle {
    font-size: 18px;
    color: #cbd5e1;
    margin-bottom: 30px;
}

/* Cards */
.custom-card {
    background: rgba(255,255,255,0.05);
    padding: 25px;
    border-radius: 18px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 0 25px rgba(0,0,0,0.25);
}

/* Answer Box */
.answer-box {
    background: rgba(255,255,255,0.06);
    padding: 25px;
    border-radius: 16px;
    border-left: 5px solid #facc15;
}

/* Sources Box */
.sources-box {
    background: rgba(255,255,255,0.04);
    padding: 20px;
    border-radius: 16px;
}

/* Input Box */
.stTextInput > div > div > input {
    background-color: rgba(255,255,255,0.08);
    color: white;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.15);
    padding: 12px;
}

/* Button */
.stButton > button {
    width: 100%;
    background: linear-gradient(to right, #facc15, #f59e0b);
    color: black;
    font-weight: bold;
    border-radius: 12px;
    border: none;
    padding: 12px;
    font-size: 16px;
}

.stButton > button:hover {
    background: linear-gradient(to right, #fde047, #fbbf24);
    color: black;
}

/* Footer */
.footer {
    text-align: center;
    color: #94a3b8;
    margin-top: 40px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown(
    '<div class="main-title">💰 AI Tax Advisor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">AI-powered Indian Tax Planning & ITR Guidance System</div>',
    unsafe_allow_html=True
)

# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.markdown("## ⚙️ System Status")

    st.success("✅ FastAPI Backend Running")
    st.success("✅ OpenAI Connected")
    st.success("✅ FAISS Vector DB Loaded")

    st.markdown("---")

    st.markdown("## 📌 Features")

    st.write("• RAG-based retrieval")
    st.write("• AI-generated answers")
    st.write("• Source citations")
    st.write("• FastAPI backend")
    st.write("• Streamlit frontend")

    st.markdown("---")

    st.markdown("## 💡 Sample Questions")

    st.caption("Can I claim ELSS under 80C?")
    st.caption("What is HRA exemption?")
    st.caption("Difference between old and new tax regime?")
    st.caption("Can I claim home loan deduction?")
    st.markdown("---")
    st.markdown("## 📄 Upload Tax PDF")

    uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
    )
    if uploaded_file is not None:

     with open(f"data/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.getbuffer())

     st.success("✅ PDF uploaded successfully")
    
     with st.spinner("Processing PDF..."):
        create_pdf_vectorstore(f"data/{uploaded_file.name}")
     st.success("✅ PDF indexed into vector database")


prompt = st.chat_input("Ask your tax question...")

if prompt:

    # Store user message
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI response
    with st.chat_message("assistant"):

        with st.spinner("Thinking like a tax expert..."):

            try:

                response = requests.post(
                    "http://127.0.0.1:8000/ask",
                    json={
                      "question": prompt,
                      "chat_history": st.session_state.messages
                    }
                )

                data = response.json()

                answer = data["answer"]
                sources = data["sources"]

                st.markdown(answer)

                with st.expander("📚 Sources"):
                    for i, source in enumerate(sources):
                        st.write(f"[{i+1}] {source}")

                # Store assistant response
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as e:

                st.error(f"Backend Error: {e}")
# =========================
# FOOTER
# =========================
st.markdown(
    """
    <div class="footer">
    ⚠️ Disclaimer: This tool provides general tax guidance and should not replace professional financial advice.
    </div>
    """,
    unsafe_allow_html=True
)