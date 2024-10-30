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

parser = argparse.ArgumentParser(prog = 'flag 16 check', description = 'returns a tuple containing (data mangling from wv, data mangling from flag)')

parser.add_argument('path', help='path to run directory (e.g. /Volumes/gaps-ssd/134/134)')
parser.add_argument('-s', '--settings', help='name of settings file by default uses run{n}.toml where n is the directory')
parser.add_argument('-c', required=True, help='path to calibrations dir')
parser.add_argument('-p', help='path to paddle mapping.csv')

args = parser.parse_args()

analysis_vals = {
    'mangling_flag': [],
    'mangling_wv': []
}

run_path = Path(args.path)
files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
f_nums = [int(file.split('.')[0].split('_')[-1]) for file in files]
files = files[np.argsort(f_nums)]

paddle_map = {}
with open(args.p) as in_file:
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
        cali.from_file(fname)  # Modify the instance
        calib[int(rbid)] = cali      # Store the modified instance
    else:
        print("No match found for:", fname)


mangling_from_status = 0
mangling_from_wv = 0

for f in files:
        reader = go.io.TofPacketReader(str(f), filter=go.io.PacketType.TofEvent)
        settings = go.liftof.LiftofSettings()
        settings = settings.from_file(args.settings)

        n_packets = 0
        for pack in reader:
            n_packets += 1

        reader.rewind()
    
        for pack in tqdm.tqdm(reader, total=n_packets, file=sys.stdout, position=0):
            ev = go.events.TofEvent()

            try:
                ev.from_tofpacket(pack)
                status = ev.mastertriggerevent.status
                if int(status) == 16:
                    mangling_from_status += 1
        
            except Exception as e:
                print(f"Error: {e}")
                pass
                continue
            
            for x in range(len(ev.hits)):
                try: 
                    paddle = int(ev.hits[x].paddle_id)

                    rb = paddle_map[paddle]['a']['rb']
                    ch = paddle_map[paddle]['a']['ch']
                    if ch == 8: continue
                    for waveform in ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            if min(waveform.voltages < -200): 
                                mangling_from_wv += 1
                                break
                    
                    rb = paddle_map[paddle]['b']['rb']
                    ch = paddle_map[paddle]['b']['ch']
                    if ch == 8: continue
                    for waveform in ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            if min(waveform.voltages < -200): 
                                mangling_from_wv += 1
                                break
                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue

analysis_vals['mangling_flag'].append(mangling_from_status)
analysis_vals['mangling_wv'].append(mangling_from_wv)

with open(f'/home/gaps/userspace/grace/intermediaries/flag_check_{args.n}.txt', 'w+') as out_file:
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