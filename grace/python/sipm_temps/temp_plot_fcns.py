from types import NoneType
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import gondola as go


def tof_projection_xy(paddle_temps={},cmap='rainbow', paddle_style={'edgecolor': 'k', 'lw': 0.4}, show_cbar=True, overlay_panels=False, axs=None, norm=None):
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    if overlay_panels:
        fig = plt.figure(figsize=(10, 10))
        axs = [fig.gca()]
    elif axs is None:
        fig, axs = plt.subplots(1, 3, figsize=(18, 5),
                                gridspec_kw={'width_ratios': [1, 1, 1]})

    else: fig=None


    pm = go.db.TofPaddle.all_as_dict()

    umb_paddles = [pm[pid] for pid in range(61, 109) if pid in pm]
    cbe_top_paddles = [pm[pid] for pid in range(1, 13) if pid in pm]
    cbe_bot_paddles = [pm[pid] for pid in range(13, 25) if pid in pm]

    # all_vals = []
    # for pid in paddle_temps:
    #     for side in ["A", "B"]:
    #         if paddle_temps[pid][side] is not None:
    #             all_vals.append(paddle_temps[pid][side])

    # vmin = np.min(all_vals)
    # vmax = np.max(all_vals)
    # norm = Normalize(vmin=vmin, vmax=vmax)

    norm = Normalize(vmin=-50, vmax=50)

    # draw gradient
    def draw_gradient_paddle(ax, pdl):
        pid = pdl.paddle_id

        if pid not in paddle_temps:
            return

        tempA = paddle_temps[pid]["A"]
        tempB = paddle_temps[pid]["B"]

        # Paddle geometry
        patch = pdl.draw_xy(fill=False, **paddle_style)
        ax.add_patch(patch)

        if tempA is None or tempB is None:
            print(f"Missing data for paddle {pid}: A={tempA}, B={tempB}")
            grey_patch = pdl.draw_xy(fill=True,
                             facecolor='black',
                             edgecolor=paddle_style.get('edgecolor', 'k'),
                             lw=paddle_style.get('lw', 0.4))
            grey_patch.set_zorder(1)
            ax.add_patch(grey_patch)
            return

                # Endpoints
        A = np.array(pdl.sideA_pos[:2])
        B = np.array(pdl.sideB_pos[:2])

        vec = B - A
        length = np.linalg.norm(vec)
        direction = vec / length

        # perpendicular direction (width)
        perp = np.array([-direction[1], direction[0]])
        width = 16  # cm

        # corners of paddle in global coords
        p1 = A + perp * (width/2)
        p2 = A - perp * (width/2)
        p3 = B - perp * (width/2)
        p4 = B + perp * (width/2)

        # bounding box for imshow
        xmin = min(p1[0], p2[0], p3[0], p4[0])
        xmax = max(p1[0], p2[0], p3[0], p4[0])
        ymin = min(p1[1], p2[1], p3[1], p4[1])
        ymax = max(p1[1], p2[1], p3[1], p4[1])

        # create gradient along paddle axis
        n = 200
        gradient = np.linspace(tempA, tempB, n)

        # project each pixel onto paddle axis
        xx = np.linspace(xmin, xmax, n)
        yy = np.linspace(ymin, ymax, 2)
        XX, YY = np.meshgrid(xx, yy)

        # projection of each point onto AB direction
        proj = ((XX - A[0]) * direction[0] + (YY - A[1]) * direction[1]) / length
        proj = np.clip(proj, 0, 1)

        values = tempA + proj * (tempB - tempA)

        im = ax.imshow(
            values,
            extent=[xmin, xmax, ymin, ymax],
            origin='lower',
            cmap=cmap,
            norm=norm,
            aspect='auto'
        )

        # draw paddle outline on top
        patch = pdl.draw_xy(fill=False, **paddle_style)
        ax.add_patch(patch)

        # clip image to paddle
        im.set_clip_path(patch)

    def draw_panel(ax, paddles, label, xylim):
        for pdl in paddles:
            draw_gradient_paddle(ax, pdl)

        ax.set_xlim(*xylim)
        ax.set_ylim(*xylim)
        ax.set_aspect('equal')
        ax.set_xlabel('x [cm]', loc='right')
        ax.set_ylabel('y [cm]', loc='top')
        ax.set_title(label, loc='right')

    # ----------------------------
    # Draw panels
    # ----------------------------
    axid = 0
    draw_panel(axs[axid], umb_paddles, 'UMB', (-200, 200))

    axid = 0 if overlay_panels else 1
    draw_panel(axs[axid], cbe_top_paddles, 'CBE TOP', (-100, 100))

    axid = 0 if overlay_panels else 2
    draw_panel(axs[axid], cbe_bot_paddles, 'CBE BOT', (-100, 100))

    # ----------------------------
    # Colorbar
    # ----------------------------
    if show_cbar:
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=axs, location='right', pad=0.02)
        cbar.set_label('Temperature [°C]')

    return fig, axs


