# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

import gsheets_config as gs

ADMIN_PASSWORD     = "admin123"
STANDARD_MONTHLY_FEE = 600


# ── Database-equivalent functions (Google Sheets) ──────────────────────────────

def fetch_all_students_data() -> pd.DataFrame:
    """Fetch all student admission records from Google Sheets."""
    try:
        df = gs.sheet_to_df(gs.SHEET_ADMISSIONS)
        if df.empty:
            return pd.DataFrame()
        # Keep only columns that exist (mirrors the SQLite SELECT)
        wanted = [
            "id", "admission_date", "nav", "janmatarikh", "ling", "mobile",
            "palak_mobile", "email", "patta", "tayari", "ssc_gun", "hsc_gun",
            "graduation_padvi", "graduation_gun", "post_graduation_padvi",
            "post_graduation_gun"
        ]
        existing = [c for c in wanted if c in df.columns]
        return df[existing]
    except Exception as e:
        st.error(f"Error fetching students: {e}")
        return pd.DataFrame()


def save_deposit(student_id, student_name, deposit_amount, deposit_required, remarks="") -> bool:
    """Save deposit record to Google Sheets."""
    try:
        new_id = gs.next_id(gs.SHEET_DEPOSITS)
        row = [
            new_id,
            student_id,
            student_name,
            deposit_amount,
            datetime.now().strftime("%Y-%m-%d"),
            1 if deposit_required else 0,
            remarks,
            "Admin",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]
        gs.append_row(gs.SHEET_DEPOSITS, row)
        return True
    except Exception as e:
        st.error(f"Error saving deposit: {e}")
        return False


def get_student_deposit(student_id) -> pd.DataFrame:
    """Get deposit info for a student."""
    try:
        df = gs.sheet_to_df(gs.SHEET_DEPOSITS)
        if df.empty:
            return pd.DataFrame()
        return df[df["student_id"].astype(str) == str(student_id)]
    except Exception:
        return pd.DataFrame()


def save_fee_payment(student_id, student_name, month, year,
                     amount_paid, payment_type, remarks="") -> bool:
    """Save fee payment record to Google Sheets."""
    try:
        new_id = gs.next_id(gs.SHEET_FEE_PAYMENTS)
        row = [
            new_id,
            student_id,
            student_name,
            datetime.now().strftime("%Y-%m-%d"),
            month,
            year,
            amount_paid,
            payment_type,
            remarks,
            "Admin",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]
        gs.append_row(gs.SHEET_FEE_PAYMENTS, row)
        return True
    except Exception as e:
        st.error(f"Error saving payment: {e}")
        return False


def get_fee_report(month=None, year=None) -> pd.DataFrame:
    """Get fee payment report from Google Sheets."""
    try:
        df = gs.sheet_to_df(gs.SHEET_FEE_PAYMENTS)
        if df.empty:
            return pd.DataFrame()

        df["amount_paid"] = pd.to_numeric(df["amount_paid"], errors="coerce").fillna(0)
        df["year"]        = pd.to_numeric(df["year"],        errors="coerce")

        if month and year and month != "All" and year != "All":
            df = df[(df["month"] == month) & (df["year"] == int(year))]

        return df.sort_values("payment_date", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"Error fetching fee report: {e}")
        return pd.DataFrame()


def save_brave_student(name, position, photo_url, display_order=0) -> bool:
    """Save a brave student to the gallery sheet."""
    try:
        new_id = gs.next_id(gs.SHEET_BRAVE_STUDENTS)
        row = [
            new_id,
            name,
            position,
            photo_url,
            display_order,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]
        gs.append_row(gs.SHEET_BRAVE_STUDENTS, row)
        return True
    except Exception as e:
        st.error(f"Error saving brave student: {e}")
        return False


