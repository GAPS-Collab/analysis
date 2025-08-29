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

parser = argparse.ArgumentParser(prog = 'create heatmap of time>550mV vs charge')
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

    peak_actual = []
    peak_calc = []
    peak_err_y_low = []
    peak_err_y_high = []
    
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

                            if 600.0 <= peak <= 700.0:
                                time_ns = time_over_threshold(voltages)
                                peak_actual.append(peak)
                                
                                if 2.9 <= time_ns < 3.4:
                                    peak_from_tot = 610.0026331203303
                                    peak_err_low = 7.581254204453103
                                    peak_err_high = 7.568196019619222

                                elif 3.4 <= time_ns < 4.0:
                                    peak_from_tot = 634.8939824280004
                                    peak_err_low = 12.4929940177974
                                    peak_err_high = 12.458883251453813

                                elif 4.0 <= time_ns < 4.5:
                                    peak_from_tot = 659.8495656149304
                                    peak_err_low = 7.800654072112707
                                    peak_err_high = 7.769806799386743

                                elif 4.5 <= time_ns <= 5.0:
                                    peak_from_tot = 684.9944558911562
                                    peak_err_low = 12.790515924626334
                                    peak_err_high = 12.693832477760793

                                else: continue

                                peak_calc.append(peak_from_tot)
                                peak_err_y_low.append(peak_y_low)
                                peak_err_y_high.append(peak_err_high)

                    # --- Side B ---
                    rb = paddle_map[paddle]['b']['rb']
                    ch = paddle_map[paddle]['b']['ch']
                    for waveform in tof_ev.waveforms:
                        if waveform.rb_id == rb and waveform.rb_channel_b == ch:
                            waveform.calibrate(calib[rb])
                            waveform.apply_spike_filter()
                            voltages = np.array(waveform.voltages_b)
                            peak  = np.max(voltages)

                            if 600.0 <= peak <= 700.0:
                            time_ns = time_over_threshold(voltages)
                            peak_actual.append(peak)

                            if 2.9 <= time_ns < 3.4:
                                peak_from_tot = 610.0026331203303
                                peak_err_low = 7.581254204453103
                                peak_err_high = 7.568196019619222

                            elif 3.4 <= time_ns < 4.0:
                                peak_from_tot = 634.8939824280004
                                peak_err_low = 12.4929940177974
                                peak_err_high = 12.458883251453813

                            elif 4.0 <= time_ns < 4.5:
                                peak_from_tot = 659.8495656149304
                                peak_err_low = 7.800654072112707
                                peak_err_high = 7.769806799386743

                            elif 4.5 <= time_ns <= 5.0:
                                peak_from_tot = 684.9944558911562
                                peak_err_low = 12.790515924626334
                                peak_err_high = 12.693832477760793

                            else: continue

                            peak_calc.append(peak_from_tot)
                            peak_err_y_low.append(peak_y_low)
                            peak_err_y_high.append(peak_err_high)

                except Exception as e:
                    print(f"Error at hit {x}: {e}")
                    continue

    print('Finished reading data')
    
    plt.figure()
    plt.errorbar(
    peak_actual,           # x-axis: true peaks
    peak_calc,             # y-axis: calculated peaks
    yerr=[peak_err_y_low, peak_err_y_high],  # asymmetric errors in y
    fmt='o',               # marker style
    capsize=5              # size of the error bar caps
    )

    plt.xlabel("Actual Peak [mV]")
    plt.ylabel("Calculated Peak based on TOT [mV]")
    plt.title("TOT Peak vs. Actual Peak")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('tot_peak_vs_real_peak.pdf')

