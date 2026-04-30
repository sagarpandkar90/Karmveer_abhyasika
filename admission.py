# -*- coding: utf-8 -*-
"""
admission.py – Student Admission Form for Karmveer Abhyasika
Improvements:
  • Mobile-first CSS with clamp() fluid typography & single-column stacking
  • Google Sheets API rate-limit detection with friendly Marathi/English messages
  • Exponential back-off retry on transient Sheets errors
  • All exceptions caught with user-friendly feedback
  • init_db() called lazily (cached) — not on every rerun
  • PDF generation wrapped in try/except
"""

import time
import datetime
import streamlit as st
import generate_form          # PDF generation logic
import gsheets_config as gs

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="कर्मवीर अभ्यासिका – प्रवेश फॉर्म",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Error message helpers ─────────────────────────────────────────────────────

def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in [
        "quota", "rate limit", "429", "resource exhausted",
        "too many requests", "limit exceeded", "ratequotaexceeded",
    ])


def _show_sheets_error(exc: Exception, context: str = ""):
    """Show a friendly, helpful error for any Google Sheets failure."""
    if _is_rate_limit(exc):
        st.error(
            "⏳ **Google Sheets वापर मर्यादा (Rate Limit) ओलांडली!**\n\n"
            "Google Sheets API ला दर मिनिटाला फक्त ठराविक विनंत्या पाठवता येतात. "
            "कृपया **30–60 सेकंद थांबून पुन्हा प्रयत्न करा.** \n\n"
            "_Google Sheets usage limit exceeded. Please wait 30–60 seconds and try again._"
        )
    else:
        st.error(
            f"❌ **Google Sheets मध्ये त्रुटी आली** {'(' + context + ')' if context else ''}\n\n"
            f"तपशील: `{exc}`\n\n"
            "कृपया इंटरनेट कनेक्शन तपासा आणि पुन्हा प्रयत्न करा."
        )


def _retry_append(sheet_name, row, retries: int = 3) -> bool:
    """
    Append a row to a Google Sheet with exponential back-off on rate-limit errors.
    Returns True on success, False after all retries fail.
    """
    delay = 5  # seconds
    for attempt in range(1, retries + 1):
        try:
            gs.append_row(sheet_name, row)
            return True
        except Exception as exc:
            if _is_rate_limit(exc):
                if attempt < retries:
                    st.warning(
                        f"⏳ Rate limit — {delay}s नंतर पुन्हा प्रयत्न होईल "
                        f"({attempt}/{retries - 1})…"
                    )
                    time.sleep(delay)
                    delay *= 2      # 5s → 10s → 20s
                else:
                    _show_sheets_error(exc, "append_row")
                    return False
            else:
                _show_sheets_error(exc, "append_row")
                return False
    return False


# ── Lazy sheet initialisation (run only once per session) ─────────────────────

@st.cache_resource(show_spinner=False)
def _init_sheets_once():
    """Creates required sheets with headers if missing. Cached for the session."""
    errors = []
    for sheet_name in [
        gs.SHEET_ADMISSIONS,
        gs.SHEET_FEE_PAYMENTS,
        gs.SHEET_DEPOSITS,
        gs.SHEET_BRAVE_STUDENTS,
    ]:
        try:
            gs.get_sheet(sheet_name)
        except Exception as exc:
            errors.append((sheet_name, exc))
    return errors


def init_db():
    init_errors = _init_sheets_once()
    for sheet_name, exc in init_errors:
        if _is_rate_limit(exc):
            st.warning(
                f"⏳ Sheet '{sheet_name}' तयार करताना rate limit आली. "
                "थोड्या वेळाने पेज रिफ्रेश करा."
            )
        else:
            st.warning(f"⚠️ Sheet '{sheet_name}' तयारी करताना त्रुटी: {exc}")


# ── Save to Google Sheets ─────────────────────────────────────────────────────

