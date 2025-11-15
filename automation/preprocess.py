import pandas as pd
import json
import os
from tqdm import tqdm

# configuration
DATA_DIR = 'data'
PRICES_DIR = 'static/data/prices'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PRICES_DIR, exist_ok=True)

# file paths
NADAC_FILE = 'nadac-comparison-11-05-2025.csv'
RXNSAT_FILE = 'RXNSAT.RRF'
RXNREL_FILE = 'RXNREL.RRF'

print("NADAC + RxNorm Data Preprocessing Pipeline")

# STEP 1: Load RxNorm RXNSAT (NDC → RxCUI mapping)
print("\n[1/4] Loading RXNSAT.RRF for NDC mappings...")

rxnsat_columns = [
    'RXCUI', 'LUI', 'SUI', 'RXAUI', 'STYPE', 'CODE', 'ATUI', 
    'SATUI', 'ATN', 'SAB', 'ATV', 'SUPPRESS', 'CVF', 'EXTRA'
]

print("   Reading RXNSAT.RRF...")
df_rxnsat = pd.read_csv(
    RXNSAT_FILE, 
    sep='|', 
    header=None, 
    names=rxnsat_columns,
    dtype=str,
    low_memory=False
)

df_ndc_map = df_rxnsat[df_rxnsat['ATN'] == 'NDC'].copy()

print(f"   Loaded {len(df_rxnsat):,} total rows from RXNSAT")
print(f"   Found {len(df_ndc_map):,} NDC entries")

df_ndc_map['NDC_CLEAN'] = df_ndc_map['ATV'].str.replace('-', '').str.strip().str.zfill(11)

ndc_to_rxcui = dict(zip(df_ndc_map['NDC_CLEAN'], df_ndc_map['RXCUI']))
print(f"   Built lookup table with {len(ndc_to_rxcui):,} unique NDCs")

del df_rxnsat, df_ndc_map

# STEP 2: Load RxNorm RXNREL (Brand/Generic relationships) 
print("\n[2/4] Loading RXNREL.RRF...")

rxnrel_columns = [
    'RXCUI1', 'RXAUI1', 'STYPE1', 'REL', 'RXCUI2', 'RXAUI2', 
    'STYPE2', 'RELA', 'RUI', 'SRUI', 'SAB', 'SL', 'DIR', 
    'RG', 'SUPPRESS', 'CVF'
]

df_rxnrel = pd.read_csv(
    RXNREL_FILE,
    sep='|',
    header=None,
    names=rxnrel_columns,
    usecols=range(len(rxnrel_columns)),
    dtype=str,
    low_memory=False
)

df_relationships = df_rxnrel[
    (df_rxnrel['SAB'] == 'RXNORM') &
    (df_rxnrel['RELA'].isin(['has_tradename', 'tradename_of', 'has_brand_name', 'brand_name_of']))
].copy()

print(f"   Loaded {len(df_rxnrel):,} rows from RXNREL")
print(f"   Found {len(df_relationships):,} tradename relationships")

print("   Building relationship lookup tables...")
brand_to_generic = {}
generic_to_brand = {}

for _, row in df_relationships.iterrows():
    rxcui1 = str(row['RXCUI1']).strip()
    rxcui2 = str(row['RXCUI2']).strip()
    rela = str(row['RELA']).strip()
    
    if rela in ['tradename_of', 'brand_name_of']:
        brand_to_generic[rxcui1] = rxcui2
        if rxcui2 not in generic_to_brand:
            generic_to_brand[rxcui2] = rxcui1
    elif rela in ['has_tradename', 'has_brand_name']:
        generic_to_brand[rxcui1] = rxcui2
        if rxcui2 not in brand_to_generic:
            brand_to_generic[rxcui2] = rxcui1

print(f"   Built lookup tables:")
print(f"     - {len(brand_to_generic):,} brand → generic mappings")
print(f"     - {len(generic_to_brand):,} generic → brand mappings")

del df_rxnrel, df_relationships

# STEP 3: Load NADAC Data 
print("\n[3/4] Loading NADAC dataset...")

df_nadac = pd.read_csv(NADAC_FILE, dtype=str)

print(f"   Loaded {len(df_nadac):,} rows from NADAC")

# helper functions 
def lookup_rxcui_from_ndc(ndc):
    clean_ndc = str(ndc).replace('-', '').strip().zfill(11)
    return ndc_to_rxcui.get(clean_ndc)

