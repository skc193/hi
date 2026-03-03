import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
import os

# 使用腳本所在的資料夾作為基準路徑，避免工作目錄不同造成找不到檔案
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the dataframe.
df = pd.read_csv(os.path.join(os.getcwd(), 'LinePay_太平R6上個月溫溼度摘要.csv'))

# Display the first 5 rows to confirm structure
print(df.head().to_markdown(index=False, numalign="left", stralign="left"))
print(df.info())
print(df['Sensor Label'].unique())
print(df['Units'].unique())

#=====================================================================================================
# Convert 'Value' to numeric, coercing errors to NaN
df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

# Drop rows with NaN values in 'Value'
df = df.dropna(subset=['Value'])

# Convert 'Time' to datetime
try:
    df['Time'] = pd.to_datetime(df['Time'].str.replace(' CST', ''), format='%m/%d/%y, %I:%M:%S %p')
except Exception as e:
    print(f"Error parsing time: {e}")

# Calculate statistics and format for log.txt
sensors = df['Sensor Label'].unique()
summary_data = {}

for sensor in sensors:
    sensor_data = df[df['Sensor Label'] == sensor]
    mean_val = sensor_data['Value'].mean()
    unit = sensor_data['Units'].iloc[0]
    
    # Check if temperature
    is_temp = 'Temperature' in sensor or '° C' in unit
    
    # 透過正規表示式萃取基礎感測器名稱 (濾除 Temperature, Humidity 等字眼)
    # 例如："A Temperature" -> "A", "A_B Hum" -> "A_B"
    base_name = re.sub(r'(?i)[-_]?\s*(Temperature|Humidity|Temp|Hum).*', '', sensor).strip()
    if not base_name:
        base_name = sensor # 萬一濾除後為空，則保留原名稱
        
    # 初始化字典結構
    if base_name not in summary_data:
        summary_data[base_name] = {'Temperature(°C )': None, 'Humidity(% RH )': None}
        
    # 將平均值填入對應的欄位
    if is_temp:
        summary_data[base_name]['Temperature(°C )'] = mean_val
    else:
        summary_data[base_name]['Humidity(% RH )'] = mean_val

# 將整理好的字典轉換為 DataFrame
summary_df = pd.DataFrame.from_dict(summary_data, orient='index').reset_index()
summary_df.rename(columns={'index': 'Sensor'}, inplace=True)

# 依照 Sensor 名稱進行英文字母排序 (A -> A_B -> B)
summary_df = summary_df.sort_values(by='Sensor')

# 將數值格式化為小數點後 1 位
summary_df['Temperature(°C )'] = summary_df['Temperature(°C )'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
summary_df['Humidity(% RH )'] = summary_df['Humidity(% RH )'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")

# 將結果儲存為 log.txt (使用 markdown 格式產生排版整齊的純文字表格)
with open(os.path.join(_BASE_DIR, 'log.txt'), 'w', encoding='utf-8') as f:
    f.write(summary_df.to_markdown(index=False, colalign=("center", "center", "center")))

print("\n--- 平均值已成功計算並儲存至 log.txt ---")
print(summary_df.to_markdown(index=False, colalign=("center", "center", "center")))
print("-----------------------------------------\n")


# Generate plots (保持原有的產生折線圖邏輯不變)
generated_files = []

for sensor in sensors:
    sensor_data = df[df['Sensor Label'] == sensor].sort_values('Time')
    
    plt.figure(figsize=(12, 6))
    plt.plot(sensor_data['Time'], sensor_data['Value'], label='Value')
    
    unit = sensor_data['Units'].iloc[0]
    is_temp = 'Temperature' in sensor or '° C' in unit
    
    if is_temp:
        # Temperature Limit: 28
        plt.axhline(y=28, color='r', linewidth=2, label='Limit (28°C)')
        plt.ylabel('Temperature (°C)')
        ymin, ymax = plt.ylim()
        plt.ylim(min(ymin, 25), max(ymax, 30))
    else:
        # Humidity Limits: 80 and 20
        plt.axhline(y=80, color='r', linewidth=2, label='Upper Limit (80%)')
        plt.axhline(y=20, color='r', linewidth=2, label='Lower Limit (20%)')
        plt.ylabel('Humidity (% RH)')
        plt.ylim(0, 100)
    
    plt.title(sensor)
    plt.xlabel('Time')
    plt.legend()
    plt.grid(True)
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    # Save file
    safe_name = sensor.replace('/', '_').replace(' ', '_') + ".png"
    plt.tight_layout()
    plt.savefig(os.path.join(_BASE_DIR, safe_name))
    plt.close()
    generated_files.append(safe_name)

print("Generated files:", generated_files)