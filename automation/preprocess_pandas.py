import pandas as pd
import json
import os
import re 
from tqdm import tqdm
import numpy as np 
import math 

# configuration
DATA_DIR = '../src/lib/data'
PRICES_DIR = '../src/lib/data/prices'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PRICES_DIR, exist_ok=True)

# file paths (assumes standard RxNorm files are present)
NADAC_FILE = 'nadac-comparison.csv'
RXNSAT_FILE = 'RXNSAT.RRF'
RXNREL_FILE = 'RXNREL.RRF'
RXNCONSO_FILE = 'RXNCONSO.RRF'

print("=" * 60)
print("NADAC + RxNorm Preprocessing (FIXED FORM EXTRACTION)")
print("=" * 60)


# STEP 1: load RxNorm RXNSAT and RXNCONSO for all lookups
print("\n[1/5] Loading and preparing RxNorm files for all lookups...")

# define columns for RXNSAT
rxnsat_columns = [
    'RXCUI', 'LUI', 'SUI', 'RXAUI', 'STYPE', 'CODE', 'ATUI', 
    'SATUI', 'ATN', 'SAB', 'ATV', 'SUPPRESS', 'CVF', 'EXTRA'
]
df_rxnsat = pd.read_csv(RXNSAT_FILE, sep='|', header=None, names=rxnsat_columns, dtype=str, low_memory=False)

# define columns for RXNCONSO
conso_cols = [
    'RXCUI', 'SAB', 'TTY', 'STR', 'SUPPRESS'
]

try:
    df_rxnconso = pd.read_csv(RXNCONSO_FILE, sep='|', header=None, names=conso_cols, 
                             dtype=str, low_memory=False, usecols=[0, 11, 12, 14, 16])
    print(f"    - RXNCONSO loaded with {len(df_rxnconso):,} rows.")
    
    # TTY lookup
    df_tty = df_rxnconso[df_rxnconso['SAB'] == 'RXNORM'][['RXCUI', 'TTY']].drop_duplicates(subset=['RXCUI'], keep='first')
    rxcui_to_tty = dict(zip(df_tty['RXCUI'], df_tty['TTY']))
    
except FileNotFoundError:
    print(f"    WARNING: {RXNCONSO_FILE} not found. Skipping official name mapping and TTY lookup.")
    df_rxnconso = pd.DataFrame(columns=conso_cols) 
    rxcui_to_tty = {}
except ValueError as e:
    print(f"    ERROR: Failed to read {RXNCONSO_FILE}. Check the number of pipe-separated fields or 'usecols' indices.")
    print(f"    Original Error: {e}")
    df_rxnconso = pd.DataFrame(columns=conso_cols)
    rxcui_to_tty = {}


# NDC to RxCUI map
df_rxcui_map = df_rxnsat[df_rxnsat['ATN'] == 'NDC'][['ATV', 'RXCUI']].copy()
df_rxcui_map['NDC_KEY'] = (
    df_rxcui_map['ATV'].str.replace('-', '', regex=False).str.strip().str.zfill(11)
)
ndc_to_rxcui = dict(zip(df_rxcui_map['NDC_KEY'], df_rxcui_map['RXCUI']))
del df_rxcui_map
print(f"    created NDC-to-RxCUI map with {len(ndc_to_rxcui):,} unique NDC keys.")


# official name lookup
if not df_rxnconso.empty:
    OFFICIAL_NAME_TTYS = ['SCD', 'SBD', 'PT', 'SCDF', 'SBDF', 'IN'] 
    SUPPRESSED_FLAGS = ['Y', 'O']
    
    df_official_names = df_rxnconso[
        (df_rxnconso['SAB'] == 'RXNORM') & 
        (df_rxnconso['TTY'].isin(OFFICIAL_NAME_TTYS)) &
        (~df_rxnconso['SUPPRESS'].isin(SUPPRESSED_FLAGS))
    ].drop_duplicates(subset=['RXCUI'], keep='first')[['RXCUI', 'STR']]
    name_lookup = dict(zip(df_official_names['RXCUI'], df_official_names['STR']))
    print(f"    extracted {len(name_lookup):,} official RxNorm names (including ingredients).")
