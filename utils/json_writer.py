import json
import os
from datetime import datetime, timezone

def write_state(agent, version, filename, data):

    state = {
        "agent": agent,
        "version": version,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "SUCCESS",
        "data": data,
    }

    os.makedirs("data/current", exist_ok=True)

    with open(
        f"data/current/{filename}",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=4
        )

    return state
