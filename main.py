from prettytable import PrettyTable
import requests
import time
import math
import json
from discord_webhook import DiscordWebhook, DiscordEmbed

with open("settings.json", "r") as config_file:
    config = json.load(config_file)

session = requests.session()
session.cookies['.ROBLOSECURITY'] = config["Cookie"] 
token = None
def send_webhook(webhook_url, embed):
    webhook = DiscordWebhook(webhook_url, content="")
    webhook.add_embed(embed)
    embed.set_timestamp()
    response = webhook.execute()
    print("Message sent")
def _set_auth():
    global token, session
    try:
        conn = session.post("https://friends.roblox.com/v1/users/1/request-friendship")
        if conn.headers.get("x-csrf-token"):
            token = conn.headers["x-csrf-token"]
    except Exception as e:
        print("Failed to authenticate:", e)
        time.sleep(5)
        return _set_auth()

_set_auth()
headers = {
    'Content-Type': 'application/json',
    "x-csrf-token": token
}

target_id = config["Item_Id"] 

cursor = ""
buyer_counts = {}
total_sales = -1
item_name = ""
creatorid = None
creatortype = None

item_response = session.get(f"https://economy.roblox.com/v2/assets/{target_id}/details", headers=headers)
if item_response.status_code == 200:
    item_data = item_response.json()
    if item_data.get("CollectiblesItemDetails") and item_data.get("CollectiblesItemDetails").get("TotalQuantity"):
        total_quantity = item_data.get("CollectiblesItemDetails").get("TotalQuantity", 0)
        remaining = item_data.get("Remaining", 0)
        total_sales = math.ceil(int(total_quantity)-int(remaining))
        item_name = item_data.get("Name")
        if item_data.get("Creator"):
            creatortype = item_data.get("Creator").get("CreatorType")
            creatorid = item_data.get("Creator").get("CreatorTargetId")
sales_found = 0
try:
    if creatortype == "Group":
        while total_sales != sales_found:
            response = session.get(f"https://economy.roblox.com/v2/groups/{str(creatorid)}/transactions?cursor={cursor}&limit=100&transactionType=Sale", headers=headers)
            if response.status_code == 200:
                data = response.json()
                transactions = data["data"]

                for entry in transactions:
                    if entry.get("details", {}).get("id") == target_id:
                        sales_found += 1
                        buyer_name = entry["agent"]["name"] + " (" + str(entry["agent"]["id"]) + ")"
                        if buyer_name in buyer_counts:
                            buyer_counts[buyer_name] += 1
                        else:
                            buyer_counts[buyer_name] = 1
                if data.get("nextPageCursor"):
                    cursor = data["nextPageCursor"]
                    print(cursor)
                else:
                    break
            else:
                print("Failed to fetch transactions:", response.status_code)
                break
    elif creatortype == "User":
        while total_sales != sales_found:
            response = session.get(f"https://economy.roblox.com/v2/users/{str(creatorid)}/transactions?cursor={cursor}&limit=100&transactionType=Sale", headers=headers)
            if response.status_code == 200:
                data = response.json()
                transactions = data["data"]

                for entry in transactions:
                    if entry.get("details", {}).get("id") == target_id:
                        sales_found += 1
                        buyer_name = entry["agent"]["name"] + " (" + str(entry["agent"]["id"]) + ")"
                        if buyer_name in buyer_counts:
                            buyer_counts[buyer_name] += 1
                        else:
                            buyer_counts[buyer_name] = 1
                if data.get("nextPageCursor"):
                    cursor = data["nextPageCursor"]
                    print(cursor)
                else:
                    break
            else:
                print("Failed to fetch transactions:", response.status_code)
                break
except Exception as e:
    print("An error occurred:", e)

table = PrettyTable()
table.field_names = ["Buyer Information", "Copies Bought"]

sorted_buyer_counts = sorted(buyer_counts.items(), key=lambda x: x[1], reverse=True)

for buyer, count in sorted_buyer_counts:
    table.add_row([buyer, count])

###################################################
    
copy_buyers = {buyer: count for buyer, count in buyer_counts.items()}

copy_counts_combined = {}
for buyer, count in copy_buyers.items():
    if count in copy_counts_combined:
        copy_counts_combined[count] += 1
    else:
        copy_counts_combined[count] = 1

table_copy_combined = PrettyTable()
table_copy_combined.field_names = ["Number of Buyers", "Number of Copies"]

sorted_combined_counts = sorted(copy_counts_combined.items(), key=lambda x: x[0])

for copies, buyers_count in sorted_combined_counts:
    table_copy_combined.add_row([str(buyers_count) + " Buyers", str(copies) + " Copy(s)"])



#####################
print("Item Buyers Information:", item_name, "("+ str(target_id)+ ")")
embed = DiscordEmbed(
    title="Item Buyers Information: " + item_name + " (" + str(target_id) + ")",
    description=f"```{table}```"
)
send_webhook(config["Discord_Webhook"], embed)
print(table)
print("Copies Bought Information:", item_name, "("+ str(target_id)+ ")")
embed = DiscordEmbed(
    title="Copies Bought Information: " + item_name + " (" + str(target_id) + ")",
    description=f"```{table_copy_combined}```"
)
send_webhook(config["Discord_Webhook"], embed)
print(table_copy_combined)
print(str(sales_found), "Sales found!")
