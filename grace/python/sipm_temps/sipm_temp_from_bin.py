import gondola as go
from glob import glob
import pandas as pd
import os
from tqdm import tqdm
import csv

#skip_indices = {2997,2999,3001}

binary_path = '/data/stoessl/flight/GAPSI/flight-starlink-moni-only/'
#binary_path = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/'
#binary_path = '/home/gtytus/data/flight_bin_test/'

df_ch_to_paddle = pd.read_csv("channel_to_paddle.csv")
df_rb_to_pb     = pd.read_csv("rb_to_pb.csv")

rb_to_pb = {
    f"{int(row['rb_id']):02d}": f"{int(row['pb_id']):02d}"
    for _, row in df_rb_to_pb.iterrows()
}


pb_channel_to_paddle = {
    f"{row['pb_number_channel']}": f"{int(row['paddle_number']):02d}{row['paddle_end']}"
    for _, row in df_ch_to_paddle.iterrows()
}

paddle_temps = {f"{i:02d}{end}": [] for i in range(1,161) for end in ["A","B"]}


files = (sorted(glob(binary_path + '*.bin')))
pa_moni_data = go.monitoring.PAMoniDataSeries()
pa_moni_data.max_size = int(10e6)

seen_channels = set()

for file in tqdm(files):
    #pa_moni_data = go.monitoring.PAMoniDataSeries()
    #pa_moni_data.max_size = int(10e6)
    pa_moni_data.add_telemetryfile(file)
    

    df = pa_moni_data.get_dataframe()
    print(file, len(df), pa_moni_data.get_first_ts)


    for x in range(len(df)):
        rb_id = f"{int(df['board_id'][x]):02d}"
        pb_id = rb_to_pb.get(rb_id, None)
        if pb_id is None:
            print(f"Missing rb_id in mapping: {rb_id}")
            continue

        for ch in range(1,17):
            temp = df[f"temps{ch}"][x]
            timestamp = df['timestamp'][x]

            pb_channel = f"{pb_id}-{ch:02d}"
            if pb_channel not in pb_channel_to_paddle:
                print(f"Missing pb_channel mapping: {pb_channel}")
                continue

            seen_channels.add(pb_channel)

            if pb_channel in pb_channel_to_paddle:
                paddle = pb_channel_to_paddle[pb_channel]
                paddle_temps[paddle].append((timestamp,temp))
            else: print(pb_channel)
print(len(seen_channels))

with open('mapping.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=pb_channel_to_paddle.keys())
    writer.writeheader()
    writer.writerow(pb_channel_to_paddle)

rows = []

for paddle, values in paddle_temps.items():
    for timestamp, temp in values:
        rows.append({"paddle": paddle, "timestamp": timestamp, "temp": temp})

df = pd.DataFrame(rows)
df.sort_values("timestamp", inplace=True)
df.to_hdf("sipm_temps.h5", key="temps", mode="w")
