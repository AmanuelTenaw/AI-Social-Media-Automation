from datetime import date, datetime

from agents.scheduler_agent import scheduler_agent
from database.supabase_client import supabase

# This file simulates publishing approved posts and prints a daily stakeholder report.


# Gets posts created today that passed QA and are ready to publish.
def get_approved_posts_for_today():
    today = date.today().isoformat()

    response = (
        supabase
        .table("posts")
        .select("*")
        .eq("status", "approved")
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )

    return response.data


# Gets posts that failed QA today so the report can explain what needs attention.
def get_failed_qa_posts_for_today():
    today = date.today().isoformat()

    response = (
        supabase
        .table("posts")
        .select("*")
        .eq("status", "needs_revision")
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )

    return response.data


def get_human_review_posts_for_today():
    today = date.today().isoformat()

    response = (
        supabase
        .table("posts")
        .select("*")
        .eq("status", "human_review_required")
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )

    return response.data


# Gets all posts created today, no matter their current status.
def get_all_posts_created_today():
    today = date.today().isoformat()

    response = (
        supabase
        .table("posts")
        .select("*")
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )

    return response.data


# Gets all mock published posts from today.
def get_published_posts_for_today():
    today = date.today().isoformat()

    response = (
        supabase
        .table("published_posts")
        .select("*")
        .gte("published_at", f"{today}T00:00:00")
        .execute()
    )

    return response.data


# Checks whether the post already has a mock publishing record.
def post_already_published(post_id):
    response = (
        supabase
        .table("published_posts")
        .select("id")
        .eq("post_id", post_id)
        .execute()
    )

    return len(response.data) > 0


# Looks up the client profile so the agent knows the mock page name.
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


# Saves the mock publishing event in the published_posts table.
def save_published_post(post, client_profile, published_at):
    published_post = {
        "post_id": post["id"],
        "client_id": post["client_id"],
        "client_name": post["client_name"],
        "mock_page_name": client_profile.get("mock_page_name", "Mock Social Media Page"),
        "platform": post.get("platform", "Facebook"),
        "caption": post["caption"],
        "publish_status": "published",
        "publish_notes": "Published to mock social media page.",
        "published_at": published_at
    }

    response = supabase.table("published_posts").insert(published_post).execute()
    return response.data


# Simulates publishing by creating a publish history record.
def publish_post(post, client_profile):
    published_at = datetime.now().isoformat(timespec="seconds")
    mock_page_name = client_profile.get("mock_page_name", "Mock Social Media Page")

    if post_already_published(post["id"]):
        return {
            "post_id": post["id"],
            "client_id": post["client_id"],
            "client_name": post["client_name"],
            "mock_page_name": mock_page_name,
            "caption": post["caption"],
            "publish_status": "already_published",
            "publish_notes": "This post already exists in the published_posts table.",
            "published_at": published_at
        }

    save_published_post(post, client_profile, published_at)

    return {
        "post_id": post["id"],
        "client_id": post["client_id"],
        "client_name": post["client_name"],
        "mock_page_name": mock_page_name,
        "caption": post["caption"],
        "publish_status": "published",
        "publish_notes": "Published to mock social media page.",
        "published_at": published_at
    }


# Publishes every approved post that was created today.
def publish_approved_posts():
    approved_posts = get_approved_posts_for_today()
    published_posts = []
    failures = []

    for post in approved_posts:
        try:
            client_profile = get_client_profile(post["client_id"])
            published_post = publish_post(post, client_profile)
            published_posts.append(published_post)
        except Exception as error:
            failures.append({
                "post_id": post.get("id"),
                "client_id": post.get("client_id"),
                "client_name": post.get("client_name"),
                "reason": str(error)
            })

    return published_posts, failures


# Builds a plain-English summary for managers and stakeholders.
def build_daily_report(published_posts, publishing_failures):
    due_clients, skipped_clients = scheduler_agent()
    posts_created_today = get_all_posts_created_today()
    published_posts_today = get_published_posts_for_today()
    failed_qa_posts = get_failed_qa_posts_for_today()
    human_review_posts = get_human_review_posts_for_today()

    report = {
        "report_date": date.today().isoformat(),
        "clients_due_today": len(due_clients),
        "clients_skipped_today": len(skipped_clients),
        "posts_created_today": len(posts_created_today),
        "posts_published_this_run": len(published_posts),
        "posts_published_today": len(published_posts_today),
        "posts_needing_revision": len(failed_qa_posts),
        "posts_needing_human_review": len(human_review_posts),
        "publishing_failures": len(publishing_failures),
        "published_posts": published_posts,
        "published_posts_today": published_posts_today,
        "failed_qa_posts": failed_qa_posts,
        "human_review_posts": human_review_posts,
        "skipped_clients": skipped_clients,
        "failures": publishing_failures
    }

    return report


