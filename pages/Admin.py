# -*- coding: utf-8 -*-
"""
admin.py – Admin Panel for Karmveer Abhyasika
Improvements:
  • Mobile-responsive UI with fluid layouts
  • @st.cache_data for fast data loads (TTL-based)
  • Full student CRUD (add via form, update, delete)
  • Password stored in st.secrets (falls back to env var, then default)
  • Robust exception handling everywhere
  • Debug prints removed; proper st.error/st.warning used
"""

import os
import calendar
import base64
from io import BytesIO
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

import gsheets_config as gs

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Admin | कर्मवीर अभ्यासिका",
    page_icon="🔑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Secure password resolution ────────────────────────────────────────────────
def _get_admin_password() -> str:
    """
    Priority:
      1. st.secrets["ADMIN_PASSWORD"]
      2. Environment variable ADMIN_PASSWORD
      3. Hardcoded fallback (change before production!)
    """
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        pass
    env_pw = os.environ.get("ADMIN_PASSWORD", "")
    if env_pw:
        return env_pw
    return "admin@2025"   # ← change this or set via secrets/env


STANDARD_MONTHLY_FEE = 600


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LAYER  –  All Google Sheets interactions with caching + error handling
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def fetch_all_students_data() -> pd.DataFrame:
    """Fetch all student admission records (cached 60s)."""
    try:
        df = gs.sheet_to_df(gs.SHEET_ADMISSIONS)
        if df.empty:
            return pd.DataFrame()
        wanted = [
            "id", "admission_date", "nav", "janmatarikh", "ling", "mobile",
            "palak_mobile", "email", "patta", "tayari", "ssc_gun", "hsc_gun",
            "graduation_padvi", "graduation_gun", "post_graduation_padvi",
            "post_graduation_gun",
        ]
        existing = [c for c in wanted if c in df.columns]
        return df[existing].copy()
    except Exception as e:
        st.error(f"विद्यार्थी डेटा लोड करताना त्रुटी: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_fee_payments() -> pd.DataFrame:
    """Fetch all fee payment records (cached 60s)."""
    try:
        df = gs.sheet_to_df(gs.SHEET_FEE_PAYMENTS)
        if df.empty:
            return pd.DataFrame()
        df["amount_paid"] = pd.to_numeric(df["amount_paid"], errors="coerce").fillna(0)
        df["year"]        = pd.to_numeric(df["year"],        errors="coerce")
        return df.sort_values("payment_date", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"फी रेकॉर्ड लोड करताना त्रुटी: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_deposits() -> pd.DataFrame:
    try:
        df = gs.sheet_to_df(gs.SHEET_DEPOSITS)
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        st.error(f"ठेव रेकॉर्ड लोड करताना त्रुटी: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_brave_students() -> pd.DataFrame:
    try:
        df = gs.sheet_to_df(gs.SHEET_BRAVE_STUDENTS)
        if df.empty:
            return pd.DataFrame()
        df["display_order"] = pd.to_numeric(df["display_order"], errors="coerce").fillna(0)
        return df.sort_values(["display_order", "id"]).reset_index(drop=True)
    except Exception as e:
        st.error(f"गॅलरी लोड करताना त्रुटी: {e}")
        return pd.DataFrame()


def _invalidate_cache():
    """Clear all cached data so next load is fresh."""
    fetch_all_students_data.clear()
    fetch_fee_payments.clear()
    fetch_deposits.clear()
    fetch_brave_students.clear()


# ── Write helpers ─────────────────────────────────────────────────────────────

def save_student(data: dict) -> bool:
    """Append a new admission record."""
    try:
        new_id = gs.next_id(gs.SHEET_ADMISSIONS)
        row = [
            new_id,
            data.get("admission_date", datetime.now().strftime("%Y-%m-%d")),
            data.get("nav", ""),
            data.get("janmatarikh", ""),
            data.get("ling", ""),
            data.get("mobile", ""),
            data.get("palak_mobile", ""),
            data.get("email", ""),
            data.get("patta", ""),
            data.get("tayari", ""),
            data.get("ssc_gun", ""),
            data.get("hsc_gun", ""),
            data.get("graduation_padvi", ""),
            data.get("graduation_gun", ""),
            data.get("post_graduation_padvi", ""),
            data.get("post_graduation_gun", ""),
        ]
        gs.append_row(gs.SHEET_ADMISSIONS, row)
        _invalidate_cache()
        return True
    except Exception as e:
        st.error(f"विद्यार्थी जतन करताना त्रुटी: {e}")
        return False


def update_student(student_id: int, data: dict) -> bool:
    """Update an existing admission record by id."""
    try:
        updates = {k: v for k, v in data.items()}
        result  = gs.update_row_by_id(gs.SHEET_ADMISSIONS, student_id, updates)
        _invalidate_cache()
        return bool(result)
    except Exception as e:
        st.error(f"विद्यार्थी अपडेट करताना त्रुटी: {e}")
        return False


def delete_student(student_id: int) -> bool:
    try:
        result = gs.delete_row_by_id(gs.SHEET_ADMISSIONS, student_id)
        _invalidate_cache()
        return bool(result)
    except Exception as e:
        st.error(f"विद्यार्थी हटवताना त्रुटी: {e}")
        return False


def save_deposit(student_id, student_name, deposit_amount, deposit_required, remarks="") -> bool:
    try:
        new_id = gs.next_id(gs.SHEET_DEPOSITS)
        row = [
            new_id, student_id, student_name, deposit_amount,
            datetime.now().strftime("%Y-%m-%d"),
            1 if deposit_required else 0,
            remarks, "Admin",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]
        gs.append_row(gs.SHEET_DEPOSITS, row)
        _invalidate_cache()
        return True
    except Exception as e:
        st.error(f"ठेव जतन करताना त्रुटी: {e}")
        return False


def save_fee_payment(student_id, student_name, month, year,
                     amount_paid, payment_type, remarks="") -> bool:
    try:
        new_id = gs.next_id(gs.SHEET_FEE_PAYMENTS)
        row = [
            new_id, student_id, student_name,
            datetime.now().strftime("%Y-%m-%d"),
            month, year, amount_paid, payment_type,
            remarks, "Admin",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]
        gs.append_row(gs.SHEET_FEE_PAYMENTS, row)
        _invalidate_cache()
        return True
    except Exception as e:
        st.error(f"फी जतन करताना त्रुटी: {e}")
        return False


def save_brave_student(name, position, photo_url, display_order=0) -> bool:
    try:
        new_id = gs.next_id(gs.SHEET_BRAVE_STUDENTS)
        row = [
            new_id, name, position, photo_url, display_order,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]
        gs.append_row(gs.SHEET_BRAVE_STUDENTS, row)
        _invalidate_cache()
        return True
    except Exception as e:
        st.error(f"विद्यार्थी गॅलरीत जोडताना त्रुटी: {e}")
        return False


def update_brave_student(student_id, name, position, photo_url) -> bool:
    try:
        result = gs.update_brave_student_row(int(student_id), name, position, photo_url)
        _invalidate_cache()
        return bool(result)
    except Exception as e:
        st.error(f"गॅलरी अपडेट करताना त्रुटी: {e}")
        return False


def delete_brave_student(student_id) -> bool:
    try:
        result = gs.delete_row_by_id(gs.SHEET_BRAVE_STUDENTS, int(student_id))
        _invalidate_cache()
        return bool(result)
    except Exception as e:
        st.error(f"गॅलरीतून हटवताना त्रुटी: {e}")
        return False


def save_uploaded_photo(uploaded_file) -> str | None:
    try:
        photos_dir = Path("student_photos")
        photos_dir.mkdir(exist_ok=True)
        timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
        filename       = f"student_{timestamp}.{file_extension}"
        filepath       = photos_dir / filename
        filepath.write_bytes(uploaded_file.getbuffer())
        return str(filepath)
    except Exception as e:
        st.error(f"फोटो जतन करताना त्रुटी: {e}")
        return None


def get_fee_report(month=None, year=None) -> pd.DataFrame:
    df = fetch_fee_payments()
    if df.empty:
        return df
    if month and year and month != "All" and year != "All":
        df = df[(df["month"] == month) & (df["year"] == int(year))]
    return df.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PDF GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_pdf_report(month: str, year: int) -> BytesIO:
    buffer   = BytesIO()
    doc      = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles   = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title2", parent=styles["Heading1"], fontSize=22,
        textColor=colors.HexColor("#6a1b9a"), spaceAfter=20, alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "Heading3", parent=styles["Heading2"], fontSize=13,
        textColor=colors.HexColor("#004d40"), spaceAfter=10,
    )
    info_style = styles["Normal"].clone("InfoStyle")
    info_style.fontSize = 11

    elements.append(Paragraph("<u>Karmveer Abhyasika</u>", title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"Monthly Fee Report – {month} {year}", heading_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", info_style))
    elements.append(Spacer(1, 16))

    fee_df = get_fee_report(month, year)

    if fee_df.empty:
        elements.append(Paragraph("No payment records found for this period.", styles["Normal"]))
    else:
        total       = len(fee_df)
        total_amt   = fee_df["amount_paid"].sum()
        full_p      = len(fee_df[fee_df["amount_paid"] >= STANDARD_MONTHLY_FEE])
        partial_p   = total - full_p

        elements.append(Paragraph("Summary", heading_style))
        summary_data = [
            ["Total Payments",           str(total)],
            ["Full Payments (≥Rs.600)",  str(full_p)],
            ["Partial Payments",         str(partial_p)],
            ["Total Collection",         f"Rs. {total_amt:,.0f}"],
        ]
        t = Table(summary_data, colWidths=[3*inch, 2*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f0f0f0")),
            ("FONTSIZE",      (0,0), (-1,-1), 11),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("GRID",          (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Payment Details", heading_style))
        rows = [["Sr.", "Student Name", "Date", "Amount", "Type", "Remarks"]]
        for i, row in fee_df.iterrows():
            rows.append([
                str(i+1),
                str(row.get("student_name",""))[:25],
                str(row.get("payment_date","")),
                f"Rs. {float(row.get('amount_paid',0)):.0f}",
                str(row.get("payment_type",""))[:20],
                str(row.get("remarks","") or "-")[:20],
            ])
        dt = Table(rows, colWidths=[0.4*inch, 2*inch, 1.1*inch, 0.9*inch, 1.5*inch, 1.3*inch])
        dt.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#6a1b9a")),
            ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0),  10),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("FONTSIZE",      (0,1), (-1,-1), 8),
            ("BACKGROUND",    (0,1), (-1,-1), colors.beige),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("GRID",          (0,0), (-1,-1), 0.5, colors.black),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        elements.append(dt)

    elements.append(Spacer(1, 24))
    footer = ParagraphStyle("Footer", parent=styles["Normal"],
                            fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph("© 2025 Karmveer Abhyasika | Lonand, Satara", footer))
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ══════════════════════════════════════════════════════════════════════════════
#  CSS (Mobile-first, beautiful)
# ══════════════════════════════════════════════════════════════════════════════

ADMIN_CSS = """
<style>
/* ── Base ── */
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', 'Noto Sans Devanagari', sans-serif; }
.block-container { padding: 0.8rem 1rem 2rem !important; max-width: 100% !important; }

/* ── Metric cards ── */
.metric-card {
    padding: clamp(14px, 3vw, 22px);
    border-radius: 14px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.18);
    margin: 6px 0;
}
.metric-value { font-size: clamp(1.6rem, 6vw, 2.5rem); font-weight: 800; margin: 8px 0; }
.metric-label { font-size: clamp(0.8rem, 2.5vw, 1rem); opacity: 0.9; }

/* ── Header banner ── */
.admin-header {
    background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
    padding: clamp(16px, 4vw, 26px);
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    text-align: center;
}
.admin-header h1 {
    color: #6a1b9a;
    font-size: clamp(1.2rem, 5vw, 2rem);
    margin: 0;
}
.admin-header p { color: #2d3436; font-size: clamp(0.8rem, 2.5vw, 1rem); margin: 4px 0 0; }

/* ── Student row cards ── */
.student-row {
    background: white;
    border-radius: 12px;
    padding: 12px 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 10px;
    border-left: 4px solid #00796b;
}

/* ── Login ── */
.login-wrap {
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding: clamp(30px, 8vw, 60px) clamp(20px, 6vw, 40px);
    border-radius: 20px;
    box-shadow: 0 16px 50px rgba(0,0,0,0.28);
    max-width: 440px;
    margin: clamp(30px, 10vh, 80px) auto;
    text-align: center;
}
.login-wrap h2 { color: white; font-size: clamp(1.4rem, 6vw, 2.4rem); margin-bottom: 6px; }
.login-wrap p  { color: #e0e0e0; font-size: clamp(0.85rem, 2.5vw, 1.1rem); }

/* ── Responsive table ── */
@media (max-width: 640px) {
    [data-testid="column"] { padding: 3px !important; }
    .block-container { padding: 0.5rem 0.6rem 2rem !important; }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] { min-width: 220px !important; }
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════

def login_page():
    st.markdown(ADMIN_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='login-wrap'>
        <div style='font-size:3rem;'>🔐</div>
        <h2>Admin Login</h2>
        <p>Karmveer Abhyasika</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=True):
            st.text_input("👤 Username", value="admin", disabled=True)
            password = st.text_input("🔑 Password", type="password",
                                     placeholder="Enter your password")
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            if submit:
                if password == _get_admin_password():
                    st.session_state["logged_in"] = True
                    st.success("✅ Login Successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect Password!")
        st.caption("💡 Set password via Streamlit Secrets or ADMIN_PASSWORD env var.")


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def admin_dashboard():
    st.markdown(ADMIN_CSS, unsafe_allow_html=True)

    # Header row
    hcol1, hcol2 = st.columns([5, 1])
    with hcol1:
        st.markdown("""
        <div class='admin-header'>
            <h1>🔑 Karmveer Abhyasika Admin Panel</h1>
            <p>Admin Dashboard & Fee Management</p>
        </div>""", unsafe_allow_html=True)
    with hcol2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout_btn",
                     use_container_width=True, type="primary"):
            st.session_state["logged_in"] = False
            st.rerun()

    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:16px;
                    background:linear-gradient(135deg,#a29bfe,#6c5ce7);
                    border-radius:10px;margin-bottom:16px;'>
            <h2 style='color:white;margin:0;font-size:1.2rem;'>📋 Menu</h2>
        </div>""", unsafe_allow_html=True)
        menu = st.radio("Select Option", [
            "📊 Dashboard", "🎓 Students", "💳 Deposits",
            "💰 Fee Management", "📄 Fee Reports", "🌟 Brave Students Gallery",
        ], label_visibility="collapsed")
        st.markdown("---")
        st.info("💡 Standard Fee: Rs. 600/month")
        if st.button("🔄 Refresh Data", use_container_width=True):
            _invalidate_cache()
            st.success("Data refreshed!")
            st.rerun()

    st.markdown("---")

    # ── Load data once ────────────────────────────────────────────────────────
    with st.spinner("डेटा लोड होत आहे…"):
        df     = fetch_all_students_data()
        fee_df = fetch_fee_payments()

    # ══════════════════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    if menu == "📊 Dashboard":
        st.markdown("### 📊 Dashboard Overview")

        curr_month = datetime.now().strftime("%B")
        curr_year  = datetime.now().year
        month_df   = get_fee_report(curr_month, curr_year)

        c1, c2, c3 = st.columns(3)
        total      = len(df)
        male       = len(df[df["ling"] == "पुरुष"]) if not df.empty and "ling" in df.columns else 0
        female     = len(df[df["ling"] == "स्त्री"]) if not df.empty and "ling" in df.columns else 0

        with c1:
            st.markdown(f"""<div class='metric-card'
                style='background:linear-gradient(135deg,#6c5ce7,#a29bfe);'>
                <div class='metric-label'>Total Students</div>
                <div class='metric-value'>{total}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'
                style='background:linear-gradient(135deg,#74b9ff,#0984e3);'>
                <div class='metric-label'>Male Students</div>
                <div class='metric-value'>{male}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class='metric-card'
                style='background:linear-gradient(135deg,#fd79a8,#e84393);'>
                <div class='metric-label'>Female Students</div>
                <div class='metric-value'>{female}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"<br>### 📅 {curr_month} {curr_year}", unsafe_allow_html=True)
        paid_count = len(month_df) if not month_df.empty else 0
        pending    = max(total - paid_count, 0)
        collection = month_df["amount_paid"].sum() if not month_df.empty else 0

        cc1, cc2, cc3 = st.columns(3)
        with cc1: st.metric("Students Paid",       paid_count)
        with cc2: st.metric("Pending Payments",    pending,    delta=f"-{pending}")
        with cc3: st.metric("Month Collection",    f"Rs. {collection:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("#### 📅 Recent Admissions")
            if not df.empty:
                recent = df.tail(5)[
                    [c for c in ["id", "nav", "mobile", "admission_date"] if c in df.columns]
                ].rename(columns={"id":"ID","nav":"Name","mobile":"Mobile","admission_date":"Date"})
                st.dataframe(recent, use_container_width=True, hide_index=True)
            else:
                st.info("No admissions yet")
        with r2:
            st.markdown("#### 💳 Recent Payments")
            if not fee_df.empty:
                rec_fee = fee_df.head(5)[
                    [c for c in ["student_name","amount_paid","payment_date"] if c in fee_df.columns]
                ].rename(columns={"student_name":"Name","amount_paid":"Amount","payment_date":"Date"})
                st.dataframe(rec_fee, use_container_width=True, hide_index=True)
            else:
                st.info("No payments recorded yet")

    # ══════════════════════════════════════════════════════════════════════════
    #  STUDENTS – full CRUD
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "🎓 Students":
        st.markdown("### 🎓 Students Management")
        tab_list, tab_add, tab_edit_del = st.tabs([
            "📋 View / Search", "➕ Add Student", "✏️ Edit / Delete"
        ])

        # ── View & Search ──────────────────────────────────────────────────
        with tab_list:
            students_df = fetch_all_students_data()
            if students_df.empty:
                st.warning("⚠️ No student records found.")
            else:
                search = st.text_input("🔍 Search by name or mobile",
                                       placeholder="Type to search…")
                view_df = students_df.copy()
                if search:
                    mask = view_df.astype(str).apply(
                        lambda x: x.str.contains(search, case=False, na=False)
                    ).any(axis=1)
                    view_df = view_df[mask]

                col_map = {
                    "id":"ID","admission_date":"Admission Date","nav":"Name",
                    "janmatarikh":"DOB","ling":"Gender","mobile":"Mobile",
                    "palak_mobile":"Parent Mobile","email":"Email","patta":"Address",
                }
                display_df   = view_df.rename(columns=col_map)
                display_cols = ["ID","Admission Date","Name","DOB","Gender",
                                "Mobile","Parent Mobile"]
                avail        = [c for c in display_cols if c in display_df.columns]

                st.success(f"📊 Records: {len(display_df)}")
                st.dataframe(display_df[avail], use_container_width=True,
                             height=380, hide_index=True)
                csv = display_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", data=csv,
                    file_name=f"students_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv")

        # ── Add Student ────────────────────────────────────────────────────
        with tab_add:
            st.markdown("#### ➕ New Student Admission")
            with st.form("add_student_form", clear_on_submit=True):
                cols = st.columns(2)
                with cols[0]:
                    s_name    = st.text_input("विद्यार्थ्याचे नाव *", placeholder="पूर्ण नाव")
                    s_dob     = st.date_input("जन्मतारीख", value=None)
                    s_gender  = st.selectbox("लिंग", ["पुरुष", "स्त्री", "इतर"])
                    s_mobile  = st.text_input("मोबाईल *", placeholder="10 अंक")
                    s_pmobile = st.text_input("पालक मोबाईल", placeholder="10 अंक")
                with cols[1]:
                    s_email   = st.text_input("Email", placeholder="email@example.com")
                    s_address = st.text_area("पत्ता", placeholder="संपूर्ण पत्ता", height=80)
                    s_tayari  = st.text_input("परीक्षा / तयारी", placeholder="UPSC, MPSC …")
                    s_ssc     = st.text_input("SSC गुण", placeholder="टक्केवारी")
                    s_hsc     = st.text_input("HSC गुण", placeholder="टक्केवारी")

                grad_cols = st.columns(2)
                with grad_cols[0]:
                    s_grad_padvi = st.text_input("Graduation पदवी")
                    s_grad_gun   = st.text_input("Graduation गुण")
                with grad_cols[1]:
                    s_pg_padvi   = st.text_input("Post Graduation पदवी")
                    s_pg_gun     = st.text_input("Post Graduation गुण")

                s_adm_date = st.date_input("Admission Date", value=datetime.now())
                submitted  = st.form_submit_button("💾 Add Student", use_container_width=True,
                                                   type="primary")
                if submitted:
                    if not s_name or not s_mobile:
                        st.error("❌ नाव आणि मोबाईल आवश्यक आहे!")
                    elif len(s_mobile) != 10 or not s_mobile.isdigit():
                        st.error("❌ मोबाईल नंबर 10 अंकी असावा!")
                    else:
                        data = {
                            "admission_date":       str(s_adm_date),
                            "nav":                  s_name,
                            "janmatarikh":          str(s_dob) if s_dob else "",
                            "ling":                 s_gender,
                            "mobile":               s_mobile,
                            "palak_mobile":         s_pmobile,
                            "email":                s_email,
                            "patta":                s_address,
                            "tayari":               s_tayari,
                            "ssc_gun":              s_ssc,
                            "hsc_gun":              s_hsc,
                            "graduation_padvi":     s_grad_padvi,
                            "graduation_gun":       s_grad_gun,
                            "post_graduation_padvi": s_pg_padvi,
                            "post_graduation_gun":   s_pg_gun,
                        }
                        if save_student(data):
                            st.success(f"✅ {s_name} यशस्वीरित्या जोडले!")
                            st.balloons()

        # ── Edit / Delete ──────────────────────────────────────────────────
        with tab_edit_del:
            st.markdown("#### ✏️ Edit or Delete a Student")
            students_df = fetch_all_students_data()
            if students_df.empty:
                st.info("No students found.")
            else:
                search2 = st.text_input("🔍 Search student", placeholder="नाव किंवा मोबाईल",
                                        key="search_edit")
                disp_df = students_df.copy()
                if search2:
                    mask = disp_df.astype(str).apply(
                        lambda x: x.str.contains(search2, case=False, na=False)
                    ).any(axis=1)
                    disp_df = disp_df[mask]

                if disp_df.empty:
                    st.warning("No matching students found.")
                else:
                    options = {
                        f"{r['nav']} (ID: {r['id']}, Mobile: {r.get('mobile','')})": r["id"]
                        for _, r in disp_df.iterrows()
                    }
                    selected_label = st.selectbox("Select Student", list(options.keys()))
                    sel_id         = options[selected_label]
                    sel_row        = students_df[students_df["id"].astype(str) == str(sel_id)].iloc[0]

                    action = st.radio("Action", ["✏️ Edit", "🗑️ Delete"],
                                      horizontal=True, key="edit_del_action")

                    if action == "🗑️ Delete":
                        st.warning(f"⚠️ '{sel_row['nav']}' हा विद्यार्थी कायमचा हटवणार!")
                        confirm = st.checkbox("हो, मला खात्री आहे – हटवा")
                        if confirm and st.button("🗑️ Delete Student", type="primary"):
                            if delete_student(int(sel_id)):
                                st.success(f"✅ {sel_row['nav']} हटवले!")
                                st.rerun()

                    else:  # Edit
                        with st.form("edit_student_form"):
                            ec = st.columns(2)
                            with ec[0]:
                                e_name    = st.text_input("नाव", value=str(sel_row.get("nav","")))
                                e_gender  = st.selectbox("लिंग", ["पुरुष","स्त्री","इतर"],
                                    index=["पुरुष","स्त्री","इतर"].index(
                                        sel_row.get("ling","पुरुष"))
                                    if sel_row.get("ling","पुरुष") in ["पुरुष","स्त्री","इतर"] else 0)
                                e_mobile  = st.text_input("मोबाईल", value=str(sel_row.get("mobile","")))
                                e_pmobile = st.text_input("पालक मोबाईल", value=str(sel_row.get("palak_mobile","")))
                                e_email   = st.text_input("Email", value=str(sel_row.get("email","")))
                            with ec[1]:
                                e_address = st.text_area("पत्ता", value=str(sel_row.get("patta","")), height=80)
                                e_tayari  = st.text_input("परीक्षा/तयारी", value=str(sel_row.get("tayari","")))
                                e_ssc     = st.text_input("SSC गुण", value=str(sel_row.get("ssc_gun","")))
                                e_hsc     = st.text_input("HSC गुण", value=str(sel_row.get("hsc_gun","")))

                            eg_cols = st.columns(2)
                            with eg_cols[0]:
                                e_grad_padvi = st.text_input("Graduation पदवी", value=str(sel_row.get("graduation_padvi","")))
                                e_grad_gun   = st.text_input("Graduation गुण", value=str(sel_row.get("graduation_gun","")))
                            with eg_cols[1]:
                                e_pg_padvi = st.text_input("PG पदवी", value=str(sel_row.get("post_graduation_padvi","")))
                                e_pg_gun   = st.text_input("PG गुण", value=str(sel_row.get("post_graduation_gun","")))

                            save_btn = st.form_submit_button("💾 Update Student",
                                                              use_container_width=True, type="primary")
                            if save_btn:
                                if not e_name or not e_mobile:
                                    st.error("❌ नाव आणि मोबाईल आवश्यक!")
                                else:
                                    upd = {
                                        "nav": e_name, "ling": e_gender,
                                        "mobile": e_mobile, "palak_mobile": e_pmobile,
                                        "email": e_email, "patta": e_address,
                                        "tayari": e_tayari, "ssc_gun": e_ssc,
                                        "hsc_gun": e_hsc,
                                        "graduation_padvi": e_grad_padvi,
                                        "graduation_gun": e_grad_gun,
                                        "post_graduation_padvi": e_pg_padvi,
                                        "post_graduation_gun": e_pg_gun,
                                    }
                                    if update_student(int(sel_id), upd):
                                        st.success(f"✅ {e_name} अपडेट झाले!")
                                        st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    #  DEPOSITS
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "💳 Deposits":
        st.markdown("### 💳 Deposit Management")
        students_df = fetch_all_students_data()
        if students_df.empty:
            st.warning("⚠️ No students found.")
            st.stop()

        tab1, tab2 = st.tabs(["📝 Record Deposit", "📋 View Deposits"])

        with tab1:
            with st.form("deposit_form", clear_on_submit=True):
                student_opts = {
                    f"{r['nav']} (ID: {r['id']})": r["id"]
                    for _, r in students_df.iterrows()
                }
                sel_student      = st.selectbox("Student", list(student_opts.keys()))
                deposit_required = st.radio("Deposit Status",
                    ["Deposit Required", "Exempted"], horizontal=True)
                amount = st.number_input(
                    "Amount (Rs.)", min_value=0, value=1000, step=100
                ) if "Required" in deposit_required else 0
                if "Exempted" in deposit_required:
                    st.info("✅ Student exempted from deposit")
                remarks = st.text_area("Remarks")
                if st.form_submit_button("💾 Save Deposit", use_container_width=True,
                                         type="primary"):
                    sid   = student_opts[sel_student]
                    sname = sel_student.split(" (ID:")[0]
                    req   = "Required" in deposit_required
                    if save_deposit(sid, sname, amount, req, remarks):
                        st.success(f"✅ Deposit saved for {sname}!")
                        st.balloons()
                        st.rerun()

        with tab2:
            dep_df = fetch_deposits()
            if dep_df.empty:
                st.info("No deposit records found.")
            else:
                disp = dep_df.copy()
                disp["deposit_required"] = disp["deposit_required"].apply(
                    lambda x: "Required" if str(x) == "1" else "Exempted")
                disp = disp.rename(columns={
                    "student_name":"Name","deposit_amount":"Amount (Rs.)",
                    "deposit_date":"Date","deposit_required":"Status","remarks":"Remarks"
                })
                show = [c for c in ["Name","Amount (Rs.)","Date","Status","Remarks"]
                        if c in disp.columns]
                st.dataframe(disp[show], use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  FEE MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "💰 Fee Management":
        st.markdown("### 💰 Fee Management")
        students_df = fetch_all_students_data()
        if students_df.empty:
            st.warning("⚠️ No students found.")
            st.stop()

        st.markdown("#### 📝 Record Fee Payment")
        col1, col2 = st.columns([3, 1])

        with col1:
            student_opts = {
                f"{r['nav']} (ID: {r['id']})": r["id"]
                for _, r in students_df.iterrows()
            }
            sel_student = st.selectbox("Student", list(student_opts.keys()),
                                       key="fee_student")
            c1, c2 = st.columns(2)
            with c1:
                curr_mo = datetime.now().strftime("%B")
                months  = list(calendar.month_name)[1:]
                month   = st.selectbox("Month", months,
                    index=months.index(curr_mo), key="fee_month")
            with c2:
                year = st.number_input("Year", min_value=2020, max_value=2030,
                                       value=datetime.now().year, key="fee_year")

            pay_opt = st.radio("Payment Option",
                ["Full Payment (Rs. 600)", "Custom Amount"], horizontal=True)
            if pay_opt.startswith("Full"):
                amount_paid  = STANDARD_MONTHLY_FEE
                payment_type = "Full Payment"
                st.success(f"Amount: Rs. {amount_paid}")
            else:
                amount_paid = st.number_input("Custom Amount (Rs.)",
                    min_value=1, max_value=10000, value=300, step=50)
                payment_type = ("Full/Over Payment" if amount_paid >= STANDARD_MONTHLY_FEE
                                else "Partial Payment")
                st.info(f"Type: {payment_type}")

            remarks = st.text_area("Remarks (Optional)", key="fee_remarks")

            if st.button("💾 Save Payment", type="primary", use_container_width=True):
                sid   = student_opts[sel_student]
                sname = sel_student.split(" (ID:")[0]
                if save_fee_payment(sid, sname, month, year,
                                    amount_paid, payment_type, remarks):
                    st.session_state.update(
                        payment_saved=True,
                        saved_student=sname,
                        saved_amount=amount_paid,
                    )
                    st.rerun()

            if st.session_state.get("payment_saved"):
                st.success(
                    f"✅ Rs. {st.session_state['saved_amount']} recorded "
                    f"for {st.session_state['saved_student']}!")
                st.balloons()
                if st.button("✔ OK / New Payment", type="primary"):
                    st.session_state["payment_saved"] = False
                    st.rerun()

        with col2:
            st.markdown("#### 💵 Fee Info")
            st.info("**Standard Monthly:** Rs. 600\n\n"
                    "Accept full or partial payments.\n\n"
                    "All records saved instantly.")

    # ══════════════════════════════════════════════════════════════════════════
    #  FEE REPORTS
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "📄 Fee Reports":
        st.markdown("### 📄 Fee Reports & Analytics")

        c1, c2, _ = st.columns([2, 2, 3])
        with c1:
            rep_month = st.selectbox("Month", ["All"] + list(calendar.month_name)[1:])
        with c2:
            yr_opts   = ["All"] + list(range(datetime.now().year, 2019, -1))
            rep_year  = st.selectbox("Year", yr_opts)

        rep_df = get_fee_report(rep_month, rep_year)

        if rep_df.empty:
            st.warning("⚠️ No records found for selected period.")
        else:
            total   = len(rep_df)
            full_p  = len(rep_df[rep_df["amount_paid"] >= STANDARD_MONTHLY_FEE])
            part_p  = total - full_p
            tot_amt = rep_df["amount_paid"].sum()

            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Total Payments", total)
            with m2: st.metric("Full (≥600)", full_p)
            with m3: st.metric("Partial", part_p)
            with m4: st.metric("Total Collected", f"Rs. {tot_amt:,.0f}")

            st.markdown("---")
            disp_cols  = ["student_name","month","year","amount_paid",
                          "payment_date","remarks","payment_type"]
            avail_cols = [c for c in disp_cols if c in rep_df.columns]
            rep_show   = rep_df[avail_cols].copy()
            rep_show.columns = ["Student","Month","Year","Amount (Rs.)",
                                 "Date","Remarks","Type"][:len(avail_cols)]
            st.dataframe(rep_show, use_container_width=True, hide_index=True)

            dl1, dl2 = st.columns(2)
            with dl1:
                csv = rep_show.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ CSV", data=csv,
                    file_name=f"fee_{rep_month}_{rep_year}.csv", mime="text/csv",
                    use_container_width=True)
            with dl2:
                if rep_month != "All" and rep_year != "All":
                    pdf = generate_pdf_report(rep_month, int(rep_year))
                    st.download_button("📄 PDF", data=pdf,
                        file_name=f"fee_{rep_month}_{rep_year}.pdf",
                        mime="application/pdf", use_container_width=True)
                else:
                    st.info("Specific month & year required for PDF.")

    # ══════════════════════════════════════════════════════════════════════════
    #  BRAVE STUDENTS GALLERY
    # ══════════════════════════════════════════════════════════════════════════
    elif menu == "🌟 Brave Students Gallery":
        st.markdown("### 🌟 Brave Students Gallery")
        tab_add, tab_manage = st.tabs(["➕ Add Student", "📋 Manage Students"])

        with tab_add:
            col1, col2 = st.columns([2, 1])
            with col1:
                new_name     = st.text_input("Student Name *", key="bs_name")
                new_position = st.text_input("Position / Achievement *", key="bs_pos")
                photo_src    = st.radio("Photo Source",
                    ["Upload from PC", "Enter URL"], horizontal=True)

                photo_val    = None
                uploaded_f   = None
                if photo_src == "Upload from PC":
                    uploaded_f = st.file_uploader("Choose photo",
                        type=["png","jpg","jpeg"], key="bs_upload")
                    if uploaded_f:
                        photo_val = "uploaded"
                else:
                    photo_val = st.text_input("Photo URL (https://…)", key="bs_url")

                if st.button("➕ Add to Gallery", type="primary",
                             use_container_width=True):
                    if not new_name or not new_position or not photo_val:
                        st.error("❌ सर्व माहिती भरा!")
                    else:
                        if photo_src == "Upload from PC" and uploaded_f:
                            fp = save_uploaded_photo(uploaded_f)
                            if fp and save_brave_student(new_name, new_position, fp):
                                st.success(f"✅ {new_name} गॅलरीत जोडले!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ फोटो जतन झाला नाही!")
                        elif photo_src == "Enter URL":
                            if save_brave_student(new_name, new_position, photo_val):
                                st.success(f"✅ {new_name} गॅलरीत जोडले!")
                                st.balloons()
                                st.rerun()

            with col2:
                st.markdown("#### 👁️ Preview")
                if photo_src == "Upload from PC" and uploaded_f:
                    try:
                        st.image(uploaded_f, caption=new_name or "Preview", width=190)
                    except Exception:
                        st.warning("Preview उपलब्ध नाही")
                elif photo_src == "Enter URL" and photo_val:
                    try:
                        st.image(photo_val, caption=new_name or "Preview", width=190)
                    except Exception:
                        st.warning("⚠️ Invalid image URL")
                else:
                    st.info("फोटो जोडल्यावर preview दिसेल")

        with tab_manage:
            brave_df = fetch_brave_students()
            if brave_df.empty:
                st.info("📭 गॅलरीत अद्याप विद्यार्थी नाहीत.")
            else:
                st.success(f"📊 Total: {len(brave_df)} students")
                for _, row in brave_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4 = st.columns([1, 3, 3, 2])
                        with c1:
                            try:
                                st.image(row["photo_url"], width=72)
                            except Exception:
                                st.markdown("🖼️")
                        with c2:
                            st.markdown(f"**{row['name']}**")
                            st.caption(row["position"])
                        with c3:
                            st.caption(f"ID: {row['id']}")
                            st.caption(f"Added: {str(row.get('created_at',''))[:10]}")
                        with c4:
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("✏️", key=f"edit_{row['id']}", help="Edit"):
                                    st.session_state[f"edit_bs_{row['id']}"] = True
                            with b2:
                                if st.button("🗑️", key=f"del_{row['id']}", help="Delete"):
                                    if delete_brave_student(row["id"]):
                                        st.success(f"✅ {row['name']} हटवले!")
                                        st.rerun()

                        if st.session_state.get(f"edit_bs_{row['id']}", False):
                            with st.form(f"edit_bs_{row['id']}"):
                                st.markdown(f"**Edit: {row['name']}**")
                                e_n = st.text_input("Name", value=row["name"],
                                                    key=f"en_{row['id']}")
                                e_p = st.text_input("Position", value=row["position"],
                                                    key=f"ep_{row['id']}")
                                e_ph= st.text_input("Photo URL", value=row["photo_url"],
                                                    key=f"eph_{row['id']}")
                                s_c, c_c = st.columns(2)
                                with s_c:
                                    if st.form_submit_button("💾 Save",
                                                              use_container_width=True):
                                        if update_brave_student(row["id"], e_n, e_p, e_ph):
                                            st.success("✅ Updated!")
                                            st.session_state[f"edit_bs_{row['id']}"] = False
                                            st.rerun()
                                with c_c:
                                    if st.form_submit_button("❌ Cancel",
                                                              use_container_width=True):
                                        st.session_state[f"edit_bs_{row['id']}"] = False
                                        st.rerun()
                        st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if "logged_in"     not in st.session_state: st.session_state["logged_in"]     = False
if "payment_saved" not in st.session_state: st.session_state["payment_saved"] = False

if st.session_state["logged_in"]:
    admin_dashboard()
else:
    login_page()