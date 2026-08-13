# app.py
import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
import os
from datetime import datetime
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import code39
from reportlab.graphics import renderPDF

# Page configuration
st.set_page_config(
    page_title="Pending Lines - Barcode Generator (4x6 Labels)",
    page_icon="📦",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton > button:hover {
        background-color: #155a8a;
        color: white;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration
USERNAME = "Raytest"
PASSWORD = "Oxoxoxox1!"
COMPANY_NAME = "18 Wheels Logistics Ltd"
ENCODED_COMPANY = quote(COMPANY_NAME, safe='')
BASE_URL = f"https://18whe.camelot3plcloud.com:37048/WEBSERVICES/ODataV4/Company('{ENCODED_COMPANY}')"
PENDING_URL = f"{BASE_URL}/Pending_Lines"

# Item to Serial mapping
ITEM_SERIAL_MAP = {
    '800382xx': '3J73H',
    '800380xx': 'XQ04S',
    '01101-12': '849429003427',
    '01102-12': '849429003434',
    '01103-12': '849429003441',
    '01104-12': '849429003458',
    '01110-12': '849429003465',
    '01111-12': '849429003472',
    '01115-12': '849429003489',
    '01118-12': '849429003496',
    '01119-12': '849429003502',
    '01121-12': '849429003526',
    '01122-12': '849429003533',
    '01125-12': '849429003557',
    '01105-12': '849429003564',
    '01106-12': '10849429003233',
    '01127-12': '10849429004360',
    '01130-12': '10849429004537',
    '01131-12': '10849429004605',
    '01107-12': '10849429003974',
    '01133-12': '10849429004681',
    '01134-12': '10849429004773',
    '01135-12': '10849429004865',
    '01145-12': '10849429004766',
    '01401-12': '10849429000898',
    '01402-12': '10849429002496',
    '01403-12': '10849429002502',
    '01404-12': '10849429000928',
    '01410-12': '10849429000935',
    '01411-12': '10849429000911',
    '01415-12': '10849429000942',
    '01419-12': '10849429000966',
    '01422-12': '10849429000904',
    '01425-12': '10849429002540',
    '01427-12': '10849429005008',
    '01405-12': '10849429002557',
    '01421-12': '10849429000959',
    '01406-12': '10849429004476',
    '01956-12': '20849429002424',
    'CAN-01625-12': '10894773001893',
    '00225-16': '10894773001879',
    'CAN-01619-12': '10894773001640',
    'CAN-01615-12': '10894773001633',
    'CAN-01610-12': '10894773001626',
    '00211-16': '10894773001527',
    '00219-16': '10894773001381',
    '00204-16': '10894773001336',
    '00210-16': '10894773001329',
    '00222-16': '10894773001312',
    '00201-16': '10894773001305',
    '01435-12': '10849429005022',
    '01434-12': '10849429005015',
    '08136-12': '10849429004971',
    'CAN-03733-12': '10849429004933',
    'CAN-03735-12': '10849429004919',
    '01431-12': '10849429004889',
    'CAN-01931-12': '10849429004841',
    'CAN-01930-12': '10849429004834',
    'CAN-01631-12': '10849429004827',
    'CAN-03731-12': '10849429004810',
    'CAN-01630-12': '10849429004803',
    'CAN-03730-12': '10849429004797',
    '08131-12': '10849429004759',
    '01931-12': '10849429004742',
    '01430-12': '10849429004735',
    '01455-12': '10849429004728',
    '08134-12': '10849429004704',
    '02234-12': '10849429004698',
    '02233-12': '10849429004674',
    '08155-12': '10849429004667',
    '02231-12': '10849429004599',
    '01450-12': '10849429004582',
    '08150-12': '10849429004575',
    '01930-12': '10849429004551',
    '08130-12': '10849429004544',
    '02230-12': '10849429004520',
    '00206-16': '10849429004490',
    '00205-16': '10849429004483',
    '08108-12': '10849429004469',
    'CAN-01905-12': '10849429004124',
    'CAN-01911-12': '10849429004117',
    'CAN-01903-12': '10849429004100',
    'CAN-01901-12': '10849429004094',
    'CAN-00606-12': '10849429003691',
    '08116-12': '10849429003226',
    'CAN-01955-12': '10849429003059',
    'CAN-01954-12': '10849429003042',
    '02227-12': '10849429002991',
    '01955-12': '10849429002458',
    '01954-12': '10849429002441',
    '02235-12': '10849429002298',
    '08119-12': '10849429001901',
    '08122-12': '10849429001895',
    '08115-12': '10849429001888',
    '08111-12': '10849429001871',
    '08110-12': '10849429001864',
    '08104-12': '10849429001857',
    '08101-12': '10849429001840',
    '01922-12': '10849429001703',
    '01911-12': '10849429001680',
    '01910-12': '10849429001673',
    '01904-12': '10849429001666',
    '01901-12': '10849429001642',
    '01708-12': '10849429001512',
    '01707-12': '10849429001505',
    '01706-12': '10849429001499',
    '01704-12': '10849429001475',
    '01703-12': '10849429001468',
    '01957-12': '10849429001413',
    '08105-12': '10849429001055',
    'CAN-01953-12': '10849429000720',
    'CAN-01952-12': '10849429000713',
    'CAN-01951-12': '10849429000706',
    '01953-12': '10849429000560',
    '01952-12': '10849429000317',
    '01951-12': '10849429000300',
    '01950-12': '10849429000294',
    'CAN-01605-12': '10849429000010',
    'CAN-01622-12': '894773001513',
    'CAN-01611-12': '894773001506',
    'CAN-01604-12': '894773001490',
    'CAN-01603-12': '894773001483',
    'CAN-01602-12': '894773001476',
    'CAN-01601-12': '894773001469',
    'RP-00710-12': '849429004950',
    'CAN-00240-12': '849429004943',
    '00253-12': '849429004905',
    '00241-12': '849429004875',
    'CAN-00250-12': '849429004714',
    '00399-12': '849429004646',
    '00250-12': '849429004622',
    'RP-00909-12': '849429004448',
    '00391-12': '849429004424',
    '00390-12': '849429004417',
    '02206-12': '849429004400',
    'CAN-03706-12': '849429003717',
    'CAN-03705-12': '849429003182',
    'CAN-03703-12': '849429003175',
    'CAN-03719-12': '849429003168',
    'CAN-03722-12': '849429003137',
    'CAN-03711-12': '849429003120',
    'CAN-03701-12': '849429003106',
    '01905-12': '849429002758',
    '08103-12': '849429002697',
    '02205-12': '849429002482',
    'RP-00908-12': '849429000747',
    '02219-12': '849429000228',
    '02210-12': '849429000211',
    '02203-12': '849429000204',
    '02202-12': '849429000198',
    '02218-12': '849429000174',
    '02225-12': '849429000150',
    '02222-12': '849429000143',
    '02221-12': '849429000136',
    '02215-12': '849429000129',
    '02211-12': '849429000112',
    '02204-12': '849429000105',
    '02201-12': '849429000099',
    '151994xx': 'JX5M0',
    '011105-13xx': 'U7L2F',
    '00605-12xx': 'LJG7Q',
}

@st.cache_data(ttl=300)
def fetch_pending_lines(document_prefix=None, client_codes=None, limit=5000, skip=0):
    """Fetch Pending_Lines with optional filters"""
    try:
        filters = []
        
        if document_prefix:
            filters.append(f"startswith(Document, '{document_prefix}')")
        
        if client_codes and len(client_codes) > 0:
            client_filter = " or ".join([f"(Client eq '{code}')" for code in client_codes])
            filters.append(f"({client_filter})")
        
        filter_str = " and ".join(filters) if filters else ""
        
        if filter_str:
            url = f"{PENDING_URL}?$filter={filter_str}&$orderby=Document desc&$top={limit}&$skip={skip}"
        else:
            url = f"{PENDING_URL}?$orderby=Document desc&$top={limit}&$skip={skip}"
        
        response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=60)
        
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
            return None
        
        data = response.json()
        rows = data.get("value", [])
        
        if rows:
            clean_rows = []
            for row in rows:
                clean_row = {k: v for k, v in row.items() if not k.startswith('@')}
                clean_rows.append(clean_row)
            
            df = pd.DataFrame(clean_rows)
            
            # Add Serial Number mapping
            df['Expected_Serial'] = df['Item'].map(ITEM_SERIAL_MAP)
            
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def generate_barcode_pdf(document_data, document_name):
    """Generate PDF with one barcode per page on 4x6 inch labels using ReportLab's barcode"""
    buffer = io.BytesIO()
    
    # Filter out items without serial
    items_with_serial = document_data[document_data['Expected_Serial'].notna() & (document_data['Expected_Serial'] != '')]
    
    if len(items_with_serial) == 0:
        doc = SimpleDocTemplate(buffer, pagesize=(4*inch, 6*inch))
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f77b4'),
            alignment=1,
            spaceAfter=10
        )
        elements.append(Paragraph(f"Document: {document_name}", title_style))
        elements.append(Paragraph("No items with serial numbers found.", styles['Normal']))
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    # Create PDF with 4x6 inch pages
    doc = SimpleDocTemplate(buffer, pagesize=(4*inch, 6*inch), leftMargin=15, rightMargin=15, topMargin=15, bottomMargin=15)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles for 4x6 labels
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=11,
        textColor=colors.HexColor('#1f77b4'),
        alignment=1,
        spaceAfter=3
    )
    
    page_style = ParagraphStyle(
        'PageStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1,
        spaceAfter=5
    )
    
    item_style = ParagraphStyle(
        'ItemStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        alignment=1,
        spaceAfter=6,
        bold=True
    )
    
    serial_style = ParagraphStyle(
        'SerialStyle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#d32f2f'),
        alignment=1,
        spaceAfter=6,
        bold=True
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=1,
        spaceBefore=5
    )
    
    total_pages = len(items_with_serial)
    
    for idx, (_, row) in enumerate(items_with_serial.iterrows(), 1):
        item = row.get('Item', '')
        serial = row.get('Expected_Serial', '')
        
        # Create page content
        page_content = []
        
        # Document header
        page_content.append(Paragraph(f"Document: {document_name}", title_style))
        page_content.append(Paragraph(f"Page {idx} of {total_pages}", page_style))
        page_content.append(Spacer(1, 3))
        
        # Item name
        page_content.append(Paragraph(f"{item}", item_style))
        page_content.append(Spacer(1, 4))
        
        # Generate barcode using ReportLab's Code39
        try:
            # Create Code39 barcode
            barcode_obj = code39.Code39(
                str(serial),
                barWidth=0.4,
                barHeight=40,
                humanReadable=False,
                stop=True,
                start=True
            )
            
            # Create drawing
            barcode_drawing = Drawing(260, 60)
            barcode_drawing.add(barcode_obj)
            
            # Add the barcode drawing to the page
            page_content.append(Spacer(1, 2))
            page_content.append(barcode_drawing)
            page_content.append(Spacer(1, 2))
            
        except Exception as e:
            error_style = ParagraphStyle(
                'ErrorStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.red,
                alignment=1
            )
            page_content.append(Paragraph(f"⚠️ Barcode unavailable: {serial}", error_style))
        
        page_content.append(Spacer(1, 3))
        
        # Serial number (large, red, centered)
        page_content.append(Paragraph(f"{serial}", serial_style))
        
        # Footer at bottom of label
        page_content.append(Spacer(1, 4))
        page_content.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", footer_style))
        page_content.append(Paragraph("Scan with any barcode scanner", footer_style))
        
        # Page break
        if idx < total_pages:
            page_content.append(PageBreak())
        
        elements.extend(page_content)
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def load_data(prefix, selected_clients):
    """Load data from API"""
    with st.spinner("Fetching data from API..."):
        prefix_filter = None if prefix == "All" else prefix
        
        df = fetch_pending_lines(
            document_prefix=prefix_filter,
            client_codes=selected_clients if selected_clients else None,
            limit=5000,
            skip=0
        )
        
        if df is not None:
            st.session_state.df = df
            st.session_state.selected_documents = []
            st.success(f"✅ Loaded {len(df)} records!")
        else:
            st.error("Failed to load data")

