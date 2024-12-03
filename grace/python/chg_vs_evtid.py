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

parser = argparse.ArgumentParser(prog = 'get charge vs event_id; ie charge over time', description = 'returns a tuple containing (data mangling from wv, data mangling from flag)')

parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')
parser.add_argument('--id')
parser.add_argument('-p', help = "path to paddle_mapping csv (sydneys's spreadhseet)" )
args = parser.parse_args()

analysis_vals = {
    '97A_charge':  [],
    '97B_charge':  [],
    '97_evt':      [],
    '99A_charge':  [],
    '99B_charge':  [],
    '99_evt':      [],
    '101A_charge': [],
    '101B_charge': [],
    '101_evt':     [],
    '104A_charge': [],
    '104B_charge': [],
    '104_evt':     [],
}

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]



paddle_map = {}
with open(args.p) as in_file:
    variables = next(in_file).strip().split(',')
    next(in_file)
    for line in in_file:
        row = line.strip().split(',')
        paddle_id = int(row[0])
        paddle_map[paddle_id] = {'a':{'rb':0,'ch':0},'b':{'rb':0,'ch':0}}
        rb, ch = [int(d) for d in row[9].split('-')]
        paddle_map[paddle_id]['a']['rb'] = rb
        paddle_map[paddle_id]['a']['ch'] = ch - 1

        row = next(in_file).strip().split(',')
        rb, ch = [int(d) for d in row[9].split('-')]
        paddle_map[paddle_id]['b']['rb'] = rb
        paddle_map[paddle_id]['b']['ch'] = ch - 1



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
                for x in range(len(ev.hits)):
                    paddle = int(ev.hits[x].paddle_id)
                    if paddle == 97:
                        analysis_vals['97A_charge'].append(ev.hits[x].charge_a)
                        analysis_vals['97B_charge'].append(ev.hits[x].charge_b)
                        analysis_vals['97_evt'].append(ev.hits[x].event_id)
                    elif paddle == 99:
                        analysis_vals['99A_charge'].append(ev.hits[x].charge_a)
                        analysis_vals['99B_charge'].append(ev.hits[x].charge_b)
                        analysis_vals['99_evt'].append(ev.hits[x].event_id)
                    elif paddle == 101:
                        analysis_vals['101A_charge'].append(ev.hits[x].charge_a)
                        analysis_vals['101B_charge'].append(ev.hits[x].charge_b)
                        analysis_vals['101_evt'].append(ev.hits[x].event_id)
                    elif paddle == 104:
                        analysis_vals['104A_charge'].append(ev.hits[x].charge_a)
                        analysis_vals['104B_charge'].append(ev.hits[x].charge_b)
                        analysis_vals['104_evt'].append(ev.hits[x].event_id)
                    else: continue

                                            
        
            except Exception as e:
                print(f"Error: {e}")
                pass
                continue

with open(f'/home/tof/umbrella_checkout/{args.id}/ch_vs_evtid{args.id}.txt', 'w+') as out_file:
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