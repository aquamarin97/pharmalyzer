
# app\views\plotting\pcr_graph\axes.py


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