def create_manager_summary(report):
    """Returns a short, plain-English overview of the daily results."""
    clients_due = report["clients_due_today"]
    posts_published = report["posts_published_today"]
    posts_needing_revision = report["posts_needing_revision"]
    posts_needing_review = report["posts_needing_human_review"]

    summary = (
        f"Today, {clients_due} {'client was' if clients_due == 1 else 'clients were'} scheduled to post. "
        f"{posts_published} {'post was' if posts_published == 1 else 'posts were'} published. "
        f"{posts_needing_revision} {'post needs' if posts_needing_revision == 1 else 'posts need'} "
        f"another automatic revision, and {posts_needing_review} "
        f"{'post needs' if posts_needing_review == 1 else 'posts need'} a human review."
    )

    if "publishing_failures" in report:
        if report["publishing_failures"]:
            failures = report["publishing_failures"]
            summary += f" {failures} {'post' if failures == 1 else 'posts'} failed to publish."
        else:
            summary += " There were no publishing failures."

    return summary


# Prints the daily report in a format a non-technical stakeholder can understand.
def print_daily_report(report):
    print("\nDaily Publish and Report Summary")
    print("=" * 60)
    print(create_manager_summary(report))
    print("-" * 60)
    print(f"Report date: {report['report_date']}")
    print(f"Clients due today: {report['clients_due_today']}")
    print(f"Clients skipped today: {report['clients_skipped_today']}")
    print(f"Posts created today: {report['posts_created_today']}")
    print(f"Posts published this run: {report['posts_published_this_run']}")
    print(f"Total posts published today: {report['posts_published_today']}")
    print(f"Posts needing revision: {report['posts_needing_revision']}")
    print(f"Posts needing human review: {report['posts_needing_human_review']}")
    print(f"Publishing failures: {report['publishing_failures']}")

    print("\nPublished posts")
    print("-" * 60)
    if report["published_posts"]:
        for post in report["published_posts"]:
            print(f"{post['client_name']} -> {post['mock_page_name']}")
            print(f"Published at: {post['published_at']}")
            print(f"Caption: {post['caption']}")
            print("-" * 60)
    else:
        print("No approved posts were available to publish today.")

    print("\nPosts needing revision")
    print("-" * 60)
    if report["failed_qa_posts"]:
        for post in report["failed_qa_posts"]:
            print(f"{post['client_name']} needs revision.")
            print(f"Revision attempts: {post.get('revision_count', 0)}")
            print(f"QA notes: {post.get('qa_notes', 'No QA notes provided.')}")
            print("-" * 60)
    else:
        print("No posts failed QA today.")

    print("\nPosts needing human review")
    print("-" * 60)
    if report["human_review_posts"]:
        for post in report["human_review_posts"]:
            print(f"{post['client_name']} needs human review.")
            print(f"Revision attempts: {post.get('revision_count', 0)}")
            print(f"QA notes: {post.get('qa_notes', 'No QA notes provided.')}")
            print(f"Caption: {post.get('caption', 'No caption saved.')}")
            print("-" * 60)
    else:
        print("No posts require human review today.")

    print("\nSkipped clients")
    print("-" * 60)
    if report["skipped_clients"]:
        for client in report["skipped_clients"]:
            print(f"{client['client_name']} - {client['reason']}")
    else:
        print("No clients were skipped today.")

    print("\nFailures")
    print("-" * 60)
    if report["failures"]:
        for failure in report["failures"]:
            print(f"{failure['client_name']} failed to publish: {failure['reason']}")
    else:
        print("No publishing failures were recorded.")


# Runs the full publish and report process.
def run_publish_report_agent():
    print("\nStarting Publish and Report Agent...")
    print("=" * 60)

    published_posts, publishing_failures = publish_approved_posts()
    report = build_daily_report(published_posts, publishing_failures)
    print_daily_report(report)

    print("\nPublish and Report Agent completed successfully.")
    return report


# Runs this agent only when this file is started directly from the terminal.
if __name__ == "__main__":
    run_publish_report_agent()
