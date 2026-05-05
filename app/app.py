import sys
import os
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rag.pipeline import get_tax_answer

st.set_page_config(page_title="AI Tax Advisor", layout="wide")

# 🎨 Custom CSS
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}

.title {
    font-size: 40px;
    font-weight: bold;
    color: #facc15;
}

.subtitle {
    color: #94a3b8;
    margin-bottom: 20px;
}

.card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 15px rgba(0,0,0,0.3);
}

.answer-box {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    border-radius: 15px;
}

.sources-box {
    background: rgba(255,255,255,0.06);
    padding: 20px;
    border-radius: 15px;
}

button {
    background: linear-gradient(to right, #facc15, #f59e0b);
    color: black !important;
    font-weight: bold;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# 🧠 HEADER
st.markdown('<div class="title">💰 AI Tax Advisor - India</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Intelligent Guidance for Your Financial Success</div>', unsafe_allow_html=True)

# 📦 MAIN INPUT CARD
st.markdown('<div class="card">', unsafe_allow_html=True)

query = st.text_input("Ask Your Tax Question:", placeholder="e.g. Can I claim ELSS under 80C?")

submit = st.button("🚀 Submit Query")

st.markdown('</div>', unsafe_allow_html=True)

# ⚙️ STATUS PANEL
col1, col2 = st.columns([3, 1])

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("🟢 Query Analysis")
    st.write("🟢 Source Retrieval")
    st.write("🟢 Answer Generation")
    st.markdown('</div>', unsafe_allow_html=True)

# 🤖 RESPONSE SECTION
if submit and query:
    with st.spinner("Thinking like a tax expert..."):
        answer, sources = get_tax_answer(query)

    colA, colB = st.columns(2)

    # 🧠 Answer
    with colA:
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.subheader("🤖 AI Generated Answer")
        st.write(answer)
        st.markdown('</div>', unsafe_allow_html=True)

    # 📚 Sources
    with colB:
        st.markdown('<div class="sources-box">', unsafe_allow_html=True)
        st.subheader("📚 Citations & Sources")
        for i, s in enumerate(sources):
            st.write(f"[{i+1}] {s}")
        st.markdown('</div>', unsafe_allow_html=True)

# ⚠️ Footer
st.markdown("""
<hr>
<small>Disclaimer: General information only. Consult a tax professional.</small>
""", unsafe_allow_html=True)