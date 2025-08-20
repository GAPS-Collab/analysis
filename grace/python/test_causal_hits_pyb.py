import gaps_online as go
import argparse
from tqdm import tqdm
from glob import glob
from pathlib import Path
import numpy as np

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MTB rate plot from telemetered binary files')
    #parser.add_argument('-rd', '--raw_dir')
    parser.add_argument('--telemetry-dir', default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start-time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end-time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')

    args = parser.parse_args()
    
    #run_path = Path(args.raw_dir)
    #files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
    #f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
    #files = files[np.argsort(f_nums)]
    files = go.io.get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)

    for f in tqdm(files, desc='Reading files..'):
        treader = go.io.TelemetryPacketReader(str(f))
        for pack in treader:
            if int(pack.header.packet_type) in [90, 190, 191]:
                ev = go.events.MergedEvent()
                ev.from_telemetrypacket(pack)
                nhits_before = len(ev.tof.hits)
                ev.tof.normalize_hit_times
                ev.tof.remove_non_causal_hits()
                nhits_after = len(ev.tof.hits)
                if (nhits_before - nhits_after) != 0: 
                    print(nhits_before - nhits_after)