def main():
    # Header
    st.markdown('<div class="main-header">📦 Pending Lines - 4x6 Barcode Labels</div>', unsafe_allow_html=True)
    
    # Info box
    st.markdown("""
    <div class="info-box">
        <strong>📋 4x6 Inch Labels</strong><br>
        Each barcode prints on a 4x6 inch label format. Perfect for shipping labels and warehouse scanning.
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'selected_documents' not in st.session_state:
        st.session_state.selected_documents = []
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Filters")
        
        auto_load = st.checkbox("🔄 Auto-load data on startup", value=True)
        
        prefix = st.selectbox(
            "Document Prefix",
            ["All", "S0", "R", "RA"],
            index=0
        )
        
        st.subheader("Client Codes")
        client_options = ["ZE01", "ZE03", "ZE05", "ZE06", "ZE07"]
        selected_clients = st.multiselect(
            "Select Clients",
            client_options,
            default=["ZE01", "ZE03"]
        )
        
        st.subheader("🔎 Document Search")
        doc_search = st.text_input("Search for Document (partial match)")
        
        load_button = st.button("🔄 Load Data", use_container_width=True, type="primary")
        
        if st.button("🗑️ Clear Selection", use_container_width=True):
            st.session_state.selected_documents = []
            st.rerun()
    
    # Auto-load on startup
    if auto_load and st.session_state.df is None:
        load_data(prefix, selected_clients)
    
    if load_button:
        load_data(prefix, selected_clients)
    
    # Main content
    if st.session_state.df is not None and not st.session_state.df.empty:
        df = st.session_state.df
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><h3>📊 Total Records</h3><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
        with col2:
            unique_docs = df['Document'].nunique() if 'Document' in df.columns else 0
            st.markdown(f'<div class="metric-card"><h3>📄 Documents</h3><h2>{unique_docs}</h2></div>', unsafe_allow_html=True)
        with col3:
            unique_items = df['Item'].nunique() if 'Item' in df.columns else 0
            st.markdown(f'<div class="metric-card"><h3>🔢 Unique Items</h3><h2>{unique_items}</h2></div>', unsafe_allow_html=True)
        with col4:
            matched_serials = df['Expected_Serial'].notna().sum() if 'Expected_Serial' in df.columns else 0
            st.markdown(f'<div class="metric-card"><h3>✅ Serials Found</h3><h2>{matched_serials}/{len(df)}</h2></div>', unsafe_allow_html=True)
        
        # Document selector
        st.subheader("📋 Document Selection")
        
        if doc_search:
            filtered_df = df[df['Document'].astype(str).str.contains(doc_search, case=False, na=False)]
        else:
            filtered_df = df
        
        unique_docs = filtered_df['Document'].unique() if 'Document' in filtered_df.columns else []
        
        valid_selected = [doc for doc in st.session_state.selected_documents if doc in unique_docs]
        if valid_selected != st.session_state.selected_documents:
            st.session_state.selected_documents = valid_selected
        
        selected_docs = st.multiselect(
            "Select Documents to view",
            sorted(unique_docs) if len(unique_docs) > 0 else [],
            default=valid_selected
        )
        st.session_state.selected_documents = selected_docs
        
        if selected_docs:
            display_df = df[df['Document'].isin(selected_docs)]
        else:
            display_df = df
        
        # Display data
        st.subheader(f"📊 Data Preview ({len(display_df)} rows)")
        
        display_cols = ['Document', 'Client', 'Item', 'Expected_Serial', 'Description', 'Qty_Ordered', 'Qty_Picked']
        display_cols = [col for col in display_cols if col in display_df.columns]
        
        def highlight_serials(row):
            if 'Expected_Serial' in row and pd.notna(row['Expected_Serial']) and row['Expected_Serial'] != '':
                return ['background-color: #d4edda'] * len(row)
            else:
                return ['background-color: #fff3cd'] * len(row)
        
        styled_df = display_df[display_cols].style.apply(highlight_serials, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Barcode generation
        if selected_docs:
            st.subheader("📄 4x6 Label Generation")
            st.info("💡 Each label is 4x6 inches - perfect for shipping labels")
            
            for doc in selected_docs:
                doc_data = df[df['Document'] == doc]
                items_with_serial = doc_data[doc_data['Expected_Serial'].notna() & (doc_data['Expected_Serial'] != '')]
                
                with st.expander(f"📄 Document: {doc} ({len(doc_data)} items, {len(items_with_serial)} with serials)", expanded=True):
                    item_cols = ['Item', 'Expected_Serial', 'Description', 'Qty_Ordered']
                    item_cols = [col for col in item_cols if col in doc_data.columns]
                    st.dataframe(doc_data[item_cols], use_container_width=True)
                    
                    st.caption(f"📊 {len(items_with_serial)} items have serial numbers and will be included in the PDF")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📥 Generate 4x6 Labels - {doc}", key=f"pdf_{doc}"):
                            with st.spinner(f"Generating {len(items_with_serial)} labels..."):
                                pdf_buffer = generate_barcode_pdf(doc_data, doc)
                                st.download_button(
                                    label="Download PDF (4x6)",
                                    data=pdf_buffer.getvalue(),
                                    file_name=f"labels_{doc}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                    mime="application/pdf",
                                    key=f"download_{doc}"
                                )
                    with col2:
                        if st.button(f"📋 Copy Serials - {doc}", key=f"copy_{doc}"):
                            serials = doc_data['Expected_Serial'].dropna().tolist()
                            serials_text = '\n'.join([str(s) for s in serials if s != ''])
                            st.code(serials_text, language="text")
                            st.info(f"✅ Copied {len(serials)} serial numbers to clipboard!")
        
        # Export options
        st.subheader("📥 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export to Excel"):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    display_df.to_excel(writer, index=False, sheet_name='Pending_Lines')
                excel_data = output.getvalue()
                st.download_button(
                    label="Click to Download Excel",
                    data=excel_data,
                    file_name=f"pending_lines_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if selected_docs and st.button("📄 Generate All 4x6 Labels"):
                import zipfile
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for doc in selected_docs:
                        doc_data = df[df['Document'] == doc]
                        pdf_buffer = generate_barcode_pdf(doc_data, doc)
                        zip_file.writestr(f"labels_{doc}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", pdf_buffer.getvalue())
                
                zip_buffer.seek(0)
                st.download_button(
                    label="📥 Download All Labels (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"all_labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
    
    elif st.session_state.df is not None and st.session_state.df.empty:
        st.warning("No data found. Please adjust your filters.")
    else:
        st.info("👈 Use the sidebar filters and click 'Load Data' to fetch records from the API")

if __name__ == "__main__":
    main()
