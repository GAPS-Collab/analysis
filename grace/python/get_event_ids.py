import gondola as go
from glob import glob
from pathlib import Path
from tqdm import tqdm
from collections import Counter

run_path = Path("/tofdata/93")
files = sorted(run_path.glob("*.tof.gaps"))

mapping = go.db.get_dsi_j_ch_pid_map()
paddle_lookup = go.db.TofPaddle.all_as_dict()
print("loaded db successfully")

event_ids_list = []

for f in tqdm(files):
    reader = go.io.TofPacketReader(str(f))

    for packet in reader:
        if packet.packet_type == go.packets.TofPacketType.TofEvent:

            tof_event = go.events.TofEvent().from_tofpacket(packet)
            event_id = tof_event.event_id
            event_ids_list.append(event_id)

event_ids_list = sorted(event_ids_list)
smallest = event_ids_list[0]
largest = event_ids_list[-1]

n_zeroes = event_ids_list.count(0)

gaps = [event_ids_list[i+1] - event_ids_list[i] for i in range(len(event_ids_list)-1)]

nonunity_gaps = [(event_ids_list[i], event_ids_list[i+1], gaps[i])
                 for i in range(len(gaps)) if gaps[i] != 1]



print("Smallest event ID:", smallest)
print("Largest event ID:", largest)
print("Number of zero IDs:", n_zeroes)

print("\nGaps != 1:")
for prev_id, next_id, gap in nonunity_gaps:
    print(f"{prev_id} → {next_id}: gap = {gap}")
