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
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
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
    #print(times[l_rates < 500][-1])
    print(f'-> Avg MTB rate {rates.mean()}')
    print(f'-> Avg Lost rate {l_rates.mean()}')
    ax.plot(times, rates, lw=0.8, alpha=0.7, label='rate')
    ax.plot(times, l_rates, lw=0.8, alpha=0.7, label='lost rate')
    ax.legend(loc='upper right', frameon=False)
    ax.set_title(f'MTB rates', loc='right')
    return fig

def hg_dropped_plot(data: list):
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
    ax.set_ylabel(r'\% dropped HG hits')
    ax.set_xlabel('met [s] (gcu)')
    ax.set_ylim((0, 100))
    ax.minorticks_on()

    times = np.array([j[0] for j in data])
    times -= times[0]
    times /= 1e9
    hg_dropped = np.array([j[1] for j in data])

    ax.scatter(times, hg_dropped, s = 0.1)
    #ax.legend()
    ax.set_title(r'\% dropped HG hits over time')
    return fig

def timeout_plot(data: list):
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
    ax.set_ylabel(r'\% timed out events')
    ax.set_xlabel('met [s] (gcu)')
    ax.set_ylim((0, 100))
    ax.minorticks_on()

    times = np.array([j[0] for j in data])
    times -= times[0]
    times /= 1e9
    hg_dropped = np.array([j[1] for j in data])

    ax.scatter(times, hg_dropped, s = 0.1)
    #ax.legend()
    ax.set_title(r'\% timed out events over time')
    return fig

def merged_event_rate_plot(data: list):
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
    ax.set_ylabel(r'Merged Event Rate')
    ax.set_xlabel('met [s] (gcu)')
    #ax.set_ylim((0, 100))
    ax.minorticks_on()

    times = np.array([j[0] for j in data])
    times -= times[0]
    #times /= 1e9
    rate = np.array([j[1].rate for j in data])

    ax.scatter(times, rate, s = 0.1)
    #ax.legend()
    ax.set_title(r'Merged Event Rate over time')
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

    # extracting from binaries
    mtb_moni_series = []
    hg_dropped = []
    te_evts = []
    num_mangled_flag = 0
    num_mangled = 0
    num_merged = 0
    num_hg = 0
    num_lg = 0
    num_packets = 0
    merged_events = []
    undecodables = 0
    num_evts = 0

    files = go.io.get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)
    for f in tqdm(files, desc='Reading files..'):
        treader = go.io.TelemetryPacketReader(str(f))
        for pack in treader:
            num_packets += 1

            if int(pack.header.packet_type) in [90, 190, 191, 192]:
                num_merged += 1
                if int(pack.header.packet_type) in [90, 190, 191]:
                    try:
                        ev = go.events.MergedEvent()
                        ev.from_telemetrypacket(pack)
                        num_evts +=1 
                        status = ev.tof.status
                        #merged_events.append((pack.header.gcutime, ev))
                        if int(status) == 16:
                            num_mangled_flag += 1

                        nlg = ev.tof.trigger_hits
                        num_lg += len(nlg)

                        nhg = ev.tof.hits
                        num_hg += len(nhg)

                        mangled_event_flag = False
                        for x in range(len(nlg)):
                            peak1 = nlg[x].peak_a
                            peak2 = nlg[x].peak_b

                            if peak1 > 200 or peak1 < -200 or peak2 > 200 or peak2 < -200:
                                if not mangled_event_flag:
                                    num_mangled += 1
                                    mangled_event_flag = True
                                break

                    except Exception as e:
                        print(f"Error: {e}")
                        undecodables +=1 
            if pack.header.packet_type == go.io.TelemetryPacketType.AnyTofHK: 
                tp = go.io.TofPacket()
                tp.from_bytestream(pack.payload, 0)

                if tp.packet_type == go.io.TofPacketType.MonitorMtb:
                    mtb_moni = go.tof.monitoring.MtbMoniData()
                    mtb_moni.from_tofpacket(tp)
                    mtb_moni_series.append((pack.header.gcutime,mtb_moni))
                
                if tp.packet_type == go.io.TofPacketType.EVTBLDRHeartbeat:
                    hb = go.commands.EVTBLDRHeartbeat()
                    try: 
                        hb.from_tofpacket(tp)
                        rb_disc = hb.n_rbe_discarded_tot
                        rb_rec = hb.n_rbe_received_tot

                        if rb_rec != 0:
                            percent_disc = (rb_disc / rb_rec) * 100
                            percent_disc = round(percent_disc, 1)
                            if percent_disc != 100.0:
                                hg_dropped.append((pack.header.gcutime, percent_disc))

                        nte = hb.n_timed_out
                        nsend = hb.n_sent
                        percent_te = (nte / nsend) * 100
                        te_evts.append((pack.header.gcutime, percent_te))

                    except Exception as e:
                        print(f"Error: {e}")

    fig0 = mtb_rate_plot(mtb_moni_series)
    fig0.savefig(outdir / 'mtb_rates.png', dpi = 300)

    fig1 = hg_dropped_plot(hg_dropped)
    fig1.savefig(outdir/ 'hg_dropped.png', dpi = 300)

    fig2 = timeout_plot(te_evts)
    fig2.savefig(outdir/ 'te_evts.png', dpi = 300)
    
    #fig3 = merged_event_rate_plot(merged_events)
    #fig3.savefig(outdir/ 'merged_evt_rate.png', dpi = 300)
    try:
        hit_ratio = num_hg / num_lg
        hit_ratio = round(hit_ratio, 2)
        mangled_ratio = num_mangled / num_evts
        mangled_ratio = round(mangled_ratio,2)
        mangled_percent = mangled_ratio * 100
    except Exception as e:
        hit_ratio = 0
        print(f"Error: {e}")


    print(f'-> Found {num_evts} events!')
    print(f'-> Found {num_mangled} events with data mangling: {mangled_percent} %')
    print(f'-> Num. events with data mangling flag: {num_mangled_flag}')
    print(f'-> Read {num_packets} telemetry packets for this run!')
    print(f'-> Found {num_merged} merged event packets for this run!')
    print(f'-> Found a ratio of {num_hg}/{num_lg} = {hit_ratio} HG hits to LG hits for this run!')
    print(f'-> {undecodables} merged events failed to be unpacked')
    
