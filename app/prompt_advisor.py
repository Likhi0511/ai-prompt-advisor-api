from pydantic import BaseModel
from fastapi import FastAPI,HTTPException
import boto3
import json
import re

app = FastAPI()
bedrock = boto3.client("bedrock-runtime",region_name="us-east-1")

class PromptAdvisor(BaseModel):
    raw_prompt: str
    response_length:str
    audience:str
    tone:str

def output_length(response_length:str):
    if response_length == "long":
        return 300
    elif response_length == "short":
        return 100
    else:
        return 200

def output_tone(audience:str,tone:str):
    return f"""
You are an expert AI Prompt Engineer.

Your task is to:
1. Improve the user's raw prompt.
2. Make it clear, specific, and optimized.
3. Adjust tone to: {tone}.
4. Tailor it for: {audience}.
5. Provide 3 improved variations.
6. Explain what improvements were made.
7. Provide a sample output for one improved version.

Return ONLY valid JSON.
Do NOT add explanations outside JSON.

Required JSON structure:

{{
  "optimized_prompt": "string",
  "improvement_explanation": "string",
  "variations": ["string", "string", "string"],
  "sample_output": "string"
}}
"""
def original_output(request:PromptAdvisor):
    max_tokens = output_length(request.response_length)
    final_prompt = output_tone(request.audience,request.tone)

    body={
        "anthropic_version": "bedrock-2023-05-31",
        "messages":[{
            "role":"user",
            "content":request.raw_prompt
        }],
        "system":final_prompt,
        "max_tokens":max_tokens,
        "temperature":0.7
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

@app.post("/prompt")
def prompt(req: PromptAdvisor):
    try:
        output = original_output(req)
        return {"output":output}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
