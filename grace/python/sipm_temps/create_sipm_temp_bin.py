import gondola as go
from glob import glob
import pandas as pd
from tqdm import tqdm
import csv

# --- Paths ---
binary_path = '/data/stoessl/flight/GAPSI/flight-starlink-moni-only/'
channel_csv = "channel_to_paddle.csv"
rb_csv = "rb_to_pb.csv"

# --- Load mappings ---
df_ch_to_paddle = pd.read_csv(channel_csv)
df_rb_to_pb     = pd.read_csv(rb_csv)

rb_to_pb = {
    f"{int(row['rb_id']):02d}": f"{int(row['pb_id']):02d}"
    for _, row in df_rb_to_pb.iterrows()
}

pb_channel_to_paddle = {
    f"{row['pb_number_channel']}": f"{int(row['paddle_number']):02d}{row['paddle_end']}"
    for _, row in df_ch_to_paddle.iterrows()
}

# --- Initialize paddle dictionary ---
paddle_temps = {f"{i:02d}{end}": [] for i in range(1,161) for end in ["A","B"]}
seen_channels = set()

# --- Get all binary files ---
files = sorted(glob(binary_path + '*.bin'))
print(f"Found {len(files)} files.")

# --- Read all files into a single PAMoniDataSeries ---
pa_moni_data = go.monitoring.PAMoniDataSeries()
pa_moni_data.max_size = int(10e6)

for file in tqdm(files):
    pa_moni_data.add_telemetryfile(file)

# --- Convert to DataFrame once ---
df = pa_moni_data.get_dataframe()
print(f"Total rows across all files: {len(df)}")
print(f"First timestamp: {pa_moni_data.get_first_ts}")
print(f"Last timestamp: {df['timestamp'].max()}")

# --- Populate paddle_temps dictionary ---
for x in tqdm(range(len(df))):
    rb_id = f"{int(df['board_id'][x]):02d}"
    pb_id = rb_to_pb.get(rb_id)
    if pb_id is None:
        print(f"Missing rb_id mapping: {rb_id}")
        continue

    for ch in range(1, 17):
        temp = df[f"temps{ch}"][x]
        timestamp = df['timestamp'][x]

        pb_channel = f"{pb_id}-{ch:02d}"
        seen_channels.add(pb_channel)

        if pb_channel in pb_channel_to_paddle:
            paddle = pb_channel_to_paddle[pb_channel]
            paddle_temps[paddle].append((timestamp, temp))
        else:
            # debug missing channel
            print(f"Missing mapping for pb_channel: {pb_channel}")

print(f"Total unique channels seen: {len(seen_channels)}")

# --- Write channel mapping for reference ---
with open('mapping.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=pb_channel_to_paddle.keys())
    writer.writeheader()
    writer.writerow(pb_channel_to_paddle)

# --- Flatten paddle_temps into a DataFrame ---
rows = []
for paddle, values in paddle_temps.items():
    for timestamp, temp in values:
        rows.append({"paddle": paddle, "timestamp": timestamp, "temp": temp})

df_out = pd.DataFrame(rows)
df_out.sort_values("timestamp", inplace=True)

# --- Optional: convert timestamp to datetime if you know experiment start ---
# start_time = pd.Timestamp("2025-12-15 00:00:00")
# df_out["time_real"] = start_time + pd.to_timedelta(df_out["timestamp"], unit='s')

df_out.to_hdf("sipm_temps.h5", key="temps", mode="w")
print("HDF5 file written successfully!")
