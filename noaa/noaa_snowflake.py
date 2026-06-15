import snowflake.connector
from snowflake_credentials import (
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
        conn = snowflake.connector.connect(
            account=ACCOUNT,
            user=USER,
            token=TOKEN,
            authenticator="programmatic_access_token",
            warehouse=WAREHOUSE,
            database=DATABASE,
            schema=SCHEMA,
            role=ROLE,
        )
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching data from Snowflake: {e}")
        return None


if __name__ == "__main__":
    data = get_noaa_weather_data()
    if data:
        for row in data:
            print(row)