else:
    name_lookup = {}

# other lookups
df_manuf_name = df_rxnsat[
    df_rxnsat['ATN'].isin(['LBL', 'MANU']) & 
    df_rxnsat['SAB'].isin(['RXNORM', 'MTHSPL']) 
][['RXCUI', 'ATV']].drop_duplicates(subset=['RXCUI'], keep='first').copy()
manuf_name_lookup = dict(zip(df_manuf_name['RXCUI'], df_manuf_name['ATV']))
del df_manuf_name

df_strength = df_rxnsat[
    df_rxnsat['ATN'].isin(['STRENGTH', 'SCD_STRING'])
].sort_values(by=['ATN'], ascending=False).drop_duplicates(subset=['RXCUI'], keep='first')[['RXCUI', 'ATV']]
strength_lookup = dict(zip(df_strength['RXCUI'], df_strength['ATV']))
del df_strength

# form lookup removed - will be extracted from drug names using regex
form_lookup = {}
print("    form lookup from RXNSAT disabled (DF attribute doesn't exist)")
print("    forms will be extracted from drug names using comprehensive regex")

del df_rxnsat


# STEP 2: load RxNorm RXNREL
print("\n[2/5] Loading and preparing RXNREL for relationship mapping...")
rxnrel_columns = [
    'RXCUI1', 'RXAUI1', 'STYPE1', 'REL', 'RXCUI2', 'RXAUI2', 
    'STYPE2', 'RELA', 'RUI', 'SRUI', 'SAB', 'SL', 'DIR', 
    'RG', 'SUPPRESS', 'CVF'
]
df_rxnrel = pd.read_csv(RXNREL_FILE, sep='|', header=None, names=rxnrel_columns, 
                         usecols=range(len(rxnrel_columns)), dtype=str, low_memory=False)

df_rxnrel = df_rxnrel[df_rxnrel['SAB'] == 'RXNORM'].copy()

# ingredient mapping
df_ingredient_rel = df_rxnrel[
    df_rxnrel['RELA'] == 'has_ingredient'
][['RXCUI1', 'RXCUI2']].rename(columns={'RXCUI1': 'Product_RxCUI', 'RXCUI2': 'Ingredient_RxCUI_Found'})
product_to_ingredient_map = dict(zip(df_ingredient_rel['Product_RxCUI'], df_ingredient_rel['Ingredient_RxCUI_Found']))
del df_ingredient_rel

# brand/generic relationship mapping
RELA_FILTERS = ['tradename_of', 'brand_name_of', 'has_tradename', 'has_brand_name']
df_relationships = df_rxnrel[df_rxnrel['RELA'].isin(RELA_FILTERS)].copy()
del df_rxnrel

print("    building bidirectional relationship lookup tables...")
brand_to_generic_map = {}
generic_to_brand_map = {}

for _, row in df_relationships.iterrows():
    rxcui1 = str(row['RXCUI1']).strip()
    rxcui2 = str(row['RXCUI2']).strip()
    rela = str(row['RELA']).strip()
    
    if rela in ['tradename_of', 'brand_name_of']:
        brand_to_generic_map[rxcui1] = rxcui2
        if rxcui2 not in generic_to_brand_map:
            generic_to_brand_map[rxcui2] = rxcui1
    elif rela in ['has_tradename', 'has_brand_name']:
        generic_to_brand_map[rxcui1] = rxcui2
        if rxcui2 not in brand_to_generic_map:
            brand_to_generic_map[rxcui2] = rxcui1

print(f"    built {len(brand_to_generic_map):,} brand to generic mappings")
print(f"    built {len(generic_to_brand_map):,} generic to brand mappings")
del df_relationships


# STEP 3: load NADAC and map RxCUI
print("\n[3/5] Loading NADAC dataset and mapping RxCUI...")

df_nadac = pd.read_csv(NADAC_FILE, dtype=str)
initial_rows = len(df_nadac)

