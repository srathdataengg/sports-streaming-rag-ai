import json
import random
import time
from datetime import datetime, timezone

def generate_event():
    return {
        "event_type": "heartbeat",
        "session_id": f"sess-{random.randint(1,1000)}",
        "region": random.choice(["US-East", "US-West"]),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    for _ in range(5):
        print(json.dumps(generate_event()))
        time.sleep(1)
