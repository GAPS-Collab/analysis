import gaps_online as go
from tqdm import tqdm
from pathlib import Path
import go_pybindings as gop
from glob import glob
import argparse
import numpy as np
import re
import matplotlib.pyplot as plt
#import gaps_pybindings as gop

parser = argparse.ArgumentParser(prog = 'get average wf for 650-749 mV energy deposition')
parser.add_argument('-rd', '--raw_dir', default='', help = 'path to .tof.gaps files')
parser.add_argument('-id', '--run_id', default = 0, help = 'the run id')
parser.add_argument('-c', required=True, help='path to calibrations dir')
parser.add_argument('-p', help='path to paddle mapping.csv')
args = parser.parse_args()

if __name__ == '__main__':
    wfs = []
    paddle_map = {}
    with open('/home/gtytus/analysis/resources/channel_mapping.csv') as in_file:
        variables = next(in_file).strip().split(',')
        next(in_file)
        for line in in_file:
            row = line.strip().split(',')
            paddle_id = int(row[0])
            paddle_map[paddle_id] = {'a':{'rb':0,'ch':0},'b':{'rb':0,'ch':0}}
            rb, ch = [int(d) for d in row[9].split('-')]
            paddle_map[paddle_id]['a']['rb'] = rb
            paddle_map[paddle_id]['a']['ch'] = ch - 1

            row = next(in_file).strip().split(',')
            rb, ch = [int(d) for d in row[9].split('-')]
            paddle_map[paddle_id]['b']['rb'] = rb
            paddle_map[paddle_id]['b']['ch'] = ch - 1

    pattern = re.compile(r'RB(\d+)_\d{6}_\d{6}UTC\.cali\.tof\.gaps')
    calibrations = glob(f'{args.c}/*.cali.tof.gaps')

    calib = {}

    for fname in calibrations:
        match = pattern.search(fname)
        if match:
            rbid = match.group(1)
            cali = gop.events.RBCalibration()
            cali.from_file(fname) 
            calib[int(rbid)] = cali
        else:
            print("No match found for:", fname)
    #print(calib)

    tof_run_path = Path(args.raw_dir)
    tof_files = np.array([str(f) for f in ((tof_run_path.glob('*.tof.gaps')))])
    tof_f_nums = [int(file.split('.')[0].split('_')[-1]) for file in tof_files]
    tof_files = tof_files[np.argsort(tof_f_nums)]

    for f in tqdm(tof_files[:5], desc = 'reading raw .tof.gaps files'):
        reader = go.io.TofPacketReader(str(f), filter = go.io.TofPacketType.TofEvent)
        for pack in reader:
            tof_ev = go.events.TofEvent()
            tof_ev.from_tofpacket(pack)
            for x in range(len(tof_ev.hits)):
                try: 
                    paddle = int(tof_ev.hits[x].paddle_id)
                    rb = paddle_map[paddle]['a']['rb']
                    ch = paddle_map[paddle]['a']['ch']
                    for waveform in tof_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel_a == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            voltages = np.array(waveform.voltages_a)
                            if np.max(voltages) > 650 and np.max(voltages) < 725:
                                wfs.append(voltages)
                    rb = paddle_map[paddle]['b']['rb']
                    ch = paddle_map[paddle]['b']['ch']
                    for waveform in tof_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel_b == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            voltages = np.array(waveform.voltages_b)
                            if np.max(voltages) > 650 and np.max(voltages) < 725:
                                wfs.append(voltages)
                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue
    print(str(len(wfs)) + ' waveforms found with peak > 650 mV and less than 725 mV')
    x = np.arange(0,len(wfs[0]), 1)
    for i in range(len(wfs)):
        #peak_idx = np.argmax(wfs[i])
        #aligned_wf = np.roll(wfs[i], -peak_idx)
        plt.plot(x-np.argmax(wfs[i]), wfs[i], color = 'navy', alpha=0.25, lw = 0.5)
    plt.savefig('combo_wf.pdf')
