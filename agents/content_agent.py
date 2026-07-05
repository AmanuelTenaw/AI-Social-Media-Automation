import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date

from agents.scheduler_agent import scheduler_agent
from database.supabase_client import supabase

# This file creates social media captions for clients who are scheduled to post today.

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
        "status": "Draft"
    }

    response = supabase.table("posts").insert(post).execute()

    return response.data


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


# Runs the content agent only when this file is started directly from the terminal.
if __name__ == "__main__":
    run_content_agent()
