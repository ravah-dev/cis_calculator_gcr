# class_soc_lookup.py
#  - ref cell F80 lookup formula in source spreadsheet (version 2) 
# import SOC lookup table from csv files for corn and soybean

import pandas as pd
from typing import Optional

class SOCLookup:
    def __init__(self, corn_csv_path: str, soybean_csv_path: str):
        """Initialize SOC Lookup with paths to both crop CSV files"""
        self.crop_data = {
            'Corn': pd.read_csv(corn_csv_path),
            'Soybean': pd.read_csv(soybean_csv_path)
        }

    def get_soc_factor(self, fips_code: int, crop: str, cover_crop: str, 
                       manure: str, tillage: str) -> Optional[float]:
        """
        Look up SOC factor for given parameters.
        
        Args:
            fips_code: County FIPS code
            crop: Crop type ("Corn" or "Soybean")
            cover_crop: Cover crop status ("No cover crop" or "Cover crop")
            manure: Manure status ("No manure" or "Manure")
            tillage: Tillage type ("Conventional tillage", "Reduced tillage", or "No till")
        
        Returns:
            SOC factor if found, None otherwise
        """
        try:
            if crop not in self.crop_data:
                raise ValueError(f"Invalid crop type: {crop}")

            # Construct column identifier
            scenario = (("C" if cover_crop.lower().startswith("cover") else "N") +
                       ("M" if manure.lower().startswith("manure") else "N") +
                       ("C" if tillage.lower().startswith("conventional") else
                        "R" if tillage.lower().startswith("reduced") else "N"))

            # Look up value
            lookup_value = self.crop_data[crop].loc[
                self.crop_data[crop]["FIPS"] == fips_code,
                scenario
            ].values

            return lookup_value[0] if len(lookup_value) > 0 else None

        except Exception as e:
            raise Exception(f"Error looking up SOC factor: {str(e)}")

if __name__ == "__main__":
    # Initialize lookup tool
    soc_lookup = SOCLookup("corn_soc.csv", "soybean_soc.csv")
    
    # Example lookup
    fips_code = 1031
    params = {
        "crop": "Corn",
        "cover_crop": "No cover crop",
        "manure": "No manure",
        "tillage": "Conventional tillage"
    }
    
    result = soc_lookup.get_soc_factor(fips_code, **params)
    print(f"SOC factor for FIPS {fips_code}: {result}")