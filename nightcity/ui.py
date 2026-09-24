from __future__ import annotations

import os
import json
import re
import sqlite3
import threading
import textwrap
from datetime import date
from decimal import Decimal
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.cache import Cache
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image, AsyncImage
from kivy.loader import Loader
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.stencilview import StencilView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform, escape_markup

from nightcity.android_bridge import AndroidBridge
from nightcity.core import CONDITIONS, FINISHES, Store, card_matches_filters, match_cards, normalized
from nightcity.i18n import translate
from nightcity.downloads import DownloadCooldown
from nightcity.services import Catalog, ExchangeRates, Prices
from nightcity.storage import storage_usage, format_bytes
from nightcity.theme import (
    BG, PANEL, INK, MUTED, YELLOW, CYAN, RED, ACCENT, MONO,
    HudButton, HudInput, HudPopup as Popup, HudSpinner as Spinner, HudProgress as ProgressBar, frame, screen_background,
)

VALUE_GREEN = (58 / 255, 247 / 255, 0, 1)
CONDITION_NAMES = dict(zip(CONDITIONS, ("Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged")))


def label(text, height=30, size=15, color=INK, adaptive=False, **kwargs):
    widget = Label(
        text=text,
        size_hint_y=None,
        height=dp(height),
        font_size=dp(size),
        color=color,
        halign=kwargs.pop("halign", "left"),
        valign="middle",
        **kwargs,
    )
    widget.bind(size=lambda obj, value: setattr(obj, "text_size", (value[0], None) if adaptive else value))
    if adaptive:
        widget.bind(texture_size=lambda obj, value: setattr(obj, "height", max(dp(height), value[1] + dp(12))))
    return widget


def button(text, callback, primary=False, height=46):
    widget = HudButton(
        text=text,
        size_hint_y=None,
        height=dp(height),
        font_size=dp(14),
        background_normal="",
        background_down="",
        background_color=YELLOW if primary else PANEL,
        color=BG if primary else INK,
    )
    widget.bind(on_release=lambda *_: callback())
    return widget


def field(hint="", text=""):
    return HudInput(
        text=text,
        hint_text=hint,
        multiline=False,
        size_hint_y=None,
        height=dp(46),
        padding=[dp(12), dp(12)],
        background_normal="",
        background_active="",
        background_color=PANEL,
        foreground_color=INK,
        hint_text_color=MUTED,
        cursor_color=CYAN,
        font_size=dp(15),
    )


def solid_background(widget, color=BG):
    """Cover artwork beneath an information bar or a floating control."""
    with widget.canvas.before:
        Color(*color)
        backdrop = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda obj, *_: setattr(backdrop, "pos", obj.pos),
                size=lambda obj, *_: setattr(backdrop, "size", obj.size))


class Panel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        frame(self, color=(*ACCENT[:3], .55), fill=PANEL)


class BinderPickerPopup(Popup):
    """Leave room above and below the binder picker on Android screens."""

    def _align_center(self, *_args):
        if not getattr(self, "_is_open", False):
            return
        height = max(dp(1), self._window.height - dp(76))
        if abs(self.height - height) > 0.1:
            self.height = height
        window_center_x, window_center_y = self._window.center
        if abs(self.center_x - window_center_x) > 0.1:
            self.center_x = window_center_x
        center_y = window_center_y + dp(18)
        if abs(self.center_y - center_y) > 0.1:
            self.center_y = center_y


class CardTile(ButtonBehavior, Panel):
    pass


class ClippedFloatLayout(FloatLayout, StencilView):
    """Keep scrolling card artwork inside the page below the app title."""


class FilterDismissScrollView(ScrollView):
    def __init__(self, dismiss_filters=None, **kwargs):
        super().__init__(**kwargs)
        self.dismiss_filters = dismiss_filters

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.dismiss_filters and self.dismiss_filters(touch):
            return True
        return super().on_touch_down(touch)


