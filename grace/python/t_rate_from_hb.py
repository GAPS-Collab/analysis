import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import sys
from tqdm import tqdm
import pathlib
from pathlib import Path
import contextlib
import io
import go_pybindings as go
import gaps_online.db as db

run_path = Path('/Users/gracetytus/gaps/test_charge_data/30198')

files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]

reader = go.io.TofPacketReader(str(files[0])) ## you can also look at more files! i just used this one to test things out

mtb_hb      = []
for f in tqdm(files, desc="Processing files", unit="file", file=sys.stdout):

    reader = go.io.TofPacketReader(str(f))
    for pack in reader:
        
        if pack.packet_type == go.io.PacketType.MTBHeartbeat:
            hb = go.commands.MTBHeartbeat()
            try: 
                hb.from_tofpacket(pack)
                mtb_hb.append(hb)
            except: continue
    
t_rate = []
lost_rate = []

for hb in mtb_hb:
    trate = hb.trate
    lrate = hb.lost_trate
    
    t_rate.append(trate)
    lost_rate.append(lrate)

    '''
    Other possible things you can get from MTBHeartbeat:
    evq_num_events_avg, evq_num_events_last, n_ev_missed, n_ev_unsent, n_events, total_elapsed (total elapsed time or mission elapsed time)
    '''



