import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
peak_height_all = np.loadtxt('peak_height_all.txt', delimiter=',')
peak_height_a   = np.loadtxt('peak_height_a.txt', delimiter=',')
peak_height_b   = np.loadtxt('peak_height_b.txt', delimiter=',')
fwhm_all        = np.loadtxt('fwhm_all.txt', delimiter=',')
fwhm_a          = np.loadtxt('fwhm_a.txt', delimiter=',')
fwhm_b          = np.loadtxt('fwhm_b.txt', delimiter=',')

if __name__ == '__main__':


    plt.figure()
    h0 = plt.hist2d(peak_height_all, fwhm_all, bins=(200,100), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h0[3])
    plt.xlabel('Peak Height [mV]')
    plt.ylabel('FWHM [nsec]')
    plt.xlim(0,900)
    plt.minorticks_on()
    plt.savefig('peak_vs_fwhm_heatmap_all.pdf')

    print('Plot 1/3 done')

    plt.figure()
    h1 = plt.hist2d(peak_height_a, fwhm_a, bins = (200,100), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h1[3])
    plt.xlabel('Peak Height [mV]')
    plt.ylabel('FWHM [nsec]')
    plt.xlim(0,900)
    plt.minorticks_on()
    plt.savefig('peak_vs_fwhm_heatmap_a_side.pdf')

    print('Plot 2/3 done')

    plt.figure()
    h2 = plt.hist2d(peak_height_b, fwhm_b, bins = (100,100), cmap='gnuplot2', norm=colors.LogNorm())
    plt.colorbar(h2[3])
    plt.xlabel('Peak Height [mV]')
    plt.ylabel('FWHM [nsec]')
    plt.xlim(0, 900)
    plt.minorticks_on()
    plt.savefig('peak_vs_fwhm_heatmap_b_side.pdf')

    print('Plot 3/3 done')
    print('goodbye and goodluck')

    np.savetxt("peak_height_all.txt", peak_height_all)
    np.savetxt("peak_height_a.txt", peak_height_a)
    np.savetxt("peak_height_b.txt", peak_height_b)
