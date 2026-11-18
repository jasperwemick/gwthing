import requests
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

class GW2Client:
    BASE_URL = "https://api.guildwars2.com/v2"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        else:
            self.session.headers.update({"Content-Type": "application/json"})

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params)
        print(response.status_code)
        if response.status_code >= 400 and response.status_code != 404:
            response.raise_for_status()
        elif response.status_code == 404:
            return []
        else:
            return response.json()

    def get_prices(self, ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        params = {"ids": ",".join(map(str, ids))} if ids else {}
        return self._request("/commerce/prices", params=params)

    def get_listings(self, ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        params = {"ids": ",".join(map(str, ids))} if ids else {}
        return self._request("/commerce/listings", params=params)

    def get_transactions(self, second_level: str = "current", third_level: str = "buys") -> List[Dict[str, Any]]:
        # Note: This is an authenticated endpoint
        endpoint = f"/commerce/transactions/{second_level}/{third_level}"
        return self._request(endpoint)

    def get_items(self, page : int = 0, page_size : int = 50) -> List[Dict[str, Any]]:
        return self._request("/items", { 'page' : page, 'page_size' : page_size })

    def get_recipes(self, page : int = 0, page_size : int = 50) -> List[Dict[str, Any]]:
        return self._request("/recipes", { 'page' : page, 'page_size' : page_size, 'v' : '2022-03-09T02:00:00.000Z' })

    def get_currencies(self, page : int = 0, page_size : int = 50) -> List[Dict[str, Any]]:
        return self._request("/currencies", { 'page' : page, 'page_size' : page_size })
