from sonas_client import SonasClient, SonasAdminClient
from datetime import datetime, timedelta, date, time
import os

username = os.environ["SONAS_USERNAME"]
password = os.environ["SONAS_PASSWORD"]
host = os.environ["SONAS_HOST"]
client = SonasClient(username, password, host)
admin_client = SonasAdminClient(username, password, host)
print("\n--- Data permissions ---")
data_permissions = client.get_data_permissions()
products = data_permissions["products"]
print(data_permissions)

print("\n--- Historical ---")
print(
    # len(
    client.get_historical(
        "BS",
        "Apr-26",
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
    )
    # )
)


print("\n--- Snapshot ---")
print(
    len(client.get_snapshot(date(2026, 3, 31), terms=["Apr-26"], start=time(17, 58, 0), end=time(17, 58, 0)))
)  # max 10 snapshots are allowed at a time

count = 0


def on_message(msg):
    global count
    count += 1
    print(count, msg)
    if count > 5000:
        client.stop_stream_prices()


def on_error(e):
    print(e)


client.stream_prices_alt(
    products=products,
    terms=[
        f"{month}-{year % 100}"
        for year in range(2025, 2030)
        for month in [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
    ],
    on_message=on_message,
    on_error=on_error,
)

# 2025-10-30T04:00:00+00:00
# admin_client.update_historical(prices=[{ "price": 23, "product": "BS", "term": "Aug-25", "ts": datetime(2025, 10, 30, 4, 0, 0, 0)}])