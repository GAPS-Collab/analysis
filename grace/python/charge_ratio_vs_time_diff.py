import gaps_online as go
import matplotlib.pyplot as plt
from tqdm import tqdm
import argparse
from glob import glob
from pathlib import Path
import matplotlib.colors as colors
import numpy as np

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

    time_diff = []
    charge_ratio     = []
    
    for f in tqdm(tof_files, desc = 'reading raw .tof.gaps files'):
        reader = go.io.TofPacketReader(str(f), filter = go.io.TofPacketType.TofEvent)
        for pack in reader:
            tof_ev = go.events.TofEvent()
            tof_ev.from_tofpacket(pack)
            for x in range(len(tof_ev.hits)):
                try:
                    paddle = int(tof_ev.hits[x].paddle_id)
                    time_a_side = tof_ev.hits[x].time_a
                    time_b_side = tof_ev.hits[x].time_b
                    if time_a_side < 0.5 or time_a_side > 495: continue
                    if time_b_side < 0.5 or time_b_side > 495: continue

                    tdiff = time_a_side - time_b_side

                    charge_a_side = tof_ev.hits[x].charge_a
                    charge_b_side = tof_ev.hits[x].charge_b
                    if charge_a_side == 0 or charge_b_side == 0: continue
                    q_rat = charge_a_side / charge_b_side

                    time_diff.append(tdiff)
                    charge_ratio.append(q_rat)
                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue


    plt.hist2d(time_diff, charge_ratio, bins=[200, 100], cmap="plasma", norm=colors.LogNorm())
    plt.colorbar(label="Counts")
    plt.xlabel("time difference A-B [nsec]")
    plt.ylabel("charge ratio A/B")
    plt.yticks(np.arange(-15,15,5))
    plt.xlim(0,200)
    plt.savefig("tdiff_vs_charge_ratio.pdf")
    plt.show()
