import gondola as go
from glob import glob
from pathlib import Path
from tqdm import tqdm
from collections import Counter

run_path = Path("/data/tofdata/8")
files = sorted(run_path.glob("*.tof.gaps"))

mapping = go.db.get_dsi_j_ch_pid_map()
paddle_lookup = go.db.TofPaddle.all_as_dict()
print("loaded db successfully")

# Data structure:
# rb → { paddle → link_id }
rb_to_paddle_links = {}

for f in tqdm(files):
    reader = go.io.TofPacketReader(str(f))

    for packet in reader:
        if packet.packet_type == go.packets.TofPacketType.TofEvent:

            tof_event = go.events.TofEvent().from_tofpacket(packet)
            #print(tof_event.event_id)
            if int(tof_event.status) == 23: continue
            if int(tof_event.status) == 16: continue            

            triggered_paddles = [int(k) for k in tof_event.get_triggered_paddles(mapping)]

            # Full metadata array for all RBs
            mtb_link_ids = tof_event.rb_link_ids
            rb_list = [paddle_lookup[p].rb_id for p in triggered_paddles]
            if len(mtb_link_ids) != 1 and len(rb_list) != 1:
                continue
            if any(hit.peak_a < 0.5 or hit.peak_b < 0.5 for hit in tof_event.hits):
                continue

            for paddle in triggered_paddles:
                rb_id = rb_list[0]
                mtb_link_id = mtb_link_ids[0]
                
                # Initialize nested dict if needed
                if rb_id not in rb_to_paddle_links:
                    rb_to_paddle_links[rb_id] = {}
                if paddle not in rb_to_paddle_links[rb_id]:
                    rb_to_paddle_links[rb_id][paddle] = Counter()
                # Record (as long as we are consistent)
                rb_to_paddle_links[rb_id][paddle][mtb_link_id] += 1


print("\nFinal RB / paddle → link ID mapping:\n")
for rb_id in sorted(rb_to_paddle_links):
    for paddle in sorted(rb_to_paddle_links[rb_id]):
        counts = rb_to_paddle_links[rb_id][paddle]
        counts_str = ', '.join(f"{link}({count})" for link, count in counts.items())
        print(f"rb {rb_id} paddle {paddle} link id {{{counts_str}}}")
