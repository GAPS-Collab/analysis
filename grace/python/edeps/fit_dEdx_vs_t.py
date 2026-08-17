import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from tqdm import tqdm
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

parser = argparse.ArgumentParser(description="Altitude vs Temperature (2D hist) per paddle")
parser.add_argument("--temps", default="sipm_temps.h5", help="SiPM temp file")
parser.add_argument("--energy_dir", default="/data/gtytus/flight_energy/", help="Energy file directory")
parser.add_argument("--outdir", default='.', help="Output directory")
parser.add_argument("--paddle", default=None, help="Optional: only process one paddle (e.g. 46")
args = parser.parse_args()

os.makedirs(args.outdir, exist_ok=True)

edep_dir = args.energy_dir

if args.paddle:
        paddle = f"{int(args.paddle):03d}"
        edep_files = [f"{edep_dir}paddle_{paddle}.h5"]

else: edep_files = glob(edep_dir + '*.h5')

df_temps = pd.read_hdf(args.temps)
df_temps["paddle"] = df_temps["paddle"].str.strip()

for file in tqdm(edep_files):
    paddle_num = os.path.basename(file).split('_')[1].split('.')[0]
    print(f"Processing paddle {paddle_num}...")

    df_energy = pd.read_hdf(file)

    sipms = [f"{int(paddle_num):02d}A", f"{int(paddle_num):02d}B"]
    print(f"Matching SiPMs: {sipms}")

    df_temp = (df_temps[df_temps["paddle"].isin(sipms)].groupby("timestamp", as_index=False)["temp"].mean())
    df_temp["paddle"] = paddle_num
    print(f"Temperature data points for paddle {paddle_num}: {len(df_temp)}")

    df_energy['datetime'] = pd.to_datetime(df_energy["timestamp"], unit="s")

    start_unix_pa = 1765793920
    start_time_pa = pd.to_datetime(start_unix_pa, unit="s")

    df_temp["datetime"] = start_time_pa + pd.to_timedelta(df_temp["timestamp"], unit="s")
    df_temp["datetime"] = pd.to_datetime(df_temp["datetime"])

    df_energy["datetime"] = pd.to_datetime(df_energy["datetime"]).astype("datetime64[ns]")
    df_temp["datetime"] = pd.to_datetime(df_temp["datetime"]).astype("datetime64[ns]")

    df_energy = df_energy.sort_values("datetime")
    df_temp = df_temp.sort_values("datetime")

    cutoff = pd.Timestamp("2025-12-20")
    df_energy = df_energy[df_energy['datetime'] > cutoff]
    df_temp = df_temp[df_temp['datetime'] > cutoff]

    print(f"Energy data points: {len(df_energy)}, Temp data points: {len(df_temp)}")
    if len(df_temp) == 0 or len(df_energy) == 0: continue

    merged = pd.merge_asof(df_energy,df_temp,on="datetime", direction="nearest", tolerance=pd.Timedelta("30sec"))
    print(f"Merged data points: {len(merged)}")

    merged = merged.dropna(subset=["temp"])
    merged = merged[merged['edep']> 0.0001]

    merged = merged[["datetime","edep","temp"]].copy()
    merged["edep"] = merged["edep"].astype("float32")
    merged["temp"] = merged["temp"].astype("float32")
    merged.to_hdf(f"{args.outdir}/paddle_{paddle_num}_merged.h5", key="data", mode="w", format="table", complevel=5, complib="blosc")


    print(f"Data points after cleaning: {len(merged)}")

    temp_bins = 80
    edep_bins = 1000

    H, xedges, yedges = np.histogram2d(merged["temp"], merged["edep"], bins=[temp_bins, edep_bins])

    H_norm = H / H.max(axis=1, keepdims=True)

    H_norm[np.isnan(H_norm)] = 0

    temp_centers = 0.5 * (xedges[:-1] + xedges[1:])
    edep_centers = 0.5 * (yedges[:-1] + yedges[1:]) 

    print(len(temp_centers), len(edep_centers), H.shape)

    mpv_indices = np.argmax(H, axis=1)
    mpv_edep = edep_centers[mpv_indices]

    valid = H.max(axis=1) > 0

    #fit_mask = temp_centers[valid] < 15

    m, b = np.polyfit(temp_centers[valid], mpv_edep[valid], 1)

    xfit = np.linspace(temp_centers[valid].min(), temp_centers[valid].max(), 200)
    yfit = m * xfit + b

    np.savez(f"{args.outdir}/paddle_{paddle_num}_histograms.npz", H=H, H_norm=H_norm, xedges=xedges, yedges=yedges, temp_centers=temp_centers, edep_centers=edep_centers, mpv_edep=mpv_edep, valid=valid, slope=m, intercept=b)

    plt.figure()

    plt.pcolormesh(xedges, yedges, H_norm.T,cmap='plasma')
    #shading='auto',
    #norm=LogNorm()
    plt.colorbar(label="Normalized Counts")
    plt.scatter(temp_centers[valid], mpv_edep[valid], marker='o', color='black', s=1, label='MPV')
    plt.plot(xfit, yfit, color='navy', linewidth=2, label=f'y = {m:.4f}x + {b:.4f}')
    plt.xlabel("Temperature [C]")
    plt.ylabel(r"$\frac{dE}{dx}$ [MeV]")
    plt.title(f'paddle {paddle_num}')
    plt.ylim(0,2.5)
    plt.legend()
    plt.savefig(f"{args.outdir}/paddle_{paddle_num}_dEdx_vs_temp.pdf")
    plt.close()

    plt.figure()
    plt.plot(temp_centers[valid], mpv_edep[valid])
    plt.xlabel('degC')
    plt.ylabel('MeV')
    plt.savefig(f"{args.outdir}/paddle_{paddle_num}_MPV_vs_temp.pdf")
    plt.close()






    

