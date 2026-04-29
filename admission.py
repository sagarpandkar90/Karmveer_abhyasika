# -*- coding: utf-8 -*-
import datetime
import streamlit as st
import generate_form  # PDF generation logic
import gsheets_config as gs


# ── Database-equivalent functions (Google Sheets) ──────────────────────────────

def init_db():
    """
    Ensures all required sheets exist with correct headers.
    Replaces the SQLite CREATE TABLE IF NOT EXISTS calls.
    """
    for sheet_name in [
        gs.SHEET_ADMISSIONS,
        gs.SHEET_FEE_PAYMENTS,
        gs.SHEET_DEPOSITS,
        gs.SHEET_BRAVE_STUDENTS,
    ]:
        gs.get_sheet(sheet_name)   # creates sheet + headers if missing


def save_to_db(data: dict) -> bool:
    """
    Saves form data to the 'admissions' Google Sheet.
    Photo/sign binary blobs are skipped (Google Sheets cannot store binary).
    The files remain available in session_state for PDF generation.
    """
    try:
        new_id = gs.next_id(gs.SHEET_ADMISSIONS)
        row = [
            new_id,
            data.get("admission_date", ""),
            data.get("नाव", ""),
            str(data.get("जन्मतारीख", "")),
            data.get("लिंग", ""),
            data.get("मोबाईल", ""),
            data.get("पालक मोबाईल", ""),
            data.get("ईमेल", ""),
            data.get("पत्ता", ""),
            data.get("तयारी", ""),
            data.get("SSC गुण", ""),
            data.get("HSC गुण", ""),
            data.get("Graduation पदवी", ""),
            data.get("Graduation गुण", ""),
            data.get("Post Graduation पदवी", ""),
            data.get("Post Graduation गुण", ""),
            "(photo stored locally)",   # binary BLOB not stored in Sheets
            "(sign stored locally)",
        ]
        gs.append_row(gs.SHEET_ADMISSIONS, row)
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False


# ── Streamlit Application ──────────────────────────────────────────────────────

