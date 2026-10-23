import os
from datetime import date

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

QUERY = """
SELECT
    TS.DATE,
    TS.VARIABLE_NAME,
    TS.VALUE
FROM
    PUBLIC_DATA.NOAA_WEATHER_METRICS_TIMESERIES TS
WHERE
    TS.NOAA_WEATHER_STATION_ID = %(noaa_weather_station_id)s
    AND TS.VARIABLE_NAME IN ('Average daily wind speed')
    AND TS.DATE BETWEEN TO_DATE(%(start_date)s) AND TO_DATE(%(end_date)s)
ORDER BY
    TS.DATE
"""


def get_noaa_weather_data(
    start_date: date, end_date: date, noaa_weather_station_id: str
) -> pd.DataFrame:
    """
    Daily NOAA weather metrics for one station from Snowflake, indexed by date
    with one column per variable name. Connection settings come from the
    SNOWFLAKE_* environment variables (see .env.example).
    """
    with (
        snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            token=os.environ["SNOWFLAKE_TOKEN"],
            authenticator="programmatic_access_token",
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
            schema=os.environ["SNOWFLAKE_SCHEMA"],
            role=os.environ["SNOWFLAKE_ROLE"],
        ) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute(
            QUERY,
            {
                "start_date": start_date,
                "end_date": end_date,
                "noaa_weather_station_id": noaa_weather_station_id,
            },
        )
        data = cursor.fetch_pandas_all()

    data = data.pivot(index="DATE", columns="VARIABLE_NAME", values="VALUE")
    data.index = data.index.astype("datetime64[ns]")
    return data
