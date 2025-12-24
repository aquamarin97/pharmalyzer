from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
import time
import logging
logger = logging.getLogger(__name__)
from app.services.pipeline import Pipeline, Step, CancelledError

from app.services.analysis_steps.calculate_with_referance import CalculateWithReferance
from app.services.analysis_steps.calculate_regration import CalculateRegration
from app.services.analysis_steps.calculate_without_referance import CalculateWithoutReferance
from app.services.analysis_steps.configurate_result_csv import ConfigurateResultCSV
from app.services.analysis_steps.csv_processor import CSVProcessor

ProgressCb = Callable[[int, str], None]
IsCancelled = Callable[[], bool]


@dataclass
class AnalysisConfig:
    referance_well: str = "F12"
    checkbox_status: bool = True
    carrier_range: float = 0.5999
    uncertain_range: float = 0.6199


class AnalysisService:
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _is_cancelled(self) -> bool:
        return self._cancelled

    def set_referance_well(self, v: str) -> None:
        self.config.referance_well = str(v)

    def set_checkbox_status(self, v: bool) -> None:
        self.config.checkbox_status = bool(v)

    def set_carrier_range(self, v: float) -> None:
        v = float(v)
        if v >= float(self.config.uncertain_range):
            raise ValueError("Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır.")
        self.config.carrier_range = v

    def set_uncertain_range(self, v: float) -> None:
        v = float(v)
        if v <= float(self.config.carrier_range):
            raise ValueError("Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır.")
        self.config.uncertain_range = v

    def run(
        self,
        progress_cb: Optional[ProgressCb] = None,
        is_cancelled: Optional[IsCancelled] = None,
    ) -> bool:
        # Her run başlangıcında cancel flag sıfırla
        self._cancelled = False
        is_cancelled = is_cancelled or self._is_cancelled

        def progress(p: int, msg: str) -> None:
            if progress_cb:
                progress_cb(int(p), str(msg))

        # Step instance'ları
        ref_step = CalculateWithReferance(
            self.config.referance_well,
            self.config.carrier_range,
            self.config.uncertain_range,
        )
        reg_step = CalculateRegration()
        sw_step = CalculateWithoutReferance(
            carrier_range=self.config.carrier_range,
            uncertain_range=self.config.uncertain_range,
        )
        post_step = ConfigurateResultCSV(self.config.checkbox_status)

        steps = [
            Step("CSV hazırlama", CSVProcessor.process),
            Step("Referanslı hesaplama", ref_step.process),
            Step("Regresyon", reg_step.process),
            Step("Referanssız hesaplama", sw_step.process),
            Step("Sonuç CSV formatlama", post_step.process),
        ]

        try:
            # Step wrapper: her adımı zamanla
            timed_steps = []
            for s in steps:
                def _wrap(fn, name):
                    def _inner(df):
                        t0 = time.perf_counter()
                        out = fn(df)
                        t1 = time.perf_counter()
                        logger.info("[PERF] Step '%s' took %.0f ms", name, (t1 - t0) * 1000)
                        return out
                    return _inner
                timed_steps.append(Step(s.name, _wrap(s.fn, s.name)))

            Pipeline.run(
                timed_steps,
                progress_cb=progress,
                is_cancelled=is_cancelled,
                copy_input_each_step=False,
            )
        except CancelledError:
            # Cancel bir hata değil → False dön
            return False

        # referans kuyusu başarısızsa checkbox zorla True
        if not getattr(ref_step, "last_success", True):
            self.config.checkbox_status = True

        return True
