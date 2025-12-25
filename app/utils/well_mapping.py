from __future__ import annotations

import string
from typing import Iterable, Optional, Set, Tuple

ROWS = tuple(string.ascii_uppercase[:8])  # A-H
COLUMNS = tuple(range(1, 13))  # 1-12


def all_well_ids() -> Set[str]:
    """Return a set with all 96 well ids in column-major order."""
    wells: list[str] = []
    for col in COLUMNS:
        for row in ROWS:
            wells.append(_format_well(row, col))
    return set(wells)


def is_valid_well_id(well_id: str | None) -> bool:
    if not well_id or not isinstance(well_id, str):
        return False
    well_id = well_id.strip().upper()
    if len(well_id) < 2:
        return False
    row = well_id[0]
    try:
        col = int(well_id[1:])
    except ValueError:
        return False
    return row in ROWS and col in COLUMNS


def patient_no_to_well_id(patient_no: int) -> str:
    """Convert patient number (1..96) to well id (e.g., 1 -> A01)."""
    if not isinstance(patient_no, int):
        raise ValueError(f"Patient number must be int, got {type(patient_no).__name__}")
    if patient_no < 1 or patient_no > 96:
        raise ValueError(f"Patient number out of range: {patient_no}")

    zero_based = patient_no - 1
    col_idx = zero_based // len(ROWS)
    row_idx = zero_based % len(ROWS)
    return _format_well(ROWS[row_idx], COLUMNS[col_idx])


def well_id_to_patient_no(well_id: str) -> int:
    """Convert a well id (A01) to patient number (1..96) using column-major order."""
    if not is_valid_well_id(well_id):
        raise ValueError(f"Invalid well id: {well_id}")
    well_id = well_id.strip().upper()
    row = well_id[0]
    col = int(well_id[1:])

    row_idx = ROWS.index(row)
    col_idx = COLUMNS.index(col)
    return col_idx * len(ROWS) + row_idx + 1


def well_id_to_table_index(well_id: str) -> Tuple[int, int]:
    """
    Convert a well id to table indexes that include header offsets.
    Returns (row, column) where row=0 and col=0 are header cells.
    """
    pn = well_id_to_patient_no(well_id)
    zero_based = pn - 1
    row_idx = zero_based % len(ROWS)
    col_idx = zero_based // len(ROWS)
    return row_idx + 1, col_idx + 1


def table_index_to_well_id(row: int, column: int) -> Optional[str]:
    """Convert a table index (with headers) to a well id. Returns None for header cells."""
    if row <= 0 or column <= 0:
        return None
    row_idx = row - 1
    col_idx = column - 1
    if row_idx >= len(ROWS) or col_idx >= len(COLUMNS):
        return None
    return _format_well(ROWS[row_idx], COLUMNS[col_idx])


def wells_for_header(row: int, column: int) -> Set[str]:
    """
    Return the set of wells represented by a header/index position:
    - (0,0): all wells
    - (0, c): entire column
    - (r, 0): entire row
    - otherwise: single well
    """
    if row == 0 and column == 0:
        return all_well_ids()

    if row == 0 and column > 0:
        col = column
        if col in COLUMNS:
            return {_format_well(r, col) for r in ROWS}
        return set()

    if column == 0 and row > 0:
        r_idx = row - 1
        if 0 <= r_idx < len(ROWS):
            row_label = ROWS[r_idx]
            return {_format_well(row_label, c) for c in COLUMNS}
        return set()

    well = table_index_to_well_id(row, column)
    return {well} if well else set()


def _format_well(row: str, column: int) -> str:
    return f"{row}{column:02d}"