import numpy as np
import argparse
from tqdm import tqdm
import gondola as go

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MTB rate plot from telemetered binary files')
    parser.add_argument('--telemetry-dir', default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start-time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end-time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')

    args = parser.parse_args()

    mtb_rate = []

    files = go.io.get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)
    for f in tqdm(files, desc='Reading files..'):
        treader = go.io.TelemetryPacketReader(str(f))
        for pack in treader:
            if pack.header.packet_type == go.io.TelemetryPacketType.AnyTofHK: 
                tp = go.io.TofPacket()
                tp.from_bytestream(pack.payload, 0)

                if tp.packet_type == go.io.TofPacketType.MTBHeartbeat:
                    hb = go.commands.EVTBLDRHeartbeat()
                    try: 
                        hb.from_tofpacket(tp)
                        n_sent = hb.n_events
                        total_elapsed = hb.total_elapsed

                        rate = n_sent/total_elapsed
                        mtb_rate.append(rate)


                    except Exception as e:
                        print(f"Error: {e}")

    mtb_rate = np.array(mtb_rate)
    max_rate = np.max(mtb_rate)
    min_rate = np.min(mtb_rate)
    avg_rate = np.average(mtb_rate)

    print(f'-> Max MTB rate recorded: {max_rate}')
    print(f'-> Min MTB rate recorded: {min_rate}')
    print(f'-> Average MTB rate recorded: {avg_rate}')
