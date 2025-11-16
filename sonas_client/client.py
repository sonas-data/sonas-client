import base64
import requests
from websockets.sync.client import connect
from datetime import datetime, date, time
import json
import logging

from websockets.exceptions import InvalidStatus


class SonasClient:
    def __init__(self, username: str, password: str, host: str):
        self.username = username
        self.password = password
        self.host = host
        self._http_url = (
            f"{"http" if host.startswith('localhost') else "https"}://{host}/api/v1"
        )
        self._ws_url = (
            f"{"ws" if host.startswith('localhost') else "wss"}://{host}/api/v1"
        )
        self._token = None
        self._stop_streaming = True

    def login(self):
        """Login to the API"""
        base64_encoded_credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode("ascii")
        ).decode("ascii")
        response = requests.post(
            f"{self._http_url}/auth/token",
            headers={"Authorization": f"Basic {base64_encoded_credentials}"},
        )
        if response.status_code != 200:
            raise Exception(f"Failed to login: {response.text}")
        self._token = response.json()["data"]["token"]

    def _get_headers(self):
        if self._token is None:
            self.login()
        return {"Authorization": f"Bearer {self._token}"}

    def get_data_permissions(self):
        res = requests.get(
            f"{self._http_url}/data-permissions",
            headers=self._get_headers(),
        )
        if res.status_code != 200:
            raise Exception(f"Failed to get data permissions: {res.text}")
        data = res.json()["data"]
        return data

    def get_snapshot(
        self,
        day: date,
        start: time = time(7, 0, 0),
        end: time = time(20, 30, 0),
        products: list[str] = [],
        terms: list[str] = [],
    ):
        """Get the snapshot of all products and terms"""
        params = {}
        if products:
            params["products"] = products
        if terms:
            params["terms"] = terms
        if day:
            params["day"] = day.isoformat()
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()

        res = requests.get(
            f"{self._http_url}/prices/snapshot",
            params=params,
            headers=self._get_headers(),
        )
        if res.status_code != 200:
            raise Exception(f"Failed to get snapshot: {res.text}")
        data = res.json()["data"]
        return data

    def get_historical(self, product: str, term: str, start: datetime, end: datetime):
        """Get historical prices for a product and term"""
        params = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "product": product,
            "term": term,
        }
        res = requests.get(
            f"{self._http_url}/prices/historical",
            params=params,
            headers=self._get_headers(),
        )
        if res.status_code != 200:
            raise Exception(f"Failed to get snapshot: {res.text}")
        data = res.json()["data"]
        return data

    def stream_prices(
        self,
        products: list[str],
        terms: list[str],
        on_message: callable,
        on_error: callable,
    ):
        """Runs a websocket clients listining to a stream of prices of subscribed products and terms"""
        self._stop_streaming = False
        MAX_PRODUCTS_PER_SUBSCRIPTION = 1000
        try:
            with connect(
                f"{self._ws_url}/prices/stream", additional_headers=self._get_headers()
            ) as ws:
                subscriptions = []
                for product in products:
                    for term in terms:
                        subscription = {
                            "product": product,
                            "term": term,
                        }
                        subscriptions.append(subscription)
                n = len(subscriptions)
                for i in range(0, n, MAX_PRODUCTS_PER_SUBSCRIPTION):
                    message = json.dumps(
                        {"action": "SUBSCRIBE", "subscriptions": subscriptions[i: i + MAX_PRODUCTS_PER_SUBSCRIPTION]}
                    )
                    ws.send(message)

                while not self._stop_streaming:
                    data = ws.recv(decode=True)
                    on_message(data)

        except InvalidStatus as e:
            if e.response.status_code == 401:
                logging.error("User is unauthorized")
            elif e.response.status_code == 403:
                logging.error(
                    "User might might not have permissions to get "
                    "streaming prices or the user is already signed in"
                )
            on_error(e)
        except Exception as e:
            on_error(e)

    def stop_stream_prices(self):
        self._stop_streaming = True


class SonasAdminClient:
    def __init__(self, username: str, password: str, host: str):
        self.username = username
        self.password = password
        self.host = host
        self._http_url = (
            f"{"http" if host.startswith('localhost') else "https"}://{host}/api/v1"
        )
        self._token = None

    def login(self):
        """Login to the API"""
        base64_encoded_credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode("ascii")
        ).decode("ascii")
        response = requests.post(
            f"{self._http_url}/auth/token",
            headers={"Authorization": f"Basic {base64_encoded_credentials}"},
        )
        if response.status_code != 200:
            raise Exception(f"Failed to login: {response.text}")
        self._token = response.json()["data"]["token"]

    def _get_headers(self):
        if self._token is None:
            self.login()
        return {"Authorization": f"Bearer {self._token}"}

    def update_historical(self, prices: list[dict]):
        """Update historical prices

        Args:
            prices: List of price dictionaries with keys: product (str), term (str),
                    price (float), ts (datetime)

        Raises:
            TypeError: If prices is not a list or contains invalid data types
            ValueError: If price dictionaries are missing required keys
        """
        # Validate that prices is a list
        if not isinstance(prices, list):
            raise TypeError(f"prices must be a list, got {type(prices).__name__}")

        # Validate each price dictionary
        for idx, price_dict in enumerate(prices):
            if not isinstance(price_dict, dict):
                raise TypeError(
                    f"prices[{idx}] must be a dict, got {type(price_dict).__name__}"
                )

            # Check for required keys
            required_keys = {"product", "term", "price", "ts"}
            missing_keys = required_keys - set(price_dict.keys())
            if missing_keys:
                raise ValueError(
                    f"prices[{idx}] is missing required keys: {', '.join(sorted(missing_keys))}"
                )

            # Validate product type (string)
            if not isinstance(price_dict["product"], str):
                raise TypeError(
                    f"prices[{idx}]['product'] must be a string, got {type(price_dict['product']).__name__}"
                )

            # Validate term type (string)
            if not isinstance(price_dict["term"], str):
                raise TypeError(
                    f"prices[{idx}]['term'] must be a string, got {type(price_dict['term']).__name__}"
                )

            # Validate price type (float or int)
            if not isinstance(price_dict["price"], (int, float)):
                raise TypeError(
                    f"prices[{idx}]['price'] must be a number (int or float), got {type(price_dict['price']).__name__}"
                )

            # Validate ts type (datetime)
            if not isinstance(price_dict["ts"], datetime):
                raise TypeError(
                    f"prices[{idx}]['ts'] must be a datetime object, got {type(price_dict['ts']).__name__}"
                )

        # Convert datetime objects to ISO format strings for JSON serialization
        serialized_prices = []
        for price_dict in prices:
            ts = price_dict["ts"]
            # Ensure timezone-aware datetime with UTC if naive
            if ts.tzinfo is None:
                # Naive datetime - format with explicit +00:00
                ts_str = ts.isoformat() + "+00:00"
            else:
                # Timezone-aware datetime - use standard isoformat
                ts_str = ts.isoformat()

            serialized_dict = {
                "product": price_dict["product"],
                "term": price_dict["term"],
                "price": float(price_dict["price"]),
                "ts": ts_str,
            }
            serialized_prices.append(serialized_dict)

        # Make PUT request
        payload = {"data": serialized_prices}
        res = requests.put(
            f"{self._http_url}/prices/historical",
            json=payload,
            headers=self._get_headers(),
        )

        if res.status_code != 200:
            raise Exception(f"Failed to update historical prices: {res.text}")

        return res.json()
