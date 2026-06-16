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


def get_noaa_weather_data():
    """Fetch NOAA weather data from Snowflake."""

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
        SI.noaa_weather_station_id = 'USW00012960'
        AND TS.VARIABLE_NAME IN ('Average daily wind speed', 'Maximum temperature')
    ORDER BY
        TS.DATE DESC,
        SI.NOAA_WEATHER_STATION_NAME
    """

    try:
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
                cursor.execute(query)
                data = cursor.fetch_pandas_all()
                data = data.pivot(index="DATE", columns="VARIABLE_NAME", values="VALUE")
                data.index = data.index.astype("datetime64[ns]")
                return data

    except Exception as e:
        print(f"Error fetching data from Snowflake: {e}")
        return None
