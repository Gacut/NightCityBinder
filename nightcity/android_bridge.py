"""All Android-specific Python imports are isolated here."""

from kivy.clock import Clock
from kivy.utils import platform
import threading


class AndroidBridge:
    SCAN, OPEN, SAVE, DELETE = 4311, 4312, 4313, 4314

    def __init__(self):
        self.callback = None
        self.export_text = ""
        if platform == "android":
            from android import activity

            activity.bind(on_activity_result=self._result)

    def launch(self, kind, callback, language="en", text=""):
        if self.callback is not None:
            raise RuntimeError("busy")
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        self.callback, self.export_text = callback, text

        @run_on_ui_thread
        def start():
            try:
                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                Intent = autoclass("android.content.Intent")
                if kind == self.SCAN:
                    intent = Intent()
                    intent.setClassName(activity.getPackageName(), "org.nightcitybinder.ScannerActivity")
                    intent.putExtra("language", language)
                elif kind in (self.OPEN, self.DELETE):
                    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
                    intent.setType("*/*")
                    intent.addCategory(Intent.CATEGORY_OPENABLE)
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                else:
                    intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
                    intent.setType("text/csv")
                    intent.addCategory(Intent.CATEGORY_OPENABLE)
                    intent.putExtra(Intent.EXTRA_TITLE, "NightCityBinder.csv")
                activity.startActivityForResult(intent, kind)
            except Exception as exc:
                self._deliver(None, str(exc))

        start()

    def safe_area(self, callback):
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def read():
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            values = list(autoclass("org.nightcitybinder.SafeArea").overlap(activity))
            Clock.schedule_once(lambda dt: callback(values), 0)

        read()

    def keep_screen_on(self, enabled):
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def update():
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            flag = autoclass("android.view.WindowManager$LayoutParams").FLAG_KEEP_SCREEN_ON
            if enabled:
                activity.getWindow().addFlags(flag)
            else:
                activity.getWindow().clearFlags(flag)

        update()

    def delete_document(self, uri, callback):
        def worker():
            try:
                from jnius import autoclass

                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                value = autoclass("org.nightcitybinder.DocumentIO").delete(
                    activity, autoclass("android.net.Uri").parse(uri))
                error = None if value else "delete_failed"
            except Exception as exc:
                value, error = None, str(exc)
            Clock.schedule_once(lambda dt: callback(value, error), 0)

        threading.Thread(target=worker, daemon=True).start()

    def request_camera(self, callback):
        from android.permissions import Permission, check_permission, request_permissions

        if check_permission(Permission.CAMERA):
            callback(True)
            return

        def result(permissions, grants):
            granted = bool(grants) and all(grants)
            Clock.schedule_once(lambda dt: callback(granted), 0)

        request_permissions([Permission.CAMERA], result)

    def open_settings(self):
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def start():
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            intent = autoclass("android.content.Intent")("android.settings.APPLICATION_DETAILS_SETTINGS")
            intent.setData(autoclass("android.net.Uri").parse("package:" + activity.getPackageName()))
            activity.startActivity(intent)

        start()

    def _deliver(self, value, error=None):
        callback, self.callback = self.callback, None
        self.export_text = ""
        if callback:
            Clock.schedule_once(lambda dt: callback(value, error), 0)

    def _result(self, request, result, intent):
        if request not in (self.SCAN, self.OPEN, self.SAVE, self.DELETE) or self.callback is None:
            return
        if result != -1 or intent is None:
            self._deliver(None)
            return
        try:
            from jnius import autoclass

            if request == self.SCAN:
                self._deliver({"text": intent.getStringExtra("text") or "",
                               "number_text": intent.getStringExtra("number_text") or ""},
                              intent.getStringExtra("error"))
            else:
                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                helper = autoclass("org.nightcitybinder.DocumentIO")
                uri, export_text = intent.getData(), self.export_text

                def worker():
                    try:
                        if request == self.DELETE:
                            value = {"uri": str(uri.toString()), "name": str(helper.name(activity, uri))}
                        elif request == self.OPEN:
                            value = helper.read(activity, uri)
                        else:
                            helper.write(activity, uri, export_text)
                            value = True
                        self._deliver(value)
                    except Exception as exc:
                        self._deliver(None, str(exc))

                threading.Thread(target=worker, daemon=True).start()
        except Exception as exc:
            self._deliver(None, str(exc))