def save_to_db(data: dict) -> bool:
    try:
        new_id = gs.next_id(gs.SHEET_ADMISSIONS)
    except Exception as exc:
        _show_sheets_error(exc, "next_id")
        return False

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
        "(photo stored locally)",
        "(sign stored locally)",
    ]
    return _retry_append(gs.SHEET_ADMISSIONS, row)


# ── Mobile-first CSS ──────────────────────────────────────────────────────────

FORM_CSS = """
<style>
/* ── Base ── */
* { box-sizing: border-box; }
html, body { overflow-x: hidden; }
body {
    background: #f7f3ff;
    font-family: 'Segoe UI', 'Noto Sans Devanagari', Tahoma, sans-serif;
}
.block-container {
    padding: clamp(0.5rem, 3vw, 1.5rem) clamp(0.6rem, 4vw, 2rem) 3rem !important;
    max-width: 860px !important;
    margin: 0 auto !important;
}

/* ── Header banner ── */
.form-header {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: clamp(18px, 5vw, 32px) clamp(14px, 4vw, 28px);
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    margin-bottom: 24px;
    animation: fadeDown 0.5s ease;
}
@keyframes fadeDown {
    from { opacity:0; transform:translateY(-14px); }
    to   { opacity:1; transform:translateY(0); }
}
.form-header h1 {
    color: #880e4f;
    font-size: clamp(1.25rem, 5vw, 2rem);
    margin: 0 0 6px;
    line-height: 1.25;
}
.form-header p {
    color: #4a148c;
    font-size: clamp(0.8rem, 2.5vw, 1rem);
    margin: 0;
}

/* ── Section headers ── */
.section-head {
    background: linear-gradient(90deg, #880e4f, #c2185b);
    color: white;
    padding: 8px 16px;
    border-radius: 10px;
    font-size: clamp(0.9rem, 3vw, 1.05rem);
    font-weight: 700;
    margin: 22px 0 10px;
    letter-spacing: 0.3px;
}

/* ── Confirm card ── */
.confirm-banner {
    background: linear-gradient(135deg, #d4fc79, #96e6a1);
    padding: clamp(14px, 4vw, 24px);
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 5px 16px rgba(0,0,0,0.12);
    margin-bottom: 20px;
}
.confirm-banner h2 {
    color: #4a148c;
    font-size: clamp(1.1rem, 4.5vw, 1.7rem);
    margin: 0;
}

/* ── Data review rows ── */
.data-row {
    background: #f0fff0;
    padding: clamp(7px, 2vw, 11px) clamp(10px, 3vw, 16px);
    border-radius: 8px;
    margin-bottom: 5px;
    font-size: clamp(0.82rem, 2.5vw, 0.97rem);
    word-break: break-word;
    border-left: 3px solid #43a047;
}
.data-row b { color: #1b5e20; }

/* ── Success card ── */
.success-card {
    background: linear-gradient(135deg, #43e97b, #38f9d7);
    padding: clamp(24px, 6vw, 48px) clamp(16px, 5vw, 40px);
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 8px 28px rgba(0,0,0,0.14);
    margin: 20px 0;
    animation: popIn 0.5s cubic-bezier(.175,.885,.32,1.275);
}
@keyframes popIn {
    from { opacity:0; transform:scale(0.88); }
    to   { opacity:1; transform:scale(1); }
}
.success-card h2 { color: #1b5e20; font-size: clamp(1.3rem, 5vw, 2rem); margin:0 0 8px; }
.success-card p  { color: #2e7d32; font-size: clamp(0.85rem, 2.5vw, 1.1rem); margin: 4px 0; }

/* ── Streamlit column gap on mobile ── */
@media (max-width: 640px) {
    [data-testid="column"] { padding: 3px 2px !important; }
    /* Stack columns on very small screens */
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 100% !important;
    }
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: clamp(0.85rem, 2.5vw, 1rem) !important;
    padding: 0.5rem 1rem !important;
    width: 100% !important;
}
</style>
"""


# ── Main Application ──────────────────────────────────────────────────────────

