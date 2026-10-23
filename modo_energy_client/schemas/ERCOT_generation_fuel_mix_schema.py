from typing import Annotated

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Index, Series


class ERCOTGenerationFuelMixSchema(pa.DataFrameModel):
    timestamp: Index[Annotated[pd.DatetimeTZDtype, "us", "UTC"]]
    coalAndLignite: Series[float]
    hydro: Series[float]
    naturalGas: Series[float]
    nuclear: Series[float]
    other: Series[float]
    powerStorage: Series[float]
    solar: Series[float]
    wind: Series[float]
    settlementType: Series[str]
    repeated_hour_flag: Series[bool]
