import os
import streamlit as st
import httpx

st.set_page_config(page_title="SLRPD", layout="wide")
st.title("SLRPD Governed Agent — Streamlit")

base = os.getenv("SLRPD_API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
base = st.text_input("SLRPD_API_BASE_URL", value=base).rstrip("/")

if st.button("Test API (/openapi.json)"):
    r = httpx.get(f"{base}/openapi.json", timeout=10)
    st.write("HTTP:", r.status_code)
    st.json(r.json())
