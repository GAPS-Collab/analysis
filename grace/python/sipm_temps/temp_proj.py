import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import tqdm
import gondola as go
import pandas as pd
import dashi as d 

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
    
    if overlay_panels:
        fig = plt.figure(figsize=(10, 10))
        axs = [fig.gca()]
    else:
        fig, axs = plt.subplots(1, 3, figsize=(18, 5), gridspec_kw={'width_ratios': [1, 1, 1]})

    umb_paddles     = go.db.get_umbrella_paddles()
    cbe_top_paddles = go.db.Paddle.objects.filter(panel_id=1)
    cbe_bot_paddles = go.db.Paddle.objects.filter(panel_id=2)

    # Determine value range for color mapping
    if paddle_temps:
        all_vals = []
        for v in paddle_temps.values():
            all_vals.extend([v["A"], v["B"]])
        vmin = min(all_vals)
        vmax = max(all_vals)
    
    def get_color(val):
        return cmap((val - vmin) / (vmax - vmin))

    def draw_gradient_paddle(ax, pdl, tempA, tempB):
        patch = pdl.draw_xy(fill=False, edgecolor='none')
        ax.add_patch(patch)

        # get paddle bounding box
        verts = patch.get_path().vertices
        xmin, ymin = verts.min(axis=0)
        xmax, ymax = verts.max(axis=0)

        # create gradient (left → right)
        grad = np.linspace(tempA, tempB, 50)
        grad = np.tile(grad, (2, 1))  # make it 2D

        im = ax.imshow(grad,extent=[xmin, xmax, ymin, ymax],origin='lower',cmap=cmap,vmin=vmin,vmax=vmax,aspect='auto')

    im.set_clip_path(patch)


    def draw_panel(ax, paddles, label, xylim=(-100, 100)):
        for pdl in paddles:
            if paddle_temps:
                temps = paddle_temps.get(pdl.paddle_id, None)

                if temps is None:
                    ax.add_patch(pdl.draw_xy(fill=True, edgecolor='gray', facecolor='gray'))
                else:
                    draw_gradient_paddle(ax, pdl, temps["A"], temps["B"])
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
        cbar.set_label('Temperature [°C]')

    return fig, axs
if __name__ == '__main__':
    d.visual()

    df = pd.read_hdf("sipm_temps.h5")
    df["paddle_num"] = df["paddle"].str[:-1].astype(int)
    df["side"] = df["paddle"].str[-1]

    grouped = (df.groupby(["paddle_num", "side"])["temp"].mean().reset_index())

    paddle_temps = {}
    '''
    for _, row in grouped.iterrows():
        p = row["paddle_num"]
        side = row["side"]
        temp = row["temp"]
    
        if p not in paddle_temps:
            paddle_temps[p] = {}
    
        paddle_temps[p][side] = temp
    '''

    paddle_temps = {
    pid: {"A": np.random.uniform(-20, 0), "B": np.random.uniform(-20, 0)}
    for pid in range(1, 161)}

    fig = plt.figure()
    ax  = fig.gca()

    fig, ax = tof_projection_xy(paddle_temps, cmap='bwr')
