# -*- coding: utf-8 -*-
"""
app.py  –  Homepage for Karmveer Abhyasika
Mobile-optimized, fast data loading with caching, beautiful UI.
"""

import base64
import os
import streamlit as st
from pathlib import Path
import gsheets_config as gs

st.set_page_config(
    page_title="कर्मवीर अभ्यासिका",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


@st.cache_data(ttl=120, show_spinner=False)   # Cache 2 min, no spinner clutter
def get_brave_students_cached() -> list:
    """Fetch brave students from Google Sheets with caching for speed."""
    try:
        import pandas as pd
        df = gs.sheet_to_df(gs.SHEET_BRAVE_STUDENTS)
        if df.empty:
            return []
        df["display_order"] = pd.to_numeric(df["display_order"], errors="coerce").fillna(0)
        df = df.sort_values(["display_order", "id"]).reset_index(drop=True)
        return [
            {"name": row["name"], "position": row["position"], "photo": row["photo_url"]}
            for _, row in df.iterrows()
        ]
    except Exception as e:
        return []


@st.cache_data(ttl=300, show_spinner=False)   # Cache library images 5 min
def get_library_images_b64() -> list:
    photos_folder  = Path("photos")
    library_photos = [
        photos_folder / f"{i}.jpg"
        for i in [6, 5, 3, 7, 4, 2, 8, 9, 10]
    ]
    result = []
    for img in library_photos:
        if img.exists():
            b64 = get_base64(str(img))
            if b64:
                result.append(b64)
    return result


# ── Header image (cached at module level) ──────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_header_b64():
    img_path = Path("photos") / "5.jpg"
    return get_base64(str(img_path)) if img_path.exists() else ""

img_base64 = get_header_b64()

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Reset & Base ── */
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #f0f8ff;
    font-family: 'Segoe UI', 'Noto Sans Devanagari', sans-serif;
}}

/* ── Header ── */
.kv-header {{
    position: relative;
    text-align: center;
    background-image: url("data:image/jpeg;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    border-radius: 16px;
    overflow: hidden;
    padding: clamp(40px, 8vw, 90px) 16px;
    box-shadow: 0 6px 28px rgba(0,0,0,0.35);
    margin-bottom: 24px;
}}
.kv-header::before {{
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(160deg,rgba(0,0,0,0.55) 0%,rgba(0,77,64,0.65) 100%);
}}
.kv-header > * {{ position: relative; z-index: 1; }}
.kv-header h1 {{
    font-size: clamp(1.8rem, 6vw, 3.4rem);
    color: #00e5cc;
    text-shadow: 2px 3px 10px rgba(0,0,0,0.8);
    letter-spacing: 1px;
    line-height: 1.2;
}}
.kv-header p {{
    font-size: clamp(0.9rem, 3vw, 1.35rem);
    color: #ff8a80;
    text-shadow: 1px 2px 6px rgba(0,0,0,0.7);
    margin-top: 10px;
}}

/* ── Info Box ── */
.info-box {{
    background: linear-gradient(135deg, #f6d365, #fda085, #ff9a9e);
    border-left: 5px solid #00796b;
    padding: clamp(14px, 3vw, 22px);
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.15);
    margin-top: 10px;
    height: 100%;
}}
.info-box h3 {{ color: #004d40; margin-bottom: 10px; font-size: clamp(1rem, 3vw, 1.2rem); }}
.info-box p, .info-box ul {{
    color: #004d40;
    font-weight: 600;
    font-size: clamp(0.85rem, 2.5vw, 1.1rem);
    line-height: 1.75em;
}}
.info-box li {{ margin-left: 18px; }}

/* ── Photo Gallery ── */
.photo-gallery {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 280px), 1fr));
    gap: 16px;
    margin: 24px 0 40px;
}}
.photo-card {{
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 5px 16px rgba(0,0,0,0.18);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    aspect-ratio: 4/3;
    background: #e0e0e0;
}}
.photo-card img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-bottom: 3px solid #ff6600;
    display: block;
}}
@media (hover: hover) {{
    .photo-card:hover {{
        transform: scale(1.04);
        box-shadow: 0 8px 22px rgba(0,0,0,0.28);
    }}
}}

