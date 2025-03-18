import pandas as pd
import logging
from typing import Dict
import os

# from models import ResponseStatusEnum, StandardResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "all_pin_codes_data.csv")

# ToDO: Add the proper path of the CSV for PINCODE
# csv_path = "all_pin_codes_data.csv"

df = pd.read_csv(csv_path, low_memory=False)

df.set_index("pincode", inplace=True, drop=False)


def get_pincode_details(pincode: int) -> Dict:
    try:
        result = df.loc[
            pincode,
            [
                "circlename",
                "regionname",
                "divisionname",
                "statename",
                "district",
                "pincode",
            ],
        ]

        # If there are multiple rows, result will be a DataFrame, else a Series
        if isinstance(result, pd.Series):
            return result.to_dict()  # Convert single row to list of dicts
        else:
            data: Dict = result.to_dict(
                orient="records"
            )  # Convert multiple rows to list of dicts
            return data[0]
    except KeyError:
        logger.error(f"No data found for pincode {pincode}")
        raise
    except Exception as e:
        logger.error(f"Failed to get pin code : {e}")
        raise e
