# app\views\plotting\pcr_graph\hit_test.py
from __future__ import annotations

from typing import Optional, Set


def find_well_at_event(r, event) -> Optional[str]:
    for line, well in r._line_to_well.items():
        if not line.get_visible():
            continue
        contains, _ = line.contains(event)
        if contains:
            return well
    return None


def find_wells_in_rect(r, x0: float, x1: float, y0: float, y1: float) -> Set[str]:
    x0, x1 = sorted([x0, x1])
    y0, y1 = sorted([y0, y1])

    wells_in_rect: Set[str] = set()
    for line, well in r._line_to_well.items():
        if not line.get_visible():
            continue
        x_data = line.get_xdata(orig=False)
        y_data = line.get_ydata(orig=False)
        for x, y in zip(x_data, y_data):
            if x is None or y is None:
                continue
            if x0 <= x <= x1 and y0 <= y <= y1:
                wells_in_rect.add(well)
                break
    return wells_in_rect