import json

with open("bedrock_quotas.json", "r", encoding="utf-8") as f:
    data = json.load(f)

matches = []

for quota in data.get("Quotas", []):
    name = quota.get("QuotaName", "")
    value = quota.get("Value", 0)

    if "On-demand model inference" in name and value and value > 0:
        matches.append(
            {
                "name": name,
                "value": value,
                "adjustable": quota.get("Adjustable"),
                "quota_code": quota.get("QuotaCode"),
            }
        )

if not matches:
    print("No non-zero on-demand Bedrock invoke quotas found in this region.")
else:
    for item in matches:
        print("\nName:", item["name"])
        print("Value:", item["value"])
        print("Adjustable:", item["adjustable"])
        print("QuotaCode:", item["quota_code"])