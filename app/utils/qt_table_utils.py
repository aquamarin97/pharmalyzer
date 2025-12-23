# app/utils/qt_table_utils.py

from __future__ import annotations

from typing import Any, List

import pandas as pd
from PyQt5.QtCore import Qt


def table_view_to_dataframe(table_view, *, include_headers: bool = True) -> pd.DataFrame:
    model = table_view.model()
    if model is None:
        raise ValueError("Tablo modeli boş!")

    rows = model.rowCount()
    cols = model.columnCount()

    data: List[List[Any]] = []
    for r in range(rows):
        row_data: List[Any] = []
        for c in range(cols):
            idx = model.index(r, c)
            row_data.append(model.data(idx, Qt.DisplayRole))
        data.append(row_data)

    if include_headers:
        headers = [model.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(cols)]
        headers = [str(h) if h is not None else "" for h in headers]
        return pd.DataFrame(data, columns=headers)

    return pd.DataFrame(data)
