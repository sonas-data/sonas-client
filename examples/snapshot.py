from datetime import date, time

from sonas_client import SonasClient
import os

username = os.environ["SONAS_USERNAME"]
password = os.environ["SONAS_PASSWORD"]
host = os.environ["SONAS_HOST"]
client = SonasClient(username, password, host)

print("\n--- Snapshot ---")
data = client.get_snapshot(
    date(2026, 4, 1), terms=["Apr-26"], start=time(4, 0, 0), end=time(4, 0, 0)
)
print(data)
