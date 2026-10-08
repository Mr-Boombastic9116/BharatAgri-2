import pandas as pd
import numpy as np

excel_path = 'data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx'
df = pd.read_excel(excel_path, sheet_name='ml_training_dataset')

print(f"ml_training_dataset shape: {df.shape}")
print(df.describe().T[['mean', 'std', 'min', '50%', 'max']])
print("\nCorrelation with actual_wait_min:")
num_cols = df.select_dtypes(include=[np.number]).columns
print(df[num_cols].corr()['actual_wait_min'].sort_values(ascending=False))
