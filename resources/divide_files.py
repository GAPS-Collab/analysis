import argparse
import numpy as np
from pathlib import Path

parser = argparse.ArgumentParser(prog = 'file divide', description = 'produces N lists of files, each a subset of the full list')
parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')
parser.add_argument('-N', type=int, help='number of subsets of files to create')

args = parser.parse_args()

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[1]) for file in files]
files = files[np.argsort(f_nums)]

n_files = int(np.ceil(len(files)/args.N))

for i, files_subset in enumerate([files[i:i+n_files] for i in range(0,len(files), n_files)]):
    with open(f'../../intermediaries/set{i}.lst', 'w+') as out_file:
        for file in files_subset:
            out_file.write(f'{file}\n')
