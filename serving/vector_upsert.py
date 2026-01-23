import os
import json
import boto3
import pandas as pd
from dotenv import load_dotenv
from pinecone import Pinecone
from pyspark.sql import SparkSession

# 1. Configuration & Secrets
load_dotenv()
PINECONE_KEY = os.getenv("PINECONE_API_KEY")
AWS_REGION = "us-east-1"

# Initialize Clients
pc = Pinecone(api_key=PINECONE_KEY)
index = pc.Index("sports-intelligence")
bedrock = boto3.client(service_name="bedrock-runtime", region_name=AWS_REGION)


def get_embedding(text):
    """
    Calls Amazon Bedrock Titan v2.
    Since index is now 1024, we use the simple schema which defaults to 1024.
    """
    body = json.dumps({
        "inputText": text
    })

    try:
        response = bedrock.invoke_model(
            body=body,
            modelId="amazon.titan-embed-text-v2:0",
            accept="application/json",
            contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        return response_body.get("embedding")
    except Exception as e:
        print(f"⚠️ Bedrock API error: {e}")
        return None


def run_upsert_pipeline():
    # 2. Start Spark Session
    spark = SparkSession.builder \
        .appName("GoldToVectorPipeline") \
        .getOrCreate()

    # 3. Read Gold Parquet Data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    gold_path = os.path.join(project_root, 'data', 'gold', 'team_performance_features')

    print(f"🚀 Reading Gold data from: {gold_path}")

    try:
        gold_df = spark.read.parquet(gold_path)
    except Exception as e:
        print(f"❌ Error reading Parquet: {e}")
        return

    # Convert to Pandas
    pdf = gold_df.toPandas()

    print(f"📊 Columns Found: {pdf.columns.tolist()}")
    print(f"🧠 Generating 1024-dim embeddings for {len(pdf)} records...")

    vectors_to_upsert = []

    for _, row in pdf.iterrows():
        try:
            text_to_embed = row.get('ai_feature_text', '')
            if not text_to_embed:
                continue

            vector = get_embedding(text_to_embed)
            if vector is None:
                continue

            # Mapping confirmed Spark columns to Pinecone metadata
            vectors_to_upsert.append({
                "id": str(row.get('game_id', 'unknown')),
                "values": vector,
                "metadata": {
                    "team": str(row.get('home_team', 'Unknown')),
                    "away_team": str(row.get('away_team', 'Unknown')),
                    "momentum": float(row.get('momentum_score', 0.0)),
                    "context": str(row.get('ai_feature_text', '')),
                    "timestamp": str(row.get('timestamp', ''))
                }
            })
        except Exception as e:
            print(f"❌ Error processing record {row.get('game_id')}: {e}")

    # 4. Push to Pinecone
    if vectors_to_upsert:
        try:
            index.upsert(vectors=vectors_to_upsert)
            print(f"✅ Success! Upserted {len(vectors_to_upsert)} vectors to 'sports-intelligence'.")
        except Exception as e:
            print(f"❌ Pinecone Upsert Error: {e}")
    else:
        print("ℹ️ No vectors were generated to upsert.")

    spark.stop()


if __name__ == "__main__":
    run_upsert_pipeline()