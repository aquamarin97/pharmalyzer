# app\common\widgets\dialogs.py

from typing import Optional

from PyQt5.QtWidgets import (
    QMessageBox,
    QWidget,
    QStyle,
    QApplication,
)
from PyQt5.QtCore import Qt


class Dialogs:
    """Uygulama genelinde kullanılan standart diyaloglar."""

    @staticmethod
    def critical(
        parent: Optional[QWidget],
        title: str,
        text: str,
        detailed_text: Optional[str] = None,
        buttons: QMessageBox.StandardButton = QMessageBox.Ok,
    ) -> QMessageBox.StandardButton:
        """
        Kritik hata mesajı gösterir.

        Args:
            parent: Parent widget (genellikle None veya main window)
            title: Pencere başlığı
            text: Ana mesaj
            detailed_text: Opsiyonel detaylı hata bilgisi (kullanıcı "Detay Göster"e basınca görünür)
            buttons: Gösterilecek butonlar

        Returns:
            Basılan buton
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)

        if detailed_text:
            msg.setDetailedText(detailed_text.strip())

        msg.setStandardButtons(buttons)
        msg.setDefaultButton(QMessageBox.Ok)

        # Qt'nin standart Critical ikonunu kullan (daha temiz görünür)
        msg.setWindowIcon(QApplication.style().standardIcon(QStyle.SP_MessageBoxCritical))

        return msg.exec_()

    @staticmethod
    def warning(
        parent: Optional[QWidget],
        title: str,
        text: str,
        detailed_text: Optional[str] = None,
        buttons: QMessageBox.StandardButton = QMessageBox.Ok,
    ) -> QMessageBox.StandardButton:
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(text)
        if detailed_text:
            msg.setDetailedText(detailed_text.strip())
        msg.setStandardButtons(buttons)
        msg.setDefaultButton(QMessageBox.Ok)
        return msg.exec_()

    @staticmethod
    def information(
        parent: Optional[QWidget],
        title: str,
        text: str,
        detailed_text: Optional[str] = None,
    ) -> None:
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(text)
        if detailed_text:
            msg.setDetailedText(detailed_text.strip())
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    @staticmethod
    def question(
        parent: Optional[QWidget],
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton = QMessageBox.Yes | QMessageBox.No,
        default_button: QMessageBox.StandardButton = QMessageBox.No,
    ) -> QMessageBox.StandardButton:
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        msg.setDefaultButton(default_button)
        return msg.exec_()