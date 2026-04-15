from sonas_client import SonasClient
import os
import json

username = os.environ["SONAS_USERNAME"]
password = os.environ["SONAS_PASSWORD"]
host = os.environ["SONAS_HOST"]
client = SonasClient(username, password, host)


count = 0
products = [item for item in client.get_products()]
terms = [
    f"{month}-{year % 100}"
    for year in range(2026, 2030)
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
    if f"{month}-{year % 100}" not in ["Jan-26", "Feb-26", "Mar-26"]
]
track_prices_map = {
    f"{product["code"]}:{term}": "" for product in products for term in terms
}

print("subscribed products", len(track_prices_map))


def on_message(msg):
    global count
    count += 1
    msg = json.loads(msg)
    print(count, msg)


def on_error(e):
    print(e)


client.stream_prices_alt(
    products=[product["code"] for product in products],
    terms=terms,
    on_message=on_message,
    on_error=on_error,
    internal_queue_size=10000,
)
