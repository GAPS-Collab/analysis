import gaps_online as go
from tqdm import tqdm
import argparse
import numpy as np
import matplotlib.pyplot as plt
import re
from glob import glob
from pathlib import Path
import go_pybindings as gop
import matplotlib.colors as colors


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

    return (right_idx - left_idx) * 0.5 #1024 bins = 512 nsec, simple conversion from bins to time

parser = argparse.ArgumentParser(prog = 'create heatmap of FWHM vs peak height')
parser.add_argument('-rd', '--raw_dir', default='', help = 'path to .tof.gaps files')
parser.add_argument('-id', '--run_id', default = 0, help = 'the run id')
parser.add_argument('-c', required=True, help='path to calibrations dir')
parser.add_argument('-p', help='path to paddle mapping.csv')
args = parser.parse_args()

if __name__ == '__main__':
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

    print('Finished Calibrating')

    tof_run_path = Path(args.raw_dir)
    tof_files = np.array([str(f) for f in ((tof_run_path.glob('*.tof.gaps')))])
    tof_f_nums = [int(file.split('.')[0].split('_')[-1]) for file in tof_files]
    tof_files = tof_files[np.argsort(tof_f_nums)]
    
    print('Finished loading TOF files')

    peak_height_all = []
    fwhm_all        = []
    peak_height_a   = []
    fwhm_a          = []
    peak_height_b   = []
    fwhm_b          = []

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

                            peak  = np.max(voltages)
                            width = fwhm(voltages)
                            
                            if peak <= 0 or width >= 100: continue
                            else:
                                peak_height_all.append(peak)
                                peak_height_a.append(peak)
                                fwhm_all.append(width)
                                fwhm_a.append(width)

                    rb = paddle_map[paddle]['b']['rb']
                    ch = paddle_map[paddle]['b']['ch']
                    for waveform in tof_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel_b == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            voltages = np.array(waveform.voltages_b)
                            
                            peak  = np.max(voltages)
                            width = fwhm(voltages)
                            
                            if peak <= 0 or width >= 100: continue
                            else:
                                peak_height_all.append(peak)
                                peak_height_b.append(peak)
                                fwhm_all.append(width)
                                fwhm_b.append(width)
    
                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue
    
    print('Finished reading data')
    
    peak_height_all = np.array(peak_height_all)
    peak_height_a   = np.array(peak_height_a)
    peak_height_b   = np.array(peak_height_b)

    fwhm_all        = np.array(fwhm_all)
    fwhm_a          = np.array(fwhm_a)
    fwhm_b          = np.array(fwhm_b)

    plt.figure()
    h0 = plt.hist2d(peak_height_all, fwhm_all, bins=(200,100), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h0[3])
    plt.xlabel('Peak Height [mV]')
    plt.ylabel('FWHM [nsec]')
    plt.xlim(0,1000)
    plt.minorticks_on()
    plt.savefig('peak_vs_fwhm_heatmap_all.pdf')

    print('Plot 1/3 done')

    plt.figure()
    h1 = plt.hist2d(peak_height_a, fwhm_a, bins = (200,100), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h1[3])
    plt.xlabel('Peak Height [mV]')
    plt.ylabel('FWHM [nsec]')
    plt.xlim(0,1000)
    plt.minorticks_on()
    plt.savefig('peak_vs_fwhm_heatmap_a_side.pdf')

    print('Plot 2/3 done')

    plt.figure()
    h2 = plt.hist2d(peak_height_b, fwhm_b, bins = (100,100), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h2[3])
    plt.xlabel('Peak Height [mV]')
    plt.ylabel('FWHM [nsec]')
    plt.xlim(0,1000)
    plt.minorticks_on()
    plt.savefig('peak_vs_fwhm_heatmap_b_side.pdf')

    print('Plot 3/3 done')
    print('goodbye and goodluck')
    
    np.savetxt("peak_height_all.txt", peak_height_all)
    np.savetxt("peak_height_a.txt", peak_height_a)
    np.savetxt("peak_height_b.txt", peak_height_b)

    np.savetxt("fwhm_all.txt", fwhm_all)
    np.savetxt("fwhm_a.txt", fwhm_a)
    np.savetxt("fwhm_b.txt", fwhm_b)

