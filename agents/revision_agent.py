import os
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI

from database.supabase_client import supabase

# This file revises captions that failed QA and escalates repeated failures.

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_REVISION_ATTEMPTS = 2


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


if __name__ == "__main__":
    run_revision_agent()