/* ── Student Gallery ── */
.students-wrap {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 155px), 1fr));
    gap: 16px;
    margin: 20px 0 40px;
}}
.student-card {{
    background: #ffffff;
    border-radius: 14px;
    padding: 12px 10px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    transition: transform 0.28s, box-shadow 0.28s;
    text-align: center;
}}
@media (hover: hover) {{
    .student-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 7px 18px rgba(0,0,0,0.22);
    }}
}}
.student-card img {{
    width: 100%;
    aspect-ratio: 1;
    border-radius: 10px;
    object-fit: cover;
    margin-bottom: 8px;
    background: #e0e0e0;
}}
.student-name     {{ font-weight: 700; color: #004d40; font-size: clamp(0.8rem, 2.5vw, 0.95rem); }}
.student-position {{ font-size: clamp(0.72rem, 2vw, 0.85rem); color: #f43b47; margin-top: 3px; }}

/* ── Section headings ── */
.section-title {{
    font-size: clamp(1.1rem, 4vw, 1.5rem);
    color: #004d40;
    margin: 32px 0 10px;
    font-weight: 700;
}}

/* ── Footer ── */
.kv-footer {{
    text-align: center;
    margin-top: 50px;
    padding: 18px;
    font-size: 0.88rem;
    color: #555;
    border-top: 1px solid #d0e8e0;
}}

/* ── Streamlit tweaks for mobile ── */
.block-container {{ padding: 0.75rem 1rem 2rem !important; max-width: 100% !important; }}
@media (max-width: 640px) {{
    .block-container {{ padding: 0.5rem 0.6rem 2rem !important; }}
    [data-testid="column"] {{ padding: 4px !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='kv-header'>
    <h1>📚 कर्मवीर अभ्यासिका</h1>
    <p>शांत वातावरण &nbsp;•&nbsp; प्रेरणादायी अध्ययन &nbsp;•&nbsp; उत्तम सुविधा</p>
</div>
""", unsafe_allow_html=True)

# ── Info + Facilities ──────────────────────────────────────────────────────────
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("""
    <div class='info-box'>
        <h3>📘 अभ्यासिकेची माहिती</h3>
        <p>
            <b>कर्मवीर अभ्यासिका</b><br>
            जुनी पेठ, लोणंद<br>
            ता. खंडाळा, जि. सातारा
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='info-box'>
        <h3>✨ सुविधा</h3>
        <ul>
            <li>प्रशस्त टेबल व कुशन खुर्च्या</li>
            <li>शुद्ध फिल्टर पाणी</li>
            <li>मोफत Wi-Fi</li>
            <li>दैनंदिन वृत्तपत्र</li>
            <li>मार्गदर्शन सत्रे</li>
            <li>स्वतंत्र चार्जिंग पॉईंट</li>
            <li>उत्तम प्रकाश व्यवस्था</li>
            <li>संपूर्ण पंखे</li>
            <li>लंच व चर्चासत्र क्षेत्र</li>
            <li>स्वतंत्र वॉशरूम</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ── Library Photo Gallery ──────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📸 लायब्ररी गॅलरी</div>", unsafe_allow_html=True)

with st.spinner(""):
    images_b64 = get_library_images_b64()

if images_b64:
    gallery_html = "<div class='photo-gallery'>"
    for b64 in images_b64:
        gallery_html += (
            f"<div class='photo-card'>"
            f"<img src='data:image/jpeg;base64,{b64}' loading='lazy'>"
            f"</div>"
        )
    gallery_html += "</div>"
    st.markdown(gallery_html, unsafe_allow_html=True)
else:
    st.info("📷 No gallery photos found.")

# ── Brave Students Gallery ─────────────────────────────────────────────────────
st.markdown(
    "<div class='section-title' style='text-align:center;'>🌟 आमचे प्रतिभावान विद्यार्थी</div>",
    unsafe_allow_html=True
)

with st.spinner("विद्यार्थी लोड होत आहेत…"):
    students = get_brave_students_cached()

if students:
    BARS = ['378ADD', '1D9E75', '7F77DD', 'BA7517', 'D4537E', '639922', 'D85A30', '4ABFBF']

    import streamlit as st

    html = """
    <style>
    .sv-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 14px;
        margin: 20px 0 40px;
    }

    .sv-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 16px;
        padding: 18px 12px 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .sv-bar {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
    }

    .sv-name {
        font-size: 17px;
        font-weight: 800;
        color: #1a237e;
        margin-top: 12px;
    }

    .sv-post {
        font-size: 13px;
        font-weight: 600;
        margin-top: 6px;
        color: #ffffff;
        background: #ff6f00;
        display: inline-block;
        padding: 4px 10px;
        border-radius: 10px;
    }
    </style>

    <div class='sv-grid'>

    <div class='sv-card'>
        <div class='sv-bar' style='background:#378ADD;'></div>
        <div class='sv-name'>Yogesh Kshirsagar</div>
        <div class='sv-post'>WRD Measurer</div>
    </div>

    <div class='sv-card'>
        <div class='sv-bar' style='background:#1D9E75;'></div>
        <div class='sv-name'>Dinesh Dhaigude</div>
        <div class='sv-post'>Agriculture Officer</div>
    </div>

    <div class='sv-card'>
        <div class='sv-bar' style='background:#7F77DD;'></div>
        <div class='sv-name'>Pratik Jadhav</div>
        <div class='sv-post'>Food Safety Officer</div>
    </div>

    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='kv-footer'>© 2026 कर्मवीर अभ्यासिका | Designed with ❤️ in Streamlit</div>",
    unsafe_allow_html=True
)