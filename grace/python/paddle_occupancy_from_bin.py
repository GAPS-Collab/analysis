import gondola as go
import dashi as d
import tqdm
import numpy as np


files = go.io.grace_get_telemetry_binaries(1766216918, 1766271155, data_dir = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/')

d.visual()

pid_hist = d.factory.hist1d(np.array([]), bins=np.arange(0.5, 160.5, 1)) #initializing a histogram which will have paddle id on the x axis and hits per paddle on y

analysis = go.tof.analysis.TofAnalysis()
analysis.active = True

for f in tqdm.tqdm(files[-2:], desc='reading TOF binaries'):
    for packet in go.io.TelemetryPacketReader(str(f)):
        if not packet.is_event_packet:
            continue
        tof_event = go.events.TelemetryEvent.from_telemetrypacket(packet).tof
        analysis.add_event(tof_event)

occu = analysis.occupancy #creates a dictionary where the key is the paddle id and the value is the n_hits in that paddle from the binaries from the binaries input

fig1, ax1 = go.visual.tof.tof_projection_xy(paddle_occupancy=occu, umbrella_only=False, paddle_style={'edgecolor': 'k', 'lw': 0.4})
fig1.savefig('12pps_occupancy.pdf')

fig2, ax2 = go.visual.tof.unroll_cbe_sides(paddle_occupancy=occu, paddle_style={'edgecolor': 'k', 'lw': 0.4})
fig2.savefig('cbe_occupancy.pdf')

fig3, ax3 = go.visual.tof.unroll_cor(paddle_occupancy=occu, paddle_style={'edgecolor': 'k', 'lw': 0.4})
fig3.savefig('cor_occupancy.pdf')
