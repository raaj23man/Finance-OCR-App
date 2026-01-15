import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import os
from datetime import datetime
from PIL import Image
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# CONFIGURATION
# ==========================================
# 1. API KEY SETUP
GOOGLE_API_KEY = None

# Attempt to load from Streamlit Secrets (Cloud) or Local .streamlit/secrets.toml
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
elif "google_api_key" in st.secrets:
    GOOGLE_API_KEY = st.secrets["google_api_key"]
# Fallback to Environment Variable (Docker/Other)
elif "GOOGLE_API_KEY" in os.environ:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

if not GOOGLE_API_KEY:
    st.error("🚨 API Key Missing!")
    st.stop()

# Configure Gemini
MODEL_NAME = 'gemini-flash-latest'
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Error configuring Google AI: {e}")

# ==========================================
# GOOGLE SHEETS SETUP
# ==========================================
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def get_db_connection():
    """
    Connects to Google Sheets using credentials from st.secrets.
    Expected structure in secrets.toml:
    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    ...
    """
    if "gcp_service_account" not in st.secrets:
        st.error("🚨 Google Cloud Credentials missing in secrets!")
        return None
    
    try:
        # Create a dictionary from the secrets object
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Failed to authorize Google Sheets: {e}")
        return None

def get_worksheet():
    client = get_db_connection()
    if not client:
        return None
    
    sheet_name = "Finance_OCR_DB" # Default Sheet Name
    if "SHEET_NAME" in st.secrets:
        sheet_name = st.secrets["SHEET_NAME"]
        
    try:
        sheet = client.open(sheet_name).sheet1
        return sheet
    except gspread.ScreenShotError: # SpreadsheetNotFound 
        st.error(f"Could not find Google Sheet named '{sheet_name}'. Please create it and share it with the service account email.")
        return None
    except Exception as e:
        st.error(f"Error accessing sheet: {e}")
        return None

