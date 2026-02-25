import gondola as go
from glob import glob
from pathlib import Path
from tqdm import tqdm

run_path = Path("/data/tofdata/3")
files = sorted(run_path.glob("*.tof.gaps"))

mapping = go.db.get_dsi_j_ch_pid_map()
paddle_lookup = go.db.TofPaddle.all_as_dict()
print("loaded db successfully")

rb_to_link = {}

for f in tqdm(files):
    reader = go.io.TofPacketReader(str(f))

    for packet in reader:
        if packet.packet_type == go.packets.TofPacketType.TofEvent:

            tof_event = go.events.TofEvent().from_tofpacket(packet)
            paddle_list = [int(k) for k in tof_event.get_triggered_paddles(mapping)]

            # Determine which RBs fired
            rb_list = [paddle_lookup[p].rb_id for p in paddle_list]
            mtb_link_ids = tof_event.rb_link_ids
            
            # Only accept events with exactly one RB
            if len(rb_list) != 1 and len(mtb_link_ids) != 1:
                continue

            rb_id = rb_list[0]
            mtb_link_id = mtb_link_ids[0]
            # Store in dictionary
            rb_to_link[rb_id] = mtb_link_id
            if rb_id == 16:
                print(f"rb 16 link id: {mtb_link_id}")
print("\nFinal sorted RB → Link mappings:")
for rb_id in sorted(rb_to_link):
    print(f"rb: {rb_id}, link: {rb_to_link[rb_id]}")

print("count:", len(rb_to_link))
