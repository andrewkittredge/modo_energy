import logging
import os
from datetime import date
from typing import Any

import pandas as pd
import pandera as pa
import requests
import requests_cache
from dotenv import load_dotenv
from pandera.typing import DataFrame as pandera_DataFrame
from tenacity import Retrying, before_sleep_log, stop_after_attempt, wait_exponential
from tqdm.auto import tqdm

from modo_energy_client.schemas.ERCOT_BESS_owners_schema import ERCOT_BESS_Owners_Schema
from modo_energy_client.schemas.ERCOT_generation_fuel_mix_schema import (
    ERCOTGenerationFuelMixSchema,
)

load_dotenv()
logger = logging.getLogger(__name__)


class ModoEnergyAPIClient:
    """
    Python client for the Modo Energy API.
    https://developers.modoenergy.com/docs/getting-started
    """

    BASE_URL = "https://api.modoenergy.com/pub/v1"
    PAGE_LIMIT = 10_000

    def __init__(self, api_token: str | None = None, cache_requests: bool = False):
        """
        api_token defaults to the MODO_API_TOKEN environment variable (a .env
        file in the project root is loaded automatically).
        With cache_requests=True responses are cached in MODO_API_CACHE.sqlite.
        """
        self.api_token = api_token or os.getenv("MODO_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "API token must be provided either as an argument or in the "
                "MODO_API_TOKEN environment variable."
            )
        self._session: requests.Session = (
            requests_cache.CachedSession(cache_name="MODO_API_CACHE")
            if cache_requests
            else requests.Session()
        )
        self._session.headers["accept"] = "application/json"
        if self.api_token:
            self._session.headers["X-Token"] = self.api_token

    def get_paginated(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """
        Fetch every page of results from an endpoint and return them as one DataFrame.
        Failed requests are retried with exponential backoff (up to 10 attempts),
        which also rides out the API rate limit.
        """
        url: str | None = f"{self.BASE_URL}/{endpoint}"
        pages: list[pd.DataFrame] = []

        with tqdm(total=None, desc="Fetching pages", unit="page") as pbar:
            while url:
                for attempt in Retrying(
                    wait=wait_exponential(multiplier=2, min=1, max=1000),
                    stop=stop_after_attempt(10),
                    before_sleep=before_sleep_log(logger, logging.WARNING),
                ):
                    with attempt:
                        response = self._session.get(url, params=params)
                        response.raise_for_status()
                data = response.json()
                if "results" in data:
                    pages.append(pd.DataFrame(data["results"]))
                url = data.get("next")
                params = None  # The "next" URL already carries the query string.
                pbar.update(1)

        return pd.concat(pages, ignore_index=True) if pages else pd.DataFrame()

    @pa.check_types
    def get_ercot_generation_fuel_mix(
        self, date_from: date, date_to: date
    ) -> pandera_DataFrame[ERCOTGenerationFuelMixSchema]:
        """
        The fuel mix of ERCOT generation in MW, indexed by timestamp.

        https://developers.modoenergy.com/reference/generation-fuel-mix
        """
        params = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "limit": self.PAGE_LIMIT,
        }
        df = self.get_paginated("us/ercot/system/fuel-mix", params)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df.set_index("timestamp")

    @pa.check_types
    def get_ercot_bess_owners(
        self, date_from: date, date_to: date, **kwargs: Any
    ) -> pandera_DataFrame[ERCOT_BESS_Owners_Schema]:
        """
        Monthly power and energy capacity of the ERCOT BESS assets held by each owner.
        Only the year and month of date_from / date_to are used.
        Extra query params can be passed as kwargs.

        https://developers.modoenergy.com/reference/bess-owners-ercot
        """
        params = {
            "date_from": date_from.strftime("%Y-%m"),
            "date_to": date_to.strftime("%Y-%m"),
            **kwargs,
        }
        df = self.get_paginated("us/ercot/modo/owners", params)
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        return df

    def get_ercot_prices(self, date_from: date, date_to: date) -> pd.DataFrame:
        """
        ERCOT day-ahead market historical settlement prices, indexed by the
        start of the delivery hour.

        https://developers.modoenergy.com/reference/dam-historical-prices
        """
        params = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "limit": self.PAGE_LIMIT,
        }
        df = self.get_paginated("us/ercot/dam/historical-prices", params)
        df["deliveryDate"] = pd.to_datetime(df["deliveryDate"]) + pd.to_timedelta(
            df["hourEnding"] - 1, unit="h"
        )
        return df.set_index("deliveryDate")
