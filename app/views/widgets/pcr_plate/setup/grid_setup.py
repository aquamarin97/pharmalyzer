# app\views\widgets\pcr_plate\setup\grid_setup.py
from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

from app.utils import well_mapping


def initialize_grid(
    table: QTableWidget,
    header_rows: int,
    header_cols: int,
    row_height: int,
    header_color,
    base_color,
    table_index_to_patient_no: Callable[[int, int], int],
) -> None:
    table.setRowCount(len(well_mapping.ROWS) + header_rows)
    table.setColumnCount(len(well_mapping.COLUMNS) + header_cols)

    for row in range(table.rowCount()):
        for col in range(table.columnCount()):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, col, item)

    _populate_headers(table)
    _populate_cells(table, table_index_to_patient_no)
    apply_base_colors(table, header_color, base_color)
    set_row_heights(table, row_height)


def _populate_headers(table: QTableWidget) -> None:
    corner = table.item(0, 0)
    if corner:
        corner.setText("")

    for idx, col in enumerate(well_mapping.COLUMNS, start=1):
        item = table.item(0, idx)
        if item:
            item.setText(f"{col:02d}")

    for idx, row_label in enumerate(well_mapping.ROWS, start=1):
        item = table.item(idx, 0)
        if item:
            item.setText(row_label)


def _populate_cells(table: QTableWidget, table_index_to_patient_no: Callable[[int, int], int]) -> None:
    for row_idx, _ in enumerate(well_mapping.ROWS, start=1):
        for col_idx, _ in enumerate(well_mapping.COLUMNS, start=1):
            item = table.item(row_idx, col_idx)
            if item:
                patient_no = table_index_to_patient_no(row_idx, col_idx)
                item.setText(str(patient_no))


def apply_base_colors(table: QTableWidget, header_color, base_color) -> None:
    for row in range(table.rowCount()):
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item is None:
                continue
            if row == 0 or col == 0:
                item.setBackground(header_color)
            else:
                item.setBackground(base_color)


def set_row_heights(table: QTableWidget, row_height: int) -> None:
    for row in range(table.rowCount()):
        table.setRowHeight(row, row_height)