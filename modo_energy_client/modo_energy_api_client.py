import logging
import os
import time
from datetime import date
from typing import Any, Dict, Optional

import pandas as pd
import pandera as pa
import requests
import requests_cache
from pandera.typing import DataFrame as pandera_DataFrame
from tqdm.auto import tqdm

from modo_energy_client.schemas.ERCOT_BESS_owners_schema import ERCOT_BESS_Owners_Schema
from modo_energy_client.schemas.ERCOT_generation_fuel_mix_schema import (
    ERCOTGenerationFuelMixSchema,
)


class ModoEnergyAPIClient:
    """
    Python client for the Modo Energy API.
    https://developers.modoenergy.com/docs/getting-started
    """

    BASE_URL = "https://api.modoenergy.com/pub/v1"
    _session: Optional[requests_cache.CachedSession]

    def __init__(self, api_token: Optional[str] = None, cache_requests: bool = False):
        self.api_token = api_token or os.getenv("MODO_API_TOKEN")
        self.headers = {"X-Token": self.api_token}
        self._session = (
            requests_cache.CachedSession(cache_name="MODO_API_CACHE")
            if cache_requests
            else requests.session()
        )

    def get_paginated(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Fetches all paginated results from an endpoint and returns as a pandas DataFrame.
        Shows a progress bar if tqdm is installed.
        If a 403 error is encountered, sleeps for 65 seconds and retries the request.
        """

        url = f"{self.BASE_URL}/{endpoint}"
        df = pd.DataFrame()

        with tqdm(total=None, desc="Fetching pages ", unit="page") as pbar:
            while url:
                while True:
                    try:
                        response = self._session.get(
                            url,
                            headers={"accept": "application/json"},
                            params=params,
                        )
                        response.raise_for_status()
                        break
                    except requests.exceptions.HTTPError as e:
                        if response.status_code == 403:
                            logging.warning(
                                "Received 403 Forbidden. Sleeping for 65 seconds before retrying..."
                            )
                            time.sleep(65)
                            continue
                        else:
                            raise
                data = response.json()
                if "results" in data:
                    df = pd.concat(
                        [df, pd.DataFrame(data["results"])], ignore_index=True
                    )
                url = data.get("next")
                params = None  # Only use params on first request

                pbar.update(1)

        return df

    @pa.check_types
    def get_ercot_generation_fuel_mix(
        self, date_from: date, date_to: date
    ) -> pandera_DataFrame[ERCOTGenerationFuelMixSchema]:
        """
        The fuel-mix of ERCOT generation in MW.

        https://developers.modoenergy.com/reference/generation-fuel-mix

        Fetch ERCOT generation fuel mix data.
        Accepts date_from and date_to as date objects.
        """
        endpoint = "us/ercot/system/fuel-mix"
        params = {
            "date_from": date_from.strftime("%Y-%m-%d"),
            "date_to": date_to.strftime("%Y-%m-%d"),
            "limit": 10_000,
        }
        df = self.get_paginated(endpoint, params)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df

    @pa.check_types
    def get_ercot_modo_owners(
        self, date_from: date, date_to: date, **kwargs
    ) -> pandera_DataFrame[ERCOT_BESS_Owners_Schema]:
        """
        The power and energy capacity of the ERCOT BESS assets owned by each owner on a monthly basis. Updated on the first of the month every month.

        https://developers.modoenergy.com/reference/bess-owners-ercot


        Fetch ERCOT BESS owners data from the 'us/ercot/modo/owners' endpoint.
        Accepts date_from and date_to as date objects.
        Additional query params can be passed as kwargs.

        """
        endpoint = "us/ercot/modo/owners"
        params = {
            "date_from": date_from.strftime("%Y-%m"),
            "date_to": date_to.strftime("%Y-%m"),
        }
        params.update(kwargs)
        df = self.get_paginated(endpoint, params)
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        return df