class MenuButton(Button):
    """Draw the hamburger so it also works with Android fonts missing U+2630."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        frame(self, color=ACCENT, mask=True, accent=False)
        with self.canvas.after:
            Color(*ACCENT)
            self.bars = [Line(width=dp(1.2)) for _ in range(3)]
        self.bind(pos=self.redraw, size=self.redraw)
        self.redraw()

    def redraw(self, *_):
        for bar, offset in zip(self.bars, (-6, 0, 6)):
            y = self.center_y + dp(offset)
            bar.points = [self.center_x - dp(10), y, self.center_x + dp(10), y]


class ScanButton(Button):
    """Floating scanner control with font-independent artwork."""

    def __init__(self, **kwargs):
        super().__init__(text="", background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), size_hint=(None, None),
                         size=(dp(56), dp(56)), **kwargs)
        solid_background(self, (0, 0, 0, 1))
        with self.canvas.after:
            Color(*YELLOW)
            self.outline = Line(width=dp(1.3))
            self.corners = [Line(width=dp(1.5)) for _ in range(4)]
            self.sweep = Line(width=dp(1.2))
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw)
        self.redraw()

    def redraw(self, *_):
        self.outline.rectangle = (self.x + dp(1), self.y + dp(1), self.width - dp(2), self.height - dp(2))
        self.outline.width = dp(2.3 if self.state == "down" else 1.3)
        for line, (sx, sy) in zip(self.corners, ((-1, -1), (-1, 1), (1, -1), (1, 1))):
            x, y = self.center_x + sx * dp(12), self.center_y + sy * dp(15)
            line.points = [x - sx * dp(7), y, x, y, x, y - sy * dp(7)]
        self.sweep.points = [self.center_x - dp(8), self.center_y, self.center_x + dp(8), self.center_y]


class SearchButton(Button):
    """Font-independent magnifying glass for the binder search toggle."""

    def __init__(self, **kwargs):
        super().__init__(text="", background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), size_hint=(None, None),
                         size=(dp(40), dp(40)), **kwargs)
        with self.canvas.after:
            Color(*CYAN)
            self.lens = Line(width=dp(1.4))
            self.handle = Line(width=dp(1.4))
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw)
        self.redraw()

    def redraw(self, *_):
        x, y = self.center
        self.lens.circle = (x - dp(3), y + dp(3), dp(7))
        self.handle.points = [x + dp(2), y - dp(2), x + dp(10), y - dp(10)]
        self.lens.width = dp(2 if self.state == "down" else 1.4)


class FilterButton(Button):
    """Font-independent funnel icon matching the search control."""

    def __init__(self, **kwargs):
        super().__init__(text="", background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), size_hint=(None, None),
                         size=(dp(40), dp(40)), **kwargs)
        with self.canvas.after:
            Color(*CYAN)
            self.funnel = Line(width=dp(1.4))
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw)
        self.redraw()

    def redraw(self, *_):
        x, y = self.center
        self.funnel.points = [x - dp(11), y + dp(9), x + dp(11), y + dp(9),
                              x + dp(3), y, x + dp(3), y - dp(9),
                              x - dp(3), y - dp(12), x - dp(3), y,
                              x - dp(11), y + dp(9)]
        self.funnel.width = dp(2 if self.state == "down" else 1.4)


class MissingPriceButton(Button):
    """Cyan-framed shortcut for showing only unpriced binder entries."""

    def __init__(self, **kwargs):
        super().__init__(background_normal="", background_down="", background_color=BG,
                         color=ACCENT, font_size=dp(11), size_hint_y=None, height=dp(48),
                         halign="center", valign="middle", **kwargs)
        self.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0] - dp(12), size[1] - dp(4))))
        frame(self, color=CYAN, mask=True, accent=False)


class CardFilterPanel(BoxLayout):
    KEYS = ("card_type", "color", "cost", "ram")

    def __init__(self, translate_key, cards, changed, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6), size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        self.any_text = translate_key("filter_any")
        self.controls = {}
        trigger = Clock.create_trigger(lambda dt: changed(), 0)
        self._change_trigger = trigger
        self._suspend = False
        grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(6))
        grid.bind(minimum_height=grid.setter("height"))
        self.add_widget(grid)
        choices = {
            "card_type": sorted({c.card_type for c in cards if c.card_type}, key=normalized),
            "color": sorted({color.strip() for c in cards for color in c.color.split("/") if color.strip()},
                            key=normalized),
            "cost": sorted({c.cost for c in cards if c.cost is not None}),
            "ram": sorted({c.ram for c in cards if c.ram is not None}),
        }
        for key in self.KEYS:
            cell = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(62), spacing=dp(2))
            cell.add_widget(label(translate_key("filter_" + key), 18, 11, MUTED))
            values = [self.any_text, *(str(value) for value in choices[key])]
            control = Spinner(text=self.any_text, values=values, size_hint_y=None, height=dp(40),
                              background_normal="", background_color=PANEL, font_size=dp(12))
            control.disabled = len(values) == 1
            control.bind(text=lambda *_: None if self._suspend else trigger())
            cell.add_widget(control)
            grid.add_widget(cell)
            self.controls[key] = control
        if not choices["cost"] and not choices["ram"]:
            self.add_widget(label(translate_key("filter_download_hint"), 48, 11, MUTED, adaptive=True))
        self.add_widget(button(translate_key("clear_filters"), self.clear, height=36))

    def selection(self):
        return {key: (int(control.text) if key in ("cost", "ram") else control.text)
                for key, control in self.controls.items() if control.text != self.any_text}

    def set_selection(self, selected):
        self._suspend = True
        try:
            for key, control in self.controls.items():
                value = selected.get(key)
                text = str(value) if value is not None else self.any_text
                control.text = text if text in control.values else self.any_text
        finally:
            self._suspend = False

    def clear(self):
        self.set_selection({})
        self._change_trigger()


class PencilButton(Button):
    def __init__(self, **kwargs):
        super().__init__(text="", background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), size_hint=(None, None),
                         size=(dp(40), dp(40)), **kwargs)
        with self.canvas.after:
            Color(*CYAN)
            self.pencil = Line(width=dp(1.3))
            self.cap = Line(width=dp(1.3))
        self.bind(pos=self.redraw, size=self.redraw)
        self.redraw()

    def redraw(self, *_):
        x, y = self.center
        self.pencil.points = [x - dp(10), y - dp(10), x - dp(8), y - dp(3),
                              x + dp(6), y + dp(11), x + dp(11), y + dp(6),
                              x - dp(3), y - dp(8), x - dp(10), y - dp(10)]
        self.cap.points = [x + dp(3), y + dp(8), x + dp(8), y + dp(3)]


class BinderButton(Button):
    """Cyan book, drawn in the same outline style as the scanner."""

    def __init__(self, **kwargs):
        super().__init__(text="", background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), size_hint=(None, None),
                         size=(dp(56), dp(56)), **kwargs)
        solid_background(self, (0, 0, 0, 1))
        with self.canvas.after:
            Color(*CYAN)
            self.outline = Line(width=dp(1.3))
            self.pages = [Line(width=dp(1.3)) for _ in range(2)]
            self.spine = Line(width=dp(1.3))
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw)
        self.redraw()

    def redraw(self, *_):
        self.outline.rectangle = (self.x + dp(1), self.y + dp(1), self.width - dp(2), self.height - dp(2))
        self.outline.width = dp(2.3 if self.state == "down" else 1.3)
        x, y = self.center
        for line, side in zip(self.pages, (-1, 1)):
            line.points = [x, y + dp(10), x + side * dp(7), y + dp(14),
                           x + side * dp(16), y + dp(14), x + side * dp(16), y - dp(11),
                           x + side * dp(7), y - dp(11), x, y - dp(15)]
        self.spine.points = [x, y + dp(10), x, y - dp(15)]


class NightCityBinderApp(App):
    title = ">NightCityBinder_"

    def t(self, key, **kwargs):
        if key == "version" and platform == "android":
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            version = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0).versionName
            return ("Wersja " if self.language == "pl" else "Version ") + str(version)
        return translate(self.language, key, **kwargs)

    def build(self):
        if platform != "android":
            Window.size = (480, 860)
        Window.clearcolor = BG
        Loader.max_upload_per_frame = 4
        default = self.user_data_dir if platform == "android" else str(Path(__file__).resolve().parents[1] / ".local")
        self.data_dir = Path(os.environ.get("NCB_DATA_DIR", default))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = Store(self.data_dir / "binder.sqlite3")
        preferences = self.store.settings()
        self.language, self.currency = preferences["language"], preferences["currency"]
        self.catalog = Catalog(self.data_dir)
        self.fx = ExchangeRates(self.data_dir)
        self.prices = Prices(self.data_dir)
        self.bridge = AndroidBridge()
        self.download_cooldown = DownloadCooldown(self.store)
        self.download_buttons = []
        self.cooldown_event = Clock.schedule_interval(self.update_download_buttons, 1)
        self.binder_id, self.page, self.busy = "mine", "binder", False
        self.catalog_body = None
        self.catalog_cache_language = None
        self.binder_body = None
        self.binder_cache_key = None
        self.history = []
        self.progress_active, self.progress_value = False, None
        self.progress_text = ""
        self.catalog_download_active = False
        self.root_box = BoxLayout(orientation="vertical", padding=[dp(18), dp(18), dp(18), dp(8)], spacing=dp(10))
        screen_background(self.root_box)
        self.render()
        Window.bind(on_keyboard=self.keyboard)
        self.progress_event = Clock.schedule_interval(self.animate_progress, 0.08)
        if platform == "android":
            self.insets_event = Clock.schedule_interval(lambda dt: self.bridge.safe_area(self.apply_insets), 0.5)
        if not os.environ.get("NCB_NO_NETWORK"):
            Clock.schedule_once(lambda dt: self.refresh_fx(silent=True), 1)
        return self.root_box

    def keyboard(self, window, key, *args):
        if key == 27:
            return self.go_back()
        return False

    def apply_insets(self, values):
        self.root_box.padding = [dp(base) + max(0, value) for base, value in zip((18, 18, 18, 8), values)]

    def capture_page(self):
        state = dict(page=self.page, binder_id=self.binder_id,
                     detail_card=getattr(self, "detail_card", None),
                     detail_entry=getattr(self, "detail_entry", None),
                     owned_default=getattr(self, "owned_default", None))
        if self.page == "catalog":
            state.update(query=self.search_input.text, candidates=getattr(self, "catalog_candidates", None),
                         limit=self.result_limit, scroll=self.result_grid.parent.scroll_y,
                         filters=self.catalog_filters.selection(), search_visible=self.catalog_search_open,
                         filters_visible=self.catalog_filters_open)
        elif self.page == "binder":
            state.update(query=self.binder_search.text, limit=self.binder_limit,
                         search_visible=self.binder_search_open, filters=self.binder_filters.selection(),
                         filters_visible=self.binder_filters_open, missing_only=self.binder_missing_only,
                         scroll=self.binder_grid.parent.scroll_y)
        return state

    def go_back(self):
        if not self.history:
            return False
        state = self.history.pop()
        self.page = state["page"]
        self.binder_id = state["binder_id"] if state["binder_id"] in self.binder_names() else "mine"
        self.detail_card, self.detail_entry = state["detail_card"], state["detail_entry"]
        self.owned_default = state["owned_default"]
        self.render()
        if self.page == "catalog":
            needs_fill = (self.search_input.text != state["query"] or self.result_limit != state["limit"]
                          or self.catalog_candidates != state["candidates"]
                          or self.catalog_filters.selection() != state["filters"])
            if needs_fill:
                self.search_input.text = state["query"]
                if self.search_event:
                    self.search_event.cancel()
                self.catalog_filters.set_selection(state["filters"])
                self.result_limit = state["limit"]
                self.fill_catalog(state["candidates"])
            self.catalog_search_open = state["search_visible"]
            self.catalog_filters_open = state["filters_visible"]
            self.layout_collapsible(self.catalog_header, self.search_input, self.catalog_filters,
                                    self.catalog_search_open, self.catalog_filters_open, self.result_count)
            Clock.schedule_once(lambda dt: setattr(self.result_grid.parent, "scroll_y", state["scroll"]), 0)
        elif self.page == "binder":
            needs_fill = (self.binder_search.text != state["query"] or
                          self.binder_filters.selection() != state["filters"] or
                          self.binder_missing_only != state["missing_only"] or
                          self.binder_limit != state["limit"])
            self.binder_search_open = state["search_visible"]
            self.binder_filters_open = state["filters_visible"]
            self.binder_search.text = state["query"]
            self.binder_filters.set_selection(state["filters"])
            self.binder_missing_only = state["missing_only"] and self.binder_missing_button.parent is not None
            self.style_missing_price_button()
            self.layout_collapsible(self.binder_header, self.binder_search, self.binder_filters,
                                    self.binder_search_open, self.binder_filters_open)
            self.binder_limit = state["limit"]
            if needs_fill:
                self.fill_binder()
            Clock.schedule_once(lambda dt: setattr(self.binder_grid.parent, "scroll_y", state["scroll"]), 0)
        return True

    def begin_progress(self, text, determinate=False):
        self.progress_active, self.progress_text = True, text
        self.progress_value = 0 if determinate else None
        self.animate_progress(0)

    def end_progress(self):
        self.progress_active = False
        self.status.text = ""
        self.animate_progress(0)

    def animate_progress(self, dt):
        if not hasattr(self, "progress_bar"):
            return
        self.progress_bar.opacity = 1 if self.progress_active else 0
        self.progress_bar.height = dp(8) if self.progress_active else 0
        if self.progress_active:
            self.progress_bar.value = (self.progress_value if self.progress_value is not None
                                       else (self.progress_bar.value + 4) % 100)
            self.status.text = (self.progress_text + "\n" + self.t("keep_screen_on")
                                if self.catalog_download_active else self.progress_text)
        self.update_footer()

    def update_footer(self, *_):
        if not hasattr(self, "footer"):
            return
        status_height = dp(70 if self.catalog_download_active else 32) if self.status.text else 0
        self.footer.height = status_height + (dp(12) if self.progress_active else 0)
        self.status.height = status_height
        visible = bool(self.status.text or self.progress_active)
        if visible and self.footer.parent is None:
            self.root_box.add_widget(self.footer)
        elif not visible and self.footer.parent is not None:
            self.root_box.remove_widget(self.footer)

    def notify(self, text):
        if getattr(self, "notice_event", None):
            self.notice_event.cancel()
        self.status.text = text
        if text:
            target = self.status
            self.notice_event = Clock.schedule_once(
                lambda dt: setattr(target, "text", "") if not self.progress_active else None, 6)

    def navigate(self, page, remember=True):
        if getattr(self, "search_event", None):
            self.search_event.cancel()
        if remember and page != self.page:
            self.history.append(self.capture_page())
        self.page = page
        self.render()

    def render(self):
        self.download_buttons = []
        root = self.root_box
        root.clear_widgets()
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(48))
        heading = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        brand_box = BoxLayout(size_hint_x=None, padding=[dp(20), 0, dp(12), 0])
        frame(brand_box, color=(*ACCENT[:3], .7), fill=PANEL, accent=False)
        brand = label(">NightCityBinder_", 42, 19, (244 / 255, 244 / 255, 68 / 255, 1), font_name=MONO)
        brand_box.add_widget(brand)
        heading.add_widget(brand_box)
        heading.add_widget(Widget())
        def fit_brand(*_):
            available = max(dp(80), heading.width - dp(64))
            measure = CoreLabel(text=brand.text, font_name=MONO, font_size=dp(19))
            measure.refresh()
            natural = measure.texture.size[0]
            scale = min(1, (available - dp(34)) / max(1, natural))
            brand.font_size = dp(19) * scale
            brand_box.width = min(available, natural * scale + dp(34))
        heading.bind(width=fit_brand)
        fit_brand()
        menu = MenuButton(text="", background_normal="", background_color=PANEL,
                          size_hint_y=None, height=dp(42))
        menu.bind(on_release=lambda *_: self.show_menu())
        menu.size_hint_x = None
        menu.width = dp(44)
        heading.add_widget(menu)
        header.add_widget(heading)
        root.add_widget(header)
        self.body_layer = ClippedFloatLayout()
        self.body = BoxLayout(orientation="vertical", spacing=dp(10), pos_hint={"x": 0, "y": 0})
        self.body_layer.add_widget(self.body)
        root.add_widget(self.body_layer)
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=0, opacity=0)
        self.footer = BoxLayout(orientation="vertical", size_hint_y=None, height=0)
        self.footer.add_widget(self.progress_bar)
        self.status = label("", height=0, size=12, color=CYAN)
        self.footer.add_widget(self.status)
        self.status.bind(text=self.update_footer)
        self.animate_progress(0)
        if self.page == "binder":
            self.render_binder()
        elif self.page == "catalog":
            self.render_catalog()
        elif self.page == "settings":
            self.render_settings()
        elif self.page == "detail":
            self.render_detail()
        if self.page == "catalog" or (self.page == "binder" and self.binder_id == "mine"):
            scanner = ScanButton()
            scanner.bind(on_release=lambda *_: self.scan())
            layer = self.body_layer

            def position(*_):
                scanner.pos = (layer.right - scanner.width, layer.y + dp(8))

            layer.bind(pos=position, size=position)
            layer.add_widget(scanner)
            position()
        if self.page == "binder":
            selector = BinderButton()
            selector.bind(on_release=lambda *_: self.show_binder_picker())
            binder_layer = self.body_layer
            bottom_offset = dp(72 if self.binder_id == "mine" else 8)

            def position_binder(*_):
                selector.pos = (binder_layer.right - selector.width, binder_layer.y + bottom_offset)

            binder_layer.bind(pos=position_binder, size=position_binder)
            binder_layer.add_widget(selector)
            position_binder()

    def show_menu(self):
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        popup = Popup(title=self.t("menu"), content=content, size_hint=(0.88, None), height=dp(300))

        def choose(page):
            popup.dismiss()
            self.navigate(page)

        for page in ("binder", "catalog", "settings"):
            item = button(self.t(page), lambda p=page: choose(p))
            item.font_name = MONO
            if self.page == page:
                item.background_color, item.color = CYAN, BG
            content.add_widget(item)
        content.add_widget(button(self.t("close"), popup.dismiss))
        popup.open()
        return popup

    def scroller(self, parent, columns=1, dismiss_filters=None):
        scroll = FilterDismissScrollView(dismiss_filters=dismiss_filters, do_scroll_x=False,
                                        bar_color=CYAN, bar_inactive_color=(*ACCENT[:3], .35),
                                        bar_width=dp(2))
        grid = GridLayout(cols=columns, size_hint_y=None, spacing=dp(10))
        if columns == 2:
            grid.col_force_default = True
            grid.bind(width=lambda obj, width: setattr(obj, "col_default_width", (width - dp(10)) / 2))
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)
        parent.add_widget(scroll)
        return grid

    @staticmethod
    def bring_header_forward(header):
        """Paint the opaque filter header after scrolling tiles without changing layout."""
        canvas = header.parent.canvas
        canvas.remove(header.canvas)
        canvas.add(header.canvas)

    def binder_names(self):
        return {b["id"]: (self.t("binder") if b["id"] == "mine" else b["name"]) for b in self.store.binders()}

    def catalog_missing_notice(self):
        notice = BoxLayout(orientation="vertical", size_hint_y=None,
                           padding=dp(12), spacing=dp(8))
        notice.bind(minimum_height=notice.setter("height"))
        frame(notice, color=YELLOW, fill=PANEL, accent=False)
        notice.add_widget(label(self.t("catalog_missing_title"), 30, 16, YELLOW,
                                adaptive=True, bold=True))
        notice.add_widget(label(self.t("catalog_missing_body"), 90, 13,
                                adaptive=True))
        notice.add_widget(button(self.t("go_to_settings"),
                                 lambda: self.navigate("settings"), height=42))
        return notice

    @staticmethod
    def layout_collapsible(container, search, filters, search_open, filters_open, trailing=None):
        for widget in (search, filters, trailing):
            if widget is None:
                continue
            if widget.parent is container:
                container.remove_widget(widget)
        if search_open:
            container.add_widget(search)
        if filters_open:
            container.add_widget(filters)
        if trailing is not None:
            container.add_widget(trailing)

    def render_binder(self):
        names = self.binder_names()
        active_name = names[self.binder_id]
        rows = self.store.entries(self.binder_id)
        cache_key = (self.binder_id, self.language, active_name, id(self.catalog.cards),
                     tuple((row["card"], row["finish"], row["condition"], row["quantity"])
                           for row in rows))
        if self.binder_body is not None and self.binder_cache_key == cache_key:
            self.body_layer.remove_widget(self.body)
            if self.binder_body.parent is not None:
                self.binder_body.parent.remove_widget(self.binder_body)
            self.body = self.binder_body
            self.body_layer.add_widget(self.body)
            self.refresh_binder_prices()
            return
        self.binder_body = self.body
        self.binder_cache_key = cache_key
        if self.binder_id != "mine":
            active_name += " · " + self.binder_id[:6]
        header = BoxLayout(orientation="vertical", size_hint_y=None, spacing=0)
        solid_background(header)
        header.bind(minimum_height=header.setter("height"))
        self.binder_header = header
        self.body.add_widget(header)
        name_row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(6))
        name_area = BoxLayout(size_hint_x=.42)
        name_label = label(active_name, 30, 13, CYAN, font_name=MONO, shorten=True, shorten_from="right")
        name_area.add_widget(name_label)
        if self.binder_id != "mine":
            pencil = PencilButton()
            pencil.height = dp(30)
            pencil.bind(on_release=lambda *_: self.rename_binder())
            name_area.add_widget(pencil)
        name_row.add_widget(name_area)
        self.binder_total_label = label("", 30, 12, VALUE_GREEN, halign="right")
        self.binder_total_label.size_hint_x = .58
        name_row.add_widget(self.binder_total_label)
        def fit_value(*_):
            if not self.binder_total_label.text or self.binder_total_label.width <= 0:
                return
            measure = CoreLabel(text=self.binder_total_label.text, font_size=dp(12))
            measure.refresh()
            self.binder_total_label.font_size = min(dp(12), dp(12) * self.binder_total_label.width / max(1, measure.texture.size[0]))
        self.binder_total_label.bind(text=fit_value, width=fit_value)
        header.add_widget(name_row)
        stats = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        stats.add_widget(label(self.t("stats", unique=len(rows), total=sum(r["quantity"] for r in rows)),
                               40, 14, CYAN))
        self.binder_value_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self.binder_value_box.bind(minimum_height=self.binder_value_box.setter("height"))
        self.binder_value_box.bind(height=lambda obj, height: setattr(stats, "height", max(dp(40), height)))
        self.binder_missing_only = False
        self.binder_missing_button = MissingPriceButton()
        self.binder_missing_button.bind(on_release=lambda *_: self.toggle_missing_prices())
        self.binder_fx_label = label(self.t("fx_missing"), 0, 11, MUTED, halign="right", adaptive=True)
        stats.add_widget(self.binder_value_box)
        search_toggle = SearchButton()
        stats.add_widget(search_toggle)
        filter_toggle = FilterButton()
        stats.add_widget(filter_toggle)
        header.add_widget(stats)
        search = field(self.t("search"))
        self.binder_search = search
        self.binder_search_open = False
        self.binder_filters_open = False
        self.binder_filters = CardFilterPanel(self.t, [self.resolve_card(row["card"]) for row in rows],
                                              lambda: self.fill_binder(reset=True))

        def toggle_search(*_):
            self.binder_search_open = not self.binder_search_open
            if not self.binder_search_open:
                search.focus = False
                search.text = ""  # A hidden field must not leave an invisible filter active.
            self.layout_collapsible(header, search, self.binder_filters,
                                    self.binder_search_open, self.binder_filters_open)
            if self.binder_search_open:
                search.focus = True

        def dismiss_filters(touch=None):
            if not self.binder_filters_open or (touch is not None and header.collide_point(*touch.pos)):
                return False
            self.binder_filters_open = False
            self.layout_collapsible(header, search, self.binder_filters,
                                    self.binder_search_open, self.binder_filters_open)
            return True

        def toggle_filters(*_):
            if not dismiss_filters():
                self.binder_filters_open = True
                self.layout_collapsible(header, search, self.binder_filters,
                                        self.binder_search_open, self.binder_filters_open)

        search_toggle.bind(on_release=toggle_search)
        filter_toggle.bind(on_release=toggle_filters)
        self.update_binder_value()
        if self.binder_id != "mine":
            imported_actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            imported_actions.add_widget(label(self.t("readonly"), 44, 12, MUTED))
            delete = button(self.t("delete_binder_short"), self.delete_binder, height=44)
            delete.size_hint_x = None
            delete.width = dp(118)
            delete.background_color = RED
            imported_actions.add_widget(delete)
            self.body.add_widget(imported_actions)
        if not self.catalog.cards:
            self.body.add_widget(self.catalog_missing_notice())
        self.binder_grid = self.scroller(self.body, 2, dismiss_filters=dismiss_filters)
        self.bring_header_forward(header)
        # Last row can scroll clear of the floating controls.
        self.binder_grid.padding = [0, 0, 0, dp(136 if self.binder_id == "mine" else 72)]
        self.binder_rows = rows
        self.binder_limit = 12
        search.bind(text=lambda *_: self.fill_binder(reset=True))
        self.fill_binder()
        self.binder_price_data = self.prices.data

    def fill_binder(self, reset=False):
        if reset:
            self.binder_limit = 12
        grid = self.binder_grid
        grid.clear_widgets()
        self.binder_price_labels = []
        query = normalized(self.binder_search.text)
        selected = self.binder_filters.selection()
        self.binder_filtered = [r for r in self.binder_rows
                                if query in normalized(r["card"].name + " " + r["card"].number)
                                and card_matches_filters(self.resolve_card(r["card"]), selected)
                                and (not self.binder_missing_only or
                                     self.prices.quote(r["card"].printing_id, r["finish"]) is None)]
        if not self.binder_filtered:
            grid.cols = 1
            grid.col_force_default = False
            grid.add_widget(label(self.t("empty") if not self.binder_rows else self.t("no_match"), 90, 18))
            if not self.binder_rows and self.catalog.cards:
                grid.add_widget(label(self.t("empty_hint"), 60, 14, MUTED))
            return
        grid.cols = 2
        grid.col_force_default = True
        for row in self.binder_filtered[:self.binder_limit]:
            self.binder_tile(grid, row)
        self.add_binder_more()

    def add_binder_more(self):
        self.binder_more = None
        if len(self.binder_filtered) > self.binder_limit:
            self.binder_more = button(self.t("more"), self.show_more_binder)
            self.binder_grid.add_widget(self.binder_more)

    def show_more_binder(self):
        if self.binder_more is not None:
            self.binder_grid.remove_widget(self.binder_more)
        start = self.binder_limit
        self.binder_limit = min(len(self.binder_filtered), start + 12)
        for row in self.binder_filtered[start:self.binder_limit]:
            self.binder_tile(self.binder_grid, row)
        self.add_binder_more()

    def rename_binder(self):
        binder_id = self.binder_id
        if binder_id == "mine":
            return
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        name_input = field(text=self.binder_names()[binder_id])
        content.add_widget(name_input)
        error = label("", 50, 12, ACCENT)
        content.add_widget(error)
        popup = Popup(title=self.t("rename_binder"), content=content,
                      size_hint=(0.92, None), height=dp(290))

        def save():
            try:
                self.store.rename_binder(binder_id, name_input.text)
            except ValueError:
                error.text = self.t("binder_name_invalid")
                return
            popup.dismiss()
            self.render()

        content.add_widget(button(self.t("save"), save, True))
        content.add_widget(button(self.t("cancel"), popup.dismiss))
        popup.open()
        return popup

    def show_binder_picker(self):
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        choices = self.scroller(content)
        binders = self.binder_names()
        popup = BinderPickerPopup(title=self.t("choose_binder"), content=content,
                                  size_hint=(0.94, None), height=Window.height - dp(76))
        # Keep the binder buttons clear of the ScrollView's scrollbar.
        choices.padding = [0, 0, dp(18), 0]

        def choose(binder_id):
            popup.dismiss()
            self.binder_id = binder_id
            self.render()

        def launch(action):
            popup.dismiss()
            Clock.schedule_once(lambda dt: action(), 0.1)

        for binder_id, name in binders.items():
            text = name if binder_id == "mine" else name + " · " + binder_id[:6]
            item = button(text, lambda key=binder_id: choose(key), height=60)
            item.font_size = dp(13)
            item.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0] - dp(16), None)))
            if binder_id == self.binder_id:
                item.background_color, item.color = CYAN, BG
            choices.add_widget(item)
        file_actions = BoxLayout(size_hint_y=None, height=dp(178), spacing=dp(8))
        own = BoxLayout(orientation="vertical", spacing=dp(6))
        own.add_widget(label(self.t("binder"), 24, 12, CYAN, halign="center"))
        own.add_widget(button(self.t("export_backup"),
                              lambda: launch(lambda: self.export("mine")), height=68))
        own.add_widget(button(self.t("import_backup"),
                              lambda: launch(lambda: self.import_binder(restore=True)), height=68))
        shared = BoxLayout(orientation="vertical", spacing=dp(6))
        shared.add_widget(label(self.t("share_binders"), 24, 12, CYAN, halign="center"))
        shared.add_widget(button(self.t("export"), lambda: launch(self.export), height=68))
        shared.add_widget(button(self.t("import"), lambda: launch(self.import_binder), height=68))
        for column in (own, shared):
            for action in column.children[:2]:
                action.font_size = dp(11)
            file_actions.add_widget(column)
        content.add_widget(file_actions)
        content.add_widget(label(self.t("transfer_hint"), 42, 11, MUTED, adaptive=True))
        content.add_widget(button(self.t("close"), popup.dismiss))
        popup.open()
        popup._align_center()
        return popup

    def binder_tile(self, grid, row):
        card = self.resolve_card(row["card"])
        tile, art, status = self.card_tile(card, lambda: self.show_detail(card, row))
        path = self.catalog.image_path(card)
        if path.exists():
            art.source, art.opacity = str(path), 1
        else:
            status.text = card.card_type.upper() or self.t("no_art")
        price = label(self.binder_price(card, row["finish"]), 22, 12, CYAN, halign="center")
        self.binder_price_labels.append((price, card, row["finish"]))
        tile.add_widget(price)
        tile.add_widget(label(f"#{card.number}  ·  {row['quantity']}×  ·  {self.t(row['finish'])}",
                              18, 10, MUTED, halign="center"))
        tile.add_widget(label(CONDITION_NAMES[row["condition"]], 18, 10, MUTED, halign="center"))
        grid.add_widget(tile)

    def card_tile(self, card, callback):
        """Shared compact name/art layout; metadata stays directly below the art."""
        tile = CardTile(orientation="vertical", size_hint_y=None, padding=dp(6), spacing=dp(2))
        tile.bind(minimum_height=tile.setter("height"))
        tile.bind(on_release=lambda *_: callback())
        title = label(card.name, 28, 12, CYAN, bold=True, halign="center",
                      shorten=True, max_lines=1, shorten_from="right")
        def fit_title(*_):
            available = max(1, title.width - dp(4))
            measure = CoreLabel(text=card.name, font_size=dp(12), bold=True)
            measure.refresh()
            title.font_size = max(dp(8), min(dp(12), dp(12) * available / max(1, measure.texture.size[0])))
        title.bind(width=fit_title)
        tile.add_widget(title)
        Clock.schedule_once(fit_title, 0)
        art_box = FloatLayout(size_hint_y=None, height=dp(170))
        art_box.bind(width=lambda obj, width: setattr(obj, "height", min(dp(170), width * 88 / 63)))
        art = AsyncImage(fit_mode="contain", opacity=0, pos_hint={"x": 0, "y": 0})
        status = label("", 32, 10, MUTED, halign="center")
        status.pos_hint = {"x": 0, "center_y": .5}
        art_box.add_widget(art)
        art_box.add_widget(status)
        tile.add_widget(art_box)
        return tile, art, status

    def binder_price(self, card, finish):
        quote = self.prices.quote(card.printing_id, finish)
        if quote is None:
            return self.t("price_unavailable_short")
        currency = self.currency
        try:
            value = self.fx.convert(quote["amount"], quote["currency"], currency)
        except (KeyError, ValueError):
            currency, value = quote["currency"], quote["amount"]
        return self.t("price_per_copy", value=value, currency=currency)

    def refresh_binder_prices(self):
        changed = getattr(self, "binder_price_data", None) is not self.prices.data
        self.binder_price_data = self.prices.data
        was_missing_only = self.binder_missing_only
        self.update_binder_value()
        if changed and was_missing_only:
            self.fill_binder(reset=True)
        else:
            for target, card, finish in getattr(self, "binder_price_labels", []):
                target.text = self.binder_price(card, finish)

    def style_missing_price_button(self):
        self.binder_missing_button.background_color = CYAN if self.binder_missing_only else BG
        self.binder_missing_button.color = BG if self.binder_missing_only else ACCENT

    def toggle_missing_prices(self):
        self.binder_missing_only = not self.binder_missing_only
        self.style_missing_price_button()
        self.fill_binder(reset=True)
        self.binder_grid.parent.scroll_y = 1

    def update_binder_value(self):
        result = self.prices.binder_value(self.store.entries(self.binder_id), self.fx, self.currency)
        amount = result["amount"]
        self.binder_total_label.text = self.t("binder_value") + " " + (f"{amount:.2f} {result['currency']}" if amount is not None else "—")
        self.binder_missing_button.text = self.t("cards_without_prices", count=result["missing"])
        if result["missing"] == 0:
            self.binder_missing_only = False
        self.style_missing_price_button()
        for widget, visible in ((self.binder_missing_button, result["missing"] > 0),
                                (self.binder_fx_label, result["fx_missing"])):
            if visible and widget.parent is None:
                self.binder_value_box.add_widget(widget)
            elif not visible and widget.parent is not None:
                self.binder_value_box.remove_widget(widget)

    def resolve_card(self, card):
        return next((c for c in self.catalog.cards if c.printing_id == card.printing_id), card)

    def render_catalog(self):
        if self.catalog_body is not None and self.catalog_cache_language == self.language:
            self.body_layer.remove_widget(self.body)
            if self.catalog_body.parent is not None:
                self.catalog_body.parent.remove_widget(self.catalog_body)
            self.body = self.catalog_body
            self.body_layer.add_widget(self.body)
            return
        self.catalog_body = self.body
        self.catalog_cache_language = self.language
        catalog_header = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        catalog_header.bind(minimum_height=catalog_header.setter("height"))
        solid_background(catalog_header)
        self.catalog_header = catalog_header
        controls_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        controls_row.add_widget(label(self.t("catalog"), 40, 14, CYAN, font_name=MONO))
        search_toggle = SearchButton()
        filter_toggle = FilterButton()
        controls_row.add_widget(search_toggle)
        controls_row.add_widget(filter_toggle)
        catalog_header.add_widget(controls_row)
        self.search_input = field(self.t("search"))
        self.search_input.bind(text=lambda *_: self.queue_search())
        self.catalog_search_open = False
        self.catalog_filters_open = False
        self.catalog_filters = CardFilterPanel(self.t, self.catalog.cards, self.filter_catalog)

        def toggle_search(*_):
            self.catalog_search_open = not self.catalog_search_open
            if not self.catalog_search_open:
                self.search_input.focus = False
                self.search_input.text = ""
            self.layout_collapsible(catalog_header, self.search_input, self.catalog_filters,
                                    self.catalog_search_open, self.catalog_filters_open, self.result_count)
            if self.catalog_search_open:
                self.search_input.focus = True

        def dismiss_filters(touch=None):
            if not self.catalog_filters_open or (touch is not None and catalog_header.collide_point(*touch.pos)):
                return False
            self.catalog_filters_open = False
            self.layout_collapsible(catalog_header, self.search_input, self.catalog_filters,
                                    self.catalog_search_open, self.catalog_filters_open, self.result_count)
            return True

        def toggle_filters(*_):
            if not dismiss_filters():
                self.catalog_filters_open = True
                self.layout_collapsible(catalog_header, self.search_input, self.catalog_filters,
                                        self.catalog_search_open, self.catalog_filters_open, self.result_count)

        search_toggle.bind(on_release=toggle_search)
        filter_toggle.bind(on_release=toggle_filters)
        self.result_count = label("", 22, 12, MUTED)
        catalog_header.add_widget(self.result_count)
        self.body.add_widget(catalog_header)
        if not self.catalog.cards:
            self.body.add_widget(self.catalog_missing_notice())
        self.result_grid = self.scroller(self.body, 2, dismiss_filters=dismiss_filters)
        self.result_limit = 12
        self.search_event = None
        self.fill_catalog()
        actions = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(8), padding=[0, 0, dp(72), dp(8)])
        actions.add_widget(button(self.t("refresh_catalog_local"), self.reload_catalog, height=50))
        self.body.add_widget(actions)
        self.bring_header_forward(catalog_header)

    def queue_search(self):
        if self.search_event:
            self.search_event.cancel()
        self.result_limit = 12
        self.search_event = Clock.schedule_once(lambda dt: self.fill_catalog(), 0.2)

    def filter_catalog(self):
        if self.search_event:
            self.search_event.cancel()
        self.result_limit = 12
        self.fill_catalog(self.catalog_candidates)

    def fill_catalog(self, candidates=None, local_only=False):
        if self.page != "catalog":
            return
        self.catalog_candidates = candidates
        self.catalog_local_only = local_only
        self.result_grid.clear_widgets()
        generation = object()
        self.art_generation = generation
        query = normalized(self.search_input.text)
        results = (
            candidates
            if candidates is not None
            else [c for c in self.catalog.cards if query in normalized(c.name + " " + c.number + " " + c.set_name)]
        )
        selected = self.catalog_filters.selection()
        results = [card for card in results
                   if query in normalized(card.name + " " + card.number + " " + card.set_name)
                   and card_matches_filters(card, selected)]
        self.catalog_results = results
        self.result_count.text = self.t("results", count=len(results))
        self.result_grid.cols = 2 if results else 1
        self.result_grid.col_force_default = bool(results)
        if not results and self.catalog.cards:
            self.result_grid.add_widget(
                label(self.t("no_match"), 120, 17)
            )
        self.append_catalog_page(0, min(self.result_limit, len(results)), generation, local_only)
        self.add_catalog_more()

    def append_catalog_page(self, start, stop, generation, local_only):
        pending = []
        for card in self.catalog_results[start:stop]:
            item, art, art_status = self.card_tile(card, lambda c=card: self.show_detail(c))
            path = self.catalog.image_path(card)
            if path.is_file() and path.stat().st_size > 0:
                art.source = str(path)
                art.opacity = 1
            elif card.image_url and not local_only:
                art_status.text = self.t("loading_art")
                pending.append((card, art, art_status))
            else:
                art_status.text = self.t("art_not_cached") if local_only and card.image_url else self.t("no_art")
            item.add_widget(label(f"#{card.number} · {card.language.upper()}", 18, 10, MUTED, halign="center"))
            self.result_grid.add_widget(item)

        def load_art():
            for card, art, status in pending:
                if self.art_generation is not generation:
                    break
                try:
                    path = self.catalog.download_image(card)
                except Exception:
                    path = ""

                def apply(dt, art=art, status=status, path=path):
                    if self.art_generation is generation:
                        art.source = path
                        art.opacity = 1 if path else 0
                        status.text = "" if path else self.t("no_art")

                Clock.schedule_once(apply)

        if pending and not local_only:
            threading.Thread(target=load_art, daemon=True).start()

    def add_catalog_more(self):
        self.catalog_more = None
        if len(self.catalog_results) > self.result_limit:
            self.catalog_more = button(self.t("more"), self.show_more_catalog)
            self.result_grid.add_widget(self.catalog_more)

    def show_more_catalog(self):
        if self.catalog_more is not None:
            self.result_grid.remove_widget(self.catalog_more)
        start = self.result_limit
        self.result_limit = min(len(self.catalog_results), start + 12)
        self.append_catalog_page(start, self.result_limit, self.art_generation, self.catalog_local_only)
        self.add_catalog_more()

    def scan(self):
        if self.busy:
            self.notify(self.t("busy"))
            return
        if platform == "android":
            self.busy = True
            self.begin_progress(self.t("opening_scanner"))
            try:
                self.bridge.request_camera(self.camera_ready)
            except Exception:
                self.busy = False
                self.end_progress()
                self.notify(self.t("scan_fail"))
            return
        self.start_scan()

    def camera_ready(self, granted):
        self.busy = False
        self.end_progress()
        if granted:
            self.start_scan()
        else:
            self.camera_denied()

    def camera_denied(self):
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(12))
        content.add_widget(label(self.t("camera_permission"), 110, 15))
        popup = Popup(title=self.t("scan"), content=content, size_hint=(0.92, None), height=dp(290))

        def settings():
            popup.dismiss()
            self.bridge.open_settings()

        content.add_widget(button(self.t("app_settings"), settings))
        content.add_widget(button(self.t("cancel"), popup.dismiss))
        popup.open()

    def start_scan(self):
        if not self.catalog.cards:
            self.navigate("catalog")
            self.notify(self.t("catalog_empty"))
            return
        if platform != "android":
            self.navigate("catalog")
            self.notify(self.t("scan_desktop"))
            self.search_input.focus = True
            return
        try:
            self.busy = True
            self.begin_progress(self.t("opening_scanner"))
            self.bridge.launch(AndroidBridge.SCAN, self.scan_result, self.language)
        except Exception:
            self.busy = False
            self.end_progress()
            self.notify(self.t("scan_fail"))

    def scan_result(self, text, error):
        self.busy = False
        self.end_progress()
        if error == "camera_permission":
            self.camera_denied()
        elif error:
            self.notify(self.t("scan_fail"))
        elif text is not None:
            self.navigate("catalog")
            if isinstance(text, dict):
                ranked = match_cards(text["text"], self.catalog.cards, limit=100,
                                     number_text=text["number_text"])
            else:
                ranked = match_cards(text, self.catalog.cards, limit=100)
            self.fill_catalog([card for score, card in ranked])
            self.notify(self.t("choose" if ranked else "no_match"))

    def show_detail(self, card, entry=None):
        self.history.append(self.capture_page())
        if entry is None:
            owned = [r for r in self.store.entries() if r["card"].printing_id == card.printing_id]
            self.owned_default = owned[0] if owned else None
        else:
            self.owned_default = None
        self.detail_card, self.detail_entry = card, entry
        self.previous_page = "binder" if entry else "catalog"
        self.navigate("detail", remember=False)

    def render_detail(self):
        card, entry = self.detail_card, self.detail_entry
        self.quantity_action = None
        self.edit_action = None
        default = entry or getattr(self, "owned_default", None)
        back_row = BoxLayout(size_hint_y=None, height=dp(34), padding=[0, 0, dp(16), 0])
        back_row.add_widget(button("‹  " + self.t("back"), self.go_back, height=34))
        self.body.add_widget(back_row)
        content = self.scroller(self.body)
        content.padding = [0, 0, dp(16), 0]
        content.add_widget(label(card.name, 44, 21, INK, bold=True))
        content.add_widget(
            label(f"{card.set_name}\n#{card.number} · {card.rarity} · {card.language.upper()}", 52, 13, MUTED)
        )
        owned_count = sum(r["quantity"] for r in self.store.entries() if r["card"].printing_id == card.printing_id)
        content.add_widget(label(self.t("owned_count", count=owned_count), 30, 12, CYAN))
        art = Image(size_hint_y=None, height=dp(285), fit_mode="contain")
        content.add_widget(art)
        art_status = label(self.t("loading_art"), 24, 11, MUTED)
        content.add_widget(art_status)
        path = self.catalog.image_path(card)
        if path.exists():
            art.source, art_status.text = str(path), ""
        elif card.image_url:

            def download():
                try:
                    path = self.catalog.download_image(card)

                    def apply(dt):
                        art.source, art_status.text = path, ""

                    Clock.schedule_once(apply)
                except Exception:
                    Clock.schedule_once(lambda dt: setattr(art_status, "text", self.t("no_art")))

            threading.Thread(target=download, daemon=True).start()
        else:
            art_status.text = self.t("no_art")
        content.add_widget(label(self.t("finish_hint"), 46, 12, MUTED))
        form = GridLayout(cols=2, size_hint_y=None, height=dp(88), spacing=dp(6))
        form.add_widget(label(self.t("finish"), 30, 13, MUTED))
        form.add_widget(label(self.t("condition"), 30, 13, MUTED))
        self.finish_select = Spinner(
            text=self.t(default["finish"] if default else "unknown"),
            values=[self.t(f) for f in FINISHES],
            background_normal="",
            background_color=PANEL,
        )
        self.condition_select = Spinner(
            text=CONDITION_NAMES[default["condition"] if default else "NM"],
            values=list(CONDITION_NAMES.values()), background_normal="", background_color=PANEL,
            font_size=dp(12)
        )
        form.add_widget(self.finish_select)
        form.add_widget(self.condition_select)
        content.add_widget(form)
        self.price_label = label("", 94, 14, CYAN, adaptive=True)
        content.add_widget(self.price_label)
        content.add_widget(button(self.t("refresh_prices_local"), self.reload_prices))
        content.add_widget(button(self.t("price_history"), self.show_price_history))
        self.finish_select.bind(text=lambda *_: self.finish_changed())
        self.update_price()
        readonly = entry is not None and self.binder_id != "mine"
        if readonly:
            self.finish_select.disabled = self.condition_select.disabled = True
            self.body.add_widget(label(self.t("readonly"), 36, 13, MUTED))
            return
        if entry is not None:
            edit_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8),
                                 padding=[0, 0, dp(16), 0])
            self.edit_quantity = field(text=str(entry["quantity"]))
            self.edit_quantity.input_filter = "int"
            edit_row.add_widget(self.edit_quantity)
            self.edit_action = button(self.t("save_changes"), self.save_entry, True, 50)
            edit_row.add_widget(self.edit_action)
            content.add_widget(label(self.t("edit_owned"), 28, 12, MUTED))
            content.add_widget(edit_row)
            self.edit_quantity.bind(text=lambda *_: self.update_edit_action())
            self.update_edit_action()
        bottom = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8), padding=[0, 0, dp(16), 0])
        self.quantity = field(text="1")
        self.last_quantity = "1"
        self.quantity.size_hint_x = 0.45

        def adjust(amount):
            current = int(self.quantity.text) if self.quantity.text not in ("", "-") else 0
            value = min(999999, max(-999999, current + amount))
            self.quantity.text = str(value)

        for text, callback in (("−", lambda: adjust(-1)), ("+", lambda: adjust(1))):
            b = button(text, callback, height=50)
            b.size_hint_x = 0.3
            if text == "+":
                bottom.add_widget(self.quantity)
            bottom.add_widget(b)
        self.quantity_action = button(self.t("add"), self.add, True, 50)
        bottom.add_widget(self.quantity_action)
        self.quantity.bind(text=self.update_quantity_action)
        self.body.add_widget(bottom)
        self.update_quantity_action(self.quantity, self.quantity.text)

    def finish_changed(self):
        self.update_price()
        if self.quantity_action is not None:
            self.update_quantity_action(self.quantity, self.quantity.text)
        if self.edit_action is not None:
            self.update_edit_action()

    def update_edit_action(self):
        if self.edit_action is not None:
            text = self.edit_quantity.text
            self.edit_action.disabled = (not text.isdigit() or not 1 <= int(text) <= 999999
                                         or self.selected_finish() == "unknown")

    def save_entry(self):
        entry = self.detail_entry
        if entry is None or self.binder_id != "mine":
            return
        try:
            quantity = int(self.edit_quantity.text)
            condition = next(code for code, name in CONDITION_NAMES.items()
                             if name == self.condition_select.text)
            self.store.update_entry(self.detail_card, entry["finish"], entry["condition"],
                                    quantity, self.selected_finish(), condition)
        except (ValueError, OverflowError, sqlite3.IntegrityError):
            self.notify(self.t("edit_invalid"))
            return
        self.history = [state for state in self.history if state["page"] != "detail"]
        self.navigate("binder", remember=False)
        self.notify(self.t("edit_saved"))

    def update_quantity_action(self, obj, value):
        if not re.fullmatch(r"-?[0-9]{0,6}", value):
            obj.text = self.last_quantity
            return
        self.last_quantity = value
        count = int(value) if value not in ("", "-") else 0
        self.quantity_action.text = self.t("delete" if count < 0 else "add")
        self.quantity_action.background_color = RED if count < 0 else YELLOW
        self.quantity_action.color = INK if count < 0 else BG
        self.quantity_action.disabled = count == 0 or (count > 0 and self.selected_finish() == "unknown")

    def selected_finish(self):
        return next(f for f in FINISHES if self.t(f) == self.finish_select.text)

    def update_price(self):
        q = self.prices.quote(self.detail_card.printing_id, self.selected_finish())
        if q is None:
            reason = self.prices.data.get("match_status", {}).get(self.detail_card.printing_id, "not_loaded")
            if self.selected_finish() == "unknown":
                reason = "finish"
            self.price_label.text = self.t("price") + "\n" + self.t("price_" + reason)
            return
        try:
            value = self.fx.convert(q["amount"], q["currency"], self.currency)
            lines = [
                f"{value} {self.currency} / szt." if self.language == "pl" else f"{value} {self.currency} / copy",
                self.t("price_date", **q),
                self.t("price_condition"),
            ]
            if q["currency"] != self.currency:
                lines.append(self.t("fx_date", date=self.fx.data["date"]))
        except (KeyError, ValueError):
            lines = [f"{q['amount']} {q['currency']}", self.t("price_date", **q), self.t("fx_missing")]
        if (date.today() - date.fromisoformat(q["date"])).days > 3:
            lines.append(self.t("price_stale"))
        self.price_label.text = "\n".join(lines)

    def refresh_prices(self, silent=False):
        if not self.catalog.cards:
            if not silent:
                self.notify(self.t("catalog_empty"))
            return
        if not self.begin_download("cardmarket"):
            return
        cards = {c.printing_id: c for c in self.catalog.cards}
        # Include saved cards in uniqueness checks; never assume a lone imported
        # variant is the only printing in its set when the full catalog is absent.
        for entry in self.store.entries():
            cards.setdefault(entry["card"].printing_id, entry["card"])

        def done(count):
            if self.page == "settings":
                self.render()
            elif self.page == "detail":
                self.update_price()
            elif self.page == "binder":
                self.refresh_binder_prices()
            if not silent:
                if self.prices.last_refresh_changed:
                    self.notify(self.t("prices_done", count=count, date=self.prices.data["guide_date"]))
                else:
                    self.notify(self.t("prices_up_to_date"))

        self.background(lambda: self.prices.refresh(list(cards.values())), done,
                        silent=silent, title="refresh_prices", error_key="prices_error")

    def show_price_history(self):
        printing, finish = self.detail_card.printing_id, self.selected_finish()
        observations = self.prices.history(printing, finish)
        layout = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        content = self.scroller(layout)
        content.add_widget(label(self.t("history_hint"), 100, 13, MUTED, adaptive=True))
        q = self.prices.quote(printing, finish)
        if q is None and observations:
            q = observations[-1]
            content.add_widget(label(self.t("history_last_known"), 64, 13, MUTED, adaptive=True))
        if q:
            content.add_widget(label(f"Cardmarket · Trend · {self.t(finish)}", 36, 15, CYAN))
            content.add_widget(label(self.t("price_date", **q), 44, 13, MUTED))
            # All rows use the SAME FX snapshot. Movement is calculated in EUR,
            # so exchange-rate movements do not masquerade as card price changes.
            currency = self.currency
            try:
                self.fx.convert(q["amount"], "EUR", currency)
            except (KeyError, ValueError):
                currency = "EUR"
                content.add_widget(label(self.t("fx_missing"), 50, 13, MUTED))
            if currency != "EUR":
                content.add_widget(label(self.t("history_fx", date=self.fx.data["date"]), 66, 12, MUTED))
            if len(observations) > 1:
                first, last = observations[0], observations[-1]
                initial = Decimal(str(first["amount"]))
                if initial > 0:
                    delta = (Decimal(str(last["amount"])) / initial - 1) * 100
                    content.add_widget(label(self.t("history_change", start=first["date"], end=last["date"],
                                                   change=f"{delta:+.2f}"), 60, 14, CYAN))
            for key, days in (("avg1", 1), ("avg7", 7), ("avg30", 30)):
                amount = q.get("averages", {}).get(key)
                if amount is not None:
                    value = self.fx.convert(amount, "EUR", currency)
                    content.add_widget(label(self.t("price_average", days=days, value=value, currency=currency),
                                             40, 13, MUTED))
            for row in reversed(observations):
                value = self.fx.convert(row["amount"], "EUR", currency)
                content.add_widget(label(f"{row['date']}    {value} {currency}", 34, 15))
        if len(observations) < 2:
            content.add_widget(label(self.t("history_short"), 90, 14, MUTED))
        popup = Popup(title=self.t("price_history"), content=layout, size_hint=(0.94, 0.85))
        layout.add_widget(button(self.t("back"), popup.dismiss))
        popup.open()
        return popup

    def add(self):
        try:
            count = int(self.quantity.text)
            condition = next(code for code, name in CONDITION_NAMES.items() if name == self.condition_select.text)
            if count < 0:
                self.remove_copies(-count, self.selected_finish(), condition)
                return
            if self.selected_finish() == "unknown":
                self.notify(self.t("finish_required"))
                return
            self.store.add(self.detail_card, count, self.selected_finish(), condition)
        except (ValueError, OverflowError, sqlite3.IntegrityError):
            self.notify(self.t("quantity") + ": 1–999999")
            return
        self.binder_id = "mine"
        self.history = [state for state in self.history if state["page"] != "detail"]
        self.navigate("binder", remember=False)
        self.notify(self.t("added", count=count))

    def remove_copies(self, count, finish, condition):
        card = self.detail_card
        available = sum(row["quantity"] for row in self.store.entries()
                        if row["card"].printing_id == card.printing_id
                        and row["finish"] == finish and row["condition"] == condition)
        if count > available:
            self.notify(self.t("not_enough_copies", count=available))
            return

        def remove():
            try:
                self.store.remove_many(card, count, finish, condition)
            except ValueError:
                self.notify(self.t("remove_failed"))
                return
            self.binder_id = "mine"
            self.history = [state for state in self.history if state["page"] != "detail"]
            self.navigate("binder", remember=False)
            self.notify(self.t("removed_copies", count=count))

        self.confirm(self.t("confirm_remove_copies", count=count) + "\n\n"
                     + self.t(finish) + " · " + CONDITION_NAMES[condition], remove)

    def render_settings(self):
        content = self.scroller(self.body)
        content.padding = [0, 0, dp(16), 0]
        content.add_widget(label(self.t("language"), 28, 13, MUTED))
        language = Spinner(
            text="Polski" if self.language == "pl" else "English",
            values=("Polski", "English"),
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=PANEL,
        )

        def change_language(_, value):
            self.language = "pl" if value == "Polski" else "en"
            self.store.setting("language", self.language)
            self.render()

        language.bind(text=change_language)
        content.add_widget(language)
        content.add_widget(label(self.t("currency"), 28, 13, MUTED))
        currency = Spinner(
            text=self.currency,
            values=("EUR", "USD", "PLN"),
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=PANEL,
        )

        def change_currency(_, value):
            self.currency = value
            self.store.setting("currency", value)

        currency.bind(text=change_currency)
        content.add_widget(currency)
        content.add_widget(button(self.t("refresh_fx"), self.refresh_fx))
        content.add_widget(label(self.t("fx_date", date=self.fx.data.get("date", "—")), 28, 12, MUTED))
        content.add_widget(self.download_button("netdeck", "sync", self.sync))
        content.add_widget(self.download_button("cardmarket", "refresh_prices", self.refresh_prices))
        content.add_widget(label(self.t("prices_status", date=self.prices.data.get("guide_date", "—"),
                                       count=len(self.prices.data.get("matches", {}))), 54, 13, CYAN))
        content.add_widget(label(self.t("price_hint"), 120, 13, MUTED, adaptive=True))
        content.add_widget(label(self.binder_names()[self.binder_id], 34, 17, CYAN))
        content.add_widget(button(self.t("clear_binder" if self.binder_id == "mine" else "delete_binder"),
                                  self.delete_binder))
        content.add_widget(button(self.t("delete_file"), self.delete_file))
        content.add_widget(label(self.t("storage_hint"), 90, 13, MUTED))
        content.add_widget(label(self.t("version"), 30, 13, CYAN))
        storage_label = label(self.t("storage_loading"), 72, 13, MUTED)
        content.add_widget(storage_label)
        self.measure_storage(storage_label)
        fan_notice = BoxLayout(orientation="vertical", size_hint_y=None,
                               padding=dp(14), spacing=dp(8))
        fan_notice.bind(minimum_height=fan_notice.setter("height"))
        frame(fan_notice, color=YELLOW, fill=PANEL, accent=False)
        fan_notice.add_widget(label(self.t("fan_title"), 30, 16, YELLOW,
                                    adaptive=True, bold=True))
        fan_notice.add_widget(label(self.t("fan_body"), 30, 13, adaptive=True))
        content.add_widget(fan_notice)
        content.add_widget(button(self.t("show_images"), self.show_images_folder))
        content.add_widget(button(self.t("privacy"), lambda: self.show_legal("privacy"), height=36))
        content.add_widget(button(self.t("credits"), lambda: self.show_legal("credits"), height=36))
        content.add_widget(button(self.t("licenses"), lambda: self.show_legal("licenses"), height=36))

    def show_legal(self, kind):
        filename = "python-notices.txt" if kind == "licenses" else f"{kind}-{self.language}.txt"
        text = (Path(__file__).resolve().parent.parent / "assets" / "legal" / filename).read_text(encoding="utf-8")
        layout = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        content = self.scroller(layout)
        if kind in ("privacy", "credits"):
            content.add_widget(button("Gacut · GitHub",
                                      lambda: self.open_external_link("https://github.com/Gacut"), height=40))
        if kind == "credits":
            content.add_widget(button("Codex",
                                      lambda: self.open_external_link("https://openai.com/pl-PL/codex/"), height=40))
        # Split before adding markup so a chunk never cuts a link tag in half.
        links = {"cdpr": "https://www.cdprojektred.com",
                 "weirdco": "https://www.weirdco.net/home",
                 "netdeck": "https://netdeck.gg", "cardmarket": "https://www.cardmarket.com",
                 "nbp": "https://nbp.pl"}
        replacements = {
            "CD PROJEKT RED — https://www.cdprojektred.com": ("cdpr", "CD PROJEKT RED"),
            "WeirdCo — https://www.weirdco.net/home": ("weirdco", "WeirdCo"),
            "Netdeck — https://netdeck.gg": ("netdeck", "Netdeck"),
            "Cardmarket — https://www.cardmarket.com": ("cardmarket", "Cardmarket"),
            "Narodowy Bank Polski — https://api.nbp.pl": ("nbp", "NBP.PL"),
        }
        blocks = text.splitlines() if kind in ("privacy", "credits") else [text]
        for block in blocks:
            if not block:
                content.add_widget(Widget(size_hint_y=None, height=dp(4)))
                continue
            chunks = (textwrap.wrap(block, width=1200, break_long_words=False,
                                    break_on_hyphens=False) if kind in ("privacy", "credits") else
                      [block[start:start + 1200] for start in range(0, len(block), 1200)])
            for part in chunks:
                if kind == "credits":
                    part = escape_markup(part)
                    for original, (ref, title) in replacements.items():
                        part = part.replace(original, f"[ref={ref}][color=5cebf2][u]{title}[/u][/color][/ref]")
                item = label(part, 24, 13, adaptive=True, markup=kind == "credits")
                if kind == "credits":
                    item.bind(on_ref_press=lambda _label, ref: self.open_external_link(links[ref]))
                content.add_widget(item)
        popup = Popup(title=self.t(kind), content=layout, size_hint=(.94, .9))
        layout.add_widget(button(self.t("close"), popup.dismiss, height=36))
        popup.open()
        return popup

    def open_external_link(self, url):
        if platform == "android":
            from android.runnable import run_on_ui_thread
            from jnius import autoclass

            @run_on_ui_thread
            def launch():
                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                intent = autoclass("android.content.Intent")
                uri = autoclass("android.net.Uri")
                activity.startActivity(intent(intent.ACTION_VIEW, uri.parse(url)))

            launch()
        else:
            import webbrowser
            webbrowser.open(url)

    def measure_storage(self, target):
        language = self.language

        def worker():
            try:
                size, count, catalog_size = storage_usage(self.data_dir)
                text = translate(language, "storage_sizes", images=format_bytes(size),
                                 count=count, catalog=format_bytes(catalog_size))
            except OSError:
                text = translate(language, "storage_error")
            Clock.schedule_once(lambda dt: setattr(target, "text", text), 0)

        threading.Thread(target=worker, daemon=True).start()

    def show_images_folder(self):
        path = self.data_dir / "images"
        path.mkdir(parents=True, exist_ok=True)
        if platform == "win":
            try:
                os.startfile(str(path.resolve()))
                return
            except OSError:
                pass  # Retain the in-app viewer if no file manager is available.
        self.images_folder_dialog(path)

    def show_image_diagnostics(self):
        report = json.dumps(self.catalog.image_diagnostics(), ensure_ascii=False, indent=2)
        layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        layout.add_widget(TextInput(text=report, readonly=True, font_size=dp(12),
                                    background_color=PANEL, foreground_color=INK))
        popup = Popup(title=self.t("image_diagnostics"), content=layout, size_hint=(.94, .9))
        layout.add_widget(button(self.t("close"), popup.dismiss))
        popup.open()

    def images_folder_dialog(self, path):
        layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        location = TextInput(text=str(path.resolve()), readonly=True, multiline=True,
                             size_hint_y=None, height=dp(70), font_size=dp(12))
        layout.add_widget(location)
        chooser = FileChooserListView(path=str(path.resolve()), rootpath=str(path.resolve()),
                                      dirselect=False, multiselect=False)
        layout.add_widget(chooser)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        popup = Popup(title=self.t("show_images"), content=layout, size_hint=(0.94, 0.85))

        def preview():
            if not chooser.selection:
                return
            selected = Path(chooser.selection[0]).resolve()
            if not selected.is_relative_to(path.resolve()) or not selected.is_file():
                return
            detail = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
            detail.add_widget(AsyncImage(source=str(selected), fit_mode="contain"))
            detail.add_widget(label(selected.name, 54, 11, MUTED))
            viewer = Popup(title=self.t("image_preview"), content=detail, size_hint=(0.94, 0.85))
            detail.add_widget(button(self.t("close"), viewer.dismiss))
            viewer.open()

        open_button = button(self.t("image_preview"), preview)
        open_button.disabled = True
        chooser.bind(selection=lambda obj, value: setattr(open_button, "disabled", not bool(value)))
        chooser.bind(on_submit=lambda *_: preview())
        actions.add_widget(open_button)
        actions.add_widget(button(self.t("close"), popup.dismiss))
        layout.add_widget(actions)
        popup.open()
        return popup

    def background(self, work, done, silent=False, title=None, error_key="offline", finished=None):
        if self.busy:
            if not silent:
                self.notify(self.t("busy"))
            return
        self.busy = True
        if not silent:
            self.begin_progress(self.t(title or "syncing"))

        def worker():
            try:
                value, error = work(), None
            except Exception as exc:
                value, error = None, exc

            def apply(dt):
                self.busy = False
                if not silent:
                    self.end_progress()
                try:
                    if error:
                        if not silent:
                            self.notify(self.t(error_key))
                    else:
                        done(value)
                finally:
                    if finished:
                        finished()

            Clock.schedule_once(apply)

        threading.Thread(target=worker, daemon=True).start()

    def download_button(self, provider, key, callback):
        widget = button(self.t(key), callback, height=58)
        widget.font_size = dp(12)
        widget.disabled_color = MUTED
        widget.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0] - dp(24), size[1])))
        self.download_buttons.append((widget, provider, key))
        self.update_download_buttons()
        return widget

    def update_download_buttons(self, *_):
        for widget, provider, key in self.download_buttons:
            remaining = self.download_cooldown.remaining(provider)
            widget.disabled = bool(remaining) or self.busy
            widget.text = self.t(key) + (" · " + self.download_cooldown.countdown(provider) if remaining else "")

    def begin_download(self, provider):
        if self.busy:
            self.notify(self.t("busy"))
            return False
        if not self.download_cooldown.start(provider):
            self.notify(self.t("download_wait", time=self.download_cooldown.countdown(provider)))
            return False
        self.update_download_buttons()
        return True

    def reload_catalog(self):
        if self.busy:
            self.notify(self.t("busy"))
            return
        try:
            self.catalog.reload()
        except (OSError, ValueError, KeyError, TypeError):
            self.notify(self.t("catalog_local_missing"))
            return
        if self.search_event:
            self.search_event.cancel()
        # Explicit refresh must decode the on-disk files again, not reuse an old
        # texture or a failed Loader placeholder. Files themselves stay intact.
        for category in ("kv.loader", "kv.image", "kv.texture"):
            Cache.remove(category)
        self.result_limit = 12
        self.fill_catalog(local_only=True)
        missing = sum(not self.catalog._has_image(self.catalog.image_path(c)) for c in self.catalog.cards)
        if missing:
            self.show_catalog_notice(self.t("images_missing_local", missing=missing, total=len(self.catalog.cards)))

    def show_catalog_notice(self, text):
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        content = self.scroller(layout)
        content.add_widget(label(text, 40, 14, adaptive=True))
        popup = Popup(title=self.t("catalog"), content=layout, size_hint=(.92, .65))
        layout.add_widget(button(self.t("close"), popup.dismiss))
        popup.open()

    def reload_prices(self):
        if self.busy:
            self.notify(self.t("busy"))
            return
        try:
            self.prices.reload()
        except (OSError, ValueError, KeyError, TypeError):
            self.notify(self.t("prices_local_missing"))
            return
        if self.page == "detail":
            self.update_price()
        elif self.page == "binder":
            self.refresh_binder_prices()

    def sync(self):
        if not self.begin_download("netdeck"):
            return
        self.catalog_download_active = True
        if platform == "android":
            self.bridge.keep_screen_on(True)

        def done(report):
            self.art_generation = object()
            self.catalog_body = None
            self.render()
            message = (self.t("catalog_up_to_date") if report["up_to_date"] else
                       self.t("catalog_images_done", available=report["available"], total=report["cards"]))
            if report["missing"]:
                message += "\n" + self.t("catalog_images_partial", missing=report["missing"])
            self.show_catalog_notice(message)

        def progress(current, total):
            def update(dt):
                self.progress_value = min(100, 100 * current / max(1, total))
                self.progress_text = self.t("catalog_progress", current=current, total=total)
            Clock.schedule_once(update)

        def images_progress(current, total):
            def update(dt):
                self.progress_value = min(100, 100 * current / max(1, total))
                self.progress_text = self.t("images_progress", current=current, total=total)
            Clock.schedule_once(update)

        def finished():
            self.catalog_download_active = False
            self.update_footer()
            if platform == "android":
                self.bridge.keep_screen_on(False)

        self.background(lambda: self.catalog.download_catalog(progress, images_progress), done,
                        finished=finished)

    def refresh_fx(self, silent=False):
        def done(date):
            if self.page == "settings":
                self.render()
            if self.page == "detail":
                self.update_price()
            if self.page == "binder":
                self.refresh_binder_prices()
            if not silent:
                self.notify(self.t("fx_date", date=date))

        self.background(self.fx.refresh, done, silent)

    def export(self, binder_id=None):
        text = self.store.export_csv(binder_id or self.binder_id)
        if platform == "android":
            self.document_action(
                AndroidBridge.SAVE,
                lambda value, error: (
                    self.notify(self.t("error" if error else "export_done")) if value or error else None
                ),
                text=text,
            )
        else:

            def save(path):
                try:
                    Path(path).write_text(text, encoding="utf-8", newline="")
                    self.notify(self.t("export_done"))
                except OSError:
                    self.notify(self.t("error"))

            self.file_dialog(save, saving=True)

    def import_binder(self, restore=False):
        callback = self.restore_text if restore else self.import_text
        if platform == "android":
            self.document_action(AndroidBridge.OPEN, callback)
        else:

            def load(path):
                try:
                    if Path(path).stat().st_size > 10_000_000:
                        raise ValueError("size")
                    text = Path(path).read_text(encoding="utf-8-sig")
                    callback(text, None, Path(path).stem)
                except (OSError, ValueError):
                    self.notify(self.t("import_error"))

            self.file_dialog(load)

    def confirm(self, message, action, title_key="confirm_delete", accept_key="delete"):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(label(message, 140, 14))
        popup = Popup(title=self.t(title_key), content=content,
                      size_hint=(0.92, None), height=dp(310))

        def accept():
            popup.dismiss()
            action()

        content.add_widget(button(self.t(accept_key), accept, True))
        content.add_widget(button(self.t("cancel"), popup.dismiss))
        popup.open()

    def delete_binder(self):
        binder_id = self.binder_id

        def remove():
            self.store.delete_binder(binder_id)
            self.binder_id = "mine"
            self.history.clear()
            self.navigate("binder", remember=False)
            self.notify(self.t("binder_deleted"))

        key = "confirm_clear" if binder_id == "mine" else "confirm_binder"
        self.confirm(self.t(key, name=self.binder_names()[binder_id]), remove)

    def document_action(self, kind, callback, **kwargs):
        if self.busy:
            self.notify(self.t("busy"))
            return
        self.busy = True
        self.begin_progress(self.t("document_work"))

        def done(value, error):
            self.busy = False
            self.end_progress()
            self.notify("")
            callback(value, error)

        try:
            self.bridge.launch(kind, done, **kwargs)
        except Exception as exc:
            done(None, str(exc))

    def delete_file(self):
        if platform == "android":
            def selected(value, error):
                if error:
                    self.notify(self.t("delete_failed"))
                elif value:
                    def remove():
                        self.busy = True
                        self.begin_progress(self.t("document_work"))

                        def done(ok, error):
                            self.busy = False
                            self.end_progress()
                            self.notify(self.t("file_deleted" if ok and not error else "delete_failed"))

                        self.bridge.delete_document(value["uri"], done)
                    self.confirm(self.t("confirm_file", name=value["name"]), remove)
            self.document_action(AndroidBridge.DELETE, selected)
        else:
            def selected(path):
                def remove():
                    try:
                        Path(path).unlink()
                        self.notify(self.t("file_deleted"))
                    except OSError:
                        self.notify(self.t("delete_failed"))
                self.confirm(self.t("confirm_file", name=str(path)), remove)
            self.file_dialog(selected)

    def import_text(self, text, error, name=None):
        if error:
            self.notify(self.t("import_error"))
        elif text is not None:
            binder_name = name or ("Import " + str(len(self.store.binders())))

            def work():
                store = Store(self.data_dir / "binder.sqlite3")
                try:
                    return store.import_csv(text, binder_name)
                finally:
                    store.close()

            def done(binder_id):
                self.binder_id = binder_id
                self.navigate("binder")
                self.notify(self.t("import_done"))

            self.background(work, done, title="document_work", error_key="import_error")

    def restore_text(self, text, error, name=None):
        if error:
            self.notify(self.t("import_error"))
            return
        if text is None:
            return

        def restore():
            def work():
                store = Store(self.data_dir / "binder.sqlite3")
                try:
                    return store.restore_csv(text)
                finally:
                    store.close()

            def done(count):
                self.binder_id = "mine"
                self.history.clear()
                self.navigate("binder", remember=False)
                self.notify(self.t("restore_done", count=count))

            self.background(work, done, title="document_work", error_key="import_error")

        self.confirm(self.t("confirm_restore"), restore,
                     title_key="restore_backup", accept_key="restore")

    def file_dialog(self, callback, saving=False):
        layout = BoxLayout(orientation="vertical", spacing=dp(8))
        chooser = FileChooserListView(path=str(self.data_dir.resolve()), filters=["*.csv"])
        layout.add_widget(chooser)
        filename = field(text="NightCityBinder.csv")
        if saving:
            layout.add_widget(filename)
        popup = Popup(title=self.t("save" if saving else "open"), content=layout, size_hint=(0.94, 0.85))
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        actions.add_widget(button(self.t("cancel"), popup.dismiss))

        def complete():
            path = (
                Path(chooser.path) / Path(filename.text).name
                if saving
                else (Path(chooser.selection[0]) if chooser.selection else None)
            )
            if path:
                if saving and path.exists():
                    # Use a unique filename rather than overwrite an existing export.
                    stem, suffix, index = path.stem, path.suffix, 2
                    while path.exists():
                        path = path.with_name(f"{stem}-{index}{suffix}")
                        index += 1
                popup.dismiss()
                callback(path)

        actions.add_widget(button(self.t("save" if saving else "open"), complete, True))
        layout.add_widget(actions)
        popup.open()

    def on_pause(self):
        return True

    def on_stop(self):
        if self.catalog_download_active and platform == "android":
            self.bridge.keep_screen_on(False)
        self.cooldown_event.cancel()
        self.progress_event.cancel()
        if hasattr(self, "insets_event"):
            self.insets_event.cancel()
        self.store.close()
