import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

import streamlit as st

from utils.form16_extractor import extract_form16_data

from utils.supabase_client import supabase

from utils.db import (
    create_chat_session,
    list_chat_sessions,
    load_chat_messages,
    save_chat_message,
    save_resource,
    delete_chat_session,
)

from utils.tax_calculator import (
    calculate_old_regime_tax,
    calculate_new_regime_tax,
)
from utils.tax_visuals import plot_tax_comparison
from rag.pdf_ingest import create_pdf_vectorstore
from rag.pipeline import get_tax_answer


# ======================================================
# PAGE CONFIG + CSS
# ======================================================

def load_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if css_path.exists():
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
# SESSION STATE
# ======================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = None

if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

if "session_tax_contexts" not in st.session_state:
    st.session_state.session_tax_contexts = {}

if "deduction_mode" not in st.session_state:
    st.session_state.deduction_mode = "Old tax regime"

if "auth_message" not in st.session_state:
    st.session_state.auth_message = ""


# ======================================================
# HELPERS
# ======================================================

DEDUCTIONS = [
    {
        "key": "hra",
        "label": "HRA (House Rent Allowance)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "max": 500000,
        "tag": "Old only",
    },
    {
        "key": "lta",
        "label": "LTA (Leave Travel Allowance)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "max": 200000,
        "tag": "Old only",
    },
    {
        "key": "80c",
        "label": "Section 80C (LIC, PPF, ELSS, etc.)",
        "allowed_in": ["Old tax regime"],
        "default": 150000,
        "max": 150000,
        "tag": "Old only",
    },
    {
        "key": "80d",
        "label": "Section 80D (Health Insurance)",
        "allowed_in": ["Old tax regime"],
        "default": 25000,
        "max": 100000,
        "tag": "Old only",
    },
    {
        "key": "80tta",
        "label": "Section 80TTA / 80TTB (Savings interest)",
        "allowed_in": ["Old tax regime"],
        "default": 10000,
        "max": 10000,
        "tag": "Old only",
    },
    {
        "key": "80e",
        "label": "Section 80E (Education loan interest)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "max": 200000,
        "tag": "Old only",
    },
    {
        "key": "24b",
        "label": "Section 24(b) (Home loan interest)",
        "allowed_in": ["Old tax regime"],
        "default": 0,
        "max": 200000,
        "tag": "Old only",
    },
    {
        "key": "80ccd1b",
        "label": "Section 80CCD(1B) (Additional NPS)",
        "allowed_in": ["Old tax regime"],
        "default": 50000,
        "max": 50000,
        "tag": "Old only",
    },
    {
        "key": "80ccd2",
        "label": "Section 80CCD(2) (Employer NPS)",
        "allowed_in": ["Old tax regime", "New tax regime"],
        "default": 0,
        "max": 200000,
        "tag": "Both regimes",
    },
    {
        "key": "standard",
        "label": "Standard Deduction",
        "allowed_in": ["Old tax regime", "New tax regime"],
        "default": 75000,
        "max": 75000,
        "tag": "Both regimes",
    },
]


def get_user_sessions():
    if not st.session_state.user:
        return []
    return list_chat_sessions(st.session_state.user)


def ensure_active_session():
    if not st.session_state.user:
        return

    sessions = get_user_sessions()

    if not sessions:
        new_id = create_chat_session(
            st.session_state.user,
            title=f"Chat {datetime.now().strftime('%d %b %H:%M')}"
        )
        st.session_state.active_session_id = new_id
        st.session_state.messages = []
        st.session_state.session_tax_contexts[new_id] = {}
        return

    active_id = st.session_state.active_session_id
    valid_ids = [s["id"] for s in sessions]

    if active_id not in valid_ids:
        st.session_state.active_session_id = sessions[0]["id"]
        st.session_state.messages = load_chat_messages(
            st.session_state.active_session_id
        )
        st.session_state.session_tax_contexts.setdefault(
            st.session_state.active_session_id, {}
        )


def open_session(session_id: str):
    st.session_state.active_session_id = session_id
    st.session_state.messages = load_chat_messages(session_id)
    st.session_state.session_tax_contexts.setdefault(session_id, {})
    st.rerun()


def start_new_chat():
    new_id = create_chat_session(
        st.session_state.user,
        title=f"Chat {datetime.now().strftime('%d %b %H:%M')}"
    )
    st.session_state.active_session_id = new_id
    st.session_state.messages = []
    st.session_state.session_tax_contexts[new_id] = {}
    st.rerun()


