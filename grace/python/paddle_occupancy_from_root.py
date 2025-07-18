import gaps_online as go
import uproot as up
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import tqdm
from pathlib import Path
import argparse
import dashi as d
from gaps_online import db

matplotlib.use('agg')

def tof_projection_xy(paddle_occupancy = {}, 
                      event            = None,
                      cmap             = 'gnuplot2',
                      paddle_style     = {'edgecolor' : 'w', 'lw' : 0.4},
                      show_cbar        = True,
                      overlay_panels   = False,
                      indicate_empty   = ''):
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)
    """

    # Keyword Arguments:
        paddle_occupancy : The number of events per paddle
        event            : Plot hits from TofEvent or TofEventSummary
        cmap             : Colormap - can be lambda function
                           to return color value based on 
                           'occupancy' numbker
        show_cbar        : Show the colorbar on the figure
        overlay_panels   : Only return one axes, have the TOF CBE bottom
                           and CBE TOP panels overlaid over the umbrella
                           (or under it)
        indicate_empty   : In case we are using this for paddle occupancy,
                           indicate empty paddles with the given color instead
                           using a value from the color map. If this behavior is 
                           not desired, set this to an empty string.
    """
    if overlay_panels:
        fig = plt.figure(figsize=(10, 10))
        axs = [fig.gca()]
    else:
        fig, axs = plt.subplots(1, 3, figsize=(18, 5), gridspec_kw={'width_ratios': [1, 1, 1]})

    umb_paddles     = db.get_umbrella_paddles()
    cbe_top_paddles = db.Paddle.objects.filter(panel_id=1)
    cbe_bot_paddles = db.Paddle.objects.filter(panel_id=2)

    # Determine value range for color mapping
    if paddle_occupancy:
        vmin = min(paddle_occupancy.values())
        vmax = max(paddle_occupancy.values())
    elif event:
        times = [h.t0 for h in event.hits]
        vmin = min(times)
        vmax = max(times)
    else:
        vmin = 0
        vmax = 1

    def get_color(val):
        return cmap((val - vmin) / (vmax - vmin))

    def draw_panel(ax, paddles, label, xylim=(-100, 100)):
        for pdl in paddles:
            if paddle_occupancy:
                val = paddle_occupancy.get(pdl.paddle_id, 0)
                color = indicate_empty if val == 0 and indicate_empty else get_color(val)
                ax.add_patch(pdl.draw_xy(fill=True, edgecolor=color, facecolor=color))
            else:
                ax.add_patch(pdl.draw_xy(fill=True, edgecolor='k', facecolor='w'))
        ax.set_xlim(*xylim)
        ax.set_ylim(*xylim)
        ax.set_aspect('equal')
        ax.set_xlabel('x [cm]', loc='right')
        ax.set_ylabel('y [cm]', loc='top')
        ax.set_title(label, loc='right')

    axid = 0
    draw_panel(axs[axid], umb_paddles, 'UMB', xylim=(-200, 200))
    if event:
        umb_ids = {p.paddle_id for p in umb_paddles}
        for h in event.hits:
            if h.paddle_id in umb_ids:
                axs[axid].scatter([0.1*h.x], [0.1*h.y], alpha=0.8, s=100*h.edep,
                                  lw=1.5, edgecolor=paddle_style['edgecolor'], color=get_color(h.t0))

    axid = 0 if overlay_panels else 1
    draw_panel(axs[axid], cbe_top_paddles, 'CBE TOP', xylim=(-100, 100))
    if event:
        top_ids = {p.paddle_id for p in cbe_top_paddles}
        for h in event.hits:
            if h.paddle_id in top_ids:
                axs[axid].scatter([0.1*h.x], [0.1*h.y], alpha=0.8, s=100*h.edep,
                                  lw=1.5, edgecolor=paddle_style['edgecolor'], color=get_color(h.t0))

    axid = 0 if overlay_panels else 2
    draw_panel(axs[axid], cbe_bot_paddles, 'CBE BOT', xylim=(-100, 100))
    if event:
        bot_ids = {p.paddle_id for p in cbe_bot_paddles}
        for h in event.hits:
            if h.paddle_id in bot_ids:
                axs[axid].scatter([0.1*h.x], [0.1*h.y], alpha=0.8, s=100*h.edep,
                                  lw=1.5, edgecolor=paddle_style['edgecolor'], color=get_color(h.t0))

    if show_cbar:
        sm = cm.ScalarMappable(cmap=cmap)
        sm.set_array(np.linspace(vmin, vmax, 100))
        cbar = fig.colorbar(sm, ax=axs, location='right', pad=0.02)
        cbar.set_label('Occupancy' if paddle_occupancy else 'Time [arb.]')

    return fig, axs


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Paddle occupancy graphic plot from root files (reco or MC)')
    parser.add_argument('-dir', '--data_dir', type=str, default = '', help = 'A directory with .root files from MC or Reconstruction')
    parser.add_argument('-id','--data_id', type=str, default ='_', help='the data id will go at the beginning of output files. the default is "_"')
    args = parser.parse_args()

    #cb.set_style_present()
    d.visual()

    files = Path(f'{args.data_dir}').glob('*.root')
    files = [k for k in files]
    vid_hid_map = go.db.get_vid_hid_map()

    pid_hist = d.factory.hist1d(np.array([]), bins=np.arange(0.5, 160.5, 1))
    occu = {k : 0 for k in range(1,161)}
    for f in tqdm.tqdm(files, total=len(files), desc='Creating plot...'):
        f = up.open(f)
        event_pids = []
        vids = f.get('TreeRec').get('Rec').get('hitseries_').get('hitseries_.volume_id_').array()
        for ev in vids:
            pids = [vid_hid_map[k] for k in ev if k < 200000000]
            event_pids.extend(pids)
            for pid in pids:
                occu[pid] += 1
        pid_hist.fill(np.array(event_pids))
        
        max_occu = max(occu.values())
        
        ## want to consider raw number of hits, not normalized
        #try:
            #for k in occu:
                #occu[k] = occu[k] / max_occu
                #if occu[k] == 0:
                    #occu[k] = np.nan
        #except ZeroDivisionError:
        # All values were 0, so nothing to normalize — set all to np.nan
            #for k in occu:
                #occu[k] = np.nan

    fig = plt.figure()
    ax  = fig.gca()
    pid_hist.line(filled=True, alpha=0.4, color='tab:blue')
    #cb.visual.adjust_minor_ticks(ax)
    ax.set_ylim(bottom=0)
    fig.savefig(f'{args.data_id}_pid_hist_reco.png')

    #cm = matplotlib.colormaps['gnuplot2']
    mapping = matplotlib.colormaps['gnuplot2']
    fig, ax = tof_projection_xy(occu, cmap='gnuplot2')
    fig.savefig(f'{args.data_id}_12pps.pdf')
    fig, ax = go.tof.visual.unroll_cbe_sides(paddle_occupancy=occu, cmap=mapping)
    fig.savefig(f'{args.data_id}_8pps_1pps.pdf')
    fig, ax = go.tof.visual.unroll_cor(paddle_occupancy=occu, cmap=mapping)
    fig.savefig(f'{args.data_id}_10pps_3pps.pdf')
