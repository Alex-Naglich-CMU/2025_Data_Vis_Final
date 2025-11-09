import pandas as pd
import requests
import zipfile
import io
import os

# --- Configuration ---
# Set the directory for the final generated JSON files
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Define column names for the RRF files (since they lack headers)
RXNSAT_COLUMNS = ['RXCUI', 'LUI', 'SUI', 'RXAUI', 'STYPE', 'CODE', 'ATUI', 'SATUI', 
                  'ATN', 'SAB', 'ATV', 'SUPPRESS', 'CVF', 'TFS', 'TS']
RXNCONSO_COLUMNS = ['RXCUI', 'LAT', 'TS', 'LUI', 'STT', 'SUI', 'ISPREF', 'RXAUI', 'SAUI', 
                    'SCUI', 'SAB', 'TTY', 'CODE', 'STR', 'SUPPRESS', 'CVF', 'TFS', 'ATUI', 'VSAB', 'SL']
RXNREL_COLUMNS = ['RXCUI1', 'RXAUI1', 'STYPE1', 'REL', 'RXCUI2', 'RXAUI2', 'STYPE2', 'RELA', 
                  'RUI', 'SRUI', 'SAB', 'SL', 'RG', 'DIR', 'SUPPRESS', 'CVF']

def process_rxnorm_and_nadac():
    print("Starting data processing pipeline...")
    
    
    # Load RxNorm Data from root
    df_rxnsat = pd.read_csv(os.path.join('', 'RXNSAT.RRF'), sep='|', dtype=str, header=None, names=RXNSAT_COLUMNS)
    df_rxnconso = pd.read_csv(os.path.join('', 'RXNCONSO.RRF'), sep='|', dtype=str, header=None, names=RXNCONSO_COLUMNS)
    df_rxnrel = pd.read_csv(os.path.join('', 'RXNREL.RRF'), sep='|', dtype=str, header=None, names=RXNREL_COLUMNS)
    
    # Load Nadac Data from root
    df_nadac = pd.read_csv(os.path.join('', 'nadac-comparison.csv'), dtype=str)

    # Clean the NDC format to remove dashes and ensure 11-digit strings
    df_nadac['NDC'] = df_nadac['ATV'].str.replace('-', '').str.zfill(11)

    # Merge RxNorm concepts (RXCUI) with their prices (NADAC_Per_Unit)
    df_final = pd.merge(
        df_nadac, 
        on='NDC', 
        how='left' # Keep all NDCs, even if they lack a NADAC price
    )
    df_final = df_final.dropna(subset=['NADAC_Per_Unit']) # Only keep rows with price data

    processed_rxcui = set()

    for ndc, rxcui in tqdm(ndc_to_rxcui_map.items(), desc="Processing NDCs and writing files"):
        if rxcui not in processed_rxcui:
            # Step 5a: Initialize the main JSON structure
            drug_data = {
                "RxCUI": rxcui,
                "Name": rxcui_metadata_map.get(rxcui, {}).get('STR', 'Unknown Name'),
                "TermType": rxcui_metadata_map.get(rxcui, {}).get('TTY', 'Unknown TTY'),
                "IsBrand": rxcui in rxcui_to_generic_map, # If a Brand maps to a Generic, it's a Brand
                "Brand_RxCUI": rxcui if rxcui in rxcui_to_generic_map else None,
                "Generic_RxCUI": rxcui_to_generic_map.get(rxcui, rxcui), # If not in map, it's likely a generic itself
                "prices": {}
            }

        # Save to the data directory with the RXCUI as the filename
        output_path = os.path.join(DATA_DIR, f'{rxcui}.json')
        with open(output_path, 'w') as f:
            import json
            json.dump(output_list, f, indent=2)
            
        print(f"Generated {rxcui}.json with {len(output_list)} entries.")
        
    print("Data processing complete.")

if __name__ == "__main__":
    process_rxnorm_and_nadac()