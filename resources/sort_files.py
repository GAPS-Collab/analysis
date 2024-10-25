import argparse
import numpy as np
from pathlib import Path

parser = argparse.ArgumentParser(prog = 'file sort', description = 'produces sorted list of files')
parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')

args = parser.parse_args()

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]

