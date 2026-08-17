import gondola as go
from glob import glob
import pandas as pd
from tqdm import tqdm

#binary_path = '/data/stoessl/flight/GAPSI/flight-starlink-moni-only/'
binary_path = '/data1/nextcloud/cra_data/data/binaries_berkeley/gcu_2_gcupool/'
#binary_path = '/data/stoessl/flight/flight-gcu-2-gcupool-moni-only/'

files = (sorted(glob(binary_path + '*.bin')))
# outfile = "sip_gps_time.h5"

# first_write = True

# for file in tqdm(files):    
#     pos_moni_data = go.monitoring.SipPosMoniDataSeries()
#     pos_moni_data.max_size = int(1e6)
    
#     pos_moni_data.add_telemetryfile(file)
    
#     t_0 = pos_moni_data.first_ts
#     df = pos_moni_data.get_dataframe()
    
#     if first_write == True: 
#         print(df)
#         first_write = False
        
#     df_out = df.select(["timestamp"]).to_pandas()
#     df_out["timestamp"] = df_out["timestamp"] + t_0
    
#     df_out.to_hdf(outfile, key='timestamp', mode = 'a', append=not first_write, format='table')
    
#     del df
#     del df_out
#     del pos_moni_data

for f in tqdm(files[-2:]): #tqdm just creates a nice progress bar, feel free to remove
    reader = go.io.TelemetryPacketReader(str(f))
    for packet in reader:
        if packet.packet_type == go.packets.TelemetryPacketType.SipGpsTime:
            sipgps = go.packets.TelemetryPacketType.from_u8(packet.payload)
        
        