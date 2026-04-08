import uproot
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import dashi as d
import argparse
import os
import gondola

def main():

    # -----------------------------
    # Args
    # -----------------------------
    parser = argparse.ArgumentParser(description="MPV vs Temperature 2D histograms per paddle")
    parser.add_argument("--temps", default="sipm_temps.h5", help="Temperature file")
    parser.add_argument("--mpv", default="combined_mpv_vs_time.root", help="MPV ROOT file")
    parser.add_argument("--outdir", default="mpv_temp_plots", help="Output directory")
    parser.add_argument("--paddle", default=None, help="Optional: only process one paddle (e.g. 46A)")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    
    paddle_vid_map = gondola.db.get_hid_vid_maps()[0]

    # -----------------------------
    # Load MPV file
    # -----------------------------
    f = uproot.open(args.mpv)

    # -----------------------------
    # Load temperature data
    # -----------------------------
    df_temps = pd.read_hdf(args.temps)

    start_unix = 1765793920
    start_time = pd.to_datetime(start_unix, unit="s")

    df_temps["time_real"] = start_time + pd.to_timedelta(
        df_temps["timestamp"], unit="s"
    )

    # -----------------------------
    # Paddle list
    # -----------------------------
    if args.paddle:
        paddles = [args.paddle]
    else:
        paddles = sorted(df_temps["paddle"].unique())

    cutoff = pd.Timestamp("2025-12-20")

    # -----------------------------
    # Loop
    # -----------------------------
    for paddle in paddles:

        print(f"Processing {paddle}")
        
        vid = paddle_vid_map[int(paddle.rstrip('A').rstrip('B'))]
        if vid >= 2000000000: continue 

        gr_name = f"volumes/mpv_vs_time_vol_{vid}"

        if gr_name not in f:
            print(f"Skipping {paddle} (no MPV graph)")
            continue

        gr = f[gr_name]

        n = gr.member("fNpoints")
        x_mpv = gr.member("fX")[:n]
        y_mpv = gr.member("fY")[:n]

        time_mpv = pd.to_datetime(x_mpv, unit="s")
        time_mpv_series = pd.to_datetime(time_mpv)

        # -----------------------------
        # Filter temperature to paddle
        # -----------------------------
        df_paddle = df_temps[df_temps["paddle"] == paddle].copy()

        if len(df_paddle) == 0:
            continue

        # -----------------------------
        # Bin temperature
        # -----------------------------
        df_paddle["time_bin"] = df_paddle["time_real"].dt.floor("2h")
        print(df_paddle.columns)
        temp_binned = (
            df_paddle
            .groupby("time_bin")["temp"]
            .mean()
            .reset_index()
        )

        # -----------------------------
        # Match MPV → temperature
        # -----------------------------
        mpv_bins = time_mpv_series.floor("2h")

        temp_matched = mpv_bins.map(
            temp_binned.set_index("time_bin")["temp"]
        )

        # -----------------------------
        # Apply cutoff
        # -----------------------------
        mask_late = time_mpv_series >= cutoff

        mpv_vals  = y_mpv[mask_late]
        temp_vals = temp_matched[mask_late]

        # clean NaNs
        mask_valid = ~np.isnan(temp_vals)
        mpv_vals  = mpv_vals[mask_valid]
        temp_vals = temp_vals[mask_valid]

        if len(mpv_vals) == 0:
            continue

        # -----------------------------
        # 2D histogram
        # -----------------------------
        h2 = d.factory.hist2d(
            (temp_vals,
            mpv_vals),
            bins=(20,20)
            #range=[
                #(temp_vals.min(), temp_vals.max()),
                #(mpv_vals.min(), mpv_vals.max())
            #]
        )

        print(len(temp_vals), len(mpv_vals))

        # -----------------------------
        # Plot
        # -----------------------------
        plt.figure(figsize=(6,5))

        h2.imshow(log=1)

        plt.xlabel("Temperature")
        plt.ylabel("MPV")
        plt.title(f"MPV vs Temperature ({paddle})")

        plt.colorbar(label="Counts")
        plt.grid(alpha=0.3)
        plt.ylim(0,2)
        # -----------------------------
        # Save instead of show
        # -----------------------------
        outpath = os.path.join(args.outdir, f"mpv_vs_temp_{paddle}.png")
        plt.savefig(outpath, dpi=150, bbox_inches="tight")
        plt.close()

    print(f"\nDone. Plots saved in: {args.outdir}")


if __name__ == "__main__":
    main()
