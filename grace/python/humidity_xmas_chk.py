import gaps_online as go
from tqdm import tqdm
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import logging
import matplotlib


logger = logging.getLogger(__name__)

def has_merged_event(frame, merged_event_types):
    for m_type in merged_event_types:
        try:
            ev = frame.get_mergedevent(m_type)
            return m_type
        except ValueError as e:
            if "Merged Event not found" in str(e):
                continue
            else: raise
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Paddle occupancy graphic plot')
    parser.add_argument('-dir', '--data_dir', type = str, default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-id', '--run_id', type=str, help = 'TOF run id' )

    args = parser.parse_args()

    MERGED_EVENT_TYPES     = [\
    "TelemetryPacketType.NoGapsTriggerEvent",
    "TelemetryPacketType.BoringEvent",
    "TelemetryPacketType.InterestingEvent",
    "TelemetryPacketType.NoTofDataEvent"]

    files = Path(f'{args.data_dir}').glob('*.gaps')

    reader = go.io.CRReader('/data1/nextcloud/cra_data/data/2024/processed/L0/9113') 
    for frame in reader:
        if frame.has('PacketType.RBMoniData'):
            tp   = frame.get_tofpacket('PacketType.RBMoniData') 
            moni = go.tof.monitoring.RBMoniData()
            moni.from_tofpacket(tp)
            print (moni)