import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from collections import defaultdict


ranges = [(600,610),(610,620),(620,630),(630,640),
          (640,650),(650,660),(660,670),(670,680),
          (680,690),(690,700)]
bins_x = np.linspace(0, 20, 40)

xvals = []
xerrs = []
means = []
rms_vals = []

for lo, hi in ranges:
    tot = np.loadtxt(f'tot_all_{lo}_{hi}.txt', delimiter=',')
    peak = np.loadtxt(f'peak_all_{lo}_{hi}.txt', delimiter=',')
    
    H, edges = np.histogram(tot, bins=bins_x)
    max_bin = np.argmax(H)
    
    # bin edges
    tot_lo, tot_hi = edges[max_bin], edges[max_bin+1]

    # select all events in that TOT bin
    mask = (tot >= tot_lo) & (tot < tot_hi)
    peak_in_bin = peak[mask]

    xvals.append(0.5 * (tot_lo + tot_hi))
    xerrs.append(0.5 * (tot_hi - tot_lo))
    mean_peak = np.mean(peak_in_bin)
    rms_peak  = np.std(peak_in_bin)

    means.append(mean_peak)
    rms_vals.append(rms_peak)

# final scatter plot
plt.figure()
plt.errorbar(xvals, means, xerr=xerrs, yerr=rms_vals, fmt='o', capsize=5)
plt.xlabel("TOT of most populated bin")
plt.ylabel("Mean Peak (± RMS)")
plt.title("Most Populated TOT Bin vs Peak")
plt.savefig('test_tot_peak.pdf')

grouped = defaultdict(list)
for xv, m, r in zip(xvals, means, rms_vals):
    grouped[xv].append((m, r))

collapsed_x = []
collapsed_y = []
collapsed_yerr_low = []
collapsed_yerr_high = []
collapsed_xerr = []

for xv, vals in grouped.items():
    m_vals = np.array([v[0] for v in vals])
    r_vals = np.array([v[1] for v in vals])

    mean_y = np.mean(m_vals)

    # full possible range using RMS
    low_y  = np.min(m_vals - r_vals)
    high_y = np.max(m_vals + r_vals)

    collapsed_x.append(xv)
    collapsed_y.append(mean_y)
    collapsed_yerr_low.append(mean_y - low_y)
    collapsed_yerr_high.append(high_y - mean_y)
    collapsed_xerr.append(0.5 * (2*xerrs[0]))  # same xerr as before

plt.figure()
plt.errorbar(
    collapsed_x,
    collapsed_y,
    xerr=collapsed_xerr,
    yerr=[collapsed_yerr_low, collapsed_yerr_high],
    fmt='o', capsize=5
)

plt.xlabel("TOT of most populated bin")
plt.ylabel("Mean Peak (collapsed ± full spread)")
plt.title("TOT vs Peak (collapsed across ranges)")
plt.savefig('tot_peak_collapsed.pdf')
#print(tot_center)
#print(mean_peak)
#print(rms_peak)
