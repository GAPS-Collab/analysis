import numpy as np
import sys
import tqdm
import pathlib
from pathlib import Path
import io
import contextlib
import gaps_online as go
import go_pybindings as gop
import re
from glob import glob
import os
import argparse

parser = argparse.ArgumentParser(prog = 'num rb events per evt_id, shows if RB events are coming in over time', description = 'returns a tuple containing (data mangling from wv, data mangling from flag)')

parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')
parser.add_argument('--id')
parser.add_argument('-p', help = "path to paddle_mapping csv (sydneys's spreadhseet)" )
args = parser.parse_args()

analysis_vals = {
    'num_rbe' : [], 
    'evtid'   : []
}

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]


for f in tqdm.tqdm(files):
        reader = go.io.TofPacketReader(str(f), filter=go.io.TofPacketType.TofEvent)

        n_packets = 0
        for pack in reader:
            n_packets += 1

        reader.rewind()
    
        for pack in reader(total=n_packets, file=sys.stdout, position=0):
            ev = go.events.TofEvent()
            try:
                ev.from_tofpacket(pack)
                rb_evts = ev.rb_event
                analysis_vals['num_rbe'].append(len(rb_evts))

                evt_id = rb_evts[0].RBEventHeader.event_id
                analysis_vals['evtid'].append(evt_id)

            except Exception as e:
                print(f"Error: {e}")
                pass
                continue

with open(f'/home/tof/umbrella_checkout/{args.id}/rbe_per_evtid{args.id}.txt', 'w+') as out_file:
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