def load_sidebar_history():
    if not st.session_state.user:
        return

    st.markdown("## 🕘 Previous Chats")

    sessions = get_user_sessions()

    if not sessions:
        st.caption("No saved chats yet.")
        return

    for s in sessions:
        title = s.get("title") or "Chat"
        is_active = s["id"] == st.session_state.active_session_id

        c1, c2 = st.columns([4, 1])

        with c1:
            label = f"👉 {title}" if is_active else title
            if st.button(label, key=f"open_{s['id']}", use_container_width=True):
                open_session(s["id"])

        with c2:
            if st.button("🗑️", key=f"del_{s['id']}", use_container_width=True):
                delete_chat_session(s["id"])
                st.session_state.session_tax_contexts.pop(s["id"], None)

                if st.session_state.active_session_id == s["id"]:
                    st.session_state.active_session_id = None
                    st.session_state.messages = []

                st.rerun()

def handle_signup():
    email = st.session_state.get("auth_email", "")
    password = st.session_state.get("auth_password", "")

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        st.session_state.auth_message = (
            "✅ Account created. Please login."
        )

    except Exception as e:
        error = str(e)

        if "rate limit" in error.lower():
            st.session_state.auth_message = (
                "⚠️ Account may already exist. Try Login instead."
            )
        else:
            st.session_state.auth_message = (
                f"❌ Signup failed: {error}"
            )
            
def handle_login():
    email = st.session_state.get("auth_email", "")
    password = st.session_state.get("auth_password", "")

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        st.session_state.user = email
        st.session_state.active_session_id = None
        st.session_state.messages = []

        st.session_state.auth_message = (
            f"✅ Logged in as {email}"
        )

        start_new_chat()

    except Exception as e:
        st.session_state.auth_message = (
            f"❌ Login failed: {e}"
        )

