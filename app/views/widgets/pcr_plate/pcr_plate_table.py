# app\views\widgets\pcr_plate\pcr_plate_table.py
from __future__ import annotations

from typing import Callable, Set

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygon, QLinearGradient
from PyQt5.QtWidgets import QTableWidget


class PlateTable(QTableWidget):
    """
    Seçim, hover ve preview durumlarını çizen pcr plakası tablosu.

    PCRPlateWidget'tan bağımsız olması için gerekli callback'ler
    constructor üzerinden enjekte edilir.
    """

    def __init__(
        self,
        parent,
        hover_index_getter: Callable[[], tuple[int | None, int | None]],
        on_hover_move: Callable,
        on_mouse_press: Callable,
        on_mouse_move: Callable | None = None,
        on_mouse_release: Callable | None = None,
    ):
        super().__init__(parent)
        self._hover_index_getter = hover_index_getter
        self._on_hover_move = on_hover_move
        self._on_mouse_press = on_mouse_press
        self._on_mouse_move = on_mouse_move
        self._on_mouse_release = on_mouse_release
        self._selected_header_rows = set()
        self._selected_header_cols = set()
        self._preview_cells: Set[tuple[int, int]] = set()

    # ---- painting ----
    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)

        self._draw_corner_indicator(painter)
        self._draw_header_selection(painter)
        self._draw_hover_highlight(painter)
        painter.end()

    def _draw_header_selection(self, painter: QPainter) -> None:
        if not self._selected_header_rows and not self._selected_header_cols:
            return

        painter.save()

        accent = QColor("#3A7AFE")  # ana vurgu
        tint = QColor(58, 122, 254, 50)  # soft arkaplan
        inner_glow = QColor(255, 255, 255, 90)  # cam hissi

        # Row header (col=0)
        for r in self._selected_header_rows:
            idx = self.model().index(r, 0)
            rect = self.visualRect(idx)
            if not rect.isValid():
                continue

            rr = rect.adjusted(1, 1, -1, -1)

            painter.setPen(Qt.NoPen)
            painter.setBrush(tint)
            painter.drawRect(rr)

            painter.setPen(QPen(accent, 2))
            painter.drawLine(rr.bottomLeft(), rr.bottomRight())

            painter.setPen(QPen(inner_glow, 1))
            painter.drawRect(rr.adjusted(1, 1, -1, -1))

        # Column header (row=0)
        for c in self._selected_header_cols:
            idx = self.model().index(0, c)
            rect = self.visualRect(idx)
            if not rect.isValid():
                continue

            rr = rect.adjusted(1, 1, -1, -1)

            painter.setPen(Qt.NoPen)
            painter.setBrush(tint)
            painter.drawRect(rr)

            painter.setPen(QPen(accent, 2))
            painter.drawLine(rr.bottomLeft(), rr.bottomRight())

            painter.setPen(QPen(inner_glow, 1))
            painter.drawRect(rr.adjusted(1, 1, -1, -1))

        painter.restore()

    def _draw_corner_indicator(self, painter: QPainter) -> None:
        corner_index = self.model().index(0, 0)
        rect = self.visualRect(corner_index)
        if not rect.isValid():
            return

        size = min(rect.width(), rect.height())
        if size <= 0:
            return

        triangle_size = max(8, int(size * 0.6))
        triangle = QPolygon(
            [
                rect.topLeft(),
                rect.topLeft() + QPoint(triangle_size, 0),
                rect.topLeft() + QPoint(0, triangle_size),
            ]
        )

        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#4ca1af"))
        painter.drawPolygon(triangle)
        painter.restore()

    def _draw_hover_highlight(self, painter: QPainter) -> None:
        painter.save()

        if self._preview_cells:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            for row_idx, col_idx in self._preview_cells:
                model_index = self.model().index(row_idx, col_idx)
                rect = self.visualRect(model_index)
                if rect.isValid():
                    painter.drawRect(rect.adjusted(1, 1, -1, -1))

        row, col = self._hover_index_getter()
        if row is None or col is None:
            painter.restore()
            return

        model_index = self.model().index(row, col)
        rect = self.visualRect(model_index)
        if not rect.isValid():
            painter.restore()
            return

        is_header = row == 0 or col == 0
        if is_header:
            r = rect.adjusted(1, 1, -1, -1)

            accent = QColor("#3A7AFE")

            grad = QLinearGradient(r.topLeft(), r.bottomLeft())
            grad.setColorAt(0.0, QColor(0, 0, 0, 18))
            grad.setColorAt(1.0, QColor(0, 0, 0, 38))

            painter.setPen(Qt.NoPen)
            painter.setBrush(grad)
            painter.drawRect(r)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(accent, 1))
            painter.drawRect(r)

            painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
            painter.drawRect(r.adjusted(1, 1, -1, -1))

        else:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))

        painter.restore()

    # ---- mouse handling ----
    def mouseMoveEvent(self, event):
        if self._on_mouse_move:
            self._on_mouse_move(event)
        else:
            self._on_hover_move(event)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._on_hover_move(None)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._on_mouse_press(event)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._on_mouse_release:
            self._on_mouse_release(event)
        super().mouseReleaseEvent(event)

    # ---- external state setters ----
    def set_preview_cells(self, cells: Set[tuple[int, int]]) -> None:
        if cells == self._preview_cells:
            return
        self._preview_cells = cells
        self.viewport().update()

    def set_selected_headers(self, rows: set[int], cols: set[int]) -> None:
        """Header seçim state'ini kapsülle; gereksiz repaint'i azalt."""
        if rows == self._selected_header_rows and cols == self._selected_header_cols:
            return
        self._selected_header_rows = rows
        self._selected_header_cols = cols
        self.viewport().update()