df_nadac['NDC_KEY'] = (
    df_nadac['NDC']
    .fillna('')
    .str.replace('-', '', regex=False)
    .str.strip()
    .str.zfill(11)
)

df_nadac['RXCUI'] = df_nadac['NDC_KEY'].map(ndc_to_rxcui)
df_nadac.drop(columns=['NDC_KEY'], inplace=True)

mapped_count = df_nadac['RXCUI'].notna().sum()
success_rate = mapped_count / initial_rows if initial_rows > 0 else 0

print(f"    total NADAC rows: {initial_rows:,}")
print(f"    successfully mapped to RxCUI: {mapped_count:,}")
print(f"    RxCUI mapping success rate: {success_rate:.2%}")


# STEP 4: data cleaning and relationship mapping
print("\n[4/5] Cleaning data and mapping relationships...")

price_col = next(col for col in ['New NADAC Per Unit', 'Old NADAC Per Unit'] if col in df_nadac.columns)
date_col = next(col for col in ['Effective Date', 'Effective_Date'] if col in df_nadac.columns)
classification_col = next(col for col in ['Classification for Rate Setting', 'Classification'] if col in df_nadac.columns)

df_nadac.rename(columns={
    'NDC Description': 'Name',
    price_col: 'Price',
    date_col: 'Date',
}, inplace=True)

df_processed = df_nadac[df_nadac['RXCUI'].notna()].copy()
df_processed['Price'] = pd.to_numeric(df_processed['Price'], errors='coerce')
df_processed = df_processed[df_processed['Price'] > 0].copy()
df_processed.dropna(subset=['Date'], inplace=True)
df_processed['RXCUI'] = df_processed['RXCUI'].astype(str).str.strip()
df_processed['Date'] = df_processed['Date'].astype(str).str.strip()
df_processed['IsBrand'] = (df_processed[classification_col].str.strip().str.upper() == 'B')


print("    mapping brand/generic relationships with fallback logic...")

def find_related_rxcui(rxcui, is_brand):
    rxcui = str(rxcui).strip()
    brand_rxcui = None
    generic_rxcui = None

    if is_brand:
        brand_rxcui = rxcui
        generic_rxcui = brand_to_generic_map.get(rxcui)
        if not generic_rxcui:
            generic_rxcui = generic_to_brand_map.get(rxcui)
    else:
        generic_rxcui = rxcui
        brand_rxcui = generic_to_brand_map.get(rxcui)
        if not brand_rxcui:
            brand_rxcui = brand_to_generic_map.get(rxcui)

    return brand_rxcui, generic_rxcui

results = df_processed.apply(
    lambda row: find_related_rxcui(row['RXCUI'], row['IsBrand']), 
    axis=1
)
df_processed['Brand_RxCUI'] = results.apply(lambda x: x[0] if x[0] else '')
df_processed['Generic_RxCUI'] = results.apply(lambda x: x[1] if x[1] else '')


df_processed['Ingredient_RxCUI_Internal'] = df_processed['RXCUI'].map(product_to_ingredient_map).fillna('')
df_processed['Manufacturer_Name'] = df_processed['RXCUI'].map(manuf_name_lookup).fillna('') 
df_processed['Strength'] = df_processed['RXCUI'].map(strength_lookup).fillna('')
df_processed['Form'] = df_processed['RXCUI'].map(form_lookup).fillna('')

df_processed['Name'] = df_processed['RXCUI'].map(name_lookup).fillna(df_processed['Name'])


# manufacturer fallback
manufacturer_pattern = r'\[([^\]]+)\]'
mask_missing_manuf = (df_processed['Manufacturer_Name'] == '')

