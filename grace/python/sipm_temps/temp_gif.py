import pandas as pd
from collections import defaultdict
import os
import contextlib
import imageio.v2 as imageio
import glob
from tqdm import tqdm
import temp_plot_fcns as tf
import gondola as go
import matplotlib.pyplot as plt


df = pd.read_hdf("sipm_temps.h5")
pm = go.db.TofPaddle.all_as_dict()

time_series_temps = {}

start_unix = 1765793920
start_time = pd.to_datetime(start_unix, unit="s")
df["time_real"] = start_time + pd.to_timedelta(df["timestamp"], unit="s")
df["time_bin"] = df["time_real"].dt.floor("2h")

grouped = df.groupby([
    "time_bin",
    df["paddle"].str[:-1].astype(int),  # pid
    df["paddle"].str[-1]                # side
])


for (time_bin, pid, side), group in grouped:
    if time_bin not in time_series_temps:
        time_series_temps[time_bin] = {
            p: {"A": None, "B": None} for p in pm.keys()
        }
    mean_temp = group["temp"].mean()
    time_series_temps[time_bin][pid][side] = mean_temp

os.makedirs("frames", exist_ok=True)

with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
    for i, (time_bin, paddle_temps) in enumerate(tqdm(sorted(time_series_temps.items()), desc="Generating frames")):
        fig = tf.plot_all_systems(paddle_temps, cmap='coolwarm')

        fig.suptitle(str(time_bin), fontsize=16)

        fig.savefig(f"frames/frame_{i:04d}.png", dpi=150)
        plt.close(fig)

files = sorted(glob.glob("frames/frame_*.png"))

images = [imageio.imread(f) for f in files]

imageio.mimsave("tof_temperature.gif", images, duration=0.5)
