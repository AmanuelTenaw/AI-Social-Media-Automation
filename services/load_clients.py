import pandas as pd
from database.supabase_client import supabase

# This file imports mock client data from Excel and uploads it to Supabase.

# Reads the spreadsheet that contains the sample client list.
df = pd.read_excel("data/mock_social_media_clients.xlsx")

# Renames the spreadsheet columns so they match the column names in Supabase.
df = df.rename(columns={
    "Client ID": "client_id",
    "Client Name": "client_name",
    "Phone Number": "phone_number",
    "Service Type": "service_type",
    "Service Specialty": "service_specialty",
    "Location": "location",
    "State": "state",
    "Posting Schedule": "posting_schedule",
    "Mock Page Name": "mock_page_name"
})

# Prints a quick preview so you can confirm the spreadsheet loaded correctly.
print(df.head())
print(df.columns)
print("Total clients:", len(df))

# Converts each spreadsheet row into a dictionary that Supabase can insert.
records = df.to_dict(orient="records")

# Uploads each client record into the Supabase "clients" table.
for record in records:
    supabase.table("clients").insert(record).execute()

print("Clients uploaded successfully.")