if mask_missing_manuf.any():
    print("    applying vectorized regex fallback for missing manufacturer (extracting [bracketed name])...")
    
    def get_first_bracketed(name_series):
        matches = name_series.str.findall(manufacturer_pattern)
        return matches.apply(lambda x: x[0] if x else '')

    manufacturer_fb = get_first_bracketed(df_processed.loc[mask_missing_manuf, 'Name'])

    df_processed.loc[mask_missing_manuf, 'Manufacturer_Name'] = np.where(
        df_processed.loc[mask_missing_manuf, 'Manufacturer_Name'] == '',
        manufacturer_fb,
        df_processed.loc[mask_missing_manuf, 'Manufacturer_Name']
    )

# strength/form fallback
mask_missing_strength_form = (df_processed['Strength'] == '') | (df_processed['Form'] == '')

if mask_missing_strength_form.any():
    print("    applying comprehensive regex fallback for missing strength/form...")
    
    strength_pattern = r'(\d+\.?\d*\s*[A-Z]{1,4}(?:/[A-Z]{1,4})?)'
    
    form_words = [
        'Extended Release Oral Tablet',
        'Extended Release Oral Capsule',
        'Disintegrating Oral Tablet',
        'Delayed Release Oral Tablet',
        'Delayed Release Oral Capsule',
        'Metered Dose Nasal Spray',
        'Powder for Oral Suspension',
        'Mucous Membrane Topical Solution',
        'Inhalant Powder for Oral Inhalation',
        'Metered Dose Inhaler',
        'Dry Powder Inhaler',
        'Injectable Solution',
        'Injectable Suspension',
        'Intraperitoneal Solution',
        'Prefilled Syringe',
        'Pen Injector',
        'Transdermal System',
        'Ophthalmic Solution',
        'Ophthalmic Suspension',
        'Ophthalmic Ointment',
        'Oral Tablet',
        'Oral Capsule',
        'Oral Solution',
        'Oral Suspension',
        'Oral Lozenge',
        'Oral Granules',
        'Oral Powder',
        'Oral Pellet',
        'Oral Gel',
        'Chewable Tablet',
        'Sublingual Tablet',
        'Topical Cream',
        'Topical Gel',
        'Topical Ointment',
        'Topical Solution',
        'Topical Lotion',
        'Topical Spray',
        'Topical Foam',
        'Topical Powder',
        'Nasal Spray',
        'Rectal Suppository',
        'Medicated Pad',
        'Medicated Shampoo',
        'Medicated Patch',
        'Medicated Liquid Soap',
        'Inhalation Solution',
        'Drug Implant',
        'Mucosal Spray',
        'Tablet',
        'Capsule',
        'Injection',
        'Solution',
        'Suspension',
        'Ointment',
        'Cream',
        'Lotion',
        'Syrup',
        'Powder',
        'Aerosol',
        'Patch',
        'Gel',
        'Kit',
        'Vial',
        'Cartridge',
        'Injector',
        'Mouthwash',
    ]
    form_pattern = r'\b(' + '|'.join(form_words) + r')(?:\s*\[|$)'

    strength_fb = df_processed.loc[mask_missing_strength_form, 'Name'].str.extract(
        strength_pattern, expand=False, flags=re.IGNORECASE
    ).fillna('')

    form_fb = df_processed.loc[mask_missing_strength_form, 'Name'].str.extract(
        form_pattern, expand=False, flags=re.IGNORECASE
    ).fillna('')
    
    df_processed.loc[mask_missing_strength_form, 'Strength'] = np.where(
        df_processed.loc[mask_missing_strength_form, 'Strength'] == '',
        strength_fb,
        df_processed.loc[mask_missing_strength_form, 'Strength']
    )

    df_processed.loc[mask_missing_strength_form, 'Form'] = np.where(
        df_processed.loc[mask_missing_strength_form, 'Form'] == '',
        form_fb,
        df_processed.loc[mask_missing_strength_form, 'Form']
    )


missing_name = df_processed['Manufacturer_Name'].eq('').sum()
missing_strength = df_processed['Strength'].eq('').sum()
missing_form = df_processed['Form'].eq('').sum()

print(f"    diagnostics on mapped attributes (total rows: {len(df_processed):,})")
print(f"      rows missing manufacturer (name): {missing_name:,}")
print(f"      rows missing strength: {missing_strength:,}")
print(f"      rows missing form: {missing_form:,}")

