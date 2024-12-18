import numpy as np
import sys
from tqdm import tqdm
import pathlib
from pathlib import Path
import io
import contextlib
import gaps_online as go
import go_pybindings as gop
import re
from glob import glob
import os
import argparse
import matplotlib.pyplot as plt
import charmingbeauty.layout as lo
import polars as pl

def plot_busy(data):
    fixed_num_bins = 15
    bin_width = 18 / fixed_num_bins
    bin_edges = np.linspace(-bin_width / 2, 18 + bin_width / 2, fixed_num_bins + 1)
    data = np.array(data)
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
    ax.set_ylabel('n')
    ax.set_xlabel('tiu busy counts [10 nsec clk cycles]')
    ax.set_title('tiu busy count distribution')
    ax.hist(data, bins=bin_edges, histtype = 'step', align = 'mid')
    print(f"--> Avg tiu lost count {data.mean()}")
    return fig

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MTB rate plot from telemetered binary files')
    parser.add_argument('--telemetry-dir', default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start-time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end-time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')
    parser.add_argument('-w','--writdir', help='Outdir to save plots', default='')

    args = parser.parse_args()

    # preparing writdir for plots
    outdir = args.writdir
    if not outdir:
        # create generic output directory
        outdir = 'plots'
    outdir = Path(outdir)
    if not outdir.exists():
        outdir.mkdir(parents=True)

    tiu_busy_cnt = []

    files = go.io.get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)
    for f in tqdm(files, desc='Reading files..'):
        treader = go.io.TelemetryPacketReader(str(f))
        for pack in treader:
            if pack.header.packet_type == go.io.TelemetryPacketType.AnyTofHK:
                tp = go.io.TofPacket()
                tp.from_bytestream(pack.payload, 0)

                if tp.packet_type == go.io.TofPacketType.MonitorMtb:
                    mtb_moni = go.tof.monitoring.MtbMoniData()
                    mtb_moni.from_tofpacket(tp)
                    count = mtb_moni.tiu_busy_len
                    tiu_busy_cnt.append(count)



    fig = plot_busy(tiu_busy_cnt)
    fig.savefig(outdir/'tiu_busy_cnt.png', dpi = 300)


