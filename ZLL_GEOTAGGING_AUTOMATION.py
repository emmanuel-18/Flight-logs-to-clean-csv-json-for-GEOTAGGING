import matplotlib
matplotlib.use('TkAgg') 
import pandas as pd
import re
import os
import matplotlib.pyplot as plt
import warnings
import subprocess
from PIL import Image
warnings.filterwarnings("ignore")

# --------- Step 1: File paths ---------
folder = r"C:\Users\User\Desktop\drone_logs"
input_file = os.path.join(folder, "ZLL_Raw.txt")   # raw log file
clean_csv_file = os.path.join(folder, "ZLL_RawToCleaned.csv")  # output CSV

# --------- Step 2: Read raw file ---------
with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# --------- Step 3: Parse lines ---------
records = []
current_record = {}

# Translation map for flight modes (extend as needed)
mode_map = {
    "手动模式": "Manual",
    "定点模式": "Position Hold",
    "GPS模式": "GPS Mode",
    "返航模式": "Return Home",
    "起飞": "Takeoff",
    "降落": "Landing",
    "智能": "Smart Mode",
    "跟随": "Follow Me",
    "环绕": "Orbit",
    "航点": "Waypoint",
    "姿态模式": "Attitude Mode",
}

for line in lines:
    line = line.strip()

    # Timestamp
    time_match = re.search(r'(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
    if time_match:
        if current_record:
            records.append(current_record)
        current_record = {"Time": time_match.group()}
        continue

    # 气压高度
    press_alt = re.search(r'气压高度[:：](\d+)', line)
    if press_alt:
        current_record["PressureAltitude"] = float(press_alt.group(1))

    # IMU温度
    imu_temp = re.search(r'IMU温度[:：](\d+)', line)
    if imu_temp:
        current_record["IMUTemperature"] = float(imu_temp.group(1))

    # 气压温度
    baro_temp = re.search(r'气压温度[:：](\d+)', line)
    if baro_temp:
        current_record["BaroTemperature"] = float(baro_temp.group(1))

    # 飞行模式 (with translation)
    mode = re.search(r'飞行模式\s*[:：]\s*([^\s-]+)', line)
    if mode:
        raw_mode = mode.group(1).strip(":：-")
        current_record["FlightMode"] = mode_map.get(raw_mode, raw_mode)

    # GPS卫星数 + 精度
    gps_match = re.search(r'GPS卫星数[:：](\d+),\s*精度[:：]([\d\.]+)', line)
    if gps_match:
        current_record["GPSSatellites"] = int(gps_match.group(1))
        current_record["GPSPrecision"] = float(gps_match.group(2))

    # 飞机坐标
    ac_coords = re.search(r'飞机坐标:\(Lat:([\d\.\-]+),Lon:([\d\.\-]+)', line)
    if ac_coords:
        current_record["AircraftLat"] = float(ac_coords.group(1))
        current_record["AircraftLon"] = float(ac_coords.group(2))

    # 遥控器坐标
    rc_coords = re.search(r'遥控器坐标:\(Lat:([\d\.\-]+), Lon:([\d\.\-]+)', line)
    if rc_coords:
        current_record["RemoteLat"] = float(rc_coords.group(1))
        current_record["RemoteLon"] = float(rc_coords.group(2))

    # 姿态角
    att_match = re.search(r'俯仰角[:：]([\-\d\.]+)\s+横滚角[:：]([\-\d\.]+)\s+偏航角[:：]([\-\d\.]+)', line)
    if att_match:
        current_record["Pitch"] = float(att_match.group(1))
        current_record["Roll"] = float(att_match.group(2))
        current_record["Yaw"] = float(att_match.group(3))

    # 磁干扰量
    mag = re.search(r'地磁干扰量[:：](\d+)', line)
    if mag:
        current_record["MagneticInterference"] = int(mag.group(1))

    # 飞机电压 (battery)
    volt = re.search(r'飞机电压[:：]([\d\.]+)V', line)
    if volt:
        current_record["BatteryVoltage"] = float(volt.group(1))

    # 飞行高度
    alt = re.search(r'飞行高度[:：](\d+)m', line)
    if alt:
        current_record["Altitude"] = float(alt.group(1))

    # 最大飞行高度 / 距离 / 返航高度
    max_alt = re.search(r'最大飞行高度[:：](\d+)', line)
    if max_alt:
        current_record["MaxFlightAltitude"] = float(max_alt.group(1))

    max_dist = re.search(r'最大飞行距离[:：](\d+)', line)
    if max_dist:
        current_record["MaxFlightDistance"] = float(max_dist.group(1))

    return_alt = re.search(r'最低返航高度[:：](\d+)', line)
    if return_alt:
        current_record["ReturnAltitude"] = float(return_alt.group(1))

    # 遥控器通道 (sticks)
    rc_sticks = re.search(r'左右[:：](\d+),\s*前后[:：](\d+),\s*油门[:：](\d+),\s*旋转[:：](\d+)', line)
    if rc_sticks:
        current_record["StickLeftRight"] = int(rc_sticks.group(1))
        current_record["StickForwardBack"] = int(rc_sticks.group(2))
        current_record["StickThrottle"] = int(rc_sticks.group(3))
        current_record["StickYaw"] = int(rc_sticks.group(4))

    # 飞机型号 / 固件版本
    model = re.search(r'飞机型号[:：](\S+),\s*版本号[:：]\s*([\w\.]+)', line)
    if model:
        current_record["AircraftModel"] = model.group(1)
        current_record["FirmwareVersion"] = model.group(2)

# Append last record
if current_record:
    records.append(current_record)

# --------- Step 4: Save DataFrame ---------
df = pd.DataFrame(records)
df_visualized = df.copy() # creating a copy of my dataframe for visualization purposes




# Drop unwanted columns if present
for col in ["Distance", "Motor1", "Motor2", "Motor3", "Motor4"]:
    if col in df.columns:
        df = df.drop(columns=[col])

# Dropping other not necessary for GEOTAGS
drop_cols = ["PressureAltitude", "FlightMode", "GPSSatellites", "GPSPrecision", 
         "MagneticInterference", "Pitch", "Roll", "Yaw", "BatteryVoltage", 
         "AircraftModel", "FirmwareVersion", "MaxFlightAltitude"]
for i in drop_cols:
    df = df.drop(columns = i)

# Reordering Columns 
df = df[['Time', 'AircraftLat', 'AircraftLon', 'Altitude']]

# Then Renaming 3 columns
df = df.rename(columns={
    'AircraftLat': 'GPSLatitude',
    'AircraftLon': 'GPSLongitude',  
    'Altitude': 'GPSAltitude'
})

# Dropping Rows with Nan and value
df = df[~((df["GPSLatitude"].isna()) | (df["GPSLatitude"] == 0) |
                   (df["GPSLongitude"].isna()) | (df["GPSLongitude"] == 0))]

# Now creating a Dummy_Images for Geotags
output_dir = r"C:\Users\User\Desktop\drone_logs\dummies"
os.makedirs(output_dir, exist_ok=True)
print("Creating dummy images in:", output_dir)
print("Total images to create:", len(df))

count = len(df)
for i in range(len(df)):  
      file_path = f"{output_dir}/IMG_{i+1:04d}.JPG"

      if os.path.exists(file_path):
        print(f"Skipping {file_path}, already exists.")
        continue
      img = Image.new('RGB', (4000, 3000), color='white')
      img.save(file_path)
      count = count - 1
      print(count)

# Injecting the Images to the csv file
num_rows = len(df)
source_files = [f"dummies/IMG_{i+1:04d}.JPG" for i in range(num_rows)]
df.insert(0, "SourceFile", source_files)

# Finaly a cleaned csv file 
df.to_csv(clean_csv_file, index=False)
print(f"✅ Extracted clean CSV saved: {clean_csv_file}")
print(df.head(20))
print("Null counts per column:")
print(df.isnull().sum())
print(len(df))


import subprocess
import os

print("\n📍 Embedding GPS data into dummy images...")

exiftool_path = r"C:\Users\User\Desktop\drone_logs\exiftool.exe"
csv_file = r"C:\Users\User\Desktop\drone_logs\ZLL_RawToCleaned.csv"
photos_folder = r"C:\Users\User\Desktop\drone_logs\dummies"

# Construct command
command = [
    exiftool_path,
    "-overwrite_original",     # directly overwrite files
    f"-csv={csv_file}",
    photos_folder
]

try:
    # Run ExifTool to embed GPS metadata
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    print("✅ ExifTool completed successfully!")
    print(result.stdout)

except subprocess.CalledProcessError as e:
    print("❌ ExifTool failed:")
    print(e.stderr)

# exiftool.exe -overwrite_original -csv=ZLL_RawToCleaned.csv dummies






















# # DATA Visualization VISUALIZATION

# import matplotlib.pyplot as plt

# # Make sure Time is datetime
# df['Time'] = pd.to_datetime(df['Time'], format='%Y:%m:%d %H:%M:%S.%f')


# # --------- Altitude ---------
# plt.figure(figsize=(12,5))
# plt.plot(df['Time'], df['Altitude'], marker='o', linestyle='-', markersize=2, color='blue')
# plt.title("Altitude Over Time")
# plt.xlabel("Time")
# plt.ylabel("Altitude (m)")
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# # --------- Pressure Altitude ---------
# plt.figure(figsize=(12,5))
# plt.plot(df['Time'], df['PressureAltitude'], marker='o', linestyle='-', markersize=2, color='green')
# plt.title("Pressure Altitude Over Time")
# plt.xlabel("Time")
# plt.ylabel("Pressure Altitude (m)")
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# # --------- Battery Voltage ---------
# plt.figure(figsize=(12,5))
# plt.plot(df['Time'], df['BatteryVoltage'], marker='o', linestyle='-', markersize=2, color='orange')
# plt.title("Battery Voltage Over Time")
# plt.xlabel("Time")
# plt.ylabel("Voltage (V)")
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# # --------- GPS Precision ---------
# plt.figure(figsize=(12,5))
# plt.plot(df['Time'], df['GPSPrecision'], marker='o', linestyle='-', markersize=2, color='purple')
# plt.title("GPS Precision Over Time")
# plt.xlabel("Time")
# plt.ylabel("Precision")
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# # --------- Flight Mode (categorical) ---------
# plt.figure(figsize=(12,4))
# df['FlightModeStr'] = df['FlightMode'].astype(str).replace('nan', '')
# plt.scatter(df['Time'], df['FlightModeStr'], c='red', s=10)
# plt.title("Flight Mode Over Time")
# plt.xlabel("Time")
# plt.ylabel("Flight Mode")
# plt.grid(True)
# plt.tight_layout()
# plt.show()












# This part is fucking optional !!!!!!!!!!!!!!!!!!!!!!!!!!!!

# from mpl_toolkits.mplot3d import Axes3D

# # Filter valid GPS rows
# gps_df = df.dropna(subset=['AircraftLat', 'AircraftLon', 'Altitude'])

# if len(gps_df) > 0:
#     fig = plt.figure(figsize=(10,8))
#     ax = fig.add_subplot(111, projection='3d')

#     sc = ax.scatter(
#         gps_df['AircraftLon'],
#         gps_df['AircraftLat'],
#         gps_df['Altitude'],
#         c=gps_df['Altitude'],
#         cmap='viridis',
#         s=10
#     )

#     ax.set_xlabel("Longitude")
#     ax.set_ylabel("Latitude")
#     ax.set_zlabel("Altitude (m)")
#     plt.colorbar(sc, label="Altitude")
#     ax.set_title("3D Drone Trajectory")
#     plt.show()
# else:
#     print("No valid GPS + Altitude data to plot.")


