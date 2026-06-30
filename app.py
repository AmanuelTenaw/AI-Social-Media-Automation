import streamlit as st
import pandas as pd
from database.supabase_client import supabase

st.set_page_config(
    page_title="Social Media Automation Dashboard",
    layout="wide"
)

st.title("Social Media Automation Dashboard")
st.subheader("AI-Powered Content Management & Reporting")

response = supabase.table("clients").select("*").execute()
clients = response.data

df = pd.DataFrame(clients)

st.metric("Total Clients", len(df))

if not df.empty:
    st.dataframe(df)

    st.subheader("Clients by Service Type")
    st.bar_chart(df["service_type"].value_counts())
else:
    st.warning("No clients found in Supabase.")