# app\views\plotting\pcr_graph\drawing.py
# app/views/plotting/pcr/drawing.py
from typing import Dict, List

from matplotlib.lines import Line2D

from app.services.graph.pcr_graph_layout_service import PCRGraphLayoutService
from app.services.pcr_data_service import PCRCoords
from app.utils import well_mapping

from .axes import setup_axes


def render_wells(r, data: Dict[str, PCRCoords]) -> None:
    r._fam_lines.clear()
    r._hex_lines.clear()
    r._line_to_well.clear()

    r.ax.clear()
    setup_axes(r)

    if not data:
        return

    wells_sorted = sorted(data.keys(), key=lambda w: well_mapping.well_id_to_patient_no(w))

    fam_all: List = []
    hex_all: List = []

    for well in wells_sorted:
        coords = data.get(well)
        if coords is None:
            continue

        fam_coords = coords.fam or []
        hex_coords = coords.hex or []

        if fam_coords:
            fam_all.extend(fam_coords)
            fam_x, fam_y = zip(*fam_coords)
        else:
            fam_x, fam_y = [], []

        if hex_coords:
            hex_all.extend(hex_coords)
            hex_x, hex_y = zip(*hex_coords)
        else:
            hex_x, hex_y = [], []

        fam_line, = r.ax.plot(
            fam_x,
            fam_y,
            label="FAM",
            color=r._style.fam_color,
            **r._style.fam_pen,
        )
        hex_line, = r.ax.plot(
            hex_x,
            hex_y,
            label="HEX",
            color=r._style.hex_color,
            **r._style.hex_pen,
        )

        fam_line.set_visible(r._fam_visible)
        hex_line.set_visible(r._hex_visible)
        fam_line.set_picker(5)
        hex_line.set_picker(5)

        r._fam_lines[well] = fam_line
        r._hex_lines[well] = hex_line
        r._line_to_well[fam_line] = well
        r._line_to_well[hex_line] = well

    apply_ylim(r, fam_all, hex_all)
    refresh_legend(r)


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


def refresh_legend(r) -> None:
    legend = r.ax.get_legend()
    if legend:
        legend.remove()

    fam_visible = any(line.get_visible() for line in r._fam_lines.values())
    hex_visible = any(line.get_visible() for line in r._hex_lines.values())
    if not fam_visible and not hex_visible:
        return

    handles: List[Line2D] = []
    labels: List[str] = []

    if fam_visible:
        handles.append(Line2D([0], [0], color=r._style.fam_color, label="FAM", **r._style.fam_pen))
        labels.append("FAM")
    if hex_visible:
        handles.append(Line2D([0], [0], color=r._style.hex_color, label="HEX", **r._style.hex_pen))
        labels.append("HEX")

    if not handles:
        return

    legend = r.ax.legend(handles, labels, fontsize=8, loc="upper left")
    s = r._style
    for text in legend.get_texts():
        text.set_color(s.legend_text_color)
    legend.get_frame().set_facecolor(s.legend_frame_facecolor)
    legend.get_frame().set_edgecolor(s.legend_frame_edgecolor)