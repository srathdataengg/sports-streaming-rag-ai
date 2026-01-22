import json
import random
import uuid
import os
from datetime import datetime, timedelta

# Configuration for our "Artificial" History
TEAMS = ["Lakers", "Warriors", "Celtics", "Heat", "Nuggets", "Suns"]
PLAYERS = {
    "Lakers": ["LeBron James", "Anthony Davis"],
    "Warriors": ["Steph Curry", "Draymond Green"],
    "Celtics": ["Jayson Tatum", "Jaylen Brown"]
}


def generate_narrative(home, away, h_score, a_score):
    """
    This is the 'Secret Sauce' for RAG.
    It creates the text the AI will actually 'read' later.
    """
    winner = home if h_score > a_score else away
    margin = abs(h_score - a_score)

    scenarios = [
        f"A dominant performance by {winner}, winning by {margin} points.",
        f"A nail-biter at the buzzer! {winner} secured the win in the final seconds.",
        f"Despite a late surge from the {away if winner == home else home}, {winner} held their lead."
    ]
    return random.choice(scenarios)


def build_bronze_history(num_games=50):
    history = []
    start_date = datetime.now() - timedelta(days=60)

    # Get the absolute path of the current module
    script_path = os.path.abspath(__file__)

    # 2. Path to the folder containing this file (scripts/)
    script_dir = os.path.dirname(script_path)

    # Get the parent directory
    project_root = os.path.dirname(script_dir)

    # Define the data path relative to the project root
    data_dir = os.path.join(project_root, 'data')
    file_path = os.path.join(data_dir, 'bronze_historical_games.json')

    # Create the respective directory if doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    for i in range(num_games):
        home, away = random.sample(TEAMS, 2)
        h_score = random.randint(90, 130)
        a_score = random.randint(90, 130)

        # Simulating the 'Bronze' Raw Record
        game = {
            "game_id": str(uuid.uuid4())[:8],
            "timestamp": (start_date + timedelta(days=i)).isoformat(),
            "home_team": home,
            "away_team": away,
            "home_score": h_score,
            "away_score": a_score,
            "key_performer": random.choice(PLAYERS.get(home, ["Unknown Player"])),
            "match_summary": generate_narrative(home, away, h_score, a_score)  # AI FUEL
        }
        history.append(game)

    with open(file_path, 'w') as f:
        json.dump(history, f, indent=4)
    print(f"✅ Generated {num_games} historical games in Bronze Layer.")


if __name__ == "__main__":
    build_bronze_history()
