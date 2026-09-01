"""
Refs

- https://github.com/tmux/tmux/issues/1477
"""

from __future__ import absolute_import, division, print_function

import os
import subprocess

from ranger.config.commands import set_, yank


class TTYNotFound(Exception):
    pass


def osc52_payload(content):
    import base64

    return b"\033]52;c;%s\a" % base64.b64encode(content.encode("utf-8"))


class set_oscyank(set_):
    """:set_oscyank <option name>=<string>

    Bypass the limit of `set` for custom oscyank options.
    Note: don't quote string values.
    """

    name = "set_oscyank"

    def execute(self):
        name = self.arg(1)
        name, value, _, toggle = self.parse_setting_line_v2()
        name = self.__class__.name[4:] + ":" + name
        if name.endswith("?"):
            self.fm.notify(self.fm.settings._settings.get(name[:-1], ""), 10)
        elif toggle:
            # self.fm.toggle_option(name)
            self.toggle_option(name)
        else:
            # self.fm.set_option_from_string(name, value)
            self.set_option_from_string(name, value)

    def toggle_option(self, option_name):
        current = self.fm.settings._settings.get(option_name, False)
        if isinstance(current, bool):
            self.fm.settings._settings[option_name] = not current
        else:
            self.fm.notify(option_name + " is not a boolean option", bad=True)

    def set_option_from_string(self, option_name, value):
        if not isinstance(value, str):
            raise ValueError("The value for an option needs to be a string.")
        self.fm.settings._settings[option_name] = self._parse_option_value(
            option_name, value
        )

    def _parse_option_value(self, name, value):
        if value.lower() in ("true", "on", "yes", "1"):
            return True
        if value.lower() in ("false", "off", "no", "0"):
            return False
        if value.lower() == "none":
            return None
        # All other values are strings. No int, float, list support yet
        return value


class oscyank(yank):
    """:oscyank [name|dir|path]

    Copies the file's name (default), directory or path into the system
    clipboard with OSC52.
    """

    def execute(self):
        mode = self.modes[self.arg(1)]
        selection = self.get_selection_attr(mode)
        selection = self.process_selection(mode, selection)
        content = "\n".join(selection)

        self.osc_copy(content)

    def process_selection(self, mode, selection):
        if mode.startswith("basename") or self.quantifier is None:
            return selection

        home_with_slash = os.path.expanduser("~")
        if not home_with_slash.endswith(os.sep):
            home_with_slash = os.path.join(home_with_slash, "")
        length = len(home_with_slash)
        if self.quantifier == 1:
            selection = [
                os.path.join("~", _[length:]) if _.startswith(home_with_slash) else _
                for _ in selection
            ]
        elif self.quantifier == 2:
            selection = [
                _[length:] if _.startswith(home_with_slash) else _ for _ in selection
            ]
        return selection

    def osc_copy(self, content):
        max_length = self.fm.settings._settings.get("oscyank:max_length", 0)
        try:
            max_length = int(max_length)
        except (TypeError, ValueError):
            max_length = 0
        content_length = len(content.encode("utf-8"))
        if max_length > 0 and content_length > max_length:
            self.fm.notify(
                "Selection is too large for OSC52 ({} bytes, limit {})".format(
                    content_length, max_length
                ),
                bad=True,
            )
            return

        tty = self.get_tty()
        with open(tty, "wb") as fobj:
            fobj.write(osc52_payload(content))

    def get_tty_from_tmux(self):
        try:
            output = subprocess.check_output(
                ["tmux", "list-panes", "-F", "#{pane_active} #{pane_tty}"]
            )
            if isinstance(output, bytes):
                output = output.decode("utf-8", "replace")
            for line in output.splitlines():
                fields = line.split()
                if len(fields) >= 2 and fields[0] == "1":
                    return fields[1]
        except (OSError, subprocess.CalledProcessError):
            pass
        raise TTYNotFound

    def get_tty(self):
        tty = None
        try:
            tty = subprocess.check_output(["tty"]).strip()
            if isinstance(tty, bytes):
                tty = tty.decode("utf-8", "replace")
            if tty == "not a tty":
                tty = None
        except (OSError, subprocess.CalledProcessError):
            pass

        if not tty and "TMUX" in os.environ:
            tty = self.get_tty_from_tmux()
        if not tty:
            self.fm.notify("No available tty is found!", bad=True)
            raise TTYNotFound
        return tty
