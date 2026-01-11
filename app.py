import streamlit as st
import pandas as pd
import io
import os
import math
import base64
import requests
import re
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# --- PAGE CONFIG ---
st.set_page_config(page_title="Murlidhar Academy PDF Tool", page_icon="📝", layout="wide")

# --- ASSETS LOADER ---
@st.cache_resource
def load_assets():
    # 1. Gujarati Font (Hind Vadodara)
    font_id = "1jVDKtad01ecE6dwitiAlrqR5Ov1YsJzw"
    font_url = f"https://drive.google.com/uc?export=download&id={font_id}"
    
    if not os.path.exists("MyCustomFont.ttf"):
        try:
            response = requests.get(font_url)
            if response.status_code == 200:
                with open("MyCustomFont.ttf", "wb") as f:
                    f.write(response.content)
        except:
            pass

    # 2. Background Image
    bg_url = "https://drive.google.com/uc?export=download&id=1NUwoSCN2OIWgjPQMPX1VileweKzta_HW"
    try:
        response = requests.get(bg_url)
        if response.status_code == 200:
            return response.content
    except:
        return None
    return None

default_bg_bytes = load_assets()

def get_image_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# --- SIDEBAR ---
st.sidebar.title("⚙️ સેટિંગ્સ")
WATERMARK_TEXT = st.sidebar.text_input("Watermark Text", "MURLIDHAR ACADEMY")
TG_LINK = st.sidebar.text_input("Telegram Link", "https://t.me/MurlidharAcademy")
IG_LINK = st.sidebar.text_input("Instagram Link", "https://www.instagram.com/murlidhar_academy_official/")
st.sidebar.divider()
st.sidebar.info("Designed by Harsh Solanki")

# --- MAIN UI ---
st.title("📝 Answer Key & Solution Generator")
st.markdown("Updated: **Helvetica Title**, **Reduced Margins**, **Perfect Alignment**.")

col1, col2, col3 = st.columns(3)
with col1:
    pdf_file = st.file_uploader("1. Question Paper (PDF)", type=['pdf'])
with col2:
    csv_file = st.file_uploader("2. Answer Key (CSV)", type=['csv'])
with col3:
    img_file_upload = st.file_uploader("3. Background (Optional)", type=['png', 'jpg', 'jpeg'])

st.divider()
st.subheader("📘 Detailed Solutions (સમજૂતી)")
add_solution = st.checkbox("Add Detailed Solutions Page?")

solution_text = ""
if add_solution:
    st.info("ℹ️ Format: **No | Answer | Explanation**")
    solution_text = st.text_area(
        "Paste Data Here:", height=200,
        placeholder="1 | A - પાટણ | પાટણ રાણકી વાવ માટે પ્રખ્યાત છે.\n2 | B - કૌશલ્ય | જીવનનિર્વાહનો ખર્ચ વધુ હોય છે."
    )

