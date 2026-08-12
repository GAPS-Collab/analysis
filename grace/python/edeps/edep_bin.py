import gondola as go
import matplotlib.pyplot as plt
from tqdm import tqdm
import pylandau
import numpy as np
from scipy.optimize import curve_fit
'''
this script produces a histogram of hits on a particular paddle in a particular time window, it was used to test the need for a cut on hit position to accurately record energy deposition. it was found that it didn't make much of a difference

'''
def landau_model(x, A, mpv, eta):
    return A * pylandau.landau(x, mpv, eta)

paddle_63_edeps_no_cut  = []
paddle_63_edeps_yes_cut = []

files = go.io.grace_get_telemetry_binaries(1766216918, 1766220518, data_dir = '/data1/nextcloud/cra_data/data/binaries_berkeley/starlink/')

for f in tqdm(files, desc = 'reading TOF binaries'):
    reader = go.io.TelemetryPacketReader(str(f))
    for packet in reader:
        if not packet.is_event_packet: continue

        event = go.events.TelemetryEvent.from_telemetrypacket(packet)
        
        tof_event = event.tof

        event_status = tof_event.event_status
        if event_status == go.events.EventStatus.AnyDataMangling or event_status == go.events.EventStatus.EventTimeOut: continue

        hits = tof_event.hits

        for hit in hits:
            paddle_id = hit.paddle_id

            if paddle_id != 63: continue

            edep = hit.edep

            pos = hit.pos

            if pos >= 600 and pos <= 1200:
                paddle_63_edeps_yes_cut.append(edep)
            
            paddle_63_edeps_no_cut.append(edep)

counts_no_cut, bin_edges_no_cut, _   = plt.hist(paddle_63_edeps_no_cut, bins=50, alpha=0.5, facecolor='blue', edgecolor='black', histtype='stepfilled', hatch = '/', label="No hit position cut", density=True)
counts_yes_cut, bin_edges_yes_cut, _ = plt.hist(paddle_63_edeps_yes_cut, bins=50, alpha=0.5, facecolor='red', edgecolor='black', histtype='stepfilled', hatch='\\', label="+- 30cm of paddle center", density=True)


bin_centers_no_cut  = 0.5 * (bin_edges_no_cut[:-1] + bin_edges_no_cut[1:])
bin_centers_yes_cut = 0.5 * (bin_edges_yes_cut[:-1] + bin_edges_yes_cut[1:])

# Find peak
peak_idx_no_cut     = np.argmax(counts_no_cut)
peak_val_no_cut     = counts_no_cut[peak_idx_no_cut] # normalization factor

peak_idx_yes_cut    = np.argmax(counts_yes_cut)
peak_val_yes_cut    = counts_yes_cut[peak_idx_yes_cut] # normalization factor


# Half max
half_max_no_cut     = peak_val_no_cut / 2.0
half_max_yes_cut    = peak_val_yes_cut / 2.0

# Find indices where counts > half max
fwhm_mask_no_cut    = counts_no_cut > half_max_no_cut
fwhm_mask_yes_cut   = counts_yes_cut > half_max_yes_cut

# Extract FWHM region
x_fwhm_no_cut       = bin_centers_no_cut[fwhm_mask_no_cut]
y_fwhm_no_cut       = counts_no_cut[fwhm_mask_no_cut]

x_fwhm_yes_cut      = bin_centers_yes_cut[fwhm_mask_yes_cut]
y_fwhm_yes_cut      = counts_yes_cut[fwhm_mask_yes_cut]

p0_no_cut           = [max(y_fwhm_no_cut), x_fwhm_no_cut[np.argmax(y_fwhm_no_cut)], 1.0]  # initial guesses
p0_yes_cut          = [max(y_fwhm_yes_cut), x_fwhm_yes_cut[np.argmax(y_fwhm_yes_cut)], 1.0]

popt_no_cut, _      = curve_fit(landau_model, x_fwhm_no_cut, y_fwhm_no_cut, p0=p0_no_cut, maxfev=100000)
popt_yes_cut, _     = curve_fit(landau_model, x_fwhm_yes_cut, y_fwhm_yes_cut, p0=p0_yes_cut, maxfev=100000)

A_fit_no_cut, mpv_fit_no_cut, eta_fit_no_cut    = popt_no_cut
A_fit_yes_cut, mpv_fit_yes_cut, eta_fit_yes_cut = popt_yes_cut

x_no_cut            = np.linspace(bin_edges_no_cut[0], bin_edges_no_cut[-1], 1000)
y_no_cut            = landau_model(x_no_cut, A_fit_no_cut, mpv_fit_no_cut, eta_fit_no_cut)

x_yes_cut           = np.linspace(bin_edges_yes_cut[0], bin_centers_yes_cut[-1], 1000)
y_yes_cut           = landau_model(x_yes_cut, A_fit_yes_cut, mpv_fit_yes_cut, eta_fit_yes_cut)

bin_width_no_cut    = bin_edges_no_cut[1] - bin_edges_no_cut[0]
bin_width_yes_cut   = bin_edges_yes_cut[1] - bin_edges_yes_cut[0]

plt.plot(x_no_cut, y_no_cut, 'r-', label=f'MPV = {mpv_fit_no_cut:.2f} MeV', color = 'navy')
plt.plot(x_yes_cut, y_yes_cut, 'r-', label=f'MPV = {mpv_fit_yes_cut:.2f} MeV', color='maroon')

plt.xlabel('Edep [MeV]')
plt.ylabel('N (normalized)')
plt.legend()

plt.savefig('paddle63_edeps_w_cut.pdf')




