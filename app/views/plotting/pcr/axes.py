# app/views/plotting/pcr/axes.py
from app.services.graph.pcr_graph_layout_service import PCRGraphLayoutService

def setup_axes(r) -> None:
    s = r._style.axes
    r.fig.patch.set_facecolor(s.fig_facecolor)
    r.ax.set_facecolor(s.ax_facecolor)
    r.ax.set_axisbelow(True)
    r.fig.set_facecolor(s.fig_facecolor)
    r.ax.grid(color=s.grid_color, linestyle=s.grid_linestyle, linewidth=s.grid_linewidth)

    r.ax.tick_params(colors=s.tick_color, width=s.tick_width)
    r.ax.xaxis.label.set_color(s.label_color)
    r.ax.yaxis.label.set_color(s.label_color)
    r.ax.title.set_color(s.title_color)

    r.ax.set_xlim(*s.default_xlim)
    r.ax.set_ylim(*s.default_ylim)

    r.ax.axhline(y=0, color=s.grid_color, linestyle="-", linewidth=1)
    r.ax.axvline(x=0, color=s.grid_color, linestyle="-", linewidth=1)
    for spine in r.ax.spines.values():
        spine.set_color(s.grid_color)

def apply_ylim(r, fam_coords, hex_coords) -> None:
    ylim = PCRGraphLayoutService.compute_ylim_for_static_draw(
        fam_coords=fam_coords,
        hex_coords=hex_coords,
        min_floor=4500.0,
        y_padding=500.0,
    )
    if ylim:
        r.ax.set_ylim(*ylim)
    else:
        r.ax.set_ylim(*r._style.axes.default_ylim)

    r.ax.relim()
    r.ax.autoscale_view(scalex=True, scaley=False)
