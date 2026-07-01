# Bedrock Setup

1. Go to Amazon Bedrock in AWS Console.
2. Choose a region.
3. Enable access to a model.
4. Configure AWS credentials.
5. Edit `.env`:

```env
MODEL_PROVIDER=bedrock
AWS_REGION=eu-west-1
BEDROCK_MODEL_ID=<enabled-model-id>
```

Run:

```bash
uvicorn app.main:app --reload --port 8001
```

Learning IAM shape:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "*"
}
```

Production should narrow permissions and use roles.
