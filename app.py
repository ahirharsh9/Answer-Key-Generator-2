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

# --- CUSTOM FONT LOADER (From Your Drive Link) ---
@st.cache_resource
def load_assets():
    # 1. Download Font from YOUR Google Drive Link
    # File ID from your link: 1jVDKtad01ecE6dwitiAlrqR5Ov1YsJzw
    font_id = "1jVDKtad01ecE6dwitiAlrqR5Ov1YsJzw"
    font_url = f"https://drive.google.com/uc?export=download&id={font_id}"
    
    font_filename = "MyCustomFont.ttf"
    
    if not os.path.exists(font_filename):
        try:
            response = requests.get(font_url)
            if response.status_code == 200:
                with open(font_filename, "wb") as f:
                    f.write(response.content)
            else:
                st.error("❌ Failed to download Font from Google Drive.")
        except Exception as e:
            st.error(f"⚠️ Font download error: {e}")

    # 2. Default Background Image (Backup)
    default_bg_url = "https://drive.google.com/uc?export=download&id=1NUwoSCN2OIWgjPQMPX1VileweKzta_HW"
    try:
        response = requests.get(default_bg_url)
        if response.status_code == 200:
            return response.content
    except:
        return None
    return None

default_bg_bytes = load_assets()

# --- HELPER: IMAGE TO BASE64 ---
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
st.markdown("Using **Custom HindVadodara Font** from your Google Drive.")

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

# --- GENERATE PDF ---
if st.button("Generate PDF 🚀"):
    if pdf_file and csv_file:
        try:
            with st.spinner("Rendering PDF with your custom font..."):
                
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

                # 2. Background Image
                if img_file_upload:
                    bg_b64 = get_image_base64(img_file_upload.getvalue())
                elif default_bg_bytes:
                    bg_b64 = get_image_base64(default_bg_bytes)
                else:
                    bg_b64 = ""

                # 3. HTML & CSS (Pointing to Downloaded Font)
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        /* Load Custom Font from Local File */
                        @font-face {{
                            font-family: 'MyCustomFont';
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
                            font-family: 'MyCustomFont', sans-serif;
                            margin: 0;
                            padding: 63.5mm 25mm 15mm 25mm;
                        }}
                        .title {{
                            text-align: center;
                            font-family: 'MyCustomFont';
                            font-weight: bold;
                            font-size: 22px;
                            color: white;
                            margin-bottom: 10mm;
                            text-transform: uppercase;
                        }}
                        
                        /* Answer Key Style */
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
                            font-weight: bold;
                        }}
                        .key-table td {{
                            padding: 4px;
                            border: 0.5px solid #cccccc;
                            text-align: center;
                            background-color: white;
                        }}
                        .col-no {{
                            background-color: #e0e0e0 !important;
                            font-weight: bold;
                        }}
                        
                        /* Solution Style */
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
                            font-weight: bold;
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
                        
                        /* Footer */
                        .footer-links {{
                            position: fixed; bottom: 10mm; left: 25mm; right: 25mm; height: 40mm;
                        }}
                        a {{ text-decoration: none; color: transparent; display: inline-block; width: 45%; height: 100%; }}
                    </style>
                </head>
                <body>
                """

                # Content Generation
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

                if add_solution and solution_text.strip():
                    html_content += "<div style='break-before: page;'></div>"
                    html_content += "<div class='title'>DETAILED SOLUTIONS</div>"
                    html_content += "<table class='sol-table'><thead><tr><th style='width:10%'>NO</th><th style='width:25%'>ANSWER</th><th>EXPLANATION</th></tr></thead><tbody>"
                    
                    lines = solution_text.strip().split('\n')
                    for line in lines:
                        parts = line.split('|')
                        if len(parts) >= 1:
                            no_txt = parts[0].strip()
                            ans_txt = parts[1].strip() if len(parts) > 1 else ""
                            expl_txt = parts[2].strip() if len(parts) > 2 else ""
                            html_content += f"<tr class='sol-row'><td class='col-no' style='text-align:center'>{no_txt}</td><td style='font-weight:bold; color:#003366'>{ans_txt}</td><td>{expl_txt}</td></tr>"
                    html_content += "</tbody></table>"

                html_content += "</body></html>"

                # 4. Generate PDF
                font_config = FontConfiguration()
                pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
                
                # 5. Merge
                reader_main = PdfReader(pdf_file)
                reader_generated = PdfReader(io.BytesIO(pdf_bytes))
                writer = PdfWriter()
                
                for page in reader_main.pages:
                    writer.add_page(page)
                for page in reader_generated.pages:
                    writer.add_page(page)
                
                final_out = io.BytesIO()
                writer.write(final_out)
                
                st.success("✅ PDF Generated using YOUR Custom Font!")
                st.download_button("Download Final PDF 📥", final_out.getvalue(), f"{os.path.splitext(pdf_file.name)[0]}_FINAL.pdf", "application/pdf")

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("Ensure packages.txt is correct on GitHub.")
    else:
        st.warning("Upload files first.")