print(f"    data cleaned and attributes mapped. {len(df_processed):,} rows remaining in pipeline.")


# STEP 5: grouping and JSON output
print("\n[5/5] Grouping and writing JSON files...")

OUTPUT_COLS = ['NDC', 'Price', 'Date', 'RXCUI', 'Name', 'IsBrand', 'Brand_RxCUI', 
               'Generic_RxCUI', 'Manufacturer_Name', 'Strength', 'Form'] 
df_final = df_processed[OUTPUT_COLS].copy()

INGREDIENT_CLEAN_TERMS = r'\b(MG|MCG|ML|GM|UNIT|TAB|CAP|VIAL|CAN|BAR|HCL|SULFATE|ACETATE|POWDER|SOLUTION|TABLET|OINTMENT|SUSPENSION|INJECTION|CAPSULE|CREAM|LOTION|SYRUP|AEROSOL|PATCH|GEL|KIT|ORAL|TOPICAL|PER|ACTUAL|BASE|CONCENTRATE|ELIXIR|SHAMPOO|SPRAY|SUPPOSITORY|SYRINGE|LIQUID|Ophthalmic|Suspension|Drops|Cream|Lotion|Foam)\b'
INGREDIENT_CLEAN_NUMBERS = r'[\d\.\/]+'
BRAND_MARKER_PATTERN = r'\s*\[[^\]]+\]\s*$'


def build_drug_data(group):
    first_row = group.iloc[0]
    
    prices_nested = group.groupby('NDC', group_keys=False).apply(
        lambda x: dict(zip(x['Date'], x['Price'])),
    ).to_dict()

    rxcui = str(first_row['RXCUI'])
    brand_rxcui = str(first_row['Brand_RxCUI']) if pd.notna(first_row['Brand_RxCUI']) else ""
    generic_rxcui = str(first_row['Generic_RxCUI']) if pd.notna(first_row['Generic_RxCUI']) else ""
    
    best_manufacturer_name = str(first_row['Manufacturer_Name']) if pd.notna(first_row['Manufacturer_Name']) else ""
    
    if not best_manufacturer_name:
        brand_rows = group[group['IsBrand'] == True]
        if not brand_rows.empty and brand_rows.iloc[0]['Manufacturer_Name']:
            best_manufacturer_name = str(brand_rows.iloc[0]['Manufacturer_Name'])
        else:
            valid_manufs_series = group['Manufacturer_Name'][group['Manufacturer_Name'] != '']
            if not valid_manufs_series.empty:
                best_manufacturer_name = str(valid_manufs_series.mode().iloc[0])

    ingredient_rxcui_internal = str(first_row['Ingredient_RxCUI_Internal']) if first_row['Ingredient_RxCUI_Internal'] else ""
    full_drug_name = str(first_row['Name'])
    
    ingredient_name = name_lookup.get(ingredient_rxcui_internal, "")
    
    if not ingredient_name:
        temp_name = full_drug_name
        temp_name = re.sub(BRAND_MARKER_PATTERN, '', temp_name, flags=re.IGNORECASE).strip()
        temp_name = re.sub(INGREDIENT_CLEAN_NUMBERS, '', temp_name, flags=re.IGNORECASE).strip()
        temp_name = re.sub(INGREDIENT_CLEAN_TERMS, '', temp_name, flags=re.IGNORECASE).strip()
        temp_name = re.sub(r'\s+', ' ', temp_name).strip()
        
        if temp_name:
            ingredient_name = temp_name
        else:
            ingredient_name = full_drug_name.split(' ', 1)[0]
            
    if ingredient_name:
        ingredient_name = ingredient_name.title()

    strength = str(first_row['Strength']) if pd.notna(first_row['Strength']) else ""
    form = str(first_row['Form']) if pd.notna(first_row['Form']) else ""

    return {
        "RxCUI": rxcui,
        "Name": full_drug_name,
        "IsBrand": bool(first_row['IsBrand']),
        "Brand_RxCUI": brand_rxcui,
        "Generic_RxCUI": generic_rxcui, 
        "Ingredient_Name": ingredient_name,
        "Manufacturer_Name": best_manufacturer_name, 
        "Strength": strength,
        "Form": form,
        "prices": prices_nested
    }

