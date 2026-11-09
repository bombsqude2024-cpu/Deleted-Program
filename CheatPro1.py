# ba_meta require api 9
"""CheatPro1 - API 9 compatibility port for BombSquad 1.7.62.

Combat-enhancement and bomb-type modifications from the original are not
implemented in this version.
"""

from __future__ import annotations

from typing import Any

import babase
import bauiv1 as bui
import bascenev1 as bs

__author__ = "OpenAI / port of egg GUI Cheat Pro"
__version__ = '1.0.0'

_CONFIG_NAME = 'CheatPro1 Settings'
_DEFAULTS: dict[str, Any] = {
    # Corrected names describe what the original code actually did.
    'آسیب‌ناپذیری بازیکنان': False,
    'حالت پرواز': False,
    'حالت هاکی (لغزندگی)': False,
    # The source's ping code referenced an undefined `bs.lage`; this is
    # retained as an informational toggle instead of crashing the loop.
    'اطلاع‌رسانی پینگ (نمایشی)': False,
}


def _get_config() -> dict[str, Any]:
    config = babase.app.config
    if _CONFIG_NAME not in config:
        config[_CONFIG_NAME] = dict(_DEFAULTS)
        config.apply_and_commit()
    else:
        for key, value in _DEFAULTS.items():
            config[_CONFIG_NAME].setdefault(key, value)
    return config[_CONFIG_NAME]


def _save_value(key: str, value: bool) -> None:
    _get_config()[key] = bool(value)
    babase.app.config.apply_and_commit()


def _is_local_host() -> bool:
    """Return True only when this device owns the foreground host session."""
    try:
        session = bs.get_foreground_host_session()
        if session is None:
            return False
        return any(
            getattr(getattr(player, 'inputdevice', None), 'client_id', None) == -1
            for player in session.sessionplayers
        )
    except Exception:
        return False


def _open_settings_window(source_widget: bui.Widget | None = None) -> None:
    try:
        main_window = bui.app.ui_v1.get_main_window()
        if main_window is not None and main_window.main_window_has_control():
            main_window.main_window_replace(
                CheatPro1Window(origin_widget=source_widget)
            )
    except Exception as exc:
        print(f'[CheatPro1] could not open settings: {exc}')


def _patch_settings_button() -> None:
    """Add a direct entry to the built-in Settings screen, as the API-6 source did."""
    try:
        from bauiv1lib.settings.allsettings import AllSettingsWindow
        if getattr(AllSettingsWindow, '_cheatpro1_patched', False):
            return
        original_init = AllSettingsWindow.__init__

        def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)
            try:
                uiscale = bui.app.ui_v1.uiscale
                x = 720 if uiscale is bui.UIScale.SMALL else 400
                bui.buttonwidget(
                    parent=self._root_widget,
                    position=(x, 380),
                    size=(118, 54),
                    label='CheatPro1',
                    button_type='square',
                    text_scale=0.85,
                    on_activate_call=bui.Call(
                        _open_settings_window, self._root_widget
                    ),
                )
            except Exception as exc:
                print(f'[CheatPro1] settings button: {exc}')

        AllSettingsWindow.__init__ = patched_init
        AllSettingsWindow._cheatpro1_patched = True
    except Exception as exc:
        # Plugin Manager settings UI remains available as a fallback.
        print(f'[CheatPro1] built-in settings hook unavailable: {exc}')


def _activity_loop() -> None:
    """Apply enabled options while this device is hosting a classic activity."""
    try:
        activity = bs.get_foreground_host_activity()
        if activity is None or not _is_local_host():
            return
        config = _get_config()
        with activity.context:
            for player in list(activity.players):
                actor = getattr(player, 'actor', None)
                if actor is None:
                    continue
                node = getattr(actor, 'node', None)
                if node is None:
                    continue

                # Apply only properties supported by the current actor/node.
                try:
                    node.invincible = bool(config['آسیب‌ناپذیری بازیکنان'])
                except Exception:
                    pass
                try:
                    node.fly_pressed = bool(config['حالت پرواز'])
                except Exception:
                    pass
                try:
                    node.hockey = bool(config['حالت هاکی (لغزندگی)'])
                except Exception:
                    pass
    except Exception as exc:
        # Never let a transient activity transition stop the repeating timer.
        print(f'[CheatPro1] activity loop: {exc}')


class CheatPro1Window(bui.MainWindow):
    """API-9 settings window for supported non-combat options."""

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
    ) -> None:
        uiscale = bui.app.ui_v1.uiscale
        self._width = 760.0 if uiscale is bui.UIScale.SMALL else 650.0
        self._height = 520.0
        scale = (
            1.45 if uiscale is bui.UIScale.SMALL
            else 1.15 if uiscale is bui.UIScale.MEDIUM
            else 1.0
        )
        root = bui.containerwidget(
            size=(self._width, self._height),
            scale=scale,
            transition=transition,
            toolbar_visibility='menu_minimal',
        )
        super().__init__(
            root_widget=root,
            transition=transition,
            origin_widget=origin_widget,
        )

        self._back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, self._height - 65),
            size=(60, 55),
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=self._back_button,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(0, self._height - 48),
            size=(self._width, 30),
            text='CHEAT PRO 1  |  API 9',
            color=(0.85, 0.9, 1.0),
            scale=1.15,
            h_align='center',
            v_align='center',
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(55, self._height - 112),
            size=(self._width - 110, 25),
            text='تنظیمات فقط هنگام میزبانی بازی اعمال می‌شوند',
            color=(0.72, 0.82, 0.92),
            scale=0.8,
            h_align='center',
        )

        config = _get_config()
        y = self._height - 175
        for key in _DEFAULTS:
            bui.checkboxwidget(
                parent=self._root_widget,
                position=(90, y),
                size=(42, 42),
                text=key,
                textcolor=(0.88, 0.92, 1.0),
                value=bool(config.get(key, False)),
                on_value_change_call=bui.Call(self._on_change, key),
                maxwidth=self._width - 190,
                scale=1.0,
            )
            y -= 55

        bui.textwidget(
            parent=self._root_widget,
            position=(45, 18),
            size=(self._width - 90, 28),
            text='گزینه پینگ فقط نمایشی است؛ تغییر پینگ واقعی در این مود انجام نمی‌شود.',
            color=(0.68, 0.72, 0.78),
            scale=0.62,
            h_align='center',
        )

    def _on_change(self, key: str, value: bool) -> None:
        _save_value(key, value)
        if key == 'اطلاع‌رسانی پینگ (نمایشی)' and value:
            bui.screenmessage(
                'این گزینه پینگ واقعی شبکه را تغییر نمی‌دهد.',
                color=(1.0, 0.8, 0.25),
            )
        else:
            bui.getsound('gunCocking').play()


# ba_meta export babase.Plugin
class CheatPro1Plugin(babase.Plugin):
    """API-9 plugin entry point."""

    def on_app_running(self) -> None:
        _get_config()
        _patch_settings_button()
        babase.apptimer(2.0, _activity_loop, repeat=True)
        print('[CheatPro1] loaded (API 9)')

    def has_settings_ui(self) -> bool:
        return True

    def show_settings_ui(self, source_widget: bui.Widget | None) -> None:
        main_window = bui.app.ui_v1.get_main_window()
        if main_window is None or not main_window.main_window_has_control():
            bui.screenmessage('ابتدا به منوی اصلی برگرد.', color=(1.0, 0.7, 0.2))
            return
        main_window.main_window_replace(
            CheatPro1Window(origin_widget=source_widget)
        )
