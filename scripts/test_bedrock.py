import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

region = os.getenv("AWS_REGION", "eu-west-1")
model_id = os.getenv("BEDROCK_MODEL_ID")

if not model_id:
    raise RuntimeError("BEDROCK_MODEL_ID is missing in .env")

client = boto3.client("bedrock-runtime", region_name=region)


def extract_final_text(response: dict) -> list[str]:
    """
    Extract only customer-visible final text blocks from Bedrock Converse responses.

    Some reasoning-style models return both:
    - reasoningContent / reasoningText
    - final text

    We deliberately ignore reasoningContent because that should never be shown
    to an end user or returned by the app.
    """
    content = (
        response
        .get("output", {})
        .get("message", {})
        .get("content", [])
    )

    texts: list[str] = []

    for block in content:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            texts.append(block["text"])

    return texts


try:
    response = client.converse(
        modelId=model_id,
        system=[
            {
                "text": (
                    "You are a concise technical assistant. "
                    "Answer in one sentence only. "
                    "Do not include reasoning or analysis."
                )
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": "Say hello and confirm Bedrock is working."
                    }
                ],
            }
        ],
        inferenceConfig={
            "temperature": 0.1,
            "maxTokens": 20,
        },
    )

    print("\nRAW RESPONSE:")
    print(json.dumps(response, indent=2, default=str))

    texts = extract_final_text(response)

    print("\nFINAL TEXT ONLY:")
    if texts:
        print("\n".join(texts))
    else:
        print("No final plain text block found.")
        print("This model may be returning a different Converse response shape.")

    print("\nUSAGE:")
    print(response.get("usage", {}))

    print("\nMETRICS:")
    print(response.get("metrics", {}))

except ClientError as e:
    print("Bedrock ClientError")
    print("Code:", e.response["Error"].get("Code"))
    print("Message:", e.response["Error"].get("Message"))
    raise