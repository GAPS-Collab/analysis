import gondola as go
from glob import glob
import pandas as pd
import os
from tqdm import tqdm
import gc
#binary_path = '/data/stoessl/flight/GAPSI/flight-starlink-moni-only/'
binary_path = '/data1/nextcloud/cra_data/data/binaries_berkeley/gcu_2_gcupool/'
#binary_path = '/data/stoessl/flight/flight-gcu-2-gcupool-moni-only/'

files = (sorted(glob(binary_path + '*.bin')))
#files=files[:2000]
outfile = "altitude_vs_time.h5"

first_write = True

for file in tqdm(files):    
    pos_moni_data = go.monitoring.SipPosMoniDataSeries()
    pos_moni_data.max_size = int(1e6)
    
    pos_moni_data.add_telemetryfile(file)
    
    t_0 = pos_moni_data.first_ts
    df = pos_moni_data.get_dataframe()
    df_out = df.select(["timestamp", "altitude"]).to_pandas()
    df_out["timestamp"] = df_out["timestamp"] + t_0

    df_out.to_hdf(outfile, key='altitude', mode = 'a', append=not first_write, format='table')
    
    first_write = False
    del df
    del df_out
    del pos_moni_data

    gc.collect()
## old version!! keep binary_path and files and this will be runnable (but memory expensive)
#pos_moni_data = go.monitoring.SipPosMoniDataSeries()
#pos_moni_data.max_size = int(100e6)
#t_1 = pos_moni_data.get_first_ts
#print(t_1)

#rows = []
#n_sip_moni = 0
#for idx, file in enumerate(tqdm(files)):
   # pos_moni_data.add_telemetryfile(file)
   # 
   # t_1 = pos_moni_data.first_ts
   # print(t_1) 
   # df = pos_moni_data.get_dataframe()
   # n_sip_moni += 1
   # for x in range(len(df)):
        #rows.append({"timestamp": df["timestamp"][x], "altitude": df["altitude"][x]})
    #print(f'got {n_sip_moni} sip moni data so far')

#df_out = pd.DataFrame(rows)
#df_out.sort_values("timestamp", inplace=True)
#df_out.to_hdf("altitude_vs_time.h5", key="altitude", mode="w")