def save_uploaded_photo(uploaded_file):
    """Save uploaded photo locally and return the file path."""
    import os
    photos_dir = "student_photos"
    if not os.path.exists(photos_dir):
        os.makedirs(photos_dir)
    timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = uploaded_file.name.split(".")[-1]
    filename       = f"student_{timestamp}.{file_extension}"
    filepath       = os.path.join(photos_dir, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath
    except Exception as e:
        st.error(f"Error saving photo: {e}")
        return None


def get_all_brave_students() -> pd.DataFrame:
    """Get all brave students ordered by display_order."""
    try:
        df = gs.sheet_to_df(gs.SHEET_BRAVE_STUDENTS)
        if df.empty:
            return pd.DataFrame()
        df["display_order"] = pd.to_numeric(df["display_order"], errors="coerce").fillna(0)
        return df.sort_values(["display_order", "id"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def delete_brave_student(student_id) -> bool:
    return gs.delete_row_by_id(gs.SHEET_BRAVE_STUDENTS, int(student_id))


def update_brave_student(student_id, name, position, photo_url) -> bool:
    return gs.update_brave_student_row(int(student_id), name, position, photo_url)


# ── PDF generation (unchanged) ─────────────────────────────────────────────────

def generate_pdf_report(month, year):
    buffer = BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles   = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontSize=24,
        textColor=colors.HexColor("#6a1b9a"), spaceAfter=30, alignment=TA_CENTER
    )
    heading_center_style = ParagraphStyle(
        "CustomTitle2", parent=styles["Heading1"], fontSize=17,
        textColor=colors.HexColor("#004d40"), spaceAfter=30, alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        "CustomHeading", parent=styles["Heading2"], fontSize=14,
        textColor=colors.HexColor("#004d40"), spaceAfter=12
    )
    info_style = styles["Normal"].clone("InfoStyle")
    info_style.fontSize = 12

    elements.append(Paragraph("<u>Karmveer Abhyasika</u>", title_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<u>Monthly Fee Report</u>", heading_center_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Report Period:</b> {month} {year}", info_style))
    elements.append(Paragraph(
        f"<b>Generated On:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", info_style))
    elements.append(Spacer(1, 20))

    fee_df = get_fee_report(month, year)

    if fee_df.empty:
        elements.append(Paragraph("No payment records found for this period.", styles["Normal"]))
    else:
        total_payments  = len(fee_df)
        total_amount    = fee_df["amount_paid"].sum()
        full_payments   = len(fee_df[fee_df["amount_paid"] >= STANDARD_MONTHLY_FEE])
        partial_payments = len(fee_df[fee_df["amount_paid"] < STANDARD_MONTHLY_FEE])

        elements.append(Paragraph("Summary", heading_style))
        summary_data = [
            ["Total Payments",          str(total_payments)],
            ["Full Payments (Rs. 600)", str(full_payments)],
            ["Partial Payments",        str(partial_payments)],
            ["Total Collection",        f"Rs. {total_amount:,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
            ("TEXTCOLOR",   (0, 0), (-1, -1), colors.black),
            ("ALIGN",       (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("GRID",        (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        elements.append(Paragraph("Payment Details", heading_style))
        table_data = [["Sr.", "Student Name", "Date", "Amount", "Type", "Remarks"]]
        for idx, row in fee_df.iterrows():
            table_data.append([
                str(idx + 1),
                str(row["student_name"])[:25],
                str(row["payment_date"]),
                f"Rs. {float(row['amount_paid']):.2f}",
                str(row["payment_type"])[:20],
                str(row["remarks"])[:20] if pd.notna(row["remarks"]) else "-",
            ])
        detail_table = Table(
            table_data,
            colWidths=[0.5*inch, 2*inch, 1.2*inch, 1*inch, 1.5*inch, 1.3*inch]
        )
        detail_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#6a1b9a")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.whitesmoke),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  11),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  12),
            ("BACKGROUND",    (0, 1), (-1, -1), colors.beige),
            ("GRID",          (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE",      (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        elements.append(detail_table)

    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=9,
        textColor=colors.grey, alignment=TA_CENTER
    )
    elements.append(Paragraph("© 2025 Karmveer Abhyasika | Lonand, Satara", footer_style))
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ── Login page (unchanged) ─────────────────────────────────────────────────────

def login_page():
    st.markdown("""
    <style>
    .login-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 60px 40px;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 80px auto;
        max-width: 450px;
        animation: fadeIn 0.8s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .login-title    { color:white; font-size:3em; text-align:center; margin-bottom:10px;
                      text-shadow:2px 2px 4px rgba(0,0,0,0.3); font-weight:700; }
    .login-subtitle { color:#f0f0f0; font-size:1.3em; text-align:center;
                      margin-bottom:30px; font-weight:300; }
    .welcome-text   { color:#e0e0e0; text-align:center; font-size:0.95em; margin-top:20px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-container">
        <div class="login-title">🔐</div>
        <div class="login-title">Admin Login</div>
        <div class="login-subtitle">Karmveer Abhyasika</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=True):
            st.text_input("👤 Username", value="admin", disabled=True)
            password = st.text_input("🔑 Password", type="password",
                                     placeholder="Enter your password")
            _, col_b, _ = st.columns([1, 2, 1])
            with col_b:
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
            if submit:
                if password == ADMIN_PASSWORD:
                    st.session_state["logged_in"] = True
                    st.success("✅ Login Successful!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Incorrect Password!")
        st.info("💡 Default Password: admin123")
        st.markdown("""
        <div class="welcome-text">
            <p>📚 Welcome to Admin Panel</p>
            <p>Manage students, fees & reports</p>
        </div>
        """, unsafe_allow_html=True)


# ── Admin Dashboard (layout/UX unchanged, DB calls replaced) ──────────────────

def admin_dashboard():
    st.markdown("""
    <style>
    .metric-card  { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                    padding:20px; border-radius:15px; color:white; text-align:center;
                    box-shadow:0 4px 15px rgba(0,0,0,0.2); margin:10px 0; }
    .metric-value { font-size:2.5em; font-weight:bold; margin:10px 0; }
    .metric-label { font-size:1.1em; opacity:0.9; }
    .header-container { background:linear-gradient(135deg,#ffeaa7 0%,#fdcb6e 100%);
                        padding:25px; border-radius:15px;
                        box-shadow:0 4px 15px rgba(0,0,0,0.1);
                        margin-bottom:30px; text-align:center; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("""
        <div class="header-container">
            <h1 style="color:#6a1b9a;margin:0;font-size:2.2em;">
                🔑 Karmveer Abhyasika Admin Panel
            </h1>
            <p style="color:#2d3436;margin:5px 0 0 0;">Admin Dashboard & Fee Management</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True, type="primary"):
            st.session_state["logged_in"] = False
            st.success("👋 Logged out successfully!")
            st.rerun()

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:20px;
                    background:linear-gradient(135deg,#a29bfe,#6c5ce7);
                    border-radius:10px;margin-bottom:20px;'>
            <h2 style='color:white;margin:0;'>📋 Menu</h2>
        </div>
        """, unsafe_allow_html=True)
        menu_selection = st.radio(
            "Select Option",
            ("📊 Dashboard", "🎓 Students", "💳 Deposits",
             "💰 Fee Management", "📄 Fee Reports", "🌟 Brave Students Gallery"),
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.info("💡 Standard Monthly Fee: Rs. 600")

    st.markdown("---")

    df     = fetch_all_students_data()
    fee_df = get_fee_report()

    # ── Dashboard ──────────────────────────────────────────────────────────────
    if menu_selection == "📊 Dashboard":
        st.markdown("### 📊 Dashboard Overview")

        current_month    = datetime.now().strftime("%B")
        current_year     = datetime.now().year
        current_month_df = get_fee_report(current_month, current_year)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="background:linear-gradient(135deg,#6c5ce7,#a29bfe);">
                <div class="metric-label">Total Students</div>
                <div class="metric-value">{len(df)}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            male = len(df[df["ling"] == "पुरुष"]) if not df.empty and "ling" in df.columns else 0
            st.markdown(f"""
            <div class="metric-card" style="background:linear-gradient(135deg,#74b9ff,#0984e3);">
                <div class="metric-label">Male Students</div>
                <div class="metric-value">{male}</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            female = len(df[df["ling"] == "स्त्री"]) if not df.empty and "ling" in df.columns else 0
            st.markdown(f"""
            <div class="metric-card" style="background:linear-gradient(135deg,#fd79a8,#e84393);">
                <div class="metric-label">Female Students</div>
                <div class="metric-value">{female}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 📅 {current_month} {current_year} Statistics")

        col1, col2, col3 = st.columns(3)
        paid_count = len(current_month_df) if not current_month_df.empty else 0
        pending    = len(df) - paid_count
        collection = current_month_df["amount_paid"].sum() if not current_month_df.empty else 0

        with col1: st.metric("Students Paid", paid_count)
        with col2: st.metric("Pending Payments", pending, delta=f"-{pending}")
        with col3: st.metric("This Month Collection", f"Rs. {collection:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📅 Recent Admissions")
            if not df.empty:
                recent_df = df.tail(5)[["id", "nav", "mobile", "admission_date"]]
                recent_df.columns = ["ID", "Name", "Mobile", "Date"]
                st.dataframe(recent_df, use_container_width=True, hide_index=True)
            else:
                st.info("No admissions yet")
        with col2:
            st.markdown("#### 💳 Recent Payments")
            if not fee_df.empty:
                recent_fee = fee_df.head(5)[["student_name", "amount_paid", "payment_date"]]
                recent_fee.columns = ["Name", "Amount", "Date"]
                st.dataframe(recent_fee, use_container_width=True, hide_index=True)
            else:
                st.info("No payments recorded yet")

    # ── Students ───────────────────────────────────────────────────────────────
    elif menu_selection == "🎓 Students":
        st.markdown("### 🎓 Students List")
        students_df = fetch_all_students_data()

        if students_df.empty:
            st.warning("⚠️ No student records found.")
            st.info("💡 Fill the admission form to see records here.")
        else:
            search_term = st.text_input("🔍 Search by name or mobile",
                                        placeholder="Type to search...")
            if search_term:
                mask = students_df.astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                students_df = students_df[mask]

            column_mapping = {
                "id": "ID", "admission_date": "Admission Date", "nav": "Name",
                "janmatarikh": "DOB", "ling": "Gender", "mobile": "Mobile",
                "palak_mobile": "Parent Mobile", "email": "Email", "patta": "Address",
            }
            display_df   = students_df.rename(columns=column_mapping)
            display_cols = ["ID", "Admission Date", "Name", "DOB", "Gender",
                            "Mobile", "Parent Mobile"]
            available = [c for c in display_cols if c in display_df.columns]

            st.success(f"📊 Total Records: {len(display_df)}")
            st.dataframe(display_df[available], use_container_width=True,
                         height=400, hide_index=True)

            csv = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download CSV", data=csv,
                file_name=f'students_list_{datetime.now().strftime("%Y%m%d")}.csv',
                mime="text/csv", key="download_students_csv"
            )

    # ── Deposits ───────────────────────────────────────────────────────────────
    elif menu_selection == "💳 Deposits":
        st.markdown("### 💳 Deposit Management")
        students_df = fetch_all_students_data()

        if students_df.empty:
            st.warning("⚠️ No students found. Please add students first.")
        else:
            tab1, tab2 = st.tabs(["📝 Record Deposit", "📋 View Deposits"])

            with tab1:
                st.markdown("#### Record Student Deposit")
                col1, col2 = st.columns([2, 1])
                with col1:
                    with st.form("deposit_form", clear_on_submit=True):
                        student_options = {
                            f"{row['nav']} (ID: {row['id']})": row["id"]
                            for _, row in students_df.iterrows()
                        }
                        selected_student = st.selectbox(
                            "Select Student", options=list(student_options.keys()))
                        deposit_required = st.radio(
                            "Deposit Requirement",
                            options=["Deposit Required", "No Deposit (Exempted)"],
                            horizontal=True
                        )
                        if "Required" in deposit_required:
                            deposit_amount = st.number_input(
                                "Deposit Amount (Rs.)", min_value=0, value=1000, step=100)
                        else:
                            deposit_amount = 0
                            st.info("✅ Student is exempted from deposit")

                        remarks = st.text_area("Remarks", placeholder="Add any notes...")
                        submit  = st.form_submit_button(
                            "💾 Save Deposit Record", use_container_width=True)

                        if submit:
                            student_id   = student_options[selected_student]
                            student_name = selected_student.split(" (ID:")[0]
                            req          = 1 if "Required" in deposit_required else 0
                            if save_deposit(student_id, student_name, deposit_amount,
                                            req, remarks):
                                st.success(f"✅ Deposit record saved for {student_name}!")
                                st.balloons()
                                st.rerun()

                with col2:
                    st.markdown("#### 💡 Deposit Info")
                    st.info("""
                    **Purpose:**
                    Record deposits at admission time.

                    **Options:**
                    - With Deposit: Enter amount
                    - No Deposit: Mark as exempted

                    Track who paid deposits and who didn't.
                    """)

            with tab2:
                st.markdown("#### All Deposit Records")
                deposit_df = gs.sheet_to_df(gs.SHEET_DEPOSITS)
                if deposit_df.empty:
                    st.info("No deposit records found")
                else:
                    display_deposit_df = deposit_df.copy()
                    display_deposit_df["deposit_required"] = \
                        display_deposit_df["deposit_required"].apply(
                            lambda x: "Required" if str(x) == "1" else "Exempted")
                    display_deposit_df = display_deposit_df.rename(columns={
                        "student_name":    "Name",
                        "deposit_amount":  "Amount (Rs.)",
                        "deposit_date":    "Date",
                        "deposit_required": "Deposit Status",
                        "remarks":         "Remarks",
                    })
                    show_cols = [c for c in
                                 ["Name", "Amount (Rs.)", "Date", "Deposit Status", "Remarks"]
                                 if c in display_deposit_df.columns]
                    st.dataframe(display_deposit_df[show_cols],
                                 use_container_width=True, hide_index=True)

    # ── Fee Management ─────────────────────────────────────────────────────────
    elif menu_selection == "💰 Fee Management":
        st.markdown("### 💰 Fee Management System")
        students_df = fetch_all_students_data()

        if students_df.empty:
            st.warning("⚠️ No students found. Please add students first.")
        else:
            st.markdown("#### 📝 Record Fee Payment")
            col1, col2 = st.columns([2, 1])

            with col1:
                student_options = {
                    f"{row['nav']} (ID: {row['id']})": row["id"]
                    for _, row in students_df.iterrows()
                }
                selected_student = st.selectbox(
                    "Select Student", options=list(student_options.keys()),
                    key="student_select")

                col_a, col_b = st.columns(2)
                with col_a:
                    current_month_name = datetime.now().strftime("%B")
                    month = st.selectbox(
                        "Month", options=list(calendar.month_name)[1:],
                        index=list(calendar.month_name)[1:].index(current_month_name),
                        key="month_select")
                with col_b:
                    year = st.number_input(
                        "Year", min_value=2020, max_value=2030,
                        value=datetime.now().year, key="year_input")

                st.markdown("**Payment Amount**")
                payment_option = st.radio(
                    "Select Option",
                    options=["Full Payment (Rs. 600)", "Custom Amount"],
                    horizontal=True, key="payment_option_radio")

                if payment_option == "Full Payment (Rs. 600)":
                    amount_paid  = STANDARD_MONTHLY_FEE
                    payment_type = "Full Payment"
                    st.success(f"Amount: Rs. {amount_paid}")
                else:
                    amount_paid = st.number_input(
                        "Enter Custom Amount (Rs.)",
                        min_value=1, max_value=10000, value=300, step=50,
                        key="custom_amount_input")
                    payment_type = ("Full/Over Payment (Custom)"
                                    if amount_paid >= STANDARD_MONTHLY_FEE
                                    else "Partial Payment (Custom)")
                    st.info(f"Payment Type: {payment_type}")

                remarks = st.text_area(
                    "Remarks (Optional)", placeholder="Add any notes here...",
                    key="remarks_input")

                if st.button("💾 Save Payment", key="save_payment_btn",
                             use_container_width=True, type="primary"):
                    student_id   = student_options[selected_student]
                    student_name = selected_student.split(" (ID:")[0]
                    if save_fee_payment(student_id, student_name, month, year,
                                        amount_paid, payment_type, remarks):
                        st.session_state["payment_saved"]  = True
                        st.session_state["saved_student"]  = student_name
                        st.session_state["saved_amount"]   = amount_paid
                        st.rerun()
                    else:
                        st.error("❌ Error saving payment record.")

                if st.session_state.get("payment_saved"):
                    st.success(
                        f"✅ Payment of Rs. {st.session_state['saved_amount']} recorded "
                        f"successfully for {st.session_state['saved_student']}!")
                    st.balloons()
                    if st.button("OK / Record New Payment",
                                 key="clear_payment_success", type="primary"):
                        st.session_state["payment_saved"] = False
                        st.rerun()

            with col2:
                st.markdown("#### 💵 Fee Structure")
                st.info("""
                **Standard Monthly Fee:** Rs. 600

                **Payment Options:**
                - Full Payment: Rs. 600
                - Custom Amount: Any amount

                Record payments as students pay. You can accept partial payments or any custom amount.
                """)

    # ── Fee Reports ────────────────────────────────────────────────────────────
    elif menu_selection == "📄 Fee Reports":
        st.markdown("### 📄 Fee Reports & Analytics")

        col1, col2, _ = st.columns([2, 2, 3])
        with col1:
            report_month = st.selectbox(
                "Select Month", options=["All"] + list(calendar.month_name)[1:], index=0)
        with col2:
            report_year_options = ["All"] + list(range(datetime.now().year, 2019, -1))
            report_year_str = st.selectbox("Select Year", options=report_year_options, index=0)
            report_year = report_year_str if report_year_str == "All" else int(report_year_str)

        fee_report_df = get_fee_report(report_month, report_year)

        if fee_report_df.empty:
            st.warning("⚠️ No payment records found for selected period")
        else:
            st.markdown("#### 📊 Summary")
            total_payments   = len(fee_report_df)
            full_payments    = len(fee_report_df[fee_report_df["amount_paid"] >= STANDARD_MONTHLY_FEE])
            partial_payments = len(fee_report_df[fee_report_df["amount_paid"] < STANDARD_MONTHLY_FEE])
            total_amount     = fee_report_df["amount_paid"].sum()

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Payments", total_payments)
            with c2: st.metric("Full Payments (≥Rs. 600)", full_payments)
            with c3: st.metric("Partial Payments (<Rs. 600)", partial_payments)
            with c4: st.metric("Total Amount Collected", f"Rs. {total_amount:,.0f}")

            st.markdown("---")
            st.markdown("#### 📋 Payment Details")

            display_columns = ["student_name", "month", "year", "amount_paid",
                               "payment_date", "remarks", "payment_type"]
            available_cols  = [c for c in display_columns if c in fee_report_df.columns]
            report_display  = fee_report_df[available_cols].copy()
            report_display.columns = [
                "Student Name", "Month", "Year", "Amount Paid (Rs.)",
                "Payment Date", "Remarks", "Payment Type"
            ][:len(available_cols)]
            st.dataframe(report_display, use_container_width=True, hide_index=True)

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                csv = report_display.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download CSV", data=csv,
                    file_name=f'fee_report_{report_month}_{report_year}_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime="text/csv", key="download_fee_report_csv",
                    use_container_width=True
                )
            with col_dl2:
                if report_month != "All" and report_year != "All":
                    pdf_buffer = generate_pdf_report(report_month, int(report_year))
                    st.download_button(
                        label="📄 Download PDF Report", data=pdf_buffer,
                        file_name=f"fee_report_{report_month}_{report_year}.pdf",
                        mime="application/pdf", key="download_pdf_report",
                        use_container_width=True
                    )
                else:
                    st.info("Select specific **Month** & **Year** for PDF report download.")

    # ── Brave Students Gallery ─────────────────────────────────────────────────
    elif menu_selection == "🌟 Brave Students Gallery":
        st.markdown("### 🌟 Manage Brave Students Gallery")
        st.info("💡 Add students with their photos and achievements!")

        tab1, tab2 = st.tabs(["➕ Add New Student", "📋 Manage Students"])

        with tab1:
            st.markdown("#### Add Student to Gallery")
            col1, col2 = st.columns([2, 1])
            with col1:
                new_name     = st.text_input("Student Name", placeholder="Enter student name",
                                             key="new_brave_name")
                new_position = st.text_input("Position/Achievement",
                                             placeholder="e.g., Academic Star, Top Reader",
                                             key="new_brave_position")
                st.markdown("**📸 Photo Source:**")
                photo_option = st.radio("Choose photo source",
                                        options=["Upload from PC", "Enter URL"],
                                        horizontal=True, key="photo_source_option")

                new_photo     = None
                uploaded_file = None
                if photo_option == "Upload from PC":
                    uploaded_file = st.file_uploader(
                        "Choose a photo", type=["png", "jpg", "jpeg"],
                        key="brave_photo_upload")
                    if uploaded_file:
                        new_photo = "uploaded_file"
                        st.success(f"✅ Photo selected: {uploaded_file.name}")
                else:
                    new_photo = st.text_input(
                        "Photo URL", placeholder="Enter image URL (https://...)",
                        key="new_brave_photo")
                    st.markdown("**Example:**")
                    st.code("https://images.unsplash.com/photo-1234567890?auto=format&w=300&q=80")

                if st.button("➕ Add Student to Gallery", key="add_brave_student_btn",
                             type="primary", use_container_width=True):
                    if new_name and new_position and new_photo:
                        if photo_option == "Upload from PC" and uploaded_file:
                            photo_path = save_uploaded_photo(uploaded_file)
                            if photo_path:
                                if save_brave_student(new_name, new_position, photo_path):
                                    st.success(f"✅ {new_name} added to gallery!")
                                    st.balloons()
                                    st.rerun()
                            else:
                                st.error("❌ Failed to save photo!")
                        elif photo_option == "Enter URL":
                            if save_brave_student(new_name, new_position, new_photo):
                                st.success(f"✅ {new_name} added to gallery!")
                                st.balloons()
                                st.rerun()
                    else:
                        st.error("❌ Please fill all fields and add a photo!")

            with col2:
                st.markdown("#### 👁️ Preview")
                if photo_option == "Upload from PC" and uploaded_file:
                    try:
                        st.image(uploaded_file, caption=new_name or "Preview", width=200)
                    except Exception:
                        st.warning("⚠️ Unable to preview image")
                elif photo_option == "Enter URL" and new_photo:
                    try:
                        st.image(new_photo, caption=new_name or "Preview", width=200)
                    except Exception:
                        st.warning("⚠️ Invalid image URL")
                else:
                    st.info("Add a photo to see preview")

        with tab2:
            st.markdown("#### Current Gallery Students")
            brave_df = get_all_brave_students()

            if brave_df.empty:
                st.info("📭 No students in gallery yet. Add some from the 'Add New Student' tab!")
            else:
                st.success(f"📊 Total Students in Gallery: {len(brave_df)}")

                for idx, row in brave_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4 = st.columns([1, 3, 3, 2])
                        with c1:
                            try:
                                st.image(row["photo_url"], width=80)
                            except Exception:
                                st.warning("🖼️")
                        with c2:
                            st.markdown(f"**{row['name']}**")
                            st.caption(f"Position: {row['position']}")
                        with c3:
                            st.caption(f"ID: {row['id']}")
                            st.caption(f"Added: {str(row['created_at'])[:10]}")
                        with c4:
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("✏️", key=f"edit_{row['id']}", help="Edit"):
                                    st.session_state[f"edit_brave_{row['id']}"] = True
                            with col_del:
                                if st.button("🗑️", key=f"delete_{row['id']}",
                                             help="Delete", type="secondary"):
                                    if delete_brave_student(row["id"]):
                                        st.success(f"✅ {row['name']} deleted!")
                                        st.rerun()

                        if st.session_state.get(f"edit_brave_{row['id']}", False):
                            with st.form(f"edit_form_{row['id']}"):
                                st.markdown(f"**Edit: {row['name']}**")
                                edit_name     = st.text_input("Name", value=row["name"],
                                                               key=f"edit_name_{row['id']}")
                                edit_position = st.text_input("Position", value=row["position"],
                                                               key=f"edit_pos_{row['id']}")
                                edit_photo    = st.text_input("Photo URL", value=row["photo_url"],
                                                               key=f"edit_photo_{row['id']}")
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Save",
                                                              use_container_width=True):
                                        if update_brave_student(row["id"], edit_name,
                                                                edit_position, edit_photo):
                                            st.success("✅ Updated successfully!")
                                            st.session_state[f"edit_brave_{row['id']}"] = False
                                            st.rerun()
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel",
                                                              use_container_width=True):
                                        st.session_state[f"edit_brave_{row['id']}"] = False
                                        st.rerun()

                        st.markdown("---")


# ── App Entry Point ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Admin Panel | Karmveer Abhyasika",
    page_icon="🔑",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "logged_in"     not in st.session_state: st.session_state["logged_in"]     = False
if "payment_saved" not in st.session_state: st.session_state["payment_saved"] = False

if st.session_state["logged_in"]:
    admin_dashboard()
else:
    login_page()