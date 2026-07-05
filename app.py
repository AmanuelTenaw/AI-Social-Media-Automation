import streamlit as st
import pandas as pd
from datetime import date
from agents.scheduler_agent import scheduler_agent
from database.supabase_client import supabase

# This file builds the Streamlit dashboard that shows clients, posts, and QA results.

# Sets the browser tab title and makes the dashboard use the full page width.
st.set_page_config(page_title="AI Social Media Automation", layout="wide")

st.title("AI Social Media Automation Dashboard")

# Loads all clients, generated posts, and published post history from Supabase.
clients_response = supabase.table("clients").select("*").execute()
posts_response = supabase.table("posts").select("*").execute()

try:
    published_posts_response = supabase.table("published_posts").select("*").execute()
    published_posts_error = None
except Exception as error:
    published_posts_response = None
    published_posts_error = error

# Converts the Supabase data into pandas DataFrames so Streamlit can display it easily.
clients = pd.DataFrame(clients_response.data)
posts = pd.DataFrame(posts_response.data)
published_posts = pd.DataFrame(published_posts_response.data) if published_posts_response else pd.DataFrame()

if not posts.empty:
    posts["created_at_date"] = pd.to_datetime(posts["created_at"]).dt.date
    today_posts = posts[posts["created_at_date"] == date.today()]
    qa_posts = today_posts[today_posts["status"] == "approved"]
else:
    qa_posts = pd.DataFrame()
    today_posts = pd.DataFrame()

if not published_posts.empty:
    published_posts["published_at_date"] = pd.to_datetime(published_posts["published_at"]).dt.date
    today_published_posts = published_posts[published_posts["published_at_date"] == date.today()]
else:
    today_published_posts = pd.DataFrame()

due_clients, skipped_clients = scheduler_agent()

st.header("Daily Stakeholder Report")

report_col1, report_col2, report_col3, report_col4, report_col5 = st.columns(5)

report_col1.metric("Total Clients", len(clients))
report_col2.metric("Clients Due Today", len(due_clients))
report_col3.metric("Clients Skipped Today", len(skipped_clients))
report_col4.metric("Posts Created Today", len(today_posts))
report_col5.metric("Published Today", len(today_published_posts))

report_col6, report_col7, report_col8 = st.columns(3)

report_col6.metric("Approved Waiting to Publish", len(today_posts[today_posts["status"] == "approved"]) if not today_posts.empty else 0)
report_col7.metric("Needs Revision", len(today_posts[today_posts["status"] == "needs_revision"]) if not today_posts.empty else 0)
report_col8.metric("Drafts Waiting for QA", len(today_posts[today_posts["status"] == "Draft"]) if not today_posts.empty else 0)

if not today_posts.empty and "qa_notes" in today_posts.columns:
    revision_posts = today_posts[today_posts["status"] == "needs_revision"]

    if not revision_posts.empty:
        st.subheader("Posts Needing Attention")
        st.dataframe(
            revision_posts[["client_id", "client_name", "caption", "qa_notes"]],
            use_container_width=True
        )

st.divider()

st.header("Scheduler Agent Output")

# Shows the full client list and each client's posting schedule.
if not clients.empty:
    st.subheader("All Clients")
    st.dataframe(
        clients[["client_id", "client_name", "service_type", "posting_schedule", "location", "state"]],
        use_container_width=True
    )
else:
    st.info("No clients found.")

st.divider()

st.header("Content Generator Output")

# Shows only captions generated today.
if not today_posts.empty:
    st.dataframe(
        today_posts[["client_id", "client_name", "service_type", "caption", "platform", "status", "created_at"]],
        use_container_width=True
    )
else:
    st.info("No captions were generated today.")

st.divider()

st.header("QA Agent Output")

# Shows posts that are currently approved by QA.
if not qa_posts.empty:
    qa_cols = ["client_id", "client_name", "caption", "status"]

    if "qa_notes" in qa_posts.columns:
        qa_cols.append("qa_notes")

    st.dataframe(
        qa_posts[qa_cols],
        use_container_width=True
    )
else:
    st.info("No QA results yet.")

st.divider()

st.header("Published Posts")

# Shows mock publishing history from the published_posts Supabase table.
if published_posts_error:
    st.info("Create the published_posts table in Supabase, then run the publish report agent.")
elif not today_published_posts.empty:
    publish_cols = [
        "post_id",
        "client_id",
        "client_name",
        "mock_page_name",
        "platform",
        "caption",
        "publish_status",
        "published_at"
    ]

    visible_publish_cols = [col for col in publish_cols if col in today_published_posts.columns]

    st.dataframe(
        today_published_posts[visible_publish_cols],
        use_container_width=True
    )
else:
    st.info("No posts have been published today.")

st.divider()

st.header("Skipped Clients")

# Shows skipped clients at the end of the report.
if skipped_clients:
    st.dataframe(
        pd.DataFrame(skipped_clients)[["client_id", "client_name", "posting_schedule", "reason"]],
        use_container_width=True
    )
else:
    st.info("No clients were skipped today.")
