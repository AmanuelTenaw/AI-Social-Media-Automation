from datetime import date
from database.supabase_client import supabase

# This file decides which clients should get social media posts today.

# Gets all client records from the Supabase "clients" table.
def get_clients():
    response = supabase.table("clients").select("*").execute()
    return response.data


# Checks one client's posting schedule and returns True if they should post today.
def is_due_today(client, today):
    schedule = client["posting_schedule"]

    # Daily clients post every day
    if schedule == "Daily":
        return True

    # Twice-per-week clients post on Monday and Thursday
    # weekday(): Monday = 0, Thursday = 3
    if schedule == "Twice per week":
        return today.weekday() in [0, 3]

    # Once-per-week clients post on Wednesday
    # weekday(): Wednesday = 2
    if schedule == "Once per week":
        return today.weekday() == 2

    # If the schedule is unknown, do not post
    return False


# Separates clients into two groups:
# 1. due_clients: clients who need content today
# 2. skipped_clients: clients who are not scheduled today
def scheduler_agent():
    today = date.today()
    clients = get_clients()

    due_clients = []
    skipped_clients = []

    for client in clients:
        if is_due_today(client, today):
            due_clients.append(client)
        else:
            skipped_clients.append({
                "client_id": client["client_id"],
                "client_name": client["client_name"],
                "posting_schedule": client["posting_schedule"],
                "reason": f"Not due today. Schedule is {client['posting_schedule']}."
            })

    return due_clients, skipped_clients


# Runs the scheduler and prints the results in the terminal.
def run_scheduler():
    due_clients, skipped_clients = scheduler_agent()

    print(f"Clients due today: {len(due_clients)}")
    print("-" * 50)

    for client in due_clients:
        print(f"{client['client_id']} - {client['client_name']} - {client['posting_schedule']}")

    print("\nSkipped clients:")
    print("-" * 50)

    for client in skipped_clients:
        print(f"{client['client_id']} - {client['client_name']} - {client['reason']}")


# Runs the scheduler only when this file is started directly from the terminal.
# Example: python -m agents.scheduler_agent
if __name__ == "__main__":
    run_scheduler()
