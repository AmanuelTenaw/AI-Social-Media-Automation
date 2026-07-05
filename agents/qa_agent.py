import os
from dotenv import load_dotenv
from openai import OpenAI

from database.supabase_client import supabase

# This file reviews generated captions and marks them as approved or needing changes.

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Gets all posts that are still waiting for QA review.
def get_draft_posts():
    response = (
        supabase
        .table("posts")
        .select("*")
        .eq("status", "Draft")
        .execute()
    )
    return response.data


# Gets the client information for one post so QA can compare the caption to the client.
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


# Builds the instructions that tell OpenAI how to review one caption.
def create_qa_prompt(post, client_profile):
    return f"""
You are a QA Agent for a social media automation system.

Review the caption against the client profile.

Client Profile:
Business Name: {client_profile["client_name"]}
Service Type: {client_profile["service_type"]}
Specialty: {client_profile["service_specialty"]}
Location: {client_profile["location"]}, {client_profile["state"]}
Phone Number: {client_profile["phone_number"]}
Mock Page Name: {client_profile["mock_page_name"]}

Caption:
{post["caption"]}

Check:
- Does the caption match the correct service type?
- Does it match the specialty?
- Is it relevant to the location?
- Is the tone friendly and professional?
- Does it include a clear call to action?
- Does it avoid unrelated or made-up services?

Return only one of these exact formats:

APPROVED: short reason

or

NEEDS_REVISION: short reason
"""


# Sends the caption and client profile to OpenAI and returns the QA result.
def review_caption(post, client_profile):
    prompt = create_qa_prompt(post, client_profile)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You review social media captions for accuracy, relevance, and quality."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


# Updates the post in Supabase with its final QA status and notes.
def update_post_status(post_id, qa_result):
    if qa_result.startswith("APPROVED"):
        status = "approved"
    else:
        status = "needs_revision"

    response = (
        supabase
        .table("posts")
        .update({
            "status": status,
            "qa_notes": qa_result
        })
        .eq("id", post_id)
        .execute()
    )

    return response.data


# Runs the full QA process for every draft post.
def run_qa_agent():
    draft_posts = get_draft_posts()

    print(f"Found {len(draft_posts)} draft posts to review.")
    print("-" * 50)

    for post in draft_posts:
        client_profile = get_client_profile(post["client_id"])

        print(f"Reviewing caption for {client_profile['client_name']}...")

        qa_result = review_caption(post, client_profile)
        update_post_status(post["id"], qa_result)

        print(qa_result)
        print("-" * 50)

    print("QA Agent finished.")


# Runs the QA agent only when this file is started directly from the terminal.
if __name__ == "__main__":
    run_qa_agent()
