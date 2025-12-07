#!/usr/bin/env python3
"""
Extract ALL dosage forms from actual drug names in RXNCONSO.RRF
grabs ONLY the form at the end, not ingredient lists
"""

import pandas as pd
import re
from collections import Counter

print("EXTRACTING DOSAGE FORMS FROM DRUG NAMES (FIXED)")

# load RXNCONSO
print("\n[1/4] Loading RXNCONSO.RRF...")

try:
    df_rxnconso = pd.read_csv('RXNCONSO.RRF', sep='|', header=None, 
                              usecols=[0, 11, 12, 14, 16],
                              names=['RXCUI', 'SAB', 'TTY', 'STR', 'SUPPRESS'],
                              dtype=str, low_memory=False)
    print(f"Loaded {len(df_rxnconso):,} rows")
except FileNotFoundError:
    print("ERROR: RXNCONSO.RRF not found!")
    exit(1)

# filter to RxNorm drug products
print("\n[2/4] Filtering to RxNorm drug products...")
df_drugs = df_rxnconso[
    (df_rxnconso['SAB'] == 'RXNORM') & 
    (df_rxnconso['TTY'].isin(['SCD', 'SBD', 'SCDF', 'SBDF'])) &
    (~df_rxnconso['SUPPRESS'].isin(['Y', 'O']))
].copy()
print(f"    ✓ Found {len(df_drugs):,} drug products")

# extract ONLY the dosage form at the end (1-5 capitalized words before optional [Brand])
print("\n[3/4] Extracting dosage forms...")

# pattern: Capture 1-5 capitalized words at the end, before optional [Brand]
# this will match:
#   "... Injectable Solution [Brand]" → "Injectable Solution"
#   "... Oral Tablet" → "Oral Tablet"
#   "... Extended Release Oral Capsule" → "Extended Release Oral Capsule"
form_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})(?:\s*\[|$)'

forms_counter = Counter()
unmatched = []

for drug_name in df_drugs['STR']:
    # find all matches (in case of multiple caps word sequences)
    matches = re.findall(form_pattern, drug_name)
    if matches:
        # take the LAST match (the one right before end or [Brand])
        form = matches[-1].strip()
        forms_counter[form] += 1
    else:
        unmatched.append(drug_name)

print(f"    ✓ Extracted forms from {len(df_drugs) - len(unmatched):,} drugs")
print(f"    ⚠ Failed to extract from {len(unmatched):,} drugs")

# get unique forms sorted by frequency
forms_by_count = sorted(forms_counter.items(), key=lambda x: x[1], reverse=True)

print(f"    ✓ Found {len(forms_by_count):,} UNIQUE dosage forms")

# display results
print("\n[4/4] Results...")
print("\n" + "=" * 60)
print(f"TOP 100 MOST COMMON DOSAGE FORMS:")
print("=" * 60)

for i, (form, count) in enumerate(forms_by_count[:100], 1):
    print(f"{i:3}. '{form}' ({count:,} occurrences)")

if len(forms_by_count) > 100:
    print(f"\n... and {len(forms_by_count) - 100} more forms")

# filter to forms appearing 3+ times
forms_filtered = [(form, count) for form, count in forms_by_count if count >= 3]

# sort by length for regex (longest first)
forms_sorted_by_length = sorted(forms_filtered, key=lambda x: (len(x[0]), x[0].lower()), reverse=True)

# coverage
total_drugs = len(df_drugs)
matched_drugs = sum(count for _, count in forms_by_count)
filtered_drugs = sum(count for _, count in forms_filtered)

print(f"\n" + "=" * 60)
print("FILTERING & COVERAGE:")
print("=" * 60)
print(f"Total unique forms: {len(forms_by_count):,}")
print(f"Forms appearing 3+ times: {len(forms_filtered):,}")
print(f"Removed rare forms: {len(forms_by_count) - len(forms_filtered):,}")
print(f"\nCoverage: {filtered_drugs:,}/{total_drugs:,} drugs ({filtered_drugs/total_drugs*100:.1f}%)")

# save curated list
output = {
    "total_unique_forms": len(forms_filtered),
    "total_extractions": filtered_drugs,
    "coverage_percent": round(filtered_drugs/total_drugs*100, 2),
    "forms": [{"form": form, "count": count} for form, count in forms_sorted_by_length]
}

import json
with open('dosage_forms_CURATED.json', 'w') as f:
    json.dump(output, f, indent=2)

# save as Python list
with open('dosage_forms_CURATED_list.txt', 'w') as f:
    f.write("# Curated dosage forms (appearing 3+ times in actual data)\n")
    f.write(f"# {len(forms_filtered)} forms covering {filtered_drugs/total_drugs*100:.1f}% of drugs\n")
    f.write("# Sorted by length (longest first) for regex matching\n\n")
    f.write("form_words = [\n")
    for form, count in forms_sorted_by_length:
        f.write(f"    '{form}',  # {count} occurrences\n")
    f.write("]\n")

print("\n✓ Saved curated list to: dosage_forms_CURATED_list.txt")
print("✓ Saved JSON to: dosage_forms_CURATED.json")
print(f"\nThis is the CLEAN list - use it in your preprocessing script!")