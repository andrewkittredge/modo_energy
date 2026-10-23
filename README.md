# modo_energy

Demo client for the [Modo Energy API](https://developers.modoenergy.com/docs/getting-started)
plus a notebook modelling intra-day arbitrage spread in the ERCOT day-ahead market as a
function of wind speed and installed BESS capacity.

## Layout

- `modo_energy_client/` - `ModoEnergyAPIClient`: paginated, retrying, optionally cached requests with pandera-validated responses.
- `noaa/` - pulls NOAA daily weather data from Snowflake.
- `analysis.ipynb` - the Prophet model and plots.

## Setup

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env  # then fill in the Modo token and Snowflake credentials
uv run jupyter lab analysis.ipynb
```

Both modules load `.env` automatically via python-dotenv.

With `ModoEnergyAPIClient(cache_requests=True)` responses are cached in `MODO_API_CACHE.sqlite`
(git-ignored). Delete the file to refetch.