# --- GENERATE PDF ---
if st.button("Generate PDF 🚀"):
    if pdf_file and csv_file:
        try:
            with st.spinner("Generating PDF..."):
                
                # 1. WATERMARK GENERATION
                packet_wm = io.BytesIO()
                reader_temp = PdfReader(pdf_file)
                page1 = reader_temp.pages[0]
                width = float(page1.mediabox.width)
                height = float(page1.mediabox.height)
                
                c_wm = canvas.Canvas(packet_wm, pagesize=(width, height))
                c_wm.setFillColor(colors.grey, alpha=0.10)
                c_wm.setFont("Helvetica-Bold", 55)
                c_wm.saveState()
                c_wm.translate(width/2, height/2)
                c_wm.rotate(45)
                c_wm.drawCentredString(0, 0, WATERMARK_TEXT)
                c_wm.restoreState()
                c_wm.save()
                packet_wm.seek(0)
                watermark_reader = PdfReader(packet_wm)
                watermark_page = watermark_reader.pages[0]

                # 2. DATA PROCESSING
                df = pd.read_csv(csv_file)
                key_cols = [c for c in df.columns if c.lower().startswith('key') and c[3:].isdigit()]
                key_cols.sort(key=lambda x: int(x[3:]))
                answers = {}
                if not df.empty:
                    for k in key_cols:
                        q_num = int(k.lower().replace('key', ''))
                        answers[q_num] = str(df.iloc[0][k]).strip()
                total_questions = len(answers)

                # 3. BACKGROUND
                if img_file_upload:
                    bg_b64 = get_image_base64(img_file_upload.getvalue())
                elif default_bg_bytes:
                    bg_b64 = get_image_base64(default_bg_bytes)
                else:
                    bg_b64 = ""

                # 4. HTML / CSS CONSTRUCTION
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        /* Load Custom Font (Hind Vadodara) */
                        @font-face {{
                            font-family: 'HindVadodara';
                            src: url('file://{os.path.abspath("MyCustomFont.ttf")}');
                        }}
                        
                        @page {{
                            size: A4;
                            margin: 0;
                            background-image: url('data:image/jpeg;base64,{bg_b64}');
                            background-size: cover;
                            background-position: center;
                        }}
                        
                        body {{
                            /* Content font is Hind Vadodara */
                            font-family: 'HindVadodara', sans-serif;
                            margin: 0;
                            /* Reduced Top Padding to pull content UP (was 63.5mm) */
                            padding: 50mm 25mm 15mm 25mm;
                        }}
                        
                        /* TITLE: Forced Helvetica Bold as requested */
                        .title {{
                            text-align: center;
                            font-family: Helvetica, Arial, sans-serif;
                            font-weight: bold;
                            font-size: 24px;
                            color: white;
                            margin-top: 0px; 
                            margin-bottom: 5mm; /* Reduced spacing below title */
                            text-transform: uppercase;
                        }}
                        
                        /* ANSWER KEY TABLE */
                        .key-container {{
                            column-count: {math.ceil(total_questions/25)};
                            column-gap: 5mm;
                        }}
                        .key-table {{
                            width: 100%;
                            border-collapse: collapse;
                            font-size: 12px;
                            margin-bottom: 2mm;
                            page-break-inside: avoid;
                        }}
                        .key-table th {{
                            background-color: #003366;
                            color: white;
                            padding: 4px;
                            border: 0.5px solid #cccccc;
                            font-family: Helvetica, Arial, sans-serif; /* Header Font English/Bold */
                            font-weight: bold;
                        }}
                        .key-table td {{
                            padding: 4px;
                            border: 0.5px solid #cccccc;
                            text-align: center;
                            background-color: white;
                            font-weight: normal;
                        }}
                        .col-no {{
                            background-color: #e0e0e0 !important;
                            font-family: Helvetica, Arial, sans-serif;
                            font-weight: bold !important;
                        }}

                        /* SOLUTION TABLE */
                        .sol-table {{
                            width: 100%;
                            border-collapse: collapse;
                            font-size: 12px;
                            margin-top: 0px;
                        }}
                        .sol-table th {{
                            background-color: #003366;
                            color: white;
                            padding: 8px;
                            text-align: center;
                            /* Header Bold in English Font */
                            font-family: Helvetica, Arial, sans-serif;
                            font-weight: bold;
                            border: 1px solid #003366;
                        }}
                        .sol-table td {{
                            padding: 8px;
                            border: 0.5px solid #cccccc;
                            vertical-align: top;
                            background-color: white;
                            line-height: 1.4;
                            text-align: left;
                            font-family: 'HindVadodara', sans-serif; /* Gujarati Content */
                        }}
                        .sol-row:nth-child(even) td {{
                            background-color: #f9f9f9;
                        }}
                        
                        .ans-bold {{
                            color:#003366; 
                            font-family: Helvetica, Arial, sans-serif;
                            font-weight: bold;
                        }}

                        /* FOOTER */
                        .footer-links {{
                            position: fixed; bottom: 10mm; left: 25mm; right: 25mm; height: 40mm;
                        }}
                        a {{ text-decoration: none; color: transparent; display: inline-block; width: 45%; height: 100%; }}
                    </style>
                </head>
                <body>
                """

                # --- PART 1: ANSWER KEY ---
                file_name_clean = os.path.splitext(pdf_file.name)[0].replace("_", " ")
                html_content += f"<div class='title'>{file_name_clean} | ANSWER KEY</div>"
                
                html_content += "<div class='key-container'>"
                questions_per_col = 25
                num_cols = math.ceil(total_questions / questions_per_col)
                
                for c in range(num_cols):
                    html_content += "<table class='key-table'>"
                    html_content += "<thead><tr><th>NO</th><th>ANS</th></tr></thead><tbody>"
                    for r in range(questions_per_col):
                        q_num = c * questions_per_col + (r + 1)
                        if q_num <= total_questions:
                            ans = answers.get(q_num, "-")
                            html_content += f"<tr><td class='col-no'>{q_num}</td><td>{ans}</td></tr>"
                    html_content += "</tbody></table>"
                html_content += "</div>"

                html_content += f"<div class='footer-links'><a href='{TG_LINK}'>.</a><a href='{IG_LINK}' style='float:right'>.</a></div>"

                # --- PART 2: SOLUTIONS ---
                if add_solution and solution_text.strip():
                    html_content += "<div style='break-before: page;'></div>"
                    html_content += "<div class='title'>DETAILED SOLUTIONS</div>"
                    
                    html_content += """
                    <table class='sol-table'>
                        <thead>
                            <tr>
                                <th style='width:8%'>NO</th>
                                <th style='width:22%'>ANSWER</th>
                                <th style='width:70%'>EXPLANATION</th>
                            </tr>
                        </thead>
                        <tbody>
                    """
                    
                    lines = solution_text.strip().split('\n')
                    for line in lines:
                        parts = line.split('|')
                        if len(parts) >= 1:
                            no_txt = parts[0].strip()
                            ans_txt = parts[1].strip() if len(parts) > 1 else ""
                            expl_txt = parts[2].strip() if len(parts) > 2 else ""
                            
                            html_content += f"""
                            <tr class='sol-row'>
                                <td class='col-no' style='text-align:center'>{no_txt}</td>
                                <td class='ans-bold'>{ans_txt}</td>
                                <td>{expl_txt}</td>
                            </tr>
                            """
                    html_content += "</tbody></table>"

                html_content += "</body></html>"

                # 5. GENERATE PDF
                font_config = FontConfiguration()
                pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
                
                # 6. MERGE
                reader_main = PdfReader(pdf_file)
                reader_generated = PdfReader(io.BytesIO(pdf_bytes))
                writer = PdfWriter()
                
                # Merge Watermark
                for i in range(len(reader_main.pages)):
                    page = reader_main.pages[i]
                    page.merge_page(watermark_page)
                    writer.add_page(page)
                
                for page in reader_generated.pages:
                    writer.add_page(page)
                
                final_out = io.BytesIO()
                writer.write(final_out)
                
                st.success("✅ PDF Generated!")
                st.download_button("Download PDF 📥", final_out.getvalue(), f"{os.path.splitext(pdf_file.name)[0]}_FINAL.pdf", "application/pdf")

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("Check requirements.txt")
    else:
        st.warning("Please upload files.")
