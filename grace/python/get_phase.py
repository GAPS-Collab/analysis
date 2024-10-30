from tqdm import tqdm
import pathlib
from pathlib import Path
import io
import numpy as np
import sys
import go_pybindings as go
import gaps_online.db as db

run_path = Path('/Users/gracetytus/gaps/test_charge_data/30198')

files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]

p_list = []

for f in tqdm(files, desc="Processing files", unit="file", file=sys.stdout):
        reader = go.io.TofPacketReader(str(f), filter=go.io.PacketType.TofEvent)
        
        for pack in reader:
            ev = go.events.TofEvent()
            ev.from_tofpacket(pack)

            tes = ev.get_summary() #this is a feature of my use of .tof.gaps files, but my point in doing this is to show how you get it from the TofEventSummary

            for x in range(len(tes.hits)):
                phase = ev.hits[x].phase
                p_list.append(phase)