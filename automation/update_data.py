import pandas as pd
import requests
import zipfile
import io
import os

# --- Configuration ---
# Set the directory for the final generated JSON files
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# URL for the NADAC Weekly File (This URL changes, check CMS site for the latest)
# Using a conceptual URL here; you must find the direct download link.
# NADAC_URL = "https://www.medicaid.gov/files/nadac-weekly-latest.csv" 
# Use a static example for now; in production, you'll need the current link.
# For RxNorm, you need a UTS license for the full RRF, but we'll use a direct link pattern for illustration.

def download_file(url):
    """Downloads a file and returns its content as a file-like object."""
    print(f"Downloading from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    return io.BytesIO(response.content)

def process_rxnorm_and_nadac():
    print("Starting data processing pipeline...")
    
    # 1. --- Download and Process RxNorm Data (RXNSAT.RRF) ---
    # NOTE: Accessing the full RRF requires a UTS account/API key. 
    # For a real implementation, you'd likely use a custom downloader or an approved mirror.
    # We will simulate loading the critical file.
    # The RxNorm file RXNSAT.RRF contains the 'NDC' attribute.
    
    # SIMULATION: Create a dummy RxNorm DataFrame (RXNSAT.RRF content)
    rxnorm_data = {
        'RXCUI': ['197316', '197316', '201990', '201990'],
        'ATN': ['NDC', 'NDC', 'NDC', 'NDC'],
        'ATV': ['0093-4100-01', '50111-0422-01', '60505-0012-01', '0003-0805-01'],
        'TTY': ['SCD', 'SCD', 'SCD', 'SCD']
    }
    df_rxnsat = pd.DataFrame(rxnorm_data)
    
    # Filter for the 'NDC' attribute and the Semantic Clinical Drugs (SCD)
    df_ndc_map = df_rxnsat[
        (df_rxnsat['ATN'] == 'NDC') & 
        (df_rxnsat['TTY'] == 'SCD')
    ].copy()
    
    # Clean up the NDC format if necessary (NADAC uses 11-digit format, no hyphens)
    df_ndc_map['NDC'] = df_ndc_map['ATV'].str.replace('-', '').str.zfill(11)
    df_ndc_map = df_ndc_map[['RXCUI', 'NDC']].drop_duplicates()
    
    print(f"RxNorm NDC map loaded: {len(df_ndc_map)} NDCs found.")

    # 2. --- Download and Process NADAC Pricing Data ---
    # In a real scenario, this would be a download_file() call
    
    # SIMULATION: Create a dummy NADAC DataFrame
    nadac_data = {
        'NDC': ['0093410001', '50111042201', '60505001201', '0003080501', '99999999999'],
        'NADAC_Per_Unit': [1.55, 0.92, 0.45, 2.10, 0.05],
        'Effective_Date': ['2025-10-01', '2025-10-01', '2025-10-01', '2025-10-01', '2025-10-01'],
        'Pricing_Unit': ['EA', 'ML', 'CAP', 'ML', 'EA']
    }
    df_nadac = pd.DataFrame(nadac_data)
    
    # Ensure NDC is string and 11-digit format
    df_nadac['NDC'] = df_nadac['NDC'].astype(str).str.zfill(11)

    print(f"NADAC data loaded: {len(df_nadac)} price entries found.")

    # 3. --- JOIN the DataFrames ---
    # Merge RxNorm concepts (RXCUI) with their prices (NADAC_Per_Unit)
    df_final = pd.merge(
        df_ndc_map, 
        df_nadac, 
        on='NDC', 
        how='left' # Keep all NDCs, even if they lack a NADAC price
    )
    df_final = df_final.dropna(subset=['NADAC_Per_Unit']) # Only keep rows with price data

    print(f"Joined data has {len(df_final)} rows with valid prices.")

    # 4. --- Generate Individual JSON Files ---
    # Group by the Generic Drug (RXCUI) and save the data for that drug
    for rxcui, group in df_final.groupby('RXCUI'):
        # Convert the group DataFrame to a list of dicts for optimal JSON output
        output_list = group.to_dict('records')
        
        # Save to the data directory with the RXCUI as the filename
        output_path = os.path.join(DATA_DIR, f'{rxcui}.json')
        with open(output_path, 'w') as f:
            import json
            json.dump(output_list, f, indent=2)
            
        print(f"Generated {rxcui}.json with {len(output_list)} entries.")
        
    print("Data processing complete.")

if __name__ == "__main__":
    process_rxnorm_and_nadac()