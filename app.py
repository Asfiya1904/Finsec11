
import streamlit as st
import pandas as pd
import numpy as np
import requests
import os

st.set_page_config(page_title="FinSec Enterprise", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    body, .stApp { background-color: #0e1117; color: #fafafa; }
    .css-1v3fvcr, .css-1dp5vir, .css-ffhzg2, .st-c1, .st-bb, .st-at, .css-18e3th9 {
        background-color: #1c1f26 !important;
        color: #fafafa !important;
    }
    .css-1aumxhk {
        padding: 1rem; border-radius: 10px;
        background-color: #1c1f26;
        border: 1px solid #282c34;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True
)

st.sidebar.image("finsec_logo.png", width=220)

if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "role": None, "email": ""}

if not st.session_state.auth["logged_in"]:
    st.title("🔐 FinSec Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Login as", ["Admin", "Financial Client"])
        email = st.text_input("Email (for alerts)")
        submit = st.form_submit_button("Login")
        if submit and username and password:
            st.session_state.auth = {"logged_in": True, "role": role, "email": email}
            st.success("✅ Logged in successfully")
            st.experimental_rerun()
        elif submit:
            st.error("Please enter all fields")
    st.stop()

st.sidebar.title("FinSec Navigation")
nav = st.sidebar.radio("Go to", ["📊 Dashboard", "📥 Upload & Analyze", "🛑 Alerts", "📁 Reports", "⚙️ Settings", "🚪 Logout"])
st.sidebar.write(f"🔓 Logged in as: {st.session_state.auth['role']}")

if nav == "🚪 Logout":
    st.session_state.auth = {"logged_in": False, "role": None, "email": ""}
    st.success("You have been logged out.")
    st.experimental_rerun()

elif nav == "📊 Dashboard":
    st.title("📊 Dashboard Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Transactions", "1240")
    col2.metric("Threats Detected", "29")
    col3.metric("API Status", "✅ Online")

elif nav == "📥 Upload & Analyze":
    st.subheader("📥 Upload and Analyze Transactions")
    api_toggle = st.toggle("Use FinSec API", value=True)
    api_url = os.getenv("FINSEC_API_URL", "https://finsec1.onrender.com/detect")
    api_key = os.getenv("FINSEC_API_KEY", "supersecret")
    uploaded_file = st.file_uploader("Upload CSV File", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Uploaded Data", df.head())
        if st.button("🚨 Run Analysis"):
            results = []
            for i, row in df.iterrows():
                record = row.to_dict()
                if api_toggle:
                    try:
                        res = requests.post(api_url, headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }, json=record, timeout=10)
                        result = res.json() if res.status_code == 200 else {"status": "API Error"}
                        record.update(result)
                    except:
                        record.update({"status": "Connection Failed"})
                else:
                    score = np.abs(row.select_dtypes(include=np.number)).sum()
                    severity = "Low" if score < 100 else "Medium" if score < 200 else "High"
                    record.update({
                        "risk_score": round(score, 2),
                        "severity": severity,
                        "status": "Suspicious" if severity != "Low" else "Normal",
                        "recommendation": "Review" if severity == "High" else "Monitor"
                    })
                results.append(record)
            result_df = pd.DataFrame(results)
            st.session_state["last_results"] = result_df
            st.success("Analysis Complete")
            st.dataframe(result_df)
            st.download_button("📄 Download Report", result_df.to_csv(index=False), "report.csv")

elif nav == "🛑 Alerts":
    st.subheader("🛑 Detected Alerts")
    if "last_results" in st.session_state:
        alerts = st.session_state["last_results"].query("severity == 'High' or severity == 'Medium'")
        st.dataframe(alerts if not alerts.empty else pd.DataFrame(columns=["No alerts detected"]))
    else:
        st.info("Upload and analyze data first.")

elif nav == "📁 Reports":
    st.subheader("📁 Reports and Logs")
    if "last_results" in st.session_state:
        st.dataframe(st.session_state["last_results"])
        st.download_button("Download Full Log", st.session_state["last_results"].to_csv(index=False), "full_log.csv")
    else:
        st.info("No data available yet.")

elif nav == "⚙️ Settings":
    st.subheader("⚙️ App Settings")
    st.text_input("Webhook URL", placeholder="https://your.webhook.url")
    st.selectbox("Alert Sensitivity", ["Low", "Medium", "High"])
    st.toggle("Enable Email Notifications", value=True)
