# class_fips_lookup.py
# - uses US Census Bureau FIPS codes source file 'national_county.txt'
# - note: national_county.txt is a csv without header row
# ref. "https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt"

import csv
from typing import Dict, Tuple, Optional

class FIPSLookup:
    def __init__(self):
        self.fips_data: Dict[Tuple[str, str], str] = {}
        self.reverse_lookup: Dict[str, Tuple[str, str]] = {}
        
    def load_data(self, filename: str = "national_county.txt") -> None:
        """
        Load FIPS data from the Census Bureau national_county.txt file.
        
        File format is:
        State Code, State FIPS, County FIPS, County Name, FIPS Class Code
        
        Args:
            filename: Path to the national_county.txt file
        """
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    # Split the line on commas and strip whitespace
                    parts = [part.strip() for part in line.split(',')]
                    
                    # Extract relevant fields
                    # Format: AL,ALABAMA,01,001,Autauga County,H1
                    state_code, state_fips, county_fips, county_name, _ = parts
                    
                    # Create the full FIPS code by combining state and county FIPS
                    full_fips = state_fips + county_fips
                    
                    # Store data both ways for forward and reverse lookup
                    # Convert to title case for consistency
                    # state_name = state_name.title()
                    self.fips_data[(state_code, county_name)] = full_fips
                    self.reverse_lookup[full_fips] = (state_code, county_name)
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find the file: {filename}")
        except Exception as e:
            raise Exception(f"Error reading the file: {str(e)}")

    def get_fips(self, state: str, county: str) -> Optional[str]:
        """
        Get FIPS code for a given state and county.
        
        Args:
            state: state code (e.g., "AL")
            county: County name (e.g., "Autauga County")
            
        Returns:
            FIPS code as string if found, None otherwise
        """
        return self.fips_data.get((state, county))
    
    def get_location(self, fips: str) -> Optional[Tuple[str, str]]:
        """
        Get state and county for a given FIPS code.
        
        Args:
            fips: 5-digit FIPS code as string
            
        Returns:
            Tuple of (state, county) if found, None otherwise
        """
        return self.reverse_lookup.get(fips)
    
    def list_counties(self, state: str) -> list:
        """
        Get all counties for a given state.
        
        Args:
            state: state code (e.g., "AL")
            
        Returns:
            List of county names in the state
        """
        return [county for (st, county) in self.fips_data.keys() if st == state]

# Example usage
if __name__ == "__main__":
    fips_lookup = FIPSLookup()
    fips_lookup.load_data()  # Assumes national_county.txt is in the current directory
    
    # Look up FIPS code
    fips = fips_lookup.get_fips("AL", "Autauga County")
    print(f"FIPS code for Autauga County, Alabama: {fips}")
    
    # Reverse lookup
    location = fips_lookup.get_location("01001")
    print(f"Location for FIPS 01001: {location}")
    
    # List all counties in a state
    counties = fips_lookup.list_counties("AL")
    print(f"\nFirst 5 counties in Alabama: {counties[:5]}")