def unroll_cbe_sides(paddle_temps = {},
                     cmap             = 'rainbow',
                     paddle_style    = {'edgecolor' : 'k', 'lw' : 0.4},
                     show_cbar        = True,
                     indicate_empty   = 'gray',
                     axs = None, 
                     norm=None
                     ):
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    # fig, axs = plt.subplots(
    #     1, 4, sharey=True, figsize=(22, 5),
    #     gridspec_kw={'width_ratios': [1, 1, 1, 1]}
    # )

    if axs is None:
      fig, axs = plt.subplots(
        1, 4, sharey=True, figsize=(22, 5),
        gridspec_kw={'width_ratios': [1, 1, 1, 1]}
      )

    else: fig=None

    pm = go.db.TofPaddle.all_as_dict()

    cbe_front = [pm[pid] for pid in range(25, 33) if pid in pm]
    ep_1      = pm[57]

    cbe_sb = [pm[pid] for pid in range(33, 41) if pid in pm]
    ep_2   = pm[58]

    cbe_back = [pm[pid] for pid in range(41, 49) if pid in pm]
    ep_3     = pm[59]

    cbe_bb = [pm[pid] for pid in range(49, 57) if pid in pm]
    ep_4   = pm[60]

    cbe_front.append(ep_1)
    cbe_sb.append(ep_2)
    cbe_back.append(ep_3)
    cbe_bb.append(ep_4)

    # all_vals = []
    # for pid in paddle_temps:
    #     for side in ["A", "B"]:
    #         if paddle_temps[pid][side] is not None:
    #             all_vals.append(paddle_temps[pid][side])

    # if len(all_vals) == 0:
    #   vmin, vmax = 0, 1
    # else:
    #   vmin, vmax = np.min(all_vals), np.max(all_vals)
    # norm = Normalize(vmin=vmin, vmax=vmax)

    norm = Normalize(vmin=-50, vmax=50)

    def draw_gradient(ax, pdl, projection):
      pid = pdl.paddle_id

      temps = paddle_temps.get(pid, {})
      tempA = temps.get("A")
      tempB = temps.get("B")

      if projection =='yz':
        patch = pdl.draw_yz(fill=False, **paddle_style)
        ax.add_patch(patch)


        A = np.array(pdl.sideA_pos[1:3])
        B = np.array(pdl.sideB_pos[1:3])

      elif projection == 'xz':
        patch = pdl.draw_xz(fill=False, **paddle_style)
        ax.add_patch(patch)

        A = np.array([pdl.sideA_pos[0], pdl.sideA_pos[2]])
        B = np.array([pdl.sideB_pos[0], pdl.sideB_pos[2]])

      else: raise ValueError("projection must be xz or yz")

      if tempA is None or tempB is None:
        print(f"Missing data for paddle {pid}: A={tempA}, B={tempB}")
        patch = patch = (
        pdl.draw_yz(fill=True, **paddle_style)
        if projection == "yz"
        else pdl.draw_xz(fill=True, **paddle_style)
        )

        patch.set_facecolor('black')
        patch.set_edgecolor(paddle_style.get('edgecolor', 'k'))
        patch.set_linewidth(paddle_style.get('lw', 0.4))
        patch.set_zorder(2)

        ax.add_patch(patch)
        return

      vec = B - A
      length = np.linalg.norm(vec)

      if length == 0: return

      direction = vec / length

      perp = np.array([-direction[1], direction[0]])

      width = 10 if pid in {57, 58, 59, 60} else 16

      p1 = A + perp * (width / 2)
      p2 = A - perp * (width / 2)
      p3 = B - perp * (width / 2)
      p4 = B + perp * (width / 2)

      xmin = min(p1[0], p2[0], p3[0], p4[0])
      xmax = max(p1[0], p2[0], p3[0], p4[0])
      ymin = min(p1[1], p2[1], p3[1], p4[1])
      ymax = max(p1[1], p2[1], p3[1], p4[4]) if False else max(p1[1], p2[1], p3[1], p4[1])

        # --- gradient resolution ---
      n = 200
      xx = np.linspace(xmin, xmax, n)
      yy = np.linspace(ymin, ymax, n)

      XX, YY = np.meshgrid(xx, yy)

      # --- projection of each point onto paddle axis ---
      proj = ((XX - A[0]) * direction[0] +
              (YY - A[1]) * direction[1]) / length

      proj = np.clip(proj, 0, 1)

      values = tempA + proj * (tempB - tempA)

      im = ax.imshow(
          values,
          extent=[xmin, xmax, ymin, ymax],
          origin='lower',
          cmap=cmap,
          norm=norm,
          aspect='auto',
          zorder=0
      )

       # clip to paddle shape
      im.set_clip_path(patch)

      ax.add_patch(patch)
      patch.set_zorder(2)

    for pdl in cbe_front:
      draw_gradient(axs[0], pdl, "yz")

    for pdl in cbe_sb:
      draw_gradient(axs[1], pdl, "xz")
    
    for pdl in cbe_back:
      draw_gradient(axs[2], pdl, "yz")

    for pdl in cbe_bb:
      draw_gradient(axs[3], pdl, "xz")


    axs[0].set_xlim(-80, 90)
    axs[0].set_ylim(-10, 110)
    axs[0].set_aspect('equal')
    axs[0].set_xlabel('y [cm]', loc='right')
    axs[0].set_ylabel('z [cm]', loc='top')
    axs[0].set_title('SOL: CBE +X', loc='right')

    axs[1].set_xlim(-90, 80)
    axs[1].set_ylim(-10, 110)
    axs[1].set_aspect('equal')
    axs[1].invert_xaxis()
    axs[1].set_xlabel('x [cm]', loc='right')
    axs[1].set_title('ANTI-BOOM: CBE +Y', loc='right')

    axs[2].set_xlim(-90, 80)
    axs[2].set_ylim(-10, 110)
    axs[2].set_aspect('equal')
    axs[2].invert_xaxis()
    axs[2].set_xlabel('y [cm]', loc='right')
    axs[2].set_title('RAD: CBE -X', loc='right')

    axs[3].set_xlim(-80, 90)
    axs[3].set_ylim(-10, 110)
    axs[3].set_aspect('equal')
    axs[3].set_xlabel('x [cm]', loc='right')
    axs[3].set_title('BOOM: CBE -Y', loc='right')

    plt.subplots_adjust(wspace=0)
    if show_cbar:
      sm = cm.ScalarMappable(norm=norm, cmap=cmap)
      sm.set_array([])

      cbar = fig.colorbar(sm, ax=axs, location='right', pad=0.02)
      cbar.set_label("Temperature [°C]")

    return fig, axs

