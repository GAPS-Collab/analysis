#! /home/gtytus/.rye/shims/python

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

def time_over_threshold(wf, threshold=550.0):
    """Return time (ns) waveform spends above threshold."""
    bins_above = np.sum(wf > threshold)
    return bins_above * 0.5  # 0.5 ns per bin

def overlay_mean_rms(xvals, yvals, hinfo, color='red'):
    """
    Compute mean and RMS of y per x-bin and overlay errorbars.
    """
    H, xedges, yedges, _ = hinfo
    bin_centers = 0.5 * (xedges[1:] + xedges[:-1])

    means = []
    rmss  = []
    xcent = []

    # loop over x-bins
    for i in range(len(xedges)-1):
        mask = (xvals >= xedges[i]) & (xvals < xedges[i+1])
        y_in_bin = np.array(yvals)[mask]
        if len(y_in_bin) > 0:
            mean = np.mean(y_in_bin)
            rms  = np.sqrt(np.mean((y_in_bin - mean)**2))
            means.append(mean)
            rmss.append(rms)
            xcent.append(bin_centers[i])

    plt.errorbar(xcent, means, yerr=rmss, fmt='o', color=color,
                 markersize=3, elinewidth=1, capsize=2, alpha=0.8)

parser = argparse.ArgumentParser(prog = 'create heatmap of time>550mV vs charge')
parser.add_argument('-rd', '--raw_dir', default='', help = 'path to .tof.gaps files')
parser.add_argument('-id', '--run_id', default = 0, help = 'the run id')
parser.add_argument('-c', required=True, help='path to calibrations dir')
parser.add_argument('-p', help='path to paddle mapping.csv')
parser.add_argument('-lb', '--lower_bound', default = 0, type=int, help = 'lower bound of pulse peak height considered')
parser.add_argument('-ub', '--upper_bound', default = 750, type = int, help = 'upper bound of pulse peak height considered')
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

    peak_all   = []
    tot_all      = []
    peak_a     = []
    tot_a        = []
    peak_b     = []
    tot_b        = []

    for f in tqdm(tof_files, desc = 'reading raw .tof.gaps files'):
        reader = go.io.TofPacketReader(str(f), filter = go.io.TofPacketType.TofEvent)
        for pack in reader:
            tof_ev = go.events.TofEvent()
            tof_ev.from_tofpacket(pack)
            for x in range(len(tof_ev.hits)):
                try:
                    paddle = int(tof_ev.hits[x].paddle_id)

                    # --- Side A ---
                    rb = paddle_map[paddle]['a']['rb']
                    ch = paddle_map[paddle]['a']['ch']
                    for waveform in tof_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel_a == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            voltages = np.array(waveform.voltages_a)
                            peak  = np.max(voltages)

                            if args.lower_bound <= peak <= args.upper_bound:
                                time_ns = time_over_threshold(voltages)
                                peak_all.append(peak)
                                tot_all.append(time_ns)
                                peak_a.append(peak)
                                tot_a.append(time_ns)

                    # --- Side B ---
                    rb = paddle_map[paddle]['b']['rb']
                    ch = paddle_map[paddle]['b']['ch']
                    for waveform in tof_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel_b == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            voltages = np.array(waveform.voltages_b)
                            peak  = np.max(voltages)

                            if args.lower_bound <= peak <= args.upper_bound:
                                time_ns = time_over_threshold(voltages)
                                peak_all.append(peak)
                                tot_all.append(time_ns)
                                peak_b.append(peak)
                                tot_b.append(time_ns)

                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue

    print('Finished reading data')

    # --- Plots ---
    bins_x = np.linspace(0, 20, 40)
    bins_y = np.linspace(args.lower_bound, args.upper_bound, 200)
    plt.figure()
    h0 = plt.hist2d(tot_all, peak_all, bins=(bins_x, bins_y), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h0[3])
    plt.xlim(0, 20)
    overlay_mean_rms(tot_all, peak_all, h0, color='black')
    plt.xlabel('Time Over Threshold [nsec]')
    plt.ylabel('Peak Voltage [mV]')
    plt.minorticks_on()
    plt.savefig(f'tot_vs_peak_{args.lower_bound}_{args.upper_bound}_heatmap_all.pdf')

    print('Plot 1/3 done')

    plt.figure()
    h1 = plt.hist2d(tot_a, peak_a,  bins =(bins_x, bins_y), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h1[3])
    plt.xlim(0, 20)
    overlay_mean_rms(tot_a, peak_a, h1, color='black')
    plt.xlabel('Time Over Threshold [nsec]')
    plt.ylabel('Peak Voltage [mV]')
    plt.minorticks_on()
    plt.savefig(f'tot_vs_peak_{args.lower_bound}_{args.upper_bound}_heatmap_a_side.pdf')

    print('Plot 2/3 done')

    plt.figure()
    h2 = plt.hist2d(tot_b, peak_b, bins = (bins_x, bins_y), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h2[3])
    plt.xlim(0,20)
    overlay_mean_rms(tot_b, peak_b, h2, color='black')
    plt.xlabel('Time Over Threshold [nsec]')
    plt.ylabel('Peak Voltage [mV]')
    plt.minorticks_on()
    plt.savefig(f'tot_vs_peak_{args.lower_bound}_{args.upper_bound}_heatmap_b_side.pdf')

    print('Plot 3/3 done')
    print('goodbye and goodluck')

    np.savetxt(f'tot_all_{args.lower_bound}_{args.upper_bound}.txt', tot_all)
    np.savetxt(f'tot_a_{args.lower_bound}_{args.upper_bound}.txt', tot_a)
    np.savetxt(f'tot_b_{args.lower_bound}_{args.upper_bound}.txt', tot_b)

    np.savetxt(f'peak_all_{args.lower_bound}_{args.upper_bound}.txt', peak_all)
    np.savetxt(f'peak_a_{args.lower_bound}_{args.upper_bound}.txt', peak_a)
    np.savetxt(f'peak_b_{args.lower_bound}_{args.upper_bound}.txt', peak_b)
