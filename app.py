# -*- coding: utf-8 -*-
"""
app.py  –  Homepage for Karmveer Abhyasika
Migrated from SQLite to Google Sheets (brave_students gallery).
All layout, CSS, and output are unchanged.
"""

import base64
import os
import streamlit as st
from pathlib import Path
import gsheets_config as gs

st.set_page_config(page_title="कर्मवीर अभ्यासिका", layout="wide")


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def image_to_base64(img_path: str) -> str:
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def get_brave_students_from_db() -> list:
    """Fetch brave students from Google Sheets (replaces SQLite call)."""
    try:
        df = gs.sheet_to_df(gs.SHEET_BRAVE_STUDENTS)
        if df.empty:
            return []
        import pandas as pd
        df["display_order"] = pd.to_numeric(df["display_order"], errors="coerce").fillna(0)
        df = df.sort_values(["display_order", "id"]).reset_index(drop=True)
        return [
            {"name": row["name"], "position": row["position"], "photo": row["photo_url"]}
            for _, row in df.iterrows()
        ]
    except Exception as e:
        st.error(f"Error fetching students: {e}")
        return []


# ── Header image ───────────────────────────────────────────────────────────────
img_path   = Path("photos") / "5.jpg"
img_base64 = get_base64(str(img_path))

# ── CSS (unchanged from original) ─────────────────────────────────────────────
st.markdown(f"""
<style>
body {{ background-color:#f0f8ff; font-family:"Segoe UI",sans-serif; }}

.header {{
    text-align:center;
    background-image:url("data:image/jpeg;base64,{img_base64}");
    background-size:cover; background-position:center;
    color:white; padding:80px 20px; border-radius:16px;
    box-shadow:0 4px 20px rgba(0,0,0,0.3);
}}
.header h1 {{ font-size:3.2em; color:#00bfa5; text-shadow:3px 3px 8px rgba(0,0,0,0.7); }}
.header p  {{ font-size:1.4em; color:#f43b47; text-shadow:2px 2px 6px rgba(0,0,0,0.6); }}

.info-box {{
    background:linear-gradient(135deg,#f6d365,#fda085,#ff9a9e);
    border-left:6px solid #00796b; padding:18px 22px; border-radius:12px;
    box-shadow:0 4px 12px rgba(0,0,0,0.15); margin-top:10px;
}}
.info-box h3 {{ color:#004d40; margin-bottom:8px; }}
.info-box p, ul {{ color:#004d40; font-weight:550; font-size:1.15em;
                   line-height:1.7em; margin:0; }}

.photo-gallery {{
    display:flex; flex-wrap:wrap; justify-content:center;
    gap:20px; margin-top:30px; margin-bottom:40px;
}}
.photo-card {{
    width:30%; border-radius:12px; overflow:hidden;
    box-shadow:0 6px 14px rgba(0,0,0,0.2);
    transition:transform 0.3s ease-in-out,box-shadow 0.3s;
}}
.photo-card img {{
    width:100%; height:320px; object-fit:cover;
    border-bottom:4px solid #ff6600;
}}
.photo-card:hover {{ transform:scale(1.05); box-shadow:0 8px 18px rgba(0,0,0,0.3); }}

.student-card {{
    display:inline-block; background-color:#ffffff; margin:10px;
    border-radius:14px; padding:10px; width:170px;
    box-shadow:0 4px 12px rgba(0,0,0,0.15);
    transition:transform 0.3s,box-shadow 0.3s; text-align:center;
}}
.student-card:hover {{ transform:translateY(-5px); box-shadow:0 6px 16px rgba(0,0,0,0.25); }}
.student-card img {{
    width:100%; height:150px; border-radius:12px;
    object-fit:cover; margin-bottom:8px;
}}
.student-name     {{ font-weight:620; color:#004d40; }}
.student-position {{ font-size:0.9em; color:#f43b47; }}

.footer {{ text-align:center; margin-top:60px; font-size:0.9em; color:#333; }}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='header'>
    <h1>कर्मवीर अभ्यासिका</h1>
    <p>शांत वातावरण • प्रेरणादायी अध्ययन • उत्तम सुविधा</p>
</div>
""", unsafe_allow_html=True)

