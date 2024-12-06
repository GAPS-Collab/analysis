import gaps_online as go
from pathlib import Path
import matplotlib.pyplot as plt 
from tqdm import tqdm
import numpy as np
import argparse

def mte_ch_rec_plot(data: list):
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
    ax.set_ylabel('Len. MTE Receiver')
    ax.set_xlabel('met [s] (gcu)')
    #ax.set_ylim((0, 100))
    ax.minorticks_on()

    times = np.array([j[0] for j in data])
    times -= times[0]
    hg_dropped = np.array([j[1] for j in data])

    ax.scatter(times, hg_dropped, s = 0.1)
    #ax.legend()
    ax.set_title('Len. MTE Receiver over time')
    return fig

def rbe_ch_rec_plot(data: list):
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
    ax.set_ylabel('Len. RBE Receiver')
    ax.set_xlabel('met [s] (gcu)')
    #ax.set_ylim((0, 100))
    ax.minorticks_on()

    times = np.array([j[0] for j in data])
    times -= times[0]
    hg_dropped = np.array([j[1] for j in data])

    ax.scatter(times, hg_dropped, s = 0.1)
    #ax.legend()
    ax.set_title('Len. RBE Receiver over time')
    return fig

def mtb_evt_queue_plot(data: list):
    plt.style.use('publication.rc')
    fig, ax = plt.subplots()
    ax.set_ylabel('Len. MTB Event Queue')
    ax.set_xlabel('met [s] (gcu)')
    #ax.set_ylim((0, 100))
    ax.minorticks_on()

    times = np.array([j[0] for j in data])
    times -= times[0]
    hg_dropped = np.array([j[1] for j in data])

    ax.scatter(times, hg_dropped, s = 0.1)
    #ax.legend()
    ax.set_title('Len. MTB Event Queue over time')
    return fig

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MTB rate plot from telemetered binary files')
    parser.add_argument('--telemetry-dir', default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start-time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end-time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')
    parser.add_argument('-w','--writdir', help='Outdir to save plots', default='')
    parser.add_argument('--id', help = 'run id')

    args = parser.parse_args()

    # preparing writdir for plots
    outdir = args.writdir
    if not outdir:
        # create generic output directory
        outdir = 'plots'
    outdir = Path(outdir)
    if not outdir.exists():
        outdir.mkdir(parents=True)

    ch_len_mte_rec = []
    ch_len_rbe_rec = []
    mtb_evq        = []

    files = go.io.get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)
    for f in tqdm(files, desc='Reading files..'):
        treader = go.io.TelemetryPacketReader(str(f))
        for pack in treader:
            if pack.header.packet_type == go.io.TelemetryPacketType.AnyTofHK: 
                tp = go.io.TofPacket()
                tp.from_bytestream(pack.payload, 0)
            
                if tp.packet_type == go.io.TofPacketType.EVTBLDRHeartbeat:
                    hb = go.commands.EVTBLDRHeartbeat()
                    try: 
                        hb.from_tofpacket(tp)
                        mte_rec = hb.mte_receiver_cbc_len
                        rb_rec = hb.rbe_receiver_cbc_len

                        ch_len_mte_rec.append((pack.header.gcutime, mte_rec))
                        ch_len_rbe_rec.append((pack.header.gcutime, rb_rec))

                    except Exception as e:
                        print(f"Error: {e}")

                if tp.packet_type == go.io.TofPacketType.MTBHeartbeat:
                    hb = go.commands.MTBHeartbeat()
                    try:
                        hb.from_tofpacket(tp)
                        evq = hb.evq_num_events_avg
                        mtb_evq.append((pack.header.gcutime, evq))
                    except Exception as e:
                        print(f"Error: {e}")

    fig0 = mte_ch_rec_plot(ch_len_mte_rec)
    fig0.savefig(outdir / f'{args.id}mte_rec_ch.png', dpi = 300)

    fig1 = rbe_ch_rec_plot(ch_len_rbe_rec)
    fig1.savefig(outdir/ f'{args.id}rbe_rec_ch.png', dpi = 300)

    fig2 = mtb_evt_queue_plot(mtb_evq)
    fig2.savefig(outdir/ f'{args.id}evq.png', dpi = 300)
