from datetime import date

import snowflake.connector

from noaa.snowflake_credentials import (
    ACCOUNT,
    DATABASE,
    ROLE,
    SCHEMA,
    TOKEN,
    USER,
    WAREHOUSE,
)


def get_noaa_weather_data(
    start_date: date, end_date: date, noaa_weather_station_id: str
) -> pd.DataFrame:
    """Fetch NOAA weather data from Snowflake for the given date range."""

    query = """
    SELECT
        TS.DATE,
        TS.VARIABLE_NAME,
        TS.VALUE,
        TS.UNIT,
        SI.NOAA_WEATHER_STATION_NAME,
        SI.STATE_NAME,
        SI.NOAA_WEATHER_STATION_ID
    FROM
        PUBLIC_DATA.NOAA_WEATHER_METRICS_TIMESERIES TS
        JOIN PUBLIC_DATA.NOAA_WEATHER_STATION_INDEX SI ON TS.NOAA_WEATHER_STATION_ID = SI.NOAA_WEATHER_STATION_ID
    WHERE
        SI.NOAA_WEATHER_STATION_ID = %(noaa_weather_station_id)s
        AND TS.VARIABLE_NAME IN ('Average daily wind speed', 'Maximum temperature')
        AND TS.DATE BETWEEN TO_DATE(%(start_date)s) AND TO_DATE(%(end_date)s)
    ORDER BY
        TS.DATE DESC,
        SI.NOAA_WEATHER_STATION_NAME
    """

    with snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        token=TOKEN,
        authenticator="programmatic_access_token",
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
        role=ROLE,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
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
