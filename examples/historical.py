from datetime import datetime, timedelta

from sonas_client import SonasClient
import os

username = os.environ["SONAS_USERNAME"]
password = os.environ["SONAS_PASSWORD"]
host = os.environ["SONAS_HOST"]
client = SonasClient(username, password, host)


print("\n--- Historical ---")

for days in range(1, 13):
    start = datetime.now()
    data = client.get_historical(
        "TS",
        "Apr-26",
        start=datetime.now() - timedelta(days=days * 30),
        end=datetime.now(),
    )
    end = datetime.now()
    print("seconds:", (end - start).seconds, "points", len(data))
