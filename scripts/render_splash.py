"""Render the native Android presplash with Kivy (no extra dependencies).

Run from any directory: python scripts/render_splash.py
The generated PNG is committed with the project; APK builds need not run this.
"""

from pathlib import Path
import struct
import zlib

from kivy.config import Config

Config.set("graphics", "width", "720")
Config.set("graphics", "height", "1280")
Config.set("graphics", "resizable", "0")

from kivy import kivy_data_dir  # noqa: E402
from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.graphics import Color, Line, Rectangle  # noqa: E402
from kivy.uix.label import Label  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402


BG = (9 / 255, 7 / 255, 12 / 255, 1)
RED = (1, .32, .39, 1)
CYAN = (.36, .92, .95, 1)
YELLOW = (244 / 255, 244 / 255, 68 / 255, 1)
FONT = str(Path(kivy_data_dir) / "fonts" / "RobotoMono-Regular.ttf")
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "presplash.png"
STORE = OUTPUT.parent.parent / "docs" / "play" / "graphics"


def save_rgb(widget, path, scale=1):
    """Opaque RGB PNG for Play's feature-graphic requirements."""
    texture = widget.export_as_image(scale=scale).texture
    width, height = texture.size
    pixels = texture.pixels
    rows = []
    for y in range(height):
        row = pixels[y * width * 4:(y + 1) * width * 4]
        rows.append(b'\0' + b''.join(row[x:x + 3] for x in range(0, len(row), 4)))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    path.write_bytes(b'\x89PNG\r\n\x1a\n'
                     + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))


class SplashApp(App):
    def build(self):
        root = Widget(size_hint=(None, None), size=(720, 1280))
        with root.canvas:
            Color(*BG)
            Rectangle(pos=(0, 0), size=root.size)
            # Subtle full-bleed grid, with no decorative frame behind the book.
            Color(*RED[:3], .065)
            for y in range(0, 1281, 32):
                Line(points=[0, y, 720, y], width=.5)
            for x in range(0, 721, 32):
                Line(points=[x, 0, x, 1280], width=.5)
            # Same open-book silhouette as the floating binder button.
            Color(*CYAN)
            x, y, scale = 360, 747, 6
            for side in (-1, 1):
                points = [(0, 10), (side * 7, 14), (side * 16, 14),
                          (side * 16, -11), (side * 7, -11), (0, -15)]
                Line(points=[v for px, py in points
                             for v in (x + px * scale, y + py * scale)], width=2)
            Line(points=[x, y + 60, x, y - 90], width=2)
        title = Label(text=">NightCityBinder_", font_name=FONT,
                              font_size=32, color=YELLOW,
                              size_hint=(None, None), size=(566, 111),
                              pos=(77, 510))
        title.texture_update()
        root.add_widget(title)
        return root

    def on_start(self):
        Clock.schedule_once(lambda _dt: Clock.schedule_once(self.save, .5), .3)

    def save(self, _dt):
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        STORE.mkdir(parents=True, exist_ok=True)
        self.root.export_to_png(str(OUTPUT), scale=1.5)
        print(f"Saved {OUTPUT}")
        # Adaptive foreground uses the central safe zone (66/108 of the layer).
        for name, adaptive in (("icon.png", False), ("icon_foreground.png", True)):
            icon = Widget(size_hint=(None, None), size=(432, 432))
            with icon.canvas:
                if not adaptive:
                    Color(*BG)
                    Rectangle(size=icon.size)
                factor = .64 if adaptive else 1
                def pt(x, y):
                    return (216 + (x - 216) * factor, 216 + (y - 216) * factor)
                Color(*YELLOW)
                corners = [(66, 66), (366, 66), (366, 322), (322, 366),
                           (66, 366), (66, 66)]
                Line(points=[v for x, y in corners for v in pt(x, y)],
                     width=4 * factor)
                Color(*CYAN)
                for side in (-1, 1):
                    points = [(0, 10), (side * 7, 14), (side * 16, 14),
                              (side * 16, -11), (side * 7, -11), (0, -15)]
                    Line(points=[v for x, y in points
                                 for v in pt(216 + x * 6, 216 + y * 6)],
                         width=3 * factor)
                Line(points=[*pt(216, 276), *pt(216, 126)], width=3 * factor)
            icon.export_to_png(str(OUTPUT.with_name(name)), scale=1024 / 432)
            if not adaptive:
                save_rgb(icon, STORE / "store-icon-512.png", scale=512 / 432)
        background = Widget(size_hint=(None, None), size=(432, 432))
        with background.canvas:
            Color(*BG)
            Rectangle(size=background.size)
        background.export_to_png(str(OUTPUT.with_name("icon_background.png")))
        banner = Widget(size_hint=(None, None), size=(1024, 500))
        with banner.canvas:
            Color(*BG)
            Rectangle(size=banner.size)
            Color(*RED[:3], .065)
            for x in range(0, 1025, 32):
                Line(points=[x, 0, x, 500], width=.5)
            for y in range(0, 501, 32):
                Line(points=[0, y, 1024, y], width=.5)
            Color(*YELLOW)
            Line(points=[90, 145, 310, 145, 310, 325, 275, 360, 90, 360, 90, 145], width=2)
            Color(*CYAN)
            for side in (-1, 1):
                points = [(0, 10), (side * 7, 14), (side * 16, 14),
                          (side * 16, -11), (side * 7, -11), (0, -15)]
                Line(points=[v for x, y in points for v in (200 + x * 4.8, 250 + y * 4.8)], width=2)
            Line(points=[200, 298, 200, 178], width=2)
        title = Label(text=">NightCityBinder_", font_name=FONT, font_size=40,
                      color=YELLOW, size_hint=(None, None), size=(650, 100), pos=(330, 200))
        title.texture_update()
        banner.add_widget(title)
        # Defer export so the label canvas has a frame to update.
        self.banner = banner
        Clock.schedule_once(self.save_banner, .3)

    def save_banner(self, _dt):
        save_rgb(self.banner, STORE / "feature-1024x500.png")
        self.stop()


if __name__ == "__main__":
    SplashApp().run()
