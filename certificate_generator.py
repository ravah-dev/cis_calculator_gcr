# certificate_generator.py
# - called by cis_calculator.py --> section 5. Generate Individual CIS Scores

# ===========================================
# This code replaces the section 5 from cis_calculator.py as a callable function
# - Currently this function is tested by saving certificates to a file.
# - This needs to be modified to generate a dataframe and save to a Delta Lake table.
# ===========================================

import json
import secrets
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)

def generate_32bit_id():
    """Generate a random 32-bit ID for unique identification."""
    return secrets.randbits(32)

def get_score(scores_list, key_name):
    """Helper function to find a score value from the nested list structure."""
    for item in scores_list:
        if item[0] == key_name:
            # if the value is a float, round to 2 decimal places else return as is
            if isinstance(item[2], float):
                return round(item[2], 2)
            return item[2]
    return None

def certificate_generator(
    feature_scores, 
    features, 
    certificate_type, 
    season, 
    data_Provider, 
    input_collection_id, 
    business_ID, 
    file_level_attributes, 
    fips_code, 
    input_properties, 
    bbox, 
    geometry
):
    """
    Generate certificates based on feature scores and properties.
    
    Args:
        feature_scores (list): List of feature scores to process
        features (list): List of features with properties
        certificate_type (str): Type of certificate to generate
        season (str): Current season
        data_Provider (str): Provider of the data
        input_collection_id (str): ID of the input collection
        business_ID (str): Business ID
        file_level_attributes (dict): File level attributes
        fips_code (str): FIPS code
        input_properties (str): Input properties key name
        bbox (dict): Bounding box information
        geometry (dict): Geometry information
        
    Returns:
        list: Updated feature_scores with certificate_generated information
    """
    # get length of feature_scores
    length_feature_scores = len(feature_scores)
    
    try:
        # verify the feature_scores & features lengths match
        if len(feature_scores) != len(features):
            raise ValueError(f"Length mismatch: feature_scores has {len(feature_scores)} elements while features has {len(features)} elements")

        # use certificate_type to determine how many certificates to generate
        if "diag" in certificate_type.lower(): 
            certs_to_generate = 2
        else: 
            certs_to_generate = length_feature_scores
        
        # ------------ STEP THROUGH EACH feature_score and build cis_json ----------
        logger.info(f".. now processing {certs_to_generate}/{len(feature_scores)} records...") 
         
        for index in range(certs_to_generate): # Process all features (real mode)
            
            feature_score = feature_scores[index]
            # Extract data from feature_score
            try:
                # get current feature properties dictionary
                properties_element = features[index]['properties']
                
                # set planting_ID & certificates_ID's 
                planting_ID = properties_element.get('PlantingId', 'N/A')
                certificate_ID = f"{certificate_type}-{planting_ID}"
        
                # --- Fetch the Millpont uniquiness ID ----------------------------
                millpont_ID = generate_32bit_id()
                
                # --- now begin building the new certificate JSON object ----------
                cis_json = { 
                    "Data Type": "CI Score",
                    "Certificate Type": certificate_type,
                    "certificate_value": get_score(feature_score['cert_value'], "cert_value"),
                    "CIS_ID": certificate_ID,
                    "Crop": properties_element.get('Crop', 'N/A'),
                    "Season": season,
                    "Year": datetime.now().year,
                    "Millpont Key": millpont_ID,
                    "DateTime Created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    "DateTime Expired": "",  
                    "billing_status": "not billed",
                    "owner_Id": "Ravah Carbon",
                    "owner_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Data Provider": data_Provider,
                    "Input CollectionId": input_collection_id,
                    "BusinessId": business_ID,
                    "Attested By 1": file_level_attributes.get('Attested By 1', 'N/A'),
                    "Signature 1": file_level_attributes.get('Signature 1', 'N/A'),
                    "Attested DateTime 1": file_level_attributes.get('Attested DateTime 1', 'N/A'),
                    "Attested By 2": file_level_attributes.get('Attested By 2', 'N/A'), 
                    "Signature 2": file_level_attributes.get('Signature 2', 'N/A'),
                    "Attested DateTime 2": file_level_attributes.get('Attested DateTime 2', 'N/A'),
                    "FarmId": properties_element.get('FarmId', 'N/A'),
                    "FieldId": properties_element.get('FieldId', 'N/A'),
                    "PlantingId": planting_ID,
                    "Country": file_level_attributes.get('Country','United States'),
                    "State": properties_element.get('State', 'N/A'),
                    "County": properties_element.get('County', 'N/A'),
                    "FIPS Code": fips_code,
                    "Centroid": get_score(feature_score['crop_scores'], "centroid"),
                    "UOM": {
                        "Farm Size": "Acres",  
                        "Crop Area": "Acres",  
                        "Yield": "Bushels/Acre",
                        "Average Crop Price": "U$",  
                        "Crop Value": "U$",  
                        "Certificate Value": "U$", 
                        "Score A": "g GHG/Bu",  
                        "Score B": "g GHG/MJ",  
                        "Score C": "ton GHG",
                        "Energy": "g GHG per Bu",
                        "Nitrogen Fertilizer": "g GHG/Bu",
                        "N2O Emissions": "g GHG/Bu",
                        "CO2 Emissions": "g GHG/Bu",
                        "CH4 Emissions": "g GHG/Bu",
                        "Other Chemicals": "g GHG/Bu",
                        "CI Score Total": "g GHG/MJ",
                        "Default SOC": "g GHG/MJ",
                        "Nutrients": "Pounds/Acre",
                        "Cover Crop Energy": "BTU",
                        "Cover Crop Yield": "Tons/Acre",
                        "Cover Crop Herbicide": "grams/Acre",
                        "Herbicide": "grams/Acre",
                        "Insecticide": "grams/Acre",
                        "Diesel": "Gallons/Acre",
                        "Gasoline": "Gallons/Acre",
                        "Natural Gas": "Cubic Feet/Acre",
                        "LPG": "Gallons/Acre",
                        "Electricity": "Kilowatt-hour (kWh)",
                        "Manure": "Tons/Acre",
                        "Manure Application Energy": "BTU",
                        "Manure Transportation Distance": "Miles",
                        "Manure Transportation Energy": "BTU/Tons/Mile",
                        "Reduction In Fertilizer": "%"
                    },
                    "Crop Area": properties_element.get('Crop Area', 'N/A'),
                    "Yield": properties_element.get('Yield', 'N/A'),
                    "Bushel Amount": get_score(feature_score['crop_scores'], "bushel_Amount"),
                    "Average Crop Price": properties_element.get('Average Crop Price', 6.01),
                    "Crop Value": get_score(feature_score['crop_scores'], "crop_Value"),
                    "GREET Default Score A": get_score(feature_score['default_scores'], "default_ScoreA"),
                    "GREET Default Score B": get_score(feature_score['default_scores'], "default_ScoreB"),
                    "CI Score A": get_score(feature_score['crop_scores'], "CI_Score_A"),
                    "CI Score B": get_score(feature_score['crop_scores'], "CI_Score_B"),
                    "CI Score C": get_score(feature_score['crop_scores'], "CI_Score_C"),
                    "GREET Default Scoring Elements": {
                        "Energy": get_score(feature_score['default_scores'], "default_Result_Energy"),
                        "Nitrogen Fertilizer": get_score(feature_score['default_scores'], "default_Result_NitrogenFertilizer"),
                        "N2O Emissions": get_score(feature_score['default_scores'], "default_Result_N2O_Emissions"),
                        "CO2 Emissions": get_score(feature_score['default_scores'], "default_Result_CO2_Emissions"),
                        "CH4 Emissions": get_score(feature_score['default_scores'], "default_Result_CH4_Emissions"),
                        "Other Chemicals": get_score(feature_score['default_scores'], "default_Result_OtherChemicals"),
                        "CI Score Total": get_score(feature_score['default_scores'], "default_CI_Total"),
                        "Default SOC": get_score(feature_score['default_scores'], "default_SOC"),
                    },
                    "Crop Scoring Elements": {
                        "Energy": get_score(feature_score['crop_scores'], "crop_Result_Energy"),
                        "Nitrogen Fertilizer": get_score(feature_score['crop_scores'], "CI_Score_NitrogenFertilizer"),
                        "N2O Emissions": get_score(feature_score['crop_scores'], "crop_Result_N2O_Emissions"),
                        "CO2 Emissions": get_score(feature_score['crop_scores'], "crop_Result_CO2_Emissions"),
                        "CH4 Emissions": get_score(feature_score['crop_scores'], "crop_Result_CH4_Emissions"),
                        "Other Chemicals": get_score(feature_score['crop_scores'], "crop_Result_OtherChemicals"),
                        "CI Score Total": get_score(feature_score['crop_scores'], "CI_Score_Total"),
                        "Crop SOC": get_score(feature_score['crop_scores'], "crop_SOC"),
                    },
                    input_properties: properties_element,
                    "bbox": bbox,
                    "geometry": geometry,
                    "GeoJSON": {
                        "type": "FeatureCollection",  
                        "features": [features[index]]
                    }  
                }
                
                # Save certificate to file
                name = f"{certificate_ID}.json"
                with open(name, 'w') as f:
                    json.dump(cis_json, f, indent=2)
                logger.info(f"File should be saved as: {name}")
                
                # Add certificate ID to feature_scores for reference in section 6
                feature_scores[index]["certificate_generated"] = certificate_ID
                
            except IndexError:
                logger.error(f"Error: Could not access index {index} in features list")
                break
                
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    
    return feature_scores