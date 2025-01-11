# ******** ci_calculator.py draft 2 ***********
# taken from 'CI_Calculator_2.ipynb' steps 2 thru 10
# note: the original syntax uses json to import a json file with input data
# This version is set up as a function that can be imported by other scripts
# The function 'calculate_ci' takes two arguments:
# - data: a dictionary containing the input data
# - global_variables: a dictionary containing global variables

# ----- this file import section is deprecated and replaced by input arguments -----
# import json
# # Load the JSON file
# file_path = 'agCommander-US-Carbon_Oct-10.json'
# with open(file_path, 'r') as file:
#     data = json.load(file)

# ----- imports for Step 3 --------------------
from class_import_greet_defaults import GREETDefaults
import pandas as pd

# ----- imports for Step 4  --------------------
from class_state_to_abbr import StateNameToAbbr
from class_fips_lookup import FIPSLookup # for step 5 of calculator

# ----- imports for Steps 5 & 6  --------------------
import json
from datetime import datetime

globals_initialized = False

# =========== DEFINE THE CALCULATOR FUNCTION =================================
def calculator_function(data, global_variables, logger, soc):
    """
    Perform calculations using the input data and global reference variables.

    Args:
        data (dict): Input data from the POST request.
        global_variables (dict): Dictionary of global variables.

    Returns:
        dict: Calculation results.
    """
    global globals_initialized, state_name_to_code, fips_lookup, greet

    # ================== Section 2 ========================
    # Initialize GREET Reference globals only once
    if not globals_initialized:
        for var_name, value in global_variables.items():
            globals()[var_name] = value
        globals_initialized = True
        
        # FIX Herbicide_CI value which is reading incorrectly from the Excel file
        # The value in the Excel file is 29.52011704, but somehow it's reading 25.29087007
        # -- SEE "'Intensities of Inputs'!D107" -- 29.52 
        # Set the correct value
        globals()["Herbicide_CI"] = 29.52011704
        logger.info(f"Herbicide_CI changed to: {Herbicide_CI}")
          
        # Initialize the StateConverter class
        state_name_to_code = StateNameToAbbr()
        
        # Initialize the FIPSLookup class
        fips_lookup = FIPSLookup()
        fips_lookup.load_data()

        # Initialize the GREET defaults manager
        logger.info("Initializing GREET Defaults Manager...")
        greet = GREETDefaults('GREET_Defaults.csv')

    # calculation logic using global variables
    try:
        # ================== Section 3 Read Input Data ==================
        # - decompose the dictionary passed in as 'data
        #  & extract all feature properties to variables
        
        length_of_features = len(data['GeoJSON']['features']) # used for reporting later
        # logger.info(f"calc line 68 length_of_features: {length_of_features}") # debugging purpose
        
        # Extract the first 1st level properties as file-level properties
        # - assumes geoJSON is always the last property
        elements_in_data = len(data)
        file_level_attributes = {key: data[key] for key in list(data.keys())[:(elements_in_data-1)]}

        # Extract the 'data_provider' property from file-level attributes
        data_Provider = file_level_attributes.get('Data Provider', 'agCommander')

        # Extract the 'Generate Certificates' property from file-level attributes
        # - initialize 'generate_certs' boolean
        generate_certificates = file_level_attributes.get('Generate Certificates', 'No')
        if generate_certificates.lower() in ('yes', 'true'): 
            generate_certs = True
        if generate_certificates.lower() in ('no', 'false'): 
            generate_certs = False

        # extract the 'Certificate Type' property from file-level attributes
        certificate_type = file_level_attributes.get('Certificate Type', 'TEST')

        # extract the UOM properties
        uom_properties = file_level_attributes.get('UOM', 'N/A')
        
        # Extracting the value for "Reduction In Fertilizer"
        fertilizer_reduction_units = uom_properties[0]["Reduction In Fertilizer"]

        # assign 'input_collection_id' variable from file-level attributes for testing
        collection_ID = file_level_attributes.get('CollectionId', 'test_collection_1') # <-- need to be replaced with actual implementation

        # Assign 'season' variable from file-level attributes for testing
        #  - season should be type str or int with current year (2024)
        season = str(file_level_attributes.get('Season', '2024')) # <-- make sure it's a string

        # Extract the 'features' array from the GeoJSON object
        features = data['GeoJSON']['features']


        # ================== Section 4 Process Features Array =========================
        # ----------------- PROCESSING EACH FEATURE ONE BY ONE ----------------
                
        # Section 4 Process features array
        logger.info(f"line 119 Processing {len(features)} features")

        # Initialize the 'feature_scores' array
        feature_scores = []
        bbox = []  # Initialize empty list for coordinates [lat, lng, lat, lng]

        # feature_tested = False  # Placeholder for debugging
        
        # *** Process each feature and assign specified properties to Global variables ***
        for feature in features:
            
            # # Placeholder for debugging 
            # if not feature_tested:
            #     logger.info(f"calc line 122 - feature: {feature}")  # Debug
            #     feature_tested = True
                
            # ------------------ bbox calculation using lat/lng coordinates -------------------------------
            # -- for future reference: the coordinates pairs in the geometry object are in the format [lng, lat]
            try:
                # **** Get the bbox array and initialize a centroid ************
                
                # -- bbox may be in the geometry object or at the feature root level
                # Check if bbox exists at the root level of the feature
                # -- Note: The bbox array at feature root is standard format [lat_min, lng_min, lat_max, lng_max]
                feature_bbox = feature.get("bbox")

                # If not found, check if it exists in the geometry object
                # -- Note: The bbox array in the geometry object is the format [lng_min, lat_min, lng_max, lat_max]
                if feature_bbox is None and "geometry" in feature:
                    feature_bbox = feature["geometry"].get("bbox")
                    if feature_bbox[0] < 1:
                        # Convert from [lng_min, lat_min, lng_max, lat_max] to [lat_min, lng_min, lat_max, lng_max]
                        feature_bbox = [feature_bbox[1], feature_bbox[0], feature_bbox[3], feature_bbox[2]]
            
                # Only process if we got a valid bbox
                if feature_bbox and len(feature_bbox) == 4:                        
                    bbox = list(feature_bbox)  # Create a copy of bbox (clear & extend combined)
                    
                    # Calculate centroid if bbox is valid
                    lngA, lngB = bbox[1], bbox[3]  # Longitude bounds
                    latA, latB = bbox[0], bbox[2]  # Latitude bounds
                    
                    # Compute centroid [lat, lng] and round to 5 decimal places
                    centroid = [
                        round((latA + latB) / 2, 5),
                        round((lngA + lngB) / 2, 5)
                    ]
                    # logger.info(f"centroid: {centroid}")  # Debug
                else:
                    # Handle invalid bbox
                    centroid = []  # Clear centroid if bbox is invalid
                    logger.warning(f"Warning: Invalid bbox data in feature: {feature_bbox}")

            except (KeyError, IndexError, TypeError) as e:
                # Handle specific exceptions
                logger.error(f"Error processing feature: {str(e)}")
                centroid = []

            # Assign crop-specific feature properties to Global variables
            business_ID = feature['properties'].get('BusinessId', 'N/A')
            farmName = feature['properties'].get('Farm Name', 'N/A')
            farm_ID = feature['properties'].get('FarmId', 'N/A')
            field_ID = feature['properties'].get('FieldId', 'N/A')
            FSA_FarmNumber = feature['properties'].get('FSA Farm Number', 'N/A')
            FSA_TractNumber = feature['properties'].get('FSA Tract Number', 'N/A')
            FSA_FieldNumber = feature['properties'].get('FSA Field Number', 'N/A')
            field_ID = feature['properties'].get('FieldId', 'N/A')
            planting_ID = feature['properties'].get('PlantingId', 'N/A')
            farmSize = feature['properties'].get('Farm Size', 1)
            county = feature['properties'].get('County', 'N/A')
            state = feature['properties'].get('State', 'N/A')
            climateZoneCorn = feature['properties'].get('Climate Zone', 'N/A')
            crop = feature['properties'].get('Crop', 'N/A')
            crop_area = feature['properties'].get('Crop Area', 1)
            crop_tillage = feature['properties'].get('Tillage', 'N/A')
            crop_yield = feature['properties'].get('Yield', 1)
            # - note: need Roger to add "Average Crop Price" to JSON
            average_Price = feature['properties'].get('Average Crop Price', 6.01)
            crop_Diesel_Gal = feature['properties'].get('Diesel', 0)
            crop_Gasoline_Gal = feature['properties'].get('Gasoline', 0)
            crop_NaturalGas_Gal = feature['properties'].get('Natural Gas', 0)
            crop_LPG_Ft3 = feature['properties'].get('LPG', 0)
            crop_Electricity_kWh = feature['properties'].get('Electricity', 0)
            crop_Urea_Lbs = feature['properties'].get('Urea', 0)
            crop_Ammonia_Lbs = feature['properties'].get('Ammonia', 0)
            crop_AmmoniumSulfate_Lbs = feature['properties'].get('Ammonium Sulfate', 0)
            crop_AmmoniumNitrate_Lbs = feature['properties'].get('Ammonium Nitrate', 0)
            crop_UAN_Lbs = feature['properties'].get('Urea-ammonium Nitrate Solution', 0)
            crop_MAP_Lbs = feature['properties'].get('Monoammonium Nitrate', 0)
            crop_DAP_Lbs = feature['properties'].get('Diammonium Nitrate', 0)
            crop_DAP_gN_Bu = feature['properties'].get('Diammonium Phosphate', 0)
            crop_MAP_gN_Bu = feature['properties'].get('Monoammonium Phosphate', 0)
            crop_MAP_P2O5_Lbs_N = feature['properties'].get('Monoammonium Phosphate P2O5', 0)
            crop_DAP_P2O5_Lbs_N = feature['properties'].get('Diammonium Phosphate P2O5', 0)
            crop_K2O_Lbs_N = feature['properties'].get('Potash K2O', 0)
            crop_CaCO3_Lbs_N = feature['properties'].get('Limestone CaCO3', 0)
            crop_Herbicide_g_Acre = feature['properties'].get('Herbicide', 0)
            crop_Insecticide_g_Acre = feature['properties'].get('Insecticide', 0)
            coverCrop = feature['properties'].get('Cover Crop Used', 'N/A').lower()
            coverCrop_Energy_BTU = feature['properties'].get('Cover Crop Energy', 0)
            covercrop_yield = feature['properties'].get('Cover Crop Yield', 1)
            coverCrop_Herbicide_g_Acre = feature['properties'].get('Cover Crop Herbicide', 0)
            manure_Swine_Ton_Acre = feature['properties'].get('Swine Manure', 0)
            manure_Cow_Ton_Acre = feature['properties'].get('Dairy Cow Manure', 0)
            manure_Beef_Ton_Acre = feature['properties'].get('Beef Cattle Manure', 0)
            manure_Chicken_Ton_Acre = feature['properties'].get('Chicken Manure', 0)
            manure_Energy_BTU = feature['properties'].get('Manure Application Energy', 0)
            manure_Dist = feature['properties'].get('Manure Transportation Distance', 0)
            manure_TransportationEnergy_BTU_TonMile = feature['properties'].get('Manure Transportation Energy', 0)
            fertilizerRateTypeCorn = "User specified reduction (%) in fertilizer application rate under 4R"
            reductionPercent_4R = feature['properties'].get('Reduction In Fertilizer', 0)
            ammoniaSource = feature['properties'].get('Ammonia Source', 'N/A')
            nitrogenManagementCorn = feature['properties'].get('Nitrogen Management', 'N/A')
            cropSOC_Tillage = feature['properties'].get('SOC Tillage', 'N/A')
            
            # ***** CLEAN UP CRITICAL VARIABLES *****
            # In case of non-standard crop names convert to known crop values
            valid_crops = {
            "corn": "Corn",
            "soybean": "Soybean",
            "sorghum": "Sorghum",
            "rice": "Rice"
            }
            crop_lower = crop.lower()
            is_valid_crop = False
            for search_term, correct_name in valid_crops.items():
                if search_term in crop_lower:
                    crop = correct_name
                    is_valid_crop = True
                    break
            if not is_valid_crop:
                # raise ValueError(f"Unknown crop: {crop}")
                logger.warning(f"Unknown crop: {crop}")
                break

            # Fix county to make sure it has the word "county"
            county_name = county.strip()
            if not county.lower().endswith("county"):
                county = f"{county} County"
            
            # in case the reduction in fertilizer comes in as whole number, convert it to fraction rate in decimal
            # - this assumes that fertilizer_reduction_percent == "%"
            if reductionPercent_4R > 1: reductionPercent_4R = reductionPercent_4R / 100
            
            # ********************** Section 4-a Get state_code, get fips_code, lookup soc_factor ********************
            state_code = state_name_to_code.get_state_abbr(state)
            # Look up the FIPS code
            fips_code = fips_lookup.get_fips(state_code, county)

            if fips_code:
                # Remove leading zeros by converting to integer and back to string
                fips_code = str(int(fips_code))
                # logger.info(f"FIPS code for {county}, {state_code}: {fips_code}") # For debugging
            else:
                logger.warning(f"No FIPS code found for {county}, {state}")
            
            # *********** Section 4-b Initialize computed GREET reference metrics *********************
            # Create GREET model vars dependent on crop input parameters
            manureUsed = "Manure" if manure_Swine_Ton_Acre > 0 or manure_Cow_Ton_Acre > 0 or manure_Beef_Ton_Acre > 0 or manure_Chicken_Ton_Acre > 0 else "No manure"
            Manure_Total_Applied = manure_Swine_Ton_Acre + manure_Cow_Ton_Acre + manure_Beef_Ton_Acre + manure_Chicken_Ton_Acre
            GWP_N2O_N = N2O_N_To_N2O * N2O_GWP
            
            # *********** Section 4-c Import GREET default reference values *********************
            # --- note: THIS SECTION IS CROP-DEPENDENT SO MUST BE PART OF THE CROP-SPECIFIC SECTIONS.
            def initialize_global_vars(vars_dict: dict, prefix: str = ''):
                """
                Initialize global variables from a dictionary.
                
                Parameters:
                    vars_dict (dict): Dictionary of variable names and values
                    prefix (str): Optional prefix for variable names
                """
                # Get IPython's global namespace if available, otherwise use globals()
                try:
                    from IPython import get_ipython
                    globals_dict = get_ipython().user_ns
                except (ImportError, AttributeError):
                    globals_dict = globals()
                
                # Create global variables using the exact name from the dictionary
                for var_name, value in vars_dict.items():
                    globals_dict[var_name] = value
                    
                # logger.info the created global variables for testing
                # logger.info(f"Created global variables: {', '.join(vars_dict.keys())}")

            # Call the GREET defaults manager to load crop-based defaults
            crop_vars = greet.get_crop_defaults(crop)

            # Initialize global variables passing in the corn_vars dict
            initialize_global_vars(crop_vars)

            # Initialize cover crop and manure driven GREET defaults values
            # Normalize values to lowercase for consistent comparison
            coverCrop = coverCrop.lower()
            manureUsed = manureUsed.lower()

            default_coverCrop_Energy_BTU_Acre = 0 if coverCrop == "no cover crop" else 62060
            default_coverCrop_Herbicide_g_Acre = 0 if coverCrop == "no cover crop" else 612.3496995
            default_covercrop_yield_Ton_Acre = 0 if coverCrop == "no cover crop" else 1.21405880091459
            default_Manure_Swine_Ton_Acre = 0 if manureUsed == "no manure" else 7.854 * 0.243
            default_Manure_Cow_Ton_Acre = 0 if manureUsed == "no manure" else 7.854 * 0.423
            default_Manure_Beef_Ton_Acre = 0 if manureUsed == "no manure" else 7.854 * 0.216
            default_Manure_Chicken_Ton_Acre = 0 if manureUsed == "no manure" else 7.854 * 0.119
            default_Manure_Energy_BTU = 0 if manureUsed == "no manure" else 221365.589648777
            default_Manure_Dist = 0 if manureUsed == "no manure" else 0.367
            default_Manure_TransportationEnergy_BTU_TonMile = 0 if manureUsed == "no manure" else 10416.49299
            
            # *********** START SECTION 4-d Compute Intermediate metrics ********************
            # creates the (global) intermediate variables 
            #   - converts farm input metrics (units per acre) to units per bushel
            #   - loads into crop_intermediates[] and default_intermediates[] arrays for scoring

            crop_intermediates = []
            default_intermediates = []

            # SOC Emissions metrics (F80 & G80)
            cropSOC_Emissions = soc.get_soc_factor(fips_code, crop, coverCrop, manureUsed, cropSOC_Tillage)
            cropSOC_Emission = -cropSOC_Emissions if isinstance(cropSOC_Emissions, float) else ""
            crop_intermediates.append(('cropSOC_Emissions', 'F80', cropSOC_Emissions))

            default_SOC_Emissions = soc.get_soc_factor(fips_code, crop, coverCrop, manureUsed, cropSOC_Tillage)
            default_SOC_Emission = -default_SOC_Emissions if isinstance(default_SOC_Emissions, float) else ""
            default_intermediates.append(('default_SOC_Emissions', 'G80', default_SOC_Emissions))

            # Crop Energy metrics (L13-L17
            crop_Diesel_BTU_Bu = crop_Diesel_Gal * Diesel_BTU2gal / crop_yield
            crop_intermediates.append(('crop_Diesel_BTU_Bu', 'L13', crop_Diesel_BTU_Bu))

            crop_Gasoline_BTU_Bu = crop_Gasoline_Gal * Gasoline_BTU2gal / crop_yield
            crop_intermediates.append(('crop_Gasoline_BTU_Bu', 'L14', crop_Gasoline_BTU_Bu))

            crop_NaturalGas_BTU_Bu = crop_NaturalGas_Gal * Natural_gas_BTU2ft3 / crop_yield
            crop_intermediates.append(('crop_NaturalGas_BTU_Bu', 'L15', crop_NaturalGas_BTU_Bu))

            crop_LPG_BTU_Bu = crop_LPG_Ft3 * LPG_BTU2gal / crop_yield
            crop_intermediates.append(('crop_LPG_BTU_Bu', 'L16', crop_LPG_BTU_Bu))

            crop_Electricity_BTU_Bu = crop_Electricity_kWh * Electricity_BTU2kWh / crop_yield
            crop_intermediates.append(('crop_Electricity_BTU_Bu', 'L17', crop_Electricity_BTU_Bu))

            # Crop Fertilizer metrics (L22-L28)
            crop_Ammonia_gN_Bu = crop_Ammonia_Lbs * g_to_lb / crop_yield
            crop_intermediates.append(('crop_Ammonia_gN_Bu', 'L22', crop_Ammonia_gN_Bu))

            crop_Urea_gN_Bu = crop_Urea_Lbs * g_to_lb / crop_yield
            crop_intermediates.append(('crop_Urea_gN_Bu', 'L23', crop_Urea_gN_Bu))

            crop_AmmoniumNitrate_gN_Bu = crop_AmmoniumNitrate_Lbs * g_to_lb / crop_yield
            crop_intermediates.append(('crop_AmmoniumNitrate_gN_Bu', 'L24', crop_AmmoniumNitrate_gN_Bu))

            crop_AmmoniumSulfate_gN_Bu = crop_AmmoniumSulfate_Lbs * g_to_lb / crop_yield
            crop_intermediates.append(('crop_AmmoniumSulfate_gN_Bu', 'L25', crop_AmmoniumSulfate_gN_Bu))

            crop_UAN_gN_Bu = crop_UAN_Lbs * g_to_lb / crop_yield
            crop_intermediates.append(('crop_UAN_gN_Bu', 'L26', crop_UAN_gN_Bu))

            crop_MAP_gN_Bu = crop_MAP_Lbs * g_to_lb / crop_yield
            crop_intermediates.append(('crop_MAP_gN_Bu', 'L27', crop_MAP_gN_Bu))

            crop_DAP_gN_Bu = crop_DAP_Lbs * g_to_lb / crop_yield
            crop_intermediates.append(('crop_DAP_gN_Bu', 'L28', crop_DAP_gN_Bu))

            # Calculate total nitrogen (L29)
            crop_Total_N_gN_Bu = (crop_Ammonia_gN_Bu + crop_Urea_gN_Bu + 
                                crop_AmmoniumNitrate_gN_Bu + crop_AmmoniumSulfate_gN_Bu + 
                                crop_UAN_gN_Bu + crop_MAP_gN_Bu + crop_DAP_gN_Bu)
            crop_intermediates.append(('crop_Total_N_gN_Bu', 'L29', crop_Total_N_gN_Bu))

            # Crop Phosphorus metrics (L31-L32)
            crop_MAP_P2O5_gP_Bu = crop_MAP_P2O5_Lbs_N * g_to_lb / crop_yield
            crop_intermediates.append(('crop_MAP_P2O5_gP_Bu', 'L31', crop_MAP_P2O5_gP_Bu))

            crop_DAP_P2O5_gP_Bu = crop_DAP_P2O5_Lbs_N * g_to_lb / crop_yield
            crop_intermediates.append(('crop_DAP_P2O5_gP_Bu', 'L32', crop_DAP_P2O5_gP_Bu))

            # Additional nutrients (L35-L44)
            crop_K2O_g_Bu = crop_K2O_Lbs_N * g_to_lb / crop_yield
            crop_intermediates.append(('crop_K2O_g_Bu', 'L35', crop_K2O_g_Bu))

            crop_CaCO3_g_Bu = crop_CaCO3_Lbs_N * g_to_lb / crop_yield
            crop_intermediates.append(('crop_CaCO3_g_Bu', 'L38', crop_CaCO3_g_Bu))

            crop_Herbicide_g_Bu = crop_Herbicide_g_Acre / crop_yield
            crop_intermediates.append(('crop_Herbicide_g_Bu', 'L41', crop_Herbicide_g_Bu))

            crop_Insecticide_g_Bu = crop_Insecticide_g_Acre / crop_yield
            crop_intermediates.append(('crop_Insecticide_g_Bu', 'L44', crop_Insecticide_g_Bu))

            # Cover crop metrics (L50-L52)
            if coverCrop == "cover crop":
                # Calculate metrics when cover crop is present
                coverCrop_Energy_BTU_Bu = coverCrop_Energy_BTU / covercrop_yield
                coverCrop_Herbicide_g_Bu = coverCrop_Herbicide_g_Acre / covercrop_yield
                coverCropN_gN_Bu = covercrop_yield * Rye_Ninbiomass_ResidueFactor / crop_yield
            else:
                # Initialize variables to 0 when no cover crop
                coverCrop_Energy_BTU_Bu = 0
                coverCrop_Herbicide_g_Bu = 0
                coverCropN_gN_Bu = 0

            # Append cover crop results to crop_intermediates
            crop_intermediates.append(('coverCrop_Energy_BTU_Bu', 'L50', coverCrop_Energy_BTU_Bu))
            crop_intermediates.append(('coverCrop_Herbicide_g_Bu', 'L51', coverCrop_Herbicide_g_Bu))
            crop_intermediates.append(('coverCropN_gN_Bu', 'L52', coverCropN_gN_Bu))

            # Manure metrics (L59-L67)
            manure_Swine_N_gN_Bu = manure_Swine_Ton_Acre * ton2g / crop_yield
            crop_intermediates.append(('manure_Swine_N_gN_Bu', 'L59', manure_Swine_N_gN_Bu))

            manure_Cow_N_gN_Bu = manure_Cow_Ton_Acre * ton2g / crop_yield
            crop_intermediates.append(('manure_Cow_N_gN_Bu', 'L60', manure_Cow_N_gN_Bu))

            manure_Beef_N_gN_Bu = manure_Beef_Ton_Acre * ton2g / crop_yield
            crop_intermediates.append(('manure_Beef_N_gN_Bu', 'L61', manure_Beef_N_gN_Bu))

            manure_Chicken_N_gN_Bu = manure_Chicken_Ton_Acre * ton2g / crop_yield
            crop_intermediates.append(('manure_Chicken_N_gN_Bu', 'L62', manure_Chicken_N_gN_Bu))

            manure_TotalTons_Acre = manure_Swine_Ton_Acre + manure_Cow_Ton_Acre + manure_Beef_Ton_Acre + manure_Chicken_Ton_Acre
            crop_intermediates.append(('manure_TotalTons_Acre', 'computed', manure_TotalTons_Acre))

            manure_Energy_BTU_Bu = manure_Energy_BTU / crop_yield
            crop_intermediates.append(('manure_Energy_BTU_Bu', 'L64', manure_Energy_BTU_Bu))

            manure_TransportationEnergy_BTU_Bu = (manure_TransportationEnergy_BTU_TonMile * 
                                            manure_TotalTons_Acre * manure_Dist / crop_yield)
            crop_intermediates.append(('manure_TransportationEnergy_BTU_Bu', 'L67', manure_TransportationEnergy_BTU_Bu))


            # ***************** START DEFAULT Intermediate Vars SECTION **************************
            # Default Energy metrics (M13-M17)
            default_Diesel_BTU_Bu = default_Diesel_Gal * Diesel_BTU2gal / default_Yield
            default_intermediates.append(('default_Diesel_BTU_Bu', 'M13', default_Diesel_BTU_Bu))

            default_Gasoline_BTU_Bu = default_Gasoline_Gal * Gasoline_BTU2gal / default_Yield
            default_intermediates.append(('default_Gasoline_BTU_Bu', 'M14', default_Gasoline_BTU_Bu))

            default_NaturalGas_BTU_Bu = default_NaturalGas_Gal * Natural_gas_BTU2ft3 / default_Yield
            default_intermediates.append(('default_NaturalGas_BTU_Bu', 'M15', default_NaturalGas_BTU_Bu))

            default_LPG_BTU_Bu = default_LPG_Ft3 * LPG_BTU2gal / default_Yield
            default_intermediates.append(('default_LPG_BTU_Bu', 'M16', default_LPG_BTU_Bu))

            default_Electricity_BTU_Bu = default_Electricity_kWh * Electricity_BTU2kWh / default_Yield
            default_intermediates.append(('default_Electricity_BTU_Bu', 'M17', default_Electricity_BTU_Bu))

            # Default Fertilizer metrics (M22-M28)
            default_Ammonia_gN_Bu = default_Ammonia_Lbs * g_to_lb / default_Yield
            default_intermediates.append(('default_Ammonia_gN_Bu', 'M22', default_Ammonia_gN_Bu))

            default_Urea_gN_Bu = default_Urea_Lbs * g_to_lb / default_Yield
            default_intermediates.append(('default_Urea_gN_Bu', 'M23', default_Urea_gN_Bu))

            default_AmmoniumNitrate_gN_Bu = default_AmmoniumNitrate_Lbs * g_to_lb / default_Yield
            default_intermediates.append(('default_AmmoniumNitrate_gN_Bu', 'M24', default_AmmoniumNitrate_gN_Bu))

            default_AmmoniumSulfate_gN_Bu = default_AmmoniumSulfate_Lbs * g_to_lb / default_Yield
            default_intermediates.append(('default_AmmoniumSulfate_gN_Bu', 'M25', default_AmmoniumSulfate_gN_Bu))

            default_UAN_gN_Bu = default_UAN_Lbs * g_to_lb / default_Yield
            default_intermediates.append(('default_UAN_gN_Bu', 'M26', default_UAN_gN_Bu))

            default_MAP_gN_Bu = default_MAP_Lbs * g_to_lb / default_Yield
            default_intermediates.append(('default_MAP_gN_Bu', 'M27', default_MAP_gN_Bu))

            default_DAP_gN_Bu = default_DAP_Lbs * g_to_lb / default_Yield
            default_intermediates.append(('default_DAP_gN_Bu', 'M28', default_DAP_gN_Bu))

            # Calculate total nitrogen (M29)
            default_Total_N_gN_Bu = (default_Ammonia_gN_Bu + default_Urea_gN_Bu + 
                                default_AmmoniumNitrate_gN_Bu + default_AmmoniumSulfate_gN_Bu + 
                                default_UAN_gN_Bu + default_MAP_gN_Bu + default_DAP_gN_Bu)
            default_intermediates.append(('default_Total_N_gN_Bu', 'M29', default_Total_N_gN_Bu))

            # Default Phosphorus metrics (M31-M32)
            default_MAP_P2O5_gP_Bu = default_MAP_P2O5_Lbs_N * g_to_lb / default_Yield
            default_intermediates.append(('default_MAP_P2O5_gP_Bu', 'M31', default_MAP_P2O5_gP_Bu))

            default_DAP_P2O5_gP_Bu = default_DAP_P2O5_Lbs_N * g_to_lb / default_Yield
            default_intermediates.append(('default_DAP_P2O5_gP_Bu', 'M32', default_DAP_P2O5_gP_Bu))

            # Additional nutrients (M35-M44)
            default_K2O_g_Bu = default_K2O_Lbs_N * g_to_lb / default_Yield
            default_intermediates.append(('default_K2O_g_Bu', 'M35', default_K2O_g_Bu))

            default_CaCO3_g_Bu = default_CaCO3_Lbs_N * g_to_lb / default_Yield
            default_intermediates.append(('default_CaCO3_g_Bu', 'M38', default_CaCO3_g_Bu))

            default_Herbicide_g_Bu = default_Herbicide_g_Acre / default_Yield
            default_intermediates.append(('default_Herbicide_g_Bu', 'M41', default_Herbicide_g_Bu))

            default_Insecticide_g_Bu = default_Insecticide_g_Acre / default_Yield
            default_intermediates.append(('default_Insecticide_g_Bu', 'M44', default_Insecticide_g_Bu))

            # Cover default metrics (M50-M52)
            default_coverCrop_Energy_BTU_Bu = default_coverCrop_Energy_BTU_Acre / default_Yield
            default_intermediates.append(('default_coverCrop_Energy_BTU_Bu', 'M50', default_coverCrop_Energy_BTU_Bu))

            default_coverCrop_Herbicide_g_Bu = default_coverCrop_Herbicide_g_Acre / default_Yield
            default_intermediates.append(('default_coverCrop_Herbicide_g_Bu', 'M51', default_coverCrop_Herbicide_g_Bu))

            default_coverCropN_gN_Bu = default_covercrop_yield_Ton_Acre * Rye_Ninbiomass_ResidueFactor
            default_intermediates.append(('default_coverCropN_gN_Bu', 'M52', default_coverCropN_gN_Bu))

            # Manure metrics (M59-M67)
            default_Manure_Swine_N_gN_Bu = default_Manure_Swine_Ton_Acre * ton2g / default_Yield
            default_intermediates.append(('default_Manure_Swine_N_gN_Bu', 'M59', default_Manure_Swine_N_gN_Bu))

            default_Manure_Cow_N_gN_Bu = default_Manure_Cow_Ton_Acre * ton2g / default_Yield
            default_intermediates.append(('default_Manure_Cow_N_gN_Bu', 'M60', default_Manure_Cow_N_gN_Bu))

            default_Manure_Beef_N_gN_Bu = default_Manure_Beef_Ton_Acre * ton2g / default_Yield
            default_intermediates.append(('default_Manure_Beef_N_gN_Bu', 'M61', default_Manure_Beef_N_gN_Bu))

            default_Manure_Chicken_N_gN_Bu = default_Manure_Chicken_Ton_Acre * ton2g / default_Yield
            default_intermediates.append(('default_Manure_Chicken_N_gN_Bu', 'M62', default_Manure_Chicken_N_gN_Bu))

            default_Manure_TotalTons_Acre = (default_Manure_Swine_Ton_Acre + default_Manure_Cow_Ton_Acre + 
                                        default_Manure_Beef_Ton_Acre + default_Manure_Chicken_Ton_Acre)
            default_intermediates.append(('default_Manure_TotalTons_Acre', 'computed', default_Manure_TotalTons_Acre))

            default_Manure_Total_N_gN_Bu = (default_Manure_Swine_N_gN_Bu + default_Manure_Cow_N_gN_Bu + 
                                        default_Manure_Beef_N_gN_Bu + default_Manure_Chicken_N_gN_Bu)
            default_intermediates.append(('default_Manure_Total_N_gN_Bu', 'M64', default_Manure_Total_N_gN_Bu))

            default_Manure_Energy_BTU_Bu = default_Manure_Energy_BTU / default_Yield
            default_intermediates.append(('default_Manure_Energy_BTU_Bu', 'M64', default_Manure_Energy_BTU_Bu))

            default_Manure_TransportationEnergy_BTU_Bu = (default_Manure_TransportationEnergy_BTU_TonMile * 
                                            default_Manure_TotalTons_Acre * default_Manure_Dist / default_Yield)
            default_intermediates.append(('default_Manure_TransportationEnergy_BTU_Bu', 'M67', default_Manure_TransportationEnergy_BTU_Bu))

            # **************** LOG INTERMEDIATE VARIABLES FOR TESTING ***
            # # crop_intermediates: Custom formatting with alignment
            # logger.info(" ")
            # logger.info("============================================")
            # logger.info(" ----- START OF FEATURE SCORE DATA ---------")
            # logger.info("--------------------------------------------")
            # logger.info(f"planting_ID {planting_ID}, crop: {crop}")
            # logger.info("crop_intermediates: Custom formatted table")
            # logger.info(f"{'Variable':<20} {'Cell':<6} {'Value':>10}")
            # logger.info("-" * 38)
            
            # for item in crop_intermediates:
            #     try:
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {float(item[2]):>10.2f}")
            #     except (ValueError, TypeError):
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {str(item[2]):>10}")
                
            # # default_intermediates: Custom formatting with alignment
            # logger.info("------------------------------------------")
            # logger.info(f"planting_ID {planting_ID}, crop: {crop}")
            # logger.info("default_intermediates: Custom formatted table")
            # logger.info(f"{'Variable':<20} {'Cell':<6} {'Value':>10}")
            # logger.info("-" * 38)
            # for item in default_intermediates:
            #     try:
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {float(item[2]):>10.2f}")
            #     except (ValueError, TypeError):
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {str(item[2]):>10}")
            # ************* END OF LOGGING INTERMEDIATE VARIABLES FOR TESTING ***        
            
            # ******* END of Computing Intermediate Variables *******************
            
            
            # =============== START SCORE CALCULATIONS ==========================
            # *************** Section 4-e Compute GREET DEFAULT CI Scores *******
            # load computed scores into default_scores list            
            default_scores = []

            # Normalize values to lowercase for consistent comparison
            coverCrop = coverCrop.lower()
            manureUsed = manureUsed.lower()

            # cell D5
            Diesel_CI_Factor = default_Diesel_BTU_Bu * Diesel_CI
            cc_CI = 0 if coverCrop == "no cover crop" else default_cc_Diesel_BTU_BU * Diesel_CI
            m_CI = 0 if manureUsed == "no manure" else (default_Manure_Energy_BTU_Bu + default_Manure_TransportationEnergy_BTU_Bu) * Diesel_CI
            default_Diesel_CI = Diesel_CI_Factor + cc_CI + m_CI
            default_scores.append(('default_Diesel_CI', 'D5', default_Diesel_CI))

            # cell D6
            default_Gasoline_CI = Gasoline_CI * default_Gasoline_BTU_Bu
            default_scores.append(('default_Gasoline_CI', 'D6', default_Gasoline_CI))

            # cell D7
            default_NaturalGas_CI = NaturalGas_CI * default_NaturalGas_BTU_Bu
            default_scores.append(('default_NaturalGas_CI', 'D7', default_NaturalGas_CI))

            # cell D8
            default_LPG_CI  = LPG_CI * default_LPG_BTU_Bu
            default_scores.append(('default_LPG_CI', 'D8', default_LPG_CI))

            # cell D9
            default_Electricity_CI = Electricity_CI * default_Electricity_BTU_Bu
            default_scores.append(('default_Electricity_CI', 'D9', default_Electricity_CI))

            #cell D12
            ammonia_CI =ConventionalAmmonia_CI / ton2g if ammoniaSource == "Conventional" else GreenAmmonia_CI / ton2g
            default_Ammonia_CI = default_Ammonia_gN_Bu / Ammonia_N_Content * ammonia_CI
            default_scores.append(('default_Ammonia_CI', 'D12', default_Ammonia_CI))

            #cell D13
            urea_CI = ConventionalUrea_CI / ton2g if ammoniaSource == "Conventional" else GreenUrea_CI / ton2g
            default_Urea_CI = default_Urea_gN_Bu / Urea_N_Content * urea_CI
            default_scores.append(('default_Urea_CI', 'D13', default_Urea_CI))

            #cell D14
            ammonium_nitrate_CI = ConventionalAmmoniumNitrate_CI / ton2g if ammoniaSource == "Conventional" else GreenAmmoniumNitrate_CI / ton2g
            default_AmmoniumNitrate_CI = default_AmmoniumNitrate_gN_Bu / AmmoniumNitrate_N_Content * ammonium_nitrate_CI
            default_scores.append(('default_AmmoniumNitrate_CI', 'D14', default_AmmoniumNitrate_CI))

            #cell D15
            ammonium_sulfate_CI = ConventionalAmmoniumSulfate_CI / ton2g if ammoniaSource == "Conventional" else GreenAmmoniumSulfate_CI / ton2g
            default_AmmoniumSulfate_CI = default_AmmoniumSulfate_gN_Bu / AmmoniumSulfate_N_Content * ammonium_sulfate_CI
            default_scores.append(('default_AmmoniumSulfate_CI', 'D15', default_AmmoniumSulfate_CI))

            #cell D16
            uan_CI = ConventionalUAN_CI / ton2g if ammoniaSource == "Conventional" else GreenUAN_CI / ton2g
            default_UAN_CI = default_UAN_gN_Bu / UAN_N_Content * uan_CI
            default_scores.append(('default_UAN_CI', 'D16', default_UAN_CI))

            #cell D17
            if ammoniaSource == "Conventional":
                map_CI = ConventionalMAP_CI / ton2g * MAP_share_as_Nfert
            else:
                map_CI = GreenMAP_CI / ton2g * MAP_share_as_Nfert
            default_MAP_CI = default_MAP_gN_Bu / MAP_N_Content * map_CI
            default_scores.append(('default_MAP_CI', 'D17', default_MAP_CI))

            #cell D18
            if ammoniaSource == "Conventional":
                dap_CI = ConventionalDAP_CI / ton2g * DAP_share_as_Nfert
            else:
                dap_CI = GreenDAP_CI / ton2g * DAP_share_as_Nfert
            default_DAP_CI = default_DAP_gN_Bu / DAP_N_Content * dap_CI
            default_scores.append(('default_DAP_CI', 'D18', default_DAP_CI))


            #cell D21
            if ammoniaSource == "Conventional":
                map_P2O5_CI = ConventionalMAP_CI / ton2g * (1 - MAP_share_as_Nfert)
            else:
                map_P2O5_CI = GreenMAP_CI / ton2g * (1 - MAP_share_as_Nfert)
            default_MAP_P2O5_CI = default_MAP_P2O5_gP_Bu / MAP_P2O5_Content * map_P2O5_CI
            default_scores.append(('default_MAP_P2O5_CI', 'D21', default_MAP_P2O5_CI))

            #cell D22
            if ammoniaSource == "Conventional":
                dap_P2O5_CI = ConventionalDAP_CI / ton2g * (1 - DAP_share_as_Nfert)
            else:
                dap_P2O5_CI = GreenDAP_CI / ton2g * (1 - DAP_share_as_Nfert)
            default_DAP_P2O5_CI = default_DAP_P2O5_gP_Bu / DAP_P2O5_Content * dap_P2O5_CI
            default_scores.append(('default_DAP_P2O5_CI', 'D22', default_DAP_P2O5_CI))


            #cell D25
            default_Potash_CI = default_K2O_g_Bu * ConventionalPotash_CI / ton2g
            default_scores.append(('default_Potash_CI', 'D25', default_Potash_CI))

            #cell D28
            default_Limestone_CI = default_CaCO3_g_Bu * ConventionalLimestone_CI / ton2g
            default_scores.append(('default_Limestone_CI', 'D28', default_Limestone_CI))

            #cell D31
            if crop == "Corn":
                if coverCrop == "no cover crop":
                    crop_CC_CI = 0
                else:
                    crop_CC_CI = default_CoverCrop_Herbicide_g_Bu * ProductionEmissions_CornHerbicide_GHG
            else:
                crop_CC_CI = 0
            default_Herbicide_CI = default_Herbicide_g_Bu * Herbicide_CI + crop_CC_CI
            default_scores.append(('default_Herbicide_CI', 'D31', default_Herbicide_CI))

            #cell D34
            default_Insecticide_CI = default_Insecticide_g_Bu  * Insecticide_CI
            default_scores.append(('default_Insecticide_CI', 'D34', default_Insecticide_CI))

            # cell D37
            # Dynamically construct variable names based on crop type using dictionary lookup
            n2o_factors = {"Corn": N2O_Factor_US_Corn, "Soybean": N2O_Factor_US_Soybean, "Sorghum": N2O_Factor_US_Sorghum, "Rice": N2O_Factor_US_Rice}
            n2o_factor_var = n2o_factors.get(crop, 0)
            biomass_residues = {"Corn": Corn_Ninbiomass_ResidueFactor, "Soybean": Soybean_Ninbiomass_ResidueFactor, "Sorghum": Sorghum_Ninbiomass_ResidueFactor, "Rice": Rice_Ninbiomass_ResidueFactor}
            biomass_residue_var = biomass_residues.get(crop, 0)
            biomass_n2o_factors = {"Corn": Corn_Biomass_N2O_Factor, "Soybean": Soybean_Biomass_N2O_Factor, "Sorghum": Sorghum_Biomass_N2O_Factor, "Rice": Rice_Biomass_N2O_Factor}
            biomass_n2o_factor_var = biomass_n2o_factors.get(crop, 0)
            
            # set up temp vars
            feedstock_GWP = n2o_factor_var * GWP_N2O_N
            biomass_ResidueFactor = (biomass_residue_var * biomass_n2o_factor_var * GWP_N2O_N)
            if crop == "Corn":
                if coverCrop == "no cover crop":
                    cc_GWP = 0
                else: cc_GWP = default_CoverCropN_gN_Bu * coverCrop_N2O_Emissions * GWP_N2O_N
            else: cc_GWP = 0
            if manureUsed == "no manure": manure_GWP = 0 
            else: manure_GWP = Manure_Total_Applied * Manure_N2O_factor * N2O_GWP
            
            # set the Carbon Intensity number
            default_N2OEmission_CI = default_Total_N_gN_Bu * feedstock_GWP + biomass_ResidueFactor + cc_GWP + manure_GWP
            default_scores.append(('default_N2OEmission_CI', 'D37', default_N2OEmission_CI))

            # *** FOR TESTING: Log D37 variables for debugging ************
            # # logger.info D37 variables with name and value
            # variable_names = [
            #     "default_Total_N_gN_Bu",
            #     "feedstock_GWP", 
            #     "biomass_residue_var", 
            #     "biomass_n2o_factor_var", 
            #     "GWP_N2O_N",
            #     "biomass_ResidueFactor",
            #     "cc_GWP", 
            #     "manure_GWP", 
            #     "default_N2OEmission_CI"]
            # # logger.info each variable with its name and value
            # logger.info(" ")
            # logger.info("---- D37 Variables:------- ")
            # for var_name in variable_names:
            #     if var_name in globals():
            #         logger.info(f"{var_name} = {globals()[var_name]}")
            #     else:
            #         logger.info(f"Variable '{var_name}' is not defined.")
            # logger.info("---------------------------")
            # *** END TESTING: Log default_scores for debugging **************
            
            # cell D38
            default_CO2EmissionUrea_CI = default_Urea_gN_Bu * Urea_N_to_CO2 + (default_UAN_gN_Bu * UreaProductionUsage_In_UAN * Urea_N * Urea_N_to_CO2)
            default_scores.append(('default_CO2EmissionUrea_CI', 'D38', default_CO2EmissionUrea_CI))

            # cell D39
            default_CO2EmissionCaCO3_CI = default_CaCO3_g_Bu * CaCO3_CO2_Content * CaCO3_PercentAcidification
            default_scores.append(('default_CO2EmissionCaCO3_CI', 'D39', default_CO2EmissionCaCO3_CI))

            # cell D40  default_N2OEmissionSoybeanFixation_CI
            # No Formula in Standard default spreadsheet --> DEFAULT to 0
            # if crop != "Soybean": default_N2OEmissionSoybeanFixation_CI = 0
            # else: default_N2OEmissionSoybeanFixation_CI = Soybean_Nfixation_N2O_factor * N2O_GWP
            default_N2OEmissionSoybeanFixation_CI = 0
            default_scores.append(('default_N2OEmissionSoybeanFixation_CI', 'D40', default_N2OEmissionSoybeanFixation_CI))

            # cell D41 & D59
            default_Result_CH4_Emissions = 0
            default_scores.append(('default_Result_CH4_Emissions', 'D41', default_Result_CH4_Emissions))

            # cell D55
            default_Result_Energy = default_Diesel_CI + default_Gasoline_CI + default_NaturalGas_CI + default_LPG_CI + default_Electricity_CI
            default_scores.append(('default_Result_Energy', 'D55', default_Result_Energy))

            # cell D56
            default_Result_NitrogenFertilizer = default_Ammonia_CI + default_Urea_CI + default_AmmoniumNitrate_CI + default_AmmoniumSulfate_CI + default_UAN_CI + default_MAP_CI + default_DAP_CI
            default_scores.append(('default_Result_NitrogenFertilizer', 'D56', default_Result_NitrogenFertilizer))

            # cell D57
            default_Result_N2O_Emissions = default_N2OEmission_CI + default_N2OEmissionSoybeanFixation_CI
            default_scores.append(('default_Result_N2O_Emissions', 'D57', default_Result_N2O_Emissions))

            # cell D58
            default_Result_CO2_Emissions = default_CO2EmissionUrea_CI + default_CO2EmissionCaCO3_CI
            default_scores.append(('default_Result_CO2_Emissions', 'D58', default_Result_CO2_Emissions))

            # cell D60
            default_Result_OtherChemicals = default_MAP_P2O5_CI + default_DAP_P2O5_CI + default_Potash_CI + default_Limestone_CI + default_Herbicide_CI + default_Insecticide_CI
            default_scores.append(('default_Result_OtherChemicals', 'D60', default_Result_OtherChemicals))

            # cell D62 & K32
            default_CI_Total = default_Result_Energy + default_Result_NitrogenFertilizer + default_Result_N2O_Emissions + default_Result_CO2_Emissions + default_Result_CH4_Emissions + default_Result_OtherChemicals
            default_scores.append(('default_CI_Total', 'K32', default_CI_Total))

            # K33
            try:
                if crop not in ["Corn", "Soybean"]: default_SOC = 0
                else: default_SOC = default_SOC_Emissions * CO2_C_to_CO2 / acre2hectare * kg2g / default_Yield
            except:
                default_SOC = "No SOC Results"
            default_scores.append(('default_SOC', 'K33', default_SOC))

            # cell K34
            if default_SOC == "No SOC Results": default_ScoreA = default_CI_Total  
            else: default_CI_Total + default_SOC
            default_scores.append(('default_ScoreA', 'K34', default_ScoreA))

            # compute megajoules (MJ/bushel = 2.75 gal/bu * 81.51 MJ/gal = 224.1525) so.. gGHG/MJ = gGHG/bu divided by 224.1525
            default_ScoreB = default_ScoreA  / 224.1525
            default_scores.append(('default_ScoreB', 'K35', default_ScoreB))

            # *** FOR TESTING: Log default_scores for debugging ************
            # # default_scores: Custom formatting with alignment
            # logger.info(" ")
            # logger.info(f"---- Default Scores:------- {crop} ")
            # logger.info("default_scores: Custom formatted table")
            # logger.info(f"{'Variable':<20} {'Cell':<6} {'Value':>10}")
            # logger.info("-" * 38)
            # for item in default_scores:
            #     try:
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {float(item[2]):>10.2f}")
            #     except (ValueError, TypeError):
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {str(item[2]):>10}")
            # *** END TESTING **********************************************
            
            # ****************** Section 4-f Compute Crop CI Scores *****************
            # compute_crop_scores.py
            crop_scores = []

            # Normalize values to lowercase for consistent comparison
            coverCrop = coverCrop.lower()
            manureUsed = manureUsed.lower()
            
            # (computed)    centroid
            crop_scores.append(('centroid', 'computed', centroid))

            # (computed)	bushel_Amount	 
            bushel_Amount = crop_area  * crop_yield
            crop_scores.append(('bushel_Amount', 'computed', bushel_Amount))
            
            # (computed)	crop_Value	 
            crop_Value = bushel_Amount  * average_Price
            crop_scores.append(('crop_Value', 'computed', crop_Value))
            
            # C5	crop_Diesel_CI 	 
            Diesel_CI_Factor = crop_Diesel_BTU_Bu * Diesel_CI
            cc_Ci = 0 if coverCrop == "no cover crop" else cc_Diesel_BTU_BU * Diesel_CI
            m_CI = 0 if manureUsed == "no manure" else (manure_Energy_BTU_Bu + 
                                            manure_TransportationEnergy_BTU_Bu) * Diesel_CI
            crop_Diesel_CI = Diesel_CI_Factor + cc_CI + m_CI
            crop_scores.append(('crop_Diesel_CI', 'C5', crop_Diesel_CI))
            
            # C6	crop_Gasoline_CI	 
            crop_Gasoline_CI =  Gasoline_CI * crop_Gasoline_BTU_Bu
            crop_scores.append(('crop_Gasoline_CI', 'C6', crop_Gasoline_CI))
            
            # C7	crop_NaturalGas_CI	 
            crop_NaturalGas_CI = NaturalGas_CI * crop_NaturalGas_BTU_Bu
            crop_scores.append(('crop_NaturalGas_CI', 'C7', crop_NaturalGas_CI))
            
            # C8	crop_LPG_CI 	 
            crop_LPG_CI = LPG_CI * crop_LPG_BTU_Bu
            crop_scores.append(('crop_LPG_CI', 'C8', crop_LPG_CI))
            
            # C9	crop_Electricity_CI	 
            crop_Electricity_CI = Electricity_CI * crop_Electricity_BTU_Bu
            crop_scores.append(('crop_Electricity_CI', 'C9', crop_Electricity_CI))
            
            # *********** C12	crop_Ammonia_CI *************
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Determine which ammonia CI value to use based on source
            def get_ammonia_ci():
                if ammoniaSource == "Conventional":
                    return ConventionalAmmonia_CI/ ton2g
                else:
                    return GreenAmmonia_CI / ton2g

            base_value = crop_Ammonia_gN_Bu / Ammonia_N_Content

            # Case 1: 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                reduction = 0.14  # 14% default reduction
                crop_Ammonia_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 2: 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                reduction = (reductionPercent_4R or 0) / 100
                crop_Ammonia_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 3: Standard calculation (no 4R management)
            else:
                crop_Ammonia_CI = base_value * get_ammonia_ci()
            # record to array
            crop_scores.append(('crop_Ammonia_CI', 'C12', crop_Ammonia_CI))


            # ************ C13	crop_Urea_CI *************
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Determine which ammonia CI value to use based on source
            def get_ammonia_ci():
                if ammoniaSource == "Conventional":
                    return ConventionalUrea_CI / ton2g
                else:
                    return GreenUrea_CI / ton2g

            base_value = crop_Urea_gN_Bu / Urea_N_Content

            # Case 1: 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                reduction = 0.14  # 14% default reduction
                crop_Urea_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 2: 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                reduction = (reductionPercent_4R or 0) / 100
                crop_Urea_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 3: Standard calculation (no 4R management)
            else:
                crop_Urea_CI = base_value * get_ammonia_ci()
            # record to array
            crop_scores.append(('crop_Urea_CI', 'C13', crop_Urea_CI))


            # ************** C14	crop_AmmoniumNitrate_CI ************
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Determine which ammonia CI value to use based on source
            def get_ammonia_ci():
                if ammoniaSource == "Conventional":
                    return ConventionalAmmoniumNitrate_CI / ton2g
                else:
                    return GreenAmmoniumNitrate_CI / ton2g

            base_value = crop_AmmoniumNitrate_gN_Bu / AmmoniumNitrate_N_Content

            # Case 1: 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                reduction = 0.14  # 14% default reduction
                crop_AmmoniumNitrate_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 2: 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                reduction = (reductionPercent_4R or 0) / 100
                crop_AmmoniumNitrate_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 3: Standard calculation (no 4R management)
            else:
                crop_AmmoniumNitrate_CI = base_value * get_ammonia_ci()
            # record to array
            crop_scores.append(('crop_AmmoniumNitrate_CI', 'C14', crop_AmmoniumNitrate_CI))


            # *********** C15	crop_AmmoniumSulfate_CI ***********
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Determine which ammonia CI value to use based on source
            def get_ammonia_ci():
                if ammoniaSource == "Conventional":
                    return ConventionalAmmoniumSulfate_CI / ton2g
                else:
                    return GreenAmmoniumSulfate_CI / ton2g

            base_value = crop_AmmoniumSulfate_gN_Bu / AmmoniumSulfate_N_Content

            # Case 1: 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                reduction = 0.14  # 14% default reduction
                crop_AmmoniumSulfate_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 2: 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                reduction = (reductionPercent_4R or 0) / 100
                crop_AmmoniumSulfate_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 3: Standard calculation (no 4R management)
            else:
                crop_AmmoniumSulfate_CI = base_value * get_ammonia_ci()
            # record to array
            crop_scores.append(('crop_AmmoniumSulfate_CI', 'C15', crop_AmmoniumSulfate_CI))


            # ************* C16	crop_UAN_CI ***********
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Determine which ammonia CI value to use based on source
            def get_ammonia_ci():
                if ammoniaSource == "Conventional":
                    return ConventionalUAN_CI / ton2g
                else:
                    return GreenUAN_CI / ton2g

            base_value = crop_UAN_gN_Bu / UAN_N_Content

            # Case 1: 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                reduction = 0.14  # 14% default reduction
                crop_UAN_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 2: 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                reduction = (reductionPercent_4R or 0) / 100
                crop_UAN_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 3: Standard calculation (no 4R management)
            else:
                crop_UAN_CI = base_value * get_ammonia_ci()
            # record to array
            crop_scores.append(('crop_UAN_CI', 'C16', crop_UAN_CI))


            # *********** C17	crop_MAP_CI **********
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Determine which ammonia CI value to use based on source
            def get_ammonia_ci():
                if ammoniaSource == "Conventional":
                    return ConventionalMAP_CI / ton2g
                else:
                    return GreenMAP_CI / ton2g

            base_value = crop_MAP_gN_Bu / MAP_N_Content

            # Case 1: 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                reduction = 0.14  # 14% default reduction
                crop_MAP_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 2: 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                reduction = (reductionPercent_4R or 0) / 100
                crop_MAP_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 3: Standard calculation (no 4R management)
            else:
                crop_MAP_CI = base_value * get_ammonia_ci()
            # record to array
            crop_scores.append(('crop_MAP_CI', 'C17', crop_MAP_CI))


            # *********** C18	crop_DAP_CI **********
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Determine which ammonia CI value to use based on source
            def get_ammonia_ci():
                if ammoniaSource == "Conventional":
                    return ConventionalDAP_CI / ton2g
                else:
                    return GreenDAP_CI / ton2g

            base_value = crop_DAP_gN_Bu / DAP_N_Content

            # Case 1: 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                reduction = 0.14  # 14% default reduction
                crop_DAP_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 2: 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                reduction = (reductionPercent_4R or 0) / 100
                crop_DAP_CI = base_value * get_ammonia_ci() * (1 - reduction)

            # Case 3: Standard calculation (no 4R management)
            else:
                crop_DAP_CI = base_value * get_ammonia_ci()
            # record to array
            crop_scores.append(('crop_DAP_CI', 'C18', crop_DAP_CI))


            # C21	crop_MAP_P2O5_CI
            get_map_ci = ConventionalMAP_CI if ammoniaSource == "Conventional" else GreenMap_CI
            crop_MAP_P2O5_CI = crop_MAP_P2O5_gP_Bu / MAP_P2O5_Content *  get_map_ci / ton2g * (1 - MAP_share_as_Nfert)
            # record to array
            crop_scores.append(('crop_MAP_P2O5_CI', 'C21', crop_MAP_P2O5_CI))

            # C22	crop_DAP_P2O5_CI
            get_dap_ci = ConventionalDAP_CI if ammoniaSource == "Conventional" else  GreenDap_CI
            crop_DAP_P2O5_CI = crop_DAP_P2O5_gP_Bu / DAP_P2O5_Content *  get_map_ci / ton2g * (1 - MAP_share_as_Nfert)
            # record to array
            crop_scores.append(('crop_DAP_P2O5_CI', 'C22', crop_DAP_P2O5_CI))
            
            # C25	crop_Potash_CI _CI 	 
            crop_Potash_CI = crop_K2O_g_Bu * ConventionalPotash_CI / ton2g
            # record to array
            crop_scores.append(('crop_Potash_CI', 'C25', crop_Potash_CI))
            
            # C28	crop_Limestone_CI 	 
            crop_Limestone_CI = crop_CaCO3_g_Bu * ConventionalLimestone_CI / ton2g

            # C31	crop_Herbicide_CI
            if crop == "Corn":
                if coverCrop == "no cover crop":
                    crop_CC_CI = 0
                else:
                    crop_CC_CI = coverCrop_Herbicide_g_Bu * ProductionEmissions_CornHerbicide_GHG
            else:
                crop_CC_CI = 0
            crop_Herbicide_CI = crop_Herbicide_g_Bu * Herbicide_CI + crop_CC_CI
            # record to array
            crop_scores.append(('crop_Herbicide_CI', 'C31', crop_Herbicide_CI))
            
            # C34	crop_Insecticide_CI 	 
            crop_Insecticide_CI = crop_Insecticide_g_Bu * Insecticide_CI
            crop_scores.append(('crop_Insecticide_CI', 'C34', crop_Insecticide_CI))
            
            # *********** C37	crop_N2OEmission_CI *****************
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # Dynamically construct variable names based on crop type using dictionary lookup
            n2o_factors = {"Corn": N2O_Factor_US_Corn, 
                            "Soybean": N2O_Factor_US_Soybean, 
                            "Sorghum": N2O_Factor_US_Sorghum, 
                            "Rice": N2O_Factor_US_Rice}
            n2o_factor_var = n2o_factors.get(crop, 0)
            biomass_residues = {"Corn": Corn_Ninbiomass_ResidueFactor, 
                                "Soybean": Soybean_Ninbiomass_ResidueFactor, 
                                "Sorghum": Sorghum_Ninbiomass_ResidueFactor, 
                                "Rice": Rice_Ninbiomass_ResidueFactor}
            biomass_residue_var = biomass_residues.get(crop, 0)
            biomass_n2o_factors = {"Corn": Corn_Biomass_N2O_Factor, 
                                    "Soybean": Soybean_Biomass_N2O_Factor, 
                                    "Sorghum": Sorghum_Biomass_N2O_Factor, 
                                    "Rice": Rice_Biomass_N2O_Factor}
            biomass_n2o_factor_var = biomass_n2o_factors.get(crop, 0)

            feedstock_n2o_gwp = n2o_factor_var * GWP_N2O_N
            feedstock_biomass_gwp = biomass_residue_var * biomass_n2o_factor_var * GWP_N2O_N

            # Handle non-Corn crops (Soybean, Rice, Sorghum)
            if crop != "Corn":
                # Proposition 1
                crop_N2OEmission_CI = (crop_Total_N_gN_Bu * feedstock_n2o_gwp + feedstock_biomass_gwp)
                C37Scenario = "scenario 1: crop not Corn"

            # Handle Corn with different management scenarios
            else:
                # Proposition 2 - Business as Usual
                if nitrogenManagementCorn.lower().startswith("business as usual") :
                    crop_N2OEmission_CI = (crop_Total_N_gN_Bu * feedstock_n2o_gwp + feedstock_biomass_gwp)
                    C37Scenario = "scenario 2: Corn, N-management BAU"

                # Proposition 3 - 4R management & default reduction
                elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                    crop_N2OEmission_CI = (default_Total_N_gN_Bu * (1 - 0.14) * feedstock_n2o_gwp +
                                        feedstock_biomass_gwp)
                    C37Scenario = "scenario 3: Corn, N-management 4R, fert rate Default"

                # Proposition 4 - 4R management & user-specified reduction 
                elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                    
                    crop_N2OEmission_CI = (default_Total_N_gN_Bu * (1 - reductionPercent_4R) * feedstock_n2o_gwp +
                                        feedstock_biomass_gwp)
                    C37Scenario = "scenario 4: Corn, N-management 4R, fert rate User-specified"

                # Proposition 5 - All other corn cases (Enhanced Efficiency reduction)
                else:
                    crop_N2OEmission_CI = (crop_Total_N_gN_Bu * (0.7 * N2O_Factor_US_Corn_Direct + 
                                                N2O_Factor_US_Corn_Indirect) * GWP_N2O_N + feedstock_biomass_gwp)
                    C37Scenario = "scenario 5, Corn, all other (usu. fert rate Enhanced Efficiency)"
            
            
            # Create alternative scenarios for comparison
            crop_N2OEmission_CI_BAU = (crop_Total_N_gN_Bu * feedstock_n2o_gwp + feedstock_biomass_gwp)
            crop_N2OEmission_CI_EE = (crop_Total_N_gN_Bu * (0.7 * N2O_Factor_US_Corn_Direct + 
                                                N2O_Factor_US_Corn_Indirect) * GWP_N2O_N + feedstock_biomass_gwp)
            # record C37 metric to array
            crop_scores.append(('crop_Total_N_gN_Bu', 'C37', crop_Total_N_gN_Bu))
            crop_scores.append(('crop_N2OEmission_CI', 'C37', crop_N2OEmission_CI))
            crop_scores.append(('C37Scenario', 'C37', C37Scenario))
            crop_scores.append(('nitrogenManagementCorn', 'C37', nitrogenManagementCorn))
            crop_scores.append(('fertilizerRateTypeCorn', 'C37', fertilizerRateTypeCorn))
            crop_scores.append(('crop_N2OEmission_CI_BAU', 'C37', crop_N2OEmission_CI_BAU))
            crop_scores.append(('crop_N2OEmission_CI_EE', 'C37', crop_N2OEmission_CI_EE))

            # *** FOR TESTING: Log C37 variables for debugging ************
            # # logger.info C37 variables with name and value
            # variable_names = [
            #     "n2o_factor_var",
            #     "biomass_residue_var",
            #     "biomass_n2o_factor_var",
            #     "GWP_N2O_N",
            #     "feedstock_n2o_gwp",
            #     "feedstock_biomass_gwp",
            #     "C37Scenario",
            #     "crop_Total_N_gN_Bu", 
            #     "crop_N2OEmission_CI"]
            # # logger.info each variable with its name and value
            # logger.info(" ")
            # logger.info("---- C37 Variables:------- ")
            # for var_name in variable_names:
            #     if var_name in globals():
            #         logger.info(f"{var_name} = {globals()[var_name]}")
            #     else:
            #         logger.info(f"Variable '{var_name}' is not defined.")
            # logger.info("---------------------------")
            # *** END TESTING: Log C37 variables for debugging ************
            # **************************** END C37 Computation *****************************
            
            # *********** C38	crop_CO2EmissionUrea_CI *****************
            # Check if conditions match Corn with 4R management
            is_corn_4r = (crop == "Corn" and nitrogenManagementCorn.upper().startswith("4R"))

            # 4R management with default 14% reduction
            if (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("default")):
                crop_CO2EmissionUrea_CI = (crop_Urea_gN_Bu * Urea_N_to_CO2 +
                                        crop_UAN_gN_Bu * UreaProductionUsage_In_UAN * Urea_N * Urea_N_to_CO2 * (1 - 0.14))

            # 4R management with user-specified reduction
            elif (is_corn_4r and fertilizerRateTypeCorn.lower().startswith("user")):
                crop_CO2EmissionUrea_CI = (crop_Urea_gN_Bu * Urea_N_to_CO2 +
                                        crop_UAN_gN_Bu * UreaProductionUsage_In_UAN * Urea_N * Urea_N_to_CO2 * (1 - reductionPercent_4R))

            # All other cases
            else:
                crop_CO2EmissionUrea_CI = (crop_Urea_gN_Bu * Urea_N_to_CO2 +
                                        crop_UAN_gN_Bu * UreaProductionUsage_In_UAN * Urea_N * Urea_N_to_CO2)

            # record to array
            crop_scores.append(('crop_CO2EmissionUrea_CI', 'C38', crop_CO2EmissionUrea_CI))
            # ************************* END C38 Computation *****************************
            
            # C39	crop_CO2EmissionCaCO3_CI	 
            crop_CO2EmissionCaCO3_CI = crop_CaCO3_g_Bu *  CaCO3_CO2_Content * CaCO3_PercentAcidification
            crop_scores.append(('crop_CO2EmissionCaCO3_CI', 'C39', crop_CO2EmissionCaCO3_CI))
            
            # C40	crop_N2OEmissionSoybeanFixation_CI	
            # No Formula in Standard default spreadsheet --> DEFAULT to 0
            # if crop == "Soybean": crop_N2OEmissionSoybeanFixation_CI = Soybean_Nfixation_N2O_factor * N2O_GWP
            # else: crop_N2OEmissionSoybeanFixation_CI = 0
            crop_N2OEmissionSoybeanFixation_CI = 0
            crop_scores.append(('crop_CO2N2OEmissionSoybeanFixation_CI', 'C40', crop_N2OEmissionSoybeanFixation_CI))
            
            # C41 & C59	crop_Result_CH4_Emissions	 
            crop_Result_CH4_Emissions = 0 
            crop_scores.append(('crop_Result_CH4_Emission', 'C39', crop_Result_CH4_Emissions))
            
            # C55	crop_Result_Energy	 
            crop_Result_Energy = crop_Diesel_CI + crop_Gasoline_CI + crop_NaturalGas_CI + crop_LPG_CI + crop_Electricity_CI
            crop_scores.append(('crop_Result_Energy', 'C55', crop_Result_Energy))
            
            # C56	crop_Result_NitrogenFertilizer	 
            crop_Result_NitrogenFertilizer = crop_Ammonia_CI + crop_Urea_CI + crop_AmmoniumNitrate_CI + crop_AmmoniumSulfate_CI + crop_UAN_CI + crop_MAP_CI + crop_DAP_CI
            crop_scores.append(('crop_Result_NitrogenFertilizer', 'C56', crop_Result_NitrogenFertilizer))
            
            # C57	crop_Result_N2O_Emissions	 
            crop_Result_N2O_Emissions = crop_N2OEmission_CI + crop_N2OEmissionSoybeanFixation_CI
            crop_scores.append(('crop_Result_N2O_Emissions', 'C57', crop_Result_N2O_Emissions))
            
            # C58	crop_Result_CO2_Emission	 
            crop_Result_CO2_Emissions = crop_CO2EmissionUrea_CI + crop_CO2EmissionCaCO3_CI
            crop_scores.append(('crop_Result_CO2_Emissions', 'C58', crop_Result_CO2_Emissions))
            
            # C59	crop_Result_CH4_Emissions	 
            crop_Result_CH4_Emissions = crop_MAP_P2O5_CI + crop_DAP_P2O5_CI + crop_Potash_CI + crop_Limestone_CI + crop_Herbicide_CI + crop_Insecticide_CI
            crop_scores.append(('crop_Result_CH4_Emissions', 'C59', crop_Result_CH4_Emissions))
            
            # C60	crop_Result_OtherChemicals	 
            crop_Result_OtherChemicals = (crop_MAP_P2O5_CI + crop_DAP_P2O5_CI + crop_Potash_CI + 
                                        crop_Limestone_CI + crop_Herbicide_CI + crop_Insecticide_CI)
            crop_scores.append(('crop_Result_OtherChemicals', 'C60', crop_Result_OtherChemicals))
            
            # C62 & J32	CI_Score_Total	 
            CI_Score_Total = crop_Result_Energy + crop_Result_NitrogenFertilizer + crop_Result_N2O_Emissions + crop_Result_CO2_Emissions + crop_Result_CH4_Emissions + crop_Result_OtherChemicals
            crop_scores.append(('CI_Score_Total', 'C62 & J32', CI_Score_Total))
            
            # J33	crop_SOC
            try:
                if crop not in ["Corn", "Soybean"]:
                    crop_SOC = 0
                else:
                    crop_SOC = cropSOC_Emissions * CO2_C_to_CO2 / acre2hectare * kg2g / crop_yield
            except:
                crop_SOC = "No SOC Results"
            # add to array
            crop_scores.append(('crop_SOC', 'J33', crop_SOC))
            
            # J34	CI_Score_A	 
            CI_Score_A = CI_Score_Total if crop_SOC == "No SOC Results" else CI_Score_Total + crop_SOC
            crop_scores.append(('CI_Score_A', 'J34', CI_Score_A))
            
            # (computed)	CI_Score_B	 
            # Convert score to MJ/Bu
            CI_Score_B = CI_Score_A  / 224.1525
            crop_scores.append(('CI_Score_B', '(computed)', CI_Score_B))

            # *** FOR TESTING: LOG FORMATTED CROP SCORES ***************
            # # logger.info crop_scores: Custom formatting with alignment
            # logger.info(" ")
            # logger.info("---- Crop Scores:------- {crop} ")
            # logger.info("crop_scores: Custom formatted table")
            # logger.info(f"{'Variable':<20} {'Cell':<6} {'Value':>10}")
            # logger.info("-" * 38)
            # for item in crop_scores:
            #     try:
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {float(item[2]):>10.2f}")
            #     except (ValueError, TypeError):
            #         logger.info(f"{item[0]:<20} {item[1]:<6} {str(item[2]):>10}")
            # *** END TESTING: LOG FORMATTED CROP SCORES ***************
            
            # ****************** Section 4-g Create CI_Score (JSON) object & Add to feature_scores array **********
            # The default_scores and crop_scores are lists of lists 
            #   - where each inner list contains [key, cell_reference, value]. 
            raw_scores = {
                'planting_id': planting_ID,
                'crop': crop,
                'default_scores': default_scores,
                'crop_scores': crop_scores
                }
            feature_scores.append(raw_scores)

            # *** FOR TESTING: LOG FORMATTED FEATURE SCORES ***************
            # logger.info feature_scores: Custom formatting with alignment
            # logger.info("\nfeature_scores: Feature[0]")
            # logger.info("-" * 38)
            # logger.info(f"Planting ID: {feature_scores[0]['planting_id']}")
            # logger.info(f"Crop: {feature_scores[0]['crop']}")
            # logger.info(f"Default Scores: {feature_scores[0]['default_scores']}")
            # logger.info(f"Crop Scores: {feature_scores[0]['crop_scores']}")
            # *** END TESTING: LOG FORMATTED FEATURE SCORES ***************
            
            # ----------- END PROCESSING EACH FEATURE ONE BY ONE--------------------------
        # =============== END SCORE CALCULATIONS =====================================
            
            
        # =========== START Section 5 - Generate Individual CIS Certs & Store ==============
        # --- uses feature_scores array to build CIS Certs for each crop (field)
        # needs:
        # import json
        # from datetime import datetime
        
        # -- FOR TESTING ONLY --
        # generate_certs = True  # Force to True to test generating certificates
        # -- FOR TESTING ONLY --

        """
        Generates JSON objects from feature_scores and saves to files.

        Args:
            feature_scores (list): List of feature score dictionaries
            collection_id (str): Collection ID for the dataset
            
        Returns:
            str: Path to the saved JSON file
        """

        # --- START if generate_certs code block --------------------------
        if generate_certs:
            # helper function to get a score value from the nested list structure
            def get_score(scores_list, key_name):
                """Helper function to find a score value from the nested list structure"""
                for item in scores_list:
                    if item[0] == key_name:
                        # if the value is a float, round to 2 decimal places else return as is
                        if isinstance(item[2], float):
                            return round(item[2], 2)
                        return item[2]
                return None

            # ---------------- Process feature scores --------------------------
            # get length of feature_scores
            length_feature_scores = len(feature_scores)
            
            try:
                # verify the feature_scores & features lengths match
                if len(feature_scores) != len(features):
                    raise ValueError(f"Length mismatch: feature_scores has {len(feature_scores)} elements while features has {len(features)} elements")

                # use certificate_type to determine how many certificates to generate
                if certificate_type == "TEST": certs_to_generate = 2
                else: certs_to_generate = length_feature_scores
                
                # ------------ START Step through each feature_score and build cis_json ----------
                logger.info(f".. now processing {certs_to_generate}/{len(feature_scores)} records...") 
                 
                for index in range(certs_to_generate): # Process all features (real mode)
                    
                    feature_score = feature_scores[index]
                    # Extract data from feature_score
                    try:
                        # get current feature properties dictionary
                        properties_element = features[index]['properties']
                        planting_ID = properties_element.get('PlantingId', 'N/A')
                        
                        # begin building the CIS JSON object
                        cis_json = { 
                            "Data Type": "CI Score",
                            "Certificate Type": certificate_type,
                            "CIS_ID": f"CIS-{planting_ID}",
                            "DateTime of Creation": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),    
                            "Data Provider": data_Provider,
                            "CollectionId": collection_ID,
                            "BusinessId": business_ID,
                            "Attested By 1": file_level_attributes.get('Attested By 1', 'N/A'),
                            "Signature 1": file_level_attributes.get('Signature 1', 'N/A'),
                            "Attested DateTime 1": file_level_attributes.get('Attested DateTime 1', 'N/A'),
                            "Attested By 2": file_level_attributes.get('Attested By 2', 'N/A'), 
                            "Signature 2": file_level_attributes.get('Signature 2', 'N/A'),
                            "Attested DateTime 2": file_level_attributes.get('Attested DateTime 2', 'N/A'),
                            "Crop": properties_element.get('Crop', 'N/A'),
                            "PlantingId": planting_ID,
                            "Season": season,
                            "FarmId": properties_element.get('FarmId', 'N/A'),
                            "FieldId": properties_element.get('FieldId', 'N/A'),
                            "Country": file_level_attributes.get('Country','United States'),
                            "State": properties_element.get('State', 'N/A'),
                            "County": properties_element.get('County', 'N/A'),
                            "Centroid": get_score(feature_score['crop_scores'], "centroid"),
                            "UOM": {
                                "Average Crop Price": "U$",  
                                "Crop Value": "U$",  
                                "Carbon Intensity Score A": "g GHG per Bu",  
                                "Carbon Intensity Score B": "g GHG per MJ",
                                "Energy": "g GHG per Bu",
                                "Nitrogen Fertilizer": "g GHG per Bu",
                                "N2O Emissions": "g GHG per Bu",
                                "CO2 Emissions": "g GHG per Bu",
                                "CH4 Emissions": "g GHG per Bu",
                                "Other Chemicals": "g GHG per Bu",
                                "CI Score Total": "g GHG per MJ",
                                "Default SOC": "g GHG per MJ",
                                "Farm Size": "Acres",  
                                "Crop Area": "Acres",  
                                "Yield": "Bushels/Acre"  
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
                            "GeoJSON": {
                            "type": "FeatureCollection",  
                            "features": [features[index]]
                            }  
                        }
                        # --- END building the cis_json object ----------
                        
                        # *** SAVE Cert To File for testing purposes ************
                        # Generate filename with input collection ID and save to file
                        filename = f"CIS-{planting_ID}.json"
                        # Save to file with nice formatting
                        with open(filename, 'w') as f:
                            json.dump(cis_json, f, indent=2)
                        logger.info(f"File should be saved as: {filename}")
                        # *** END SAVE Cert To File for testing purposes ********
                        
                        # **************************************************************
                        # --- INSERT Code to call graphQL API to insert the CIS record
                        # Example code to insert a CIS record using a GraphQL client
                        # Assuming 'graphql_client' is a GraphQL client instance
                        # Assuming 'cis_json' is the CIS record as a Python dictionary
                        # Example:
                        # graphql_client.execute(
                        #     mutation=insert_cis_record,
                        #     variables={"cisRecord": cis_json},
                        # )
                        # --- END Code to call graphQL API to insert the CIS record
                        # ****************************************************************
                        
                    except IndexError:
                        logger.error(f"Error: Could not access index {index} in features list")
                        break
                    # ----------- END of try-except block ------ Extract data from feature_score -----
                # ----------- END of For loop - feature_score in feature_scores -----
                    
            except Exception as e:
                logger.error(f"An unexpected error occurred: {str(e)}")
            # ----------- END of try-except block - Process feature scores -----------
        # ----------- END of if generate_certs code block ------------------------
        
        # example Generate filename with timestamp
        # filename = f"feature_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # ============== END Section 5 - Generate Individual CIS Scores ==============
        
        
        
        # =========== Section 6 Build the agC Results Collection ==========================
        # --- uses feature_scores array to build the agC ResultsCollection
        # Section 5 - Build the agC ResultsCollection
        # needs:
        # import json
        # from datetime import datetime

        def generate_feature_scores_json(feature_scores, collection_id):
            """
            Generates a JSON object from feature scores and saves it to a file.
            
            Args:
                feature_scores (list): List of feature score dictionaries
                input_collection_id (str): Collection ID for the dataset
                
            Returns:
                str: Path to the saved JSON file
            """
            def get_score(scores_list, key_name):
                """Helper function to find a score value from the nested list structure"""
                for item in scores_list:
                    if item[0] == key_name:
                        # if the value is a float, round to 2 decimal places else return as is
                        if isinstance(item[2], float):
                            return round(item[2], 2)
                        return item[2]
                return None

            json_structure = {
                "Data Type": "ResultsCollection",
                "Collection ID": collection_ID,
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
            
            # Example: Generate filename with timestamp
            # filename = f"feature_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Example: Generate filename with input collection ID
            # filename = f"feature_scores_{collection_id}.json"
            
            # Save to file with nice formatting
            # with open(filename, 'w') as f:
            #     json.dump(json_structure, f, indent=2)
            
            # return filename
            return json_structure

        # **** USE FOR TESTING ONLY - DON'T RUN IN PRODUCTION ---------------------
        # output_file = generate_feature_scores_json(feature_scores, collection_ID)
        # logger.info(f"File should be saved as: {output_file}")
        
        # =========== END Section 6 Build the agC Results Collection ======================
        
        
        
        # ---------- RETURN FEATURE SCORES ARRAY -----------------------------
        # (this is still in the 'Try..Except' block)
        return generate_feature_scores_json(feature_scores, collection_ID)
    
        # # --- example of returning a sample result --------
        # result_value = data["value1"] + data["value2"] + Herbicide_CI
        # return {"result": result_value}
    
    except KeyError as e:
        raise ValueError(f"Missing key: {str(e)} in input data or global variables") from e


# --------------- end of the function definition ------------------
