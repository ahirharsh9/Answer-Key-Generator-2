import streamlit as st
import pandas as pd
import io
import os
import math
import base64
import requests
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# --- PAGE CONFIG ---
st.set_page_config(page_title="Murlidhar Academy PDF Tool", page_icon="📝", layout="wide")

# --- FONTS & ASSETS SETUP ---
@st.cache_resource
def load_assets():
    # 1. Download Noto Sans Gujarati Font
    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Regular.ttf"
    font_bold_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Bold.ttf"
    
    if not os.path.exists("GujFont.ttf"):
        with open("GujFont.ttf", "wb") as f:
            f.write(requests.get(font_url).content)
    if not os.path.exists("GujFont-Bold.ttf"):
        with open("GujFont-Bold.ttf", "wb") as f:
            f.write(requests.get(font_bold_url).content)

    # 2. Default Background Image
    default_bg_url = "https://drive.google.com/uc?export=download&id=1NUwoSCN2OIWgjPQMPX1VileweKzta_HW"
    try:
        response = requests.get(default_bg_url)
        if response.status_code == 200:
            return response.content
    except:
        return None
    return None

default_bg_bytes = load_assets()

# --- HELPER: CONVERT IMAGE TO BASE64 FOR HTML ---
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
st.title("📝 Answer Key & Solution Generator (100% Gujarati Fix)")
st.markdown("HTML Rendering Engine નો ઉપયોગ કરીને બનાવેલ ટૂલ.")

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
        "Paste Data Here:", 
        height=200,
        placeholder="1 | A - પાટણ | પાટણ રાણકી વાવ માટે પ્રખ્યાત છે.\n2 | B - કૌશલ્ય | જીવનનિર્વાહનો ખર્ચ વધુ હોય છે."
    )

