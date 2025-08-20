import gaps_online as go
from tqdm import tqdm
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import logging
import matplotlib
import numpy as np

logger = logging.getLogger(__name__)

def has_merged_event(frame, merged_event_types):
    for m_type in merged_event_types:
        try:
            ev = frame.get_mergedevent(m_type)
            return m_type
        except ValueError as e:
            if "Merged Event not found" in str(e):
                continue
            else: raise
    return None
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Paddle occupancy graphic plot')
    parser.add_argument('-dir', '--data_dir', type = str, default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-id', '--run_id', type=str, help = 'TOF run id' )

    args = parser.parse_args()

    MERGED_EVENT_TYPES     = [\
    "TelemetryPacketType.NoGapsTriggerEvent",
    "TelemetryPacketType.BoringEvent",
    "TelemetryPacketType.InterestingEvent",
    "TelemetryPacketType.NoTofDataEvent"]

    run_path = Path(f'{args.data_dir}')
    files = np.array([str(f) for f in ((run_path.glob('*.tof.gaps')))])
    

    tofevents = []
    stop = False 
    for f in tqdm(files):
        reader  = go.io.TofPacketReader(str(f))
        for pack in reader:
            #m_type = has_merged_event(frame, merged_event_types = MERGED_EVENT_TYPES)
            #if m_type is None:
                #continue
            #print(m_type)
        
            ev = go.events.TofEvent
            tofevents.append(ev)

    print(tofevents[0])


    # tofevents = [k.tof for k in data['events']]
    occu = go.tof.analysis.create_occupancy_dict(events = tofevents)
    
    cm = matplotlib.colormaps['gnuplot2']
    
    title1 = str(args.run_id) + '_12pps'
    title2 = str(args.run_id) + '_8pps_1pps'
    title3 = str(args.run_id) + '_10pps_3pps'

    fig1, ax1 = go.tof.visual.tof_projection_xy(occu, cmap=cm)
    fig1.suptitle(title1)
    fig2, ax2 = go.tof.visual.unroll_cbe_sides(paddle_occupancy=occu, cmap=cm)
    fig2.suptitle(title2)
    fig3, ax3 = go.tof.visual.unroll_cor(paddle_occupancy=occu, cmap=cm)
    fig3.suptitle(title3)
    
    fig1.savefig(title1 + '.pdf')
    fig3.savefig(title3 +'.pdf')
    fig2.savefig(title2 +'.pdf')
