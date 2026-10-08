import pandas as pd
import numpy as np

excel_path = 'data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx'

df_cdm = pd.read_excel(excel_path, sheet_name='centre_daily_metrics')
print("centre_daily_metrics shape:", df_cdm.shape)
print("Columns:", df_cdm.columns.tolist())
print(df_cdm.describe().T[['mean', 'std', 'min', '50%', 'max']])

df_qe = pd.read_excel(excel_path, sheet_name='queue_events')
print("\nqueue_events shape:", df_qe.shape)
print("Columns:", df_qe.columns.tolist())
df_qe['hour'] = pd.to_datetime(df_qe['timestamp']).dt.hour
print("Queue length by hour in queue_events:")
print(df_qe.groupby('hour')['queue_length'].agg(['mean', 'median', 'max', 'count']))
