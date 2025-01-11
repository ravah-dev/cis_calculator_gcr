# class_RefDataLoader.py
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
import csv

class RefDataLoader:
    def __init__(self, mapping_csv_path: str):
        self._variables: Dict[str, float] = {}
        self._mapping = self._load_variable_mapping(mapping_csv_path)

    # <internal function> create a dictionary to store the reference mapping data
    @staticmethod
    def _load_variable_mapping(csv_path: str) -> Dict[str, Dict[str, str]]:
        """
        Load the variable mapping from a CSV file.
        """
        try:
            mapping = {} # Initialize an empty dictionary
            # Open file with UTF-8-SIG encoding to handle the BOM
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                required_columns = {'name', 'sheet', 'cell', 'type', 'description'}
                if not required_columns.issubset(set(reader.fieldnames)):
                    missing = required_columns - set(reader.fieldnames)
                    raise ValueError(f"Missing required columns in CSV: {missing}")
                
                # Populate the mapping dictionary with the data from the CSV reader
                for row in reader:
                    mapping[row['name']] = {
                        'sheet': row['sheet'],
                        'cell': row['cell'],
                        'type': row['type'],
                        'description': row['description']
                    }
            return mapping
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Mapping CSV file not found: {csv_path}")
        except Exception as e:
            raise ValueError(f"Error loading mapping CSV: {str(e)}")

    # <internal function> convert Excel column letter to zero-based column index
    @staticmethod
    def _excel_column_to_index(column_letter: str) -> int:
        """Convert Excel column letter to zero-based column index."""
        result = 0
        for char in column_letter:
            result = result * 26 + (ord(char.upper()) - ord('A') + 1)
        return result - 1

    # <public function> load variables from an Excel file
    def load_from_excel(self, filepath: str) -> None:
        """Load all variables from Excel file with validation."""
        try:
            wb = pd.ExcelFile(filepath)
            
            for var_name, details in self._mapping.items():
                sheet = details['sheet']
                cell = details['cell'].replace('!$', '').replace('$', '')  # Strip absolute refs
                
                # Parse the cell reference
                col_letter = ''.join(c for c in cell if c.isalpha())
                row = int(''.join(c for c in cell if c.isdigit()))
                
                try:
                    # Convert column letter to index
                    col_idx = self._excel_column_to_index(col_letter)
                    
                    # Read the specific cell using numeric index
                    df = pd.read_excel(
                        wb,
                        sheet_name=sheet,
                        usecols=[col_idx],
                        nrows=row,
                        header=None
                    )
                    value = df.iloc[row-1, 0]
                    
                    # Validate and convert type
                    if pd.isna(value):
                        raise ValueError(f"Missing value for {var_name} at {sheet}!{cell}")
                    
                    try:
                        self._variables[var_name] = float(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Cannot convert value '{value}' to float for {var_name}")
                    
                except Exception as e:
                    raise ValueError(f"Error loading {var_name} from {sheet}!{cell}: {str(e)}")
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Error loading Excel file: {str(e)}")

    # <public function> get a variable value with type safety
    def get_variable(self, name: str) -> Optional[float]:
        """
        Get a variable value with type safety.

        This method retrieves the value of a variable from the internal dictionary.
        If the variable does not exist, it returns None.

        Parameters:
        name (str): The name of the variable to retrieve.

        Returns:
        Optional[float]: The value of the variable if it exists, otherwise None.
        """
        return self._variables.get(name)
    
    # <public function> get all variables as a dictionary
    def get_all_variables(self) -> Dict[str, float]:
        """
        Returns a copy of all variables as a dictionary.
        """
        return self._variables.copy()
    
    # <public function> validate all variables present in the loaded Excel file
    def validate_all_variables_present(self) -> list[str]:
        """
        Check if all expected variables are loaded.
        
        Returns:
            List of missing variable names
        """
        missing = []
        for var_name in self._mapping.keys():
            if var_name not in self._variables:
                missing.append(var_name)
        return missing
    
    # <public function> get the description of a variable
    def get_variable_description(self, name: str) -> Optional[str]:
        """
        Get the description of a variable.
        """
        if name in self._mapping:
            return self._mapping[name]['description']
        return None

    # <internal function> allow attribute-style access to variables
    def __getattr__(self, name: str) -> float:
        """Allow attribute-style access to variables."""
        if name in self._variables:
            return self._variables[name]
        raise AttributeError(f"Variable '{name}' not found")

    # <public function> print a summary of all loaded variables and their values
    def print_variable_summary(self) -> None:
        """Print a summary of all loaded variables and their values."""
        print("\nVariable Summary:")
        print("-" * 80)
        print(f"{'Variable Name':<40} {'Value':<15} {'Description'}")
        print("-" * 80)
        for var_name, value in sorted(self._variables.items()):
            desc = self._mapping[var_name]['description']
            print(f"{var_name:<40} {value:<15.6f} {desc}")