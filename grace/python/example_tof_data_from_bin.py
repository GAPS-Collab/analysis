import gondola as go
from glob import glob
from tqdm import tqdm

'''
---- Method 1 ---- 
look at all binary files in a particular directory, best if you're trying to look over full flight

'''

binary_path = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/' #path to binary data on UHCRA from starlink source.
files = (sorted(glob(binary_path + '*.bin'))) #the binary file titles contain timestamps, so 'sorted' ensures that the files are in order

n_events                 = 0 # total number events of all types
n_boring_events          = 0 # events deemed boring by "interesting event algorithm" (based on edep in TOF/Tracker and distribution of hits in the TOF)
n_interesting_events     = 0 # events deemed as interesting by "interesting event algorithm" 
n_no_gaps_trigger_events = 0 # these are single track events which satisfied the Track trigger only
n_no_tof_data_events     = 0 # events which generated a TOF trigger but for some reason are missing TOF data

event_ids = []

n_data_mangled_events  = 0
n_timed_out_tof_events = 0
n_complete_tof_events  = 0

for f in tqdm(files[-2:], desc = 'reading TOF binaries'): #tqdm just creates a nice progress bar, feel free to remove
    reader = go.io.TelemetryPacketReader(str(f))
    for packet in reader:
        if not packet.is_event_packet: continue #checks if packet is one of the 4 Telemetry Packet Types; there are lots of types of TelemetryPackets
        
        n_events += 1

        if packet.header.packet_type == go.packets.TelemetryPacketType.BoringEvent:
            n_boring_events += 1
        
        elif packet.header.packet_type == go.packets.TelemetryPacketType.InterestingEvent:
            n_interesting_events += 1
        
        elif packet.header.packet_type == go.packets.TelemetryPacketType.NoGapsTriggerEvent:
            n_no_gaps_trigger_events += 1
        
        elif packet.header.packet_type == go.packets.TelemetryPacketType.NoTofDataEvent:
            n_no_tof_data_events += 1

        event = go.events.TelemetryEvent.from_telemetrypacket(packet)
        
        #event id
        event_id = event.event_id
        event_ids.append(event_id)

        #tof specific information
        tof_event = event.tof

        #run id
        run_id = tof_event.run_id

        #event status: EventTimeOut (int == 24) or AnyDataMangling (int == 16) are going to be missing TOF data
        event_status = tof_event.event_status

        if event_status == go.events.EventStatus.AnyDataMangling:
            n_data_mangled_events += 1
        
        elif event_status == go.events.EventStatus.EventTimeOut:
            n_timed_out_tof_events += 1
        
        else: n_complete_tof_events += 1

        #energy deposition (in whole TOF and by subregion)
        edep = tof_event.edep

        edep_cor = tof_event.edep_cor
        edep_umb = tof_event.edep_umb
        edep_cbe = tof_event.edep_cbe

        #counting hits (in whole TOF and by subregion)
        n_hits = tof_event.nhits

        n_hits_cor = tof_event.nhits_cor
        n_hits_umb = tof_event.nhits_umb
        n_hits_cbe = tof_event.nhits_cbe

        #rbevents (these are where the information for each hit is stored, because this info is calculated on the RB. There are 8 paddles on each RB)
        rb_events_list = tof_event.rb_events
        for rb_event in rb_events_list:
            hits = rb_event.hits

            for hit in hits: #this is now one hit on one paddle! 
                '''
                Everything found in the TofHit class can be found here in the documentation: 
                
                https://gaps-collab.github.io/gaps-online-software/apidocs-v0.12/_autosummary/gondola.events.html#gondola.events.TofHit
                
                but I have included some common parameters for a start.
                '''
                paddle_id = hit.paddle_id #you can map this back to VolumeID if you want to

                #timing
                hit_time_a = hit.time_a
                hit_time_b = hit.time_b
                
                #related to waveform
                hit_peak_a = hit.peak_a
                hit_peak_b = hit.peak_b
                
                hit_charge_a = hit.charge_a
                hit_charge_b = hit.charge_b

print(f" found {n_boring_events} boring events")       
print(f" found {n_interesting_events} interesting events")
print(f" found {n_no_gaps_trigger_events} no GAPS trigger events")
print(f" found {n_no_tof_data_events} no TOF data events")

print('\n')

event_ids = sorted(event_ids)
print(f" the smallest event id found is {min(event_ids)}")
print(f" the biggest event id found is {max(event_ids)}")

print('\n')
print(f" found {n_data_mangled_events} TofEvents with data mangling")
print(f" found {n_timed_out_tof_events} TofEvents which timed out")
print(f" found {n_complete_tof_events} complete TofEvents")

'''
---- Method 2 ---- 
look at all binaries found in a particular time window
best for per run (get times from elog) or fine grained analysis

example call: 
gondola.io.grace_get_telemetry_binaries(unix_time_start, unix_time_stop, data_dir='/gaps_binaries/live/raw/ethernet')

    # Arguments
    unix_time_start : seconds since epoch for run start
    unix_time_end : seconds since epoch for run end
    # Keyword Arguments
    data_dir : folder with telemetry binaries ('.bin')

'''

files = go.io.grace_get_telemetry_binaries(1766216918, 1766271155, data_dir = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/')