# ── Info + Facilities ──────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class='info-box'>
        <h3>📘 अभ्यासिकेची माहिती</h3>
        <p>
            <b>कर्मवीर अभ्यासिका</b><br>
            वेताळ पेठ, लोणंद<br>
            ता. खंडाळा, जि. सातारा<br>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='info-box'>
        <h3>✨ अभ्यासिकेच्या सुविधा</h3>
        <ul>
            <li>सुविधायुक्त प्रशस्त टेबल आणि कुशन खुर्च्या</li>
            <li>शुद्ध फिल्टर केलेले पिण्याचे पाणी</li>
            <li>मोफत Wi-Fi सुविधा</li>
            <li>दैनंदिन वृत्तपत्र वाचन</li>
            <li>मार्गदर्शन सत्रे आणि शैक्षणिक चर्चा</li>
            <li>स्वतंत्र चार्जिंग पॉईंट व बॅटरी बॅकअप</li>
            <li>स्वच्छ आणि प्रशस्त प्रकाश व्यवस्था</li>
            <li>पूर्ण पंख्यांची सोय</li>
            <li>स्वतंत्र लंच व चर्चासत्र क्षेत्र</li>
            <li>मुला-मुलींसाठी स्वतंत्र स्वच्छ वॉशरूम</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ── Library Photo Gallery ──────────────────────────────────────────────────────
st.markdown("<h3 style='margin-top:40px;'>📸 लायब्ररी गॅलरी</h3>",
            unsafe_allow_html=True)

photos_folder  = Path("photos")
library_photos = [
    photos_folder / "6.jpg",
    photos_folder / "5.jpg",
    photos_folder / "3.jpg",
    photos_folder / "7.jpg",
    photos_folder / "4.jpg",
    photos_folder / "2.jpg",
    photos_folder / "8.jpg",
    photos_folder / "9.jpg",
    photos_folder / "10.jpg",
]

gallery_html = "<div class='photo-gallery'>"
for img in library_photos:
    if img.exists():
        b64 = image_to_base64(str(img))
        gallery_html += (
            f"<div class='photo-card'>"
            f"<img src='data:image/jpeg;base64,{b64}'>"
            f"</div>"
        )
gallery_html += "</div>"
st.markdown(gallery_html, unsafe_allow_html=True)

# ── Brave Students Gallery – FROM GOOGLE SHEETS ────────────────────────────────
st.markdown(
    "<h3 style='text-align:center;margin-top:60px;color:#004d40;'>"
    "🌟 आमचे प्रतिभावान विद्यार्थी</h3>",
    unsafe_allow_html=True
)

students = get_brave_students_from_db()

if not students:
    st.info("⚠️ No students found in gallery. Admin can add students from the admin panel.")

num_students = len(students)
rows_needed  = (num_students + 4) // 5

for row_idx in range(rows_needed):
    cols      = st.columns(5)
    start_idx = row_idx * 5
    end_idx   = min(start_idx + 5, num_students)

    for col_idx, col in enumerate(cols):
        student_idx = start_idx + col_idx
        if student_idx < num_students:
            s          = students[student_idx]
            photo_path = s["photo"]

            if os.path.exists(photo_path):
                b64       = get_base64(photo_path)
                photo_src = f"data:image/jpeg;base64,{b64}"
            else:
                photo_src = photo_path   # treat as URL

            col.markdown(f"""
            <div class='student-card'>
                <img src='{photo_src}' alt='{s["name"]}'>
                <div class='student-name'>{s["name"]}</div>
                <div class='student-position'>{s["position"]}</div>
            </div>
            """, unsafe_allow_html=True)

    if row_idx < rows_needed - 1:
        st.write("<br>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='footer'>© 2025 कर्मवीर अभ्यासिका | Designed with ❤️ in Streamlit</div>",
    unsafe_allow_html=True
)