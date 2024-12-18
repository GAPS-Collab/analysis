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


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MTB rate plot from telemetered binary files')
    parser.add_argument('--telemetry-dir', default='', help='A directory with telemetry binaries, as received from the telemetry stream')
    parser.add_argument('-s','--start-time', type=int, default=-1, help='The run start time, e.g. as taken from the elog')
    parser.add_argument('-e','--end-time',type=int, default=-1, help='The run end time, e.g. as taken from the elog')

    args = parser.parse_args()

    tes = []

    files = go.io.get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)
    for f in tqdm(files, desc='Reading files..'):
        treader = go.io.TelemetryPacketReader(str(f))
        for pack in treader:
            if int(pack.header.packet_type) in [90, 190, 191]:
                try:
                    ev = go.events.MergedEvent()
                    ev.from_telemetrypacket(pack)

                    summary = ev.tof
                    tes.append(summary)


                except Exception as e:
                    print(f"Error: {e}")
    print(tes[0])
    print(len(tes))
