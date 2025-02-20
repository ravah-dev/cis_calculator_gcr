# feature_scores_processor.py

# =======================================================================
    # =========== SECTION 6 agC Results Collection ==========================
    # --- uses feature_scores array to build the agC ResultsCollection
    # Section 6 - Build the agC ResultsCollection

from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)

def get_score(scores_list, key_name):
    """Helper function to find a score value from the nested list structure."""
    for item in scores_list:
        if item[0] == key_name:
            # if the value is a float, round to 2 decimal places else return as is
            if isinstance(item[2], float):
                return round(item[2], 2)
            return item[2]
    return None

def create_feature_scores_collection(
    feature_scores, 
    input_collection_id, 
    generate_certificates, 
    certificate_type=None
):
    """
    Generates a collection object from feature scores.
    
    Args:
        feature_scores (list): List of feature score dictionaries
        input_collection_id (str): Collection ID for the dataset
        generate_certificates (bool): Flag indicating if certificates were generated
        certificate_type (str): Type of certificate generated (if any)
        
    Returns:
        dict: Structured JSON data for the results collection
    """
    # Create JSON structure for agC ResultsCollection
    json_structure = {
        "Data Type": "ResultsCollection",
        "Collection ID": input_collection_id,
        "Date of Creation": datetime.now().strftime("%Y-%m-%d"),
        "Data Provider": "agCommander",
        "Generate Certificates": generate_certificates,
        "UOM": {
            "Average Crop Price": "U$",
            "Crop Value": "U$",
            "Carbon Intensity Score A": "g GHG per Bu",
            "Carbon Intensity Score B": "g GHG per MJ",
            "Farm Size": "Acres",
            "Crop Area": "Acres",
            "Yield": "Bushels/Acre"
        },
        "Data": []
    }
    
    # Process each feature score
    # - convert individual score information to json_structure
    for feature_score in feature_scores:
        planting_id = feature_score.get('planting_id')
        
        data_entry = {
            "Planting ID": planting_id,
            "Crop": feature_score.get('crop'),
            "Default Scores": {
                "Energy": get_score(feature_score['default_scores'], "default_Result_Energy"),
                "Nitrogen Fertilizer": get_score(feature_score['default_scores'], "default_Result_NitrogenFertilizer"),
                "N2O Emissions": get_score(feature_score['default_scores'], "default_Result_N2O_Emissions"),
                "CO2 Emissions": get_score(feature_score['default_scores'], "default_Result_CO2_Emissions"),
                "CH4 Emissions": get_score(feature_score['default_scores'], "default_Result_CH4_Emissions"),
                "Other Chemicals": get_score(feature_score['default_scores'], "default_Result_OtherChemicals"),
                "CI Score Total": get_score(feature_score['default_scores'], "default_CI_Total"),
                "Default SOC": get_score(feature_score['default_scores'], "default_SOC"),
                "GREET Default Score A": get_score(feature_score['default_scores'], "default_ScoreA"),
                "GREET Default Score B": get_score(feature_score['default_scores'], "default_ScoreB")
            },
            "Crop Scores": {
                "Energy": get_score(feature_score['crop_scores'], "crop_Result_Energy"),
                "Nitrogen Fertilizer": get_score(feature_score['crop_scores'], "CI_Score_NitrogenFertilizer"),
                "N2O Emissions": get_score(feature_score['crop_scores'], "crop_Result_N2O_Emissions"),
                "CO2 Emissions": get_score(feature_score['crop_scores'], "crop_Result_CO2_Emissions"),
                "CH4 Emissions": get_score(feature_score['crop_scores'], "crop_Result_CH4_Emissions"),
                "Other Chemicals": get_score(feature_score['crop_scores'], "crop_Result_OtherChemicals"),
                "CI Score Total": get_score(feature_score['crop_scores'], "CI_Score_Total"),
                "Crop SOC": get_score(feature_score['crop_scores'], "crop_SOC"),
                "CI Score A": get_score(feature_score['crop_scores'], "CI_Score_A"),
                "CI Score B": get_score(feature_score['crop_scores'], "CI_Score_B")
            },
            "Corn N2O Emission cell C37 comparators": {
                "Crop Nitrogen Management": get_score(feature_score['crop_scores'], "nitrogenManagementCorn"),
                "Fertilizer Rate Type": get_score(feature_score['crop_scores'], "fertilizerRateTypeCorn"),
                "C37Scenario": get_score(feature_score['crop_scores'], "C37Scenario"),
                "N2O emission CI": get_score(feature_score['crop_scores'], "crop_N2OEmission_CI"),
                "N2O emission CI BAU": get_score(feature_score['crop_scores'], "crop_N2OEmission_CI_BAU"),
                "N2O emission CI enhanced efficiency": get_score(feature_score['crop_scores'], "crop_N2OEmission_CI_EE")
            }
        }
        
        # If certificates were generated, add certificate information
        if generate_certificates:
            # Check if this feature_score has a certificate_generated field
            if 'certificate_generated' in feature_score:
                certificate = {
                    "Certificate ID": feature_score['certificate_generated'],
                    "Certificate Type": certificate_type,
                    "Date Created": datetime.now().strftime("%Y-%m-%d")
                }
                data_entry["Certificate"] = certificate
        
        # Add the entry to the data array
        json_structure["Data"].append(data_entry)
    
    return json_structure
