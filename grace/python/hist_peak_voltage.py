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

    peak = []
    
    for f in tqdm(tof_files, desc = 'reading raw .tof.gaps files'):
        reader = go.io.TofPacketReader(str(f), filter = go.io.TofPacketType.TofEvent)
        for pack in reader:
            tof_ev = go.events.TofEvent()
            tof_ev.from_tofpacket(pack)
            for x in range(len(tof_ev.hits)):
                try:
                    peak_a = tof_ev.hits[x].peak_a
                    peak_b = tof_ev.hits[x].peak_b

                    peak.append(peak_a)
                    peak.append(peak_b)
                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue


    plt.hist(peak, bins=100, histtype='step', color='dodgerblue')
    plt.xlabel("peak voltage from TofEventSummary [?]")
    plt.ylabel("n")
    plt.savefig("TES_peak_hist.pdf")
    plt.show()
