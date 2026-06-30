import pandas as pd
from database.supabase_client import supabase

df = pd.read_excel("data/mock_social_media_clients.xlsx")
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

print(df.head())
print(df.columns)
print("Total clients:", len(df))

records = df.to_dict(orient="records")

for record in records:
    supabase.table("clients").insert(record).execute()

print("Clients uploaded successfully.")