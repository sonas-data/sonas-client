import base64
import requests
from websockets.sync.client import connect
from datetime import datetime
import json


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
        self.token = None

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
        self.token = response.json()["data"]["token"]

    def _get_headers(self):
        if self.token is None:
            self.login()
        return {"Authorization": f"Bearer {self.token}"}

    def get_snapshot(self, products: list[str] = [], terms: list[str] = []):
        """Get the snapshot of all products and terms"""
        params = {}
        if products:
            params["products"] = products
        if terms:
            params["terms"] = terms

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

    def on_stream_prices(
        self,
        products: list[str],
        terms: list[str],
        on_open: callable,
        on_message: callable,
        on_error: callable,
        on_close: callable,
    ):
        """Runs a websocket clients listining to a stream of prices of subscribed products and terms"""
        try:
            with connect(f"{self._ws_url}/prices/stream", additional_headers=self._get_headers()) as ws:
                on_open(ws)
                for product in products:
                    for term in terms:
                        message = json.dumps({
                                "action": "SUBSCRIBE",
                                "product": product,
                                "term": term,
                            })
                        ws.send(message)

                    while True:
                        data = ws.recv()
                        on_message(data)

        except Exception as e:
            on_error(e)
        finally:
            on_close()