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


def mtb_rate_plot(data : list):
    """
    Create a plot of MTB rates + MTB lost rate for these quantities
    as extrected from the telemetry stream

    # Arguments:
        data :  A list of tuples (met, MtbMoniData) where met is the
                "mission elapsed time" in seconds, which we can get
                from the TelemetryPacketHeader
                Alternatively, this can be a list of polars dataframes
                obtained from MtbMoniData as well
    """
    fig = plt.figure(figsize=lo.FIGSIZE_A4_LANDSCAPE_HALF_HEIGHT)
    plt.style.use('publication.rc')
    ax = fig.gca()
    ax.set_ylabel('Hz', loc='top')
    ax.set_xlabel('MET [s] (gcu)')
    if isinstance(data[0], pl.DataFrame):
        stacked = pl.concat([k[1] for k in data])
        rates   = stacked['rate']
        l_rates = stacked['lost_rate']
        times   = range(len(rates))
        times   = 20*np.array(times) # mtb moni every 20s
        
        #rates   = np.array([j[1]['rate'] for j in data])
        #l_rates = np.array([j[1]['lost_rate'] for j in data])
    else:
        rates   = np.array([j[1].rate for j in data])
        l_rates = np.array([j[1].lost_rate for j in data])
        times   = np.array([j[0] for j in data])
        times  -= times[0]
        times   /= 1e9
    #print(times[l_rates < 500][-1])
    print(f'-> Avg MTB rate {rates.mean()}')
    print(f'-> Avg Lost rate {l_rates.mean()}')
    ax.plot(times, rates, lw=0.8, alpha=0.7, label='rate')
    ax.plot(times, l_rates, lw=0.8, alpha=0.7, label='lost rate')
    ax.legend(loc='upper right', frameon=False)
    ax.set_title(f'MTB rates', loc='right')
    return fig

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MTB rate plot from telemetered binary files')
    parser.add_argument('--telemetry-dir', default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start-time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end-time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')
    parser.add_argument('-w','--writdir', help='Outdir to save plots', default='')

    args = parser.parse_args()

    # preparing outdir for plots
    outdir = args.outdir
    if not outdir:
        # create generic output directory
        outdir = 'plots'
    outdir = Path(outdir)
    if not outdir.exists():
        outdir.mkdir(parents=True)

    # extracting from binaries
    mtb_moni_series = []

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
                    mtb_moni_series.append((pack.header.gcutime,mtb_moni))

    fig = mtb_rate_plot(mtb_moni_series)
    fig.savefig(outdir / 'mtb_rates.png')