def unroll_cor_sides(paddle_temps = {},
                     cmap             = 'rainbow',
                     paddle_style    = {'edgecolor' : 'k', 'lw' : 0.4},
                     show_cbar        = True,
                     indicate_empty   = 'gray',
                     axs=None,
                     norm=None
                     ):
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    if axs is None:
      fig, axs = plt.subplots(
          1, 4, sharey=True, figsize=(22, 5),
          gridspec_kw={'width_ratios': [1, 1, 1, 1]}
      )

    else: fig=None

    pm = go.db.TofPaddle.all_as_dict()

    cor_front = [pm[pid] for pid in range(109, 119) if pid in pm]
    ep_1      = [pm[pid] for pid in range(149, 152) if pid in pm]

    cor_sb = [pm[pid] for pid in range(119, 129) if pid in pm]
    ep_2   = [pm[pid] for pid in range(152, 155) if pid in pm]

    cor_back = [pm[pid] for pid in range(129, 139) if pid in pm]
    ep_3     = [pm[pid] for pid in range(155, 158) if pid in pm]

    cor_bb = [pm[pid] for pid in range(139, 149) if pid in pm]
    ep_4   = [pm[pid] for pid in range(158, 161) if pid in pm]

    cor_front.extend(ep_1)
    cor_sb.extend(ep_2)
    cor_back.extend(ep_3)
    cor_bb.extend(ep_4)

    # all_vals = []
    # for pid in paddle_temps:
    #     for side in ["A", "B"]:
    #         if paddle_temps[pid][side] is not None:
    #             all_vals.append(paddle_temps[pid][side])

    # if len(all_vals) == 0:
    #   vmin, vmax = 0, 1
    # else:
    #   vmin, vmax = np.min(all_vals), np.max(all_vals)
    # norm = Normalize(vmin=vmin, vmax=vmax)

    norm = Normalize(vmin=-50, vmax=50)

    def draw_gradient(ax, pdl, projection):
      pid = pdl.paddle_id

      temps = paddle_temps.get(pid, {})
      tempA = temps.get("A")
      tempB = temps.get("B")

      if projection =='yz':
        patch = pdl.draw_yz(fill=False, **paddle_style)
        ax.add_patch(patch)


        A = np.array(pdl.sideA_pos[1:3])
        B = np.array(pdl.sideB_pos[1:3])

      elif projection == 'xz':
        patch = pdl.draw_xz(fill=False, **paddle_style)
        ax.add_patch(patch)

        A = np.array([pdl.sideA_pos[0], pdl.sideA_pos[2]])
        B = np.array([pdl.sideB_pos[0], pdl.sideB_pos[2]])

      else: raise ValueError("projection must be xz or yz")

      if tempA is None or tempB is None:
        print(f"Missing data for paddle {pid}: A={tempA}, B={tempB}")
        patch = patch = (
        pdl.draw_yz(fill=True, **paddle_style)
        if projection == "yz"
        else pdl.draw_xz(fill=True, **paddle_style)
        )

        patch.set_facecolor('black')
        patch.set_edgecolor(paddle_style.get('edgecolor', 'k'))
        patch.set_linewidth(paddle_style.get('lw', 0.4))
        patch.set_zorder(2)

        ax.add_patch(patch)
        return

      vec = B - A
      length = np.linalg.norm(vec)

      if length == 0: return

      direction = vec / length

      perp = np.array([-direction[1], direction[0]])

      width = 16

      p1 = A + perp * (width / 2)
      p2 = A - perp * (width / 2)
      p3 = B - perp * (width / 2)
      p4 = B + perp * (width / 2)

      xmin = min(p1[0], p2[0], p3[0], p4[0])
      xmax = max(p1[0], p2[0], p3[0], p4[0])
      ymin = min(p1[1], p2[1], p3[1], p4[1])
      ymax = max(p1[1], p2[1], p3[1], p4[4]) if False else max(p1[1], p2[1], p3[1], p4[1])

        # --- gradient resolution ---
      n = 200
      xx = np.linspace(xmin, xmax, n)
      yy = np.linspace(ymin, ymax, n)

      XX, YY = np.meshgrid(xx, yy)

      # --- projection of each point onto paddle axis ---
      proj = ((XX - A[0]) * direction[0] +
              (YY - A[1]) * direction[1]) / length

      proj = np.clip(proj, 0, 1)

      values = tempA + proj * (tempB - tempA)

      im = ax.imshow(
          values,
          extent=[xmin, xmax, ymin, ymax],
          origin='lower',
          cmap=cmap,
          norm=norm,
          aspect='auto',
          zorder=0
      )

       # clip to paddle shape
      im.set_clip_path(patch)

      ax.add_patch(patch)
      patch.set_zorder(2)

    for pdl in cor_front:
      draw_gradient(axs[0], pdl, "yz")

    for pdl in cor_sb:
      draw_gradient(axs[1], pdl, "xz")

    for pdl in cor_back:
      draw_gradient(axs[2], pdl, "yz")

    for pdl in cor_bb:
      draw_gradient(axs[3], pdl, "xz")


    axs[0].set_xlim(-100, 130)
    axs[0].set_ylim(-25, 160)
    axs[0].set_aspect('equal', adjustable='box')
    axs[0].set_xlabel('y [cm]', loc='right')
    axs[0].set_ylabel('z [cm]', loc='top')
    axs[0].set_title('SOL: COR +X', loc='right', y=0.98)

    axs[1].set_xlim(-130, 100)
    axs[1].set_ylim(-25, 160)
    axs[1].set_aspect('equal', adjustable='box')
    axs[1].invert_xaxis()
    axs[1].set_xlabel('x [cm]', loc='right')
    axs[1].set_title('ANTI-BOOM: COR +Y', loc='right', y=0.98)

    axs[2].set_xlim(-130, 100)
    #axs[2].set_ylim(-10, 120)
    axs[2].set_ylim(-25, 160)
    axs[2].set_aspect('equal', adjustable='box')
    axs[2].invert_xaxis()
    axs[2].set_xlabel('y [cm]', loc='right')
    axs[2].set_title('RAD: COR -X', loc='right', y=0.98)

    axs[3].set_xlim(-100, 130)
    axs[3].set_ylim(-25, 160)
    axs[3].set_aspect('equal', adjustable='box')
    axs[3].set_xlabel('x [cm]', loc='right')
    axs[3].set_title('BOOM: COR -Y', loc='right', y=0.98)


    if fig is not None:
      plt.subplots_adjust(wspace=0)
    if show_cbar:
      sm = cm.ScalarMappable(norm=norm, cmap=cmap)
      sm.set_array([])

      cbar = fig.colorbar(sm, ax=axs, location='right', pad=0.02)
      cbar.set_label("Temperature [°C]")

    return fig, axs

