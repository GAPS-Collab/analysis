import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Altitude vs Temperature plots per paddle")
    parser.add_argument("--temps", default="sipm_temps.h5", help="SiPM temp file")
    parser.add_argument("--alt", default="altitude_vs_time.h5", help="Altitude file")
    parser.add_argument("--outdir", required=True, help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load data
    df = pd.read_hdf(args.temps)
    df_altitude = pd.read_hdf(args.alt)

    # Time setup (same for everything)
    start_unix = 1765793920
    start_time = pd.to_datetime(start_unix, unit="s")

    df["time_real"] = start_time + pd.to_timedelta(df["timestamp"], unit="s")
    df_altitude["time_real"] = start_time + pd.to_timedelta(df_altitude["timestamp"], unit="s")

    # Sort altitude ONCE (important for merge_asof)
    df_altitude = df_altitude.sort_values("time_real")

    cutoff = pd.Timestamp("2025-12-20")

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

            # Apply your filters
            df_merged = df_merged[
                (df_merged["altitude"] > 5000)].reset_index(drop=True)

            if df_merged.empty:
                continue

            # Masks
            mask_early = df_merged["time_real"] < cutoff
            mask_late  = df_merged["time_real"] >= cutoff

            # Plot
            plt.figure(figsize=(8,5))

            plt.scatter(
                df_merged.loc[mask_early, "temp"],
                df_merged.loc[mask_early, "altitude"],
                s=1,
                alpha=0.5,
                color="tab:blue",
                label="Before Dec 20",
                marker="o"
            )

            plt.scatter(
                df_merged.loc[mask_late, "temp"],
                df_merged.loc[mask_late, "altitude"],
                s=1,
                alpha=0.5,
                color="tab:red",
                label="After Dec 20",
                marker="x"
            )

            plt.xlabel("Temperature [°C]")
            plt.ylabel("Altitude [m]")
            plt.ylim(30000, 40000)
            plt.title(f"Altitude vs Temperature of Paddle {paddle}")
            plt.legend()
            plt.grid(alpha=0.3)
            plt.tight_layout()

            # Save
            outpath = os.path.join(args.outdir, f"alt_vs_temp_{paddle}.png")
            plt.savefig(outpath, dpi=150, bbox_inches="tight")
            plt.close()


if __name__ == "__main__":
    main()