grouped_data = df_processed.groupby('RXCUI')

total_groups = len(grouped_data)
print(f"    starting aggregation of {total_groups:,} unique RxCUIs into individual JSON files...")

processed_count = 0
created_files = set()
comparison_map = {} 

for rxcui, group in tqdm(grouped_data, desc="Writing JSON Files"):
    try:
        data = build_drug_data(group)
        filename = os.path.join(PRICES_DIR, f'{rxcui}.json')
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        processed_count += 1
        created_files.add(rxcui)

        brand_RxCUI = data['Brand_RxCUI']
        generic_RxCUI = data['Generic_RxCUI']
        # ... rest of code
        
    except Exception as e:
        print(f"\nERROR on RxCUI {rxcui}: {e}")
        import traceback
        traceback.print_exc()
        break  # stop after first error so we can see it

print("\n" + "=" * 60)
print("PREPROCESSING COMPLETE!")
print("=" * 60)
print(f"processed and aggregated: {processed_count:,} unique drugs")
print(f"created: {len(created_files):,} unique drug JSON files")


if created_files:
    print("\n[BONUS] Creating three search indexes...")
    
    search_index_all = {}
    search_index_has_pair = {} 
    
    for filename in os.listdir(PRICES_DIR):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(PRICES_DIR, filename), 'r') as f:
                    data = json.load(f)
                    
                drug_name_raw = data.get('Name', '')
                rxcui = data.get('RxCUI')
                
                if drug_name_raw and rxcui:
                    brand_mate = data.get('Brand_RxCUI', '')
                    generic_mate = data.get('Generic_RxCUI', '')
                    is_brand = data.get('IsBrand', False)

                    has_valid_pair = (brand_mate and generic_mate and brand_mate != generic_mate)

                    if is_brand:
                        mate_rxcui = generic_mate
                    else:
                        mate_rxcui = brand_mate
                    
                    mate_name = name_lookup.get(mate_rxcui, "") if mate_rxcui else ""
                    ingredient_name = data.get('Ingredient_Name', "") 
                    manufacturer_name = data.get('Manufacturer_Name', "") 
                    
                    entry = {
                        "rxcui": rxcui,
                        "name": drug_name_raw,
                        "is_brand": is_brand,
                        "mate_rxcui": mate_rxcui,
                        "mate_name": mate_name,
                        "ingredient_name": ingredient_name, 
                        "manufacturer_name": manufacturer_name, 
                    }
                    
                    search_index_all[rxcui] = entry
                    
                    if has_valid_pair:
                        tag = 'BRAND' if is_brand else 'GENERIC'
                        unique_search_key = f"{drug_name_raw.lower()} [{tag}]"
                        search_index_has_pair[unique_search_key] = entry
                        
            except:
                continue
    
    search_index_all_path = os.path.join(DATA_DIR, 'search_index_all.json')
    with open(search_index_all_path, 'w') as f:
        json.dump(search_index_all, f, indent=2)
    print(f"created index 1 (all drugs - keyed by RxCUI) with {len(search_index_all):,} entries.")

    search_index_has_pair_path = os.path.join(DATA_DIR, 'search_index_has_pair.json')
    with open(search_index_has_pair_path, 'w') as f:
        json.dump(search_index_has_pair, f, indent=2)
    print(f"created index 2 (drugs with pair - has_pair) with {len(search_index_has_pair):,} entries.")

    comparison_map_path = os.path.join(DATA_DIR, 'comparison_map.json')
    with open(comparison_map_path, 'w') as f:
        json.dump(comparison_map, f, indent=2)
    print(f"created index 3 (brand/generic comparison map) with {len(comparison_map):,} entries.")
    
    print(f"saved all indexes to: {DATA_DIR}/")