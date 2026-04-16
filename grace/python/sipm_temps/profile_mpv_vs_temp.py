import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from tqdm import tqdm
import argparse
import os
import dashi as d
import numpy as np
import uproot
import gondola as go

def main():
    parser = argparse.ArgumentParser(description="Altitude vs Temperature (2D hist) per paddle")
    parser.add_argument("--mpvs", default="combined_mpv_vs_time.root", help="paddle mpv file")
    parser.add_argument("--temps", default="sipm_temps.h5", help="temperature file")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument('--paddles', required=False, help="list of paddles to plot")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    
    d.visual()
    
    paddle_vid_map = go.db.get_hid_vid_maps()[0]

    f = uproot.open(args.mpvs)
    df_temps = pd.read_hdf(args.temps)
    
    # convert unix to HR time
    start_unix = 1765793920
    start_time = pd.to_datetime(start_unix, unit="s")
    df_temps["time_real"] = start_time + pd.to_timedelta(
        df_temps["timestamp"], unit="s"
    )
    
    if args.paddles:
        paddles = [args.paddles]
    else:
        paddles = sorted(df_temps["paddle"].unique())

    cutoff = pd.Timestamp("2025-12-20") #after gain correction

    slopes = []
    slope_errs = []
    paddles_with_slopes = []

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

        df_paddle = df_temps[df_temps["paddle"] == paddle].copy()

        if len(df_paddle) == 0:
            continue

        df_paddle["time_bin"] = df_paddle["time_real"].dt.floor("1h")
        temp_binned = (
            df_paddle
            .groupby("time_bin")["temp"]
            .mean()
            .reset_index()
        )

        mpv_bins = time_mpv_series.floor("1h")

        temp_matched = mpv_bins.map(
            temp_binned.set_index("time_bin")["temp"]
        )
        
        mask = (
            (time_mpv_series >= cutoff) &
            (~np.isnan(temp_matched)) &
            (~np.isnan(y_mpv)) &
            (y_mpv >= 0.1)
        )   

        mpv_vals  = y_mpv[mask]
        temp_vals = temp_matched[mask]

        #mask_late = time_mpv_series >= cutoff

        #mpv_vals  = y_mpv[mask_late]
        #temp_vals = temp_matched[mask_late]

        #mask_valid = ~np.isnan(temp_vals) & (~np.isnan(mpv_vals))
        #mpv_vals  = mpv_vals[mask_valid]
        #temp_vals = temp_vals[mask_valid]
        #
        #mask_mpv = mpv_vals >= 0.1
        #mpv_vals  = mpv_vals[mask_mpv]
        #temp_vals = temp_vals[mask_mpv]


        #mpv_edges = np.linspace(mpv_vals.min(), mpv_vals.max(), 100)
        mpv_edges = np.linspace(0,2,100)

        if len(mpv_vals) == 0:
            continue

        max_temp = float(temp_vals.max())
        min_temp = float(temp_vals.min())
        mean_mpv = float(mpv_vals.mean())
        
        if min_temp == max_temp:
            print(f"Skipping {paddle}: no temp variation")
            continue
        
        temp_range = max_temp - min_temp

        n_temp_bins = int(temp_range) if temp_range >= 20 else 20
        n_temp_bins = max(n_temp_bins, 2)
        #temp_edges = np.linspace(min_temp, max_temp, n_temp_bins + 1)
        temp_edges = np.linspace(-50,50,100)

        #mpv_edges = np.linspace(mean_mpv * 0.8, mean_mpv * 1.2, 21)
        x_bins = temp_edges
        
        bin_centers = []
        means = []
        sems = []

        cmap = matplotlib.colormaps['coolwarm']

        #fitting
        x = temp_vals
        y = mpv_vals
        
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

        try:
            h2 = d.factory.hist2d(
                (temp_vals,
                mpv_vals),
                bins=(temp_edges, mpv_edges)
            )

            #print(len(temp_vals), len(mpv_vals))            

            plt.figure(figsize=(6,5))
            
            #h2.imshow(log=0, cmap=cmap)
            if np.any(h2.bincontent > 0):
                h2.imshow(log=0, cmap=cmap, zorder=0)
            else:
                print(f"{paddle}: no populated bins, skipping log scale")
                h2.imshow(log=0, cmap=cmap, zorder=0)
            
            x_bins = temp_edges
            y_centers = 0.5 * (mpv_edges[:-1] + mpv_edges[1:])
            
            
            x_fit = np.array(bin_centers)
            y_fit = np.array(means)
            y_err = np.array(sems)
                 
            mask = (~np.isnan(x_fit)) & (~np.isnan(y_fit)) & (~np.isnan(y_err)) & (y_err > 0)
                 
            if np.sum(mask) < 3:
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
    

            cb = plt.colorbar()
            plt.plot(x_line,y_line,color='#aa0066',linewidth=1,label=f"slope = {slope:.2e} ± {slope_err:.1e}",zorder=10)
            plt.errorbar(bin_centers,means,yerr=sems,fmt='o',color='xkcd:neon pink',markersize=2,label="Mean ± SEM",zorder=11)
            plt.xlabel("Temperature")
            plt.ylabel("MPV")
            plt.title(f"MPV vs Temperature ({paddle})")
            plt.grid(alpha=0.3)
            
            y_min = np.nanmin(means)
            y_max = np.nanmax(means)
            #plt.ylim(y_min - 0.1*(y_max - y_min), y_max + 0.1*(y_max - y_min))
            #plt.ylim(y_min - 0.1, y_max + 0.1)
            #plt.xlim(min_temp - 5, max_temp + 5)
            plt.xlim(-50,50)
            plt.ylim(0,2)
            plt.legend() 
            outpath = os.path.join(args.outdir, f"profile_mpv_vs_temp_2d_{paddle}.png")
            plt.savefig(outpath, dpi=150, bbox_inches="tight")
            plt.close()
        except Exception as e:
            print(f"Histogram failed for {paddle}: {e}")
            continue
    
    plt.figure(figsize=(8,5))

    plt.hist(slopes, bins=20, alpha=0.7, edgecolor="black")

    plt.xlabel("Slope (mV/°C)")
    plt.ylabel("Number of paddles")
    #plt.title("Histogram of Temperature vs Altitude Slopes")

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

    print(f"Max slope: {max_slope:.3e} ({max_slope:.3f} mV/°C) → paddle {max_paddle}")
    print(f"Min slope: {min_slope:.3e} ({min_slope:.3f} mV/°C) → paddle {min_paddle}")

    print(f"\nAverage slope: {avg_slope:.3e} ({avg_slope:.3f} mV/°C)")
    print(f"Closest to average: {closest_avg_slope:.3e} → paddle {avg_paddle}")

    print(f"\nClosest to zero slope: {zero_slope:.3e} ({zero_slope:.3f} mV/°C) → paddle {zero_paddle}")

    plt.figure(figsize=(14,6))

    paddle_indices = np.arange(len(paddles_with_slopes))

    plt.scatter(paddle_indices, slopes, s=10)

    plt.xticks(paddle_indices, paddles_with_slopes, rotation=90, fontsize=4)

    plt.xlabel("Paddle")
    plt.ylabel("Slope (mV/°C)")
    #plt.title("Slope vs Paddle")

    plt.grid(alpha=0.3)

    plt.tight_layout()

    outpath = os.path.join(args.outdir, "slope_vs_paddle_labeled.pdf")
    plt.savefig(outpath)
    plt.close()

    print(f"\nDone. Plots saved in: {args.outdir}")     

if __name__ == "__main__":
    main()
