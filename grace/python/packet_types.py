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

    num_packets = 0
    num_merged = 0
    type90 = 0
    type190 = 0
    type191 = 0
    type192 = 0
    type0 = 0
    type30 = 0
    type40 = 0
    type50 = 0
    type80 = 0
    type81 = 0
    type82 = 0
    type83 = 0
    type91 = 0
    type92 = 0
    type93 = 0
    type100 = 0
    type108 = 0
    type110 = 0
    type200 = 0
    type255 = 0
    type130 = 0
    #potentially unused below
    type33 = 0
    type34 = 0
    type37 = 0
    type38 = 0
    type55 = 0
    type64 = 0
    type96 = 0
    type214 = 0
    type4 = 0
    type56 = 0
    type93 = 0
    type94 = 0

    mtb_hb = 0
    evtbldr_hb = 0
    mtb_monitoring = 0 
    rbcalib = 0
    datahb = 0
    mtbevent = 0
    rbevtheader = 0
    cpumoni = 0
    rbmoni = 0
    pbmoni = 0
    ltbmoni = 0
    pamoni = 0
    rbeventmem = 0
    status = 0

    files = go.io.grace_get_telemetry_binaries(args.start_time, args.end_time, data_dir=args.telemetry_dir)
    for f in tqdm(files, desc='Reading files..'):
        treader = go.io.TelemetryPacketReader(str(f))
        for pack in treader:
            num_packets += 1

            if int(pack.header.packet_type) in [90, 190, 191, 192]:
                num_merged += 1
                if int(pack.header.packet_type) == 90:
                    type90 += 1
                elif int(pack.header.packet_type) == 190:
                    type190 += 1
                elif int(pack.header.packet_type) == 191:
                    type191 += 1
                elif int(pack.header.packet_type) == 192:
                    type192 += 1
            elif int(pack.header.packet_type) == 0:
                type0 += 1

            elif int(pack.header.packet_type) == 30:
                type30 += 1

            elif int(pack.header.packet_type) == 40: 
                type40 += 1

            elif int(pack.header.packet_type) == 50:
                type50 += 1

            elif int(pack.header.packet_type) == 80:
                type80 += 1

            elif int(pack.header.packet_type) == 81:
                type81 += 1

            elif int(pack.header.packet_type) == 82:
                type82 += 1

            elif int(pack.header.packet_type) == 83:
                type83 += 1

            elif int(pack.header.packet_type) == 91:
                type91 += 1

            elif int(pack.header.packet_type) == 92:
                type92 += 1
                tp = go.io.TofPacket()
                tp.from_bytestream(pack.payload, 0)

                if tp.packet_type == 90:
                    mtb_monitoring += 1

                if tp.packet_type == go.io.TofPacketType.EVTBLDRHeartbeat:
                    evtbldr_hb += 1
                
                if tp.packet_type == go.io.TofPacketType.MTBHeartbeat:
                    mtb_hb += 1

                if tp.packet_type == 130:
                    rbcalib += 1
                if tp.packet_type == 40:
                    datahb += 1

                if tp.packet_type == 60:
                    mtbevent += 1

                if tp.packet_type == 70:
                    rbevtheader += 1

                if tp.packet_type == 80:
                    cpumoni += 1

                if tp.packet_type == 100:
                    rbmoni += 1

                if tp.packet_type == 101:
                    pbmoni += 1

                if tp.packet_type == 102:
                    ltbmoni += 1

                if tp.packet_type == 103:
                    pamoni += 1

                if tp.packet_type == 120:
                    rbevtmem += 1

                if tp.packet_type == 171:
                    status += 1

            elif int(pack.header.packet_type) == 93:
                type93 += 1

            elif int(pack.header.packet_type) == 100:
                type100 += 1

            elif int(pack.header.packet_type) == 108:
                type108 += 1

            elif int(pack.header.packet_type) == 110:
                type110 += 1

            elif int(pack.header.packet_type) == 130 or int(pack.header.packet_type) in range(205, 226):
            #elif int(pack.header.packet_type) == 210 or int(pack.header.packet_type) == 211:    
                type130 += 1

            elif int(pack.header.packet_type) == 200:
                type200 += 1

            elif int(pack.header.packet_type) == 255:
                type255 += 1

            elif int(pack.header.packet_type) == 33:
                type33 += 1

            elif int(pack.header.packet_type) == 34:
                type34 += 1

            elif int(pack.header.packet_type) == 37:
                type37 += 1

            elif int(pack.header.packet_type) == 38:
                type38 += 1

            elif int(pack.header.packet_type) == 55:
                type55 += 1

            elif int(pack.header.packet_type) == 64:
                type64 += 1

            elif int(pack.header.packet_type) == 96:
                type96 += 1

            elif int(pack.header.packet_type) == 214:
                type214 += 1

            elif int(pack.header.packet_type) == 4:
                type4 += 1 

            elif int(pack.header.packet_type) == 56:
                type56 += 1

            elif int(pack.header.packet_type) == 93:
                type93 += 1

            elif int(pack.header.packet_type) == 94:
                type94 += 1



    
    print(f'-> Found {num_packets} packets')
    print('---------------------------------------------------------------------------')
    print(f'-> Found {num_merged} merged events')
    print(f'-> Found {type90} packet type 90 -- uninteresting merged events')
    print(f'-> Found {type190} packet type 190 -- interesting merged events')
    print(f'-> Found {type191} packet type 191 -- track trigger only merged events')
    print(f'-> Found {type192} packet type 192 -- no tof data merged event')
    print('---------------------------------------------------------------------------')
    print(f' -> Found {type92} packet type 92 -- AnyTofHk packets')
    print(f' -> Found {mtb_monitoring} MTBMoni packets in AnyTofHK')
    print(f' -> Found {evtbldr_hb} EventBuilderHB in AnyTofHK')
    print(f' -> Found {mtb_hb} MasterTriggerHB in AnyTofHK')
    print(f' -> Found {datahb} DataSendHB in AnytofHK')
    print(f' -> Found {mtbevent} mastertriggerevents in AnyTofHK')
    print(f' -> Found {rbevtheader} RB Event headers in AnyTofHK')
    print(f' -> Found {cpumoni} CPU Monitoring in AnyTofHK')
    print(f' -> Found {rbmoni} RBMoni in AnyTofHK')
    print(f' -> Found {pbmoni} PBMoni in AnyTofHK')
    print(f' -> Found {ltbmoni} LTBMoni in AnyTofHK')
    print(f' -> Found {pamoni} PAMoni in AnyTofHK')
    print(f' -> Found {rbeventmem} RB Event Memory in AnyTofHK')
    print(f' -> Found {status} TofDetector Status in AnyTofHK')
    print(f' -> Found {rbcalib} RB Calibrations in AnyTofHK')
    print('---------------------------------------------------------------------------')
    print(f' -> Found {type30} packet type 30 -- CardHKP')
    print(f' -> Found {type40} packet type 40 -- CoolingHKP')
    print(f' -> Found {type50} packet type 50 -- PDUHK')
    print(f' -> Found {type100} packet type 100 -- LabJackHK')
    print(f' -> Found {type108} packet type 108 -- MagHK')
    print('---------------------------------------------------------------------------')
    print(f' -> Found {type80} packet type 80 -- Tracker')
    print(f' -> Found {type255} packet type 255 -- AnyTrackerHK')
    print(f' -> Found {type81} packet type 81 - TrackerDAQCtr')
    print(f' -> Found {type82} packet type 82 --> DAQ GPS')
    print(f' -> Found {type83} packet type 83 -- TrkTempLeak')
    print('---------------------------------------------------------------------------')
    print(f' -> Found {type55} packet type 55 -- Maximum Power Point Tracking (charge controller)')
    print(f' -> Found {type56} packet type 56 -- raspi/battery')
    print('---------------------------------------------------------------------------')
    print(f' -> Found {type93} packet type 93 -- EventBuilderHKP')
    print(f' -> Found {type94} packet type 94 -- MergedEventHKP')
    print('---------------------------------------------------------------------------')
    print(f' -> Found {type200} packet type 200 -- Acknowledgement')
    print(f' -> Found {type0} packet type 0 -- UNKNOWN')
