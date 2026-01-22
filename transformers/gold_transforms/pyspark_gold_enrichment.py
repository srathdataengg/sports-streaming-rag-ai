import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def generate_gold_features():
    spark = SparkSession.builder.appName("StatPulse_Gold_Enrichment").getOrCreate()

    # Dynamic Path Resolution (The "Lead Engineer" way)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bronze_path = os.path.join(project_root, 'data', 'bronze', 'bronze_historical_games.json')
    gold_output_path = os.path.join(project_root, 'data', 'gold', 'team_performance_features')

    # 1. Load Bronze (Multi-line JSON support)
    df = spark.read.option("multiline", "true").json(bronze_path)

    # 2. Window Spec: Partition by Team, Order by Time
    # We look at the current row + previous 2 rows for a 3-game rolling window
    team_window = Window.partitionBy("home_team").orderBy("timestamp")

    # 3. Feature Engineering: Momentum & Rolling Avg
    gold_df = df.withColumn(
        "momentum_score",
        F.avg("home_score").over(team_window.rowsBetween(-2, 0))
    )

    # 4. AI-Ready Text Generation (The RAG Bridge)
    # This creates a 'Semantic Column' that the LLM can understand directly
    gold_df = gold_df.withColumn(
        "ai_feature_text",
        F.concat(
            F.lit("As of "), F.col("timestamp").cast("string"),
            F.lit(", the "), F.col("home_team"),
            F.lit(" are showing a momentum score of "), F.round(F.col("momentum_score"), 1),
            F.lit(". Key historical performer: "), F.col("key_performer")
        )
    )

    # 5. Write to Gold as Parquet (Optimized for Lakehouse)
    gold_df.write.mode("overwrite").parquet(gold_output_path)

    print(f"✨ Gold Features saved to Parquet at: {gold_output_path}")


if __name__ == "__main__":
    generate_gold_features()