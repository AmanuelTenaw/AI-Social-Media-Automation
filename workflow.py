from agents.scheduler_agent import run_scheduler
from agents.content_agent import run_content_agent
from agents.qa_agent import run_qa_agent
from agents.publish_report_agent import run_publish_report_agent

# This file runs the whole daily automation process from start to finish.

# Runs each agent in order:
# 1. Scheduler Agent decides which clients need posts today.
# 2. Content Agent writes and saves captions for those clients.
# 3. QA Agent reviews the saved captions and updates their status.
# 4. Publish Report Agent simulates publishing and prints the daily report.
def run_daily_workflow():
    print("\nStarting daily social media automation workflow...")
    print("=" * 60)

    print("\nSTEP 1: Scheduler Agent")
    run_scheduler()

    print("\nSTEP 2: Content Generator Agent")
    run_content_agent()

    print("\nSTEP 3: QA Agent")
    run_qa_agent()

    print("\nSTEP 4: Publish Report Agent")
    run_publish_report_agent()

    print("\nDaily workflow completed successfully.")


# Starts the daily workflow only when this file is run directly.
if __name__ == "__main__":
    run_daily_workflow()
