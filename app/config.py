import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    model_provider: str = os.getenv("MODEL_PROVIDER", "local")
    prompt_version: str = os.getenv("PROMPT_VERSION", "utility_assistant_v1")
    aws_region: str = os.getenv("AWS_REGION", "eu-west-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    max_retrieved_docs: int = int(os.getenv("MAX_RETRIEVED_DOCS", "4"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "600"))

settings = Settings()