# ==========================================
# AUTHENTICATION (PASSWORD PROTECTED)
# ==========================================
def check_password():
    """Returns `True` if the user had the correct password."""
    
    # If no password is set in secrets, allow open access (dev mode)
    if "APP_PASSWORD" not in st.secrets:
        return True

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Enter App Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input again.
        st.text_input(
            "Enter App Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

# ==========================================
# CUSTOM CSS & UI SETUP
# ==========================================
st.set_page_config(page_title="SNF FX Engine", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

    :root {
        --primary: #6366f1;
        --secondary: #818cf8;
        --accent: #ec4899;
        --bg-color: #0f172a;
        --card-bg: rgba(255, 255, 255, 0.95);
        --text-primary: #1e293b;
    }

    /* Animated Background */
    .stApp {
        background-color: #eef2ff;
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        background-size: 100% 100%;
        font-family: 'Inter', sans-serif;
    }
    
    /* For Light Mode clarity over dark gradients if Streamlit forces light theme */
    .stApp {
        background: radial-gradient(circle at top left, #e0e7ff, transparent 40%),
                    radial-gradient(circle at top right, #fce7f3, transparent 40%),
                    linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }

    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        color: #0f172a;
        letter-spacing: -0.02em;
    }

    h1 {
        background: linear-gradient(135deg, #4f46e5 0%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
        padding-bottom: 0.5rem;
        font-size: 3.5rem !important;
    }

    /* Centered Container Strategy - Expanded for Dashboard */
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* HIDE HEADER AND TOOLBAR */
    header[data-testid="stHeader"] {
        visibility: hidden;
        height: 0%;
    }
    
    footer {
        visibility: hidden;
    }

    #MainMenu {
        visibility: hidden;
    }

    /* Cards */
    .stForm, div[data-testid="stMetric"], .css-1r6slb0, .stDataFrame {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1), 
            0 2px 4px -1px rgba(0, 0, 0, 0.06),
            inset 0 1px 1px rgba(255, 255, 255, 0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    div[data-testid="stMetric"] {
        background: white;
    }

    /* Dashboard Specific */
    .dashboard-card {
        padding: 1.5rem; 
        background: white; 
        border-radius: 20px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(to right, #4f46e5, #8b5cf6);
        color: white;
        border: none;
        border-radius: 9999px; /* Pill shape */
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-family: 'Outfit', sans-serif;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 16px rgba(99, 102, 241, 0.4);
        color: white;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        margin-bottom: 2rem;
        gap: 1rem;
        background: rgba(255,255,255,0.5);
        padding: 0.5rem;
        border-radius: 9999px;
        display: inline-flex;
        width: auto;
        min-width: 600px; 
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        color: #64748b;
        border-radius: 9999px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        flex: 1;
        text-align: center;
    }

    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #4f46e5 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Input Fields Fix */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox [data-baseweb="select"] {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
        background-color: white !important;
        color: #1e293b !important;
    }
    
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }

    /* Ensure dropdown items are readable */
    div[data-baseweb="popover"] {
        background-color: white !important;
    }
    
    div[role="listbox"] div {
        color: #1e293b !important;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-enter {
        animation: fadeIn 0.5s ease-out forwards;
    }
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA MODEL & PERSISTENCE
# ==========================================
COLS = [
    "Date",
    "Description",
    "Source_Type",      # Invoice / Payment Slip
    "Mode_of_Payment",  # Bank Transfer, Check, Cash, etc.
    "Purchase_USD",     # Amount in USD
    "ROE",              # Rate of Exchange
    "Payment_NPR",      # Amount in NPR
    "Remarks",
    "Timestamp"
]

@st.cache_data(ttl=10)
def load_data():
    sheet = get_worksheet()
    if not sheet:
        return pd.DataFrame(columns=COLS)
    
    try:
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLS)
        return pd.DataFrame(data)
    except Exception as e:
        # If the sheet is completely empty (no headers)
        return pd.DataFrame(columns=COLS)

def save_transaction(record):
    sheet = get_worksheet()
    if not sheet:
        st.error("Cannot save to Google Sheet. Check configuration.")
        return None

    try:
        # Check if sheet is empty and add headers if needed
        if not sheet.get_all_values():
            sheet.append_row(COLS)
            
        # Ensure record values are in the correct order of COLS
        row_data = [
            str(record.get('Date', '')),
            str(record.get('Description', '')),
            str(record.get('Source_Type', '')),
            str(record.get('Mode_of_Payment', '')),
            float(record.get('Purchase_USD', 0.0)),
            float(record.get('ROE', 0.0)),
            float(record.get('Payment_NPR', 0.0)),
            str(record.get('Remarks', '')),
            str(record.get('Timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        ]
        
        sheet.append_row(row_data)
        load_data.clear() # Clear cache to show new data immediately
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheet: {e}")
        return False

def save_transactions_batch(records):
    """
    Save multiple transactions in a single API call for better speed.
    Uses append_rows() instead of multiple append_row() calls.
    """
    sheet = get_worksheet()
    if not sheet:
        st.error("Cannot save to Google Sheet. Check configuration.")
        return 0

    try:
        # Check if sheet is empty and add headers if needed
        if not sheet.get_all_values():
            sheet.append_row(COLS)
        
        rows_data = []
        for record in records:
            rows_data.append([
                str(record.get('Date', '')),
                str(record.get('Description', '')),
                str(record.get('Source_Type', '')),
                str(record.get('Mode_of_Payment', '')),
                float(record.get('Purchase_USD', 0.0)),
                float(record.get('ROE', 0.0)),
                float(record.get('Payment_NPR', 0.0)),
                str(record.get('Remarks', '')),
                str(record.get('Timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            ])
        
        if rows_data:
            sheet.append_rows(rows_data)
            load_data.clear()  # Clear cache to show new data immediately
        return len(rows_data)
    except Exception as e:
        st.error(f"Error saving batch to Google Sheet: {e}")
        return 0

# ==========================================
# AI LOGIC
# ==========================================
def analyze_gemini(image, type_context):
    """
    Structured extraction based on context.
    Returns a LIST of dictionaries.
    """
    model = genai.GenerativeModel(
        MODEL_NAME, 
        generation_config=genai.GenerationConfig(response_mime_type="application/json")
    )
    
    # Optimize Image Size for Faster Processing
    image.thumbnail((1024, 1024))

    if type_context == 'purchase_usd':
        prompt = """
        Analyze this image for USD Invoices or Purchase documents.
        There may be ONE or MULTIPLE transactions in this single image.
        For EACH transaction found, extract:
        1. date: YYYY-MM-DD
        2. vendor_name: Name of the seller
        3. amount_usd: The total amount in USD (number only)
        4. remarks: Summary of items purchased
        
        Return a JSON LIST of objects: 
        [
            { "date": "...", "vendor_name": "...", "amount_usd": 0.0, "remarks": "..." },
            ...
        ]
        """
    else:  # payment_npr
        prompt = """
        Analyze this image for NPR Payment Slips.
        There may be ONE or MULTIPLE transactions.
        For EACH transaction found, extract:
        1. date: YYYY-MM-DD
        2. recipient: Who received the money?
        3. amount_npr: Total payment in NPR (number only)
        4. payment_mode: Bank Name, Check Number, or 'Cash'
        5. remarks: Any specific notes
        
        Return a JSON LIST of objects: 
        [
            { "date": "...", "recipient": "...", "amount_npr": 0.0, "payment_mode": "...", "remarks": "..." },
            ...
        ]
        """

    try:
        response = model.generate_content([prompt, image])
        result = json.loads(response.text)
        if isinstance(result, dict):
            return [result]
        return result
    except Exception as e:
        return [{"error": str(e)}]

# ==========================================
# MAIN APP
# ==========================================

# CHECK AUTHENTICATION FIRST
if not check_password():
    st.image("https://cdn-icons-png.flaticon.com/512/3064/3064197.png", width=100)
    st.title("Admin Access Required")
    st.stop()  # Stop execution if password is wrong

st.title("🚀 SNF FX Engine")
st.markdown("<p style='text-align: center; color: #64748b; margin-top: -20px; margin-bottom: 2rem;'>Financial Intelligence System v2.0</p>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🇺🇸 USD Purchase", "🇳🇵 NPR Payment", "📝 Manual Entry", "📊 Data & Exports"])

# ==========================================
# TAB 1: USD PURCHASE
# ==========================================
with tab1:
    # Central Uploader Layout
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; border: 2px dashed #cbd5e1; border-radius: 16px; background: rgba(255,255,255,0.5);">
            <h3 style="margin:0; font-size: 1.2rem;">Upload USD Invoice</h3>
            <p style="color: #64748b; font-size: 0.9rem;">Supports multiple transactions</p>
        </div>
        """, unsafe_allow_html=True)
        usd_file = st.file_uploader("", type=['jpg', 'png', 'jpeg', 'webp'], key="u1", label_visibility="collapsed")
        
        if usd_file:
            st.image(usd_file, caption="Preview", width=None, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ Extract Invoice Data", key="b1"):
                with st.spinner("🤖 Analyzing your document..."):
                    img = Image.open(usd_file)
                    data = analyze_gemini(img, 'purchase_usd')
                    st.session_state['usd_data'] = data
                    st.session_state['active_tab'] = 'usd'

    # Extracted Data Section (Centered)
    if st.session_state.get('active_tab') == 'usd' and 'usd_data' in st.session_state:
        st.markdown("---")
        data_list = st.session_state['usd_data']
        
        if data_list and "error" in data_list[0]:
            st.error(data_list[0]["error"])
        else:
            st.markdown(f"<div class='animate-enter'><h3 style='text-align:center;'>Found {len(data_list)} Transaction(s)</h3></div>", unsafe_allow_html=True)
            
            # Use smaller centered columns for the form to keep it looking good on wide screen
            c_form = st.columns([1, 2, 1])
            with c_form[1]:
                with st.form("usd_form_multi"):
                    for idx, raw in enumerate(data_list):
                        st.markdown(f"<div style='background: white; padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem; border: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                        st.markdown(f"**Transaction #{idx+1}**")
                        c_a, c_b = st.columns(2)
                        dt = c_a.text_input("Date", raw.get('date', datetime.today().strftime('%Y-%m-%d')), key=f"usd_date_{idx}")
                        desc = c_b.text_input("Vendor", raw.get('vendor_name', ''), key=f"usd_desc_{idx}")
                        c_c, c_d = st.columns(2)
                        amt_usd = c_c.number_input("Amount ($)", value=float(raw.get('amount_usd', 0.0)), key=f"usd_amt_{idx}")
                        roe = c_d.number_input("ROE", value=0.0, help="Rate of Exchange", key=f"usd_roe_{idx}")
                        rem = st.text_area("Remarks", raw.get('remarks', ''), height=70, key=f"usd_rem_{idx}")
                        st.markdown("</div>", unsafe_allow_html=True)

                    if st.form_submit_button("✅ Save All Transactions"):
                        valid_records = []
                        for i in range(len(data_list)):
                            try:
                                valid_records.append({
                                    "Date": st.session_state[f"usd_date_{i}"], 
                                    "Description": st.session_state[f"usd_desc_{i}"], 
                                    "Source_Type": "USD Invoice",
                                    "Mode_of_Payment": "N/A", 
                                    "Purchase_USD": st.session_state[f"usd_amt_{i}"],
                                    "ROE": st.session_state[f"usd_roe_{i}"], 
                                    "Payment_NPR": 0.0, 
                                    "Remarks": st.session_state[f"usd_rem_{i}"],
                                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                            except KeyError:
                                pass
                        
                        # Filter valid records and save in batch for speed
                        final_records = [rec for rec in valid_records if rec['Purchase_USD'] > 0 or rec['Description']]
                        
                        if final_records:
                            count = save_transactions_batch(final_records)
                            if count > 0:
                                st.success(f"⚡ Saved {count} records successfully!")
                                del st.session_state['usd_data']
                                st.session_state['active_tab'] = None
                                st.rerun()

# ==========================================
# TAB 2: NPR PAYMENT
# ==========================================
with tab2:
    # Central Uploader Layout
    col_center_2 = st.columns([1, 2, 1])
    with col_center_2[1]:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; border: 2px dashed #cbd5e1; border-radius: 16px; background: rgba(255,255,255,0.5);">
            <h3 style="margin:0; font-size: 1.2rem;">Upload NPR Slip</h3>
            <p style="color: #64748b; font-size: 0.9rem;">Supports multiple transactions</p>
        </div>
        """, unsafe_allow_html=True)
        npr_file = st.file_uploader("", type=['jpg', 'png', 'jpeg', 'webp'], key="u2", label_visibility="collapsed")
        
        if npr_file:
            st.image(npr_file, caption="Preview", width=None, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ Extract Payment Data", key="b2"):
                with st.spinner("Analyzing..."):
                    img = Image.open(npr_file)
                    data = analyze_gemini(img, 'payment_npr')
                    st.session_state['npr_data'] = data
                    st.session_state['active_tab'] = 'npr'

    # Extracted Data
    if st.session_state.get('active_tab') == 'npr' and 'npr_data' in st.session_state:
        st.markdown("---")
        data_list = st.session_state['npr_data']
        
        if data_list and "error" in data_list[0]:
            st.error(data_list[0]["error"])
        else:
             st.markdown(f"<div class='animate-enter'><h3 style='text-align:center;'>Found {len(data_list)} Transaction(s)</h3></div>", unsafe_allow_html=True)
             
             c_form = st.columns([1, 2, 1])
             with c_form[1]:
                with st.form("npr_form_multi"):
                    for idx, raw in enumerate(data_list):
                        st.markdown(f"<div style='background: white; padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem; border: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                        st.markdown(f"**Transaction #{idx+1}**")
                        c_a, c_b = st.columns(2)
                        dt = c_a.text_input("Date", raw.get('date', datetime.today().strftime('%Y-%m-%d')), key=f"npr_date_{idx}")
                        recipient = c_b.text_input("Paid To", raw.get('recipient', ''), key=f"npr_rec_{idx}")
                        c_c, c_d = st.columns(2)
                        amt_npr = c_c.number_input("Amount (NPR)", value=float(raw.get('amount_npr', 0.0)), key=f"npr_amt_{idx}")
                        mode = c_d.text_input("Mode", raw.get('payment_mode', ''), key=f"npr_mode_{idx}")
                        rem = st.text_area("Remarks", raw.get('remarks', ''), height=70, key=f"npr_rem_{idx}")
                        st.markdown("</div>", unsafe_allow_html=True)

                    if st.form_submit_button("✅ Save All NPR Payments"):
                        valid_records = []
                        for i in range(len(data_list)):
                            try:
                                valid_records.append({
                                    "Date": st.session_state[f"npr_date_{i}"], 
                                    "Description": st.session_state[f"npr_rec_{i}"], 
                                    "Source_Type": "Payment Slip",
                                    "Mode_of_Payment": st.session_state[f"npr_mode_{i}"], 
                                    "Purchase_USD": 0.0,
                                    "ROE": 0.0, 
                                    "Payment_NPR": st.session_state[f"npr_amt_{i}"], 
                                    "Remarks": st.session_state[f"npr_rem_{i}"],
                                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                            except KeyError:
                                pass

                        # Filter valid records and save in batch for speed
                        final_records = [rec for rec in valid_records if rec['Payment_NPR'] > 0 or rec['Description']]
                        
                        if final_records:
                            count = save_transactions_batch(final_records)
                            if count > 0:
                                st.success(f"⚡ Saved {count} records successfully!")
                                del st.session_state['npr_data']
                                st.session_state['active_tab'] = None
                                st.rerun()

# ==========================================
# TAB 3: MANUAL ENTRY
# ==========================================
with tab3:
    c_form = st.columns([1, 2, 1])
    with c_form[1]:
        st.markdown("<h3 style='text-align: center'>Manual Entry</h3>", unsafe_allow_html=True)
        with st.form("manual_entry"):
            c1, c2 = st.columns(2)
            dt = c1.text_input("Date (YYYY-MM-DD)", datetime.today().strftime('%Y-%m-%d'))
            src = c2.selectbox("Source Type", ["Manual Entry", "USD Invoice", "Payment Slip"])
            st.divider()
            
            desc = st.text_input("Description / Party Name")
            
            c3, c4, c5 = st.columns(3)
            usd = c3.number_input("Purchase USD", 0.0)
            roe = c4.number_input("Exchange Rate (ROE)", 0.0)
            npr = c5.number_input("Payment NPR", 0.0)
            
            st.divider()
            mode = st.text_input("Mode of Payment", placeholder="e.g. Cash, Nabil Bank 1234")
            rem = st.text_area("Remarks")
            
            if st.form_submit_button("💾 Save Record"):
                rec = {
                    "Date": dt, "Description": desc, "Source_Type": src,
                    "Mode_of_Payment": mode, "Purchase_USD": usd,
                    "ROE": roe, "Payment_NPR": npr, "Remarks": rem,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if save_transaction(rec):
                    st.success("Record Added Manually.")
                    st.rerun()

# ==========================================
# TAB 4: DATA & EXPORT
# ==========================================
with tab4:
    df = load_data()
    
    if not df.empty:
        # Calculate Balance logic
        df['Purchase_USD'] = pd.to_numeric(df['Purchase_USD'], errors='coerce').fillna(0)
        df['ROE'] = pd.to_numeric(df['ROE'], errors='coerce').fillna(0)
        df['Payment_NPR'] = pd.to_numeric(df['Payment_NPR'], errors='coerce').fillna(0)
        
        df['Calculated_Cost_NPR'] = df['Purchase_USD'] * df['ROE']
        
        # ============================================
        # FINANCIAL SUMMARY DASHBOARD
        # ============================================
        total_usd = df['Purchase_USD'].sum()
        total_npr_paid = df['Payment_NPR'].sum()
        total_calculated_cost = df['Calculated_Cost_NPR'].sum()
        net_balance = total_npr_paid - total_calculated_cost
        
        # Get latest transaction date
        if 'Date' in df.columns:
            df['DateParsed'] = pd.to_datetime(df['Date'], errors='coerce')
            latest_date = df['DateParsed'].max()
            if pd.notna(latest_date):
                latest_date_str = latest_date.strftime('%Y-%m-%d')
            else:
                latest_date_str = "N/A"
        else:
            latest_date_str = "N/A"
        
        # Count transactions by type
        invoice_count = len(df[df['Source_Type'].str.contains('Invoice|USD', case=False, na=False)])
        payment_count = len(df[df['Source_Type'].str.contains('Payment|Slip', case=False, na=False)])
        
        # Average ROE (excluding zeros)
        roe_values = df[df['ROE'] > 0]['ROE']
        avg_roe = roe_values.mean() if len(roe_values) > 0 else 0
        
        # ============================================
        # DASHBOARD HEADER WITH SUMMARY CARDS
        # ============================================
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="margin: 0; color: #1e293b;">📊 Financial Dashboard</h2>
            <p style="color: #64748b; margin-top: 0.5rem;">Complete overview of your USD purchases and NPR payments</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Row 1: Main Financial Metrics
        st.markdown("#### 💰 Financial Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 1.2rem; border-radius: 16px; color: white; text-align: center;">
                <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">💵 Total USD Purchased</p>
                <h2 style="margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: 700;">$""" + f"{total_usd:,.2f}" + """</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1.2rem; border-radius: 16px; color: white; text-align: center;">
                <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">💳 Total NPR Paid</p>
                <h2 style="margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: 700;">Rs. """ + f"{total_npr_paid:,.2f}" + """</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 1.2rem; border-radius: 16px; color: white; text-align: center;">
                <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">📐 Calculated Cost (NPR)</p>
                <h2 style="margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: 700;">Rs. """ + f"{total_calculated_cost:,.2f}" + """</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Dynamic color based on balance
            if net_balance >= 0:
                balance_gradient = "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)"
                balance_label = "✅ Receivable (Overpaid)"
                balance_icon = "📈"
            else:
                balance_gradient = "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
                balance_label = "⚠️ Payable (Due)"
                balance_icon = "📉"
            
            st.markdown(f"""
            <div style="background: {balance_gradient}; padding: 1.2rem; border-radius: 16px; color: white; text-align: center;">
                <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">{balance_icon} Net Balance</p>
                <h2 style="margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: 700;">Rs. {abs(net_balance):,.2f}</h2>
                <p style="margin: 0.3rem 0 0 0; font-size: 0.75rem; opacity: 0.85;">{balance_label}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: Secondary Stats
        st.markdown("#### 📈 Quick Stats")
        stat1, stat2, stat3, stat4 = st.columns(4)
        
        with stat1:
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
                <p style="margin: 0; color: #64748b; font-size: 0.8rem;">📄 USD Invoices</p>
                <h3 style="margin: 0.3rem 0 0 0; color: #1e293b;">{invoice_count}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with stat2:
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
                <p style="margin: 0; color: #64748b; font-size: 0.8rem;">🧾 NPR Payments</p>
                <h3 style="margin: 0.3rem 0 0 0; color: #1e293b;">{payment_count}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with stat3:
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
                <p style="margin: 0; color: #64748b; font-size: 0.8rem;">📊 Avg. ROE</p>
                <h3 style="margin: 0.3rem 0 0 0; color: #1e293b;">{avg_roe:.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with stat4:
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
                <p style="margin: 0; color: #64748b; font-size: 0.8rem;">📅 Latest Entry</p>
                <h3 style="margin: 0.3rem 0 0 0; color: #1e293b; font-size: 1rem;">{latest_date_str}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ============================================
        # CHARTS & DATA TABLE
        # ============================================
        c_chart, c_table = st.columns([1, 2])
        
        with c_chart:
            st.markdown("#### 📉 Transaction Trends")
            if 'DateParsed' in df.columns:
                try:
                    daily = df.groupby('DateParsed')[['Purchase_USD', 'Payment_NPR']].sum()
                    if not daily.empty:
                        st.bar_chart(daily)
                    else:
                        st.info("Not enough data for trend chart.")
                except:
                    st.info("Not enough data for trend chart.")
            else:
                st.info("Date column missing.")

        with c_table:
            st.markdown("#### 📋 Recent Transactions")
            
            # Prepare display dataframe
            display_df = df.copy()
            if 'Timestamp' in display_df.columns:
                display_df['Timestamp'] = pd.to_datetime(display_df['Timestamp'], errors='coerce')
            
            # Select and order columns for display
            display_cols = ['Date', 'Description', 'Source_Type', 'Purchase_USD', 'ROE', 'Payment_NPR', 'Mode_of_Payment', 'Remarks']
            display_cols = [c for c in display_cols if c in display_df.columns]
            
            st.dataframe(
                display_df[display_cols].sort_values(by="Date", ascending=False) if 'Date' in display_df.columns else display_df, 
                use_container_width=True,
                height=350,
                column_config={
                    "Purchase_USD": st.column_config.NumberColumn("USD Amount", format="$%.2f"),
                    "Payment_NPR": st.column_config.NumberColumn("NPR Amount", format="Rs. %.2f"),
                    "ROE": st.column_config.NumberColumn("Rate", format="%.2f"),
                    "Source_Type": st.column_config.TextColumn("Type"),
                    "Mode_of_Payment": st.column_config.TextColumn("Payment Mode"),
                }
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ============================================
        # EXPORT SECTION
        # ============================================
        st.markdown("#### 📥 Export Data")
        exp1, exp2 = st.columns(2)
        
        with exp1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Complete Ledger (CSV)",
                data=csv,
                file_name=f"snf_fx_ledger_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with exp2:
            # Summary report as text
            summary_report = f"""SNF FX Engine - Financial Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

FINANCIAL OVERVIEW
------------------
Total USD Purchased: ${total_usd:,.2f}
Total NPR Paid: Rs. {total_npr_paid:,.2f}
Calculated Cost (NPR): Rs. {total_calculated_cost:,.2f}
Net Balance: Rs. {net_balance:,.2f} ({'Receivable' if net_balance >= 0 else 'Payable'})

TRANSACTION STATS
-----------------
USD Invoices: {invoice_count}
NPR Payments: {payment_count}
Average ROE: {avg_roe:.2f}
Latest Entry: {latest_date_str}
"""
            st.download_button(
                "📄 Download Summary Report (TXT)",
                data=summary_report.encode('utf-8'),
                file_name=f"snf_fx_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: white; border-radius: 20px; margin: 2rem 0;">
            <h3 style="color: #64748b;">📊 No Data Yet</h3>
            <p style="color: #94a3b8;">Upload invoices or add manual entries to see your financial dashboard</p>
        </div>
        """, unsafe_allow_html=True)
