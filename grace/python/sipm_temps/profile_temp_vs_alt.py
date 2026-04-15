import pandas as pd
import matplotlib
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

    d.visual()

    # Load data
    df = pd.read_hdf(args.temps)
    df_altitude = pd.read_hdf(args.alt)

    # Time setup
    start_unix = 1765793920
    start_time = pd.to_datetime(start_unix, unit="s")

    df["time_real"] = start_time + pd.to_timedelta(df["timestamp"], unit="s")
    df_altitude["time_real"] = start_time + pd.to_timedelta(df_altitude["timestamp"], unit="s")
    df_altitude["altitude"] = df_altitude["altitude"]/1000

    # Sort altitude once
    df_altitude = df_altitude.sort_values("time_real")

    cutoff = pd.Timestamp("2025-12-20")
       
    slopes = []
    slope_errs = []
    paddles_with_slopes = []

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
            df_merged = df_merged[df_merged["altitude"].notna()].reset_index(drop=True)

            if df_merged.empty:
                continue

            # --- ONLY keep data AFTER cutoff ---
            df_merged = df_merged[df_merged["time_real"] >= cutoff]

            if df_merged.empty:
                continue

            # Extract numpy arrays (important for dashi)
            y = df_merged["temp"].values
            x = df_merged["altitude"].values
            
            x_bins = np.linspace(30, 40, 101)
            y_bins = np.linspace(-50, 50, 101)

            bin_centers = []
            means = []
            sems = []

            for b in range(len(x_bins) - 1):
                mask = (x >= x_bins[b]) & (x < x_bins[b+1])
                y_slice = y[mask]

                if len(y_slice) > 0:
                    mean = np.mean(y_slice)
                    std = np.std(y_slice)
                    sem = std / np.sqrt(len(y_slice))
                else:
                    mean = np.nan
                    sem = np.nan

                center = 0.5 * (x_bins[b] + x_bins[b+1])

                bin_centers.append(center)
                means.append(mean)
                sems.append(sem)
            
            cmap = matplotlib.colormaps['viridis']

            # Fit
            x_fit = np.array(bin_centers)
            y_fit = np.array(means)
            y_err = np.array(sems)

            mask = (~np.isnan(x_fit)) & (~np.isnan(y_fit)) & (~np.isnan(y_err)) & (y_err > 0)

            if np.sum(mask) < 2:
                print(f"{paddle}: not enough points for fit")
                continue

            x_fit = x_fit[mask]
            y_fit = y_fit[mask]
            y_err = y_err[mask]

            coeffs, cov = np.polyfit(x_fit, y_fit, 1, w=1/y_err, cov=True)

            slope, intercept = coeffs
            slope_err = np.sqrt(cov[0,0])
            slopes.append(slope)
            slope_errs.append(slope_err)
            paddles_with_slopes.append(paddle)

            x_line = np.linspace(x_fit.min(), x_fit.max(), 200)
            y_line = slope * x_line + intercept

            # Create 2D histogram
            h = d.factory.hist2d(
                (x, y),
                bins=(x_bins, y_bins),
                labels=("Altitude [km]", "Temperature [°C]")
            )
            
            # Plot 
            plt.figure(figsize=(8,5)) 
            
            if np.any(h.bincontent > 0):
                h.imshow(log=1, cmap=cmap, zorder=0)
            else:
                print(f"{paddle}: no populated bins, skipping log scale")
                h.imshow(log=0, cmap=cmap, zorder=0)

            #h.imshow(log=1, cmap=cmap) 
            cb = plt.colorbar() 
            cb.set_label("log10(count)") 
            plt.plot(x_line, y_line,color='#aa0066', linewidth=1,label=f"slope = {slope:.2e} ± {slope_err:.1e}",zorder=11)
            plt.errorbar(bin_centers, means, yerr=sems,fmt='o', color='xkcd:neon pink', markersize=1, label="Mean ± SEM")
            plt.ylabel("Temperature [°C]") 
            plt.xlabel("Altitude [km]") 
            plt.title(f"Temperature vs Altitude (post 12/20) {paddle}") 
            plt.xlim(30, 40) 
            
            y_min = np.nanmin(means)
            y_max = np.nanmax(means)
            plt.ylim(y_min - 10, y_max + 10)

            #plt.ylim(-20,10) 
            plt.legend()
            plt.tight_layout() 
            # Save 
            outpath = os.path.join(args.outdir, f"profile_alt_vs_temp_2d_{paddle}.png") 
            plt.savefig(outpath, dpi=150, bbox_inches="tight") 
            plt.close()

    plt.figure(figsize=(8,5))

    plt.hist(slopes, bins=20, alpha=0.7, edgecolor="black")
    
    plt.xlabel("Slope (°C / m)")
    plt.ylabel("Number of paddles")
    plt.title("Histogram of Temperature vs Altitude Slopes")
    
    plt.grid(alpha=0.3)
    
    outpath = os.path.join(args.outdir, "slope_histogram.png")
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()

    slopes = np.array(slopes)
    paddles_with_slopes = np.array(paddles_with_slopes)
    
    idx_max = np.argmax(slopes)
    max_slope = slopes[idx_max]
    max_paddle = paddles_with_slopes[idx_max]

    idx_min = np.argmin(slopes)
    min_slope = slopes[idx_min]
    min_paddle = paddles_with_slopes[idx_min]
    
    avg_slope = np.mean(slopes)

    idx_avg = np.argmin(np.abs(slopes - avg_slope))
    avg_paddle = paddles_with_slopes[idx_avg]
    closest_avg_slope = slopes[idx_avg]

    idx_zero = np.argmin(np.abs(slopes))
    zero_paddle = paddles_with_slopes[idx_zero]
    zero_slope = slopes[idx_zero]

    print("\n===== SLOPE SUMMARY =====")

    print(f"Max slope: {max_slope:.3e} ({max_slope*1000:.3f} °C/km) → paddle {max_paddle}")
    print(f"Min slope: {min_slope:.3e} ({min_slope*1000:.3f} °C/km) → paddle {min_paddle}")
    
    print(f"\nAverage slope: {avg_slope:.3e} ({avg_slope*1000:.3f} °C/km)")
    print(f"Closest to average: {closest_avg_slope:.3e} → paddle {avg_paddle}")
    
    print(f"\nClosest to zero slope: {zero_slope:.3e} ({zero_slope*1000:.3f} °C/km) → paddle {zero_paddle}")

    plt.figure(figsize=(14,6))

    paddle_indices = np.arange(len(paddles_with_slopes))
    
    plt.scatter(paddle_indices, slopes, s=10)
    
    plt.xticks(paddle_indices, paddles_with_slopes, rotation=90, fontsize=4)
    
    plt.xlabel("Paddle")
    plt.ylabel("Slope (°C / km)")
    plt.title("Slope vs Paddle")
    
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    
    outpath = os.path.join(args.outdir, "slope_vs_paddle_labeled.pdf")
    plt.savefig(outpath)
    plt.close()

if __name__ == "__main__":
    main()
