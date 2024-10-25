import gaps_online as go
import argparse
import numpy as np
import io
import contextlib
from tqdm import tqdm
import sys

parser = argparse.ArgumentParser(prog = 'file divide', description = 'produces N lists of files, each a subset of the full list')

parser.add_argument('-s', '--settings', help='name of settings file by default uses run{n}.toml where n is the directory')
parser.add_argument('-n', required=True, help='file list number to use i.e. setn.lst')

args = parser.parse_args()

with open(f'intermediaries/set{args.n}.lst') as in_file:
    files = [f.strip() for f in in_file]

if args.settings is None:
    args.settings = f'{files[0][:files[0].rfind('/')]}/run{files[0].split('/')[-2]}.toml'

analysis_vals = {
    'charge_a_old': [],
    'charge_b_old': [],
    'charge_a_new': [],
    'charge_b_new': [],
    'peak_a_old': [],
    'peak_b_old': [],
    'peak_a_new': [],
    'peak_b_new': []
}

with contextlib.redirect_stderr(io.StringIO()):
    for file in tqdm(files, desc="Processing files", unit="file", file=sys.stdout):
        reader = go.rust_api.io.TofPacketReader(file, filter=go.rust_api.io.PacketType.TofEvent)
        settings = go.liftof.LiftofSettings()
        settings = settings.from_file(args.settings)
        
        for pack in reader:
            ev = go.rust_api.events.TofEvent()
            new_ev = go.liftof.waveform_analysis(ev, settings)
            
            try:
                ev.from_tofpacket(pack)
                new_ev.from_tofpacket(pack) ## do i need to add this line??
                
            except Exception as e:
                pass
                continue
                
            for x in range(len(ev.hits)):
                try:
                    q1_old = ev.hits[x].charge_a
                    q2_old = ev.hits[x].charge_b
                    analysis_vals['charge_a_old'].append(q1_old)
                    analysis_vals['charge_b_old'].append(q2_old)

                    v_old_a = ev.hits[x].peak_a
                    v_old_b = ev.hits[x].peak_b
                    analysis_vals['peak_a_old'].append(v_old_a)
                    analysis_vals['peak_b_old'].append(v_old_b)
                    
    
                except Exception as e:
                        pass
                        continue
    
            for y in range(len(new_ev.hits)):
                try: 
                    q1_new = new_ev.hits[x].charge_a
                    q2_new = new_ev.hits[x].charge_b
                    analysis_vals['charge_a_new'].append(q1_new)
                    analysis_vals['charge_b_new'].append(q2_new)

                    v_new_a = new_ev.hits[x].peak_a
                    v_new_b = new_ev.hits[x].peak_b
                    analysis_vals['peak_a_new'].append(v_new_a)
                    analysis_vals['peak_b_new'].append(v_new_b)
                    
                except Exception as e:
                    pass
                    continue

with open(f'intermediaries/output_{args.n}.txt', 'w+') as out_file:
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