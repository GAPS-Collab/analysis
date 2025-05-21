import gaps_online as go
import numpy as np
import sys
from tqdm import tqdm
from pathlib import Path
import io
import contextlib
import go_pybindings as gop
import re
from glob import glob
import os
import argparse

parser = argparse.ArgumentParser(prog = 'get RB moni'. description = 'get and extract info from RBMoniData in .tof.gaps files')
parser.add_argument('path')

args = parser.parse_args()

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]

for f in tqdm(files):
    reader = go.io.TofPacketReader(str(f))
    for pack in reader: 
        if int(pack.packet_type) == 100:
            rbmoni = go.monitoring.RBMoniData()
            rate = rbmoni.rate

            