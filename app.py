import html

import streamlit as st
import pandas as pd
from datetime import date
from agents.scheduler_agent import scheduler_agent
from database.supabase_client import supabase

# This file builds the Streamlit dashboard that shows clients, posts, and QA results.

# Sets the browser tab title and makes the dashboard use the full page width.
st.set_page_config(page_title="AI Social Media Automation", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --cream: #f8f1e8;
            --cream-2: #fffaf3;
            --sand: #ead8c3;
            --sand-2: #d8bfa4;
            --coffee: #4a3326;
            --coffee-2: #6f4d38;
            --ink: #2f2925;
            --muted: #806b5d;
            --line: #e4d3c0;
            --success: #58734d;
            --warning: #9b6a28;
            --danger: #9a463a;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(216, 191, 164, 0.32), transparent 34rem),
                linear-gradient(180deg, var(--cream-2) 0%, var(--cream) 100%);
            color: var(--ink);
        }

        .block-container {
            padding-top: 2.4rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        h1, h2, h3 {
            color: var(--coffee);
            letter-spacing: 0;
        }

        div[data-testid="stHeader"] {
            background: rgba(255, 250, 243, 0.86);
            border-bottom: 1px solid var(--line);
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 250, 243, 0.92);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 22px rgba(74, 51, 38, 0.06);
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: 0.86rem;
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: var(--coffee);
            font-weight: 800;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 8px 22px rgba(74, 51, 38, 0.05);
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid var(--line);
            background-color: rgba(255, 250, 243, 0.95);
        }

        hr {
            border-color: var(--line);
            margin: 2rem 0;
        }

        .hero {
            background: linear-gradient(135deg, #6f4d38 0%, #a9825f 100%);
            border: 1px solid #c7a98a;
            border-radius: 8px;
            padding: 1.45rem 1.6rem;
            box-shadow: 0 14px 34px rgba(74, 51, 38, 0.16);
            margin-bottom: 1.4rem;
        }

        .hero-eyebrow {
            color: #f0dac5;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .hero-title {
            color: #fffaf3;
            font-size: 2.1rem;
            font-weight: 850;
            line-height: 1.12;
            margin: 0;
        }

        .hero-copy {
            color: #f8eadb;
            font-size: 0.98rem;
            max-width: 760px;
            margin-top: 0.6rem;
        }

        .section-kicker {
            color: var(--warning);
            font-size: 0.76rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }

        .section-title {
            color: var(--coffee);
            font-size: 1.45rem;
            font-weight: 850;
            margin: 0 0 0.75rem 0;
        }

        .status-strip {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin: 0.75rem 0 1.2rem 0;
        }

        .status-pill {
            border-radius: 999px;
            border: 1px solid var(--line);
            background: rgba(255, 250, 243, 0.9);
            color: var(--coffee);
            padding: 0.42rem 0.7rem;
            font-size: 0.84rem;
            font-weight: 750;
        }

        .status-pill.success { border-color: rgba(88, 115, 77, 0.35); color: var(--success); }
        .status-pill.warning { border-color: rgba(155, 106, 40, 0.35); color: var(--warning); }
        .status-pill.danger { border-color: rgba(154, 70, 58, 0.35); color: var(--danger); }

        .helper-text {
            color: var(--muted);
            font-size: 0.86rem;
            margin: -0.45rem 0 0.9rem 0;
        }

        .history-list {
            display: grid;
            gap: 0.72rem;
        }

        .history-row {
            background: rgba(255, 250, 243, 0.96);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.95rem 1rem;
            box-shadow: 0 8px 22px rgba(74, 51, 38, 0.05);
        }

        .history-row-top {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }

        .history-client-link {
            color: var(--coffee-2);
            font-size: 1.02rem;
            font-weight: 850;
            text-decoration: none;
        }

        .history-client-link:hover {
            text-decoration: underline;
        }

        .history-date {
            color: var(--muted);
            font-size: 0.84rem;
            white-space: nowrap;
        }

        .history-meta {
            color: var(--muted);
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }

        .caption-preview {
            color: var(--ink);
            font-size: 0.92rem;
            line-height: 1.45;
        }

        .post-shell {
            max-width: 720px;
            margin: 0 auto;
        }

        .post-card {
            background: #fffaf3;
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 18px 48px rgba(74, 51, 38, 0.12);
            overflow: hidden;
        }

        .post-topbar {
            background: #f3e5d5;
            border-bottom: 1px solid var(--line);
            color: var(--coffee);
            font-weight: 850;
            padding: 0.9rem 1rem;
        }

        .post-body {
            padding: 1.2rem;
        }

        .post-profile {
            display: flex;
            gap: 0.8rem;
            align-items: center;
            margin-bottom: 1rem;
        }

        .post-avatar {
            width: 48px;
            height: 48px;
            border-radius: 999px;
            background: linear-gradient(135deg, #7b573f, #b58f6b);
            color: #fffaf3;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 850;
            letter-spacing: 0.02em;
        }

        .post-name {
            color: var(--coffee);
            font-weight: 850;
            line-height: 1.2;
        }

        .post-date {
            color: var(--muted);
            font-size: 0.86rem;
            margin-top: 0.12rem;
        }

        .post-caption {
            color: var(--ink);
            font-size: 1.05rem;
            line-height: 1.55;
            white-space: pre-wrap;
            margin: 1rem 0;
        }

        .post-image {
            height: 220px;
            border-radius: 8px;
            border: 1px solid var(--line);
            background:
                linear-gradient(135deg, rgba(111, 77, 56, 0.92), rgba(194, 152, 113, 0.88)),
                repeating-linear-gradient(45deg, transparent 0 14px, rgba(255, 250, 243, 0.08) 14px 28px);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fffaf3;
            font-size: 1.45rem;
            font-weight: 850;
            text-align: center;
            padding: 1rem;
        }

        .post-actions {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
            border-top: 1px solid var(--line);
            padding-top: 0.9rem;
            margin-top: 1rem;
            color: var(--muted);
            font-weight: 800;
            text-align: center;
        }

        .back-link a {
            color: var(--coffee-2);
            font-weight: 850;
            text-decoration: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)


def section_header(kicker, title):
    st.markdown(
        f"""
        <div class="section-kicker">{kicker}</div>
        <div class="section-title">{title}</div>
        """,
        unsafe_allow_html=True
    )


def render_html(html_content):
    if hasattr(st, "html"):
        st.html(html_content)
    else:
        st.markdown(html_content, unsafe_allow_html=True)


def get_query_param(name):
    value = st.query_params.get(name)

    if isinstance(value, list):
        return value[0] if value else None

    return value


def format_display_datetime(value):
    if not value:
        return "Date unavailable"

    parsed_value = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed_value):
        return str(value)

    return parsed_value.strftime("%B %-d, %Y at %-I:%M %p")


def get_initials(name):
    words = [word for word in str(name).split() if word]

    if not words:
        return "AI"

    return "".join(word[0].upper() for word in words[:2])


def render_published_post_page(post):
    client_name = html.escape(str(post.get("client_name", "Client")))
    page_name = html.escape(str(post.get("mock_page_name", client_name)))
    caption = html.escape(str(post.get("caption", "No caption available.")))
    platform = html.escape(str(post.get("platform", "Facebook")))
    published_at = html.escape(format_display_datetime(post.get("published_at")))
    initials = html.escape(get_initials(page_name))

    render_html(
        f"""
<div class="post-shell">
    <div class="back-link"><a href="?">Back to dashboard</a></div>
    <br />
    <div class="post-card">
        <div class="post-topbar">{platform}-style published post preview</div>
        <div class="post-body">
            <div class="post-profile">
                <div class="post-avatar">{initials}</div>
                <div>
                    <div class="post-name">{page_name}</div>
                    <div class="post-date">{published_at}</div>
                </div>
            </div>
            <div class="post-caption">{caption}</div>
            <div class="post-image">{client_name}</div>
            <div class="post-actions">
                <div>Like</div>
                <div>Comment</div>
                <div>Share</div>
            </div>
        </div>
    </div>
</div>
"""
    )


def render_published_posts_history(posts_to_render):
    rows = []

    for _, post in posts_to_render.iterrows():
        published_row_id = post.get("id", post.get("post_id", ""))
        client_name = html.escape(str(post.get("client_name", "Client")))
        page_name = html.escape(str(post.get("mock_page_name", "")))
        platform = html.escape(str(post.get("platform", "")))
        publish_status = html.escape(str(post.get("publish_status", "")))
        published_at = html.escape(format_display_datetime(post.get("published_at")))
        caption = html.escape(str(post.get("caption", "")))

        rows.append(
            f"""
<div class="history-row">
    <div class="history-row-top">
        <a class="history-client-link" href="?published_post_id={published_row_id}">{client_name}</a>
        <div class="history-date">{published_at}</div>
    </div>
    <div class="history-meta">{page_name} · {platform} · {publish_status}</div>
    <div class="caption-preview">{caption}</div>
</div>
            """
        )

    render_html(
        f"""
<div class="history-list">
{''.join(rows)}
</div>
"""
    )

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

published_post_id = get_query_param("published_post_id")

if published_post_id and not published_posts.empty:
    detail_matches = pd.DataFrame()

    if "id" in published_posts.columns:
        detail_matches = published_posts[published_posts["id"].astype(str) == str(published_post_id)]

    if detail_matches.empty and "post_id" in published_posts.columns:
        detail_matches = published_posts[published_posts["post_id"].astype(str) == str(published_post_id)]

    if detail_matches.empty:
        st.error("Published post not found.")
    else:
        render_published_post_page(detail_matches.iloc[0].to_dict())

    st.stop()

if not today_posts.empty:
    if not today_published_posts.empty and "post_id" in today_published_posts.columns:
        published_post_ids = set(today_published_posts["post_id"])
    else:
        published_post_ids = set()

    approved_posts = today_posts[today_posts["status"] == "approved"]
    approved_waiting_posts = approved_posts[~approved_posts["id"].isin(published_post_ids)]
    revision_posts = today_posts[today_posts["status"] == "needs_revision"]
    draft_posts = today_posts[today_posts["status"] == "Draft"]
    human_review_posts = today_posts[today_posts["status"] == "human_review_required"]
    qa_reviewed_posts = today_posts[
        today_posts["status"].isin(["approved", "needs_revision", "human_review_required"])
    ]
else:
    approved_waiting_posts = pd.DataFrame()
    revision_posts = pd.DataFrame()
    draft_posts = pd.DataFrame()
    human_review_posts = pd.DataFrame()
    qa_reviewed_posts = pd.DataFrame()

due_clients, skipped_clients = scheduler_agent()

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-eyebrow">Daily operations dashboard</div>
        <h1 class="hero-title">AI Social Media Automation</h1>
        <div class="hero-copy">
            Monitoring content generation, QA decisions, publishing history, and human review queues for {date.today().isoformat()}.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

section_header("Overview", "Daily Stakeholder Report")

report_col1, report_col2, report_col3, report_col4, report_col5 = st.columns(5)

report_col1.metric("Total Clients", len(clients))
report_col2.metric("Clients Due Today", len(due_clients))
report_col3.metric("Clients Skipped Today", len(skipped_clients))
report_col4.metric("Posts Created Today", len(today_posts))
report_col5.metric("Published Today", len(today_published_posts))

report_col6, report_col7, report_col8 = st.columns(3)

report_col6.metric("Approved Not Yet Published", len(approved_waiting_posts))
report_col7.metric("Needs Revision", len(revision_posts))
report_col8.metric("Drafts Waiting for QA", len(draft_posts))

report_col9, report_col10 = st.columns(2)

report_col9.metric("Needs Human Review", len(human_review_posts))
report_col10.metric("Revision Attempts", int(today_posts["revision_count"].fillna(0).sum()) if not today_posts.empty and "revision_count" in today_posts.columns else 0)

st.markdown(
    f"""
    <div class="status-strip">
        <span class="status-pill success">{len(approved_waiting_posts)} approved and waiting</span>
        <span class="status-pill warning">{len(revision_posts)} queued for automatic revision</span>
        <span class="status-pill danger">{len(human_review_posts)} waiting on human review</span>
        <span class="status-pill">{len(today_published_posts)} published records today</span>
    </div>
    """,
    unsafe_allow_html=True
)

if not today_posts.empty and "qa_notes" in today_posts.columns:
    if not revision_posts.empty:
        section_header("Action Queue", "Posts Waiting for Automatic Revision")
        revision_cols = ["client_id", "client_name", "caption", "qa_notes"]

        if "revision_count" in revision_posts.columns:
            revision_cols.append("revision_count")

        st.dataframe(
            revision_posts[revision_cols],
            hide_index=True,
            use_container_width=True
        )

    if not human_review_posts.empty:
        section_header("Action Queue", "Posts Needing Human Review")
        human_review_cols = ["client_id", "client_name", "caption", "qa_notes"]

        if "revision_count" in human_review_posts.columns:
            human_review_cols.append("revision_count")

        st.dataframe(
            human_review_posts[human_review_cols],
            hide_index=True,
            use_container_width=True
        )

st.divider()

section_header("Scheduler", "Client Posting Schedule")

# Shows the full client list and each client's posting schedule.
if not clients.empty:
    st.dataframe(
        clients[["client_id", "client_name", "service_type", "posting_schedule", "location", "state"]],
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No clients found.")

st.divider()

section_header("Content", "Content Generator Output")

# Shows all current post records created today.
if not today_posts.empty:
    content_cols = ["client_id", "client_name", "service_type", "caption", "platform", "status", "created_at"]

    if "revision_count" in today_posts.columns:
        content_cols.append("revision_count")

    st.dataframe(
        today_posts[content_cols],
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No captions were generated today.")

st.divider()

section_header("Quality Control", "QA Agent Output")

# Shows posts that have received a QA decision today.
if not qa_reviewed_posts.empty:
    qa_cols = ["client_id", "client_name", "caption", "status"]

    if "qa_notes" in qa_reviewed_posts.columns:
        qa_cols.append("qa_notes")

    if "revision_count" in qa_reviewed_posts.columns:
        qa_cols.append("revision_count")

    st.dataframe(
        qa_reviewed_posts[qa_cols],
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No QA results yet.")

st.divider()

section_header("Publishing", "Published Posts History")
st.markdown(
    '<div class="helper-text">Click on each client name to see the published post preview.</div>',
    unsafe_allow_html=True
)

# Shows mock publishing history from the published_posts Supabase table.
if published_posts_error:
    st.info("Create the published_posts table in Supabase, then run the publish report agent.")
elif not today_published_posts.empty:
    render_published_posts_history(today_published_posts)
else:
    st.info("No posts have been published today.")

st.divider()

section_header("Scheduler", "Skipped Clients")

# Shows skipped clients at the end of the report.
if skipped_clients:
    st.dataframe(
        pd.DataFrame(skipped_clients)[["client_id", "client_name", "posting_schedule", "reason"]],
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No clients were skipped today.")
