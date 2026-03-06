import gondola as go
from glob import glob
import pandas as pd
import os


#binary_path = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/'
binary_path = '/home/gtytus/data/flight_bin_test/'

df = pd.read_csv("channel_to_paddle.csv")

channel_to_paddle = {
    f"{row['pb_number_channel']}": f"{int(row['paddle_number'])}{row['paddle_end']}"
    for _, row in df.iterrows()
}

paddle_temps = {f"{i}{end}": [] for i in range(1,161) for end in ["A","B"]}

pa_moni_data = go.monitoring.PAMoniDataSeries()

for file in sorted(glob(binary_path + '*.bin')):
    basename = os.path.basename(file)
    date_str, time_str = basename[3:9], basename[10:16]
    timestamp = int(date_str + time_str)

    pa_moni_data.add_telemetryfile(file)
    df = pa_moni_data.get_dataframe()

    for x in range(len(df)):
        rb_id = f"{int(df['board_id'][x]):02d}"

        for ch in range(1,17):

            temp = df[f"temps{ch}"][x]

            pb_channel = f"{rb_id}-{ch:02d}"

            if pb_channel in channel_to_paddle:

                paddle = channel_to_paddle[pb_channel]

                paddle_temps[paddle].append((timestamp,temp))

rows = []
for paddle, values in paddle_temps.items():
    for timestamp, temp in values:
        rows.append({"paddle": paddle, "timestamp": timestamp, "temp": temp})

df = pd.DataFrame(rows)
df.sort_values("timestamp", inplace=True)
df.to_hdf("sipm_temps.h5", key="temps", mode="w")
