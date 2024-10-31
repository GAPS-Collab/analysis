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

parser = argparse.ArgumentParser(prog = 'flag 16 check', description = 'returns a tuple containing (data mangling from wv, data mangling from flag)')

parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')
parser.add_argument('--id')

args = parser.parse_args()

analysis_vals = {
    'mangling_flag': []
}

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]

mangling_from_status = 0

for f in tqdm.tqdm(files):
        reader = go.io.TofPacketReader(str(f), filter=go.io.TofPacketType.TofEvent)

        n_packets = 0
        for pack in reader:
            n_packets += 1

        reader.rewind()
    
        for pack in reader, total=n_packets, file=sys.stdout, position=0:
            ev = go.events.TofEvent()

            try:
                ev.from_tofpacket(pack)
                status = ev.mastertriggerevent.status
                if int(status) == 16:
                    mangling_from_status += 1
        
            except Exception as e:
                print(f"Error: {e}")
                pass
                continue

analysis_vals['mangling_flag'].append(mangling_from_status)

with open(f'/home/gaps/userspace/grace/intermediaries/count_flags_{args.id}.txt', 'w+') as out_file:
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
