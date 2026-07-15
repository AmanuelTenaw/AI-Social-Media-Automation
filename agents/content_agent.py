import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date

from agents.scheduler_agent import scheduler_agent
from database.supabase_client import supabase

# This file creates social media captions for clients who are scheduled to post today.

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_REVISION_ATTEMPTS = 2


# Builds the instructions that tell OpenAI what kind of caption to write.
def create_caption_prompt(client_profile):
    return f"""
You are a social media content writer for a marketing company.

Create ONE unique Facebook caption for the following client.

Client Information:
Business Name: {client_profile["client_name"]}
Service Type: {client_profile["service_type"]}
Specialty: {client_profile["service_specialty"]}
Location: {client_profile["location"]}, {client_profile["state"]}
Phone Number: {client_profile["phone_number"]}

Requirements:
- Match the client's service type and specialty.
- Mention the location naturally.
- Include the phone number only if it fits naturally.
- Friendly and professional tone.
- 2–4 sentences.
- End with a simple call to action.
- Do NOT use hashtags.
- Do NOT use emojis.
- Do NOT mention AI.
- Make every caption unique.
"""


def create_revision_prompt(client_profile, post):
    return f"""
You are a social media content writer for a marketing company.

The previous caption did not pass QA. Rewrite it using the QA feedback.

Client Information:
Business Name: {client_profile["client_name"]}
Service Type: {client_profile["service_type"]}
Specialty: {client_profile["service_specialty"]}
Location: {client_profile["location"]}, {client_profile["state"]}
Phone Number: {client_profile["phone_number"]}

Previous Caption:
{post["caption"]}

QA Feedback:
{post.get("qa_notes", "No QA notes provided.")}

Requirements:
- Address the QA feedback directly.
- Match the client's service type and specialty.
- Mention the location naturally.
- Include the phone number only if it fits naturally.
- Friendly and professional tone.
- 2-4 sentences.
- End with a simple call to action.
- Do NOT use hashtags.
- Do NOT use emojis.
- Do NOT mention AI.
- Return only the revised caption.
"""


# Checks Supabase to see if this client already has a post created today.
def post_already_created_today(client_id):
    today = date.today().isoformat()

    response = (
        supabase
        .table("posts")
        .select("*")
        .eq("client_id", client_id)
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )

    return len(response.data) > 0


def get_client_profile(client_id):
    response = (
        supabase
        .table("clients")
        .select("*")
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    return response.data


def get_revision_posts_for_today(max_revision_attempts=MAX_REVISION_ATTEMPTS):
    today = date.today().isoformat()

    response = (
        supabase
        .table("posts")
        .select("*")
        .eq("status", "needs_revision")
        .lt("revision_count", max_revision_attempts)
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )

    return response.data


def get_human_review_posts_for_today(max_revision_attempts=MAX_REVISION_ATTEMPTS):
    today = date.today().isoformat()

    response = (
        supabase
        .table("posts")
        .select("*")
        .eq("status", "needs_revision")
        .gte("revision_count", max_revision_attempts)
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )

    return response.data


# Sends the client information to OpenAI and returns the finished caption text.
def generate_caption(client_profile):
    prompt = create_caption_prompt(client_profile)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You create high-quality, client-specific social media captions "
                    "for local service businesses."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    return response.choices[0].message.content.strip()


def regenerate_caption(client_profile, post):
    prompt = create_revision_prompt(client_profile, post)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You revise local business social media captions based on QA feedback. "
                    "Return only the improved caption."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


# Saves the generated caption into the Supabase "posts" table as a draft post.
def save_post(client_profile, caption):

    post = {
        "client_id": client_profile["client_id"],
        "client_name": client_profile["client_name"],
        "service_type": client_profile["service_type"],
        "service_specialty": client_profile["service_specialty"],
        "location": client_profile["location"],
        "state": client_profile["state"],
        "caption": caption,
        "platform": "Facebook",
        "status": "Draft",
        "revision_count": 0
    }

    response = supabase.table("posts").insert(post).execute()

    return response.data


def save_revised_post(post, revised_caption):
    revision_count = post.get("revision_count") or 0
    next_revision_count = revision_count + 1

    response = (
        supabase
        .table("posts")
        .update({
            "caption": revised_caption,
            "status": "Draft",
            "revision_count": next_revision_count,
            "qa_notes": (
                f"Revision {next_revision_count} generated from QA feedback: "
                f"{post.get('qa_notes', 'No QA notes provided.')}"
            )
        })
        .eq("id", post["id"])
        .execute()
    )

    return response.data


def mark_posts_for_human_review(max_revision_attempts=MAX_REVISION_ATTEMPTS):
    posts = get_human_review_posts_for_today(max_revision_attempts)

    for post in posts:
        supabase.table("posts").update({
            "status": "human_review_required",
            "qa_notes": (
                f"Human review required after {max_revision_attempts} revision attempts. "
                f"Latest QA feedback: {post.get('qa_notes', 'No QA notes provided.')}"
            )
        }).eq("id", post["id"]).execute()

    return posts


# Runs the full content generation process:
# 1. Finds clients due today.
# 2. Skips clients who already have a post today.
# 3. Generates and saves new captions for the remaining clients.
def run_content_agent():
    due_clients, skipped_clients = scheduler_agent()

    posts_generated = 0
    already_created = 0

    print(f"\nGenerating captions for {len(due_clients)} clients...")
    print("-" * 60)

    for client_profile in due_clients:
        if post_already_created_today(client_profile["client_id"]):
            already_created += 1
            print(f"Skipping {client_profile['client_name']} - post already created today.")
            continue

        print(f"Generating caption for {client_profile['client_name']}...")

        caption = generate_caption(client_profile)
        save_post(client_profile, caption)

        posts_generated += 1

        print("Saved to Supabase.")
        print("-" * 60)

    print("\nContent Agent completed successfully.")
    print(f"Posts generated: {posts_generated}")
    print(f"Already created today: {already_created}")
    print(f"Clients not due today: {len(skipped_clients)}")


def run_revision_agent(max_revision_attempts=MAX_REVISION_ATTEMPTS):
    revision_posts = get_revision_posts_for_today(max_revision_attempts)
    revised_count = 0

    print(f"\nFound {len(revision_posts)} posts to revise.")
    print("-" * 60)

    for post in revision_posts:
        client_profile = get_client_profile(post["client_id"])

        print(f"Regenerating caption for {client_profile['client_name']}...")
        print(f"QA feedback: {post.get('qa_notes', 'No QA notes provided.')}")

        revised_caption = regenerate_caption(client_profile, post)
        save_revised_post(post, revised_caption)

        revised_count += 1
        print("Saved revised caption for another QA pass.")
        print("-" * 60)

    human_review_posts = mark_posts_for_human_review(max_revision_attempts)

    if human_review_posts:
        print(f"Marked {len(human_review_posts)} posts for human review.")

    print("\nRevision Agent completed successfully.")
    print(f"Posts revised: {revised_count}")

    return revised_count


# Runs the content agent only when this file is started directly from the terminal.
if __name__ == "__main__":
    run_content_agent()
