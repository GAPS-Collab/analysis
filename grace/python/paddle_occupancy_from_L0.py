import gaps_online as go
from tqdm import tqdm
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import logging
import matplotlib


logger = logging.getLogger(__name__)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Paddle occupancy graphic plot')
    parser.add_argument('-dir', '--data_dir', type = str, default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-id', '--run_id', type=int, help = 'TOF run id' )

    args = parser.parse_args()

    MERGED_EVENT_TYPES     = [\
    "TelemetryPacketType.NoGapsTriggerEvent",
    "TelemetryPacketType.BoringEvent",
    "TelemetryPacketType.InterestingEvent",
    "TelemetryPacketType.NoTofDataEvent"]

#def file_loader(filename, merged_event_types = MERGED_EVENT_TYPES):

    files = Path(f'{args.data_dir}').glob('*.gaps')
    #files = [k for k in files]

    events = []
    for f in files:
        reader  = go.io.CRReader(str(f))
        for frame in reader:
                    m_type = frame.has_merged_event(frame, merged_event_types = MERGED_EVENT_TYPES)
                    if m_type is None:
                        continue
                    try:
                        ev = frame.get_mergedevent(m_type)
                    except Exception as e:
                        logger.warning(f'Merged event is corrupt! {e}')
                        continue
                    ev = ev.tof
                    events.append(ev)

    print(events[:5])


    # tofevents = [k.tof for k in data['events']]
    # occu = go.tof.analysis.create_occupancy_dict(events = tofevents)
    
    # cm = matplotlib.colormaps['gnuplot2']

    # fig1, ax1 = go.tof.visual.tof_projection_xy(occu, cmap=cm)
    # fig2, ax2 = go.tof.visual.unroll_cbe_sides(paddle_occupancy=occu, cmap=cm)
    # fig3, ax3 = go.tof.visual.unroll_cor(paddle_occupancy=occu, cmap=cm)
    
    # fig1.savefig(str(args.run_id)+'_'+str(args.start_time)+'_'+str(args.end_time)+'_12pps.pdf')
    # fig3.savefig(str(args.run_id)+'_'+str(args.start_time)+'_'+str(args.end_time)+'_10pps_3pps.pdf')
    # fig2.savefig(str(args.run_id)+'_'+str(args.start_time)+'_'+str(args.end_time)+'_8pps_1pps.pdf')