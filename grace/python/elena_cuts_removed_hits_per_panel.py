import gaps_online as go
import matplotlib.pyplot as plt
from tqdm import tqdm
import argparse
from glob import glob
from pathlib import Path
import matplotlib.colors as colors
import numpy as np

def passes_elena_cut(hit) -> bool:
    charge_cut = 5
    peak_cut = 10
    time_sat = 490
    time_min = 0.1

    return (
        time_min < hit.time_a < time_sat and
        time_min < hit.time_b < time_sat and
        hit.charge_a > charge_cut and
        hit.charge_b > charge_cut and
        hit.peak_a > peak_cut and
        hit.peak_b > peak_cut
    )


parser = argparse.ArgumentParser(prog = 'create heatmap of FWHM vs peak height')
parser.add_argument('-rd', '--raw_dir', default='', help = 'path to .tof.gaps files')
parser.add_argument('-id', '--run_id', default = 0, help = 'the run id')
args = parser.parse_args()

if __name__ == '__main__':
    tof_run_path = Path(args.raw_dir)
    tof_files = np.array([str(f) for f in ((tof_run_path.glob('*.tof.gaps')))])
    tof_f_nums = [int(file.split('.')[0].split('_')[-1]) for file in tof_files]
    tof_files = tof_files[np.argsort(tof_f_nums)]

    print('Finished loading TOF files')

    paddle_counts_removed = {pid: 0 for pid in range(1,161)}


    for f in tqdm(tof_files, desc = 'reading raw .tof.gaps files'):
        reader = go.io.TofPacketReader(str(f), filter = go.io.TofPacketType.TofEvent)
        for pack in reader:
            tof_ev = go.events.TofEvent()
            tof_ev.from_tofpacket(pack)
            for x in range(len(tof_ev.hits)):
                try:
                    paddle = int(tof_ev.hits[x].paddle_id)
                    if passes_elena_cut(tof_ev.hits[x]) == False: 
                        paddle_counts_removed[paddle] += 1
                    
                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue


    with open("hits_removed_per_panel.txt", "w") as f:
        for pid, count in paddle_counts_removed.items():
            f.write(f"{pid} {count}\n")
