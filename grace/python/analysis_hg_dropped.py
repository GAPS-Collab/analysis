import argparse
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import sys
from tqdm import tqdm
import pathlib
from pathlib import Path
import contextlib
import io
import go_pybindings as go
import gaps_online.db as db

parser = argparse.ArgumentParser(prog = 'file sort', description = 'produces sorted list of files')
parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')
parser.add_argument('--id')

args = parser.parse_args()

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]


analysis_vals = {
    'percent_dropped_hg': [],
    'met'               : [],
}

with contextlib.redirect_stderr(io.StringIO()):
    for f in tqdm(files, desc="Processing files", unit="file", file=sys.stdout):

        reader = go.io.TofPacketReader(str(f))
        for pack in reader:
            # heartbeat data is only stored in later runs
            if pack.packet_type == go.io.PacketType.EVTBLDRHeartbeat:
                hb = go.commands.EVTBLDRHeartbeat()
                #hb = go.tof.monitoring.EVTBLDRHeartbeat()
                try: 
                    hb.from_tofpacket(pack)
                    rb_disc = hb.n_rbe_discarded_tot
                    rb_rec = hb.n_rbe_received_tot
                    
                    if rb_rec != 0:
                        percent_disc = (rb_disc / rb_rec) * 100
                        percent_disc = round(percent_disc, 1)
                        if percent_disc != 100.0:
                            analysis_vals['percent_dropped_hg'].append(percent_disc)
                    
                            analysis_vals['met'].append(hb.met_seconds)
                except: continue

with open(f'intermediaries/output_{args.id}.txt', 'w+') as out_file:
    vals = list(analysis_vals.keys())
    row = ''    
    for val in vals:
        row += val + ','
    row = row[:-1] + '\n'
    out_file.write(row)
    for i in range(len(analysis_vals[vals[0]])):
        row = ''
        for val in analysis_vals:
            row += f'{analysis_vals[val][i]},'
        row = row[:-1] + '\n'
        out_file.write(row)

        '/Users/gracetytus/gaps/test_charge_data/30198'