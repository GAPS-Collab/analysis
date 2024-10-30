import gaps_online as go
import argparse
import numpy as np
import io
import contextlib
from tqdm import tqdm
import sys
import go_pybindings as gop
import re
from glob import glob
import os

parser = argparse.ArgumentParser(prog = 'file divide', description = 'produces N lists of files, each a subset of the full list')

parser.add_argument('-s', '--settings', help='name of settings file by default uses run{n}.toml where n is the directory')
parser.add_argument('-n', required=True, help='file list number to use i.e. setn.lst')
parser.add_argument('-c', required=True, help='path to calibrations dir')
parser.add_argument('-p', help='path to paddle mapping.csv')

args = parser.parse_args()

with open(f'intermediaries/set{args.n}.lst') as in_file:
    files = [f.strip() for f in in_file]

if args.settings is None:
    args.settings = f'{files[0][:files[0].rfind('/')]}/run{files[0].split('/')[-2]}.toml'

analysis_vals = {
    'q_a': [],
    'q_b': [],
    'time_a': [],
    'time_b': [],
    'v_a': [],
    'v_b': [],
    'waveform_a': [],
    'waveform_b': []
}

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
        cali.from_file(fname) 
        calib[int(rbid)] = cali
    else:
        print("No match found for:", fname)

with contextlib.redirect_stderr(io.StringIO()):
    for file in tqdm(files, desc="Processing files", unit="file", file=sys.stdout):
        reader = go.rust_api.io.TofPacketReader(file, filter=go.rust_api.io.PacketType.TofEvent)
        settings = go.liftof.LiftofSettings()
        settings = settings.from_file(args.settings)

        n_packets = 0
        for pack in reader:
            n_packets += 1

        reader.rewind()
        
        for pack in tqdm(reader, total=n_packets, file=sys.stdout, position=0):
            ev = go.rust_api.events.TofEvent()
            new_ev = go.liftof.waveform_analysis(ev, settings)
            
            try:
                ev.from_tofpacket(pack)
                new_ev.from_tofpacket(pack)
                
            except Exception as e:
                print(f"Error at hit {x}: {e}")
                pass
                continue
                
            for x in range(len(new_ev.hits)):
                try:

                    paddle = int(new_ev.hits[x].paddle_id)
                    if new_ev.hits[x].charge_a == 0 or new_ev.hits[x].charge_b == 0:
                        continue

                    q = new_ev.hits[x].charge_a
                    v = new_ev.hits[x].peak_a
                    t = new_ev.hits[x].time_a

                    rb = paddle_map[paddle]['a']['rb']
                    ch = paddle_map[paddle]['a']['ch']
                    if ch == 8: continue
                    for waveform in new_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()

                            analysis_vals['waveform_a'].append(waveform.voltages)
                            analysis_vals['time_a'].append(t)
                            analysis_vals['q_a'].append(q)
                            analysis_vals['v_a'].append(v)
                            break

                    q = new_ev.hits[x].charge_b
                    v = new_ev.hits[x].peak_b
                    t = new_ev.hits[x].time_b
                    
                    rb = paddle_map[paddle]['b']['rb']
                    ch = paddle_map[paddle]['b']['ch']
                    if ch == 8: continue
                    for waveform in new_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            analysis_vals['waveform_b'].append(waveform.voltages)
                            analysis_vals['time_b'].append(t)
                            analysis_vals['q_b'].append(q)
                            analysis_vals['v_b'].append(v)
                            break
                    
    
                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue
    
with open(f'intermediaries/output_wv_{args.n}.txt', 'w+') as out_file:
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
