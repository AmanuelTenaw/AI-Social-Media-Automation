# AI Social Media Automation

## Summary

AI Social Media Automation is a multi-agent Python application that creates, reviews, revises, and mock-publishes Facebook captions for local service businesses. Client profiles, captions, QA results, revision history, and publishing records are stored in Supabase. A Streamlit dashboard presents daily results and posts that require human review to stakeholders.

## Problem

Marketing teams that manage many local business accounts repeatedly perform the same tasks:

- Determine which clients are scheduled to post.
- Write captions that match each client's services and location.
- Review captions for accuracy, tone, and relevance.
- Rewrite captions that do not meet quality standards.
- Track publishing activity and communicate results to stakeholders.

Completing this process manually takes time, introduces inconsistent quality, and becomes difficult to monitor as the number of clients grows.

## Solution

This project organizes the work into specialized agents coordinated by a daily workflow:

1. **Scheduler Agent** selects clients scheduled to post today.
2. **Content Generator Agent** uses OpenAI to create a client-specific Facebook caption.
3. **QA Agent** uses OpenAI to approve the caption or provide actionable revision feedback.
4. **Revision Agent** rewrites failed captions and returns them to QA, allowing up to two automatic revisions.
5. **Human-review escalation** stops automatic processing when the revision limit is reached and marks the post `human_review_required`.
6. **Publish and Report Agent** mock-publishes approved posts and builds a daily report.
7. **Stakeholder Dashboard** displays client schedules, content output, publishing history, and the human-review queue.

Only posts with an `approved` status are eligible for mock publishing. This prevents captions awaiting revision or human review from being published.

> This project simulates social media publishing by writing records to the Supabase `published_posts` table. It does not publish to a live Facebook account.

## Tech Stack

- **Python 3.12** - application and workflow logic
- **OpenAI API (`gpt-4o-mini`)** - caption generation, QA, and revision
- **Supabase** - client, post, and mock-publishing data storage
- **Streamlit** - stakeholder dashboard
- **Pandas** - dashboard data preparation
- **OpenPyXL** - importing mock client data from Excel
- **python-dotenv** - local environment-variable management

## Agent Architecture

| Component | Type | Responsibility |
| --- | --- | --- |
| Scheduler Agent | Rule-based | Selects clients according to their posting schedules |
| Content Generator Agent | AI-powered | Creates the initial caption |
| QA Agent | AI-powered | Reviews captions and provides feedback |
| Revision Agent | AI-powered | Rewrites captions using QA feedback |
| Publish and Report Agent | Rule-based | Mock-publishes approved posts and generates reports |

## Project Structure

```text
AI-Social-Media-Automation/
├── agents/
│   ├── content_agent.py
│   ├── publish_report_agent.py
│   ├── qa_agent.py
│   ├── revision_agent.py
│   └── scheduler_agent.py
├── data/
│   └── mock_social_media_clients.xlsx
├── database/
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   └── supabase_client.py
├── services/
│   └── load_clients.py
├── .env.example
├── README.md
├── app.py
├── workflow.py
├── requirements.txt
└── runtime.txt
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment-variable example:

   ```bash
   cp .env.example .env
   ```

   Then replace the placeholders in `.env` with your OpenAI and Supabase
   credentials:

   ```env
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

4. Create a Supabase project, open its **SQL Editor**, copy the contents of
   `database/migrations/001_initial_schema.sql`, and run the SQL. The migration
   creates the required tables, relationships, constraints, and indexes:

   - `clients`
   - `posts`
   - `published_posts`

   The migration is designed for this mock-data demo, which accesses Supabase
   with the anonymous key and no user sign-in. It therefore disables Row Level
   Security on these three tables. Do not use this access model for real client
   data. A production deployment should enable RLS and define authenticated,
   least-privilege policies.

5. Load the sample client spreadsheet into an empty `clients` table:

   ```bash
   python -m services.load_clients
   ```

   The loader uses `data/mock_social_media_clients.xlsx`. Run it once for a new
   database; `client_id` is a primary key, so loading the same rows again will
   produce duplicate-key errors.

## Running the Project

Run the complete daily workflow:

```bash
python workflow.py
```

Start the stakeholder dashboard:

```bash
streamlit run app.py
```

Run an individual agent:

```bash
python -m agents.scheduler_agent
python -m agents.content_agent
python -m agents.qa_agent
python -m agents.revision_agent
python -m agents.publish_report_agent
```

## Human Review

If a caption still fails QA after two automatic revisions, the Revision Agent changes its status to `human_review_required`. The dashboard displays the client, caption, latest QA feedback, and revision count. Because the publishing process selects only approved posts, the escalated caption remains blocked until a human reviews it.
