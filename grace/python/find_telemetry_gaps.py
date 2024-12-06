import gaps_online as go
from tqdm import tqdm
import argparse
from pathlib import Path



if __name__ == '__main__':

    gcu_time = []

    parser = argparse.ArgumentParser(description='MTB rate plot from telemetered binary files')
    parser.add_argument('--telemetry-dir', default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start-time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end-time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')
    parser.add_argument('-w','--writdir', help='Outdir to save plots', default='')
    parser.add_argument('-t', '--threshold', type = int, default = 5, help = 'The amount of time defined to constitute a gap in data')

    args = parser.parse_args()

    GAP_THRESHOLD = args.threshold

    # preparing writdir for plots
    outdir = args.writdir
    if not outdir:
        # create generic output directory
        outdir = 'plots'
    outdir = Path(outdir)
    if not outdir.exists():
        outdir.mkdir(parents=True)


files = go.io.get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)
for f in tqdm(files, desc='Reading files..'):
    treader = go.io.TelemetryPacketReader(str(f))
    for pack in treader:
        t = pack.header.gcutime
        gcu_time.append(t)

# Make a copy of the original list
original_gcu_time = gcu_time[:]

# Sort the timestamps in ascending order
gcu_time.sort()

# Compare sorted list with the original
if gcu_time == original_gcu_time:
    print("Timestamps arrived in order")
else:
    print("Timestamps did not arrive in order")


# Find time gaps
time_gaps = []
for i in range(1, len(gcu_time)):
    if gcu_time[i] - gcu_time[i - 1] > GAP_THRESHOLD:
        time_gaps.append((gcu_time[i - 1], gcu_time[i]))

# Output the result
if time_gaps:
    print(f"Found {len(time_gaps)} gaps exceeding {GAP_THRESHOLD} seconds:")
    for start, stop in time_gaps:
        print(f"Gap from {start} to {stop} (duration: {stop - start} seconds)")
else:
    print("No significant gaps found.")
