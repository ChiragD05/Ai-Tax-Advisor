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
from utils.tax_simulator import simulate_tax_scenarios
from utils.tax_visuals import plot_tax_comparison, plot_scenario_comparison
from utils.firebase_config import firebase_config
from utils.firestore_db import save_chat, get_user_chats
from utils.tax_calculator import (
    calculate_old_regime_tax,
    calculate_new_regime_tax,
)
from utils.tax_visuals import plot_tax_comparison
from rag.pdf_ingest import create_pdf_vectorstore


# ======================================================
# PAGE CONFIG + CSS
# ======================================================

def load_css() -> None:
    css_path = Path("assets/styles.css")
    st.markdown(
        f"<style>{css_path.read_text()}</style>",
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="AI Tax Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


# ======================================================
# FIREBASE INIT
# ======================================================

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()


# ======================================================
# SESSION STATE
# ======================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = None

if "deduction_mode" not in st.session_state:
    st.session_state.deduction_mode = "Old tax regime"


# ======================================================
# HELPERS
# ======================================================

DEDUCTIONS = [
    {
        "key": "hra",
        "label": "HRA (House Rent Allowance)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "tag": "Old only",
    },
    {
        "key": "lta",
        "label": "LTA (Leave Travel Allowance)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "tag": "Old only",
    },
    {
        "key": "80c",
        "label": "Section 80C (LIC, PPF, ELSS, etc.)",
        "allowed_in": ["Old tax regime"],
        "default": 150000,
        "tag": "Old only",
    },
    {
        "key": "80d",
        "label": "Section 80D (Health Insurance)",
        "allowed_in": ["Old tax regime"],
        "default": 25000,
        "tag": "Old only",
    },
    {
        "key": "80tta",
        "label": "Section 80TTA / 80TTB (Savings interest)",
        "allowed_in": ["Old tax regime"],
        "default": 10000,
        "tag": "Old only",
    },
    {
        "key": "80e",
        "label": "Section 80E (Education loan interest)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "tag": "Old only",
    },
    {
        "key": "24b",
        "label": "Section 24(b) (Home loan interest)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "tag": "Old only",
    },
    {
        "key": "80ccd1b",
        "label": "Section 80CCD(1B) (Additional NPS)",
        "allowed_in": ["Old tax regime"],
        "default": 50000,
        "tag": "Old only",
    },
    {
        "key": "80ccd2",
        "label": "Section 80CCD(2) (Employer NPS)",
        "allowed_in": ["Old tax regime", "New tax regime"],
        "default": 0,
        "tag": "Both regimes",
    },
    {
        "key": "standard",
        "label": "Standard Deduction",
        "allowed_in": ["Old tax regime", "New tax regime"],
        "default": 75000,
        "tag": "Both regimes",
    },
]


def load_sidebar_history() -> None:
    if st.session_state.user:
        st.markdown("## 🕘 Previous Chats")
        previous_chats = get_user_chats(st.session_state.user)

        if not previous_chats:
            st.caption("No saved chats yet.")
            return

        for chat in previous_chats[-5:]:
            st.markdown(
                f"<div class='history-card'>💬 {chat['question']}</div>",
                unsafe_allow_html=True,
            )


# ======================================================
# HEADER
# ======================================================

st.markdown(
    """
    <div class='main-header'>
        <div class='main-title'>💰 AI Tax Advisor</div>
        <div class='subtitle'>AI-powered Indian Tax Planning & Financial Guidance Platform</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ======================================================
# SIDEBAR: AUTH + HISTORY ONLY
# ======================================================

with st.sidebar:
    st.markdown("## 🔐 Authentication")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    auth_col1, auth_col2 = st.columns(2)
    with auth_col1:
        login = st.button("Login")
    with auth_col2:
        signup = st.button("Signup")

    logout = st.button("Logout")

    if signup:
        try:
            auth.create_user_with_email_and_password(email, password)
            st.success("✅ Account created")
        except Exception as e:
            error_message = str(e)
            if "WEAK_PASSWORD" in error_message:
                st.error("❌ Password must be at least 6 characters")
            elif "EMAIL_EXISTS" in error_message:
                st.error("❌ Email already exists")
            else:
                st.error("❌ Signup failed")

    if login:
        try:
            auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = email
            st.success(f"✅ Logged in as {email}")
        except Exception as e:
            error_message = str(e)
            if "INVALID_PASSWORD" in error_message:
                st.error("❌ Wrong password")
            elif "EMAIL_NOT_FOUND" in error_message:
                st.error("❌ User not found")
            else:
                st.error("❌ Login failed")

    if logout and st.session_state.user:
        st.session_state.user = None
        st.success("Logged out")

    st.markdown("---")
    load_sidebar_history()


# ======================================================
# AUTH GUARD
# ======================================================

if not st.session_state.user:
    st.warning("🔒 Please login to access AI Tax Advisor")
    st.stop()


# ======================================================
# MAIN LAYOUT
# ======================================================

left_col, right_col = st.columns([1, 2])


# ------------------------------------------------------
# LEFT: TAX PLANNER
# ------------------------------------------------------

with left_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("## 🧮 Tax Planner")

    st.caption(
        "Old regime allows most deductions; new regime blocks most Chapter VI-A deductions."
    )

    regime = st.radio(
        "Choose tax regime",
        ["Old tax regime", "New tax regime"],
        horizontal=True,
        key="deduction_mode",
    )

    salary = st.number_input(
        "Annual Salary (₹)",
        min_value=0,
        step=50000,
        value=1200000,
    )

    st.markdown("### ✅ Enter deductions")

    deduction_breakdown = {}

    for item in DEDUCTIONS:
        allowed = regime in item["allowed_in"]

        st.markdown(f"**{item['label']}**  \n*{item['tag']}*")

        amount = st.slider(
            f"{item['key']}_slider",
            min_value=0,
            max_value=250000 if item["key"] in ["80c", "80ccd1b", "24b"] else 100000,
            value=item["default"] if allowed else 0,
            step=1000,
            disabled=not allowed,
            label_visibility="collapsed",
        )

        if not allowed:
            st.caption("Not available in the new tax regime")

        if allowed:
            deduction_breakdown[item["key"]] = amount
    
        current_total = sum(deduction_breakdown.values())

    st.markdown("### 📌 Selected deductions")
    for key, amount in deduction_breakdown.items():
        if amount > 0:
            label = next(
                (item["label"] for item in DEDUCTIONS if item["key"] == key),
                key
            )
            st.write(f"• {label} = ₹{amount:,.0f}")

    calculate_tax = st.button("Calculate Tax & Simulate")

    if calculate_tax:
        old_tax = calculate_old_regime_tax(salary, current_total)
        new_tax = calculate_new_regime_tax(salary)

        simulation_results = simulate_tax_scenarios(
            salary=salary,
            deduction_breakdown=deduction_breakdown,
        )

        st.session_state.tax_context = {
            "salary": salary,
            "regime": regime,
            "selected_total": current_total,
            "deduction_breakdown": deduction_breakdown,
            "old_tax": old_tax,
            "new_tax": new_tax,
            "best_regime": "Old tax regime" if old_tax < new_tax else "New tax regime" if new_tax < old_tax else "Both equal",
            "simulation_results": simulation_results,
        }

        st.markdown("### 📊 Tax Comparison")
        st.write(f"Old Regime Tax: ₹{old_tax:,.2f}")
        st.write(f"New Regime Tax: ₹{new_tax:,.2f}")

        if old_tax < new_tax:
            st.success("✅ Old Regime is better for you")
        elif new_tax < old_tax:
            st.success("✅ New Regime is better for you")
        else:
            st.info("Both regimes result in the same tax")

        fig = plot_tax_comparison(old_tax, new_tax)
        st.pyplot(fig)

        st.markdown("### 🔁 Tax Simulations")
        st.dataframe(
            [
                {
                    "Scenario": s["scenario"],
                    "Deductions": f"₹{s['deductions']:,.0f}",
                    "Old Tax": f"₹{s['old_tax']:,.2f}",
                    "New Tax": f"₹{s['new_tax']:,.2f}",
                    "Savings": f"₹{s['savings']:,.2f}",
                    "Best Regime": s["best_regime"],
                }
                for s in simulation_results
            ],
            use_container_width=True,
        )

        scenario_fig = plot_scenario_comparison(simulation_results)
        st.pyplot(scenario_fig)

        tax_saved = abs(old_tax - new_tax)
        st.markdown(f"### 💰 Tax Difference: ₹{tax_saved:,.2f}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                f"I've calculated your taxes. Old regime tax: ₹{old_tax:,.2f}, "
                f"New regime tax: ₹{new_tax:,.2f}. Ask me anything about this result."
            )
        })


# ------------------------------------------------------
# RIGHT: CHATBOT
# ------------------------------------------------------

with right_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("## 🤖 AI Tax Assistant")

    with st.expander("📄 Upload Tax PDF", expanded=False):
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

        if uploaded_file is not None:
            save_path = f"data/{uploaded_file.name}"
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success("✅ PDF uploaded")
            with st.spinner("Processing PDF..."):
                create_pdf_vectorstore(save_path)
            st.success("✅ PDF indexed successfully")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask your tax question...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking like a tax expert..."):
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/ask",
                        json={
                            "question": prompt,
                            "chat_history": st.session_state.messages,
                            "tax_context": st.session_state.get("tax_context", {})
                        },
                        timeout=90,
                    )

                    response.raise_for_status()
                    data = response.json()

                    answer = data["answer"]
                    sources = data["sources"]

                    save_chat(
                        st.session_state.user,
                        prompt,
                        answer,
                    )

                    st.markdown(answer)

                    with st.expander("📚 Sources"):
                        for i, source in enumerate(sources):
                            st.write(f"[{i+1}] {source}")

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )

                except Exception as e:
                    st.error(f"Backend Error: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ======================================================
# FOOTER
# ======================================================

st.markdown(
    """
    <div class='footer'>
        ⚠️ Disclaimer: This tool provides general tax guidance and should not replace professional financial advice.
    </div>
    """,
    unsafe_allow_html=True,
)