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

def align_wf(wf, peak_index):
    shift_amount = peak_index - np.argmax(wf)
    if shift_amount > 0:
        return np.r_[np.zeros(shift_amount), wf[:-shift_amount]]
    elif shift_amount < 0:
        return np.r_[wf[-shift_amount:], np.zeros(-shift_amount)]
    else:
        return wf

def fwhm(wf):
    peak_idx = np.argmax(wf)
    peak_val = wf[peak_idx]
    half_max = peak_val / 2.0

    # Find left crossing
    left_idx = np.where(wf[:peak_idx] <= half_max)[0]
    left_idx = left_idx[-1] if len(left_idx) > 0 else 0

    # Find right crossing
    right_idx = np.where(wf[peak_idx:] <= half_max)[0]
    right_idx = right_idx[0] + peak_idx if len(right_idx) > 0 else len(wf) - 1

    return right_idx - left_idx

parser = argparse.ArgumentParser(prog = 'get average wf for 650-749 mV energy deposition')
parser.add_argument('-rd', '--raw_dir', default='', help = 'path to .tof.gaps files')
parser.add_argument('-id', '--run_id', default = 0, help = 'the run id')
parser.add_argument('-c', required=True, help='path to calibrations dir')
parser.add_argument('-p', help='path to paddle mapping.csv')
args = parser.parse_args()

if __name__ == '__main__':
    wfs = np.zeros(1024, dtype=float)
    n_wfs = 0
    fwhm_vals =[]
    n_pass_fwhm = 0

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

    for f in tqdm(tof_files, desc = 'reading raw .tof.gaps files'):
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
                                aligned_wf = align_wf(voltages, 500)
                                #wfs += np.array(aligned_wf)
                                n_wfs += 1
                                width = fwhm(aligned_wf)
                                fwhm_vals.append(width)
                                if width >= 20 and width < 22:
                                    wfs += np.array(aligned_wf)
                                    n_pass_fwhm += 1
                    rb = paddle_map[paddle]['b']['rb']
                    ch = paddle_map[paddle]['b']['ch']
                    for waveform in tof_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel_b == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            voltages = np.array(waveform.voltages_b)
                            if np.max(voltages) > 650 and np.max(voltages) < 725:
                                aligned_wf = align_wf(voltages, 500)
                                #wfs += np.array(aligned_wf)
                                n_wfs += 1
                                width = fwhm(aligned_wf)
                                fwhm_vals.append(width)
                                if width >=20 and width <22:
                                    wfs += np.array(aligned_wf)
                                    n_pass_fwhm += 1

                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue
    wfs = wfs/n_wfs

    print(str(n_wfs) + ' waveforms found with peak > 650 mV and less than 725 mV')
    print(str(n_pass_fwhm) + ' waveforms found with a FWHM between 20 and 22')
    x = np.arange(0,len(wfs), 1)
    plt.figure()
    plt.plot(x-np.argmax(wfs), wfs, color = 'navy', alpha=0.25, lw = 0.5)
    plt.xlim(-50, 200)
    plt.savefig('avg_wf.pdf')
    
    x_shifted = x-np.argmax(wfs)
    mask = (x_shifted >= -50) & (x_shifted <= 250)

    data = np.column_stack((x_shifted[mask], wfs[mask]))
    np.savetxt('average_waveform.txt', data, fmt="%.6f", header="x y")
    
    plt.figure()
    plt.hist(fwhm_vals, histtype='step', bins=30)
    plt.xlim(0,50)
    plt.minorticks_on()
    plt.savefig('fwhm_dist_650_725.pdf')
