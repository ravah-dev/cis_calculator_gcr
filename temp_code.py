"""_summary_
----------------------------------------------------------------------
temp_code.py is a holding file for refactoring the 'cis_calculator.py'
----------------------------------------------------------------------
"""

# =======================================================================
        # =========== SECTION 6 agC Results Collection ==========================
        # --- uses feature_scores array to build the agC ResultsCollection
        # Section 6 - Build the agC ResultsCollection
        # needs:
        # - import json
        # - from datetime import datetime

        def generate_feature_scores_json(feature_scores, input_collection_id):
            """
            Generates a JSON object from feature scores and saves it to a file.
            
            Args:
                feature_scores (list): List of feature score dictionaries
                input_input_collection_id (str): Collection ID for the dataset
                
            Returns:
                str: Path to the saved JSON file
            """
            # FUNCTION get_score() - Helper function
            def get_score(scores_list, key_name):
                """Helper function to find a score value from the nested list structure"""
                for item in scores_list:
                    if item[0] == key_name:
                        # if the value is a float, round to 2 decimal places else return as is
                        if isinstance(item[2], float):
                            return round(item[2], 2)
                        return item[2]
                return None

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
            
            # if generate_certs bool true, feature_score contains certificate info
            # - add cert info to json_structure
            if generate_certs:
                cert_info = {
                    "Certificate Generated": feature_score.get('certificate_generated'),
                    "Certificate Type": feature_score.get('certificate_type')
                }
                json_structure['Data'].append(cert_info)
            
            # Process each feature score
            # - convert individual score information to json_structure
            for feature_score in feature_scores:
                data_entry = {
                    "Planting ID": feature_score.get('planting_id'),
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
                if generate_certs:
                    certificate = {
                        "Certificate ID": f"CIS-{planting_ID}",
                        "Certificate Type": certificate_type,
                        "Date Created": datetime.now().strftime("%Y-%m-%d")
                    }
                    data_entry["Certificate"] = certificate
                json_structure["Data"].append(data_entry)
            
            # ---- TESTING: PRINT FORMATTED FEATURE SCORES ***************
            # Example: Generate filename with input collection ID
            # filename = f"feature_scores_{input_collection_id}.json"
            
            # Save to file with nice formatting
            # with open(filename, 'w') as f:
            #     json.dump(json_structure, f, indent=2)
            
            # return filename
            # ---- END TESTING: PRINT FORMATTED FEATURE SCORES ***************
            
            return json_structure

        # **** USE FOR TESTING ONLY - DON'T RUN IN PRODUCTION ---------------------
        # output_file = generate_feature_scores_json(feature_scores, input_collection_id)
        # logger.info(f"File should be saved as: {output_file}")
        
        # =========== END Section 6 Build the agC Results Collection ======================