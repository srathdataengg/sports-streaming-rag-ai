import os
import json
import boto3
from dotenv import load_dotenv
from pinecone import Pinecone

# Setup
load_dotenv()
PINECONE_KEY = os.getenv("PINECONE_API_KEY")
AWS_REGION = "us-east-1"

pc = Pinecone(api_key=PINECONE_KEY)
index = pc.Index("sports-intelligence")
bedrock = boto3.client(service_name="bedrock-runtime", region_name=AWS_REGION)


def get_query_embedding(text):
    body = json.dumps({"inputText": text})
    response = bedrock.invoke_model(
        body=body,
        modelId="amazon.titan-embed-text-v2:0",
        accept="application/json",
        contentType="application/json"
    )
    return json.loads(response.get("body").read()).get("embedding")


def generate_answer(question, context):
    """Sends the question + Pinecone data to Amazon Titan Text Premier."""
    # This prompt format is optimized for Titan's RAG capabilities
    prompt = f"""
    Instruction: You are a sports data expert. Use the provided context to answer the question.
    If the answer isn't in the context, say you don't have enough data.

    Context:
    {context}

    Question: {question}

    Output:
    """

    # Using Titan Text Premier (The 2025-2026 standard for us-east-1)
    body = json.dumps({
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": 0.3,  # Low temperature for factual sports reporting
            "topP": 0.9
        }
    })

    try:
        response = bedrock.invoke_model(
            body=body,
            modelId="amazon.titan-text-premier-v1:0",
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response.get("body").read())
        return response_body.get("results")[0].get("outputText")
    except Exception as e:
        return f"⚠️ Model Access Error: {e}. Please ensure 'Titan Text Premier' is enabled in Bedrock Model Access."


def ask_sports_ai(question):
    print(f"🔍 Vectorizing query and searching Pinecone...")
    query_vector = get_query_embedding(question)

    results = index.query(vector=query_vector, top_k=3, include_metadata=True)

    # Consolidate results into a text block for the LLM
    context_list = []
    for match in results['matches']:
        m = match['metadata']
        context_list.append(f"- {m['team']} (Momentum: {m['momentum']}): {m['context']}")

    combined_context = "\n".join(context_list)

    print("🤖 AI Analyst is thinking...")
    ai_response = generate_answer(question, combined_context)

    print("\n" + "=" * 50)
    print("🏀 SPORTS AI ANALYST REPORT")
    print("=" * 50)
    print(ai_response)
    print("=" * 50 + "\n")


if __name__ == "__main__":
    q = "Give me a summary of which teams are performing best and why."
    ask_sports_ai(q)
