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

parser = argparse.ArgumentParser(prog = 'file sort', description = 'produces sorted list of files')
parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')
parser.add_argument('--id')
parser.add_argument('--writdir')

args = parser.parse_args()

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]


analysis_vals = {
    't_rate' : [],
    'l_rate' : [],
}

for f in tqdm(files, desc="Processing files", unit="file"):

    reader = go.io.TofPacketReader(str(f))
    for pack in reader:
        if pack.packet_type == go.io.PacketType.MTBHeartbeat:
            hb = go.commands.MTBHeartbeat()
            try: 
                hb.from_tofpacket(pack)
                analysis_vals['t_rate'].append(hb.trate)
                analysis_vals['l_rate'].append(hb.l_rate)
            except Exception as e:
                print(f"Error: {e}")

with open({args.writdir}.txt, 'w+') as out_file:
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

