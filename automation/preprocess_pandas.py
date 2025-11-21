import pandas as pd
import json
import os
import re 
from tqdm import tqdm
import numpy as np 
import math 

# --- Configuration ---
DATA_DIR = 'data'
PRICES_DIR = 'data/prices'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PRICES_DIR, exist_ok=True)

# File paths (Assumes standard RxNorm files are present)
NADAC_FILE = 'nadac-comparison.csv'
RXNSAT_FILE = 'RXNSAT.RRF'
RXNREL_FILE = 'RXNREL.RRF'
RXNCONSO_FILE = 'RXNCONSO.RRF' # Required for official SBD/SCD names

print("=" * 60)
print("NADAC + RxNorm Preprocessing (Ingredient/VA Class fields removed)")
print("=" * 60)


# --- STEP 1: Load RxNorm RXNSAT and RXNCONSO for all lookups ---
print("\n[1/5] Loading and preparing RxNorm files for all lookups...")

# Define columns for RXNSAT
rxnsat_columns = [
    'RXCUI', 'LUI', 'SUI', 'RXAUI', 'STYPE', 'CODE', 'ATUI', 
    'SATUI', 'ATN', 'SAB', 'ATV', 'SUPPRESS', 'CVF', 'EXTRA'
]
df_rxnsat = pd.read_csv(RXNSAT_FILE, sep='|', header=None, names=rxnsat_columns, dtype=str, low_memory=False)

# Define columns for RXNCONSO (We only need 5 columns for the official name lookup)
conso_cols = [
    'RXCUI', 'SAB', 'TTY', 'STR', 'SUPPRESS'
]

try:
    # NOTE: Assuming the correct column indices are [0, 11, 12, 14, 16] for RRF files
    df_rxnconso = pd.read_csv(RXNCONSO_FILE, sep='|', header=None, names=conso_cols, 
                             dtype=str, low_memory=False, usecols=[0, 11, 12, 14, 16])
    print(f"    - RXNCONSO loaded with {len(df_rxnconso):,} rows.")
    
    # 1a. TTY Lookup: Map every RxCUI to its Concept Type (TTY)
    df_tty = df_rxnconso[df_rxnconso['SAB'] == 'RXNORM'][['RXCUI', 'TTY']].drop_duplicates(subset=['RXCUI'], keep='first')
    rxcui_to_tty = dict(zip(df_tty['RXCUI'], df_tty['TTY']))
    
except FileNotFoundError:
    print(f"    ⚠️ WARNING: {RXNCONSO_FILE} not found. Skipping official name mapping and TTY lookup.")
    df_rxnconso = pd.DataFrame(columns=conso_cols) 
    rxcui_to_tty = {}
except ValueError as e:
    print(f"    ❌ ERROR: Failed to read {RXNCONSO_FILE}. Check the number of pipe-separated fields or 'usecols' indices.")
    print(f"    Original Error: {e}")
    df_rxnconso = pd.DataFrame(columns=conso_cols)
    rxcui_to_tty = {}


# --- 1b. NDC to RxCUI Map ---
# The NDC key must be consistently cleaned and padded to 11 digits for accurate matching.
df_rxcui_map = df_rxnsat[df_rxnsat['ATN'] == 'NDC'][['ATV', 'RXCUI']].copy()
df_rxcui_map['NDC_KEY'] = (
    df_rxcui_map['ATV'].str.replace('-', '', regex=False).str.strip().str.zfill(11)
)
ndc_to_rxcui = dict(zip(df_rxcui_map['NDC_KEY'], df_rxcui_map['RXCUI']))
del df_rxcui_map
print(f"    ✓ Created NDC-to-RxCUI map with {len(ndc_to_rxcui):,} unique NDC keys.")


