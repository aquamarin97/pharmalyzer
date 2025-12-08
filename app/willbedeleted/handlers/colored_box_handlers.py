from PyQt5.QtCore import QObject, pyqtSignal


class CalculationHandler(QObject):
    calculationCompleted = pyqtSignal(float)

    def perform_calculation(self):
        """
        Hesaplama işlemini gerçekleştirir ve sonucu sinyal ile yayar.
        """
        import random

        result = random.uniform(0, 10)
        print(f"Hesaplanan değer: {result}")
        self.calculationCompleted.emit(result)
