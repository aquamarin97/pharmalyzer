def update_widget_color(widget, condition):
    """
    Widget'ın rengini belirtilen şarta göre günceller.
    """
    color = "#00FF00" if condition else "#FF0000"  # Yeşil veya kırmızı
    widget.setStyleSheet(
        f"""
background-color: #{color}; /* İstediğiniz renk kodunu buraya yazın */
border: 2px solid #333333; /* Kenar çerçevesini ayarlamak için opsiyonel */
border-radius: 5px; /* Köşeleri yuvarlamak için opsiyonel */
border-color: white
    """
    )
