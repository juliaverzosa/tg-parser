import streamlit as st
import re
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# ----------------------------
# Google Sheets configuration
# ----------------------------
SPREADSHEET_ID = '163qEg3eJ6cHY8RjnMeiargVhDjdzZxVJD8dy4uBYtd8'
RANGE_NAME = 'Sheet1!A2:F'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Load credentials from Streamlit Secrets
creds_info = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

# Build Google Sheets service
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# ----------------------------
# Extract data from Telegram report
# ----------------------------
def extract_teams(message):
    lines = message.strip().split('\n')
    extracted_rows = []
    date = ""

    for line in lines:
        line = line.strip()
        if line.lower().startswith("date:"):
            date_match = re.search(r'Date[:\-]?\s*(.+)', line)
            if date_match:
                date = date_match.group(1).strip()
        elif re.search(r'\d+/\d+/\d+', line):
            parts = line.rsplit(' ', 1)
            if len(parts) == 2:
                names = parts[0].split()
                counts = parts[1].split('/')
                if len(counts) == 3:
                    dispatch, delay, completion = counts
                    senior = names[0] if len(names) > 0 else ""
                    junior = names[1] if len(names) > 1 else ""
                    extracted_rows.append([senior, junior, dispatch, delay, completion, date])
    return extracted_rows

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Globe Telegram Parser", layout="wide")

globe_blue = "#EAEEF3"
st.markdown(f"""
    <style>
    .main {{
        background-color: {globe_blue};
        color: white;
    }}
    .report-box {{
        background-color: white;
        color: black;
        padding: 2rem;
        border-radius: 15px;
        max-width: 700px;
        margin: auto;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    .report-header {{
        text-align: center;
        margin-bottom: 2rem;
    }}
    textarea {{
        font-family: monospace;
        font-size: 15px;
    }}
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 6])
with col1:
    st.image("globelogo.png", width=100)
with col2:
    st.markdown("## Globe Telegram Report Parser")
    st.markdown("Submit team reports directly to Google Sheets")

# Input area
message = st.text_area("Paste the report message below", height=300)

if st.button("Submit to Google Sheets"):
    if message.strip() == "":
        st.warning("Please paste a message first.")
    else:
        try:
            extracted_rows = extract_teams(message)
            if extracted_rows:
                sheet.values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=RANGE_NAME,
                    valueInputOption="USER_ENTERED",
                    body={"values": extracted_rows}
                ).execute()
                st.success(f"Submitted {len(extracted_rows)} rows to Google Sheets!")
            else:
                st.warning("No valid team data found in the message.")
        except Exception as e:
            st.error(f"Error: {e}")