def admission():
    st.markdown(FORM_CSS, unsafe_allow_html=True)

    # Lazy sheet init — shows warnings if something is wrong
    init_db()

    if "confirm_stage" not in st.session_state:
        st.session_state.confirm_stage = "form"

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="form-header">
        <h1>📘 कर्मवीर अभ्यासिका</h1>
        <p>विद्यार्थी प्रवेश फॉर्म | Student Admission Form</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  STAGE 1 – Form entry
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.confirm_stage == "form":
        with st.form("admission_form", clear_on_submit=False):

            # ── Personal info ──────────────────────────────────────────────
            st.markdown("<div class='section-head'>👤 वैयक्तिक माहिती</div>",
                        unsafe_allow_html=True)

            full_name = st.text_input("पूर्ण नाव *", placeholder="उदा. राहुल शिंदे")

            # On mobile, date + gender on same row still; they stack via CSS
            col_dob, col_gen = st.columns(2)
            with col_dob:
                dob = st.date_input(
                    "जन्मतारीख *",
                    min_value=datetime.date(1950, 1, 1),
                    max_value=datetime.date.today(),
                )
            with col_gen:
                gender = st.selectbox("लिंग *", ["पुरुष", "स्त्री", "इतर"])

            col_m, col_pm = st.columns(2)
            with col_m:
                mobile = st.text_input("मोबाईल नंबर *", placeholder="10 अंकी")
            with col_pm:
                parent_mobile = st.text_input("पालकांचा मोबाईल *", placeholder="10 अंकी")

            email   = st.text_input("ईमेल आयडी", placeholder="email@example.com")
            address = st.text_area("पत्ता *", placeholder="संपूर्ण पत्ता टाका", height=90)

            # ── Exam preparation ───────────────────────────────────────────
            st.markdown("<div class='section-head'>🎯 परीक्षा तयारी</div>",
                        unsafe_allow_html=True)
            preparation = st.selectbox("कोणत्या परीक्षेसाठी तयारी? *", [
                "MPSC", "UPSC", "Talathi", "Saralseva", "Police", "Railway",
                "Staff Selection Commission", "NEET", "Teacher",
                "10th", "12th", "Other",
            ])

            # ── Academic marks ─────────────────────────────────────────────
            st.markdown("<div class='section-head'>🎓 शैक्षणिक पात्रता</div>",
                        unsafe_allow_html=True)

            col_ssc, col_hsc = st.columns(2)
            with col_ssc:
                ssc_marks = st.text_input("SSC गुण (%) *", placeholder="उदा. 85.40")
            with col_hsc:
                hsc_marks = st.text_input("HSC गुण (%)", placeholder="उदा. 72.60")

            # Graduation
            DEGREE_OPTS = [
                "---निवडा---",
                "B.A", "B.Sc", "B.Com", "B.Tech", "B.E",
                "B.Ed", "BBA", "BCA", "LLB", "MBBS", "BAMS", "BHMS", "Other",
            ]
            col_gd, col_gm = st.columns(2)
            with col_gd:
                degree_select = st.selectbox("Graduation पदवी", DEGREE_OPTS)
                if degree_select == "Other":
                    degree_name = st.text_input("Graduation पदवी नाव *",
                                                placeholder="पदवी नाव")
                elif degree_select == "---निवडा---":
                    degree_name = ""
                else:
                    degree_name = degree_select
            with col_gm:
                grad_marks = st.text_input("Graduation गुण (%)", placeholder="उदा. 68.20")

            # Post-Graduation
            PG_OPTS = [
                "---निवडा---",
                "M.A", "M.Sc", "M.Com", "M.Tech", "M.E",
                "M.Ed", "MBA", "MCA", "LLM", "MD", "Other",
            ]
            col_pg, col_pgm = st.columns(2)
            with col_pg:
                postgrad_select = st.selectbox("Post Graduation पदवी", PG_OPTS)
                if postgrad_select == "Other":
                    postgrad_degree_name = st.text_input(
                        "Post Graduation पदवी नाव *", placeholder="पदवी नाव")
                elif postgrad_select == "---निवडा---":
                    postgrad_degree_name = ""
                else:
                    postgrad_degree_name = postgrad_select
            with col_pgm:
                postgrad_marks = st.text_input("Post Graduation गुण (%)",
                                               placeholder="उदा. 71.50")

            # ── Photo & Signature ──────────────────────────────────────────
            st.markdown("<div class='section-head'>🖼️ फोटो आणि सही</div>",
                        unsafe_allow_html=True)
            st.caption("📱 मोबाईलवरून गॅलरीतून फोटो निवडा. फाईल साइज 2MB पेक्षा कमी असावी.")

            col_ph, col_sg = st.columns(2)
            with col_ph:
                photo = st.file_uploader("फोटो अपलोड करा *",
                                         type=["jpg", "png", "jpeg"],
                                         key="photo_upload")
                if photo:
                    try:
                        st.image(photo, caption="फोटो Preview", width=130)
                    except Exception:
                        st.warning("⚠️ फोटो preview उपलब्ध नाही.")
            with col_sg:
                sign = st.file_uploader("सही अपलोड करा *",
                                        type=["jpg", "png", "jpeg"],
                                        key="sign_upload")
                if sign:
                    try:
                        st.image(sign, caption="सही Preview", width=130)
                    except Exception:
                        st.warning("⚠️ सही preview उपलब्ध नाही.")

            st.markdown("<br>", unsafe_allow_html=True)
            confirm_click = st.form_submit_button(
                "✅ माहिती तपासा (Confirm & Preview)", use_container_width=True)

        # ── Validation ─────────────────────────────────────────────────────
        if confirm_click:
            errors = []

            required = {
                "पूर्ण नाव":            full_name,
                "मोबाईल नंबर":          mobile,
                "पालकांचा मोबाईल":      parent_mobile,
                "पत्ता":                address,
                "SSC गुण":              ssc_marks,
            }
            for label, val in required.items():
                if not str(val).strip():
                    errors.append(f"⚠️ **{label}** हे फील्ड रिकामे आहे.")

            if photo is None:
                errors.append("⚠️ **फोटो** अपलोड करणे आवश्यक आहे.")
            if sign is None:
                errors.append("⚠️ **सही** अपलोड करणे आवश्यक आहे.")

            if mobile and (not mobile.isdigit() or len(mobile) != 10):
                errors.append("⚠️ **मोबाईल नंबर** बरोबर 10 अंकी असावा.")
            if parent_mobile and (not parent_mobile.isdigit() or len(parent_mobile) != 10):
                errors.append("⚠️ **पालकांचा मोबाईल** बरोबर 10 अंकी असावा.")

            if degree_select == "Other" and not degree_name.strip():
                errors.append("⚠️ **Graduation पदवी** नाव टाका.")
            if postgrad_select == "Other" and not postgrad_degree_name.strip():
                errors.append("⚠️ **Post Graduation पदवी** नाव टाका.")

            if errors:
                st.error("खालील त्रुटी सुधारा:")
                for err in errors:
                    st.markdown(err)
                st.stop()

            # Store validated data
            st.session_state.form_data = {
                "नाव":                   full_name.strip(),
                "जन्मतारीख":             dob,
                "लिंग":                  gender,
                "मोबाईल":               mobile.strip(),
                "पालक मोबाईल":          parent_mobile.strip(),
                "ईमेल":                  email.strip(),
                "पत्ता":                 address.strip(),
                "तयारी":                 preparation,
                "SSC गुण":               ssc_marks.strip(),
                "HSC गुण":               hsc_marks.strip(),
                "Graduation पदवी":       degree_name,
                "Graduation गुण":        grad_marks.strip(),
                "Post Graduation पदवी":  postgrad_degree_name,
                "Post Graduation गुण":   postgrad_marks.strip(),
                "photo":                 photo,
                "sign":                  sign,
            }
            st.session_state.confirm_stage = "confirm"
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    #  STAGE 2 – Confirm & Review
    # ══════════════════════════════════════════════════════════════════════════
    elif st.session_state.confirm_stage == "confirm":
        data = st.session_state.get("form_data", {})

        if not data:
            st.warning("⚠️ Session संपला. कृपया फॉर्म पुन्हा भरा.")
            st.session_state.confirm_stage = "form"
            st.rerun()

        st.markdown("""
        <div class="confirm-banner">
            <h2>📋 कृपया माहिती तपासा</h2>
        </div>""", unsafe_allow_html=True)

        REVIEW_FIELDS = [
            "नाव", "जन्मतारीख", "लिंग", "मोबाईल", "पालक मोबाईल",
            "ईमेल", "पत्ता", "तयारी",
            "SSC गुण", "HSC गुण",
            "Graduation पदवी", "Graduation गुण",
            "Post Graduation पदवी", "Post Graduation गुण",
        ]
        for key in REVIEW_FIELDS:
            val = data.get(key, "—")
            st.markdown(
                f"<div class='data-row'><b>{key}:</b>&nbsp; {val}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("#### 📸 फोटो आणि सही Preview")
        col_p, col_s = st.columns(2)
        with col_p:
            if data.get("photo"):
                try:
                    data["photo"].seek(0)
                    st.image(data["photo"], caption="फोटो", width=140)
                except Exception as e:
                    st.warning(f"⚠️ फोटो दाखवता आला नाही: {e}")
        with col_s:
            if data.get("sign"):
                try:
                    data["sign"].seek(0)
                    st.image(data["sign"], caption="सही", width=140)
                except Exception as e:
                    st.warning(f"⚠️ सही दाखवता आली नाही: {e}")

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("✅ Submit – जमा करा", type="primary",
                         use_container_width=True):
                with st.spinner("Google Sheets मध्ये जतन होत आहे…"):
                    admission_date         = datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S")
                    data["admission_date"] = admission_date

                    ok = save_to_db(data)

                if ok:
                    st.session_state.confirm_stage = "submitted"
                    st.rerun()
                else:
                    # Error message already shown by save_to_db / _show_sheets_error
                    st.info("💡 वरील त्रुटी सुधारून **Submit** पुन्हा दाबा. "
                            "Rate limit असल्यास 30–60 सेकंद थांबा.")

        with btn2:
            if st.button("✏️ Edit – माहिती बदला", use_container_width=True):
                st.session_state.confirm_stage = "form"
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    #  STAGE 3 – Success
    # ══════════════════════════════════════════════════════════════════════════
    elif st.session_state.confirm_stage == "submitted":
        st.markdown("""
        <div class="success-card">
            <h2>🎉 यशस्वी! Submitted!</h2>
            <p>तुमचा प्रवेश फॉर्म यशस्वीरित्या जतन झाला आहे.</p>
            <p>Your admission form has been saved successfully.</p>
        </div>""", unsafe_allow_html=True)

        col_pdf, col_new = st.columns(2)
        with col_pdf:
            if st.button("📄 PDF Download करा", use_container_width=True, type="primary"):
                form_data = st.session_state.get("form_data", {})
                if not form_data:
                    st.warning("⚠️ Session संपला, PDF तयार करता येणार नाही.")
                else:
                    try:
                        with st.spinner("PDF तयार होत आहे…"):
                            generate_form.generate_pdf(form_data)
                    except Exception as e:
                        st.error(
                            f"❌ PDF तयार करताना त्रुटी आली: `{e}`\n\n"
                            "कृपया पुन्हा प्रयत्न करा."
                        )

        with col_new:
            if st.button("🔄 नवीन फॉर्म भरा", use_container_width=True):
                for key in ["confirm_stage", "form_data"]:
                    st.session_state.pop(key, None)
                st.rerun()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    admission()