def find_related_rxcui(rxcui, is_brand):
    """Find the related brand or generic RxCUI."""
    rxcui = str(rxcui).strip()
    
    brand_rxcui = None
    generic_rxcui = None

    if is_brand:
        brand_rxcui = rxcui
        generic_rxcui = brand_to_generic.get(rxcui)
        if not generic_rxcui:
            generic_rxcui = generic_to_brand.get(rxcui)
    else:
        generic_rxcui = rxcui
        brand_rxcui = generic_to_brand.get(rxcui)
        if not brand_rxcui:
            brand_rxcui = brand_to_generic.get(rxcui)

    return brand_rxcui, generic_rxcui

# STEP 4: Process NADAC Row by Row
print("\n[4/4] Processing NADAC data row-by-row...")

processed_count = 0
skipped_count = 0
no_rxcui_count = 0
created_files = set()
relationship_found_count = 0

for index, row in tqdm(df_nadac.iterrows(), total=len(df_nadac), desc="Processing"):
    try:
        ndc = str(row.get('NDC', '')).strip()
        if not ndc or ndc == 'nan':
            skipped_count += 1
            continue
        
        drug_name = str(row.get('NDC Description', 'Unknown Drug')).strip()
        
        price = None
        for price_col in ['New NADAC Per Unit', 'Old NADAC Per Unit']:
            if price_col in row and row[price_col]:
                try:
                    price = float(row[price_col])
                    if price > 0:
                        break
                except (ValueError, TypeError):
                    continue
        
        if price is None or price <= 0:
            skipped_count += 1
            continue
        
        date = None
        for date_col in ['Effective Date', 'Effective_Date']:
            if date_col in row and row[date_col]:
                date = str(row[date_col]).strip()
                if date != 'nan':
                    break
        
        if not date or date == 'nan':
            skipped_count += 1
            continue
        
        classification = str(row.get('Classification for Rate Setting', 
                                    row.get('Classification', 'G'))).strip()
        is_brand = (classification == 'B')
        
        rxcui = lookup_rxcui_from_ndc(ndc)
        
        if rxcui is None:
            no_rxcui_count += 1
            continue
        
        rxcui = str(rxcui).strip()
        
        brand_rxcui, generic_rxcui = find_related_rxcui(rxcui, is_brand)
        
        if generic_rxcui and brand_rxcui:
            relationship_found_count += 1
        
        filename = os.path.join(PRICES_DIR, f'{rxcui}.json')
        
        if not os.path.exists(filename):
            data = {
                "RxCUI": rxcui,
                "Name": drug_name,
                "IsBrand": is_brand,
                "Brand_RxCUI": brand_rxcui,
                "Generic_RxCUI": generic_rxcui,
                "prices": {}
            }
            created_files.add(rxcui)
        else:
            with open(filename, 'r') as f:
                data = json.load(f)
        
        if brand_rxcui and not data.get('Brand_RxCUI'):
            data['Brand_RxCUI'] = brand_rxcui
        if generic_rxcui and not data.get('Generic_RxCUI'):
            data['Generic_RxCUI'] = generic_rxcui

        if ndc not in data['prices']:
            data['prices'][ndc] = {}
        
        data['prices'][ndc][date] = price
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        processed_count += 1
        
    except Exception as e:
        skipped_count += 1
        continue

# summary
print("PREPROCESSING COMPLETE")
print(f"Processed: {processed_count:,} rows successfully")
print(f"Created: {len(created_files):,} unique drug JSON files")
print(f"Found relationships: {relationship_found_count:,} drugs have brand/generic links")
print(f"Skipped: {skipped_count:,} rows (invalid data)")
print(f"No RxCUI found: {no_rxcui_count:,} NDCs")
print(f"Output directory: {PRICES_DIR}/")

# create search index
if created_files:
    print("\nCreating search index...")
    
    search_index = {}
    for filename in os.listdir(PRICES_DIR):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(PRICES_DIR, filename), 'r') as f:
                    data = json.load(f)
                    drug_name = data.get('Name', '').lower()
                    rxcui = data.get('RxCUI')
                    if drug_name and rxcui:
                        search_index[drug_name] = {
                            "rxcui": rxcui,
                            "name": data.get('Name'),
                            "is_brand": data.get('IsBrand', False)
                        }
            except:
                continue
    
    search_index_path = os.path.join(DATA_DIR, 'search_index.json')
    with open(search_index_path, 'w') as f:
        json.dump(search_index, f, indent=2)
    
    print(f"Created search index with {len(search_index):,} drugs")
    print(f"Saved to: {search_index_path}")