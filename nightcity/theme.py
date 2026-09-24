"""Lightweight vector UI inspired by the game's inventory terminals.

No game assets, shaders or continuous animation; all geometry scales in dp.
"""
from pathlib import Path

from kivy import kivy_data_dir
from kivy.graphics import Color, Line, Mesh, Rectangle, Triangle, InstructionGroup
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty

BG = (0.035, 0.027, 0.047, 1)
PANEL = (0.085, 0.044, 0.068, 1)
INK = (0.94, 0.91, 0.91, 1)
MUTED = (0.68, 0.56, 0.60, 1)
ACCENT = (1, 0.32, 0.39, 1)
CYAN = (0.36, 0.92, 0.95, 1)
YELLOW = (0.96, 0.96, 0.27, 1)
RED = (0.72, 0.12, 0.19, 1)
MONO = str(Path(kivy_data_dir) / "fonts" / "RobotoMono-Regular.ttf")


def frame(widget, color=ACCENT, fill=None, mask=False, accent=True):
    group = InstructionGroup()
    (widget.canvas.after if mask else widget.canvas.before).add(group)

    def draw(*_):
        group.clear()
        x, y, w, h = widget.x, widget.y, widget.width, widget.height
        cut = min(dp(9), w / 4, h / 4)
        points = [x + cut, y, x + w, y, x + w, y + h - cut,
                  x + w - cut, y + h, x, y + h, x, y + cut]
        if fill:
            group.add(Color(*fill))
            vertices = [value for i in range(0, len(points), 2) for value in (points[i], points[i + 1], 0, 0)]
            group.add(Mesh(vertices=vertices, indices=list(range(6)), mode="triangle_fan"))
        if mask:
            group.add(Color(*BG))
            group.add(Triangle(points=[x, y, x + cut, y, x, y + cut]))
            group.add(Triangle(points=[x + w, y + h, x + w - cut, y + h, x + w, y + h - cut]))
        pressed = getattr(widget, "state", "normal") == "down"
        group.add(Color(*(CYAN if pressed else color)))
        group.add(Line(points=points, close=True, width=dp(1.2 if pressed else .65)))
        if accent:
            group.add(Line(points=[x, y + h - dp(5), x, y + h - min(dp(26), h / 2)], width=dp(2)))
    widget.bind(pos=draw, size=draw)
    if hasattr(widget, "state"):
        widget.bind(state=draw)
    draw()


def screen_background(widget):
    group = InstructionGroup()
    widget.canvas.before.add(group)

    def draw(*_):
        group.clear()
        group.add(Color(*BG))
        group.add(Rectangle(pos=widget.pos, size=widget.size))
        # Subtle burgundy glow at the top, drawn once per layout change.
        for i in range(48):
            group.add(Color(.32, .055, .10, .18 * (1 - i / 48)))
            height = widget.height * .48 / 48
            group.add(Rectangle(pos=(widget.x, widget.top - (i + 1) * height), size=(widget.width, height + 1)))
        group.add(Color(*ACCENT[:3], .22))
        for side in (widget.x + dp(6), widget.right - dp(6)):
            group.add(Line(points=[side, widget.y + dp(18), side, widget.top - dp(18)], width=dp(.5)))
            for offset in range(36, int(widget.height / dp(1)), 48):
                yy = widget.y + dp(offset)
                group.add(Line(points=[side - dp(2), yy, side + dp(2), yy], width=dp(.5)))
    widget.bind(pos=draw, size=draw)
    draw()


class HudButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", PANEL)
        kwargs.setdefault("color", INK)
        super().__init__(**kwargs)
        self.halign = "center"
        self.valign = "middle"
        self.padding = [dp(14), dp(4)]
        self.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0] - dp(26), size[1] - dp(6))))
        frame(self, mask=True)


class HudOption(HudButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48))
        kwargs.setdefault("font_size", dp(13))
        super().__init__(**kwargs)


class HudSpinner(Spinner):
    def __init__(self, **kwargs):
        kwargs.setdefault("option_cls", HudOption)
        kwargs.setdefault("color", CYAN)
        kwargs.setdefault("font_size", dp(13))
        super().__init__(**kwargs)
        frame(self, color=CYAN, mask=True, accent=False)


class HudInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selection_color = (*CYAN[:3], .25)
        group = InstructionGroup()
        self.canvas.after.add(group)

        def draw(*_):
            group.clear()
            group.add(Color(*(CYAN if self.focus else ACCENT)))
            right = self.x + self.width
            group.add(Line(points=[self.x, self.y + dp(6), self.x, self.y,
                                   right, self.y, right, self.y + dp(6)], width=dp(.8)))
            self.underline_points = (self.x, right)
        self._redraw_underline = Clock.create_trigger(draw, -1)
        self.bind(pos=self._redraw_underline, size=self._redraw_underline,
                  focus=self._redraw_underline)
        self._redraw_underline()


class HudPopup(Popup):
    def __init__(self, **kwargs):
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", BG)
        kwargs.setdefault("separator_color", ACCENT)
        kwargs.setdefault("separator_height", dp(1))
        kwargs.setdefault("title_color", ACCENT)
        kwargs.setdefault("title_font", MONO)
        kwargs.setdefault("title_size", dp(16))
        kwargs.setdefault("overlay_color", (0, 0, 0, .8))
        super().__init__(**kwargs)
        frame(self, mask=True)


class HudProgress(Widget):
    max = NumericProperty(100)
    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*PANEL)
            self.track = Rectangle()
            Color(*CYAN)
            self.bar = Rectangle()
        self.bind(pos=self.redraw, size=self.redraw, value=self.redraw, max=self.redraw)
        self.redraw()

    def redraw(self, *_):
        self.track.pos, self.track.size = self.pos, self.size
        self.bar.pos = self.pos
        self.bar.size = (self.width * min(1, max(0, self.value / (self.max or 1))), self.height)
