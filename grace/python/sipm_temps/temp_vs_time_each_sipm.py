import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Plot SiPM temperature vs time")
    parser.add_argument(
        "--input",
        default="sipm_temps.h5",
        help="Input HDF5 file (default: sipm_temps.h5)"
    )
    parser.add_argument(
        "--outdir",
        required=True,
        help="Directory to save output plots"
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.outdir, exist_ok=True)

    # Load data
    df = pd.read_hdf(args.input)

    # Global time reference
    start_unix = 1765793920
    start_time = pd.to_datetime(start_unix, unit="s")

    # Precompute real time
    df["time_real"] = start_time + pd.to_timedelta(df["timestamp"], unit="s")

    # Loop over paddles
    for i in tqdm(range(1, 161)):
        for end in ["A", "B"]:
            paddle = f"{i:02d}{end}"

            df_p = df[df["paddle"] == paddle]

            if df_p.empty:
                continue

            plt.figure(figsize=(10, 3))

            plt.scatter(
                df_p["time_real"],
                df_p["temp"],
                s=1,
                alpha=0.5
            )

            plt.xlabel("Time [UTC]")
            plt.ylabel("Temperature [°C]")
            plt.title(f"Temperature vs Time for Paddle {paddle}")
            plt.ylim(-50, 40)
            plt.xticks(rotation=30)

            # Save to specified directory
            outpath = os.path.join(args.outdir, f"temp_vs_time_{paddle}.png")
            plt.savefig(outpath, dpi=150, bbox_inches="tight")
            plt.close()


if __name__ == "__main__":
    main()
