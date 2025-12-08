import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class GraphDrawer(FigureCanvas):
    def __init__(self, parent=None):
        """
        Matplotlib grafiğini oluşturur ve QWidget içine yerleştirir.

        Args:
            parent (QWidget): Ana widget.
        """
        self.fig = Figure(figsize=(6, 4.5))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.title = "PCR Grafik"  # Varsayılan başlık

        # Arka planı siyah yap
        self.fig.patch.set_facecolor("black")
        self.ax.set_facecolor("black")
        self.ax.grid(color="grey", linestyle="--", linewidth=0.5)

        # Eksen ve metin renklerini beyaz yap
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")

        (self.fam_line,) = self.ax.plot(
            [],
            [],
            label="FAM",
            linestyle="-",
            linewidth=2,
            color="#39FF14",  # Neon Yeşili
        )
        (self.hex_line,) = self.ax.plot(
            [],
            [],
            label="HEX",
            linestyle="-",
            linewidth=2,
            color="#FF7F00",  # Neon Turuncu
        )

        # Başlangıç eksen limitlerini ayarla
        self.ax.set_xlim(0, 40)  # X ekseni maksimum 40
        self.ax.set_ylim(0, 5000)  # Y ekseni maksimum 5000
        # self.ax.set_yticks(range(0, 5500, 500))  # Y ekseni 500'er artacak şekilde

        # (x, 0) ekseninde çizgi ekle
        self.ax.axhline(y=0, color="grey", linestyle="-", linewidth=1)
        # (0, y) ekseninde çizgi ekle
        self.ax.axvline(x=0, color="grey", linestyle="-", linewidth=1)

    def set_title(self, title):
        """
        Grafiğin başlığını ayarlar.

        Args:
            title (str): Yeni başlık.
        """
        self.title = title
        self.ax.set_title(self.title)

    def animate_graph(self, fam_coords, hex_coords, start_x=21, speed=25):
        """
        Grafiği animasyonla çizer.

        Args:
            fam_coords (list): FAM koordinat listesi [(x1, y1), (x2, y2)].
            hex_coords (list): HEX koordinat listesi [(x1, y1), (x2, y2)].
            start_x (int): Animasyonun başlayacağı minimum X değeri.
            speed (int): Animasyonun hızı (milisaniye cinsinden).
        """
        # Verileri X=20'den önce ve sonra olarak ayır
        static_fam_coords = [(x, y) for x, y in fam_coords if x < start_x]
        static_hex_coords = [(x, y) for x, y in hex_coords if x < start_x]

        anim_fam_coords = [(x, y) for x, y in fam_coords if x >= start_x]
        anim_hex_coords = [(x, y) for x, y in hex_coords if x >= start_x]

        static_fam_x, static_fam_y = (
            zip(*static_fam_coords) if static_fam_coords else ([], [])
        )
        static_hex_x, static_hex_y = (
            zip(*static_hex_coords) if static_hex_coords else ([], [])
        )
        anim_fam_x, anim_fam_y = zip(*anim_fam_coords) if anim_fam_coords else ([], [])
        anim_hex_x, anim_hex_y = zip(*anim_hex_coords) if anim_hex_coords else ([], [])

        # Eksen sınırlarını animasyon başlamadan önce belirle
        all_x = [x for x, _ in fam_coords + hex_coords]
        all_y = [y for _, y in fam_coords + hex_coords]
        self.ax.set_xlim(
            min(all_x) - 1, max(all_x) + 1
        )  # X ekseninde biraz boşluk bırak
        if max(all_y) > 5000:
            self.ax.set_ylim(0, max(all_y) + 500)
        else:
            self.ax.set_ylim(0, 5000)

        # Önce X=20'den önceki değerleri statik olarak çiz
        self.fam_line.set_data(static_fam_x, static_fam_y)
        self.hex_line.set_data(static_hex_x, static_hex_y)

        # Güncelleme fonksiyonu
        def update(frame):
            self.fam_line.set_data(
                list(static_fam_x) + list(anim_fam_x[:frame]),
                list(static_fam_y) + list(anim_fam_y[:frame]),
            )
            self.hex_line.set_data(
                list(static_hex_x) + list(anim_hex_x[:frame]),
                list(static_hex_y) + list(anim_hex_y[:frame]),
            )
            return self.fam_line, self.hex_line

        # Animasyon
        self.ani = animation.FuncAnimation(
            self.fig,
            update,
            frames=len(anim_fam_x) + 1,
            interval=speed,
            blit=False,
            repeat=False,
        )

        self.draw_idle()

    def draw_graph(self, fam_coords, hex_coords):
        """
        Verilen koordinatlara göre grafiği çizer (Animasyon olmadan).

        Args:
            fam_coords (list): FAM koordinat listesi [(x1, y1), (x2, y2)].
            hex_coords (list): HEX koordinat listesi [(x1, y1), (x2, y2)].
        """
        fam_x, fam_y = zip(*fam_coords)
        hex_x, hex_y = zip(*hex_coords)

        # Çizgi verilerini güncelle
        self.fam_line.set_data(fam_x, fam_y)
        self.hex_line.set_data(hex_x, hex_y)

        # Eksen sınırlarını güncelle
        if max(max(fam_y), max(hex_y)) > 4500:
            self.ax.set_ylim(0, max(max(fam_y), max(hex_y)) + 500)
        else:
            self.ax.set_ylim(0, 4500)
        self.ax.relim()

        # Yeniden çiz
        self.draw()

