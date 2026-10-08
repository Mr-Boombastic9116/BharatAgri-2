import pandas as pd

excel_path = 'data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx'
df_centres = pd.read_excel(excel_path, sheet_name='procurement_centres')
print(f"Centres in SIH ({len(df_centres)}):")
print(df_centres.head(10))
print("\nCentres columns:", df_centres.columns.tolist())
print("Districts in SIH:", df_centres['district'].unique().tolist())
print("States in SIH:", df_centres['state'].unique().tolist())
