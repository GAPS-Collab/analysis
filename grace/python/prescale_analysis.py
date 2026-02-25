from pathlib import Path
from glob import glob
from tqdm import tqdm
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import gondola as go
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='produce plots for prescale scan analysis')
    parser.add_argument('-p', '--path', type=str, help='path of .tof.gaps files')
    args = parser.parse_args()

    files = Path(f'{args.path}').glob('*.tof.gaps')

    rate_register = []
    lost_rate_register = []
    rb_rates = defaultdict(list)
    rates_hb = []

    for f in tqdm(files):
        reader = go.io.TofPacketReader(str(f))

        for packet in reader:
            if packet.packet_type == go.packets.TofPacketType.MtbMoniData:
                moni = go.monitoring.MtbMoniData.from_tofpacket(packet)
                rate = moni.rate
                lost_rate = moni.lost_rate
                rate_register.append(rate)
                lost_rate_register.append(lost_rate)

            if packet.packet_type == go.packets.TofPacketType.MasterTriggerHB:
                hb = go.monitoring.MasterTriggerHB.from_tofpacket(packet)
                rate = hb.trate
                rates_hb.append(rate)
        
            if packet.packet_type == go.packets.TofPacketType.RBMoniData:
                rb_moni = go.monitoring.RBMoniData.from_tofpacket(packet)
                rb_id = rb_moni.board_id
                rb_rate = rb_moni.rate
                rb_rates[rb_id].append(rb_rate)


    avg_rate_register = np.average(np.array(rate_register))
    avg_lost_rate_register = np.average(np.array(lost_rate_register))
    avg_rate_hb = np.average(np.array(rates_hb))
    avg_rb_rates = {
        rb_id: round(sum(rates) / len(rates), 1)
        for rb_id, rates in sorted(rb_rates.items())
    }

    print(f'avg. lost rate from register: {avg_lost_rate_register}')
    print(f'avg. rate from register:      {avg_rate_register}')
    print(f'avg. rate from hb:            {avg_rate_hb}')
    print(avg_rb_rates)

