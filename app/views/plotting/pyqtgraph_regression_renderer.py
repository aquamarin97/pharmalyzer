# app\views\plotting\pyqtgraph_regression_renderer.py
from __future__ import annotations

import pyqtgraph as pg

from app.services.interaction_store import InteractionStore
from app.services.regression_plot_service import RegressionPlotData
from app.views.plotting.regression.interaction import RegressionInteraction
from app.views.plotting.regression.renderer import RegressionRenderer
from app.views.plotting.regression.styles import RegressionPlotStyle


class PyqtgraphRegressionRenderer:
    def __init__(self, style: RegressionPlotStyle):
        self._renderer = RegressionRenderer(style=style)
        self._interaction = RegressionInteraction()

    def render(
        self,
        plot_item: pg.PlotItem,
        data: RegressionPlotData,
        enable_hover: bool = True,
        hover_text_item: pg.TextItem | None = None,
        interaction_store: InteractionStore | None = None,
    ) -> list[pg.GraphicsObject]:
        plot_item.clear()

        result = self._renderer.render(data)
        if hover_text_item is not None:
            plot_item.addItem(hover_text_item)

        for item in result.items:
            plot_item.addItem(item)

        self._interaction.detach()
        if enable_hover and hover_text_item is not None and not result.hover_points.is_empty:
            self._interaction.attach(
                plot_item=plot_item,
                hover_text_item=hover_text_item,
                hover_points=result.hover_points,
                interaction_store=interaction_store,
            )
        elif hover_text_item is not None:
            hover_text_item.hide()

        return result.items

    def update_styles(self, selected_wells: set[str] | None, hover_well: str | None) -> None:
        self._renderer.update_styles(selected_wells, hover_well)

    def detach_hover(self) -> None:
        self._interaction.detach()