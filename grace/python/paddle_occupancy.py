import gaps_online as go
from tqdm import tqdm
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Paddle occupancy graphic plot')
    parser.add_argument('-dir', --'data_dir', tyep = str, default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start_time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end_time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')
    parser.add_argument('-id', '--run_id', type=int, help = 'TOF run id' )

    args = parser.parse_args()

    
    
    runs  = { args.run_id : {'start' : args.start_time , 'end' : args.end_time, 'data_dir' : Path(args.data_dir)}}

    data = go.run.load_run_from_telemetry(**runs[args.run_id]) 
    tofevents = [k.tof for k in data['events']]
    occu = go.tof.analysis.create_occupancy_dict(events = tofevents)

    fig, ax = plt.subplots()
    fig, ax = go.tof.visual.tof_projection_xy(occu)
    fig, ax = go.tof.visual.unroll_cbe_sides(paddle_occupancy=occu)
    fig, ax = go.tof.visual.unroll_cor(paddle_occupancy=occu)

    plt.show()