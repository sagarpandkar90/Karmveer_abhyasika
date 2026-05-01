import streamlit as st
import streamlit.components.v1 as components


# -------------------------------
# Page Setup
# -------------------------------
import admission
import instruction_page

st.set_page_config(page_title="sub_pages | Karmveer Abhyasika", page_icon="🎓", layout="wide")

# -------------------------------
# Page Header
# -------------------------------
st.markdown("""
    
    <h1 style="text-align:center; color:#004d80; font-size:35px; margin-bottom:10px;">
        🎓 Karmveer Abhyasika - Student Section
    </h1>
    <hr style="height:3px; background:#00bcd4; border:none;">
""", unsafe_allow_html=True)


def general_form():
    html_code = """
<div style="
    
    background: linear-gradient(135deg, #f0f9ff, #b2ebf2);
    padding: 40px 50px;
    border-radius: 30px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.3);
    font-family: 'Segoe UI', sans-serif;
    line-height: 1.8em;
    max-width: 1200px;
    margin: 0 auto;
    overflow: visible;
">
    <h2 style="color:#d81b60; text-align:center; font-size:2em; margin-bottom:25px; text-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
        ग्रंथालयाचे नियम 📚
    </h2>

    <ol style="color:#004d40; font-size:1.1em; padding-left:25px;">
        <li style="margin-bottom:10px; background: #ffe0b2; border-radius:8px; padding:8px 12px;">
            📌 ग्रंथालयात <b>शांतता</b> राखावी; मोबाईलवर बोलू नये.
        </li>
        <li style="margin-bottom:10px; background: #c8e6c9; border-radius:8px; padding:8px 12px;">
            📌 हलकेच हालचाल आवश्यक असल्यासच; अनावश्यक हालचाल टाळावी.
        </li>
        <li style="margin-bottom:10px; background: #b3e5fc; border-radius:8px; padding:8px 12px;">
            💡 प्रकाश आवश्यकता नसताना <b>लाईट बंद</b> करावी.
        </li>
        <li style="margin-bottom:10px; background: #ffe0b2; border-radius:8px; padding:8px 12px;">
            🌬️ पंखा आवश्यकता नसताना बंद करावा.
        </li>
        <li style="margin-bottom:10px; background: #c5cae9; border-radius:8px; padding:8px 12px;">
            👞 बाहेरील चप्पल व्यवस्थित ठेवाव्यात; वॉशरूमसाठी बाहेरील चप्पल वापरावी.
        </li>
        <li style="margin-bottom:10px; background: #dcedc8; border-radius:8px; padding:8px 12px;">
            📰 ग्रंथालयातील वर्तमानपत्र ठरवलेल्या ठिकाणी वाचावे; घरी नेऊ नये.
        </li>
        <li style="margin-bottom:10px; background: #ffccbc; border-radius:8px; padding:8px 12px;">
            📱 मोबाइल फोन मूक किंवा सायलेंट मोडवर ठेवा.
        </li>
        <li style="margin-bottom:10px; background: #ffe082; border-radius:8px; padding:8px 12px;">
            🪑 आपले स्थान ठरवून बसावे; एकाच जागा व्यापू नका.
        </li>
        <li style="margin-bottom:10px; background: #b2dfdb; border-radius:8px; padding:8px 12px;">
            🙏 ग्रंथालय कर्मचारी व इतर सदस्यांचा सन्मान करावा.
        </li>
        <li style="margin-bottom:10px; background: #f0f4c3; border-radius:8px; padding:8px 12px;">
            💻 संगणक व Wi-Fi योग्यरित्या वापरावे.
        </li>
        <li style="margin-bottom:10px; background: #ffcdd2; border-radius:8px; padding:8px 12px;">
            ⚠️ कोणत्याही साहित्याची हानी झाल्यास तत्काळ कळवावी.
        </li>
        <li style="margin-bottom:10px; background: #d1c4e9; border-radius:8px; padding:8px 12px;">
            📷 फोटोग्राफी किंवा व्हिडिओ शूट करण्यासाठी परवानगी आवश्यक आहे.
        </li>
        <li style="margin-bottom:10px; background: #b2ebf2; border-radius:8px; padding:8px 12px;">
            🚫 ग्रंथालयातील नियमांचे उल्लंघन झाल्यास सदस्यत्व रद्द होऊ शकते.
        </li>
        <li style="margin-bottom:10px; background: #ffe082; border-radius:8px; padding:8px 12px;">
            📚 ग्रंथालयातील साहित्य फक्त अभ्यासासाठी वापरावे.
        </li>
        <li style="margin-bottom:10px; background: #c8e6c9; border-radius:8px; padding:8px 12px;">
            🤝 इतर सदस्यांना त्रास देणे टाळावे.
        </li>
    </ol>
</div>
"""

    components.html(html_code, scrolling=False, height=1400)  # increased height





# -------------------------------
# Tabs for Navigation
# -------------------------------
tab1, tab2 = st.tabs(["📘 General Info", "📝 Admission Form"])

# -------------------------------
# Tab 1 - General Info
# -------------------------------
with tab1:
    general_form()

# -------------------------------
# Tab 2 - Admission Form
# -------------------------------
with tab2:
    instruction_page.instruction_page()