def handle_logout():

    try:
        supabase.auth.sign_out()
    except:
        pass

    st.session_state.user = None
    st.session_state.active_session_id = None
    st.session_state.messages = []

    st.session_state.session_tax_contexts = {}

    st.session_state.auth_message = (
        "Logged out"
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
    if not st.session_state.user:
        st.markdown("## 🔐 Authentication")

        st.text_input("Email", key="auth_email")
        st.text_input("Password", type="password", key="auth_password")

        auth_col1, auth_col2 = st.columns(2)
        with auth_col1:
            if st.button("Login", use_container_width=True):
                handle_login()
        with auth_col2:
            if st.button("Signup", use_container_width=True):
                handle_signup()
                st.rerun()
    else:
        st.markdown(f"## 👤 Logged in as\n**{st.session_state.user}**")
        if st.button("Logout", use_container_width=True):
            handle_logout()
            st.rerun()

    if st.session_state.auth_message:
        if st.session_state.auth_message.startswith("✅") or st.session_state.auth_message == "Logged out":
            st.success(st.session_state.auth_message)
        else:
            st.error(st.session_state.auth_message)

    st.markdown("---")

    if st.session_state.user:
        if st.button("➕ New Chat", use_container_width=True):
            start_new_chat()

        st.markdown("---")
        load_sidebar_history()


# ======================================================
# AUTH GUARD
# ======================================================

if not st.session_state.user:
    st.warning("🔒 Please login to access AI Tax Advisor")
    st.stop()

ensure_active_session()


# ======================================================
# MAIN LAYOUT
# ======================================================

left_col, right_col = st.columns([2, 3])


# ------------------------------------------------------
# LEFT: TAX PLANNER
# ------------------------------------------------------

with left_col:
    st.markdown("## 🧮 Tax Planner")

    st.caption(
        "Old regime allows most deductions; new regime blocks most Chapter VI-A deductions."
    )

    regime = st.radio(
        "Choose tax regime",
        ["Old tax regime", "New tax regime"],
        horizontal=True,
        key=f"deduction_mode_{st.session_state.active_session_id}",
    )

    salary = st.number_input(
        "Annual Salary (₹)",
        min_value=0,
        step=50000,
        value=1200000,
    )

    st.markdown("### ✅ Enter deductions")
    st.caption("Old-only deductions are disabled in the new tax regime.")

    deduction_breakdown = {}

    for item in DEDUCTIONS:
        allowed = regime in item["allowed_in"]

        st.markdown(f"**{item['label']}**")
        if not allowed:
            st.caption("Only available in the old tax regime")

        # Initialize session state for this slider if not present
        slider_key = f"{item['key']}_slider_{st.session_state.active_session_id}"
        if slider_key not in st.session_state:
            st.session_state[slider_key] = item["default"] if allowed else 0

        # Draw value from session state (or force 0 if not allowed in current regime)
        current_val = st.session_state[slider_key] if allowed else 0

        amount = st.slider(
            f"{item['key']}_slider_widget_{st.session_state.active_session_id}",
            min_value=0,
            max_value=item["max"],
            value=current_val,
            step=1000,
            disabled=not allowed,
            label_visibility="collapsed",
        )

        if allowed:
            st.session_state[slider_key] = amount
            deduction_breakdown[item["key"]] = amount

    selected_total = sum(deduction_breakdown.values())

    st.markdown("### 📌 Selected deductions")
    if deduction_breakdown:
        for key, amount in deduction_breakdown.items():
            if amount > 0:
                label = next(
                    (x["label"] for x in DEDUCTIONS if x["key"] == key),
                    key
                )
                st.write(f"• {label} = ₹{amount:,.0f}")
    else:
        st.caption("No deductions selected.")

    calculate_tax = st.button("Calculate Tax")

    if calculate_tax:
        old_tax = calculate_old_regime_tax(salary, selected_total)
        new_tax = calculate_new_regime_tax(salary, selected_total)

        current_tax_context = st.session_state.session_tax_contexts.get(
            st.session_state.active_session_id,
            {}
        )

        current_tax_context.update({
            "salary": salary,
            "regime": regime,
            "selected_total": selected_total,
            "deduction_breakdown": deduction_breakdown,
            "old_tax": old_tax,
            "new_tax": new_tax,
            "best_regime": (
                "Old tax regime" if old_tax < new_tax
                else "New tax regime" if new_tax < old_tax
                else "Both equal"
            ),
        })

        st.session_state.session_tax_contexts[st.session_state.active_session_id] = current_tax_context

        st.markdown("### 📊 Tax Comparison")
        
        # Dashboard columns with metrics (2 columns for taxes, full-width banner for savings)
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Old Regime Tax", f"₹{old_tax:,.2f}")
        with m2:
            st.metric("New Regime Tax", f"₹{new_tax:,.2f}")
        
        tax_saved = abs(old_tax - new_tax)
        st.markdown(
            f"""
            <div style='background-color: rgba(16, 185, 129, 0.1); border-left: 5px solid #10B981; padding: 16px; border-radius: 12px; margin-top: 15px; margin-bottom: 15px;'>
                <h3 style='margin: 0; color: #065f46; font-size: 1.3rem; font-weight: 700;'>
                    💰 Potential Savings: ₹{tax_saved:,.2f}
                </h3>
                <p style='margin: 4px 0 0 0; color: #047857; font-size: 0.9rem;'>
                    {"Old Regime is cheaper." if old_tax < new_tax else "New Regime is cheaper." if new_tax < old_tax else "Both regimes have equal liability."}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if old_tax < new_tax:
            st.success("✅ Old Regime is better for you")
        elif new_tax < old_tax:
            st.success("✅ New Regime is better for you")
        else:
            st.info("Both regimes result in the same tax")

        # Interactive Plotly chart
        fig = plot_tax_comparison(old_tax, new_tax)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Section: Recommended Optimization Actions
        st.markdown("### 💡 Recommended Optimization Actions")
        recommendations = []
        
        if regime == "Old tax regime":
            # Check 80C
            claimed_80c = deduction_breakdown.get("80c", 0)
            if claimed_80c < 150000:
                diff = 150000 - claimed_80c
                recommendations.append(f"• **Section 80C**: Invest **₹{diff:,.0f}** more in ELSS, PPF, or NPS to save up to **₹{diff * 0.3:,.0f}** in taxes.")
            # Check 80D
            claimed_80d = deduction_breakdown.get("80d", 0)
            if claimed_80d < 25000:
                diff = 25000 - claimed_80d
                recommendations.append(f"• **Section 80D (Health Premium)**: Claim **₹{diff:,.0f}** more for health insurance premium to save up to **₹{diff * 0.3:,.0f}**.")
            # Check 24b
            claimed_24b = deduction_breakdown.get("24b", 0)
            if claimed_24b == 0:
                recommendations.append("• **Section 24(b) (Home Loan)**: If you pay interest on a home loan, you can claim up to **₹2,00,000** in tax deductions.")
        else:
            recommendations.append("• **Section 80CCD(2) (Employer NPS)**: Ask your employer to contribute up to 10% of your basic salary to NPS; it is fully tax-exempt under the new regime.")
            
        if recommendations:
            for rec in recommendations:
                st.info(rec)
        else:
            st.success("🎉 Excellent! You have fully optimized all major deduction categories.")

        summary_msg = (
            f"I've calculated your taxes. Old regime tax: ₹{old_tax:,.2f}, "
            f"New regime tax: ₹{new_tax:,.2f}. Ask me anything about this result."
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": summary_msg
        })
        save_chat_message(
            st.session_state.active_session_id,
            "assistant",
            summary_msg
        )




# ------------------------------------------------------
# RIGHT: CHATBOT
# ------------------------------------------------------

with right_col:
    st.markdown("## 🤖 AI Tax Assistant")

    with st.expander("📄 Upload Form 16", expanded=False):
        form16_file = st.file_uploader(
            "Upload Form 16 PDF",
            type=["pdf"],
            key="form16_uploader"
        )

        if form16_file is not None:
            session_id = st.session_state.active_session_id

            if not session_id:
                st.error("Create or open a chat first.")
            else:
                upload_dir = f"data/form16/{session_id}"
                os.makedirs(upload_dir, exist_ok=True)

                save_path = f"{upload_dir}/{os.path.basename(form16_file.name)}"

                with open(save_path, "wb") as f:
                    f.write(form16_file.getbuffer())

                with st.spinner("Extracting Form 16 details..."):
                    form16_data = extract_form16_data(save_path)

                st.session_state.session_tax_contexts[session_id]["form16_data"] = form16_data
                save_resource(session_id, form16_file.name, save_path, None)

                st.success("✅ Form 16 extracted successfully")

                st.markdown("### Extracted Summary")
                st.write(f"**Employer:** {form16_data.get('employer_name')}")
                st.write(f"**Employee:** {form16_data.get('employee_name')}")
                st.write(f"**Gross Salary:** ₹{form16_data.get('gross_salary') or 0:,.2f}")
                st.write(f"**Exemptions:** ₹{form16_data.get('exemptions') or 0:,.2f}")
                st.write(f"**Deductions:** ₹{form16_data.get('deductions') or 0:,.2f}")
                st.write(f"**Taxable Income:** ₹{form16_data.get('taxable_income') or 0:,.2f}")
                st.write(f"**TDS:** ₹{form16_data.get('tds') or 0:,.2f}")

    with st.expander("📄 Upload Tax PDF", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            key="tax_pdf_uploader"
        )

        if uploaded_file is not None:
            session_id = st.session_state.active_session_id
            if not session_id:
                st.error("Create or open a chat first.")
            else:
                upload_dir = f"data/uploads/{session_id}"
                index_dir = f"data/vectorstores/{session_id}"

                os.makedirs(upload_dir, exist_ok=True)
                os.makedirs(index_dir, exist_ok=True)

                save_path = f"{upload_dir}/{os.path.basename(uploaded_file.name)}"

                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success("✅ PDF uploaded")
                with st.spinner("Processing PDF..."):
                    create_pdf_vectorstore(save_path, index_dir)

                save_resource(
                    session_id,
                    uploaded_file.name,
                    save_path,
                    index_dir
                )

                tax_context = st.session_state.session_tax_contexts.get(session_id, {})
                tax_context["vectorstore_path"] = index_dir
                tax_context["uploaded_pdf_name"] = uploaded_file.name
                st.session_state.session_tax_contexts[session_id] = tax_context

                st.success("✅ PDF indexed successfully")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask your tax question...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message(
            st.session_state.active_session_id,
            "user",
            prompt
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking like a tax expert..."):
                try:
                    answer, sources = get_tax_answer(
                        prompt,
                        st.session_state.messages[:-1],
                        st.session_state.session_tax_contexts.get(
                            st.session_state.active_session_id, {}
                        )
                    )

                    import time

                    def stream_text(text):
                        for word in text.split(" "):
                            yield word + " "
                            time.sleep(0.015)

                    st.write_stream(stream_text(answer))

                    with st.expander("📚 Sources"):
                        for i, source in enumerate(sources):
                            st.write(f"[{i+1}] {source}")

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                    save_chat_message(
                        st.session_state.active_session_id,
                        "assistant",
                        answer
                    )

                except Exception as e:
                    st.error(f"Backend Error: {e}")




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