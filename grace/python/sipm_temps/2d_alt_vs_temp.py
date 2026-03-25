import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import argparse
import os
import dashi as d
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Altitude vs Temperature (2D hist) per paddle")
    parser.add_argument("--temps", default="sipm_temps.h5", help="SiPM temp file")
    parser.add_argument("--alt", default="altitude_vs_time.h5", help="Altitude file")
    parser.add_argument("--outdir", required=True, help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    d.visual()  # enable dashi plotting style

    # Load data
    df = pd.read_hdf(args.temps)
    df_altitude = pd.read_hdf(args.alt)

    # Time setup
    start_unix = 1765793920
    start_time = pd.to_datetime(start_unix, unit="s")

    df["time_real"] = start_time + pd.to_timedelta(df["timestamp"], unit="s")
    df_altitude["time_real"] = start_time + pd.to_timedelta(df_altitude["timestamp"], unit="s")

    # Sort altitude once
    df_altitude = df_altitude.sort_values("time_real")

    cutoff = pd.Timestamp("2025-12-20")
    
    corr_coeffs = []
        
    # Loop over paddles
    for i in tqdm(range(1, 161)):
        for end in ["A", "B"]:
            paddle = f"{i:02d}{end}"

            df_paddle = df[df["paddle"] == paddle]

            if df_paddle.empty:
                continue

            # Merge
            df_merged = pd.merge_asof(
                df_paddle.sort_values("time_real"),
                df_altitude,
                on="time_real",
                tolerance=pd.Timedelta("5s"),
                direction="nearest"
            )

            # Drop failed matches + apply filters
            df_merged = df_merged[
                (df_merged["altitude"].notna()) &
                (df_merged["altitude"] > 5000)
            ].reset_index(drop=True)

            if df_merged.empty:
                continue

            # --- ONLY keep data AFTER cutoff ---
            df_merged = df_merged[df_merged["time_real"] >= cutoff]

            if df_merged.empty:
                continue

            # Extract numpy arrays (important for dashi)
            y = df_merged["temp"].values
            x = df_merged["altitude"].values
            
            r = np.corrcoef(x, y)[0,1]
            corr_coeffs.append(r)

            # Create 2D histogram
            h = d.factory.hist2d(
                (x, y),
                bins=(50, 50),
                labels=("Altitude [m]", "Temperature [°C]")
            )

            # Plot
            plt.figure(figsize=(8,5))

            h.imshow(log=1)
            cb = plt.colorbar()
            cb.set_label("log10(count)")

            plt.ylabel("Temperature [°C]")
            plt.xlabel("Altitude [m]")
            plt.title(f"Temperature vs Altitude (post 12/20) {paddle}")
            plt.xlim(30000, 40000)
            plt.ylim(-20,10)

            plt.tight_layout()

            # Save
            outpath = os.path.join(args.outdir, f"alt_vs_temp_2d_{paddle}.png")
            plt.savefig(outpath, dpi=150, bbox_inches="tight")
            plt.close()
    
    plt.figure(figsize=(8,5))
    plt.hist(corr_coeffs, bins=20, alpha=0.7, color="tab:blue", edgecolor="black")
    plt.xlabel("Correlation coefficient (r)")
    plt.ylabel("Number of paddles")
    plt.title("Histogram of Altitude vs Temperature Correlation Coefficients")
    plt.grid(alpha=0.3)
    hist_out = os.path.join(args.outdir, "correlation_histogram.png")
    plt.savefig(hist_out, dpi=150, bbox_inches="tight")
    plt.close()

if __name__ == "__main__":
    main()
