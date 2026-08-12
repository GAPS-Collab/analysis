

import gaps_online as go
import matplotlib
import matplotlib.pyplot as plt

paddle_counts = {}

#with open("hits_removed_per_panel.txt", "r") as f:
    #paddle_counts = {int(pid) : int(count) for pid, count in (line.split() for line in f)}
data = open('hits_removed_per_panel.txt')
hit_data = dict()
for k in data.readlines():
    k = k.split()
    hit_data[int(k[0])] = int(k[1])
for k in range(1,161):
    if not k in hit_data:
        hit_data[k] = 0
print (hit_data)
maxval = max(hit_data.values())
for k in hit_data:
    hit_data[k] = hit_data[k]/maxval




cm = matplotlib.colormaps['plasma']

fig1, ax1 = go.tof.visual.tof_projection_xy(paddle_occupancy=hit_data,event =None,cmap=cm,paddle_style = {'edgecolor' : 'w', 'lw' : 0.4}, show_cbar=True, indicate_empty='gray')
fig2, ax2 = go.tof.visual.unroll_cbe_sides(paddle_occupancy=hit_data, event=None,cmap=cm, paddle_style = {'edgecolor' : 'w', 'lw' : 0.4}, show_cbar=True, indicate_empty='gray')
fig3, ax3 = go.tof.visual.unroll_cor(paddle_occupancy=hit_data, event=None, cmap=cm,paddle_style = {'edgecolor' : 'w', 'lw' : 0.4}, show_cbar=True, indicate_empty='gray')

fig1.savefig("12pps_elena_cuts.pdf")
fig2.savefig("10pps_3pps_elena_cuts.pdf")
fig3.savefig("8pps_1pps_elena_cuts.pdf")

