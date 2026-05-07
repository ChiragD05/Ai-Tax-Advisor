
import sys
import os
from pathlib import Path

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

import streamlit as st
import requests
import pyrebase

from utils.firebase_config import firebase_config
from utils.firestore_db import save_chat, get_user_chats

from utils.tax_calculator import (
    calculate_old_regime_tax,
    calculate_new_regime_tax
)

from utils.tax_visuals import plot_tax_comparison

from rag.pdf_ingest import create_pdf_vectorstore


# =========================================
# LOAD CSS
# =========================================

def load_css():

    css_path = Path("assets/styles.css")

    with open(css_path) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="AI Tax Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()


# =========================================
# FIREBASE
# =========================================

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()


# =========================================
# SESSION STATE
# =========================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================
# HEADER
# =========================================

st.markdown(
    """
    <div class='main-header'>
        <div class='main-title'>💰 AI Tax Advisor</div>
        <div class='subtitle'>
            AI-powered Indian Tax Planning & Financial Guidance Platform
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================
# SIDEBAR
# =========================================

with st.sidebar:

    st.markdown("## 🔐 Authentication")

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:
        login = st.button("Login")

    with col2:
        signup = st.button("Signup")

    logout = st.button("Logout")


    # SIGNUP
    if signup:

        try:

            auth.create_user_with_email_and_password(
                email,
                password
            )

            st.success("✅ Account created")

        except Exception as e:

            error_message = str(e)

            if "WEAK_PASSWORD" in error_message:
                st.error(
                    "❌ Password must be at least 6 characters"
                )

            elif "EMAIL_EXISTS" in error_message:
                st.error(
                    "❌ Email already exists"
                )

            else:
                st.error("❌ Signup failed")


    # LOGIN
    if login:

        try:

            auth.sign_in_with_email_and_password(
                email,
                password
            )

            st.session_state["user"] = email

            st.success(f"✅ Logged in as {email}")

        except Exception as e:

            error_message = str(e)

            if "INVALID_PASSWORD" in error_message:
                st.error("❌ Wrong password")

            elif "EMAIL_NOT_FOUND" in error_message:
                st.error("❌ User not found")

            else:
                st.error("❌ Login failed")


    # LOGOUT
    if logout:

        if "user" in st.session_state:

            del st.session_state["user"]
            st.success("Logged out")


    st.markdown("---")


    # PREVIOUS CHATS
    if "user" in st.session_state:

        st.markdown("## 🕘 Previous Chats")

        previous_chats = get_user_chats(
            st.session_state["user"]
        )

        for chat in previous_chats[-5:]:

            st.markdown(
                f"""
                <div class='history-card'>
                    💬 {chat['question']}
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================
# AUTH PROTECTION
# =========================================

if "user" not in st.session_state:

    st.warning(
        "🔒 Please login to access AI Tax Advisor"
    )

    st.stop()


# =========================================
# MAIN LAYOUT
# =========================================

left_col, right_col = st.columns([1, 2])


# =========================================
# TAX CALCULATOR
# =========================================

with left_col:

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("## 🧮 Tax Calculator")

    salary = st.number_input(
        "Annual Salary (₹)",
        min_value=0,
        step=50000
    )

    deductions = st.number_input(
        "Total Deductions (₹)",
        min_value=0,
        step=10000
    )

    calculate_tax = st.button(
        "Calculate Tax"
    )

    if calculate_tax:

        old_tax = calculate_old_regime_tax(
            salary,
            deductions
        )

        new_tax = calculate_new_regime_tax(
            salary
        )

        st.markdown("### 📊 Tax Comparison")

        st.write(
            f"Old Regime Tax: ₹{old_tax:,.2f}"
        )

        st.write(
            f"New Regime Tax: ₹{new_tax:,.2f}"
        )

        if old_tax < new_tax:

            st.success(
                "✅ Old Regime is better for you"
            )

        elif new_tax < old_tax:

            st.success(
                "✅ New Regime is better for you"
            )

        else:

            st.info(
                "Both regimes result in same tax"
            )

        fig = plot_tax_comparison(
            old_tax,
            new_tax
        )

        st.pyplot(fig)

        tax_saved = abs(old_tax - new_tax)

        st.markdown(
            f"### 💰 Tax Difference: ₹{tax_saved:,.2f}"
        )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# CHATBOT
# =========================================

with right_col:

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("## 🤖 AI Tax Assistant")


    # PDF Upload
    uploaded_file = st.file_uploader(
        "Upload Tax PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        save_path = f"data/{uploaded_file.name}"

        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("✅ PDF uploaded")

        with st.spinner("Processing PDF..."):
            create_pdf_vectorstore(save_path)

        st.success("✅ PDF indexed successfully")


    # CHAT HISTORY
    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


    # CHAT INPUT
    prompt = st.chat_input(
        "Ask your tax question..."
    )


    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)


        with st.chat_message("assistant"):

            with st.spinner(
                "Thinking like a tax expert..."
            ):

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


                    save_chat(
                        st.session_state["user"],
                        prompt,
                        answer
                    )

                    st.markdown(answer)

                    with st.expander("📚 Sources"):

                        for i, source in enumerate(sources):
                            st.write(f"[{i+1}] {source}")


                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )

                except Exception as e:

                    st.error(
                        f"Backend Error: {e}"
                    )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# FOOTER
# =========================================

st.markdown(
    """
    <div class='footer'>
        ⚠️ Disclaimer: This tool provides general tax guidance and should not replace professional financial advice.
    </div>
    """,
    unsafe_allow_html=True
)


