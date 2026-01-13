# 🚀 SNF FX Engine (Finance OCR App)

**Financial Intelligence System v2.0**

A powerful Streamlit application designed to streamline financial tracking by leveraging AI for Optical Character Recognition (OCR). This tool automates the extraction of transaction details from USD invoices and NPR payment slips, allowing for seamless financial management and analysis.

## 🌟 Features

- **🤖 AI-Powered OCR**: Uses Google's **Gemini Flash** model to intelligently extract transaction data from images.
  - **USD Invoices**: Extracts Date, Vendor Name, Amount (USD), and Remarks.
  - **NPR Payment Slips**: Extracts Date, Recipient, Amount (NPR), Payment Mode, and Remarks.
- **📄 Multi-Transaction Support**: Capable of detecting and extracting multiple transactions from a single uploaded image.
- **📝 Manual Entry**: specific form for manually logging transactions that don't have digital receipts.
- **📊 Interactive Dashboard**:
  - **Key Metrics**: Real-time view of Total USD Purchased, Total NPR Paid, and Net Imbalance.
  - **Visualizations**: Bar charts showing daily transaction trends.
  - **Data Table**: Sortable and filterable view of recent transactions.
- **💾 Data Persistence & Export**: Automatically saves all records to a local CSV database (`antigravity_database.csv`) and offers one-click CSV export.

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) (with custom CSS for a modern UI)
- **AI/ML**: [Google Generative AI (Gemini)](https://ai.google.dev/)
- **Data Processing**: Pandas
- **Image Processing**: Pillow (PIL)

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- A Google Cloud API Key with access to Gemini models.

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/raaj23man/Finance-OCR-App.git
   cd Finance-OCR-App
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   You need to provide your Google API Key for the AI features to work.
   
   **Option A: Local `secrets.toml` (Recommended for local dev)**
   Create a file at `.streamlit/secrets.toml`:
   ```toml
   GOOGLE_API_KEY = "your_actual_api_key_here"
   ```

   **Option B: Environment Variable**
   Set the `GOOGLE_API_KEY` environment variable in your system.

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```

## 📖 Usage Guide

1. **🇺🇸 USD Purchase Tab**: 
   - Upload an image of a USD invoice.
   - Click "Extract Invoice Data".
   - Review the extracted fields, add the Exchange Rate (ROE), and click "Save".

2. **🇳🇵 NPR Payment Tab**:
   - Upload an image of a bank deposit slip or check.
   - Click "Extract Payment Data".
   - Verify the details and click "Save".

3. **📝 Manual Entry Tab**:
   - Use this for transactions without images or to make corrections.
   - Select the source type and fill in the financial details.

4. **📊 Data & Exports Tab**:
   - View your financial summary.
   - Analyze trends with the built-in charts.
   - Download the full ledger as a CSV file for external use.

## 📂 Project Structure

- `app.py`: Main application logic and Streamlit UI.
- `requirements.txt`: Python dependencies.
- `antigravity_database.csv`: Local storage for transaction records (auto-generated).
- `models.txt`: Reference for models used.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/raaj23man/Finance-OCR-App/issues).

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).
