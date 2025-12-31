# app\views\widgets\pcr_plate\setup\resizing.py
from __future__ import annotations

from PyQt5.QtWidgets import QTableWidget


def resize_columns_to_fit(table: QTableWidget, min_column_width: int) -> None:
    column_count = table.columnCount()
    if column_count == 0:
        return

    available_width = table.viewport().width()
    if available_width <= 0:
        available_width = table.width()

    if available_width <= 0:
        return

    target_width = max(min_column_width, available_width // column_count)
    if target_width * column_count > available_width:
        target_width = max(1, available_width // column_count)

    remainder = available_width - target_width * column_count
    for col in range(column_count):
        width = target_width + (1 if col < remainder else 0)
        table.setColumnWidth(col, width)