import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import os
from datetime import datetime
from PIL import Image

# ==========================================
# CONFIGURATION
# ==========================================
# REPLACE WITH YOUR ACTUAL KEY
# For production, use st.secrets["GOOGLE_API_KEY"]
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    st.error("Secrets file not found. Please create .streamlit/secrets.toml")
    st.stop()
except KeyError:
    st.error("GOOGLE_API_KEY not found in secrets.")
    st.stop() 

# Model Configuration
# We use the latest stable Pro model. 
# When "Gemini 3" is released, simply update this string to 'gemini-3.0-pro'
MODEL_NAME = 'gemini-1.5-pro' 

genai.configure(api_key=GOOGLE_API_KEY)

DATA_FILE = "antigravity_database.csv"

# ==========================================
# AI PROCESSING (STRUCTURED MODE)
# ==========================================
def analyze_image(image, transaction_type):
    """
    Sends image to Gemini with enforced JSON output mode.
    This guarantees the app never crashes due to markdown formatting.
    """
    # Configuration for JSON enforcement
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json"
    )

    model = genai.GenerativeModel(MODEL_NAME, generation_config=generation_config)
    
    prompt = f"""
    You are an autonomous financial data extractor.
    Analyze this image of a {transaction_type}.
    
    Extract the following fields accurately:
    1. transaction_date: Format YYYY-MM-DD. If year is missing, assume current year.
    2. amount: Float/Number only. Remove currency symbols or commas.
    3. currency: ISO Code (USD, NPR, INR, etc).
    4. vendor_or_recipient: The entity paid or purchasing from.
    5. category: Infer one (e.g., Software, Utility, Office, Salary, Tax, Travel).
    6. remarks: A concise summary of the transaction.

    Return the data strictly conforming to this JSON structure.
    """
    
    try:
        response = model.generate_content([prompt, image])
        # Direct JSON parsing without string cleanup needed
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e), "raw_response": str(e)}

# ==========================================
# DATA MANAGEMENT
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "Type", "Date", "Amount", "Currency", "Party", "Category", "Remarks", "Timestamp"
        ])

def save_transaction(data_dict):
    df = load_data()
    new_row = pd.DataFrame([data_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    return df

# ==========================================
# FRONTEND (STREAMLIT UI)
# ==========================================
st.set_page_config(page_title="Antigravity", page_icon="🚀", layout="wide")

# Sidebar
with st.sidebar:
    st.header("📂 Data Export")
    if os.path.exists(DATA_FILE):
        df_export = pd.read_csv(DATA_FILE)
        st.metric("Total Records", len(df_export))
        
        # Download
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download CSV",
            data=csv,
            file_name=f"antigravity_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("No data yet.")

# Main Interface
st.title("🚀 Antigravity")
st.caption(f"Powered by {MODEL_NAME} | Zero-Touch Financial Entry")

col1, col2 = st.columns([1, 1.5])

# LEFT COLUMN: INPUT
with col1:
    st.subheader("1. Ingest Document")
    doc_type = st.selectbox("Document Type", ["USD Purchase Invoice", "Payment Slip/Receipt", "Bank Statement Screenshot"])
    uploaded_file = st.file_uploader("Drop image here...", type=['jpg', 'png', 'jpeg', 'webp'])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='Source Document', use_container_width=True)
        
        analyze_btn = st.button("⚡ Extract Data", type="primary", use_container_width=True)

# RIGHT COLUMN: REVIEW & SAVE
with col2:
    st.subheader("2. Review & Commit")
    
    if uploaded_file and 'analyze_btn' in locals() and analyze_btn:
        with st.spinner('Gemini is extracting structured data...'):
            extracted_data = analyze_image(image, doc_type)
            
            if "error" in extracted_data:
                st.error(f"Extraction Failed: {extracted_data['error']}")
            else:
                # Store in session state to persist during editing
                st.session_state['current_data'] = extracted_data
                st.session_state['data_ready'] = True

    # If data is ready, show the form
    if st.session_state.get('data_ready'):
        data = st.session_state['current_data']
        
        # EDITABLE FORM (The "Pro" feature)
        with st.form("data_review"):
            c1, c2, c3 = st.columns(3)
            date_val = c1.text_input("Date (YYYY-MM-DD)", value=data.get("transaction_date"))
            amount_val = c2.number_input("Amount", value=float(data.get("amount", 0.0)))
            curr_val = c3.text_input("Currency", value=data.get("currency", "USD"))
            
            c4, c5 = st.columns(2)
            party_val = c4.text_input("Vendor/Party", value=data.get("vendor_or_recipient"))
            cat_val = c5.text_input("Category", value=data.get("category", "General"))
            
            rem_val = st.text_area("Remarks", value=data.get("remarks"))
            
            submitted = st.form_submit_button("✅ Verify & Save to Database")
            
            if submitted:
                final_record = {
                    "Type": doc_type,
                    "Date": date_val,
                    "Amount": amount_val,
                    "Currency": curr_val,
                    "Party": party_val,
                    "Category": cat_val,
                    "Remarks": rem_val,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_transaction(final_record)
                st.success("Transaction Recorded!")
                # Optional: Clear state to reset
                del st.session_state['data_ready']
                st.rerun()

# BOTTOM: HISTORY
st.divider()
st.subheader("History (Last 5 Entries)")
if os.path.exists(DATA_FILE):
    st.dataframe(pd.read_csv(DATA_FILE).sort_index(ascending=False).head(5), use_container_width=True)