# --- 1c. Official Name Lookup (SCD/SBD/PT + IN for Ingredients) ---
if not df_rxnconso.empty:
    # Include IN (Ingredient) TTY here so we can look up the Ingredient name later.
    OFFICIAL_NAME_TTYS = ['SCD', 'SBD', 'PT', 'SCDF', 'SBDF', 'IN'] 
    SUPPRESSED_FLAGS = ['Y', 'O']
    
    df_official_names = df_rxnconso[
        (df_rxnconso['SAB'] == 'RXNORM') & 
        (df_rxnconso['TTY'].isin(OFFICIAL_NAME_TTYS)) &
        (~df_rxnconso['SUPPRESS'].isin(SUPPRESSED_FLAGS))
    ].drop_duplicates(subset=['RXCUI'], keep='first')[['RXCUI', 'STR']]
    name_lookup = dict(zip(df_official_names['RXCUI'], df_official_names['STR']))
    print(f"    ✓ Extracted {len(name_lookup):,} Official RxNorm Names (including Ingredients).")
else:
    name_lookup = {}

# --- 1d-1f. Other Lookups (Manufacturer, Strength, Form) ---
# VA Class lookup REMOVED per user request.

df_manuf_name = df_rxnsat[
    # Look for Labeler (LBL) or Manufacturer (MANU) attributes
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

df_form = df_rxnsat[
    df_rxnsat['ATN'] == 'DF' # Dosage Form
][['RXCUI', 'ATV']].drop_duplicates(subset=['RXCUI'], keep='first')
form_lookup = dict(zip(df_form['RXCUI'], df_form['ATV']))
del df_form, df_rxnsat # Clean up memory


# --- STEP 2: Load RxNorm RXNREL (Brand/Generic and Ingredient relationships) ---
print("\n[2/5] Loading and preparing RXNREL for relationship mapping...")
rxnrel_columns = [
    'RXCUI1', 'RXAUI1', 'STYPE1', 'REL', 'RXCUI2', 'RXAUI2', 
    'STYPE2', 'RELA', 'RUI', 'SRUI', 'SAB', 'SL', 'DIR', 
    'RG', 'SUPPRESS', 'CVF'
]
df_rxnrel = pd.read_csv(RXNREL_FILE, sep='|', header=None, names=rxnrel_columns, 
                         usecols=range(len(rxnrel_columns)), dtype=str, low_memory=False)

df_rxnrel = df_rxnrel[df_rxnrel['SAB'] == 'RXNORM'].copy()

# 2a. Ingredient Mapping (Product -> Ingredient)
# We keep this map to attempt the *name* lookup, even if we remove the RxCUI field from output.
df_ingredient_rel = df_rxnrel[
    df_rxnrel['RELA'] == 'has_ingredient'
][['RXCUI1', 'RXCUI2']].rename(columns={'RXCUI1': 'Product_RxCUI', 'RXCUI2': 'Ingredient_RxCUI_Found'})
product_to_ingredient_map = dict(zip(df_ingredient_rel['Product_RxCUI'], df_ingredient_rel['Ingredient_RxCUI_Found']))
del df_ingredient_rel

# 2b. Brand/Generic Relationship Mapping (Prioritizing SCD/SBD) (unchanged)
RELA_FILTERS = ['tradename_of', 'brand_name_of', 'has_tradename', 'has_brand_name']
df_relationships = df_rxnrel[df_rxnrel['RELA'].isin(RELA_FILTERS)].copy()
del df_rxnrel

TTY_PRIORITY = {'SCD': 1, 'SCDG': 1, 'SCDF': 1, 'SBDF': 1, 'SBD': 1, 'GPCK': 2, 'BPCK': 2, 'IN': 3} 

def get_tty_rank(rxcui):
    tty = rxcui_to_tty.get(rxcui, 'Unknown')
    return TTY_PRIORITY.get(tty, 4)

df_relationships['TTY_Rank'] = df_relationships['RXCUI2'].apply(get_tty_rank)

def select_best_mate(df):
    if df.empty:
        return None
    best_mate = df.sort_values(by='TTY_Rank', ascending=True).iloc[0]['RXCUI2']
    return best_mate

df_brand_to_generic_lookup = df_relationships[
    df_relationships['RELA'].isin(['tradename_of', 'brand_name_of'])
].groupby('RXCUI1').apply(select_best_mate, include_groups=False).reset_index(name='Generic_RxCUI_Found')
brand_to_generic_map = dict(zip(df_brand_to_generic_lookup['RXCUI1'], df_brand_to_generic_lookup['Generic_RxCUI_Found']))
del df_brand_to_generic_lookup

df_generic_to_brand_lookup = df_relationships[
    df_relationships['RELA'].isin(['has_tradename', 'has_brand_name'])
].groupby('RXCUI1').apply(select_best_mate, include_groups=False).reset_index(name='Brand_RxCUI_Found')
generic_to_brand_map = dict(zip(df_generic_to_brand_lookup['RXCUI1'], df_generic_to_brand_lookup['Brand_RxCUI_Found']))
del df_generic_to_brand_lookup, df_relationships


# --- STEP 3: Load NADAC and Vectorize NDC → RxCUI Mapping ---
print("\n[3/5] Loading NADAC dataset and mapping RxCUI...")

df_nadac = pd.read_csv(NADAC_FILE, dtype=str)
initial_rows = len(df_nadac)

# 3a. Clean NDC key (must match the key generation in Step 1b exactly)
df_nadac['NDC_KEY'] = (
    df_nadac['NDC']
    .fillna('')
    .str.replace('-', '', regex=False)
    .str.strip()
    .str.zfill(11)
)

# 3b. Vectorized Mapping
df_nadac['RXCUI'] = df_nadac['NDC_KEY'].map(ndc_to_rxcui)
df_nadac.drop(columns=['NDC_KEY'], inplace=True)

# 3c. 🚨 CRITICAL DIAGNOSTIC: Check mapping success 🚨
mapped_count = df_nadac['RXCUI'].notna().sum()
success_rate = mapped_count / initial_rows if initial_rows > 0 else 0

print(f"    Total NADAC rows: {initial_rows:,}")
print(f"    Successfully mapped to RxCUI: {mapped_count:,}")
print(f"    RxCUI Mapping Success Rate: {success_rate:.2%} ⬅️ This is likely the source of all missing data.")


# --- STEP 4: Data Cleaning, Typing, and Hyper-Vectorized Relationship Mapping ---
print("\n[4/5] Cleaning data and mapping relationships...")

# 4a. Standardize column names and types
price_col = next(col for col in ['New NADAC Per Unit', 'Old NADAC Per Unit'] if col in df_nadac.columns)
date_col = next(col for col in ['Effective Date', 'Effective_Date'] if col in df_nadac.columns)
classification_col = next(col for col in ['Classification for Rate Setting', 'Classification'] if col in df_nadac.columns)

df_nadac.rename(columns={
    'NDC Description': 'Name',
    price_col: 'Price',
    date_col: 'Date',
}, inplace=True)

# Data Filtering and Cleaning
df_processed = df_nadac[df_nadac['RXCUI'].notna()].copy() # Only proceed with mapped RxCUIs
df_processed['Price'] = pd.to_numeric(df_processed['Price'], errors='coerce')
df_processed = df_processed[df_processed['Price'] > 0].copy()
df_processed.dropna(subset=['Date'], inplace=True) # RXCUI already handled
df_processed['RXCUI'] = df_processed['RXCUI'].astype(str).str.strip()
df_processed['Date'] = df_processed['Date'].astype(str).str.strip()
df_processed['IsBrand'] = (df_processed[classification_col].str.strip().str.upper() == 'B')


# 4b. Hyper-Vectorized Relationship Mapping (Brand/Generic Mates) (unchanged)
print("    → Mapping Brand/Generic Mates (Prioritizing SCD/SBD concepts)...")

df_processed['Mapped_Generic_RxCUI'] = df_processed['RXCUI'].map(brand_to_generic_map)
df_processed['Mapped_Brand_RxCUI'] = df_processed['RXCUI'].map(generic_to_brand_map)

# Initialize final columns as 'object' (string) dtype
df_processed['Generic_Mate_RxCUI'] = pd.Series([np.nan] * len(df_processed), dtype='object')
df_processed['Brand_Mate_RxCUI'] = pd.Series([np.nan] * len(df_processed), dtype='object')

brand_mask = df_processed['IsBrand']
generic_mask = ~df_processed['IsBrand']

df_processed.loc[brand_mask, 'Brand_Mate_RxCUI'] = df_processed.loc[brand_mask, 'RXCUI'] 
df_processed.loc[brand_mask, 'Generic_Mate_RxCUI'] = df_processed.loc[brand_mask, 'Mapped_Generic_RxCUI'] 

df_processed.loc[generic_mask, 'Generic_Mate_RxCUI'] = df_processed.loc[generic_mask, 'RXCUI']
df_processed.loc[generic_mask, 'Brand_Mate_RxCUI'] = df_processed.loc[generic_mask, 'Mapped_Brand_RxCUI']

df_processed.drop(columns=['Mapped_Generic_RxCUI', 'Mapped_Brand_RxCUI'], inplace=True)


# 4c. Map Ingredient RxCUI (FOR INTERNAL NAME LOOKUP ONLY) and other attributes
# NOTE: We map Ingredient_RxCUI here but DO NOT include it in final output.
df_processed['Ingredient_RxCUI_Internal'] = df_processed['RXCUI'].map(product_to_ingredient_map).fillna('')
df_processed['Manufacturer_Name'] = df_processed['RXCUI'].map(manuf_name_lookup).fillna('') 
df_processed['Strength'] = df_processed['RXCUI'].map(strength_lookup).fillna('')
df_processed['Form'] = df_processed['RXCUI'].map(form_lookup).fillna('')
# VA_Drug_Class REMOVED per user request.

# Overwrite 'Name' with the official RxNorm name (SCD/SBD)
df_processed['Name'] = df_processed['RXCUI'].map(name_lookup).fillna(df_processed['Name'])


# --- CRITICAL ATTRIBUTE FIXES (Vectorized Fallbacks) ---

# 1. Fallback for Manufacturer Name (Addressing the [calcitrene] example)
manufacturer_pattern = r'\[([^\]]+)\]'
mask_missing_manuf = (df_processed['Manufacturer_Name'] == '')

if mask_missing_manuf.any():
    print("    → Applying vectorized regex fallback for missing Manufacturer (Extracting [Bracketed Name])...")
    
    def get_first_bracketed(name_series):
        # Only extract from the subset that is missing the name
        matches = name_series.str.findall(manufacturer_pattern)
        return matches.apply(lambda x: x[0] if x else '')

    manufacturer_fb = get_first_bracketed(df_processed.loc[mask_missing_manuf, 'Name'])

    # Use np.where for robust assignment within the filtered loc block
    df_processed.loc[mask_missing_manuf, 'Manufacturer_Name'] = np.where(
        df_processed.loc[mask_missing_manuf, 'Manufacturer_Name'] == '', # Condition: If original is empty
        manufacturer_fb,                                                  # Use fallback
        df_processed.loc[mask_missing_manuf, 'Manufacturer_Name']         # Otherwise, keep original
    )

# 2. Fallback for Strength/Form
mask_missing_strength_form = (df_processed['Strength'] == '') | (df_processed['Form'] == '')

if mask_missing_strength_form.any():
    print("    → Applying vectorized regex fallback for missing Strength/Form (Optimized Regex)...")
    
    strength_pattern = r'(\d+\.?\d*\s*[A-Z]{1,4}(?:/[A-Z]{1,4})?)'
    
    form_words = [
        'Tablet', 'Capsule', 'Injection', 'Solution', 'Suspension', 'Ointment', 
        'Cream', 'Lotion', 'Syrup', 'Powder', 'Aerosol', 'Patch', 'Gel', 'Kit', 
        'Vial', 'Can', 'Bar', 'Inhalant'
    ]
    form_pattern = r'(' + '|'.join(form_words) + r')$'

    # Generate fallback series only for the rows that need it (subset index)
    strength_fb = df_processed.loc[mask_missing_strength_form, 'Name'].str.extract(
        strength_pattern, expand=False, flags=re.IGNORECASE
    ).fillna('')

    form_fb = df_processed.loc[mask_missing_strength_form, 'Name'].str.extract(
        form_pattern, expand=False, flags=re.IGNORECASE
    ).fillna('')
    
    # Use np.where() for robust conditional assignment within loc
    
    # Update Strength only where it is currently empty
    df_processed.loc[mask_missing_strength_form, 'Strength'] = np.where(
        df_processed.loc[mask_missing_strength_form, 'Strength'] == '', # Condition: If original is empty
        strength_fb,                                                     # Use fallback
        df_processed.loc[mask_missing_strength_form, 'Strength']         # Otherwise, keep original
    )

    # Update Form only where it is currently empty
    df_processed.loc[mask_missing_strength_form, 'Form'] = np.where(
        df_processed.loc[mask_missing_strength_form, 'Form'] == '',
        form_fb,
        df_processed.loc[mask_missing_strength_form, 'Form']
    )


# 4d. Attribute Mapping Diagnostics ---
missing_name = df_processed['Manufacturer_Name'].eq('').sum()
missing_strength = df_processed['Strength'].eq('').sum()
missing_form = df_processed['Form'].eq('').sum()

# Removed the confusing 'missing Ingredient RxCUI' check from print output
# missing_ingredient_rxcui = df_processed['Ingredient_RxCUI_Internal'].eq('').sum() 

print(f"    → Diagnostics on Mapped Attributes (Total rows: {len(df_processed):,})")
# print(f"      - Rows missing Ingredient RxCUI (Internal Check): {missing_ingredient_rxcui:,}") # REMOVED
print(f"      - Rows missing Manufacturer (Name): {missing_name:,}")
print(f"      - Rows missing Strength: {missing_strength:,}")
print(f"      - Rows missing Form: {missing_form:,}")


print(f"    ✓ Data cleaned and attributes mapped. {len(df_processed):,} rows remaining in pipeline.")


# --- STEP 5: Vectorized Grouping and JSON Output ---
print("\n[5/5] Grouping and writing JSON files...")

# REMOVED: 'VA_Drug_Class', 'Ingredient_RxCUI'
OUTPUT_COLS = ['NDC', 'Price', 'Date', 'RXCUI', 'Name', 'IsBrand', 'Brand_Mate_RxCUI', 
               'Generic_Mate_RxCUI', 'Manufacturer_Name', 'Strength', 'Form'] 
df_final = df_processed[OUTPUT_COLS].copy()

# New patterns for aggressive ingredient name extraction (outside the function for efficiency)
# Matches common units, forms, and dosage modifiers globally (case-insensitive)
INGREDIENT_CLEAN_TERMS = r'\b(MG|MCG|ML|GM|UNIT|TAB|CAP|VIAL|CAN|BAR|HCL|SULFATE|ACETATE|POWDER|SOLUTION|TABLET|OINTMENT|SUSPENSION|INJECTION|CAPSULE|CREAM|LOTION|SYRUP|AEROSOL|PATCH|GEL|KIT|ORAL|TOPICAL|PER|ACTUAL|BASE|CONCENTRATE|ELIXIR|SHAMPOO|SPRAY|SUPPOSITORY|SYRINGE|LIQUID|Ophthalmic|Suspension|Drops|Cream|Lotion|Foam)\b'
INGREDIENT_CLEAN_NUMBERS = r'[\d\.\/]+'
BRAND_MARKER_PATTERN = r'\s*\[[^\]]+\]\s*$'


def build_drug_data(group):
    """Aggregates a grouped RxCUI into a structured dictionary."""
    first_row = group.iloc[0]
    
    # Aggregation for prices: create a dictionary of NDC -> {Date -> Price}
    prices_nested = group.groupby('NDC', group_keys=False).apply(
        lambda x: dict(zip(x['Date'], x['Price'])),
        include_groups=False 
    ).to_dict()

    # Get the RxCUI values, ensuring they are not None/NaN before processing
    rxcui = str(first_row['RXCUI'])
    brand_rxcui = str(first_row['Brand_Mate_RxCUI']) if pd.notna(first_row['Brand_Mate_RxCUI']) else ""
    generic_rxcui = str(first_row['Generic_Mate_RxCUI']) if pd.notna(first_row['Generic_Mate_RxCUI']) else ""
    
    # --- MANUFACTURER NAME ---
    best_manufacturer_name = str(first_row['Manufacturer_Name']) if pd.notna(first_row['Manufacturer_Name']) else ""
    
    if not best_manufacturer_name:
        brand_rows = group[group['IsBrand'] == True]
        if not brand_rows.empty and brand_rows.iloc[0]['Manufacturer_Name']:
            best_manufacturer_name = str(brand_rows.iloc[0]['Manufacturer_Name'])
        else:
            # Fix: Use boolean masking to avoid FutureWarning
            valid_manufs_series = group['Manufacturer_Name'][group['Manufacturer_Name'] != '']
            if not valid_manufs_series.empty:
                best_manufacturer_name = str(valid_manufs_series.mode().iloc[0])


    # 🌟 INGREDIENT NAME EXTRACTION
    ingredient_rxcui_internal = str(first_row['Ingredient_RxCUI_Internal']) if first_row['Ingredient_RxCUI_Internal'] else ""
    full_drug_name = str(first_row['Name'])
    
    # 1. Attempt RxNorm lookup (Highest priority)
    ingredient_name = name_lookup.get(ingredient_rxcui_internal, "")
    
    # 2. Fallback: Aggressively parse the full drug name
    if not ingredient_name:
        temp_name = full_drug_name
        
        # A. Remove brand marker (e.g., [Calcitrene])
        temp_name = re.sub(BRAND_MARKER_PATTERN, '', temp_name, flags=re.IGNORECASE).strip()
        
        # B. Aggressive Global Cleanup: Remove all numbers, units, and forms globally
        # Remove all numbers and slashes
        temp_name = re.sub(INGREDIENT_CLEAN_NUMBERS, '', temp_name, flags=re.IGNORECASE).strip()
        
        # Remove all common units and forms (case-insensitive word boundaries)
        temp_name = re.sub(INGREDIENT_CLEAN_TERMS, '', temp_name, flags=re.IGNORECASE).strip()

        # Remove multiple spaces caused by stripping
        temp_name = re.sub(r'\s+', ' ', temp_name).strip()
        
        # C. Final result logic
        if temp_name:
            ingredient_name = temp_name
        else:
            # D. Last resort: use the first word of the original name
            ingredient_name = full_drug_name.split(' ', 1)[0]
            
    
    # Always ensure the final ingredient name is title-cased for presentation
    if ingredient_name:
        ingredient_name = ingredient_name.title()


    # Ensure other attributes are strings
    strength = str(first_row['Strength']) if pd.notna(first_row['Strength']) else ""
    form = str(first_row['Form']) if pd.notna(first_row['Form']) else ""


    return {
        "RxCUI": rxcui,
        "Name": full_drug_name,
        "IsBrand": bool(first_row['IsBrand']),
        
        "Brand_Mate_RxCUI": brand_rxcui,
        # CRITICAL FIX: Changed 'generic_mate_rxcui' (undefined) to 'generic_rxcui'
        "Generic_Mate_RxCUI": generic_rxcui, 
        
        "Ingredient_Name": ingredient_name, # FIXED/FALLBACK field
        
        "Manufacturer_Name": best_manufacturer_name, 
        "Strength": strength,
        "Form": form,
        "prices": prices_nested
    }

grouped_data = df_processed.groupby('RXCUI')

total_groups = len(grouped_data)
print(f"    → Starting aggregation of {total_groups:,} unique RxCUIs into individual JSON files...")

processed_count = 0
created_files = set()
comparison_map = {} 

for rxcui, group in tqdm(grouped_data, desc="Writing JSON Files"):
    try:
        data = build_drug_data(group)
        filename = os.path.join(PRICES_DIR, f'{rxcui}.json')
        
        # 1. Write the detailed JSON file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        processed_count += 1
        created_files.add(rxcui)

        # 2. Update the Brand/Generic Comparison Map (Symmetrical Pair)
        brand_mate_rxcui = data['Brand_Mate_RxCUI']
        generic_mate_rxcui = data['Generic_Mate_RxCUI']

        if brand_mate_rxcui and generic_mate_rxcui and brand_mate_rxcui != generic_mate_rxcui:
            
            # Using the official name lookup for the comparison map is safest
            brand_name = name_lookup.get(brand_mate_rxcui, 'Unknown Brand')
            generic_name = name_lookup.get(generic_mate_rxcui, 'Unknown Generic')

            comparison_map[brand_mate_rxcui] = {
                "rxcui": brand_mate_rxcui,
                "name": brand_name,
                "mate_rxcui": generic_mate_rxcui,
                "mate_name": generic_name,
                "type": "BRAND"
            }
            comparison_map[generic_mate_rxcui] = {
                "rxcui": generic_mate_rxcui,
                "name": generic_name,
                "mate_rxcui": brand_mate_rxcui,
                "mate_name": brand_name,
                "type": "GENERIC"
            }
        
    except Exception as e:
        # print(f"Error processing RxCUI {rxcui}: {e}") # We rely on this check for the fix above, but keeping it commented for clean output.
        continue


# --- Summary and Index Creation (Index creation updated) ---
print("\n" + "=" * 60)
print("PREPROCESSING COMPLETE!")
print("=" * 60)
print(f"✓ Processed and aggregated: {processed_count:,} unique drugs")
print(f"✓ Created: {len(created_files):,} unique drug JSON files")


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
                    
                    brand_mate = data.get('Brand_Mate_RxCUI')
                    generic_mate = data.get('Generic_Mate_RxCUI')

                    # Determine if this concept is the 'Brand' part of a pair (to avoid redundancy)
                    is_brand_part_of_pair = (rxcui == brand_mate and brand_mate != generic_mate)

                    # Get the mate info for the search index entry
                    mate_rxcui = generic_mate if is_brand_part_of_pair else brand_mate
                    mate_name = name_lookup.get(mate_rxcui, "")
                    
                    # Ensure all new/fixed attributes are pulled into the index
                    ingredient_name = data.get('Ingredient_Name', "") 
                    manufacturer_name = data.get('Manufacturer_Name', "") 
                    
                    entry = {
                        "rxcui": rxcui,
                        "name": drug_name_raw,
                        "is_brand": data.get('IsBrand', False),
                        "mate_rxcui": mate_rxcui, 
                        "mate_name": mate_name,
                        "ingredient_name": ingredient_name, 
                        "manufacturer_name": manufacturer_name, 
                    }
                    
                    search_index_all[rxcui] = entry
                    
                    if brand_mate and generic_mate and brand_mate != generic_mate:
                        # Create unique key for the pair-only index
                        tag = 'BRAND' if is_brand_part_of_pair else 'GENERIC'
                        unique_search_key = f"{drug_name_raw.lower()} [{tag}]"
                        search_index_has_pair[unique_search_key] = entry
                        
            except:
                continue
    
    search_index_all_path = os.path.join(DATA_DIR, 'search_index_all.json')
    with open(search_index_all_path, 'w') as f:
        json.dump(search_index_all, f, indent=2)
    print(f"✓ Created Index 1 (All Drugs - Keyed by RxCUI) with {len(search_index_all):,} entries.")

    search_index_has_pair_path = os.path.join(DATA_DIR, 'search_index_has_pair.json')
    with open(search_index_has_pair_path, 'w') as f:
        json.dump(search_index_has_pair, f, indent=2)
    print(f"✓ Created Index 2 (Drugs with Pair - has_pair) with {len(search_index_has_pair):,} entries. (Unique Name Keying)")

    comparison_map_path = os.path.join(DATA_DIR, 'comparison_map.json')
    with open(comparison_map_path, 'w') as f:
        json.dump(comparison_map, f, indent=2)
    print(f"✓ Created Index 3 (Brand/Generic Comparison Map) with {len(comparison_map):,} entries.")
    
    print(f"Saved all indexes to: {DATA_DIR}/")