#import gaps_online as go
import gondola as go
import uproot as up
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import tqdm
from pathlib import Path
import argparse
import dashi as d
from gondola import db

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
    
    tof_paddles = db.TofPaddle.all_as_dict()

    umb_paddles = [
        tof_paddles[pid]
        for pid in range(61, 109)
        if pid in tof_paddles
    ]

    cbe_top_paddles = [
        tof_paddles[pid]
        for pid in range(1, 13)
        if pid in tof_paddles
    ]

    cbe_bot_paddles = [
        tof_paddles[pid]
        for pid in range(13, 25)
        if pid in tof_paddles
    ]   
    

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
    
def unroll_cbe_sides(paddle_occupancy = {},
                     event            = None,
                     cmap             = matplotlib.colormaps['hot'],
                     paddle_style    = {'edgecolor' : 'w', 'lw' : 0.4},
                     show_cbar        = True,
                     indicate_empty   = 'gray'
                     ):
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    fig, axs = plt.subplots(
        1, 4, sharey=True, figsize=(22, 5),
        gridspec_kw={'width_ratios': [1, 1, 1, 1]}
    )
    
    tof_paddles = db.TofPaddle.all_as_dict()

    cbe_front = [
        tof_paddles[pid]
        for pid in range(25, 33)
        if pid in tof_paddles
    ]
    ep_1 = tof_paddles[57]

    cbe_sb = [
        tof_paddles[pid]
        for pid in range(33,41)
        if pid in tof_paddles
    ]
    ep_2 = tof_paddles[58]

    cbe_back = [
        tof_paddles[pid]
        for pid in range(41,49)
        if pid in tof_paddles
    ]
    ep_3 = tof_paddles[59]

    cbe_bb = [
        tof_paddles[pid]
        for pid in range(49,57)
        if pid in tof_paddles
    ]
    ep_4 = tof_paddles[60]

    cbe_front.append(ep_1)
    cbe_sb.append(ep_2)
    cbe_back.append(ep_3)
    cbe_bb.append(ep_4)

    xmin, xmax = -110,110
    ymin, ymax = -110,110
    zmin, zmax = -25, 120
    title      = 'Absolute occupancy, xy projection'
    
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

    for pdl in cbe_front:
        if paddle_occupancy: 
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[0].add_patch(pdl.draw_yz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[0].add_patch(pdl.draw_yz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[0].add_patch(pdl.draw_yz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        cbe_front_ids = {pdl.paddle_id for pdl in cbe_front}
        for h in event.hits:
            if h.paddle_id in cbe_front_ids:
                axs[0].scatter([0.1*h.y], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[0].set_xlabel('y [cm]', loc='right')
    axs[0].set_ylabel('z [cm]', loc='top')#, rotation=90)
    axs[0].set_aspect('equal')
    axs[0].set_xlim(-80, 90)
    axs[0].set_ylim(-10, 120)
    axs[0].set_title('CBE +X', loc='right')
    for pdl in cbe_sb:
        if paddle_occupancy:
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val==0 and indicate_empty else get_color(val)
            axs[1].add_patch(pdl.draw_xz(fill=True, edgecolor=color, facecolor=color))

        else: 
            if event:
                axs[1].add_patch(pdl.draw_xz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[1].add_patch(pdl.draw_xz(fill=True, edgecolor='k', facecolor='w'))

    if event:
        cbe_sb_ids = {pdl.paddle_id for pdl in cbe_sb}
        for h in event.hits:
            if h.paddle_id in cbe_sb_ids:
                axs[1].scatter([0.1*h.x], [0.1*h.y], alpha = 0.8, marker='o', s=100*h.edep, lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[1].set_xlabel('x [cm]', loc='right')
    axs[1].set_aspect('equal')
    axs[1].set_xlim(-90, 80)
    axs[1].set_ylim(-10, 120)
    axs[1].set_title('CBE +Y', loc='right')
    axs[1].invert_xaxis()
    for pdl in cbe_back:
        if paddle_occupancy: 
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[2].add_patch(pdl.draw_yz(fill=True, edgecolor=color, facecolor=color))
        else: 
            if event:
                axs[2].add_patch(pdl.draw_yz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[2].add_patch(pdl.draw_yz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        cbe_back_ids = {pdl.paddle_id for pdl in cbe_back}
        for h in event.hits:
            if h.paddle_id in cbe_back_ids:
                axs[2].scatter([0.1*h.y], [0.1*h.z], alpha=0.8, marker='o', s=100*h.edep, lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[2].set_xlabel('y [cm]', loc='right')
    axs[2].set_xlim(-90, 80)
    axs[2].set_ylim(-10, 120)
    axs[2].set_aspect('equal')
    axs[2].invert_xaxis()
    axs[2].set_title('CBE -X', loc='right')
    for pdl in cbe_bb:
        if paddle_occupancy:
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[3].add_patch(pdl.draw_xz(fill=True, edgecolor=color, facecolor=color))
        else: 
            if event:
                axs[3].add_patch(pdl.draw_xz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[3].add_patch(pdl.draw_xz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        cbe_bb_ids = {pdl.paddle_id for pdl in cbe_bb}
        for h in event.hits:
            if h.paddle_id in cbe_bb_ids:
                axs[3].scatter([0.1*h.x], [0.1*h.z], alpha=0.8, marker='o', s=100*h.edep, lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[3].set_xlabel('x [cm]', loc='right')
    axs[3].set_aspect('equal')
    axs[3].set_xlim(-80, 90)
    axs[3].set_ylim(-10, 120)
    axs[3].set_title('CBE +Y', loc='right')
    axs[0].spines['top'].set_visible(True)
    axs[1].spines['top'].set_visible(True)
    axs[2].spines['top'].set_visible(True)
    axs[3].spines['top'].set_visible(True)
    axs[0].spines['right'].set_visible(True)
    axs[1].spines['right'].set_visible(True)
    axs[2].spines['right'].set_visible(True)
    axs[3].spines['right'].set_visible(True)

    plt.subplots_adjust(wspace=0)

    if show_cbar:
        sm = cm.ScalarMappable(cmap=cmap)
        sm.set_array(np.linspace(vmin, vmax, 100))
        cbar = fig.colorbar(sm, ax=axs, location='right', pad=0.02)
        cbar.set_label('Occupancy' if paddle_occupancy else 'Time[arb.]')
    
    return fig, axs

def unroll_cor(paddle_occupancy = {},
               event            = None,
               cmap             = matplotlib.colormaps['gnuplot2'],
               paddle_style     = {'edgecolor' : 'w', 'lw' : 0.4},
               show_cbar        = True,
               indicate_empty   = 'gray'):
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    fig, axs  = plt.subplots(1, 4, sharey=True, figsize=(22, 5), gridspec_kw={'width_ratios': [1, 1, 1, 1]})

    tof_paddles = db.TofPaddle.all_as_dict()

    cor_front = [
        tof_paddles[pid]
        for pid in range(109, 119)
        if pid in tof_paddles
    ]
    ep_1 = [
        tof_paddles[pid]
        for pid in range(149, 152)
        if pid in tof_paddles
    ]

    cor_sb = [
        tof_paddles[pid]
        for pid in range(119, 129)
        if pid in tof_paddles
    ]

    ep_2 = [
        tof_paddles[pid]
        for pid in range(152,155)
        if pid in tof_paddles
    ]

    cor_back = [
        tof_paddles[pid]
        for pid in range(129, 139)
        if pid in tof_paddles
    ] 

    ep_3 = [
        tof_paddles[pid]
        for pid in range(155, 158)
        if pid in tof_paddles
    ]

    cor_bb = [
        tof_paddles[pid]
        for pid in range(139, 149)
        if pid in tof_paddles
    ]

    ep_4 = [
        tof_paddles[pid]
        for pid in range(158, 161)
        if pid in tof_paddles
    ]

    xmin, xmax = -100,130
    ymin, ymax = -25,175 # these are the z-coordinates
    title      = 'Absolute occupancy, xy projection'
    
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

    for ep in ep_1:
        if paddle_occupancy:
            val = paddle_occupancy.get(ep.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[0].add_patch(ep.draw_yz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[0].add_patch(ep.draw_yz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[0].add_patch(ep.draw_yz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        ep_1_ids = {ep.paddle_id for ep in ep_1}
        for h in event.hits:
            if h.paddle_id in ep_1_ids:
                axs[0].scatter([0.1*h.y], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    for pdl in cor_front:
        if paddle_occupancy:
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[0].add_patch(pdl.draw_yz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[0].add_patch(pdl.draw_yz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[0].add_patch(pdl.draw_yz(fill=True, edgecolor='k', facecolor='w'))

    if event:
        cbe_front_ids = {pdl.paddle_id for pdl in cbe_front}
        for h in event.hits:
            if h.paddle_id in cbe_front_ids:
                axs[0].scatter([0.1*h.y], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[0].set_xlabel('y [cm]', loc='right')
    axs[0].set_ylabel('z [cm]', loc='top')#, rotation=90)
    axs[0].set_xlim(xmin, xmax)
    axs[0].set_ylim(ymin, ymax)
    axs[0].set_title('COR +X', loc='right')

    for ep in ep_2:
        if paddle_occupancy:
            val = paddle_occupancy.get(ep.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[1].add_patch(ep.draw_xz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[1].add_patch(ep.draw_xz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[1].add_patch(ep.draw_xz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        ep_2_ids = {ep.paddle_id for ep in ep_2}
        for h in event.hits:
            if h.paddle_id in ep_2_ids:
                axs[1].scatter([0.1*h.x], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))    
    
    for pdl in cor_sb:
        if paddle_occupancy:
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[1].add_patch(pdl.draw_xz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[1].add_patch(pdl.draw_xz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[1].add_patch(pdl.draw_xz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        cbe_sb_ids = {pdl.paddle_id for pdl in cbe_sb}
        for h in event.hits:
            if h.paddle_id in cbe_sb_ids:
                axs[1].scatter([0.1*h.x], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[1].set_xlabel('x [cm]', loc='right')
    axs[1].set_xlim(-1*xmax, -1*xmin)
    axs[1].set_ylim(ymin, ymax)
    axs[1].set_title('COR +Y', loc='right')
    axs[1].invert_xaxis()
    
    for ep in ep_3:
        if paddle_occupancy:
            val = paddle_occupancy.get(ep.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[2].add_patch(ep.draw_yz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[2].add_patch(ep.draw_yz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[2].add_patch(ep.draw_yz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        ep_3_ids = {ep.paddle_id for ep in ep_3}
        for h in event.hits:
            if h.paddle_id in ep_3_ids:
                axs[2].scatter([0.1*h.y], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    
    for pdl in cor_back:
        if paddle_occupancy:
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[2].add_patch(pdl.draw_yz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[2].add_patch(pdl.draw_yz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[2].add_patch(pdl.draw_yz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        cbe_back_ids = {pdl.paddle_id for pdl in cbe_back}
        for h in event.hits:
            if h.paddle_id in cbe_back_ids:
                axs[2].scatter([0.1*h.y], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[2].set_xlabel('y [cm]', loc='right')
    axs[2].set_xlim(-1*xmax, -1*xmin)
    axs[2].set_ylim(ymin, ymax)
    axs[2].invert_xaxis()
    axs[2].set_title('COR -X', loc='right')

    for ep in ep_4:
        if paddle_occupancy:
            val = paddle_occupancy.get(ep.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[3].add_patch(ep.draw_xz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[3].add_patch(ep.draw_xz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[3].add_patch(ep.draw_xz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        ep_4_ids = {ep.paddle_id for ep in ep_4}
        for h in event.hits:
            if h.paddle_id in ep_4_ids:
                axs[3].scatter([0.1*h.x], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    for pdl in cor_bb:
        if paddle_occupancy:
            val = paddle_occupancy.get(pdl.paddle_id, 0)
            color = indicate_empty if val == 0 and indicate_empty else get_color(val)
            axs[3].add_patch(pdl.draw_xz(fill=True, edgecolor=color, facecolor=color))
        else:
            if event:
                axs[3].add_patch(pdl.draw_xz(fill=False, facecolor='tab:blue', **paddle_style))
            else:
                axs[3].add_patch(pdl.draw_xz(fill=True, edgecolor='k', facecolor='w'))
    if event:
        cbe_bb_ids = {pdl.paddle_id for pdl in cbe_bb}
        for h in event.hits:
            if h.paddle_id in cbe_bb_ids:
                axs[3].scatter([0.1*h.x], [0.1*h.z], alpha = 0.8 , marker='o', s=100*h.edep,lw=1.5, edgecolor='k', color=get_color(h.t0))
    axs[3].set_xlabel('x [cm]', loc='right')
    axs[3].set_xlim(xmin, xmax)
    axs[3].set_ylim(ymin, ymax)
    axs[3].set_title('COR +Y', loc='right')

    axs[0].spines['top'].set_visible(True)
    axs[1].spines['top'].set_visible(True)
    axs[2].spines['top'].set_visible(True)
    axs[3].spines['top'].set_visible(True)
    axs[0].spines['right'].set_visible(True)
    axs[1].spines['right'].set_visible(True)
    axs[2].spines['right'].set_visible(True)
    axs[3].spines['right'].set_visible(True)

    plt.subplots_adjust(wspace=0)
    
    if show_cbar:
        sm = cm.ScalarMappable(cmap=cmap)
        sm.set_array(np.linspace(vmin, vmax, 100))
        cbar = fig.colorbar(sm, ax=axs, location='right', pad=0.02)
        cbar.set_label('Occupancy' if paddle_occupancy else 'Time[arb.]')

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
        #event_pids = []
        vids = f.get('TreeRec').get('Rec').get('hitseries_').get('hitseries_.volume_id_').array()
        for ev in vids:
            for vid in ev:
            #pids = [vid_hid_map[k] for k in ev if k < 200000000]
                if vid >= 200000000: continue
                pid = vid_hid_map.get(vid)
                if pid is None: 
                    print(str(pid))
                    continue
                #event_pids.extend(pids)
                #for pid in pids:
                    #occu[pid] += 1
                occu[pid] += 1
        
        #pid_hist.fill(np.array(event_pids))
        
        max_occu = max(occu.values())
        scale = max(occu.values())
        occu_scaled = {pid: n * scale for pid, n in occu.items()}

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
    #for pid in sorted(occu):
        #print(f"{pid:3d}: {occu[pid]}")
    
    fig = plt.figure()
    ax  = fig.gca()
    '''
    pid_hist.line(filled=True, alpha=0.4, color='tab:blue')
    #cb.visual.adjust_minor_ticks(ax)
    ax.set_ylim(bottom=0)
    fig.savefig(f'{args.data_id}_pid_hist_reco.png')
    '''
    #cm = matplotlib.colormaps['gnuplot2']
    mapping = matplotlib.colormaps['gnuplot2']
    fig, ax = tof_projection_xy(occu, cmap='gnuplot2')
    fig.savefig(f'{args.data_id}_12pps.pdf')
    fig, ax = unroll_cbe_sides(occu, cmap='gnuplot2')
    fig.savefig(f'{args.data_id}_8pps_1pps.pdf')
    fig, ax = unroll_cor(occu, cmap='gnuplot2')
    fig.savefig(f'{args.data_id}_10pps_3pps.pdf')
    
