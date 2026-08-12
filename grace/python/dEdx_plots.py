import uproot
import awkward as ak
import pandas as pd
import numpy as np
import gondola as go
from matplotlib.colors import LogNorm
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import matplotlib.pyplot as plt


def find_good_peaks(profile):
    peaks, _ = find_peaks(profile, prominence = 0.10 * profile.max(), distance=15)
    return peaks

tof, trkr = go.db.get_hid_vid_maps()

#f = uproot.open("/Users/gracetytus/gaps/track_edep.root")
f = uproot.open("/data/gtytus/track_edep.root")

tree = f["tracks"]

df = tree.arrays(library="pd")

df = tree.arrays(
    ["edep", "step_length", "volume_id", "timestamp"],
    library="pd"
)

df["dedx"] = df["edep"] / df["step_length"]

#dt = pd.read_hdf('/Users/gracetytus/gaps/sipm_temps.h5')
dt = pd.read_hdf('/home/gtytus/analysis/grace/python/sipm_temps/sipm_temps.h5')


start_unix_pa = 1765793920
dt["timestamp_cal"] = start_unix_pa + dt["timestamp"]

df = df.sort_values("timestamp")
dt = dt.sort_values("timestamp_cal")

dt["timestamp_cal"] = dt["timestamp_cal"].astype("int64")

cutoff = 1766188800
dt = dt[dt['timestamp_cal'] > cutoff]

dt["paddle_num"] = dt["paddle"].str[:-1].astype(int)
dt["side"] = dt["paddle"].str[-1]
avg_temp = (
    dt.groupby(["paddle_num", "timestamp_cal"])["temp"]
      .mean()
      .reset_index()
)

df["timestamp"] = df["timestamp"].astype("int64")

## start loop here

for j in range (1, 3):

    dt_paddle = avg_temp[avg_temp['paddle_num'] == j]
    
    dt_paddle["timestamp_cal"] = dt_paddle["timestamp_cal"].astype("int64")
    
    df = df[df['timestamp'] > cutoff]
    
    merged = pd.merge_asof(
        df.sort_values("timestamp"),
        dt_paddle.sort_values("timestamp_cal"),
        left_on="timestamp",
        right_on="timestamp_cal",
        direction="nearest",
        tolerance=30
    )
    
    merged = merged.dropna(subset=["temp"])
    
    merged = merged[merged["volume_id"] == tof[j]]
    merged = merged.replace([np.inf, -np.inf], np.nan)
    merged = merged.dropna(subset=["temp", "dedx"])
    
    merged = merged[merged['edep']> 0.0001]
    
    temp_bins = 80
    edep_bins = 800
    
    H, xedges, yedges = np.histogram2d(
        merged["temp"],
        merged["dedx"],
        bins=[temp_bins, edep_bins]
    )
    
    edep_centers = 0.5 * (yedges[:-1] + yedges[1:])
    temp_centers = 0.5 * (xedges[:-1] + xedges[1:])
    
    H_norm = H / H.max(axis=1, keepdims=True)
    #H_norm = H / H.max()
    
    H_norm[np.isnan(H_norm)] = 0
    
    H_smooth = gaussian_filter1d(H, sigma=1, axis=1)
    #H_smooth = gaussian_filter1d(H_norm, sigma=2, axis=1)
    
    mpv_indices = np.zeros(temp_bins, dtype=int)
    
    start = np.argmax(H.sum(axis=1))
    
    profile = H_smooth[start]
    
    peaks = find_good_peaks(profile)
    
    if len(peaks) > 0:
        chosen_peak = peaks[np.argmax(profile[peaks])]
    
        lo = max(0, chosen_peak - 3)
        hi = min(len(H[start]), chosen_peak + 4)
        
        mpv_indices[start] = lo + np.argmax(H[start, lo:hi])
    else:
        mpv_indices[start] = np.argmax(profile)
    
    window = 20
    
    for i in range(start + 1, temp_bins):
    
        profile = H_smooth[i]
    
        peaks = find_good_peaks(profile)
        
        prev = mpv_indices[i - 1]
    
        if len(peaks) == 0:
            mpv_indices[i] = prev
            continue
        
        nearby = peaks[np.abs(peaks - prev) < window]
        
        if len(nearby):
            chosen_peak = nearby[np.argmax(profile[nearby])]
        else:
            chosen_peak = peaks[np.argmin(np.abs(peaks - prev))]
        
        lo = max(0, chosen_peak - 3)
        hi = min(len(H[i]), chosen_peak + 4)
        
        refined = lo + np.argmax(H[i, lo:hi])
        
        mpv_indices[i] = refined
    
    for i in range(start - 1, -1, -1):
    
        profile = H_smooth[i]
    
        peaks = find_good_peaks(profile)
        
        prev = mpv_indices[i + 1]  
    
        if len(peaks) == 0:
            mpv_indices[i] = prev
            continue
        
        nearby = peaks[np.abs(peaks - prev) < window]
        
        if len(nearby):
            chosen_peak = nearby[np.argmax(profile[nearby])]
        else:
            chosen_peak = peaks[np.argmin(np.abs(peaks - prev))]
        
        lo = max(0, chosen_peak - 3)
        hi = min(len(H[i]), chosen_peak + 4)
        
        refined = lo + np.argmax(H[i, lo:hi])
        
        mpv_indices[i] = refined
            
    
    mpv_edep = edep_centers[mpv_indices]
    
    ### same as before
    
    valid = H.max(axis=1) > 0
    
    fit_mask = (valid & (H.max(axis=1) > 20))
    
    m, b = np.polyfit(temp_centers[fit_mask], mpv_edep[fit_mask], 1)
    
    xfit = np.linspace(temp_centers[valid].min(), temp_centers[valid].max(),100)
    
    yfit = m * xfit + b
    
    plt.figure()
    
    plt.pcolormesh(xedges, yedges, H_norm.T, cmap='plasma') #shading='auto', #norm=LogNorm())
    plt.colorbar(label="Normalized Counts")
    
    plt.scatter(temp_centers[valid], mpv_edep[valid], marker='o', color='black', s=1)
    
    plt.plot(xfit, yfit, color='black', linewidth=1, label=f'y = {m:.4f}x + {b:.4f}')
    
    plt.xlabel("Temperature [C]")
    plt.ylabel(r"$\frac{dE}{dx}$ [MeV/cm]")
    plt.title('paddle 8')
    plt.ylim(0, 20)
    plt.legend()
    #plt.show()
    plt.savefig("uncalibrated_p" + str(i) + ".png", dpi=150)
