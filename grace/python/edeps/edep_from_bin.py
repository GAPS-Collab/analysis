from glob import glob
from tqdm import tqdm
import pandas as pd
import gondola as go

'''
This script will produce a binary file with energy depositions and corresponding gcutimes for every hit falling within the fiducial volume of every paddle. The goal is to use this for the gain calibration
'''

binary_path = '/data1/nextcloud/cra_data/data/binaries_berkeley/gcu_2_gcupool/'
files = (sorted(glob(binary_path + '*.bin')))

outdir = 'paddle_data'

FLUSH_SIZE = 50000

buffers = {pid: {"timestamp": [], "edep": []} for pid in range(1,161)}

first_write = {pid: True for pid in range(1,161)}

for file in tqdm(files):
    reader = go.io.TelemetryPacketReader(str(file))
    for packet in reader: 
        if not packet.is_event_packet: continue
        gcu_time = packet.header.gcutime
        try: 
            event=go.events.TelemetryEvent.from_telemetrypacket(packet)
        
        except Exception: continue

        tof_event = event.tof

        for hit in tof_event.hits:
            pid = hit.paddle_id
            if pid not in buffers: continue

            pos = hit.pos
            if pos < 600 or pos > 1200: continue

            buffers[pid]["timestamp"].append(gcu_time)
            buffers[pid]["edep"].append(hit.edep)

            if len(buffers[pid]["timestamp"]) >= FLUSH_SIZE:
                df = pd.DataFrame(buffers[pid])
                outfile = f"{outdir}/paddle_{pid:03d}.h5"
                df.to_hdf(outfile, key='hits', mode='a', append=not first_write[pid], format='table')

                first_write[pid] = False
                buffers[pid] = {"timestamp": [], "edep": []}

for pid in range(1, 161):
    if len(buffers[pid]["timestamp"]) == 0: continue

    df = pd.DataFrame(buffers[pid])
    outfile = f"{outdir}/paddle_{pid:03d}.h5"
    df.to_hdf(outfile, key='hits', mode='a', append=not first_write[pid], format='table')
    first_write[pid] = False



