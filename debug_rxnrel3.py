import pandas as pd

print("Complete RXNREL.RRF analysis...\n")

# Count total lines
print("Counting total rows in file...")
with open('RXNREL.RRF', 'r') as f:
    total_lines = sum(1 for _ in f)
print(f"Total rows in RXNREL.RRF: {total_lines:,}")

# Read the ENTIRE file and search for tradename
print("\nReading entire file (this may take a minute)...")
df = pd.read_csv('RXNREL.RRF', sep='|', header=None, dtype=str, low_memory=False)

print(f"Loaded {len(df):,} rows")
print(f"Columns: {len(df.columns)}")

# Based on RxNorm docs, column 7 should be RELA (the relationship attribute)
# Let's check what's actually in that column
print("\nColumn 7 (should be RELA) unique values:")
if 7 < len(df.columns):
    print(df[7].value_counts().head(20))

# Search for tradename in ALL columns
print("\n\nSearching entire file for 'tradename'...")
found_tradename = False
for col_idx in range(len(df.columns)):
    tradename_count = df[df[col_idx].str.contains('tradename', na=False, case=False)].shape[0]
    if tradename_count > 0:
        print(f"  ✓ Column {col_idx}: {tradename_count:,} rows with 'tradename'")
        print(f"    Sample values:")
        print(df[df[col_idx].str.contains('tradename', na=False, case=False)][col_idx].value_counts().head(5))
        found_tradename = True

if not found_tradename:
    print("  ⚠️  NO 'tradename' found in any column!")
    print("\n  This means the 'Current Prescribable' RxNorm doesn't include brand/generic relationships!")

# Look for what relationship types DO exist
print("\n\nWhat relationship types ARE in the file?")
for col_idx in [3, 7]:  # REL and RELA columns
    if col_idx < len(df.columns):
        print(f"\nColumn {col_idx} unique values (top 10):")
        print(df[col_idx].value_counts().head(10))