def plot_all_systems(paddle_temps,
                     cmap='bwr',
                     paddle_style={'edgecolor': 'k', 'lw': 0.4}):

    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.cm as cm
    from matplotlib.colors import Normalize
    import numpy as np

    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    # ----------------------------
    # Global normalization --> does not work when comparing frames from different days
    # ----------------------------
    # all_vals = []
    # for pid in paddle_temps:
    #     for side in ["A", "B"]:
    #         val = paddle_temps[pid].get(side)
    #         if val is not None:
    #             all_vals.append(val)

    # if len(all_vals) == 0:
    #     vmin, vmax = 0, 1
    # else:
    #     vmin, vmax = np.min(all_vals), np.max(all_vals)

    # norm = Normalize(vmin=vmin, vmax=vmax)

    # Safe normalization
    norm = Normalize(vmin=-50, vmax=50)

    # ----------------------------
    # Layout
    # ----------------------------
    fig = plt.figure(figsize=(18, 12))

    fig.text(0.06, 0.77, "Z-ALIGNED", fontsize=18,
             #fontweight='bold',
             va='center', rotation=90)

    fig.text(0.06, 0.49, "CUBE", fontsize=18,
             #fontweight='bold',
             va='center', rotation=90)

    fig.text(0.06, 0.21, "CORTINA", fontsize=18,
             #fontweight='bold',
             va='center', rotation=90)

    gs = gridspec.GridSpec(
        3, 5,
        width_ratios=[1, 1, 1, 1, 0.08],  # last column = colorbar
        height_ratios=[1, 1, 1],
        wspace=0.25,
        hspace=0.25
    )

    # ----------------------------
    # TOF (centered)
    # ----------------------------
    axs_tof = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
    ]

    ax_empty=fig.add_subplot(gs[0,3])
    ax_empty.axis('off')

    # empty spacer (to center visually)
    #fig.add_subplot(gs[0, 3]).axis('off')

    # ----------------------------
    # CBE row
    # ----------------------------
    axs_cbe = [fig.add_subplot(gs[1, i]) for i in range(4)]

    # ----------------------------
    # COR row
    # ----------------------------
    axs_cor = [fig.add_subplot(gs[2, i]) for i in range(4)]
    print(len(axs_cor))

    for ax in axs_tof + axs_cbe + axs_cor:
      ax.set_anchor('W')
      for spine in ax.spines.values():
        spine.set_visible(False)
      # ax.tick_params(length=0)

    # ----------------------------
    # DRAW EVERYTHING (clean!)
    # ----------------------------
    tof_projection_xy(
        paddle_temps=paddle_temps,
        cmap=cmap,
        paddle_style=paddle_style,
        show_cbar=False,
        overlay_panels=False,
        axs=axs_tof,
        norm=norm
    )

    unroll_cbe_sides(
        paddle_temps=paddle_temps,
        cmap=cmap,
        paddle_style=paddle_style,
        show_cbar=False,
        axs=axs_cbe,
        norm=norm
    )

    unroll_cor_sides(
        paddle_temps=paddle_temps,
        cmap=cmap,
        paddle_style=paddle_style,
        show_cbar=False,
        axs=axs_cor,
        norm=norm
    )

    # ----------------------------
    # Shared colorbar (centered)
    # ----------------------------
    cax = fig.add_subplot(gs[:, 4])  # spans all rows

    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label("Temperature [°C]")

    return fig
