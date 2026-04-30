import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors

#tot_600_610 = np.loadtxt('tot_all_600_610.txt', delimeter = ',')
#tot_610_620 = np.loadtxt('tot_all_610_620.txt', delimeter = ',')
#tot_620_630 = np.loadtxt('tot_all_620_630.txt', delimeter = ',')
#tot_630_640 = np.loadtxt('tot_all_630_640.txt', delimeter = ',')
#tot_640_650 = np.loadtxt('tot_all_640_650.txt', delimeter = ',')
#tot_650_660 = np.loadtxt('tot_all_650_660.txt', delimeter = ',')
#tot_660_670 = np.loadtxt('tot_all_660_670.txt', delimeter = ',')
#tot_670_680 = np.loadtxt('tot_all_670_680.txt', delimeter = ',')
#tot_680_690 = np.loadtxt('tot_all_680_690.txt', delimeter = ',')
#tot_690_700 = np.loadtxt('tot_all_690_700.txt', delimeter = ',')

#peak_600_610 = np.loadtxt('peak_all_600_610.txt', delimeter = ',')
#peak_610_620 = np.loadtxt('peak_all_610_620.txt', delimeter = ',')
#peak_620_630 = np.loadtxt('peak_all_620_630.txt', delimeter = ',')
#peak_630_640 = np.loadtxt('peak_all_630_640.txt', delimeter = ',')
#peak_640_650 = np.loadtxt('peak_all_640_650.txt', delimeter = ',')
#peak_650_660 = np.loadtxt('peak_all_650_660.txt', delimeter = ',')
#peak_660_670 = np.loadtxt('peak_all_660_670.txt', delimeter = ',')
#peak_670_680 = np.loadtxt('peak_all_670_680.txt', delimeter = ',')
#peak_680_690 = np.loadtxt('peak_all_680_690.txt', delimeter = ',')
#peak_690_700 = np.loadtxt('peak_all_690_700.txt', delimeter = ',')

ranges = [(600,610),(610,620),(620,630),(630,640),
          (640,650),(650,660),(660,670),(670,680),
          (680,690),(690,700)]

tot_data = []
peak_data = []
for lo,hi in ranges:
    tot = np.loadtxt(f'tot_all_{lo}_{hi}.txt', delimiter=',')
    peak = np.loadtxt(f'peak_all_{lo}_{hi}.txt', delimiter=',')
    tot_data.append(tot)
    peak_data.append(peak)

tot_bin_centers = []
means = []
rms_vals = []

for tot, peak in zip(tot_data, peak_data):
    # make 2D histogram
    H, xedges, yedges = np.histogram2d(tot, peak, bins=50)

    # find most populated bin
    ix, iy = np.unravel_index(np.argmax(H), H.shape)

    # bin centers
    tot_center = 0.5 * (xedges[ix] + xedges[ix+1])
    peak_center = 0.5 * (yedges[iy] + yedges[iy+1])

    # select points inside this bin
    xmask = (tot >= xedges[ix]) & (tot < xedges[ix+1])
    ymask = (peak >= yedges[iy]) & (peak < yedges[iy+1])
    mask = xmask & ymask

    # mean and RMS of peak values in that bin
    peak_in_bin = peak[mask]
    mean_peak = np.mean(peak_in_bin)
    rms_peak = np.sqrt(np.mean((peak_in_bin - mean_peak)**2))

    tot_bin_centers.append(tot_center)
    means.append(mean_peak)
    rms_vals.append(rms_peak)

# final scatter plot
plt.errorbar(tot_bin_centers, means, yerr=rms_vals, fmt='o', capsize=5)
plt.xlabel("TOT of most populated bin")
plt.ylabel("Mean Peak (± RMS)")
plt.title("Most Populated TOT Bin vs Peak")
plt.savefig('tot_vs_peak_binceners.pdf')
