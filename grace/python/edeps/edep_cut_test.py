import matplotlib.pyplot as plt
import pylandau
import numpy as np
from scipy.optimize import curve_fit
import pandas as pd

def landau_model(x, A, mpv, eta):
    return A * pylandau.landau(x, mpv, eta)

df = pd.read_hdf("paddle_pos_edep.h5", key="df")

for i in range(1, 161):
    print(f"working on paddle {i}")
    plt.figure()
    
    pass_cut = []
    all_data = []

    data = df[df["paddle_id"] == i]

    edep = data["edep"]
    pos   = data["pos"]

    mask = (data["pos"] >= 600) & (data["pos"] <= 1200)
    pass_cut = data[mask]["edep"]
    all_data = data["edep"]

    if len(all_data) < 50: 
        print(f'too few data for paddle {i}')
        continue

    counts_no_cut, bin_edges_no_cut, _   = plt.hist(all_data, bins=50, alpha=0.5, facecolor='blue', edgecolor='black', histtype='stepfilled', hatch = '/', label="No hit position cut", density=True)
    counts_yes_cut, bin_edges_yes_cut, _ = plt.hist(pass_cut, bins=50, alpha=0.5, facecolor='red', edgecolor='black', histtype='stepfilled', hatch='\\', label="+- 30cm of paddle center", density=True)

    bin_centers_no_cut  = 0.5 * (bin_edges_no_cut[:-1] + bin_edges_no_cut[1:])
    bin_centers_yes_cut = 0.5 * (bin_edges_yes_cut[:-1] + bin_edges_yes_cut[1:])

    range_mask_no_cut = (bin_centers_no_cut >= 0) & (bin_centers_no_cut <= 4)
    range_mask_yes_cut = (bin_centers_yes_cut >= 0) & (bin_centers_yes_cut <= 4)

    x_restricted_no_cut = bin_centers_no_cut[range_mask_no_cut]
    y_restricted_no_cut = counts_no_cut[range_mask_no_cut]

    x_restricted_yes_cut = bin_centers_yes_cut[range_mask_yes_cut]
    y_restricted_yes_cut = counts_yes_cut[range_mask_yes_cut]

    peak_idx_no_cut = np.argmax(y_restricted_no_cut)
    peak_val_no_cut = y_restricted_no_cut[peak_idx_no_cut]

    peak_idx_yes_cut    = np.argmax(y_restricted_yes_cut)
    peak_val_yes_cut    = y_restricted_yes_cut[peak_idx_yes_cut]

    half_max_no_cut = peak_val_no_cut / 2.0
    half_max_yes_cut = peak_val_yes_cut / 2.0

    fwhm_mask_no_cut = y_restricted_no_cut > half_max_no_cut
    fwhm_mask_yes_cut = y_restricted_yes_cut > half_max_yes_cut

    x_fwhm_no_cut = x_restricted_no_cut[fwhm_mask_no_cut]
    y_fwhm_no_cut = y_restricted_no_cut[fwhm_mask_no_cut]

    x_fwhm_yes_cut = x_restricted_yes_cut[fwhm_mask_yes_cut]
    y_fwhm_yes_cut = y_restricted_yes_cut[fwhm_mask_yes_cut]

    p0_no_cut           = [max(y_fwhm_no_cut), x_fwhm_no_cut[np.argmax(y_fwhm_no_cut)], 1.0] 
    p0_yes_cut          = [max(y_fwhm_yes_cut), x_fwhm_yes_cut[np.argmax(y_fwhm_yes_cut)], 1.0]

    if len(x_fwhm_no_cut) < 3 or len(x_fwhm_yes_cut) < 3: 
        print(f'too few data in fwhm for fit on paddle {i}')
        plt.xlabel('Edep [MeV]')
        plt.ylabel('N (normalized)')
        plt.legend()

        plt.savefig(f'paddle{i}_edeps_tof_cut.pdf')
        plt.close()
        print(f'done with padle{i}')
        continue

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

    plt.plot(x_no_cut, y_no_cut, label=f'MPV = {mpv_fit_no_cut:.2f} MeV', color = 'navy')
    plt.plot(x_yes_cut, y_yes_cut, label=f'MPV = {mpv_fit_yes_cut:.2f} MeV', color='maroon')

    plt.xlabel('Edep [MeV]')
    plt.ylabel('N (normalized)')
    plt.legend()

    plt.savefig(f'paddle{i}_edeps_tof_cut.pdf')
    plt.close()
    print(f'done with padle{i}')
