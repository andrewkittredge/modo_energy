import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series


class ERCOT_BESS_Owners_Schema(pa.DataFrameModel):
    date: Series[pd.Timestamp]
    owner: Series[str]
    total_energy_capacity_mwh: Series[float]
    total_rated_power_mw: Series[float]
