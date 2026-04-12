
import pandas as pd
import sys

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def inspect_asset_data(path, outfile):
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(f"Inspecting AssetData in {path}...\n")
        try:
            # Try to read without header to see layout
            df = pd.read_excel(path, sheet_name='AssetData', header=None, nrows=15)
            f.write(df.to_string())
            
            f.write("\n\nChecking LPMData again for Term...\n")
            df_lpm = pd.read_excel(path, sheet_name='LPMData', nrows=5)
            f.write(str(df_lpm.columns.tolist()))
            
            # Check if there is a 'Term' column or similar in LPMData or AssetData
            # Maybe row 3 of AssetData is header?
            df_asset_h = pd.read_excel(path, sheet_name='AssetData', header=2, nrows=5)
            f.write("\n\nAssetData with header=2:\n")
            f.write(str(df_asset_h.columns.tolist()))
            
        except Exception as e:
            f.write(f"Error reading {path}: {e}")

inspect_asset_data('../portfolio_v1/mock_data.xlsm', 'result.txt')
