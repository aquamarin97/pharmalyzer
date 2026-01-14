# app/views/widgets/pcr_plate/_ui_setup.py
from __future__ import annotations

from PyQt5.QtWidgets import QHeaderView

from app.views.widgets.pcr_plate.setup.grid_setup import initialize_grid
from app.views.widgets.pcr_plate.setup.resizing import resize_columns_to_fit


def configure_headers(table, min_col_width: int, row_height: int) -> None:
    h_header = table.horizontalHeader()
    h_header.setSectionResizeMode(QHeaderView.Fixed)
    h_header.setMinimumSectionSize(1)
    h_header.setDefaultSectionSize(min_col_width)

    v_header = table.verticalHeader()
    v_header.setSectionResizeMode(QHeaderView.Fixed)
    v_header.setMinimumSectionSize(row_height)


def setup_grid(widget, table) -> None:
    # widget sabitlerini kullanıyoruz
    initialize_grid(
        table,
        header_rows=widget.HEADER_ROWS,
        header_cols=widget.HEADER_COLS,
        row_height=widget.ROW_HEIGHT,
        header_color=widget.COLOR_HEADER,
        base_color=widget.COLOR_BASE,
        table_index_to_patient_no=widget._table_index_to_patient_no,
    )


def resize_columns_to_fit_safe(table, min_column_width: int) -> None:
    resize_columns_to_fit(table, min_column_width)
