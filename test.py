#!/usr/bin/env python3

import time
import requests

URL = "https://www.githubstatus.com/api/v2/status.json"
INTERVAL = 60  # seconds

last_message = None

while True:
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()
        data = r.json()

        message = data["status"]["description"]
        indicator = data["status"]["indicator"]

        current = f"{indicator.upper()}: {message}"

        if current != last_message:
            print(time.strftime("%Y-%m-%d %H:%M:%S"), current)
            last_message = current

    except Exception as e:
        print("Error:", e)

    time.sleep(INTERVAL)
