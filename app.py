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

# --- CUSTOM FONT LOADER ---
@st.cache_resource
def load_assets():
    # 1. Gujarati Font (Hind Vadodara from your Drive)
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

# --- HELPER: MIXED FONT TEXT ---
def format_mixed_text(text):
    """
    Splits text to wrap Gujarati in CustomFont and English/Numbers in Sans-Serif (Bold).
    """
    if not isinstance(text, str): return str(text)
    
    # Logic: If character is Gujarati, wrap in span with custom font.
    # Otherwise (English/Numbers), let it use system sans-serif (which looks better/bolder).
    
    # Simple strategy: Wrap the whole thing in a wrapper that defaults to English font,
    # but uses CSS class for Gujarati parts.
    
    # Regex to find Gujarati segments
    # Gujarati Unicode Range: \u0A80-\u0AFF
    formatted_html = ""
    parts = re.split(r'([^\u0000-\u007F]+)', text) # Split by non-ASCII (assuming non-ascii is Gujarati here)
    
    for part in parts:
        if re.search(r'[^\u0000-\u007F]', part): # It has non-ascii (Gujarati)
            formatted_html += f"<span class='guj-font'>{part}</span>"
        else:
            formatted_html += f"<span class='eng-font'>{part}</span>"
            
    return formatted_html

# --- SIDEBAR ---
st.sidebar.title("⚙️ સેટિંગ્સ")
WATERMARK_TEXT = st.sidebar.text_input("Watermark Text", "MURLIDHAR ACADEMY")
TG_LINK = st.sidebar.text_input("Telegram Link", "https://t.me/MurlidharAcademy")
IG_LINK = st.sidebar.text_input("Instagram Link", "https://www.instagram.com/murlidhar_academy_official/")
st.sidebar.divider()
st.sidebar.info("Designed by Harsh Solanki")

# --- MAIN UI ---
st.title("📝 Answer Key & Solution Generator")
st.markdown("Features: **Every Page Watermark** + **Better English Fonts** + **Perfect Margins**")

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
        placeholder="1 | A - પાટણ | પાટણ રાણકી વાવ માટે પ્રખ્યાત છે.\n2 | B - Text | English looks bold."
    )

# --- PDF GENERATION ---
if st.button("Generate PDF 🚀"):
    if pdf_file and csv_file:
        try:
            with st.spinner("Processing PDF..."):
                
                # 1. CREATE WATERMARK PDF (Using ReportLab)
                # We create a single watermark page first
                packet_wm = io.BytesIO()
                reader_temp = PdfReader(pdf_file)
                page1 = reader_temp.pages[0]
                width = float(page1.mediabox.width)
                height = float(page1.mediabox.height)
                
                c_wm = canvas.Canvas(packet_wm, pagesize=(width, height))
                c_wm.setFillColor(colors.grey, alpha=0.10) # Light opacity
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

                # 2. PREPARE DATA
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

                # 4. HTML CONSTRUCTION
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        /* Load Gujarati Font */
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
                            /* Base Font settings */
                            font-family: Helvetica, Arial, sans-serif; /* Default English looks good here */
                            margin: 0;
                            /* Adjusted Margins for Alignment */
                            padding: 63.5mm 25mm 15mm 25mm;
                        }}
                        
                        /* Font Classes */
                        .guj-font {{ font-family: 'MyCustomFont'; }}
                        .eng-font {{ font-family: Helvetica, Arial, sans-serif; font-weight: bold; }}

                        .title {{
                            text-align: center;
                            font-family: 'MyCustomFont';
                            font-weight: bold;
                            font-size: 22px;
                            color: white;
                            margin-bottom: 10mm;
                            text-transform: uppercase;
                        }}
                        
                        /* KEY TABLE */
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

                        /* SOLUTION TABLE */
                        .sol-table {{
                            width: 100%;
                            border-collapse: collapse;
                            font-size: 11px; /* Slightly smaller to fit content */
                            margin-top: 10px;
                        }}
                        .sol-table th {{
                            background-color: #003366;
                            color: white;
                            padding: 8px;
                            text-align: center;
                            font-weight: bold;
                            border: 1px solid #003366;
                        }}
                        .sol-table td {{
                            padding: 8px;
                            border: 0.5px solid #cccccc;
                            vertical-align: top;
                            background-color: white;
                            line-height: 1.4;
                            text-align: left; /* Ensure left alignment */
                        }}
                        .sol-row:nth-child(even) td {{
                            background-color: #f9f9f9;
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

                # --- Content: Answer Key ---
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
                            # Format Answer (Mixed Fonts)
                            fmt_ans = format_mixed_text(ans)
                            html_content += f"<tr><td class='col-no'>{q_num}</td><td>{fmt_ans}</td></tr>"
                    html_content += "</tbody></table>"
                html_content += "</div>"

                html_content += f"<div class='footer-links'><a href='{TG_LINK}'>.</a><a href='{IG_LINK}' style='float:right'>.</a></div>"

                # --- Content: Solutions ---
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
                            no_txt = format_mixed_text(parts[0].strip())
                            ans_txt = format_mixed_text(parts[1].strip()) if len(parts) > 1 else ""
                            expl_txt = format_mixed_text(parts[2].strip()) if len(parts) > 2 else ""
                            
                            html_content += f"""
                            <tr class='sol-row'>
                                <td class='col-no' style='text-align:center'>{no_txt}</td>
                                <td style='color:#003366; font-weight:bold;'>{ans_txt}</td>
                                <td>{expl_txt}</td>
                            </tr>
                            """
                    html_content += "</tbody></table>"

                html_content += "</body></html>"

                # 5. GENERATE HTML PDF
                font_config = FontConfiguration()
                pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
                
                # 6. MERGING LOGIC (Watermark on EVERY Page)
                reader_main = PdfReader(pdf_file)
                reader_generated = PdfReader(io.BytesIO(pdf_bytes))
                writer = PdfWriter()
                
                # Step A: Add Question Paper Pages (With Watermark on EACH)
                for i in range(len(reader_main.pages)):
                    page = reader_main.pages[i]
                    page.merge_page(watermark_page) # Merge watermark on this specific page
                    writer.add_page(page)
                
                # Step B: Add Answer Key/Solution Pages (Already has background)
                for page in reader_generated.pages:
                    writer.add_page(page)
                
                final_out = io.BytesIO()
                writer.write(final_out)
                
                st.success("✅ PDF Generated: Perfect Fonts & Watermarks!")
                st.download_button("Download PDF 📥", final_out.getvalue(), f"{os.path.splitext(pdf_file.name)[0]}_FINAL.pdf", "application/pdf")

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("Ensure packages.txt exists on GitHub.")
    else:
        st.warning("Please upload files.")