def admission():
    st.set_page_config(
        page_title="कर्मवीर अभ्यासिका प्रवेश फॉर्म",
        page_icon="📚",
        layout="wide"
    )

    # Ensure sheets exist on startup
    init_db()

    if "confirm_stage" not in st.session_state:
        st.session_state.confirm_stage = "form"

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #a8edea, #fed6e3);
        padding: 20px;
        border-radius: 20px;
        text-align:center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        font-family: 'Segoe UI', sans-serif;
        margin-bottom: 20px;
    ">
        <h1 style="color:#880e4f; font-size:2em; margin:0;">
            📘 कर्मवीर अभ्यासिका प्रवेश फॉर्म
        </h1>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")

    # ── Stage 1: Form entry ────────────────────────────────────────────────────
    if st.session_state.confirm_stage == "form":
        st.subheader("📝 विद्यार्थी माहिती")

        with st.form("admission_form"):
            full_name = st.text_input("पूर्ण नाव")
            dob       = st.date_input("जन्मतारीख",
                                      min_value=datetime.date(1950, 1, 1),
                                      max_value=datetime.date.today())
            gender    = st.selectbox("लिंग", ["पुरुष", "स्त्री", "इतर"])

            col1, col2 = st.columns(2)
            with col1:
                mobile        = st.text_input("मोबाईल नंबर")
            with col2:
                parent_mobile = st.text_input("पालकांचा मोबाईल नंबर")

            email   = st.text_input("ईमेल आयडी")
            address = st.text_area("पत्ता")

            st.write("### 🎯 तयारी कोणत्या परीक्षेसाठी आहे?")
            preparation = st.selectbox(
                "तयारी प्रकार",
                ["MPSC", "UPSC", "Talathi", "Saralseva", "Police", "Railway",
                 "Staff Selection Commission", "NEET", "Teacher", "10th", "12th", "Other"]
            )

            st.write("### 🎓 शैक्षणिक पात्रता आणि गुण")
            ssc_marks = st.text_input("SSC गुण (%)")
            hsc_marks = st.text_input("HSC गुण (%)")

            col1, col2 = st.columns(2)
            with col1:
                degree_options = [
                    "---निवडा---",
                    "B.A", "B.Sc", "B.Com", "B.Tech", "B.E",
                    "B.Ed", "BBA", "BCA", "LLB", "MBBS", "BAMS", "BHMS", "Other"
                ]
                degree_select = st.selectbox("Graduation पदवी", degree_options)
                if degree_select == "Other":
                    degree_name = st.text_input("Graduation पदवी नाव टाका")
                elif degree_select == "---निवडा---":
                    degree_name = ""
                else:
                    degree_name = degree_select
            with col2:
                grad_marks = st.text_input("Graduation गुण (%)")

            col3, col4 = st.columns(2)
            with col3:
                postgrad_options = [
                    "---निवडा---",
                    "M.A", "M.Sc", "M.Com", "M.Tech", "M.E",
                    "M.Ed", "MBA", "MCA", "LLM", "MD", "Other"
                ]
                postgrad_select = st.selectbox("Post Graduation पदवी", postgrad_options)
                if postgrad_select == "Other":
                    postgrad_degree_name = st.text_input("Post Graduation पदवी नाव टाका")
                elif postgrad_select == "---निवडा---":
                    postgrad_degree_name = ""
                else:
                    postgrad_degree_name = postgrad_select
            with col4:
                postgrad_marks = st.text_input("Post Graduation गुण (%)")

            st.write("### 🖼️ फोटो आणि सही अपलोड करा")
            col_img1, col_img2 = st.columns(2)
            with col_img1:
                photo = st.file_uploader("फोटो अपलोड करा",
                                         type=["jpg", "png", "jpeg"])
            with col_img2:
                sign  = st.file_uploader("सही अपलोड करा",
                                         type=["jpg", "png", "jpeg"])

            confirm_click = st.form_submit_button("✅ Confirm")

        if confirm_click:
            errors = []
            required_fields = {
                "पूर्ण नाव":           full_name,
                "मोबाईल नंबर":         mobile,
                "पालकांचा मोबाईल नंबर": parent_mobile,
                "ईमेल आयडी":           email,
                "पत्ता":               address,
                "SSC गुण (%)":         ssc_marks,
            }

            if photo is None: errors.append("⚠️ 'फोटो' हे फील्ड रिकामे आहे.")
            if sign  is None: errors.append("⚠️ 'सही' हे फील्ड रिकामे आहे.")

            for label, value in required_fields.items():
                if not value:
                    errors.append(f"⚠️ '{label}' हे फील्ड रिकामे आहे.")

            if mobile and not (mobile.isdigit() and len(mobile) == 10):
                errors.append("⚠️ मोबाईल नंबर 10 अंकी असावा.")
            if parent_mobile and not (parent_mobile.isdigit() and len(parent_mobile) == 10):
                errors.append("⚠️ पालकांचा मोबाईल नंबर 10 अंकी असावा.")

            # Validate Other text boxes are filled if selected
            if degree_select == "Other" and not degree_name.strip():
                errors.append("⚠️ 'Graduation पदवी' नाव टाका.")
            if postgrad_select == "Other" and not postgrad_degree_name.strip():
                errors.append("⚠️ 'Post Graduation पदवी' नाव टाका.")

            if errors:
                for err in errors:
                    st.error(err)
                st.stop()

            st.session_state.form_data = {
                "नाव":                   full_name,
                "जन्मतारीख":             dob,
                "लिंग":                  gender,
                "मोबाईल":               mobile,
                "पालक मोबाईल":          parent_mobile,
                "ईमेल":                  email,
                "पत्ता":                 address,
                "तयारी":                 preparation,
                "SSC गुण":               ssc_marks,
                "HSC गुण":               hsc_marks,
                "Graduation पदवी":       degree_name,
                "Graduation गुण":        grad_marks,
                "Post Graduation पदवी":  postgrad_degree_name,
                "Post Graduation गुण":   postgrad_marks,
                "photo":                 photo,
                "sign":                  sign,
            }
            st.session_state.confirm_stage = "confirm"
            st.rerun()

    # ── Stage 2: Confirm ───────────────────────────────────────────────────────
    elif st.session_state.confirm_stage == "confirm":
        data = st.session_state.form_data

        st.markdown("""
        <div style="background:linear-gradient(135deg,#d4fc79,#96e6a1);
                    padding:20px;border-radius:15px;box-shadow:0 5px 15px rgba(0,0,0,0.2);
                    text-align:center;">
            <h2 style="color:#4a148c;">📋 कृपया तुमची माहिती तपासा</h2>
        </div>
        """, unsafe_allow_html=True)

        st.write(" ")
        for key in [
            "नाव", "जन्मतारीख", "लिंग", "मोबाईल", "पालक मोबाईल",
            "ईमेल", "पत्ता", "तयारी",
            "SSC गुण", "HSC गुण",
            "Graduation पदवी", "Graduation गुण",
            "Post Graduation पदवी", "Post Graduation गुण",
        ]:
            st.markdown(
                f"<div style='background:#f0fff0;padding:8px;border-radius:8px;"
                f"margin-bottom:5px;'><b>{key}:</b> {data[key]}</div>",
                unsafe_allow_html=True
            )

        st.write("### 📸 फोटो आणि सही")
        col1, col2 = st.columns(2)
        with col1:
            if data["photo"]:
                data["photo"].seek(0)
                st.image(data["photo"], caption="फोटो", width=150)
        with col2:
            if data["sign"]:
                data["sign"].seek(0)
                st.image(data["sign"], caption="सही", width=150)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Submit"):
                admission_date         = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data["admission_date"] = admission_date

                if save_to_db(data):
                    st.session_state.confirm_stage = "submitted"
                    st.rerun()
                else:
                    st.error("❌ Google Sheets मध्ये डेटा जतन करताना त्रुटी आली. "
                             "कृपया पुन्हा प्रयत्न करा.")
                    st.session_state.confirm_stage = "form"
                    st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.confirm_stage = "form"
                st.rerun()

    # ── Stage 3: Submitted ─────────────────────────────────────────────────────
    elif st.session_state.confirm_stage == "submitted":
        st.success(
            "🎉 तुमचा प्रवेश फॉर्म यशस्वीरित्या सबमिट आणि "
            "Google Sheets मध्ये जतन झाला आहे!"
        )

        if st.button("Generate PDF"):
            form_data = st.session_state.get("form_data", {})
            generate_form.generate_pdf(form_data)


if __name__ == "__main__":
    admission()

if __name__ == "__main__":
    admission()