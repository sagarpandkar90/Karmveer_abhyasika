from pathlib import Path

import streamlit.components.v1 as components
import base64

from datetime import datetime


def get_marathi_date():
    marathi_digits = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"]

    def to_marathi_number(num):
        return "".join(marathi_digits[int(d)] for d in str(num))

    today = datetime.today()
    dd = to_marathi_number(today.day)
    mm = to_marathi_number(today.month)
    yyyy = "".join(marathi_digits[int(d)] for d in str(today.year))

    return f"{dd}/{mm}/{yyyy}"


# Example usage
marathi_date = get_marathi_date()


# Helper to convert uploaded image to base64
def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return ""
    return "data:image/png;base64," + base64.b64encode(uploaded_file.read()).decode()


def generate_pdf(form_data):
    form_data["photo_base64"] = image_to_base64(form_data.get("photo"))
    form_data["sign_base64"] = image_to_base64(form_data.get("sign"))
    with open("photos/sign.jpg", "rb") as f:
        form_data["sign_owner"] = image_to_base64(f)

    # Load Marathi font
    font_path = "fonts/NotoSerifDevanagari-VariableFont_wdth,wght.ttf"
    with open(font_path, "rb") as f:
        font_bytes = f.read()
        font_b64 = base64.b64encode(font_bytes).decode("utf-8")

    components.html(
        f"""
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.72/pdfmake.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.72/vfs_fonts.js"></script>
</head>

<body>

<button onclick="previewPDF()" 
 style="padding:10px 15px; background:#2196F3; color:white; border:none; border-radius:6px; cursor:pointer; margin-right:10px;">
 👁️ Preview PDF
</button>

<button onclick="downloadPDF()" 
 style="padding:10px 15px; background:#4CAF50; color:white; border:none; border-radius:6px; cursor:pointer;">
 ⬇️ Download PDF
</button>


<script>

pdfMake.vfs["CustomFont.ttf"] = "{font_b64}";
pdfMake.fonts = {{
    MarathiFont: {{
        normal: "CustomFont.ttf",
        bold: "CustomFont.ttf",
        italics: "CustomFont.ttf",
        bolditalics: "CustomFont.ttf"
    }}
}};

var docDefinition = {{
  pageSize: 'A4',
  pageMargins: [40, 60, 25, 40],
  background: [
    {{
      canvas: [
        {{
          type: 'rect',
          x: 10,        // left
          y: 10,        // top
          w: 575,       // width
          h: 820,       // height
          lineWidth: 1  // border thickness
        }}
      ]
    }}
  ],
  content: [

    // ---------------- First Page ----------------
    {{
      stack: [

        {{
          columns: [
            {{
              stack: [
                {{ text: "कर्मवीर अभ्यासिका व स्पर्धा परीक्षा मार्गदर्शन केंद्र", style:'header', alignment:'center', margin:[0,0,0,5] }},
                {{ text: "लोणंद, ता. खडाळा, जि. सातारा - ४१५५२१", style:'subheader', alignment:'center', margin:[0,0,0,5] }},
                {{ text: "_______________________________________________________________", style:'subheader', alignment:'center', margin:[0,0,0,5] }}
              ]
            }},
            {{
              image: "{form_data.get('photo_base64', '')}",
              width:90, height:90, alignment:'right'
            }}
          ],
          margin:[0,0,0,10]
        }},

        {{ text:"प्रवेश अर्ज", style:'title', alignment:'center', margin:[0,5,0,0] }},
        {{ text:"सभासद क्र.:", alignment:'right', margin:[0,0,30,15] }},
        {{
          text: "मा. व्यवस्थापक यांस,\\nमी आपल्या अभ्यासिका विभागाचा दि. {marathi_date} पासून सभासद होऊ इच्छितो. अर्जाच्या मागील बाजूस छापलेले नियम मी वाचलेले असून ते मला मान्य आहेत. तसेच त्यात बदल झाल्यास तेही मी मान्य करीन. नियमांनुसार मी प्रस्तुत विभागाचा सभासद होण्यास इच्छुक आहे. कृपया मला सभासद करून घ्यावे.",
          style:'body',
          margin:[0,0,0,15]
        }},

        // Student Details Table
        {{
          table: {{
            widths: ['30%','70%'],
            body: [
              ['१. विद्यार्थीचे नाव :', '{form_data.get("नाव", "")}'],
              ['२. जन्मतारीख :', '{form_data.get("जन्मतारीख", "")}'],
              ['३. लिंग :', '{form_data.get("लिंग", "")}'],
              ['४. मोबाईल नं :', '{form_data.get("मोबाईल", "")}'],
              ['५. पालक मोबाईल :', '{form_data.get("पालक मोबाईल", "")}'],
              ['६. ई-मेल :', '{form_data.get("ईमेल", "")}'],
              ['७. पत्ता :', '{form_data.get("पत्ता", "")}'],
              ['८. तयारी :', '{form_data.get("तयारी", "")}'],
              ['९. SSC गुण :', '{form_data.get("SSC गुण", "")}'],
              ['१०. HSC गुण :', '{form_data.get("HSC गुण", "")}'],
              ['११. Graduation पदवी :', '{form_data.get("Graduation पदवी", "")}'],
              ['१२. Graduation गुण :', '{form_data.get("Graduation गुण", "")}'],
              ['१३. Post Graduation पदवी :', '{form_data.get("Post Graduation पदवी", "")}'],
              ['१४. Post Graduation गुण :', '{form_data.get("Post Graduation गुण", "")}']
            ]
          }},
          layout: {{
            hLineWidth: function(i,node){{return 1;}},
            vLineWidth: function(i,node){{return 1;}},
            hLineColor: function(i,node){{return '#000';}},
            vLineColor: function(i,node){{return '#000';}}
          }},
          margin:[0,0,0,20]
        }},
        {{
              image: "{form_data.get('sign_owner', '')}",
              width:80, height:40, alignment:'right', margin:[0,0,10,0]
        }},
        {{ text:"व्यवस्थापकाची सही     ", alignment:'right', margin:[0,0,20,10] }},
        {{ text:"(नियम व अटी वाचून सही करावी.)" }}
      ]
    }},

    // ---------------- Second Page ----------------
    {{ text:'', pageBreak:'before' }},

    {{
      text: "अभ्यासिकेचे फी बाबतचे नियम व अटी",
      style:'header',
      alignment:'center',
      margin:[0,0,0,15]
    }},

    {{
      ol: [
        "लोणंद अभ्यासिका केंद्राचे सभासद होण्यासाठी प्रवेश फी १०० रु. राहील. (विद्यार्थी सलग २ महिने न आल्यास त्याचा प्रवेश रद्द केला जाईल व पुन्हा प्रवेश घेताना १०० रु. प्रवेश फी भरावी लागेल.)",
        "अभ्यासिकेमध्ये बोलताना किंवा कुजबुज करताना कोणी सापडल्यास त्याला त्याच क्षणी अभ्यासिकेमधून बाहेर काढण्यात येईल.अन्यथा १०० रु. दंड आकारण्यात येईल.",
        "दुस-याची चप्पल घालून जाणे,वही घेणे,पुस्तक घेणे हे परवानगी न घेता केल्यास त्याही विद्यार्थ्याला अभ्यासिकेमधून बाहेर काढण्यात येईल. अन्यथा १०० रु. दंड आकारण्यात येईल.",
        "अभ्यासिकेच्या विद्यार्थ्यांनी फी भरताना ओळखपत्र घेऊन येणे सक्तीचे आहे.अन्यथा १०० रु   दंड आकारण्यात येईल.",
        "अभ्यासिकेतील विद्यार्थ्यांना येताना व जाताना नोंद वहीत नोंद करणे बंधनकारक आहे,जर विद्यार्थ्याने नोंद केली नसेल व तो अभ्यासिकेत    बसला असेल तर त्या दिवशी त्याला घरी पाठवण्यात येईल.अन्यथा त्या दिवसाचा १०० रु दंड घेण्यात येईल  .",
        "महिन्यात विद्यार्थ्याने कितीही दिवस अथवा दिवसातील कितीही तास अभ्यासिकेत येणार असल्यास त्याच्याकडून पूर्ण महिन्याचीच फी आकारली जाईल    दि. १ ते १५ च्या आतमध्ये कधीही प्रवेश घेतला तरी पूर्ण महिन्याची फी द्यावी लागेल    दि. १५ च्या पुढे आला तर निम्मीच फी भरावी लागेल .",
        "नवीन विद्यार्थ्याने प्रवेश घेतेवेळी दुस-या दिवशीच प्रवेश फी व महिन्याची मासिक फी भरावी लागेल  अन्यथा प्रवेश नाकारला जाईल.",
        "विद्यार्थ्याला अभ्यासिका बंद करायची असल्यास व्यवस्थापकास भेटणे आवश्यक राहील नाहीतर नंतर जरी तो अभ्यासिकेत नसल्यासही त्याच्याकडून पूर्ण महिन्याची फी घेतली जाईल.",
        "अभ्यासिकेची फी भरण्याची शेवटची १० तारीख असेन  त्यानंतर कोणतेही कारण न ऐकता त्याचा प्रवेश रद्द करण्यात येईल.",
        "अभ्यासिकेच्या आवारात गप्पा मारणे,मोबाईलवर बोलणे अथवा मोठ्‌याने बोलण्यास सक्त मनाई आहे.",
        "विद्यार्थ्याने आपल्या मौल्यवान वस्तु,मोबाईल,पुस्तके,वाहन यांची जबाबदारी स्वतः घ्यावी या वस्तू गहाळ झाल्यास संस्था जबाबदार राहणार नाही.",
        "विद्यार्थ्याने अभ्यासिकेच्या आवारात कोणत्याही प्रकारचे गैरवर्तन अथवा बेशिस्त वर्तन केल्यास त्या विद्यार्थाचे सभासदत्व रद्द करण्यात येईल व त्यावर योग्य ती कायदेशीर कारवाई केली जाईल.",
        "विद्यार्थ्याने अभ्यासिकेतील कोणत्याही वस्तूंची तोडफोड अथवा नुकसान केल्यास त्याची नुकसान भरपाई विद्यार्थ्यांकडून वसूल केली जाईल.",
        "अभ्यासिकेत कोणाचीही जागा फिक्स नाही   त्यामुळे जागा राखून ठेवता येणार नाही त्यामुळे जिथे मोकळी जागा असेल त्याठिकाणी पुस्तके ठेवली असल्यास ती तिथेच खाली जमिनीवर ठेवून अन्य सभासदाने त्या जागेवर बसावे.",
        "सभासदाला अभ्यासिकेचा प्रवेश रद्द करावयाचा असल्यास तसा लेखी अर्ज व्यवस्थापकाकडे द्यावा.",
        "सभासदांव्यतिरिक्त इतर व्यक्तींना अभ्यासिकेत येण्यास मनाई आहे अभ्यासिकेत किंवा अभ्यासिकेच्या आवारात मित्र/मैत्रिणींना आणू नये.",
        "अभ्यासिकेतील सदस्यांनी परिसरातील नागरिकांना त्रास होईल असे वर्तन करू नये अन्यथा प्रवेश रद्द करण्यात येईल.",
        "सभासदांनी आपली वाहने रस्त्यावर अडथळा होणार नाही याची काळजी घ्यावी याबाबतची कोणतीही जबाबदारी अभ्यासिकेची राहणार नाही.",
        "गच्ची (टेरेस) च्या आवारात फिरताना योग्य ती काळजी घ्यावी कोणताही अपघात घडल्यास अभ्यासिका जबाबदार राहणार नाही.",
        "वरील नियम व अटी मी वाचल्या असून त्या मला मान्य आहेत त्याचा भंग झाल्यास होणाऱ्या कारवाईस मी जबाबदार राहीन."
      ]
    }},
    {{
              image: "{form_data.get('sign_base64', '')}",
              width:60, height:40, alignment:'right', margin:[20,0,10,0]
        }},
    {{ text:"सभासदाची सही ", alignment:'right', margin:[0,0,40,0] }}

  ],

  defaultStyle: {{
    font: 'MarathiFont',
    fontSize: 12
  }},

  styles: {{
    header: {{ fontSize: 18, bold:true }},
    subheader: {{ fontSize: 14 }},
    title: {{ fontSize: 16, bold:true }},
    body: {{ fontSize: 12 }}
  }}

}};


function previewPDF(){{
  pdfMake.createPdf(docDefinition).open();
}}
function downloadPDF(){{
  pdfMake.createPdf(docDefinition).download("{form_data.get("नाव", "")}प्रवेश_फॉर्म.pdf");
  alert("PDF Downloaded Successfully");
}}

</script>

</body>
</html>
""",
        height=900,
        scrolling=True
    )