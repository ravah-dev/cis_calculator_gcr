# class_import_greet_defaults.py
# version 4 - (Claude version)
# sources GREET defaults from a csv "GREET_Defaults.csv"
# built to set up global variables in the calling implementation
# - see "example_greet_defaults_usage.py" for usage examples

# dependencies
# pip install pandas numpy

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Union

class GREETDefaults:
    """
    A class to manage GREET default values for different crops.
    """
    def __init__(self, filepath: str):
        """
        Initialize the GREET defaults manager.
        
        Parameters:
            filepath (str): Path to the CSV file containing GREET defaults
        """
        self.filepath = filepath
        self._data = self._load_data()
        self.available_crops = list(self._data.columns)

    def _load_data(self) -> pd.DataFrame:
        """
        Private method to load and process the CSV data.
        
        Returns:
            pd.DataFrame: Processed DataFrame with GREET defaults
        """
        df = pd.read_csv(self.filepath)
        df.set_index('Var_Name', inplace=True)
        df = df.replace('', np.nan)
        df = df.fillna(0)
        return df.astype(float)

    def load_crop_globals(self, crop: str, prefix: str = '') -> Dict[str, float]:
        """
        Load default values for a specified crop as global variables.
        
        Parameters:
            crop (str): Name of the crop (case-insensitive)
            prefix (str): Optional prefix for variable names
            
        Returns:
            Dict[str, float]: Dictionary of variable names and their values
            
        Raises:
            ValueError: If specified crop is not found in the data
        """
        crop = crop.capitalize()
        
        if crop not in self.available_crops:
            raise ValueError(
                f"Crop '{crop}' not found. Available crops: {', '.join(self.available_crops)}"
            )

        crop_values = self._data[crop]
        variables = {}
        
        # Get IPython's global namespace
        try:
            from IPython import get_ipython
            global_namespace = get_ipython().user_ns
        except (ImportError, AttributeError):
            global_namespace = globals()
        
        for var_name, value in crop_values.items():
            clean_name = var_name.replace('default_', '')
            full_name = f"{prefix}{clean_name}"
            variables[full_name] = value
            global_namespace[full_name] = value
            
        return variables

    def get_available_crops(self) -> List[str]:
        """
        Get list of available crops in the data.
        
        Returns:
            List[str]: List of available crop names
        """
        return self.available_crops

    def get_crop_defaults(self, crop: str) -> Dict[str, float]:
        """
        Get all default values for a specified crop as a dictionary.
        
        Parameters:
            crop (str): Name of the crop (case-insensitive)
            
        Returns:
            Dict[str, float]: Dictionary of variable names and their values
        """
        crop = crop.capitalize()
        if crop not in self.available_crops:
            raise ValueError(
                f"Crop '{crop}' not found. Available crops: {', '.join(self.available_crops)}"
            )
        
        return self._data[crop].to_dict()

    def get_metric_values(self, metric: str) -> Dict[str, float]:
        """
        Get values for a specific metric across all crops.
        
        Parameters:
            metric (str): Name of the metric (must start with 'default_')
            
        Returns:
            Dict[str, float]: Dictionary of crop names and their values for the metric
        """
        if not metric.startswith('default_'):
            metric = f'default_{metric}'
            
        if metric not in self._data.index:
            raise ValueError(f"Metric '{metric}' not found in the data")
            
        return self._data.loc[metric].to_dict()