import pandas as pd
import gondola as go
from tqdm import tqdm

rows = []

files = go.io.grace_get_telemetry_binaries(1766216918, 1766271155, data_dir = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/')

for f in tqdm(files, desc='reading TOF binaries'):
    reader = go.io.TelemetryPacketReader(str(f))
    
    for packet in reader:
        if not packet.is_event_packet:
            continue

        event = go.events.TelemetryEvent.from_telemetrypacket(packet)
        tof_event = event.tof

        event_status = tof_event.event_status
        if event_status == go.events.EventStatus.AnyDataMangling: continue

        for hit in tof_event.hits:
            rows.append({
                "paddle_id": hit.paddle_id,
                "pos": hit.pos,
                "edep": hit.edep
            })

df = pd.DataFrame(rows)

df.to_hdf("paddle_pos_edep.h5", key="df", mode="w", format="table", data_columns=["paddle_id"])