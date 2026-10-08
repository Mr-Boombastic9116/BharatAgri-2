import pandas as pd

excel_path = 'data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx'

for sheet in ['ml_training_dataset', 'queue_events', 'centre_daily_metrics', 'appointments', 'notifications', 'procurement_transactions']:
    df = pd.read_excel(excel_path, sheet_name=sheet, nrows=5)
    print(f"\n--- SHEET: {sheet} ---")
    print("Columns:", df.columns.tolist())
    print("Sample row 0:")
    print(df.iloc[0].to_dict())