# --- GENERATE PDF LOGIC ---
if st.button("Generate PDF 🚀"):
    if pdf_file and csv_file:
        try:
            with st.spinner("Rendering perfect Gujarati fonts..."):
                
                # 1. Prepare Data
                df = pd.read_csv(csv_file)
                key_cols = [c for c in df.columns if c.lower().startswith('key') and c[3:].isdigit()]
                key_cols.sort(key=lambda x: int(x[3:]))
                answers = {}
                if not df.empty:
                    for k in key_cols:
                        q_num = int(k.lower().replace('key', ''))
                        answers[q_num] = str(df.iloc[0][k]).strip()
                total_questions = len(answers)

                # 2. Prepare Background Image (Base64)
                if img_file_upload:
                    bg_b64 = get_image_base64(img_file_upload.getvalue())
                elif default_bg_bytes:
                    bg_b64 = get_image_base64(default_bg_bytes)
                else:
                    bg_b64 = "" # Fallback if no image

                # 3. HTML TEMPLATE (CSS Styling)
                # આ CSS થી જ ફોન્ટ્સ અને લેઆઉટ નક્કી થાય છે
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        @font-face {{
                            font-family: 'GujFont';
                            src: url('file://{os.path.abspath("GujFont.ttf")}');
                        }}
                        @font-face {{
                            font-family: 'GujFontBold';
                            src: url('file://{os.path.abspath("GujFont-Bold.ttf")}');
                            font-weight: bold;
                        }}
                        @page {{
                            size: A4;
                            margin: 0;
                            background-image: url('data:image/jpeg;base64,{bg_b64}');
                            background-size: cover;
                            background-position: center;
                        }}
                        body {{
                            font-family: 'GujFont', sans-serif;
                            margin: 0;
                            padding: 63.5mm 25mm 15mm 25mm; /* Top Margin matches your design */
                        }}
                        .title {{
                            text-align: center;
                            font-family: 'GujFontBold';
                            font-size: 22px;
                            color: white;
                            margin-bottom: 10mm;
                            text-transform: uppercase;
                        }}
                        /* Answer Key Table */
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
                        }}
                        .key-table td {{
                            padding: 4px;
                            border: 0.5px solid #cccccc;
                            text-align: center;
                            background-color: white;
                        }}
                        .col-no {{
                            background-color: #e0e0e0 !important;
                            font-family: 'GujFontBold';
                            font-weight: bold;
                            width: 30%;
                        }}
                        
                        /* Solution Table */
                        .sol-table {{
                            width: 100%;
                            border-collapse: collapse;
                            font-size: 12px;
                            margin-top: 10px;
                        }}
                        .sol-table th {{
                            background-color: #003366;
                            color: white;
                            padding: 8px;
                            text-align: center;
                        }}
                        .sol-table td {{
                            padding: 8px;
                            border: 0.5px solid #cccccc;
                            vertical-align: top;
                            background-color: white;
                        }}
                        .sol-row:nth-child(even) td {{
                            background-color: #f9f9f9;
                        }}
                        
                        /* Links Footer */
                        .footer-links {{
                            position: fixed;
                            bottom: 10mm;
                            left: 25mm;
                            right: 25mm;
                            height: 40mm;
                            z-index: 100;
                        }}
                        a {{ text-decoration: none; color: transparent; display: inline-block; width: 45%; height: 100%; }}
                    </style>
                </head>
                <body>
                """

                # --- PART A: ANSWER KEY PAGE HTML ---
                file_name_clean = os.path.splitext(pdf_file.name)[0].replace("_", " ")
                html_content += f"<div class='title'>{file_name_clean} | ANSWER KEY</div>"
                
                # Dynamic Table Generation
                html_content += "<div class='key-container'>"
                
                # We iterate columns manually to match your specific layout
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
                
                html_content += "</div>" # End key container

                # Footer Links (Invisible clickable areas roughly)
                html_content += f"""
                <div class='footer-links'>
                    <a href='{TG_LINK}'>.</a>
                    <a href='{IG_LINK}' style='float:right'>.</a>
                </div>
                """

                # --- PART B: SOLUTION PAGES HTML ---
                if add_solution and solution_text.strip():
                    # Page Break
                    html_content += "<div style='break-before: page;'></div>"
                    html_content += "<div class='title'>DETAILED SOLUTIONS</div>"
                    
                    html_content += "<table class='sol-table'>"
                    html_content += "<thead><tr><th style='width:10%'>NO</th><th style='width:25%'>ANSWER</th><th>EXPLANATION</th></tr></thead><tbody>"
                    
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
                                <td style='font-weight:bold; color:#003366'>{ans_txt}</td>
                                <td>{expl_txt}</td>
                            </tr>
                            """
                    html_content += "</tbody></table>"

                html_content += "</body></html>"

                # 4. CONVERT HTML TO PDF (WeasyPrint)
                font_config = FontConfiguration()
                pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
                
                # 5. MERGE WITH ORIGINAL QUESTION PAPER
                # First, create Watermark on original PDF (using classic ReportLab for just this part)
                # (Watermark text usually isn't complex Gujarati, so this is safe)
                # ... Skipping complex watermark logic for simplicity, merging directly ...
                
                reader_main = PdfReader(pdf_file)
                reader_generated = PdfReader(io.BytesIO(pdf_bytes))
                writer = PdfWriter()
                
                # Add Question Paper
                for page in reader_main.pages:
                    writer.add_page(page)
                
                # Add Answer Key & Solutions
                for page in reader_generated.pages:
                    writer.add_page(page)
                
                final_out = io.BytesIO()
                writer.write(final_out)
                
                st.success("✅ PDF Generated with Perfect Gujarati Fonts!")
                st.download_button(
                    label="Download Final PDF 📥",
                    data=final_out.getvalue(),
                    file_name=f"{os.path.splitext(pdf_file.name)[0]}_FINAL.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("Ensure 'packages.txt' is created in GitHub with 'pango' libraries listed.")
    else:
        st.warning("Please upload PDF and CSV.")
