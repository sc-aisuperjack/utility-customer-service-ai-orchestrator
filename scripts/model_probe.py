import boto3
from botocore.exceptions import ClientError

CANDIDATES = [
    ("us-east-1", "amazon.nova-micro-v1:0"),
    ("us-east-1", "amazon.nova-lite-v1:0"),
    ("us-east-1", "openai.gpt-oss-20b-1:0"),
    ("us-east-1", "openai.gpt-oss-120b-1:0"),
    ("us-east-1", "mistral.mistral-7b-instruct-v0:2"),
    ("us-east-1", "mistral.mistral-small-2402-v1:0"),
    ("us-east-1", "meta.llama3-8b-instruct-v1:0"),
    ("eu-west-1", "openai.gpt-oss-120b-1:0"),
    ("eu-west-1", "google.gemma-3-4b-it"),
    ("eu-west-1", "google.gemma-3-12b-it"),
    ("eu-west-1", "zai.glm-4.7-flash"),
]


def extract_final_text(response: dict) -> str:
    content = (
        response
        .get("output", {})
        .get("message", {})
        .get("content", [])
    )

    texts = []

    for block in content:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            texts.append(block["text"])

    return "\n".join(texts)


def try_model(region: str, model_id: str):
    print("\n" + "=" * 90)
    print(f"Trying region={region} model={model_id}")

    client = boto3.client("bedrock-runtime", region_name=region)

    try:
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": "Reply with exactly: Bedrock works."
                        }
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": 30,
                "temperature": 0.0,
            },
        )

        text = extract_final_text(response)

        print("✅ SUCCESS")
        print("Text:", text)
        print("Usage:", response.get("usage", {}))
        print("Metrics:", response.get("metrics", {}))

        return True

    except ClientError as e:
        print("❌ CLIENT ERROR")
        print("Code:", e.response["Error"].get("Code"))
        print("Message:", e.response["Error"].get("Message"))
        return False

    except Exception as e:
        print("❌ OTHER ERROR")
        print(type(e).__name__, str(e))
        return False


def main():
    working = []

    for region, model_id in CANDIDATES:
        ok = try_model(region, model_id)
        if ok:
            working.append((region, model_id))
            break

    print("\n" + "=" * 90)
    if working:
        region, model_id = working[0]
        print("Use this in .env:")
        print(f"AWS_REGION={region}")
        print(f"BEDROCK_MODEL_ID={model_id}")
    else:
        print("No candidate worked.")
        print("Most likely causes:")
        print("- your account has exhausted daily Bedrock token quota")
        print("- model access/subscription is not enabled")
        print("- IAM permissions allow listing models but not invoking them")
        print("- provider-specific quota is too low")


if __name__ == "__main__":
    main()