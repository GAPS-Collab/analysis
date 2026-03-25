import gondola as go
from glob import glob
import pandas as pd
import os
from tqdm import tqdm

#skip_indices = {2997,2999,3001}

print(go.__version__)

binary_path = '/data/stoessl/flight/GAPSI/flight-starlink-moni-only/'
#binary_path = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/'
#binary_path = '/home/gtytus/data/flight_bin_test/'

files = (sorted(glob(binary_path + '*.bin')))

pos_moni_data = go.monitoring.SipPosMoniDataSeries()
pos_moni_data.max_size = int(10e6)
#t_1 = pos_moni_data.get_first_ts
#print(t_1)

rows = []

for idx, file in enumerate(tqdm(files)):
    pos_moni_data.add_telemetryfile(file)
    
    t_1 = pos_moni_data.get_first_ts
    print(t_1)
    
    df = pos_moni_data.get_dataframe()

    for x in range(len(df)):
        rows.append({"timestamp": df["timestamp"][x], "altitude": df["altitude"][x]})

df_out = pd.DataFrame(rows)
df_out.sort_values("timestamp", inplace=True)
df_out.to_hdf("altitude_vs_time.h5", key="altitude", mode="w")
