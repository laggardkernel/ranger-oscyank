"""
Refs

- https://github.com/tmux/tmux/issues/1477
"""

from __future__ import absolute_import, division, print_function

import curses
import os
import subprocess
from functools import partial

from ranger.config.commands import set_, yank


class TTYNotFound(Exception):
    pass


class set_oscyank(set_):
    """:set_oscyank <option name>=<string>

    Bypass limit of `set` that not support custom options.
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

    Copies the file's name (default), directory or path into system clipboard
    with OSC 52 support. Fallbacks to default 'yank' command which uses
    the primary X selection and the clipboard.
    """

    def execute(self):
        copy_func = None
        if self.do_prefer_osc():
            copy_func = self.osc_copy
        else:
            clipboard_cmd = self.get_clipboard_cmd()
            if clipboard_cmd:
                copy_func = partial(self.clipboard_copy, clipboard_cmd)
        if copy_func is None:
            copy_func = self.osc_copy

        mode = self.modes[self.arg(1)]
        selection = self.get_selection_attr(mode)
        selection = self.process_selection(mode, selection)
        content = "\n".join(selection)

        copy_func(content)

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

    @classmethod
    def clipboard_copy(cls, command, content):
        process = subprocess.Popen(
            command, universal_newlines=True, stdin=subprocess.PIPE
        )
        process.communicate(input=content)

    def do_prefer_osc(self):
        explicit_backend = self.fm.settings._settings.get("oscyank:backend", "auto")
        if explicit_backend in ("osc52", "osc"):
            return True
        elif explicit_backend == "manager":
            return False
        return "SSH_TTY" in os.environ and curses.tigetstr("Ms")

    def osc_copy(self, content):
        import base64

        tty = self.get_tty()
        with open(tty, "wb") as fobj:
            r = b""  # osc sequence

            # kitty has obsolete the modified chunking protocol since 0.22.
            # No need to keep the clear sequence for backward support.
            # if (
            #     "kitty" == os.environ.get("LC_TERMINAL")
            #     or "KITTY_WINDOW_ID" in os.environ
            #     or "xterm-kitty" == os.environ.get("TERM")
            # ):
            #     r += b"\033]52;c;!\a"

            r += b"\033]52;c;%s\a" % base64.b64encode(content.encode("utf-8"))

            # https://github.com/tmux/tmux/wiki/Clipboard
            # Passthrough of OSC52 seq is controlled by `allow-passthrough` in tmux.
            #  No need to wrap the escape sequence with \ePtmux{seq}\e\\ anymore.
            # if os.environ.get("TMUX"):
            #     r = r.replace(b"\033", b"\033\033")
            #     r = b"\033Ptmux;%s\033\\" % r

            # WARN: terminals may limit the max size of escape seq
            fobj.write(r)

    @classmethod
    def get_clipboard_cmd(cls):
        from ranger.ext.get_executables import get_executables

        executables = get_executables()
        clipboard_cmds = (
            "pbcopy",
            "wl-copy",
            "termux-clipboard-get",
            "xclip -i -selection clipboard",
            "xsel -i --clipboard",
        )
        for cmd_str in clipboard_cmds:
            cmd_list = cmd_str.split()
            if cmd_list[0] in executables:
                return cmd_list
        return []

    def get_tty_from_tmux(self):
        try:
            tmux_tty = [
                tty
                for is_active, tty in (
                    line.split()
                    for line in subprocess.check_output(
                        ["tmux", "list-panes", "-F", "#{pane_active} #{pane_tty}"]
                    )
                    .strip()
                    .split(b"\n")
                )
                if is_active
            ][0]
        except (subprocess.CalledProcessError, IndexError):
            raise TTYNotFound
        return tmux_tty

    def get_tty(self):
        tty = None
        try:
            tty = subprocess.check_output(["tty"]).strip()
            if tty == "not a tty":
                tty = None
        except subprocess.CalledProcessError:
            pass

        if not tty:
            if "TMUX" in os.environ:
                tty = self.get_tty_from_tmux()
            else:
                self.fm.notify("No available tty is found!", bad=True)
                raise TTYNotFound
        return tty
