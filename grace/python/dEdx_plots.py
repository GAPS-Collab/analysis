import uproot
import pandas as pd
import numpy as np
import gondola as go
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

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

for j in range (0, 160):
    print('starting loop')
    dt_paddle = avg_temp[avg_temp['paddle_num'] == j + 1]
    
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
    
    merged = merged[merged["volume_id"] == tof[j+1]]
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
    plt.title(f"paddle {j + 1} uncalibrated")
    plt.ylim(0, 20)
    plt.legend()
    #plt.show()
    plt.savefig(f"edeps/final/uncalibrated_p{j + 1}.png", dpi=150)
    print(f"saved uncalibrated_p{j + 1}.png")
    
    ## onto the calibration for T
    T_ref = np.average(dt_paddle["temp"])
    MPV_ref = m * T_ref + b
    
    merged['MPV_pred'] = merged['temp']*m + b
    merged['dedx_corr'] = merged['dedx']* (MPV_ref/ merged['MPV_pred'])
    
    merged = merged[merged['dedx_corr']> 0.0001]
    H, xedges, yedges = np.histogram2d(
    merged["temp"],
    merged["dedx_corr"],
    bins=[temp_bins, edep_bins]
    )

    edep_centers = 0.5 * (yedges[:-1] + yedges[1:])
    temp_centers = 0.5 * (xedges[:-1] + xedges[1:])

    H_norm = H / H.max(axis=1, keepdims=True)
    
    H_norm[np.isnan(H_norm)] = 0

    H_smooth = gaussian_filter1d(H, sigma=2, axis=1)
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

    plt.pcolormesh(
        xedges,
        yedges,
        H_norm.T,
        cmap='plasma'
        #shading='auto',
        #norm=LogNorm()
    )
    plt.colorbar(label="Normalized Counts")

    plt.scatter(
        temp_centers[valid],
        mpv_edep[valid],
        marker='o',
        color='black',
        s=1
    )

    plt.plot(
        xfit,
        yfit,
        color='navy',
        linewidth=1,
        label=f'y = {m:.4f}x + {b:.4f}'
    )

    plt.xlabel("Temperature [C]")
    plt.ylabel(r"$\frac{dE}{dx}$ [MeV/mm]")
    plt.title(f'paddle {j + 1} calibrated')
    plt.ylim(0,20)
    plt.legend()
    plt.savefig(f"edeps/final/calibrated_p{j + 1}.png", dpi=150)
    print(f"saved calibrated_p{j + 1}.png")
    
    
    ## final plot
    # ============================================================
    # 1. Histogram
    # ============================================================

    nbins = 1000

    counts, edges = np.histogram(
        merged["dedx_corr"],
        bins=nbins,
        range=(0, 35)
    )

    centers = 0.5 * (edges[:-1] + edges[1:])


    # ============================================================
    # 2. Smooth histogram ONLY to find the approximate peak
    # ============================================================

    smooth_counts = gaussian_filter1d(
        counts.astype(float),
        sigma=3
    )


    # ============================================================
    # 3. Find approximate MIP peak
    # ============================================================

    peak_search_mask = (
        (centers > 0.5) &
        (centers < 3.0)
    )

    search_x = centers[peak_search_mask]
    search_y = smooth_counts[peak_search_mask]

    peak_index = np.argmax(search_y)

    peak_bin_index = np.where(
        peak_search_mask
    )[0][peak_index]

    peak_guess = centers[peak_bin_index]


    print(
        f"Initial MIP peak: "
        f"{peak_guess:.5f} MeV/cm"
    )


    # ============================================================
    # 4. Local cubic function
    # ============================================================

    def cubic(x, a, b, c, d):

        return (
            a * x**3 +
            b * x**2 +
            c * x +
            d
        )


    # ============================================================
    # 5. Try different numbers of bins around the peak
    # ============================================================

    window_sizes = [
        5,
        7,
        9,
        11,
        13,
        15
    ]


    results = []


    for window in window_sizes:

        half_window = window // 2

        start = peak_bin_index - half_window
        stop = peak_bin_index + half_window + 1

        if start < 0 or stop > len(counts):
            continue

        x_local = centers[start:stop]
        y_local = counts[start:stop]

        # Need positive counts
        valid = y_local > 0

        x_local = x_local[valid]
        y_local = y_local[valid]

        if len(x_local) < 5:
            continue


        # --------------------------------------------------------
        # Fit cubic to COUNTS, not log(counts)
        # --------------------------------------------------------

        # Poisson uncertainty
        sigma_y = np.sqrt(
            np.maximum(y_local, 1)
        )

        # Center x for numerical stability
        x_center = peak_guess

        x_fit = x_local - x_center


        def cubic_centered(x, a, b, c, d):

            return (
                a * x**3 +
                b * x**2 +
                c * x +
                d
            )


        p0 = [
            0,
            -10000,
            0,
            y_local.max()
        ]

        try:

            pars, cov = curve_fit(
                cubic_centered,
                x_fit,
                y_local,
                p0=p0,
                sigma=sigma_y,
                absolute_sigma=False,
                maxfev=10000
            )

        except (
            RuntimeError,
            ValueError
        ):
            continue


        a, b, c, d = pars


        # --------------------------------------------------------
        # Find extrema of cubic
        #
        # derivative:
        #
        #   3ax² + 2bx + c = 0
        # --------------------------------------------------------

        roots = np.roots([
            3 * a,
            2 * b,
            c
        ])


        # Only real extrema
        real_roots = [
            r.real
            for r in roots
            if abs(r.imag) < 1e-10
        ]


        # Only extrema inside the fitting window
        x_min = x_fit.min()
        x_max = x_fit.max()

        valid_roots = [
            r for r in real_roots
            if x_min <= r <= x_max
        ]


        if len(valid_roots) == 0:
            continue


        # --------------------------------------------------------
        # Choose the LOCAL MAXIMUM
        # --------------------------------------------------------

        candidate_peaks = []

        for r in valid_roots:

            # Second derivative
            second_derivative = (
                6 * a * r +
                2 * b
            )

            # Negative second derivative = maximum
            if second_derivative < 0:

                candidate_peaks.append(r)


        if len(candidate_peaks) == 0:
            continue


        # If multiple maxima somehow exist, choose the one
        # closest to the observed histogram peak.

        refined_offset = min(
            candidate_peaks,
            key=lambda r: abs(r)
        )

        refined_peak = (
            x_center +
            refined_offset
        )


        # --------------------------------------------------------
        # Calculate residuals
        # --------------------------------------------------------

        fitted_y = cubic_centered(
            x_fit,
            *pars
        )

        residuals = (
            y_local -
            fitted_y
        )

        chi2 = np.sum(
            (residuals / sigma_y)**2
        )

        dof = len(y_local) - 4

        reduced_chi2 = (
            chi2 / dof
            if dof > 0
            else np.nan
        )


        results.append({
            "window": window,
            "peak": refined_peak,
            "chi2": reduced_chi2,
            "x": x_local,
            "y": y_local,
            "pars": pars
        })


    # ============================================================
    # 6. Print results
    # ============================================================

    print()
    print("======================================")
    print("LOCAL CUBIC MIP FITS")
    print("======================================")

    for result in results:

        print(
            f"{result['window']:2d} bins: "
            f"MIP = {result['peak']:.5f} MeV/cm   "
            f"reduced χ² = {result['chi2']:.3f}"
        )


    # ============================================================
    # 7. Extract peak values
    # ============================================================

    windows = np.array([
        r["window"]
        for r in results
    ])

    peaks = np.array([
        r["peak"]
        for r in results
    ])


    # ============================================================
    # 8. Look at stability
    # ============================================================

    print()
    print("======================================")
    print("PEAK STABILITY")
    print("======================================")

    print(
        f"Histogram-bin peak: "
        f"{peak_guess:.5f} MeV/cm"
    )

    print(
        f"Mean local-fit peak: "
        f"{np.mean(peaks):.5f} MeV/cm"
    )

    print(
        f"Median local-fit peak: "
        f"{np.median(peaks):.5f} MeV/cm"
    )

    print(
        f"Standard deviation: "
        f"{np.std(peaks, ddof=1):.5f} MeV/cm"
    )

    print(
        f"Range: "
        f"{np.min(peaks):.5f} - "
        f"{np.max(peaks):.5f} MeV/cm"
    )


    # ============================================================
    # 9. Choose final MIP
    # ============================================================

    # For now, use the MEDIAN of the local peak estimates.
    #
    # This is deliberately independent of 1.92.

    measured_mip = np.median(
        peaks
    )


    print()
    print("======================================")
    print("FINAL MIP")
    print("======================================")

    print(
        f"Measured MIP: "
        f"{measured_mip:.5f} MeV/cm"
    )


    # ============================================================
    # 10. Normalize to expected Z=1 MPV
    # ============================================================

    coeff = 1.92 / measured_mip

    merged["dedx_norm"] = (
        merged["dedx_corr"] * coeff
    )


    print()
    print("======================================")
    print("NORMALIZATION")
    print("======================================")

    print(
        f"Measured MIP: "
        f"{measured_mip:.5f} MeV/cm"
    )

    print(
        f"Normalization coefficient: "
        f"{coeff:.6f}"
    )

    print(
        f"Normalized MIP: "
        f"{measured_mip * coeff:.5f} MeV/cm"
    )


    # ============================================================
    # 11. Plot peak stability
    # ============================================================

    # plt.figure(figsize=(8, 5))

    # plt.plot(
    #     windows,
    #     peaks,
    #     "o-",
    #     label="local cubic MIP peak"
    # )

    # plt.axhline(
    #     peak_guess,
    #     linestyle="--",
    #     label=f"histogram peak = {peak_guess:.3f}"
    # )

    # plt.axhline(
    #     measured_mip,
    #     linestyle=":",
    #     linewidth=2,
    #     label=f"median = {measured_mip:.3f}"
    # )

    # plt.xlabel("Number of bins in local fit")
    # plt.ylabel("MIP peak [MeV/cm]")

    # plt.title(
    #     "MIP peak stability vs local fit size"
    # )

    # plt.xticks(window_sizes)

    # plt.legend()
    # plt.tight_layout()
    # plt.show()


    # ============================================================
    # 12. Plot the fits themselves
    # ============================================================

    # plt.figure(figsize=(9, 5))

    # plt.step(
    #     centers,
    #     smooth_counts,
    #     where="mid",
    #     label="smoothed histogram"
    # )

    # for result in results:

    #     x_local = result["x"]
    #     pars = result["pars"]

    #     x_plot = np.linspace(
    #         x_local.min(),
    #         x_local.max(),
    #         200
    #     )

    #     y_plot = cubic_centered(
    #         x_plot - peak_guess,
    #         *pars
    #     )

    #     plt.plot(
    #         x_plot,
    #         y_plot,
    #         "--",
    #         alpha=0.5,
    #         label=f"{result['window']} bins"
    #     )


    # plt.axvline(
    #     peak_guess,
    #     linestyle="--",
    #     label=f"histogram peak = {peak_guess:.3f}"
    # )

    # plt.axvline(
    #     measured_mip,
    #     linestyle=":",
    #     linewidth=2,
    #     label=f"chosen MIP = {measured_mip:.3f}"
    # )

    # plt.xlabel("dE/dx [MeV/cm]")
    # plt.ylabel("Counts")

    # plt.title(
    #     "Local MIP fits"
    # )

    # plt.xlim(
    #     max(0, peak_guess - 1.0),
    #     peak_guess + 1.5
    # )

    # plt.legend()
    # plt.tight_layout()
    # plt.show()


    # ============================================================
    # 13. Final normalized histogram
    # ============================================================

    plt.figure(figsize=(9, 5))

    plt.hist(
        merged["dedx"],
        bins=nbins,
        range=(0, 35),
        histtype="step",
        color="mediumblue",
        label="uncorrected"
    )

    plt.hist(
        merged["dedx_corr"],
        bins=nbins,
        range=(0, 35),
        histtype="step",
        color="tomato",
        label="corrected temperature"
    )

    plt.hist(
        merged["dedx_norm"],
        bins=nbins,
        range=(0, 35),
        histtype="step",
        color="black",
        label="corrected temperature + normalized"
    )

    plt.axvline(
        1.92,
        linestyle="--",
        label="Z=1 MPV = 1.92 MeV/cm"
    )

    plt.axvline(
        7.68,
        linestyle="--",
        label="Z=2 MPV = 7.68 MeV/cm"
    )

    plt.xlabel("dE/dx [MeV/cm]")
    plt.ylabel("Counts")

    plt.title(f'paddle {j + 1} dE/dx distribution')

    plt.xlim(0, 20)
    plt.yscale("log")

    plt.legend()
    plt.tight_layout()
    plt.savefig(f"edeps/final/final_dEdx_dist_p{j + 1}.png", dpi=150)