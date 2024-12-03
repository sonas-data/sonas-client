from sonas_client import SonasClient
from datetime import datetime, timedelta, date, time
import websockets.sync.client as websockets
import os

username = os.environ["SONAS_USERNAME"]
password = os.environ["SONAS_PASSWORD"]
host = os.environ["SONAS_HOST"]
client = SonasClient(username, password, host)

print("\n--- Data permissions ---")
print(client.get_data_permissions())

print("\n--- Historical ---")
print(len(client.get_historical("BS", "Nov-24", start=datetime.now() - timedelta(days=30), end=datetime.now())))

print("\n--- Snapshot ---")
print(
    len(client.get_snapshot(date(2024, 11, 27), start=time(7, 0, 0), end=time(7, 9, 0)))
)  # max 10 snapshots are allowed at a time

count = 0
conn: websockets.ClientConnection | None = None


def on_message(msg):
    global count
    count += 1
    print(count, msg)
    if count > 2000:
        conn.close()


def on_open(ws: websockets.ClientConnection):
    global conn
    conn = ws
    print("stream opened")


def on_close(code, reason):
    print("stream closed")
    print(code, reason)


def on_error(e):
    print(e)


print("\n--- Stream ---")
client.on_stream_prices(
    products=["BS", "BOB", "GS", "OS"],
    terms=[
        f"{month}-{year % 100}"
        for year in [2025, 2026, 2027]
        for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ],
    on_close=on_close,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
)
